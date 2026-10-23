"""Fetch or verify pinned upstream UI source; never install or execute upstream code."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

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
        name = source.get("id", "")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or name in seen:
            raise ValueError("Invalid or duplicate source identifier")
        seen.add(name)
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
    check_identity(source, target)
    if git(target, "rev-parse", "HEAD", capture=True) != source["commit"]:
        raise ValueError(f"{source['id']}: HEAD differs from the pinned commit; run fetch")
    for relative in source["required_files"] + source["license_files"]:
        file = (target / relative).resolve()
        if not file.is_relative_to(target) or not file.is_file() or file.stat().st_size == 0:
            raise ValueError(f"{source['id']}: required source or license file is missing: {relative}")


def fetch_source(source: dict, cache: Path = CACHE) -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("fetch", "verify"))
    parser.add_argument("--source", action="append", help="Limit to a named manifest source; repeatable")
    args = parser.parse_args()
    try:
        sources = load_sources()
        selected = set(args.source or (source["id"] for source in sources))
        if selected - {source["id"] for source in sources}:
            raise ValueError("Unknown source identifier")
        for source in sources:
            if source["id"] in selected:
                if args.operation == "fetch":
                    fetch_source(source)
                else:
                    verify_source(source)
                print(f"PASS: {source['id']} {source['commit']}", flush=True)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        message = str(error) if isinstance(error, ValueError) else "Git or filesystem operation failed; source verification did not pass"
        print(f"FAIL: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
