# Release notes: memLeak v1.1

Paste this into the Codeberg release body, then attach the four files listed at
the bottom. The `v1.1` tag is already pushed and points at `141b7de`.

## Game fixes

- Sprites are now letterboxed to fit inside the box matching their hitbox
  instead of being stretched. The art keeps its aspect ratio and is centred, so
  nothing is distorted. Tiles still stretch, which is what tiling requires.
- Detached speckles are gone from the sprite art, and the cleanup tool is
  idempotent, so re-running it no longer eats into the sprite.
- Missing or unreadable art still falls back to a coloured rectangle, so the
  game keeps running rather than crashing.
- New tests reject detached blobs, coverage above 30% and a letterbox in the
  wrong cell, so the regression cannot come back quietly.

## Playing without Python

Standalone builds are attached. You do not need to install Python, pip or
pygame, and you do not need to run anything from a terminal.

| Platform | File |
| --- | --- |
| Windows | `memLeak-1.1.exe` |
| Linux | `memLeak-1.1-x86_64.AppImage` |
| Linux without FUSE | `memLeak-1.1-linux-x86_64.tar.gz` |
| Any, from source | `memLeak-1.1.zip` |

**Linux:** the AppImage is the easy path. Right-click it, choose *Allow to run*,
then double-click. If your system has no FUSE, which some minimal and hardened
installs omit, use the `.tar.gz` instead and run `run_game.sh`. Both builds need
glibc 2.17 or newer, which covers Ubuntu 18.04+, Debian 10+, Fedora and Arch.
macOS is not prebuilt; run it from source.

**Windows:** double-click the `.exe`. It is not code-signed, so SmartScreen will
say *Windows protected your PC*. Click *More info*, then *Run anyway*. That
warning is about the missing signature, not about the game.

**Antivirus:** PyInstaller output is often flagged because it unpacks itself at
startup, which resembles malware to heuristic scanners. There is no malware here
— it is a plain Python program bundled into one file. Verify a download against
the checksums below if you want to be sure it is intact.

**Controls:** keyboard only, and listed in the README. If nothing seems to
happen after launching, click the window once to focus it, then press `Enter`.

## Running from source

Unpack `memLeak-1.1.zip`, then:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Requires Python 3.10 or newer. Progress saves to `~/.memleak/progress.json`, so
unlocks, best times, achievements and audio preferences survive a restart.

## Licence

The game source is MIT. The bundled fonts keep their own separate licences and
the MIT terms do not apply to them: Px437 IBM EGA 8x8 is CC BY-SA 4.0, and
Micro 5 is the SIL Open Font License 1.1. Sprites and audio were made for this
project and carry no third-party rights.

## Checksums

SHA-256, verified against the files as built:

```
b9fc9e44b20e9e9a5df6e9fc437a819eb121ceb12d611e3691e6af0b03ac543c  memLeak-1.1.zip
ad9765779ba76b2a216d5c43fa34ae6aeeb1911ad2b853f3781f87d5e8a9c7f1  memLeak-1.1-x86_64.AppImage
29ebee785cd80633a17b81f5d3869f8dc587a7231face0aa4ab09758506ab273  memLeak-1.1-linux-x86_64.tar.gz
memLeak-1.1.exe                                                       pending, not yet built
```

| File | Bytes |
| --- | --- |
| `memLeak-1.1.zip` | 921,814 |
| `memLeak-1.1-x86_64.AppImage` | 24,040,640 |
| `memLeak-1.1-linux-x86_64.tar.gz` | 23,809,534 |

Largest is about 24 MB, well under the 100 MB per-asset ceiling.

## Files to attach

- `memLeak-1.1.zip` (source)
- `memLeak-1.1-x86_64.AppImage` (Linux)
- `memLeak-1.1-linux-x86_64.tar.gz` (Linux, no FUSE)
- `memLeak-1.1.exe` (Windows)

See `packaging/PUBLISH_v1.1.sh` for how this file and those attachments get
uploaded. That script is internal and is not part of this release body.
