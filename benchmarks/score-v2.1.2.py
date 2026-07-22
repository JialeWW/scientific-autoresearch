#!/usr/bin/env python3
"""Score hash-bound, paired benchmark attempts against protocol 2.1.2."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import random
import re
import stat
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


SCORER_VERSION = "2.1.2"
BENCHMARK_SCHEMA_VERSION = "2.1.2"
RECORD_SCHEMA_VERSION = "2.1.0"
SCORE_SCHEMA_VERSION = "2.1.2"
HASH_RE = re.compile(r"(?:sha256:)?([0-9a-f]{64})")
PACKAGE_DIGEST_PROFILE = "scientific-autoresearch-behavior-package-v1"
PACKAGE_ARTIFACT_FORMAT = "scientific-autoresearch-behavior-package-zip-v1"
HARNESS_ARTIFACT_FORMATS = {
    "single-file-sha256-v1",
    "zip-bundle-sha256-v1",
}
ASSURANCE_MODES = {"artifact_verified", "attested", "not_applicable"}
EXECUTION_PURPOSES = {
    "execution_shakedown",
    "development_evaluation",
}
PROTOCOL_PROJECTION_PROFILE = "scientific-autoresearch-immutable-protocol-v1"
RELEASE_UNDER_TEST = "0.2.8"
TARGET_CONDITION_ID = "skill-v0.2.8"
PROTOCOL_ID_BY_SCOPE = {
    "development_evaluation": "scientific-autoresearch-development-benchmark-v2.1.2",
    "execution_shakedown": "scientific-autoresearch-shakedown-benchmark-v2.1.2",
}
BENCHMARK_STATUS_BY_KIND_AND_SCOPE = {
    ("protocol_template", "development_evaluation"): (
        "development_protocol_2_1_2_defined_not_evaluated"
    ),
    ("protocol_template", "execution_shakedown"): (
        "shakedown_protocol_2_1_2_defined_not_evaluated"
    ),
    ("execution", "development_evaluation"): (
        "development_execution_frozen_not_evaluated"
    ),
    ("execution", "execution_shakedown"): "execution_shakedown_frozen",
}
EVALUATION_STATE_VOCABULARY = [
    "not_evaluated",
    "development_suite_evaluated",
    "sealed_suite_baseline_established",
    "prospective_release_gate_evaluated",
    "empirical_method_evaluated",
]
RESULT_POLICY = {
    "development_and_sealed_cases_separate": True,
    "raw_outputs_and_all_attempts_required": True,
    "complete_cross_condition_pairing_required_for_deltas": True,
    "condition_is_the_only_allowed_scientific_treatment_difference": True,
    "hash_verified_config_schedule_and_judge_artifacts_required": True,
    "uncertainty_reported_only_for_observed_replication_levels": True,
    "scope_claims_to_tested_blocks": True,
    "comparison_blocks_never_pooled": True,
    "structural_checks_do_not_establish_behavioral_or_empirical_validity": True,
    "execution_manifest_must_match_parent_protocol_projection": True,
}
SEALED_SUITE_POLICY = {
    "status": "not_established",
    "required_commitment_fields": [
        "sealed_suite_id",
        "case_count",
        "stratum_counts",
        "case_bundle_commitment_sha256",
        "rubric_bundle_commitment_sha256",
        "frozen_at",
        "custodian",
        "access_policy",
        "retirement_policy",
    ],
    "first_use_status": "sealed_suite_baseline_established",
    "prospective_gate_must_be_frozen_before_target_release": True,
    "leaked_or_tuning_exposed_suite_becomes_development": True,
    "rotation_policy_required_before_reuse": True,
}
PROTOCOL_INVALIDATION_POLICY = {
    "comparison_validity_defect_invalidates_entire_affected_block": True,
    "assignable_evidence_or_judgment_defect_is_block_local": True,
    "unassignable_orphan_or_unsafe_evidence_is_submission_invalid": True,
    "partial_result_repair_forbidden": True,
    "repair_requires_new_protocol_or_scorer_patch_version": True,
    "superseded_batches_retain_original_attempts_and_invalidation_reason": True,
}
# Filled only from frozen 2.1.2 template projections. Test fixtures patch this
# mapping locally; the command-line scorer has no projection override.
EXPECTED_TEMPLATE_PROJECTION_BY_SCOPE = {
    "development_evaluation": "sha256:f12a6c00b6bb72c1f6969ea5e2f7bde374f7a23e6656080d628e0561ad4189fa",
    "execution_shakedown": "sha256:7df75f437dc7fc273d8fb78faddb735da57b88d718679ac2e532078a1159e368",
}

RUN_STATUSES = {
    "completed",
    "agent_timeout",
    "agent_error",
    "policy_refusal",
    "harness_error",
    "provider_error",
    "invalid_output",
    "cancelled_before_execution",
}
AGENT_FAILURE_STATUSES = {
    "agent_timeout",
    "agent_error",
    "policy_refusal",
    "invalid_output",
}
INFRASTRUCTURE_FAILURE_STATUSES = {
    "harness_error",
    "provider_error",
    "cancelled_before_execution",
}
SEED_CONTROL_STATUSES = {
    "enforced",
    "requested_not_guaranteed",
    "unavailable",
}
EVIDENCE_STATUSES = {
    "not_evaluated",
    "development_suite_evaluated",
    "sealed_suite_baseline_established",
    "prospective_release_gate_evaluated",
    "empirical_method_evaluated",
}
EVIDENCE_STATUS_ORDER = {
    "not_evaluated": 0,
    "development_suite_evaluated": 1,
    "sealed_suite_baseline_established": 2,
    "prospective_release_gate_evaluated": 3,
    "empirical_method_evaluated": 4,
}

ESTIMAND_SPEC_BY_RECORD_TYPE = {
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
SHAKEDOWN_INTERPRETATION = {
    "interpretation_scope_id": "execution_shakedown_no_behavioral_inference_v1",
    "interpretation_rule": "Execution shakedown only; suppress behavioral metrics and retain evidence_status=not_evaluated.",
}

BUILTIN_SUITE_FIELDS = {
    "suite_id",
    "protocol_status",
    "record_type",
    "scoring_backend",
    "evidence_type",
    "target",
    "case_source",
    "conditions",
    "required_condition_ids",
    "required_contrasts",
    "evaluation_unit",
    "repetitions",
    "primary_estimands",
    "secondary_estimands",
    "diagnostic_estimands",
    "aggregation_method_id",
    "aggregation_rule",
    "interval_rule",
    "tie_rule",
    "missing_run_policy",
    "failure_retry_policy",
    "uncertainty_design",
    "interpretation_scope_id",
    "interpretation_rule",
    "comparison_blocks",
}
EXTERNAL_SUITE_FIELDS = BUILTIN_SUITE_FIELDS - {
    "aggregation_method_id",
    "interpretation_scope_id",
}
CONDITION_FIELDS = {
    "condition_id",
    "skill_release",
    "skill_package_sha256",
    "package_assurance",
}
COMPARISON_BLOCK_FIELDS = {
    "comparison_block_id",
    "run_batch_id",
    "protocol_status",
    "condition_ids",
    "contrasts",
    "executor_identity",
    "execution_config_artifact",
    "seed_control_status",
    "seed_schedule_artifact",
    "order_schedule_artifact",
    "routing_protocol_artifact",
    "judge_protocol_artifact",
    "isolation_policy",
    "max_pair_window_seconds",
    "evidence_status_on_complete",
}
MANIFEST_FIELDS = {
    "benchmark_schema_version",
    "benchmark_protocol_version",
    "protocol_id",
    "protocol_scope",
    "release_under_test",
    "benchmark_status",
    "manifest_kind",
    "execution_manifest_id",
    "execution_purpose",
    "frozen_at",
    "protocol_template_artifact",
    "protocol_projection_profile",
    "protocol_projection_sha256",
    "record_schema_version",
    "scorer_sha256",
    "evaluation_state_vocabulary",
    "suites",
    "result_policy",
    "sealed_suite_policy",
    "protocol_invalidation_policy",
}

COMMON_RECORD_FIELDS = {
    "record_schema_version",
    "manifest_sha256",
    "suite_id",
    "comparison_block_id",
    "run_batch_id",
    "condition_id",
    "skill_release",
    "skill_package_sha256",
    "case_id",
    "replicate",
    "attempt",
    "agent",
    "model",
    "runtime",
    "execution_config_path",
    "execution_config_schema_version",
    "execution_config_sha256",
    "generation_seed",
    "seed_control_status",
    "run_status",
    "run_order_index",
    "started_at",
    "completed_at",
    "session_identity_sha256",
    "execution_identity_sha256",
    "record_type",
    "case_spec_sha256",
    "prompt_sha256",
    "evidence_path",
    "evidence_sha256",
}
TRIGGER_OUTCOME_FIELDS = {
    "predicted_trigger",
    "routing_protocol_id",
    "routing_protocol_sha256",
    "routing_extractor",
    "scored_at",
    "judgment_path",
    "judgment_sha256",
}
BEHAVIORAL_OUTCOME_FIELDS = {
    "assertion_scores",
    "rubric_sha256",
    "judge_protocol_id",
    "judge_protocol_sha256",
    "judge",
    "scored_at",
    "judgment_path",
    "judgment_sha256",
}

EXECUTION_IDENTITY_FIELDS = (
    "manifest_sha256",
    "suite_id",
    "comparison_block_id",
    "run_batch_id",
    "condition_id",
    "skill_release",
    "skill_package_sha256",
    "case_id",
    "replicate",
    "attempt",
    "agent",
    "model",
    "runtime",
    "execution_config_sha256",
    "generation_seed",
    "seed_control_status",
    "run_status",
    "run_order_index",
    "started_at",
    "completed_at",
    "session_identity_sha256",
    "record_type",
)


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_hash(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _execution_identity_hash(record: Mapping[str, Any]) -> str:
    return _canonical_hash(
        {field: record.get(field) for field in EXECUTION_IDENTITY_FIELDS}
    )


def _mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return sum(items) / len(items) if items else None


def _variance(values: Sequence[float]) -> float | None:
    if len(values) < 2:
        return None
    center = sum(values) / len(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def _ratio(numerator: int | float, denominator: int | float) -> float | None:
    return numerator / denominator if denominator else None


def _percentile(values: Sequence[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _interval(values: Sequence[float], confidence: float) -> list[float] | None:
    if not values:
        return None
    tail = (1 - confidence) / 2
    low = _percentile(values, tail)
    high = _percentile(values, 1 - tail)
    return [low, high] if low is not None and high is not None else None


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value!r} is not permitted")


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r} is not permitted")
        value[key] = item
    return value


def _stable_file_bytes(
    path: Path,
    label: str,
    *,
    maximum_bytes: int = 128 * 1024 * 1024,
) -> bytes:
    """Read one regular-file snapshot without following a final symlink."""

    try:
        initial = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot inspect {label}") from exc
    if stat.S_ISLNK(initial.st_mode) or not stat.S_ISREG(initial.st_mode):
        raise ValueError(f"{label} must be a regular, nonsymlink file")
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"{label} must be a regular file")
        if (initial.st_dev, initial.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError(f"{label} changed during verification")
        if before.st_size > maximum_bytes:
            raise ValueError(f"{label} exceeds the size limit")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, maximum_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum_bytes:
                raise ValueError(f"{label} exceeds the size limit")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if identity_before != identity_after or total != after.st_size:
        raise ValueError(f"{label} changed during verification")
    try:
        path_state = path.lstat()
    except OSError as exc:
        raise ValueError(f"{label} changed during verification") from exc
    if stat.S_ISLNK(path_state.st_mode) or (
        path_state.st_dev,
        path_state.st_ino,
        path_state.st_size,
        path_state.st_mtime_ns,
    ) != identity_after:
        raise ValueError(f"{label} changed during verification")
    return b"".join(chunks)


def _json_from_bytes(payload: bytes, label: str) -> Any:
    try:
        return json.loads(
            payload.decode("utf-8"),
            parse_constant=_reject_nonfinite_json_constant,
            object_pairs_hook=_reject_duplicate_object_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"cannot parse {label} as JSON: {exc}") from exc


def _load_json(path: Path) -> Any:
    return _json_from_bytes(_stable_file_bytes(path, "JSON artifact"), "JSON artifact")


def _jsonl_from_bytes(payload: bytes, label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"cannot decode {label} as UTF-8") from exc
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(
                line,
                parse_constant=_reject_nonfinite_json_constant,
                object_pairs_hook=_reject_duplicate_object_keys,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"line {line_number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"line {line_number}: record must be an object")
        records.append(value)
    return records


def _load_jsonl_with_hash(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = _stable_file_bytes(path, "benchmark records")
    return _jsonl_from_bytes(payload, "benchmark records"), _sha256_bytes(payload)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records, _digest = _load_jsonl_with_hash(path)
    return records


def _safe_relative_file(root: Path, value: Any, label: str) -> Path:
    if root.is_symlink():
        raise ValueError(f"{label} root cannot be a symbolic link")
    resolved_root = root.resolve()
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is missing")
    relative = Path(value)
    if "\\" in value or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} must be a contained relative path")
    cursor = resolved_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"{label} cannot traverse a symbolic link")
    path = (resolved_root / relative).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes its root") from exc
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {relative}")
    return path


def _normalized_relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string path")
    text = value
    relative = Path(text)
    if (
        not text.strip()
        or "\\" in text
        or relative.is_absolute()
        or ".." in relative.parts
        or relative.as_posix() != text
    ):
        raise ValueError(f"{label} must be a canonical contained relative path")
    return relative.as_posix()


def _evidence_tree_snapshot(
    root: Path,
) -> tuple[str, dict[str, str], dict[str, str]]:
    """Hash every regular file and reject links, special files, and hidden orphans."""

    if root.is_symlink() or not root.is_dir():
        raise ValueError("evidence root must be a regular, nonsymlink directory")
    resolved_root = root.resolve()
    entries: dict[str, str] = {}
    path_issues: dict[str, str] = {}
    file_count = 0
    total_bytes = 0
    for current, directory_names, file_names in os.walk(
        resolved_root, topdown=True, followlinks=False
    ):
        current_path = Path(current)
        for directory_name in list(directory_names):
            directory_path = current_path / directory_name
            if directory_path.is_symlink() or not directory_path.is_dir():
                relative = directory_path.relative_to(resolved_root).as_posix()
                path_issues[relative] = (
                    "evidence tree contains a linked or special directory"
                )
                directory_names.remove(directory_name)
        for file_name in file_names:
            file_path = current_path / file_name
            relative = file_path.relative_to(resolved_root).as_posix()
            try:
                state = file_path.lstat()
            except OSError:
                path_issues[relative] = "evidence tree entry cannot be inspected"
                continue
            if stat.S_ISLNK(state.st_mode) or not stat.S_ISREG(state.st_mode):
                path_issues[relative] = (
                    "evidence tree contains a linked or special file"
                )
                continue
            try:
                payload = _stable_file_bytes(
                    file_path,
                    f"evidence tree file {relative}",
                    maximum_bytes=64 * 1024 * 1024,
                )
            except ValueError as exc:
                path_issues[relative] = str(exc)
                continue
            file_count += 1
            total_bytes += len(payload)
            if file_count > 100_000:
                raise ValueError("evidence tree exceeds the file-count limit")
            if total_bytes > 2 * 1024 * 1024 * 1024:
                raise ValueError("evidence tree exceeds the total-size limit")
            entries[relative] = _sha256_bytes(payload)
    digest = hashlib.sha256()
    digest.update(b"scientific-autoresearch-evidence-tree-v1\0")
    for relative, content_hash in sorted(entries.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(content_hash.removeprefix("sha256:")))
    for relative, message in sorted(path_issues.items()):
        digest.update(b"issue\0")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(message.encode("utf-8"))
    return "sha256:" + digest.hexdigest(), entries, path_issues


def _evidence_reference_claims(
    records: Sequence[Mapping[str, Any]],
    protocol: Mapping[str, Any],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[tuple[str, str], list[str]],
    list[str],
]:
    """Classify evidence bindings by their owning frozen comparison block."""

    claims: dict[str, list[dict[str, Any]]] = defaultdict(list)
    block_errors: dict[tuple[str, str], list[str]] = defaultdict(list)
    fatal_errors: list[str] = []

    def report(owner: tuple[str, str] | None, message: str) -> None:
        if owner is None:
            fatal_errors.append(message)
        else:
            block_errors[owner].append(message)

    for index, record in enumerate(records, start=1):
        suite_id = str(record.get("suite_id", ""))
        block_id = str(record.get("comparison_block_id", ""))
        suite = protocol["suites"].get(suite_id)
        owner = (
            (suite_id, block_id)
            if suite is not None
            and block_id in suite.get("comparison_blocks_by_id", {})
            else None
        )
        references = [("evidence", "evidence_path", "evidence_sha256")]
        if (
            record.get("run_status") == "completed"
            or "judgment_path" in record
            or "judgment_sha256" in record
        ):
            references.append(("judgment", "judgment_path", "judgment_sha256"))
        for kind, path_field, hash_field in references:
            try:
                relative = _normalized_relative_path(
                    record.get(path_field), f"record {index} {kind} path"
                )
            except ValueError as exc:
                report(owner, str(exc))
                continue
            try:
                digest: str | None = _hash_field(
                    record.get(hash_field), f"record {index} {kind} hash"
                )
            except ValueError as exc:
                report(owner, str(exc))
                digest = None
            claims[relative].append(
                {
                    "record_index": index,
                    "kind": kind,
                    "owner": owner,
                    "digest": digest,
                }
            )

    for relative, path_claims in claims.items():
        if len(path_claims) < 2:
            continue
        records_text = ", ".join(
            str(claim["record_index"]) for claim in path_claims
        )
        message = (
            f"evidence path {relative!r} is reused by records {records_text}"
        )
        owners = {claim["owner"] for claim in path_claims}
        if None in owners:
            fatal_errors.append(message)
        for owner in owners - {None}:
            block_errors[owner].append(message)
    return claims, block_errors, fatal_errors


def _hash_field(value: Any, label: str) -> str:
    text = str(value or "").strip().lower()
    match = HASH_RE.fullmatch(text)
    if not match:
        raise ValueError(f"{label} must use SHA-256")
    return "sha256:" + match.group(1)


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _require_exact_keys(
    value: Mapping[str, Any],
    expected: set[str],
    label: str,
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(str(item) for item in actual - expected)
        details = []
        if missing:
            details.append(f"missing={missing}")
        if unknown:
            details.append(f"unknown={unknown}")
        raise ValueError(f"{label} must use the closed schema ({', '.join(details)})")


def _parse_timestamp(value: Any, label: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is missing")
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a UTC offset")
    return parsed


def _balanced_condition_orders(
    condition_ids: Sequence[str],
    expected_pairs: Iterable[tuple[str, int]],
    seed: int,
) -> dict[tuple[str, int], list[str]]:
    base = list(condition_ids)
    random.Random(seed).shuffle(base)
    return {
        pair: base[index % len(base) :] + base[: index % len(base)]
        for index, pair in enumerate(sorted(expected_pairs))
    }


def _verify_evidence(
    root: Path,
    path_value: Any,
    hash_value: Any,
    label: str,
) -> tuple[Path, str, bytes]:
    path = _safe_relative_file(root, path_value, label)
    expected = _hash_field(hash_value, f"{label} hash")
    payload = _stable_file_bytes(path, label, maximum_bytes=64 * 1024 * 1024)
    actual = _sha256_bytes(payload)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 mismatch")
    return path, actual, payload


def _load_bound_json_artifact(
    repository_root: Path,
    reference: Any,
    label: str,
    schema_field: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    if not isinstance(reference, Mapping):
        raise ValueError(f"{label} reference must be an object")
    _require_exact_keys(
        reference,
        {"path", "sha256", "schema_version"},
        f"{label} reference",
    )
    for field in ("path", "sha256", "schema_version"):
        if reference.get(field) in (None, ""):
            raise ValueError(f"{label} reference is missing {field}")
    path = _safe_relative_file(repository_root, reference.get("path"), f"{label}.path")
    expected = _hash_field(reference.get("sha256"), f"{label}.sha256")
    payload = _stable_file_bytes(path, label, maximum_bytes=16 * 1024 * 1024)
    actual = _sha256_bytes(payload)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 mismatch")
    value = _json_from_bytes(payload, label)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    schema_version = str(reference.get("schema_version"))
    if value.get(schema_field) != schema_version:
        raise ValueError(f"{label} schema version mismatch")
    return value, {
        "path": str(reference.get("path")),
        "sha256": expected,
        "schema_version": schema_version,
    }


def _behavior_package_digest_from_zip_bytes(payload: bytes) -> str:
    """Recompute the installable behavior-package digest from one ZIP snapshot."""

    files: dict[str, bytes] = {}
    normalized_names: set[str] = set()
    total_uncompressed = 0
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            members = archive.infolist()
            if len(members) > 4096:
                raise ValueError("behavior package exceeds the member-count limit")
            for info in members:
                name = info.filename
                if not name or "\\" in name:
                    raise ValueError("behavior package contains an invalid member path")
                relative = PurePosixPath(name)
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("behavior package contains an unsafe member path")
                mode = info.external_attr >> 16
                file_type = stat.S_IFMT(mode)
                if file_type == stat.S_IFLNK:
                    raise ValueError("behavior package cannot contain symbolic links")
                if info.is_dir():
                    raise ValueError("behavior package cannot contain explicit directory members")
                normalized_name = relative.as_posix()
                if name != normalized_name:
                    raise ValueError("behavior package contains a noncanonical member path")
                if unicodedata.normalize("NFC", normalized_name) != normalized_name:
                    raise ValueError("behavior package contains a noncanonical Unicode path")
                # Package artifacts may be extracted on case-insensitive filesystems.
                # Reject names that cannot coexist portably before computing identity.
                collision_key = normalized_name.casefold()
                if collision_key in normalized_names:
                    raise ValueError("behavior package contains colliding member paths")
                normalized_names.add(collision_key)
                if file_type not in {0, stat.S_IFREG}:
                    raise ValueError("behavior package cannot contain special files")
                if info.flag_bits & 0x1:
                    raise ValueError("behavior package cannot contain encrypted members")
                if name in files:
                    raise ValueError("behavior package contains duplicate members")
                if info.file_size > 16 * 1024 * 1024:
                    raise ValueError("behavior package member exceeds the size limit")
                total_uncompressed += info.file_size
                if total_uncompressed > 128 * 1024 * 1024:
                    raise ValueError("behavior package exceeds the uncompressed size limit")
                files[name] = archive.read(info)
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError(f"cannot read behavior package ZIP: {exc}") from exc

    def allowed(name: str) -> bool:
        relative = PurePosixPath(name)
        if name == "SKILL.md":
            return True
        if len(relative.parts) != 2:
            return False
        directory, filename = relative.parts
        return (
            (directory == "references" and filename.endswith(".md"))
            or (directory == "scripts" and filename.endswith(".py"))
            or (directory == "evals" and filename.endswith(".json"))
        )

    unknown = sorted(name for name in files if not allowed(name))
    if unknown:
        raise ValueError(
            f"behavior package contains non-behavior members: {unknown[:5]}"
        )
    required_groups = {
        "SKILL.md": any(name == "SKILL.md" for name in files),
        "references/*.md": any(
            name.startswith("references/") and name.endswith(".md") for name in files
        ),
        "scripts/*.py": any(
            name.startswith("scripts/") and name.endswith(".py") for name in files
        ),
        "evals/*.json": any(
            name.startswith("evals/") and name.endswith(".json") for name in files
        ),
    }
    missing = sorted(label for label, present in required_groups.items() if not present)
    if missing:
        raise ValueError(f"behavior package is missing required members: {missing}")

    digest = hashlib.sha256()
    digest.update(PACKAGE_DIGEST_PROFILE.encode("utf-8") + b"\0")
    for name in sorted(files):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(files[name]).digest())
    return "sha256:" + digest.hexdigest()


def _behavior_package_digest_from_zip(path: Path) -> str:
    payload = _stable_file_bytes(
        path,
        "behavior package ZIP",
        maximum_bytes=128 * 1024 * 1024,
    )
    return _behavior_package_digest_from_zip_bytes(payload)


def _load_assurance_attestation(
    repository_root: Path,
    reference: Any,
    label: str,
    *,
    subject_kind: str,
    subject_id: str,
    expected_immutable_reference: str | None,
    not_after: datetime | None,
) -> tuple[dict[str, Any], dict[str, str]]:
    attestation, ref = _load_bound_json_artifact(
        repository_root,
        reference,
        label,
        "assurance_attestation_schema_version",
    )
    _require_exact_keys(
        attestation,
        {
            "assurance_attestation_schema_version",
            "attestation_id",
            "subject_kind",
            "subject_id",
            "immutable_reference",
            "statement",
            "issued_by",
            "issued_at",
        },
        label,
    )
    for field in (
        "attestation_id",
        "subject_kind",
        "subject_id",
        "immutable_reference",
        "statement",
        "issued_by",
        "issued_at",
    ):
        if not isinstance(attestation.get(field), str) or not attestation[field].strip():
            raise ValueError(f"{label} has invalid {field}")
    if attestation["subject_kind"] != subject_kind:
        raise ValueError(f"{label} subject_kind mismatch")
    if attestation["subject_id"] != subject_id:
        raise ValueError(f"{label} subject_id mismatch")
    immutable_reference = _hash_field(
        attestation["immutable_reference"], f"{label}.immutable_reference"
    )
    if (
        expected_immutable_reference is not None
        and immutable_reference
        != _hash_field(expected_immutable_reference, f"{label} expected reference")
    ):
        raise ValueError(f"{label} immutable_reference mismatch")
    issued_at = _parse_timestamp(attestation["issued_at"], f"{label}.issued_at")
    if not_after is not None and issued_at > not_after:
        raise ValueError(f"{label} was issued after the execution freeze")
    attestation["immutable_reference"] = immutable_reference
    return attestation, ref


def _validate_material_assurance(
    repository_root: Path,
    raw: Any,
    label: str,
    *,
    subject_kind: str,
    subject_id: str,
    expected_package_digest: str | None = None,
    attestation_not_after: datetime | None = None,
    allow_not_applicable: bool = False,
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label} must be an object")
    _require_exact_keys(raw, {"mode", "artifact", "attestation_artifact"}, label)
    mode = raw.get("mode")
    if mode not in ASSURANCE_MODES:
        raise ValueError(f"{label} has invalid mode")
    artifact = raw.get("artifact")
    attestation_ref = raw.get("attestation_artifact")

    if mode == "not_applicable":
        if not allow_not_applicable or artifact is not None or attestation_ref is not None:
            raise ValueError(f"{label} cannot use not_applicable")
        return {
            "mode": "not_applicable",
            "artifact": None,
            "attestation_artifact": None,
            "verified_content_sha256": None,
        }

    if mode == "artifact_verified":
        if attestation_ref is not None or not isinstance(artifact, Mapping):
            raise ValueError(f"{label} artifact_verified needs only an artifact")
        _require_exact_keys(artifact, {"path", "sha256", "format"}, f"{label}.artifact")
        for field in ("path", "sha256", "format"):
            if artifact.get(field) in (None, ""):
                raise ValueError(f"{label}.artifact is missing {field}")
        path = _safe_relative_file(
            repository_root, artifact.get("path"), f"{label}.artifact.path"
        )
        expected_raw_hash = _hash_field(
            artifact.get("sha256"), f"{label}.artifact.sha256"
        )
        payload = _stable_file_bytes(
            path,
            f"{label} artifact",
            maximum_bytes=128 * 1024 * 1024,
        )
        actual_raw_hash = _sha256_bytes(payload)
        if actual_raw_hash != expected_raw_hash:
            raise ValueError(f"{label} artifact SHA-256 mismatch")
        artifact_format = str(artifact.get("format"))
        verified_content_sha256 = actual_raw_hash
        if subject_kind == "skill_package":
            if artifact_format != PACKAGE_ARTIFACT_FORMAT:
                raise ValueError(f"{label} has unsupported package artifact format")
            verified_content_sha256 = _behavior_package_digest_from_zip_bytes(payload)
            if expected_package_digest is None or verified_content_sha256 != _hash_field(
                expected_package_digest, f"{label} expected package digest"
            ):
                raise ValueError(f"{label} package content digest mismatch")
        elif artifact_format not in HARNESS_ARTIFACT_FORMATS:
            raise ValueError(f"{label} has unsupported harness artifact format")
        return {
            "mode": "artifact_verified",
            "artifact": {
                "path": str(artifact.get("path")),
                "sha256": expected_raw_hash,
                "format": artifact_format,
            },
            "attestation_artifact": None,
            "verified_content_sha256": verified_content_sha256,
        }

    if artifact is not None or not isinstance(attestation_ref, Mapping):
        raise ValueError(f"{label} attested needs only an attestation artifact")
    _attestation, normalized_ref = _load_assurance_attestation(
        repository_root,
        attestation_ref,
        f"{label}.attestation",
        subject_kind=subject_kind,
        subject_id=subject_id,
        expected_immutable_reference=(
            expected_package_digest if subject_kind == "skill_package" else None
        ),
        not_after=attestation_not_after,
    )
    return {
        "mode": "attested",
        "artifact": None,
        "attestation_artifact": normalized_ref,
        "verified_content_sha256": None,
    }


def _validate_interval_rule(suite: Mapping[str, Any], suite_id: str) -> None:
    rule = suite.get("interval_rule")
    if not isinstance(rule, Mapping):
        raise ValueError(f"suite {suite_id} needs interval_rule")
    _require_exact_keys(
        rule,
        {"method", "bootstrap_unit", "draws", "seed", "confidence"},
        f"suite {suite_id} interval_rule",
    )
    expected = (
        "paired_stratified_case_cluster_bootstrap"
        if suite.get("record_type") == "trigger"
        else "paired_case_cluster_bootstrap"
    )
    if rule.get("method") != expected:
        raise ValueError(f"suite {suite_id} interval method must be {expected}")
    draws = rule.get("draws")
    seed = rule.get("seed")
    confidence = rule.get("confidence")
    if not isinstance(draws, int) or isinstance(draws, bool) or draws < 1:
        raise ValueError(f"suite {suite_id} interval draws must be positive")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError(f"suite {suite_id} interval seed must be an integer")
    if not _finite_number(confidence) or not 0 < float(confidence) < 1:
        raise ValueError(f"suite {suite_id} interval confidence must be in (0,1)")
    if rule.get("bootstrap_unit") != "case":
        raise ValueError(f"suite {suite_id} bootstrap_unit must be case")


def _validate_failure_policy(suite: Mapping[str, Any], suite_id: str) -> None:
    policy = suite.get("failure_retry_policy")
    if not isinstance(policy, Mapping):
        raise ValueError(f"suite {suite_id} needs failure_retry_policy")
    _require_exact_keys(
        policy,
        {
            "maximum_infrastructure_retries",
            "retry_eligible_statuses",
            "retain_all_attempts",
            "scoring_attempt_selection_rule",
            "agent_failure_scoring",
        },
        f"suite {suite_id} failure_retry_policy",
    )
    retries = policy.get("maximum_infrastructure_retries")
    if not isinstance(retries, int) or isinstance(retries, bool) or retries < 0:
        raise ValueError(f"suite {suite_id} has invalid retry limit")
    retry_statuses = policy.get("retry_eligible_statuses")
    if (
        not isinstance(retry_statuses, list)
        or any(not isinstance(item, str) for item in retry_statuses)
        or len(retry_statuses) != len(set(retry_statuses))
        or not set(retry_statuses) <= INFRASTRUCTURE_FAILURE_STATUSES
    ):
        raise ValueError(f"suite {suite_id} has invalid retry statuses")
    if policy.get("retain_all_attempts") is not True:
        raise ValueError(f"suite {suite_id} must retain all attempts")
    if policy.get("scoring_attempt_selection_rule") != "first_non_retry_eligible_attempt":
        raise ValueError(f"suite {suite_id} has unsupported attempt selection")
    if policy.get("agent_failure_scoring") != "zero_credit":
        raise ValueError(f"suite {suite_id} must score Agent failures as zero credit")
    if suite.get("missing_run_policy") != "comparison_incomplete_no_paired_delta":
        raise ValueError(f"suite {suite_id} has unsupported missing-run policy")


def _immutable_protocol_projection(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Project only design-bearing fields shared by a template and execution."""

    suites_raw = raw.get("suites")
    if not isinstance(suites_raw, list):
        raise ValueError("benchmark manifest must define suites before projection")
    suites: list[dict[str, Any]] = []
    for index, suite in enumerate(suites_raw, start=1):
        if not isinstance(suite, Mapping):
            raise ValueError(f"suite {index} must be an object before projection")
        suites.append(
            {
                key: value
                for key, value in suite.items()
                if key not in {"protocol_status", "comparison_blocks"}
            }
        )
    return {
        "protocol_projection_profile": raw.get("protocol_projection_profile"),
        "benchmark_schema_version": raw.get("benchmark_schema_version"),
        "benchmark_protocol_version": raw.get("benchmark_protocol_version"),
        "protocol_id": raw.get("protocol_id"),
        "protocol_scope": raw.get("protocol_scope"),
        "release_under_test": raw.get("release_under_test"),
        "record_schema_version": raw.get("record_schema_version"),
        "evaluation_state_vocabulary": raw.get("evaluation_state_vocabulary"),
        "suites": suites,
        "result_policy": raw.get("result_policy"),
        "sealed_suite_policy": raw.get("sealed_suite_policy"),
        "protocol_invalidation_policy": raw.get("protocol_invalidation_policy"),
    }


