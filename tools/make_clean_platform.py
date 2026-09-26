# tools/make_clean_platform.py
from PIL import Image, ImageDraw

img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Main deck plate body (slate grey)
draw.rectangle([0, 1, 15, 15], fill=(55, 62, 80, 255))

# Bright top ledge highlight (so the player clearly sees where to land)
draw.line([(0, 0), (15, 0)], fill=(120, 140, 175, 255))

# Dark bottom edge shadow
draw.line([(0, 15), (15, 15)], fill=(30, 32, 42, 255))

# Subtle corner rivets
for rx, ry in [(2, 3), (13, 3), (2, 13), (13, 13)]:
    draw.point((rx, ry), fill=(85, 100, 125, 255))

img.save("assets/sprites/tile_platform.png")
print("Updated assets/sprites/tile_platform.png")
