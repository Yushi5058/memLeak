"""Repair the sprite art so the game stops squashing it.

The generated PNGs are 402x1536 canvases whose subject occupies a small
region in the middle, surrounded by hundreds of stray specks. src/sprites.py
used to stretch that whole canvas into the 24x32 art box, which scaled x and
y by different factors and turned a standing figure into a flat smear. For the
player that left 91 lit pixels out of 768, less than half the coverage of the
plain rectangle it replaced, so adding art made the character harder to see.

The repair is per sprite: keep the connected components that are plausibly
part of the subject, drop the speckle, crop to what survived, then scale that
crop to fit inside the art box while preserving its aspect ratio. Nothing is
ever stretched, so proportions survive.

Run from the repository root:

    python tools/fix_sprites.py           # rewrite assets/sprites in place
    python tools/fix_sprites.py --dry-run # report only, touch nothing
"""

from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
SPRITE_DIR = REPO / "assets" / "sprites"
sys.path.insert(0, str(REPO))

from src.sprites import ART_SIZES, SPRITE_NAMES  # noqa: E402

ALPHA_FLOOR = 16
KEEP_FRACTION = 0.01
REDUCING_GAP = 2.0


def components(alpha: bytearray, width: int, height: int) -> list[tuple[int, int, int, int, int]]:
    """Return (area, min_x, min_y, max_x, max_y) for every 4-connected blob."""
    seen = bytearray(width * height)
    found: list[tuple[int, int, int, int, int]] = []
    for start in range(width * height):
        if alpha[start] <= ALPHA_FLOOR or seen[start]:
            continue
        queue = deque([start])
        seen[start] = 1
        area = 0
        min_x = max_x = start % width
        min_y = max_y = start // width
        while queue:
            pixel = queue.popleft()
            area += 1
            x, y = pixel % width, pixel // width
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    nxt = ny * width + nx
                    if alpha[nxt] > ALPHA_FLOOR and not seen[nxt]:
                        seen[nxt] = 1
                        queue.append(nxt)
        found.append((area, min_x, min_y, max_x, max_y))
    return found


def repair(name: str, dry_run: bool) -> tuple[str, ...]:
    path = SPRITE_DIR / f"{name}.png"
    target = ART_SIZES.get(name)
    if target is None:
        return (f"{name}: no art size declared, skipped",)

    image = Image.open(path).convert("RGBA")
    width, height = image.size
    if width <= target[0] and height <= target[1]:
        return (
            f"{name}: already {width}x{height}, within {target[0]}x{target[1]}, left alone",
        )
    alpha = image.split()[3].tobytes()
    blobs = components(alpha, width, height)
    if not blobs:
        return (f"{name}: canvas is empty, skipped",)

    biggest = max(area for area, *_ in blobs)
    keep = [b for b in blobs if b[0] >= biggest * KEEP_FRACTION]
    dropped = len(blobs) - len(keep)
    dropped_ink = sum(b[0] for b in blobs if b[0] < biggest * KEEP_FRACTION)

    box = (
        min(b[1] for b in keep),
        min(b[2] for b in keep),
        max(b[3] for b in keep) + 1,
        max(b[4] for b in keep) + 1,
    )
    cropped = image.crop(box)
    crop_w, crop_h = cropped.size

    scale = min(target[0] / crop_w, target[1] / crop_h)
    new_w = max(1, round(crop_w * scale))
    new_h = max(1, round(crop_h * scale))
    scaled = cropped.resize((new_w, new_h), Image.LANCZOS, reducing_gap=REDUCING_GAP)

    out = Image.new("RGBA", target, (0, 0, 0, 0))
    out.paste(scaled, ((target[0] - new_w) // 2, (target[1] - new_h) // 2), scaled)
    loose_blobs, loose_pixels = drop_detached(out)

    if not dry_run:
        out.save(path, optimize=True)

    squashed_baseline = image.resize(target, Image.LANCZOS, reducing_gap=REDUCING_GAP)
    before, before_pct = _ink(squashed_baseline)
    after, after_pct = _ink(out)
    gain = f"{after / before:.1f}x more ink" if before else "n/a"
    lines = (
        f"{name}: {width}x{height} -> {target[0]}x{target[1]}",
        f"  subject {crop_w}x{crop_h} aspect {crop_w / crop_h:.3f} "
        f"vs box {target[0] / target[1]:.3f}, drawn at {new_w}x{new_h} undistorted",
        f"  dropped {dropped} speckle blobs ({dropped_ink} px of "
        f"{100.0 * dropped_ink / max(1, sum(b[0] for b in blobs)):.1f}% of ink)",
        f"  art-box ink {before} px ({before_pct:.1f}%) -> {after} px "
        f"({after_pct:.1f}%): {gain}",
        f"  removed {loose_blobs} detached blobs ({loose_pixels} px) "
        f"floating clear of the body",
    )
    return tuple(lines)


def drop_detached(image: Image.Image) -> tuple[int, int]:
    """Erase every blob not connected to the largest one.

    Cropping to the kept blobs leaves detached chunks that are opaque but
    separated from the body by transparent columns, so they survive the
    despeckle and read as a stray pixel floating beside the sprite. Keeping
    only the largest blob cannot damage the body, it can only remove those
    loose fragments. Returns (blobs erased, pixels erased).
    """
    width, height = image.size
    alpha = image.split()[3].tobytes()
    seen = bytearray(width * height)
    blobs: list[list[int]] = []
    largest = 0
    keep = -1
    for start in range(width * height):
        if alpha[start] <= ALPHA_FLOOR or seen[start]:
            continue
        queue = deque([start])
        seen[start] = 1
        pixels: list[int] = []
        while queue:
            pixel = queue.popleft()
            pixels.append(pixel)
            x, y = pixel % width, pixel // width
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    nxt = ny * width + nx
                    if alpha[nxt] > ALPHA_FLOOR and not seen[nxt]:
                        seen[nxt] = 1
                        queue.append(nxt)
        if len(pixels) > largest:
            largest = len(pixels)
            keep = len(blobs)
        blobs.append(pixels)

    cleaned = bytearray(alpha)
    erased_blobs = 0
    erased_pixels = 0
    for index, pixels in enumerate(blobs):
        if index == keep:
            continue
        for pixel in pixels:
            cleaned[pixel] = 0
        erased_blobs += 1
        erased_pixels += len(pixels)
    if erased_blobs:
        image.putalpha(Image.frombytes("L", (width, height), bytes(cleaned)))
    return erased_blobs, erased_pixels


def _ink(image: Image.Image) -> tuple[int, float]:
    alpha = image.split()[3].tobytes()
    lit = sum(1 for value in alpha if value > ALPHA_FLOOR)
    return lit, 100.0 * lit / (image.size[0] * image.size[1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    for name in SPRITE_NAMES:
        for line in repair(name, args.dry_run):
            print(line)
    if args.dry_run:
        print("\ndry run, nothing written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
