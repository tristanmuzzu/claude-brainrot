# What the reference maps actually do, read frame by frame

Research pass 2, 2026-08-13. Everything below was read off the video frames
themselves. **Seen** = visible in a named frame. **Inferred** = a reading of
several frames that a builder could still disagree with. Where the footage
cannot settle a question I say so.

All paths are relative to
`/tmp/claude-1000/-home-tristan-projects-claude-brainrot/7d49286c-3332-4cc0-9d89-cadc822a1df6/scratchpad/r2/`.

---

## 0. Correction first: two of the three videos are not Parkour Spiral

This matters before anything else is read.

- `ps1_shaders.webm` opens on a garden with a painted map board reading
  **"Parkour Volcano"** over a picture of a lava-veined cone —
  `f/d1/a_001.jpg`, `f/d1/a_003.jpg`, crop `crops/sign2.png` (t ≈ 6–7 s).
- `ps3_shaders.webm` opens on **the same board, in the same garden**, seen
  down a stone gate corridor — `f/ps3/p3_0003.jpg` (t ≈ 10 s), and the same
  "H" maker's sign as `f/ps1/p1_0004.jpg`.

So the two long "shaders" videos are **the same map, Parkour Volcano**, at two
paces (703 s and 2236 s), not Parkour Spiral 1 and Parkour Spiral 3. Only
`ps_speedrun.webm` is a different map: it starts on a gold pressure plate in a
sandstone-and-grass plaza with "Time started!" in the action bar
(`f/sr1s/x_0003.jpg`, `f/srhead/h_07.jpg`), a start that does not appear
anywhere in Volcano.

The genre, the author and the shape are the same — a course spiralling up the
outside of a cone with the sea at the bottom — so the design observations
transfer. But `docs/TOWER.md` § "What the reference actually does" is sourced
from **Parkour Volcano**, and anything that claims to be a Parkour Spiral
frame observation should be relabelled or re-checked against the actual Spiral
world save, which the project already has.

### What was looked at

| video | sampling | frames | how read |
|---|---|---|---|
| Volcano A (703 s) | 3 s | 234 | 10 contact sheets `sheets/PS1_01..10.jpg`, 9 read |
| Volcano A | 1 s | 703 | `sheets/TIMELINE_300_420.jpg` (120 s at 1 s) + the automated metrics below |
| Volcano A | 0.5 s | 4 × 120 | `sheets/D1_*` t 6–66 s, `sheets/D2_*` t 175–235 s |
| Volcano A | 0.33 s | 2 × 90 | `sheets/D3_*` t 318–348 s, `sheets/D4_*` t 556–586 s |
| Volcano A | 0.25 s | 72 | `sheets/ICE_*` t 320–338 s (one level end to end) |
| Volcano B (2236 s) | 4 s | 559 | 12 sheets `sheets/P3_01..12.jpg`, 4 read (01, 02, 06, 09) |
| speedrun (392 s) | 2 s / 0.5 s | 196 / 12 | `sheets/SR_01..09.jpg`, 2 read; `sheets/SRHEAD.jpg` |

Frame filename → timestamp: `p1_NNNN` = 3N − 1.5 s; `p3_NNNN` = 4N − 2 s;
`sr_NNNN` = 2N − 1 s; `s_NNNN` = N − 0.5 s; `a_NNN` = 6 + (N−1)/2;
`b_NNN` = 175 + (N−1)/2; `c_NNN` = 318 + (N−1)/3; `d_NNN` = 556 + (N−1)/3;
`i_NNN` = 320 + (N−1)/4.

---

## 1. How a level opens and closes

**The opening is a lit green block set flush in the floor, placed on a rise so
you see it several seconds early.** Seen: `f/d1/a_056.jpg` +
`crops/greenpad2.png` (a single emissive lime block in the grass beside the
path, with a gold pressure plate two blocks on); `f/d2/b_067.jpg` +
`crops/greenpad.png` (the same block flush in a mossy ledge); `f/d4/d_059.jpg`
(the same block on a dark terracotta promontory, a lamp post beside it, cloud
below). It is one block, level with the floor, and it *emits light* — it reads
at distance and at speed, and it never looks like scenery. Do not confuse it
with the matte stacked emerald blocks used as treasure dressing in the vault
levels (`f/d4/d_046.jpg`) — different job, different finish.

