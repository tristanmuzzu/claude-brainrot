"""16x16 pixel-art block textures.

The voxel idiom is not really about cubes -- it is about *sixteen-by-sixteen
crisp pixels per face*, sampled with nearest-neighbour so they stay hard-edged
at any zoom. A cube with a noise gradient on it reads as a generic 3D box; the
same cube with a legible 16x16 cobblestone pattern reads instantly as the thing
everyone recognises.

So these are authored at 16x16 and never filtered. Each generator is
structural rather than noisy: cobblestone has discrete rounded stones separated
by dark mortar, planks have horizontal boards with vertical seams and grain,
logs have bark streaks and end rings. Noise only perturbs a structure that is
already correct -- pure noise at this resolution just looks like static.

Palettes are the conventional ones for the idiom (earthy greens and browns,
mid-grey stone) rather than the run's generated palette. Terrain that changes
hue every run stops reading as terrain; only accents and lighting follow the
run.
"""

from __future__ import annotations

import random

import numpy as np
import pygame

RGB = tuple[int, int, int]
TEX = 16

# Conventional block palette for the idiom. Kept as module constants so the
# scenes cannot drift from them independently.
GRASS_GREEN = (124, 189, 107)
GRASS_DARK = (95, 159, 82)
DIRT_BROWN = (134, 96, 67)
DIRT_DARK = (111, 75, 44)
STONE_GREY = (127, 127, 127)
STONE_DARK = (90, 90, 90)
STONE_LIGHT = (154, 154, 154)
PLANK_TAN = (176, 139, 84)
PLANK_DARK = (145, 113, 63)
BARK_BROWN = (107, 83, 46)
LEAF_GREEN = (74, 143, 50)
SAND_PALE = (219, 211, 160)
WATER_BLUE = (63, 118, 228)


def _jitter(base: RGB, rng: random.Random, amount: int) -> RGB:
    delta = rng.randint(-amount, amount)
    return (
        max(0, min(255, base[0] + delta)),
        max(0, min(255, base[1] + delta)),
        max(0, min(255, base[2] + delta)),
    )


def _canvas(base: RGB) -> np.ndarray:
    return np.full((TEX, TEX, 3), base, dtype=np.uint8)


def _speckle(arr: np.ndarray, rng: random.Random, colors: list[RGB], count: int) -> None:
    for _ in range(count):
        x, y = rng.randrange(TEX), rng.randrange(TEX)
        arr[y, x] = colors[rng.randrange(len(colors))]


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------


def grass_top(rng: random.Random) -> np.ndarray:
    arr = _canvas(GRASS_GREEN)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(GRASS_GREEN, rng, 14)
    _speckle(arr, rng, [GRASS_DARK, (140, 200, 118)], 40)
    return arr


def grass_side(rng: random.Random) -> np.ndarray:
    """Dirt with an irregular grass fringe over the top few rows.

    The ragged boundary is the whole point -- a straight line across the top
    looks like a painted stripe, the jagged one reads as grass overhanging soil.
    """
    arr = dirt(rng)
    for x in range(TEX):
        depth = 2 + rng.randrange(3)  # 2..4 rows of grass, varying per column
        for y in range(depth):
            arr[y, x] = _jitter(GRASS_GREEN, rng, 12)
        # A single darker pixel under the fringe reads as shadow.
        if depth < TEX:
            arr[depth, x] = _jitter(GRASS_DARK, rng, 8)
    return arr


def dirt(rng: random.Random) -> np.ndarray:
    arr = _canvas(DIRT_BROWN)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(DIRT_BROWN, rng, 16)
    _speckle(arr, rng, [DIRT_DARK, (150, 112, 80)], 34)
    return arr


def stone(rng: random.Random) -> np.ndarray:
    arr = _canvas(STONE_GREY)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(STONE_GREY, rng, 12)
    _speckle(arr, rng, [STONE_DARK, STONE_LIGHT], 26)
    return arr