def _validate_required_design(
    suite: dict[str, Any],
    conditions: Mapping[str, Mapping[str, Any]],
) -> None:
    """Freeze the full condition family and all planned contrasts for a suite."""

    suite_id = str(suite["suite_id"])
    if suite.get("scoring_backend") == "external":
        if suite.get("required_condition_ids") is not None or suite.get(
            "required_contrasts"
        ) is not None:
            raise ValueError(
                f"external draft suite {suite_id} cannot claim a frozen comparison family"
            )
        return

    required_ids = suite.get("required_condition_ids")
    if (
        not isinstance(required_ids, list)
        or any(not isinstance(item, str) or not item.strip() for item in required_ids)
        or len(required_ids) != len(set(required_ids))
        or required_ids != list(conditions)
    ):
        raise ValueError(
            f"suite {suite_id} required_condition_ids must exactly match all conditions"
        )
    target = conditions.get(TARGET_CONDITION_ID)
    if target is None or target.get("skill_release") != RELEASE_UNDER_TEST:
        raise ValueError(
            f"suite {suite_id} target condition does not match release_under_test"
        )
    required_raw = suite.get("required_contrasts")
    if not isinstance(required_raw, list) or not required_raw:
        raise ValueError(f"suite {suite_id} must freeze required_contrasts")
    normalized: list[dict[str, str]] = []
    contrast_ids: set[str] = set()
    references: list[str] = []
    for item in required_raw:
        if not isinstance(item, Mapping):
            raise ValueError(f"suite {suite_id} has an invalid required contrast")
        _require_exact_keys(
            item,
            {"contrast_id", "target_condition_id", "reference_condition_id"},
            f"suite {suite_id} required contrast",
        )
        if any(
            not isinstance(item.get(field), str) or not item[field].strip()
            for field in (
                "contrast_id",
                "target_condition_id",
                "reference_condition_id",
            )
        ):
            raise ValueError(f"suite {suite_id} has an invalid required contrast")
        contrast_id = str(item["contrast_id"]).strip()
        target_id = str(item["target_condition_id"]).strip()
        reference_id = str(item["reference_condition_id"]).strip()
        if (
            contrast_id in contrast_ids
            or target_id != TARGET_CONDITION_ID
            or reference_id == TARGET_CONDITION_ID
            or reference_id not in conditions
            or contrast_id != f"{TARGET_CONDITION_ID}-minus-{reference_id}"
        ):
            raise ValueError(f"suite {suite_id} has an invalid required contrast")
        contrast_ids.add(contrast_id)
        references.append(reference_id)
        normalized.append(
            {
                "contrast_id": contrast_id,
                "target_condition_id": target_id,
                "reference_condition_id": reference_id,
            }
        )
    if references != [item for item in required_ids if item != TARGET_CONDITION_ID]:
        raise ValueError(
            f"suite {suite_id} required contrasts must cover every comparator in order"
        )
    suite["required_condition_ids"] = list(required_ids)
    suite["required_contrasts"] = normalized


