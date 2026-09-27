import importlib.util
import unittest
from pathlib import Path

from src.settings import VERSION

REPO = Path(__file__).resolve().parent.parent
SOURCE = (REPO / "tools" / "build_release.py").read_text()


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_release_under_test", REPO / "tools" / "build_release.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackageNameTest(unittest.TestCase):
    def test_default_package_tracks_the_declared_version(self):
        builder = load_builder()
        self.assertEqual(builder.DEFAULT_PACKAGE, f"memLeak-{VERSION}")
        self.assertEqual(builder.resolve_package(None), f"memLeak-{VERSION}")

    def test_no_version_is_hardcoded_in_the_builder(self):
        self.assertNotIn('PACKAGE = "memLeak-', SOURCE)
        self.assertNotIn("memLeak-1.0", SOURCE)

    def test_override_is_honoured_for_rebuilding_an_older_release(self):
        builder = load_builder()
        self.assertEqual(builder.resolve_package("memLeak-1.0"), "memLeak-1.0")

    def test_unsafe_package_names_are_refused(self):
        builder = load_builder()
        for bad in ("", ".", "..", "a/b", "a\\b", "../escape"):
            with self.subTest(bad):
                with self.assertRaises(SystemExit):
                    builder.resolve_package(bad)

    def test_allowlist_still_covers_the_shipped_tree(self):
        builder = load_builder()
        self.assertEqual(builder.check_allowed(builder.members()), 0)


if __name__ == "__main__":
    unittest.main()
