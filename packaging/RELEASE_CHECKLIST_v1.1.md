# Release checklist: memLeak v1.1

Internal maintainer notes. Not part of the public release body.

The public body is `RELEASE_NOTES_v1.1.md`, which `PUBLISH_v1.1.sh` passes
straight to `tea releases create --note-file`. Keep process detail here so it
does not ship to the releases page.

## Open before publishing

- **Tag `v1.1` points at `141b7de`, a pre-fix commit.** The launcher bug meant
  the build script there emitted `memLeak-$1.1`, so that commit cannot produce a
  runnable artefact. The attached binaries are fine, but Codeberg generates the
  release page's source download from the tag, so visitors would get source that
  does not match them. `PUBLISH_v1.1.sh` therefore refuses to run until this is
  resolved. Either retag to the fix commit, publish against a tag that matches,
  or, if shipping the mismatch is genuinely intended, acknowledge it explicitly
  with `ALLOW_TAG_MISMATCH=1`.
- **The Windows `.exe` is not built yet.** Build it on a Windows machine with
  Python 3.10+ on PATH: `tools\build_windows.bat`.
- **The repository must be public** and `tea` authenticated:
  `tea login add --name codeberg --url https://codeberg.org --token <token>`.

## Steps

1. Build the missing `.exe`. `build_windows.bat` writes it straight to
   `dist-windows/dist/memLeak-1.1.exe`, which is where the publish script looks
   for it, so there is nothing to copy or rename.
2. Copy the `sha256 <digest>` line the build printed into the checksum table in
   `RELEASE_NOTES_v1.1.md`, replacing the `pending, not yet built` entry. The
   publish script refuses to run until every asset's real digest appears there, so
   this is not optional bookkeeping.
3. Resolve the tag as above.
4. Confirm the repository is public and `tea login list --output json` is not `[]`.
5. `./packaging/PUBLISH_v1.1.sh` — add `TAG=<tag>` if you published against a
   different tag, or `ALLOW_TAG_MISMATCH=1` if you decided to ship the mismatch.
6. Verify with `tea releases --repo yushi_61/memLeak`, then download each asset
   and check it against the published checksums.

## Files to attach

- `memLeak-1.1.zip` (source)
- `memLeak-1.1-x86_64.AppImage` (Linux)
- `memLeak-1.1-linux-x86_64.tar.gz` (Linux, no FUSE)
- `memLeak-1.1.exe` (Windows)
