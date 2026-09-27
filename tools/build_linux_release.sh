#!/usr/bin/env bash
# Build the portable Linux release: an AppImage and a tar.gz fallback.
#
#   tools/build_linux_release.sh
#
# Why this is not just tools/build_executable.py: PyInstaller bundles the shared
# libraries it finds on the build machine. Built on a current rolling-release
# distro, the collected libasound alone demands GLIBC_2.43, which silently
# excludes most players. The fix is to build inside a manylinux2014 container
# (CentOS 7, GLIBC_2.17) so every bundled library is an old one, then wrap the
# result in an AppImage so no FUSE-less host is left behind.
#
# The manylinux images ship a statically linked CPython with no shared
# libpython, which PyInstaller refuses to use, so a python-build-standalone
# interpreter is staged in instead. That interpreter already has a GLIBC_2.17
# baseline, so it runs fine inside the old container.
#
# Result: both artefacts run on GLIBC_2.17 and newer, which covers Ubuntu
# 18.04+, Debian 10+, Fedora and Arch.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO/dist-portable"
STAGE="${STAGE:-/tmp/memleak-portable-stage}"
IMAGE="${IMAGE:-quay.io/pypa/manylinux2014_x86_64:latest}"
PINNED_PYTHON="${PINNED_PYTHON:-cpython-3.12.10-linux-x86_64-gnu}"
UV_PYTHON_DIR="${UV_PYTHON_DIR:-$HOME/.local/share/uv/python}"
APPIMAGETOOL="${APPIMAGETOOL:-/tmp/memleak-appimagetool-x86_64.AppImage}"

say() { printf '\n=== %s ===\n' "$1"; }

# The payload is smoke-tested directly, but the launcher is what users actually
# run, and a bad substitution in it produces a file that exists and still cannot
# start. Check the substitution landed and that the target is really there.
verify_launcher() {
    launcher="$1"
    binary="$2"
    if grep -q 'VERSION' "$launcher"; then
        echo "refusing to ship: $launcher still has an unsubstituted VERSION token" >&2
        exit 1
    fi
    if [ ! -e "$binary" ]; then
        echo "refusing to ship: $launcher points at a missing binary: $binary" >&2
        exit 1
    fi
}

command -v podman >/dev/null || { echo "podman is required" >&2; exit 1; }

# Read the version from the single source of truth rather than pattern-matching
# settings.py, which has a trailing comment on the VERSION line.
VERSION="$(cd "$REPO" && python3 -c 'import sys; sys.path.insert(0, "."); from src.settings import VERSION; print(VERSION)')"
[ -n "$VERSION" ] || { echo "could not read VERSION from src/settings.py" >&2; exit 1; }

say "Staging a shared-libpython interpreter ($PINNED_PYTHON)"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$UV_PYTHON_DIR/$PINNED_PYTHON" "$STAGE/py312"
"$STAGE/py312/bin/python3.12" -c 'import sys; assert sys.version_info[:2] == (3, 12)'

say "Building the PyInstaller onedir payload inside $IMAGE"
rm -rf "$OUT"
podman run --rm \
    -v "$REPO":/src \
    -v "$STAGE":/stage:ro \
    -w /src \
    "$IMAGE" /bin/bash -c '
        set -e
        /stage/py312/bin/python3.12 -m venv /tmp/venv
        /tmp/venv/bin/pip install -q --upgrade pip setuptools wheel
        /tmp/venv/bin/pip install -q "pyinstaller==6.22.3" "pygame-ce==2.5.8"
        /tmp/venv/bin/python tools/build_executable.py --onedir --outdir /src/dist-portable
    '

PAYLOAD="$OUT/dist/memLeak-$VERSION"
[ -x "$PAYLOAD/memLeak-$VERSION" ] || { echo "payload missing: $PAYLOAD" >&2; exit 1; }

