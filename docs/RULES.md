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
your own. Eighty to a hundred metres of arc, and a filler beat that repeats if
the terrace outlasts the script.

### **A level is nine to twelve landings, and two to five of them are yours**

Measured over 8 runs on all twenty levels, counting what actually gets laid.
This is the most important number in this document and nothing in the level
table says it:

| level | landings | authored | exit climb | lock | landmark |
|---|---|---|---|---|---|
| THE CRUCIBLE | 9.8 | **1.2** | **7.0** | 0.9 | 0.6 |
| ROPE BRIDGE | 10.1 | 1.9 | 4.9 | 1.6 | 1.5 |
| THE VAULT | 9.2 | 2.2 | 3.8 | 1.6 | 1.5 |
| WOOLWORKS | 7.2 | 2.9 | 2.0 | 1.2 | 1.1 |
| MARKET STREET | 9.9 | 3.4 | 3.9 | 1.8 | 0.9 |
| GLACIER SHELF (`breaks=0`) | 11.2 | **6.4** | 3.8 | **0.0** | 1.0 |
| CANOPY WALK | 25.8 | 13.4 | 7.6 | 2.0 | 2.6 |
| THE CISTERN | 26.2 | 16.2 | 6.5 | 3.2 | 0.0 |

**Everything past your fifth authored beat is never laid.** Seventeen of the
twenty levels lay five or fewer; a table that writes twelve landings is writing
twelve and showing four. Only CANOPY WALK, THE CISTERN and THE BALCONIES are
long enough to show a real script.

Three consequences, and they change how a level is written:

1. **Put the level's identity in the first two or three beats and in the
   filler.** The filler repeats; the tail of your script does not. This inverts
   the "showpiece at 60% of the way through" advice — that is what the
   *reference* does, and this engine cannot express it on most levels.
2. **The exit climb is the biggest single consumer of a level**, three to seven
   landings of every nine to twelve, and 71% of THE CRUCIBLE. `Level.exit_beats`
   writes it landing by landing with the generated climb still underneath as the
   fallback. Taking it back is the largest lever a level author has.
3. **`breaks=0` removes the lock.** Any `breaks >= 1` forces it — a level's
   first floor break is always 5.5–6.7 m wide — and it costs one to three
   landings. Legitimate whenever moats and the shelf's own wobble already hold
   the walk number down: GLACIER SHELF measures 27% covered with no breaks at
   all, against a 55% limit.

It is **one place**, not a stretch of corridor. The reference's levels are a
windmill farm, a market street, a mine gallery, a flooded cistern — you could
name each in one word after two seconds of looking at it, and you cannot name
"a bit of tower with some blocks on it".

**The three failures this pass exists to end**, all of them the owner's words
and all of them still true of the current roster:

1. *You can just run past half the obstacles.* Was: sixteen of the first
   twenty levels 100% plain hop over continuous ground. **Now: 0 of 33 levels
   walkable end to end, 41% mean coverage** against the real map's 46%.
2. *It's the same jump every time.* Was 94% plain hop. **Now 82%, with walk 8,
   slide 4, climb 3, bounce 2 and bubble 1** — an 18.5% non-hop share against
   about 6%. Note the research qualifies this one: the reference is hop-heavy
   too, and its variety is architectural rather than a vocabulary of special
   blocks (§2).
3. *It doesn't read as a place.* Was two or three materials a level against the
   reference's fourteen, and half of every frame empty sky. **Now six to eleven
   materials a level and 44–56% empty** — better, and still the weakest of the
   three: it is why the rule below tightened to 48%.

All three are measured over the whole rebuilt roster; the numbers a level is
held to individually are in §8.

---

## 1. The physics, exactly

One jump impulse and one horizontal speed. Nobody chose these; they are
Minecraft's own numbers converted from ticks, in `parkourkit`:

    GRAVITY 28.0    JUMP_V 8.4     AIR_SPEED 7.10 (in flight)
    RUN_SPEED 5.612 WALK_SPEED 4.317   MIN_HOP 2.0 m

**Three metres is the jump you are writing.** Measured off the real map's own
solved routes (`docs/RESEARCH.md` §3): 122 jumps, **modal 3.0 m, median 3.16,
mean 3.20, p90 4.12, max 5.10** — and 60% of them are level or up one. This is
the single most useful number here, because the temptation with an envelope in
front of you is to sit at the top of it, and the reference does not. Write your
ordinary jump at **`arc` 3.0–3.5**, let the level's harder beats run to
`arc` 4.0–4.4, and keep anything past that for one showpiece — but read the
next section first, because `arc` is not the distance the physics checks.

The reference also **almost never jumps down**: 2 of 122 jumps drop more than
one block. Our envelope is *more* generous below the horizontal than the real
map ever needs. Levels descend by **falling off an edge**, which costs nothing
and is free variety — see §3.

### `arc` is not the jump. Write this table down.

The number you write is `arc`; the number the physics checks is `arc` **minus
both landings' `EDGE`**, which for two ordinary blocks is **0.68 m**. An agent
lost a pass to this, so here it is explicitly:

| `arc` you write | reach the physics sees | legal at +1 | level | −1 |
|---|---|---|---|---|
| 2.6 | 1.92 | — | — | — |
| **2.8** | **2.12** | ok | ok | — |
| 3.2 | 2.52 | ok | ok | ok |
| 3.6 | 2.92 | ok | ok | ok |
| **3.8** | **3.12** | — | ok | ok |
| 4.4 | 3.72 | — | ok | ok |
| 4.9 | 4.22 | — | ok | ok |
| 5.4 | 4.72 | — | — | ok |

So **`arc` below 2.68 is illegal at every rise**, and **a rising hop's `arc`
cannot exceed 3.78**. An `arc=2.8` +1 hop — which much of the old roster was
written as — is a reach of 2.12 against a minimum of 2.00: the shortest legal
jump in the game, and the owner's "tiny jumps" complaint in one number.

One honest caveat on comparing to the reference. Its modal 3.0 m is a
*block-centre to block-centre* gap, which is the same quantity as `arc`, not as
reach. So writing `arc` 3.0–3.5 matches the reference's spacing; it just means
the *feet* only travel 2.3–2.8 m, because a body takes off and lands a third of
a block in from each edge. Both readings are defensible — what is not
defensible is `arc=2.8` everywhere, which is what the roster had.

**The jump envelope.** `hop_span(rise)` computes it in **reach**; no design may
sit outside it and `tools/tower_probe.py --design-only` refuses one that does.

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

**The one place the reference beats this envelope, and the way round it.** The
real map routinely jumps **four metres while gaining a block**; here, up-one
stops at 3.10 m. The mechanics that buy it there are ones this kernel does not
have (half-block slab and stair surfaces as *landing heights*, head-hitting to
cancel a jump, ice momentum). What you *can* do is split the climb:
`form="slab"` lands at **+0.5** and reaches **3.78 m**, so two slab steps gain
a block across seven metres of ground where one hop could only manage 3.10 —
and a slab step reads as a deliberate half-height ledge rather than a fudge.
`kind="slide"` off ice is the other answer: 4.36 m gaining a block.

