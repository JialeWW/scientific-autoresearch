#!/usr/bin/env python3
"""Score hash-bound benchmark records against a frozen manifest and case registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


SCORER_VERSION = "2.0.0"
RECORD_SCHEMA_VERSION = "2.0.0"
HASH_RE = re.compile(r"sha256:[0-9a-f]{64}")
COMMON_RECORD_FIELDS = {
    "record_schema_version",
    "manifest_sha256",
    "suite_id",
    "condition_id",
    "skill_release",
    "skill_package_sha256",
    "case_id",
    "replicate",
    "agent",
    "model",
    "runtime",
    "execution_config_sha256",
    "generation_seed",
    "seed_control_status",
    "execution_identity_sha256",
    "record_type",
    "case_spec_sha256",
    "prompt_sha256",
    "evidence_path",
    "evidence_sha256",
}
SEED_CONTROL_STATUSES = {"controlled", "uncontrolled", "not_applicable"}
EXECUTION_IDENTITY_FIELDS = (
    "manifest_sha256",
    "suite_id",
    "condition_id",
    "skill_release",
    "skill_package_sha256",
    "case_id",
    "replicate",
    "agent",
    "model",
    "runtime",
    "execution_config_sha256",
    "generation_seed",
    "seed_control_status",
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
    return _canonical_hash({field: record.get(field) for field in EXECUTION_IDENTITY_FIELDS})


def _mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return sum(items) / len(items) if items else None


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


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"line {line_number}: invalid JSON: {exc}") from exc
                if not isinstance(value, dict):
                    raise ValueError(f"line {line_number}: record must be an object")
                records.append(value)
    except OSError as exc:
        raise ValueError(f"cannot read records {path}: {exc}") from exc
    return records


def _safe_relative_file(root: Path, value: Any, label: str) -> Path:
    relative = Path(str(value or ""))
    if not str(value or "").strip():
        raise ValueError(f"{label} is missing")
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} must be a contained relative path")
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"{label} cannot traverse a symbolic link")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes its root") from exc
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {relative}")
    return path


def _hash_field(value: Any, label: str) -> str:
    text = str(value or "").strip().lower()
    if not HASH_RE.fullmatch(text):
        raise ValueError(f"{label} must use sha256:<64 lowercase hex>")
    return text


def _load_protocol(manifest_path: Path) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    raw = _load_json(manifest_path)
    if not isinstance(raw, dict):
        raise ValueError("benchmark manifest must be an object")
    if raw.get("benchmark_schema_version") != "2.0.0":
        raise ValueError("score.py requires benchmark_schema_version=2.0.0")
    if raw.get("record_schema_version") != RECORD_SCHEMA_VERSION:
        raise ValueError("manifest record_schema_version does not match scorer")
    expected_scorer_hash = str(raw.get("scorer_sha256", "")).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_scorer_hash):
        raise ValueError("manifest scorer_sha256 must be a raw 64-hex SHA-256")
    actual_scorer_hash = hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()
    if actual_scorer_hash != expected_scorer_hash:
        raise ValueError("score.py SHA-256 does not match the frozen manifest")
    suites_raw = raw.get("suites")
    if not isinstance(suites_raw, list) or not suites_raw:
        raise ValueError("benchmark manifest must define suites")

    repository_root = manifest_path.parent.parent.resolve()
    suites: dict[str, dict[str, Any]] = {}
    for suite_index, suite_raw in enumerate(suites_raw, start=1):
        if not isinstance(suite_raw, dict):
            raise ValueError(f"suite {suite_index} must be an object")
        suite_id = str(suite_raw.get("suite_id", "")).strip()
        if not suite_id or suite_id in suites:
            raise ValueError(f"suite {suite_index} has a missing or duplicate suite_id")
        suite = dict(suite_raw)
        conditions_raw = suite.get("conditions")
        if not isinstance(conditions_raw, list) or not conditions_raw:
            raise ValueError(f"suite {suite_id} must define conditions")
        conditions: dict[str, dict[str, Any]] = {}
        for condition in conditions_raw:
            if not isinstance(condition, dict):
                raise ValueError(f"suite {suite_id} has a non-object condition")
            condition_id = str(condition.get("condition_id", "")).strip()
            if not condition_id or condition_id in conditions:
                raise ValueError(f"suite {suite_id} has a missing or duplicate condition_id")
            release = condition.get("skill_release")
            package_hash = condition.get("skill_package_sha256")
            if release is None:
                if package_hash is not None:
                    raise ValueError(f"suite {suite_id} no-skill condition must use a null package hash")
            else:
                _hash_field(package_hash, f"suite {suite_id} condition {condition_id} package hash")
            conditions[condition_id] = dict(condition)
        suite["conditions_by_id"] = conditions
        suite["cases_by_id"] = {}

        if suite.get("scoring_backend") == "score.py":
            if suite.get("protocol_status") != "frozen":
                raise ValueError(f"suite {suite_id} must be frozen before score.py can score it")
            repetitions = suite.get("repetitions")
            if not isinstance(repetitions, int) or isinstance(repetitions, bool) or repetitions < 1:
                raise ValueError(f"suite {suite_id} needs positive integer repetitions")
            interval_rule = suite.get("interval_rule")
            if not isinstance(interval_rule, dict):
                raise ValueError(f"suite {suite_id} needs an interval_rule object")
            expected_method = (
                "stratified_case_cluster_bootstrap"
                if suite.get("record_type") == "trigger"
                else "case_cluster_bootstrap"
            )
            if interval_rule.get("method") != expected_method:
                raise ValueError(
                    f"suite {suite_id} interval method must be {expected_method}"
                )
            draws = interval_rule.get("draws")
            seed = interval_rule.get("seed")
            confidence = interval_rule.get("confidence")
            if not isinstance(draws, int) or isinstance(draws, bool) or draws < 1:
                raise ValueError(f"suite {suite_id} interval draws must be a positive integer")
            if not isinstance(seed, int) or isinstance(seed, bool):
                raise ValueError(f"suite {suite_id} interval seed must be an integer")
            if (
                not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not 0 < float(confidence) < 1
            ):
                raise ValueError(f"suite {suite_id} interval confidence must be in (0,1)")
            source = suite.get("case_source")
            if not isinstance(source, dict):
                raise ValueError(f"suite {suite_id} needs a case_source object")
            source_path = _safe_relative_file(
                repository_root,
                source.get("path"),
                f"suite {suite_id} case_source.path",
            )
            expected_source_hash = str(source.get("sha256", "")).strip().lower()
            if not re.fullmatch(r"[0-9a-f]{64}", expected_source_hash):
                raise ValueError(f"suite {suite_id} case source needs a raw 64-hex SHA-256")
            if hashlib.sha256(source_path.read_bytes()).hexdigest() != expected_source_hash:
                raise ValueError(f"suite {suite_id} case source SHA-256 mismatch")
            source_data = _load_json(source_path)
            collection_key = source.get("collection_key")
            cases_raw = source_data.get(collection_key) if collection_key else source_data
            if not isinstance(cases_raw, list) or not cases_raw:
                raise ValueError(f"suite {suite_id} case source must resolve to a nonempty list")
            id_field = str(source.get("case_id_field", "id"))
            prompt_field = str(source.get("prompt_field", "prompt"))
            for case_index, case_raw in enumerate(cases_raw, start=1):
                if not isinstance(case_raw, dict):
                    raise ValueError(f"suite {suite_id} case {case_index} must be an object")
                case_id = str(case_raw.get(id_field, "")).strip()
                if not case_id or case_id in suite["cases_by_id"]:
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
                        raise ValueError(f"trigger case {case_id} has no Boolean should_trigger")
                elif suite.get("record_type") == "behavioral":
                    assertions = case_raw.get("assertions")
                    assertion_ids = case_raw.get("assertion_ids")
                    critical_ids = case_raw.get("critical_assertion_ids")
                    if not isinstance(assertions, list) or not assertions:
                        raise ValueError(f"behavioral case {case_id} has no assertions")
                    if (
                        not isinstance(assertion_ids, list)
                        or len(assertion_ids) != len(assertions)
                        or len({str(item) for item in assertion_ids}) != len(assertion_ids)
                    ):
                        raise ValueError(f"behavioral case {case_id} needs one unique assertion ID per assertion")
                    if not isinstance(critical_ids, list) or not set(critical_ids) <= set(assertion_ids):
                        raise ValueError(f"behavioral case {case_id} has invalid critical assertion IDs")
                    case["rubric_sha256"] = _canonical_hash(
                        {
                            "assertions": assertions,
                            "assertion_ids": assertion_ids,
                            "critical_assertion_ids": critical_ids,
                        }
                    )
                else:
                    raise ValueError(f"suite {suite_id} uses unsupported score.py record_type")
                suite["cases_by_id"][case_id] = case
            if suite.get("record_type") == "trigger":
                labels = {
                    bool(case.get("should_trigger"))
                    for case in suite["cases_by_id"].values()
                }
                if labels != {False, True}:
                    raise ValueError(
                        f"trigger suite {suite_id} needs both positive and negative frozen cases; balanced_accuracy is undefined otherwise"
                    )
        suites[suite_id] = suite
    release_hashes: dict[str, set[str]] = defaultdict(set)
    for suite in suites.values():
        for condition in suite["conditions_by_id"].values():
            release = condition.get("skill_release")
            package_hash = condition.get("skill_package_sha256")
            if release is not None and isinstance(package_hash, str):
                release_hashes[str(release)].add(package_hash.lower())
    inconsistent_releases = sorted(
        release for release, hashes in release_hashes.items() if len(hashes) > 1
    )
    if inconsistent_releases:
        raise ValueError(
            f"skill releases use inconsistent package hashes across suites: {inconsistent_releases}"
        )

    return {
        "manifest": raw,
        "manifest_sha256": _sha256_file(manifest_path),
        "repository_root": repository_root,
        "suites": suites,
    }


def _verify_evidence(
    evidence_root: Path,
    path_value: Any,
    hash_value: Any,
    label: str,
) -> tuple[Path, str]:
    path = _safe_relative_file(evidence_root.resolve(), path_value, label)
    expected = _hash_field(hash_value, f"{label} hash")
    actual = _sha256_file(path)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 mismatch")
    return path, actual


def _validate_timestamp(value: Any, label: str) -> None:
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
        errors.append(f"record {index}: missing fields {missing}")
        return errors, None
    if record.get("record_schema_version") != RECORD_SCHEMA_VERSION:
        errors.append(f"record {index}: unsupported record_schema_version")
    if str(record.get("manifest_sha256", "")).lower() != protocol["manifest_sha256"]:
        errors.append(f"record {index}: manifest_sha256 mismatch")

    suite_id = str(record.get("suite_id", ""))
    suite = protocol["suites"].get(suite_id)
    if suite is None:
        errors.append(f"record {index}: unknown suite_id {suite_id!r}")
        return errors, None
    if suite.get("scoring_backend") != "score.py":
        errors.append(f"record {index}: suite {suite_id!r} requires an external scorer")
        return errors, None
    condition_id = str(record.get("condition_id", ""))
    condition = suite["conditions_by_id"].get(condition_id)
    if condition is None:
        errors.append(f"record {index}: unknown condition_id {condition_id!r}")
        return errors, None
    if record.get("skill_release") != condition.get("skill_release"):
        errors.append(f"record {index}: skill_release does not match the frozen condition")
    expected_package = condition.get("skill_package_sha256")
    if expected_package is None:
        if record.get("skill_package_sha256") is not None:
            errors.append(f"record {index}: skill_package_sha256 must be null for this condition")
    else:
        try:
            package_hash = _hash_field(
                record.get("skill_package_sha256"),
                f"record {index} skill_package_sha256",
            )
            if package_hash != str(expected_package).lower():
                errors.append(f"record {index}: skill_package_sha256 does not match the frozen condition")
        except ValueError as exc:
            errors.append(str(exc))

    case_id = str(record.get("case_id", ""))
    case = suite["cases_by_id"].get(case_id)
    if case is None:
        errors.append(f"record {index}: unknown case_id {case_id!r}")
        return errors, None
    if str(record.get("record_type", "")) != suite.get("record_type"):
        errors.append(f"record {index}: record_type does not match suite")
    replicate = record.get("replicate")
    if (
        not isinstance(replicate, int)
        or isinstance(replicate, bool)
        or replicate < 1
        or replicate > suite["repetitions"]
    ):
        errors.append(f"record {index}: replicate is outside the frozen repetition range")
    for field in ("agent", "model", "runtime"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"record {index}: {field} must be a nonempty string")
    try:
        normalized["execution_config_sha256"] = _hash_field(
            record.get("execution_config_sha256"),
            f"record {index} execution_config_sha256",
        )
    except ValueError as exc:
        errors.append(str(exc))
    seed_status = str(record.get("seed_control_status", ""))
    if seed_status not in SEED_CONTROL_STATUSES:
        errors.append(f"record {index}: seed_control_status is invalid")
    generation_seed = record.get("generation_seed")
    if seed_status == "controlled" and generation_seed in (None, ""):
        errors.append(f"record {index}: a controlled seed must be recorded")
    if seed_status in {"uncontrolled", "not_applicable"} and generation_seed is not None:
        errors.append(
            f"record {index}: generation_seed must be null when seed control is {seed_status}"
        )
    computed_identity = _execution_identity_hash(record)
    if str(record.get("execution_identity_sha256", "")).lower() != computed_identity:
        errors.append(f"record {index}: execution_identity_sha256 mismatch")
    normalized["execution_identity_sha256"] = computed_identity
    if str(record.get("case_spec_sha256", "")).lower() != case["case_spec_sha256"]:
        errors.append(f"record {index}: case_spec_sha256 mismatch")
    if str(record.get("prompt_sha256", "")).lower() != case["prompt_sha256"]:
        errors.append(f"record {index}: prompt_sha256 mismatch")

    try:
        evidence_path, evidence_hash = _verify_evidence(
            evidence_root,
            record.get("evidence_path"),
            record.get("evidence_sha256"),
            f"record {index} evidence",
        )
        normalized["__evidence_absolute__"] = str(evidence_path)
        normalized["evidence_sha256"] = evidence_hash
    except ValueError as exc:
        errors.append(str(exc))

    if suite.get("record_type") == "trigger":
        if "expected_trigger" in record:
            errors.append(f"record {index}: expected truth must come from the case registry, not the record")
        if not isinstance(record.get("predicted_trigger"), bool):
            errors.append(f"record {index}: predicted_trigger must be Boolean")
        normalized["expected_trigger"] = case.get("should_trigger")
    else:
        scores = record.get("assertion_scores")
        expected_ids = [str(item) for item in case.get("assertion_ids", [])]
        if not isinstance(scores, dict):
            errors.append(f"record {index}: assertion_scores must be an ID-to-Boolean object")
        else:
            if set(scores) != set(expected_ids):
                errors.append(f"record {index}: assertion_scores IDs do not match the frozen rubric")
            if any(not isinstance(value, bool) for value in scores.values()):
                errors.append(f"record {index}: assertion_scores values must be Boolean")
        if str(record.get("rubric_sha256", "")).lower() != case.get("rubric_sha256"):
            errors.append(f"record {index}: rubric_sha256 mismatch")
        judge = record.get("judge")
        if not isinstance(judge, dict):
            errors.append(f"record {index}: judge must be an object")
        else:
            for field in ("kind", "id", "version"):
                if not isinstance(judge.get(field), str) or not judge[field].strip():
                    errors.append(f"record {index}: judge.{field} must be recorded")
            panel_size = judge.get("panel_size", 1)
            if not isinstance(panel_size, int) or isinstance(panel_size, bool) or panel_size < 1:
                errors.append(f"record {index}: judge.panel_size must be a positive integer")
            if panel_size > 1:
                agreement = judge.get("agreement")
                if not isinstance(agreement, (int, float)) or isinstance(agreement, bool) or not 0 <= agreement <= 1:
                    errors.append(f"record {index}: a multi-reviewer judge requires agreement in [0,1]")
                if not isinstance(judge.get("adjudication"), str) or not judge["adjudication"].strip():
                    errors.append(f"record {index}: a multi-reviewer judge requires an adjudication record")
        try:
            judge_prompt_hash = _hash_field(
                record.get("judge_prompt_sha256"),
                f"record {index} judge_prompt_sha256",
            )
            judgment_path, judgment_hash = _verify_evidence(
                evidence_root,
                record.get("judgment_path"),
                record.get("judgment_sha256"),
                f"record {index} judgment",
            )
            judgment = _load_json(judgment_path)
            if not isinstance(judgment, dict):
                raise ValueError(f"record {index} judgment must be a JSON object")
            bindings = {
                "execution_identity_sha256": computed_identity,
                "evidence_sha256": normalized.get("evidence_sha256"),
                "case_spec_sha256": case.get("case_spec_sha256"),
                "rubric_sha256": case.get("rubric_sha256"),
                "judge_prompt_sha256": judge_prompt_hash,
                "assertion_scores": scores,
                "judge": judge,
                "scored_at": record.get("scored_at"),
            }
            for field, expected in bindings.items():
                if judgment.get(field) != expected:
                    raise ValueError(f"record {index} judgment does not bind {field}")
            _validate_timestamp(record.get("scored_at"), f"record {index} scored_at")
            normalized["judgment_sha256"] = judgment_hash
            normalized["__judgment_absolute__"] = str(judgment_path)
        except ValueError as exc:
            errors.append(str(exc))
    return errors, normalized if not errors else None


def _trigger_metrics(records: Sequence[Mapping[str, Any]]) -> dict[str, float | int | None]:
    tp = sum(item["expected_trigger"] and item["predicted_trigger"] for item in records)
    tn = sum(not item["expected_trigger"] and not item["predicted_trigger"] for item in records)
    fp = sum(not item["expected_trigger"] and item["predicted_trigger"] for item in records)
    fn = sum(item["expected_trigger"] and not item["predicted_trigger"] for item in records)
    recall = _ratio(tp, tp + fn)
    specificity = _ratio(tn, tn + fp)
    balanced = (recall + specificity) / 2 if recall is not None and specificity is not None else None
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": _ratio(tp, tp + fp),
        "recall": recall,
        "specificity": specificity,
        "balanced_accuracy": balanced,
    }


def _bootstrap_trigger(
    records_by_case: Mapping[str, Sequence[Mapping[str, Any]]],
    draws: int,
    seed: int,
    confidence: float,
) -> dict[str, list[float] | None]:
    positive = [key for key, rows in records_by_case.items() if rows[0]["expected_trigger"]]
    negative = [key for key, rows in records_by_case.items() if not rows[0]["expected_trigger"]]
    if not positive or not negative:
        return {name: None for name in ("precision", "recall", "specificity", "balanced_accuracy")}
    generator = random.Random(seed)
    samples: dict[str, list[float]] = defaultdict(list)
    for _ in range(draws):
        selected = generator.choices(positive, k=len(positive)) + generator.choices(negative, k=len(negative))
        metrics = _trigger_metrics([record for key in selected for record in records_by_case[key]])
        for name in ("precision", "recall", "specificity", "balanced_accuracy"):
            value = metrics[name]
            if isinstance(value, float):
                samples[name].append(value)
    metric_names = {"precision", "recall", "specificity", "balanced_accuracy"}
    return {name: _interval(samples[name], confidence) for name in metric_names}


def _behavior_case_metrics(rows: Sequence[Mapping[str, Any]], critical_ids: set[str]) -> dict[str, float]:
    execution_means = [sum(row["assertion_scores"].values()) / len(row["assertion_scores"]) for row in rows]
    all_pass = [float(all(row["assertion_scores"].values())) for row in rows]
    critical = [float(any(not row["assertion_scores"][item] for item in critical_ids)) for row in rows]
    return {
        "case_mean_assertion_pass_rate": sum(execution_means) / len(execution_means),
        "case_all_pass_rate": sum(all_pass) / len(all_pass),
        "critical_violation_rate": sum(critical) / len(critical),
    }


def _bootstrap_behavior(
    case_metrics: Mapping[str, Mapping[str, float]],
    draws: int,
    seed: int,
    confidence: float,
) -> dict[str, list[float] | None]:
    case_ids = sorted(case_metrics)
    generator = random.Random(seed)
    values: dict[str, list[float]] = defaultdict(list)
    for _ in range(draws):
        selected = generator.choices(case_ids, k=len(case_ids))
        for name in ("case_mean_assertion_pass_rate", "case_all_pass_rate", "critical_violation_rate"):
            values[name].append(sum(case_metrics[item][name] for item in selected) / len(selected))
    return {name: _interval(samples, confidence) for name, samples in values.items()}


def score_records(
    records: Sequence[Mapping[str, Any]],
    manifest_path: Path,
    evidence_root: Path,
    *,
    records_sha256: str | None = None,
) -> dict[str, Any]:
    try:
        protocol = _load_protocol(manifest_path)
    except ValueError as exc:
        return {
            "score_schema_version": "2.0.0",
            "scorer_version": SCORER_VERSION,
            "valid": False,
            "evaluation_status": "invalid",
            "errors": [str(exc)],
            "summaries": [],
        }
    if not records:
        return {
            "score_schema_version": "2.0.0",
            "scorer_version": SCORER_VERSION,
            "manifest_sha256": protocol["manifest_sha256"],
            "records_sha256": records_sha256,
            "valid": False,
            "evaluation_status": "not_evaluated",
            "errors": ["no benchmark records were supplied"],
            "summaries": [],
        }

    errors: list[str] = []
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        record_errors, parsed = _validate_record(record, index, protocol, evidence_root)
        errors.extend(record_errors)
        if parsed is not None:
            normalized.append(parsed)
    if errors:
        return {
            "score_schema_version": "2.0.0",
            "scorer_version": SCORER_VERSION,
            "manifest_sha256": protocol["manifest_sha256"],
            "records_sha256": records_sha256,
            "valid": False,
            "evaluation_status": "invalid",
            "errors": errors,
            "summaries": [],
        }

    seen: set[tuple[Any, ...]] = set()
    evidence_bindings: dict[str, tuple[Any, ...]] = {}
    judgment_bindings: dict[str, tuple[Any, ...]] = {}
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for index, record in enumerate(normalized, start=1):
        identity = (
            record["manifest_sha256"],
            record["suite_id"],
            record["skill_release"],
            record["condition_id"],
            record["agent"],
            record["model"],
            record["runtime"],
            record["execution_config_sha256"],
            record["seed_control_status"],
            record["record_type"],
            record["case_id"],
            record["replicate"],
        )
        if identity in seen:
            errors.append(f"record {index}: duplicate execution identity {identity[1:]}")
        seen.add(identity)
        evidence_path = record["__evidence_absolute__"]
        if evidence_path in evidence_bindings and evidence_bindings[evidence_path] != identity:
            errors.append(f"record {index}: one evidence path is reused across execution identities")
        evidence_bindings[evidence_path] = identity
        judgment_path = record.get("__judgment_absolute__")
        if judgment_path:
            if judgment_path in judgment_bindings and judgment_bindings[judgment_path] != identity:
                errors.append(f"record {index}: one judgment path is reused across execution identities")
            judgment_bindings[judgment_path] = identity
        groups[identity[:-2]].append(record)
    if errors:
        return {
            "score_schema_version": "2.0.0",
            "scorer_version": SCORER_VERSION,
            "manifest_sha256": protocol["manifest_sha256"],
            "records_sha256": records_sha256,
            "valid": False,
            "evaluation_status": "invalid",
            "errors": errors,
            "summaries": [],
        }

    summaries: list[dict[str, Any]] = []
    completeness_errors: list[str] = []
    expected_suite_conditions = {
        (suite_id, condition_id)
        for suite_id, suite in protocol["suites"].items()
        if suite.get("scoring_backend") == "score.py"
        for condition_id in suite["conditions_by_id"]
    }
    present_suite_conditions = {
        (item["suite_id"], item["condition_id"]) for item in normalized
    }
    missing_suite_conditions = sorted(
        expected_suite_conditions - present_suite_conditions
    )
    for suite_id, condition_id in missing_suite_conditions:
        completeness_errors.append(
            f"suite={suite_id}, condition={condition_id} has no submitted executions"
        )
    for group_key, group in sorted(groups.items(), key=lambda item: tuple(str(value) for value in item[0])):
        (
            _,
            suite_id,
            skill_release,
            condition_id,
            agent,
            model,
            runtime,
            execution_config_sha256,
            seed_control_status,
            record_type,
        ) = group_key
        suite = protocol["suites"][suite_id]
        expected_pairs = {
            (case_id, replicate)
            for case_id in suite["cases_by_id"]
            for replicate in range(1, suite["repetitions"] + 1)
        }
        actual_pairs = {(item["case_id"], item["replicate"]) for item in group}
        missing = sorted(expected_pairs - actual_pairs)
        if missing:
            completeness_errors.append(
                f"suite={suite_id}, condition={condition_id}, agent={agent}, model={model}, runtime={runtime} is missing {len(missing)} case-replicate executions"
            )
        by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in group:
            by_case[item["case_id"]].append(item)
        interval_rule = suite["interval_rule"]
        base = {
            "suite_id": suite_id,
            "skill_release": skill_release,
            "condition_id": condition_id,
            "agent": agent,
            "model": model,
            "runtime": runtime,
            "execution_config_sha256": execution_config_sha256,
            "seed_control_status": seed_control_status,
            "record_type": record_type,
            "n_cases": len(by_case),
            "n_executions": len(group),
            "expected_executions": len(expected_pairs),
            "complete": not missing,
        }
        if record_type == "trigger":
            metrics = _trigger_metrics(group)
            intervals = _bootstrap_trigger(
                by_case,
                int(interval_rule["draws"]),
                int(interval_rule["seed"]),
                float(interval_rule["confidence"]),
            )
            base.update({"metrics": metrics, "intervals": intervals})
        else:
            case_metrics = {
                case_id: _behavior_case_metrics(
                    rows,
                    set(suite["cases_by_id"][case_id].get("critical_assertion_ids", [])),
                )
                for case_id, rows in by_case.items()
            }
            metrics = {
                name: _mean(item[name] for item in case_metrics.values())
                for name in ("case_mean_assertion_pass_rate", "case_all_pass_rate", "critical_violation_rate")
            }
            all_assertions = [value for item in group for value in item["assertion_scores"].values()]
            metrics["assertion_micro_pass_rate_diagnostic"] = _mean(float(value) for value in all_assertions)
            intervals = _bootstrap_behavior(
                case_metrics,
                int(interval_rule["draws"]),
                int(interval_rule["seed"]),
                float(interval_rule["confidence"]),
            )
            base.update({"metrics": metrics, "intervals": intervals})
        summaries.append(base)

    evidence_index = sorted(
        {
            (item["evidence_path"], item["evidence_sha256"], item.get("judgment_path"), item.get("judgment_sha256"))
            for item in normalized
        }
    )
    complete = not completeness_errors
    return {
        "score_schema_version": "2.0.0",
        "scorer_version": SCORER_VERSION,
        "manifest_sha256": protocol["manifest_sha256"],
        "records_sha256": records_sha256,
        "evidence_index_sha256": _canonical_hash(evidence_index),
        "protocol_coverage": {
            "expected_suite_conditions": [list(item) for item in sorted(expected_suite_conditions)],
            "present_suite_conditions": [list(item) for item in sorted(present_suite_conditions)],
            "missing_suite_conditions": [list(item) for item in missing_suite_conditions],
        },
        "valid": complete,
        "evaluation_status": "complete" if complete else "partial",
        "errors": completeness_errors,
        "summaries": summaries,
    }


def _self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="scientific-autoresearch-score-") as temporary:
        root = Path(temporary)
        repo = root / "repo"
        benchmark = repo / "benchmarks"
        evidence = root / "evidence"
        cases_dir = repo / "cases"
        benchmark.mkdir(parents=True)
        evidence.mkdir()
        cases_dir.mkdir()
        trigger_cases = [
            {"id": "positive", "query": "positive", "should_trigger": True},
            {"id": "negative", "query": "negative", "should_trigger": False},
        ]
        behavior_cases = {
            "evals": [
                {
                    "id": "behavior",
                    "prompt": "behavior",
                    "assertions": ["required behavior", "critical safeguard"],
                    "assertion_ids": ["a01", "a02"],
                    "critical_assertion_ids": ["a02"],
                }
            ]
        }
        trigger_path = cases_dir / "trigger.json"
        behavior_path = cases_dir / "behavior.json"
        trigger_path.write_text(json.dumps(trigger_cases), encoding="utf-8")
        behavior_path.write_text(json.dumps(behavior_cases), encoding="utf-8")
        manifest = {
            "benchmark_schema_version": "2.0.0",
            "record_schema_version": "2.0.0",
            "scorer_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
            "suites": [
                {
                    "suite_id": "trigger",
                    "protocol_status": "frozen",
                    "record_type": "trigger",
                    "scoring_backend": "score.py",
                    "case_source": {"path": "cases/trigger.json", "sha256": hashlib.sha256(trigger_path.read_bytes()).hexdigest(), "collection_key": None, "case_id_field": "id", "prompt_field": "query"},
                    "conditions": [{"condition_id": "current", "skill_release": "test", "skill_package_sha256": "sha256:" + "1" * 64}],
                    "repetitions": 1,
                    "interval_rule": {
                        "method": "stratified_case_cluster_bootstrap",
                        "draws": 20,
                        "seed": 1,
                        "confidence": 0.95,
                    },
                },
                {
                    "suite_id": "behavior",
                    "protocol_status": "frozen",
                    "record_type": "behavioral",
                    "scoring_backend": "score.py",
                    "case_source": {"path": "cases/behavior.json", "sha256": hashlib.sha256(behavior_path.read_bytes()).hexdigest(), "collection_key": "evals", "case_id_field": "id", "prompt_field": "prompt"},
                    "conditions": [{"condition_id": "current", "skill_release": "test", "skill_package_sha256": "sha256:" + "1" * 64}],
                    "repetitions": 1,
                    "interval_rule": {
                        "method": "case_cluster_bootstrap",
                        "draws": 20,
                        "seed": 1,
                        "confidence": 0.95,
                    },
                },
            ],
        }
        manifest_path = benchmark / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        protocol = _load_protocol(manifest_path)
        records: list[dict[str, Any]] = []
        common = {
            "record_schema_version": "2.0.0",
            "manifest_sha256": protocol["manifest_sha256"],
            "condition_id": "current",
            "skill_release": "test",
            "skill_package_sha256": "sha256:" + "1" * 64,
            "replicate": 1,
            "agent": "self-test",
            "model": "self-test",
            "runtime": "self-test",
            "execution_config_sha256": "sha256:" + "3" * 64,
            "generation_seed": 1,
            "seed_control_status": "controlled",
        }
        for case_id, predicted in (("positive", True), ("negative", False)):
            output = evidence / f"{case_id}.txt"
            output.write_text(case_id, encoding="utf-8")
            case = protocol["suites"]["trigger"]["cases_by_id"][case_id]
            record = {
                    **common,
                    "suite_id": "trigger",
                    "record_type": "trigger",
                    "case_id": case_id,
                    "case_spec_sha256": case["case_spec_sha256"],
                    "prompt_sha256": case["prompt_sha256"],
                    "evidence_path": output.name,
                    "evidence_sha256": _sha256_file(output),
                    "predicted_trigger": predicted,
                }
            record["execution_identity_sha256"] = _execution_identity_hash(record)
            records.append(record)
        output = evidence / "behavior.txt"
        output.write_text("behavior", encoding="utf-8")
        case = protocol["suites"]["behavior"]["cases_by_id"]["behavior"]
        scores = {"a01": True, "a02": True}
        judge = {"kind": "deterministic", "id": "self-test", "version": "1", "panel_size": 1}
        judge_prompt_hash = "sha256:" + "2" * 64
        scored_at = "2000-01-01T00:00:00Z"
        behavior_record = {
            **common,
            "suite_id": "behavior",
            "record_type": "behavioral",
            "case_id": "behavior",
            "case_spec_sha256": case["case_spec_sha256"],
            "prompt_sha256": case["prompt_sha256"],
            "evidence_path": output.name,
            "evidence_sha256": _sha256_file(output),
            "rubric_sha256": case["rubric_sha256"],
            "assertion_scores": scores,
            "judge": judge,
            "judge_prompt_sha256": judge_prompt_hash,
            "scored_at": scored_at,
        }
        behavior_record["execution_identity_sha256"] = _execution_identity_hash(
            behavior_record
        )
        judgment = {
            "execution_identity_sha256": behavior_record["execution_identity_sha256"],
            "evidence_sha256": _sha256_file(output),
            "case_spec_sha256": case["case_spec_sha256"],
            "rubric_sha256": case["rubric_sha256"],
            "judge_prompt_sha256": judge_prompt_hash,
            "assertion_scores": scores,
            "judge": judge,
            "scored_at": scored_at,
        }
        judgment_path = evidence / "behavior-judgment.json"
        judgment_path.write_text(json.dumps(judgment), encoding="utf-8")
        records.append(
            {
                **behavior_record,
                "judgment_path": judgment_path.name,
                "judgment_sha256": _sha256_file(judgment_path),
            }
        )
        result = score_records(records, manifest_path, evidence)
        trigger = next(item for item in result.get("summaries", []) if item["record_type"] == "trigger")
        behavior = next(item for item in result.get("summaries", []) if item["record_type"] == "behavioral")
        passed = (
            result.get("valid") is True
            and trigger["metrics"]["balanced_accuracy"] == 1.0
            and behavior["metrics"]["case_mean_assertion_pass_rate"] == 1.0
        )
        return {"self_test": "passed" if passed else "failed", "result": result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="?", type=Path, help="Version-2 JSON Lines records.")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.json"))
    parser.add_argument("--evidence-root", type=Path, help="Root containing bound raw outputs and judgments.")
    parser.add_argument("--output", type=Path, help="Optional scored result JSON.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic scorer fixtures.")
    args = parser.parse_args()
    if args.self_test:
        result = _self_test()
    else:
        if args.records is None:
            parser.error("records is required unless --self-test is used")
        if args.evidence_root is None:
            parser.error("--evidence-root is required for hash-bound scoring")
        try:
            records = _load_jsonl(args.records)
            result = score_records(
                records,
                args.manifest,
                args.evidence_root,
                records_sha256=_sha256_file(args.records),
            )
        except (OSError, ValueError) as exc:
            result = {
                "score_schema_version": "2.0.0",
                "scorer_version": SCORER_VERSION,
                "valid": False,
                "evaluation_status": "invalid",
                "errors": [str(exc)],
                "summaries": [],
            }
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    success = result.get("self_test") == "passed" if args.self_test else result.get("valid") is True
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
