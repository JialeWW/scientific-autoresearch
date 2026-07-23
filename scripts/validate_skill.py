#!/usr/bin/env python3
"""Check this repository's Agent Skill package for internal consistency."""

from __future__ import annotations

import json
import hashlib
import importlib.util
import re
import sys
from pathlib import Path


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def reject_duplicate_object_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r} is not permitted")
        value[key] = item
    return value


def strict_json_loads(payload: str | bytes) -> object:
    return json.loads(payload, object_pairs_hook=reject_duplicate_object_keys)


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


def contained_directory(root: Path, relative_value: object) -> Path | None:
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
    return resolved if resolved.is_dir() else None


def runtime_package_sha256(skill_dir: Path) -> str:
    """Use the same runtime-package digest as the installed run validator."""

    root = skill_dir.resolve()
    skill_md = root / "SKILL.md"
    resource_specs = (
        (root / "references", "*.md"),
        (root / "scripts", "*.py"),
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
    digest.update(b"scientific-autoresearch-runtime-package-v2\0")
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


SEMVER_RE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def strict_semver(value: object) -> tuple[int, int, int] | None:
    text = str(value or "")
    match = SEMVER_RE.fullmatch(text)
    return tuple(int(part) for part in match.groups()) if match else None


def prefixed_file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_json_snapshot(path: Path) -> tuple[object, str]:
    payload = path.read_bytes()
    return strict_json_loads(payload), "sha256:" + hashlib.sha256(payload).hexdigest()


def load_python_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load Python module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(skill_dir: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    repository_skill_dir = (repo_root / "scientific-autoresearch").resolve()
    validating_repository_source = skill_dir.resolve() == repository_skill_dir
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
        current_package_hash = runtime_package_sha256(skill_dir)
    except (OSError, ValueError) as exc:
        errors.append(f"Cannot compute current runtime-package digest: {exc}")
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
        evals = strict_json_loads(evals_path.read_text(encoding="utf-8"))
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
            if not isinstance(assertions, list) or any(
                not isinstance(item, str) or not item.strip() for item in assertions
            ):
                errors.append(f"Eval case {case.get('id')} assertions must be nonempty strings")
            if (
                not isinstance(assertion_ids, list)
                or len(assertion_ids) != len(assertions)
                or any(
                    not isinstance(item, str) or not item.strip()
                    for item in assertion_ids
                )
                or len(assertion_ids) != len(set(assertion_ids))
            ):
                errors.append(f"Eval case {case.get('id')} needs one unique assertion ID per assertion")
            if (
                not isinstance(critical_ids, list)
                or not critical_ids
                or any(
                    not isinstance(item, str) or not item.strip()
                    for item in critical_ids
                )
                or len(critical_ids) != len(set(critical_ids))
                or not set(critical_ids) <= set(assertion_ids or [])
            ):
                errors.append(f"Eval case {case.get('id')} has invalid critical assertion IDs")
    except FileNotFoundError as exc:
        if validating_repository_source:
            errors.append(f"Invalid evals/evals.json: {exc}")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        errors.append(f"Invalid evals/evals.json: {exc}")

    try:
        queries = strict_json_loads(queries_path.read_text(encoding="utf-8"))
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
    except FileNotFoundError as exc:
        if validating_repository_source:
            errors.append(f"Invalid evals/eval_queries.json: {exc}")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        errors.append(f"Invalid evals/eval_queries.json: {exc}")

    benchmark_root = repo_root / "benchmarks"
    protocol_index_path = benchmark_root / "protocol-index.json"
    protocol_index: dict[str, object] = {}
    protocol_entries_by_version: dict[str, dict[str, object]] = {}
    protocol_entries_by_manifest_hash: dict[str, dict[str, object]] = {}
    protocol_manifests_by_version: dict[str, dict[str, object]] = {}
    protocol_manifests_by_hash: dict[str, dict[str, object]] = {}
    result_index_entries: list[dict[str, object]] = []
    result_values_by_path: dict[str, dict[str, object]] = {}
    execution_index_entries: list[dict[str, object]] = []
    try:
        protocol_index = strict_json_loads(protocol_index_path.read_text(encoding="utf-8"))
        if not isinstance(protocol_index, dict):
            raise ValueError("top level must be an object")
        expected_index_fields = {
            "protocol_index_schema_version",
            "latest_protocol_version",
            "protocols",
            "results",
            "legacy_unbound_results",
            "executions",
        }
        if set(protocol_index) != expected_index_fields:
            errors.append("benchmarks/protocol-index.json must use the closed schema")
        if protocol_index.get("protocol_index_schema_version") != "1.1.0":
            errors.append("Benchmark protocol index must use schema 1.1.0")
        latest_protocol_version = protocol_index.get("latest_protocol_version")
        if strict_semver(latest_protocol_version) is None:
            errors.append("Benchmark latest protocol version is not strict SemVer")
        elif latest_protocol_version != "2.1.2":
            errors.append("Benchmark latest protocol version must be 2.1.2")
        protocols = protocol_index.get("protocols")
        if not isinstance(protocols, list) or not protocols:
            errors.append("Benchmark protocol index must define protocols")
            protocols = []
        for entry in protocols:
            if not isinstance(entry, dict) or set(entry) != {
                "benchmark_protocol_version",
                "release_under_test",
                "status",
                "manifest_path",
                "manifest_sha256",
                "scorer_path",
                "scorer_sha256",
            }:
                errors.append("Benchmark protocol index has an invalid protocol entry")
                continue
            protocol_version = entry.get("benchmark_protocol_version")
            if strict_semver(protocol_version) is None:
                errors.append(f"Invalid benchmark protocol version: {protocol_version!r}")
                continue
            protocol_version = str(protocol_version)
            if protocol_version in protocol_entries_by_version:
                errors.append(f"Duplicate benchmark protocol version: {protocol_version}")
                continue
            manifest_path = contained_regular_file(repo_root, entry.get("manifest_path"))
            scorer_path = contained_regular_file(repo_root, entry.get("scorer_path"))
            manifest_hash = entry.get("manifest_sha256")
            scorer_hash = entry.get("scorer_sha256")
            if manifest_path is None or scorer_path is None:
                errors.append(f"Benchmark protocol {protocol_version} has an unsafe artifact path")
                continue
            if not isinstance(manifest_hash, str) or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", manifest_hash
            ):
                errors.append(f"Benchmark protocol {protocol_version} has an invalid manifest hash")
                continue
            if not isinstance(scorer_hash, str) or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", scorer_hash
            ):
                errors.append(f"Benchmark protocol {protocol_version} has an invalid scorer hash")
                continue
            manifest_value, actual_manifest_hash = load_json_snapshot(manifest_path)
            if actual_manifest_hash != manifest_hash:
                errors.append(f"Benchmark protocol {protocol_version} manifest hash mismatch")
            if prefixed_file_sha256(scorer_path) != scorer_hash:
                errors.append(f"Benchmark protocol {protocol_version} scorer hash mismatch")
            if not isinstance(manifest_value, dict):
                errors.append(f"Benchmark protocol {protocol_version} manifest is not an object")
            else:
                declared_protocol = manifest_value.get(
                    "benchmark_protocol_version",
                    manifest_value.get("benchmark_schema_version"),
                )
                if declared_protocol != protocol_version:
                    errors.append(f"Benchmark protocol {protocol_version} manifest version mismatch")
                if manifest_value.get("release_under_test") != entry.get("release_under_test"):
                    errors.append(f"Benchmark protocol {protocol_version} release mismatch")
                declared_scorer = manifest_value.get("scorer_sha256")
                if declared_scorer != str(scorer_hash).removeprefix("sha256:"):
                    errors.append(f"Benchmark protocol {protocol_version} scorer binding mismatch")
                protocol_manifests_by_version[protocol_version] = manifest_value
                protocol_manifests_by_hash[str(manifest_hash)] = manifest_value
            protocol_entries_by_version[protocol_version] = entry
            if manifest_hash in protocol_entries_by_manifest_hash:
                errors.append(f"Benchmark manifest hash is ambiguously indexed: {manifest_hash}")
            protocol_entries_by_manifest_hash[str(manifest_hash)] = entry
        if str(latest_protocol_version) not in protocol_entries_by_version:
            errors.append("Benchmark latest protocol version is not indexed")
        current_protocols = [
            entry
            for entry in protocol_entries_by_version.values()
            if entry.get("status") == "current_protocol_not_evaluated"
        ]
        if (
            len(current_protocols) != 1
            or current_protocols[0].get("benchmark_protocol_version")
            != latest_protocol_version
        ):
            errors.append(
                "Benchmark index must identify exactly one current latest protocol"
            )
        raw_results = protocol_index.get("results")
        if not isinstance(raw_results, list):
            errors.append("Benchmark protocol index results must be a list")
            raw_results = []
        result_paths: set[str] = set()
        for entry in raw_results:
            if not isinstance(entry, dict) or set(entry) != {
                "path",
                "result_sha256",
                "result_schema_version",
                "skill_release",
                "benchmark_protocol_version",
                "manifest_sha256",
            }:
                errors.append("Benchmark protocol index has an invalid result entry")
                continue
            relative_path = str(entry.get("path", ""))
            if relative_path in result_paths:
                errors.append(f"Duplicate indexed benchmark result: {relative_path}")
            result_paths.add(relative_path)
            indexed_result_path = contained_regular_file(repo_root, relative_path)
            if indexed_result_path is None:
                errors.append(f"Indexed benchmark result has an unsafe path: {relative_path}")
            else:
                result_value, actual_result_hash = load_json_snapshot(indexed_result_path)
                if entry.get("result_sha256") != actual_result_hash:
                    errors.append(f"Indexed benchmark result hash mismatch: {relative_path}")
                if not isinstance(result_value, dict):
                    errors.append(f"Indexed benchmark result is not an object: {relative_path}")
                else:
                    result_values_by_path[relative_path] = result_value
            if strict_semver(entry.get("result_schema_version")) is None:
                errors.append(f"Indexed benchmark result has invalid schema: {relative_path}")
            protocol_entry = protocol_entries_by_version.get(
                str(entry.get("benchmark_protocol_version"))
            )
            if protocol_entry is None or entry.get("manifest_sha256") != protocol_entry.get(
                "manifest_sha256"
            ):
                errors.append(f"Indexed benchmark result has an invalid protocol binding: {relative_path}")
            result_index_entries.append(entry)
        legacy_results = protocol_index.get("legacy_unbound_results")
        if not isinstance(legacy_results, list) or any(
            contained_regular_file(repo_root, path) is None for path in legacy_results
        ):
            errors.append("Benchmark legacy unbound result index is invalid")
        raw_executions = protocol_index.get("executions")
        if not isinstance(raw_executions, list):
            errors.append("Benchmark protocol index executions must be a list")
            raw_executions = []
        execution_index_entries = [
            entry for entry in raw_executions if isinstance(entry, dict)
        ]
        if len(execution_index_entries) != len(raw_executions):
            errors.append("Benchmark protocol index has an invalid execution entry")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        errors.append(f"Invalid benchmarks/protocol-index.json: {exc}")

    benchmark_manifest_path = benchmark_root / "manifest-v2.1.2.json"
    benchmark_scorer_path = benchmark_root / "score-v2.1.2.py"
    benchmark_manifest: dict[str, object] = {}
    if not benchmark_scorer_path.is_file():
        errors.append("Missing repository benchmark scorer: benchmarks/score-v2.1.2.py")
    try:
        current_protocol_entry = protocol_entries_by_version.get("2.1.2")
        if current_protocol_entry is None:
            raise ValueError("protocol 2.1.2 is not indexed")
        expected_manifest_path = str(benchmark_manifest_path.relative_to(repo_root))
        if current_protocol_entry.get("manifest_path") != expected_manifest_path:
            raise ValueError("protocol 2.1.2 does not bind the current manifest path")
        benchmark_manifest = protocol_manifests_by_version.get("2.1.2", {})
        if not isinstance(benchmark_manifest, dict):
            raise ValueError("top level must be an object")
        if benchmark_manifest.get("benchmark_schema_version") != "2.1.2":
            errors.append("benchmarks/manifest-v2.1.2.json must use benchmark schema 2.1.2")
        if benchmark_manifest.get("benchmark_protocol_version") != "2.1.2":
            errors.append("benchmarks/manifest-v2.1.2.json must bind protocol 2.1.2")
        if benchmark_manifest.get("record_schema_version") != "2.1.0":
            errors.append("benchmarks/manifest-v2.1.2.json must bind record schema 2.1.0")
        scorer_hash = benchmark_manifest.get("scorer_sha256")
        if not isinstance(scorer_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", scorer_hash):
            errors.append("benchmarks/manifest-v2.1.2.json must bind the scorer SHA-256")
        elif benchmark_scorer_path.is_file() and hashlib.sha256(
            benchmark_scorer_path.read_bytes()
        ).hexdigest() != scorer_hash:
            errors.append("benchmarks/manifest-v2.1.2.json scorer SHA-256 mismatch")
        if benchmark_manifest.get("release_under_test") != current_protocol_entry.get(
            "release_under_test"
        ):
            errors.append(
                "benchmarks/manifest-v2.1.2.json release does not match its protocol-index entry"
            )
        if benchmark_manifest.get("benchmark_status") != (
            "development_protocol_2_1_2_defined_not_evaluated"
        ):
            errors.append("benchmarks/manifest-v2.1.2.json has an invalid benchmark_status")
        if benchmark_manifest.get("manifest_kind") != "protocol_template":
            errors.append("Current benchmark protocol must remain a protocol_template")
        if any(
            benchmark_manifest.get(field) is not None
            for field in ("execution_manifest_id", "execution_purpose", "frozen_at")
        ):
            errors.append("Current benchmark protocol template cannot claim execution state")
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
            errors.append("benchmarks/manifest-v2.1.2.json must define the evidence suites")
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
                package_assurance = condition.get("package_assurance")
                if condition.get("skill_release") is None:
                    if package_hash is not None:
                        errors.append(f"Benchmark suite {suite_id!r} no-skill package must be null")
                    if not isinstance(package_assurance, dict) or package_assurance != {
                        "mode": "not_applicable",
                        "artifact": None,
                        "attestation_artifact": None,
                    }:
                        errors.append(
                            f"Benchmark suite {suite_id!r} no-skill assurance must be not_applicable"
                        )
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
                            f"Benchmark suite {suite_id!r} current runtime-package hash does not match the installable skill"
                        )
                    if not isinstance(package_assurance, dict) or set(package_assurance) != {
                        "mode",
                        "artifact",
                        "attestation_artifact",
                    }:
                        errors.append(
                            f"Benchmark suite {suite_id!r} package assurance is invalid"
                        )
                    elif package_assurance.get("mode") not in {
                        "artifact_verified",
                        "attested",
                    }:
                        errors.append(
                            f"Benchmark suite {suite_id!r} package assurance mode is invalid"
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
                                f"Built-in suite {suite_id!r} {field} does not match protocol 2.1.2"
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
        if benchmark_scorer_path.is_file():
            scorer_module = load_python_module(
                benchmark_scorer_path,
                "scientific_autoresearch_benchmark_score_2_1_2_validation",
            )
            scorer_module._load_protocol(benchmark_manifest_path)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        errors.append(f"Invalid benchmarks/manifest-v2.1.2.json: {exc}")

    current_result_entries = [
        entry for entry in result_index_entries if entry.get("skill_release") == version
    ]
    if version and current_result_entries:
        benchmark_result_path = benchmark_root / "results" / f"v{version}.json"
        try:
            result_relative_path = str(benchmark_result_path.relative_to(repo_root))
            benchmark_result = result_values_by_path.get(result_relative_path)
            if not isinstance(benchmark_result, dict):
                raise ValueError("current result is not an indexed object snapshot")
            indexed_result = next(
                (
                    entry
                    for entry in result_index_entries
                    if entry.get("path") == result_relative_path
                ),
                None,
            )
            if indexed_result is None:
                raise ValueError(
                    "current release has an indexed result but not at its canonical path"
                )
            result_manifest_hash = indexed_result.get("manifest_sha256")
            result_protocol_entry = protocol_entries_by_manifest_hash.get(
                str(result_manifest_hash)
            )
            result_manifest_path = (
                contained_regular_file(repo_root, result_protocol_entry.get("manifest_path"))
                if result_protocol_entry is not None
                else None
            )
            if result_manifest_path is None:
                errors.append("Current benchmark result cannot resolve its historical manifest")
                result_manifest: dict[str, object] = {}
            else:
                result_manifest = protocol_manifests_by_hash.get(
                    str(result_manifest_hash), {}
                )
                if not isinstance(result_manifest, dict):
                    raise ValueError("resolved result manifest must be an object")
            if len(current_result_entries) != 1:
                errors.append("Current release must not have multiple indexed result snapshots")
            if benchmark_result.get("benchmark_result_schema_version") != indexed_result.get(
                "result_schema_version"
            ):
                errors.append("Current benchmark result schema does not match its index entry")
            if benchmark_result.get("benchmark_protocol_version") != indexed_result.get(
                "benchmark_protocol_version"
            ):
                errors.append("Current benchmark result protocol does not match its index entry")
            if benchmark_result.get("skill_release") != version:
                errors.append("Current benchmark result release does not match SKILL.md")
            if benchmark_result.get("manifest_sha256") != result_manifest_hash:
                errors.append("Current benchmark result does not bind its indexed historical manifest")
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
                actual_frozen_blocks = frozen_comparison_block_count(result_manifest)
                if (
                    not isinstance(reported_frozen_blocks, int)
                    or isinstance(reported_frozen_blocks, bool)
                    or reported_frozen_blocks != actual_frozen_blocks
                ):
                    errors.append(
                        "Unevaluated result comparison_blocks_frozen does not match "
                        f"the manifest ({actual_frozen_blocks})"
                    )
                if benchmark_result.get("package_validation") != "separate_structural_check":
                    errors.append("Package consistency must remain a separate evidence state")
                if "not_evaluated" not in str(result_manifest.get("benchmark_status", "")):
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

    for indexed_result in result_index_entries:
        try:
            result_path_key = str(indexed_result.get("path", ""))
            result_value = result_values_by_path.get(result_path_key)
            if not isinstance(result_value, dict):
                raise ValueError("indexed result is not an object snapshot")
            if result_value.get("benchmark_result_schema_version") != indexed_result.get(
                "result_schema_version"
            ):
                errors.append(f"Indexed result schema mismatch: {indexed_result.get('path')}")
            if result_value.get("skill_release") != indexed_result.get("skill_release"):
                errors.append(f"Indexed result release mismatch: {indexed_result.get('path')}")
            if result_value.get("manifest_sha256") != indexed_result.get("manifest_sha256"):
                errors.append(f"Indexed result manifest mismatch: {indexed_result.get('path')}")
            content_protocol = result_value.get("benchmark_protocol_version")
            if content_protocol is not None and content_protocol != indexed_result.get(
                "benchmark_protocol_version"
            ):
                errors.append(f"Indexed result protocol mismatch: {indexed_result.get('path')}")
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            errors.append(f"Invalid indexed benchmark result {indexed_result.get('path')}: {exc}")

    frozen_anchor_hashes = {
        "benchmarks/manifest-v2.0.0.json": "sha256:38169dcc0ba0c6c24906a4eb6bf5248e58378347179ff96bddf98d1a2a0f8109",
        "benchmarks/score-v2.0.0.py": "sha256:19d8ba84a19c2a450d92b02de6e218cee669a887ac9a56d1bbd0d6c285a9f4a5",
        "benchmarks/results/v0.2.7.json": "sha256:245195e6c8d330ada7a000305b7d45e8a2aa773feb121a24edb52734edc5e842",
        "benchmarks/manifest.json": "sha256:76063b3f8f6155938a01a7810951ca3beaac84f5cc1f2d34b22aca90c31f2e96",
        "benchmarks/score.py": "sha256:409f19d74a69b417b96dfabea7c62d1973e96b0dc04957937a00144ae1d92549",
        "benchmarks/results/v0.2.8.json": "sha256:1d334d4273be58c5767b1f9a93499376414d798d21e2e7f03fd8d6be78c207e4",
        "benchmarks/results/v0.2.6.json": "sha256:0fd05bcd0e08e63369d767f66fdd51d150b74a70055744c47099bcc0939fd88a",
        "benchmarks/manifest-v2.1.1.json": "sha256:cf3943270a4d2645eb96ce0a4ba583894577b731723363477a4de4ac6e1ec724",
        "benchmarks/score-v2.1.1.py": "sha256:801e17a84bc04c00cb0ec1757bdaf2b5c6da6ee3b51def90b715824c3c7c889f",
        "benchmarks/prepare-shakedown.py": "sha256:37403936561949280ad9a086e91cc1f4c9a230dd52a3f1c8ab95e97c761f1b17",
        "benchmarks/shakedown-harness.py": "sha256:3abacf79911b14c9ee9be5d5350552a9fae0eaa2493f1d3e2449d6784fa6f115",
        "benchmarks/execution-manifest-shakedown-v2.1.1.json": "sha256:7edd65ffd0d5351b3bfc4e25c729e9f04358364f081c6b4be62564ba53839951",
        "benchmarks/executions/shakedown-v2.1.1/records.jsonl": "sha256:228909085a740fe62ede7706950bf2c144c26b77bff3336cd99c004c861f6ed8",
        "benchmarks/executions/shakedown-v2.1.1/result.json": "sha256:6b00547600fbe33595353fb7c751a7764c5b5310b53aefa8ef6f79cd0cec4303",
        "benchmarks/executions/shakedown-v2.1.1/execution-receipt.json": "sha256:00345d7b8dde3c462b4a30660cad3aa98e08aee437ebbf76cc85bbca37eb3faa",
        "benchmarks/tests/test_score_v2_1_1.py": "sha256:a095ce8b082260e4c75f666dc374337f86d00483d4e7f6264a62ded9546dc6b2",
        "benchmarks/artifacts/packages/scientific-autoresearch-v0.2.8.zip": "sha256:4bfdf765018e8026d7ecd8f7dbe9bc423ffc237827b8ad5b9d901e23d7becbb9",
        "benchmarks/artifacts/packages/scientific-autoresearch-v0.2.7.zip": "sha256:d24c3f166682f755043b10debd1dc5f4c98e7e7028b46e1a38c14ee0a0606d7b",
        "benchmarks/artifacts/packages/scientific-autoresearch-v0.2.6.zip": "sha256:368c215f36fb4b9f66bd760726a686118e3de8a23ff883de58cf9987b31e442c",
    }
    for relative_path, expected_hash in frozen_anchor_hashes.items():
        anchor_path = contained_regular_file(repo_root, relative_path)
        if anchor_path is None or prefixed_file_sha256(anchor_path) != expected_hash:
            errors.append(f"Frozen benchmark anchor changed: {relative_path}")

    try:
        expected_execution_fields = {
            "execution_manifest_id",
            "execution_purpose",
            "benchmark_protocol_version",
            "manifest_path",
            "manifest_sha256",
            "protocol_template_path",
            "protocol_template_sha256",
            "protocol_projection_sha256",
            "scorer_path",
            "scorer_sha256",
            "harness_path",
            "harness_sha256",
            "records_path",
            "records_sha256",
            "evidence_root",
            "evidence_tree_sha256",
            "result_path",
            "result_sha256",
            "receipt_path",
            "receipt_sha256",
            "evidence_status",
        }
        execution_ids: set[str] = set()
        for entry in execution_index_entries:
            if set(entry) != expected_execution_fields:
                errors.append("Benchmark execution index entry must use the closed schema")
                continue
            execution_id = str(entry.get("execution_manifest_id", ""))
            if not execution_id or execution_id in execution_ids:
                errors.append("Benchmark execution IDs must be present and unique")
                continue
            execution_ids.add(execution_id)
            manifest_path = contained_regular_file(repo_root, entry.get("manifest_path"))
            scorer_path = contained_regular_file(repo_root, entry.get("scorer_path"))
            harness_path = contained_regular_file(repo_root, entry.get("harness_path"))
            records_path = contained_regular_file(repo_root, entry.get("records_path"))
            result_path = contained_regular_file(repo_root, entry.get("result_path"))
            receipt_path = contained_regular_file(repo_root, entry.get("receipt_path"))
            evidence_path = contained_directory(repo_root, entry.get("evidence_root"))
            if (
                manifest_path is None
                or scorer_path is None
                or harness_path is None
                or records_path is None
                or result_path is None
                or receipt_path is None
                or evidence_path is None
            ):
                errors.append(f"Benchmark execution {execution_id} has an unsafe artifact path")
                continue
            if entry.get("scorer_sha256") != prefixed_file_sha256(scorer_path):
                errors.append(f"Benchmark execution {execution_id} scorer_sha256 mismatch")
            if entry.get("harness_sha256") != prefixed_file_sha256(harness_path):
                errors.append(f"Benchmark execution {execution_id} harness_sha256 mismatch")
            protocol_version = str(entry.get("benchmark_protocol_version", ""))
            if strict_semver(protocol_version) is None:
                errors.append(f"Benchmark execution {execution_id} has an invalid protocol version")
                continue
            registered_protocol = protocol_entries_by_version.get(protocol_version)
            if (
                registered_protocol is None
                or entry.get("scorer_path") != registered_protocol.get("scorer_path")
                or entry.get("scorer_sha256")
                != registered_protocol.get("scorer_sha256")
            ):
                errors.append(
                    f"Benchmark execution {execution_id} does not use its registered scorer"
                )
            scorer_module = load_python_module(
                scorer_path,
                "scientific_autoresearch_benchmark_score_"
                + protocol_version.replace(".", "_")
                + "_execution_validation",
            )
            protocol = scorer_module._load_protocol(manifest_path)
            records, records_digest = scorer_module._load_jsonl_with_hash(records_path)
            stored_result, result_digest = load_json_snapshot(result_path)
            receipt, receipt_digest = load_json_snapshot(receipt_path)
            for actual_digest, field in (
                (protocol["manifest_sha256"], "manifest_sha256"),
                (records_digest, "records_sha256"),
                (result_digest, "result_sha256"),
                (receipt_digest, "receipt_sha256"),
            ):
                if entry.get(field) != actual_digest:
                    errors.append(f"Benchmark execution {execution_id} {field} mismatch")
            rescored = scorer_module.score_records(
                records,
                manifest_path,
                evidence_path,
                records_sha256=records_digest,
            )
            if not isinstance(stored_result, dict):
                raise ValueError("stored execution result must be an object")
            if rescored != stored_result:
                errors.append(f"Benchmark execution {execution_id} result is not reproducible")
            manifest_value = protocol["manifest"]
            if manifest_value.get("benchmark_protocol_version") != protocol_version:
                errors.append(
                    f"Benchmark execution {execution_id} protocol version mismatch"
                )
            parent_path_value = entry.get("protocol_template_path")
            parent_hash_value = entry.get("protocol_template_sha256")
            projection_hash_value = entry.get("protocol_projection_sha256")
            parent_ref = manifest_value.get("protocol_template_artifact")
            if parent_path_value is None and parent_hash_value is None:
                if protocol_version == "2.1.2":
                    errors.append(
                        f"Benchmark execution {execution_id} lacks the required parent template"
                    )
                if parent_ref is not None:
                    errors.append(
                        f"Benchmark execution {execution_id} parent-template index is incomplete"
                    )
                if projection_hash_value is not None:
                    errors.append(
                        f"Benchmark execution {execution_id} cannot index an unbound projection"
                    )
            else:
                parent_path = contained_regular_file(repo_root, parent_path_value)
                if (
                    parent_path is None
                    or parent_hash_value != prefixed_file_sha256(parent_path)
                    or not isinstance(parent_ref, dict)
                    or parent_ref.get("path") != parent_path_value
                    or parent_ref.get("sha256") != parent_hash_value
                    or projection_hash_value
                    != manifest_value.get("protocol_projection_sha256")
                ):
                    errors.append(
                        f"Benchmark execution {execution_id} parent-template binding is invalid"
                    )
            if (
                entry.get("execution_purpose") != manifest_value.get("execution_purpose")
                or entry.get("execution_purpose") != stored_result.get("execution_purpose")
                or manifest_value.get("execution_manifest_id") != execution_id
                or stored_result.get("execution_manifest_id") != execution_id
                or entry.get("evidence_status") != stored_result.get("evidence_status")
                or entry.get("evidence_tree_sha256")
                != stored_result.get("evidence_tree_sha256")
            ):
                errors.append(
                    f"Benchmark execution {execution_id} index, manifest, and result disagree"
                )
            if (
                stored_result.get("valid") is not True
                or stored_result.get("execution_purpose") != "execution_shakedown"
                or stored_result.get("evidence_status") != "not_evaluated"
                or stored_result.get("condition_summaries") != []
                or stored_result.get("paired_comparisons") != []
            ):
                errors.append(f"Benchmark execution {execution_id} crosses the shakedown boundary")
            receipt_fields = {
                "execution_receipt_schema_version",
                "assurance",
                "execution_manifest_id",
                "execution_purpose",
                "manifest_sha256",
                "scorer_sha256",
                "harness_sha256",
                "records_sha256",
                "result_sha256",
                "evidence_tree_sha256",
                "attempt_count",
                "injected_failure_classes",
                "clock_mode",
                "statement",
            }
            if (
                not isinstance(receipt, dict)
                or set(receipt) != receipt_fields
                or receipt.get("execution_receipt_schema_version") != "1.0.0"
                or receipt.get("assurance") != "runner_attested"
                or receipt.get("execution_manifest_id") != execution_id
                or receipt.get("execution_purpose") != entry.get("execution_purpose")
                or receipt.get("manifest_sha256") != protocol["manifest_sha256"]
                or receipt.get("scorer_sha256") != prefixed_file_sha256(scorer_path)
                or receipt.get("harness_sha256") != prefixed_file_sha256(harness_path)
                or receipt.get("records_sha256") != records_digest
                or receipt.get("result_sha256") != result_digest
                or receipt.get("evidence_tree_sha256")
                != stored_result.get("evidence_tree_sha256")
                or receipt.get("attempt_count") != len(records)
                or receipt.get("injected_failure_classes")
                != ["infrastructure_retry", "agent_failure"]
                or receipt.get("clock_mode") != "deterministic_fixture"
                or receipt.get("statement")
                != "This receipt attests to the local fixture execution; it is not independent or cryptographic assurance and is not behavioral evidence."
                or stored_result.get("execution_artifact_assurance", {}).get(
                    "runtime_use_assurance"
                )
                != "unreported"
            ):
                errors.append(f"Benchmark execution {execution_id} receipt is invalid")
            statuses = [record.get("run_status") for record in records]
            if "harness_error" not in statuses or "agent_error" not in statuses:
                errors.append(f"Benchmark execution {execution_id} did not exercise both failure classes")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        errors.append(f"Invalid benchmark execution archive: {exc}")

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