**Hard rule.** Every authored hop and slide legal on paper:
`python tools/tower_probe.py --design-only` — 0.2 s, run it after every edit.
It names level, beat and node index.

---

## 2. The verbs — and the six the tower has never used

`kind=` on a node. The tower is 94% `hop` and six of the seven verbs have never
appeared in any level, so each was **placement-tested in an authored level**
before being written down here; the recipes are what actually fired, not what
the source suggests should. Read the box after the table before deciding how
much of your effort this deserves — the answer turned out to be "less than the
floor".

| verb | what it is | speed | verified recipe |
|---|---|---|---|
| `hop` | the default | 7.10 in air | — |
| `slide` | an ice jump: same arc time, **10.0 m/s across** | 10.0 | works flat out. `kind="slide"`, pair with `form="ice"` and an ice material. **Reaches 6.00 m level and 7.02 m down one** — half again a hop, and the easiest way to make a jump *read* as big |
| `bounce` | off a slime pad — **the only way a landing gains two blocks** | steered 2.6–7.81 | a landing whose **material** is slime (`n("slime", ...)`), then a node with `kind="bounce"` **and `spread` ≥ 1**. See §7 for the arrival speed it needs, which is the part that actually decides whether it fires. Note `form="slime"` is geometrically identical to `form="full"` — `SPRINGY` is imported by `spiralplan` and never read — so the *style* is what makes a pad, not the form |
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

### What the reference actually uses — and it is not a zoo of gadgets

Measured over the whole real map (`docs/RESEARCH.md` §2), because the honest
answer changes the rule:

| | on the walking line | legs using it |
|---|---|---|
| **lava** | 1,562 cells | **26 / 43** |
| **water** | 1,069 | **20 / 43** |
| **slime** | 155 | **26 / 43** — but only 189 cells in the entire map, in 46 clusters, **34 of them exactly 2×2** |
| magma | 442 | 10 / 43 |
| soul sand / soil | 355 | 7 / 43 |
| ice, packed and blue | 557 | **3 / 43** |
| ladder / vine | 52 / 84 | 7 / 43 each |
| **cobweb** | **0 in the entire map** | 0 |
| honey / scaffolding / powder snow | 2 / 3 / 25 cells, whole map | ~0 |

**Lava and water are the mechanic**; slime is *one 2×2 bounce pad per level*;
ice is a two-or-three-level speciality; cobweb, honey and scaffolding do not
exist. The median leg spends **15% of its walking band** on or beside a physics
block, and only two legs of forty-three have none at all.

And on the reference's own solved routes, **slime bounces are 16.4% of all
jumps** — because a real level only has **4.7 jumps in forty metres**. One pad,
used once, is a sixth of the level's parkour.

And the footage says it harder still. Across **~2,900 seconds** of reference
video read frame by frame: **no slime, no honey, no soul sand, no magma bounce,
no bubble column, and no cobweb waded through.** The only physics-altering
block on screen anywhere is **ice, as one level's ground**.

> **So the honest conclusion, which is not the one this document started with:
> a tower that is mostly plain hops is *matching* the reference, not falling
> short of it.** The reference's variety is architectural — rooms, shafts,
> hazard floors, ladders, stairs, ledges — not a vocabulary of special blocks.
> The verbs below are seasoning. **If you have a choice between spending an
> hour on a bounce pad and an hour on the level's floor palette, spend it on
> the floor.**

**Design rules — the verb quota, grounded in that:**

- **≤ 85% plain hop**, and **at least one non-hop verb firing in the level's
  own body** — not merely in its exit staircase, which is where the tower's
  entire current non-hop share lives.
- **The ladder is the one special block the reference leans on hard**, and it
  carries a whole level: a six-second climb up a dark shaft with a lit doorway
  at the top, and no staircase alternative. `kind="climb"` inside a
  `shell="shaft"` is that, and it is worth more than any other verb here.
- **One slime bounce pad**, roughly 2×2, where it fits. The Spiral save has one
  per level in 26 of 43; it is invisible in the footage because a 2×2 pad is
  easy to miss. It is also the only way this engine gains two blocks.
- **Liquid on or beside the walking line in at least one beat** — `moat=True`,
  `profile="channel"`, a lava or water cut through the level's own ground.
  This is the single most-used mechanic in the reference and this tower barely
  has it.
- **Stairs and slabs are the commonest non-cube form in the reference by a wide
  margin**, and `form="slab"` is barely used here. A half-height landing is
  cheap, reads as deliberate architecture, and buys reach (§1).
- **Ice is a speciality, not a staple.** Three levels of forty-three. If your
  level is the ice level, lean on it hard; otherwise leave it alone.
- **Cobweb and honey: don't.** Cobweb appears nowhere in either map and honey
  has no physics here at all.

---

## 3. The ground — and why you cannot just walk it

This is failure (1), and it is a property of the **floor**, not of the jumps.
If there is continuous ground under a beat, the parkour on top of it is
decoration and reads as decoration however good the jumps are.

**Hard-ish rule, measured:** a level must come in at **≤ 55% covered by a
no-jump walker, and must never be walkable end to end.** The real map measures
46% mean and 0 of 43 legs passable. Printed by `level_review --report` under
`CAN IT BE WALKED`, and tower-wide by `tools/bypass_probe.py`.

**But the reference does not achieve that by breaking a continuous ledge**, and
this is the part worth getting right. Read frame by frame, it does two things:

1. **The walking surface is two to four blocks wide with the drop directly
   outboard**, so there is nothing to walk *around*. This is most of the work.
2. **Where the ground is wide, its whole width is hazard.** A lava lake
   spanning the terrace with one lit block standing in it; a room whose entire
   floor is lava, crossed on a run of oak stairs; a stretch where the floor is
   the *sea* and the landings are lily pads. The landings are isolated single
   blocks with two or three blocks of hazard between them — **not a five-block
   chasm**.

And the nuance: **the rule is "no level walkable end to end", not "no metre
walkable".** At its widest the reference's ground stops being a course and
becomes a *place* — a village terrace with fences and a trough — and it lets
you walk that for a few seconds, because the level's entrance and exit are
still separated by a real break somewhere else. A level that is unwalkable
every single metre is as wrong as one you can stroll.

The levers, in the order they are worth reaching for:

1. **`profile="ledge"`** (the default). Ground is a shelf `shelf` cells wide
   against the core wall with the drop genuinely outboard. `shelf` floors at
   3.0 and is capped at `band - 2.0`. **`profile="plaza"` is a full floor and a bare
   one is the thing that killed the last tower** — but a plaza *with breaks and
   hazard cut through it* is the reference's own "wide ground, whole width
   hazard", and it measures well: ledge → plaza on one level, with `breaks` 3→4
   and three lava moats, took the no-jump walker from 41% to **31%** and the
   empty frame from 60% to **50%**. Use it for a level that dresses the floor
   as a real place, and then break it hard. What fails is the *undressed*
   plaza, not the profile.
