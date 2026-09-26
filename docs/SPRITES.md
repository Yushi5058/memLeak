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
| `hazard_moving.png` | 28x40 | moving hazard, 14x20 hitbox | no |
| `portal.png` | 28x40 | the goal gate, 14x20 hitbox | no |
| `tile_platform.png` | 16x16 | ground and ledges | yes |
| `tile_hazard.png` | 8x8 | floor spikes and wall barriers | yes |

`hazard_moving.png` needs a matching code slot before it will load. Until that
lands, the moving hazard reuses `hazard_falling.png`, so a black hole dropped
in as `hazard_falling.png` would turn **both** hazards into black holes.

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

**hazard_falling.png** — a meteorite. This falls from the top of the screen
onto the player, so it should read as heavy and unstoppable.

> 16-bit pixel art sprite of a jagged meteorite asteroid, chunky dark
> charcoal and grey rock with a cracked molten red-orange glowing core
> showing through deep fissures, irregular lumpy silhouette, slight
> bottom-heavy taper. 16-bit pixel art sprite, limited 16-colour palette,
> hard pixel edges, no anti-aliasing, no gradients, no blur, single flat
> light source from the upper left, dark outline, transparent background.
> Retro sci-fi space station interior, worn metal panels, cyan and amber
> accent lights. Centred with small empty margins. Single object, no
> ground, no shadow, no motion trail, no text.

**hazard_moving.png** — a black hole. This drifts left and right along a
fixed path at the player's height, so it should read as a floating orb.

Keep it **warm amber/orange**, never cyan. The goal portal is bright cyan
and the player must never mistake a hazard for the exit.

> 16-bit pixel art sprite of a small black hole, pure black circular void at
> the centre, ringed by a bright amber and orange accretion disk with
> gravitational lensing, a few warped light arcs, floating and upright.
> 16-bit pixel art sprite, limited 16-colour palette, hard pixel edges, no
> anti-aliasing, no gradients, no blur, single flat light source from the
> upper left, dark outline, transparent background. Retro sci-fi space
> station interior, worn metal panels, cyan and amber accent lights.
> Centred with small empty margins. Single object, no ground, no shadow,
> no text.

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

## Generating with Gemini (nano banana)

Two things matter more than the wording:

1. **Generate all six in ONE image as a labelled-free sprite sheet**, then
   slice it. Separate generations drift in palette, outline weight and
   lighting angle, and a mismatched set looks worse than the rectangles.
2. **The loader rescales, so do not fight the model over exact pixel
   dimensions.** Gemini cannot reliably hit a 20x28 grid. Ask for a large
   sheet, then downscale with nearest-neighbour.

### Palette to quote

| Role | Hex |
| --- | --- |
| background | `#12101A` |
| ground / stone | `#2D3040` |
| player | `#32CD32` |
| hazard | `#E6283C` |
| portal / target | `#50DCF0` |
| dim / inactive | `#68687C` |

### Sprite sheet prompt

> Create a single PNG sprite sheet containing exactly six separate 16-bit
> pixel art game sprites, arranged in one horizontal row of six evenly
> spaced cells on a fully transparent background. Every sprite must share
> one identical palette and one identical light direction, upper left.
>
> Cell 1: a small astronaut in a battered white EVA suit with a cracked
> gold visor, standing upright, side view facing right, arms at sides.
> Cell 2: a jagged meteorite asteroid, chunky dark charcoal rock with a
> cracked molten red-orange glowing core, irregular lumpy silhouette.
> Cell 3: a small black hole, pure black circular void ringed by a bright
> amber and orange accretion disk with light lensing arcs.
> Cell 4: a glowing rectangular airlock gate ring seen straight on, bright
> cyan energy field across the opening, amber warning lights on the frame.
> Cell 5: a seamless dark grey metal deck plate tile with rivets and a thin
> cyan stripe.
> Cell 6: a single sharp red-tipped metal spike on a dark base.
>
> Style for all six: 16-bit pixel art, limited 16-colour palette, hard
> pixel edges, absolutely no anti-aliasing, no gradients, no blur, no
> smooth vector look, no 3D render, no photorealism, dark outline, single
> flat light source from the upper left, transparent background. Retro
> sci-fi space station interior, worn metal panels, cyan and amber accent
> lights.
>
> Critical: keep generous empty transparent margin around each sprite so the
> cells can be sliced apart. No text, no labels, no numbers, no grid lines,
> no watermark, no signature, no drop shadow, no cast shadow, no ground
> plane, no background scenery, no white or black backdrop behind the
> sprites.

### Fallback: one prompt per sprite

If you must generate separately, reuse the same style block and the same
seed or style reference for every call, and generate the two hazards back
to back — they are the pair most likely to drift.

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
