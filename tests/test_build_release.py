import importlib.util
import re
import unittest
from pathlib import Path

from src.settings import VERSION

REPO = Path(__file__).resolve().parent.parent
SOURCE = (REPO / "tools" / "build_release.py").read_text()
README = (REPO / "README.md").read_text()
LAYOUT_HEADING = "The first block below is what ships"


def promised_layout() -> list[str]:
    _, _, after = README.partition(LAYOUT_HEADING)
    block = after.split("```")[1]
    return [line.split()[0] for line in block.splitlines() if line.strip()]


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


class ReadmeClaimTest(unittest.TestCase):
    def test_every_promised_path_really_ships(self):
        builder = load_builder()
        shipped = {p.relative_to(REPO).as_posix() for p in builder.members()}
        for entry in promised_layout():
            with self.subTest(entry):
                prefix = entry.rstrip("/") + "/"
                self.assertTrue(
                    any(name == entry or name.startswith(prefix) for name in shipped),
                    f"README promises {entry!r} in the release archive, but the "
                    f"allowlist does not ship it",
                )

    def test_documented_test_count_is_accurate(self):
        claimed = re.search(r"#\s*(\d+)\s+tests", README)
        self.assertIsNotNone(claimed, "README no longer states a test count")
        found = unittest.defaultTestLoader.discover(
            str(REPO / "tests"), top_level_dir=str(REPO)
        )
        self.assertEqual(
            claimed.group(1),
            str(found.countTestCases()),
            "README's test count is stale; update the number in the Development section",
        )


if __name__ == "__main__":
    unittest.main()
