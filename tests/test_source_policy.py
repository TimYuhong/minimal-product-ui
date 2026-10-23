import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.validate_repository import portability_errors

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ui_sources", ROOT / "skills/minimal-product-ui/scripts/ui_sources.py")
ui_sources = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ui_sources)


class PublicPortabilityTests(unittest.TestCase):
    def test_rejects_windows_absolute_path(self):
        path = "Q:" + "\\private-project\\checkout"
        self.assertTrue(portability_errors(path))

    def test_rejects_personal_posix_path(self):
        path = "/home" + "/example-person/private-checkout/file"
        self.assertTrue(portability_errors(path))

    def test_allows_relative_paths_and_environment_variables(self):
        self.assertEqual(portability_errors("skills/minimal-product-ui\n$env:CODEX_HOME\n${CODEX_HOME:-$HOME/.codex}/skills"), [])


class UpstreamSourceTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix=".test-tmp-", dir=ROOT)
        self.addCleanup(self.scratch.cleanup)
        self.cache = Path(self.scratch.name)
        self.repo = self.cache / "example-ui"
        self.repo.mkdir()
        self.run_git("init", "-q")
        self.run_git("config", "user.name", "Source verification test")
        self.run_git("config", "user.email", "test@example.invalid")
        self.run_git("config", "core.autocrlf", "false")
        self.run_git("remote", "add", "origin", "https://github.com/example/example-ui.git")
        (self.repo / "button.tsx").write_text("export const Button = () => null;\n", encoding="utf-8")
        (self.repo / "LICENSE").write_text("Example fixture license\n", encoding="utf-8")
        self.run_git("add", "--", "button.tsx", "LICENSE")
        self.run_git("-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "test fixture")
        self.source = {
            "id": "example-ui", "repository": "https://github.com/example/example-ui.git",
            "ref": "main", "commit": self.run_git("rev-parse", "HEAD"),
            "sparse_paths": ["src"], "required_files": ["button.tsx"], "license_files": ["LICENSE"],
        }

    def run_git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()

    def test_accepts_clean_pinned_source(self):
        ui_sources.verify_source(self.source, self.cache)

    def test_repeated_fetch_keeps_verified_checkout_and_avoids_network(self):
        original_git = ui_sources.git
        operations = []
        def inspected_git(directory, *args, capture=False):
            operations.append(args[0])
            return original_git(directory, *args, capture=capture)
        with patch.object(ui_sources, "git", side_effect=inspected_git):
            ui_sources.fetch_source(self.source, self.cache)
        self.assertNotIn("fetch", operations)
        self.assertNotIn("clone", operations)
        self.assertNotIn("checkout", operations)

    def test_rejects_changed_source_without_resetting_it(self):
        changed = "// user changes\n"
        (self.repo / "button.tsx").write_text(changed, encoding="utf-8")
        with self.assertRaises(ValueError):
            ui_sources.verify_source(self.source, self.cache)
        self.assertEqual((self.repo / "button.tsx").read_text(encoding="utf-8"), changed)

    def test_rejects_wrong_remote(self):
        self.run_git("remote", "set-url", "origin", "https://github.com/another/example.git")
        with self.assertRaises(ValueError):
            ui_sources.verify_source(self.source, self.cache)

    def test_rejects_wrong_commit(self):
        with self.assertRaises(ValueError):
            ui_sources.verify_source({**self.source, "commit": "0" * 40}, self.cache)

    def test_rejects_missing_license(self):
        with self.assertRaises(ValueError):
            ui_sources.verify_source({**self.source, "license_files": ["missing-license"]}, self.cache)

    def test_rejects_manifest_path_traversal(self):
        manifest = self.cache / "manifest.json"
        self.source["sparse_paths"] = ["../outside"]
        manifest.write_text(json.dumps({"schema_version": 1, "sources": [self.source]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            ui_sources.load_sources(manifest)


if __name__ == "__main__":
    unittest.main()
