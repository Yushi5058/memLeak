# Sprite art spec

The game ships with coloured rectangles and looks fine. Drop real art into
`assets/sprites/` and it switches over automatically, per sprite, with no
code changes. Anything you do not provide keeps its rectangle fallback.

## How it works

- One PNG per sprite, named exactly as below, in `assets/sprites/`.
- **Any resolution works.** The loader resizes to the target size on load:
  smooth when shrinking, nearest-neighbour when growing. You do not have to
  produce exact pixel dimensions.
- Sprites are drawn **centred on the hitbox**, never stretched. Art is
  authored at 2x the hitbox, so it visually overhangs the collision box.
  That is intentional and normal platformer practice — it makes the player
  and hazards read clearly.
- Tiles are repeated to cover their rectangle, so they must tile seamlessly.
- The canvas is 320x180. Anything below ~12px of on-screen detail will not
  read. Do not ask for tiny detail.

Restart the game after adding art. There is no hot reload.

## Files

| File | Target size | Replaces | Tiled? |
| --- | --- | --- | --- |
| `player.png` | 24x32 | player, 12x16 hitbox | no |
| `hazard_falling.png` | 20x28 | falling hazard, 10x14 hitbox | no |
| `portal.png` | 28x40 | the goal gate, 14x20 hitbox | no |
| `tile_platform.png` | 16x16 | ground and ledges | yes |
| `tile_hazard.png` | 8x8 | floor spikes and wall barriers | yes |

## Style brief

Paste this into **every** prompt. Inconsistent art is the one thing that
will make the game look worse than rectangles, so reuse the wording
verbatim and, if your tool supports it, reuse the same seed or style
reference across all five.

> 16-bit pixel art sprite, limited 16-colour palette, hard pixel edges, no
> anti-aliasing, no gradients, no blur, single flat light source from the
> upper left, dark outline, transparent background. Retro sci-fi space
> station interior, worn metal panels, cyan and amber accent lights.

## Prompts

**player.png** — the astronaut. Side view, facing right.

> 16-bit pixel art sprite of a small astronaut in a battered white EVA suit
> with a cracked gold visor, standing upright, side view facing right, arms
> at sides. 16-bit pixel art sprite, limited 16-colour palette, hard pixel
> edges, no anti-aliasing, no gradients, no blur, single flat light source
> from the upper left, dark outline, transparent background. Retro sci-fi
> space station interior, worn metal panels, cyan and amber accent lights.
> Full body visible with small empty margins. Single character, no ground,
> no shadow, no text.

**hazard_falling.png** — the thing that falls on you.

> 16-bit pixel art sprite of a jagged cluster of dark crystal spikes with
> faint red glowing cores, pointing downward, symmetrical. 16-bit pixel art
> sprite, limited 16-colour palette, hard pixel edges, no anti-aliasing, no
> gradients, no blur, single flat light source from the upper left, dark
> outline, transparent background. Retro sci-fi space station interior, worn
> metal panels, cyan and amber accent lights. Centred with small empty
> margins. Single object, no ground, no shadow, no text.

**portal.png** — the gate you are trying to reach. This is the player's
goal, so it should be the brightest, most inviting thing on screen.

> 16-bit pixel art sprite of a glowing rectangular airlock gate ring, bright
> cyan energy field across the opening, amber warning lights on the frame,
> seen straight on. 16-bit pixel art sprite, limited 16-colour palette, hard
> pixel edges, no anti-aliasing, no gradients, no blur, single flat light
> source from the upper left, dark outline, transparent background. Retro
> sci-fi space station interior, worn metal panels, cyan and amber accent
> lights. Front view, upright, filling the frame. Single object, no ground,
> no shadow, no text.

**tile_platform.png** — station decking. **Must tile seamlessly** on all
four edges, because the ground is 320x20 and gets repeated.

> 16-bit pixel art tile of a dark grey metal deck plate with rivets along the
> edges and a thin cyan stripe, perfectly seamless, tileable on all four
> edges with no visible border. 16-bit pixel art sprite, limited 16-colour
> palette, hard pixel edges, no anti-aliasing, no gradients, no blur, single
> flat light source from the upper left, dark outline. Retro sci-fi space
> station interior, worn metal panels, cyan and amber accent lights. Flat
> front view, fills the entire frame edge to edge, no margin, no text.

**tile_hazard.png** — 8x8, the smallest asset, so keep it extremely simple.
**Must tile seamlessly** horizontally; floor spikes repeat along a 30px
ledge and wall barriers repeat down a 60px column.

> 16-bit pixel art tile of a single sharp red-tipped metal spike on a dark
> base, reading clearly at 8 by 8 pixels, seamless and tileable horizontally
> with no visible gap. 16-bit pixel art sprite, limited 16-colour palette,
> hard pixel edges, no anti-aliasing, no gradients, no blur, dark outline.
> Retro sci-fi space station interior, worn metal panels, cyan and amber
> accent lights. Side view, fills the entire frame edge to edge, no margin,
> no text.

## Exporting

- **PNG with real transparency.** A flat or white background will show up as
  a white box around your sprite. If your generator cannot output alpha,
  ask it for the sprite on a pure black background and remove the black
  afterwards, but transparent output is strongly preferred.
- Save at whatever size your tool produces. The loader handles the rest.
- Keep the filenames exact and lowercase.

## When art arrives

Drop the files in and run:

```sh
python -m unittest tests.test_sprites
python main.py
```

The tests only assert loader behaviour, so they will not tell you the art
looks good. That part is your eye. If a sprite looks wrong, the most common
cause is a non-transparent background or art that is not square enough to
survive the resize to the target size.