2. **`breaks=`** — in-level floor gaps. Three for a ledge, two for a full
   floor, by default. The first break wider than 4.5 m gets a *lock*: an
   approach at height, an island floated over the hole, a landing on the far
   ground. More breaks is the bluntest and most reliable way to move the walk
   number.
3. **`pedestal=False`** floats a landing with nothing under it. A run of
   floating landings over the drop cannot be walked by construction.
4. **`moat=True`** cuts the theme's liquid under the jump — a radius-3 disc of
   ground dug out and filled. Verified: two `moat=True` nodes put about **70
   liquid cells** into a level, and `profile="channel"` roughly doubles it.
   `pedestal_style="lava"` picks the liquid where the theme's own is wrong.
   This is the reference's single most-used mechanic and this tower barely has
   it.
5. **`form="floor"`** is the opposite and must be used deliberately: it places
   *no block*, requires the cell to be solid ground already, and is how a beat
   says "run along the terrace here". Every `form="floor"` landing is a metre
   of walkable ground you are choosing to give away.

**Design rule.** No more than three consecutive `form="floor"` landings, and
never a whole beat of them.

### The net motion is up, and the ladder is not the answer to every level

Owner's note on the first preview run, 2026-08-13: *"whenever there's some way
you want to get up, it just puts a ladder there... and then from the high
ladder point they just jump back down to a lower part than where the ladder
was. The whole idea is that it keeps going up by level."* Both halves measured
and both are real.

**Too many ladders, and it is this document's fault.** §2 says the ladder is
the one special block the reference leans on hard, and twenty levels took it:
**17 of the 20 rebuilt levels now exit by a climb** — 12 ladder, 4 bubble, 1
vine, against 3 by stair. The roster before this pass was the other way round.
And the reference is nothing like either: **ladders appear in 7 of its 43
legs**, about one level in six.

> **Design rule.** A climb exit belongs on **about one level in five**. It is
> for a level whose *idea* is the climb — a bell tower, a mine shaft, a well.
> A level that merely needs to get out uses a stair, and a stair on a themed
> footing (`step`) is not a worse ending, it is a quieter one.

**And the run must not undo itself.** Measured over six runs: the level seam
itself is fine — median +0 blocks, and only 4% of seams start the next level
two or more below the top of the climb, which is the designed `hop_span(-1)`
crossing doing its job. The problem is *inside* the level: **23% of levels drop
three or more blocks after their own high point**, WINDMILL REACH by 4.5 and
THE TIMBERWORKS by 4.0. Put a tall ladder at the end of a level that has just
dropped four and the eye reads the whole thing as climb-then-fall.

That descent came from the rule below, which is right — the reference travels
eleven blocks vertically to gain four. What the reference does *not* do is
spend the descent at the end. It falls off edges early and in the middle, and
the last thing before the seam is the way out.

> **Design rule.** A level's own descent belongs in its **first two thirds**.
> The exit is the highest thing in the level, and nothing after it goes down.
> Keep the drop after a level's high point under three blocks.

### A level goes down as well as up

Measured on the real map: **36 of 43 legs descend somewhere, and 22 dip below
their own starting checkpoint.** A leg travels eleven blocks vertically to gain
four — a ratio of **3.36 to 1**. Every level in this tower is a monotonic
climb, and that alone makes them feel like a corridor rather than a place.

The reference does not *jump* down — 2 of 122 jumps drop more than one block.
It **falls off an edge**, which costs nothing and needs no jump at all. In this
vocabulary that is a lower `lift` on the next landing, a `step_y` descent, a
drop into a pit or a channel and a climb back out. Use it: it is free variety,
free exposure, and it is how you get a view back down over where you have been.

**Design rule.** A level descends somewhere. Net rise across the level is the
frozen `rise`, but the *path* need not be monotonic and should not be.

**The corridor.** `band` is the level's own width, core face to rim: 7.5 is a
gallery whose walls press in, 13.0 is a court. Both are levels; a tower where
every level is 9.5 is a corridor. The course itself keeps 2.0 off each edge.
Landings may stand **past the rim** on floating spurs by asking for a `hug`
larger than the band — the real map's course wanders twenty blocks radially
and that is much of why its levels read as places.

---

## 4. Structures

**First, the awkward measurement: the real map has no landmark per level.** The
median biggest thing standing on a real terrace is **12 cells and 4 blocks
tall**, the median leg has **zero** masses over 20 cells, and the few big ones
are a tree, a wooded knoll, a rock outcrop — terrain, not architecture. The
biggest genuinely *built* thing found anywhere in forty-three levels is 9×4×7.

That does **not** mean delete the landmarks. It means know what they are for.
The reference tells levels apart by their **floor palette** (§5), and this
tower has never done that; the landmark was added because the owner could not
tell our levels apart, and it measurably helped — running the course *through*
a structure took levels holding one at readable size from 20% to 52%. So:

- **The level's identity is its ground.** Fourteen materials, a committed
  dominant colour, detail underfoot. Do this first.
- **Then one structure, kept honest.** One thing you would name the place
  after, sized to be seen, and ideally passed through rather than admired from
  outside.
- **And several small ones.** The reference's terraces are covered in
  four-block furniture — a tree, a fence, a cart, an outcrop. A level with one
  big object and nothing else is not what the reference looks like either.

The rest of this section is about making the big one work, and — this is the
part that took a probe to learn — **placing it is not the same as it being
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

**The tower's own design doc says the reference alternates exposed ledge and
enclosed interior every ten to twenty seconds. Measured, that is false**, and
it is worth knowing before you build a level around it. Over 1,662 metre-samples
of the real map: fully enclosed **6.1%** of the way, **0 of 43** legs enclosed
more than half, and an enclosed run lasts a **median of two metres**. Twenty of
forty-three legs are essentially never enclosed.

What it does instead is uniform, and better:

| | |
|---|---|
| a wall within 4 m on at least one side | **71%** of samples (median distance **3 m**) |
| a rock lid somewhere overhead | **98%** of samples (median **8 blocks** up) |
| roof within 6 | 25% |
| open runs | median **13 m** |

**The real shape is a groove**: a shelf with rock a few metres away on one
side, the open drop on the other, and a lid eight blocks overhead. Almost
always half-enclosed; almost never fully enclosed; **almost never actually open
to the sky.**

- **Design rule.** The groove is the default and you should be building it:
  something solid within about 4 m on the core side, the drop outboard, and
  something overhead. An interior is a **two-metre pinch** — a doorway, an
  overhang, a short tunnel — not a fifteen-second room. One or two `shell=`
  beats in a level is right; a level that is a tunnel throughout is as wrong as
  one that is an open plate throughout.

