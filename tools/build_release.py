"""Build the PyWeek release archive for memLeak from an explicit allowlist.

Standard library only, matching the rest of tools/. Deterministic: running
twice produces a byte-identical archive, so the upload can be checked against
a local rebuild.

The allowlist is deliberately explicit rather than "everything except X". An
exclusion list silently ships whatever someone forgets to think of, and this
repository holds two things that must never reach a judge: the secret
achievement notes and the agent session traces under .omo/.

Run it with no arguments from anywhere:

    python tools/build_release.py
"""

import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKAGE = "memLeak-1.0"
OUT = REPO / f"{PACKAGE}.zip"

TOP_FILES = (
    "run_game.py",
    "main.py",
    "LICENSE",
    "README.md",
    "requirements.txt",
    "PROLOGUE.txt",
    "CHAPTER_I.txt",
    "CHAPTER_II.txt",
)

ASSET_FILES = (
    "assets/fonts/LICENSE.TXT",
    "assets/fonts/Micro5-Regular.ttf",
    "assets/fonts/OFL-Micro5.txt",
    "assets/fonts/Px437_IBM_EGA_8x8.ttf",
    "assets/music/game.wav",
    "assets/music/menu.wav",
    "assets/music/prologue.wav",
    "assets/sounds/hazard.wav",
    "assets/sounds/jump.wav",
    "assets/sounds/land.wav",
    "assets/sounds/portal.wav",
    "assets/sounds/ui.wav",
    "assets/sprites/hazard_blackhole.png",
    "assets/sprites/hazard_falling.png",
    "assets/sprites/hazard_moving.png",
    "assets/sprites/player.png",
    "assets/sprites/portal.png",
    "assets/sprites/tile_hazard.png",
    "assets/sprites/tile_platform.png",
)

# Fixed timestamp so two builds of the same tree agree byte for byte.
STAMP = (2026, 1, 1, 0, 0, 0)

# Any archive path containing one of these is a packaging bug, not a warning.
FORBIDDEN = (
    ".omo",
    "SECRET_ACHIEVEMENTS",
    "run-continuation",
    ".ruff_cache",
    "__pycache__",
    ".gitignore",
    "ruff.toml",
    ".gitkeep",
    "tests/",
    "tools/",
    "docs/",
)


def members() -> list[Path]:
    paths = [REPO / name for name in TOP_FILES]
    paths += [REPO / name for name in ASSET_FILES]
    paths += sorted((REPO / "src").glob("*.py"))
    return paths


def check_allowed(paths: list[Path]) -> int:
    absent = [str(p.relative_to(REPO)) for p in paths if not p.is_file()]
    if absent:
        print("Allowlist names a file that does not exist:")
        for name in absent:
            print(f"  {name}")
        return 1
    return 0


def check_clean(names: list[str]) -> int:
    smuggled = [n for n in names if any(bad in n for bad in FORBIDDEN)]
    if smuggled:
        print("Refusing to ship these paths:")
        for name in smuggled:
            print(f"  {name}")
        return 1
    return 0


def build(paths: list[Path]) -> list[str]:
    OUT.unlink(missing_ok=True)
    written: list[str] = []
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for src in sorted(paths):
            arcname = f"{PACKAGE}/{src.relative_to(REPO).as_posix()}"
            info = zipfile.ZipInfo(arcname, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, src.read_bytes())
            written.append(arcname)
    return written


def main() -> int:
    paths = members()
    if check_allowed(paths):
        return 1
    written = build(paths)
    if check_clean(written):
        OUT.unlink(missing_ok=True)
        return 1
    print(f"wrote {OUT.name}  entries={len(written)}  size={OUT.stat().st_size // 1024} KB")
    print("Upload this file. It is already gitignored, so it stays out of history.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
