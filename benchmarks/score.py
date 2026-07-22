#!/usr/bin/env python3
"""Aggregate standardized benchmark records without executing an agent."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_FIELDS = {
    "suite_id",
    "release",
    "condition",
    "case_id",
    "replicate",
    "agent",
    "model",
    "runtime",
    "output_hash",
    "record_type",
}


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return sum(items) / len(items) if items else None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
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
    return records


def _validate_record(record: Mapping[str, Any], index: int) -> list[str]:
    errors = [
        f"record {index}: missing {field}"
        for field in sorted(REQUIRED_FIELDS)
        if record.get(field) in (None, "")
    ]
    record_type = record.get("record_type")
    if record_type == "trigger":
        if not isinstance(record.get("expected_trigger"), bool):
            errors.append(f"record {index}: trigger record needs Boolean expected_trigger")
        if not isinstance(record.get("predicted_trigger"), bool):
            errors.append(f"record {index}: trigger record needs Boolean predicted_trigger")
    elif record_type == "behavioral":
        scores = record.get("assertion_scores")
        if not isinstance(scores, list) or not scores or any(
            not isinstance(score, bool) for score in scores
        ):
            errors.append(f"record {index}: behavioral record needs nonempty Boolean assertion_scores")
        violations = record.get("critical_violations", 0)
        if not isinstance(violations, int) or isinstance(violations, bool) or violations < 0:
            errors.append(f"record {index}: critical_violations must be a nonnegative integer")
    else:
        errors.append(f"record {index}: unsupported record_type {record_type!r}")
    replicate = record.get("replicate")
    if not isinstance(replicate, int) or isinstance(replicate, bool) or replicate < 1:
        errors.append(f"record {index}: replicate must be a positive integer")
    output_hash = str(record.get("output_hash", ""))
    if not output_hash.startswith("sha256:") or len(output_hash) != 71:
        errors.append(f"record {index}: output_hash must use sha256:<64hex>")
    else:
        try:
            int(output_hash.removeprefix("sha256:"), 16)
        except ValueError:
            errors.append(f"record {index}: output_hash contains nonhexadecimal characters")
    return errors


def aggregate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    seen: set[tuple[str, str, str, int]] = set()
    groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for index, record in enumerate(records, start=1):
        errors.extend(_validate_record(record, index))
        key = (
            str(record.get("suite_id", "")),
            str(record.get("condition", "")),
            str(record.get("case_id", "")),
            int(record.get("replicate", 0))
            if isinstance(record.get("replicate"), int)
            and not isinstance(record.get("replicate"), bool)
            else 0,
        )
        if key in seen:
            errors.append(f"record {index}: duplicate suite/condition/case/replicate key {key}")
        seen.add(key)
        groups[(key[0], key[1], str(record.get("record_type", "")))].append(record)
    if errors:
        return {"valid": False, "errors": errors, "summaries": []}

    summaries: list[dict[str, Any]] = []
    for (suite_id, condition, record_type), group in sorted(groups.items()):
        if record_type == "trigger":
            tp = sum(record["expected_trigger"] and record["predicted_trigger"] for record in group)
            tn = sum(not record["expected_trigger"] and not record["predicted_trigger"] for record in group)
            fp = sum(not record["expected_trigger"] and record["predicted_trigger"] for record in group)
            fn = sum(record["expected_trigger"] and not record["predicted_trigger"] for record in group)
            recall = _ratio(tp, tp + fn)
            specificity = _ratio(tn, tn + fp)
            summaries.append(
                {
                    "suite_id": suite_id,
                    "condition": condition,
                    "record_type": record_type,
                    "n": len(group),
                    "tp": tp,
                    "tn": tn,
                    "fp": fp,
                    "fn": fn,
                    "precision": _ratio(tp, tp + fp),
                    "recall": recall,
                    "specificity": specificity,
                    "balanced_accuracy": _mean(
                        value for value in (recall, specificity) if value is not None
                    ),
                }
            )
        else:
            assertion_scores = [
                score for record in group for score in record["assertion_scores"]
            ]
            all_pass = [all(record["assertion_scores"]) for record in group]
            critical = [record.get("critical_violations", 0) > 0 for record in group]
            summaries.append(
                {
                    "suite_id": suite_id,
                    "condition": condition,
                    "record_type": record_type,
                    "n": len(group),
                    "assertion_count": len(assertion_scores),
                    "assertion_pass_rate": _ratio(sum(assertion_scores), len(assertion_scores)),
                    "case_all_pass_rate": _ratio(sum(all_pass), len(all_pass)),
                    "critical_violation_rate": _ratio(sum(critical), len(critical)),
                }
            )
    return {"valid": True, "errors": [], "summaries": summaries}


def _self_test() -> dict[str, Any]:
    base = {
        "suite_id": "self-test",
        "release": "0.0.0",
        "condition": "test",
        "agent": "test",
        "model": "test",
        "runtime": "test",
        "output_hash": "sha256:" + "0" * 64,
    }
    records = [
        {**base, "case_id": "p", "replicate": 1, "record_type": "trigger", "expected_trigger": True, "predicted_trigger": True},
        {**base, "case_id": "n", "replicate": 1, "record_type": "trigger", "expected_trigger": False, "predicted_trigger": False},
        {**base, "case_id": "b", "replicate": 1, "record_type": "behavioral", "assertion_scores": [True, False], "critical_violations": 1},
    ]
    result = aggregate(records)
    trigger = next(item for item in result.get("summaries", []) if item["record_type"] == "trigger")
    behavioral = next(item for item in result.get("summaries", []) if item["record_type"] == "behavioral")
    passed = (
        result.get("valid") is True
        and math.isclose(trigger["balanced_accuracy"], 1.0)
        and math.isclose(behavioral["assertion_pass_rate"], 0.5)
        and math.isclose(behavioral["critical_violation_rate"], 1.0)
    )
    return {"self_test": "passed" if passed else "failed", "result": result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="?", type=Path, help="Standardized JSON Lines records.")
    parser.add_argument("--output", type=Path, help="Optional aggregate JSON output.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic scorer fixtures.")
    args = parser.parse_args()
    if args.self_test:
        result = _self_test()
    else:
        if args.records is None:
            parser.error("records is required unless --self-test is used")
        try:
            result = aggregate(_load_jsonl(args.records))
        except (OSError, ValueError) as exc:
            result = {"valid": False, "errors": [str(exc)], "summaries": []}
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    success = result.get("self_test") == "passed" if args.self_test else result.get("valid") is True
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
