# Still outstanding

The backlog, moved verbatim from `CLAUDE.md` on 2026-09-02. Items are numbered
by age (more zeros is newer), struck through when done, and each names the
probe that measures it. `FINDINGS.md` is the defect ledger; this is the
design backlog. Background for every item is in `docs/HISTORY.md`.

00000. **ROPE BRIDGE grew a re-entry, once.** The impulse pass re-rolls which
   candidates place, and over fourteen runs the tower reads 10 shortcut
   re-entries on one level visit of 146 against 2 on two visits before it
   (`tools/reentry_probe.py --runs 14 --levels`). It is not systematic -- the
   level is clean on its other visits -- but the criterion in `docs/REHASH.md`
   is zero and this is the one number that went the wrong way. `--only "ROPE
   BRIDGE"` plus the throwaway path-printer described under item 0a is the way
   in.
00000a. ~~An unchecked emergency could create an impossible hop.~~ **Fixed
   2026-10-07.** Recovery now uses checked local hops/walks and ascending
   turns. Exit landings preserve their unwrapped bearing and leave room to
   gain the next terrace's height. The unchecked fallback has been removed.
   Eight seeds completed 38,224 landings across every level without a solver
   failure. See `docs/PATH.md` for the current verification record.
00000b. ~~Tower moves pass through drawn structures.~~ **Fixed 2026-10-07.**
   Continuous swept-body clearance covers the landing, structures, departure
   run and furniture. Drawn bridges/pedestals retain collision after retirement;
   glass, leaves and scaffolds cannot be crossed as air. The final sweep checked
   15,005 played moves with no body, camera, furniture or prop penetration.

0000. ~~The sideways hop between two roofs happens 0.75 times a minute~~
   **Done, and the guess in this entry was half right.** Laying the flank
   *against* the chain was indeed the fix -- 3.62 crossings a minute now, and
   `runner_probe` counts them rather than anybody estimating from the code.
   What the entry did not say is that mirroring alone makes it *worse*:
   `_roof_across` crosses only for coins the far lane has and this one has
   not, so two identical trails are worth the same and the body correctly
   holds its lane. The coin road has to change lanes at every gap. See "The
   speed has no top".
0000a. ~~A body crossing between roofs grinds along a train's side~~ **Fixed,
   and it was never a crossing.** It was a fall off the back of a convoy
   carrying a lane change decided on the roof; see "The speed has no top".
   135 -> 42 frames. **What is left is 42 over three hours, worst 0.534 m**,
   and the deep one is the same shape with the contact happening in the air
   rather than after landing -- the cancel in `Motion.advance` fires when the
   body walks off an edge, and by then the fall is already committed to an x
   the world has moved under. ~~Next thing to try: refuse the *offer* rather
   than the arrival~~ -- **tried 2026-08-23 and it is worse.** Distance-swept
   far-lane sampling was built at the offer, the advance and verify, in every
   combination, and every one read 71 frames on the same sweep against 42: a
   crossing refused for a gap the forward leap already handles strands the
   body on a roof that is about to end. The full note is at `_roof_across`.
   No cheap answer to the residue is known.
0000b. **Dead air is 4.0%, against 0.7-2.2% before this pass.** Two causes and
   both are the run ending: the two or three seconds of `blind` running before
   a wreck, in which nothing is planned and so nothing is counted as an
   action, and the restart's own first seconds. Neither is idle *track* --
   the frames are full of train -- so the honest fix is probably to teach the
   probe that a blind stretch is not dead air rather than to change the scene.
   Check that before tuning anything.
000. **The runner reports no surviving plan nine times as often as it used
   to** -- 1,789 over 60 runs x 180 s against 192 before convoys, or 1.7% of
   re-solves against 0.18%. It is a warning counter and not a contact: the
   thing it warns about, the body inside something, is **zero** over that same
   sweep, and reflex saves went *down* (525 -> 230) over 36% more track. Two
   thirds of the reports arrive while the body is on a roof, and the
   breakdown to start from is in `scratchpad`-style form: patch
   `plan.verify` and `plan.schedule_vertical`, bucket by `(riding?, threat
   kind, ride_link, hard)`, and the answer comes out in one twelve-run pass.
   What is already known: the remaining "on the rails" cases are a convoy
   whose ramp offer lapses while the body is squarely in its lane, which is a
   cliff -- the whole chain goes from free to wall in one frame. Read the two
   measured dead ends in "The runner is a convoy" before trying the obvious
   fixes; both of them are worse.
