# Handoff — run the course *through* the oddity gates

Written 2026-08-20 at the end of the session that built the oddities. One job,
scoped, with the measurements that make it checkable. Read `CLAUDE.md` first —
all of it, and in particular "One odd thing every other level", "The course
flies over its terrace", "The course runs *through* the landmarks" and the
Landmines section. Then `docs/REHASH.md` §5 and `docs/PATH.md`.

**Do not start by writing code.** Every reduction this format has ever had came
from reading a rejection table or a contact sheet, and not one was found by
reading the source. The first commit of this job should be a measurement.

---

## The job in one paragraph

`assets/src/props_odd.py` has six pieces with a **verified-clear three-by-three
passage** — `torii`, `brokenarch`, `doorframe`, `hollowlog`, `pipemouth`,
`boneribs`. `spiralplan.ODD_THROUGH` places one on about one level in three,
standing on the terrace and yawed so its hole faces along the corridor. The
body never goes through it, because **the course flies two to four blocks above
its own terrace** (the 2026-08-16 rehash) and the gate is standing on the
floor. The job is to stand the gate at the course's own height and steer the
course through the hole, the way `handplan.Course._landmark_nodes` already
steers it through a gated landmark.

When it is done, `tools/landmark_probe.py`'s question — is the structure ever
actually *framed* — should be answerable for the gates too, and a contact sheet
of a run should show the body passing under a torii rather than beside one.

---

## What already exists, and is worth copying rather than reinventing

* **`spiralplan.GATED` + `Course._reserve_landmark`** hold a passage open from
  the moment a level enters the horizon, as *cells*, against placement, arcs,
  shells, pours and dressing. `landmark_cross[level] = (cells, void, kind)`:
  the three landings to make, the cells to hand back, and whether the passage
  is walked or hopped.
* **`handplan.Course._landmark_nodes`** is the crossing: approach legs that
  climb to the doorway's own height, then the three stored landings. It is
  offered **once** per level and the cursor is untouched.
* **`_gate_lift`** reads the doorway's height off the stored cells rather than
  off the design's `deck`, because the plinth is what *fitted*, not what was
  asked for.
* **`_take_down` / `_retire_gates`** remove a gate the course ran past. A gate
  the course never reaches measured **1.96% unchecked against 0.30%**; that is
  the cost of holding a wall for nothing, and it is why retiring exists.

## The five things that will bite, all of them already learned once

1. **A doorway is walked through, not jumped through.** One jump impulse always
   rises 1.25 m and the head then sweeps three cells above the take-off, so an
   arc under a lintel low enough to read as a doorway is refused every time.
   Interiors are `walk` gates (three cells of clearance, crossed at a run);
   arches and canopies are `hop` gates, five cells high. The six oddity
   passages are **3.1–3.4 m high**, which is a `walk` gate. The exact clear
   rectangle of each is in the table at the bottom of this file.
2. **A passage is three cells wide or it is a graze.** The body is 0.6 m across
   and straddles the next cell whenever it is not dead centre, and on a circle
   the diagonal step is the normal case. All six are ≥3.10 m — no margin.
   Check the *shoulders*, not the centre line: `tools/arc_probe.py` reports
   `landmark` as the largest remaining writer of cells inside the body (5 moves
   in 2,408, worst 0.575 m) and the gated landmarks are the suspect.
3. **The plinth is the dangerous part.** A gated landmark stands on a plinth as
   tall as the level's `deck` so its passage is on the running line — and *the
   plinth stops short of its own passage*, so a fall through the doorway
   carries on down rather than landing in it. That one detail was worth 4.5
   points of re-entry and 1.6 of unchecked placement. A plinth under an oddity
   is a stack of terrain beside the course, which is a staircase back onto it:
   `Course.noclimb` exists to forbid exactly that, and `tools/reentry_probe.py`
   is the number that catches it. **Re-entry is 1 shortcut in 8,484 missed
   jumps today. If your change makes that worse, it is wrong**, however good
   the frames look.
4. **Retrying a refused crossing makes it worse.** Measured: offering up to
   three times took retirements from 18 in twelve runs to 65 and unchecked
   placements from 0.34% to 0.60%, because `_last_resort`'s recovery hop is
   three to five blocks in whatever direction will take one, so the second
   attempt aims behind itself. Offer once; let a refused *stored landing* fall
   through to the next one (that one is worth +6 passages entered).
5. **Two inserted features cannot share ground.** The lock lays seventeen
   blocks in one decision and walked the frontier straight past doorways.
   Breaks on a gate-capable level are kept nine blocks clear and on the far
   side of the apron, the lock defers to a nearer doorway, and script beats are
   clipped short of one (`_clip_to_landmark`, `_gate_dist`). An oddity gate is
   a *third* inserted feature and has to take its place in that order.

## Two things that measured worse and must not be re-derived

* **Aiming the last approach landing one level hop back from the doorway.** It
  halves the hop refusals (157 → 77) and *reduces* passages entered, 56 → 48,
  because an `at` node is strict, the crossing is offered once, and a launch
  cell that will not take a landing spends the offer.