def cobblestone(rng: random.Random) -> np.ndarray:
    """Discrete rounded stones separated by dark mortar.

    Authored as explicit cells rather than thresholded noise: the recognisable
    thing about cobble is that you can count the stones.
    """
    arr = _canvas(STONE_DARK)
    # Irregular grid of stones, offset per row so they do not line up.
    rows = [(0, 5), (5, 6), (11, 5)]
    for top, height in rows:
        x = rng.randrange(0, 3)
        while x < TEX:
            width = rng.choice((4, 5, 6, 7))
            tone = _jitter(STONE_GREY, rng, 18)
            for yy in range(top + 1, min(TEX, top + height)):
                for xx in range(x + 1, min(TEX, x + width)):
                    arr[yy, xx] = tone
            # Lit top edge and shadowed bottom give each stone a little relief.
            for xx in range(x + 1, min(TEX, x + width)):
                if top + 1 < TEX:
                    arr[top + 1, xx] = _jitter(STONE_LIGHT, rng, 10)
                if top + height - 1 < TEX:
                    arr[top + height - 1, xx] = _jitter(STONE_DARK, rng, 8)
            x += width
    return arr


def planks(rng: random.Random) -> np.ndarray:
    """Horizontal boards with seams and grain."""
    arr = _canvas(PLANK_TAN)
    board_height = 4
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(PLANK_TAN, rng, 10)
    for y in range(0, TEX, board_height):
        # Seam between boards.
        for x in range(TEX):
            arr[y, x] = _jitter(PLANK_DARK, rng, 8)
        # One vertical end-joint per board, offset per row.
        joint = rng.randrange(TEX)
        for yy in range(y, min(TEX, y + board_height)):
            arr[yy, joint] = _jitter(PLANK_DARK, rng, 8)
        # Grain streaks.
        for _ in range(2):
            gy = y + 1 + rng.randrange(max(1, board_height - 1))
            if gy < TEX:
                start = rng.randrange(TEX - 4)
                for xx in range(start, min(TEX, start + rng.randrange(3, 7))):
                    arr[gy, xx] = _jitter(PLANK_DARK, rng, 14)
    return arr


def log_side(rng: random.Random) -> np.ndarray:
    """Bark: vertical streaks, strongly directional."""
    arr = _canvas(BARK_BROWN)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(BARK_BROWN, rng, 12)
    for _ in range(9):
        x = rng.randrange(TEX)
        tone = _jitter((78, 60, 33), rng, 10)
        start = rng.randrange(TEX)
        for yy in range(start, min(TEX, start + rng.randrange(5, TEX))):
            arr[yy, x] = tone
    return arr


def log_top(rng: random.Random) -> np.ndarray:
    """End grain: concentric rings around the centre."""
    arr = _canvas(PLANK_TAN)
    centre = (TEX - 1) / 2
    for y in range(TEX):
        for x in range(TEX):
            radius = max(abs(x - centre), abs(y - centre))
            ring = int(radius) % 2 == 0
            base = PLANK_TAN if ring else PLANK_DARK
            arr[y, x] = _jitter(base, rng, 8)
    return arr


def leaves(rng: random.Random) -> np.ndarray:
    arr = _canvas(LEAF_GREEN)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(LEAF_GREEN, rng, 20)
    # Dark gaps read as depth between clumps.
    _speckle(arr, rng, [(46, 92, 30), (58, 112, 38)], 46)
    return arr


def sand(rng: random.Random) -> np.ndarray:
    arr = _canvas(SAND_PALE)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(SAND_PALE, rng, 10)
    _speckle(arr, rng, [(200, 191, 142)], 18)
    return arr


def metal_panel(rng: random.Random, base: RGB) -> np.ndarray:
    """Riveted panel, for train carriages and city furniture."""
    arr = _canvas(base)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(base, rng, 8)
    dark = tuple(max(0, c - 40) for c in base)
    light = tuple(min(255, c + 34) for c in base)
    for y in (0, TEX - 1):
        for x in range(TEX):
            arr[y, x] = dark  # type: ignore[assignment]
    for x in range(1, TEX, 5):
        arr[2, x] = light  # type: ignore[assignment]
        arr[TEX - 3, x] = light  # type: ignore[assignment]
    return arr


