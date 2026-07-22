#!/usr/bin/env python3
"""Check this repository's Agent Skill package for internal consistency."""

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
    match = re.search(rf"(?m)^[ \t]*{re.escape(key)}:\s*(.+?)\s*$", frontmatter)
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

    if not version:
        errors.append("Frontmatter is missing metadata version")
    elif not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        errors.append(f"Invalid skill release version: {version}")

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
        if evals.get("evaluation_kind") != "behavioral_specification":
            errors.append("evals/evals.json must identify itself as a behavioral specification")
        if evals.get("contains_scored_results") is not False:
            errors.append("evals/evals.json must not claim to contain scored results")
        if len(evals.get("evals", [])) < 3:
            errors.append("evals/evals.json must contain at least 3 cases")
        ids = [case.get("id") for case in evals.get("evals", [])]
        if len(ids) != len(set(ids)):
            errors.append("evals/evals.json case IDs must be unique")
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

    benchmark_root = repo_root / "benchmarks"
    benchmark_manifest_path = benchmark_root / "manifest.json"
    benchmark_scorer_path = benchmark_root / "score.py"
    if not benchmark_scorer_path.is_file():
        errors.append("Missing repository benchmark scorer: benchmarks/score.py")
    try:
        benchmark_manifest = json.loads(
            benchmark_manifest_path.read_text(encoding="utf-8")
        )
        if benchmark_manifest.get("release_under_test") != version:
            errors.append("benchmarks/manifest.json release does not match SKILL.md")
        if benchmark_manifest.get("benchmark_status") != "specification_only":
            errors.append(
                "Benchmark manifest must remain specification_only until scored results are published"
            )
        suites = benchmark_manifest.get("suites")
        if not isinstance(suites, list) or len(suites) < 3:
            errors.append("benchmarks/manifest.json must define the evidence suites")
        else:
            suite_ids = [suite.get("suite_id") for suite in suites if isinstance(suite, dict)]
            if len(suite_ids) != len(suites) or len(suite_ids) != len(set(suite_ids)):
                errors.append("Benchmark suite IDs must be present and unique")
            for suite in suites:
                if not isinstance(suite, dict):
                    continue
                for field in (
                    "suite_id",
                    "evidence_type",
                    "target",
                    "metrics",
                    "execution_status",
                ):
                    if suite.get(field) in (None, "", []):
                        errors.append(
                            f"Benchmark suite {suite.get('suite_id')!r} is missing {field}"
                        )
                source = suite.get("case_source")
                if source and not (repo_root / str(source)).is_file():
                    errors.append(
                        f"Benchmark suite {suite.get('suite_id')!r} references missing {source}"
                    )
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid benchmarks/manifest.json: {exc}")

    if version:
        benchmark_result_path = benchmark_root / "results" / f"v{version}.json"
        try:
            benchmark_result = json.loads(
                benchmark_result_path.read_text(encoding="utf-8")
            )
            if benchmark_result.get("skill_release") != version:
                errors.append("Current benchmark result release does not match SKILL.md")
            if benchmark_result.get("status") == "not_evaluated":
                for field in (
                    "scored_behavioral_runs",
                    "scored_trigger_runs",
                    "empirical_method_runs",
                ):
                    if benchmark_result.get(field) != 0:
                        errors.append(
                            f"Unevaluated benchmark result must keep {field}=0"
                        )
                if benchmark_result.get("summary") is not None:
                    errors.append("Unevaluated benchmark result must keep summary=null")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid current benchmark result: {exc}")

    cff = repo_root / "CITATION.cff"
    bib = repo_root / "CITATION.bib"
    readme = repo_root / "README.md"
    changelog = repo_root / "CHANGELOG.md"
    if version:
        release_tag = f"/releases/tag/v{version}"
        release_dates: dict[str, str] = {}

        if not cff.is_file():
            errors.append("Missing CITATION.cff")
        else:
            cff_text = cff.read_text(encoding="utf-8")
            cff_match = re.search(r'(?m)^version:\s*["\']?([^"\'\s]+)', cff_text)
            if not cff_match or cff_match.group(1) != version:
                errors.append("CITATION.cff version does not match SKILL.md metadata version")
            if release_tag not in cff_text:
                errors.append("CITATION.cff release URL does not match the current version")
            cff_date_match = re.search(
                r'(?m)^date-released:\s*["\']?(\d{4}-\d{2}-\d{2})', cff_text
            )
            if cff_date_match:
                release_dates["CITATION.cff"] = cff_date_match.group(1)

        if not bib.is_file():
            errors.append("Missing CITATION.bib")
        else:
            bib_text = bib.read_text(encoding="utf-8")
            bib_match = re.search(r"(?m)^\s*version\s*=\s*\{v?([^}]+)\}", bib_text)
            if not bib_match or bib_match.group(1) != version:
                errors.append("CITATION.bib version does not match SKILL.md metadata version")
            if release_tag not in bib_text:
                errors.append("CITATION.bib release URL does not match the current version")
            bib_date_match = re.search(
                r"(?m)^\s*date\s*=\s*\{(\d{4}-\d{2}-\d{2})\}", bib_text
            )
            if bib_date_match:
                release_dates["CITATION.bib"] = bib_date_match.group(1)

        if not readme.is_file():
            errors.append("Missing README.md")
        else:
            readme_text = readme.read_text(encoding="utf-8")
            if f"Current version: **{version}**." not in readme_text:
                errors.append("README.md current-version declaration does not match SKILL.md")
            if f"## Version {version} Highlights" not in readme_text:
                errors.append("README.md highlights heading does not match the current version")

        if not changelog.is_file():
            errors.append("Missing CHANGELOG.md")
        else:
            changelog_text = changelog.read_text(encoding="utf-8")
            release_match = re.search(r"(?m)^##\s+([0-9]+\.[0-9]+\.[0-9]+)\s+-", changelog_text)
            if not release_match or release_match.group(1) != version:
                errors.append("Latest CHANGELOG.md release does not match SKILL.md metadata version")
            changelog_date_match = re.search(
                rf"(?m)^##\s+{re.escape(version)}\s+-\s+(\d{{4}}-\d{{2}}-\d{{2}})\s*$",
                changelog_text,
            )
            if changelog_date_match:
                release_dates["CHANGELOG.md"] = changelog_date_match.group(1)

        if len(set(release_dates.values())) > 1:
            details = ", ".join(
                f"{source}={date}" for source, date in sorted(release_dates.items())
            )
            errors.append(f"Current release dates are inconsistent: {details}")

        figures = repo_root / "figures"
        for suffix in ("pdf", "png", "svg"):
            figure_name = f"scientific-autoresearch-workflow.{suffix}"
            if not (figures / figure_name).is_file():
                errors.append(f"Missing stable workflow figure: figures/{figure_name}")
            if readme.is_file() and f"figures/{figure_name}" not in readme_text:
                errors.append(f"README.md does not reference figures/{figure_name}")
        if figures.is_dir():
            old_names = sorted(path.name for path in figures.glob("scientific-autoresearch-workflow-v*"))
            if old_names:
                errors.append(f"Versioned current workflow filenames are stale: {old_names}")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    skill_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else repo_root / "scientific-autoresearch"
    errors = validate(skill_dir, repo_root)
    if errors:
        print("Package consistency checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Package consistency checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
