from pathlib import Path
import tempfile
import unittest

from scripts.validate_skill import DEFAULT_SKILL, validate_skill


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

    def test_missing_anchor_in_existing_reference(self):
        (self.root / "reference.md").write_text("# Heading\n", encoding="utf-8")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Review](reference.md#missing)\n")
        self.assertTrue(any("Broken local anchor" in error for error in validate_skill(self.root)))

    def test_same_document_anchor_is_checked(self):
        original = self.entry.read_text(encoding="utf-8")
        for anchor, valid in (("example", True), ("missing", False)):
            with self.subTest(anchor=anchor):
                self.entry.write_text(original + f"\n[Jump](#{anchor})\n", encoding="utf-8")
                self.assertEqual(validate_skill(self.root) == [], valid)

    def test_explicit_anchor_supports_workflow_routes(self):
        (self.root / "reference.md").write_text('<a id="visual-review"></a>\n\n## 视觉审查\n', encoding="utf-8")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Review](reference.md#visual-review)\n")
        self.assertEqual(validate_skill(self.root), [])

    def test_encoded_path_and_unicode_heading_anchor(self):
        (self.root / "review notes.md").write_text("## 视觉 检查\n", encoding="utf-8")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Review](review%20notes.md#%E8%A7%86%E8%A7%89-%E6%A3%80%E6%9F%A5)\n")
        self.assertEqual(validate_skill(self.root), [])

    def test_data_attribute_is_not_an_explicit_anchor(self):
        (self.root / "reference.md").write_text('<div data-id="visual-review"></div>\n', encoding="utf-8")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Review](reference.md#visual-review)\n")
        self.assertTrue(validate_skill(self.root))

    def test_fenced_example_does_not_satisfy_anchor(self):
        original = self.entry.read_text(encoding="utf-8")
        for fence in ("```", "~~~~"):
            for anchor in ("fake", "example-id"):
                with self.subTest(fence=fence, anchor=anchor):
                    (self.root / "reference.md").write_text(
                        f'{fence}md\n# Fake\n<a id="example-id"></a>\n{fence}\n# Real\n', encoding="utf-8"
                    )
                    self.entry.write_text(original + f"\n[Review](reference.md#{anchor})\n", encoding="utf-8")
                    self.assertTrue(validate_skill(self.root))

    def test_heading_after_fenced_example_is_linkable(self):
        (self.root / "reference.md").write_text("```md\n# Example\n```\n## Actual Review\n", encoding="utf-8")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Review](reference.md#actual-review)\n")
        self.assertEqual(validate_skill(self.root), [])

    def test_formatted_and_duplicate_headings(self):
        (self.root / "reference.md").write_text("## **Review** `UI` & states ##\n## Repeat\n## Repeat\n", encoding="utf-8")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Review](reference.md#review-ui--states)\n[Repeat](reference.md#repeat-1)\n")
        self.assertEqual(validate_skill(self.root), [])

    def test_invalid_utf8_reference_returns_error(self):
        (self.root / "reference.md").write_bytes(b"\xff")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[Review](reference.md#review)\n")
        self.assertTrue(validate_skill(self.root))

    def test_non_markdown_fragment_does_not_require_heading(self):
        (self.root / "example.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write("\n[View](example.svg#view)\n")
        self.assertEqual(validate_skill(self.root), [])

    def test_maintained_skill_metadata_and_reference_routes(self):
        # Integration coverage for the shipped package, not assertions about its wording or taste.
        self.assertEqual(validate_skill(DEFAULT_SKILL), [])

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

    def test_external_downloaded_docs_are_not_skill_instructions(self):
        upstream = self.root / "assets/upstream/example"
        upstream.mkdir(parents=True)
        (upstream / "README.md").write_text("[Upstream-only link](missing-file.md)\n", encoding="utf-8")
        self.assertEqual(validate_skill(self.root), [])


if __name__ == "__main__":
    unittest.main()
