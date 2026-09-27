import hashlib
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExecutableDataFileTest(unittest.TestCase):
    def setUp(self):
        self.packager = load("build_executable")
        self.release = load("build_release")
        self.bundled = {
            Path(source).relative_to(REPO).as_posix()
            for source, _ in self.packager.data_files()
        }

    def test_every_bundled_source_exists(self):
        for source, _ in self.packager.data_files():
            with self.subTest(source):
                self.assertTrue(Path(source).is_file(), source)

    def test_layout_is_preserved_so_frozen_paths_resolve(self):
        # The game reads assets via Path(__file__).parent.parent / "assets", which
        # inside the bundle is the extraction root, so each file has to keep its
        # own subdirectory rather than being flattened.
        for source, dest in self.packager.data_files():
            with self.subTest(source):
                relative = Path(source).relative_to(REPO)
                self.assertEqual(Path(dest), relative.parent)

    def test_asset_allowlist_cannot_drift_from_the_source_archive(self):
        missing = set(self.release.ASSET_FILES) - self.bundled
        self.assertEqual(missing, set(), f"shipped by the zip but not bundled: {missing}")

    def test_every_script_the_game_reads_at_runtime_is_bundled(self):
        for script in ("PROLOGUE.txt", "CHAPTER_I.txt", "CHAPTER_II.txt"):
            with self.subTest(script):
                self.assertIn(script, self.bundled)

    def test_entry_point_exists(self):
        self.assertTrue((REPO / "run_game.py").is_file())

    def test_licence_travels_with_the_binary(self):
        self.assertIn("LICENSE", self.bundled)

    def test_data_separator_matches_the_platform(self):
        self.assertEqual(self.packager.SEPARATOR, ";" if sys.platform == "win32" else ":")


class CommandContractTest(unittest.TestCase):
    def setUp(self):
        self.packager = load("build_executable")
        self.outdir = Path("/tmp/memleak-contract-check")

    def test_default_is_onefile(self):
        argv = self.packager.command(self.outdir, onedir=False, name="memLeak-1.1")
        self.assertIn("--onefile", argv)
        self.assertNotIn("--onedir", argv)

    def test_onedir_swaps_the_layout_flag(self):
        argv = self.packager.command(self.outdir, onedir=True, name="memLeak-1.1")
        self.assertIn("--onedir", argv)
        self.assertNotIn("--onefile", argv)

    def test_explicit_onefile_flag_is_rejected(self):
        # Onefile is the default, so argparse rejects an explicit --onefile.
        # build_windows.bat passed one, and the build died at the final step on
        # a Windows machine that took an hour to set up.
        saved = sys.argv
        sys.argv = ["build_executable.py", "--onefile"]
        try:
            with self.assertRaises(SystemExit):
                self.packager.main()
        finally:
            sys.argv = saved

    def test_name_is_passed_through(self):
        argv = self.packager.command(self.outdir, onedir=False, name="custom-name")
        self.assertIn("custom-name", argv)

    def test_pygame_bloat_is_pruned_from_the_payload(self):
        # Asserting the --exclude-module flags are present is not enough: they
        # were, and the 11.8 MB of fixtures still shipped, because
        # --collect-data walks the package directory on disk. So check the
        # payload actually loses the bloat and keeps what the game imports.
        root = Path("/tmp/memleak-prune-check")
        if root.exists():
            shutil.rmtree(root)
        for rel in ("pygame/tests/fixtures", "pygame/examples", "pygame/docs"):
            (root / rel).mkdir(parents=True)
            (root / rel / "stub.txt").write_text("x")
        (root / "pygame" / "font.py").write_text("x")

        removed = self.packager.prune_payload(root)

        self.assertEqual(
            sorted(removed), ["pygame/docs", "pygame/examples", "pygame/tests"]
        )
        self.assertFalse((root / "pygame" / "tests").exists())
        self.assertFalse((root / "pygame" / "examples").exists())
        self.assertFalse((root / "pygame" / "docs").exists())
        self.assertTrue((root / "pygame" / "font.py").exists())
        shutil.rmtree(root)


class WindowsBranchTest(unittest.TestCase):
    """The Windows build can only be run by hand on a VM, so check the branch here.

    SEPARATOR is decided at import time, so the module has to be re-executed
    with sys.platform patched rather than merely re-read.
    """

    def setUp(self):
        self.saved_platform = sys.platform
        sys.platform = "win32"
        try:
            self.packager = load("build_executable")
        finally:
            sys.platform = self.saved_platform

    def test_separator_is_a_semicolon_on_windows(self):
        self.assertEqual(self.packager.SEPARATOR, ";")

    def test_add_data_entries_use_the_windows_separator(self):
        argv = self.packager.command(Path("/tmp/x"), onedir=False, name="memLeak-1.1")
        entries = [argv[i + 1] for i, arg in enumerate(argv) if arg == "--add-data"]
        self.assertTrue(entries)
        for entry in entries:
            with self.subTest(entry):
                self.assertIn(";", entry)

    def test_data_files_survive_the_reload(self):
        self.assertTrue(self.packager.data_files())


class ReleaseMetadataTest(unittest.TestCase):
    """The builder reports the digest and size the publisher will check.

    The Windows build runs on a machine the maintainer drives by hand, so the
    digest it prints is what gets pasted into the release notes. These pin the
    two values that hand-off depends on.
    """

    def setUp(self):
        self.packager = load("build_executable")

    def test_sha256_file_matches_the_standard_abc_vector(self):
        with tempfile.NamedTemporaryFile() as handle:
            handle.write(b"abc")
            handle.flush()
            self.assertEqual(
                self.packager.sha256_file(Path(handle.name)),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )

    def test_sha256_file_handles_content_spanning_read_chunks(self):
        payload = b"x" * (1 << 20) + b"tail"
        with tempfile.NamedTemporaryFile() as handle:
            handle.write(payload)
            handle.flush()
            digest = self.packager.sha256_file(Path(handle.name))
        self.assertEqual(digest, hashlib.sha256(payload).hexdigest())

    def test_publish_ceiling_agrees_with_the_publish_script(self):
        script = (REPO / "packaging" / "PUBLISH_v1.1.sh").read_text()
        self.assertIn(str(self.packager.PUBLISH_CEILING), script)


if __name__ == "__main__":
    unittest.main()
