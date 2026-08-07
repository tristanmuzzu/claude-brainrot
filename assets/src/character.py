"""The runner. Stylized big-head proportions, hoodie + cap + backpack, with
run / jump / roll clips. Zones the runtime recolours per seed: hoodie, cap,
pants, pack. Skin and shoes stay fixed."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    bake_and_export, box, build_armature, euler_q, record_action, reset,
    run_script_banner, skin, skinned_part, zone, join,
)

reset()
run_script_banner("character")

SKIN = zone("skin", (0.83, 0.58, 0.40))
HOODIE = zone("hoodie", (0.88, 0.26, 0.10))
PANTS = zone("pants", (0.16, 0.22, 0.44))
SHOE = zone("shoe", (0.93, 0.93, 0.93))
CAP = zone("cap", (0.12, 0.52, 0.84))
PACK = zone("pack", (0.95, 0.72, 0.12))

# Proportions: legs slightly short, head oversized -- the mobile-runner
# silhouette that stays readable at 40 pixels tall.
LEG = 0.80
TORSO = 0.78
HEAD = 0.60
HIP_Z = LEG
SHO_Z = HIP_Z + TORSO * 0.88
ARM_L = 0.62

parts = [
    skinned_part("torso", "spine", (0.56, 0.36, TORSO), (0, 0, HIP_Z + TORSO / 2), HOODIE, 0.06),
    # hood bump behind the neck
    skinned_part("hood", "spine", (0.30, 0.16, 0.22), (-0.18, 0, HIP_Z + TORSO - 0.06), HOODIE, 0.04),
    skinned_part("pack", "spine", (0.20, 0.42, 0.5), (-0.36, 0, HIP_Z + TORSO * 0.55), PACK, 0.05),
    skinned_part("head", "head", (HEAD, HEAD, HEAD), (0.02, 0, HIP_Z + TORSO + HEAD / 2 + 0.02), SKIN, 0.06),
    skinned_part("captop", "head", (HEAD * 1.08, HEAD * 1.08, HEAD * 0.36), (0.02, 0, HIP_Z + TORSO + HEAD * 0.86), CAP, 0.03),
    skinned_part("brim", "head", (0.30, HEAD * 0.92, 0.055), (HEAD / 2 + 0.12, 0, HIP_Z + TORSO + HEAD * 0.72), CAP, 0.01),
    skinned_part("arm_l", "arm.L", (0.16, 0.16, ARM_L), (0, -0.30, SHO_Z - ARM_L / 2), HOODIE),
    skinned_part("arm_r", "arm.R", (0.16, 0.16, ARM_L), (0, +0.30, SHO_Z - ARM_L / 2), HOODIE),
    skinned_part("hand_l", "arm.L", (0.14, 0.14, 0.13), (0, -0.30, SHO_Z - ARM_L - 0.05), SKIN, 0.02),
    skinned_part("hand_r", "arm.R", (0.14, 0.14, 0.13), (0, +0.30, SHO_Z - ARM_L - 0.05), SKIN, 0.02),
    skinned_part("leg_l", "leg.L", (0.20, 0.20, LEG - 0.09), (0, -0.14, HIP_Z - (LEG - 0.09) / 2), PANTS),
    skinned_part("leg_r", "leg.R", (0.20, 0.20, LEG - 0.09), (0, +0.14, HIP_Z - (LEG - 0.09) / 2), PANTS),
    skinned_part("shoe_l", "leg.L", (0.32, 0.20, 0.14), (0.05, -0.14, 0.07), SHOE, 0.02),
    skinned_part("shoe_r", "leg.R", (0.32, 0.20, 0.14), (0.05, +0.14, 0.07), SHOE, 0.02),
]
body = join(parts, "character")

rig = build_armature({
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "spine": ((0, 0, HIP_Z), (0, 0, HIP_Z + TORSO), "root"),
    "head": ((0, 0, HIP_Z + TORSO), (0, 0, HIP_Z + TORSO + HEAD), "spine"),
    "arm.L": ((0, -0.30, SHO_Z), (0, -0.30, SHO_Z - 0.75), "spine"),
    "arm.R": ((0, +0.30, SHO_Z), (0, +0.30, SHO_Z - 0.75), "spine"),
    "leg.L": ((0, -0.14, HIP_Z), (0, -0.14, 0.0), "root"),
    "leg.R": ((0, +0.14, HIP_Z), (0, +0.14, 0.0), "root"),
})
skin(body, rig)


def run_pose(pose, t01):
    t = t01 * 2 * math.pi
    swing = math.radians(58)
    pose.bones["leg.L"].rotation_quaternion = euler_q(x=swing * math.sin(t))
    pose.bones["leg.R"].rotation_quaternion = euler_q(x=swing * math.sin(t + math.pi))
    # Arms counter-swing, elbows implied by a slight inward yaw.
    pose.bones["arm.L"].rotation_quaternion = euler_q(
        x=swing * 0.85 * math.sin(t + math.pi), z=math.radians(-8))
    pose.bones["arm.R"].rotation_quaternion = euler_q(
        x=swing * 0.85 * math.sin(t), z=math.radians(8))
    pose.bones["spine"].rotation_quaternion = euler_q(
        x=math.radians(8), z=math.radians(4) * math.sin(t))
    pose.bones["head"].rotation_quaternion = euler_q(x=math.radians(-5))
    # Bounce twice per cycle -- once per footfall.
    pose.bones["root"].location = (0, 0, 0.07 * abs(math.sin(t)))


def jump_pose(pose, t01):
    tuck = math.sin(t01 * math.pi)
    pose.bones["leg.L"].rotation_quaternion = euler_q(x=math.radians(78) * tuck)
    pose.bones["leg.R"].rotation_quaternion = euler_q(x=math.radians(50) * tuck)
    pose.bones["arm.L"].rotation_quaternion = euler_q(x=math.radians(-130) * tuck, z=math.radians(-14) * tuck)
    pose.bones["arm.R"].rotation_quaternion = euler_q(x=math.radians(-110) * tuck, z=math.radians(14) * tuck)
    pose.bones["spine"].rotation_quaternion = euler_q(x=math.radians(16) * tuck)
    pose.bones["head"].rotation_quaternion = euler_q(x=math.radians(-10) * tuck)
    pose.bones["root"].location = (0, 0, 0.12 * tuck)


def roll_pose(pose, t01):
    # A crouch-slide: sink low over the front foot, chest folded, arms back.
    # The root drop and the knee fold must agree or the feet leave the ground.
    c = math.sin(t01 * math.pi)
    pose.bones["root"].location = (0.10 * c, 0, -0.34 * c)
    pose.bones["spine"].rotation_quaternion = euler_q(x=math.radians(38) * c)
    pose.bones["head"].rotation_quaternion = euler_q(x=math.radians(-26) * c)
    pose.bones["leg.L"].rotation_quaternion = euler_q(x=math.radians(62) * c)
    pose.bones["leg.R"].rotation_quaternion = euler_q(x=math.radians(-18) * c)
    pose.bones["arm.L"].rotation_quaternion = euler_q(x=math.radians(-46) * c, z=math.radians(-8) * c)
    pose.bones["arm.R"].rotation_quaternion = euler_q(x=math.radians(-46) * c, z=math.radians(8) * c)


record_action(rig, "run", 20, run_pose)
record_action(rig, "jump", 22, jump_pose)
record_action(rig, "roll", 22, roll_pose)

bake_and_export([body], "character", resolution=256, export_animations=True)