**You see it before you reach it.** In the one level I sampled at 4 fps, the
pad is on screen from `f/ice/i_002.jpg` (t 320.25) to `f/ice/i_011.jpg`
(t 322.5) — 2.3 s of approach with the marker in frame, on a green mound
*above* the player, before the level's own material starts.

**The material change at the seam is abrupt and total, not blended.** Between
`f/d3/c_009.jpg` (jungle leaf ledge, t ≈ 320.7) and `f/d3/c_016.jpg` (packed
and blue ice with jagged spires, t ≈ 323) — about 2.5 s — the palette changes
completely. The 1 s timeline sheet `sheets/TIMELINE_300_420.jpg` shows nine
such changes in 120 s and in every one the seam is one or two frames wide.

**The close of an interior is a bright hole you aim at.** Seen:
`f/d1/a_053.jpg` (a 3-wide stone-brick corridor, oak-stair floor, two hanging
lanterns hung *at the exit* and daylight through it), `f/ps1/p1_0116.jpg` (a
dark vaulted hall, red-and-white carpet down the middle, a white doorway at the
far end), `f/d2/b_018.jpg` (a speckled cave whose only bright thing is a
glowstone-coloured doorway at the end). The lamps are put at the *far* end of
the room, not spread through it.

**Literal gates exist.** Volcano B opens by running through a stone gatehouse
corridor with a wooden floor, walls both sides, the map's own title board
framed dead centre at the end (`f/ps3/p3_0002.jpg`, `f/ps3/p3_0003.jpg`).

**The very top is a wide flat plaza and it is the only one.** The summit is a
savanna plateau above the clouds with a diamond monument and "THANKS FOR
PLAYING" spelled in blocks (`sheets/PS1_10.jpg` rows 2–3, t ≈ 655–700). The
map spends its whole length refusing to give you flat ground and then gives you
flat ground as the prize.

*Inferred:* the exit of a level is not signposted the way the entrance is.
What you get instead is the corridor itself narrowing to a tongue that ends in
air (`f/ps1/p1_0197.jpg`) or a doorway. The design tells you where the level
*starts*; it lets the geometry tell you where it ends.

---

## 2. How you are told where to go, with no HUD

Six devices, all seen, roughly in order of how often they carry the frame:

1. **The route is paved.** A stripe of a different floor material runs down the
   middle of every wide terrace: dirt/mud path across grass (`f/d2/b_067.jpg`,
   `f/d1/a_004.jpg`), gravel and stone path in the start garden
   (`f/d1/a_005.jpg`), a red-and-white carpet runner down a stone hall
   (`f/ps1/p1_0116.jpg`, and again at `sheets/PS1_06.jpg` row 3 ≈ t 397–412).
   Where the ground is wide enough to be ambiguous, it is painted.
2. **Light marks the far end, not the near end.** Lanterns hang at the exit of
   corridors (`f/d1/a_053.jpg`), a lamp post stands at the tip of a promontory
   where the course turns (`f/ps1/p1_0197.jpg`, `f/d4/d_059.jpg`), and a whole
   floor is lit from beneath by sea lanterns under a checker
   (`sheets/PS1_08.jpg` row 3 col 4 and row 4 col 1–2, t ≈ 550–560).
3. **The emissive green checkpoint block** (see §1) is the single strongest
   aim point in the game and it is placed where you must be, not where it looks
   pretty.
4. **A corridor is genuinely a corridor.** In the enclosed 21% of frames (see
   §3) there is exactly one way to face: walls both sides, ceiling 3–4 blocks
   up, `f/d1/a_053.jpg`, `f/d2/b_030.jpg`, `f/ps1/p1_0011.jpg`.
5. **The overhang deletes every wrong answer above you.** Measured over 325
   frames of Volcano A at 1 s: the top 22% of the frame is dark rock on
   **63% of its pixels on average**, and **73% of frames have that band more
   than half filled with dark rock**. You are in a slot; the roof is the
   underside of the level above, so there is nothing to be tempted by upward
   and the frame's only bright exit is forward (typical: `f/d2/b_052.jpg`,
   `f/d4/d_046.jpg`).
