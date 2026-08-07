"""The runner. Stylized big-head proportions, hoodie + cap + backpack, with
run / jump / roll clips. Zones the runtime recolours per seed: hoodie, cap,
pants, pack. Skin, shoes and eyes stay fixed.

The rig has real knees and elbows (two bones per limb, rigid-skinned), and
the run cycle is keyed on the classic four positions -- contact, down,
passing, up -- rather than a sine wave. A sine swing reads as a metronome;
the asymmetry between the slow stance phase and the fast folded swing phase
is most of what reads as *running*.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, build_armature, lift, record_action, reset,
    run_script_banner, skin, skinned_part, swing, zone, join,
)

reset()
run_script_banner("character")

SKIN = zone("skin", (0.83, 0.58, 0.40))
EYE = zone("eye", (0.07, 0.07, 0.09))
HOODIE = zone("hoodie", (0.88, 0.26, 0.10))
PANTS = zone("pants", (0.16, 0.22, 0.44))
SHOE = zone("shoe", (0.93, 0.93, 0.93))
CAP = zone("cap", (0.12, 0.52, 0.84))
PACK = zone("pack", (0.95, 0.72, 0.12))

# Proportions: legs slightly short, head oversized -- the mobile-runner
# silhouette that stays readable at 40 pixels tall.
THIGH = 0.42
SHIN = 0.38
LEG = THIGH + SHIN
TORSO = 0.78
HEAD = 0.60
HIP_Z = LEG
KNEE_Z = SHIN
SHO_Z = HIP_Z + TORSO * 0.88
UPARM = 0.34
FOREARM = 0.30
ELB_Z = SHO_Z - UPARM

parts = [
    skinned_part("torso", "spine", (0.56, 0.36, TORSO), (0, 0, HIP_Z + TORSO / 2), HOODIE, 0.06),
    # hood bump behind the neck
    skinned_part("hood", "spine", (0.30, 0.16, 0.22), (-0.18, 0, HIP_Z + TORSO - 0.06), HOODIE, 0.04),
    skinned_part("pack", "spine", (0.20, 0.42, 0.5), (-0.36, 0, HIP_Z + TORSO * 0.55), PACK, 0.05),
    skinned_part("head", "head", (HEAD, HEAD, HEAD), (0.02, 0, HIP_Z + TORSO + HEAD / 2 + 0.02), SKIN, 0.06),
    # eyes: two dark texels proud of the face -- the difference between "a
    # character" and "a box wearing a cap"
    skinned_part("eye_l", "head", (0.03, 0.09, 0.10),
                 (0.02 + HEAD / 2 + 0.005, -0.115, HIP_Z + TORSO + HEAD * 0.58), EYE, 0.0),
    skinned_part("eye_r", "head", (0.03, 0.09, 0.10),
                 (0.02 + HEAD / 2 + 0.005, +0.115, HIP_Z + TORSO + HEAD * 0.58), EYE, 0.0),
    skinned_part("captop", "head", (HEAD * 1.08, HEAD * 1.08, HEAD * 0.36), (0.02, 0, HIP_Z + TORSO + HEAD * 0.86), CAP, 0.03),
    skinned_part("brim", "head", (0.30, HEAD * 0.92, 0.055), (HEAD / 2 + 0.12, 0, HIP_Z + TORSO + HEAD * 0.72), CAP, 0.01),
]
for side, sgn in (("L", -1), ("R", 1)):
    y_arm = sgn * 0.30
    y_leg = sgn * 0.14
    parts += [
        skinned_part(f"uparm_{side}", f"arm.{side}", (0.16, 0.16, UPARM),
                     (0, y_arm, SHO_Z - UPARM / 2), HOODIE),
        skinned_part(f"forearm_{side}", f"farm.{side}", (0.145, 0.145, FOREARM),
                     (0, y_arm, ELB_Z - FOREARM / 2), HOODIE, 0.02),
        skinned_part(f"hand_{side}", f"farm.{side}", (0.14, 0.14, 0.12),
                     (0, y_arm, ELB_Z - FOREARM - 0.04), SKIN, 0.02),
        skinned_part(f"thigh_{side}", f"leg.{side}", (0.21, 0.21, THIGH),
                     (0, y_leg, HIP_Z - THIGH / 2), PANTS),
        skinned_part(f"shin_{side}", f"shin.{side}", (0.185, 0.185, SHIN),
                     (0, y_leg, KNEE_Z - SHIN / 2), PANTS, 0.02),
        skinned_part(f"shoe_{side}", f"shin.{side}", (0.32, 0.20, 0.14),
                     (0.05, y_leg, 0.07), SHOE, 0.02),
    ]
body = join(parts, "character")

rig = build_armature({
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "spine": ((0, 0, HIP_Z), (0, 0, HIP_Z + TORSO), "root"),
    "head": ((0, 0, HIP_Z + TORSO), (0, 0, HIP_Z + TORSO + HEAD), "spine"),
    "arm.L": ((0, -0.30, SHO_Z), (0, -0.30, ELB_Z), "spine"),
    "farm.L": ((0, -0.30, ELB_Z), (0, -0.30, ELB_Z - FOREARM), "arm.L"),
    "arm.R": ((0, +0.30, SHO_Z), (0, +0.30, ELB_Z), "spine"),
    "farm.R": ((0, +0.30, ELB_Z), (0, +0.30, ELB_Z - FOREARM), "arm.R"),
    "leg.L": ((0, -0.14, HIP_Z), (0, -0.14, KNEE_Z), "root"),
    "shin.L": ((0, -0.14, KNEE_Z), (0, -0.14, 0.0), "leg.L"),
    "leg.R": ((0, +0.14, HIP_Z), (0, +0.14, KNEE_Z), "root"),
    "shin.R": ((0, +0.14, KNEE_Z), (0, +0.14, 0.0), "leg.R"),
})
skin(body, rig)


def _key_track(table, t01):
    """Piecewise-linear lookup in a [(t, value), ...] table, wrapping."""
    t01 %= 1.0
    pts = list(table) + [(table[0][0] + 1.0, table[0][1])]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t01 <= t1:
            f = (t01 - t0) / (t1 - t0) if t1 > t0 else 0.0
            return v0 + (v1 - v0) * f
    return pts[0][1]


# One leg's cycle: contact -> stance -> push-off -> folded swing -> reach.
# Angles in degrees; thigh +ve swings forward, knee +ve folds the shin back.
THIGH_KEYS = [(0.0, 34), (0.14, 8), (0.30, -22), (0.42, -38),
              (0.55, -24), (0.68, 6), (0.82, 30), (0.92, 38)]
KNEE_KEYS = [(0.0, 14), (0.14, 22), (0.30, 30), (0.42, 62),
             (0.55, 96), (0.68, 82), (0.82, 40), (0.92, 16)]
# Upper arm counter-swings; the elbow stays pumped at ~70 with a small beat.
ARM_KEYS = [(0.0, -38), (0.25, -6), (0.5, 40), (0.75, 4)]


def run_pose(pose, t01):
    for side, phase in (("L", 0.0), ("R", 0.5)):
        thigh = _key_track(THIGH_KEYS, t01 + phase)
        knee = _key_track(KNEE_KEYS, t01 + phase)
        swing(pose, f"leg.{side}", thigh)
        swing(pose, f"shin.{side}", -knee)      # knee folds the shin backward
        arm = _key_track(ARM_KEYS, t01 + phase)
        swing(pose, f"arm.{side}", arm, side_deg=(4 if side == "L" else -4))
        # elbows stay pumped: forearms folded up-forward with a small beat
        swing(pose, f"farm.{side}", 74 + 12 * math.sin((t01 + phase) * math.tau))
    # Two footfalls per cycle: the body is lowest just after each contact.
    bounce = abs(math.sin(t01 * math.tau))
    lift(pose, "root", up=-0.035 + 0.075 * bounce)
    swing(pose, "spine", 9, side_deg=4 * math.sin(t01 * math.tau))
    swing(pose, "head", -6, side_deg=-3 * math.sin(t01 * math.tau))


def jump_pose(pose, t01):
    tuck = math.sin(t01 * math.pi)
    swing(pose, "leg.L", 62 * tuck)
    swing(pose, "shin.L", -95 * tuck)
    swing(pose, "leg.R", 28 * tuck)
    swing(pose, "shin.R", -60 * tuck)
    # arms thrown up and back for balance
    swing(pose, "arm.L", -55 * tuck, side_deg=10 * tuck)
    swing(pose, "arm.R", -45 * tuck, side_deg=-10 * tuck)
    swing(pose, "farm.L", 40 * tuck)
    swing(pose, "farm.R", 40 * tuck)
    swing(pose, "spine", 14 * tuck)
    swing(pose, "head", -9 * tuck)
    lift(pose, "root", up=0.10 * tuck)


#: Fraction of the roll clip spent ramping in, and again ramping out. The
#: remainder is a flat hold at the bottom -- see roll_pose.
ROLL_RAMP = 0.18


def _hold(t01, ramp=ROLL_RAMP):
    """A smoothed trapezoid: 0 at the ends, a flat 1 across the middle."""
    if t01 < ramp:
        f = t01 / ramp
    elif t01 > 1.0 - ramp:
        f = (1.0 - t01) / ramp
    else:
        return 1.0
    return f * f * (3.0 - 2.0 * f)


def roll_pose(pose, t01):
    """A baseball slide: hips drop, legs shoot forward, chest folds over them.

    Two things this has to get right, because the collision model is measured
    from the result rather than assumed:

    * The silhouette must actually get LOW -- the point of the move is to pass
      under a gantry, so the top of the head is the number that matters.
    * Nothing may sink below y=0. Dropping the root alone takes the feet
      through the track with it; the legs have to fold up by as much as the
      hips come down, which is what a real slide does anyway.
    """
    # Drop, HOLD, rise -- not a sine through the bottom. How long the body
    # stays low is what decides whether it fits under a hoarding, and a sine
    # is only at its lowest for an instant: at the bottom of the speed range
    # the runner spends over a third of a second under the board, and a slide
    # that merely touches its lowest point in passing does not clear it.
    # The flat middle is measured by assets/measure.py and is what
    # Kinematics.roll_low_from/to describe.
    c = _hold(t01)
    # Limbs lead, hips follow: the trailing heel has to be tucked *before* the
    # hips drop onto it, or the foot is driven through the track on the way
    # into the slide. Two curves, not one, is the whole trick.
    cr = c ** 1.6
    lift(pose, "root", up=-0.34 * cr, forward=0.12 * cr)
    # Chest folded well over: this is what buys the height, not the hip drop.
    swing(pose, "spine", 84 * c)
    swing(pose, "head", -54 * c)
    # Lead leg thrusts forward almost straight; the trailing heel folds right
    # up under the hip so nothing reaches below the railhead.
    swing(pose, "leg.L", 100 * c)
    swing(pose, "shin.L", -22 * c)
    swing(pose, "leg.R", 58 * c)
    swing(pose, "shin.R", -150 * c)
    # Arms swept back and low, out of the silhouette's top edge.
    swing(pose, "arm.L", -66 * c, side_deg=16 * c)
    swing(pose, "arm.R", -66 * c, side_deg=-16 * c)
    swing(pose, "farm.L", 74 * c)
    swing(pose, "farm.R", 74 * c)


record_action(rig, "run", 24, run_pose, step=1)
record_action(rig, "jump", 22, jump_pose)
record_action(rig, "roll", 22, roll_pose)

bake_and_export([body], "character", resolution=256, export_animations=True)
