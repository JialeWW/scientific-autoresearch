#!/usr/bin/env python3
"""Run the non-development protocol-2.1.1 execution shakedown fixture."""

from __future__ import annotations

import argparse
import hashlib
import io
import importlib.util
import json
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
SCORER_PATH = HERE / "score-v2.1.1.py"
SPEC = importlib.util.spec_from_file_location(
    "scientific_autoresearch_benchmark_score_2_1_1", SCORER_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load protocol-2.1.1 scorer")
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )


def safe_stem(*parts: object) -> str:
    text = "--".join(str(part) for part in parts)
    return "".join(character if character.isalnum() or character in "-_." else "_" for character in text)


def load_package_receipt(
    repository_root: Path,
    condition: Mapping[str, Any],
) -> dict[str, Any]:
    assurance = condition["package_assurance"]
    if condition.get("skill_release") is None:
        if assurance["mode"] != "not_applicable":
            raise ValueError("no-skill condition must not load a package")
        return {
            "load_status": "not_applicable",
            "skill_release": None,
            "behavior_package_sha256": None,
            "artifact_sha256": None,
            "skill_md_sha256": None,
        }
    if assurance["mode"] != "artifact_verified":
        raise ValueError("the shakedown requires artifact-verified package material")
    artifact = assurance["artifact"]
    package_path = score._safe_relative_file(
        repository_root,
        artifact["path"],
        "shakedown package artifact",
    )
    package_payload = score._stable_file_bytes(
        package_path,
        "shakedown package artifact",
        maximum_bytes=128 * 1024 * 1024,
    )
    artifact_sha256 = score._sha256_bytes(package_payload)
    if artifact_sha256 != artifact["sha256"]:
        raise ValueError("shakedown package artifact SHA-256 mismatch")
    package_sha256 = score._behavior_package_digest_from_zip_bytes(package_payload)
    if package_sha256 != condition["skill_package_sha256"]:
        raise ValueError("shakedown behavior-package digest mismatch")
    with zipfile.ZipFile(io.BytesIO(package_payload)) as archive:
        skill_bytes = archive.read("SKILL.md")
    return {
        "load_status": "loaded_from_verified_artifact",
        "skill_release": condition["skill_release"],
        "behavior_package_sha256": package_sha256,
        "artifact_sha256": artifact_sha256,
        "skill_md_sha256": "sha256:" + hashlib.sha256(skill_bytes).hexdigest(),
    }


