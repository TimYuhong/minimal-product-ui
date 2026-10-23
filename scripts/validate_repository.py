"""Check public text portability and pinned source records without scanning ignored downloads."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".ps1", ".toml"}
PERSONAL_PATH = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/])|/(?:Users|home)/[^\s/]+/|\\\\[A-Za-z0-9_-]+\\[A-Za-z0-9_$-]+\\")


def portability_errors(content: str) -> list[str]:
    return [f"line {number}: machine-specific absolute path" for number, line in enumerate(content.splitlines(), 1) if PERSONAL_PATH.search(line)]


def validate_repository(root: Path = ROOT) -> list[str]:
    output = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root, check=True, stdout=subprocess.PIPE).stdout
    errors: list[str] = []
    for name in sorted(set(output.decode("utf-8").split("\0")) - {""}):
        file = root / name
        if file.is_file() and file.suffix.lower() in TEXT_SUFFIXES:
            try:
                errors.extend(f"{name}: {error}" for error in portability_errors(file.read_text(encoding="utf-8")))
            except UnicodeError:
                errors.append(f"{name}: public text must be UTF-8")
    helper_path = root / "skills" / "minimal-product-ui" / "scripts" / "ui_sources.py"
    spec = importlib.util.spec_from_file_location("ui_sources_validator", helper_path)
    if spec is None or spec.loader is None:
        return errors + ["Source verification helper is missing"]
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    try:
        helper.load_sources()
    except (ValueError, OSError) as error:
        errors.append(f"Invalid source manifest: {error}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        errors = validate_repository()
    except (OSError, subprocess.CalledProcessError):
        print("FAIL: repository file inventory unavailable")
        return 1
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: public text portability and source lock records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