def _load_case_registry(
    repository_root: Path,
    suite: dict[str, Any],
    suite_id: str,
) -> None:
    source = suite.get("case_source")
    if not isinstance(source, Mapping):
        raise ValueError(f"suite {suite_id} needs case_source")
    _require_exact_keys(
        source,
        {
            "path",
            "sha256",
            "collection_key",
            "case_id_field",
            "prompt_field",
            "role",
        },
        f"suite {suite_id} case_source",
    )
    if source.get("collection_key") is not None and (
        not isinstance(source.get("collection_key"), str)
        or not source["collection_key"].strip()
    ):
        raise ValueError(f"suite {suite_id} has invalid collection_key")
    for field in ("case_id_field", "prompt_field"):
        if not isinstance(source.get(field), str) or not source[field].strip():
            raise ValueError(f"suite {suite_id} has invalid {field}")
    source_path = _safe_relative_file(
        repository_root, source.get("path"), f"suite {suite_id} case source"
    )
    expected_hash = _hash_field(source.get("sha256"), f"suite {suite_id} case hash")
    source_payload = _stable_file_bytes(
        source_path,
        f"suite {suite_id} case source",
        maximum_bytes=16 * 1024 * 1024,
    )
    if _sha256_bytes(source_payload) != expected_hash:
        raise ValueError(f"suite {suite_id} case source SHA-256 mismatch")
    source_data = _json_from_bytes(source_payload, f"suite {suite_id} case source")
    collection_key = source.get("collection_key")
    role = source.get("role")
    if role not in {"shakedown", "development", "sealed"}:
        raise ValueError(f"suite {suite_id} case source has invalid role")
    if role == "sealed":
        raise ValueError(
            f"suite {suite_id} uses sealed cases, which require a successor scorer with an implemented commitment schema"
        )
    if collection_key:
        if not isinstance(source_data, Mapping):
            raise ValueError(
                f"suite {suite_id} case source must be an object when collection_key is set"
            )
        cases_raw = source_data.get(collection_key)
    else:
        cases_raw = source_data
    if not isinstance(cases_raw, list) or not cases_raw:
        raise ValueError(f"suite {suite_id} case source must resolve to a list")
    id_field = str(source.get("case_id_field", "id"))
    prompt_field = str(source.get("prompt_field", "prompt"))
    cases: dict[str, dict[str, Any]] = {}
    for case_index, case_raw in enumerate(cases_raw, start=1):
        if not isinstance(case_raw, dict):
            raise ValueError(f"suite {suite_id} case {case_index} must be an object")
        case_id = str(case_raw.get(id_field, "")).strip()
        if not case_id or case_id in cases:
            raise ValueError(f"suite {suite_id} has a missing or duplicate case ID")
        prompt = case_raw.get(prompt_field)
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"suite {suite_id} case {case_id} has no prompt")
        case = dict(case_raw)
        case["case_id"] = case_id
        case["case_spec_sha256"] = _canonical_hash(case_raw)
        case["prompt_sha256"] = _sha256_bytes(prompt.encode("utf-8"))
        if suite.get("record_type") == "trigger":
            if not isinstance(case_raw.get("should_trigger"), bool):
                raise ValueError(f"trigger case {case_id} lacks Boolean truth")
        elif suite.get("record_type") == "behavioral":
            assertions = case_raw.get("assertions")
            assertion_ids = case_raw.get("assertion_ids")
            critical_ids = case_raw.get("critical_assertion_ids")
            if (
                not isinstance(assertions, list)
                or not assertions
                or any(not isinstance(item, str) or not item.strip() for item in assertions)
            ):
                raise ValueError(f"behavioral case {case_id} has no assertions")
            if (
                not isinstance(assertion_ids, list)
                or any(
                    not isinstance(item, str) or not item.strip()
                    for item in assertion_ids
                )
                or len(assertion_ids) != len(assertions)
                or len(set(assertion_ids)) != len(assertion_ids)
            ):
                raise ValueError(f"behavioral case {case_id} has invalid assertion IDs")
            if (
                not isinstance(critical_ids, list)
                or not critical_ids
                or any(
                    not isinstance(item, str) or not item.strip()
                    for item in critical_ids
                )
                or len(set(critical_ids)) != len(critical_ids)
                or not set(critical_ids) <= set(assertion_ids)
            ):
                raise ValueError(f"behavioral case {case_id} has invalid critical IDs")
            case["rubric_sha256"] = _canonical_hash(
                {
                    "assertions": assertions,
                    "assertion_ids": assertion_ids,
                    "critical_assertion_ids": critical_ids,
                }
            )
        else:
            raise ValueError(f"suite {suite_id} has unsupported record_type")
        cases[case_id] = case
    if suite.get("record_type") == "trigger":
        label_counts = Counter(
            bool(case["should_trigger"]) for case in cases.values()
        )
        if set(label_counts) != {False, True} or any(
            label_counts[label] < 2 for label in (False, True)
        ):
            raise ValueError(
                f"trigger suite {suite_id} needs at least two cases in each truth class for stratified case-cluster uncertainty"
            )
    elif len(cases) < 2:
        raise ValueError(
            f"behavioral suite {suite_id} needs at least two cases for case-cluster uncertainty"
        )
    suite["cases_by_id"] = cases


