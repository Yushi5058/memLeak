from pathlib import Path

from PIL import Image

SHEET_PATH = Path("spritesheet.png")
OUT_DIR = Path("assets/sprites")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Order matching your horizontal row from left to right:
NAMES = [
    "player.png",
    "hazard_falling.png",
    "hazard_moving.png",
    "hazard_blackhole.png",
    "portal.png",
    "tile_platform.png",
    "tile_hazard.png",
]


def clean_checkerboard(img: Image.Image) -> Image.Image:
    """Turn the faux grey checkerboard pixels transparent."""
    img = img.convert("RGBA")
    data = img.getdata()
    cleaned = []
    # Dark and light checkerboard greys
    for r, g, b, a in data:
        # Check if the pixel is near-neutral grey within the checkerboard range
        if abs(r - g) <= 3 and abs(g - b) <= 3 and 70 <= r <= 150:
            cleaned.append((0, 0, 0, 0))
        else:
            cleaned.append((r, g, b, a))
    img.putdata(cleaned)
    return img


def main() -> None:
    if not SHEET_PATH.exists():
        print(f"Error: {SHEET_PATH} not found. Place the downloaded sheet in the root.")
        return

    sheet = Image.open(SHEET_PATH).convert("RGBA")
    w, h = sheet.size
    col_w = w // len(NAMES)

    for i, name in enumerate(NAMES):
        box = (i * col_w, 0, (i + 1) * col_w, h)
        cell = sheet.crop(box)
        cell = clean_checkerboard(cell)

        # Autocrop to the actual ink bounding box
        bbox = cell.getbbox()
        if bbox:
            cell = cell.crop(bbox)

        out_path = OUT_DIR / name
        cell.save(out_path)
        print(f"Saved: {out_path} ({cell.size[0]}x{cell.size[1]})")


if __name__ == "__main__":
    main()