say "Confirming the GLIBC ceiling before shipping"
HIGHEST="$(find "$PAYLOAD" \( -name '*.so' -o -name '*.so.*' -o -name "memLeak-$VERSION" \) -type f -print0 \
    | xargs -0 -r objdump -T 2>/dev/null \
    | grep -o 'GLIBC_[0-9]\+\.[0-9]\+' | sort -t_ -k2 -V -u | tail -1)"
echo "highest required symbol: ${HIGHEST:-none}"
case "${HIGHEST:-GLIBC_2.0}" in
    GLIBC_2.1[0-7]|GLIBC_2.[0-9]) ;;
    *) echo "refusing to ship: the payload needs ${HIGHEST}, newer than the 2.17 target" >&2; exit 1 ;;
esac

say "Smoke-testing the payload headless"
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 20 "$PAYLOAD/memLeak-$VERSION" \
    && { echo "exited too early, the event loop never started"; exit 1; } \
    || echo "stayed running, as expected"

say "Fetching appimagetool"
if [ ! -x "$APPIMAGETOOL" ]; then
    curl -fsSL -o "$APPIMAGETOOL" \
        https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$APPIMAGETOOL"
fi

APPDIR="$STAGE/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR"
cp -a "$PAYLOAD" "$APPDIR/payload"
cp "$REPO/packaging/memleak.png" "$APPDIR/memleak.png"
ln -sf memleak.png "$APPDIR/.DirIcon"
cp "$REPO/packaging/memleak.desktop" "$APPDIR/memleak.desktop"
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/sh
# AppImage entry point. The PyInstaller onedir payload has to stay in one
# directory because it resolves its data files relative to its own location.
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/payload/memLeak-$VERSION" "$@"
APPRUN
sed -i "s/\$VERSION/$VERSION/g" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"
verify_launcher "$APPDIR/AppRun" "$APPDIR/payload/memLeak-$VERSION"

say "Building the AppImage"
ARCH=x86_64 "$APPIMAGETOOL" --no-appstream "$APPDIR" "$OUT/memLeak-$VERSION-x86_64.AppImage"

say "Building the tar.gz fallback for hosts that refuse AppImages"
TARDIR="$STAGE/memLeak-$VERSION-linux"
rm -rf "$TARDIR"
mkdir -p "$TARDIR"
cp -a "$PAYLOAD/." "$TARDIR/"
cp "$REPO/LICENSE" "$TARDIR/"
cat > "$TARDIR/run_game.sh" <<'LAUNCHER'
#!/bin/sh
# Fallback launcher for systems without FUSE. Self-contained: no Python needed.
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/memLeak-$VERSION" "$@"
LAUNCHER
sed -i "s/\$VERSION/$VERSION/g" "$TARDIR/run_game.sh"
chmod +x "$TARDIR/run_game.sh"
verify_launcher "$TARDIR/run_game.sh" "$TARDIR/memLeak-$VERSION"
cat > "$TARDIR/README.txt" <<'TARREADME'
memLeak VERSION - Linux (glibc 2.17 or newer)

Run:   ./run_game.sh

No install step and no Python needed. Unpack, then run the script.

If it will not start, make it executable:  chmod +x run_game.sh memLeak-VERSION

Controls are in the project README. The game is keyboard-only.

Licence: MIT (see LICENSE). The bundled fonts keep their own licences:
Px437 IBM EGA 8x8 is CC BY-SA 4.0, Micro 5 is SIL OFL 1.1.
TARREADME
sed -i "s/VERSION/$VERSION/g" "$TARDIR/README.txt"
tar -czf "$OUT/memLeak-$VERSION-linux-x86_64.tar.gz" -C "$STAGE" "memLeak-$VERSION-linux"

say "Artefacts"
(cd "$OUT" && sha256sum ./*.AppImage ./*.tar.gz) && ls -lh "$OUT"/*.AppImage "$OUT"/*.tar.gz | awk '{print "  " $5 "\t" $9}'
echo
echo "Both need GLIBC_2.17 or newer: Ubuntu 18.04+, Debian 10+, Fedora, Arch."