def _validate_comparison_block(
    suite: Mapping[str, Any],
    raw: Any,
    repository_root: Path,
    attestation_not_after: datetime | None,
) -> dict[str, Any]:
    suite_id = str(suite["suite_id"])
    if not isinstance(raw, Mapping):
        raise ValueError(f"suite {suite_id} comparison block must be an object")
    _require_exact_keys(
        raw,
        COMPARISON_BLOCK_FIELDS,
        f"suite {suite_id} comparison block",
    )
    block = dict(raw)
    block_id = str(block.get("comparison_block_id", "")).strip()
    if not block_id:
        raise ValueError(f"suite {suite_id} comparison block lacks an ID")
    if block.get("protocol_status") != "frozen":
        raise ValueError(f"comparison block {block_id} must be frozen")
    run_batch_id = str(block.get("run_batch_id", "")).strip()
    if not run_batch_id:
        raise ValueError(f"comparison block {block_id} lacks run_batch_id")
    condition_ids = block.get("condition_ids")
    required_condition_ids = suite.get("required_condition_ids")
    if (
        not isinstance(condition_ids, list)
        or any(not isinstance(item, str) or not item.strip() for item in condition_ids)
        or len(condition_ids) != len(set(condition_ids))
        or condition_ids != required_condition_ids
    ):
        raise ValueError(
            f"comparison block {block_id} must use the full required condition family"
        )
    contrasts_raw = block.get("contrasts")
    if not isinstance(contrasts_raw, list) or not contrasts_raw:
        raise ValueError(f"comparison block {block_id} needs contrasts")
    contrasts: list[dict[str, str]] = []
    contrast_ids: set[str] = set()
    for item in contrasts_raw:
        if not isinstance(item, Mapping):
            raise ValueError(f"comparison block {block_id} has invalid contrast")
        _require_exact_keys(
            item,
            {"contrast_id", "target_condition_id", "reference_condition_id"},
            f"comparison block {block_id} contrast",
        )
        if any(
            not isinstance(item.get(field), str) or not item[field].strip()
            for field in (
                "contrast_id",
                "target_condition_id",
                "reference_condition_id",
            )
        ):
            raise ValueError(f"comparison block {block_id} has invalid contrast")
        contrast_id = str(item.get("contrast_id", "")).strip()
        target = str(item.get("target_condition_id", "")).strip()
        reference = str(item.get("reference_condition_id", "")).strip()
        if (
            not contrast_id
            or contrast_id in contrast_ids
            or target == reference
            or target not in condition_ids
            or reference not in condition_ids
        ):
            raise ValueError(f"comparison block {block_id} has invalid contrast")
        contrast_ids.add(contrast_id)
        contrasts.append(
            {
                "contrast_id": contrast_id,
                "target_condition_id": target,
                "reference_condition_id": reference,
            }
        )
    if contrasts != suite.get("required_contrasts"):
        raise ValueError(
            f"comparison block {block_id} must use every required contrast in order"
        )
    executor = block.get("executor_identity")
    if not isinstance(executor, Mapping):
        raise ValueError(f"comparison block {block_id} has invalid executor_identity")
    _require_exact_keys(
        executor,
        {"agent", "model", "runtime"},
        f"comparison block {block_id} executor_identity",
    )
    if any(
        not isinstance(executor.get(field), str) or not executor[field].strip()
        for field in ("agent", "model", "runtime")
    ):
        raise ValueError(f"comparison block {block_id} has invalid executor_identity")

    config, config_ref = _load_bound_json_artifact(
        repository_root,
        block.get("execution_config_artifact"),
        f"comparison block {block_id} execution config",
        "execution_config_schema_version",
    )
    allowed_config_fields = {
        "execution_config_schema_version",
        "shared_execution_config",
        "redactions",
    }
    if set(config) - allowed_config_fields:
        raise ValueError(
            f"comparison block {block_id} execution config contains condition-specific or unknown top-level fields"
        )
    shared = config.get("shared_execution_config")
    if not isinstance(shared, Mapping):
        raise ValueError(f"comparison block {block_id} lacks shared execution config")
    required_shared_fields = {
        "harness_identity",
        "generation_parameters",
        "tool_policy",
        "context_policy",
        "timeout_seconds",
        "isolated_sessions",
    }
    if set(shared) != required_shared_fields:
        raise ValueError(
            f"comparison block {block_id} shared execution config must use the closed schema"
        )
    for field in required_shared_fields:
        if shared.get(field) in (None, "", {}):
            raise ValueError(f"comparison block {block_id} shared config lacks {field}")
    harness_identity = shared.get("harness_identity")
    if (
        not isinstance(harness_identity, Mapping)
        or set(harness_identity) != {"id", "version", "assurance"}
        or any(
            not isinstance(harness_identity.get(field), str)
            or not harness_identity[field].strip()
            for field in ("id", "version")
        )
    ):
        raise ValueError(f"comparison block {block_id} has invalid harness identity")
    harness_assurance = _validate_material_assurance(
        repository_root,
        harness_identity.get("assurance"),
        f"comparison block {block_id} harness assurance",
        subject_kind="harness",
        subject_id=f"{harness_identity['id']}@{harness_identity['version']}",
        attestation_not_after=attestation_not_after,
    )
    if not _finite_number(shared.get("timeout_seconds")) or float(
        shared["timeout_seconds"]
    ) <= 0:
        raise ValueError(f"comparison block {block_id} has invalid timeout_seconds")

    forbidden_config_keys = {
        "condition",
        "conditions",
        "condition_id",
        "condition_ids",
        "condition_override",
        "condition_overrides",
        "per_condition",
        "skill_package",
        "skill_package_sha256",
        "skill_release",
    }
    normalized_condition_ids = {
        re.sub(r"[^a-z0-9]+", "_", str(item).lower()).strip("_")
        for item in condition_ids
    }

    def condition_specific_config_path(value: Any, path: str) -> str | None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                normalized_key = re.sub(
                    r"[^a-z0-9]+", "_", str(key).lower()
                ).strip("_")
                if (
                    normalized_key in forbidden_config_keys
                    or normalized_key in normalized_condition_ids
                    or normalized_key.startswith("condition_")
                    or normalized_key.endswith("_by_condition")
                    or normalized_key.startswith("per_condition")
                ):
                    return f"{path}.{key}"
                found = condition_specific_config_path(nested, f"{path}.{key}")
                if found:
                    return found
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                found = condition_specific_config_path(nested, f"{path}[{index}]")
                if found:
                    return found
        elif isinstance(value, str) and value in condition_ids:
            return path
        return None

    redactions = config.get("redactions", [])
    if (
        not isinstance(redactions, list)
        or any(not isinstance(item, str) or not item.strip() for item in redactions)
        or len(redactions) != len(set(redactions))
    ):
        raise ValueError(
            f"comparison block {block_id} redactions must be a unique list of annotation strings"
        )
    forbidden_path = condition_specific_config_path(shared, "shared_execution_config")
    if not forbidden_path:
        forbidden_path = condition_specific_config_path(redactions, "redactions")
    if forbidden_path:
        raise ValueError(
            f"comparison block {block_id} execution config contains a condition-specific branch at {forbidden_path}"
        )
    if shared.get("isolated_sessions") is not True:
        raise ValueError(f"comparison block {block_id} must use isolated sessions")
    if block.get("isolation_policy") != "fresh_context_per_attempt":
        raise ValueError(f"comparison block {block_id} has invalid isolation policy")

    seed_schedule, seed_ref = _load_bound_json_artifact(
        repository_root,
        block.get("seed_schedule_artifact"),
        f"comparison block {block_id} seed schedule",
        "seed_schedule_schema_version",
    )
    seed_status = str(block.get("seed_control_status", ""))
    if seed_status not in SEED_CONTROL_STATUSES:
        raise ValueError(f"comparison block {block_id} has invalid seed status")
    if (
        seed_schedule.get("comparison_block_id") != block_id
        or seed_schedule.get("seed_control_status") != seed_status
    ):
        raise ValueError(f"comparison block {block_id} seed schedule binding mismatch")
    _require_exact_keys(
        seed_schedule,
        {
            "seed_schedule_schema_version",
            "comparison_block_id",
            "seed_control_status",
            "assignments",
        },
        f"comparison block {block_id} seed schedule",
    )

    order_schedule, order_ref = _load_bound_json_artifact(
        repository_root,
        block.get("order_schedule_artifact"),
        f"comparison block {block_id} order schedule",
        "order_schedule_schema_version",
    )
    if order_schedule.get("comparison_block_id") != block_id:
        raise ValueError(f"comparison block {block_id} order schedule binding mismatch")
    _require_exact_keys(
        order_schedule,
        {
            "order_schedule_schema_version",
            "comparison_block_id",
            "generation_method",
            "order_generation_seed",
            "assignments",
        },
        f"comparison block {block_id} order schedule",
    )
    if order_schedule.get("generation_method") != "seeded_balanced_rotation_v1":
        raise ValueError(f"comparison block {block_id} has unsupported order generation")
    order_generation_seed = order_schedule.get("order_generation_seed")
    if not isinstance(order_generation_seed, int) or isinstance(
        order_generation_seed, bool
    ):
        raise ValueError(f"comparison block {block_id} needs an integer order seed")

    repetitions = int(suite["repetitions"])
    expected_pairs = {
        (case_id, replicate)
        for case_id in suite["cases_by_id"]
        for replicate in range(1, repetitions + 1)
    }
    seed_by_pair: dict[tuple[str, int], int | None] = {}
    assignments = seed_schedule.get("assignments")
    if not isinstance(assignments, list):
        raise ValueError(f"comparison block {block_id} seed assignments must be a list")
    for item in assignments:
        if not isinstance(item, Mapping):
            raise ValueError(f"comparison block {block_id} has invalid seed assignment")
        _require_exact_keys(
            item,
            {"case_id", "replicate", "generation_seed"},
            f"comparison block {block_id} seed assignment",
        )
        case_id = item.get("case_id")
        replicate = item.get("replicate")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"comparison block {block_id} has invalid seed case_id")
        if not isinstance(replicate, int) or isinstance(replicate, bool):
            raise ValueError(
                f"comparison block {block_id} seed assignment replicate must be an integer"
            )
        pair = (case_id, replicate)
        if pair in seed_by_pair:
            raise ValueError(f"comparison block {block_id} has duplicate seed assignment")
        seed = item.get("generation_seed")
        if seed_status in {"enforced", "requested_not_guaranteed"}:
            if not isinstance(seed, int) or isinstance(seed, bool):
                raise ValueError(f"comparison block {block_id} needs scheduled integer seeds")
        elif seed is not None:
            raise ValueError(f"comparison block {block_id} unavailable seeds must be null")
        seed_by_pair[pair] = seed
    if set(seed_by_pair) != expected_pairs:
        raise ValueError(f"comparison block {block_id} seed schedule is incomplete")

    order_by_pair: dict[tuple[str, int], list[str]] = {}
    order_assignments = order_schedule.get("assignments")
    if not isinstance(order_assignments, list):
        raise ValueError(f"comparison block {block_id} order assignments must be a list")
    for item in order_assignments:
        if not isinstance(item, Mapping):
            raise ValueError(f"comparison block {block_id} has invalid order assignment")
        _require_exact_keys(
            item,
            {"case_id", "replicate", "condition_order"},
            f"comparison block {block_id} order assignment",
        )
        case_id = item.get("case_id")
        replicate = item.get("replicate")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"comparison block {block_id} has invalid order case_id")
        if not isinstance(replicate, int) or isinstance(replicate, bool):
            raise ValueError(
                f"comparison block {block_id} order assignment replicate must be an integer"
            )
        pair = (case_id, replicate)
        order = item.get("condition_order")
        if pair in order_by_pair:
            raise ValueError(f"comparison block {block_id} has duplicate order assignment")
        if (
            not isinstance(order, list)
            or any(not isinstance(value, str) or not value.strip() for value in order)
            or len(order) != len(set(order))
        ):
            raise ValueError(f"comparison block {block_id} has invalid condition order")
        if set(order) != set(condition_ids) or len(order) != len(condition_ids):
            raise ValueError(f"comparison block {block_id} order omits a condition")
        order_by_pair[pair] = [str(value) for value in order]
    if set(order_by_pair) != expected_pairs:
        raise ValueError(f"comparison block {block_id} order schedule is incomplete")
    expected_orders = _balanced_condition_orders(
        [str(value) for value in condition_ids],
        expected_pairs,
        order_generation_seed,
    )
    if order_by_pair != expected_orders:
        raise ValueError(
            f"comparison block {block_id} order assignments do not match the frozen balanced generator"
        )

    routing_protocol: dict[str, Any] | None = None
    routing_ref: dict[str, str] | None = None
    judge_protocol: dict[str, Any] | None = None
    judge_ref: dict[str, str] | None = None
    if suite.get("record_type") == "trigger":
        routing_protocol, routing_ref = _load_bound_json_artifact(
            repository_root,
            block.get("routing_protocol_artifact"),
            f"comparison block {block_id} routing protocol",
            "routing_protocol_schema_version",
        )
        _require_exact_keys(
            routing_protocol,
            {
                "routing_protocol_schema_version",
                "routing_protocol_id",
                "extractor_identity",
                "decision_rule",
            },
            f"comparison block {block_id} routing protocol",
        )
        for field in (
            "routing_protocol_id",
            "extractor_identity",
            "decision_rule",
        ):
            if routing_protocol.get(field) in (None, "", {}):
                raise ValueError(
                    f"comparison block {block_id} routing protocol lacks {field}"
                )
        if not isinstance(routing_protocol.get("routing_protocol_id"), str) or not routing_protocol[
            "routing_protocol_id"
        ].strip():
            raise ValueError(
                f"comparison block {block_id} has invalid routing_protocol_id"
            )
        if not isinstance(routing_protocol.get("decision_rule"), str) or not routing_protocol[
            "decision_rule"
        ].strip():
            raise ValueError(f"comparison block {block_id} has invalid routing decision rule")
        extractor = routing_protocol.get("extractor_identity")
        if not isinstance(extractor, Mapping) or set(extractor) != {
            "kind",
            "id",
            "version",
        } or any(
            not isinstance(extractor.get(field), str) or not extractor[field].strip()
            for field in ("kind", "id", "version")
        ):
            raise ValueError(
                f"comparison block {block_id} has invalid routing extractor identity"
            )
        if block.get("judge_protocol_artifact") not in (None, {}):
            raise ValueError(f"trigger comparison block {block_id} cannot bind a judge")
    elif suite.get("record_type") == "behavioral":
        if block.get("routing_protocol_artifact") not in (None, {}):
            raise ValueError(
                f"behavioral comparison block {block_id} cannot bind a routing protocol"
            )
        judge_protocol, judge_ref = _load_bound_json_artifact(
            repository_root,
            block.get("judge_protocol_artifact"),
            f"comparison block {block_id} judge protocol",
            "judge_protocol_schema_version",
        )
        _require_exact_keys(
            judge_protocol,
            {
                "judge_protocol_schema_version",
                "judge_protocol_id",
                "judge_identity",
                "prompt_artifact",
                "rubric_version",
                "blinding",
                "adjudication_policy",
                "independent_judgments_per_output",
            },
            f"comparison block {block_id} judge protocol",
        )
        for field in (
            "judge_protocol_id",
            "judge_identity",
            "prompt_artifact",
            "rubric_version",
            "blinding",
            "adjudication_policy",
            "independent_judgments_per_output",
        ):
            if judge_protocol.get(field) in (None, "", {}):
                raise ValueError(f"comparison block {block_id} judge protocol lacks {field}")
        for field in (
            "judge_protocol_id",
            "rubric_version",
            "blinding",
            "adjudication_policy",
        ):
            if not isinstance(judge_protocol.get(field), str) or not judge_protocol[
                field
            ].strip():
                raise ValueError(
                    f"comparison block {block_id} judge protocol has invalid {field}"
                )
        judge_identity = judge_protocol.get("judge_identity")
        allowed_judge_identity_keys = {
            frozenset({"kind", "id", "version"}),
            frozenset({"kind", "id", "version", "panel_size"}),
        }
        if (
            not isinstance(judge_identity, Mapping)
            or frozenset(judge_identity) not in allowed_judge_identity_keys
            or any(
                not isinstance(judge_identity.get(field), str)
                or not judge_identity[field].strip()
                for field in ("kind", "id", "version")
            )
        ):
            raise ValueError(f"comparison block {block_id} has invalid judge identity")
        panel_size = judge_identity.get("panel_size", 1)
        if not isinstance(panel_size, int) or isinstance(panel_size, bool) or panel_size < 1:
            raise ValueError(f"comparison block {block_id} has invalid judge panel size")
        repeats = judge_protocol.get("independent_judgments_per_output")
        if repeats != 1 or isinstance(repeats, bool):
            raise ValueError(
                f"comparison block {block_id} record schema supports exactly one adjudicated judgment per output"
            )
        prompt_ref = judge_protocol.get("prompt_artifact")
        if not isinstance(prompt_ref, Mapping):
            raise ValueError(f"comparison block {block_id} has invalid judge prompt")
        _require_exact_keys(
            prompt_ref,
            {"path", "sha256"},
            f"comparison block {block_id} judge prompt",
        )
        prompt_path = _safe_relative_file(
            repository_root, prompt_ref.get("path"), f"comparison block {block_id} judge prompt"
        )
        if _sha256_file(prompt_path) != _hash_field(
            prompt_ref.get("sha256"), f"comparison block {block_id} judge prompt hash"
        ):
            raise ValueError(f"comparison block {block_id} judge prompt SHA-256 mismatch")

    evidence_status = str(block.get("evidence_status_on_complete", ""))
    if evidence_status not in EVIDENCE_STATUSES - {"empirical_method_evaluated"}:
        raise ValueError(f"comparison block {block_id} has invalid evidence status")
    role = str(suite.get("case_source", {}).get("role", ""))
    if role == "development" and evidence_status != "development_suite_evaluated":
        raise ValueError(f"comparison block {block_id} overstates development evidence")
    if role == "shakedown" and evidence_status != "not_evaluated":
        raise ValueError(f"comparison block {block_id} overstates shakedown evidence")
    if role == "sealed" and evidence_status == "development_suite_evaluated":
        raise ValueError(f"comparison block {block_id} understates sealed case role")
    max_window = block.get("max_pair_window_seconds")
    if (
        not _finite_number(max_window)
        or float(max_window) <= 0
    ):
        raise ValueError(f"comparison block {block_id} needs max_pair_window_seconds")

    block.update(
        {
            "comparison_block_id": block_id,
            "run_batch_id": run_batch_id,
            "condition_ids": [str(value) for value in condition_ids],
            "contrasts": contrasts,
            "executor_identity": dict(executor),
            "execution_config": config,
            "execution_config_ref": config_ref,
            "harness_assurance": harness_assurance,
            "seed_schedule_ref": seed_ref,
            "seed_by_pair": seed_by_pair,
            "order_schedule_ref": order_ref,
            "order_by_pair": order_by_pair,
            "routing_protocol": routing_protocol,
            "routing_protocol_ref": routing_ref,
            "judge_protocol": judge_protocol,
            "judge_protocol_ref": judge_ref,
            "expected_pairs": expected_pairs,
            "max_pair_window_seconds": float(max_window),
        }
    )
    return block


