from pathlib import Path
import tempfile
import unittest

from scripts.validate_skill import validate_skill


class SkillValidationTests(unittest.TestCase):
    def setUp(self):
        # Temporary fixtures stay in this checkout and are removed by tearDown.
        self.scratch = tempfile.TemporaryDirectory(prefix=".test-tmp-", dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name) / "sample-skill"
        self.root.mkdir()
        self.entry = self.root / "SKILL.md"
        self.entry.write_text("---\nname: sample-skill\ndescription: A reusable example skill\n---\n# Example\n", encoding="utf-8")

    def test_valid_minimal_skill(self):
        self.assertEqual(validate_skill(self.root), [])

    def test_missing_entrypoint(self):
        self.entry.unlink()
        self.assertTrue(validate_skill(self.root))

    def test_invalid_yaml(self):
        self.entry.write_text("---\nname: [broken\n---\n", encoding="utf-8")
        self.assertTrue(validate_skill(self.root))

    def test_empty_description(self):
        self.entry.write_text("---\nname: sample-skill\ndescription: ''\n---\n", encoding="utf-8")
        self.assertTrue(validate_skill(self.root))

    def test_name_must_match_folder(self):
        self.entry.write_text("---\nname: another-skill\ndescription: Example\n---\n", encoding="utf-8")
        self.assertTrue(validate_skill(self.root))

    def test_broken_local_reference(self):
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Missing](references/missing.md)\n")
        self.assertTrue(validate_skill(self.root))

    def test_reference_must_stay_inside_package(self):
        (self.root.parent / "outside.md").write_text("Outside", encoding="utf-8")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Outside](../outside.md)\n")
        self.assertTrue(validate_skill(self.root))

    def test_valid_reference_with_anchor(self):
        (self.root / "reference.md").write_text("# Heading\n", encoding="utf-8")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Reference](reference.md#heading)\n[External](https://example.com/docs)\n")
        self.assertEqual(validate_skill(self.root), [])

    def test_ui_prompt_requires_actual_skill_invocation(self):
        (self.root / "agents").mkdir()
        (self.root / "agents" / "openai.yaml").write_text(
            "interface:\n  display_name: Example\n  short_description: A sufficiently descriptive example skill summary\n  default_prompt: Use another skill\n",
            encoding="utf-8",
        )
        self.assertTrue(validate_skill(self.root))

    def test_unfinished_scaffold_is_rejected(self):
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[TODO: finish this section]\n")
        self.assertTrue(validate_skill(self.root))


if __name__ == "__main__":
    unittest.main()
