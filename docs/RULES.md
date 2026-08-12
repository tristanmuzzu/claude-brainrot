# Rules for building a level of the spiral tower

The constitution a level in `src/brainrot/scenes/levels/` must satisfy. It is
written to be checkable: nearly every rule here has a number and a command that
prints it. `docs/RESEARCH.md` is *why* these are the rules — the real map and
the reference footage, measured; `docs/TOWER.md` is the roster and the
tower-wide design. Read this one before writing a single landing.

Two kinds of rule, and the difference matters:

- **Hard** — the engine or a test refuses it. Breaking one is a bug.
- **Design** — nothing stops you, and a level that breaks one is the thing the
  owner has now rejected three times.

---

## 0. What a level is

A level is six to ten seconds of screen: a themed terrace on the outside of an
inverted cone, ended by a chasm with no floor in it, with the next level four
to eight blocks higher. You get in off the level below's exit climb and out by
your own. Eighty to a hundred metres of arc, ten to fifteen authored landings,
one filler beat that repeats if the terrace outlasts the script.

It is **one place**, not a stretch of corridor. The reference's levels are a
windmill farm, a market street, a mine gallery, a flooded cistern — you could
name each in one word after two seconds of looking at it, and you cannot name
"a bit of tower with some blocks on it".

**The three failures this pass exists to end**, all of them the owner's words
and all of them still true of the current roster:

1. *You can just run past half the obstacles.* Sixteen of the first twenty
   levels are 100% plain hop over ground that is continuous underneath.
2. *It's the same jump every time.* Measured: the tower is 94% plain hop
   against a kernel that expresses seven verbs.
3. *It doesn't read as a place.* Levels average two dozen designed landings
   and one structure that is on screen, at readable size, essentially never.

---

## 1. The physics, exactly

One jump impulse and one horizontal speed. Nobody chose these; they are
Minecraft's own numbers converted from ticks, in `parkourkit`:

    GRAVITY 28.0    JUMP_V 8.4     AIR_SPEED 7.10 (in flight)
    RUN_SPEED 5.612 WALK_SPEED 4.317   MIN_HOP 2.0 m

**The jump envelope.** `hop_span(rise)` computes it; no design may sit outside
it and `tools/tower_probe.py --design-only` refuses one that does. Distances
are stand-point to stand-point, which is `hypot(arc, radial)` minus both
landings' `EDGE`.

| rise | ordinary hop | on ice (`kind="slide"`) |
|---|---|---|
| **+2 or more** | **no solution — none, at any distance** | none |
| +1 | 2.00 – **3.10** | 2.67 – 4.36 |
| +0.5 (onto a slab) | 2.00 – 3.78 | 2.00 – 5.33 |
| level | 2.00 – **4.26** | 2.00 – **6.00** |
| −1 | 2.35 – 4.98 | 3.30 – 7.02 |
| −2 | 3.12 – 5.56 | 4.39 – 7.83 |
| −3 | 3.72 – 6.05 | 5.24 – 8.52 |
| −4 | 4.22 – 6.48 | 5.95 – 9.13 |
| −6 | 5.07 – 7.24 | 7.14 – 10.20 |
| −8 | 5.79 – 7.90 | 8.15 – 11.13 |

Three consequences worth having in your head:

- **A descent is the only long jump.** Falling takes time and the body does not
  slow down while it falls, so a two-block drop buys a metre and a half of
  reach. If you want a jump that reads as *long*, step it down.
- **A descent cannot also be short.** −4 has a *minimum* of 4.22 m: the arc
  covers that much ground before it arrives. Descents leap out into the drop.
- **The head sweeps three cells above every take-off.** One impulse always
  rises 1.25 m, so a lid two blocks up is a lid inside the player and the arc
  under it is refused every time. `ceiling=` lids sit at three. This is why a
  doorway is *walked* through, never jumped through.

**Hard rule.** Every authored hop and slide legal on paper:
`python tools/tower_probe.py --design-only` — 0.2 s, run it after every edit.
It names level, beat and node index.

---

## 2. The verbs — and the six the tower has never used

`kind=` on a node. **The tower is 94% `hop` and this is the single biggest
thing to change.** Every verb below was placement-tested in an authored level
this session; the recipes are what actually fired, not what the source
suggests should.

