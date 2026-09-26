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
| `Left` / `A` | Step left (costs 0.5 years) |
| `Right` / `D` | Step right (costs 0.5 years) |
| `Space` | Jump (costs 2 years, only when grounded) |
| `Esc` | Pause and resume |
| `R` | Retry after winning or running out |
| `Enter` / `Space` | Advance the title card and prologue |

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

## Project layout

```
main.py              event pump, state dispatch, rendering
src/settings.py      every tuning constant and the palette
src/states.py        the State enum
src/chamber.py       static level geometry and collision queries
src/session.py       one run's mutable state and its simulation step
src/player.py        player physics
src/hazards.py       falling hazard spawner
src/audio.py         sound loading, degrades to silence with no device
src/overlay.py       cached CRT scanline and vignette
src/prologue.py      typewriter reveal of PROLOGUE.txt
tools/gen_sfx.py     regenerates the sound effects
tests/               unit tests
```

Balance lives entirely in `src/settings.py`. The simulation runs at a
fixed 320x180 internal resolution and is scaled 3x with nearest-neighbour
so pixels stay square.

## Development

```sh
python -m unittest discover -s tests -t .   # 69 tests
ruff check .                                 # lint
python tools/gen_sfx.py                      # regenerate sounds
```

`tools/gen_sfx.py` uses only the standard library and is deterministic, so
regenerating produces byte-identical files. A test asserts the committed
WAVs still match a fresh synthesis. The tests set `SDL_VIDEODRIVER` and
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

All sound effects are synthesised from scratch by `tools/gen_sfx.py` and
carry no third-party rights.

## License

No license has been chosen for the game source yet. The bundled font is
separately licensed under CC BY-SA 4.0 as described above.