6. **A landmark stands where the course turns**, not in the middle of the
   terrace: the lamp tower at the end of the mesa tongue (`f/ps1/p1_0197.jpg`),
   the pale sail structure at the rim (`f/ps1/p1_0111.jpg`,
   `sheets/PS1_05.jpg` row 3).

---

## 3. Why you cannot just walk it

The reference does **not** achieve this by breaking a continuous ledge with
gaps. Three mechanisms, in order of how much work they do:

1. **The walkable surface is mostly 2–4 blocks wide with the drop directly
   outboard, so there is nothing to walk around.** Seen throughout:
   `f/d2/b_067.jpg` (mossy shelf, sea and cloud left, cliff right),
   `f/ps1/p1_0197.jpg` (a terracotta tongue perhaps 3 wide narrowing to 2 and
   ending in air over cloud), `sheets/ICE_02.jpg` rows 1–3, `sheets/D4_02.jpg`
   rows 2–5. Automated over Volcano A at 1 s, excluding intro/outro
   (650 frames): **66.6% of seconds have more than 10% of the frame as open
   sky or sea, and 53.1% more than 20%.** Exposure is the default state.
2. **Where the ground is wide, it is filled with a hazard for its whole
   width.** `f/d2/b_052.jpg` (t ≈ 200.5): a lava lake spans the terrace from
   the cliff to the drop, with one green block sitting in it as the landing —
   there is no bank to walk along. `f/ps1/p1_0011.jpg` and `f/d1/a_049–a_054`:
   a stone-brick room whose entire floor is lava, crossed on a staircase of oak
   stairs. `sheets/P3_09.jpg` row 5 col 6–7: a lava river down the centre of a
   corridor with the walkable bank cut to one block. `f/d1/a_022–a_030`
   (t ≈ 16.5–20.5): the floor is *the sea*, crossed on isolated lily pads.
3. **Interiors are corridors of 2–3 blocks, so bypass is not a question.**
   Measured on the same 650 frames: **20.8% of seconds show no sky at all**;
   there are **17 fully-enclosed runs of ≥3 s, mean 5.6 s, longest 15 s**, and
   the longest fully-open run is 21 s. (Caveat: the metric is "bright,
   low-saturation pixels", so a very bright white interior can read as open and
   a frame pressed against a dark wall reads as enclosed. Spot-checks against
   `sheets/TIMELINE_300_420.jpg` rows 4, 8 and 9 agree.)

**At its widest, the ground stops being a course and becomes a place.** The
village/farm terrace at `f/ps1/p1_0165.jpg` (t ≈ 493) is 5–6 blocks of grass
with fences, a trough, a garden bed and sandstone walls; the start garden
(`f/ps1/p1_0004.jpg`) is wider still. In those stretches you *can* walk, and
the map lets you — for a few seconds — because the level's entrance and exit
are still separated by a real break (the lily-pad water, the lava room, the
ladder shaft). This matches the project's own measurement of the Spiral world
save (46% of a checkpoint leg walkable, no leg walkable end to end): **the rule
is "no leg walkable end to end", not "no metre walkable".**

*Cannot be settled from stills:* the exact width of the breaks in blocks. The
FOV is very wide and heavily distorted at the edges, and no frame gives a
clean orthogonal view of a gap. What I can say is that at the two crossings I
could count — the lily pads at t ≈ 17–20 and the lava-lake island at
t ≈ 200 — the landings are **isolated single blocks with 2–3 blocks of
hazard between them**, not a 5–7 block chasm.

---

## 4. Six structures, read closely