def concrete(rng: random.Random, base: RGB) -> np.ndarray:
    arr = _canvas(base)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(base, rng, 11)
    return arr


# ---------------------------------------------------------------------------
# Urban / rail blocks
# ---------------------------------------------------------------------------


def carriage_side(rng: random.Random, base: RGB) -> np.ndarray:
    """Train flank: window band, skirt, and a roof line.

    The window band is what makes a coloured box a train. It sits in the upper
    half with visible pillars between panes, and the body is banded rather than
    flat so long carriages do not read as one extruded rectangle.
    """
    arr = _canvas(base)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(base, rng, 7)

    dark = tuple(max(0, c - 52) for c in base)
    light = tuple(min(255, c + 40) for c in base)
    glass = (74, 110, 142)
    glass_lit = (150, 196, 226)

    for x in range(TEX):
        arr[0, x] = light  # type: ignore[assignment]
        arr[1, x] = light  # type: ignore[assignment]
        arr[TEX - 2, x] = dark  # type: ignore[assignment]
        arr[TEX - 1, x] = dark  # type: ignore[assignment]

    for y in range(4, 9):
        for x in range(TEX):
            # Pillars every four pixels break the band into panes.
            if x % 5 == 0:
                arr[y, x] = dark  # type: ignore[assignment]
            else:
                arr[y, x] = glass_lit if y < 6 else glass  # type: ignore[assignment]
    for x in range(TEX):
        arr[3, x] = dark  # type: ignore[assignment]
        arr[9, x] = dark  # type: ignore[assignment]
    return arr


def carriage_front(rng: random.Random, base: RGB) -> np.ndarray:
    """Cab end: windscreen and two headlights."""
    arr = _canvas(base)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(base, rng, 7)
    dark = tuple(max(0, c - 52) for c in base)
    for y in range(3, 8):
        for x in range(2, TEX - 2):
            arr[y, x] = (86, 122, 156) if y > 4 else (146, 188, 218)  # type: ignore[assignment]
    for x in range(TEX):
        arr[2, x] = dark  # type: ignore[assignment]
        arr[8, x] = dark  # type: ignore[assignment]
    for lx in (2, 3, TEX - 4, TEX - 3):
        arr[12, lx] = (255, 238, 178)
        arr[13, lx] = (255, 226, 140)
    return arr


def carriage_roof(rng: random.Random, base: RGB) -> np.ndarray:
    roof = tuple(max(0, int(c * 0.72)) for c in base)
    arr = _canvas(roof)  # type: ignore[arg-type]
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(roof, rng, 8)  # type: ignore[arg-type]
    vent = tuple(max(0, c - 30) for c in roof)
    for x in range(2, TEX - 2):
        arr[5, x] = vent  # type: ignore[assignment]
        arr[10, x] = vent  # type: ignore[assignment]
    return arr


def gravel(rng: random.Random, base: RGB) -> np.ndarray:
    arr = _canvas(base)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = _jitter(base, rng, 22)
    return arr