| verb | what it is | speed | verified recipe |
|---|---|---|---|
| `hop` | the default | 7.10 in air | — |
| `slide` | an ice jump: same arc time, **10.0 m/s across** | 10.0 | works flat out. `kind="slide"`, pair with `form="ice"` and an ice material. **Reaches 6.00 m level and 7.02 m down one** — half again a hop, and the easiest way to make a jump *read* as big |
| `bounce` | off a slime pad — **the only way a landing gains two blocks** | steered 2.6–7.81 | a landing with `form="slime"`, then a node with `kind="bounce"` **and `spread` ≥ 1**. Gains **+2** with the arc anywhere from 3.2 to 6.5 m |
| `web` | wading through cobweb | **1.20** | `kind="web"`, `form="web"`; the whole line of cells must be clear; 3-D distance 1.4–3.6 m and within one block of level |
| `walk` | crossing a threshold on foot | 5.612 | `kind="walk"`, ground distance ≤ 2.4 m, height change ≤ 0.55. This is how a body gets *through a doorway* |
| `climb` | a ladder or vine | 2.35 | `kind="climb"`, `climb_style="ladder"|"vine"`, `step_y` between +1.5 and +9.5, `hug` 1.6–2.0, **short arc (2.4 works, 3.0 often does not)**. Needs a free column with solid rock behind it |
| `bubble` | a soul-sand water column | **11.0** | as `climb` but `kind="bubble"`; the soul sand is added for you |

Surfaces change ground pace without any `kind` at all — `packedice` and
`blueice` run at **8.5**, `soulsand` at **2.51**, `web` at **1.20** against a
normal 5.612. A soul-sand stretch is a *slow* beat and reads as one.

**`honey` is a material with no physics.** It is a colour. Do not design a beat
around it thinking it is sticky.

**Two traps, both measured:**

- **`spread=0` silently kills a bounce.** With `spread=0` the bounce is refused
  and the landing is placed a block lower as an ordinary hop — it looks like it
  worked and it is a hop. Always `spread` ≥ 1 on a `bounce`.
- **`--design-only` does not check any of these verbs.** It only checks `hop`
  and `slide`, because checking a ladder against a jump table would be checking
  the wrong thing. A climb, bubble, web, walk or bounce that cannot be built
  fails *silently at build time* and the beat quietly gets less of your design.
  The only proof is a placement count:
  `python tools/level_review.py --level N --report` and read the per-beat
  fidelity table. A beat under 98% is a design to look at; a beat at 0% never
  happened.

**Design rule — the verb quota.** No level may be more than **70% plain hop**,
and every level uses **at least two** non-hop verbs, one of which is its
*signature*: the thing you would name the level's parkour after. Printed by
`level_review --report` as `hop share`.

---

## 3. The ground — and why you cannot just walk it

This is failure (1), and it is a property of the **floor**, not of the jumps.
If there is continuous ground under a beat, the parkour on top of it is
decoration and reads as decoration however good the jumps are.

**Hard-ish rule, measured:** a level must come in at **≤ 55% covered by a
no-jump walker, and must never be walkable end to end.** The real map measures
46% mean and 0 of 43 legs passable. Printed by `level_review --report` under
`CAN IT BE WALKED`, and tower-wide by `tools/bypass_probe.py`.

The levers, in the order they are worth reaching for:

1. **`profile="ledge"`** (the default). Ground is a shelf `shelf` cells wide
   against the core wall with the drop genuinely outboard. `shelf` floors at
   3.0 and is capped at `band - 2.0`. **`profile="plaza"` is a full floor and
   is the thing that killed the last tower** — use it only for a level that
   dresses the floor as a real place (a street, a temple hall) and then break
   it hard.
2. **`breaks=`** — in-level floor gaps. Three for a ledge, two for a full
   floor, by default. The first break wider than 4.5 m gets a *lock*: an
   approach at height, an island floated over the hole, a landing on the far
   ground. More breaks is the bluntest and most reliable way to move the walk
   number.
3. **`pedestal=False`** floats a landing with nothing under it. A run of
   floating landings over the drop cannot be walked by construction.
4. **`moat=True`** cuts the theme's liquid under the jump.
5. **`form="floor"`** is the opposite and must be used deliberately: it places
   *no block*, requires the cell to be solid ground already, and is how a beat
   says "run along the terrace here". Every `form="floor"` landing is a metre
   of walkable ground you are choosing to give away.

**Design rule.** No more than three consecutive `form="floor"` landings, and
never a whole beat of them.

**The corridor.** `band` is the level's own width, core face to rim: 7.5 is a
gallery whose walls press in, 13.0 is a court. Both are levels; a tower where
every level is 9.5 is a corridor. The course itself keeps 2.0 off each edge.
Landings may stand **past the rim** on floating spurs by asking for a `hug`
larger than the band — the real map's course wanders twenty blocks radially
and that is much of why its levels read as places.