00. ~~Frame cost is the one criterion the rehash lost~~ **It was the
   machine.** Five rounds while the test suite ran in the background read
   tower 3.63 ms and tower/parkour 1.78, against the recorded 1.46; nine
   rounds on a quiet machine read **tower 3.00 ms and 1.389**, which is better
   than the record and inside the 3.5 ms the criteria ask for. The world got
   *smaller*, which is the other half of the answer -- a tower run writes 5,187
   cells against 5,780 before the rehash, because the pedestals went. The
   lesson is the one already written under item 5 and it cost an hour anyway:
   **do not read `frame_cost` off a busy machine, and do not read a ratio off
   five rounds when the spread is 1.0 ms.**
0a. **One missed jump in 8,484 still walks back onto the course**, and it is
   a fall onto the lower step of the same generated staircase -- tread 21 to
   22 missed, landing on tread 20, which is under the arc because the stair
   weaves. What kills it is not a wider weave but the level topping out on its
   own, which is item 0. Everything else that used to do this was a ledge
   beside a landing: more landings at terrace
   height than the geometry needs. `python tools/reentry_probe.py --levels
   --only NAME` names them; `docs/REHASH.md` is the criterion. Trace one with
   a throwaway path-printer -- a forward walk from the fall cells with parent
   pointers, printing what each step stands on -- because all six causes found
   in this pass were invisible in the aggregate and obvious in one path.
0. **The generated staircase is 16% of the exit climb**, and what is left of
   it is per-level authoring rather than an engine change -- see "What the
   exit climb is made of" above for the decomposition and the per-level
   reject table. The loop that works is `scratchpad`-style per-tread
   instrumentation: tag each authored exit node with its index, count
   `_attempt` calls and successes per index, and read which tread stops
   landing. On WINDMILL REACH it said the first four place on every visit
   and the fifth on two of six, which is a terrace running out and is fixed
   by writing one fewer tread (mean exit climb 11.0 -> 5.5 landings).

   **But the staircase is not a tread problem at all: it is the crossing.**
   That was worth two wrong turns to find, and both are worth knowing.
   Attribution was suspected first -- the table buckets by `blk["theme"]`,
   which is the theme of wherever a landing physically *is*, and THE QUARRY's
   exit descends the outside of the tower past a revolution above THE VAULT.
   Blocks now also carry `author`, the level whose plan emitted them, and the
   two attributions **agree**: 143 staircase landings a sweep either way, and
   THE QUARRY is charged 24 by both. `author` is kept because it is the right
   thing to bucket by, not because it changed an answer.

   What the measurement actually says is that on THE QUARRY, WINDMILL REACH,
   WART FIELDS and THE WEIR the authored treads place on nearly every visit
   and the staircase still fires four to nine times in eight runs -- about
   once a visit -- and always *after* `_crossing` has been refused. So the
   generated staircase is the crossing's failure, once per level visit, and
   the lever is `_aim_crossing`.

   **And the crossing fails on distance, not on height.** Instrumented over
   eight runs: 338 crossings asked, 114 placed, the staircase fired 134 times.
   The body is at exactly the intended height on 290 of the 338 asks (+1 above
   the next floor, which is where `_drop_climbed_treads` leaves it) and on 102
   of the 134 give-ups. What it is asked to jump is the problem --
   `_aim_crossing` sets `arc = (lv.u1 - u) * radius + 1.2`, which is *the
   distance to the end of the level*, not a distance a body can cover: at
   give-up the median arc asked for is **9.9 m** and the worst is 76.6, against
   a level hop of 4.26 and 4.98 dropping one. So the crossing is arithmetically
   impossible until the body has walked most of the way to the lip, and the
   generated staircase is what walks it there. The cheap answer to try first is
   to not ask at all while the arc is beyond the physics, and to travel along
   the trough instead -- but see the dead end immediately below before writing
   the loop.

   Do **not** answer it by shortening the recovery. A body already level with
   the terrace it is jumping to gains nothing from climbing, so one
   repositioning step instead of eight looks obviously right; measured, it
   loops -- step, crossing refused, step -- and takes the exit climb from 16%
   of the course to 40% (staircase 126 -> 357 a sweep, crossings 180 -> 71).
   The full staircase at least terminates.