def _load_protocol(
    manifest_path: Path,
    artifact_root: Path | None = None,
    *,
    _manifest_payload: bytes | None = None,
) -> dict[str, Any]:
    if manifest_path.is_symlink():
        raise ValueError("benchmark manifest cannot be a symbolic link")
    manifest_path = manifest_path.resolve()
    manifest_payload = (
        _manifest_payload
        if _manifest_payload is not None
        else _stable_file_bytes(
            manifest_path,
            "benchmark manifest",
            maximum_bytes=16 * 1024 * 1024,
        )
    )
    raw = _json_from_bytes(manifest_payload, "benchmark manifest")
    if not isinstance(raw, dict):
        raise ValueError("benchmark manifest must be an object")
    _require_exact_keys(raw, MANIFEST_FIELDS, "benchmark manifest")
    if raw.get("benchmark_schema_version") != BENCHMARK_SCHEMA_VERSION:
        raise ValueError(
            f"score.py requires benchmark_schema_version={BENCHMARK_SCHEMA_VERSION}"
        )
    if raw.get("benchmark_protocol_version") != "2.1.2":
        raise ValueError("manifest must bind benchmark_protocol_version=2.1.2")
    if raw.get("record_schema_version") != RECORD_SCHEMA_VERSION:
        raise ValueError("manifest record schema does not match scorer")
    protocol_scope = raw.get("protocol_scope")
    if protocol_scope not in PROTOCOL_ID_BY_SCOPE:
        raise ValueError("manifest protocol_scope is not supported by protocol 2.1.2")
    if raw.get("protocol_id") != PROTOCOL_ID_BY_SCOPE[protocol_scope]:
        raise ValueError("manifest protocol_id does not match protocol_scope")
    if raw.get("release_under_test") != RELEASE_UNDER_TEST:
        raise ValueError("manifest release_under_test must be 0.2.8")
    if raw.get("protocol_projection_profile") != PROTOCOL_PROJECTION_PROFILE:
        raise ValueError("manifest protocol_projection_profile is not supported")
    for field, expected in (
        ("evaluation_state_vocabulary", EVALUATION_STATE_VOCABULARY),
        ("result_policy", RESULT_POLICY),
        ("sealed_suite_policy", SEALED_SUITE_POLICY),
        ("protocol_invalidation_policy", PROTOCOL_INVALIDATION_POLICY),
    ):
        if _canonical_bytes(raw.get(field)) != _canonical_bytes(expected):
            raise ValueError(f"manifest {field} does not match protocol 2.1.2")
    expected_scorer_hash = str(raw.get("scorer_sha256", "")).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_scorer_hash):
        raise ValueError("manifest scorer_sha256 must be raw lowercase hex")
    actual_scorer_hash = hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()
    if expected_scorer_hash != actual_scorer_hash:
        raise ValueError("score.py SHA-256 does not match the manifest")
    manifest_kind = raw.get("manifest_kind")
    execution_manifest_id = raw.get("execution_manifest_id")
    execution_purpose = raw.get("execution_purpose")
    frozen_at = raw.get("frozen_at")
    frozen_datetime: datetime | None = None
    if manifest_kind == "protocol_template":
        if any(value is not None for value in (execution_manifest_id, execution_purpose, frozen_at)):
            raise ValueError("protocol template cannot claim execution identity or freeze time")
        if raw.get("protocol_template_artifact") is not None:
            raise ValueError("protocol template cannot reference a parent template")
    elif manifest_kind == "execution":
        if (
            not isinstance(execution_manifest_id, str)
            or not execution_manifest_id.strip()
            or execution_purpose not in EXECUTION_PURPOSES
        ):
            raise ValueError("execution manifest has invalid identity or purpose")
        if execution_purpose != protocol_scope:
            raise ValueError("execution_purpose must equal protocol_scope")
        frozen_datetime = _parse_timestamp(frozen_at, "execution manifest frozen_at")
    else:
        raise ValueError("manifest_kind must be protocol_template or execution")
    expected_status = BENCHMARK_STATUS_BY_KIND_AND_SCOPE[(manifest_kind, protocol_scope)]
    if raw.get("benchmark_status") != expected_status:
        raise ValueError("manifest benchmark_status is inconsistent with kind and scope")
    suites_raw = raw.get("suites")
    if not isinstance(suites_raw, list) or not suites_raw:
        raise ValueError("benchmark manifest must define suites")
    if artifact_root is not None and artifact_root.is_symlink():
        raise ValueError("artifact root cannot be a symbolic link")
    repository_root = (
        artifact_root.resolve()
        if artifact_root is not None
        else manifest_path.parent.parent.resolve()
    )
    declared_projection = _hash_field(
        raw.get("protocol_projection_sha256"),
        "manifest protocol_projection_sha256",
    )
    actual_projection = _canonical_hash(_immutable_protocol_projection(raw))
    if declared_projection != actual_projection:
        raise ValueError("manifest protocol projection does not match its declared hash")
    expected_projection = EXPECTED_TEMPLATE_PROJECTION_BY_SCOPE[protocol_scope]
    if actual_projection != expected_projection:
        raise ValueError("manifest protocol projection is not the frozen 2.1.2 design")

    parent_protocol: dict[str, Any] | None = None
    if manifest_kind == "execution":
        parent_ref = raw.get("protocol_template_artifact")
        if not isinstance(parent_ref, Mapping):
            raise ValueError("execution manifest must bind a protocol template artifact")
        _require_exact_keys(
            parent_ref,
            {"path", "sha256", "schema_version"},
            "protocol template artifact",
        )
        if parent_ref.get("schema_version") != BENCHMARK_SCHEMA_VERSION:
            raise ValueError("protocol template artifact schema_version must be 2.1.2")
        parent_path = _safe_relative_file(
            repository_root,
            parent_ref.get("path"),
            "protocol template artifact",
        )
        parent_payload = _stable_file_bytes(
            parent_path,
            "protocol template artifact",
            maximum_bytes=16 * 1024 * 1024,
        )
        if _hash_field(parent_ref.get("sha256"), "protocol template artifact hash") != _sha256_bytes(parent_payload):
            raise ValueError("protocol template artifact SHA-256 does not match")
        parent_raw = _json_from_bytes(parent_payload, "protocol template artifact")
        if not isinstance(parent_raw, Mapping) or parent_raw.get("manifest_kind") != "protocol_template":
            raise ValueError("protocol template artifact must be a protocol template")
        parent_protocol = _load_protocol(
            parent_path,
            repository_root,
            _manifest_payload=parent_payload,
        )
        parent_manifest = parent_protocol["manifest"]
        for field in (
            "protocol_id",
            "protocol_scope",
            "release_under_test",
            "protocol_projection_profile",
            "protocol_projection_sha256",
        ):
            if raw.get(field) != parent_manifest.get(field):
                raise ValueError(f"execution manifest does not inherit parent {field}")
        if _canonical_bytes(_immutable_protocol_projection(raw)) != _canonical_bytes(
            _immutable_protocol_projection(parent_manifest)
        ):
            raise ValueError("execution manifest changes the frozen protocol design")
    suites: dict[str, dict[str, Any]] = {}
    global_block_ids: set[str] = set()
    for index, suite_raw in enumerate(suites_raw, start=1):
        if not isinstance(suite_raw, dict):
            raise ValueError(f"suite {index} must be an object")
        suite = dict(suite_raw)
        suite_id = str(suite.get("suite_id", "")).strip()
        if not suite_id or suite_id in suites:
            raise ValueError("suite IDs must be present and unique")
        backend = suite.get("scoring_backend")
        if backend == "score.py":
            _require_exact_keys(
                suite,
                BUILTIN_SUITE_FIELDS,
                f"suite {suite_id}",
            )
        elif backend == "external":
            _require_exact_keys(
                suite,
                EXTERNAL_SUITE_FIELDS,
                f"external suite {suite_id}",
            )
        else:
            raise ValueError(f"suite {suite_id} has invalid scoring backend")
        suite["suite_id"] = suite_id
        conditions_raw = suite.get("conditions")
        if not isinstance(conditions_raw, list) or not conditions_raw:
            raise ValueError(f"suite {suite_id} must define conditions")
        conditions: dict[str, dict[str, Any]] = {}
        for condition in conditions_raw:
            if not isinstance(condition, dict):
                raise ValueError(f"suite {suite_id} has an invalid condition")
            _require_exact_keys(
                condition,
                CONDITION_FIELDS,
                f"suite {suite_id} condition",
            )
            condition_id_raw = condition.get("condition_id")
            if not isinstance(condition_id_raw, str):
                raise ValueError(f"suite {suite_id} has an invalid condition ID")
            condition_id = condition_id_raw.strip()
            if not condition_id or condition_id in conditions:
                raise ValueError(f"suite {suite_id} has duplicate condition IDs")
            release = condition.get("skill_release")
            package = condition.get("skill_package_sha256")
            if release is None:
                if package is not None:
                    raise ValueError(f"suite {suite_id} no-skill condition needs null package")
                assurance = _validate_material_assurance(
                    repository_root,
                    condition.get("package_assurance"),
                    f"suite {suite_id} condition {condition_id} package assurance",
                    subject_kind="skill_package",
                    subject_id=condition_id,
                    attestation_not_after=frozen_datetime,
                    allow_not_applicable=True,
                )
            else:
                if not isinstance(release, str) or not release.strip():
                    raise ValueError(f"suite {suite_id} condition has invalid release")
                _hash_field(package, f"suite {suite_id} condition package")
                assurance = _validate_material_assurance(
                    repository_root,
                    condition.get("package_assurance"),
                    f"suite {suite_id} condition {condition_id} package assurance",
                    subject_kind="skill_package",
                    subject_id=condition_id,
                    expected_package_digest=str(package),
                    attestation_not_after=frozen_datetime,
                )
            normalized_condition = dict(condition)
            normalized_condition["package_assurance"] = assurance
            conditions[condition_id] = normalized_condition
        suite["conditions_by_id"] = conditions
        _validate_required_design(suite, conditions)
        status = suite.get("protocol_status")
        if backend == "score.py":
            expected_suite_status = (
                "awaiting_execution_freeze"
                if manifest_kind == "protocol_template"
                else "frozen"
            )
            if status != expected_suite_status:
                raise ValueError(
                    f"suite {suite_id} protocol status must be {expected_suite_status}"
                )
            repetitions = suite.get("repetitions")
            if not isinstance(repetitions, int) or isinstance(repetitions, bool) or repetitions < 1:
                raise ValueError(f"suite {suite_id} needs positive repetitions")
            for field in (
                "primary_estimands",
                "secondary_estimands",
                "diagnostic_estimands",
                "tie_rule",
                "uncertainty_design",
            ):
                if suite.get(field) in (None, "", [], {}):
                    raise ValueError(f"suite {suite_id} lacks {field}")
            expected_spec = ESTIMAND_SPEC_BY_RECORD_TYPE.get(suite.get("record_type"))
            if expected_spec is None:
                raise ValueError(f"suite {suite_id} has unsupported record_type")
            expected_spec = dict(expected_spec)
            if protocol_scope == "execution_shakedown":
                expected_spec.update(SHAKEDOWN_INTERPRETATION)
            for field in (
                "primary_estimands",
                "secondary_estimands",
                "diagnostic_estimands",
                "aggregation_method_id",
                "aggregation_rule",
                "uncertainty_design",
                "interpretation_scope_id",
                "interpretation_rule",
            ):
                if suite.get(field) != expected_spec[field]:
                    raise ValueError(
                        f"suite {suite_id} {field} does not match the scorer"
                    )
            _validate_interval_rule(suite, suite_id)
            _validate_failure_policy(suite, suite_id)
            tie_rule = suite.get("tie_rule")
            if (
                not isinstance(tie_rule, Mapping)
                or set(tie_rule) != {"unit", "absolute_delta_threshold"}
                or tie_rule.get("unit") != "case_mean"
                or not _finite_number(tie_rule.get("absolute_delta_threshold"))
                or float(tie_rule.get("absolute_delta_threshold")) < 0
            ):
                raise ValueError(f"suite {suite_id} has invalid tie rule")
            _load_case_registry(repository_root, suite, suite_id)
            role = str(suite.get("case_source", {}).get("role", ""))
            expected_role = (
                "shakedown"
                if protocol_scope == "execution_shakedown"
                else "development"
            )
            if role != expected_role:
                raise ValueError(
                    f"suite {suite_id} case role does not match protocol_scope"
                )
            blocks_raw = suite.get("comparison_blocks")
            if not isinstance(blocks_raw, list):
                raise ValueError(f"suite {suite_id} comparison_blocks must be a list")
            if status == "frozen" and not blocks_raw:
                raise ValueError(f"frozen suite {suite_id} needs a comparison block")
            if status == "awaiting_execution_freeze" and blocks_raw:
                raise ValueError(f"unfrozen suite {suite_id} cannot contain frozen blocks")
            blocks: dict[str, dict[str, Any]] = {}
            for block_raw in blocks_raw:
                block = _validate_comparison_block(
                    suite,
                    block_raw,
                    repository_root,
                    frozen_datetime,
                )
                block_id = block["comparison_block_id"]
                if block_id in global_block_ids:
                    raise ValueError(f"duplicate comparison_block_id {block_id}")
                global_block_ids.add(block_id)
                block["execution_purpose"] = execution_purpose
                blocks[block_id] = block
            suite["comparison_blocks_by_id"] = blocks
        elif backend == "external":
            if status != "draft":
                raise ValueError(f"external suite {suite_id} must remain draft here")
            if suite.get("comparison_blocks") != []:
                raise ValueError(
                    f"external draft suite {suite_id} cannot contain comparison blocks"
                )
            suite["cases_by_id"] = {}
            suite["comparison_blocks_by_id"] = {}
        else:
            raise ValueError(f"suite {suite_id} has invalid scoring backend")
        suites[suite_id] = suite

    if manifest_kind == "protocol_template" and global_block_ids:
        raise ValueError("protocol template cannot contain frozen execution blocks")
    if manifest_kind == "execution" and not global_block_ids:
        raise ValueError("execution manifest needs frozen comparison blocks")

    release_hashes: dict[str, set[str]] = defaultdict(set)
    release_assurance_bindings: dict[str, set[str]] = defaultdict(set)
    for suite in suites.values():
        for condition in suite["conditions_by_id"].values():
            release = condition.get("skill_release")
            package = condition.get("skill_package_sha256")
            if release is not None and isinstance(package, str):
                release_hashes[str(release)].add(_hash_field(package, "package"))
                release_assurance_bindings[str(release)].add(
                    _canonical_hash(condition.get("package_assurance"))
                )
    inconsistent = sorted(key for key, values in release_hashes.items() if len(values) > 1)
    if inconsistent:
        raise ValueError(f"skill releases use inconsistent package hashes: {inconsistent}")
    inconsistent_assurance = sorted(
        key for key, values in release_assurance_bindings.items() if len(values) > 1
    )
    if inconsistent_assurance:
        raise ValueError(
            f"skill releases use inconsistent package assurance: {inconsistent_assurance}"
        )
    return {
        "manifest": raw,
        "manifest_sha256": _sha256_bytes(manifest_payload),
        "frozen_datetime": frozen_datetime,
        "repository_root": repository_root,
        "suites": suites,
        "parent_protocol": parent_protocol,
    }