---

## 4. Structures

Failure (3). A level needs one thing you would recognise it by, and — this is
the part that took a probe to learn — **placing it is not the same as it being
seen.** 97% of landmarks were built; 18% were ever held at readable size.

- `landmark=` names a blueprint. Twelve of the fourteen have a **gated**
  variant carrying a passage held open from the moment the level appears, and
  the course is steered *through* it. Running through a structure took levels
  holding it at 25° from 20% to 52%.
- **A passage is walked through, not jumped through** (see §1: the head sweeps
  three cells). Interiors are `walk` gates with three cells of clearance;
  arches, bell frames and canopies are `hop` gates five cells high.
- **A passage is three cells wide or it is a graze.** The body is 0.6 m across
  and straddles the next cell whenever it is not dead centre, which on a circle
  is the normal case.
- **`shell=`** on a beat builds an interior around the move: `tunnel` (tight,
  flat roof), `hall` (tall, lamp niches), `cave` (rough), `shaft` (a tube round
  a climb), `grotto` (a lamplit bay carved into the core wall). Shells are
  painted through the same reservation checks as everything else, so a shell
  can never close over a jump — the doorways cut themselves.

**Design rule.** The level's structure is on screen within its first four
seconds, and `level_review --report` shows it held at 25° for **≥ 1.5 s**.

---

## 5. Rhythm, light and palette

The reference alternates exposed ledge and enclosed interior every ten to
twenty seconds, and the old tower was 100% open corridor.

- **Design rule.** A level is not one state throughout. Either it is enclosed
  and opens out, or it is exposed and passes through something. At least one
  `shell=` beat in any level that is not deliberately an open ledge run, and
  never more than about fifteen seconds in one state.
- **Design rule — palette.** Three to five materials naming real value
  contrast, and any single frame shows at least three of distinct value. A
  level that is one colour of box is failure (3) in miniature. `skin` re-skins
  the base theme; the roles are `ground`, `sub`, `rock`, `accent`, `glow`,
  `liquid`, and only those six may be given a material name.
- **Light is a level's own.** Interiors carry their own lamps; the `glow` role
  and `deco="lamp"` are what make a dark level legible rather than black.

---

## 6. The shape of a level

Beats are laid **whole or not at all**, in order, and `filler` repeats if the
terrace outlasts the script — so put the level's *character* in the filler and
its *surprise* in a beat. Filler loops back on itself, and the seam from its
last landing to its first is checked; get it wrong and half your fidelity loss
is there.

A level that works has:

1. **an opening** that says where you are — the structure in frame, the
   material change, the threshold;
2. **an escalation** — the beats get harder, not louder;
3. **one showpiece** — the jump or the room you would remember. Difficulty is
   the punctuation, not the sentence;
4. **an exit that is visible before it is reached.**

**Frozen for this pass:** a level's `name`, `theme` and `rise`. `rise` is
cyclic — any three consecutive rises *are* the head-room over the lowest of
them (`sum − 5` must land in 6…16) — so it cannot be a per-level decision while
levels are being rewritten in parallel. Everything else is yours: every beat,
`filler`, `profile`, `shelf`, `band`, `landmark`, `breaks`, `exit`,
`exit_beats`, and the whole `skin`.

---

## 7. The checklist

Run in this order. The first is free and catches most mistakes; the last is
the only one that actually decides.

```bash
python tools/tower_probe.py --design-only            # 0.2 s, after every edit
python tools/level_review.py --level N --all         # ~25 s: sheet, blueprint, seam, numbers
python tools/level_review.py --level N --outside     # Blender, the shape of the place
python -m pytest tests/test_tower.py -q              # ~36 s, the tower-wide invariants
```

A level is done when **all** of these hold:

| | |
|---|---|
| every authored jump legal on paper | `--design-only` clean |
| designed landings placed as authored | ≥ 90%, and no beat under 98% with ≥ 6 samples |
| unchecked emergency placements | 0 |
| plain hop | ≤ 70% of moves, ≥ 2 non-hop verbs used |
| covered by a no-jump walker | ≤ 55% mean, never end to end |
| designed content | ≥ 45% of the level's landings (the rest is the exit climb and machinery) |
| body inside the world | 0 frames |
| its structure held at 25° | ≥ 1.5 s |
| **the contact sheet** | **it looks like a place, and you would not confuse it with the level before it** |

The last row is the only one that has ever caught what was actually wrong. The
others are a floor.