0b. **Half the gate-capable levels still do not get entered**, and the fix
   this file used to recommend has been tried and is **worse**. Over 8 runs:
   173 levels wanted a gate, 135 got the reservation, the offer was made on
   107, and 62 put a landing in the passage. Aiming the last approach landing
   at a cell one level hop back from the doorway halves the hop refusals
   (157 -> 77) and *reduces* passages entered, 56 -> 48, because an `at` node
   is strict, the crossing is offered once, and a launch cell that will not
   take a landing spends the offer. Pre-checking the cell for occupancy
   changes nothing -- the cells are free; what fails is the hop into them.
   Doing it properly means the reservation holding the approach cells too,
   which is a real change to `_reserve_landmark`. What *did* work is letting
   a refused stored landing fall through to the next one (56 -> 62), which is
   the same shape as the authored-exit recovery.
0c. ~~The gated structures cost 0.74 ms a frame~~ **Was met, and the rehash
   lost it again -- see item 00.** Measured 2026-08-14 with all four scenes in
   one process: parkour 1.91, tower 2.79, spiral 2.07, runner 1.83 ms/frame,
   tower/parkour 1.46. The 3.74 ms on record predates the level rebuild.
1. **A wall fills the lens on 1.8-2.9% of frames**, and the biggest cause is
   now known and fixed: bucketing every jammed frame by what the body was
   *doing* said **climb 42.0% and bubble 30.3% against hop 1.0%** -- three
   quarters of every jammed frame was a ladder or a bubble ride, because a
   climbable column has to anchor on the core and the ride is therefore the
   one move whose body is pinned against the surface it cannot see past. The
   camera now looks outward for the length of a ride (`RIDE_OUT`): jammed
   frames 3.23% -> 1.83%, climb -> 16.3%, bubble -> 15.2%. It is *not*
   enclosure -- frames with rock overhead jam at 0.9% against 4.1% for open
   ones, so a tunnel is the level working as designed. Next by rate, both
   level-specific: `basin` 16.7% of 54 frames, `sill` 8.2% of 748.
1c. **Level openings are not the problem they were recorded as.** Measured
   over 4 runs x 35 s, a level's first ninety frames are 46.2% sky against
   41.9% everywhere else -- four points, not "one or two frames of sky with a
   cube in them". What is actually empty is the exit climb (48.6% of 3,716
   frames) and three beats: `stacks` 60.2%, `gate` 55.7%, `stalls` 55.3%.
   Whole-frame emptiness is 14.9% against vanilla's 24.4%, so this axis has
   headroom rather than a deficit.
1b. **The roster still wants assets**: per-theme pours (falling lava/water
   columns past the course), the windmill's blades, a bell, coral fans, a
   scarecrow -- all `assets/src/` work, none load-bearing.
2. **The spiral's move mix is 94% plain hop.** The exit climb is 47% of all
   landings and can only ever be hops, so this is bounded by what the *kernel*
   can express, not by the feature table -- reweighting `FEATURES` was tried
   and is not it. Two things did move it, both in this session: a level's
   signature verb prefers a non-hop where the theme owns one (+1.4 points on
   identical worlds), and `_grab_the_wall` doubled the climb share by turning
   the last stuck case into a ladder up the far side of the chasm. Getting
   materially past this needs a kernel change, and the honest list of what is
   available is short:
   - **Jump-cancel** (hitting your head zeroes the rise and keeps the run) is a
     closed form and would make `_ceiling_cells` honest at two blocks instead
     of three. Worth doing for the head-hitter, but note what it does *not*
     buy: worked through, a 2bc level jump reaches at most 1.7 m, under
     `MIN_HOP`. A 2bc is a thing you sprint under, not a gap you clear -- so
     the genre's `2bc` is already expressible today as a lid over a `walk` or
     `web` leg, which never rises at all.
   - **Momentum between landings** reads well on paper and fights this model.
     A `full` block's run-up is 0.68 m *by construction* (`EDGE` at both ends),
     so scaling jump speed by run-up length shortens every hop in the scene by
     about an eighth and takes the +1 reach from 3.10 to 2.73. The reason this
     project's body is always at sprint speed is that **it never stops** --
     which is a deliberate, load-bearing feature of the flat scene too.
   - **Two-leg steered jumps** (the neo family) and **ice accumulation** are
     both real and both still untried.