### The composition rule — read the reference sheet before you argue with this

Put `docs/reference/sheets/ps1_sheet_a.jpg` beside a contact sheet of any level
in this tower and the difference is not the parkour, it is **what is in the top
half of the frame**.

In the real map, nearly every frame is built the same way: the **overhanging
rock brow fills the top of the frame**, ragged and dark; the **level's own
coloured ground fills the bottom** — grass, terracotta, gold, cherry pink,
nether red; and the sky is a bright *slot* between the two. Measured over 325
reference frames:

| | |
|---|---|
| the top fifth of the screen, share of its pixels that are dark rock | **63%** |
| frames whose top fifth is more than half dark rock | **73%** |
| seconds showing no sky at all | 20.8% |
| luminance standard deviation across the frame | mean **65.8** — these frames are not flat |

In this tower the top of the frame is sky in almost every frame of almost every
level, the bottom is grey cone stone, and the level's colour is two isolated
cubes floating in it. Measured: **43–77% of the view is empty sky, sea or
drop**, and half the levels are unidentifiable from a still.

**The overhang is what deletes every wrong answer above you.** You are in a
slot; the roof is the underside of the level above; the floor is the lightest
thing in the lower half and the cliff the darkest in the upper; and the only
bright exit is forward.

Three things follow, and they are the level designer's, not the renderer's:

1. **Build upward.** Something must be over the body — a `shell` roof, a
   `ceiling=` lid, a canopy, a gantry, the underside of a structure the course
   passes beneath. A level with nothing above head height will always frame as
   sky.
2. **Commit to a colour.** The reference's frames are *one strong hue* plus
   dark rock: a whole frame of gold, a whole frame of pink, a whole frame of
   red. Not a grey plate with a red cube on it. Skin the level's `ground` and
   `sub` as well as its `rock` — the ground is a third of every frame and it is
   currently the cone's own stone in most levels.
3. **Fill the near ground.** The reference is never a bare plate: there is
   always small detail underfoot at the bottom of the frame. Props, fences,
   lamps, path materials, a liquid channel.

**Design rule.** Empty frame **under 48%** on average, printed by
`level_review --report`. It was 55% and that was too lax: six of the back
thirteen passed it at 45–55% and still read as two cubes low-left against a
pale blue wash when the owner looked at a contact sheet. The reference sits
near 45%.

**And the number is not the rule — the intent is.** The probe cannot see a
roof higher than 4.6 m over the eye (§7), so a level can sit at 47% and still
frame as sky, or fill the top of every shot with a high soffit and read as
"empty". What you are actually building is the reference's composition: **the
dark brow filling the top of the frame** — it is more than half dark rock in
73% of reference shots — **the level's own coloured ground filling the
bottom, and the sky as a bright slot between them.** Judge that on the sheet.
- **Design rule — palette. Fourteen materials, not three.** This is the rule
  that changed most on measuring the real map, and it is probably the single
  biggest reason its levels read as places and ours read as boxes. A real leg
  uses a **median 14 distinct floor materials** (min 7, max 26), **no material
  owns more than half** of any level (median dominant share **26%**), and it
  takes a **median 7 kinds to cover 80%** of what you see. The theme is one
  strong material at about a quarter with a long tail underneath — sand 44%,
  or podzol 24%, or honeycomb 25% — never a two-tone plate.

  This tower gives a level six roles (`ground`, `sub`, `rock`, `accent`,
  `glow`, `liquid`) and most levels set two or three. Use all six, vary
  `style` per node rather than naming the same role every time, and let the
  props and the `deco` carry more kinds on top. **Identity comes from the
  floor**, not from the one big structure — see §4.
### Route legibility — four devices, all cheap, none of them used here

Read off the footage. There is no HUD and you never hesitate.

1. **The route is painted.** A stripe of a different floor material down the
   middle of every terrace wide enough to be ambiguous — a dirt path across
   grass, gravel through a garden, a carpet runner down a hall. Where the
   ground could be read two ways, it is coloured.
2. **Every lamp is at the far end.** Lanterns hang at a corridor's *exit*, not
   spread through it. A lamp post stands at the tip of the promontory where the
   course turns. **There is no ambient decorative lighting anywhere in the
   reference — every light in those frames is doing a job.** Put nothing
   decorative in the middle distance.
3. **The landmark stands where the ledge ends**, not in the middle of the
   terrace. It is the turn signal.
4. **Silhouettes against sky are legible; anything against the cliff is not.**
   If you want something seen, put sky behind it.

### A level has a threshold

The reference signposts where a level *begins* and lets geometry say where it
ends: **an emissive block set flush in the floor, on a rise, on screen 2.3
seconds before it is reached — and the palette changes completely at that
block**, in one or two frames, with no blend. Nine seams in two minutes, every
one abrupt, and no two adjacent levels sharing a dominant hue.

**Design rule.** Your level's first beat is a threshold: a light, a material
change, and something to aim at. Its `skin` must not share a dominant colour
with the level before it — check `--seam`.

- **Light is a level's own.** Interiors carry their own lamps; the `glow` role
  and `deco="lamp"` are what make a dark level legible rather than black.
- **Fine dressing is for the still, not for the strip.** Flowers, grass tufts,
  ore speckle and moss are in almost every reference frame and contribute
  essentially nothing at glance distance. Value contrast, emissives,
  silhouettes and the route stripe are what read at speed.

---

## 6. The shape of a level

Beats are laid **whole or not at all**, in order, and `filler` repeats if the
terrace outlasts the script — so put the level's *character* in the filler and
its *surprise* in a beat. Filler loops back on itself, and the seam from its
last landing to its first is checked; get it wrong and half your fidelity loss
is there.

A level that works has:

1. **an opening** that says where you are — the threshold light, the complete
   material change, the structure in frame;
2. **an escalation** — the beats get harder, not louder;
3. **one showpiece**, and the reference puts it at about **60% of the way
   through the level**, not at the end. Difficulty is the punctuation, not the
   sentence;
4. **an exit that geometry announces** — the ledge narrowing to a tongue that
   ends in air, or a lit doorway. The reference does not signpost exits the way
   it signposts entrances.

The reference's levels run **10–15 seconds** (mean 12); ours are 6–10. That is
a deliberate difference — this is an overlay strip, not a map you sit down to
play — but it means your level has *less* room than the reference's to say what
it is, so the threshold and the palette have to do more work, not less.

**Frozen for this pass:** a level's `name`, `theme` and `rise`. `rise` is
cyclic — any three consecutive rises *are* the head-room over the lowest of
them (`sum − 5` must land in 6…16) — so it cannot be a per-level decision while
levels are being rewritten in parallel. Everything else is yours: every beat,
`filler`, `profile`, `shelf`, `band`, `landmark`, `breaks`, `exit`,
`exit_beats`, and the whole `skin`.