def hazard_stripe(rng: random.Random, base: RGB) -> np.ndarray:
    """Diagonal warning stripes -- the universal 'do not hit this' texture."""
    arr = _canvas(base)
    warn = (248, 214, 78)
    dark = (38, 34, 30)
    for y in range(TEX):
        for x in range(TEX):
            arr[y, x] = warn if ((x + y) // 3) % 2 == 0 else dark  # type: ignore[assignment]
    return arr


# ---------------------------------------------------------------------------
# Character skins
# ---------------------------------------------------------------------------


def _fill(w: int, h: int, base: RGB) -> np.ndarray:
    return np.full((h, w, 3), base, dtype=np.uint8)


def humanoid_skin(
    rng: random.Random,
    skin: RGB,
    hair: RGB,
    shirt: RGB,
    trousers: RGB,
    shoes: RGB,
    cap: RGB | None = None,
) -> dict[str, np.ndarray]:
    """Per-body-part textures for a box humanoid.

    The face is the reason this exists. A head with no features is a coloured
    cube no matter how good its proportions are; two eyes and a mouth at 8x8 is
    all it takes for the figure to read as a person, and it is the single
    highest-impact texture in the whole project.

    Body-part textures are authored at their real pixel sizes -- 8x8 head
    faces, 8x12 torso, 4x12 limbs -- so pixels come out square once mapped onto
    correctly-proportioned boxes.
    """
    out: dict[str, np.ndarray] = {}
    crown = cap or hair
    brow = 3 if cap else 2  # a cap sits lower on the forehead than hair does

    # --- head, 8x8 per face
    face = _fill(8, 8, skin)
    for y in range(brow):
        for x in range(8):
            face[y, x] = _jitter(crown, rng, 6)
    eye_white = (238, 238, 242)
    pupil = (58, 74, 132)
    for ex in (1, 5):
        face[brow + 1, ex] = eye_white
        face[brow + 1, ex + 1] = pupil
    mouth_y = min(7, brow + 3)
    for mx in (3, 4):
        face[mouth_y, mx] = tuple(max(0, c - 58) for c in skin)  # type: ignore[assignment]
    out["head_face"] = face

    side = _fill(8, 8, skin)
    for y in range(brow):
        for x in range(8):
            side[y, x] = _jitter(crown, rng, 6)
    # A darker patch reads as an ear in profile.
    side[brow + 1, 5] = tuple(max(0, c - 34) for c in skin)  # type: ignore[assignment]
    side[brow + 2, 5] = tuple(max(0, c - 34) for c in skin)  # type: ignore[assignment]
    out["head_side"] = side

    back = _fill(8, 8, crown)
    for y in range(8):
        for x in range(8):
            back[y, x] = _jitter(crown, rng, 7)
    # Hair does not reach the very bottom at the back -- that is the neck.
    for x in range(8):
        back[7, x] = _jitter(skin, rng, 5)
    out["head_back"] = back

    top = _fill(8, 8, crown)
    for y in range(8):
        for x in range(8):
            top[y, x] = _jitter(crown, rng, 8)
    out["head_top"] = top

    # --- torso, 8x12
    torso = _fill(8, 12, shirt)
    for y in range(12):
        for x in range(8):
            torso[y, x] = _jitter(shirt, rng, 8)
    collar = tuple(max(0, c - 40) for c in shirt)
    for x in range(2, 6):
        torso[0, x] = collar  # type: ignore[assignment]
    # Waistband, so the torso and legs do not merge into one block of colour.
    for x in range(8):
        torso[11, x] = tuple(max(0, c - 30) for c in trousers)  # type: ignore[assignment]
    out["torso"] = torso

    # --- arm, 4x12: sleeve down to the wrist, then bare hand
    arm = _fill(4, 12, shirt)
    for y in range(12):
        for x in range(4):
            arm[y, x] = _jitter(shirt if y < 9 else skin, rng, 8)
    out["arm"] = arm

    # --- leg, 4x12: trousers, then a shoe at the bottom
    leg = _fill(4, 12, trousers)
    for y in range(12):
        for x in range(4):
            leg[y, x] = _jitter(trousers if y < 10 else shoes, rng, 7)
    out["leg"] = leg

    return out


BLOCKS = {
    "grass_top": grass_top,
    "grass_side": grass_side,
    "dirt": dirt,
    "stone": stone,
    "cobblestone": cobblestone,
    "planks": planks,
    "log_side": log_side,
    "log_top": log_top,
    "leaves": leaves,
    "sand": sand,
}


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------


def to_surface(arr: np.ndarray) -> pygame.Surface:
    """(H, W, 3) array -> Surface, without any smoothing."""
    height, width = arr.shape[:2]
    return pygame.image.frombytes(
        np.ascontiguousarray(arr, dtype=np.uint8).tobytes(), (width, height), "RGB"
    ).convert()


def shaded(arr: np.ndarray, factor: float) -> np.ndarray:
    """Scale a texture's brightness for a face orientation.

    Applied to the texture rather than blended over the drawn face, so the
    pixels stay crisp and the shading costs nothing at draw time.
    """
    return np.clip(arr.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def build_atlas(rng: random.Random) -> dict[str, np.ndarray]:
    """Generate every block texture once for a run."""
    return {name: fn(rng) for name, fn in BLOCKS.items()}
