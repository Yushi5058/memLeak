import importlib.util
import sys
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


if __name__ == "__main__":
    unittest.main()
