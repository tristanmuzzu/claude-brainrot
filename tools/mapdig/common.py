"""Shared vocabulary for the Parkour Spiral map dig.

Leg = the stretch between two consecutive checkpoint plates (44 plates,
43 legs), ordered by y.  Each leg gets a *spine*: a helical polyline that
interpolates radius, bearing (the short way round) and height between its
two plates, sampled about every metre.  Everything else is measured
against that spine.
"""
import json
import math
import pickle

R1 = ("/tmp/claude-1000/-home-tristan-projects-claude-brainrot/"
      "7d49286c-3332-4cc0-9d89-cadc822a1df6/scratchpad/r1")
OLD = ("/tmp/claude-1000/-home-tristan-projects-claude-brainrot/"
       "ae099ecc-79f8-4994-8bb6-bf154d746d6b/scratchpad")

# --- block classification -------------------------------------------------

FLUID = {"water", "lava", "bubble_column", "flowing_water", "flowing_lava"}

# Things a body walks straight through.
PASSABLE_EXACT = {
    "light", "structure_void", "barrier", "torch", "wall_torch", "soul_torch",
    "soul_wall_torch", "redstone_torch", "lever", "rail", "powered_rail",
    "detector_rail", "activator_rail", "tripwire", "tripwire_hook", "snow",
    "vine", "cave_vines", "cave_vines_plant", "glow_lichen", "sculk_vein",
    "ladder", "scaffolding", "cobweb", "water", "lava", "bubble_column",
    "lily_pad", "sugar_cane", "bamboo", "kelp", "kelp_plant", "seagrass",
    "tall_seagrass", "dead_bush", "short_grass", "grass", "tall_grass",
    "fern", "large_fern", "nether_sprouts", "warped_roots", "crimson_roots",
    "hanging_roots", "big_dripleaf_stem", "twisting_vines",
    "twisting_vines_plant", "weeping_vines", "weeping_vines_plant",
    "chorus_flower", "chorus_plant", "sea_pickle", "end_rod", "chain",
    "lantern", "soul_lantern", "flower_pot", "redstone_wire", "repeater",
    "comparator", "string", "powder_snow", "moss_carpet", "pale_moss_carpet",
    "snow_layer", "sculk_shrieker",
}
PASSABLE_SUFFIX = ("_door",       # doors get opened; the map wires them to
                                  # pressure plates, and treating them as
                                  # walls made whole legs unsolvable
                   "_carpet", "_banner", "_sign", "_button", "_pressure_plate",
                   "_sapling", "_tulip", "_torch", "_rail", "_candle",
                   "_coral_fan", "_coral_wall_fan", "_amethyst_bud")
PASSABLE_KEYS = ("flower", "mushroom", "seeds", "poppy", "dandelion",
                 "azure_bluet", "cornflower", "allium", "oxeye_daisy",
                 "lily_of_the_valley", "blue_orchid", "wither_rose", "torch")

# Blocks whose whole point is what they do to a jumping body.
PHYSICS = {
    "slime_block": "slime",
    "honey_block": "honey",
    "ice": "ice", "packed_ice": "ice", "blue_ice": "ice", "frosted_ice": "ice",
    "soul_sand": "soul_sand", "soul_soil": "soul_sand",
    "scaffolding": "scaffolding",
    "cobweb": "cobweb",
    "water": "water", "bubble_column": "water",
    "lava": "lava",
    "ladder": "ladder",
    "vine": "vine", "cave_vines": "vine", "cave_vines_plant": "vine",
    "weeping_vines": "vine", "weeping_vines_plant": "vine",
    "twisting_vines": "vine", "twisting_vines_plant": "vine",
    "powder_snow": "powder_snow",
    "magma_block": "magma",
    "sweet_berry_bush": "berry_bush",
    "big_dripleaf": "dripleaf",
    "hay_block": "hay",
    "bed": "bed",
}
PHYSICS_SUFFIX = {"_trapdoor": "trapdoor", "_fence_gate": "fence_gate",
                  "_bed": "bed"}


def kind(name):
    """Physics family of a block name, or None."""
    if name in PHYSICS:
        return PHYSICS[name]
    for suf, fam in PHYSICS_SUFFIX.items():
        if name.endswith(suf):
            return fam
    return None


def passable(name):
    """True if a body occupies the same cell without being stopped."""
    if name is None:
        return True
    if name in PASSABLE_EXACT:
        return True
    if name.endswith(PASSABLE_SUFFIX):
        return True
    for k in PASSABLE_KEYS:
        if k in name:
            return True
    return False


def solid_name(name):
    """True if the cell blocks a body (any collision box you stand on)."""
    return name is not None and not passable(name)


def full_cube(name):
    """True if the block is an ordinary whole cube (for the band census)."""
    if not solid_name(name):
        return False
    for suf in ("_slab", "_stairs", "_fence", "_wall", "_pane", "_door",
                "_trapdoor", "_fence_gate", "_bars", "_head", "_skull",
                "_chest", "_anvil", "_cauldron", "_hopper", "_grindstone",
                "_lectern", "_campfire"):
        if name.endswith(suf):
            return False
    if name in ("iron_bars", "chest", "hopper", "cauldron", "anvil", "farmland",
                "dirt_path", "composter", "enchanting_table", "brewing_stand",
                "end_portal_frame", "snow", "cake", "conduit", "beacon"):
        return False
    return True


# --- world ---------------------------------------------------------------

def load_world():
    with open(R1 + "/world.pkl", "rb") as f:
        return pickle.load(f)


def load_plates():
    p = [tuple(v) for v in json.load(open(OLD + "/plates.json"))]
    p.sort(key=lambda q: q[1])
    return p


# --- leg spines ----------------------------------------------------------

def spine(a, b, step=1.0):
    """Helical polyline from plate a to plate b, sampled ~every `step` m."""
    ra, rb = math.hypot(a[0], a[2]), math.hypot(b[0], b[2])
    ta = math.atan2(a[2], a[0])
    tb = math.atan2(b[2], b[0])
    dt = (tb - ta + math.pi) % (2 * math.pi) - math.pi     # short way round
    arc = abs(dt) * (ra + rb) / 2
    n = max(4, int(arc / step) + 1)
    pts = []
    for i in range(n + 1):
        u = i / n
        th = ta + dt * u
        r = ra + (rb - ra) * u
        y = a[1] + (b[1] - a[1]) * u
        pts.append((r * math.cos(th), y, r * math.sin(th), th, r))
    return pts


def legs():
    """[(index, a, b, spine_points)] for the 43 checkpoint legs."""
    pl = load_plates()
    return [(i, a, b, spine(a, b)) for i, (a, b) in
            enumerate(zip(pl, pl[1:]))]


def near_spine(pts, x, y, z):
    """Min 3-D distance from a cell centre to the spine, and the index."""
    best, bi = 1e18, 0
    for i, p in enumerate(pts):
        d = (p[0] - x) ** 2 + (p[1] - y) ** 2 + (p[2] - z) ** 2
        if d < best:
            best, bi = d, i
    return math.sqrt(best), bi


def horiz_spine(pts, x, z):
    best, bi = 1e18, 0
    for i, p in enumerate(pts):
        d = (p[0] - x) ** 2 + (p[2] - z) ** 2
        if d < best:
            best, bi = d, i
    return math.sqrt(best), bi


def pct(vals, q):
    if not vals:
        return float("nan")
    s = sorted(vals)
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[i]
