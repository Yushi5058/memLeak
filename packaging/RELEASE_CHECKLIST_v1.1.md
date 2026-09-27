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
  does not match them. `PUBLISH_v1.1.sh` warns about this at publish time. Either
  retag to the fix commit, or pass `TAG=<newtag>`.
- **The Windows `.exe` is not built yet.** Build it on a Windows machine with
  Python 3.10+ on PATH: `tools\build_windows.bat`.
- **The repository must be public** and `tea` authenticated:
  `tea login add --name codeberg --url https://codeberg.org --token <token>`.

## Steps

1. Build the missing `.exe` and copy it to `dist-windows/dist/memLeak-1.1.exe`.
2. Add its SHA-256 to the checksum table in `RELEASE_NOTES_v1.1.md`. The publish
   script refuses to run until every asset's real digest appears there, so this
   is not optional bookkeeping.
3. Resolve the tag as above.
4. Confirm the repository is public and `tea login list --output json` is not `[]`.
5. `./packaging/PUBLISH_v1.1.sh` — add `TAG=<newtag>` if the tag changed.
6. Verify with `tea releases --repo yushi_61/memLeak`, then download each asset
   and check it against the published checksums.

## Files to attach

- `memLeak-1.1.zip` (source)
- `memLeak-1.1-x86_64.AppImage` (Linux)
- `memLeak-1.1-linux-x86_64.tar.gz` (Linux, no FUSE)
- `memLeak-1.1.exe` (Windows)
