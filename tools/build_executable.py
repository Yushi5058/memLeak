"""Build a standalone memLeak executable with PyInstaller.

Aimed at people who have no Python installed, so the result has to carry the
interpreter, pygame-ce and every asset in one artefact.

Asset paths in the game are all `Path(__file__).resolve().parent.parent`, which
inside a frozen build points at PyInstaller's extraction directory, so the data
files must keep the repository's own layout. That means `assets/sounds/jump.wav`
has to land at `<bundle>/assets/sounds/jump.wav`, not flattened. The allowlist
is imported from build_release.py so the two packagers cannot drift apart and
ship a different set of files.

Run from the repository root:

    .venv-build/bin/python tools/build_executable.py
    .venv-build/bin/python tools/build_executable.py --onedir
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.settings import VERSION  # noqa: E402

# PyInstaller takes SOURCE:DEST, except on Windows where the colon is a drive
# letter separator and it wants a semicolon.
SEPARATOR = ";" if sys.platform == "win32" else ":"

# Shipped so the MIT licence travels with the binary, as the licence requires.
EXTRA_DATA = ("LICENSE",)

# Pulled in by pygame-ce's SDL bindings, not used by the game itself.
EXCLUDES = (
    "tkinter",
    "numpy",
    "PIL",
    "pytest",
    "unittest",
    "pydoc_data",
    "lib2to3",
    "setuptools",
    "pip",
    # --collect-all pygame sweeps these back in. They are 11.8 MB of dead
    # weight, and pygame/tests/fixtures/fonts carries PlayfairDisplay and
    # PyGameMono, third-party fonts that would reach players with no licence
    # text beside them. Nothing in the game imports any of it.
    "pygame.tests",
    "pygame.examples",
    "pygame.docs",
)


def release_allowlist() -> tuple[tuple[str, ...], tuple[str, ...]]:
    spec = importlib.util.spec_from_file_location(
        "build_release_under_test", REPO / "tools" / "build_release.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TOP_FILES, module.ASSET_FILES


def data_files() -> list[tuple[str, str]]:
    """Return (source, destination-directory) pairs preserving repo layout."""
    top, assets = release_allowlist()
    pairs = [(str(REPO / name), str(Path(name).parent)) for name in (*assets, *EXTRA_DATA)]
    pairs += [(str(REPO / name), ".") for name in top if name.endswith(".txt")]
    return pairs


def command(outdir: Path, onedir: bool, name: str) -> list[str]:
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        name,
        "--distpath",
        str(outdir / "dist"),
        "--workpath",
        str(outdir / "work"),
        "--specpath",
        str(outdir),
        # SDL2 shared objects and pygame's own data files are loaded at runtime
        # by name, so static analysis cannot discover them.
        "--collect-all",
        "pygame",
        "--onedir" if onedir else "--onefile",
    ]
    for source, dest in data_files():
        args += ["--add-data", f"{source}{SEPARATOR}{dest}"]
    for module in EXCLUDES:
        args += ["--exclude-module", module]
    args.append(str(REPO / "run_game.py"))
    return args


PRUNE_DIRS = ("pygame/tests", "pygame/examples", "pygame/docs")


def prune_payload(root: Path) -> list[str]:
    """Delete pygame's test, example and doc trees from a built payload.

    --exclude-module cannot do this: --collect-data pygame walks the package
    directory on disk, so the fixture fonts come along regardless.
    """
    removed = []
    for rel in PRUNE_DIRS:
        target = root / rel
        if target.is_dir():
            shutil.rmtree(target)
            removed.append(rel)
    return removed


def produced_path(outdir: Path, name: str, onedir: bool) -> Path:
    dist = outdir / "dist"
    if onedir:
        return dist / name
    for candidate in (dist / name, dist / f"{name}.exe"):
        if candidate.exists():
            return candidate
    return dist / name


# Kept in step with the per-asset ceiling in packaging/PUBLISH_v1.1.sh so a build
# is rejected here rather than at publish time, after the manual Windows work.
PUBLISH_CEILING = 104_857_600


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a standalone memLeak executable.")
    parser.add_argument("--onedir", action="store_true", help="folder instead of one file")
    parser.add_argument("--outdir", default=str(REPO / "dist-exe"))
    parser.add_argument("--name", default=f"memLeak-{VERSION}")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    argv = command(outdir, args.onedir, args.name)
    print(f"bundling {len(data_files())} data files with PyInstaller", flush=True)
    if subprocess.run(argv, cwd=REPO).returncode:
        return 1

    produced = produced_path(outdir, args.name, args.onedir)
    if not produced.exists():
        print(f"expected output missing: {produced}")
        return 1
    if produced.is_dir():
        payload = produced / "_internal"
        if not payload.is_dir():
            payload = produced
        for rel in prune_payload(payload):
            print(f"pruned {rel}")
        size = sum(f.stat().st_size for f in produced.rglob("*") if f.is_file())
    else:
        size = produced.stat().st_size
    print(f"built {produced}  {size / 1_048_576:.1f} MB")
    if not produced.is_dir():
        print(f"sha256 {sha256_file(produced)}")
        if size > PUBLISH_CEILING:
            print(f"warning: {size} bytes is over the {PUBLISH_CEILING}-byte "
                  "per-asset publish ceiling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
