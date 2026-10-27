"""Fetch or verify pinned upstream UI source; never install or execute upstream code."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

SKILL_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = SKILL_ROOT / "references" / "upstreams.json"
CACHE = SKILL_ROOT / "assets" / "upstream"


def safe_relative(value: str) -> bool:
    return (
        isinstance(value, str) and bool(value) and "\\" not in value and ":" not in value
        and not value.startswith("-") and not PurePosixPath(value).is_absolute()
        and ".." not in PurePosixPath(value).parts
    )


def load_sources(path: Path = MANIFEST) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("sources"), list) or not data["sources"]:
        raise ValueError("Invalid upstream manifest schema")
    seen: set[str] = set()
    for source in data["sources"]:
        if not isinstance(source, dict):
            raise ValueError("Each upstream source must be an object")
        name = source.get("id", "")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or name in seen:
            raise ValueError("Invalid or duplicate source identifier")
        seen.add(name)
        if source.get("kind", "git") == "registry":
            artifacts = source.get("artifacts")
            if source.get("homepage") != "https://ui.aceternity.com" or not isinstance(artifacts, list) or not artifacts:
                raise ValueError(f"Invalid registry source: {name}")
            paths = set()
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    raise ValueError(f"Invalid registry artifact: {name}")
                if not safe_relative(artifact.get("file", "")) or artifact["file"] in paths:
                    raise ValueError(f"Invalid registry artifact path: {name}")
                paths.add(artifact["file"])
                if not re.fullmatch(r"[0-9a-f]{64}", artifact.get("sha256", "")) or not official_registry_url(artifact.get("url", "")):
                    raise ValueError(f"Invalid registry artifact identity: {name}")
                if "extract" in artifact and type(artifact["extract"]) is not bool:
                    raise ValueError(f"Invalid registry extraction flag: {name}")
            for field in ("required_files", "license_files"):
                values = source.get(field)
                if not isinstance(values, list) or not values or not all(safe_relative(value) for value in values):
                    raise ValueError(f"Invalid registry {field}: {name}")
            if not set(source["license_files"]).issubset(paths):
                raise ValueError(f"Registry license evidence must have locked artifacts: {name}")
            continue
        if source.get("kind", "git") != "git":
            raise ValueError(f"Unknown source kind: {name}")
        if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", source.get("repository", "")):
            raise ValueError(f"Source {name} must use a public HTTPS GitHub repository URL")
        if not re.fullmatch(r"[0-9a-f]{40}", source.get("commit", "")):
            raise ValueError(f"Source {name} must pin a full commit SHA")
        ref = source.get("ref", "")
        if not isinstance(ref, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", ref):
            raise ValueError(f"Invalid source ref: {name}")
        for field in ("sparse_paths", "required_files", "license_files"):
            values = source.get(field)
            if not isinstance(values, list) or not values or not all(safe_relative(value) for value in values):
                raise ValueError(f"Unsafe or missing {field}: {name}")
    return data["sources"]


def git(directory: Path, *args: str, capture: bool = False) -> str:
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args], cwd=directory,
        check=True, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def source_path(source: dict, cache: Path = CACHE) -> Path:
    base = cache.resolve()
    target = (base / source["id"]).resolve()
    if not target.is_relative_to(base) or target == base:
        raise ValueError("Source path escapes the managed source cache")
    return target


def check_identity(source: dict, target: Path) -> None:
    if not (target / ".git").exists():
        raise ValueError(f"{source['id']}: missing Git checkout; run fetch")
    if Path(git(target, "rev-parse", "--show-toplevel", capture=True)).resolve() != target.resolve():
        raise ValueError(f"{source['id']}: unexpected checkout root")
    if git(target, "remote", "get-url", "origin", capture=True) != source["repository"]:
        raise ValueError(f"{source['id']}: origin differs from the manifest")
    if git(target, "status", "--porcelain", capture=True):
        raise ValueError(f"{source['id']}: checkout has local changes; preserve them before fetching")


def verify_source(source: dict, cache: Path = CACHE) -> None:
    target = source_path(source, cache)
    if source.get("kind") == "registry":
        verify_registry(source, target)
        return
    check_identity(source, target)
    if git(target, "rev-parse", "HEAD", capture=True) != source["commit"]:
        raise ValueError(f"{source['id']}: HEAD differs from the pinned commit; run fetch")
    for relative in source["required_files"] + source["license_files"]:
        file = (target / relative).resolve()
        if not file.is_relative_to(target) or not file.is_file() or file.stat().st_size == 0:
            raise ValueError(f"{source['id']}: required source or license file is missing: {relative}")


def fetch_source(source: dict, cache: Path = CACHE) -> None:
    if source.get("kind") == "registry":
        fetch_registry(source, cache)
        return
    target = source_path(source, cache)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        # A complete, clean pinned source needs no network access on repeat fetch.
        # Unknown or dirty targets are never reset or overwritten.
        check_identity(source, target)
        try:
            verify_source(source, cache)
        except ValueError:
            pass
        else:
            return
    if not target.exists():
        git(target.parent, "clone", "--filter=blob:none", "--no-checkout", "--depth=1", "--branch", source["ref"], "--", source["repository"], source["id"])
    # A partial clone reads only the chosen source paths. It does not run package scripts.
    git(target, "fetch", "--filter=blob:none", "--depth=1", "origin", source["commit"])
    git(target, "sparse-checkout", "set", "--cone", "--", *source["sparse_paths"])
    git(target, "checkout", "--detach", source["commit"])
    verify_source(source, cache)


def official_registry_url(value: str) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return parsed.scheme == "https" and parsed.hostname == "ui.aceternity.com" and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment and parsed.port in (None, 443) and (
        parsed.path in {"/registry.json", "/licence", "/terms"} or re.fullmatch(r"/registry/[a-z0-9-]+\.json", parsed.path) is not None)


def download_registry(url: str) -> bytes:
    if not official_registry_url(url):
        raise ValueError("Registry URL is not an approved official source")
    request = Request(url, headers={"User-Agent": "minimal-product-ui-source-verifier/1.0"})
    with urlopen(request, timeout=30) as response:
        if not official_registry_url(response.url):
            raise ValueError("Registry redirected away from its approved source")
        body = response.read(8 * 1024 * 1024 + 1)
    if not body or len(body) > 8 * 1024 * 1024:
        raise ValueError("Empty or oversized registry artifact")
    return body


def cache_file(target: Path, relative: str) -> Path:
    if not safe_relative(relative):
        raise ValueError("Unsafe cached source path")
    file = (target / relative).resolve()
    if not file.is_relative_to(target.resolve()):
        raise ValueError("Cached source path escapes its source checkout")
    return file


def registry_identity(source: dict, target: Path, create: bool = False) -> None:
    marker = target / "SOURCE.json"
    expected = {"id": source["id"], "homepage": "https://ui.aceternity.com", "kind": "registry"}
    if not target.exists() and create:
        target.mkdir(parents=True)
        marker.write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")) != expected:
        raise ValueError("Registry cache identity differs; preserve the existing directory")


def registry_files(artifact: dict, body: bytes) -> dict[str, bytes]:
    if not artifact.get("extract"):
        return {}
    item = json.loads(body)
    name = Path(artifact["file"]).stem
    if not isinstance(item, dict) or item.get("name") != name or item.get("type") != "registry:ui" or not isinstance(item.get("files"), list) or not item["files"]:
        raise ValueError(f"Invalid registry component bundle: {name}")
    base = Path(artifact["file"]).parent.parent / "items" / name
    files = {}
    for entry in item["files"]:
        if not isinstance(entry, dict) or not safe_relative(entry.get("path", "")) or not isinstance(entry.get("content"), str) or not entry["content"].strip():
            raise ValueError(f"Registry component lacks valid source: {name}")
        relative = (base / entry["path"]).as_posix()
        if relative in files:
            raise ValueError(f"Duplicate registry component path: {name}")
        files[relative] = entry["content"].encode("utf-8")
    return files


def verify_registry(source: dict, target: Path) -> None:
    registry_identity(source, target)
    for artifact in source["artifacts"]:
        file = cache_file(target, artifact["file"])
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != artifact["sha256"]:
            raise ValueError(f"{source['id']}: missing or changed registry artifact: {artifact['file']}")
        for relative, expected in registry_files(artifact, file.read_bytes()).items():
            extracted = cache_file(target, relative)
            if not extracted.is_file() or extracted.read_bytes() != expected:
                raise ValueError(f"{source['id']}: missing or changed extracted source: {relative}")
    for relative in source["required_files"] + source["license_files"]:
        file = cache_file(target, relative)
        if not file.is_file() or not file.stat().st_size:
            raise ValueError(f"{source['id']}: required source/license evidence missing: {relative}")


def write_new_or_equal(file: Path, body: bytes) -> None:
    if file.exists():
        if not file.is_file() or file.read_bytes() != body:
            raise ValueError("Cached source has changes; it was not overwritten")
        return
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(body)


def fetch_registry(source: dict, cache: Path = CACHE) -> None:
    target = source_path(source, cache)
    registry_identity(source, target, create=True)
    for artifact in source["artifacts"]:
        file = cache_file(target, artifact["file"])
        body = file.read_bytes() if file.is_file() else download_registry(artifact["url"])
        if hashlib.sha256(body).hexdigest() != artifact["sha256"]:
            raise ValueError(f"{source['id']}: registry content no longer matches its lock; explicit maintenance is required")
        write_new_or_equal(file, body)
        for relative, content in registry_files(artifact, body).items():
            write_new_or_equal(cache_file(target, relative), content)
    verify_registry(source, target)


def refresh_aceternity() -> None:
    """Explicit maintainer operation: capture public UI items, never paid blocks/templates."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    previous = next((s for s in data["sources"] if s["id"] == "aceternity-ui"), None)
    if previous:
        verify_source(previous)
    source = {"id": "aceternity-ui", "kind": "registry", "homepage": "https://ui.aceternity.com"}
    target = source_path(source)
    registry_identity(source, target, create=True)
    index = download_registry("https://ui.aceternity.com/registry.json")
    registry = json.loads(index)
    if registry.get("name") != "aceternity" or registry.get("homepage") != source["homepage"]:
        raise ValueError("Unexpected official registry identity")
    names = sorted({item["name"] for item in registry["items"] if item.get("type") == "registry:ui"})
    if not names or not all(re.fullmatch(r"[a-z0-9-]+", name) for name in names):
        raise ValueError("Invalid official registry component names")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prefix = f"snapshots/{stamp}-{hashlib.sha256(index).hexdigest()[:12]}"
    artifacts = []
    def capture(url, relative, body=None, extract=False):
        body = download_registry(url) if body is None else body
        artifact = {"url": url, "file": f"{prefix}/{relative}", "sha256": hashlib.sha256(body).hexdigest()}
        if extract:
            artifact["extract"] = True
        extracted = registry_files(artifact, body)
        write_new_or_equal(cache_file(target, artifact["file"]), body)
        for path, content in extracted.items():
            write_new_or_equal(cache_file(target, path), content)
        return artifact
    artifacts.append(capture("https://ui.aceternity.com/registry.json", "registry/index.json", index))
    for slug in ("licence", "terms"):
        artifacts.append(capture(f"https://ui.aceternity.com/{slug}", f"license/{slug}.html"))
    def component(name):
        return capture(f"https://ui.aceternity.com/registry/{name}.json", f"registry/{name}.json", extract=True)
    with ThreadPoolExecutor(max_workers=6) as executor:
        for number, artifact in enumerate(executor.map(component, names), 1):
            artifacts.append(artifact)
            if number % 10 == 0 or number == len(names):
                print(f"Captured Aceternity UI source {number}/{len(names)}", flush=True)
    source.update({"version": f"registry-{stamp}", "component_count": len(names), "artifacts": artifacts,
        "required_files": [path for artifact in artifacts if artifact.get("extract") for path in registry_files(artifact, cache_file(target, artifact["file"]).read_bytes())],
        "license_files": [f"{prefix}/license/licence.html", f"{prefix}/license/terms.html"]})
    verify_registry(source, target)
    data["sources"] = [s for s in data["sources"] if s["id"] != source["id"]] + [source]
    data["verified_on"] = datetime.now(timezone.utc).date().isoformat()
    # Generated lock data, refreshed only through this explicit maintainer command.
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: aceternity-ui {source['version']} ({len(names)} public UI items)", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("fetch", "verify", "refresh-registry", "inspect"))
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--source", action="append", help="Select a named manifest source; repeatable")
    selection.add_argument("--all", action="store_true", help="Explicitly select all sources for fetch or verify")
    parser.add_argument("--file", help="Source-relative text file to inspect after verification")
    parser.add_argument("--component", help="Official registry component name to inspect after verification")
    args = parser.parse_args()
    if args.all and args.operation not in ("fetch", "verify"):
        parser.error("--all is only supported for fetch or verify")
    try:
        if args.operation == "refresh-registry":
            if args.source != ["aceternity-ui"]:
                raise ValueError("Explicit registry maintenance requires --source aceternity-ui")
            refresh_aceternity()
            return 0
        sources = load_sources()
        selected = {source["id"] for source in sources} if args.all else set(args.source)
        if selected - {source["id"] for source in sources}:
            raise ValueError("Unknown source identifier")
        if args.operation == "inspect" and (len(selected) != 1 or bool(args.file) == bool(args.component)):
            raise ValueError("Inspect requires one --source and either --file or --component")
        for source in sources:
            if source["id"] in selected:
                if args.operation == "fetch":
                    fetch_source(source)
                else:
                    verify_source(source)
                identity = source.get("commit", source.get("version"))
                print(f"PASS: {source['id']} {identity}", flush=True)
                if args.operation == "inspect":
                    if args.component:
                        artifact = next((item for item in source.get("artifacts", []) if item.get("extract") and Path(item["file"]).stem == args.component), None)
                        if artifact is None:
                            raise ValueError("Component is not in the locked official registry")
                        body = cache_file(source_path(source), artifact["file"]).read_bytes()
                        item = json.loads(body)
                        print("DEPENDENCIES: " + json.dumps({key: item.get(key, []) for key in ("dependencies", "registryDependencies")}, ensure_ascii=False))
                        for relative, content in registry_files(artifact, body).items():
                            print(f"SOURCE: {source['id']} / {relative}\n" + content.decode("utf-8"))
                        continue
                    file = cache_file(source_path(source), args.file)
                    if ".git" in Path(args.file).parts or not file.is_file() or file.stat().st_size > 1024 * 1024:
                        raise ValueError("Inspect requires an existing source text file up to 1 MiB")
                    if source.get("kind", "git") == "git":
                        git(source_path(source), "ls-files", "--error-unmatch", "--", args.file, capture=True)
                    elif args.file not in source["required_files"] + source["license_files"] + [item["file"] for item in source["artifacts"]]:
                        raise ValueError("File is not part of the locked registry source")
                    print(f"SOURCE: {source['id']} / {args.file}\n" + file.read_text(encoding="utf-8"))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        message = str(error) if isinstance(error, ValueError) else "Git or filesystem operation failed; source verification did not pass"
        print(f"FAIL: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
