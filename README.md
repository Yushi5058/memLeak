# memLeak

A PyWeek jam platformer about spending a finite budget of Earth years.

You stand still and the planet loses time. Reach the gate before the
allocation hits zero or your vital chronos deplete.

## Requirements

- Python 3.10 or newer
- A display; the game opens a 960x540 window

## Install and run

### Linux / macOS

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Windows (Command Prompt / PowerShell)

```cmd
:: Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

:: Install dependencies and launch
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
| --- | --- |
| `Up` / `Down` | Move the menu selection |
| `Left` / `Right` | Adjust the selected settings row |
| `Enter` / `Space` | Confirm, or advance the current script one phase |
| `S` | Skip the rest of the current script and start playing |
| `Esc` | Back out of a menu, or pause and resume |
| `Left` / `A` | Step left (costs 0.5 years) |
| `Right` / `D` | Step right (costs 0.5 years) |
| `Space` | Jump (costs 2 years, only when grounded) |
| `R` | Retry after winning or running out |

Every menu is keyboard-only; there is no mouse input.

## How it plays

`EARTH_ALLOC` represents the timeline's lifespan and your final score, while your
**3-Heart Vital System** safeguards your physical cohesion:

- **Temporal Drain**: Standing still burns years continually based on the chamber's atmospheric decay rate.
- **Action Tax**: Stepping costs 0.5 years; jumping costs 2.0 years.
- **Hazard Damage**: Hazard strikes damage your hearts instead of draining years, granting 1.0s of invulnerability frames (i-frames):
  - **Falling Meteorite**: Deducts 0.5 heart.
  - **Time-Infected Robot**: Deducts 1.0 heart.
  - **Black Hole Singularity**: Deducts 1.0 heart.
- **Timeline Failure**: The run halts if `EARTH_ALLOC` reaches 0 or your hearts reach 0.0.

Clearing a chamber banks whatever allocation remains, and your best time and saved
years persist across retries.

## The three chambers

Progress is saved to `~/.memleak/progress.json`, so unlocks, best times,
best years, achievements, read story scripts, and audio preferences all survive a restart.

| Chamber | Starting Time | Drain Rate | What changes |
| --- | --- | --- | --- |
| `OUTER HULL` | 500.0 YRS | 6.0 YRS/s | Training run. Generous margin, falling meteorites only. |
| `CARGO SPINE` | 440.0 YRS | 9.0 YRS/s | Faster drain, tighter spawns, time-infected patrol robots. |
| `CORE BREACH` | 380.0 YRS | 13.0 YRS/s | Rapid decay, narrow platforms, high-speed black hole singularities. |

`src/levels.py` holds the level table and a geometry validator that enforces
physics reach budgets, ensuring jumps are physically clearable before shipping.

## Achievements

Seven achievements in total (five visible, two hidden secrets revealed when earned):

| Key | How |
| --- | --- |
| `first_steps` | Clear the first chamber |
| `clean_run` | Clear any chamber without taking a hit |
| `speedster` | Clear a chamber under its par time |
| `deep_pocket` | Bank at least 300 years in one run |
| `completionist` | Clear all three chambers |

Secret achievements stay off the screen and do not contribute to the header
count until unlocked. Discover them through disciplined play.

## Sprites

The game ships with hand-made pixel art for every character, hazard and tile, so it needs
no external downloads to run. Each PNG is rescaled to the box matching its hitbox, and
anything missing or unreadable falls back to a coloured rectangle per-sprite, so the
game still runs if the art is stripped.

| File | Target size | Replaces | Tiled? |
| --- | --- | --- | --- |
| `player.png` | 24x32 | Player hitbox (12x16) | no |
| `hazard_falling.png` | 20x28 | Falling meteorite (10x14) | no |
| `hazard_moving.png` | 24x20 | Time-infected robot (12x10) | no |
| `hazard_blackhole.png` | 28x28 | Black hole singularity (14x14) | no |
| `portal.png` | 28x40 | Exit gate (14x20) | no |
| `tile_platform.png` | 16x16 | Ground and ledges | yes |
| `tile_hazard.png` | 8x8 | Floor spikes and wall barriers | yes |

Images are rescaled to their canonical box on load. The complete visual brief, palette
hex locks and image-generation prompts live in `docs/SPRITES.md` in the development
repository, which is not part of the release archive.

## Project layout

The first block below is what ships in the release archive.

```
run_game.py          version guard, then hands off to main
main.py              event pump, state dispatch, rendering
LICENSE              MIT licence for the game source
requirements.txt     pinned dependency
PROLOGUE.txt         script shown before the first chamber
CHAPTER_I.txt        script shown on entering the second chamber
CHAPTER_II.txt       script shown on entering the third chamber
src/settings.py      palette, window and display tuning constants
src/states.py        the State enum
src/menu.py          reusable keyboard menu widget
src/screens.py       main, pause, level select, settings, achievements
src/levels.py        level table, mover definitions, and geometry validator
src/progression.py   saved profile on disk
src/flow.py          chamber routing, restart, advance, and win recording
src/achievements.py  achievement definitions and unlock rules
src/chamber.py       static level geometry and collision queries
src/session.py       run simulation, 3-heart system, i-frames, and timer integration
src/player.py        player physics and collision resolution
src/hazards.py       falling meteorites, moving robots, and black holes
src/sprites.py       sprite loading, normalising, rectangle fallback
src/audio.py         sfx and music playback, degrades to silence
src/overlay.py       cached CRT scanline and vignette
src/prologue.py      phased typewriter reveal of PROLOGUE.txt
src/chapters.py      CHAPTER_I/II scripts and on-screen narration manager
assets/              fonts and their licences, chiptune audio, sprite art
```

These live in the development repository only and are not shipped in the archive:

```
tools/build_release.py  builds the release archive from an allowlist
tools/gen_sfx.py     regenerates the sound effects
tools/gen_music.py   regenerates the chiptune loops
tests/               unit tests
docs/SPRITES.md      visual brief and image-generation prompts
```

`PROLOGUE.txt` introduces the first chamber. Each later chamber has its own
`CHAPTER_*.txt` script shown upon entry. Press `S` to skip straight to play or
`Enter` to advance phase-by-phase. Lines wrap to 18 columns to fit the 320px screen.

Once every chamber has been cleared, the final cleared screen offers `Enter`
to return to the main menu. Everything remains replayable, and achievements stay reachable.

Balance lives entirely in `src/levels.py`. The simulation runs at a
fixed 320x180 internal resolution and is scaled 3x with nearest-neighbour so pixels stay square.

## Development

Everything in this section needs the full repository, not the release archive.

```sh
python -m unittest discover -s tests -t .   # 277 tests
ruff check .                                 # lint
python tools/gen_sfx.py                      # regenerate sounds
python tools/gen_music.py                    # regenerate music
python tools/build_release.py                # build memLeak-1.0.zip
```

`tools/gen_sfx.py` and `tools/gen_music.py` use only the standard library
and are deterministic, so regenerating produces byte-identical files.
`tools/build_release.py` is deterministic too, and builds the archive from an
explicit allowlist rather than an exclusion list, so agent traces and secret
achievement notes cannot slip in by being forgotten.
Tests set `SDL_VIDEODRIVER` and `SDL_AUDIODRIVER` to `dummy`, allowing them to run headless.

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

`assets/fonts/Micro5-Regular.ttf` is **Micro 5** by **The Soft Type Project
Authors**, obtained from the Google Fonts repository at
<https://github.com/google/fonts/tree/main/ofl/micro5>.

Licensed under the **SIL Open Font License, Version 1.1** — the full license
text is in `assets/fonts/OFL-Micro5.txt`. Vendored file SHA-256:
`08a08c0d10129d2ecd869ff2f8914fcbf32487d3cbee3568b2a2957866dfdac8`.

Micro 5 is used for the achievement goal text. Its glyphs sit on a 5x6 pixel
grid, rendering 1:1 at 14px with crisp square pixels.

### Audio

All sound effects and music are synthesised from scratch for this project and carry no
third-party rights. The generator scripts live in the development repository and are
not part of the release archive.

### Sprites

No external sprite art is bundled. Everything in `assets/sprites/` was drawn for this
entry and carries no third-party rights.

## License

The game source code is released under the **MIT License** — the full text is in
`LICENSE`.

The bundled fonts keep their own separate licences, listed under
[Third-party assets](#third-party-assets): Pix437 IBM EGA 8x8 under CC BY-SA 4.0, and
Micro 5 under the SIL Open Font License 1.1. The MIT licence does not apply to them.

This release is version 1.0, submitted to PyWeek. **Any later version may be released
under different terms**, including a commercial licence, so check the licence that
ships with the version you have rather than assuming MIT carries forward.

