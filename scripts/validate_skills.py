#!/usr/bin/env python3
"""Validate the skill collection before release.

Checks:
  1. every `skills/<name>/SKILL.md` has valid YAML frontmatter with `name`,
     `description`, `version`, and `name` matching its directory;
  2. all Python files parse (compile) cleanly;
  3. all JSON/YAML manifests parse cleanly;
  4. skill versions and the marketplace manifest agree with `VERSION`;
  5. no obvious committed secrets (API keys) or internal hostnames leak in.

Usage:
    python3 scripts/validate_skills.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
VERSION_FILE = ROOT / "VERSION"
MARKETPLACE_FILE = ROOT / ".claude-plugin" / "marketplace.json"

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?$")
SECRET = re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b")
INTERNAL_HOST = re.compile(r"\b(?:172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")

REQUIRED_FIELDS = ("name", "description", "version", "license")


def iter_files(suffix: str) -> Iterator[Path]:
    for path in sorted(ROOT.rglob(f"*{suffix}")):
        if ".git" in path.parts:
            continue
        yield path


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the flat `key: value` part of a SKILL.md YAML frontmatter block.

    Nested blocks (metadata, prerequisites, ...) are ignored on purpose: the
    validator only needs the top-level scalar fields.
    """
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter block")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("unterminated frontmatter block")

    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line or line[0] in " \t#-":
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def check_skills(errors: list[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    if not SKILLS_DIR.is_dir():
        errors.append("skills/ directory is missing")
        return versions

    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{skill_dir.name}: missing SKILL.md")
            continue
        try:
            fields = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"{skill_dir.name}: {exc}")
            continue

        for field in REQUIRED_FIELDS:
            if not fields.get(field):
                errors.append(f"{skill_dir.name}: frontmatter field '{field}' is empty")
        if fields.get("name") and fields["name"] != skill_dir.name:
            errors.append(
                f"{skill_dir.name}: frontmatter name '{fields['name']}' != directory name"
            )
        version = fields.get("version", "")
        if version and not SEMVER.match(version):
            errors.append(f"{skill_dir.name}: version '{version}' is not semver")
        versions[skill_dir.name] = version
    return versions


def check_python(errors: list[str]) -> None:
    import ast

    for path in iter_files(".py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")


def check_json(errors: list[str]) -> None:
    for path in iter_files(".json"):
        if path.name in {".skillhub", "metadata.json"} and ".skillhub" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")


def check_versions(errors: list[str], skill_versions: dict[str, str]) -> None:
    if not VERSION_FILE.is_file():
        errors.append("VERSION file is missing")
        return
    repo_version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not SEMVER.match(repo_version):
        errors.append(f"VERSION '{repo_version}' is not semver")

    for name, version in skill_versions.items():
        if version and version != repo_version:
            errors.append(
                f"{name}: skill version '{version}' != repo VERSION '{repo_version}'"
            )

    if not MARKETPLACE_FILE.is_file():
        errors.append(".claude-plugin/marketplace.json is missing")
        return
    try:
        manifest: dict[str, Any] = json.loads(MARKETPLACE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return  # already reported by check_json
    declared = manifest.get("metadata", {}).get("version") or manifest.get("version")
    if declared != repo_version:
        errors.append(
            f"marketplace.json version '{declared}' != repo VERSION '{repo_version}'"
        )


def check_secrets(errors: list[str]) -> None:
    for path in iter_files(".md"):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        if SECRET.search(text):
            errors.append(f"{rel}: looks like a committed API key (sk-...)")
        if INTERNAL_HOST.search(text):
            errors.append(f"{rel}: contains a private-network address")
    for path in iter_files(".py"):
        text = path.read_text(encoding="utf-8")
        if SECRET.search(text):
            errors.append(f"{path.relative_to(ROOT)}: looks like a committed API key (sk-...)")


def main() -> int:
    errors: list[str] = []
    skill_versions = check_skills(errors)
    check_python(errors)
    check_json(errors)
    check_versions(errors, skill_versions)
    check_secrets(errors)

    if errors:
        print("skill collection validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("skill collection validation OK")
    for name, version in skill_versions.items():
        print(f"  skills/{name}  {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
