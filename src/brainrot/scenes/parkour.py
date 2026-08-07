"""First-person infinite parkour, the way the actual background reels do it.

The reference footage is first-person Minecraft: an endless course of brightly
coloured blocks floating high over scenic terrain, one flawless sprint-jump
every beat, blocks materialising a few hops ahead and vanishing a couple
behind.

What makes those reels watchable for more than ten seconds is that the course
keeps *changing shape*. It is not a uniform stream of cubes: it arrives in
recognisable pieces -- a staircase, a plank causeway, a spiral round a tower,
a gate you run through, a long fall onto a lantern-lit platform -- and each
piece is built from one family of materials, so the eye reads a structure
rather than a queue of blocks. So generation here works in **segments**: the
generator picks a set-piece, expands it into a run of nodes, and lays those
nodes down one at a time. :data:`SEGMENT_TABLE` is the whole vocabulary.

Two things about the motion are worth knowing before changing any of it.

**The course knows its own path.** Where the player will stand on each block
is drawn when the block is generated, not when it is landed on, so the exact
ballistic arc of every future hop is computable at generation time. That is
what lets orbs hang *on* the flight path rather than near it: a pickup is
placed at the chest height of a body that is going to pass through that point,
so collecting it is a fact about the course rather than a hope about the
simulation. ``tests/test_generation.py`` asserts every orb laid down is taken.

**Flight time comes from the drop, not just the distance.** A hop covers its
gap at running pace, but a fall takes as long as a fall takes -- so descents
hang in the air, which is what makes a drop read as a drop instead of as a
step down.

Far below: an ocean with reef shallows, drifting cloud shelves, and wooded
voxel islands -- the drop is what supplies the vertigo, so the world down
there exists to be fallen toward, never reached.

Two things carry more of the "this is Minecraft" reading than any amount of
terrain: whatever is in the player's hand swinging in the corner of the frame,
and the crosshair in the middle of it. Both are here, because a first-person
shot without them reads as a generic flying camera.
"""

from __future__ import annotations

import math

from ..engine import rl, voxel
from ..engine.collide import AABB, model_aabb, placed
from ..engine.fx import Burst, Weather, glow_billboard, ground_quad, unit_quad
from ..engine.hud import text
from ..engine.scene import Scene, SceneContext, register
from ..engine import textures
from ..engine.sky import SkyDome
from ..engine.textures import cloud_blob

#: weighted like the reference generator: mostly short hops, rare long ones
GAP_TABLE = (1, 1, 1, 2, 2, 2, 2, 3, 3, 4)
RISE_TABLE = (-2, -1, -1, 0, 0, 0, 0, 0, 1, 1)

EYE = 1.62
COURSE_ALT = 58.0          # block altitude above the ocean
#: How far the course may wander from its altitude before the generator insists
#: on going the other way. Wide enough that a descent set-piece has somewhere
#: to fall to.
BAND = 18.0
TRAIL = 2                  # blocks kept behind the player
AHEAD = 14                 # blocks generated ahead
FOG_FAR = 70.0
BELOW_FOG = 0.55           # extra fog on the world far below

GRAVITY = 26.0
HOP_SPEED = 5.3            # horizontal m/s while airborne
#: Take-off speed a hop would use if it were only clearing a gap. Descents are
#: timed against this: the arc leaves the block like any other hop and then
#: simply keeps falling, which is what makes a five-block drop feel like one.
HOP_LAUNCH = 4.6
#: A level hop never hangs longer than this however wide the gap; without the
#: cap a chasm turns into a moon jump.
AIR_LEVEL_MAX = 0.85
AIR_MIN, AIR_MAX = 0.42, 1.30
#: Fastest a hop may cross the ground. Anything above this stops reading as a
#: jump and starts reading as a dolly move; asserted in the generation tests.
HOP_SPEED_MAX = 9.0
#: Shortest hop the generator will lay down, measured stand point to stand
#: point. Below this it is a shuffle, not a jump.
MIN_HOP = 1.5

#: The player's collision volume: vanilla's own 0.6 x 1.8 box, standing on the
#: block surface. There is no player model in first person to measure, so this
#: is the one volume in the scene that is declared rather than derived -- and
#: everything it collects has its box built from the model that draws it.
BODY_HALF_W = 0.30
BODY_H = 1.80
#: Where on that body an orb is aimed, so passing through it cannot miss.
CHEST = 0.90

#: form -> height of the walking surface above the block's base.
FORMS = {"full": 1.0, "slab": 0.5, "wide": 1.0, "stair": 1.0}
#: form -> how far off centre a landing may wander. A three-wide breather
#: platform is a place to relax; a single block is not.
MARGIN = {"wide": 0.9}

#: The set-piece vocabulary, with its weights. Names map to ``_seg_<name>``.
SEGMENT_TABLE = (
    ("cruise", 30),
    ("staircase", 10),
    ("descent", 10),
    ("zigzag", 10),
    ("chasm", 8),
    ("causeway", 9),
    ("spiral", 8),
    ("gate", 7),
    ("lanternwalk", 6),
)
#: Segments that climb, and segments that fall. Whichever way the course has
#: drifted, the other list gets the weight -- which is how verticality happens
#: without the altitude band ever having to veto a set-piece halfway through.
CLIMBERS = frozenset(("staircase", "spiral"))
FALLERS = frozenset(("descent",))
#: Set-pieces that dictate their own heading, and so cannot be steered.
TURNERS = frozenset(("spiral", "zigzag"))


