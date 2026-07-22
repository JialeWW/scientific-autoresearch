#!/usr/bin/env python3
"""Check this repository's Agent Skill package for internal consistency."""

from __future__ import annotations

import json
import hashlib
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


def contained_regular_file(root: Path, relative_value: object) -> Path | None:
    relative = Path(str(relative_value or ""))
    if not str(relative_value or "").strip() or relative.is_absolute() or ".." in relative.parts:
        return None
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None
    try:
        resolved = (root / relative).resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def behavior_package_sha256(skill_dir: Path) -> str:
    """Use the same fixed behavior-package digest as the installed run validator."""

    root = skill_dir.resolve()
    skill_md = root / "SKILL.md"
    resource_specs = (
        (root / "references", "*.md"),
        (root / "scripts", "*.py"),
        (root / "evals", "*.json"),
    )
    if skill_md.is_symlink() or not skill_md.is_file():
        raise ValueError("SKILL.md must be a regular, nonsymlink file")
    files = [skill_md]
    for directory, pattern in resource_specs:
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"{directory.relative_to(root)} must be a regular directory")
        resources = sorted(directory.glob(pattern), key=lambda item: item.name)
        if not resources:
            raise ValueError(f"no behavior-bearing files matched {directory.relative_to(root) / pattern}")
        if any(path.is_symlink() or not path.is_file() for path in resources):
            raise ValueError(f"{directory.relative_to(root)} contains an invalid behavior-bearing file")
        files.extend(resources)
    digest = hashlib.sha256()
    digest.update(b"scientific-autoresearch-behavior-package-v1\0")
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return "sha256:" + digest.hexdigest()