---

## 7. Field notes — things that only turn up when you build a level

Measured by agents rebuilding levels against this document. Each cost real
time; none is guessable from the source.

- **An in-body `climb` needs `pedestal=True`.** `_climb_move` wants solid rock
  beside the ladder column at its middle *and* its top, and out in the lane the
  only candidate is the landing's own pedestal stack. The generated climbs get
  away with `pedestal=False` because a `shaft` shell supplies the wall.
  Measured: 89% of the beat placed with the pedestal, 43% without, and the
  climb silently degrades to hops. **`hug=2.4` works** for a climb, wider than
  the 1.6–2.0 quoted in §2.
- **`step_y` on a climb is not freely tunable.** The same node at `step_y=4`
  fires; at `step_y=3` the beat fell to 43%, `climb` vanished from the move mix
  entirely, and the level's *exit* ladder fell back to a staircase with it. No
  explanation found — if a climb will not fire, try moving `step_y` before
  assuming the position is wrong.
- **A gated landmark cannot stand on a `channel` level.** The liquid cut runs
  where the lane runs and `Cone.rock` is False under it, so the structure's
  base cells fail: 1 reservation in 8 runs on a channel against 8 in 8 on a
  ledge.
- **`walk` gates almost never reserve on a `ledge`** — windmill, watchtower and
  cabin came in at 0–2 of 8 across every band and shelf tried, where the `hop`
  gates (arch, totem, bell, hoodoo, crane, hoard, tree, greatcap) reserve 8 of
  8 in the same conditions. And an *ungated* landmark cannot reserve on a ledge
  at all. So a ledge level's real choice is **a hop gate or nothing**.
- **Any `breaks >= 1` forces the lock**, because a level's first floor break is
  always 5.5–6.7 m wide. The lock plus a landmark crossing can be two thirds of
  a level's landings — designed content fell 56% to 27–39% purely by turning
  breaks on. `breaks=0` is legitimate when moats and a wobbling shelf already
  hold the walk number down; one level measured 27% covered with no breaks at
  all.
- **A shell's roof builds even where its walls find no footing**, because the
  roof loop sits outside the footing check. On a narrow ledge that hands you
  the reference's groove for free — lid overhead, wall on the core side, drop
  outboard. But **three shelled landings in a row jam the lens** on 10% of
  frames (`tunnel`) to 21% (`hall`). One shell is a pinch; three is a corridor.
- **`--design-only` checks `hop` and `slide` only.** Note that
  `spiralplan.BALLISTIC` is a *different* set that also contains `walk` — that
  one is the placement-time "nothing rises two blocks" clamp, not the paper
  check. A `walk`, `climb`, `bubble`, `web` or `bounce` is still only ever
  proved by a placement count.
- **`ceiling=3` over a `kind="walk"` leg is a real head-hitter** that the arc
  clearance test never refuses, because a walk has no arc. This is the genre's
  `2bc` — the lid you sprint under — expressible today.
- **A climb or bubble that cannot anchor silently becomes a staircase.**
  `_climb_move` wants solid rock within one cell of its column at the column's
  **middle index** and at its **top**, and a column standing mid-lane has
  nothing to grab whatever it stands on. Instrumented: 674 of 819 candidates
  refused for "no anchor" on a vine, and **11,097 of 13,000 on a generated
  bubble exit, which became a six-step staircase — a third of that level —
  with nothing reporting it.** The recipe: a pedestal under the column *and* a
  rise of at least four blocks, so the middle index lands on the landing rather
  than on the stack below. Always check the move mix for `climb`/`bubble` by
  name; absence is silent.
- **Machinery is inserted *between* script beats and leaves the body back at
  lift 1.** So a beat whose first node drops off the height the previous beat
  climbed to drops nothing about half the time — a `bounce` there silently
  becomes a hop and the beat still reads as placed. **Put the rise and the drop
  in the same beat.** Same class as the walk-first-in-a-beat trap above.
- **The bounce needs an arrival speed, and the arithmetic is exact.** It fires
  only at `impact >= 7.0` m/s. A level hop arrives at **5.4 and cannot bounce
  at all**. A one-block drop across a 4.4 m arc arrives at 9.2 and is thrown
  back **one** block; **two** blocks needs `impact >= 11.0`, i.e. a two-block
  drop across 4.4 m or more. So a bounce pad must be at the bottom of a real
  fall, and how high it throws you is decided by that fall.
- **...and the feed jump must survive its own *short fallback arc*.** `_node`
  offers `arc * 0.84` as a fallback, and at that length a one-block drop lands
  at impact 6.75 against the 6.72 threshold — the bounce is refused and
  silently becomes a hop with the beat still reading as placed. Write the feed
  at `arc=4.9–5.2`, near the top of the envelope, so the 0.84 fallback is still
  about 4.2 m. `spread >= 1` on its own does not save it.
- **A shell grows walls only at `lift=1`.** `_shell` skips any wall column with
  nothing under it, so a higher beat gets a roof and open sides. And a walled
  bay fills the two cells either side of the move four high, so the landing
  *after* one must stay in the corridor: shelling a doorway at lift 1 and
  stepping the next beat to lift 2 took that beat from 100% placed to 62%.
- **A wide shelf costs the exit climb its lane.** `shelf=5.0, band=9.0` gave 15
  unchecked placements in 8 runs; `shelf=3.5, band=8.0` with nothing else
  changed gave 1 — and took walker coverage from 57% to 20% as well.
- **A gated landmark moves the level's breaks** (kept 9 m clear, far side of
  the apron only), which pushes the first uncrossable gap past halfway and
  raises walker coverage by about 20 points. But removing the gate to get that
  back was much worse on every other count: 6 of 8 runs looped and 14 unchecked
  placements. The crossing is what keeps the frontier in its lane.
- **Half the landmark blueprints name materials literally** (`_lm_g_hoodoo` is
  terracotta whatever your theme is) and half take `theme.rock`/`accent`/`glow`
  (`_lm_g_arch`, `_lm_g_bell`). Pick one that takes roles or the level gets a
  structure from another biome standing in it. And `_lm_g_tree` hangs its
  canopy at dy 5–6, so any landing at lift 4 or above on a `tree` level puts
  the camera inside the leaves.
- **Reported, not reproduced: a level's usable shelf may be bounded by the
  `core_r` of the level three below**, that being the cliff at your back, with
  anything inboard of it painted as cone skin. One level at `band=11.5` had 65%
  of the cell the body stands on come out as `conerib` — a jungle that rendered
  as a grey plate — and dropping `band` to match the level three below fixed
  it. A check of `cone.rock` across the roster reads under 1% everywhere and
  the terrace floor is analytic rather than in `course.struct`, so this is
  recorded as a **symptom to look for** rather than a rule: if the floor under
  the body reads as grey cone stone in a contact sheet, try the band.
