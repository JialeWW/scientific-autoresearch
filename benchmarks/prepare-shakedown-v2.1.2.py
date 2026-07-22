#!/usr/bin/env python3
"""Freeze the protocol-2.1.2 non-development shakedown execution."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parent
SCORER_PATH = HERE / "score-v2.1.2.py"
SOURCE_MANIFEST_PATH = HERE / "manifest-shakedown-v2.1.2.json"
HARNESS_PATH = HERE / "shakedown-harness-v2.1.2.py"
SPEC = importlib.util.spec_from_file_location(
    "scientific_autoresearch_benchmark_score_2_1_2_prepare", SCORER_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load protocol-2.1.2 scorer")
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)


def sha256_file(path: Path, *, prefixed: bool = True) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return "sha256:" + digest if prefixed else digest


def write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )


def artifact_ref(path: Path, schema_version: str) -> dict[str, str]:
    return {
        "path": str(path.resolve().relative_to(REPOSITORY_ROOT.resolve())),
        "schema_version": schema_version,
        "sha256": sha256_file(path),
    }


def freeze_suite(
    source_suite: dict[str, Any],
    *,
    suite_id: str,
    case_path: Path,
    collection_key: str | None,
    prompt_field: str,
    repetitions: int,
    block_id: str,
    order_seed: int,
    interval_seed: int,
    execution_config_path: Path,
    routing_path: Path | None,
    judge_path: Path | None,
) -> dict[str, Any]:
    suite = copy.deepcopy(source_suite)
    case_payload = score._stable_file_bytes(
        case_path,
        f"{suite_id} shakedown case source",
        maximum_bytes=16 * 1024 * 1024,
    )
    source_data = score._json_from_bytes(
        case_payload, f"{suite_id} shakedown case source"
    )
    suite["suite_id"] = suite_id
    suite["protocol_status"] = "frozen"
    suite["target"] = "non-development fixture coverage of the execution and scoring boundary"
    suite["case_source"] = {
        "path": str(case_path.resolve().relative_to(REPOSITORY_ROOT.resolve())),
        "sha256": score._sha256_bytes(case_payload),
        "collection_key": collection_key,
        "case_id_field": "id",
        "prompt_field": prompt_field,
        "role": "shakedown",
    }
    suite["repetitions"] = repetitions
    suite["interval_rule"]["draws"] = 40
    suite["interval_rule"]["seed"] = interval_seed
    suite["interpretation_scope_id"] = score.SHAKEDOWN_INTERPRETATION[
        "interpretation_scope_id"
    ]
    suite["interpretation_rule"] = score.SHAKEDOWN_INTERPRETATION[
        "interpretation_rule"
    ]
    cases = source_data[collection_key] if collection_key else source_data
    case_ids = [str(case["id"]) for case in cases]
    pairs = [
        (case_id, replicate)
        for case_id in case_ids
        for replicate in range(1, repetitions + 1)
    ]
    condition_ids = [str(condition["condition_id"]) for condition in suite["conditions"]]
    seed_path = execution_config_path.parent / f"{block_id}-seed-schedule.json"
    write_json(
        seed_path,
        {
            "seed_schedule_schema_version": "1.0.0",
            "comparison_block_id": block_id,
            "seed_control_status": "enforced",
            "assignments": [
                {
                    "case_id": case_id,
                    "replicate": replicate,
                    "generation_seed": 2_110_000 + index,
                }
                for index, (case_id, replicate) in enumerate(sorted(pairs), start=1)
            ],
        },
    )
    orders = score._balanced_condition_orders(condition_ids, pairs, order_seed)
    order_path = execution_config_path.parent / f"{block_id}-order-schedule.json"
    write_json(
        order_path,
        {
            "order_schedule_schema_version": "1.0.0",
            "comparison_block_id": block_id,
            "generation_method": "seeded_balanced_rotation_v1",
            "order_generation_seed": order_seed,
            "assignments": [
                {
                    "case_id": case_id,
                    "replicate": replicate,
                    "condition_order": orders[(case_id, replicate)],
                }
                for case_id, replicate in sorted(pairs)
            ],
        },
    )
    suite["comparison_blocks"] = [
        {
            "comparison_block_id": block_id,
            "run_batch_id": f"batch-{block_id}",
            "protocol_status": "frozen",
            "condition_ids": condition_ids,
            "contrasts": [
                {
                    "contrast_id": f"skill-v0.2.8-minus-{condition_id}",
                    "target_condition_id": "skill-v0.2.8",
                    "reference_condition_id": condition_id,
                }
                for condition_id in condition_ids
                if condition_id != "skill-v0.2.8"
            ],
            "executor_identity": {
                "agent": "deterministic-canary-fixture",
                "model": "no-model-fixture",
                "runtime": "python-3.12-stdlib-fixture-contract",
            },
            "execution_config_artifact": artifact_ref(execution_config_path, "1.1.0"),
            "seed_control_status": "enforced",
            "seed_schedule_artifact": artifact_ref(seed_path, "1.0.0"),
            "order_schedule_artifact": artifact_ref(order_path, "1.0.0"),
            "routing_protocol_artifact": (
                artifact_ref(routing_path, "1.0.0") if routing_path else None
            ),
            "judge_protocol_artifact": (
                artifact_ref(judge_path, "1.0.0") if judge_path else None
            ),
            "isolation_policy": "fresh_context_per_attempt",
            "max_pair_window_seconds": 120,
            "evidence_status_on_complete": "not_evaluated",
        }
    ]
    return suite


def prepare(output_manifest: Path, frozen_at: str) -> dict[str, Any]:
    if output_manifest.exists():
        raise ValueError("refusing to overwrite an immutable execution manifest")
    score._parse_timestamp(frozen_at, "frozen_at")
    source = score._load_protocol(SOURCE_MANIFEST_PATH)["manifest"]
    source_suites = {suite["suite_id"]: suite for suite in source["suites"]}
    artifact_root = HERE / "artifacts" / "shakedown-v2.1.2"
    if artifact_root.exists() and any(artifact_root.iterdir()):
        raise ValueError("refusing to overwrite frozen shakedown artifacts")
    artifact_root.mkdir(parents=True, exist_ok=True)
    execution_config_path = artifact_root / "execution-config.json"
    execution_config = {
        "execution_config_schema_version": "1.1.0",
        "shared_execution_config": {
            "harness_identity": {
                "id": "scientific-autoresearch-shakedown-harness",
                "version": "2.1.2",
                "assurance": {
                    "mode": "artifact_verified",
                    "artifact": {
                        "path": str(HARNESS_PATH.relative_to(REPOSITORY_ROOT)),
                        "sha256": sha256_file(HARNESS_PATH),
                        "format": "single-file-sha256-v1",
                    },
                    "attestation_artifact": None,
                },
            },
            "generation_parameters": {
                "fixture_mode": "deterministic",
                "temperature": 0,
            },
            "tool_policy": "no external tools; local artifact reads and writes only",
            "context_policy": "load exactly one package artifact per skill condition; load none for no-skill",
            "timeout_seconds": 60,
            "isolated_sessions": True,
        },
        "redactions": [],
    }
    write_json(execution_config_path, execution_config)
    routing_path = artifact_root / "routing-protocol.json"
    write_json(
        routing_path,
        {
            "routing_protocol_schema_version": "1.0.0",
            "routing_protocol_id": "deterministic-canary-routing-v1",
            "extractor_identity": {
                "kind": "deterministic",
                "id": "canary-json-routing-extractor",
                "version": "1",
            },
            "decision_rule": "Read the Boolean predicted_trigger field from the fixture response.",
        },
    )
    judge_prompt_path = HERE / "fixtures" / "shakedown-v2.1.2" / "judge-prompt.txt"
    judge_path = artifact_root / "judge-protocol.json"
    write_json(
        judge_path,
        {
            "judge_protocol_schema_version": "1.0.0",
            "judge_protocol_id": "deterministic-canary-judge-v1",
            "judge_identity": {
                "kind": "deterministic",
                "id": "canary-assertion-map-judge",
                "version": "1",
                "panel_size": 1,
            },
            "prompt_artifact": {
                "path": str(judge_prompt_path.relative_to(REPOSITORY_ROOT)),
                "sha256": sha256_file(judge_prompt_path),
            },
            "rubric_version": "canary-structure-v1",
            "blinding": "condition labels are not used by the deterministic fixture judge",
            "adjudication_policy": "single deterministic fixture judgment; no adjudication",
            "independent_judgments_per_output": 1,
        },
    )
    trigger_cases = HERE / "fixtures" / "shakedown-v2.1.2" / "trigger-canary.json"
    behavioral_cases = (
        HERE / "fixtures" / "shakedown-v2.1.2" / "behavioral-canary.json"
    )
    trigger_suite = freeze_suite(
        source_suites["shakedown-trigger-routing"],
        suite_id="shakedown-trigger-routing",
        case_path=trigger_cases,
        collection_key=None,
        prompt_field="query",
        repetitions=1,
        block_id="shakedown-trigger-block-v2.1.2",
        order_seed=2121,
        interval_seed=211101,
        execution_config_path=execution_config_path,
        routing_path=routing_path,
        judge_path=None,
    )
    behavioral_suite = freeze_suite(
        source_suites["shakedown-behavioral-routing"],
        suite_id="shakedown-behavioral-routing",
        case_path=behavioral_cases,
        collection_key="evals",
        prompt_field="prompt",
        repetitions=2,
        block_id="shakedown-behavioral-block-v2.1.2",
        order_seed=2122,
        interval_seed=211102,
        execution_config_path=execution_config_path,
        routing_path=None,
        judge_path=judge_path,
    )
    manifest = {
        "benchmark_schema_version": source["benchmark_schema_version"],
        "benchmark_protocol_version": source["benchmark_protocol_version"],
        "protocol_id": source["protocol_id"],
        "protocol_scope": source["protocol_scope"],
        "release_under_test": source["release_under_test"],
        "benchmark_status": "execution_shakedown_frozen",
        "manifest_kind": "execution",
        "execution_manifest_id": "scientific-autoresearch-shakedown-v2.1.2-20260722",
        "execution_purpose": "execution_shakedown",
        "frozen_at": frozen_at,
        "protocol_template_artifact": artifact_ref(
            SOURCE_MANIFEST_PATH, "2.1.2"
        ),
        "protocol_projection_profile": source["protocol_projection_profile"],
        "protocol_projection_sha256": source["protocol_projection_sha256"],
        "record_schema_version": "2.1.0",
        "scorer_sha256": sha256_file(SCORER_PATH, prefixed=False),
        "evaluation_state_vocabulary": source["evaluation_state_vocabulary"],
        "suites": [trigger_suite, behavioral_suite],
        "result_policy": source["result_policy"],
        "sealed_suite_policy": source["sealed_suite_policy"],
        "protocol_invalidation_policy": source["protocol_invalidation_policy"],
    }
    write_json(output_manifest, manifest)
    protocol = score._load_protocol(output_manifest)
    return {
        "execution_manifest_id": manifest["execution_manifest_id"],
        "execution_purpose": manifest["execution_purpose"],
        "manifest_path": str(output_manifest),
        "manifest_sha256": protocol["manifest_sha256"],
        "comparison_block_count": sum(
            len(suite.get("comparison_blocks_by_id", {}))
            for suite in protocol["suites"].values()
        ),
        "evidence_status_on_complete": "not_evaluated",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-manifest",
        type=Path,
        default=HERE / "execution-manifest-shakedown-v2.1.2.json",
    )
    parser.add_argument(
        "--frozen-at",
        default="2026-07-22T18:00:00+08:00",
    )
    args = parser.parse_args()
    try:
        result = prepare(args.output_manifest, args.frozen_at)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"prepare_status": "failed", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"prepare_status": "passed", **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