| # | what it is | rough size | course goes | entered / left | load-bearing? |
|---|---|---|---|---|---|
| 1 | **The gatehouse** — stone walls both sides, plank floor, hedge and trees beyond, map title board framed at the end (`f/ps3/p3_0002.jpg`, `f/ps3/p3_0003.jpg`, `f/d1/a_001.jpg`) | corridor ~3 w × 4 h × 12 long, walls ~6 h | **through** | walked in at ground level, walked out into the garden | scenery; it is a threshold, and the only jump-free stretch of the map |
| 2 | **The lava hall** — stone-brick room, lantern pairs on the walls, floor entirely lava, an ascending run of oak stairs across it (`f/ps1/p1_0011.jpg`, `f/d1/a_049`–`a_054`, t 30–42 s) | ~4 w × 5 h, ~20 long, climbing ~4 | **through**, and it is the only way | entered from an open ledge through a hole; left through a lit doorway to sky | fully load-bearing: the floor is the hazard |
| 3 | **The ladder shaft** — a tall narrow tube, ladders on one face, dark walls speckled with black ore, a lit doorway at the top (`f/d2/b_025`–`b_036`, t 187–193) | ~3 × 3 in plan, climbed for **~6 s continuously** | **up the inside** | entered at the base from a smooth stone gallery; left at the top onto a snowy fenced ledge | load-bearing: this is how the level gains its height, and there is no staircase alternative visible |
| 4 | **The carpeted hall** — a big rough-vaulted stone chamber, deep coffered ceiling, red-and-white carpet runner down the centre, ice-blue floor inlays, bright doorway (`f/ps1/p1_0116.jpg`, `sheets/D3_02.jpg` row 5, `sheets/PS1_06.jpg` row 3) | ~6–8 w × 6 h, ~30 long | **through** | doorway in, doorway out | mostly scenery — the parkour inside it is mild; its job is the pause and the carpet's wayfinding |
| 5 | **The lamp tower on the promontory** — a post of terracotta and wood with a glowing four-window lantern cage on top, standing on the last block of a tongue of ground with cloud below (`f/ps1/p1_0197.jpg`, `f/d4/d_059.jpg`) | post ~6 tall, head 3 × 3 | **past it, right at its foot** | you run out to it and turn | scenery, but it is the turn signal: it is placed exactly where the ledge ends |
| 6 | **The pale sail / white rim structure** — enormous smooth white slabs and stairs cantilevered off the rim above the cloud layer (`f/ps1/p1_0111.jpg`, `sheets/PS1_05.jpg` row 3 col 3–4, t ≈ 325–335) | tens of blocks across, several storeys | **across its top surface** | arrived from a snow ledge, left down its far stair | load-bearing: its steps *are* the landings |

Two structural habits worth copying, both inferred from the six: **a structure
is either a corridor you are inside or a silhouette you run at the foot of** —
nothing in the footage is a solid mass parked next to the course; and **the
big interiors are always the level's height gain** (2, 3, 6), so the structure
and the climb are the same decision.

---

## 5. The obstacle vocabulary, as actually seen

Counted over the frames listed in §0. "per level" means per themed section,
about 10–15 s of play (§6).

Frequently, in nearly every level:

- **Plain gaps between blocks on a ledge, level or ±1** — the staple. Every
  exposed sheet.
- **Stairs and slabs as the walking surface** — oak stairs across the lava room
  (`f/ps1/p1_0011.jpg`), snow-layer steps (`f/ps1/p1_0111.jpg`), sandstone
  stairs (`sheets/P3_09.jpg` row 5 col 2). Slabs and stairs are the commonest
  non-cube form by a wide margin, consistent with the project's own world-save
  count (slabs 0.7%, everything else under 1%).
- **Fence and post furniture at the rim** — `f/ps1/p1_0165.jpg`,
  `sheets/D2_02.jpg` rows 2–3, `sheets/ICE_02.jpg`. Seen as *edging and
  scenery* far more often than as something jumped onto; I could not find a
  frame where a fence is unambiguously a landing.
- **Hazard floors: lava, then water** — see §3. Lava appears in roughly a third
  of all sheets; it is the map's signature.
- **Doorways and lids** — you run under a lintel at the exit of every interior
  (`f/d1/a_053.jpg`, `f/d2/b_018.jpg`). Whether any of these is a true
  **head-hitter** — a ceiling low enough that the jump's rise is cut — cannot
  be established from stills.

Once or twice a level:

- **One-block landings in a hazard field** — `f/d2/b_052.jpg` (a single block in
  a lava lake), `f/d1/a_022`–`a_030` (lily pads over sea),
  `sheets/P3_06.jpg` row 1 col 6 and row 2 col 8.
- **Ladders**, both as a whole level's climb (`f/d2/b_025`–`b_036`) and as short
  wall climbs (`sheets/PS1_03.jpg` row 3 col 3–4, `sheets/SR_01.jpg` row 4
  col 5). Vines and bamboo appear as *decoration* on the beach ledges
  (`f/d1/a_056.jpg`) — I did not see one climbed.
- **Ice as terrain**: one whole level of packed and blue ice with jagged spires
  (`sheets/ICE_01.jpg` rows 3–5, `sheets/D3_01/02`, t 321–337).