- **A `shell=` or `moat=` is painted the moment its landing commits, and blocks
  the *next* landing of the same beat.** Put `shell=` on a beat's **last** node,
  and keep two `moat=True` landings more than the pond's radius (3 cells) apart
  or the second stands in the hole the first dug. One level's nave sat at 81%
  through four passes on exactly this.
- **`_targets` can return nothing and record no rejection**, so a beat reads 0%
  placed with an empty trace. The cause is always `wants_ground` over a floor
  break, or `hug` past the shelf edge — and a ledge's shelf wobbles about ±1.3
  around `shelf`. `pedestal=False` is the fix; it took one gallery from 0% to
  100%.
- **Changing `breaks` moves *every* break, not just how many.** The position is
  `f = 0.14 + (k + h) * (0.52 / n)`, so a beat at 100% with `breaks=4` can be at
  0% with `breaks=3` for no other reason.
- **The generated exit ladder essentially never fires.** `_ascent_climb` swept
  across `hug` 1.4–3.0 gave at best 12 successful climb-moves in 2,751
  candidates — "no wall to hang on" every time — and the exit climb's length did
  not move at any value. This is why almost every level's way out is a
  staircase whatever its `exit` says, and it is the same anchor problem as the
  in-body climb above.
- **A water moat is a pit; a lava moat is a floor.** Water is in `SEE_THROUGH`,
  so the walker drops into the bowl the moat digs and cannot step back out —
  that is the 65.8% → 25.8% below. Lava is **solid**, so the walker simply walks
  across the top of it: a lava moat buys atmosphere and nothing at all for
  walkability. If your theme's liquid is lava and you need the walk number
  down, you need holes.
- **`moat=True` and `pedestal_style=` on the same node fill the pond with that
  solid material.** `Course._moat` digs its bowl and fills it with
  `pedestal_style or theme.liquid`, so a landing written with both cuts a hole
  and packs it with walkable stone — no error, no rejection, nothing in the
  fidelity table, and the unwalkability the moat existed for silently gone.
  Two levels shipped it in a first draft. It is a natural pair to write when
  the plinth under a landing wants a colour; it is recorded here as well as in
  `docs/LEVEL_BRIEF.md` because this is the file open when the node is being
  written.
- **Never repeat a `moat` in a `filler`.** The filler loops, and the second lap
  digs away the ground the first lap's pedestals stand on: 27,859 "pedestal
  will not stand" refusals from one keyword.
- **A pedestal cannot stand in a `channel` cut**, and `hug` on a `ledge` is
  load-bearing — unhugged, `_targets` pulls the course to the *outer* edge of
  its own shelf.
- **`frame empty` is seed-noisy: average it.** The same unchanged level read
  45% on seed 3 and 38% on seed 5. Quote a mean over several seeds with the
  range, never one seed — most of the numbers in this document's history are
  single-seed and should be read with that in mind.
- **Changing a level re-rolls the levels above it.** The tower is one
  continuous run, so a neighbour's edit moves your numbers: the same unchanged
  design measured 56 / 43 / 62% designed content and 98 / 96 / 95% exact across
  three worlds that differed only in the level below it. **A before/after of
  ±10 points on one seed is not evidence.** If a row moves and you did not
  touch what it measures, hold the neighbour fixed and re-measure — that A/B is
  the only way to tell your change from the re-roll.
- **The emptiness is overhead, not underfoot.** Instrumented by ray direction:
  the fan's two *up*-rows were 57–77% empty against the down-rows' 13–46%. And
  by beat, the exit climb is the bill — 42% of the run at 42–46% empty. **The
  single biggest win is roofing the exit's launch**, worth about four points on
  its own. `shell="cave"` on the launch landing takes its chimney from the
  reserved climb cells for free; `shell="shaft"` closes the gap completely and
  is rejected, because it puts the body 0.46 m inside the tube wall on three
  frames of every six hundred.
- **A `ceiling=n` beam is spread *along the direction of travel* and checked
  against the feet**, so a climbing tread takes one as happily as a `walk`
  does. That reconciles the two measurements above: **one** lid is worth about
  a tenth of a point, but **chained beat to beat** it fills the one column of
  the ray fan that looks where you are going — beams on an exit climb alone
  took it from 64% to 55% empty.
- **A `shell` roof sits in the cell the head sweeps at a hop's apex**, so
  `write` refuses it there: a tunnel over a jump is a roof with a hole in the
  middle of it. It only survives whole over a `walk`.
- **Overhead mass belongs on a beat's first two nodes.** A beat's tail is
  almost never laid — two beats contributed one landing each per run — so a
  shell or a lid written last is written and never seen. Same shape as the
  non-hop-verb rule above.
- **Widening the `shelf` is the frame lever on a narrow level, and it is free
  or better.** The ground *beside* the lane is what the down-rays miss: 4.5→6.0
  moved the fan's bottom row from 32% empty to 19% and the row below the horizon
  from 44% to 33%, and it **improved** fidelity, because a pedestal on a ledge
  then has ground to find. This contradicts the "a wide shelf costs the exit
  climb its lane" note above — that was measured at `band=9.0`, and with a block
  of band to spare it does not hold. Check both before choosing.
- **Lids and shells are near-noise on a narrow `ledge`.** A shell's two wall
  columns land one cell inside the cliff and one cell past the shelf edge, so it
  writes about thirteen cells, all roof — `cave`, `hall` and `tunnel` produced
  worlds identical to the last decimal on one level, and `ceiling=` beams bought
  0.7 and 0.2 points. The "two shells on the highest landings are worth five"
  measurement was taken on a wide level and does not transfer to a four-block
  shelf.
- **An authored `exit_beats` list shorter than `need` is discarded whole.** The
  crossing is refused and `_pending` is replaced by the unlidded generated
  stair — four treads left one level at 59% empty where eight roofed,
  pedestalled treads at `hug=1.8` reached 49%, at identical exactness, unchecked
  count and move mix. And `need` does not shrink because your design ends high:
  machinery between beats puts the body back at lift 1, so it is 6–7 whatever
  the level does.
- **A wider `shelf` can break the gated-landmark crossing.** Measured on one
  level: `shelf=5.0` passes `test_the_course_goes_through_the_landmarks_it_gates`
  and 5.2 and 5.5 both fail it, with a crossing falling through to the unchecked
  answer. The frame cost of staying at 5.0 was under a point. Widening a shelf
  is a tower-test change, not a local one.
- **`lift` is not a universal frame lever.** It is worth about ten points where
  the shelf is wide enough for the down-rays to land on, and **nothing at all on
  a narrow ledge**, where they clear the shelf into the void at any height.
- **Only five material names emit light.** `spiral._GLOWING` is `lantern`,
  `torch`, `glowstone`, `sealantern`, `magma` — and `magma` is the only warm
  one. `shroomlight`, `pumpkin` and the rest are bright *textures* that emit
  nothing. This decides a whole palette: a jack-o-lantern field is lit by
  magma or it is not lit.
