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
from ..engine.fx import (Burst, Weather, glow_pass, ground_quad, no_depth_write,
                         unit_quad)
from ..engine.hud import text
from ..engine.scene import Scene, SceneContext, register
from ..engine import textures
from ..engine.sky import SkyDome
from ..engine.textures import cloud_blob
from .parkourkit import GroundRun

#: A gap is blocks *of air*, so the centre-to-centre step is one more.
#:
#: Two tables, not one, because a course that is as hard after four minutes as
#: it was after four seconds has nothing to show you. A run opens on the easy
#: pair and ends on the hard pair, interpolated by :attr:`ParkourScene.
#: difficulty` -- see :func:`_ramped` for how, and ``SEGMENT_RAMP`` for the
#: same idea applied to which set-pieces get chosen.
#:
#: There is no entry below two, and that is not a taste call. ``MIN_HOP`` is
#: 2 m, so :func:`fit_gap` widens a one-block gap to two wherever it is asked
#: for; a table that still offered 1 would be describing a hop the generator
#: cannot lay. One block of air is a step, not a jump, and a run of them back
#: to back is the shuffling the rebuild was asked to get rid of.
#: And the tables lean high, which is the *shape* of the jump and not merely
#: its length. There is one jump impulse in this game and one horizontal
#: speed, so how high an arc goes is decided entirely by how far it has to
#: reach: a hop at the top of what the rise allows apexes at the familiar
#: 1.25 blocks, and a two-block one apexes at a third of a metre. Measured
#: over the old tables, the mean hop apexed at 0.53 m -- 43% of a vanilla
#: jump, which is not a jump anybody recognises but a *skip*, and a run of
#: skips is most of what "it looks bot-like" was. Nothing about the physics
#: had to change to fix it; asking for the gaps a real course has was enough,
#: and it is *faster* as well, because a longer hop at the same speed covers
#: more ground for the same landing.
#:
#: A level gap of four is the sprint jump itself and a level five cannot be
#: jumped at all, so the fives and sixes here only ever come out at their full
#: width when the rise drawn with them is a drop, and :func:`fit_gap` narrows
#: them back when it is not.
#:
#: The easy table leans to three now and it is the *only* place a ramp in hop
#: length can still live. Every hop is a full-impulse sprint jump, so the
#: reach of one is fixed by its rise: a level three is 3.24 m taken at ninety
#: per cent of the impulse, a level four is the whole 4.24, and there is
#: nothing in between and nothing beyond. Weighted to fours at both ends -- as
#: this table was when the impulse floor arrived -- the mean hop read 4.14 m
#: early and 4.12 m late, which is not a ramp at all.
GAP_EASY = (3, 3, 3, 3, 3, 3, 4, 4)
GAP_HARD = (4, 4, 4, 5, 5, 5, 5, 5, 6, 6)
#: Rises pair with gaps because the physics ties them together: falling is the
#: only thing that buys reach, so the hard table drops more often. It is also
#: what keeps the long hops honest -- a five-block gap is only jumpable off a
#: descent, and asking for one level just gets it narrowed back down.
RISE_EASY = (-1, -1, 0, 0, 0, 0, 0, 0, 1, 1)
RISE_HARD = (-3, -2, -2, -2, -1, -1, -1, 0, 0, 1)
#: Blocks laid before a run is at full difficulty. Roughly eighty hops, which
#: at sprint pace is a little under a minute -- inside the length of a turn the
#: overlay is actually on screen for.
RAMP_BLOCKS = 80

EYE = 1.62
COURSE_ALT = 58            # block altitude above the ocean
#: How far the course may wander from its altitude before the generator insists
#: on going the other way. Wide enough that a descent set-piece has somewhere
#: to fall to.
BAND = 18
TRAIL = 2                  # blocks kept behind the player
AHEAD = 14                 # blocks generated ahead
#: Distance at which the course has faded fully into the haze. Generation runs
#: fourteen blocks ahead, which is about forty metres, so at the old seventy
#: the far half of the course sat washed out against a pale sea and read as
#: two or three blocks and then nothing. Past the last block there is nothing
#: to hide anyway -- blocks fade themselves in as they arrive.
FOG_FAR = 95.0
BELOW_FOG = 0.55           # extra fog on the world far below

# -- how a body moves, in Minecraft's own numbers ---------------------------
#
# Everything below is vanilla, converted from ticks to seconds, because the
# motion is the single thing a viewer who has played the game will judge this
# on. The previous version solved each hop for whatever duration made the
# distance work and clamped the result into a hang-time window, which meant
# horizontal speed swung between about 3.5 and 6 m/s from hop to hop -- and
# then the body stopped dead on every block for up to nine tenths of a second
# before the next one. Constant speed with a beat you never quite stop for is
# the difference between a run and a slideshow.

#: How flat the arc is against vanilla's, and the one number in this block
#: that is not the game's.
#:
#: It scales the jump impulse and gravity *together*, and that is what makes
#: it safe to turn: hang time is ``2*v/g`` and reach is that time at sprint
#: speed, so both are unchanged, while the apex is ``v^2/2g`` and comes down
#: in proportion. Every span the generator computes, every gap table, every
#: run-up and the whole rhythm of the scene stay exactly where they were --
#: the arc simply sits lower under the same timing. At 0.86 a level hop
#: apexes at 1.08 m rather than 1.26.
#:
#: Set by eye, on the owner's note that the arc was "a tiny bit off" once
#: everything else was right, and it is the only place this scene knowingly
#: leaves vanilla's numbers. Worth knowing why the obvious alternatives are
#: worse: dropping ``JUMP_V`` alone shortens the jump's reach, which makes the
#: four-block gap illegal and pulls the whole course back to threes; raising
#: ``AIR_SPEED`` alone flattens the arc by making the body outrun it, which
#: changes the pace of everything.
ARC = 0.86
#: 0.08 blocks/tick^2 with vanilla's drag applied, flattened by :data:`ARC`.
GRAVITY = 28.0 * ARC
#: 0.42 blocks/tick: the only jump impulse the game has, flattened to match.
JUMP_V = 8.4 * ARC
#: Vanilla sprint, and what the player crosses a block at.
RUN_SPEED = 5.612
#: Sprinting adds a forward impulse on the tick you jump, which is the entire
#: reason a four-block gap is clearable at all. Horizontal speed is constant at
#: this for the whole flight -- no easing, no per-hop solve.
AIR_SPEED = 7.10
#: Vanilla walk. What holding the block down does: you cross it slower, you do
#: not stand still.
WALK_SPEED = 4.317
#: The least of the one jump impulse a hop in this scene is allowed to spend.
#:
#: This is the number the whole "it does not feel like a Minecraft jump" note
#: came down to. There is exactly one jump in the game and a player spends all
#: of it every time; what varies is the gap, and a gap shorter than the jump's
#: own reach is answered by landing further onto the block -- not by jumping
#: less hard. Solving each hop's take-off from its endpoints did the opposite:
#: two thirds of every hop came out at 60-85% of the impulse, apexing 0.5-0.9 m
#: against vanilla's 1.25, which is a *hop* and not a jump, and a run of them
#: is what reads as bouncing.
#:
#: It is enforced through :func:`hop_span`, whose ``lo`` is now the same
#: formula as its ``hi`` with a smaller impulse in it, so every gap the
#: generator can ask for is one a real jump lands on. 0.90 admits the level
#: three-block gap alongside the four; 0.95 leaves only the four, and a course
#: of nothing but its longest jump has nothing to show you.
IMPULSE_MIN = 0.90
#: How much of a hop's shortfall against the full jump's reach the *geometry*
#: gives back, in metres, before the impulse has to come down for it. The
#: sources are the two a player uses: land deeper into the block, and leave
#: the one behind a little earlier. Both are bounded by a block's own size --
#: see :func:`_hop_points` -- so this is the conservative figure for the
#: one-cell landing that most of the course is made of, and it is what
#: :func:`hop_span` budgets with.
ABSORB = 0.60
#: The shortest run a landing keeps for itself once the hop out of it has
#: taken what it needs.
#:
#: 0.35 and not the 0.12 this started at, and the difference is a *beat*. At
#: 0.12 the feet were down for two frames in thirty: the body was airborne 93%
#: of the time and a correct 1.25 m arc back to back with no gap between them
#: reads as pogo-ing rather than as running. Landings that cannot buy their
#: impulse within what is left are simply refused, and the generator answers
#: with a wider gap -- which is the right trade twice over, because a longer
#: hop is a *slower* rhythm as well as a fuller jump.
MIN_RUN = 0.35
#: A hop is legal exactly when the take-off it needs is one a body has. Zero is
#: stepping off an edge without jumping; :data:`JUMP_V` is the only jump there
#: is. Everything the generator lays down is checked against this pair, which
#: is why there is no separate table of legal gaps and rises.
#: The floor is not zero, and the reason is geometric rather than physical.
#: The feet leave from the block's far *edge*, so half the body is still over
#: the block at the moment of take-off -- 0.2 m of it on a wide platform, whose
#: footprint reaches beyond where anybody stands on it. A hop that barely
#: leaves the ground is therefore already falling while the body is still over
#: the block it left, and the camera dips through the platform's own outer
#: cube. A tenth of vanilla's jump is enough to be clear before that happens.
VY_MIN = 1.6 * ARC
VY_MAX = JUMP_V
#: Hang time bounds, derived from the above rather than chosen: a level hop at
#: full jump is 0.6 s, and the longest fall the band allows is under 1.3 s.
AIR_MIN, AIR_MAX = 0.12, 1.30
#: Shortest hop the generator will lay down, take-off point to landing point.
#: Below this it is a shuffle, not a jump.
#:
#: This one number does most of the work of raising the whole distribution, and
#: it does it in one place. Every set-piece that hard-codes ``gap=1`` -- the
#: staircase, the causeway, the spiral, half the zigzag -- goes through
#: :func:`fit_gap`, which widens a gap until the hop across it is one this
#: floor admits. At 1.1 a one-block gap was legal, so a third of every cruise
#: and all of those set-pieces laid 1.32 m hops: in the real game that is a
#: step you take without thinking about it, and a run of them reads as
#: shuffling. At 2.0 the narrowest thing the generator can express is two
#: blocks of air, and nothing else had to be touched to get it.
MIN_HOP = 2.0

#: The player's collision volume: vanilla's own 0.6 x 1.8 box, standing on the
#: block surface. There is no player model in first person to measure, so this
#: is the one volume in the scene that is declared rather than derived -- and
#: everything it collects has its box built from the model that draws it.
BODY_HALF_W = 0.30
BODY_H = 1.80
#: Where on that body an orb is aimed, so passing through it cannot miss.
CHEST = 0.90
#: Headroom a landing needs, in whole cells: a 1.8 m body standing on a
#: surface needs the two cells above it clear.
HEADROOM = 2

#: form -> height of the walking surface above the block's base.
#:
#: ``stair`` is a full block. It used to draw a second half-block a metre
#: behind itself as a tread, which cut into the block it belonged to on every
#: course not running due north -- and a real vanilla stair cannot help either,
#: because the walking surface of one is 1.0 at one edge of the cell and 0.5 at
#: the other, while a body lands on the near edge and leaves from the far one.
#: A separated block at gap one and rise one already reads as a staircase; that
#: is what an infinite-parkour staircase looks like in the reference footage.
FORMS = {"full": 1.0, "slab": 0.5, "wide": 1.0, "stair": 1.0}
#: form -> how far from the block's centre the player's feet plant, along the
#: direction of travel. You land on the near edge of a block and take off from
#: the far one -- which is what a run-up *is*, and what makes the gap the body
#: actually clears bigger than the gap between block centres.
#:
#: 0.38, and the whole of the difference is whether the classic four-block
#: jump exists. The feet plant this far inside a landing's edge, so a four-block
#: gap asks for ``5 - 2*EDGE`` -- 4.32 m at 0.34, which is past the 4.26 a full
#: jump reaches at sprint speed, so ``fit_gap`` narrowed every level four back
#: to a three and the longest level hop in the scene was 3.28 m. A body has to
#: be *walking* to spend the whole jump impulse on 3.28 m, and walking is
#: exactly what it looked like from inside. At 0.38 the four-block jump is
#: 4.24 m: the full impulse at 7.07 m/s, which is a sprint jump and the move
#: the game is famous for.
#:
#: The ceiling on this number is the *climb*, not the body. A hop that rises a
#: block has 3.10 m of reach, and a two-block gap at 0.42 asks for 3.16 -- so
#: at 0.42 no staircase in the scene is legal and every one of them silently
#: declines. Vanilla stands with the feet 0.5 from the centre and the hitbox
#: hanging 0.3 past the edge, so there is room here; there is just no *use*
#: for it.
EDGE = {"full": 0.38, "slab": 0.38, "stair": 0.38, "wide": 1.30}
#: Half-footprint of a form, in cells: a wide platform is three by three.
SPREAD = {"wide": 1}

