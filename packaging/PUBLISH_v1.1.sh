#!/usr/bin/env bash
# Create the memLeak v1.1 release on Codeberg and attach the built artefacts.
#
#   packaging/PUBLISH_v1.1.sh
#
# Prerequisites, both of which need your account rather than this script:
#   1. The repository is public, otherwise the release assets are unreachable.
#   2. A token exists at Codeberg > Settings > Applications.
#
# The tag v1.1 is already pushed, so nothing here creates a new commit.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

SLUG="yushi_61/memLeak"
# Overridable because tag v1.1 was pushed before the launcher bug was found, so
# it points at a commit whose build script cannot produce a working artefact.
# Resolve that by retagging or by naming a new tag, then run with TAG set:
#     TAG=v1.1.1 ./packaging/PUBLISH_v1.1.sh
TAG="${TAG:-v1.1}"
TITLE="memLeak 1.1"
NOTES="packaging/RELEASE_NOTES_v1.1.md"
SERVER="https://codeberg.org"

ASSETS=(
    "memLeak-1.1.zip"
    "dist-portable/memLeak-1.1-x86_64.AppImage"
    "dist-portable/memLeak-1.1-linux-x86_64.tar.gz"
    "dist-windows/dist/memLeak-1.1.exe"
)

die() { printf '\n[X] %s\n\n' "$1" >&2; exit 1; }

command -v tea >/dev/null || die "tea is not installed"

# tea calls this 'login add'; there is no 'login create'. And 'login add' takes a
# token, or a user and password to mint one.
# --output json because the plain listing prints a table header even when no
# logins exist, so grepping its text would always succeed.
if [ "$(tea login list --output json 2>/dev/null | tr -d '[:space:]')" = "[]" ]; then
    printf '\nNo tea login found. Create one with:\n\n'
    printf '    tea login add --name codeberg --url %s --token <your-token>\n\n' "$SERVER"
    printf 'Get a token from %s/yushi_61/settings/applications\n\n' "$SERVER"
    die "no authenticated tea login"
fi

[ -f "$NOTES" ] || die "release notes missing: $NOTES"

missing=()
for asset in "${ASSETS[@]}"; do
    [ -f "$asset" ] || missing+=("$asset")
done
if [ ${#missing[@]} -gt 0 ]; then
    die "not built yet: ${missing[*]}"
fi

printf '\nArtefacts to attach:\n'
ls -lh "${ASSETS[@]}" | awk '{print "  " $5 "\t" $9}'

largest=$(du -b "${ASSETS[@]}" | sort -n | tail -1 | cut -f1)
if [ "$largest" -gt 104857600 ]; then
    die "largest asset is $largest bytes, over the 100 MB per-asset ceiling"
fi

printf '\nCreating the release ...\n'
# Attachments are passed as repeated --asset on create. There is no
# 'tea releases upload' subcommand; that name does not exist.
args=(releases create
    --repo "$SLUG"
    --tag "$TAG"
    --title "$TITLE"
    --note-file "$NOTES")
for asset in "${ASSETS[@]}"; do
    args+=(--asset "$asset")
done

tea "${args[@]}"

printf '\nDone. Verify with:\n\n    tea releases --repo %s\n\n' "$SLUG"
