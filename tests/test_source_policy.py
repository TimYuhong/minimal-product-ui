import importlib.util
import contextlib
import copy
import hashlib
import io
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

    def test_inspect_git_prints_verified_tracked_file(self):
        output = io.StringIO()
        args = ["ui_sources.py", "inspect", "--source", self.source["id"], "--file", "button.tsx"]
        with patch.object(ui_sources, "load_sources", return_value=[self.source]), \
             patch.object(ui_sources, "source_path", return_value=self.repo), \
             patch.object(ui_sources.sys, "argv", args), contextlib.redirect_stdout(output):
            self.assertEqual(ui_sources.main(), 0)
        self.assertIn("export const Button", output.getvalue())

    def test_inspect_rejects_untracked_or_modified_source_before_printing(self):
        for changed in (False, True):
            with self.subTest(changed=changed):
                filename = "button.tsx" if changed else "untracked.tsx"
                (self.repo / filename).write_text("CANARY_UNVERIFIED_SOURCE\n", encoding="utf-8")
                output, errors = io.StringIO(), io.StringIO()
                args = ["ui_sources.py", "inspect", "--source", self.source["id"], "--file", filename]
                with patch.object(ui_sources, "load_sources", return_value=[self.source]), \
                     patch.object(ui_sources, "source_path", return_value=self.repo), \
                     patch.object(ui_sources.sys, "argv", args), \
                     contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    self.assertEqual(ui_sources.main(), 1)
                self.assertNotIn("CANARY_UNVERIFIED_SOURCE", output.getvalue())


class RegistrySourceTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix=".test-tmp-", dir=ROOT)
        self.addCleanup(self.scratch.cleanup)
        self.cache = Path(self.scratch.name)
        self.target = self.cache / "aceternity-ui"
        self.prefix = "snapshots/fixture"
        self.item = {
            "name": "sidebar", "type": "registry:ui", "dependencies": ["motion"],
            "registryDependencies": ["utils"],
            "files": [{"path": "components/ui/sidebar.tsx", "content": "export const Sidebar = () => null;\n"}],
        }
        item_body = json.dumps(self.item).encode()
        self.payloads = {
            "https://ui.aceternity.com/registry/sidebar.json": item_body,
            "https://ui.aceternity.com/licence": b"Fixture license evidence\n",
        }
        self.source = {
            "id": "aceternity-ui", "kind": "registry", "homepage": "https://ui.aceternity.com",
            "version": "registry-fixture", "artifacts": [
                {"url": url, "file": f"{self.prefix}/{relative}", "sha256": hashlib.sha256(self.payloads[url]).hexdigest(), **extra}
                for url, relative, extra in [
                    ("https://ui.aceternity.com/registry/sidebar.json", "registry/sidebar.json", {"extract": True}),
                    ("https://ui.aceternity.com/licence", "license/licence.html", {}),
                ]
            ],
            "required_files": [f"{self.prefix}/items/sidebar/components/ui/sidebar.tsx"],
            "license_files": [f"{self.prefix}/license/licence.html"],
        }

    def fetch(self):
        with patch.object(ui_sources, "download_registry", side_effect=self.payloads.__getitem__):
            ui_sources.fetch_source(self.source, self.cache)

    def manifest(self, source=None):
        path = self.cache / "manifest.json"
        path.write_text(json.dumps({"schema_version": 1, "sources": [source or self.source]}), encoding="utf-8")
        return path

    def test_manifest_admits_locked_official_registry(self):
        self.assertEqual(ui_sources.load_sources(self.manifest()), [self.source])

    def test_fetch_materializes_raw_json_source_and_license(self):
        self.fetch()
        ui_sources.verify_source(self.source, self.cache)
        source = self.target / self.source["required_files"][0]
        self.assertEqual(source.read_text(encoding="utf-8"), self.item["files"][0]["content"])
        self.assertEqual((self.target / self.source["artifacts"][0]["file"]).read_bytes(), self.payloads[self.source["artifacts"][0]["url"]])

    def test_complete_fetch_is_offline_and_preserves_existing_files(self):
        self.fetch()
        with patch.object(ui_sources, "download_registry", side_effect=AssertionError("Network not needed")):
            ui_sources.fetch_source(self.source, self.cache)

    def test_missing_extracted_file_is_rebuilt_from_locked_json_offline(self):
        self.fetch()
        file = self.target / self.source["required_files"][0]
        file.unlink()
        with patch.object(ui_sources, "download_registry", side_effect=AssertionError("Network not needed")):
            ui_sources.fetch_source(self.source, self.cache)
        self.assertEqual(file.read_text(encoding="utf-8"), self.item["files"][0]["content"])

    def test_changed_extracted_source_is_rejected_and_never_overwritten(self):
        self.fetch()
        changed = self.target / self.source["required_files"][0]
        changed.write_text("// User changes\n", encoding="utf-8")
        with self.assertRaises(ValueError): ui_sources.verify_source(self.source, self.cache)
        with self.assertRaises(ValueError): ui_sources.fetch_source(self.source, self.cache)
        self.assertEqual(changed.read_text(encoding="utf-8"), "// User changes\n")

    def test_remote_content_change_fails_without_relocking(self):
        path = self.manifest()
        original_lock = path.read_bytes()
        with patch.object(ui_sources, "download_registry", return_value=b"Upstream changed"):
            with self.assertRaises(ValueError): ui_sources.fetch_source(self.source, self.cache)
        self.assertEqual(path.read_bytes(), original_lock)
        self.assertFalse((self.target / self.source["artifacts"][0]["file"]).exists())

    def test_unknown_existing_directory_is_preserved(self):
        self.target.mkdir()
        user_file = self.target / "user.txt"
        user_file.write_text("Keep me", encoding="utf-8")
        with self.assertRaises(ValueError): self.fetch()
        self.assertEqual(user_file.read_text(encoding="utf-8"), "Keep me")

    def test_tampered_raw_json_and_license_fail_verification(self):
        self.fetch()
        for artifact in self.source["artifacts"]:
            file = self.target / artifact["file"]
            original = file.read_bytes()
            file.write_bytes(b"Changed")
            with self.assertRaises(ValueError): ui_sources.verify_source(self.source, self.cache)
            file.write_bytes(original)

    def test_component_bundle_rejects_traversal_duplicate_and_non_ui(self):
        artifact = self.source["artifacts"][0]
        for changes in [
            {"files": [{"path": "../outside.tsx", "content": "no"}]},
            {"files": self.item["files"] * 2}, {"files": ["invalid"]},
            {"files": [{"path": "components/ui/empty.tsx", "content": " "}]},
            {"type": "registry:block"}, {"name": "other"},
        ]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                ui_sources.registry_files(artifact, json.dumps({**self.item, **changes}).encode())

    def test_manifest_rejects_unapproved_urls_bad_hash_and_unlocked_license(self):
        for mutation in ["url", "sha256", "extract", "file", "license"]:
            source = copy.deepcopy(self.source)
            if mutation == "license": source["license_files"] = ["not-locked.html"]
            else: source["artifacts"][0][mutation] = {
                "url": "https://attacker.invalid/sidebar.json", "sha256": "bad", "extract": "yes", "file": "../outside.json",
            }[mutation]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                ui_sources.load_sources(self.manifest(source))

    def test_inspect_component_reads_verified_source_and_dependencies(self):
        self.fetch()
        output = io.StringIO()
        args = ["ui_sources.py", "inspect", "--source", "aceternity-ui", "--component", "sidebar"]
        with patch.object(ui_sources, "load_sources", return_value=[self.source]), \
             patch.object(ui_sources, "source_path", return_value=self.target), \
             patch.object(ui_sources.sys, "argv", args), contextlib.redirect_stdout(output):
            self.assertEqual(ui_sources.main(), 0)
        self.assertIn('"dependencies": ["motion"]', output.getvalue())
        self.assertIn("export const Sidebar", output.getvalue())

    def test_inspect_rejects_text_outside_registry_lock(self):
        self.fetch()
        untrusted = self.target / "untrusted.tsx"
        untrusted.write_text("CANARY_UNLOCKED_SOURCE", encoding="utf-8")
        output, errors = io.StringIO(), io.StringIO()
        args = ["ui_sources.py", "inspect", "--source", "aceternity-ui", "--file", "untrusted.tsx"]
        with patch.object(ui_sources, "load_sources", return_value=[self.source]), \
             patch.object(ui_sources, "source_path", return_value=self.target), \
             patch.object(ui_sources.sys, "argv", args), \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(ui_sources.main(), 1)
        self.assertNotIn("CANARY_UNLOCKED_SOURCE", output.getvalue())

    def test_explicit_refresh_captures_only_public_ui_and_keeps_previous_snapshot(self):
        self.fetch()
        manifest = self.manifest()
        urls = []
        index = {"name": "aceternity", "homepage": "https://ui.aceternity.com", "items": [
            {"name": "sidebar", "type": "registry:ui"},
            {"name": "paid-block", "type": "registry:block"},
        ]}
        payloads = {**self.payloads, "https://ui.aceternity.com/registry.json": json.dumps(index).encode(),
                    "https://ui.aceternity.com/terms": b"Fixture terms\n"}
        def downloaded(url): urls.append(url); return payloads[url]
        output = io.StringIO()
        with patch.object(ui_sources, "MANIFEST", manifest), \
             patch.object(ui_sources, "source_path", return_value=self.target), \
             patch.object(ui_sources, "download_registry", side_effect=downloaded), contextlib.redirect_stdout(output):
            ui_sources.refresh_aceternity()
        updated = ui_sources.load_sources(manifest)[0]
        self.assertEqual(updated["component_count"], 1)
        self.assertNotIn("https://ui.aceternity.com/registry/paid-block.json", urls)
        self.assertTrue((self.target / self.source["required_files"][0]).is_file())
        ui_sources.verify_source(updated, self.cache)

    def test_failed_refresh_does_not_replace_existing_lock(self):
        self.fetch()
        manifest = self.manifest()
        original_lock = manifest.read_bytes()
        with patch.object(ui_sources, "MANIFEST", manifest), \
             patch.object(ui_sources, "source_path", return_value=self.target), \
             patch.object(ui_sources, "download_registry", side_effect=OSError("Network unavailable")):
            with self.assertRaises(OSError): ui_sources.refresh_aceternity()
        self.assertEqual(manifest.read_bytes(), original_lock)
        ui_sources.verify_source(self.source, self.cache)


if __name__ == "__main__":
    unittest.main()
