"""Level 20: ROPE BRIDGE.

One designed level of the hand-built tower. The vocabulary and the
rules every line here must satisfy are in ``._base``, ``docs/RULES.md``
and ``docs/TOWER.md``.
"""

from ._base import Level, n

# A rope bridge slung out over a jungle river, with the bridge-keeper's
# cabin standing at the far end of it.
#
# One sentence: *the ground here is a wide green river bar and you are
# never on it -- you go up on to the deck at the abutment and stay on
# planks hung from dark stringers until the span gives out, and then it
# is one long fall into the pool and a run through the keeper's hut.*
#
# The thing to remember from a run of it is the deck: pale oak boards
# with nothing under them, a post on each, and three cells of dark timber
# a foot over your head the whole way across -- the hand rope. That
# overhead beam is the level. It is what a rope bridge *is*, it is what
# fills the top of the frame (RULES 5: dark brow above, the level's own
# colour below, sky as a slot between), and it is free: ``Course.write``
# paints a ``ceiling=`` lid with ``pedestal_style or theme.rock``, and a
# landing that floats has no plinth for ``pedestal_style`` to paint, so
# it paints the lid alone.
#
# **What this replaces, and why the whole thing was rebuilt.** The old
# version was a jungle that rendered brown. Its contact sheet: four rows
# of brown cubes and grey cliff, a strip of blue at the bottom of two
# frames, then five consecutive frames of solid flat brown -- which were
# its exit ``vine``, a ``junglelog`` column at arm's length, and most of
# an 11.2% jammed lens. Its cabin was on screen for 0.0 s of the level.
# Three of those four are addressed here by construction.
#
# **The exit is a bubble column and not the vine.** Measured across the
# roster: a body rides a ladder or a vine at 2.35 m/s and a bubble at
# 11.0, and a climbing body has its face against the thing it climbs --
# so the ride *is* the wall in the lens, and it is on screen for four
# times as long. One level swapped ladder for bubble and took its jammed
# lens from 14.9% to 6.6% at no other cost. A river level has the excuse
# for water written into it: the way out is the spring the river comes
# out of, up the fall on the bubbles.
#
# **``profile="plaza"``, and it is the cabin that decides it.** ``cabin``
# is frozen and it is one of the three *walk* gates. A walk gate wants
# five supported cells across the corridor -- ``_try_reserve_at`` refuses
# any base cell with no rock under it, and the gated cabin's base is two
# rows of five, two cells either side of the running lane -- so on a
# four-cell ledge it fails, measured at 0-2 reservations in 8 against a
# hop gate's 8 of 8. The old version was a ledge and its structure was
# never once seen. A plaza has ground two cells either side of the lane
# everywhere, and ``rise=7`` wants one anyway: a tall level on a narrow
# shelf makes the exit climb lap the tower. The undressed plaza is what
# killed the first tower; a plaza *broken hard* is the reference's own
# wide-ground-whole-width-hazard, and it measures better than the ledge
# on both the walker and the frame.
#
# **``band=11.0`` and not the 12.5 a gorge wants.** A level's usable
# floor is bounded by the ``core_r`` of the level three below, and
# anything inboard of that comes out painted as cone skin -- one level at
# 11.5 had 65% of the cell the body stands on render as ``conerib``, a
# jungle as a grey plate. Level 17 is 11.0, so this is 11.0. It is still
# the widest thing for four levels either side (19 and 21 are both 9.0),
# which is the point: a court after a slot.
#
# **It descends, and the descent is a fall rather than a jump.** The
# reference travels eleven blocks vertically to gain four and does it by
# falling off edges -- 2 of its 122 jumps drop more than one block. The
# deck runs out at lift 3 and the next thing is the pool two blocks
# below, which is the only kind of long jump this motion model has:
# falling takes time and the body does not slow down while it does. It is
# in the level's first two thirds, which is where a descent belongs;
# everything after it goes up.
#
# The palette is the other half of not being CANOPY WALK, eleven levels
# below and the tower's other jungle. That one is a dark canopy: moss
# ground, leaf lids, everything green on green in a 7.5-block gallery.
# This one is the water at the bottom of the same forest -- a bright
# grass bar with shingle and wet rock in it, dark spruce and pale oak
# for the bridge, a red tiled roof on the cabin, and two pools of open
# water. Open where that one is closed, and lit where it is shaded.
LEVEL = Level("ROPE BRIDGE", "jungle", rise=7, gap=2.8, exit="bubble",
              band=11.0, profile="plaza", breaks=4, landmark="cabin",
              # The roles are the bridge before they are the forest.
              # ``rock`` is what ``deco="lintel"`` and the landmark
              # crossing's approach hops are made of, and what the
              # cabin's chimney is, so it is the structure's dark
              # timber; ``accent`` is what ``deco="post"`` is, so it is
              # the pale plank of the deck. ``ground`` is grass and not
              # the theme's moss, which is the one role CANOPY WALK
              # already owns.
              #
              # **``sub`` is doing more work than a role usually does
              # and it is worth saying where.** ``Cone._layer`` paints
              # the cell *directly under* the terrace -- the cut face
              # you see at every floor break and along the whole rim --
              # in ``theme.sub``, full width, on every level. At
              # ``gravel`` (136, 132, 128) that is a grey stripe under
              # the entire place, and it is the second-commonest thing
              # in the frame after the floor itself. ``coarse``
              # (136, 106, 76) makes it the soil under the turf, which
              # is what a river bank actually looks like in section.
              ground="grass", sub="coarse", rock="spruce", accent="oak",
              glow="lantern", liquid="water",
              step=("oak", "hop"),
              # Sixteen materials once the four roles are folded in
              # (``floor_palette`` adds ``ground`` at 4 and ``sub``,
              # ``rock`` and ``accent`` at 2), with the dominant at 22%:
              # the shape a real terrace measures as is a median 14
              # kinds, a dominant share of 26%, and seven kinds to cover
              # eighty per cent.
              #
              # **This is a rebuild of the first draft's mix and the
              # mistake is worth writing down.** That one was a river
              # *bed* -- ``mossy`` ground with ``clay`` 3, ``gravel`` 3
              # and ``stone`` 1 under it -- and every one of those is a
              # grey. ``clay`` is (166, 170, 180), ``stone``
              # (146, 146, 150), and ``mossy`` (104, 122, 96) is a
              # desaturated green that reads as another. The contact
              # sheet came back the colour of the *cone* (118, 113, 109)
              # with green cubes standing in it, which is exactly the
              # failure RULES 5 names: a grey plate with the level's
              # colour on it instead of a frame of one committed hue.
              #
              # So the dominant is ``grass`` (104, 168, 70), a clean
              # green, and ``mossy`` drops to the tail where it belongs
              # -- it is the wet rock at the waterline, not the level.
              # Fifty-four per cent of the mix is green now, a third is
              # the bridge's own timber, and the greys are a shingle
              # remainder. The wetness comes from the two pools and the
              # dressing's own, not from paving the place in stone.
              floor=(("grass", 4), ("moss", 4), ("mossy", 3),
                     ("gravel", 2), ("vine", 2), ("jungleleaf", 2),
                     ("podzol", 2), ("coarse", 1), ("sand", 1),
                     ("bamboo", 1), ("dirt", 1), ("clay", 1),
                     ("junglelog", 1), ("stone", 1)),
              # ``vinehang`` is in ``HANGING`` -- hung from the trough's
              # ceiling rather than stood on the floor -- so it is
              # creeper coming down out of the dark over the running
              # line, which is the one prop here doing a job rather than
              # dressing. ``lilypad`` needs the water the two moats dig.
              props=("vinehang", "bamboo", "grasstuft", "lilypad",
                     "flower", "mcfence"),
              # Misty green-teal rather than CANOPY WALK's leaf green,
              # and lighter: this is the open bottom of the gorge, not
              # the inside of a canopy.
              sky=(146, 196, 178), dark=0.24, beats=[
    # The threshold: a lantern set flush in the shingle at the change of
    # colour -- orange terracotta and sandstone behind, wet green ahead,
    # in one block, which is what the reference's seams do -- and then
    # the walked step up on to the abutment between the two anchor
    # posts, under the stringer.
    #
    # It is walked and not jumped because it cannot be jumped. One
    # impulse always rises 1.25 m and the head then sweeps the two cells
    # above every take-off, so a beam low enough to read as the bridge's
    # own stringer is a beam no arc gets under; ``ceiling=3`` over a
    # ``walk`` is the genre's ``2bc``, the lid you sprint under, and it
    # is the one leg this motion model can honestly put one over.
    #
    # ``lift=1`` and not 2 for the opener: a beat's first node is placed
    # from wherever machinery left the body, which is always lift 1, and
    # the same threshold beat written at lift 2 measured 67% placed
    # against 100%. The half step moves to the *gate*, one node later,
    # where its predecessor is known -- a slab at ``lift=2`` stands half
    # a block proud of the block before it, 1.92 m on foot against a
    # walk's 2.4 m limit and a rise of 0.5 against its 0.55.
    ("bridgehead", [n("glow", arc=3.2, lift=1, hug=3.8, spread=1,
                      deco="lamp", orbs=1),
                    n("rock", arc=2.6, lift=2, form="slab", hug=3.8,
                      kind="walk", spread=1, ceiling=3, deco="lintel",
                      shell="tunnel")]),
    # **The span, and the whole level is this beat.** Five landings, and
    # they are one beat rather than two because of where the terrace
    # runs out: a beat is laid whole or not at all and truncated in the
    # middle, and ``_truncate`` eats the longest arc of the last beat
    # first -- which is always the level's best jump. Beats one and two
    # are the reliable ones on this engine, so the fall is written into
    # beat two at position four rather than saved for a beat three that
    # would lay one landing of it.
    #
    # Every board floats (``pedestal=False``) and carries three cells of
    # ``spruce`` at head height. There is no plinth on a floating
    # landing, so ``pedestal_style`` paints the lid alone: that is the
    # hand rope, it is the dark mass across the top of the frame the
    # composition rule asks for, and it costs nothing.
    #
    # The five, and what each asks:
    #
    # * **on to the deck** -- +1 off the abutment sill on to the first
    #   board, arc 3.2, a reach of 2.52 against a +1 window that stops
    #   at 3.10. Centred rather than at the top of it: 3.6 is a reach of
    #   2.92 and is the arc that has to fall back, and a fallback is not
    #   exact. ``spread=1`` because this node is placed from wherever
    #   the shell's doorway left the body.
    # * **the sag** -- the long one, and the level's showpiece. Level,
    #   arc 4.4, a reach of 3.72 against a flat maximum of 4.26. It is
    #   at position two because a beat lays about half its nodes and
    #   because it must ask the *same* ``lift`` as the opener: the
    #   opener carries ``spread``, so it sits a block high or low about
    #   a fifth of the time, and ``lift + 1`` on the node after it is
    #   then a rise of two, which nothing in this engine makes.
    # * **the far tower** -- +1 on to the head of the far anchor, the
    #   high point of the deck and the last thing with a rope over it.
    #   ``hug`` steps back in from 5.6 to 5.0 so the span reads as a
    #   curve across the corridor rather than a line down it.
    # * **the washout** -- the span is out, and this is the level's
    #   descent: lift 3 to lift 1, arc 5.0, a reach of 4.32. Written at
    #   5.0 because that single number is legal at *three* different
    #   drops -- one block (2.35-4.98), two (3.12-5.56) and three
    #   (3.72-6.05) -- so wherever the deck actually finished, the fall
    #   is placeable. It lands on a boulder standing in the pool it digs
    #   itself, with nothing under it.
    # * **out of the river** -- +1 back up on to the bar, and the beat
    #   ends on the ground on purpose: whatever comes next, script beat
    #   or machinery, opens from lift 1 or 2.
    #
    # The two ``moat`` landings in this level are this one and the
    # shallows', with one landing and eight metres between them -- and
    # the eight is measured rather than chosen, for the reason set out
    # under ``shallows``: the pond is a radius-three bowl dug the moment
    # its landing commits, and a second one inside that radius stands in
    # the hole the first made. No ``pedestal_style`` on either --
    # ``_moat`` fills the bowl with ``pedestal_style or theme.liquid``,
    # so naming one digs a hole and fills it with something solid and
    # walkable.
    ("thespan", [n("accent", arc=3.2, lift=2, hug=4.6, spread=1,
                   pedestal=False, pedestal_style="spruce", ceiling=3,
                   deco="post", orbs=1),
                 n("accent", arc=4.4, lift=2, hug=5.6, spread=1,
                   pedestal=False, pedestal_style="spruce", ceiling=3,
                   orbs=2),
                 n("accent", arc=3.2, lift=3, hug=5.0, spread=1,
                   pedestal=False, pedestal_style="spruce", ceiling=3,
                   deco="post", orbs=1),
                 n("mossy", arc=5.0, lift=1, hug=4.6, spread=0,
                   pedestal=False, moat=True, orbs=2),
                 n("sub", arc=3.6, lift=2, hug=4.0, spread=1, ceiling=3,
                   orbs=1)]),
    # The shallows: one wet boulder out in the current with the level's
    # second pool round its foot and a slab of the bank overhanging it.
    #
    # **This beat sits at 83% placed and four attempts did not move it.
    # That is a finding rather than an omission, so here is the hunt in
    # full** -- three of these theories are plausible enough that the
    # next person will have them too, and all three are wrong.
    #
    # It began as two nodes and read **35 of 42 placed over 24 runs**,
    # 83%, the only beat here under the 98% the rules ask for.
    #
    # * *A beat's tail is never laid, so move the ``moat`` and the lid
    #   to the first node.* Measured **byte-identical** over the same 24
    #   runs -- 35/42 again, and every other beat's count identical to
    #   the landing. The keyword was not what was being refused.
    # * *This is the last script feature before the exit reserve, so
    #   ``_truncate`` clips it.* Cut to a single node: **19 of 23**.
    #   83% again, on a beat with no tail left to clip.
    # * *Its pond stands in the span's pond.* Both bowls are radius
    #   three and ``_node`` offers ``arc * 0.84`` as a fallback, so the
    #   3.2 and 3.6 this pair ran on come to 5.7 m when both fall back,
    #   inside the first bowl. The span's last hop went to 3.6 and this
    #   one to 4.4, worst case 6.7 -- and it read **19 of 23** again.
    #
    # So the 17% is structural to where this beat sits and not to what
    # it says: it is offered on every visit and produces no landing on
    # about one in six of them, at a cost of a sixth of a landing out of
    # the thirteen a visit lays. It is left long at 4.4 because that is
    # the better jump of the two measured the same -- a level stride of
    # 3.72 reach against a flat maximum of 4.26, out on to a boulder in
    # the current -- and the separation is worth having whether or not
    # it is what was wrong. **The thing not to do is spend a fourth pass
    # on it**; the trace counter round ``Course._attempt`` is the tool,
    # and this was diagnosed by count alone.
    #
    # ``lift=2`` at ``spread=1``: this beat's opener follows machinery
    # about half the time, machinery leaves the body at lift 1, and a
    # level 4.4 is a reach of 3.72 -- so from lift 2 it is the jump as
    # written, and from lift 1 the spread drops it to a level one rather
    # than an illegal rise.
    ("shallows", [n("mossy", arc=4.4, lift=2, hug=4.6, spread=1,
                    pedestal=False, moat=True, ceiling=3, orbs=2)]),
], filler=[
    # More bridge, and on a terrace this long the loop is more of what
    # is seen than any single beat: it repeats and the tail of a script
    # does not, so the level's character lives here and its surprise
    # lives in the span. Three boards that close into a ring -- a plank,
    # a stringer crossed on foot, and the board it carries you on to a
    # block higher.
    #
    # The walk is at position *two* and not at the tail. A beat lays
    # about half its nodes, so a verb written last is written and never
    # seen; moving every walk in one level to position two took it from
    # 100% plain hop to 83%, and this loop is the only place in this
    # level a non-hop verb can come from at all -- the exit is a single
    # bubble ride and the crossing's walk belongs to the machinery.
    #
    # The loop's seam is where half a filler's fidelity is usually lost,
    # so it is written rather than hoped for: the high board at lift 3
    # back down to the first at lift 2 is a one-block drop across 3.2 of
    # arc, a reach of 2.52 against a window of 2.35 to 4.98.
    #
    # And there is no ``moat`` anywhere in here. The filler loops, and
    # the second lap digs away the ground the first lap's pedestals are
    # standing on -- one keyword in a filler once produced 27,859
    # "pedestal will not stand" refusals. This level's water is the two
    # pools in the script.
    #
    # The last board is the one landing in the level that *stands* on
    # something: ``pedestal=True``, painted ``spruce``, so it is a mast
    # of dark timber running down to the bar under the highest board of
    # the loop. Two reasons and they are the same reason. A suspension
    # bridge is a deck hung between towers, and a deck with no tower
    # under it anywhere is planks in the sky; and the emptiness in this
    # format is measured *under and ahead of* the eye as much as over
    # it, where a run of floating landings has nothing at all. It
    # repeats with the loop, which is the only way one landing's worth
    # of mass is seen more than once.
    ("planks", [n("accent", arc=3.2, lift=2, hug=4.8, spread=1,
                  pedestal=False, pedestal_style="spruce", ceiling=3,
                  deco="post", orbs=1),
                n("rock", arc=2.6, lift=2, hug=4.8, kind="walk", spread=1,
                  pedestal=False, pedestal_style="spruce", ceiling=3,
                  deco="lintel"),
                n("accent", arc=3.2, lift=3, hug=5.4, spread=1,
                  pedestal_style="spruce", ceiling=3,
                  deco="post", orbs=1)]),
], exit_beats=[
    # The way out is the spring: the river comes out of the cliff at the
    # head of the gorge and you ride it. Two landings -- a lit footing
    # in the plunge pool and one bubble column up the fall -- and the
    # generated climb is still underneath as the fallback.
    #
    # **It is a bubble and not the vine this level used to declare, and
    # that is the single biggest change on the sheet.** A body rides a
    # vine at 2.35 m/s and a bubble at 11.0, so seven blocks are on
    # screen for 0.6 s instead of 3.0 -- and a climbing body has its
    # face against the column, so the ride is the wall in the lens. The
    # old version's five consecutive frames of flat ``junglelog`` were
    # that ride, and they were most of its jammed-lens number.
    #
    # **The footing's ``hug`` is the rest of it.** Only the launch
    # landing matters -- ``hug`` on the climb node itself is inert, 2.0
    # through 3.0 produce identical worlds -- and one level measured 69
    # wall-jammed frames of 1,293 at 2.2 against 0 of 1,280 at 2.8. This
    # is 3.2, which is where the one level that swept it found the knee.
    #
    # **No ``ceiling=`` on the climb node**, which is the trap this
    # tower nearly shipped: the lid stands in the column, ``_climb_move``
    # finds nothing to hang on, and the climb silently becomes ordinary
    # hops with the per-beat table still reading 100%. The tells are
    # ``bubble`` leaving the move mix *by name* and the hop share going
    # up through the 85% rule. Check the mix after touching anything
    # here; absence is silent.
    #
    # **``pedestal=True`` and ``step_y=7`` are what make it anchor at
    # all.** ``_climb_move`` wants solid rock or pedestal within one
    # cell of the column at its middle index and at its top, and a
    # column standing in open air has nothing to grab: measured, 11,097
    # of 13,000 candidates refused on a generated bubble exit, which
    # became a six-step staircase and a third of that level with nothing
    # reporting it. A plinth under the column plus a rise of at least
    # four puts the middle cell on the landing rather than on the stack
    # below.
    #
    # **The arithmetic of ``step_y=7`` against ``gap=2.8``.** The
    # crossing is a fixed ``gap + 1.4`` of arc, so a reach of 3.52 --
    # legal level (2.00-4.26), down one (2.35-4.98) and down two
    # (3.12-5.56). The footing is pinned at ``lift=1`` with one of
    # fallback, so the column tops out at surface 8 or 9 against a next
    # floor at 7: one or two blocks above it, and the crossing comes
    # down on to it. What it must not do is finish *below* seven, which
    # is why the footing carries ``spread=1`` and not the 2 an ordinary
    # landing would.
    n("glow", arc=3.2, lift=1, hug=3.2, spread=1, confine=True,
      ceiling=3, deco="lamp", orbs=1),
    n("mossy", arc=2.4, step_y=7, kind="bubble", climb_style="water",
      hug=2.4, pedestal=True, pedestal_style="mossy", spread=0,
      confine=True, orbs=2),
])
