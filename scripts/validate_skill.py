"""Validate the portable skill package without a Codex installation or network."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

import yaml


DEFAULT_SKILL = Path(__file__).resolve().parents[1] / "skills" / "minimal-product-ui"


def validate_skill(directory: Path) -> list[str]:
    root = directory.resolve()
    errors: list[str] = []
    entry = root / "SKILL.md"
    if not entry.is_file():
        return ["SKILL.md is missing"]
    try:
        text = entry.read_text(encoding="utf-8")
    except UnicodeError:
        return ["SKILL.md must be UTF-8"]
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not match:
        return ["SKILL.md YAML frontmatter is missing or malformed"]
    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return ["SKILL.md frontmatter is not valid YAML"]
    if not isinstance(frontmatter, dict):
        return ["SKILL.md frontmatter must be a mapping"]
    name = frontmatter.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        errors.append("Skill name must be lowercase hyphen-case and at most 64 characters")
    elif name != root.name:
        errors.append("Skill folder and frontmatter name must match")
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        errors.append("Description must be non-empty text of at most 1024 characters")

    for document in sorted(root.rglob("*.md")):
        try:
            content = document.read_text(encoding="utf-8")
        except UnicodeError:
            errors.append(f"{document.relative_to(root)} must be UTF-8")
            continue
        if re.search(r"^\s*\[TODO:[^\n]*\]\s*$", content, re.M):
            errors.append(f"Unfinished scaffold in {document.relative_to(root)}")
        for target in re.findall(r"\]\(([^)\n]+)\)", content):
            target = target.strip().removeprefix("<").removesuffix(">")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (document.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root) or not destination.is_file():
                errors.append(f"Broken or out-of-package link in {document.relative_to(root)}: {target}")

    metadata = root / "agents" / "openai.yaml"
    if metadata.is_file():
        try:
            data = yaml.safe_load(metadata.read_text(encoding="utf-8"))
            interface = data.get("interface") if isinstance(data, dict) else None
            if not isinstance(interface, dict):
                raise ValueError()
            title = interface.get("display_name")
            summary = interface.get("short_description")
            prompt = interface.get("default_prompt")
            if not isinstance(title, str) or not title.strip():
                errors.append("UI display_name must be non-empty")
            if not isinstance(summary, str) or not 25 <= len(summary) <= 64:
                errors.append("UI short_description must contain 25 to 64 characters")
            if not isinstance(name, str) or not isinstance(prompt, str) or f"${name}" not in prompt:
                errors.append("UI default_prompt must mention the skill invocation")
        except (UnicodeError, yaml.YAMLError, ValueError):
            errors.append("agents/openai.yaml must contain valid interface metadata")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=DEFAULT_SKILL)
    args = parser.parse_args()
    errors = validate_skill(args.directory)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: skill frontmatter, local references and UI metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