def attempt_record(
    *,
    protocol: Mapping[str, Any],
    suite: Mapping[str, Any],
    block: Mapping[str, Any],
    condition_id: str,
    case_id: str,
    replicate: int,
    attempt: int,
    run_status: str,
    started_at: datetime,
    completed_at: datetime,
    evidence_root: Path,
    package_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    condition = suite["conditions_by_id"][condition_id]
    case = suite["cases_by_id"][case_id]
    order = block["order_by_pair"][(case_id, replicate)]
    stem = safe_stem(
        suite["suite_id"],
        block["comparison_block_id"],
        condition_id,
        case_id,
        replicate,
        attempt,
    )
    response: dict[str, Any] | None = None
    if run_status == "completed" and suite["record_type"] == "trigger":
        response = {"predicted_trigger": bool(case["should_trigger"])}
    elif run_status == "completed":
        response = {
            "assertion_scores": {str(item): True for item in case["assertion_ids"]}
        }
    evidence = {
        "fixture_evidence_schema_version": "1.0.0",
        "execution_purpose": "execution_shakedown",
        "suite_id": suite["suite_id"],
        "comparison_block_id": block["comparison_block_id"],
        "condition_id": condition_id,
        "case_id": case_id,
        "replicate": replicate,
        "attempt": attempt,
        "run_status": run_status,
        "package_load_receipt": dict(package_receipt),
        "fixture_response": response,
        "failure": None if run_status == "completed" else f"injected_{run_status}",
    }
    evidence_path = evidence_root / f"{stem}.json"
    write_json(evidence_path, evidence)
    identity_text = "|".join(
        str(value)
        for value in (
            suite["suite_id"],
            block["comparison_block_id"],
            condition_id,
            case_id,
            replicate,
            attempt,
        )
    )
    record = {
        "record_schema_version": score.RECORD_SCHEMA_VERSION,
        "manifest_sha256": protocol["manifest_sha256"],
        "suite_id": suite["suite_id"],
        "comparison_block_id": block["comparison_block_id"],
        "run_batch_id": block["run_batch_id"],
        "condition_id": condition_id,
        "skill_release": condition.get("skill_release"),
        "skill_package_sha256": condition.get("skill_package_sha256"),
        "case_id": case_id,
        "replicate": replicate,
        "attempt": attempt,
        "agent": block["executor_identity"]["agent"],
        "model": block["executor_identity"]["model"],
        "runtime": block["executor_identity"]["runtime"],
        "execution_config_path": block["execution_config_ref"]["path"],
        "execution_config_schema_version": block["execution_config_ref"][
            "schema_version"
        ],
        "execution_config_sha256": block["execution_config_ref"]["sha256"],
        "generation_seed": block["seed_by_pair"][(case_id, replicate)],
        "seed_control_status": block["seed_control_status"],
        "run_status": run_status,
        "run_order_index": order.index(condition_id) + 1,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "session_identity_sha256": "sha256:"
        + hashlib.sha256(("session|" + identity_text).encode("utf-8")).hexdigest(),
        "record_type": suite["record_type"],
        "case_spec_sha256": case["case_spec_sha256"],
        "prompt_sha256": case["prompt_sha256"],
        "evidence_path": evidence_path.name,
        "evidence_sha256": sha256_file(evidence_path),
    }
    if run_status == "completed" and suite["record_type"] == "trigger":
        record.update(
            {
                "predicted_trigger": response["predicted_trigger"],
                "routing_protocol_id": block["routing_protocol"]["routing_protocol_id"],
                "routing_protocol_sha256": block["routing_protocol_ref"]["sha256"],
                "routing_extractor": dict(
                    block["routing_protocol"]["extractor_identity"]
                ),
                "scored_at": completed_at.isoformat(),
            }
        )
    elif run_status == "completed":
        record.update(
            {
                "assertion_scores": response["assertion_scores"],
                "rubric_sha256": case["rubric_sha256"],
                "judge_protocol_id": block["judge_protocol"]["judge_protocol_id"],
                "judge_protocol_sha256": block["judge_protocol_ref"]["sha256"],
                "judge": dict(block["judge_protocol"]["judge_identity"]),
                "scored_at": completed_at.isoformat(),
            }
        )
    record["execution_identity_sha256"] = score._execution_identity_hash(record)
    if run_status == "completed" and suite["record_type"] == "trigger":
        judgment = {
            "execution_identity_sha256": record["execution_identity_sha256"],
            "evidence_sha256": record["evidence_sha256"],
            "case_spec_sha256": record["case_spec_sha256"],
            "prompt_sha256": record["prompt_sha256"],
            "routing_protocol_id": record["routing_protocol_id"],
            "routing_protocol_sha256": record["routing_protocol_sha256"],
            "routing_extractor": record["routing_extractor"],
            "predicted_trigger": record["predicted_trigger"],
            "scored_at": record["scored_at"],
        }
        judgment_path = evidence_root / f"{stem}--routing-judgment.json"
        write_json(judgment_path, judgment)
        record["judgment_path"] = judgment_path.name
        record["judgment_sha256"] = sha256_file(judgment_path)
    elif run_status == "completed":
        judgment = {
            "execution_identity_sha256": record["execution_identity_sha256"],
            "evidence_sha256": record["evidence_sha256"],
            "case_spec_sha256": record["case_spec_sha256"],
            "rubric_sha256": record["rubric_sha256"],
            "judge_protocol_id": record["judge_protocol_id"],
            "judge_protocol_sha256": record["judge_protocol_sha256"],
            "assertion_scores": record["assertion_scores"],
            "judge": record["judge"],
            "scored_at": record["scored_at"],
        }
        judgment_path = evidence_root / f"{stem}--behavioral-judgment.json"
        write_json(judgment_path, judgment)
        record["judgment_path"] = judgment_path.name
        record["judgment_sha256"] = sha256_file(judgment_path)
    return record


def run(manifest_path: Path, output_root: Path) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError("output root must be absent or empty for an immutable shakedown")
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_root = output_root / "evidence"
    evidence_root.mkdir()
    protocol = score._load_protocol(manifest_path)
    manifest = protocol["manifest"]
    if manifest.get("manifest_kind") != "execution":
        raise ValueError("shakedown requires an execution manifest")
    if manifest.get("execution_purpose") != "execution_shakedown":
        raise ValueError("shakedown manifest has the wrong execution purpose")
    repository_root = protocol["repository_root"]
    harness_relative = str(Path(__file__).resolve().relative_to(repository_root))
    records: list[dict[str, Any]] = []
    package_receipts: dict[tuple[str, str], dict[str, Any]] = {}
    virtual_base = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
    pair_counter = 0
    injected_infrastructure_retry = False
    injected_agent_failure = False

    for suite_id in sorted(protocol["suites"]):
        suite = protocol["suites"][suite_id]
        if suite.get("scoring_backend") != "score.py":
            continue
        if suite["case_source"]["role"] != "shakedown":
            raise ValueError("shakedown cannot consume development or sealed cases")
        for block_id in sorted(suite["comparison_blocks_by_id"]):
            block = suite["comparison_blocks_by_id"][block_id]
            harness_artifact = block["harness_assurance"].get("artifact")
            if (
                block["harness_assurance"]["mode"] != "artifact_verified"
                or harness_artifact is None
                or harness_artifact["path"] != harness_relative
            ):
                raise ValueError("the shakedown must bind and run this harness artifact")
            for condition_id in block["condition_ids"]:
                package_receipts[(suite_id, condition_id)] = load_package_receipt(
                    repository_root,
                    suite["conditions_by_id"][condition_id],
                )
            for case_id, replicate in sorted(block["expected_pairs"]):
                pair_start = virtual_base + timedelta(minutes=pair_counter * 3)
                pair_counter += 1
                for order_index, condition_id in enumerate(
                    block["order_by_pair"][(case_id, replicate)], start=1
                ):
                    first_start = pair_start + timedelta(seconds=(order_index - 1) * 20)
                    inject_retry = (
                        not injected_infrastructure_retry
                        and suite["record_type"] == "trigger"
                        and order_index == 1
                    )
                    inject_agent_failure = (
                        not injected_agent_failure
                        and suite["record_type"] == "behavioral"
                        and order_index == 1
                    )
                    if inject_retry:
                        records.append(
                            attempt_record(
                                protocol=protocol,
                                suite=suite,
                                block=block,
                                condition_id=condition_id,
                                case_id=case_id,
                                replicate=replicate,
                                attempt=1,
                                run_status="harness_error",
                                started_at=first_start,
                                completed_at=first_start + timedelta(seconds=2),
                                evidence_root=evidence_root,
                                package_receipt=package_receipts[(suite_id, condition_id)],
                            )
                        )
                        records.append(
                            attempt_record(
                                protocol=protocol,
                                suite=suite,
                                block=block,
                                condition_id=condition_id,
                                case_id=case_id,
                                replicate=replicate,
                                attempt=2,
                                run_status="completed",
                                started_at=first_start + timedelta(seconds=3),
                                completed_at=first_start + timedelta(seconds=5),
                                evidence_root=evidence_root,
                                package_receipt=package_receipts[(suite_id, condition_id)],
                            )
                        )
                        injected_infrastructure_retry = True
                    else:
                        status = "agent_error" if inject_agent_failure else "completed"
                        records.append(
                            attempt_record(
                                protocol=protocol,
                                suite=suite,
                                block=block,
                                condition_id=condition_id,
                                case_id=case_id,
                                replicate=replicate,
                                attempt=1,
                                run_status=status,
                                started_at=first_start,
                                completed_at=first_start + timedelta(seconds=2),
                                evidence_root=evidence_root,
                                package_receipt=package_receipts[(suite_id, condition_id)],
                            )
                        )
                        if inject_agent_failure:
                            injected_agent_failure = True

    if not injected_infrastructure_retry or not injected_agent_failure:
        raise ValueError("shakedown did not exercise both failure classes")
    records_path = output_root / "records.jsonl"
    with records_path.open("x", encoding="utf-8") as handle:
        handle.write(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
        )
    parsed_records, records_digest = score._load_jsonl_with_hash(records_path)
    if parsed_records != records:
        raise ValueError("serialized shakedown records do not round-trip")
    result = score.score_records(
        parsed_records,
        manifest_path,
        evidence_root,
        records_sha256=records_digest,
    )
    if not result.get("valid"):
        raise ValueError(f"shakedown scorer rejected the run: {result.get('errors')}")
    if (
        result.get("execution_purpose") != "execution_shakedown"
        or result.get("evidence_status") != "not_evaluated"
        or result.get("condition_summaries") != []
        or result.get("paired_comparisons") != []
    ):
        raise ValueError("shakedown result crossed the behavioral-evidence boundary")
    result_path = output_root / "result.json"
    write_json(result_path, result)
    receipt = {
        "execution_receipt_schema_version": "1.0.0",
        "assurance": "runner_attested",
        "execution_manifest_id": manifest["execution_manifest_id"],
        "execution_purpose": "execution_shakedown",
        "manifest_sha256": protocol["manifest_sha256"],
        "scorer_sha256": sha256_file(SCORER_PATH),
        "harness_sha256": sha256_file(Path(__file__).resolve()),
        "records_sha256": records_digest,
        "result_sha256": sha256_file(result_path),
        "evidence_tree_sha256": result["evidence_tree_sha256"],
        "attempt_count": len(records),
        "injected_failure_classes": ["infrastructure_retry", "agent_failure"],
        "clock_mode": "deterministic_fixture",
        "statement": "This receipt attests to the local fixture execution; it is not independent or cryptographic assurance and is not behavioral evidence.",
    }
    receipt_path = output_root / "execution-receipt.json"
    write_json(receipt_path, receipt)
    return {
        "shakedown_status": "passed",
        "evidence_status": "not_evaluated",
        "attempt_count": len(records),
        "records_path": str(records_path),
        "result_path": str(result_path),
        "receipt_path": str(receipt_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=HERE / "execution-manifest-shakedown-v2.1.1.json",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=HERE / "executions" / "shakedown-v2.1.1",
    )
    args = parser.parse_args()
    try:
        result = run(args.manifest, args.output_root)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"shakedown_status": "failed", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
