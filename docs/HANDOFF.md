# Handoff — the spiral tower needs a real level-design pass

Written 2026-08-13, at the end of a session that rebuilt all thirty-three
levels and did **not** produce a good result. Read this whole file before
planning anything. It is deliberately light on prescribed method: the last
pass failed partly by following a plan too confidently, and how to tackle this
is yours to decide.

## The verdict, from the owner, watching it live

He restarted into the rebuilt tower and this is what he said, close to
verbatim. Treat it as the specification:

- **Ninety per cent of the levels are still bad.** The jumps are not thought
  out. It looks like far less than the work that went in.
- **Half the jumps are at ground level, or more.** You can walk much of a level
  and only start jumping later.
- **There are not many non-standard jumps.** It is a couple of ground-level
  hops, then a couple higher, then stairs, then you drop back down.
- **Jumps sit right next to the tower core**, so the body clips through the
  wall when it jumps — "apparently no real hitboxes", which is strange in
  itself. Many jumps are narrow and close to an edge, and it is the **core**
  edge, not the outboard one.
- **The structures are still arches.** This was called out as a failure of the
  *previous* rebuild — "village was plaster-coloured boxes" — and eighty per
  cent of what he ran past is an arch again.
- **The levels are badly structured: too long and too thin.** They keep going
  for a long time without much happening. They should be **shorter, and feel
  longer** — more complex in what happens, not more metres of it.
- **It does not feel like scaling a tower.** It goes round in a circle, and
  every so often the run climbs and then drops back to where it started, on a
  new level. There need to be readable stages and real height.
- **Every level must have exactly one way to the end.** No walking half of it.
  That is what buys the levels being shorter.
- **The whole ground has to be reshaped, not just the jump blocks.** Right now
  the tower is a thin layer wrapped around one big undifferentiated tower, and
  it feels wrong. A level is the terrain, the walls and the structures as much
  as it is the course laid on them.
- Every jump should be *planned*: why from this block to that one, what the
  physics of it are, what it asks of the player.

What he wants: **thirty-three subagents, one per level**, each doing its own
research from its theme outward, deciding block by block, using Blender to see
what it is building, planning the route like a game designer, taking as long as
it takes. Not a reset — a real pass over what exists. And **heavy, strict
visual reasoning**, for the subagents and for whoever coordinates them.

## Three of those claims, measured, so you do not start from impressions

| claim | measured |
|---|---|
| "half the jumps are ground level" | **55% of authored landings are at `lift` 0 or 1** (20 and 239 of 473). Spread: lift 2 ×147, 3 ×50, 4 ×11, 5 ×6 |
| "eighty per cent of structures are arches" | overstated, but **`arch` is the most-used landmark by a distance — 8 of 33 levels**, and 12 of 33 use a gate-type structure the course runs through, which is what reads as an arch |
| "jumps right next to the core" | only **8% of landings sit within 2 m of the core face**, so the *landing positions* are not the whole story. Something else makes it read that way — worth finding out rather than assuming. The camera, the `hug` distribution and the near-clip plane are all candidates |

## Why the last pass fell short — my own reading

This matters more than any of the tooling notes, because the failure repeated a
mistake the project had already written down.

1. **I optimised metrics rather than the thing the metrics stand for.** Every
   number in `docs/RULES.md` §8 is green or nearly so — 95.2% placed as
   authored, 18.6% non-hop, 0 of 33 levels walkable end to end, 0.09%
   unchecked, 628 tests — and the result is still poor. `CLAUDE.md` already
   says *"a metric that measures the thing you can build rather than the thing
   the viewer sees reads green forever"*, and I did it again.
2. **The walkability metric does not mean what the owner means.** It measures a
   no-jump flood from the level's entry and passes at ≤55% coverage with no
   level passable end to end. He means something stricter and simpler:
   **there should be exactly one route, and standing on the ground should not
   be one of it.** 55% of landings at lift 0–1 is the same fact from the other
   side. A better metric probably has to ask "how much of the level can be
   reached without leaving the floor", not "can a walker cross it".
3. **I judged from contact sheets and a 400-second video, and he judged from
   the running overlay.** Those disagree. The sheets look much better than the
   thing feels, because a sheet flatters: it shows the best-composed frame of
   each level and never shows you the pacing, the repetition, or how many jumps
   in a row are trivial.