@register("parkour")
class ParkourScene(Scene):
    def __init__(self, ctx: SceneContext) -> None:
        super().__init__(ctx)
        pal = ctx.palette
        seed = ctx.seed

        self.sky = SkyDome(pal, seed, ctx.width, ctx.height)
        self.weather = Weather(pal, ctx.width, ctx.height, seed.root & 0xFFFF)
        self.burst = Burst()
        self.camera = rl.make_camera(70.0)
        self.detail = {"high": 1.0, "balanced": 0.7, "low": 0.45}.get(ctx.quality, 1.0)

        self.styles = _build_styles(pal, seed.run)
        self.candy = ["candy0", "candy1", "candy2"]

        self.rng = ctx.stream("course")
        self.irng = ctx.stream("islands")
        self.hop_rng = ctx.stream("hops")

        # What the player is carrying. Deliberately never one of the course
        # colours: a held block in the same candy family as the platforms just
        # reads as another platform floating oddly close to the lens.
        self.kit = _choose_kit(ctx.stream("kit"), pal)
        self.sleeve = voxel.block_model(f"run{seed.run}-sleeve", pal.accent,
                                        noise=0.03, seed=seed.run * 13 + 4)
        self.skin = voxel.block_model("hand-skin", (198, 148, 112),
                                      noise=0.03, seed=17)
        self.swing = 0.0
        self.mine = 0.0            # a deliberate swing of the held item
        self.place = 0.0           # the thrust that puts a block down

        # -- course --------------------------------------------------------
        self.blocks: list[dict] = []
        self.heading = 0.0            # radians, 0 = -Z
        #: What a held direction is doing to the course, -1..1. Zero on
        #: autopilot, which is every frame nobody has taken the keyboard.
        self.steer = 0.0
        self.driven_t = 0.0
        self._pending: list[dict] = []
        self.segment = "cruise"
        self._spawn_block(first=True)
        while len(self.blocks) < AHEAD:
            self._spawn_block()

        # -- motion: a ground/air state machine, not a tween ---------------
        # Real parkour footage has a beat ON each block (land, settle, aim)
        # and a ballistic arc between them: constant horizontal velocity,
        # gravity vertically. Easing positions between block centres reads as
        # teleportation, which is exactly what this replaces.
        self.jump_index = 0           # block we are standing on
        self.phase = "ground"
        self.phase_t = 0.0
        self.ground_dur = 0.5
        self.air_dur = 0.6
        self.stand = list(self._stand_point(self.blocks[0]))
        self.takeoff = list(self.stand)
        self.land_at = list(self.stand)
        self.vy0 = 0.0
        self.pos = list(self.stand)
        self.vy = 0.0
        self.land_dip = 0.0
        self.distance = 0.0
        self.hops = 0
        self.yaw = self.heading
        self._roll = 0.0

        # -- scoring -------------------------------------------------------
        self.orbs = 0
        self.orbs_missed = 0
        self.combo = 0
        self.best_combo = 0
        self.combo_t = 0.0

        # -- world below ---------------------------------------------------
        self.islands: list[dict] = []
        self._next_island_z = 0.0
        for _ in range(6):
            self._spawn_island()

        # Cloud shelves: few, wide and low. Small crisp ones scattered under
        # the course read as sheets of paper on the sea, because that is
        # geometrically what they are; a broken layer of large faint ones a
        # long way down reads as weather.
        self.shelves = []
        crng = ctx.stream("shelves")
        for i in range(int(9 * self.detail) or 4):
            self.shelves.append({
                "tex": cloud_blob(seed.run * 31 + i, 160),
                "x": crng.uniform(-110, 110),
                "z": -crng.uniform(0, 300),
                "y": crng.uniform(13, 22),
                "s": crng.uniform(46, 95),
                "yaw": crng.uniform(0, 360),
                "drift": crng.uniform(0.4, 1.4),
            })
        self.cloud_tint = rl.mix_rgb(pal.sky_bottom, (255, 255, 255), 0.55)

    # -- style catalogue ---------------------------------------------------

    def _model(self, name: str):
        return self.styles[name]["model"]

    def _colour(self, name: str) -> rl.RGB:
        return self.styles[name]["color"]

    # -- generation: segments ---------------------------------------------

    def _node(self, gap: float, rise: float, style: str, turn: float | None = None,
              form: str = "full", deco: str | None = None, orbs: int = 0) -> dict:
        return {"gap": gap, "rise": rise, "turn": turn, "form": form,
                "style": style, "deco": deco, "orbs": orbs}

    def _plan_segment(self) -> None:
        """Choose the next set-piece and expand it into nodes."""
        rng = self.rng
        y = self.blocks[-1]["y"] if self.blocks else COURSE_ALT
        drift = (y - COURSE_ALT) / BAND        # -1 floor, +1 ceiling

        weights = []
        for name, weight in SEGMENT_TABLE:
            if name in FALLERS:
                if drift < -0.35:
                    continue                   # already low: nothing to fall to
                weight = int(weight * (1.0 + 2.0 * max(0.0, drift)))
            elif name in CLIMBERS:
                if drift > 0.55:
                    continue
                weight = int(weight * (1.0 + 2.0 * max(0.0, -drift)))
            # Never the same set-piece twice running: repetition is the exact
            # complaint this whole mechanism exists to answer.
            if name == self.segment and name != "cruise":
                continue
            # A set-piece that dictates its own turns is not steerable, and a
            # player holding a direction through one is a player pressing a
            # key that does nothing. Taking the wheel calms the choreography.
            if self.steer and name in TURNERS:
                continue
            weights.append((name, max(1, weight)))

        roll = rng.random() * sum(w for _, w in weights)
        upto = 0.0
        name = weights[-1][0]
        for candidate, weight in weights:
            upto += weight
            if roll <= upto:
                name = candidate
                break
        self.segment = name
        self._pending = getattr(self, f"_seg_{name}")(rng)

    def _seg_cruise(self, rng) -> list[dict]:
        """The default: hops from the weighted tables, in the candy colours."""
        out = []
        for i in range(rng.randint(4, 9)):
            out.append(self._node(
                gap=rng.choice(GAP_TABLE), rise=rng.choice(RISE_TABLE),
                style=self.candy[(i // 2) % 3],
                form="slab" if rng.random() < 0.18 else "full",
                deco="crumb" if rng.random() < 0.22 else None,
                orbs=1 if rng.random() < 0.45 else 0))
        # a breather platform closes some cruises, as somewhere to arrive.
        # Its posts are unlit: lanterns are what mark the set-pieces, and a
        # lantern on every platform marks nothing.
        if rng.random() < 0.4:
            out.append(self._node(gap=rng.choice((2, 2, 3)), rise=0,
                                  style="stone", form="wide", deco="posts",
                                  orbs=1))
        return out

    def _seg_staircase(self, rng) -> list[dict]:
        """A flight of stairs, climbing one block a step."""
        style = rng.choice(("stone", "quartz"))
        bend = rng.uniform(-0.13, 0.13)
        return [self._node(gap=1, rise=1, style=style, turn=bend, form="stair",
                           orbs=1 if i % 2 else 0)
                for i in range(rng.randint(5, 8))]

    def _seg_descent(self, rng) -> list[dict]:
        """The long fall. Pillars hang under the landings so the eye has
        something to measure the drop against on the way down."""
        out = []
        for i in range(rng.randint(3, 5)):
            drop = rng.randint(3, 5) if i == 0 else rng.randint(2, 4)
            out.append(self._node(gap=rng.choice((2, 2, 3)), rise=-drop,
                                  style="stone", deco="pillar", orbs=2))
        out.append(self._node(gap=2, rise=0, style="lantern", form="wide",
                              deco="lanterns", orbs=1))
        return out

    def _seg_zigzag(self, rng) -> list[dict]:
        """Tight alternating turns -- the camera work is the point."""
        swing = rng.uniform(0.5, 0.78)
        return [self._node(gap=rng.choice((1, 1, 2)), rise=rng.choice((0, 0, 1, -1)),
                           style=self.candy[i % 3],
                           turn=swing if i % 2 else -swing,
                           orbs=1 if rng.random() < 0.5 else 0)
                for i in range(rng.randint(6, 9))]

    def _seg_chasm(self, rng) -> list[dict]:
        """Lantern platform, the longest jump in the game, lantern platform.
        Orbs strung across the void mark the line.

        The gap is only a little wider than the gap table's own maximum, and
        deliberately so: a purely ballistic arc that lands where it aimed can
        answer a longer jump only by crossing the ground faster than a body
        runs or by arcing higher than a body jumps, and both look wrong. What
        makes this read as a chasm is the void under it and the two lit
        platforms either side, not another metre of distance.
        """
        gap = rng.uniform(4.2, 4.9)
        return [
            self._node(gap=2, rise=0, style="quartz", form="wide", deco="lanterns"),
            self._node(gap=gap, rise=rng.choice((0, 0, 1)), style="lantern", orbs=3),
            self._node(gap=2, rise=0, style="quartz", form="wide", deco="lanterns",
                       orbs=1),
        ]

    def _seg_causeway(self, rng) -> list[dict]:
        """A plank walkway with a fence: short hops, a straight line, and a
        completely different material. Contrast is what makes the rest read."""
        return [self._node(gap=1, rise=0, style="wood", form="slab",
                           turn=rng.uniform(-0.05, 0.05),
                           deco="rail" if i % 2 == 0 else None,
                           orbs=1 if i % 3 == 1 else 0)
                for i in range(rng.randint(6, 10))]

    def _seg_spiral(self, rng) -> list[dict]:
        """A staircase that winds, with a tower under it."""
        turn = rng.choice((0.52, -0.52))
        return [self._node(gap=rng.choice((1, 2)), rise=1 if i % 2 else 0,
                           style="brick", turn=turn,
                           deco="pillar" if i % 2 == 0 else None,
                           orbs=1 if i % 3 == 0 else 0)
                for i in range(rng.randint(6, 9))]

    def _seg_gate(self, rng) -> list[dict]:
        """Something to run *through* rather than only on."""
        return [
            self._node(gap=2, rise=0, style="quartz"),
            self._node(gap=rng.choice((2, 3)), rise=0, style="quartz",
                       deco="gate", orbs=1),
            self._node(gap=2, rise=rng.choice((0, 0, -1)), style="quartz"),
        ]

    def _seg_lanternwalk(self, rng) -> list[dict]:
        """Torchlit stepping stones -- the night runs live for this."""
        return [self._node(gap=rng.choice((1, 2)), rise=rng.choice((0, 0, 1, -1)),
                           style="lantern" if i % 2 else self.candy[i % 3],
                           deco="torch" if i % 2 == 0 else None,
                           orbs=1 if rng.random() < 0.6 else 0)
                for i in range(rng.randint(4, 7))]

    # -- generation: placement --------------------------------------------

    def _spawn_block(self, first: bool = False) -> None:
        if first:
            self.blocks.append({
                "x": 0.0, "y": COURSE_ALT, "z": 0.0, "ox": 0.0, "oz": 0.0,
                "style": "candy0", "form": "wide", "yaw": 0.0, "born": -1e9,
                "deco": [], "orbs": [], "segment": "start"})
            return
        if not self._pending:
            self._plan_segment()
        node = self._pending.pop(0)
        prev = self.blocks[-1]
        rng = self.rng

        rise = node["rise"]
        # The band is a hard guard, not a plan: segments are chosen to head the
        # right way, and this only catches the case where one still overshoots.
        if prev["y"] + rise < COURSE_ALT - BAND:
            rise = abs(rise)
        elif prev["y"] + rise > COURSE_ALT + BAND:
            rise = -abs(rise) or -1

        # Gaussian sideways drift, steered back toward the spine, unless the
        # segment asked for a specific turn. Candidate headings fan out from
        # there and the first that does not land on recent course wins -- the
        # reference generator likewise refuses self-overlapping placements.
        # A held direction bends the course; ``self.steer`` is zero on
        # autopilot, so this term does nothing until somebody is driving.
        hand = self.steer * STEER
        if node["turn"] is None:
            drift = rng.gauss(0.0, 0.55)
            # Back toward the spine -- but mostly out of the way while
            # someone is steering, or the two cancel and holding a direction
            # buys a couple of metres and then nothing.
            home = -0.028 * prev["x"] * (1.0 - 0.85 * abs(self.steer))
            preferred = max(-0.9, min(0.9,
                                      self.heading + drift * 0.22 + home + hand))
        else:
            preferred = max(-1.1, min(1.1, self.heading + node["turn"] + hand * 0.6))
        recent = self.blocks[-7:-1]
        step = node["gap"] + 1.0

        def landing(heading: float):
            return (prev["x"] + math.sin(heading) * step,
                    prev["z"] - math.cos(heading) * step)

        best, best_clearance = preferred, -1.0
        for fan in (0.0, 0.2, -0.2, 0.45, -0.45, 0.7, -0.7):
            heading = max(-1.1, min(1.1, preferred + fan))
            nx, nz = landing(heading)
            clearance = min((math.dist((nx, nz), (b["x"], b["z"])) for b in recent),
                            default=99.0)
            if clearance > 1.45:
                best = heading
                break
            if clearance > best_clearance:
                best, best_clearance = heading, clearance
        self.heading = best
        dx = math.sin(best) * step
        dz = -math.cos(best) * step

        form = node["form"]
        margin = MARGIN.get(form, 0.24)
        # Where the player will stand, decided now: the arc of the hop that
        # arrives here is a fact about the course from this moment on.
        ox, oz = rng.uniform(-margin, margin), rng.uniform(-margin, margin)

        # What makes a hop is the distance between the two *stand points*, not
        # between the two block centres. A landing that wandered to the near
        # edge of a three-wide platform can otherwise leave under a metre to
        # the next block, which reads as a shuffle rather than a jump -- so the
        # step is pushed out until there is a real jump to make.
        frm = self._stand_point(prev)
        for _ in range(6):
            short = MIN_HOP - math.dist((frm[0], frm[2]),
                                        (prev["x"] + dx + ox, prev["z"] + dz + oz))
            if short <= 0.0:
                break
            step += short + 0.05
            dx, dz = math.sin(best) * step, -math.cos(best) * step

        blk = {
            "x": prev["x"] + dx,
            "y": prev["y"] + rise,
            "z": prev["z"] + dz,
            "ox": ox,
            "oz": oz,
            "born": self.elapsed,
            "style": node["style"],
            "form": form,
            "yaw": best,
            "deco": [],
            "orbs": [],
            "segment": self.segment,
        }
        if node["deco"]:
            blk["deco"] = self._deco_cubes(node["deco"], blk, rng)
        self.blocks.append(blk)
        if node["orbs"]:
            self._hang_orbs(prev, blk, node["orbs"])

    def _deco_cubes(self, kind: str, blk: dict, rng) -> list[dict]:
        """Expand a decoration into boxes, in the block's own frame.

        Offsets are rotated into the course's heading, so a gate faces the way
        you are running through it rather than the way the world happens to be
        pointing.
        """
        yaw = blk["yaw"]
        sin, cos = math.sin(yaw), math.cos(yaw)

        def local(side: float, fwd: float, dy: float, sx: float, sy: float,
                  sz: float, style: str, glow: bool = False,
                  loose: bool = False, born: float = -1e9) -> dict:
            return {"dx": side * cos + fwd * sin, "dz": -side * sin + fwd * cos,
                    "dy": dy, "sx": sx, "sy": sy, "sz": sz,
                    "style": style, "glow": glow, "loose": loose, "born": born}

        if kind == "pillar":
            depth = rng.randint(3, 6)
            return [local(0, 0, -1.0 - i, 0.86, 1.0, 0.86, blk["style"])
                    for i in range(depth)]
        if kind in ("lanterns", "posts"):
            lit = kind == "lanterns"
            out = []
            for sx in (-1.3, 1.3):
                for sz in (-1.3, 1.3):
                    out.append(local(sx, sz, 1.0, 0.22, 1.0, 0.22, "wood"))
                    if lit:
                        out.append(local(sx, sz, 1.7, 0.34, 0.34, 0.34,
                                         "lantern", glow=True))
                    else:
                        # a fence cap, not a grey knob: a stone cube on a wood
                        # post reads as a mushroom from every angle
                        out.append(local(sx, sz, 1.62, 0.4, 0.16, 0.4, "wood"))
            return out
        if kind == "torch":
            side = rng.choice((-0.42, 0.42))
            return [local(side, 0.0, 1.0, 0.14, 0.7, 0.14, "wood"),
                    local(side, 0.0, 1.5, 0.2, 0.2, 0.2, "lantern", glow=True)]
        if kind == "rail":
            return [local(side, 0.0, 0.5, 0.16, 0.62, 0.16, "wood")
                    for side in (-0.42, 0.42)]
        if kind == "gate":
            # Light jambs, a dark lintel, a lantern hung in the opening. Built
            # the other way round -- dark posts under a pale beam -- it read as
            # a wall with a hole rather than as a doorway.
            out = []
            for side in (-1.6, 1.6):
                for i in range(3):
                    out.append(local(side, 0.0, 1.0 + i, 0.86, 1.0, 0.86, "quartz"))
            for side in (-1.6, -0.8, 0.0, 0.8, 1.6):
                out.append(local(side, 0.0, 4.0, 0.9, 0.7, 0.9, "stone"))
            out.append(local(0.0, 0.0, 3.1, 0.34, 0.34, 0.34, "lantern", glow=True))
            return out
        if kind == "crumb":
            # A loose block beside the path, there to be broken as you land.
            side = rng.choice((-1.0, 1.0)) * rng.uniform(1.0, 1.4)
            return [local(side, rng.uniform(-0.4, 0.4), rng.uniform(0.0, 0.8),
                          0.8, 0.8, 0.8, rng.choice(self.candy), loose=True)]
        return []

    def _hang_orbs(self, prev: dict, blk: dict, count: int) -> None:
        """Put pickups on the flight path from ``prev`` to ``blk``.

        Not near it: on it. The takeoff and landing points are both already
        decided, so the arc is known exactly, and an orb placed at the chest
        height of the body that will fly through cannot be missed. That makes
        "every orb laid down is collected" a property of generation rather
        than a hope, which is what the test asserts.
        """
        frm = self._stand_point(prev)
        to = self._stand_point(blk)
        dur, vy0 = flight(frm, to)
        fractions = {1: (0.5,), 2: (0.36, 0.68), 3: (0.28, 0.5, 0.72)}[count]
        for f in fractions:
            t = dur * f
            blk["orbs"].append({
                "x": frm[0] + (to[0] - frm[0]) * f,
                "y": frm[1] + vy0 * t - 0.5 * GRAVITY * t * t + CHEST,
                "z": frm[2] + (to[2] - frm[2]) * f,
                "taken": False,
            })

    # -- course geometry ---------------------------------------------------

    def surface(self, blk: dict) -> float:
        """Height of the walking surface on a block."""
        return blk["y"] + FORMS[blk["form"]]

    def _stand_point(self, blk: dict) -> tuple[float, float, float]:
        """Exactly where the player stands on a block. Decided at generation,
        so nothing downstream has to guess."""
        return (blk["x"] + blk["ox"], self.surface(blk), blk["z"] + blk["oz"])

    def body_box(self) -> AABB:
        """The player's volume right now, feet at :attr:`pos`."""
        return AABB.around(self.pos[0], self.pos[1], self.pos[2],
                           BODY_HALF_W, BODY_H, BODY_HALF_W)

    def orb_box(self, orb: dict) -> AABB:
        """An orb's hitbox, from the model that draws it and the transform it
        is drawn with -- the same rule the runner's obstacles follow. Change
        :data:`ORB_SCALE` and the box moves with the picture."""
        return placed(model_aabb(self._model("orb")),
                      (orb["x"], orb["y"], orb["z"]),
                      scale=(ORB_SCALE, ORB_SCALE, ORB_SCALE))

    # -- the world below ---------------------------------------------------

    def _spawn_island(self) -> None:
        """A wooded island: mound, shore, trees, and sometimes a ruin or a
        waterfall. All of it is cheap -- the fog eats most of it -- and all of
        it is what stops the ocean reading as an empty blue floor."""
        rng = self.irng
        z = self._next_island_z - rng.uniform(42, 95)
        self._next_island_z = z
        cx = rng.gauss(0.0, 24.0)      # hug the spine: vertigo needs land under
        base = rng.uniform(7, 12)
        cubes: list[dict] = []

        # biome tint, applied at draw time rather than as another texture
        biome = rng.choice((
            (1.00, 1.00, 1.00),        # temperate
            (1.10, 0.96, 0.72),        # arid
            (0.82, 0.98, 1.08),        # cold
            (0.88, 1.06, 0.86),        # jungle
        ))

        top = 0.0
        for i in range(rng.randint(3, 6)):
            s = rng.uniform(0.5, 1.0) * base * (1.0 - i * 0.12)
            y = rng.uniform(0.5, 2.5) + i * rng.uniform(0.8, 1.8)
            cubes.append({"dx": rng.uniform(-base * 0.9, base * 0.9),
                          "dz": rng.uniform(-base * 0.9, base * 0.9),
                          "y": y, "s": s, "style": "grass"})
            top = max(top, y + s / 2)
        # a sand shelf just clear of the water
        for _ in range(int(3 * self.detail) + 1):
            s = rng.uniform(2.5, 5.0)
            cubes.append({"dx": rng.uniform(-base, base), "dz": rng.uniform(-base, base),
                          "y": rng.uniform(0.4, 1.2), "s": s, "style": "sand"})

        for _ in range(int(rng.randint(2, 4) * self.detail) + 1):
            tx, tz = rng.uniform(-base * 0.7, base * 0.7), rng.uniform(-base * 0.7, base * 0.7)
            trunk = rng.uniform(3.0, 5.5)
            foot = rng.uniform(1.5, 3.5)
            cubes.append({"dx": tx, "dz": tz, "y": foot + trunk / 2,
                          "sx": 0.9, "sy": trunk, "sz": 0.9, "style": "wood"})
            crown = rng.uniform(3.0, 4.6)
            for k in range(2):
                cubes.append({"dx": tx, "dz": tz, "y": foot + trunk + k * crown * 0.42,
                              "sx": crown * (1.0 - k * 0.3), "sy": crown * 0.55,
                              "sz": crown * (1.0 - k * 0.3), "style": "leaf"})

        if rng.random() < 0.35:        # a ruined tower
            rx, rz = rng.uniform(-base * 0.5, base * 0.5), rng.uniform(-base * 0.5, base * 0.5)
            for k in range(rng.randint(3, 6)):
                cubes.append({"dx": rx, "dz": rz, "y": top + k * 1.6, "s": 1.9,
                              "style": "stone"})
        waterfall = None
        if rng.random() < 0.3:
            wx, wz = rng.uniform(-base, base), rng.uniform(-base, base)
            waterfall = {"dx": wx, "dz": wz, "h": top}

        self.islands.append({"x": cx, "z": z, "cubes": cubes, "biome": biome,
                             "reef": base * 2.6, "waterfall": waterfall})

    # -- simulation -------------------------------------------------------

    def _begin_air(self) -> None:
        target = self.blocks[self.jump_index + 1]
        self.takeoff = list(self.stand)
        self.land_at = list(self._stand_point(target))
        self.air_dur, self.vy0 = flight(self.takeoff, self.land_at)
        self.phase = "air"
        self.phase_t = 0.0
        # Leaving the block is when the hand does something other than bob.
        if self.hop_rng.random() < 0.35:
            self.mine = 1.0

    def _land(self) -> None:
        self.jump_index += 1
        self.stand = list(self.land_at)
        self.pos = list(self.stand)
        self.phase = "ground"
        self.phase_t = 0.0
        self.land_dip = 1.0
        self.swing = 1.0
        self.hops += 1
        landed_on = self.blocks[self.jump_index]
        # a scuff of block-coloured dust at the feet, kicked up by the landing
        self.burst.spawn(self.stand[0], self.stand[1] - 0.1, self.stand[2],
                         self._colour(landed_on["style"]),
                         count=7, speed=1.6, rng=self.hop_rng)
        self.distance += math.dist((self.takeoff[0], self.takeoff[2]),
                                   (self.stand[0], self.stand[2]))

        # Breaking the loose block beside the landing: the single most
        # Minecraft thing a first-person shot can do that is not the hand.
        crumbs = [d for d in landed_on["deco"] if d["loose"]]
        if crumbs:
            crumb = crumbs[0]
            landed_on["deco"].remove(crumb)
            self.burst.spawn(landed_on["x"] + crumb["dx"],
                             landed_on["y"] + crumb["dy"] + 0.4,
                             landed_on["z"] + crumb["dz"],
                             self._colour(crumb["style"]), count=12, speed=2.4,
                             rng=self.hop_rng)
            self.mine = 1.0

        # a proper breather on checkpoint platforms, a beat everywhere else
        wide = landed_on["form"] == "wide"
        self.ground_dur = (self.hop_rng.uniform(0.5, 0.9) if wide
                           else self.hop_rng.uniform(0.10, 0.26))
        # A breather is long enough to do something with your hands. Carrying a
        # block, you put one down -- and it is still there behind you, because
        # a placement that leaves nothing behind is an animation, not an act.
        if wide and self.hop_rng.random() < 0.7:
            if self.kit["name"] == "block":
                self.place = 1.0
                yaw = landed_on["yaw"]
                side = self.hop_rng.choice((-1.3, 1.3))
                fwd = self.hop_rng.uniform(-1.0, 1.0)
                landed_on["deco"].append({
                    "dx": side * math.cos(yaw) + fwd * math.sin(yaw),
                    "dz": -side * math.sin(yaw) + fwd * math.cos(yaw),
                    "dy": 1.0, "sx": 1.0, "sy": 1.0, "sz": 1.0,
                    "style": self.kit["parts"][0]["style"],
                    "glow": False, "loose": False,
                    # dated forward: it arrives as the hand reaches out
                    "born": self.elapsed + 0.18})
            else:
                self.mine = 1.0

        # A steer is answered once per landing rather than once per frame:
        # sixty rebuilds a second would be a course that never settles, and
        # every block would spend its whole life arriving.
        if self.driven and self.steer:
            self._steer_course()

        # keep the horizon of generated course ahead of the player
        while len(self.blocks) - self.jump_index < AHEAD:
            self._spawn_block()
        if self.jump_index > TRAIL:
            drop = self.jump_index - TRAIL
            for blk in self.blocks[:drop]:
                self.orbs_missed += sum(1 for o in blk["orbs"] if not o["taken"])
            self.blocks = self.blocks[drop:]
            self.jump_index -= drop
        z_here = self.stand[2]
        if self.islands and self.islands[0]["z"] > z_here + 90:
            self.islands.pop(0)
        while self._next_island_z > z_here - 260:
            self._spawn_island()

    # -- being driven -----------------------------------------------------

    playable = True

    def control(self, intent) -> None:
        """Steer by hand for one frame.

        There is no free movement to give a player here: the body is a
        sequence of solved ballistic arcs between blocks that do not exist
        yet, and letting someone walk off one would mean inventing a fall, a
        death and a restart for a thing that runs behind a terminal. What
        there *is* to give is the two decisions the autopilot makes -- which
        way the course goes, and when to leave the block.

        So left and right bend the course, taking effect on the next landing
        (see :meth:`_land`); up jumps off the block early instead of waiting
        for the beat; down holds it. Everything the scene guarantees on
        autopilot still holds, because a steered course is generated by the
        same generator and an early take-off changes the timing of an arc, not
        its endpoints -- the orbs on it are still exactly where the body goes.
        """
        self.steer = (1.0 if intent.right else 0.0) - (1.0 if intent.left else 0.0)
        self.driven_t = DRIVEN_HOLD
        if self.phase != "ground":
            return
        if intent.jump:
            self.ground_dur = min(self.ground_dur, self.phase_t)
        elif intent.duck:
            self.ground_dur = min(self.ground_dur + 0.05, HOLD_MAX)

    @property
    def driven(self) -> bool:
        return self.driven_t > 0.0

    def _steer_course(self) -> None:
        """Re-lay the course beyond the next hop, bent the way it is asked.

        Only the tail is thrown away: the block being landed on and the one
        after it are already committed, and rebuilding those would move the
        ground out from under a jump in progress. Two blocks of commitment is
        about a second, which is the difference between "press left and it
        turns left" and "press left and it eventually turns left".
        """
        keep = self.jump_index + STEER_KEEP
        if len(self.blocks) <= keep + 1:
            return
        del self.blocks[keep + 1:]
        self._pending.clear()
        self.heading = self.blocks[-1]["yaw"]
        while len(self.blocks) - self.jump_index < AHEAD:
            self._spawn_block()

    def _collect(self) -> None:
        """Take any orb the body is inside. Only the hop in progress and its
        neighbours can possibly be in reach, so this stays a handful of box
        tests however long the run gets."""
        # Reach, not contact. An orb is placed exactly where the eye is going,
        # so waiting for the body to touch it means watching it fill the frame
        # for two frames on its way past the lens. An arm's length of reach
        # takes it while it is still an object in the world.
        body = self.body_box().grown(PICKUP_REACH, PICKUP_REACH, PICKUP_REACH)
        lo = max(0, self.jump_index - 1)
        for blk in self.blocks[lo:self.jump_index + 3]:
            for orb in blk["orbs"]:
                if orb["taken"] or not body.overlaps(self.orb_box(orb)):
                    continue
                orb["taken"] = True
                self.orbs += 1
                self.combo += 1
                self.best_combo = max(self.best_combo, self.combo)
                self.combo_t = COMBO_HOLD
                self.burst.spawn(orb["x"], orb["y"], orb["z"], ORB_COLOR,
                                 count=9, speed=2.2, rng=self.hop_rng)

    def update(self, dt: float) -> None:
        self.phase_t += dt
        if self.phase == "ground":
            self.pos = list(self.stand)
            self.vy = 0.0
            if self.phase_t >= self.ground_dur:
                self._begin_air()
        else:
            t = min(self.phase_t, self.air_dur)
            f = t / self.air_dur
            self.pos[0] = self.takeoff[0] + (self.land_at[0] - self.takeoff[0]) * f
            self.pos[2] = self.takeoff[2] + (self.land_at[2] - self.takeoff[2]) * f
            self.pos[1] = self.takeoff[1] + self.vy0 * t - 0.5 * GRAVITY * t * t
            self.vy = self.vy0 - GRAVITY * t
            if self.phase_t >= self.air_dur:
                self._land()

        self._collect()
        self._look()
        self.driven_t = max(0.0, self.driven_t - dt)
        if not self.driven:
            self.steer = 0.0
        self.land_dip = max(0.0, self.land_dip - dt * 5.0)
        self.swing = max(0.0, self.swing - dt * 2.6)
        self.mine = max(0.0, self.mine - dt * 2.2)
        self.place = max(0.0, self.place - dt * 1.6)
        if self.combo_t > 0.0:
            self.combo_t -= dt
            if self.combo_t <= 0.0:
                self.combo = 0
        self.burst.update(dt)

    # -- drawing ----------------------------------------------------------

    def _fog(self, dist: float, extra: float = 0.0, alpha: int = 255,
             tint: tuple[float, float, float] | None = None):
        f = max(0.0, min(1.0, dist / FOG_FAR + extra))
        f = f * f * (3 - 2 * f)
        c = rl.mix_rgb((255, 255, 255), self.palette.fog, f)
        if tint is not None:
            c = (max(0, min(255, int(c[0] * tint[0]))),
                 max(0, min(255, int(c[1] * tint[1]))),
                 max(0, min(255, int(c[2] * tint[2]))))
        return rl.rgba(c, alpha)


    def draw(self) -> None:
        pal = self.palette
        self.sky.draw(self.elapsed)

        x, y, z = self.pos
        self._aim_camera(x, y, z)
        cam = self.camera

        rl.BeginMode3D(cam[0])
        self._draw_ocean(x, z)
        self._draw_islands(x, z)
        self._draw_shelves(x, z)
        rl.EndMode3D()

        # Aerial perspective over the world below only: leave 3D, lay a smooth
        # alpha fade from the horizon down, then re-enter the same camera for
        # the course. The haze writes no depth, so the course draws over it
        # while still depth-testing correctly against the islands.
        # Starts above the true horizon and fades in, because the eye finds a
        # hard edge in a clear sky instantly -- and the previous band drew one
        # right where the sea was supposed to dissolve.
        # Not too strong. Dawn and dusk fog is a saturated gold or pink, and at
        # the alpha this used to carry it stopped being aerial perspective and
        # became an orange wash laid over the middle of the frame.
        band = textures.alpha_band(f"haze-{self.ctx.seed.run}", pal.fog, 155, 1.6,
                                   ramp=0.22)
        horizon = int(self.height * 0.30)
        rl.DrawTexturePro(band, (0, 0, 4, 128),
                          (0, horizon, self.width, int(self.height * 0.46)),
                          (0, 0), 0.0, rl.WHITE4)
        rl.BeginMode3D(cam[0])

        self._draw_course(x, z)
        self._draw_orbs(x, z)
        self.burst.draw(self.camera)
        self._draw_held()
        rl.EndMode3D()

        self.weather.draw(self.elapsed)
        self._draw_crosshair()
        self._draw_hud()

    def _look(self) -> None:
        """Ease the head toward where the run is going.

        Lives in ``update`` rather than in ``draw`` so that drawing a frame
        twice draws the same frame twice. It did not, and the difference is
        not academic: every screenshot this scene is judged from is captured
        by presenting a frame a second time.
        """
        x, z = self.pos[0], self.pos[2]
        # Aim: mid-air, at where we will land; on the ground, pre-aim toward
        # the NEXT landing so the turn happens as a deliberate look, not a
        # camera glued to a moving block.
        if self.phase == "air":
            aim = self.land_at
            ease = 0.14
        else:
            # aim through the course, not at one block: averaging the next
            # few keeps more of the run in frame through bends
            idx = self.jump_index
            ahead = self.blocks[min(idx + 1, len(self.blocks) - 1):
                                min(idx + 4, len(self.blocks))]
            aim = (sum(b["x"] for b in ahead) / len(ahead),
                   sum(self.surface(b) for b in ahead) / len(ahead),
                   sum(b["z"] for b in ahead) / len(ahead))
            ease = 0.06
        target_yaw = math.atan2(aim[0] - x, -(aim[2] - z))
        dy = target_yaw - self.yaw
        while dy > math.pi:
            dy -= 2 * math.pi
        while dy < -math.pi:
            dy += 2 * math.pi
        self.yaw += dy * ease
        # a touch of roll into the turn sells the head motion
        self._roll += (max(-0.05, min(0.05, dy * 0.35)) - self._roll) * 0.1

    def _aim_camera(self, x: float, y: float, z: float) -> None:
        # landing dip with a small overshoot, plus an idle breath on ground
        dip = self.land_dip ** 1.4 * 0.17 - math.sin(self.land_dip * math.pi) * 0.02
        breathe = math.sin(self.elapsed * 2.1) * 0.012 if self.phase == "ground" else 0.0

        cam = self.camera
        eye_y = y + EYE - dip + breathe
        cam.position = (x, eye_y, z)
        look = 5.5
        # pitch follows vertical velocity: rising lifts the gaze, falling
        # drops it toward the landing block. Base pitch keeps the horizon
        # near mid-frame like the reference footage.
        pitch_drop = 1.1 - max(-0.6, min(0.85, self.vy * 0.1))
        cam.target = (x + math.sin(self.yaw) * look,
                      eye_y - pitch_drop,
                      z - math.cos(self.yaw) * look)
        # roll: tilt the up vector about the view direction
        fx, fz = math.sin(self.yaw), -math.cos(self.yaw)
        cam.up = (math.sin(self._roll) * -fz, math.cos(self._roll), math.sin(self._roll) * fx)
        cam.fovy = 70.0 + (2.5 if self.phase == "air" else 0.0)

    def _draw_ocean(self, x: float, z: float) -> None:
        pal = self.palette
        # A sea, not a blue floor: the deep is keyed to the sky so night runs
        # get a black ocean, and every island sits on its own pale reef, which
        # is most of what stops the water reading as a painted plane.
        deep = rl.mix_rgb(rl.mix_rgb(pal.sky_bottom, (10, 46, 96), 0.78),
                          pal.fog, 0.10)
        # Big enough that its far edge is over the horizon rather than short of
        # it: a 760 m sea seen from 58 m up runs out three hundred metres
        # before the horizon does, and the strip of bare sky underneath it read
        # as a pale band lying on the water.
        rl.DrawPlane((x, 0.0, z - 900), (4000, 4000), rl.rgba(deep, 255))
        # Submit it before anything else draws. A batched plane is otherwise
        # rendered after every model in the frame and loses the depth test to
        # all of them -- which is where the sea grew holes in the shape of the
        # cloud shelves floating above it.
        rl.flush()
        # Each island sits on its own pale shallow. Drawn as the soft-edged
        # disc the blob shadows use rather than as a quad: a hard-edged
        # rectangle of lighter blue on the sea reads as a mistake, and the
        # only thing separating the two is which texture is on the quad.
        shallow = rl.mix_rgb(deep, (120, 226, 226), 0.62)
        for isl in self.islands:
            dist = math.dist((x, z), (isl["x"], isl["z"]))
            if dist > 260:
                continue
            reef = rl.mix_rgb(shallow, pal.fog, min(1.0, dist / 300))
            rl.DrawModelEx(ground_quad(), (isl["x"], 0.06, isl["z"]), (0, 1, 0), 0.0,
                           (isl["reef"], 1.0, isl["reef"]), rl.rgba(reef, 235))

    def _draw_islands(self, x: float, z: float) -> None:
        for isl in self.islands:
            biome = isl["biome"]
            for c in isl["cubes"]:
                bx, bz = isl["x"] + c["dx"], isl["z"] + c["dz"]
                dist = math.dist((x, z), (bx, bz))
                if dist > 300:
                    continue
                tint = self._fog(dist * 0.62, BELOW_FOG * 0.4, tint=biome)
                s = c.get("s")
                if s is not None:
                    voxel.draw_block(self._model(c["style"]), bx, c["y"], bz, tint, s)
                else:
                    voxel.draw_box(self._model(c["style"]), bx, c["y"], bz, tint,
                                   c["sx"], c["sy"], c["sz"])
            fall = isl["waterfall"]
            if fall is not None:
                bx, bz = isl["x"] + fall["dx"], isl["z"] + fall["dz"]
                dist = math.dist((x, z), (bx, bz))
                if dist <= 300:
                    voxel.draw_box(self._model("water"), bx, fall["h"] / 2, bz,
                                   self._fog(dist * 0.62, BELOW_FOG * 0.3),
                                   1.4, fall["h"], 1.4)

    def _draw_shelves(self, x: float, z: float) -> None:
        """Cloud shelves drifting between the course and the sea.

        They are flat quads, and seen from above a flat quad is exactly what
        they look like unless they fade -- so they take the same distance fog
        as everything else down there. Without it a shelf reads as a pane of
        glass lying on the water.
        """
        shelf = unit_quad("cloud-shelf")
        for s in self.shelves:
            sx = s["x"] + math.sin(self.elapsed * 0.05 * s["drift"]) * 6
            if s["z"] > z + 60:
                s["z"] -= 300
                continue
            dist = math.dist((x, z), (sx, s["z"]))
            fade = max(0.0, min(1.0, dist / 200.0))
            shelf.materials[0].maps[rl.MATERIAL_MAP_ALBEDO].texture = s["tex"]
            tint = rl.rgba(rl.mix_rgb(self.cloud_tint, self.palette.fog, fade),
                           int(64 - 30 * fade))
            # Two sheets a little apart, the upper one smaller: from directly
            # above a single quad is unmistakably a single quad, and the second
            # layer is what gives it a top and a shoulder.
            for k, (lift, shrink) in enumerate(((0.0, 1.0), (3.5, 0.66))):
                # the cloud texture is 2:1, so the quad is squashed to match
                rl.DrawModelEx(shelf, (sx, s["y"] + lift, s["z"]), (0, 1, 0),
                               s["yaw"] + k * 37.0,
                               (s["s"] * shrink, 1.0, s["s"] * shrink * 0.5), tint)

    def _arrival(self, born: float) -> tuple[float, int]:
        """How far into its arrival a block is: a vertical offset and an alpha.

        Blocks in the reference footage do not simply exist at the generation
        horizon, they *appear* there -- which is the single clearest signal
        that the course is being built for you rather than run through. They
        rise the last half block into place as they fade in.
        """
        p = (self.elapsed - born) / POP_IN
        if p >= 1.0:
            return 0.0, 255
        p = max(0.0, p)
        return -(1.0 - p) * 0.45, int(40 + 215 * p)

    def _draw_course(self, x: float, z: float) -> None:
        for blk in self.blocks:
            dist = math.dist((x, z), (blk["x"], blk["z"]))
            model = self._model(blk["style"])
            lift, alpha = self._arrival(blk["born"])
            tint = self._fog(dist, alpha=alpha)
            form = blk["form"]
            bx, by, bz = blk["x"], blk["y"] + lift, blk["z"]
            if form == "wide":
                for ox in (-1, 0, 1):
                    for oz in (-1, 0, 1):
                        voxel.draw_block(model, bx + ox, by + 0.5, bz + oz, tint)
            elif form == "slab":
                voxel.draw_box(model, bx, by + 0.25, bz, tint, 1.0, 0.5, 1.0)
            else:
                voxel.draw_block(model, bx, by + 0.5, bz, tint)
                if form == "stair":
                    # the tread, set back toward where you came from
                    yaw = blk["yaw"]
                    voxel.draw_box(model, bx - math.sin(yaw), by + 0.25,
                                   bz + math.cos(yaw), tint, 1.0, 0.5, 1.0)
            for d in blk["deco"]:
                dx, dz = bx + d["dx"], bz + d["dz"]
                dd = math.dist((x, z), (dx, dz))
                d_lift, d_alpha = self._arrival(max(blk["born"], d["born"]))
                dy = by + d_lift - lift + d["dy"] + d["sy"] / 2
                voxel.draw_box(self._model(d["style"]), dx, dy, dz,
                               self._fog(dd, alpha=d_alpha),
                               d["sx"], d["sy"], d["sz"])
                if d["glow"] and dd < 44:
                    glow_billboard(self.camera, dx, dy, dz, 1.5, LANTERN_GLOW,
                                   90 if self.palette.is_dark else 45)

    def _draw_orbs(self, x: float, z: float) -> None:
        model = self._model("orb")
        spin = (self.elapsed * 150.0) % 360.0
        hover = math.sin(self.elapsed * 3.4) * 0.08
        for blk in self.blocks:
            for orb in blk["orbs"]:
                if orb["taken"]:
                    continue
                dist = math.dist((x, z), (orb["x"], orb["z"]))
                if dist > FOG_FAR:
                    continue
                voxel.draw_box(model, orb["x"], orb["y"] + hover, orb["z"],
                               self._fog(dist), ORB_SCALE, ORB_SCALE, ORB_SCALE,
                               yaw=spin)
                glow_billboard(self.camera, orb["x"], orb["y"] + hover, orb["z"],
                               0.85, ORB_COLOR, 110)

    # -- first person -----------------------------------------------------

    def _camera_basis(self):
        """Right / up / forward of the current view, orthonormal."""
        cam = self.camera
        px, py, pz = cam.position.x, cam.position.y, cam.position.z
        fx, fy, fz = cam.target.x - px, cam.target.y - py, cam.target.z - pz
        fl = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
        fx, fy, fz = fx / fl, fy / fl, fz / fl
        ux, uy, uz = cam.up.x, cam.up.y, cam.up.z
        rx, ry, rz = fy * uz - fz * uy, fz * ux - fx * uz, fx * uy - fy * ux
        rl_ = math.sqrt(rx * rx + ry * ry + rz * rz) or 1.0
        rx, ry, rz = rx / rl_, ry / rl_, rz / rl_
        # re-derive up so the three are exactly orthogonal even with roll on
        ux, uy, uz = ry * fz - rz * fy, rz * fx - rx * fz, rx * fy - ry * fx
        return (rx, ry, rz), (ux, uy, uz), (fx, fy, fz)

    def _view_matrix(self, right, up, forward):
        """A rotation that puts model +X along ``right``, +Y up, +Z back.

        Built by hand rather than composed from yaw and pitch: the camera also
        rolls into its turns, and a model oriented from Euler angles ignores
        that and shears away from the frame it is supposed to be pinned to.
        """
        m = rl.ffi.new("Matrix *")
        m.m0, m.m1, m.m2, m.m3 = right[0], right[1], right[2], 0.0
        m.m4, m.m5, m.m6, m.m7 = up[0], up[1], up[2], 0.0
        m.m8, m.m9, m.m10, m.m11 = -forward[0], -forward[1], -forward[2], 0.0
        m.m12, m.m13, m.m14, m.m15 = 0.0, 0.0, 0.0, 1.0
        return m[0]

    def _draw_held(self) -> None:
        """Whatever is in your hand, bobbing in the corner of the frame.

        Positioned from the camera basis rather than in screen space, so it
        picks up the same perspective as the world and swings with the head.
        Drawn last and very close in, which puts it in front of everything
        without needing its own pass.

        Three things move it: the walk bob, a landing punch, and a deliberate
        swing -- of the item, downward and back, the way you swing a tool.
        A hand that only ever bobs is a hand you stop seeing.
        """
        cam = self.camera
        right, up, forward = self._camera_basis()
        px, py, pz = cam.position.x, cam.position.y, cam.position.z

        # Size everything against the actual frustum at the distance it is
        # drawn, so the hand keeps its share of the frame whatever the field
        # of view does -- and this view widens by 2.5 degrees in mid-air.
        near = 0.5
        half_h = near * math.tan(math.radians(cam.fovy * 0.5))
        half_w = half_h * (self.width / self.height)

        t = self.elapsed
        bob_x = math.sin(t * 4.6) * 0.05
        bob_y = abs(math.cos(t * 4.6)) * 0.05
        punch = self.swing ** 1.5
        # the swing: over the top and down, then back to rest
        arc = math.sin(self.mine * math.pi) if self.mine > 0 else 0.0
        thrust = math.sin(self.place * math.pi) if self.place > 0 else 0.0

        def place(model, u, v, off_f, size, yaw, tilt):
            """u, v are fractions of the half-frame: (1, -1) is bottom-right."""
            off_r, off_u = u * half_w, v * half_h
            x = px + forward[0] * (near + off_f) + right[0] * off_r + up[0] * off_u
            y = py + forward[1] * (near + off_f) + right[1] * off_r + up[1] * off_u
            z = pz + forward[2] * (near + off_f) + right[2] * off_r + up[2] * off_u
            basis = self._view_matrix(right, up, forward)
            spin = rl.MatrixMultiply(rl.MatrixRotateX(math.radians(tilt)),
                                     rl.MatrixRotateY(math.radians(yaw)))
            model.transform = rl.MatrixMultiply(spin, basis)
            rl.DrawModelEx(model, (x, y, z), (0, 1, 0), 0.0,
                           (size[0] * half_w, size[1] * half_w, size[2] * half_w),
                           rl.WHITE4)
            # Put it back. The kit is built from the same shared block models
            # the course is, and a transform left on one is a transform every
            # plank walkway and stone staircase in the world inherits on the
            # next frame -- which is where the tilted slabs floating over the
            # sea were coming from.
            model.transform = rl.MatrixIdentity()

        # Forearm out of the bottom-right corner, hand, then whatever it is
        # carrying -- turned so two faces are visible, which is what makes a
        # cube read as a cube rather than a coloured square.
        # Sat well into the corner with part of it past the frame edge, the
        # way a held item actually sits -- fully inside the frame it stops
        # being scenery you look past and becomes an object you look at.
        drop = -1.06 - bob_y * 0.6 - punch * 0.34 + arc * 0.30
        lift = arc * 34.0 + thrust * -18.0
        forward_push = thrust * 0.16
        place(self.sleeve, 1.08 + bob_x * 0.3, drop - 0.66, 0.02 + forward_push,
              (0.34, 1.30, 0.34), yaw=-26.0, tilt=-24.0 + punch * 10.0 + lift * 0.6)
        place(self.skin, 0.94 + bob_x * 0.4, drop - 0.10, 0.01 + forward_push,
              (0.34, 0.34, 0.34), yaw=-26.0, tilt=-24.0 + punch * 10.0 + lift * 0.6)
        # Part offsets are quoted in the same units as part sizes -- fractions
        # of the half-frame WIDTH -- so an item's geometry is isotropic. The
        # frame is a tall strip, so quoting the vertical offset against the
        # half-height instead (as the arm does) stretches every item apart:
        # a lantern's handle ends up floating a foot above its lantern.
        vw = half_w / half_h
        for part in self.kit["parts"]:
            place(self._model(part["style"]),
                  0.82 + bob_x * 0.5 + part["u"], drop + 0.24 + part["v"] * vw,
                  0.05 + part["f"] + forward_push, part["size"],
                  yaw=-32.0 + part["yaw"],
                  tilt=-16.0 + punch * 14.0 + lift + part["tilt"])
        if self.kit["glow"]:
            # a torch or lantern actually lights the corner it sits in
            gx = px + forward[0] * 0.6 + right[0] * half_w * 0.8 - up[0] * half_h * 0.9
            gy = py + forward[1] * 0.6 + right[1] * half_w * 0.8 - up[1] * half_h * 0.9
            gz = pz + forward[2] * 0.6 + right[2] * half_w * 0.8 - up[2] * half_h * 0.9
            glow_billboard(self.camera, gx, gy, gz, 0.42, LANTERN_GLOW,
                           150 if self.palette.is_dark else 70)

    def _draw_crosshair(self) -> None:
        """Centre-screen, dark-edged so it survives a bright sky.

        Minecraft's own crosshair inverts whatever is behind it. There is no
        blend mode here that does that, and plain white vanishes against the
        sun -- so it gets a dark outline and a light core, which reads on
        anything.
        """
        cx, cy = self.width // 2, self.height // 2
        arm = 8
        for pad, color in ((1, (20, 20, 24, 150)), (0, (238, 238, 242, 225))):
            t = 2 + pad * 2
            rl.DrawRectangle(cx - arm - pad, cy - t // 2, (arm + pad) * 2, t, color)
            rl.DrawRectangle(cx - t // 2, cy - arm - pad, t, (arm + pad) * 2, color)

    def _draw_hud(self) -> None:
        pal = self.palette
        text(f"{int(self.distance)}m", self.width - 12, 10, 20, pal.ink,
             anchor="topright")
        # the orb tally, with a chip of the thing being collected
        rl.DrawRectangle(self.width - 62, 40, 10, 10, rl.rgba(ORB_COLOR, 255))
        rl.DrawRectangle(self.width - 60, 42, 6, 6, (255, 255, 255, 210))
        text(f"{self.orbs}", self.width - 12, 36, 18, ORB_COLOR, anchor="topright")
        if self.combo >= 3 and self.combo_t > 0.0:
            fade = min(1.0, self.combo_t / (COMBO_HOLD * 0.5))
            text(f"x{self.combo}", self.width - 14, 60, 16 + min(8, self.combo // 3),
                 rl.mix_rgb(pal.ink, ORB_COLOR, fade), anchor="topright")


# ---------------------------------------------------------------------------
# Flight, materials and kit -- shared by generation and simulation
# ---------------------------------------------------------------------------

#: Orbs are drawn and boxed at this scale; both read it, so they cannot drift.
ORB_SCALE = 0.28
#: How far the player reaches for one. Roughly an arm.
PICKUP_REACH = 0.85
ORB_COLOR = (120, 240, 190)
LANTERN_GLOW = (255, 216, 140)
COMBO_HOLD = 1.8
#: How long a block takes to arrive at the generation horizon.
POP_IN = 0.28
#: How hard a held direction bends the course, in radians of heading.
STEER = 0.5
#: Blocks ahead of the player a steer may not touch. They are committed: the
#: one being landed on, and the one after it.
STEER_KEEP = 2
#: Longest a player may hold a block before the beat resumes.
HOLD_MAX = 1.6
#: How long a key press keeps the scene in the player's hands.
DRIVEN_HOLD = 0.6


def flight(frm, to) -> tuple[float, float]:
    """Duration and take-off speed of the hop from ``frm`` to ``to``.

    A hop covers its gap at running pace -- but a *fall* takes as long as a
    fall takes, so a descent is timed by the drop instead, at the same launch
    speed any other hop uses. That is the whole difference between a five-block
    drop that reads as a drop and one that reads as a long step down.
    """
    dist = math.dist((frm[0], frm[2]), (to[0], to[2]))
    dy = to[1] - frm[1]
    dur = min(dist / HOP_SPEED, AIR_LEVEL_MAX)
    if dy < 0.0:
        dur = max(dur, (HOP_LAUNCH + math.sqrt(HOP_LAUNCH ** 2
                                               + 2 * GRAVITY * -dy)) / GRAVITY)
    dur = max(AIR_MIN, min(AIR_MAX, dur))
    # launch speed that lands exactly on target under gravity
    return dur, dy / dur + 0.5 * GRAVITY * dur


def _build_styles(pal, run: int) -> dict[str, dict]:
    """Every material the scene can draw, built once per run.

    The candy colours come from the palette so two runs never look alike; the
    *materials* -- wood, brick, stone, quartz -- keep recognisable colours,
    because a plank walkway that is only "another shade of the accent colour"
    stops being a plank walkway. They are dimmed toward the run's ambient so a
    night course is lit like a night course.
    """
    lit = 0.45 + 0.55 * pal.ambient

    def tone(c: rl.RGB) -> rl.RGB:
        return rl.scale_rgb(c, lit)

    recipe: list[tuple[str, rl.RGB, str, float]] = [
        ("candy0", pal.blocks[0], "checker", 0.05),
        ("candy1", pal.blocks[1], "noise", 0.06),
        ("candy2", pal.blocks[2], "speck", 0.05),
        ("wood", tone((150, 106, 60)), "planks", 0.04),
        ("brick", tone((170, 88, 70)), "bricks", 0.04),
        ("stone", tone((132, 132, 140)), "cobble", 0.05),
        ("quartz", tone((228, 226, 218)), "grain", 0.03),
        ("lantern", (255, 212, 128), "lantern", 0.03),
        ("orb", ORB_COLOR, "lantern", 0.02),
        ("sand", tone((222, 208, 150)), "noise", 0.06),
        ("leaf", tone((72, 148, 62)), "leaves", 0.05),
        ("water", rl.scale_rgb((120, 200, 236), lit), "grain", 0.04),
    ]
    styles = {
        name: {"model": voxel.block_model(f"run{run}-{name}", colour,
                                          noise=noise, seed=run * 17 + i,
                                          pattern=pattern),
               "color": colour}
        for i, (name, colour, pattern, noise) in enumerate(recipe)
    }
    styles["grass"] = {
        "model": voxel.block_model(f"run{run}-grass", tone((124, 92, 62)),
                                   noise=0.05, seed=run * 17 + 40,
                                   top=tone((96, 186, 82)),
                                   side_band=tone((104, 170, 76)),
                                   pattern="speck"),
        "color": tone((96, 186, 82)),
    }
    return styles


def _choose_kit(rng, pal) -> dict:
    """What the player is carrying this run.

    Each kit is assembled from the same unit cube as everything else -- a
    sword is a blade, a guard and a grip -- so a new one costs a list of boxes
    and no new geometry at all.
    """
    def part(style, u=0.0, v=0.0, f=0.0, size=(0.5, 0.5, 0.5), yaw=0.0, tilt=0.0):
        return {"style": style, "u": u, "v": v, "f": f, "size": size,
                "yaw": yaw, "tilt": tilt}

    kits = [
        ("block", [part(rng.choice(("candy0", "candy1", "candy2", "stone")))], False),
        ("sword", [part("wood", v=-0.30, size=(0.10, 0.34, 0.10)),
                   part("stone", v=-0.08, size=(0.34, 0.09, 0.09)),
                   part("quartz", v=0.36, size=(0.10, 0.78, 0.06), tilt=-4.0)], False),
        ("pickaxe", [part("wood", size=(0.09, 0.86, 0.09)),
                     part("stone", v=0.44, size=(0.60, 0.13, 0.10), tilt=-6.0)], False),
        ("torch", [part("wood", v=-0.10, size=(0.10, 0.62, 0.10)),
                   part("lantern", v=0.28, size=(0.16, 0.18, 0.16))], True),
        ("lantern", [part("lantern", size=(0.34, 0.42, 0.34)),
                     part("wood", v=0.30, size=(0.07, 0.16, 0.07))], True),
    ]
    name, parts, glow = kits[rng.randrange(len(kits))]
    return {"name": name, "parts": parts, "glow": glow}