#: The set-piece vocabulary, with its weights. Names map to ``_seg_<name>``.
SEGMENT_TABLE = (
    ("cruise", 26),
    ("staircase", 10),
    ("descent", 10),
    ("zigzag", 9),
    ("chasm", 8),
    ("causeway", 9),
    ("spiral", 8),
    ("gate", 7),
    ("lanternwalk", 6),
    ("pillars", 9),
    ("ruin", 8),
    ("squeeze", 8),
    ("slabs", 8),
)
#: How the ramp reweights the vocabulary: a weight is multiplied by
#: ``1 + bias * difficulty``. The demanding set-pieces are rare at the start of
#: a run and common by the end of it, and the forgiving ones go the other way.
#: This is the half of the ramp a viewer actually *reads* -- a wider gap is a
#: number, but a squeeze or a chasm arriving instead of a plank causeway is a
#: change of subject.
SEGMENT_RAMP = {
    "squeeze": 3.0, "slabs": 2.5, "chasm": 2.0, "pillars": 1.0,
    "cruise": -0.55, "causeway": -0.7, "lanternwalk": -0.4, "staircase": -0.3,
    "spiral": -0.4,
}
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
        #: Glows queued by this frame's draws, issued in one pass at the end of
        #: it. Emptied by :meth:`_draw_glows`, so it is per-frame state that a
        #: frame drawn twice ends up with exactly as it started -- which is the
        #: property every screenshot this scene is judged from depends on.
        self._glows: list[tuple[float, float, float, float, rl.RGB, int]] = []
        # A sea, not a blue floor: the deep is keyed to the sky, so night runs
        # get a black ocean. Every island then sits on its own pale reef, which
        # is most of what stops the water reading as a painted plane.
        self.deep = rl.mix_rgb(rl.mix_rgb(pal.sky_bottom, (10, 46, 96), 0.78),
                               pal.fog, 0.10)

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
        #: Every solid cell the live course occupies, rebuilt whenever the
        #: course changes rather than maintained incrementally -- the course is
        #: only ever a couple of dozen blocks long, and a stale occupancy map
        #: is exactly the bug this exists to prevent.
        self._solid: set[tuple[int, int, int]] = set()
        #: How many times placement has had to fall back on its emergency hop.
        #: Should be zero; the generation tests hold it to that.
        self.stuck = 0
        #: Blocks laid down this run. Drives :attr:`difficulty`, and nothing
        #: else reads it.
        self.laid = 0
        self._spawn_block(first=True)
        while len(self.blocks) < AHEAD:
            self._spawn_block()

        # -- motion: a body that never stops -------------------------------
        # Two phases, and horizontal speed is constant through both: you run
        # across the block you are on, from where you landed to the edge you
        # leave from, and then you fly. There is no beat where the body is
        # stationary -- that beat is what made this read as a slideshow of
        # camera positions rather than as somebody running.
        self.jump_index = 0           # block we are standing on
        #: Landings since the run began, and the one count of them that only
        #: ever goes up: ``jump_index`` is walked back whenever the course
        #: drops blocks off its tail. A probe cannot segment hops by watching
        #: the phase flip -- a landing between two jumps is now routinely
        #: shorter than a frame -- so it watches this instead.
        self.landings = 0
        self.phase = "ground"
        self.phase_t = 0.0
        self.ground_dur = 0.2
        self.air_dur = 0.4
        self.stand = list(self._land_point(self.blocks[0]))
        self.takeoff = list(self.stand)
        self.land_at = list(self.stand)
        self.run_from = list(self.stand)
        self.run_to = list(self.stand)
        self.vy0 = 0.0
        #: Horizontal speed of the hop in progress. Not a constant any more --
        #: see :func:`flight`.
        self.air_speed = AIR_SPEED
        self.pos = list(self.stand)
        self.vy = 0.0
        #: How far the eye is below where it rests, and how fast it is getting
        #: there. A spring, kicked by the impact -- see :data:`DIP_W`.
        self.dip = 0.0
        self.dip_v = 0.0
        #: How much of the walk bob is showing, 0..1. Eased, not switched.
        self.foot = 1.0
        #: Field of view, eased toward what the speed asks for.
        self.fov = FOV
        #: Cruise speed a held duck is asking for, 0 when nobody is holding one.
        self.hold_speed = 0.0
        self.distance = 0.0
        #: Ground distance covered, which is what drives the walk cycle. Time
        #: would drive it too, but then the bob keeps swinging in mid-air.
        self.stride = 0.0
        self.yaw = self.heading
        self.pitch = 0.12
        #: How much of a look is still owed. A player does not ease onto a new
        #: heading at a constant rate -- they flick toward the next block as
        #: they leave the one they are on, then hold it.
        self._flick = 0.0
        self._roll = 0.0
        self._speed = RUN_SPEED
        self._begin_ground(self.blocks[0])

        # -- scoring -------------------------------------------------------
        self.orbs = 0
        self.orbs_missed = 0
        #: Orbs thrown away with a re-laid tail while somebody was steering.
        #: Not misses -- see :meth:`_steer_course`.
        self.orbs_discarded = 0
        self.combo = 0
        self.combo_t = 0.0

        # -- world below ---------------------------------------------------
        self.islands: list[dict] = []
        self._next_island_z = 0.0
        for _ in range(int(9 * self.detail) or 5):
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

    @property
    def difficulty(self) -> float:
        """0 at the start of a run, 1 once it has been going a while.

        Real infinite-parkour servers ramp -- gaps widen, landings narrow, the
        margin for error shrinks -- and a course that does not is as hard at
        four minutes as at four seconds, which is the same as having no shape
        at all.

        Counted in blocks laid rather than metres travelled, for two reasons.
        Generation runs fourteen blocks ahead of the body, so metres travelled
        is the wrong clock for deciding what to build. And the geometry probes
        and half the generation tests grow a course by calling
        :meth:`_spawn_block` without ever moving a body: keyed to
        ``self.distance`` this would read zero forever, and every test that
        believes it is checking the hard end of the course would be checking
        the easy one.
        """
        return min(1.0, self.laid / RAMP_BLOCKS)

    def _gap(self, rng, easy, hard) -> int:
        """A set-piece's gap, ramped between two of its own tables.

        Every set-piece goes through this rather than choosing a constant,
        because the ramp has to reach the whole vocabulary to mean anything:
        the cruise is about a fifth of the blocks laid, so a ramp that only
        touched the cruise moved the median by two centimetres. Measured.

        The tables are per set-piece and not shared, because what "harder"
        means is not the same for all of them -- a causeway with a four-block
        gap is not a causeway, and a staircase physically cannot have one.
        """
        return _ramped(rng, easy, hard, self.difficulty)

    def _node(self, gap: float, rise: float, style: str, turn: float | None = None,
              form: str = "full", deco: str | None = None, orbs: int = 0,
              deco_style: str | None = None) -> dict:
        return {"gap": gap, "rise": rise, "turn": turn, "form": form,
                "style": style, "deco": deco, "orbs": orbs,
                # What the structure under a block is made of, when that is
                # not what the block is made of. A coloured cap on a stone
                # column is most of what a vanilla parkour map looks like, and
                # a column in the same colour as its cap is a smear.
                "deco_style": deco_style}

    def _plan_segment(self) -> None:
        """Choose the next set-piece and expand it into nodes."""
        rng = self.rng
        y = self.blocks[-1]["y"] if self.blocks else COURSE_ALT
        drift = (y - COURSE_ALT) / BAND        # -1 floor, +1 ceiling

        hard = self.difficulty
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
            # The ramp. Applied after the altitude weighting and before the
            # repetition rule, so it changes what a run reaches for without
            # ever overriding either.
            weight = int(weight * max(0.0, 1.0 + SEGMENT_RAMP.get(name, 0.0) * hard))
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
        """The default: hops from the weighted tables, in the candy colours.

        Both tables are ramped, and the rise is drawn first because it is the
        rise that decides what a gap is allowed to be -- there is one jump
        impulse, so reach comes from falling and nothing else.
        """
        hard = self.difficulty
        out = []
        for i in range(rng.randint(4, 9)):
            rise = _ramped(rng, RISE_EASY, RISE_HARD, hard)
            out.append(self._node(
                gap=fit_gap(_ramped(rng, GAP_EASY, GAP_HARD, hard), rise),
                rise=rise,
                style=self.candy[(i // 2) % 3],
                # Landings narrow as the run goes on: a slab is half the
                # target a full block is, and the eye reads that instantly.
                form="slab" if rng.random() < 0.12 + 0.24 * hard else "full",
                deco="crumb" if rng.random() < 0.22 else None,
                orbs=1 if rng.random() < 0.45 else 0))
        # A breather platform closes some cruises, as somewhere to arrive --
        # and fewer of them arrive late in a run, because a breather is the
        # opposite of the thing the ramp is for. Its posts are unlit: lanterns
        # mark the set-pieces, and a lantern on every platform marks nothing.
        if rng.random() < 0.42 - 0.30 * hard:
            out.append(self._node(gap=3, rise=0, style="stone", form="wide",
                                  deco="posts", orbs=1))
        return out

    def _seg_slabs(self, rng) -> list[dict]:
        """A run of half-height landings: the same hop onto half the target.

        ``FORMS`` has carried ``slab`` all along and the cruise sprinkles them,
        but a *run* of them is a different thing to watch -- the course visibly
        thins out, and because a slab's walking surface is halfway up its cell
        the whole line sits at a height nothing else in the scene uses. It is
        also the cheapest difficulty there is: no new geometry, no new
        placement rule, and every guarantee the scene makes still holds,
        because a slab is already a form placement knows how to reason about.
        """
        style = rng.choice(("quartz", "stonebrick"))
        out = []
        for i in range(rng.randint(5, 8)):
            rise = rng.choice((0, 0, 0, -1))
            out.append(self._node(
                gap=fit_gap(self._gap(rng, (3, 3, 3, 4), (4, 4, 4, 5)), rise),
                rise=rise,
                style=style if i % 2 else self.candy[i % 3],
                form="slab",
                deco="rail" if i % 3 == 0 else None,
                orbs=1 if rng.random() < 0.55 else 0))
        return out

    def _seg_squeeze(self, rng) -> list[dict]:
        """Beams to skim under and columns to clear -- the two shapes vanilla
        parkour uses to make an ordinary jump frightening.

        Both are placed *against the arc that arrives*, which is the only
        reason either is safe to build. A block's landing point and the
        take-off it was jumped from are both known by the time its decoration
        is expanded, so the exact flight the body is about to make is a list of
        points -- and a beam hung a body's height above the highest of them, or
        a column topped out just under the lowest, is guaranteed to be missed
        while looking as though it will not be. :func:`_in_the_way` then checks
        that guarantee rather than trusting it.

        Note what is *not* being done. ``HEADROOM`` still keeps two cells clear
        over every landing, because a body has to be able to stand where it
        arrives; what is relaxed is the space over the **gap**, which nothing
        ever needed and which is where a head-hitter lives in the real game.
        """
        style = rng.choice(("stonebrick", "brick", "stone"))
        out = []
        for i in range(rng.randint(4, 6)):
            rise = rng.choice((0, 0, 0, -1))
            out.append(self._node(
                gap=fit_gap(self._gap(rng, (3, 3, 3), (4, 4, 5)), rise),
                rise=rise,
                style=self.candy[i % 3], deco_style=style,
                deco="lintel" if i % 2 else "hurdle",
                orbs=1 if rng.random() < 0.5 else 0))
        return out

    def _seg_staircase(self, rng) -> list[dict]:
        """A flight of stairs, climbing one block a step.

        Stair blocks rather than cubes, and the tread lives *inside* the
        block's own cell the way a vanilla stair does. The previous version
        hung a second half-block a metre behind each step, which cut into the
        step it belonged to on every course not running due north.

        A staircase is the one set-piece the ramp cannot widen, and the reason
        is arithmetic rather than taste: climbing a block means arriving past
        the apex, so ``hop_span(1)`` tops out at 3.1 m and only a two-block gap
        fits under it. What the ramp does with staircases instead is call for
        fewer of them -- see ``SEGMENT_RAMP``.
        """
        style = rng.choice(("stonebrick", "quartz"))
        bend = rng.uniform(-0.10, 0.10)
        return [self._node(gap=2, rise=1, style=style, turn=bend, form="stair",
                           orbs=1 if i % 2 else 0)
                for i in range(rng.randint(5, 8))]

    def _seg_descent(self, rng) -> list[dict]:
        """The long fall.

        A drop cannot also be a short hop: the body keeps its speed all the way
        down, so it covers as much ground as the fall takes. :func:`fit_gap`
        opens the gap to whatever the drop needs, which is why these read as
        leaping *out* into a void rather than as walking down a staircase.
        Pillars hang under the landings so the eye has something to measure
        the drop against on the way past.
        """
        out = []
        for i in range(rng.randint(3, 4)):
            drop = rng.randint(3, 5) if i == 0 else rng.randint(2, 4)
            out.append(self._node(gap=fit_gap(self._gap(rng, (3, 4), (4, 5)), -drop),
                                  rise=-drop,
                                  style="stone", deco="pillar", orbs=2))
        out.append(self._node(gap=2, rise=0, style="lantern", form="wide",
                              deco="lanterns", orbs=1))
        return out

    def _seg_zigzag(self, rng) -> list[dict]:
        """Tight alternating turns -- the camera work is the point.

        The swing is smaller than it was. On a strip this narrow a
        forty-degree change of heading throws the whole course out of frame,
        and a viewer watching an empty ocean swing past is not watching
        parkour.
        """
        swing = rng.uniform(0.34, 0.52)
        gap = self._gap(rng, (3, 3, 3, 4), (4, 4, 5))
        return [self._node(gap=gap, rise=rng.choice((0, 0, 0, 1)),
                           style=self.candy[i % 3],
                           turn=swing if i % 2 else -swing,
                           orbs=1 if rng.random() < 0.5 else 0)
                for i in range(rng.randint(6, 9))]

    def _seg_chasm(self, rng) -> list[dict]:
        """Lantern platform, the longest jump in the game, lantern platform.
        Orbs strung across the void mark the line.

        "The longest jump in the game" is a computed number here rather than a
        dramatic one: a body leaves the ground at one speed and falls at one
        rate, so the furthest it can reach is fixed, and reaching further is
        only available by dropping. Hence the deliberate step down -- the extra
        hang time of a one- or two-block drop is what buys the last metre, and
        it is exactly how a player clears a gap they cannot make level.
        """
        drop = rng.choice((-1, -1, -2))
        return [
            self._node(gap=self._gap(rng, (3, 3), (3, 4)), rise=0,
                       style="quartz", form="wide", deco="lanterns"),
            self._node(gap=max_gap(drop), rise=drop, style="lantern", orbs=3),
            self._node(gap=self._gap(rng, (3, 3), (3, 4)), rise=0,
                       style="quartz", form="wide", deco="lanterns", orbs=1),
        ]

    def _seg_causeway(self, rng) -> list[dict]:
        """A plank walkway with a fence: short hops, a straight line, and a
        completely different material. Contrast is what makes the rest read."""
        gap = self._gap(rng, (2,), (2, 3))
        return [self._node(gap=gap, rise=0, style="wood", form="slab",
                           turn=rng.uniform(-0.05, 0.05),
                           deco="rail" if i % 2 == 0 else None,
                           orbs=1 if i % 3 == 1 else 0)
                for i in range(rng.randint(6, 10))]

    def _seg_spiral(self, rng) -> list[dict]:
        """A staircase that winds, with a tower under it."""
        turn = rng.choice((0.5, -0.5))
        gap = self._gap(rng, (2,), (2, 3))
        return [self._node(gap=gap, rise=1 if i % 2 else 0,
                           style="brick", turn=turn,
                           deco="pillar" if i % 2 == 0 else None,
                           orbs=1 if i % 3 == 0 else 0)
                for i in range(rng.randint(6, 9))]

    def _seg_gate(self, rng) -> list[dict]:
        """Something to run *through* rather than only on."""
        return [
            self._node(gap=self._gap(rng, (3, 4), (4, 5)), rise=0,
                       style="quartz"),
            self._node(gap=self._gap(rng, (3, 4), (4, 5)), rise=0,
                       style="quartz", deco="gate", orbs=1),
            self._node(gap=self._gap(rng, (3, 4), (4, 5)),
                       rise=rng.choice((0, 0, -1)), style="quartz"),
        ]

    def _seg_lanternwalk(self, rng) -> list[dict]:
        """Torchlit stepping stones -- the night runs live for this."""
        gap = self._gap(rng, (3, 4), (4, 4, 5))
        return [self._node(gap=gap, rise=rng.choice((0, 0, 1, -1)),
                           style="lantern" if i % 2 else self.candy[i % 3],
                           deco="torch" if i % 2 == 0 else None,
                           orbs=1 if rng.random() < 0.6 else 0)
                for i in range(rng.randint(4, 7))]

    def _seg_pillars(self, rng) -> list[dict]:
        """Columns standing out of the void, tops at staggered heights.

        The one set-piece that is mostly *below* the path: each landing caps a
        shaft running down out of sight, so this stretch reads as ruins
        standing in the sea rather than as blocks hanging in air. Vanilla
        parkour maps are full of these and it costs one decoration.
        """
        style = rng.choice(("stonebrick", "stone", "brick"))
        out = []
        for i in range(rng.randint(5, 8)):
            rise = rng.choice((0, 0, 1, -1, -1))
            out.append(self._node(gap=fit_gap(self._gap(rng, (3, 3, 4, 4),
                                                        (4, 5, 5, 6)), rise),
                                  rise=rise,
                                  style=self.candy[i % 3] if i % 2 else style,
                                  deco_style=style,
                                  turn=rng.uniform(-0.16, 0.16),
                                  deco="shaft",
                                  orbs=1 if rng.random() < 0.5 else 0))
        return out

    def _seg_ruin(self, rng) -> list[dict]:
        """A broken wall you hop along the top of, with what is left of its
        arches still standing.

        One material, buttresses under alternate blocks and a lintel over the
        others, so the eye reads a structure that used to be something. A
        course made only of free-floating cubes never gets to say that.
        """
        style = rng.choice(("stonebrick", "brick"))
        bend = rng.uniform(-0.08, 0.08)
        gap = self._gap(rng, (3, 3, 3, 4), (4, 4, 5))
        return [self._node(gap=gap,
                           rise=rng.choice((0, 0, 1, -1)),
                           style=style, turn=bend,
                           deco="buttress" if i % 2 == 0 else "arch",
                           orbs=1 if rng.random() < 0.45 else 0)
                for i in range(rng.randint(5, 8))]

    # -- generation: placement --------------------------------------------

    # -- the occupancy map -------------------------------------------------
    #
    # Every solid thing the course draws lives in a whole cell of an integer
    # lattice, and this set is what those cells are. It exists because the
    # previous generator only ever asked "is the centre of the next block at
    # least 1.45 m from the centre of a recent one", which is not a question
    # about volumes at all: it let a three-wide platform's outer cube sit
    # halfway inside the next platform's, and it never looked at decorations
    # or at the air the player flies through. Measured over eight thousand
    # blocks, one pair in two interpenetrated and the body was inside a solid
    # block on nine per cent of frames.

    def _cells_of(self, blk: dict):
        """Every integer cell a block and its decorations fill.

        Only whole-cube decoration counts. Fence posts, rails, torches and
        lanterns are sub-block furniture that sits *inside* a cell exactly as
        vanilla's does, so treating them as solid would have the generator
        refusing to lay a course past a lamp post. They are kept out of the
        player's way by where they are put instead -- see :meth:`_deco_cubes`.
        """
        x, y, z = blk["x"], blk["y"], blk["z"]
        sp = SPREAD.get(blk["form"], 0)
        for ox in range(-sp, sp + 1):
            for oz in range(-sp, sp + 1):
                yield (x + ox, y, z + oz)
        for d in blk["deco"]:
            if d["sx"] > 0.5 and d["sz"] > 0.5:
                yield (x + _round(d["dx"]), y + _round(d["dy"]),
                       z + _round(d["dz"]))

    def _rebuild_solid(self) -> None:
        self._solid = {c for blk in self.blocks for c in self._cells_of(blk)}

    def _free(self, cells) -> bool:
        return all(c not in self._solid for c in cells)

    def _body_cells(self, x: float, y: float, z: float):
        """Cells a body with its feet at (x, y, z) touches.

        Deliberately generous at the edges: the body is 0.6 wide, so on the
        grid it straddles two cells whenever it is not dead centre, and a
        corridor test that missed the cell the shoulder is in would clear an
        arc that visibly grazes a wall.
        """
        for cy in range(_floor(y + 0.05), _floor(y + BODY_H - 0.05) + 1):
            for cx in (_round(x - BODY_HALF_W), _round(x + BODY_HALF_W)):
                for cz in (_round(z - BODY_HALF_W), _round(z + BODY_HALF_W)):
                    yield (cx, cy, cz)

    def _arc_is_clear(self, frm, to, exempt: frozenset) -> bool:
        """Nothing solid between the take-off and the landing.

        Samples the actual arc the body will fly rather than a straight line,
        because the whole point of an arc is that it goes over things.

        Almost nothing is exempt, and that is the point. Feet standing on a
        full block are level with the *top* of its cell, so the block never
        shows up as an obstacle unless the arc has dipped below its own
        take-off surface -- which, while still over the block it left, is
        exactly the failure worth catching. Only a slab needs excusing, because
        its walking surface is halfway up its cell and the lower half really is
        air. Exempting both end blocks wholesale, as this used to, made the one
        check that would have caught a hop leaving a wide platform too flat
        blind to it by construction.
        """
        dur, vy0 = flight(frm, to)
        if dur <= 0.0:
            return False
        n = _samples(frm, to)
        for i in range(1, n):
            f = i / n
            t = dur * f
            x = frm[0] + (to[0] - frm[0]) * f
            z = frm[2] + (to[2] - frm[2]) * f
            y = frm[1] + vy0 * t - 0.5 * GRAVITY * t * t
            for cell in self._body_cells(x, y, z):
                if cell in self._solid and cell not in exempt:
                    return False
        return True

    # -- generation: placement --------------------------------------------

    def _spawn_block(self, first: bool = False) -> None:
        if first:
            blk = {
                "x": 0, "y": COURSE_ALT, "z": 0,
                "style": "candy0", "form": "wide", "yaw": 0.0, "born": -1e9,
                "step": (0, -1), "deco": [], "orbs": [], "segment": "start"}
            self.blocks.append(blk)
            self._solid.update(self._cells_of(blk))
            return
        self.laid += 1
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
        # segment asked for a specific turn. A held direction bends the course;
        # ``self.steer`` is zero on autopilot, so this term does nothing until
        # somebody is driving.
        hand = self.steer * STEER
        if node["turn"] is None:
            drift = rng.gauss(0.0, 0.55)
            # Back toward the spine -- but mostly out of the way while
            # someone is steering, or the two cancel and holding a direction
            # buys a couple of metres and then nothing.
            home = -0.028 * prev["x"] * (1.0 - 0.85 * abs(self.steer))
            want = max(-0.9, min(0.9, self.heading + drift * 0.22 + home + hand))
        else:
            want = self.heading + node["turn"] + hand * 0.6
            # A set-piece that only asks for a small bend each block is doing a
            # random walk in heading, and a random walk does not come back --
            # so a pillar run or a ruined wall would curl steadily away and
            # spend its second half leaving the frame. The ones that turn on
            # purpose are exempt: a spiral that gets pulled straight is not a
            # spiral.
            if self.segment not in TURNERS:
                want -= 0.20 * self.heading
            want = max(-1.1, min(1.1, want))

        form = node["form"]
        # Every set-piece's gap is reconciled with its rise here rather than in
        # nine separate places. A staircase asking for a one-block gap while
        # climbing is asking for a hop no body can make -- there is not enough
        # ground to cover before the arc comes back down -- and what used to
        # happen was that placement rejected every candidate and fell through
        # to its emergency answer, which is how a flight of stairs ended up
        # stacked almost vertically.
        gap = fit_gap(node["gap"], rise)
        (sx, sz), rise = self._choose_cell(prev, gap, rise, want, form)
        heading = math.atan2(sx, -sz)
        self.heading = heading

        blk = {
            "x": prev["x"] + sx,
            "y": prev["y"] + rise,
            "z": prev["z"] + sz,
            "born": self.elapsed,
            "style": node["style"],
            "form": form,
            "yaw": heading,
            #: The integer offset that arrived here. Which way the block faces,
            #: which side its decorations go, and where the player plants their
            #: feet all come off this -- and being integer is what keeps every
            #: one of those on the lattice too.
            "step": (sx, sz),
            "deco": [],
            "orbs": [],
            "segment": self.segment,
            "deco_style": node["deco_style"],
        }
        # Prev's take-off is only decided once we know where the course goes
        # next, so it is written here rather than when prev was laid down --
        # and only now can its own scenery be checked against the run across it
        # and the hop out of it, neither of which existed when it was built.
        # Both ends of the hop are stored rather than recomputed, because
        # ``_hop_points`` moves them off the edges to keep the arc a full jump
        # and every later reader -- the orbs, the clearance, the run-up, the
        # live take-off -- has to be looking at the same two points.
        prev["out"] = (sx, sz)
        prev["launch"], blk["land"] = _hop_points(
            prev, self._land_point(prev), (sx, sz), form,
            blk["x"], self.surface(blk), blk["z"])
        self._clear_deco_path(prev, self._land_point(blk))
        arc = _arc_points(self._takeoff_point(prev), self._land_point(blk))
        if node["deco"]:
            blk["deco"] = self._deco_cubes(node["deco"], blk, rng, arc)
        self.blocks.append(blk)
        self._solid.update(self._cells_of(blk))
        if node["orbs"]:
            self._hang_orbs(prev, blk, node["orbs"])

    def _choose_cell(self, prev: dict, gap: int, rise: int, want: float,
                     form: str):
        """Pick the integer offset the next block sits at.

        Four things have to be true at once and none of them is negotiable:
        the block's own cells are empty, the two cells above the landing are
        empty (a body is 1.8 m tall and has to fit somewhere), the hop is one
        a body can actually make, and the arc does not pass through anything.
        Candidates are tried in order of how close they are to the heading and
        gap the set-piece asked for, so the first that satisfies all four is
        also the nearest thing to what was wanted -- solvability by
        construction, rather than by generating and then checking.
        """
        # Rises are tried in the order that least disturbs the set-piece: what
        # it asked for first, then a block either side of it -- and each is
        # given the gap *it* needs, since a rise the caller did not ask for
        # changes what a body can reach.
        for strict in (True, False):
            for r in (rise, rise - 1, rise + 1, rise - 2, rise + 2):
                if not COURSE_ALT - BAND <= prev["y"] + r <= COURSE_ALT + BAND:
                    continue
                for sx, sz in _offsets(want, fit_gap(gap, r) + 1):
                    if self._fits(prev, sx, sz, r, form, strict):
                        return (sx, sz), r
        # Still nothing, so stop trying to honour the set-piece and start
        # trying to leave. A wider gap has strictly more cells to land in and a
        # drop buys reach, so widening and descending is the direction that
        # always has more room in it -- and it is far better to give up the
        # shape of one hop than to lay one the body cannot fly.
        for strict in (True, False):
            for g in range(gap, 7):
                for r in (0, -1, -2, -3):
                    if prev["y"] + r < COURSE_ALT - BAND:
                        continue
                    for sx, sz in _offsets(want, fit_gap(g, r) + 1):
                        if self._fits(prev, sx, sz, r, form, strict):
                            return (sx, sz), r
        self.stuck += 1
        # Nothing worked, which means the course has boxed itself in. Step up
        # and out: the cells above a landing are kept clear for the player's
        # own head, so there is always somewhere up there, and a body can
        # always jump one block. Better a dull hop than a generator that
        # cannot return -- this runs inside the frame loop. It is counted, and
        # the generation tests assert it stays at zero across many runs: a
        # course that reaches this often is a course laying hops nobody can
        # make, and the only visible symptom is a set-piece that looks wrong.
        return _offsets(want, 3)[0], 0

    def _fits(self, prev: dict, sx: int, sz: int, rise: int, form: str,
              strict: bool) -> bool:
        bx, by, bz = prev["x"] + sx, prev["y"] + rise, prev["z"] + sz
        sp = SPREAD.get(form, 0)
        cells = [(bx + ox, by, bz + oz)
                 for ox in range(-sp, sp + 1) for oz in range(-sp, sp + 1)]
        if not self._free(cells):
            return False
        # Headroom over every cell of the landing: you have to be able to
        # stand there. Without this the generator will happily tuck a landing
        # under an arch it laid down three blocks ago.
        if not self._free((cx, cy + h, cz)
                          for cx, cy, cz in cells
                          for h in range(1, HEADROOM + 1)):
            return False
        frm, to = _hop_points(prev, self._land_point(prev), (sx, sz), form,
                              bx, by + FORMS[form], bz)
        d = math.dist((frm[0], frm[2]), (to[0], to[2]))
        if d < MIN_HOP:
            return False
        dur, vy0 = flight(frm, to)
        if not (VY_MIN <= vy0 <= VY_MAX and AIR_MIN <= dur <= AIR_MAX):
            return False
        # ...and it has to be a *jump*. ``hop_span`` keeps the gap tables
        # honest, but the lattice answers a three-cell request with anything
        # from 2.4 to 4.3 cells, so the floor is asked for again here against
        # the two points the body will actually use. A landing the arc reaches
        # without spending the impulse is the skip this scene was sent back
        # for; the candidate is refused and the next one along is nearly
        # always a cell further out.
        if d + 1e-6 < hop_span(by + FORMS[form] - frm[1])[0]:
            return False
        # You have to be on the way *down* when you arrive. A hop that is still
        # rising as it reaches its target has come up through the side of it --
        # which is what a short jump onto a higher block is, and it was putting
        # the camera inside a staircase for a frame or two on every flight.
        if dur < vy0 / GRAVITY:
            return False
        if not strict:
            return True
        return self._arc_is_clear(frm, to, _standing_cells(prev, prev["y"])
                                  | _standing_cells({"form": form}, by, cells))

    def _deco_cubes(self, kind: str, blk: dict, rng, arc) -> list[dict]:
        """Expand a decoration into boxes, one per cell of the lattice.

        Two rules keep the whole scene on the grid. First, a decoration's
        offsets are whole cells, rotated into the *quantised* heading -- one of
        the eight lattice directions -- rather than into the exact float angle
        the course happens to be running at. A gate still faces the way you run
        through it; it just cannot land its jamb three-fifths of the way into
        a cell any more. Second, sub-block furniture (posts, rails, torches) is
        centred inside its cell exactly as vanilla's is, so a fence occupies a
        block without filling it.

        Anything that would land in a cell already taken is dropped rather than
        drawn: decoration is scenery, and one missing lantern is invisible
        where a lantern buried in a wall is not.
        """
        fx, fz = _quantise(blk["step"])          # forward, on the lattice
        rx, rz = -fz, fx                         # and ninety degrees off it
        # What the structure under a block is made of, which is not always what
        # the block is made of: a coloured cap standing on a stone column is
        # the shape a vanilla parkour map is built in, and a column in the same
        # colour as its cap is one smear from the sea to the sky.
        under = blk.get("deco_style") or blk["style"]

        def local(side: int, fwd: int, dy: float, sx: float, sy: float,
                  sz: float, style: str, glow: bool = False,
                  loose: bool = False, born: float = -1e9,
                  bias: float = 1.0) -> dict:
            """``bias`` pushes sub-block furniture out within its own cell.

            The cell it belongs to is still ``side``/``fwd``, so occupancy and
            the drawing agree; the piece just sits toward that cell's outer
            face the way a fence rail or a wall torch does, which is both what
            the game looks like and how far it has to be from the line the
            player runs along.
            """
            return {"dx": (side * rx + fwd * fx) * bias,
                    "dz": (side * rz + fwd * fz) * bias,
                    "dy": dy, "sx": sx, "sy": sy, "sz": sz,
                    # What this piece is, kept on the piece. Decoration used to
                    # be anonymous once expanded, which made "does the squeeze
                    # actually build any beams" a question nothing could ask --
                    # and a set-piece whose scenery is silently dropped by the
                    # path checks looks exactly like one that works.
                    "kind": kind,
                    "style": style, "glow": glow, "loose": loose, "born": born}

        out: list[dict] = []
        if kind == "pillar":
            out = [local(0, 0, -1 - i, 1.0, 1.0, 1.0, under)
                   for i in range(rng.randint(3, 6))]
        elif kind == "shaft":
            # Deeper than a pillar and tapering, so it reads as something
            # standing in the sea rather than as a stub hung under a block.
            depth = rng.randint(7, 12)
            out = [local(0, 0, -1 - i, 1.0 if i < 2 else 0.86,
                         1.0, 1.0 if i < 2 else 0.86, under)
                   for i in range(depth)]
        elif kind == "buttress":
            side = rng.choice((-1, 1))
            out = [local(0, 0, -1 - i, 1.0, 1.0, 1.0, under)
                   for i in range(rng.randint(2, 4))]
            out.append(local(side, 0, -1, 1.0, 1.0, 1.0, under))
        elif kind == "arch":
            # A lintel three cells up: high enough to run under, low enough to
            # frame the shot. What is left of a wall reads as a wall.
            for side in (-1, 1):
                out.append(local(side, 0, HEADROOM + 1, 1.0, 1.0, 1.0,
                                 under))
            out.append(local(0, 0, HEADROOM + 1, 1.0, 1.0, 1.0, under))
        elif kind in ("lanterns", "posts"):
            # Out into the *corners* of the platform's corner cells, not their
            # middles. The feet plant 1.3 m from a wide platform's centre, and
            # on a course running diagonally that lands them within a hand's
            # breadth of a post sitting at the middle of the corner cell --
            # which is where the body was found standing inside the scenery.
            #
            # In *world* cells, not rotated ones, and that is a fix rather
            # than a shortcut: a three-by-three platform occupies the cells
            # -1..1 whichever way the course runs through it, so a corner
            # taken as ``side`` across plus ``fwd`` along lands two cells out
            # on a diagonal heading -- off the platform entirely, and 2.6 m
            # out once the bias is on it. That is a whole cell past the
            # footprint, and with the course now laying three- and four-cell
            # steps it reaches into the *next block*: two posts a sweep were
            # measured standing 0.21 m inside one.
            lit = kind == "lanterns"
            for cx in (-1, 1):
                for cz in (-1, 1):
                    def corner(dy: float, sx: float, sy: float, sz: float,
                               style: str, glow: bool = False,
                               _cx=cx, _cz=cz) -> dict:
                        return {"dx": _cx * CORNER, "dz": _cz * CORNER,
                                "dy": dy, "sx": sx, "sy": sy, "sz": sz,
                                "kind": kind, "style": style, "glow": glow,
                                "loose": False, "born": -1e9}

                    out.append(corner(1, 0.22, 1.0, 0.22, "wood"))
                    if lit:
                        # sitting ON the post, not sunk into it: at 1.7 the
                        # lantern ate the top 0.3 m of the post it stood on
                        out.append(corner(2, 0.34, 0.34, 0.34, "lantern",
                                          glow=True))
                    else:
                        # a fence cap, not a grey knob: a stone cube on a wood
                        # post reads as a mushroom from every angle
                        out.append(corner(2, 0.4, 0.16, 0.4, "wood"))
        elif kind == "torch":
            # A wall torch on the side of the block, which is where a torch
            # goes in the game. On *top* it cannot go: the body crosses the
            # block within a third of a metre of its centre line, and a
            # 1 x 1 block has nowhere on it that is far enough from that.
            side = rng.choice((-1, 1))
            out = [local(side, 0, 0.55, 0.12, 0.55, 0.12, "wood", bias=FLANK),
                   local(side, 0, 1.10, 0.2, 0.2, 0.2, "lantern", glow=True,
                         bias=FLANK)]
        elif kind == "rail":
            out = [local(side, 0, 1, 0.16, 0.62, 0.16, "wood", bias=FLANK)
                   for side in (-1, 1)]
        elif kind == "gate":
            # Light jambs, a dark lintel, a lantern hung in the opening. Built
            # the other way round -- dark posts under a pale beam -- it read as
            # a wall with a hole rather than as a doorway.
            for side in (-2, 2):
                for i in range(HEADROOM + 1):
                    out.append(local(side, 0, 1 + i, 1.0, 1.0, 1.0, "quartz"))
            for side in (-2, -1, 0, 1, 2):
                out.append(local(side, 0, HEADROOM + 2, 1.0, 0.7, 1.0, "stone"))
            out.append(local(0, 0, HEADROOM + 1, 0.34, 0.34, 0.34, "lantern",
                             glow=True))
            out[-1]["dy"] = HEADROOM + 1.6       # hung from the beam
        elif kind in ("lintel", "hurdle"):
            out = _span_piece(kind, blk, arc, local, under)
        elif kind == "crumb":
            # A loose block beside the path, there to be broken as you land.
            # Sits on the floor of its cell rather than floating a little way
            # up it: a crumb counts as solid for occupancy, so an offset that
            # is not a whole number of cells puts the drawn block and the cell
            # it reserves in slightly different places.
            out = [local(rng.choice((-1, 1)), rng.choice((-1, 0, 1)), 0,
                         0.7, 0.7, 0.7, rng.choice(self.candy), loose=True)]

        # Drop anything that would share a cell with the course, with the block
        # it decorates, or with another part of itself -- and anything standing
        # in the arc that arrives here. That last one is not a nicety: a block
        # is placed before its decoration exists, so the hop onto it was
        # cleared against a cell an arch had not been built in yet, and the
        # body flew through the arch on every ruin the generator laid.
        own = set(self._cells_of(blk))
        # Whole cells stop whole cubes running into each other; furniture is
        # smaller than a cell and needs its actual box compared. A lantern
        # standing on a post is two boxes an inch apart by design, and getting
        # that inch wrong is invisible in the code and obvious on screen.
        near = [_deco_box(b, d) for b in self.blocks[-3:] for d in b["deco"]]
        keep = []
        for d in out:
            solid = d["sx"] > 0.5 and d["sz"] > 0.5
            cell = (blk["x"] + _round(d["dx"]), blk["y"] + _round(d["dy"]),
                    blk["z"] + _round(d["dz"]))
            if solid and (cell in self._solid or cell in own):
                continue
            if _in_the_way(blk, d, arc):
                continue
            box = _deco_box(blk, d)
            if any(box.penetration(other) > 1e-4 for other in near):
                continue
            if solid:
                own.add(cell)
            near.append(box)
            keep.append(d)
        return keep

    def _clear_deco_path(self, blk: dict, landing) -> None:
        """Take away anything on ``blk`` that the player is about to run into.

        Called once, at the moment the course commits to where it goes next.
        Up to here a block's scenery has only ever been checked against the hop
        that *arrives*; the run across the block and the hop that leaves it are
        both decided later, and a fence post standing on the line of either is
        a post the camera walks through. Nothing here is load-bearing, so the
        answer is always to remove the furniture rather than move the player.
        """
        if not blk["deco"]:
            return
        path = (_line_points(self._land_point(blk), self._takeoff_point(blk))
                + _arc_points(self._takeoff_point(blk), landing))
        keep = [d for d in blk["deco"] if not _in_the_way(blk, d, path)]
        if len(keep) != len(blk["deco"]):
            blk["deco"] = keep
            self._rebuild_solid()

    def _hang_orbs(self, prev: dict, blk: dict, count: int) -> None:
        """Put pickups on the flight path from ``prev`` to ``blk``.

        Not near it: on it. The take-off and landing points are both already
        decided, so the arc is known exactly, and an orb placed at the chest
        height of the body that will fly through cannot be missed. That makes
        "every orb laid down is collected" a property of generation rather
        than a hope, which is what the test asserts.
        """
        frm = self._takeoff_point(prev)
        to = self._land_point(blk)
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
        """The middle of a block's walking surface -- what to aim at."""
        return (blk["x"], self.surface(blk), blk["z"])

    def _land_point(self, blk: dict) -> tuple[float, float, float]:
        """Where the feet touch down.

        A player does not arrive in the middle of a block and stop. They catch
        the near edge and carry on across it, and the gap they actually cleared
        is therefore wider than the gap between the two block centres by the
        width of two edges. Making this the landing point rather than a random
        offset is what gives every block a run-up to take off from.

        The near edge is the *nominal* point and what a max-length jump gets;
        a shorter gap lands further in, because that is how a player at sprint
        pace answers one. :func:`_hop_points` decides how much further and
        writes it here when the block is laid.
        """
        got = blk.get("land")
        if got is not None:
            return got
        return _land_of(blk["x"], self.surface(blk), blk["z"],
                        blk["form"], blk["step"])

    def _takeoff_point(self, blk: dict) -> tuple[float, float, float]:
        """Where the feet leave: the far edge, on the way out, less whatever
        the hop out of here needed to leave early for.

        Falls back to the incoming direction when nothing has been generated
        beyond this block yet, which only happens for the very last block of
        the live course and is corrected the moment the next one is laid.
        """
        got = blk.get("launch")
        if got is not None:
            return got
        return _takeoff_of(blk, blk.get("out") or blk["step"])

    def body_box(self) -> AABB:
        """The player's volume right now, feet at :attr:`pos`."""
        return AABB.around(self.pos[0], self.pos[1], self.pos[2],
                           BODY_HALF_W, BODY_H, BODY_HALF_W)

    def orb_hover(self) -> float:
        """How far an orb is bobbing above its hung position this frame."""
        return math.sin(self.elapsed * 3.4) * 0.08

    def orb_spin(self) -> float:
        return (self.elapsed * 150.0) % 360.0

    def orb_box(self, orb: dict) -> AABB:
        """An orb's hitbox, from the model that draws it and the transform it
        is drawn with -- the same rule the runner's obstacles follow.

        Including the bob and the spin, which it did not: an orb is drawn eight
        centimetres above or below where its box sat, and drawn turning, so the
        box was neither where the orb was nor the shape of it. It never changed
        an outcome, because the pickup reaches most of a metre and the error is
        under a tenth of one -- but a hitbox that is *nearly* the drawn object
        is exactly the kind of thing this project has a rule against, and the
        test that guards it was checking this method against itself.
        """
        return placed(model_aabb(self._model("orb")),
                      (orb["x"], orb["y"] + self.orb_hover(), orb["z"]),
                      yaw_deg=self.orb_spin(),
                      scale=(ORB_SCALE, ORB_SCALE, ORB_SCALE))

    # -- the world below ---------------------------------------------------

    def _spawn_island(self) -> None:
        """A wooded island: mound, shore, trees, and sometimes a ruin, a
        waterfall or a sea stack.

        Bigger and closer together than they were, because the camera sits
        nearly sixty metres above them and looks slightly down: at the old size
        and spacing they were specks and the lower two thirds of every frame
        was flat blue. All of it is cheap -- the fog eats most of it -- and all
        of it is what stops the ocean reading as a painted floor.
        """
        rng = self.irng
        z = self._next_island_z - rng.uniform(30, 62)
        self._next_island_z = z
        cx = rng.gauss(0.0, 26.0)      # hug the spine: vertigo needs land under
        base = rng.uniform(10, 20)
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

        # A sea stack: a stepped column climbing a third of the way to the
        # course. Everything else down there is flat enough to read as a map
        # rather than as a place, and there is no sense of the drop at all
        # without something standing in it that the eye can measure against.
        # It is also the most expensive thing on an island, so it is the first
        # thing the lower quality settings stop drawing.
        if rng.random() < 0.45 * self.detail:
            sx_, sz_ = rng.uniform(-base, base), rng.uniform(-base, base)
            height = rng.uniform(14, 30)
            steps = int(height / 3.5) + 1
            for k in range(steps):
                w = rng.uniform(3.0, 6.5) * (1.0 - 0.55 * k / steps)
                cubes.append({"dx": sx_ + rng.uniform(-1.2, 1.2),
                              "dz": sz_ + rng.uniform(-1.2, 1.2),
                              "y": 1.0 + k * (height / steps),
                              "sx": w, "sy": height / steps + 1.2, "sz": w,
                              "style": "stone" if k < steps - 1 else "grass"})
        waterfall = None
        if rng.random() < 0.3:
            wx, wz = rng.uniform(-base, base), rng.uniform(-base, base)
            waterfall = {"dx": wx, "dz": wz, "h": top}

        self.islands.append({"x": cx, "z": z, "cubes": cubes, "biome": biome,
                             "reef": base * 2.6, "waterfall": waterfall})

    # -- simulation -------------------------------------------------------

    def _begin_air(self) -> None:
        """Leave the block from wherever the feet have got to.

        The arc is re-solved here rather than read off generation, because a
        player can jump early and that genuinely changes where the take-off is.
        The orbs strung on this hop are moved onto the arc that is actually
        about to be flown, which is what keeps "every orb laid down is
        collected" true whether or not somebody is driving. On autopilot the
        two are the same numbers and nothing moves.
        """
        target = self.blocks[self.jump_index + 1]
        self.takeoff = list(self.pos)
        self.land_at = list(self._land_point(target))
        self.air_dur, self.vy0 = flight(self.takeoff, self.land_at)
        self.air_speed = math.dist((self.takeoff[0], self.takeoff[2]),
                                   (self.land_at[0], self.land_at[2])) \
            / self.air_dur
        self._rehang(target)
        self.phase = "air"
        self.phase_t = 0.0
        self.vy = self.vy0
        self._speed = AIR_SPEED
        # A new heading is committed the instant the feet leave: the look
        # toward it is a flick, not a drift.
        self._flick = 1.0
        # Leaving the block is when the hand does something other than bob.
        if self.hop_rng.random() < 0.35:
            self.mine = 1.0

    def _rehang(self, blk: dict) -> None:
        """Re-place this hop's orbs onto the arc that is about to be flown."""
        orbs = [o for o in blk["orbs"] if not o["taken"]]
        spread = ORB_FRACTIONS.get(len(orbs))
        if spread is None:
            return
        frm, to, dur, vy0 = self.takeoff, self.land_at, self.air_dur, self.vy0
        for orb, f in zip(orbs, spread):
            t = dur * f
            orb["x"] = frm[0] + (to[0] - frm[0]) * f
            orb["y"] = frm[1] + vy0 * t - 0.5 * GRAVITY * t * t + CHEST
            orb["z"] = frm[2] + (to[2] - frm[2]) * f

    def _land(self) -> None:
        self.jump_index += 1
        self.landings += 1
        #: Height of the surface just landed on. A landing can be over inside
        #: one frame, so a probe that reads the body's height afterwards reads
        #: it already airborne; this is the number it wanted.
        self.land_y = self.land_at[1]
        self.stand = list(self.land_at)
        self.pos = list(self.stand)
        self.phase = "ground"
        self.phase_t = 0.0
        # The eye carries the body's downward speed into the legs rather than
        # being dropped a fixed distance -- but only the part of it that is
        # more than an ordinary jump arrives with. Every hop lands at about
        # the impulse it left with, so a dip taken off the raw speed fired on
        # every single landing, twice a second, and vanilla dips the lens on
        # none of them. Above that it is a *fall*, and a fall is exactly when
        # a person's legs give: the dip now says how far you dropped rather
        # than that you landed. Capped, and only ever added to what the spring
        # is already doing, so two landings close together do not cancel.
        self.dip_v = max(self.dip_v, DIP_KEEP * (
            DIP_BASE + min(DIP_CAP, max(0.0, abs(self.vy) - DIP_FREE))))
        self.vy = 0.0
        self._speed = RUN_SPEED
        self.swing = 1.0
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
            # A crumb is a whole cube, so it holds a cell. Breaking it has to
            # give the cell back: the occupancy map is only ever rebuilt from
            # the live course when blocks drop off the back, so until then the
            # generator would keep refusing to place anything where a block the
            # player already smashed used to be.
            self._solid.discard((landed_on["x"] + _round(crumb["dx"]),
                                 landed_on["y"] + _round(crumb["dy"]),
                                 landed_on["z"] + _round(crumb["dz"])))
            self.burst.spawn(landed_on["x"] + crumb["dx"],
                             landed_on["y"] + crumb["dy"] + 0.4,
                             landed_on["z"] + crumb["dz"],
                             self._colour(crumb["style"]), count=12, speed=2.4,
                             rng=self.hop_rng)
            self.mine = 1.0

        # A breather is long enough to do something with your hands. Carrying a
        # block, you put one down -- and it is still there behind you, because
        # a placement that leaves nothing behind is an animation, not an act.
        wide = landed_on["form"] == "wide"
        if wide and self.hop_rng.random() < 0.7:
            if self.kit["name"] == "block":
                self._place_block(landed_on)
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
            # Cells behind the player are released here and nowhere else. An
            # occupancy map that only ever grows would refuse the whole world
            # after a few hundred blocks; one rebuilt from the live course
            # cannot go stale in either direction.
            self._rebuild_solid()
        self._begin_ground(self.blocks[self.jump_index])
        z_here = self.stand[2]
        if self.islands and self.islands[0]["z"] > z_here + 90:
            self.islands.pop(0)
        while self._next_island_z > z_here - 260:
            self._spawn_island()

    def _place_block(self, blk: dict) -> None:
        """Put a block down beside you, on the platform you have landed on.

        The cell has to be empty *and* out of the way, and the second half is
        the one that bit. Generated decoration goes through the path check in
        :meth:`_clear_deco_path`; this is placed live, mid-run, and only ever
        checked the occupancy map -- so on a platform where the course *turns*,
        where the line from the landing edge to the take-off edge does not pass
        through the middle, the block was put down exactly where the player was
        about to walk. It is the same test either way; there is no reason for
        this to be the one placement that skips it.
        """
        fx, fz = _quantise(blk["step"])
        takeoff = self._takeoff_point(blk)
        path = _line_points(self._land_point(blk), takeoff)
        nxt = self.blocks[self.jump_index + 1] if \
            self.jump_index + 1 < len(self.blocks) else None
        if nxt is not None:
            path += _arc_points(takeoff, self._land_point(nxt))
        for side in self.hop_rng.sample((-1, 1), 2):
            deco = {"dx": -side * fz, "dz": side * fx, "kind": "placed",
                    "dy": 1, "sx": 1.0, "sy": 1.0, "sz": 1.0,
                    "style": self.kit["parts"][0]["style"],
                    "glow": False, "loose": False,
                    # dated forward: it arrives as the hand reaches out
                    "born": self.elapsed + 0.18}
            cell = (blk["x"] + deco["dx"], blk["y"] + 1, blk["z"] + deco["dz"])
            if cell in self._solid or _in_the_way(blk, deco, path):
                continue
            self._solid.add(cell)
            blk["deco"].append(deco)
            self.place = 1.0
            return
        # Nowhere to put it. Swing at the block instead -- doing nothing at all
        # with your hands on a breather is the tell that nobody is holding them.
        self.mine = 1.0

    def _begin_ground(self, blk: dict) -> None:
        """Set up the run across the block just landed on.

        This is the whole of the fix for the scene reading as scripted. What
        used to happen here was a stopwatch: the body was pinned to one point
        for somewhere between a tenth of a second and nine tenths, and then
        teleported onto an arc. Measured over three minutes of running, the
        player was stationary for thirty per cent of every frame drawn.

        What happens now is that the feet keep going. The landing was on the
        near edge, the take-off is from the far one, and the time between them
        is not a number anybody chose -- it is that distance at running pace.
        A wide platform is still a breather, because crossing three blocks
        takes half a second; it is just a breather you spend moving.

        And it is crossed at a *profile* rather than at a constant, which is
        the second half of the same idea and was missing until the owner named
        what was left: the body arrived at the arc's speed, dropped to sprint
        pace for a tenth of a second, and jumped back up to the arc's speed
        again. Two steps of a metre and a half a second, four times a second,
        which reads from inside the head as sticking to each block on the way
        past. :class:`GroundRun` brakes and accelerates instead, so the speed
        is the same number either side of every landing and every take-off.
        """
        self.run_from = list(self.stand)
        self.run_to = list(self._takeoff_point(blk))
        self.run_len = math.dist((self.run_from[0], self.run_from[2]),
                                 (self.run_to[0], self.run_to[2]))
        self.run_s = 0.0
        self.ground_speed = self.hold_speed or RUN_SPEED
        # Both ends are known: the hop just flown ran at one speed the whole
        # way, and the next one is solved here against the take-off point the
        # autopilot is heading for. An early take-off moves that point a
        # little and the profile is a metre or two a second out for the last
        # frame of the crossing, which is a hundredth of what it was worth
        # getting right.
        nxt = self.blocks[min(self.jump_index + 1, len(self.blocks) - 1)]
        self.run = GroundRun(self.run_len, self.air_speed,
                             flight_speed(self.run_to, self._land_point(nxt)),
                             self.ground_speed)
        self.ground_dur = max(GROUND_MIN, self.run.dur)

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
            # Leave now, from wherever the feet have got to. The arc is solved
            # against the real take-off point in :meth:`_begin_air`, so an early
            # jump is a shorter run-up and a different hop -- not the same hop
            # started sooner.
            #
            # Expressed as "the block ends here" and not as "the clock ran
            # out", because the crossing is a distance covered at a speed and
            # the clock is a consequence of it rather than the other way
            # round.
            self.run_len = self.run_s
            self.ground_dur = min(self.ground_dur, self.phase_t)
        elif intent.duck:
            # Vanilla's own answer to "hold this block": walk it instead of
            # sprinting it. Crossing takes longer because you are slower, which
            # is a thing a body does; stretching the clock while the position
            # was read off that clock was not.
            self._hold(WALK_SPEED)
        elif self.hold_speed:
            self._hold(0.0)

    def _hold(self, cruise: float) -> None:
        """Re-cruise the crossing in progress, without moving the body.

        The profile is a function of where along the block the feet are, so
        rebuilding it mid-crossing changes the speed from here on and nothing
        else -- which is what pressing and releasing a key ought to do.
        """
        if cruise == self.hold_speed:
            return
        self.hold_speed = cruise
        self.ground_speed = cruise or RUN_SPEED
        self.run = GroundRun(self.run_len, AIR_SPEED, AIR_SPEED,
                             self.ground_speed)
        self.ground_dur = max(GROUND_MIN, self.run.dur)

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
        # Orbs on the discarded tail were never in play -- the player has not
        # reached that stretch and now never will, because it no longer exists.
        # They are counted separately rather than as misses, because a miss is
        # supposed to mean "ran past one and did not take it", which is the
        # thing :attr:`orbs_missed` is asserted to be zero. Without this
        # distinction a steered run can pass that assertion by deleting
        # everything it would otherwise have had to collect.
        for blk in self.blocks[keep + 1:]:
            self.orbs_discarded += sum(1 for o in blk["orbs"] if not o["taken"])
        del self.blocks[keep + 1:]
        self._pending.clear()
        self.blocks[-1].pop("out", None)
        # The discarded tail's cells have to go with it, or a steered course
        # spends the rest of the run refusing to be laid through the ghost of
        # the one it replaced.
        self._rebuild_solid()
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
                self.combo_t = COMBO_HOLD
                self.burst.spawn(orb["x"], orb["y"], orb["z"], ORB_COLOR,
                                 count=9, speed=2.2, rng=self.hop_rng)

    def _step_ground(self, dt: float) -> float:
        """Run some of the way across the block. Returns the time it took.

        Advanced by *distance covered at a speed*, never by a fraction of the
        phase's duration. That distinction is the whole of it: the duration is
        something a player can change mid-phase (jump ends it early, holding
        the block stretches it), and a position interpolated against a
        duration that moves underneath it moves with it. Jump used to snap the
        feet to the far edge in a single frame -- three and a half metres, two
        hundred metres a second -- and holding the block dragged the body
        *backwards* across it, because the denominator grew faster than the
        numerator.
        """
        remain = self.run_len - self.run_s
        if remain <= 1e-6:
            self._begin_air()
            return 0.0
        v = self.run.speed_at(self.run_s)
        step = v * dt
        used = dt
        if step >= remain:
            # The block runs out part way through the frame. Take only the
            # time that actually crossed it and hand the rest back, or the
            # body spends the remainder of the frame standing on the far edge
            # -- a fraction of a frame at nearly zero speed, twice per landing,
            # four landings a second. That stall is small enough to be
            # invisible frame by frame and is exactly what a run of them reads
            # as.
            used = min(dt, remain / v)
            step = remain
        self.run_s += step
        f = self.run_s / self.run_len
        self.pos[0] = self.run_from[0] + (self.run_to[0] - self.run_from[0]) * f
        self.pos[1] = self.run_from[1]
        self.pos[2] = self.run_from[2] + (self.run_to[2] - self.run_from[2]) * f
        self.vy = 0.0
        self.phase_t += used
        self.stride += step
        if self.run_s >= self.run_len - 1e-9:
            self._begin_air()
        return used

    def _step_air(self, dt: float) -> float:
        """Fly some of the arc. Returns the time it took."""
        remain = self.air_dur - self.phase_t
        if remain <= 1e-9:
            self._land()
            return 0.0
        used = min(dt, remain)
        t = self.phase_t + used
        f = t / self.air_dur
        self.pos[0] = self.takeoff[0] + (self.land_at[0] - self.takeoff[0]) * f
        self.pos[2] = self.takeoff[2] + (self.land_at[2] - self.takeoff[2]) * f
        self.pos[1] = self.takeoff[1] + self.vy0 * t - 0.5 * GRAVITY * t * t
        self.vy = self.vy0 - GRAVITY * t
        self.phase_t = t
        if self.phase_t >= self.air_dur - 1e-9:
            self._land()
        return used

    def update(self, dt: float) -> None:
        was = (self.pos[0], self.pos[2])
        # A frame is spent across as many phases as it reaches into. A landing
        # or a take-off almost never falls on a frame boundary, and the old
        # loop threw the remainder of the frame away at every one of them.
        left = dt
        for _ in range(8):
            if left <= 1e-9:
                break
            left -= (self._step_ground(left) if self.phase == "ground"
                     else self._step_air(left))

        moved = math.dist(was, (self.pos[0], self.pos[2]))
        self._speed = moved / dt if dt > 0.0 else 0.0

        # Recycling a cloud shelf that has drifted behind the camera belongs
        # here and not in the draw, however naturally it falls out of the loop
        # that draws them. Drawing a frame twice has to draw the same frame
        # twice -- every screenshot this scene is judged from is captured by
        # presenting one a second time.
        for s in self.shelves:
            if s["z"] > self.pos[2] + 60:
                s["z"] -= 300

        self._collect()
        self._look(dt)
        self.driven_t = max(0.0, self.driven_t - dt)
        if not self.driven:
            self.steer = 0.0
            if self.hold_speed and self.phase == "ground":
                self._hold(0.0)
        self._settle(dt)
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
        self._draw_reefs(x, z)
        self._draw_islands(x, z)
        self._draw_shelves(x, z)
        rl.EndMode3D()

        self._draw_haze(pal)
        rl.BeginMode3D(cam[0])

        self._draw_course(x, z)
        self._draw_orbs(x, z)
        self.burst.draw(self.camera)
        self._draw_held()
        # Every glow in the frame goes down here, in one pass, after all the
        # opaque geometry -- see :meth:`_draw_glows`. The held item still wins
        # against them without needing a pass of its own: it is the nearest
        # thing in the frame and the depth *test* is still on.
        self._draw_glows()
        rl.EndMode3D()

        self.weather.draw(self.elapsed)
        self._draw_crosshair()
        self._draw_hud()

    def _settle(self, dt: float) -> None:
        """Advance everything the camera rides on that is not a position.

        Three springs and an ease, and all four exist for the same reason:
        each of them used to be a value switched between two constants at a
        phase boundary, and a whole-frame step in the eye, the lens or the bob
        is read as a jolt however correct the frames either side of it are.
        """
        # A damped spring, integrated semi-implicitly so a stiff one cannot
        # wind itself up at a long frame.
        acc = -DIP_W * DIP_W * self.dip - 2.0 * DIP_ZETA * DIP_W * self.dip_v
        self.dip_v += acc * dt
        self.dip += self.dip_v * dt
        want_foot = 1.0 if self.phase == "ground" else 0.0
        self.foot += (want_foot - self.foot) * min(1.0, dt * FOOT_EASE)
        # The neck: a first-order lag on the eye's height, and the only reason
        # it is not a spring is that a spring stiff enough to keep up here
        # sits at the frequency a run of hops arrives at and would *amplify*
        # what it is meant to take off.
        # Off the *state*, not off the instantaneous speed. Vanilla's sprint
        # boost is a flag: it comes on when you sprint and stays there. Hung
        # off the speed it became a pulse instead, because the body genuinely
        # is faster in the air than across a block -- two degrees in and out
        # twice a second, a lens breathing in step with the jumps, and a good
        # part of what "it bounces" was.
        cruise = self.hold_speed or AIR_SPEED
        want_fov = FOV + FOV_GAIN * max(0.0, cruise - RUN_SPEED)
        self.fov += (want_fov - self.fov) * min(1.0, dt * FOV_EASE)

    def _look(self, dt: float) -> None:
        """Turn the head toward where the run is going.

        Lives in ``update`` rather than in ``draw`` so that drawing a frame
        twice draws the same frame twice. It did not, and the difference is
        not academic: every screenshot this scene is judged from is captured
        by presenting a frame a second time.

        The profile matters as much as the target. A constant ease toward the
        next block is a camera on rails -- it starts turning the instant the
        block moves and never finishes. What a person does is *flick*: they
        commit to the next jump as their feet leave the ground, snap the view
        onto it, and then hold still while they fly. So the rate is high for a
        moment after take-off and low the rest of the time, and the difference
        between those two is the whole reason the shot reads as somebody
        playing rather than as a path being followed.
        """
        x, z = self.pos[0], self.pos[2]
        idx = self.jump_index
        # Aim at the block being jumped to, and a little through it toward the
        # one after -- looking dead at your feet is what a beginner does, and
        # it keeps nothing else in frame.
        last = len(self.blocks) - 1
        ahead = [(self.blocks[min(idx + n, last)], w)
                 for n, w in ((1, 0.46), (2, 0.30), (3, 0.24))]
        aim = (sum(b["x"] * w for b, w in ahead),
               sum(self.surface(b) * w for b, w in ahead),
               sum(b["z"] * w for b, w in ahead))

        self._flick = max(0.0, self._flick - dt * 5.5)
        rate = (5.0 + 22.0 * self._flick ** 2) * dt

        dy = _wrap(math.atan2(aim[0] - x, -(aim[2] - z)) - self.yaw)
        self.yaw += dy * min(1.0, rate)

        # Aim at head height over the target, not at the block itself. A camera
        # that points at the surface it is about to land on spends the whole
        # run looking at its own feet -- with an eye 1.62 m up and a block
        # three metres away that is nearly thirty degrees of downward pitch,
        # and the picture it produces is a strip of sea with the sky pushed off
        # the top of the frame.
        flat = math.hypot(aim[0] - x, aim[2] - z)
        # **From the block, not from the arc.** The head's angle is worked out
        # as if the eye were standing on the surface the feet left, so a jump
        # does not drive it: the aim point is four metres away and the body
        # rises 1.25 m over it, so measured from the body the wanted pitch
        # swings seventeen degrees *down* on the way up and back on the way
        # down -- against the body, and the world then pitches about twice as
        # far as the jump does. That was the whole of "he is jumping even
        # higher". Freezing the aim through the flight fixes it too and costs
        # more than it buys: a head that does not move while the body flies
        # reads as a camera on rails.
        want_pitch = math.atan2(self.stand[1] + EYE - (aim[1] + EYE * 0.95),
                                max(3.4, flat))
        # A body in the air looks where it is going: falling drops the gaze,
        # rising lifts it, on top of wherever the target already is. Gently,
        # and that is the point of the number: a jump swings ``vy`` from +8.4
        # to -8.4, so at the 0.030 this used to be the view pitched twenty-
        # seven degrees over every hop -- on top of the body's own 1.25 m of
        # rise, twice a second. Vanilla does not move the view at all when you
        # jump. Seven degrees reads as a glance and stays out of the way of
        # what the body is actually doing.
        want_pitch -= max(-0.09, min(0.12, self.vy * 0.012))
        self.pitch += _wrap(max(-0.16, min(0.55, want_pitch)) - self.pitch) \
            * min(1.0, rate * 0.8)

        # Roll comes off the walk cycle, not off the turn. Vanilla's own view
        # bobbing tilts the camera in step with the feet and does not tilt at
        # all for a turn, and a camera that banks into corners reads as a
        # drone -- which is exactly the note this scene came back with.
        want_roll = math.sin(self.stride * STRIDE_RATE) * 0.035
        if self.phase != "ground":
            want_roll = 0.0
        self._roll += (want_roll - self._roll) * min(1.0, dt * 9.0)

    def _aim_camera(self, x: float, y: float, z: float) -> None:
        # Vanilla's bob is a figure of eight: the head rises twice per stride
        # and swings side to side once. Driven by distance covered, so it
        # stops dead when the feet leave the ground instead of swimming on --
        # and faded rather than switched, so leaving the ground does not put a
        # five-centimetre step in the eye.
        step = self.stride * STRIDE_RATE
        # ``sin^2``, which is ``|sin|`` with the corner taken off it. The head
        # rises twice a stride either way, but ``|sin|`` reverses the eye's
        # velocity in a single frame at the bottom of every step -- six times
        # a second at sprint pace, and the largest jolt left in the camera
        # once the landing and the lens had been smoothed.
        bob_y = (0.5 - 0.5 * math.cos(2.0 * step)) * 0.055 * self.foot
        sway = math.sin(step * 0.5) * 0.045 * self.foot

        cam = self.camera
        # Rigid. The eye is where the body's head is, frame for frame, exactly
        # as vanilla's is -- lagging it was tried (a fifth of the arc's
        # amplitude, rounding the apex and the landing) and it reads as a
        # camera being *carried along a path*, which is the one thing worse
        # than a jump that looks a little high. What the vertical swing needed
        # was not damping; it was for the *pitch* to stop swinging against it.
        eye_y = y + EYE - self.dip + bob_y
        # the sway is across the direction of travel, which is what a head
        # rolling over alternate feet actually does
        cam.position = (x + math.cos(self.yaw) * sway, eye_y,
                        z + math.sin(self.yaw) * sway)
        look = 5.5
        flat = math.cos(self.pitch) * look
        cam.target = (cam.position.x + math.sin(self.yaw) * flat,
                      eye_y - math.sin(self.pitch) * look,
                      cam.position.z - math.cos(self.yaw) * flat)
        # roll: tilt the up vector about the view direction
        fx, fz = math.sin(self.yaw), -math.cos(self.yaw)
        cam.up = (math.sin(self._roll) * -fz, math.cos(self._roll), math.sin(self._roll) * fx)
        cam.fovy = self.fov

    def _horizon_y(self) -> int:
        """Screen row the sea's horizon falls on, this frame.

        A point at eye height and effectively infinite distance projects to it
        exactly, whatever the camera is doing. Clamped, because a projection
        can degenerate and a haze band flung off the top of the frame would
        take the horizon's disguise with it.
        """
        cam = self.camera
        far = (cam.position.x + math.sin(self.yaw) * 1e5,
               cam.position.y,
               cam.position.z - math.cos(self.yaw) * 1e5)
        try:
            y = int(rl.GetWorldToScreen(far, cam[0]).y)
        except Exception:
            y = int(self.height * 0.42)
        return max(int(self.height * 0.18), min(int(self.height * 0.68), y))

    def _draw_ocean(self, x: float, z: float) -> None:
        deep = self.deep
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

    def _draw_reefs(self, x: float, z: float) -> None:
        """Each island's pale shallow, lying on the sea.

        Drawn as the soft-edged disc the blob shadows use rather than as a
        quad: a hard-edged rectangle of lighter blue on the sea reads as a
        mistake, and the only thing separating the two is which texture is on
        the quad.

        The disc is soft-edged, so the quad carrying it is mostly transparent
        --  and a transparent quad fifty metres across still stamps its whole
        square into the depth buffer. What that removed was the far islands
        seen past the near one's corner: measured at up to 110 pixels, and
        replacing land with open sea, which is why the count is small and the
        colour change is not. It is an overlay lying on the water with nothing
        of its own to occlude, so it writes no depth at all.
        """
        shallow = rl.mix_rgb(self.deep, (120, 226, 226), 0.62)
        with no_depth_write():
            for isl in self.islands:
                dist = math.dist((x, z), (isl["x"], isl["z"]))
                if dist > 260:
                    continue
                reef = rl.mix_rgb(shallow, self.palette.fog, min(1.0, dist / 300))
                rl.DrawModelEx(ground_quad(), (isl["x"], 0.06, isl["z"]),
                               (0, 1, 0), 0.0,
                               (isl["reef"], 1.0, isl["reef"]), rl.rgba(reef, 235))

    def _draw_haze(self, pal) -> None:
        """Aerial perspective over the world below only.

        Leaves 3D, lays a smooth alpha fade from the horizon down, and the
        caller then re-enters the same camera for the course. This is a 2D
        draw, so it writes no depth at all and the course draws over it while
        still depth-testing correctly against the islands.

        Starts above the true horizon and fades in, because the eye finds a
        hard edge in a clear sky instantly -- and the previous band drew one
        right where the sea was supposed to dissolve. Not too strong, either:
        dawn and dusk fog is a saturated gold or pink, and at the alpha this
        used to carry it stopped being aerial perspective and became an orange
        wash laid over the middle of the frame.

        The sea is one flat plane with no distance shading of its own, so
        without this it meets the sky along a drawn line rather than dissolving
        into one. The band therefore has to be strongest exactly where the sea
        ends and fade downward from there, and it has to fade *in* at its top
        edge, or it draws its own line across the sky a few rows above the one
        it was meant to hide.

        Where the sea ends is not a fixed fraction of the frame: the camera
        pitches with the jump. So it is projected rather than guessed -- a
        point at eye height and effectively infinite distance is the horizon by
        definition. Pinning it to a constant left a bruise-coloured strip of
        unhazed water above the haze whenever the head was up.
        """
        band = textures.alpha_band(f"haze-{self.ctx.seed.run}", pal.fog, 235, 1.7,
                                   ramp=0.22)
        horizon = self._horizon_y()
        rl.DrawTexturePro(band, (0, 0, 4, 128),
                          (0, horizon - int(self.height * 0.09), self.width,
                           int(self.height * 0.45)),
                          (0, 0), 0.0, rl.WHITE4)

    def _below_tint(self, dist: float, biome=None):
        """Aerial perspective for the world far below.

        Distance fog here is a *tint*, and a tint multiplies -- so fogging a
        dark object toward a dark fog colour only ever makes it darker. By day
        the fog is near white and that reads correctly; at night it turned the
        islands into black slicks lying on the water, darker than the sea they
        were supposed to be receding into. So the far end of the range is
        carried by alpha as well, which fades them into whatever is behind
        them instead of toward a colour.
        """
        f = max(0.0, min(1.0, dist * 0.62 / FOG_FAR + BELOW_FOG * 0.4))
        f = f * f * (3 - 2 * f)
        alpha = int(255 - (205 if self.palette.is_dark else 95) * f)
        return self._fog(dist * 0.62, BELOW_FOG * 0.4, alpha=alpha, tint=biome)

    def _draw_islands(self, x: float, z: float) -> None:
        for isl in self.islands:
            biome = isl["biome"]
            for c in isl["cubes"]:
                bx, bz = isl["x"] + c["dx"], isl["z"] + c["dz"]
                dist = math.dist((x, z), (bx, bz))
                if dist > 300:
                    continue
                tint = self._below_tint(dist, biome)
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
                                   self._below_tint(dist), 1.4, fall["h"], 1.4)

    def _draw_shelves(self, x: float, z: float) -> None:
        """Cloud shelves drifting between the course and the sea.

        They are flat quads, and seen from above a flat quad is exactly what
        they look like unless they fade -- so they take the same distance fog
        as everything else down there. Without it a shelf reads as a pane of
        glass lying on the water.

        Cloud, and so it writes no depth. At alpha 34 to 64 these are barely
        there, and they were still stamping their full quads into the depth
        buffer and deleting the islands behind them -- up to 2,136 pixels of
        one. They have nothing to occlude in any case: the two sheets of a
        shelf are meant to blend into each other rather than one cutting the
        other off, and the depth *test* still hides a shelf that really is
        behind an island.
        """
        shelf = unit_quad("cloud-shelf")
        with no_depth_write():
            for s in self.shelves:
                if s["z"] > z + 60:
                    continue                # recycled in update, not here
                sx = s["x"] + math.sin(self.elapsed * 0.05 * s["drift"]) * 6
                dist = math.dist((x, z), (sx, s["z"]))
                fade = max(0.0, min(1.0, dist / 200.0))
                shelf.materials[0].maps[rl.MATERIAL_MAP_ALBEDO].texture = s["tex"]
                tint = rl.rgba(rl.mix_rgb(self.cloud_tint, self.palette.fog, fade),
                               int(64 - 30 * fade))
                # Two sheets a little apart, the upper one smaller: from
                # directly above a single quad is unmistakably a single quad,
                # and the second layer gives it a top and a shoulder.
                for k, (lift, shrink) in enumerate(((0.0, 1.0), (3.5, 0.66))):
                    # the cloud texture is 2:1, so the quad is squashed to match
                    rl.DrawModelEx(shelf, (sx, s["y"] + lift, s["z"]), (0, 1, 0),
                                   s["yaw"] + k * 37.0,
                                   (s["s"] * shrink, 1.0, s["s"] * shrink * 0.5),
                                   tint)

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

    def _glow(self, x: float, y: float, z: float, size: float, color: rl.RGB,
              alpha: int) -> None:
        """Queue an emissive overlay for the single glow pass.

        Nothing draws a glow where it stands. See :meth:`_draw_glows`.
        """
        if alpha > 0:
            self._glows.append((x, y, z, size, color, alpha))

    def _draw_glows(self) -> None:
        """Issue the frame's queued glows. :func:`~..engine.fx.glow_pass` owns
        the reasoning: writing no depth, and drawn after everything opaque.

        This scene is where that bug was found. Lanterns, gates and orbs all
        glow, and their discs were being stamped into the depth buffer
        *interleaved with the course itself*, so each one deleted whatever
        block happened to be drawn after it and further away. In motion the
        disc sweeps along the course, which is what "there's still like
        invisible blocks or walls blocking other stuff from being seen" looks
        like from the outside.
        """
        glow_pass(self.camera, self._glows)
        self._glows.clear()

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
            for d in blk["deco"]:
                dx, dz = bx + d["dx"], bz + d["dz"]
                dd = math.dist((x, z), (dx, dz))
                d_lift, d_alpha = self._arrival(max(blk["born"], d["born"]))
                dy = by + d_lift - lift + d["dy"] + d["sy"] / 2
                voxel.draw_box(self._model(d["style"]), dx, dy, dz,
                               self._fog(dd, alpha=d_alpha),
                               d["sx"], d["sy"], d["sz"])
                if d["glow"] and dd < 44:
                    self._glow(dx, dy, dz, 1.5, LANTERN_GLOW,
                               90 if self.palette.is_dark else 45)

    def _draw_orbs(self, x: float, z: float) -> None:
        model = self._model("orb")
        spin = self.orb_spin()
        hover = self.orb_hover()
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
                # The glow fades out as the orb comes at the lens. A billboard
                # of fixed world size is a small spark at twenty metres and a
                # bloom across a third of the frame at one, and every orb is
                # collected from about one metre away.
                self._glow(orb["x"], orb["y"] + hover, orb["z"], 0.85, ORB_COLOR,
                           int(110 * min(1.0, max(0.0, (dist - 0.6) / 2.6))))

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
        # Sizes are quoted as a fraction of the half-frame, so widening the
        # field of view scales the hand up with it -- and a held item is sized
        # against the *width* of a 16:9 frame in the game, where this strip is
        # a tall crop of one. Same fraction, much narrower frame, a lantern the
        # size of your head. So the sizes get their own scale and the positions
        # keep the real half-frame, which leaves the item in the corner it
        # belongs in rather than dragging it toward the middle as it shrinks.
        hand_w = half_w * HAND

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
                           (size[0] * hand_w, size[1] * hand_w, size[2] * hand_w),
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
            self._glow(gx, gy, gz, 0.42, LANTERN_GLOW,
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
ORB_SCALE = 0.24
#: How far the player reaches for one. Roughly an arm.
PICKUP_REACH = 0.85
#: Where along a hop a run of orbs is strung. Shared by generation and by the
#: re-hang at take-off, so a driven run cannot end up with them in a different
#: order from the one they were laid in.
ORB_FRACTIONS = {1: (0.5,), 2: (0.36, 0.68), 3: (0.28, 0.5, 0.72)}
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
#: How long a key press keeps the scene in the player's hands.
DRIVEN_HOLD = 0.6
#: Shortest a ground phase may be. Below a few frames the run-up stops being
#: visible and the landing reads as a bounce.
GROUND_MIN = 0.07
#: Steps per metre, for the walk cycle. Vanilla's bob runs at roughly this
#: against sprint speed, and it is what the head bob and the roll share.
STRIDE_RATE = 2.9
#: Points along a hop the corridor check tests the body at.
ARC_SAMPLES = 9
#: How far out into its own cell a piece of sub-block furniture sits. A fence
#: post goes to the corner of the platform, a rail or a wall torch hugs the
#: side of the block it is fixed to. Both numbers are what it takes to clear
#: the line the body runs along, and both are also where the game puts them.
CORNER = 1.3
FLANK = 0.72
#: How many integer offsets a placement will consider before giving up on the
#: heading it wanted.
OFFSET_FAN = 16
#: How far a beam or a column in a gap stays clear of the body that flies past
#: it. Small on purpose: the whole effect is that it looks as though it will
#: not clear. It is a floor rather than the real margin, because both pieces
#: are then rounded onto the lattice away from the body.
SPAN_CLEAR = 0.06
#: How much shorter than the step it was asked for an integer offset may be.
#: Under one cell, so a diagonal is still reachable while a whole block of the
#: requested gap can never be given away. See :func:`_offsets`.
SHORT_FALL = 0.6
#: How large the held item is against the frame's half-width. See
#: :meth:`ParkourScene._draw_held` for why it is not simply 1.
HAND = 0.76
#: Vertical field of view. The strip is a tall crop of what would be a 16:9
#: frame, so a vanilla-default 70 leaves barely forty degrees across it and a
#: course that turns at all walks out of the picture. Widened until a bend
#: stays on screen; past about here the block under the lens starts to smear.
FOV = 76.0
#: Degrees of extra field of view per metre a second over sprint pace, and how
#: fast the lens gets there.
#:
#: This used to be two degrees while the phase was ``air`` and none otherwise,
#: which is a *step* at every take-off and every landing -- eight a second, and
#: a whole-frame zoom is about the most visible thing a camera can do. Hung off
#: the speed instead it says the same thing (you are moving fastest in flight)
#: and says it continuously, because the speed itself is continuous now.
FOV_GAIN = 1.4
FOV_EASE = 6.0
#: The landing dip, as a spring the impact kicks rather than a number set to
#: one and decayed. The old form dropped the eye 0.17 m in a single frame --
#: ten metres a second of camera, on every landing -- and that snap is what
#: reads as the body clicking into the block. Given the body's own downward
#: speed at the moment its feet stop, the eye keeps going and is brought back
#: by the legs: the camera's velocity is then *continuous* through a landing,
#: which is what the knees are for.
#: The stiffness is set by the frame clock and not by taste: a spring whose
#: damping term is comparable to 1/dt kills the eye's velocity inside a single
#: frame, which is the hard stop it was meant to replace wearing a spring's
#: clothes. At 13 rad/s the follow-through lasts three or four frames, which is
#: the shortest a person reads as a knee rather than as a cut.
DIP_W = 13.0
DIP_ZETA = 1.0
#: How much of the impact the legs pass on to the head.
DIP_KEEP = 0.6
#: The impact an ordinary jump lands with, which costs the lens nothing. A hop
#: comes down at about the speed it went up at, so *every* landing used to dip
#: the eye 8 cm -- twice a second, on a camera that vanilla holds perfectly
#: still. Measuring the dip from here instead means it fires when the body has
#: actually fallen further than it jumped, which is the only time a person's
#: legs give at all.
DIP_FREE = JUMP_V
#: Fastest impact past that the legs will pass on. A twelve-block drop should
#: not put the lens through the floor.
DIP_CAP = 6.0
#: ...and what *every* landing is worth regardless, which is about two and a
#: half centimetres of eye. Zero was tried and it is the thing that made a
#: chain of correct arcs read as a body being carried along a path: with the
#: feet down for a tenth of a second and the dip gone, nothing in the frame
#: marks the landing at all, and the camera is a smooth function of position
#: from one block to the next. This is the beat, not the bounce -- the eight
#: centimetres it replaced were the bounce.
DIP_BASE = 1.6
#: How fast the walk bob fades in and out. It used to switch, which put a
#: five-centimetre step in the eye at every take-off.
FOOT_EASE = 9.0


def _ramped(rng, easy, hard, difficulty: float):
    """Draw from ``easy`` early in a run and from ``hard`` late in it.

    A coin weighted by difficulty picks the table, rather than the two being
    blended into a third. Blending would give a distribution that is always the
    average of both and never either -- and the point of the hard table is that
    the hops in it turn up, not that they raise a mean.
    """
    return rng.choice(hard if rng.random() < difficulty else easy)


def _wrap(a: float) -> float:
    """An angle folded into (-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


def _floor(v: float) -> int:
    return int(math.floor(v))


def _round(v: float) -> int:
    return int(math.floor(v + 0.5))


def _quantise(step: tuple[int, int]) -> tuple[int, int]:
    """An integer step reduced to one of the eight lattice directions.

    Decorations hang off this rather than off the exact heading, which is what
    keeps a gate's jambs and a fence's posts in whole cells however obliquely
    the course happens to be running.
    """
    sx, sz = step
    m = max(abs(sx), abs(sz)) or 1
    qx = 0 if abs(sx) * 2 < m else (1 if sx > 0 else -1)
    qz = 0 if abs(sz) * 2 < m else (1 if sz > 0 else -1)
    return (qx, qz) if (qx or qz) else (0, -1)


def _standing_cells(blk: dict, y: int, cells=None) -> frozenset:
    """The cells a block's own walking surface sits inside, if any.

    Empty for anything a full cell high: its surface is the top of its cell, so
    a body standing there is above the cell, not in it. A slab's surface is
    halfway up, so its cell has to be excused or every hop off one is refused.
    """
    if FORMS[blk["form"]] >= 1.0:
        return frozenset()
    if cells is not None:
        return frozenset(cells)
    sp = SPREAD.get(blk["form"], 0)
    return frozenset((blk["x"] + ox, y, blk["z"] + oz)
                     for ox in range(-sp, sp + 1) for oz in range(-sp, sp + 1))


def _samples(frm, to) -> int:
    """How many points a path of this length is tested at.

    By *distance*, not a fixed count, and the difference is a body's width. A
    fixed nine put consecutive tests 0.6 m apart on a five-metre hop -- exactly
    the width of the thing being tested, so a shoulder could pass either side
    of a sample and through a lintel in between. It got worse the moment the
    arcs grew: measured, the body came 0.155 m inside a piece of scenery it
    had been checked against, against 0.039 before.
    """
    span = math.dist(frm, to)
    return max(ARC_SAMPLES, min(48, int(span / 0.2) + 1))


def _arc_points(frm, to) -> list[tuple[float, float, float]]:
    """Where the feet are, sampled along a hop. Used to keep scenery out of
    the way of a body that is already committed to flying through it."""
    dur, vy0 = flight(frm, to)
    n = _samples(frm, to)
    out = []
    for i in range(n + 1):
        f = i / n
        t = dur * f
        out.append((frm[0] + (to[0] - frm[0]) * f,
                    frm[1] + vy0 * t - 0.5 * GRAVITY * t * t,
                    frm[2] + (to[2] - frm[2]) * f))
    return out


def _line_points(frm, to) -> list[tuple[float, float, float]]:
    """A straight run, sampled the same way an arc is."""
    n = _samples(frm, to)
    return [(frm[0] + (to[0] - frm[0]) * i / n,
             frm[1] + (to[1] - frm[1]) * i / n,
             frm[2] + (to[2] - frm[2]) * i / n)
            for i in range(n + 1)]


def _span_piece(kind: str, blk: dict, arc, local, style: str) -> list[dict]:
    """A beam over the gap, or a column standing in it.

    Both are built out of the arc that arrives at ``blk``, which is why they
    can be tight without ever being wrong. A ``lintel`` goes a body's height
    above the highest point of that flight, so the head passes under it with
    centimetres to spare; a ``hurdle`` tops out just below the lowest, so the
    feet pass over it with the same. Neither is a guess: both clearances are
    read off the sampled arc and rounded *away* from the body, and
    :func:`_in_the_way` re-checks the result against the same arc before it is
    kept.

    The horizontal position is the cell the relevant arc point falls in,
    expressed in the quantised heading -- the same whole-cell frame every other
    decoration uses, so a beam is on the lattice like everything else.

    Returns nothing at all when the arc is too flat to fit a piece into. A
    hurdle needs somewhere below the feet that is still above the block it
    stands beside, and a hop that barely leaves the ground has nowhere; the
    honest answer there is no scenery rather than scenery in the way.
    """
    if len(arc) < 3:
        return []
    # Ends excluded: the first and last samples are the take-off and landing
    # points themselves, which are on top of blocks rather than over the gap.
    span = arc[1:-1]
    fx, fz = _quantise(blk["step"])
    n = fx * fx + fz * fz
    mid = span[len(span) // 2]
    fwd = _round(((mid[0] - blk["x"]) * fx + (mid[2] - blk["z"]) * fz) / n)
    if fwd >= 0:
        return []                  # the middle of the hop is over the block

    # The heights the body reaches anywhere near that cell. "Near" and not
    # "in", because a body is 0.6 m wide and a piece is checked against it with
    # that width added: taking the extreme over the cell alone would clear a
    # beam that the shoulder of the very next sample walks into, and the piece
    # would then be silently dropped by :func:`_in_the_way` instead.
    cx = blk["x"] + fwd * fx
    cz = blk["z"] + fwd * fz
    near = [p[1] for p in span
            if abs(p[0] - cx) < 1.0 + BODY_HALF_W
            and abs(p[2] - cz) < 1.0 + BODY_HALF_W]
    if not near:
        return []

    if kind == "lintel":
        # ceil, so rounding onto the lattice can only ever move the beam
        # further from the head, never into it.
        dy = math.ceil(max(near) + BODY_H + SPAN_CLEAR - blk["y"])
        # Three cells across: a single cube overhead reads as debris, a beam
        # reads as a thing you had to duck under.
        return [local(side, fwd, dy, 1.0, 1.0, 1.0, style)
                for side in (-1, 0, 1)]

    # A column standing in the gap, topping out just under the feet. How far
    # under is not a choice: the arc apexes less than a metre above the surface
    # it left -- ``flight`` solves the take-off for the two endpoints, so a
    # level hop peaks about 0.77 m up, not at vanilla's full 1.25 -- and a
    # whole cell is one metre. So the top face lands at or just below the
    # course itself, and what the eye reads is a pillar in the gap that the
    # body clears rather than lands on. A first attempt hung this off the arc's
    # *lowest* point, which is always at one of the ends where there is no
    # clearance at all, and built precisely zero of them in twelve runs.
    top = _floor(min(near) - SPAN_CLEAR - blk["y"])
    return [local(0, fwd, top - 1 - i, 1.0, 1.0, 1.0, style)
            for i in range(3)]


def _deco_box(blk: dict, deco: dict) -> AABB:
    """A decoration's world box, from the numbers ``_draw_course`` draws it
    with -- the same rule every other hitbox in the project follows."""
    return AABB.around(blk["x"] + deco["dx"], blk["y"] + deco["dy"],
                       blk["z"] + deco["dz"],
                       deco["sx"] * 0.5, deco["sy"], deco["sz"] * 0.5)


def _in_the_way(blk: dict, deco: dict, arc) -> bool:
    """Does this piece of scenery intersect the body flying the given arc?"""
    dx = blk["x"] + deco["dx"]
    dy = blk["y"] + deco["dy"]
    dz = blk["z"] + deco["dz"]
    half_x = deco["sx"] * 0.5 + BODY_HALF_W
    half_z = deco["sz"] * 0.5 + BODY_HALF_W
    for x, y, z in arc:
        if (abs(x - dx) < half_x and abs(z - dz) < half_z
                and y < dy + deco["sy"] and y + BODY_H > dy):
            return True
    return False


def _unit(step: tuple[int, int]) -> tuple[float, float]:
    sx, sz = step
    length = math.hypot(sx, sz) or 1.0
    return sx / length, sz / length


def _edge_offset(form: str, ux: float, uz: float) -> tuple[float, float]:
    """Where the feet plant, as an offset from a block's centre.

    Measured against the block's *face* rather than as a fixed radius, because
    a block is square and a radius is round. A three-wide platform reaches
    1.5 m along an axis and 2.1 m into its corner; plant the feet at a flat
    1.3 m and a course running diagonally takes off with a metre of platform
    still ahead of it -- and since the arc starts falling almost immediately,
    the camera dips straight through that platform's own outer cube. Scaling
    by the larger component puts the feet the same distance inside the edge
    whichever way the course is running, and leaves the per-axis offset no
    bigger than ``EDGE[form]`` either way.
    """
    m = max(abs(ux), abs(uz)) or 1.0
    e = EDGE[form] / m
    return ux * e, uz * e


def _takeoff_of(blk: dict, out_step: tuple[int, int]):
    """The far edge of a block, along the way out of it."""
    ox, oz = _edge_offset(blk["form"], *_unit(out_step))
    return (blk["x"] + ox, blk["y"] + FORMS[blk["form"]], blk["z"] + oz)


def _land_of(x: float, surface: float, z: float, form: str,
             in_step: tuple[int, int]):
    """The near edge of a block, along the way into it."""
    ox, oz = _edge_offset(form, *_unit(in_step))
    return (x - ox, surface, z - oz)


def _hop_points(prev: dict, prev_land, step: tuple[int, int], form: str,
                bx: float, surface: float, bz: float):
    """Where the feet leave ``prev`` and touch down on the next block.

    Nominally the far edge of one and the near edge of the other, which is
    what gives every block a run-up -- but that pair also *decides the arc*,
    and a pair that comes out shorter than the jump's own reach can only be
    flown by not jumping properly. There is one impulse in this game. So the
    shortfall is spent on the geometry instead, in the order a player spends
    it:

    * **land deeper.** A short gap is met by carrying on into the block rather
      than catching its lip. Bounded at the block's middle, so the landing is
      always on the near half of its own footprint and the take-off point --
      which is not known yet, and may be in any direction once the course
      turns -- is always still ahead of it.
    * **leave earlier.** Whatever is left comes off the run-up behind, along
      the line the body is actually running, down to :data:`MIN_RUN`.

    Both are bounded by a block's own size, so a gap far under the reach still
    arrives with some shortfall on it -- which is why :func:`hop_span` refuses
    to lay one in the first place.
    """
    ux, uz = _unit(step)
    frm = _takeoff_of(prev, step)
    to = _land_of(bx, surface, bz, form, step)
    short = reach(VY_MAX, to[1] - frm[1]) \
        - math.dist((frm[0], frm[2]), (to[0], to[2]))
    if short > 1e-6:
        m = max(abs(ux), abs(uz)) or 1.0
        deep = min(short, EDGE[form] / m)
        to = (to[0] + ux * deep, to[1], to[2] + uz * deep)
        short -= deep
    if short > 1e-6:
        rx, rz = prev_land[0] - frm[0], prev_land[2] - frm[2]
        run = math.hypot(rx, rz)
        back = min(short, max(0.0, run - MIN_RUN))
        if back > 0.0:
            frm = (frm[0] + rx / run * back, frm[1], frm[2] + rz / run * back)
    return frm, to


_OFFSETS: dict[tuple[float, int], list[tuple[int, int]]] = {}


def _offsets(heading: float, step: int) -> list[tuple[int, int]]:
    """Integer offsets near a heading and a length, best first.

    This is where the course meets the lattice. Everything upstream still
    thinks in a continuous heading, because a course that may only run along
    eight compass points looks like a maze; everything downstream is on whole
    cells, because two cubes at whole cells cannot be inside one another. The
    ranking is angle first and length second: which way the run is going is
    what a viewer reads, and a gap one block wider than the set-piece asked
    for is not something anybody can see.

    The length window is deliberately lopsided. Overshooting is free -- a hop a
    bit longer than asked for still looks like the hop that was asked for --
    but undershooting is the exact defect this scene was sent back with. A
    symmetric window let a request for a three-cell step be answered with one
    of 1.65, and the scoring would take it whenever its angle was better, so a
    set-piece that asked for a real jump kept getting a shuffle. Short
    candidates are now simply not offered.
    """
    key = (round(heading, 2), int(step))
    got = _OFFSETS.get(key)
    if got is not None:
        return got
    want, s = key
    scored = []
    reach = s + 2
    for dz in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            if dx == 0 and dz == 0:
                continue
            length = math.hypot(dx, dz)
            if not (s - SHORT_FALL <= length <= s + 1.35):
                continue
            err = abs(_wrap(math.atan2(dx, -dz) - want))
            if err > 0.9:
                continue
            scored.append((err * 1.7 + abs(length - s) * 0.5, dx, dz))
    scored.sort()
    got = [(dx, dz) for _, dx, dz in scored[:OFFSET_FAN]]
    if not got:                              # a heading nothing lines up with
        got = [(_round(math.sin(want) * s) or 1, -_round(math.cos(want) * s))]
    _OFFSETS[key] = got
    return got


def flight(frm, to) -> tuple[float, float]:
    """Duration and take-off vertical speed of the hop from ``frm`` to ``to``.

    One line, and it is the line the whole scene's motion rests on: horizontal
    speed is *constant*, so the time a hop takes is simply how far it goes
    divided by how fast a body sprints, and the take-off is then whatever
    lands you on the far end under gravity.

    The version this replaces solved for a duration and then clamped it into a
    hang-time window, which meant the horizontal speed came out different on
    every hop -- three and a half metres a second on the short ones, six on the
    long. Nothing about that is visible as a number and all of it is visible as
    motion: the short hops floated. What keeps a run reading as a run is that
    the body never changes pace, and the only thing that varies between hops is
    how high the arc goes.

    Whether the take-off it asks for is one a body actually has is a separate
    question, and :meth:`ParkourScene._fits` is where it gets asked -- no hop
    outside ``VY_MIN..VY_MAX`` is ever laid down.

    **Slowing the approach was tried and it is not what a player does.** For a
    while the speed was solved first -- the fastest approach that still spent
    the whole impulse -- which arcs a short hop properly at the cost of the
    body creeping up to it at 6.4 m/s. Measured over twelve runs that was the
    median hop, so the scene spent most of its life below sprint pace for the
    benefit of gaps that should not have been there in the first place. A
    player at full sprint meets a short gap by *landing further onto the far
    block*, and that is where the shortfall goes now: :func:`_hop_points`
    spends it on the geometry before this function ever sees the endpoints,
    and :func:`hop_span` refuses to lay a gap whose remainder would take the
    impulse below :data:`IMPULSE_MIN`. So the speed here is the sprint jump's,
    always, and the arc is the vanilla one to within a tenth of its impulse.
    """
    dist = math.dist((frm[0], frm[2]), (to[0], to[2]))
    rise = to[1] - frm[1]
    dur = max(1e-4, dist / AIR_SPEED)
    vy0 = rise / dur + 0.5 * GRAVITY * dur
    # A hop laid at exactly the full jump's reach solves to ``VY_MAX`` plus or
    # minus a part in 10^16, and ``_fits`` refuses anything over it. Clamp the
    # rounding rather than losing the scene's commonest jump to it.
    if VY_MAX < vy0 <= VY_MAX + 1e-6:
        vy0 = VY_MAX
    return dur, vy0


def flight_speed(frm, to) -> float:
    """How fast the body is travelling over the ground during that hop."""
    dist = math.dist((frm[0], frm[2]), (to[0], to[2]))
    return dist / flight(frm, to)[0]


def reach(vy0: float, rise: float) -> float:
    """How far a hop that leaves at ``vy0`` and climbs ``rise`` gets.

    Its flight time is the descending root of ``rise = vy0*t - g*t^2/2`` and
    the reach is that time at sprint speed -- so this is one function for both
    ends of :func:`hop_span`, which differ only in how much of the impulse is
    being spent. Zero when there is no root: nothing rises two blocks, here or
    in the game.
    """
    disc = vy0 * vy0 - 2.0 * GRAVITY * rise
    return 0.0 if disc < 0.0 else AIR_SPEED * (vy0 + math.sqrt(disc)) / GRAVITY


def hop_span(rise: int) -> tuple[float, float]:
    """Shortest and longest hop a body can make for a given change in height.

    Both ends fall out of the same two facts -- one jump impulse, one constant
    horizontal speed -- and neither is a number anybody chose:

    * **Longest** is the full jump: ``reach(VY_MAX, rise)``. A level hop makes
      4.3 m; dropping buys more, because falling takes longer and the body does
      not slow down while it does. Rising two blocks has no solution at all,
      which is why nothing here can express it.
    * **Shortest** is the *same jump with ninety per cent of its impulse*, less
      what the geometry can give back (:data:`ABSORB`). This is the floor that
      keeps every jump in the scene a jump. Solving a short gap by taking off
      more gently is the one thing a Minecraft player cannot do, and it was
      what made two thirds of the course apex at half of vanilla; a short gap
      is answered by landing deeper instead, and where even that will not cover
      it the gap is simply not laid.

    Two older floors are folded in and both still bind somewhere. A *climb* has
    to be past its apex when it arrives -- land while still rising and the body
    has come up through the side of the block -- which is ``t >= sqrt(2*rise/g)``.
    A *drop* has to leave the ground properly rather than be thrown off it, so
    its take-off has to clear ``VY_MIN``.
    """
    if rise >= 0:
        lo = AIR_SPEED * math.sqrt(2.0 * rise / GRAVITY)
    else:
        lo = AIR_SPEED * (VY_MIN + math.sqrt(VY_MIN * VY_MIN
                                             - 2.0 * GRAVITY * rise)) / GRAVITY
    hi = reach(VY_MAX, rise)
    lo = max(lo, reach(IMPULSE_MIN * VY_MAX, rise) - ABSORB)
    # ...but the floor may never ask for more than the lattice can offer at
    # this rise, or the window is empty and ``fit_gap`` has nothing to return.
    # It bites at the bottom of the range: a five-block drop reaches 7.18 m,
    # the impulse floor wants 6.28, and the only gaps either side of that are
    # 6.24 and 7.24. A hop that long is not a shuffle whatever its take-off
    # was -- a body dropping five blocks steps off rather than jumping, here
    # and in the game -- so the floor gives way to the geometry.
    widest = max((g + 1 - 2 * EDGE["full"] for g in range(1, 9)
                  if g + 1 - 2 * EDGE["full"] <= hi), default=hi)
    return max(MIN_HOP, min(lo, widest)), hi


def fit_gap(gap: int, rise: int) -> int:
    """Widen a gap until the hop across it is one a body can make.

    A drop is the case that matters. Falling takes time, the body keeps its
    speed the whole way down, and so a hop that descends four blocks covers
    close to four metres of ground whether the set-piece wanted it to or not.
    Ask for a two-block gap under a four-block drop and the only way to deliver
    it is to throw the player at the floor, which is why the old descent looked
    like falling down a lift shaft. Here the gap opens instead, and a descent
    reads as leaping out into the drop.
    """
    lo, hi = hop_span(rise)
    if hi <= 0.0:
        # Nothing is jumpable at this rise -- two blocks up has no solution,
        # here or in the game. The gap comes back unchanged rather than as
        # some placeholder, because there is no answer to give and the caller
        # is going to have every candidate rejected by ``_fits`` and move on
        # to a different rise. Returning a number that *looks* jumpable is how
        # a caller that skipped ``_fits`` would get a hop nobody can make.
        return max(1, gap)
    for g in range(max(1, gap), 9):
        span = g + 1 - 2 * EDGE["full"]
        if lo - 1e-6 <= span <= hi + 1e-6:
            return g
    return max(1, max_gap(rise))


def max_gap(rise: int) -> int:
    """The widest gap this rise can be jumped across, or zero if none can.

    The chasm's whole premise, and a computed number rather than a chosen one.
    """
    hi = hop_span(rise)[1]
    best = 0
    for g in range(1, 9):
        if g + 1 - 2 * EDGE["full"] <= hi:
            best = g
    return best


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

    # The course's own colours wear wool and concrete, because that is what
    # brightly coloured blocks in the game are; the noise amplitude on top of
    # each pattern is now small, since the patterns carry the grain themselves.
    # Both used to be turned up far enough that a block read as a stamp rather
    # than a material -- an eight-texel chequerboard on a magenta cube.
    recipe: list[tuple[str, rl.RGB, str, float]] = [
        ("candy0", pal.blocks[0], "wool", 0.03),
        ("candy1", pal.blocks[1], "concrete", 0.02),
        ("candy2", pal.blocks[2], "wool", 0.03),
        ("wood", tone((150, 106, 60)), "planks", 0.02),
        ("brick", tone((170, 88, 70)), "bricks", 0.02),
        ("stonebrick", tone((140, 140, 146)), "stonebrick", 0.02),
        ("stone", tone((132, 132, 140)), "cobble", 0.03),
        ("quartz", tone((228, 226, 218)), "grain", 0.02),
        ("lantern", (255, 212, 128), "lantern", 0.02),
        ("orb", ORB_COLOR, "lantern", 0.02),
        ("sand", tone((222, 208, 150)), "sand", 0.03),
        ("leaf", tone((72, 148, 62)), "leaves", 0.04),
        ("water", rl.scale_rgb((120, 200, 236), lit), "grain", 0.03),
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
                                   noise=0.03, seed=run * 17 + 40,
                                   top=tone((96, 186, 82)),
                                   side_band=tone((104, 170, 76)),
                                   pattern="dirt"),
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