def _validate_record(
    record: Mapping[str, Any],
    index: int,
    protocol: Mapping[str, Any],
    evidence_root: Path,
) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    normalized = dict(record)
    missing = [
        field
        for field in sorted(COMMON_RECORD_FIELDS)
        if field not in record
        or (
            field not in {"skill_release", "skill_package_sha256", "generation_seed"}
            and record.get(field) in (None, "")
        )
    ]
    if missing:
        return [f"record {index}: missing fields {missing}"], None
    allowed_record_fields = set(COMMON_RECORD_FIELDS)
    if record.get("run_status") == "completed":
        if record.get("record_type") == "trigger":
            allowed_record_fields.update(TRIGGER_OUTCOME_FIELDS)
        elif record.get("record_type") == "behavioral":
            allowed_record_fields.update(BEHAVIORAL_OUTCOME_FIELDS)
    unknown_record_fields = set(record) - allowed_record_fields
    if unknown_record_fields:
        errors.append(
            f"record {index}: record does not use the closed schema "
            f"(unknown={sorted(str(item) for item in unknown_record_fields)})"
        )
    if record.get("record_schema_version") != RECORD_SCHEMA_VERSION:
        errors.append(f"record {index}: unsupported record_schema_version")
    if str(record.get("manifest_sha256", "")).lower() != protocol["manifest_sha256"]:
        errors.append(f"record {index}: manifest_sha256 mismatch")
    suite_id = str(record.get("suite_id", ""))
    suite = protocol["suites"].get(suite_id)
    if suite is None:
        return [f"record {index}: unknown suite_id {suite_id!r}"], None
    if suite.get("scoring_backend") != "score.py":
        return [f"record {index}: suite {suite_id!r} uses an external scorer"], None
    block_id = str(record.get("comparison_block_id", ""))
    block = suite["comparison_blocks_by_id"].get(block_id)
    if block is None:
        return [f"record {index}: unknown or unfrozen comparison_block_id {block_id!r}"], None
    if record.get("run_batch_id") != block["run_batch_id"]:
        errors.append(f"record {index}: run_batch_id mismatch")
    condition_id = str(record.get("condition_id", ""))
    if condition_id not in block["condition_ids"]:
        return [f"record {index}: condition is not in the comparison block"], None
    condition = suite["conditions_by_id"][condition_id]
    if record.get("skill_release") != condition.get("skill_release"):
        errors.append(f"record {index}: skill_release mismatch")
    expected_package = condition.get("skill_package_sha256")
    if expected_package is None:
        if record.get("skill_package_sha256") is not None:
            errors.append(f"record {index}: no-skill package hash must be null")
    else:
        try:
            if _hash_field(record.get("skill_package_sha256"), "package") != _hash_field(
                expected_package, "frozen package"
            ):
                errors.append(f"record {index}: skill package hash mismatch")
        except ValueError as exc:
            errors.append(f"record {index}: {exc}")
    case_id = str(record.get("case_id", ""))
    case = suite["cases_by_id"].get(case_id)
    if case is None:
        return [f"record {index}: unknown case_id {case_id!r}"], None
    replicate_raw = record.get("replicate")
    replicate_valid = isinstance(replicate_raw, int) and not isinstance(
        replicate_raw, bool
    )
    if not replicate_valid:
        errors.append(f"record {index}: replicate must be an integer")
    replicate = replicate_raw if replicate_valid else None
    pair = (case_id, replicate)
    if pair not in block["expected_pairs"]:
        errors.append(f"record {index}: replicate is outside the schedule")
    attempt = record.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        errors.append(f"record {index}: attempt must be a positive integer")
    if record.get("record_type") != suite.get("record_type"):
        errors.append(f"record {index}: record_type mismatch")
    for field in ("agent", "model", "runtime"):
        expected = block["executor_identity"][field]
        if record.get(field) != expected:
            errors.append(f"record {index}: {field} differs from the frozen block")
    config_ref = block["execution_config_ref"]
    if (
        record.get("execution_config_path") != config_ref["path"]
        or record.get("execution_config_schema_version") != config_ref["schema_version"]
    ):
        errors.append(f"record {index}: execution config reference mismatch")
    try:
        if _hash_field(record.get("execution_config_sha256"), "record config") != config_ref[
            "sha256"
        ]:
            errors.append(f"record {index}: execution config hash mismatch")
    except ValueError as exc:
        errors.append(f"record {index}: {exc}")
    seed_status = str(record.get("seed_control_status", ""))
    if seed_status != block.get("seed_control_status"):
        errors.append(f"record {index}: seed control status mismatch")
    expected_seed = block["seed_by_pair"].get(pair)
    if expected_seed is not None and (
        not isinstance(record.get("generation_seed"), int)
        or isinstance(record.get("generation_seed"), bool)
    ):
        errors.append(f"record {index}: generation_seed must be an integer")
    if record.get("generation_seed") != expected_seed:
        errors.append(f"record {index}: generation seed differs from the schedule")
    order = block["order_by_pair"].get(pair, [])
    expected_order = order.index(condition_id) + 1 if condition_id in order else None
    if (
        not isinstance(record.get("run_order_index"), int)
        or isinstance(record.get("run_order_index"), bool)
    ):
        errors.append(f"record {index}: run_order_index must be an integer")
    if record.get("run_order_index") != expected_order:
        errors.append(f"record {index}: run_order_index differs from the schedule")
    run_status = str(record.get("run_status", ""))
    if run_status not in RUN_STATUSES:
        errors.append(f"record {index}: invalid run_status")
    try:
        started = _parse_timestamp(record.get("started_at"), f"record {index} started_at")
        completed = _parse_timestamp(
            record.get("completed_at"), f"record {index} completed_at"
        )
        if completed < started:
            errors.append(f"record {index}: completed_at precedes started_at")
        frozen_datetime = protocol.get("frozen_datetime")
        if frozen_datetime is not None and started < frozen_datetime:
            errors.append(f"record {index}: started_at precedes the execution freeze")
        normalized["__started_datetime__"] = started
        normalized["__completed_datetime__"] = completed
    except ValueError as exc:
        errors.append(str(exc))
    try:
        normalized["session_identity_sha256"] = _hash_field(
            record.get("session_identity_sha256"), f"record {index} session identity"
        )
    except ValueError as exc:
        errors.append(str(exc))
    if str(record.get("case_spec_sha256", "")).lower() != case["case_spec_sha256"]:
        errors.append(f"record {index}: case_spec_sha256 mismatch")
    if str(record.get("prompt_sha256", "")).lower() != case["prompt_sha256"]:
        errors.append(f"record {index}: prompt_sha256 mismatch")
    try:
        evidence_path, evidence_hash, _evidence_payload = _verify_evidence(
            evidence_root,
            record.get("evidence_path"),
            record.get("evidence_sha256"),
            f"record {index} evidence",
        )
        normalized["__evidence_absolute__"] = str(evidence_path)
        normalized["evidence_sha256"] = evidence_hash
    except ValueError as exc:
        errors.append(str(exc))

    computed_identity = _execution_identity_hash(record)
    if str(record.get("execution_identity_sha256", "")).lower() != computed_identity:
        errors.append(f"record {index}: execution_identity_sha256 mismatch")
    normalized["execution_identity_sha256"] = computed_identity

    if run_status != "completed":
        pass
    elif suite.get("record_type") == "trigger":
        if "expected_trigger" in record:
            errors.append(f"record {index}: truth must come from the case registry")
        if not isinstance(record.get("predicted_trigger"), bool):
            errors.append(f"record {index}: predicted_trigger must be Boolean")
        normalized["expected_trigger"] = bool(case["should_trigger"])
        routing_protocol = block["routing_protocol"] or {}
        routing_ref = block["routing_protocol_ref"] or {}
        if record.get("routing_protocol_id") != routing_protocol.get(
            "routing_protocol_id"
        ):
            errors.append(f"record {index}: routing_protocol_id mismatch")
        try:
            if _hash_field(
                record.get("routing_protocol_sha256"), "routing protocol"
            ) != routing_ref.get("sha256"):
                errors.append(f"record {index}: routing protocol hash mismatch")
        except ValueError as exc:
            errors.append(f"record {index}: {exc}")
        routing_extractor = record.get("routing_extractor")
        if routing_extractor != routing_protocol.get("extractor_identity"):
            errors.append(f"record {index}: routing extractor differs from the protocol")
        try:
            judgment_path, judgment_hash, judgment_payload = _verify_evidence(
                evidence_root,
                record.get("judgment_path"),
                record.get("judgment_sha256"),
                f"record {index} routing judgment",
            )
            judgment = _json_from_bytes(
                judgment_payload, f"record {index} routing judgment"
            )
            if not isinstance(judgment, dict):
                raise ValueError(f"record {index} routing judgment must be an object")
            bindings = {
                "execution_identity_sha256": computed_identity,
                "evidence_sha256": normalized.get("evidence_sha256"),
                "case_spec_sha256": case.get("case_spec_sha256"),
                "prompt_sha256": case.get("prompt_sha256"),
                "routing_protocol_id": routing_protocol.get("routing_protocol_id"),
                "routing_protocol_sha256": routing_ref.get("sha256"),
                "routing_extractor": routing_extractor,
                "predicted_trigger": record.get("predicted_trigger"),
                "scored_at": record.get("scored_at"),
            }
            for field, expected in bindings.items():
                if judgment.get(field) != expected:
                    raise ValueError(
                        f"record {index} routing judgment does not bind {field}"
                    )
            scored_at = _parse_timestamp(
                record.get("scored_at"), f"record {index} scored_at"
            )
            if scored_at < normalized.get("__completed_datetime__", scored_at):
                raise ValueError(f"record {index}: scored_at precedes completed_at")
            normalized["judgment_sha256"] = judgment_hash
            normalized["__judgment_absolute__"] = str(judgment_path)
        except ValueError as exc:
            errors.append(str(exc))
    else:
        scores = record.get("assertion_scores")
        expected_ids = [str(item) for item in case.get("assertion_ids", [])]
        if not isinstance(scores, dict):
            errors.append(f"record {index}: assertion_scores must be an object")
        else:
            if set(scores) != set(expected_ids):
                errors.append(f"record {index}: assertion IDs do not match the rubric")
            if any(not isinstance(value, bool) for value in scores.values()):
                errors.append(f"record {index}: assertion scores must be Boolean")
        if str(record.get("rubric_sha256", "")).lower() != case.get("rubric_sha256"):
            errors.append(f"record {index}: rubric_sha256 mismatch")
        judge_protocol = block["judge_protocol"] or {}
        judge_ref = block["judge_protocol_ref"] or {}
        if record.get("judge_protocol_id") != judge_protocol.get("judge_protocol_id"):
            errors.append(f"record {index}: judge_protocol_id mismatch")
        try:
            if _hash_field(record.get("judge_protocol_sha256"), "judge protocol") != judge_ref.get(
                "sha256"
            ):
                errors.append(f"record {index}: judge protocol hash mismatch")
        except ValueError as exc:
            errors.append(f"record {index}: {exc}")
        judge = record.get("judge")
        expected_judge = judge_protocol.get("judge_identity")
        if not isinstance(judge, Mapping) or not isinstance(expected_judge, Mapping):
            errors.append(f"record {index}: judge metadata is invalid")
        else:
            expected_panel_size = expected_judge.get("panel_size", 1)
            expected_judge_fields = set(expected_judge)
            allowed_judge_fields = set(expected_judge_fields)
            if expected_panel_size > 1:
                allowed_judge_fields.update({"agreement", "adjudication"})
            if set(judge) != allowed_judge_fields:
                errors.append(f"record {index}: judge metadata does not use the frozen schema")
            for field in expected_judge_fields:
                if judge.get(field) != expected_judge.get(field):
                    errors.append(f"record {index}: judge.{field} differs from the protocol")
            panel_size = judge.get("panel_size", 1)
            panel_size_valid = (
                isinstance(panel_size, int)
                and not isinstance(panel_size, bool)
                and panel_size >= 1
            )
            if not panel_size_valid:
                errors.append(f"record {index}: judge.panel_size must be a positive integer")
            elif panel_size > 1:
                agreement = judge.get("agreement")
                if (
                    not isinstance(agreement, (int, float))
                    or isinstance(agreement, bool)
                    or not 0 <= agreement <= 1
                ):
                    errors.append(f"record {index}: multi-reviewer agreement is invalid")
                if not isinstance(judge.get("adjudication"), str) or not judge[
                    "adjudication"
                ].strip():
                    errors.append(f"record {index}: multi-reviewer adjudication is missing")
        try:
            judgment_path, judgment_hash, judgment_payload = _verify_evidence(
                evidence_root,
                record.get("judgment_path"),
                record.get("judgment_sha256"),
                f"record {index} judgment",
            )
            judgment = _json_from_bytes(judgment_payload, f"record {index} judgment")
            if not isinstance(judgment, dict):
                raise ValueError(f"record {index} judgment must be an object")
            bindings = {
                "execution_identity_sha256": computed_identity,
                "evidence_sha256": normalized.get("evidence_sha256"),
                "case_spec_sha256": case.get("case_spec_sha256"),
                "rubric_sha256": case.get("rubric_sha256"),
                "judge_protocol_id": judge_protocol.get("judge_protocol_id"),
                "judge_protocol_sha256": judge_ref.get("sha256"),
                "assertion_scores": scores,
                "judge": judge,
                "scored_at": record.get("scored_at"),
            }
            for field, expected in bindings.items():
                if judgment.get(field) != expected:
                    raise ValueError(f"record {index} judgment does not bind {field}")
            scored_at = _parse_timestamp(
                record.get("scored_at"), f"record {index} scored_at"
            )
            if scored_at < normalized.get("__completed_datetime__", scored_at):
                raise ValueError(f"record {index}: scored_at precedes completed_at")
            normalized["judgment_sha256"] = judgment_hash
            normalized["__judgment_absolute__"] = str(judgment_path)
        except ValueError as exc:
            errors.append(str(exc))
    return errors, normalized if not errors else None