def frozen_comparison_block_count(manifest: object) -> int:
    """Count comparison blocks that the manifest explicitly marks as frozen."""

    if not isinstance(manifest, dict):
        return 0
    suites = manifest.get("suites")
    if not isinstance(suites, list):
        return 0
    count = 0
    for suite in suites:
        if not isinstance(suite, dict):
            continue
        blocks = suite.get("comparison_blocks")
        if not isinstance(blocks, list):
            continue
        count += sum(
            isinstance(block, dict) and block.get("protocol_status") == "frozen"
            for block in blocks
        )
    return count


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
    for key in ("name", "description"):
        if len(re.findall(rf"(?m)^[ \t]*{key}:\s*", frontmatter)) != 1:
            errors.append(f"Frontmatter must contain exactly one {key} field")
    if len(re.findall(r"(?m)^metadata:\s*$", frontmatter)) != 1:
        errors.append("Frontmatter must contain exactly one metadata mapping")
    if len(re.findall(r"(?m)^\s+version:\s*", frontmatter)) != 1:
        errors.append("Frontmatter metadata must contain exactly one version field")
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

    try:
        current_package_hash = behavior_package_sha256(skill_dir)
    except (OSError, ValueError) as exc:
        errors.append(f"Cannot compute current behavior-package digest: {exc}")
        current_package_hash = None

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
        if not isinstance(evals, dict):
            raise ValueError("top level must be an object")
        if evals.get("skill_name") != name:
            errors.append("evals/evals.json skill_name does not match frontmatter name")
        if evals.get("evaluation_kind") != "behavioral_specification":
            errors.append("evals/evals.json must identify itself as a behavioral specification")
        if evals.get("contains_scored_results") is not False:
            errors.append("evals/evals.json must not claim to contain scored results")
        eval_cases = evals.get("evals")
        if not isinstance(eval_cases, list):
            raise ValueError("evals must be a list")
        if len(eval_cases) < 3:
            errors.append("evals/evals.json must contain at least 3 cases")
        if any(not isinstance(case, dict) for case in eval_cases):
            raise ValueError("every eval case must be an object")
        ids = [case.get("id") for case in eval_cases]
        if len(ids) != len(set(ids)):
            errors.append("evals/evals.json case IDs must be unique")
        for case in eval_cases:
            if not case.get("prompt") or not case.get("expected_output") or not case.get("assertions"):
                errors.append(f"Incomplete output eval case: {case.get('id')}")
                continue
            assertions = case.get("assertions")
            assertion_ids = case.get("assertion_ids")
            critical_ids = case.get("critical_assertion_ids")
            if not isinstance(assertions, list) or any(not isinstance(item, str) or not item for item in assertions):
                errors.append(f"Eval case {case.get('id')} assertions must be nonempty strings")
            if (
                not isinstance(assertion_ids, list)
                or len(assertion_ids) != len(assertions)
                or any(not isinstance(item, str) or not item for item in assertion_ids)
                or len(assertion_ids) != len(set(assertion_ids))
            ):
                errors.append(f"Eval case {case.get('id')} needs one unique assertion ID per assertion")
            if not isinstance(critical_ids, list) or not set(critical_ids) <= set(assertion_ids or []):
                errors.append(f"Eval case {case.get('id')} has invalid critical assertion IDs")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        errors.append(f"Invalid evals/evals.json: {exc}")

    try:
        queries = json.loads(queries_path.read_text(encoding="utf-8"))
        if not isinstance(queries, list) or any(not isinstance(item, dict) for item in queries):
            raise ValueError("top level must be a list of objects")
        positives = sum(item.get("should_trigger") is True for item in queries)
        negatives = sum(item.get("should_trigger") is False for item in queries)
        if positives < 8 or negatives < 8:
            errors.append("eval_queries.json needs at least 8 positive and 8 negative cases")
        query_ids = [item.get("id") for item in queries]
        if any(not isinstance(item, str) or not item for item in query_ids):
            errors.append("eval_queries.json cases need stable string IDs")
        elif len(query_ids) != len(set(query_ids)):
            errors.append("eval_queries.json case IDs must be unique")
        for item in queries:
            if not isinstance(item.get("query"), str) or not item["query"].strip():
                errors.append(f"Trigger case {item.get('id')!r} needs a query")
            if not isinstance(item.get("should_trigger"), bool):
                errors.append(f"Trigger case {item.get('id')!r} needs Boolean should_trigger")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        errors.append(f"Invalid evals/eval_queries.json: {exc}")

    benchmark_root = repo_root / "benchmarks"
    benchmark_manifest_path = benchmark_root / "manifest.json"
    benchmark_scorer_path = benchmark_root / "score.py"
    benchmark_manifest: dict[str, object] = {}
    if not benchmark_scorer_path.is_file():
        errors.append("Missing repository benchmark scorer: benchmarks/score.py")
    try:
        benchmark_manifest = json.loads(benchmark_manifest_path.read_text(encoding="utf-8"))
        if not isinstance(benchmark_manifest, dict):
            raise ValueError("top level must be an object")
        if benchmark_manifest.get("benchmark_schema_version") != "2.1.0":
            errors.append("benchmarks/manifest.json must use benchmark schema 2.1.0")
        if benchmark_manifest.get("benchmark_protocol_version") != "2.1.0":
            errors.append("benchmarks/manifest.json must bind protocol 2.1.0")
        if benchmark_manifest.get("record_schema_version") != "2.1.0":
            errors.append("benchmarks/manifest.json must bind record schema 2.1.0")
        scorer_hash = benchmark_manifest.get("scorer_sha256")
        if not isinstance(scorer_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", scorer_hash):
            errors.append("benchmarks/manifest.json must bind the scorer SHA-256")
        elif benchmark_scorer_path.is_file() and hashlib.sha256(
            benchmark_scorer_path.read_bytes()
        ).hexdigest() != scorer_hash:
            errors.append("benchmarks/manifest.json scorer SHA-256 mismatch")
        if benchmark_manifest.get("release_under_test") != version:
            errors.append("benchmarks/manifest.json release does not match SKILL.md")
        if benchmark_manifest.get("benchmark_status") not in {
            "protocol_2_1_defined_not_evaluated",
            "partially_evaluated",
            "evaluated",
        }:
            errors.append("benchmarks/manifest.json has an invalid benchmark_status")
        states = benchmark_manifest.get("evaluation_state_vocabulary")
        required_states = {
            "not_evaluated",
            "development_suite_evaluated",
            "sealed_suite_baseline_established",
            "prospective_release_gate_evaluated",
            "empirical_method_evaluated",
        }
        if not isinstance(states, list) or set(states) != required_states:
            errors.append("Benchmark evaluation-state vocabulary is incomplete")
        suites = benchmark_manifest.get("suites")
        if not isinstance(suites, list) or len(suites) < 3:
            errors.append("benchmarks/manifest.json must define the evidence suites")
            suites = []
        suite_ids = [suite.get("suite_id") for suite in suites if isinstance(suite, dict)]
        if len(suite_ids) != len(suites) or len(suite_ids) != len(set(suite_ids)):
            errors.append("Benchmark suite IDs must be present and unique")
        package_hashes_by_release: dict[str, set[str]] = {}
        benchmark_specs = {
            "trigger": {
                "primary_estimands": ["trigger_balanced_accuracy_delta"],
                "secondary_estimands": [
                    "case_level_win_loss_tie",
                    "absolute_condition_scores",
                ],
                "diagnostic_estimands": [
                    "completed_output_confusion",
                    "agent_failure_rate",
                    "infrastructure_retry_count",
                ],
                "aggregation_method_id": "trigger_paired_truth_stratified_case_macro_v1",
                "aggregation_rule": "Compute paired case-by-replicate credit differences, average replicates within case, then form a truth-stratified case macro difference.",
                "uncertainty_design": {
                    "case_variation": "case_cluster_bootstrap",
                    "execution_stochasticity": "within_case_paired_replicates_when_available",
                    "judge_uncertainty": "not_applicable",
                },
                "interpretation_scope_id": "development_only_no_generalization_v1",
                "interpretation_rule": "Development evidence only; do not infer a release gate or deployment generalization.",
            },
            "behavioral": {
                "primary_estimands": [
                    "behavioral_case_macro_delta",
                    "critical_violation_risk_difference",
                ],
                "secondary_estimands": [
                    "case_all_pass_rate_delta",
                    "case_level_win_loss_tie",
                    "critical_violation_discordance",
                    "absolute_condition_scores",
                ],
                "diagnostic_estimands": [
                    "assertion_micro_pass_rate",
                    "agent_failure_rate",
                    "infrastructure_retry_count",
                ],
                "aggregation_method_id": "behavioral_paired_case_macro_v1",
                "aggregation_rule": "Compute paired case-by-replicate differences, average replicates within case, then weight cases equally.",
                "uncertainty_design": {
                    "case_variation": "case_cluster_bootstrap",
                    "execution_stochasticity": "within_case_paired_replicates_when_available",
                    "judge_uncertainty": "not_estimable_without_repeated_independent_judgments",
                },
                "interpretation_scope_id": "development_only_no_generalization_v1",
                "interpretation_rule": "Development evidence only; do not infer a release gate or deployment generalization.",
            },
        }
        for suite in suites:
            if not isinstance(suite, dict):
                continue
            suite_id = suite.get("suite_id")
            for field in (
                "suite_id",
                "protocol_status",
                "record_type",
                "scoring_backend",
                "evidence_type",
                "target",
                "conditions",
                "evaluation_unit",
                "primary_estimands",
            ):
                if suite.get(field) in (None, "", []):
                    errors.append(f"Benchmark suite {suite_id!r} is missing {field}")
            status = suite.get("protocol_status")
            backend = suite.get("scoring_backend")
            record_type = suite.get("record_type")
            if backend not in {"score.py", "external"}:
                errors.append(f"Benchmark suite {suite_id!r} has invalid scoring_backend")
            if backend == "score.py" and record_type not in {"trigger", "behavioral"}:
                errors.append(f"Benchmark suite {suite_id!r} has unsupported record_type")
            if backend == "score.py" and status not in {"awaiting_execution_freeze", "frozen"}:
                errors.append(f"Benchmark suite {suite_id!r} has invalid protocol_status")
            if backend == "external" and status != "draft":
                errors.append(f"External benchmark suite {suite_id!r} must remain draft")
            conditions = suite.get("conditions")
            if not isinstance(conditions, list) or not conditions or any(
                not isinstance(condition, dict) for condition in conditions
            ):
                errors.append(f"Benchmark suite {suite_id!r} conditions are invalid")
                conditions = []
            condition_ids = [condition.get("condition_id") for condition in conditions]
            if any(not isinstance(item, str) or not item for item in condition_ids):
                errors.append(f"Benchmark suite {suite_id!r} needs stable condition IDs")
            elif len(condition_ids) != len(set(condition_ids)):
                errors.append(f"Benchmark suite {suite_id!r} condition IDs must be unique")
            for condition in conditions:
                package_hash = condition.get("skill_package_sha256")
                if condition.get("skill_release") is None:
                    if package_hash is not None:
                        errors.append(f"Benchmark suite {suite_id!r} no-skill package must be null")
                elif not isinstance(package_hash, str) or not re.fullmatch(
                    r"sha256:[0-9a-f]{64}", package_hash
                ):
                    errors.append(f"Benchmark suite {suite_id!r} skill package hash is invalid")
                else:
                    release = str(condition.get("skill_release"))
                    package_hashes_by_release.setdefault(release, set()).add(package_hash)
                    if (
                        release == version
                        and current_package_hash is not None
                        and package_hash != current_package_hash
                    ):
                        errors.append(
                            f"Benchmark suite {suite_id!r} current package hash does not match the installable skill"
                        )
            blocks = suite.get("comparison_blocks")
            if not isinstance(blocks, list):
                errors.append(f"Benchmark suite {suite_id!r} comparison_blocks must be a list")
                blocks = []
            if backend == "score.py":
                expected_spec = benchmark_specs.get(record_type)
                if expected_spec is not None:
                    for field, expected in expected_spec.items():
                        if suite.get(field) != expected:
                            errors.append(
                                f"Built-in suite {suite_id!r} {field} does not match protocol 2.1"
                            )
                for field in (
                    "repetitions",
                    "aggregation_method_id",
                    "aggregation_rule",
                    "interval_rule",
                    "tie_rule",
                    "missing_run_policy",
                    "failure_retry_policy",
                    "uncertainty_design",
                    "interpretation_scope_id",
                    "interpretation_rule",
                ):
                    if suite.get(field) in (None, "", [], {}):
                        errors.append(f"Built-in suite {suite_id!r} is missing {field}")
                if status == "awaiting_execution_freeze" and blocks:
                    errors.append(f"Unfrozen suite {suite_id!r} cannot claim frozen blocks")
                if status == "frozen" and not blocks:
                    errors.append(f"Frozen suite {suite_id!r} needs a comparison block")
                repetitions = suite.get("repetitions")
                if not isinstance(repetitions, int) or isinstance(repetitions, bool) or repetitions < 1:
                    errors.append(f"Built-in suite {suite_id!r} needs positive repetitions")
                interval = suite.get("interval_rule")
                expected_method = (
                    "paired_stratified_case_cluster_bootstrap"
                    if record_type == "trigger"
                    else "paired_case_cluster_bootstrap"
                )
                if not isinstance(interval, dict) or interval.get("method") != expected_method:
                    errors.append(f"Built-in suite {suite_id!r} has invalid interval method")
                elif interval.get("bootstrap_unit") != "case":
                    errors.append(f"Built-in suite {suite_id!r} must bootstrap cases")
                source = suite.get("case_source")
                if not isinstance(source, dict):
                    errors.append(f"Built-in suite {suite_id!r} requires case_source")
                else:
                    source_path = contained_regular_file(repo_root, source.get("path"))
                    expected_hash = str(source.get("sha256", ""))
                    if source_path is None:
                        errors.append(f"Benchmark suite {suite_id!r} has an unsafe case source")
                    if not re.fullmatch(r"sha256:[0-9a-f]{64}", expected_hash):
                        errors.append(f"Benchmark suite {suite_id!r} case hash is invalid")
                    elif source_path is not None and (
                        "sha256:" + hashlib.sha256(source_path.read_bytes()).hexdigest()
                    ) != expected_hash:
                        errors.append(f"Benchmark suite {suite_id!r} case hash mismatch")
                    for field in ("case_id_field", "prompt_field", "role"):
                        if source.get(field) in (None, ""):
                            errors.append(f"Benchmark suite {suite_id!r} case source lacks {field}")
            elif suite.get("case_source") is not None and not isinstance(
                suite.get("case_source"), dict
            ):
                errors.append(f"External suite {suite_id!r} case_source is invalid")
        for release, package_hashes in sorted(package_hashes_by_release.items()):
            if len(package_hashes) > 1:
                errors.append(f"Benchmark release {release} has inconsistent package hashes")
        sealed_policy = benchmark_manifest.get("sealed_suite_policy")
        if not isinstance(sealed_policy, dict) or sealed_policy.get("status") != "not_established":
            errors.append("Current manifest must state that no sealed suite is established")
        invalidation = benchmark_manifest.get("protocol_invalidation_policy")
        if not isinstance(invalidation, dict) or invalidation.get(
            "comparison_validity_defect_invalidates_entire_affected_block"
        ) is not True:
            errors.append("Benchmark protocol invalidation policy is incomplete")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        errors.append(f"Invalid benchmarks/manifest.json: {exc}")

    if version:
        benchmark_result_path = benchmark_root / "results" / f"v{version}.json"
        try:
            benchmark_result = json.loads(benchmark_result_path.read_text(encoding="utf-8"))
            if not isinstance(benchmark_result, dict):
                raise ValueError("top level must be an object")
            if benchmark_result.get("benchmark_result_schema_version") != "2.1.0":
                errors.append("Current benchmark result must use result schema 2.1.0")
            if benchmark_result.get("benchmark_protocol_version") != "2.1.0":
                errors.append("Current benchmark result must bind protocol 2.1.0")
            if benchmark_result.get("skill_release") != version:
                errors.append("Current benchmark result release does not match SKILL.md")
            manifest_hash = "sha256:" + hashlib.sha256(
                benchmark_manifest_path.read_bytes()
            ).hexdigest()
            if benchmark_result.get("manifest_sha256") != manifest_hash:
                errors.append("Current benchmark result does not bind the current manifest")
            if not isinstance(benchmark_result.get("statement"), str) or not benchmark_result[
                "statement"
            ].strip():
                errors.append("Current benchmark result needs a nonempty scope statement")
            scoring_status = benchmark_result.get("scoring_status")
            evidence_status = benchmark_result.get("evidence_status")
            if scoring_status == "not_evaluated":
                if evidence_status != "not_evaluated":
                    errors.append("Unevaluated scoring cannot claim evaluated evidence")
                if benchmark_result.get("behavioral_evaluation") != "not_evaluated":
                    errors.append("Unevaluated scoring cannot claim behavioral evaluation")
                if benchmark_result.get("empirical_method_validation") != "not_evaluated":
                    errors.append("Unevaluated scoring cannot claim empirical method validation")
                counts = benchmark_result.get("scored_attempt_counts")
                expected_keys = {"trigger", "behavioral", "empirical"}
                if (
                    not isinstance(counts, dict)
                    or set(counts) != expected_keys
                    or any(
                        not isinstance(value, int) or isinstance(value, bool) or value != 0
                        for value in counts.values()
                    )
                ):
                    errors.append("Unevaluated result must keep every attempt count at zero")
                if benchmark_result.get("summary") is not None:
                    errors.append("Unevaluated result must keep summary=null")
                reported_frozen_blocks = benchmark_result.get("comparison_blocks_frozen")
                actual_frozen_blocks = frozen_comparison_block_count(benchmark_manifest)
                if (
                    not isinstance(reported_frozen_blocks, int)
                    or isinstance(reported_frozen_blocks, bool)
                    or reported_frozen_blocks != actual_frozen_blocks
                ):
                    errors.append(
                        "Unevaluated result comparison_blocks_frozen does not match "
                        f"the manifest ({actual_frozen_blocks})"
                    )
                if actual_frozen_blocks != 0:
                    errors.append(
                        "Unevaluated prepared protocol must have zero frozen comparison blocks"
                    )
                if benchmark_result.get("package_validation") != "separate_structural_check":
                    errors.append("Package consistency must remain a separate evidence state")
                if benchmark_manifest.get("benchmark_status") != "protocol_2_1_defined_not_evaluated":
                    errors.append("Unevaluated result conflicts with manifest status")
            elif scoring_status not in {
                "complete",
                "comparison_incomplete",
                "invalid",
                "invalidated",
            }:
                errors.append("Current benchmark result has invalid scoring_status")
            else:
                for field in (
                    "scorer_version",
                    "records_sha256",
                    "evidence_index_sha256",
                    "summary",
                ):
                    if benchmark_result.get(field) in (None, "", [], {}):
                        errors.append(f"Evaluated result is missing {field}")
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
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
