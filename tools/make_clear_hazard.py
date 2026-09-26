# tools/make_clean_hazard.py
from PIL import Image, ImageDraw

# Create an 8x8 repeating hazard tile
img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Deep warning crimson base
draw.rectangle([0, 0, 7, 7], fill=(180, 20, 35, 255))

# Diagonal bright hazard warning stripe (#E6283C / safety bright red)
for x, y in [(0, 7), (1, 6), (2, 5), (3, 4), (4, 3), (5, 2), (6, 1), (7, 0)]:
    draw.point((x, y), fill=(255, 70, 80, 255))

# Hot energy edge highlights so columns and floor spikes pop immediately
draw.line([(0, 0), (7, 0)], fill=(255, 120, 130, 255))
draw.line([(0, 7), (7, 7)], fill=(100, 10, 20, 255))

img.save("assets/sprites/tile_hazard.png")
print("Updated assets/sprites/tile_hazard.png with high-visibility hazard stripes.")
