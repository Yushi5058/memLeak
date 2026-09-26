# tools/fix_player.py
from PIL import Image

p = Image.open("assets/sprites/player.png").convert("RGBA")
# Boost non-transparent pixels slightly so dark robes pop against the background
data = []
for r, g, b, a in p.getdata():
    if a > 0:
        # Give dark robes a subtle cool lift
        if r < 50 and g < 50 and b < 50:
            data.append((r + 30, g + 35, b + 50, a))
        else:
            data.append((r, g, b, a))
    else:
        data.append((0, 0, 0, 0))

p.putdata(data)
p.save("assets/sprites/player.png")
print("Player contrast tuned.")