3. ~~`tools/depth_probe.py` does not know about the spiral or the tower.~~
   **Done.** `--scene spiral|tower` and a suspect table for that family.
   Answer: the depth guards are load-bearing and now have a number -- without
   them, up to 3,370 px (1.06%) of the course is deleted on the tower and
   7,428 px on the generated spiral. Glows, bursts, cloud shelves and the haze
   band all measure zero; props reach at most 99 px of the course. Two
   instrumentation traps are written into the tool and both read as a clean
   pass: wrapping `_draw_furniture` measures the *opaque* ladders it also
   draws, and patching `fx.no_depth_write` reaches nothing because `spiral.py`
   imports it by name.
4. **DPI**: measured 2026-08-07 on the owner's 1920x1080 at 125%. The daemon
   *is* per-monitor DPI aware — GLFW sets that at `InitWindow` — so every
   `GetWindowRect`/`SetWindowPos`/work-area number inside it is in **physical
   pixels**, and placement is self-consistent. What is still open is that
   `width`/`height` are therefore physical too, so the strip is 1/1.25 of the
   apparent size you would expect from the number. Beware when comparing
   against an outside probe: a plain script is DPI-*un*aware and reads the
   same window back scaled (1920 → 1536), which looks exactly like a bug and
   is not. Call `SetProcessDpiAwareness(2)` in probes.
5. Per-frame cost at sustained top speed, vsync off, against a 16.7 ms
   budget. `python tools/frame_cost.py` is the harness and it does the things
   that have to be right: `HeadlessWindow` + `SetTargetFPS(0)` (`DesktopWindow`
   has vsync on and reports a flat 16.6 ms that tells you nothing), and the two
   scenes built alternately round by round, because only one scene may be alive
   at a time and alternating averages out whatever else the machine started
   doing. Absolute milliseconds off a busy machine are worthless; **the ratio
   between the two scenes in one process is not**.

   Measured 2026-08-11: parkour **2.02 ms**, runner 1.78 ms, ratio 1.15. Do not
   read that ratio against the old 0.75 without checking the denominator: the
   runner was rewritten in a parallel session and now measures 1.78 ms against
   the 2.6-3.0 ms this file used to record, and 2.02/2.8 = 0.72, which is the
   old number. What did change on this side is the new set-pieces -- parkour
   past the ramp costs 2.02 ms against 1.49 ms with `squeeze` and `slabs`
   weighted out, so their geometry is about half a millisecond. The ramp
   itself is free.

   Measured 2026-08-14 with **all four** scenes in one process, which is what
   it defaults to now, and every scene is reported against the first one asked
   for rather than against `runner` by name: parkour **1.91**, tower **2.79**,
   spiral **2.07**, runner **1.83** ms/frame; tower/parkour **1.46**. The
   rebuilt spiral and the hand-built tower had never been through this harness
   at all, because the ratio table listed scenes by name and neither was in it.
   The ring tower's 1.28 ms went with that scene -- do not quote it.

   Scene *construction* is a separate cost and worth watching: the tower takes
   **1.80 s**, up from 1.53 s since `emit_layer` began gating every cell of
   skin on `rock`. That is paid once when the strip appears, and it buys the
   guarantee that nothing drawn is walk-through.

   The runner's own set-piece rewrite was measured the same way, back to back
   on a busier machine: **1.025 before, 1.005 after**, against a round-to-round
   spread of 0.77 ms. Cost-neutral. Do not compare either of those to the 1.15
   above -- that was a quiet machine, and only the ratio survives the
   difference.