- **A `ceiling=` lid is the cheapest overhead mass, and it darkens the level.**
  The lid cells are real, so the lens probe counts them — but a lid within
  eight blocks of the head also makes `_indoor_want` return 0.85, which takes
  27% off every tint in the frame. **Lid half the landings, not all of them** — except above `dark=0.85`, where
  `_indoor_want` returns `max(theme.dark, 0.85)` and a lid costs nothing at all.
  A level inheriting `deepdark`'s 0.86 was being lit as a cave whatever it did;
  every authored level with an opinion sits at 0.25–0.62.
  And `pedestal_style` paints the lid as well as the plinth, so a floating
  landing can carry a differently-coloured roof for free.
- **A structure you run *between* beats one you run *under*, on the frame.**
  Same seed: a bell's two five-tall posts either side of the passage read 54%
  empty; a tree, whose trunk stands off the run and whose canopy hangs clear
  above the lids, read 60%.
- **The slime pad is unreliable even written exactly to the recipe above.**
  Measured over 24 runs with `pedestal=False`, `spread=1` and a three-block
  drop over a 6.0 arc so the 0.84 fallback is still three blocks: it **placed
  on 6 runs of 24 and fired on 1**, and cost two beats of terrace. Two
  reliable `walk` strides bought more non-hop share than the pad ever did.
  Treat a bounce as a flourish you can afford to lose, never as the level's
  signature verb.
- **Measuring a level above about 20 needs a longer sweep.** `level_review`'s
  fidelity, move mix and walk run **unpinned**, so they have to climb to the
  level; at the old default a level in the twenties was a truncated tail. Level
  25 sampled 17 designed landings at `--blocks 260` against 120 once the sweep
  scaled, and its hop share read 82% against 76%. The tool now scales the floor
  with the level index (`level_review.reach`), but any hand-rolled sweep needs
  the same.
- **A beat's first node belongs at `lift=1`, and this is a *fidelity* lever.**
  Machinery leaves the body at lift 1, so a beat opening at lift 2 is asking for
  a rise it may not have. Measured on four separate beats by two agents:
  86% → 100%, 81% → 100%, 78% → 92%, 67% → 100%. One line each.
- **Centre a `+1` hop's `arc` at 3.2, not 3.6.** 3.6 is a reach of 2.92 against
  a window topping out at 3.10, so it is the arc that has to fall back — and a
  fallback is not `exact`. Worth several points a beat.
- **`spread` cannot rescue exactness.** `exact` is `trial is node` in
  `Course._attempt`, so *any* fallback — of lift **or** arc — counts as inexact.
  Raising `spread` converts a lost landing into a fallback, which reads the same
  in the fidelity number and better in the placement one. Know which you are
  moving.
- **Floor breaks are a *frame* lever, not only a walker lever.** One level read
  58% empty with `breaks=0` and 53% with a single break, walker coverage
  unchanged — the lock's approach stack and its island stand in the corridor
  ahead of the body where an open shelf has nothing.
- **A `ceiling=` lid is legal over a *level* hop, not only over a `walk`.** A
  flat hop's apex is 1.25 m and the lid sits at 3, so a flat filler can be
  roofed at every landing. It is the cheapest thing a level author has against
  the sky. A `shell="tunnel"` on two treads of an exit stair is the other one:
  56% → 54% empty at no fidelity cost, and the exit climb is the emptiest third
  of a level.
- **A tall `rise` on a narrow `ledge` makes the exit climb lap the tower.**
  ECHO SHAFT at `rise=8` on a 3.5-cell shelf failed the twice-claimed
  invariant: its exit staircase came back over its own cells one lap later.
  `profile="plaza"` fixed it and cost only walkability (4% → 33%, against a 55%
  ceiling). Reserve is `(need + 1) * 3.2` metres, so the tallest levels need the
  widest ground — the opposite of the "narrow shelf helps the climb" note above,
  which holds at ordinary rises.
- **`shell="shaft"` around an authored exit climb is expensive and not needed.**
  Taking it off one vine took *body inside the world* from 3 frames of 556 to
  **0** and the jammed lens from 18.2% to 10.4%, and the climb still anchored —
  the pedestal plus `step_y >= 4` recipe is sufficient on its own, and the tube
  is what puts the body in the wall. A second agent independently reverted a
  shaft shell for the same symptom.
- **On a `ledge`, *every* landing needs a `hug`, not just the climbs.** An
  unhugged landing is pulled to the middle of the **band**, which on a 4-block
  shelf inside a 10-block band is out over the drop. Two beats came out at 67%
  and 0% placed with an unchecked emergency behind them; hugging everything to
  2.4–3.2 took the same design to 100% and zero.
- **The exit climb's reserve is what decides how much design a level gets.**
  `want = (need + 1) * ASCENT_ARC + gap + …` with `ASCENT_ARC = 3.2`, measured
  from wherever the body is standing — so a tall `rise` eats the terrace before
  a single beat is laid, and a beat that leaves the body low costs the *next*
  beat several metres of room. Short beats that gain height early are worth
  more than long ones, and since a beat is truncated in the middle, whatever it
  is about must be in its first two nodes.
- *Unverified hypothesis:* a single `moat` on a beat's **first** node may eat
  the ground about 2.5 m downstream and cost that beat's next landing. It
  follows from the radius-3 bowl and the two-moats-apart rule above, but moving
  the moat did not fix the beat it was proposed for. Treat as a lead, not a
  rule.
- **A bounce pad's material is free.** `SPRINGY` is imported by `spiralplan`
  and **never read**; the physics is entirely `kind="bounce"` on the next node
  against `prev["impact"]`. So `n("magma", form="slime", pedestal=False)`
  bounces exactly like slime does, which is what lets a bounce stay on theme —
  a green slime cube in a nether vent field is not a place. (Earlier drafts of
  §2 said first the `form` and then the *material* made a pad. Neither does.)
- **Empty frame is driven by `lift` more than by band or lids.** The ray fan is
  ±36° vertical inside 8 m, so at `lift 1` the ground a metre below is hit by
  two whole rows of it, and at `lift 4` the shallow down-rows fly over the
  shelf into the void. A level that must run high — a tall `rise` with a stair
  exit — starts about **10 points of empty frame down** before anything else is
  decided. And `ceiling=n` is a one-cell beam that answers only the centre
  column of the fan; a `shell` roof is five to seven cells wide and is the only
  real lid. Two shells added anywhere moved it under half a point; the two on
  the *highest* landings were worth five.
- **A slime pad must be `pedestal=False`.** With a pedestal it is only offered
  cells that have ground under them, and at the foot of a fall there are none:
  3 of 6 placed became 7 of 7.