**The negative result, and it is the load-bearing one for this project.**
Across roughly **2,900 seconds of footage viewed as frames** — all ten Volcano
A sheets bar one, four of twelve Volcano B sheets, two speedrun sheets, and
six dense windows totalling 216 s at 2–4 fps — I found **no slime block, no
honey block, no soul sand, no magma-block bounce, no bubble column, and no
cobweb used as a movement surface**. The physics-altering block that *is*
present is **ice, and only as the ground of one themed level**; nothing in the
stills shows the player sliding on it rather than running across it, because
speed is not readable from a still.

So on the question the parent flagged as load-bearing: **the reference does not
use the exotic movement blocks either.** Its variety comes from what the cubes
are arranged as — rooms, shafts, lava floors, water floors, ladders, stairs —
not from special block physics. An engine that can express ice slides, slime
bounces, web wading and bubble columns and uses almost none of them is
*matching* the reference, not falling short of it. The one exception worth
building is the **ladder**, which the reference leans on hard and uses to
carry a whole level.

*Not settled by the footage:* head-hitters, neos, momentum jumps and any other
technique defined by player input rather than by geometry. A still cannot show
them, and the walkthrough player is not doing anything that looks technical.

---

## 6. Pacing

**A level is 10–15 seconds.** Method: I read `sheets/TIMELINE_300_420.jpg`,
120 consecutive seconds of Volcano A at 1 frame per second, and marked the
palette seams. Ten distinct places in 120 s: lava terrace → jungle/cave →
ice → carpeted hall → white rim → red nether terraces → moss terraces →
quartz hall → sandstone lava hall → red-carpet cave. Mean **12 s**, none
shorter than 8 s or longer than about 15 s. The whole map is 703 s of
walkthrough, so of order 50 sections; the project's own count of the Spiral
world save (44 checkpoints) is the same order.

**One level, end to end, at 4 fps** — the ice level, `sheets/ICE_01..03.jpg`,
72 frames, checkpoint pad at t ≈ 320.7 (`f/ice/i_003.jpg`) to the next
interior's pad at t ≈ 337 (`f/d3/c_058.jpg`): **16.3 s**. Within it: about
2.5 s of approach and arrival on the pad, roughly 11 s of ice terraces, and a
2–3 s descent into the hall. The hardest-looking moment — the narrowest ice
ledge with the drop on both sides — is at `f/ice/i_040`–`i_046`
(t ≈ 329.8–331.3), i.e. **at about 60% of the way through the level**, not at
its end.

**Running versus jumping:** I could not count take-offs reliably from stills.
The camera is very wide-FOV, motion-blurred and hand-held, and at 4 fps an
airborne frame is not distinguishable from a running one with any confidence.
What is countable is that in the 16.3 s level the player is on continuous
ground he could walk for perhaps a third of it and on isolated blocks or a
hazard bank for the rest — an eyeball estimate from `sheets/ICE_01..03.jpg`,
and I would not defend it to better than ±15 points. **A builder should treat
"10–15 s per level" as the solid number here and treat the jump count as
unmeasured.**

---

## 7. What decoration does

**Reads at speed:**

- **Value contrast between the floor and the wall.** Measured over 325 frames
  of Volcano A: mean luminance standard deviation **65.8** (p10 28.7, p90
  89.7) — these frames are not flat. The floor is nearly always the lightest
  thing in the lower half and the overhanging cliff the darkest in the upper.
- **Anything emissive.** Lanterns, glowstone doorways, lava, sea-lantern
  floors, the green checkpoint block. In `f/d2/b_018.jpg` the entire
  information content of the frame is one lit doorway.
- **The route stripe** (§2.1) — a different floor material down the middle.
- **Silhouettes against sky**: the lamp tower (`f/ps1/p1_0197.jpg`), fence
  lines at the rim (`sheets/ICE_02.jpg` row 3), the pale sail
  (`f/ps1/p1_0111.jpg`). Anything with sky behind it is legible; anything with
  cliff behind it is not.

**Invisible at speed:** the fine sub-block dressing — flowers, grass tufts,
single-block ore speckle in walls, moss patches, bamboo — is present in almost
every exposed frame (`f/d1/a_056.jpg` has at least four kinds) and contributes
essentially nothing at 3-second glance distance. It is there for the still.

