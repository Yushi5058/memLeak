# memLeak

A PyWeek jam platformer about spending a finite budget of Earth years.

You stand still and the planet loses time. Reach the gate before the
allocation hits zero.

## Requirements

- Python 3.10 or newer
- A display; the game opens a 960x540 window

## Install and run

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
| --- | --- |
| `Up` / `Down` | Move the menu selection |
| `Left` / `Right` | Adjust the selected settings row |
| `Enter` / `Space` | Confirm, or advance the prologue one phase |
| `Esc` | Back out of a menu, or pause and resume |
| `Left` / `A` | Step left (costs 0.5 years) |
| `Right` / `D` | Step right (costs 0.5 years) |
| `Space` | Jump (costs 2 years, only when grounded) |
| `R` | Retry after winning or running out |

Every menu is keyboard-only; there is no mouse input.

## How it plays

`EARTH_ALLOC` is your life bar and your score at the same time. Three
things drain it:

- **Standing still** costs 8 years per second, always.
- **Jumping** costs 2 years per jump.
- **Taking a hit** costs 50 years and respawns you at the entrance.

Falling hazards spawn on a timer that ramps from one every 2.5 seconds
down to one every 0.8 seconds over the first minute, so the chamber gets
hostile whether or not you move. Clearing it banks whatever allocation you
have left, and the best time and best remaining years persist across
retries.

## The three chambers

Progress is saved to `~/.memleak/progress.json`, so unlocks, best times,
best years, achievements, whether you have seen the prologue, and your
audio volume and mute choice all survive a restart.

| Chamber | What changes |
| --- | --- |
| `OUTER HULL` | The original chamber. Ground movement, one hazard ramp. |
| `CARGO SPINE` | Faster drain, tighter spawns, the first moving hazard. |
| `CORE BREACH` | Narrower platforms, faster movers, a much tighter budget. |

`src/levels.py` holds the level table and a geometry validator that
enforces the physics budgets the player can actually clear, so an
unreachable jump fails loudly instead of shipping.

## Achievements

Five, awarded the moment you clear a chamber:

| Key | How |
| --- | --- |
| `first_steps` | Clear the first chamber |
| `clean_run` | Clear any chamber without taking a hit |
| `speedster` | Clear a chamber under its par time |
| `deep_pocket` | Bank at least 500 years |
| `completionist` | Clear all three chambers |

## Sprites

The game ships with rectangle placeholders and needs no art to run. Drop
PNGs into `assets/sprites/` and they are picked up automatically at the
next launch; anything missing or unreadable falls back per-sprite, so a
partial set still works.

| File | Canonical size |
| --- | --- |
| `player.png` | 24x32 |
| `hazard.png` | 20x28 |
| `portal.png` | 28x40 |
| `platform.png` | 16x16, tiles horizontally |
| `spike.png` | 8x8, tiles horizontally |

Images may be any size; they are rescaled to the canonical box on load.
`docs/SPRITES.md` has the full art brief and image prompts.

## Project layout

```
main.py              event pump, state dispatch, rendering
src/settings.py      every tuning constant and the palette
src/states.py        the State enum
src/menu.py          reusable keyboard menu widget
src/screens.py       main, pause, level select, settings, achievements
src/levels.py        level table and geometry validator
src/progression.py   the saved profile on disk
src/flow.py          start, restart, advance, and win recording
src/achievements.py  achievement definitions and unlock rules
src/chamber.py       static level geometry and collision queries
src/session.py       one run's mutable state and its simulation step
src/player.py        player physics
src/hazards.py       falling and moving hazards
src/sprites.py       sprite loading, normalising, rectangle fallback
src/audio.py         sfx and music playback, degrades to silence
src/overlay.py       cached CRT scanline and vignette
src/prologue.py      phased typewriter reveal of PROLOGUE.txt
tools/gen_sfx.py     regenerates the sound effects
tools/gen_music.py   regenerates the chiptune loops
tests/               unit tests
```

Balance lives entirely in `src/settings.py`. The simulation runs at a
fixed 320x180 internal resolution and is scaled 3x with nearest-neighbour
so pixels stay square.

## Development

```sh
python -m unittest discover -s tests -t .   # 223 tests
ruff check .                                 # lint
python tools/gen_sfx.py                      # regenerate sounds
python tools/gen_music.py                    # regenerate music
```

`tools/gen_sfx.py` and `tools/gen_music.py` use only the standard library
and are deterministic, so regenerating produces byte-identical files. A
test asserts the committed WAVs still match a fresh synthesis. The music
generator ends every track on a rest and fades the boundary to silence so
the loops wrap without a click. The tests set `SDL_VIDEODRIVER` and
`SDL_AUDIODRIVER` to `dummy`, so they run headless.

## Third-party assets

### Fonts

`assets/fonts/Px437_IBM_EGA_8x8.ttf` is redistributed from the **Ultimate
Oldschool PC Font Pack** by **VileR**, obtained from
<https://int10h.org/oldschool-pc-fonts/>.

Licensed under **Creative Commons Attribution-ShareAlike 4.0 International
(CC BY-SA 4.0)** — <https://creativecommons.org/licenses/by-sa/4.0/>.
The full license text is in `assets/fonts/LICENSE.TXT`.

- The font file remains under CC BY-SA 4.0 regardless. Any future
  modification of the font must be shared under the same terms.
- Vendored file SHA-256:
  `09c8e0a4bc82507dec55bbcc215ec7dc0388f565432ac81cab079cd0345cb6d0`
  Compare it against the upstream pack to confirm the file is byte-for-byte
  unmodified; this has not been re-verified against a fresh upstream
  download.

If you fork this project, keep the attribution above and the license file
in place.

### Audio

All sound effects and music are synthesised from scratch by
`tools/gen_sfx.py` and `tools/gen_music.py` and carry no third-party
rights.

### Sprites

No sprite art is bundled. The game ships coloured rectangles and only uses
PNGs you supply in `assets/sprites/`, so any art you drop in is entirely
yours to license. `docs/SPRITES.md` describes the sizes the loader expects.

## License

No license has been chosen for the game source yet. The bundled font is
separately licensed under CC BY-SA 4.0 as described above.
