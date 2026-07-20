#!/usr/bin/env python3
"""Validate this repository's Agent Skill package."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def frontmatter_value(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", frontmatter)
    return unquote(match.group(1)) if match else None


def validate(skill_dir: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"Missing {skill_md}"]

    content = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return ["SKILL.md must begin with valid YAML frontmatter delimiters"]

    frontmatter = match.group(1)
    name = frontmatter_value(frontmatter, "name")
    description = frontmatter_value(frontmatter, "description")
    version = frontmatter_value(frontmatter, "version")

    if not name:
        errors.append("Frontmatter is missing name")
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append(f"Invalid skill name: {name}")
    elif len(name) > 64:
        errors.append("Skill name exceeds 64 characters")
    elif skill_dir.name != name:
        errors.append(f"Skill folder {skill_dir.name!r} does not match name {name!r}")

    if not description:
        errors.append("Frontmatter is missing description")
    elif len(description) > 1024:
        errors.append("Description exceeds 1024 characters")

    if len(content.splitlines()) > 500:
        errors.append("SKILL.md exceeds 500 lines")

    referenced = set(
        re.findall(
            r"(?<![A-Za-z0-9_])((?:references|scripts|assets|evals)/[A-Za-z0-9_.\-/]+)",
            content,
        )
    )
    for relative in sorted(referenced):
        if not (skill_dir / relative).exists():
            errors.append(f"Missing referenced file: {relative}")

    reference_files = {p.relative_to(skill_dir).as_posix() for p in (skill_dir / "references").glob("*.md")}
    missing_routes = sorted(reference_files - referenced)
    for relative in missing_routes:
        errors.append(f"Reference is not routed from SKILL.md: {relative}")

    evals_path = skill_dir / "evals" / "evals.json"
    queries_path = skill_dir / "evals" / "eval_queries.json"
    try:
        evals = json.loads(evals_path.read_text(encoding="utf-8"))
        if evals.get("skill_name") != name:
            errors.append("evals/evals.json skill_name does not match frontmatter name")
        if len(evals.get("evals", [])) < 3:
            errors.append("evals/evals.json must contain at least 3 cases")
        for case in evals.get("evals", []):
            if not case.get("prompt") or not case.get("expected_output") or not case.get("assertions"):
                errors.append(f"Incomplete output eval case: {case.get('id')}")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid evals/evals.json: {exc}")

    try:
        queries = json.loads(queries_path.read_text(encoding="utf-8"))
        positives = sum(item.get("should_trigger") is True for item in queries)
        negatives = sum(item.get("should_trigger") is False for item in queries)
        if positives < 8 or negatives < 8:
            errors.append("eval_queries.json needs at least 8 positive and 8 negative cases")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid evals/eval_queries.json: {exc}")

    cff = repo_root / "CITATION.cff"
    readme = repo_root / "README.md"
    if version:
        if cff.is_file() and f'version: "{version}"' not in cff.read_text(encoding="utf-8"):
            errors.append("CITATION.cff version does not match SKILL.md metadata version")
        if readme.is_file() and version not in readme.read_text(encoding="utf-8"):
            errors.append("README.md does not mention the current skill version")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    skill_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else repo_root / "scientific-autoresearch"
    errors = validate(skill_dir, repo_root)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