* **Refusing to gate the narrow levels** (band under 8.5, shelf under four):
  worse on both counts — 0.56% unchecked against 0.47%, and two fewer
  structures seen — because the fallback there is a hold on the apron with the
  course squeezing past.

---

## Suggested shape

1. **Measure first.** Extend `tools/landmark_probe.py` (or write
   `tools/gate_probe.py` beside it) to count, per run: gates placed, gates the
   course passed within N metres of, gates the body actually went *through*
   (a landing inside the passage cells), and gates framed at 25° for 1.5 s.
   Today's answer for the oddity gates is 0 for the middle two and that is the
   baseline. Do this before touching `spiralplan`.
2. **Give `ODD_THROUGH` its passage as data.** Each entry needs the hole's
   local offset, its clear width and height, and the axis it is crossed along —
   the table below has all of it, measured from the committed GLBs by a
   triangle-versus-box check. Put it in the table, not in the placement code.
3. **Stand it at `section.deck`.** Re-use whatever `_reserve_landmark` does for
   the gated landmark plinth rather than writing a second one, including the
   rule that the plinth stops short of the passage.
4. **Reserve the passage cells and the approach cells.** The known gap in the
   landmark version is that only the passage is held, not the ground the last
   approach hop needs — "doing it properly means the reservation holding the
   approach cells too, which is a real change to `_reserve_landmark`". This job
   is the right time to make that change once, for both.
5. **Steer, then verify.** `_landmark_nodes` is the template. Offer once.
6. **Run everything.** `tools/tower_probe.py --runs 12` (fidelity must not
   fall below 94%), `tools/reentry_probe.py --runs 6` (shortcut must stay at 1
   in ~8,000), `tools/arc_probe.py --runs 8` (`landmark` must not grow),
   `tools/endurance_probe.py --hours 1 --runs 4` (stalls 0, give-backs 0),
   `tools/spiral_probe.py --plan tower` (unchecked under 0.4%),
   `tools/frame_cost.py` (tower/parkour was 1.535 with the oddities in), and
   `python -m pytest tests/` (675 passed, 34 skipped). **And look at the
   frames**: `brainrot shoot --scene tower --seed N --frames 1600 --every 20`
   plus `tools/contact_sheet.py`. A gate the numbers say was crossed and the
   sheet does not show is not crossed.

## The six passages, measured

| asset | W×D×H (m) | clear hole | crossed along | notes |
|---|---|---|---|---|
| `torii` | 7.31 × 0.98 × 5.19 | 3.10 w × 3.30 h | local **Y** | thin — a gateway, not a tunnel |
| `brokenarch` | 6.87 × 4.30 × 5.78 | 3.20 × 3.30 | local Y | two thin rings of voussoirs |
| `doorframe` | 5.59 × 2.50 × 5.24 | 3.32 × 3.41 | local Y | hole starts at z=**0.14**, its own threshold |
| `hollowlog` | 7.45 × 10.78 × 5.94 | 3.10 × 3.10 | local Y | 8.6 m of bore; goes to z=−1.42 |
| `pipemouth` | 10.82 × 10.53 × 7.43 | 3.20 × 3.10 | local Y | 6.0 m bore, 4.70 across at the axis; z=−1.75 |
| `boneribs` | 8.78 × 10.89 × 6.52 | 3.20 × 3.20 | local Y | 5.9 m; the arch is an **ellipse** — see below |

All six are **ground origin**: z=0 is where the piece meets the terrace, and
the three with negative minima are meant to be bedded into it.

**The rib cage is the warning.** Its arch is an ellipse, so the honest clear
*rectangle* was 3.4 × 2.1 and not 3.4 × 3.4 — the naive "widest gap × tallest
gap" reading is wrong for any curved opening, and the same will be true of the
next curved thing anybody adds. The numbers above are from a triangle-versus-
AABB check against the committed GLBs, which found six real intrusions the eye
had passed. If you change a model, re-run that check; do not re-measure by
looking.

## Where the code is

* `assets/src/props_odd.py` — the models.
* `src/brainrot/scenes/spiralplan.py` — `ODDITIES`, `ODD_THROUGH`, `ODD_EAVE`,
  `ODD_LANE`, `Course._stand_oddity`, `Course._oddity_fits`, and the gated
  landmark machinery (`GATED`, `_reserve_landmark`, `landmark_cross`).
* `src/brainrot/scenes/handplan.py` — `Course._landmark_nodes`, `_gate_lift`,
  `_gate_ahead`, `_gate_dist`, `_clip_to_landmark`, `_take_down`,
  `_retire_gates`, `_abandon`.
* `src/brainrot/scenes/spiral.py` — `ODD_FAR`, `ODD_AHEAD` and the second loop
  in `_draw_props`; the models are loaded into `scene_props`.

## What "done" looks like

A contact sheet of an ordinary tower run in which the body is seen approaching,
entering and leaving a torii — and every probe in step 6 at or better than the
figures quoted there. Anything less than that, write down what it measured and
why you stopped; a number with a date on it is worth more than a finished
feature nobody checked.