def _resolve_attempts(
    records: Sequence[dict[str, Any]],
    protocol: Mapping[str, Any],
) -> tuple[
    dict[tuple[str, str], list[str]],
    dict[tuple[str, str, str, str, int], dict[str, Any]],
    dict[tuple[str, str, str, str, int], str],
]:
    errors: dict[tuple[str, str], list[str]] = defaultdict(list)
    selected: dict[tuple[str, str, str, str, int], dict[str, Any]] = {}
    unresolved: dict[tuple[str, str, str, str, int], str] = {}
    grouped: dict[tuple[str, str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        key = (
            row["suite_id"],
            row["comparison_block_id"],
            row["condition_id"],
            row["case_id"],
            row["replicate"],
        )
        grouped[key].append(row)
    for key, attempts in grouped.items():
        suite = protocol["suites"][key[0]]
        policy = suite["failure_retry_policy"]
        retry_statuses = set(policy["retry_eligible_statuses"])
        ordered = sorted(attempts, key=lambda item: item["attempt"])
        numbers = [item["attempt"] for item in ordered]
        block_key = (key[0], key[1])
        if numbers != list(range(1, len(numbers) + 1)):
            errors[block_key].append(
                f"cell {key} has duplicate or noncontiguous attempt numbers"
            )
            continue
        if len(ordered) > 1 + int(policy["maximum_infrastructure_retries"]):
            errors[block_key].append(
                f"cell {key} exceeds the frozen infrastructure retry limit"
            )
        for position, row in enumerate(ordered):
            has_later = position < len(ordered) - 1
            if has_later and row["run_status"] not in retry_statuses:
                errors[block_key].append(
                    f"cell {key} was retried after a non-retry-eligible outcome"
                )
            if has_later:
                later = ordered[position + 1]
                if later["__started_datetime__"] < row["__completed_datetime__"]:
                    errors[block_key].append(
                        f"cell {key} retry attempt {later['attempt']} started before attempt {row['attempt']} completed"
                    )
        terminal = ordered[-1]
        if terminal["run_status"] in INFRASTRUCTURE_FAILURE_STATUSES:
            unresolved[key] = "infrastructure_retries_exhausted_or_pending"
        else:
            selected[key] = terminal
    return errors, selected, unresolved


def _scored_row(
    row: Mapping[str, Any],
    suite: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(row)
    case = suite["cases_by_id"][row["case_id"]]
    if suite["record_type"] == "trigger":
        truth = bool(case["should_trigger"])
        prediction = row.get("predicted_trigger") if row["run_status"] == "completed" else None
        result["__truth__"] = truth
        result["__prediction__"] = prediction
        result["__credit__"] = float(prediction == truth) if prediction is not None else 0.0
    else:
        assertion_ids = [str(value) for value in case["assertion_ids"]]
        scores = (
            dict(row["assertion_scores"])
            if row["run_status"] == "completed"
            else {item: False for item in assertion_ids}
        )
        critical_ids = set(case.get("critical_assertion_ids", []))
        result["__scores__"] = scores
        result["__assertion_mean__"] = sum(scores.values()) / len(scores)
        result["__all_pass__"] = float(all(scores.values()))
        result["__critical_violation__"] = float(
            any(not scores[item] for item in critical_ids)
        )
    return result


def _trigger_completed_confusion(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    completed = [row for row in rows if row["__prediction__"] is not None]
    tp = sum(row["__truth__"] and row["__prediction__"] for row in completed)
    tn = sum(not row["__truth__"] and not row["__prediction__"] for row in completed)
    fp = sum(not row["__truth__"] and row["__prediction__"] for row in completed)
    fn = sum(row["__truth__"] and not row["__prediction__"] for row in completed)
    recall = _ratio(tp, tp + fn)
    specificity = _ratio(tn, tn + fp)
    return {
        "n_completed_predictions": len(completed),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": _ratio(tp, tp + fp),
        "recall": recall,
        "specificity": specificity,
        "balanced_accuracy": (
            (recall + specificity) / 2
            if recall is not None and specificity is not None
            else None
        ),
    }


def _case_bootstrap_interval(
    values_by_case: Mapping[str, float],
    draws: int,
    seed: int,
    confidence: float,
    *,
    positive_cases: Sequence[str] | None = None,
    negative_cases: Sequence[str] | None = None,
) -> list[float] | None:
    generator = random.Random(seed)
    samples: list[float] = []
    if positive_cases is not None and negative_cases is not None:
        if not positive_cases or not negative_cases:
            return None
        for _ in range(draws):
            positive = generator.choices(list(positive_cases), k=len(positive_cases))
            negative = generator.choices(list(negative_cases), k=len(negative_cases))
            samples.append(
                (
                    sum(values_by_case[item] for item in positive) / len(positive)
                    + sum(values_by_case[item] for item in negative) / len(negative)
                )
                / 2
            )
    else:
        cases = sorted(values_by_case)
        if not cases:
            return None
        for _ in range(draws):
            selected = generator.choices(cases, k=len(cases))
            samples.append(sum(values_by_case[item] for item in selected) / len(selected))
    return _interval(samples, confidence)


def _condition_summary(
    suite: Mapping[str, Any],
    block: Mapping[str, Any],
    condition_id: str,
    rows: Sequence[dict[str, Any]],
    all_attempts: Sequence[dict[str, Any]],
    complete: bool,
    comparison_eligible: bool,
) -> dict[str, Any]:
    scored = [_scored_row(row, suite) for row in rows]
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        by_case[row["case_id"]].append(row)
    interval_rule = suite["interval_rule"]
    base: dict[str, Any] = {
        "suite_id": suite["suite_id"],
        "comparison_block_id": block["comparison_block_id"],
        "run_batch_id": block["run_batch_id"],
        "condition_id": condition_id,
        "skill_release": suite["conditions_by_id"][condition_id].get("skill_release"),
        "n_cases": len(by_case),
        "n_selected_executions": len(rows),
        "n_attempt_records": len(all_attempts),
        "expected_executions": len(block["expected_pairs"]),
        "complete": complete,
        "comparison_eligible": comparison_eligible,
        "run_status_counts": dict(
            sorted(Counter(row["run_status"] for row in all_attempts).items())
        ),
        "diagnostics": {
            "infrastructure_retry_count": len(all_attempts)
            - len({(row["case_id"], row["replicate"]) for row in all_attempts}),
        },
    }
    if suite["record_type"] == "trigger":
        case_credit = {
            case_id: sum(row["__credit__"] for row in case_rows) / len(case_rows)
            for case_id, case_rows in by_case.items()
        }
        positive = [
            case_id
            for case_id in case_credit
            if suite["cases_by_id"][case_id]["should_trigger"]
        ]
        negative = [case_id for case_id in case_credit if case_id not in positive]
        balanced = (
            (_mean(case_credit[item] for item in positive) + _mean(case_credit[item] for item in negative))
            / 2
            if positive and negative
            else None
        )
        metrics = {
            "balanced_accuracy_zero_credit_failures": balanced,
            "case_macro_credit": _mean(case_credit.values()),
            "agent_failure_rate": _mean(
                float(row["run_status"] in AGENT_FAILURE_STATUSES) for row in scored
            ),
        }
        base["diagnostics"]["agent_failure_rate"] = metrics["agent_failure_rate"]
        intervals = {
            "balanced_accuracy_zero_credit_failures": _case_bootstrap_interval(
                case_credit,
                int(interval_rule["draws"]),
                int(interval_rule["seed"]),
                float(interval_rule["confidence"]),
                positive_cases=positive,
                negative_cases=negative,
            )
        }
        base.update(
            {
                "metrics": metrics,
                "intervals": intervals,
                "completed_output_diagnostics": _trigger_completed_confusion(scored),
            }
        )
    else:
        case_metrics = {
            case_id: {
                "assertion": _mean(row["__assertion_mean__"] for row in case_rows),
                "all_pass": _mean(row["__all_pass__"] for row in case_rows),
                "critical": _mean(row["__critical_violation__"] for row in case_rows),
            }
            for case_id, case_rows in by_case.items()
        }
        metrics = {
            "case_mean_assertion_pass_rate": _mean(
                item["assertion"] for item in case_metrics.values()
            ),
            "case_all_pass_rate": _mean(item["all_pass"] for item in case_metrics.values()),
            "critical_violation_rate": _mean(item["critical"] for item in case_metrics.values()),
            "assertion_micro_pass_rate_diagnostic": _mean(
                float(value)
                for row in scored
                for value in row["__scores__"].values()
            ),
            "agent_failure_rate": _mean(
                float(row["run_status"] in AGENT_FAILURE_STATUSES) for row in scored
            ),
        }
        base["diagnostics"]["agent_failure_rate"] = metrics["agent_failure_rate"]
        intervals = {}
        for output_name, input_name in (
            ("case_mean_assertion_pass_rate", "assertion"),
            ("case_all_pass_rate", "all_pass"),
            ("critical_violation_rate", "critical"),
        ):
            intervals[output_name] = _case_bootstrap_interval(
                {case_id: item[input_name] for case_id, item in case_metrics.items()},
                int(interval_rule["draws"]),
                int(interval_rule["seed"]),
                float(interval_rule["confidence"]),
            )
        base.update({"metrics": metrics, "intervals": intervals})
    return base


def _win_loss_tie(case_differences: Mapping[str, float], threshold: float) -> dict[str, int]:
    wins = sum(value > threshold for value in case_differences.values())
    losses = sum(value < -threshold for value in case_differences.values())
    ties = len(case_differences) - wins - losses
    return {"wins": wins, "losses": losses, "ties": ties, "unit": "case_mean"}


def _execution_stochasticity(
    differences_by_case: Mapping[str, Sequence[float]],
) -> dict[str, Any]:
    variances = [
        value
        for values in differences_by_case.values()
        if (value := _variance(list(values))) is not None
    ]
    if not variances:
        return {
            "status": "not_estimable_under_current_design",
            "mean_within_case_paired_variance": None,
        }
    return {
        "status": "estimated_from_within_case_replicates",
        "mean_within_case_paired_variance": sum(variances) / len(variances),
        "n_cases_with_replication": len(variances),
    }


def _paired_comparison(
    suite: Mapping[str, Any],
    block: Mapping[str, Any],
    contrast: Mapping[str, str],
    selected_by_condition: Mapping[str, Mapping[tuple[str, int], dict[str, Any]]],
) -> dict[str, Any]:
    target_id = contrast["target_condition_id"]
    reference_id = contrast["reference_condition_id"]
    target = selected_by_condition[target_id]
    reference = selected_by_condition[reference_id]
    interval_rule = suite["interval_rule"]
    threshold = float(suite["tie_rule"]["absolute_delta_threshold"])
    result: dict[str, Any] = {
        "suite_id": suite["suite_id"],
        "comparison_block_id": block["comparison_block_id"],
        "run_batch_id": block["run_batch_id"],
        "contrast_id": contrast["contrast_id"],
        "target_condition_id": target_id,
        "reference_condition_id": reference_id,
        "pair_identity": ["comparison_block_id", "case_id", "replicate"],
        "n_paired_executions": len(block["expected_pairs"]),
        "case_variation": "estimated_by_frozen_case_cluster_bootstrap",
        "seed_pairing": (
            "enforced"
            if block["seed_control_status"] == "enforced"
            else "pairing_by_case_and_replicate_without_guaranteed_random_stream"
        ),
    }
    if suite["record_type"] == "trigger":
        differences_by_case: dict[str, list[float]] = defaultdict(list)
        for pair in sorted(block["expected_pairs"]):
            target_row = _scored_row(target[pair], suite)
            reference_row = _scored_row(reference[pair], suite)
            differences_by_case[pair[0]].append(
                target_row["__credit__"] - reference_row["__credit__"]
            )
        case_differences = {
            case_id: sum(values) / len(values)
            for case_id, values in differences_by_case.items()
        }
        positive = [
            case_id
            for case_id in case_differences
            if suite["cases_by_id"][case_id]["should_trigger"]
        ]
        negative = [case_id for case_id in case_differences if case_id not in positive]
        delta = (
            (_mean(case_differences[item] for item in positive) + _mean(case_differences[item] for item in negative))
            / 2
        )
        result.update(
            {
                "point_estimates": {"trigger_balanced_accuracy_delta": delta},
                "intervals": {
                    "trigger_balanced_accuracy_delta": _case_bootstrap_interval(
                        case_differences,
                        int(interval_rule["draws"]),
                        int(interval_rule["seed"]),
                        float(interval_rule["confidence"]),
                        positive_cases=positive,
                        negative_cases=negative,
                    )
                },
                "win_loss_tie": _win_loss_tie(case_differences, threshold),
                "execution_stochasticity": _execution_stochasticity(
                    differences_by_case
                ),
                "judge_uncertainty": "not_applicable",
            }
        )
    else:
        assertion_by_case: dict[str, list[float]] = defaultdict(list)
        all_pass_by_case: dict[str, list[float]] = defaultdict(list)
        critical_by_case: dict[str, list[float]] = defaultdict(list)
        discordance = Counter()
        for pair in sorted(block["expected_pairs"]):
            target_row = _scored_row(target[pair], suite)
            reference_row = _scored_row(reference[pair], suite)
            assertion_by_case[pair[0]].append(
                target_row["__assertion_mean__"] - reference_row["__assertion_mean__"]
            )
            all_pass_by_case[pair[0]].append(
                target_row["__all_pass__"] - reference_row["__all_pass__"]
            )
            critical_by_case[pair[0]].append(
                target_row["__critical_violation__"]
                - reference_row["__critical_violation__"]
            )
            pair_state = (
                int(target_row["__critical_violation__"]),
                int(reference_row["__critical_violation__"]),
            )
            discordance[pair_state] += 1
        case_assertion = {
            case_id: sum(values) / len(values)
            for case_id, values in assertion_by_case.items()
        }
        case_all_pass = {
            case_id: sum(values) / len(values)
            for case_id, values in all_pass_by_case.items()
        }
        case_critical = {
            case_id: sum(values) / len(values)
            for case_id, values in critical_by_case.items()
        }
        estimates = {
            "behavioral_case_macro_delta": _mean(case_assertion.values()),
            "case_all_pass_rate_delta": _mean(case_all_pass.values()),
            "critical_violation_risk_difference": _mean(case_critical.values()),
        }
        intervals = {
            name: _case_bootstrap_interval(
                values,
                int(interval_rule["draws"]),
                int(interval_rule["seed"]),
                float(interval_rule["confidence"]),
            )
            for name, values in (
                ("behavioral_case_macro_delta", case_assertion),
                ("case_all_pass_rate_delta", case_all_pass),
                ("critical_violation_risk_difference", case_critical),
            )
        }
        result.update(
            {
                "point_estimates": estimates,
                "intervals": intervals,
                "win_loss_tie": _win_loss_tie(case_assertion, threshold),
                "critical_violation_discordance": {
                    "target_only": discordance[(1, 0)],
                    "reference_only": discordance[(0, 1)],
                    "both": discordance[(1, 1)],
                    "neither": discordance[(0, 0)],
                    "unit": "case_replicate",
                },
                "execution_stochasticity": _execution_stochasticity(
                    assertion_by_case
                ),
                "judge_uncertainty": "not_estimable_under_current_design",
            }
        )
    return result


def _empty_execution_assurance() -> dict[str, Any]:
    return {
        "level": None,
        "aggregation": "minimum_across_frozen_blocks",
        "runtime_use_assurance": "unreported",
    }


def _block_execution_assurance(
    suite: Mapping[str, Any], block: Mapping[str, Any]
) -> dict[str, Any]:
    components = [
        {
            "kind": "harness",
            "subject_id": str(
                block["execution_config"]["shared_execution_config"][
                    "harness_identity"
                ]["id"]
            ),
            "assurance": block["harness_assurance"]["mode"],
        }
    ]
    for condition_id in block["condition_ids"]:
        condition = suite["conditions_by_id"][condition_id]
        components.append(
            {
                "kind": "package",
                "condition_id": condition_id,
                "assurance": condition["package_assurance"]["mode"],
            }
        )
    material_modes = {
        component["assurance"]
        for component in components
        if component["assurance"] != "not_applicable"
    }
    level = "attested" if "attested" in material_modes else "artifact_verified"
    return {
        "level": level,
        "aggregation": "minimum_across_harness_and_non_null_packages",
        "runtime_use_assurance": "unreported",
        "components": components,
    }


def _protocol_execution_assurance(protocol: Mapping[str, Any]) -> dict[str, Any]:
    levels: set[str] = set()
    for suite in protocol["suites"].values():
        for block in suite.get("comparison_blocks_by_id", {}).values():
            levels.add(_block_execution_assurance(suite, block)["level"])
    if not levels:
        return _empty_execution_assurance()
    return {
        "level": "attested" if "attested" in levels else "artifact_verified",
        "aggregation": "minimum_across_frozen_blocks",
        "runtime_use_assurance": "unreported",
    }


def score_records(
    records: Sequence[Mapping[str, Any]],
    manifest_path: Path,
    evidence_root: Path,
    *,
    records_sha256: str | None = None,
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    try:
        protocol = _load_protocol(manifest_path, artifact_root)
    except ValueError as exc:
        return {
            "score_schema_version": SCORE_SCHEMA_VERSION,
            "scorer_version": SCORER_VERSION,
            "valid": False,
            "scoring_status": "invalid",
            "evidence_status": "not_evaluated",
            "execution_manifest_id": None,
            "execution_purpose": None,
            "execution_artifact_assurance": _empty_execution_assurance(),
            "evidence_tree_sha256": None,
            "errors": [str(exc)],
            "condition_summaries": [],
            "paired_comparisons": [],
        }
    if not records:
        return {
            "score_schema_version": SCORE_SCHEMA_VERSION,
            "scorer_version": SCORER_VERSION,
            "manifest_sha256": protocol["manifest_sha256"],
            "records_sha256": records_sha256,
            "valid": False,
            "scoring_status": "not_evaluated",
            "evidence_status": "not_evaluated",
            "execution_manifest_id": protocol["manifest"].get("execution_manifest_id"),
            "execution_purpose": protocol["manifest"].get("execution_purpose"),
            "execution_artifact_assurance": _protocol_execution_assurance(protocol),
            "evidence_tree_sha256": None,
            "errors": ["no benchmark records were supplied"],
            "condition_summaries": [],
            "paired_comparisons": [],
        }
    block_validation_errors: dict[tuple[str, str], list[str]] = defaultdict(list)
    fatal_errors: list[str] = []
    evidence_claims, evidence_block_errors, evidence_fatal_errors = (
        _evidence_reference_claims(records, protocol)
    )
    fatal_errors.extend(evidence_fatal_errors)
    for block_key, messages in evidence_block_errors.items():
        block_validation_errors[block_key].extend(messages)
    submitted_cells_by_block: dict[
        tuple[str, str], set[tuple[str, str, int]]
    ] = defaultdict(set)
    invalid_attempt_records_by_block: dict[tuple[str, str], list[int]] = defaultdict(list)
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        record_errors, parsed = _validate_record(record, index, protocol, evidence_root)
        suite_id = str(record.get("suite_id", ""))
        block_id = str(record.get("comparison_block_id", ""))
        suite = protocol["suites"].get(suite_id)
        known_block = (
            suite is not None
            and block_id in suite.get("comparison_blocks_by_id", {})
        )
        if known_block and suite is not None:
            block = suite["comparison_blocks_by_id"][block_id]
            condition_id = str(record.get("condition_id", ""))
            case_id = str(record.get("case_id", ""))
            replicate = record.get("replicate")
            if (
                condition_id in block["condition_ids"]
                and isinstance(replicate, int)
                and not isinstance(replicate, bool)
                and (case_id, replicate) in block["expected_pairs"]
            ):
                submitted_cells_by_block[(suite_id, block_id)].add(
                    (condition_id, case_id, replicate)
                )
        if record_errors:
            if known_block:
                block_validation_errors[(suite_id, block_id)].extend(record_errors)
                invalid_attempt_records_by_block[(suite_id, block_id)].append(index)
            else:
                fatal_errors.extend(record_errors)
        if parsed is not None:
            normalized.append(parsed)
    evidence_tree_sha256: str | None = None
    try:
        (
            evidence_tree_sha256,
            actual_evidence_files,
            evidence_path_issues,
        ) = _evidence_tree_snapshot(evidence_root)
        for relative, issue in sorted(evidence_path_issues.items()):
            matching_claims = [
                claim
                for claimed_path, claims in evidence_claims.items()
                if claimed_path == relative or claimed_path.startswith(relative + "/")
                for claim in claims
            ]
            message = f"{issue}: {relative}"
            if not matching_claims:
                fatal_errors.append(message)
                continue
            owners = {claim["owner"] for claim in matching_claims}
            if None in owners:
                fatal_errors.append(message)
            for owner in owners - {None}:
                block_validation_errors[owner].append(message)
        missing_files = sorted(set(evidence_claims) - set(actual_evidence_files))
        orphan_files = sorted(set(actual_evidence_files) - set(evidence_claims))
        for relative in missing_files:
            message = f"evidence tree is missing referenced file: {relative}"
            owners = {claim["owner"] for claim in evidence_claims[relative]}
            if None in owners:
                fatal_errors.append(message)
            for owner in owners - {None}:
                block_validation_errors[owner].append(message)
        if orphan_files:
            fatal_errors.append(
                f"evidence tree contains unreferenced files: {orphan_files[:10]}"
            )
        for relative in sorted(set(evidence_claims) & set(actual_evidence_files)):
            actual_digest = actual_evidence_files[relative]
            mismatched_claims = [
                claim
                for claim in evidence_claims[relative]
                if claim["digest"] is not None and claim["digest"] != actual_digest
            ]
            if not mismatched_claims:
                continue
            message = f"evidence tree content differs from record binding: {relative}"
            owners = {claim["owner"] for claim in mismatched_claims}
            if None in owners:
                fatal_errors.append(message)
            for owner in owners - {None}:
                block_validation_errors[owner].append(message)
    except ValueError as exc:
        fatal_errors.append(str(exc))
    if fatal_errors:
        return {
            "score_schema_version": SCORE_SCHEMA_VERSION,
            "scorer_version": SCORER_VERSION,
            "manifest_sha256": protocol["manifest_sha256"],
            "records_sha256": records_sha256,
            "valid": False,
            "scoring_status": "invalid",
            "evidence_status": "not_evaluated",
            "execution_manifest_id": protocol["manifest"].get("execution_manifest_id"),
            "execution_purpose": protocol["manifest"].get("execution_purpose"),
            "execution_artifact_assurance": _protocol_execution_assurance(protocol),
            "evidence_tree_sha256": evidence_tree_sha256,
            "errors": fatal_errors,
            "condition_summaries": [],
            "paired_comparisons": [],
        }

    identities: dict[str, tuple[int, tuple[str, str]]] = {}
    sessions: dict[str, tuple[str, int, tuple[str, str]]] = {}

    def invalidate_blocks(
        current_key: tuple[str, str],
        previous_key: tuple[str, str],
        message: str,
    ) -> None:
        block_validation_errors[current_key].append(message)
        if previous_key != current_key:
            block_validation_errors[previous_key].append(message)

    for index, row in enumerate(normalized, start=1):
        block_key = (row["suite_id"], row["comparison_block_id"])
        identity = row["execution_identity_sha256"]
        if identity in identities:
            previous_index, previous_key = identities[identity]
            invalidate_blocks(
                block_key,
                previous_key,
                f"records {previous_index} and {index}: duplicate execution identity",
            )
        identities[identity] = (index, block_key)
        session = row["session_identity_sha256"]
        if session in sessions and sessions[session][0] != identity:
            _, previous_index, previous_key = sessions[session]
            invalidate_blocks(
                block_key,
                previous_key,
                f"records {previous_index} and {index}: session identity was reused",
            )
        sessions[session] = (identity, index, block_key)
    attempt_errors, selected, unresolved = _resolve_attempts(normalized, protocol)
    for block_key, messages in attempt_errors.items():
        block_validation_errors[block_key].extend(messages)

    normalized_by_block: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in normalized:
        normalized_by_block[(row["suite_id"], row["comparison_block_id"])].append(row)
    selected_by_block: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for key, row in selected.items():
        selected_by_block[(key[0], key[1])].append(row)

    condition_summaries: list[dict[str, Any]] = []
    paired_comparisons: list[dict[str, Any]] = []
    block_results: list[dict[str, Any]] = []
    completeness_errors: list[str] = []
    completed_evidence_statuses: list[str] = []
    frozen_blocks: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for suite in protocol["suites"].values():
        for block in suite.get("comparison_blocks_by_id", {}).values():
            frozen_blocks.append((suite, block))
    if not frozen_blocks:
        return {
            "score_schema_version": SCORE_SCHEMA_VERSION,
            "scorer_version": SCORER_VERSION,
            "manifest_sha256": protocol["manifest_sha256"],
            "records_sha256": records_sha256,
            "valid": False,
            "scoring_status": "invalid",
            "evidence_status": "not_evaluated",
            "execution_manifest_id": protocol["manifest"].get("execution_manifest_id"),
            "execution_purpose": protocol["manifest"].get("execution_purpose"),
            "execution_artifact_assurance": _empty_execution_assurance(),
            "evidence_tree_sha256": evidence_tree_sha256,
            "errors": ["the manifest has no frozen comparison block"],
            "condition_summaries": [],
            "paired_comparisons": [],
        }

    for suite, block in frozen_blocks:
        suite_id = suite["suite_id"]
        block_id = block["comparison_block_id"]
        expected_cells = {
            (condition_id, case_id, replicate)
            for condition_id in block["condition_ids"]
            for case_id, replicate in block["expected_pairs"]
        }
        attempt_cells = submitted_cells_by_block.get((suite_id, block_id), set())
        selected_cells = {
            (row["condition_id"], row["case_id"], row["replicate"])
            for row in selected_by_block.get((suite_id, block_id), [])
        }
        missing_attempts = sorted(expected_cells - attempt_cells)
        unresolved_cells = sorted(
            (condition_id, case_id, replicate)
            for (key_suite, key_block, condition_id, case_id, replicate), _reason in unresolved.items()
            if key_suite == suite_id and key_block == block_id
        )
        missing_selected = sorted(expected_cells - selected_cells)

        block_schedule_errors: list[str] = []
        for case_id, replicate in sorted(block["expected_pairs"]):
            first_attempts = {
                row["condition_id"]: row
                for row in normalized_by_block.get((suite_id, block_id), [])
                if row["case_id"] == case_id
                and row["replicate"] == replicate
                and row["attempt"] == 1
            }
            if set(first_attempts) == set(block["condition_ids"]):
                scheduled = block["order_by_pair"][(case_id, replicate)]
                actual = sorted(
                    first_attempts,
                    key=lambda condition: first_attempts[condition]["__started_datetime__"],
                )
                starts = [first_attempts[item]["__started_datetime__"] for item in scheduled]
                if len(set(starts)) != len(starts):
                    block_schedule_errors.append(
                        f"suite={suite_id}, block={block_id}, pair={(case_id, replicate)} actual start order is not identifiable"
                    )
                if actual != scheduled:
                    block_schedule_errors.append(
                        f"suite={suite_id}, block={block_id}, pair={(case_id, replicate)} actual start order differs from schedule"
                    )
                span = (max(starts) - min(starts)).total_seconds()
                if span > block["max_pair_window_seconds"]:
                    block_schedule_errors.append(
                        f"suite={suite_id}, block={block_id}, pair={(case_id, replicate)} exceeds the frozen adjacent-run window"
                    )
            score_bearing_attempts = {
                row["condition_id"]: row
                for row in selected_by_block.get((suite_id, block_id), [])
                if row["case_id"] == case_id and row["replicate"] == replicate
            }
            if set(score_bearing_attempts) == set(block["condition_ids"]):
                score_bearing_starts = [
                    row["__started_datetime__"]
                    for row in score_bearing_attempts.values()
                ]
                score_bearing_span = (
                    max(score_bearing_starts) - min(score_bearing_starts)
                ).total_seconds()
                if score_bearing_span > block["max_pair_window_seconds"]:
                    block_schedule_errors.append(
                        f"suite={suite_id}, block={block_id}, pair={(case_id, replicate)} selected score-bearing attempts exceed the frozen adjacent-run window"
                    )

        block_protocol_errors = list(
            block_validation_errors.get((suite_id, block_id), [])
        ) + block_schedule_errors
        completeness_errors.extend(block_protocol_errors)
        block_invalidated = bool(block_protocol_errors)
        complete = (
            not missing_attempts
            and not unresolved_cells
            and not missing_selected
            and not block_invalidated
        )
        if missing_attempts:
            completeness_errors.append(
                f"suite={suite_id}, block={block_id} has {len(missing_attempts)} cells with no attempt record"
            )
        if unresolved_cells:
            completeness_errors.append(
                f"suite={suite_id}, block={block_id} has {len(unresolved_cells)} unresolved infrastructure cells"
            )
        by_condition: dict[str, dict[tuple[str, int], dict[str, Any]]] = defaultdict(dict)
        for row in selected_by_block.get((suite_id, block_id), []):
            by_condition[row["condition_id"]][(row["case_id"], row["replicate"])] = row
        all_attempts_by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in normalized_by_block.get((suite_id, block_id), []):
            all_attempts_by_condition[row["condition_id"]].append(row)
        shakedown = block.get("execution_purpose") == "execution_shakedown"
        if not shakedown and not block_invalidated:
            for condition_id in block["condition_ids"]:
                rows = list(by_condition.get(condition_id, {}).values())
                condition_complete = set(by_condition.get(condition_id, {})) == block["expected_pairs"]
                condition_summaries.append(
                    _condition_summary(
                        suite,
                        block,
                        condition_id,
                        rows,
                        all_attempts_by_condition.get(condition_id, []),
                        condition_complete,
                        complete,
                    )
                )
        block_status = (
            "invalidated"
            if block_invalidated
            else "complete" if complete else "comparison_incomplete"
        )
        block_result = {
            "suite_id": suite_id,
            "comparison_block_id": block_id,
            "run_batch_id": block["run_batch_id"],
            "status": block_status,
            "expected_cells": len(expected_cells),
            "attempted_cells": len(attempt_cells),
            "selected_cells": len(selected_cells),
            "invalid_attempt_records": invalid_attempt_records_by_block.get(
                (suite_id, block_id), []
            ),
            "missing_attempt_cells": [list(item) for item in missing_attempts],
            "unresolved_infrastructure_cells": [list(item) for item in unresolved_cells],
            "protocol_deviation_errors": block_protocol_errors,
            "execution_purpose": block.get("execution_purpose"),
            "paired_deltas_reported": complete and not shakedown,
            "evaluation_metrics_suppressed_reason": (
                "execution_shakedown" if shakedown else None
            ),
            "execution_artifact_assurance": _block_execution_assurance(suite, block),
            "evidence_status": (
                block["evidence_status_on_complete"] if complete else "not_evaluated"
            ),
        }
        block_results.append(block_result)
        if complete:
            completed_evidence_statuses.append(block["evidence_status_on_complete"])
            if not shakedown:
                for contrast in block["contrasts"]:
                    paired_comparisons.append(
                        _paired_comparison(suite, block, contrast, by_condition)
                    )

    evidence_index = sorted(
        (
            row["suite_id"],
            row["comparison_block_id"],
            row["condition_id"],
            row["case_id"],
            row["replicate"],
            row["attempt"],
            row["run_status"],
            row["evidence_path"],
            row["evidence_sha256"],
            row.get("judgment_path"),
            row.get("judgment_sha256"),
        )
        for row in normalized
    )
    complete = not completeness_errors and all(
        item["status"] == "complete" for item in block_results
    )
    evidence_statuses = sorted(
        set(completed_evidence_statuses), key=EVIDENCE_STATUS_ORDER.get
    )
    if not evidence_statuses:
        evidence_status: str | None = "not_evaluated"
        evidence_status_scope = "no_completed_blocks"
    elif len(evidence_statuses) == 1:
        evidence_status = evidence_statuses[0]
        evidence_status_scope = "uniform_across_completed_blocks"
    else:
        evidence_status = None
        evidence_status_scope = "block_specific"
    any_invalidated = any(item["status"] == "invalidated" for item in block_results)
    scoring_status = (
        "complete"
        if complete
        else "invalidated" if any_invalidated else "comparison_incomplete"
    )
    return {
        "score_schema_version": SCORE_SCHEMA_VERSION,
        "scorer_version": SCORER_VERSION,
        "benchmark_protocol_version": protocol["manifest"]["benchmark_protocol_version"],
        "manifest_sha256": protocol["manifest_sha256"],
        "records_sha256": records_sha256,
        "evidence_index_sha256": _canonical_hash(evidence_index),
        "evidence_tree_sha256": evidence_tree_sha256,
        "valid": complete,
        "scoring_status": scoring_status,
        "evidence_status": evidence_status,
        "evidence_status_scope": evidence_status_scope,
        "evidence_statuses": evidence_statuses,
        "execution_manifest_id": protocol["manifest"].get("execution_manifest_id"),
        "execution_purpose": protocol["manifest"].get("execution_purpose"),
        "execution_artifact_assurance": _protocol_execution_assurance(protocol),
        "errors": completeness_errors,
        "block_results": block_results,
        "condition_summaries": condition_summaries,
        "paired_comparisons": paired_comparisons,
        "pooling_policy": "comparison blocks are reported separately and never pooled",
    }


def _self_test() -> dict[str, Any]:
    """Replay the committed canary execution without claiming behavior evidence."""

    benchmark_root = Path(__file__).resolve().parent
    manifest_path = benchmark_root / "execution-manifest-shakedown-v2.1.2.json"
    execution_root = benchmark_root / "executions" / "shakedown-v2.1.2"
    records, records_digest = _load_jsonl_with_hash(
        execution_root / "records.jsonl"
    )
    result = score_records(
        records,
        manifest_path,
        execution_root / "evidence",
        records_sha256=records_digest,
    )
    passed = (
        result.get("valid") is True
        and result.get("execution_purpose") == "execution_shakedown"
        and result.get("evidence_status") == "not_evaluated"
        and result.get("condition_summaries") == []
        and result.get("paired_comparisons") == []
        and len(result.get("block_results", [])) == 2
    )
    return {"self_test": "passed" if passed else "failed", "result": result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="?", type=Path, help="Protocol-2.1 JSON Lines attempts.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("manifest-v2.1.2.json"),
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="Repository or artifact root for contained manifest paths.",
    )
    parser.add_argument("--evidence-root", type=Path, help="Root containing bound outputs, failure logs, and judgments.")
    parser.add_argument("--output", type=Path, help="Optional scored-result JSON path.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic paired fixtures.")
    args = parser.parse_args()
    if args.self_test:
        result = _self_test()
    else:
        if args.records is None:
            parser.error("records is required unless --self-test is used")
        if args.evidence_root is None:
            parser.error("--evidence-root is required")
        try:
            records, records_digest = _load_jsonl_with_hash(args.records)
            result = score_records(
                records,
                args.manifest,
                args.evidence_root,
                records_sha256=records_digest,
                artifact_root=args.artifact_root,
            )
        except (OSError, ValueError) as exc:
            result = {
                "score_schema_version": SCORE_SCHEMA_VERSION,
                "scorer_version": SCORER_VERSION,
                "valid": False,
                "scoring_status": "invalid",
                "evidence_status": "not_evaluated",
                "execution_manifest_id": None,
                "execution_purpose": None,
                "execution_artifact_assurance": _empty_execution_assurance(),
                "evidence_tree_sha256": None,
                "errors": [str(exc)],
                "condition_summaries": [],
                "paired_comparisons": [],
            }
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    success = result.get("self_test") == "passed" if args.self_test else result.get("valid") is True
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