**Materials per frame:** counted by eye rather than by algorithm, because the
shaders' gradients defeat colour quantisation. `f/d1/a_053.jpg`: stone brick,
a cracked/darker variant, a brown coarse band, oak stairs, oak planks, lantern,
dark ceiling stone — **7**. `f/d2/b_067.jpg`: grass, mud path, coarse dirt,
moss, purple concrete, sandstone cliff, oak fence, the lime lamp — **8**.
`f/ps1/p1_0165.jpg`: grass, path, oak fence, oak log trough, leaves, two
sandstones, snow, terracotta — **9**. Call it **6–9 named materials in a
typical frame, of which 2–3 carry real value contrast.**

**Palette shifts between levels** and does so completely (§1): green → blue
ice → grey hall → white rim → crimson → yellow-green → quartz within 120 s
(`sheets/TIMELINE_300_420.jpg`). No two adjacent levels share a dominant hue in
that window.

**Light** is used three ways and only three: hazard light from the floor (lava,
sea lanterns), point light at the destination (lanterns at exits, lamp towers
at turns), and the marker light of the checkpoint block. There is no ambient
decorative lighting anywhere — every light in these frames is doing a job.

**Altitude changes the backdrop.** Below roughly the halfway point the drop
reads as sea and beach (`f/d1/a_056.jpg`); above it, the drop is a flat white
cloud deck and the sea is gone (`f/ps1/p1_0111.jpg`, `f/ps1/p1_0197.jpg`,
`sheets/D4_02.jpg`). That single change makes the top half of the map feel
higher without any geometry change at all.

---

## 8. The move vocabulary, named correctly (bounded web check)

Two searches, community sources (Hypixel/ManaCube forums, the Minecraft Parkour
Wiki, the Minecraft Wiki parkour tutorial). Consistent across them:

- **2bc = head-hitter (HH).** A jump under a ceiling low enough that the
  player's head strikes it, cutting the rise and accelerating the descent, so
  you clear a gap you could not clear with a full arc. The two names are the
  same move.
- **Neo.** Jumping off the edge of a block at full sprint and landing back
  against the side/face of the pillar you left; double and triple variants
  chain it. A **neup** is a neo where the target is one block higher.
- **Ladder jump.** Climb a ladder, jump off it, use the height gained to clear
  a horizontal gap that is otherwise impossible.
- **Momentum / FMM (force momentum).** Sprinting in mid-air after jamming in a
  confined space, to widen the timing window from one tick to as many as eight.
- **Notation**: `3b +1` is a three-block jump one block up; `x` suffixes give
  horizontal offset. `Thins` are fence/pane/carpet jumps; `slime jumps` and
  `soul sand jumps` are named categories.
- "Pixel drop" and "ninja jump" did not appear in any authoritative list; a
  "pixel" is 1/16 block. I would not use either term without better sourcing.

**Where the sources and the frames disagree, the frames win, and they do
disagree in one important way.** The community lists are written for *technical*
parkour servers, where the interest is neos, momentum tricks and one-tick
windows. Hielke's maps as filmed contain almost none of that: the jumps are
ordinary, the ceilings are doorways rather than head-hitters, and there is no
frame in 2,900 s where the player is doing anything that needs a named
technique. **This genre is adventure parkour, not technical parkour**, and the
vocabulary that matters for building it is architectural — corridor, shaft,
hazard floor, ledge, threshold — not the trick list.

---

## What I would tell someone building one of these levels

1. Put an **emissive marker block flush in the floor at the entrance, on a
   rise**, and make the material change at that block, completely, in one step.
2. Make the level **10–15 seconds**, and change the dominant colour every time.
3. Keep the walking surface **2–4 blocks wide with the drop outboard**; when it
   has to be wider, either make it a *place* (a street, a garden) for a few
   seconds or **fill its width with lava or water** and leave one block in it.
4. **Paint the route** — a different floor material down the middle wherever the
   ground is wide enough to be ambiguous.
5. Put **every lamp at the far end** of a room and a **lit landmark exactly
   where the ledge ends**; put nothing decorative in the middle distance.
6. Spend the special blocks on **ladders**, not on slime, honey, soul sand or
   bubble columns — the reference does not use those at all.