- **`shell=` on a landing blocks the move *out* of it**, because `_shell` wraps
  the arc that *arrived* and its roof then refuses the next arc. Put the shell
  on the landing **after** the move you want roofed — a `cave` on a bounce's own
  landing killed the bounce.
- **A `walk` gate can be refused on every bearing.** `GATE_NODES["walk"]` is
  `(-3, 0, 3)` against a 1.4–3.05 m window, and it also wants five supported
  cells across the corridor, so it fails "no support under base" on any narrow
  or `ledge` level: refused 20 of 20 on one level where a `hop` gate reserved
  4 of 4. The walk gates are `watchtower`, `windmill` and `cabin`.
- **A non-hop verb belongs at position *two* of a beat, never at its tail.**
  A beat lays about half its nodes, so a `walk` or a `bounce` written last is
  written and never seen. Moving each walk to position two and changing nothing
  else took one level from **100% plain hop to 83%**. This is the corollary of
  the truncation note above and of "a walk is never a beat's first node".
- **A gated landmark on a `channel` level costs the level's second half.** The
  reservation fails there (above), and the bill is measurable: same eight runs,
  landmark on against off, designed content **42% → 57%**, the exit climb 30 →
  24 landings, and the last two script beats went from 2 and 1 landings to 6 and
  9 — the crossing is inserted between beats and eats whatever is due next. It
  bought 0.9 s of structure on screen.
- **Splitting a long exit ladder: the earlier negative result was wrong, and
  why is instructive.** It was measured as "116 of 640 jammed frames both ways,
  to the frame" — but the ladder was **not firing at all** in either arm, so
  both were a staircase and of course they matched. Re-measured with the climb
  actually anchoring: `step_y=8` is nine consecutive flat-grey frames on the
  sheet and takes the jam to 22.5%, against `step_y=6`. **Shorten the exit
  climb.** Before trusting any A/B on a climb, check the move mix shows
  `climb`/`bubble` by name in *both* arms.
- **`pedestal=False` also fixes the beat parked at 89-92%.** The note above
  offers it for a beat at 0% with an empty trace; the commoner symptom is a beat
  stuck just under target for several passes, because a pedestal on a `ledge`
  must find ground under a shelf that wobbles about ±1.3 and has holes in it.
  Floating the two ledge-dependent landings in three beats took one level from
  90% exact with beats at 89/90/90 to **98% with every script beat at 100%**.
- **The node after a beat's opener must ask for the *same* `lift`.** A beat's
  first node carries `spread` (it is placed from wherever machinery left the
  body), so it sits a block high or low about a fifth of the time — and
  `lift + 1` on the node after it is then a rise of two, which nothing makes.
  The same `lift` is +1 / level / −1, all legal. Measured on one beat:
  78% → 92%. For the same reason, **write a threshold beat at `lift 1`, not
  `lift 2`**: the identical beat read 67% at lift 2 and **100%** at lift 1.
- **`form="slab"` stands half a block *down* in its own cell.** `FORMS["slab"]`
  is 0.5 against a full block's 1.0, so a slab written at the *same* `lift` as
  the block before it is a **−0.5 step**, and the node after it then asks for
  +1.5, which `--design-only` rejects as "rises +1.5 on a hop". A half-height
  step **up** is `lift + 1, form="slab"`.
- **Know what `frame empty` can and cannot see.** It is
  `spiral_probe._lens_rays`: 25 rays, ±26° horizontal and ±36° vertical, against
  voxels within an **8 m horizon**. So the steepest up-ray reaches only **4.6 m
  above the eye**, and *anything higher than that over the head cannot move the
  number* — nor can props, which are models rather than cells. **This is a
  limitation of the metric, not a design rule**: the reference's own lid sits a
  median eight blocks up, fills the top of its frames, and would read as "empty"
  to this probe. Build the roof the composition rule asks for, and use the
  contact sheet — not this number — to judge whether the frame is full.
- **A beat's fidelity has about ±14 points of resolution at the default 8
  runs**, because a level only gets about three visits and one landing is a
  seventh of a beat. The same beat definition read 78 / 92 / 78 across runs that
  differed only in an unrelated node. The "no beat under 98%" criterion is not
  measurable there: use `--report --runs 24 --no-motion`, which needs no window
  and takes seconds.
- **Two non-findings, recorded so nobody repeats them.** The core's overhang
  does *not* eat close hugs — `Cone.core_r` moves 0.13 blocks over four of
  height, and a cell at `hug` 1.8–4.2 is rock 0.1% of the time over 1,320
  samples, because `outer_at − band_at` **is** `core_r`. And the `body inside
  the world` and `lens jammed` rows are one seed's run: they flipped between 0
  and 15 frames across revisions that could not have caused it. Treat both as
  noisy at that sample size.
- **Three things that were reported by agents and are *not* true**, both checked
  by the parent and recorded so they do not get rediscovered: `kind="walk"`
  **can** be authored (six levels use it with `--design-only` clean; the
  confusion is `spiralplan.BALLISTIC`, which contains `walk`, against
  `tower_probe.BALLISTIC`, which does not); `moat=True` **does** dig (three moat
  nodes add about 54 liquid cells a run, not four); and moats **do** stop the
  no-jump walker — measured on identical worlds with `breaks=0`, coverage falls
  from **65.8% to 25.8%** with moats on. The mechanism is worth knowing though,
  because the agent who doubted it was right about the *reason*: `water` is in
  `SEE_THROUGH` and `lava` is solid, so neither liquid blocks the walker. What
  stops it is the **pit the moat digs** — the walker can enter the bowl and
  cannot step back out. Liquid on its own is atmosphere; liquid in a hole is a
  barrier.
- **`form="floor"` clamps `lift` to zero.** It places no block; the cell must
  already be solid ground. Writing `lift=1, form="floor"` used to pass the
  paper check and build a block lower, taking every jump after it in the beat
  with it; the checker now clamps the same way `Course._node` does.

## 8. The checklist

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
| plain hop | ≤ 85% of moves, ≥ 1 non-hop verb firing **in the level's own body** |
| liquid on or beside the walking line | at least one beat |
| a threshold: light + complete material change at the first beat | yes |
| exit by a climb | only if the climb is the level's idea — about 1 level in 5 |
| drop after the level's own high point | under 3 blocks, and none after the exit |
| the route painted wherever the ground is wide | yes |
| the level descends somewhere | not a monotonic climb |
| distinct materials named | ≥ 6 across roles, nodes and props |
| covered by a no-jump walker | ≤ 55% mean, never end to end |
| designed content | ≥ 45% of the level's landings (the rest is the exit climb and machinery) |
| body inside the world | 0 frames |
| frame empty (sky, sea, drop) | **< 55% of the view**; the reference sits nearer 45% |
| its structure held at 25° | ≥ 1.5 s |
| **the contact sheet** | **it looks like a place, and you would not confuse it with the level before it** |

The last row is the only one that has ever caught what was actually wrong. The
others are a floor.