4. **Twenty-odd agents each optimised one level against a shared rubric, and
   nobody was responsible for the tower.** Every level improved on its own
   numbers; the whole did not become a place you climb. Whatever you do, someone
   has to own the through-line — the sense of height, the variety *between*
   levels, and the fact that eight of them ended up with an arch.
5. **`docs/RULES.md` grew to about a thousand lines during the pass** and is
   now a mix of physics facts, engine landmines, measured findings, retracted
   findings and design opinion. The engine facts in §7 are hard-won and worth
   keeping. The design rules are the part that produced this result and should
   be treated as suspect.

## What exists, and what is worth keeping

- **`docs/RULES.md` §1 and §7** — the physics envelope and about thirty
  measured engine facts (what silently fails, what `arc` really means, the
  anchor recipe for climbs, which materials glow, what the probes can and
  cannot see). This is the genuinely valuable output of the pass. Several
  entries record things that were *retracted* after being measured properly;
  keep that habit.
- **`docs/RESEARCH.md`** — the real Parkour Spiral map dug block by block, plus
  the footage read frame by frame. It overturned three things the tower had
  been designed around. Note the caveat in it: two of the three reference
  videos are Parkour *Volcano*, not Spiral.
- **`docs/reference/`** — 182 frames, contact sheets, the checkpoint and palette
  data. `tools/mapdig/` reads the world save.
- **`tools/level_review.py`** — one command per level: the game camera, a
  blueprint (elevation and plan of the built world), a Blender orthographic
  three-view, and that level's numbers. **One level per process.**
  `tools/roster_sheet.py` tiles one frame per level.
- **`src/brainrot/scenes/levels/`** — one module per level, so parallel work
  does not collide.

### Traps that cost this pass real time

- The phase pin skewed **four** separate metrics before it was noticed, each
  time by measuring a world different from the one a real run builds. Anything
  measured through a shortcut needs an A/B against the unshortcut path.
- Both `frame empty` and `lens jammed` are **seed-noisy** — the same unchanged
  level reads 45% on one seed and 38% on another. Average 6–8 seeds.
- **Changing a level re-rolls the levels above it.** The same untouched design
  measured 56 / 43 / 62% designed content across three worlds that differed
  only in its neighbour. A ±10-point before/after on one seed is not evidence.
- A level only lays **9–12 landings**, of which 2–5 are authored; the exit climb
  is often a third of it. Anything past the fifth authored beat is never built.
- Agents are told not to run `tests/test_tower.py` (it measures the whole
  tower); that means **whoever merges must run it**. A shelf widening silently
  broke the gated-crossing invariant during this pass and was caught only at
  merge.

## Things worth questioning rather than inheriting

The owner's complaints point at the tower's *shape*, not just its levels, and
several fixed decisions may be the actual problem:

- A level is one third of a revolution and 80–100 m of arc. He wants shorter
  and denser. `LEVEL_ARC`, `BAND`, and the 33-level roster are all changeable.
- The exit climb is generated machinery, is often a third of a level, and its
  ladder variant **essentially never anchors** — measured at 1 successful column
  in 1,559 candidates without a pedestal. A one-line fix is measured and
  unapplied in `docs/TOWER.md`'s outstanding list. That is the biggest single
  lever nobody pulled.
- `rise` was frozen across the whole pass so that parallel agents could not
  collide. That froze the tower's vertical rhythm, which is exactly what he
  says is missing.
- The core is analytic (`Cone.rock`) and the terrace is painted from it, so
  "reshape the ground" is partly an engine question, not only a level-data one.

## How it goes live

The daemon loads the level modules at start, so nothing is visible until it
restarts. It is currently running the state described here.

    kill $(pgrep -f 'brainrot run')
    cd /home/tristan/projects/claude-brainrot && setsid nohup .venv/bin/brainrot run >/dev/null 2>&1 &
    .venv/bin/brainrot doctor      # expect 0 failed, 14 passed, "1 daemon"

Never leave two daemons running — the second silently steals events, and every
symptom of that looks like a bug in the overlay.

## Branch state

`claude/project-visuals-animations-qzbkiq`, pushed, clean, 628 tests passing.
All thirty-three levels were rewritten this session; the history is one commit
per pair with the measurements in the message.
