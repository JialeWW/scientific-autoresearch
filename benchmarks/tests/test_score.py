from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "score.py"
SPEC = importlib.util.spec_from_file_location(
    "scientific_autoresearch_benchmark_score", MODULE_PATH
)
assert SPEC and SPEC.loader
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)


class BenchmarkFixture:
    def __init__(
        self,
        *,
        repetitions: int = 2,
        seed_status: str = "enforced",
        block_copies: int = 1,
    ) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="benchmark-score-test-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.benchmarks = self.repo / "benchmarks"
        self.cases = self.repo / "cases"
        self.artifacts = self.repo / "artifacts"
        self.evidence = self.root / "evidence"
        for directory in (self.benchmarks, self.cases, self.artifacts, self.evidence):
            directory.mkdir(parents=True, exist_ok=True)
        self.repetitions = repetitions
        self.seed_status = seed_status
        self.block_copies = block_copies
        self.conditions = ["target", "previous", "legacy", "no-skill"]
        self.condition_specs = [
            {
                "condition_id": "target",
                "skill_release": "test-target",
                "skill_package_sha256": "sha256:" + "1" * 64,
            },
            {
                "condition_id": "previous",
                "skill_release": "test-previous",
                "skill_package_sha256": "sha256:" + "2" * 64,
            },
            {
                "condition_id": "legacy",
                "skill_release": "test-legacy",
                "skill_package_sha256": "sha256:" + "3" * 64,
            },
            {
                "condition_id": "no-skill",
                "skill_release": None,
                "skill_package_sha256": None,
            },
        ]
        self.trigger_cases = [
            {"id": "positive", "query": "positive prompt", "should_trigger": True},
            {"id": "positive-2", "query": "second positive prompt", "should_trigger": True},
            {"id": "negative", "query": "negative prompt", "should_trigger": False},
            {"id": "negative-2", "query": "second negative prompt", "should_trigger": False},
        ]
        self.behavior_cases = {
            "evals": [
                {
                    "id": "short",
                    "prompt": "short prompt",
                    "assertions": ["short assertion"],
                    "assertion_ids": ["a01"],
                    "critical_assertion_ids": ["a01"],
                },
                {
                    "id": "long",
                    "prompt": "long prompt",
                    "assertions": ["one", "two", "three"],
                    "assertion_ids": ["a01", "a02", "a03"],
                    "critical_assertion_ids": ["a03"],
                },
            ]
        }
        self.write_protocol()

    def close(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def raw_sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def prefixed_sha(path: Path) -> str:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

    def artifact_ref(self, path: Path, schema_version: str = "1.0.0") -> dict[str, str]:
        return {
            "path": str(path.relative_to(self.repo)),
            "schema_version": schema_version,
            "sha256": self.prefixed_sha(path),
        }

    def write_protocol(self) -> None:
        trigger_path = self.cases / "trigger.json"
        behavior_path = self.cases / "behavior.json"
        trigger_path.write_text(json.dumps(self.trigger_cases), encoding="utf-8")
        behavior_path.write_text(json.dumps(self.behavior_cases), encoding="utf-8")
        self.config = {
            "execution_config_schema_version": "1.0.0",
            "shared_execution_config": {
                "harness_identity": {
                    "id": "fixture-harness",
                    "version": "1",
                    "sha256_or_immutable_version": "fixture-harness@1",
                    "attestation_mode": "immutable_version",
                },
                "generation_parameters": {"temperature": 0},
                "tool_policy": "frozen fixture policy",
                "context_policy": "fresh fixture context",
                "timeout_seconds": 60,
                "isolated_sessions": True,
            },
        }
        self.config_path = self.artifacts / "execution-config.json"
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.judge_prompt_path = self.artifacts / "judge-prompt.txt"
        self.judge_prompt_path.write_text("frozen judge prompt\n", encoding="utf-8")
        self.judge_protocol = {
            "judge_protocol_schema_version": "1.0.0",
            "judge_protocol_id": "judge-protocol-1",
            "judge_identity": {
                "kind": "deterministic",
                "id": "fixture-judge",
                "version": "1",
                "panel_size": 1,
            },
            "prompt_artifact": {
                "path": str(self.judge_prompt_path.relative_to(self.repo)),
                "sha256": self.prefixed_sha(self.judge_prompt_path),
            },
            "rubric_version": "fixture-rubric-1",
            "blinding": "condition labels hidden from the judge",
            "adjudication_policy": "single frozen judgment; no adjudication",
            "independent_judgments_per_output": 1,
        }
        self.judge_path = self.artifacts / "judge-protocol.json"
        self.judge_path.write_text(json.dumps(self.judge_protocol), encoding="utf-8")
        self.routing_protocol = {
            "routing_protocol_schema_version": "1.0.0",
            "routing_protocol_id": "routing-protocol-1",
            "extractor_identity": {
                "kind": "deterministic",
                "id": "fixture-routing-extractor",
                "version": "1",
            },
            "decision_rule": "Read the frozen Boolean trigger decision from the output.",
        }
        self.routing_path = self.artifacts / "routing-protocol.json"
        self.routing_path.write_text(
            json.dumps(self.routing_protocol), encoding="utf-8"
        )

        def suite_blocks(suite_id: str, case_ids: list[str], behavioral: bool) -> list[dict]:
            blocks = []
            for block_index in range(self.block_copies):
                suffix = chr(ord("a") + block_index)
                block_id = f"{suite_id}-block-{suffix}"
                assignments = [
                    {
                        "case_id": case_id,
                        "replicate": replicate,
                        "generation_seed": (
                            1000 + replicate if self.seed_status != "unavailable" else None
                        ),
                    }
                    for case_id in case_ids
                    for replicate in range(1, self.repetitions + 1)
                ]
                seed_path = self.artifacts / f"{block_id}-seed.json"
                seed_path.write_text(
                    json.dumps(
                        {
                            "seed_schedule_schema_version": "1.0.0",
                            "comparison_block_id": block_id,
                            "seed_control_status": self.seed_status,
                            "assignments": assignments,
                        }
                    ),
                    encoding="utf-8",
                )
                order_path = self.artifacts / f"{block_id}-order.json"
                order_seed = 77 + block_index
                pair_list = [
                    (case_id, replicate)
                    for case_id in case_ids
                    for replicate in range(1, self.repetitions + 1)
                ]
                balanced_orders = score._balanced_condition_orders(
                    self.conditions,
                    pair_list,
                    order_seed,
                )
                order_path.write_text(
                    json.dumps(
                        {
                            "order_schedule_schema_version": "1.0.0",
                            "comparison_block_id": block_id,
                            "generation_method": "seeded_balanced_rotation_v1",
                            "order_generation_seed": order_seed,
                            "assignments": [
                                {
                                    "case_id": case_id,
                                    "replicate": replicate,
                                    "condition_order": balanced_orders[
                                        (case_id, replicate)
                                    ],
                                }
                                for case_id in case_ids
                                for replicate in range(1, self.repetitions + 1)
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                blocks.append(
                    {
                        "comparison_block_id": block_id,
                        "run_batch_id": f"batch-{block_id}",
                        "protocol_status": "frozen",
                        "condition_ids": self.conditions,
                        "contrasts": [
                            {
                                "contrast_id": f"target-minus-{condition}",
                                "target_condition_id": "target",
                                "reference_condition_id": condition,
                            }
                            for condition in self.conditions
                            if condition != "target"
                        ],
                        "executor_identity": {
                            "agent": "agent-a",
                            "model": "model-a",
                            "runtime": "runtime-a",
                        },
                        "execution_config_artifact": self.artifact_ref(self.config_path),
                        "seed_control_status": self.seed_status,
                        "seed_schedule_artifact": self.artifact_ref(seed_path),
                        "order_schedule_artifact": self.artifact_ref(order_path),
                        "judge_protocol_artifact": (
                            self.artifact_ref(self.judge_path) if behavioral else None
                        ),
                        "routing_protocol_artifact": (
                            None if behavioral else self.artifact_ref(self.routing_path)
                        ),
                        "isolation_policy": "fresh_context_per_attempt",
                        "max_pair_window_seconds": 120,
                        "evidence_status_on_complete": "development_suite_evaluated",
                    }
                )
            return blocks

        common_policy = {
            "repetitions": self.repetitions,
            "tie_rule": {"unit": "case_mean", "absolute_delta_threshold": 0.0},
            "missing_run_policy": "comparison_incomplete_no_paired_delta",
            "failure_retry_policy": {
                "maximum_infrastructure_retries": 1,
                "retry_eligible_statuses": [
                    "harness_error",
                    "provider_error",
                    "cancelled_before_execution",
                ],
                "retain_all_attempts": True,
                "scoring_attempt_selection_rule": "first_non_retry_eligible_attempt",
                "agent_failure_scoring": "zero_credit",
            },
        }
        self.manifest = {
            "benchmark_schema_version": "2.1.0",
            "benchmark_protocol_version": "2.1.0",
            "record_schema_version": "2.1.0",
            "scorer_sha256": self.raw_sha(MODULE_PATH),
            "suites": [
                {
                    "suite_id": "trigger",
                    "protocol_status": "frozen",
                    "record_type": "trigger",
                    "scoring_backend": "score.py",
                    "evidence_type": "behavioral_conformance",
                    "target": "fixture trigger routing",
                    "case_source": {
                        "path": "cases/trigger.json",
                        "sha256": self.prefixed_sha(trigger_path),
                        "collection_key": None,
                        "case_id_field": "id",
                        "prompt_field": "query",
                        "role": "development",
                    },
                    "conditions": self.condition_specs,
                    "evaluation_unit": "one fixture case in one isolated execution attempt",
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
                    "interval_rule": {
                        "method": "paired_stratified_case_cluster_bootstrap",
                        "bootstrap_unit": "case",
                        "draws": 40,
                        "seed": 1,
                        "confidence": 0.95,
                    },
                    "comparison_blocks": suite_blocks(
                        "trigger", [item["id"] for item in self.trigger_cases], False
                    ),
                    **common_policy,
                },
                {
                    "suite_id": "behavior",
                    "protocol_status": "frozen",
                    "record_type": "behavioral",
                    "scoring_backend": "score.py",
                    "evidence_type": "behavioral_conformance",
                    "target": "fixture safeguard behavior",
                    "case_source": {
                        "path": "cases/behavior.json",
                        "sha256": self.prefixed_sha(behavior_path),
                        "collection_key": "evals",
                        "case_id_field": "id",
                        "prompt_field": "prompt",
                        "role": "development",
                    },
                    "conditions": self.condition_specs,
                    "evaluation_unit": "one fixture case in one isolated execution attempt",
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
                    "interval_rule": {
                        "method": "paired_case_cluster_bootstrap",
                        "bootstrap_unit": "case",
                        "draws": 40,
                        "seed": 2,
                        "confidence": 0.95,
                    },
                    "comparison_blocks": suite_blocks(
                        "behavior",
                        [item["id"] for item in self.behavior_cases["evals"]],
                        True,
                    ),
                    **common_policy,
                },
            ],
        }
        self.manifest_path = self.benchmarks / "manifest.json"
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.protocol = score._load_protocol(self.manifest_path)

    def block_ids(self, suite_id: str) -> list[str]:
        return sorted(self.protocol["suites"][suite_id]["comparison_blocks_by_id"])

    def common_record(
        self,
        suite_id: str,
        block_id: str,
        condition_id: str,
        case_id: str,
        replicate: int,
        *,
        attempt: int = 1,
        run_status: str = "completed",
    ) -> dict[str, object]:
        suite = self.protocol["suites"][suite_id]
        block = suite["comparison_blocks_by_id"][block_id]
        condition = suite["conditions_by_id"][condition_id]
        case_index = sorted(suite["cases_by_id"]).index(case_id)
        condition_order = block["order_by_pair"][(case_id, replicate)]
        condition_index = condition_order.index(condition_id)
        block_index = self.block_ids(suite_id).index(block_id)
        start = datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(
            days=block_index,
            minutes=(case_index * self.repetitions + replicate - 1) * 2,
            seconds=condition_index * 10 + (attempt - 1) * 45,
        )
        identity_text = (
            f"{suite_id}|{block_id}|{condition_id}|{case_id}|{replicate}|{attempt}"
        )
        return {
            "record_schema_version": "2.1.0",
            "manifest_sha256": self.protocol["manifest_sha256"],
            "suite_id": suite_id,
            "comparison_block_id": block_id,
            "run_batch_id": block["run_batch_id"],
            "condition_id": condition_id,
            "skill_release": condition.get("skill_release"),
            "skill_package_sha256": condition.get("skill_package_sha256"),
            "case_id": case_id,
            "replicate": replicate,
            "attempt": attempt,
            "agent": "agent-a",
            "model": "model-a",
            "runtime": "runtime-a",
            "execution_config_path": block["execution_config_ref"]["path"],
            "execution_config_schema_version": block["execution_config_ref"][
                "schema_version"
            ],
            "execution_config_sha256": block["execution_config_ref"]["sha256"],
            "generation_seed": block["seed_by_pair"][(case_id, replicate)],
            "seed_control_status": self.seed_status,
            "run_status": run_status,
            "run_order_index": condition_index + 1,
            "started_at": start.isoformat(),
            "completed_at": (start + timedelta(seconds=2)).isoformat(),
            "session_identity_sha256": "sha256:"
            + hashlib.sha256(identity_text.encode()).hexdigest(),
            "record_type": suite["record_type"],
            "case_spec_sha256": suite["cases_by_id"][case_id]["case_spec_sha256"],
            "prompt_sha256": suite["cases_by_id"][case_id]["prompt_sha256"],
        }

    def write_evidence(self, record: dict[str, object]) -> None:
        stem = "-".join(
            str(record[field])
            for field in (
                "suite_id",
                "comparison_block_id",
                "condition_id",
                "case_id",
                "replicate",
                "attempt",
            )
        )
        output = self.evidence / f"{stem}.txt"
        output.write_text(f"{stem}:{record['run_status']}", encoding="utf-8")
        record["evidence_path"] = output.name
        record["evidence_sha256"] = self.prefixed_sha(output)

    def trigger_record(
        self,
        block_id: str,
        condition_id: str,
        case_id: str,
        replicate: int,
        *,
        attempt: int = 1,
        run_status: str = "completed",
    ) -> dict[str, object]:
        record = self.common_record(
            "trigger",
            block_id,
            condition_id,
            case_id,
            replicate,
            attempt=attempt,
            run_status=run_status,
        )
        self.write_evidence(record)
        if run_status == "completed":
            truth = self.protocol["suites"]["trigger"]["cases_by_id"][case_id][
                "should_trigger"
            ]
            record["predicted_trigger"] = (
                truth if condition_id in {"target", "previous"} else not truth
            )
            block = self.protocol["suites"]["trigger"]["comparison_blocks_by_id"][
                block_id
            ]
            record.update(
                {
                    "routing_protocol_id": block["routing_protocol"][
                        "routing_protocol_id"
                    ],
                    "routing_protocol_sha256": block["routing_protocol_ref"]["sha256"],
                    "routing_extractor": dict(
                        block["routing_protocol"]["extractor_identity"]
                    ),
                    "scored_at": record["completed_at"],
                }
            )
            record["execution_identity_sha256"] = score._execution_identity_hash(record)
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
            judgment_path = self.evidence / (
                Path(str(record["evidence_path"])).stem + "-routing.json"
            )
            judgment_path.write_text(json.dumps(judgment), encoding="utf-8")
            record["judgment_path"] = judgment_path.name
            record["judgment_sha256"] = self.prefixed_sha(judgment_path)
        else:
            record["execution_identity_sha256"] = score._execution_identity_hash(record)
        return record

    def behavior_record(
        self,
        block_id: str,
        condition_id: str,
        case_id: str,
        replicate: int,
        *,
        attempt: int = 1,
        run_status: str = "completed",
    ) -> dict[str, object]:
        record = self.common_record(
            "behavior",
            block_id,
            condition_id,
            case_id,
            replicate,
            attempt=attempt,
            run_status=run_status,
        )
        self.write_evidence(record)
        if run_status == "completed":
            suite = self.protocol["suites"]["behavior"]
            case = suite["cases_by_id"][case_id]
            passed = condition_id in {"target", "previous"}
            scores = {str(item): passed for item in case["assertion_ids"]}
            block = suite["comparison_blocks_by_id"][block_id]
            judge = dict(block["judge_protocol"]["judge_identity"])
            record.update(
                {
                    "rubric_sha256": case["rubric_sha256"],
                    "assertion_scores": scores,
                    "judge_protocol_id": block["judge_protocol"]["judge_protocol_id"],
                    "judge_protocol_sha256": block["judge_protocol_ref"]["sha256"],
                    "judge": judge,
                    "scored_at": record["completed_at"],
                }
            )
            record["execution_identity_sha256"] = score._execution_identity_hash(record)
            judgment = {
                "execution_identity_sha256": record["execution_identity_sha256"],
                "evidence_sha256": record["evidence_sha256"],
                "case_spec_sha256": case["case_spec_sha256"],
                "rubric_sha256": case["rubric_sha256"],
                "judge_protocol_id": record["judge_protocol_id"],
                "judge_protocol_sha256": record["judge_protocol_sha256"],
                "assertion_scores": scores,
                "judge": judge,
                "scored_at": record["scored_at"],
            }
            judgment_path = self.evidence / (
                Path(str(record["evidence_path"])).stem + "-judgment.json"
            )
            judgment_path.write_text(json.dumps(judgment), encoding="utf-8")
            record["judgment_path"] = judgment_path.name
            record["judgment_sha256"] = self.prefixed_sha(judgment_path)
        else:
            record["execution_identity_sha256"] = score._execution_identity_hash(record)
        return record

    def all_records(self) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for block_id in self.block_ids("trigger"):
            for case_id in sorted(self.protocol["suites"]["trigger"]["cases_by_id"]):
                for replicate in range(1, self.repetitions + 1):
                    for condition_id in self.conditions:
                        records.append(
                            self.trigger_record(
                                block_id, condition_id, case_id, replicate
                            )
                        )
        for block_id in self.block_ids("behavior"):
            for case_id in sorted(self.protocol["suites"]["behavior"]["cases_by_id"]):
                for replicate in range(1, self.repetitions + 1):
                    for condition_id in self.conditions:
                        records.append(
                            self.behavior_record(
                                block_id, condition_id, case_id, replicate
                            )
                        )
        return records

    def recompute_identity(self, record: dict[str, object]) -> None:
        record["execution_identity_sha256"] = score._execution_identity_hash(record)
        if record.get("run_status") != "completed" or "judgment_path" not in record:
            return
        if record.get("record_type") == "trigger":
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
            suffix = "routing"
        else:
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
            suffix = "judgment"
        judgment_path = self.evidence / (
            Path(str(record["evidence_path"])).stem + f"-{suffix}.json"
        )
        judgment_path.write_text(json.dumps(judgment), encoding="utf-8")
        record["judgment_path"] = judgment_path.name
        record["judgment_sha256"] = self.prefixed_sha(judgment_path)

    @staticmethod
    def strip_outcome_fields(record: dict[str, object]) -> None:
        for field in (
            "predicted_trigger",
            "routing_protocol_id",
            "routing_protocol_sha256",
            "routing_extractor",
            "assertion_scores",
            "rubric_sha256",
            "judge_protocol_id",
            "judge_protocol_sha256",
            "judge",
            "scored_at",
            "judgment_path",
            "judgment_sha256",
        ):
            record.pop(field, None)

    def score(self, records: list[dict[str, object]]) -> dict[str, object]:
        return score.score_records(records, self.manifest_path, self.evidence)


class ScoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = BenchmarkFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def comparison(self, result: dict, suite_id: str, contrast_id: str) -> dict:
        return next(
            item
            for item in result["paired_comparisons"]
            if item["suite_id"] == suite_id and item["contrast_id"] == contrast_id
        )

    def test_complete_four_condition_blocks_produce_paired_deltas(self) -> None:
        result = self.fixture.score(self.fixture.all_records())
        self.assertTrue(result["valid"])
        self.assertEqual(result["scoring_status"], "complete")
        self.assertEqual(result["evidence_status"], "development_suite_evaluated")
        trigger = self.comparison(result, "trigger", "target-minus-no-skill")
        behavior = self.comparison(result, "behavior", "target-minus-no-skill")
        self.assertEqual(trigger["point_estimates"]["trigger_balanced_accuracy_delta"], 1.0)
        self.assertEqual(behavior["point_estimates"]["behavioral_case_macro_delta"], 1.0)
        self.assertEqual(
            behavior["point_estimates"]["critical_violation_risk_difference"], -1.0
        )

    def test_repository_manifest_loads_without_frozen_execution_blocks(self) -> None:
        protocol = score._load_protocol(MODULE_PATH.with_name("manifest.json"))
        self.assertEqual(protocol["manifest"]["release_under_test"], "0.2.8")
        self.assertTrue(
            all(
                not suite.get("comparison_blocks_by_id")
                for suite in protocol["suites"].values()
                if suite.get("scoring_backend") == "score.py"
            )
        )

    def test_empty_records_are_not_evaluated(self) -> None:
        result = self.fixture.score([])
        self.assertFalse(result["valid"])
        self.assertEqual(result["scoring_status"], "not_evaluated")

    def test_missing_condition_cell_suppresses_only_that_block_deltas(self) -> None:
        records = self.fixture.all_records()
        removed = records.pop(0)
        result = self.fixture.score(records)
        self.assertFalse(result["valid"])
        self.assertEqual(result["scoring_status"], "comparison_incomplete")
        self.assertFalse(
            any(
                item["comparison_block_id"] == removed["comparison_block_id"]
                for item in result["paired_comparisons"]
            )
        )

    def test_block_rejects_mixed_executor_identity(self) -> None:
        records = self.fixture.all_records()
        records[0]["model"] = "different-model"
        self.fixture.recompute_identity(records[0])
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(any("model differs" in item for item in result["errors"]))

    def test_attempt_record_rejects_unfrozen_execution_field(self) -> None:
        records = self.fixture.all_records()
        records[0]["temperature"] = 1
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(
            any("record does not use the closed schema" in item for item in result["errors"])
        )

    def test_modified_execution_config_artifact_is_rejected(self) -> None:
        self.fixture.config["shared_execution_config"]["generation_parameters"][
            "temperature"
        ] = 1
        self.fixture.config_path.write_text(json.dumps(self.fixture.config), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "execution config SHA-256 mismatch"):
            score._load_protocol(self.fixture.manifest_path)

    def test_condition_specific_execution_config_is_rejected(self) -> None:
        self.fixture.config["condition_overrides"] = {
            "target": {"temperature": 0},
            "previous": {"temperature": 1},
        }
        self.fixture.config_path.write_text(json.dumps(self.fixture.config), encoding="utf-8")
        ref = self.fixture.manifest["suites"][0]["comparison_blocks"][0][
            "execution_config_artifact"
        ]
        ref["sha256"] = self.fixture.prefixed_sha(self.fixture.config_path)
        self.fixture.manifest_path.write_text(json.dumps(self.fixture.manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "condition-specific"):
            score._load_protocol(self.fixture.manifest_path)

    def test_nested_condition_specific_execution_config_is_rejected(self) -> None:
        self.fixture.config["shared_execution_config"]["generation_parameters"] = {
            "temperature": 0,
            "condition_overrides": {"target": {"temperature": 1}},
        }
        self.fixture.config_path.write_text(
            json.dumps(self.fixture.config), encoding="utf-8"
        )
        ref = self.fixture.manifest["suites"][0]["comparison_blocks"][0][
            "execution_config_artifact"
        ]
        ref["sha256"] = self.fixture.prefixed_sha(self.fixture.config_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "condition-specific"):
            score._load_protocol(self.fixture.manifest_path)

    def test_list_style_condition_value_in_shared_config_is_rejected(self) -> None:
        self.fixture.config["shared_execution_config"]["generation_parameters"] = [
            {"label": "target"}
        ]
        self.fixture.config_path.write_text(
            json.dumps(self.fixture.config), encoding="utf-8"
        )
        ref = self.fixture.manifest["suites"][0]["comparison_blocks"][0][
            "execution_config_artifact"
        ]
        ref["sha256"] = self.fixture.prefixed_sha(self.fixture.config_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "condition-specific"):
            score._load_protocol(self.fixture.manifest_path)

    def test_condition_schema_rejects_extra_treatment_field(self) -> None:
        self.fixture.manifest["suites"][0]["conditions"][0]["temperature"] = 1
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "condition.*closed schema"):
            score._load_protocol(self.fixture.manifest_path)

    def test_manifest_schema_rejects_top_level_condition_override(self) -> None:
        self.fixture.manifest["condition_overrides"] = {
            "target": {"temperature": 1}
        }
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "closed top-level schema"):
            score._load_protocol(self.fixture.manifest_path)

    def test_comparison_block_schema_rejects_condition_override(self) -> None:
        self.fixture.manifest["suites"][0]["comparison_blocks"][0][
            "condition_overrides"
        ] = {"target": {"temperature": 1}}
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "comparison block.*closed schema"):
            score._load_protocol(self.fixture.manifest_path)

    def test_judge_protocol_schema_rejects_unknown_condition_field(self) -> None:
        self.fixture.judge_protocol["target_temperature"] = 1
        self.fixture.judge_path.write_text(
            json.dumps(self.fixture.judge_protocol), encoding="utf-8"
        )
        behavior = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "behavior"
        )
        behavior["comparison_blocks"][0]["judge_protocol_artifact"][
            "sha256"
        ] = self.fixture.prefixed_sha(self.fixture.judge_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "judge protocol.*closed schema"):
            score._load_protocol(self.fixture.manifest_path)

    def test_structured_redactions_cannot_hide_execution_settings(self) -> None:
        self.fixture.config["redactions"] = {
            "target": {"temperature": 1}
        }
        self.fixture.config_path.write_text(
            json.dumps(self.fixture.config), encoding="utf-8"
        )
        ref = self.fixture.manifest["suites"][0]["comparison_blocks"][0][
            "execution_config_artifact"
        ]
        ref["sha256"] = self.fixture.prefixed_sha(self.fixture.config_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "redactions must be"):
            score._load_protocol(self.fixture.manifest_path)

    def test_harness_requires_immutable_binding(self) -> None:
        self.fixture.config["shared_execution_config"]["harness_identity"].pop(
            "sha256_or_immutable_version"
        )
        self.fixture.config_path.write_text(
            json.dumps(self.fixture.config), encoding="utf-8"
        )
        ref = self.fixture.manifest["suites"][0]["comparison_blocks"][0][
            "execution_config_artifact"
        ]
        ref["sha256"] = self.fixture.prefixed_sha(self.fixture.config_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "harness identity"):
            score._load_protocol(self.fixture.manifest_path)

    def test_order_schedule_must_match_balanced_generator(self) -> None:
        block = self.fixture.manifest["suites"][0]["comparison_blocks"][0]
        order_path = self.fixture.repo / block["order_schedule_artifact"]["path"]
        order = json.loads(order_path.read_text(encoding="utf-8"))
        first = order["assignments"][0]["condition_order"]
        first[0], first[1] = first[1], first[0]
        order_path.write_text(json.dumps(order), encoding="utf-8")
        block["order_schedule_artifact"]["sha256"] = self.fixture.prefixed_sha(
            order_path
        )
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "balanced generator"):
            score._load_protocol(self.fixture.manifest_path)

    def test_seed_mismatch_is_rejected(self) -> None:
        records = self.fixture.all_records()
        records[0]["generation_seed"] = 999
        self.fixture.recompute_identity(records[0])
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(any("generation seed" in item for item in result["errors"]))

    def test_missing_seed_schedule_cell_is_rejected(self) -> None:
        block = self.fixture.manifest["suites"][0]["comparison_blocks"][0]
        seed_path = self.fixture.repo / block["seed_schedule_artifact"]["path"]
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        seed["assignments"].pop()
        seed_path.write_text(json.dumps(seed), encoding="utf-8")
        block["seed_schedule_artifact"]["sha256"] = self.fixture.prefixed_sha(seed_path)
        self.fixture.manifest_path.write_text(json.dumps(self.fixture.manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "seed schedule is incomplete"):
            score._load_protocol(self.fixture.manifest_path)

    def test_duplicate_seed_schedule_cell_is_rejected(self) -> None:
        block = self.fixture.manifest["suites"][0]["comparison_blocks"][0]
        seed_path = self.fixture.repo / block["seed_schedule_artifact"]["path"]
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        seed["assignments"].append(dict(seed["assignments"][0]))
        seed_path.write_text(json.dumps(seed), encoding="utf-8")
        block["seed_schedule_artifact"]["sha256"] = self.fixture.prefixed_sha(
            seed_path
        )
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "duplicate seed assignment"):
            score._load_protocol(self.fixture.manifest_path)

    def test_seed_schedule_replicate_container_is_rejected_without_crash(self) -> None:
        block = self.fixture.manifest["suites"][0]["comparison_blocks"][0]
        seed_path = self.fixture.repo / block["seed_schedule_artifact"]["path"]
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        seed["assignments"][0]["replicate"] = []
        seed_path.write_text(json.dumps(seed), encoding="utf-8")
        block["seed_schedule_artifact"]["sha256"] = self.fixture.prefixed_sha(
            seed_path
        )
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "replicate must be an integer"):
            score._load_protocol(self.fixture.manifest_path)

    def test_unavailable_seed_is_visible_and_valid(self) -> None:
        self.fixture.close()
        self.fixture = BenchmarkFixture(seed_status="unavailable")
        result = self.fixture.score(self.fixture.all_records())
        self.assertTrue(result["valid"])
        comparison = self.comparison(result, "trigger", "target-minus-no-skill")
        self.assertIn("without_guaranteed", comparison["seed_pairing"])

    def test_judge_protocol_mismatch_is_rejected(self) -> None:
        records = self.fixture.all_records()
        record = next(item for item in records if item["suite_id"] == "behavior")
        record["judge"]["id"] = "other-judge"
        self.fixture.recompute_identity(record)
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(any("judge.id" in item for item in result["errors"]))
        invalidated_block = str(record["comparison_block_id"])
        invalidated_result = next(
            item
            for item in result["block_results"]
            if item["comparison_block_id"] == invalidated_block
        )
        self.assertEqual(invalidated_result["status"], "invalidated")
        self.assertEqual(invalidated_result["missing_attempt_cells"], [])
        self.assertTrue(invalidated_result["invalid_attempt_records"])
        self.assertTrue(
            any(item["suite_id"] == "trigger" for item in result["paired_comparisons"])
        )
        self.assertFalse(
            any(
                item["comparison_block_id"] == invalidated_block
                for item in result["paired_comparisons"]
            )
        )

    def test_trigger_prediction_is_bound_to_routing_judgment(self) -> None:
        records = self.fixture.all_records()
        record = next(item for item in records if item["suite_id"] == "trigger")
        record["predicted_trigger"] = not bool(record["predicted_trigger"])
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(
            any("routing judgment does not bind predicted_trigger" in item for item in result["errors"])
        )

    def test_actual_start_order_mismatch_blocks_comparison(self) -> None:
        records = self.fixture.all_records()
        trigger = [
            item
            for item in records
            if item["suite_id"] == "trigger"
            and item["case_id"] == "negative"
            and item["replicate"] == 1
            and item["comparison_block_id"] == self.fixture.block_ids("trigger")[0]
        ]
        target = next(item for item in trigger if item["condition_id"] == "target")
        previous = next(item for item in trigger if item["condition_id"] == "previous")
        target["started_at"], previous["started_at"] = (
            previous["started_at"],
            target["started_at"],
        )
        target["completed_at"], previous["completed_at"] = (
            previous["completed_at"],
            target["completed_at"],
        )
        self.fixture.recompute_identity(target)
        self.fixture.recompute_identity(previous)
        result = self.fixture.score(records)
        self.assertFalse(result["valid"])
        self.assertTrue(any("start order" in item for item in result["errors"]))
        trigger_block = self.fixture.block_ids("trigger")[0]
        block_result = next(
            item
            for item in result["block_results"]
            if item["comparison_block_id"] == trigger_block
        )
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertEqual(block_result["status"], "invalidated")
        self.assertFalse(block_result["paired_deltas_reported"])
        self.assertFalse(
            any(
                item["comparison_block_id"] == trigger_block
                for item in result["paired_comparisons"]
            )
        )

    def test_primary_estimand_name_mismatch_is_rejected(self) -> None:
        trigger = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "trigger"
        )
        trigger["primary_estimands"] = ["switched_after_results"]
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "primary_estimands"):
            score._load_protocol(self.fixture.manifest_path)

    def test_secondary_estimand_switch_is_rejected(self) -> None:
        trigger = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "trigger"
        )
        trigger["secondary_estimands"].append("post_outcome_metric")
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "secondary_estimands"):
            score._load_protocol(self.fixture.manifest_path)

    def test_uncertainty_design_must_match_estimable_levels(self) -> None:
        behavior = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "behavior"
        )
        behavior["uncertainty_design"]["judge_uncertainty"] = "estimated"
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "uncertainty_design"):
            score._load_protocol(self.fixture.manifest_path)

    def test_repeated_judgments_are_rejected_until_individual_evidence_exists(self) -> None:
        self.fixture.judge_protocol["independent_judgments_per_output"] = 2
        self.fixture.judge_path.write_text(
            json.dumps(self.fixture.judge_protocol), encoding="utf-8"
        )
        behavior = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "behavior"
        )
        behavior["comparison_blocks"][0]["judge_protocol_artifact"][
            "sha256"
        ] = self.fixture.prefixed_sha(self.fixture.judge_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "exactly one adjudicated judgment"):
            score._load_protocol(self.fixture.manifest_path)

    def test_agent_failure_gets_zero_credit_without_retry(self) -> None:
        records = self.fixture.all_records()
        record = next(
            item
            for item in records
            if item["suite_id"] == "trigger"
            and item["condition_id"] == "target"
            and item["case_id"] == "positive"
            and item["replicate"] == 1
        )
        record["run_status"] = "agent_error"
        self.fixture.strip_outcome_fields(record)
        self.fixture.recompute_identity(record)
        result = self.fixture.score(records)
        self.assertTrue(result["valid"])
        target_summary = next(
            item
            for item in result["condition_summaries"]
            if item["suite_id"] == "trigger"
            and item["condition_id"] == "target"
            and item["comparison_block_id"] == record["comparison_block_id"]
        )
        self.assertGreater(target_summary["metrics"]["agent_failure_rate"], 0)
        self.assertLess(
            target_summary["metrics"]["balanced_accuracy_zero_credit_failures"], 1
        )

    def test_agent_failure_cannot_be_retried(self) -> None:
        records = self.fixture.all_records()
        original = records[0]
        retry = self.fixture.trigger_record(
            str(original["comparison_block_id"]),
            str(original["condition_id"]),
            str(original["case_id"]),
            int(original["replicate"]),
            attempt=2,
        )
        original["run_status"] = "agent_timeout"
        self.fixture.strip_outcome_fields(original)
        self.fixture.recompute_identity(original)
        records.append(retry)
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(any("non-retry-eligible" in item for item in result["errors"]))

    def test_infrastructure_failure_retry_retains_both_attempts(self) -> None:
        records = self.fixture.all_records()
        original = records[0]
        retry = self.fixture.trigger_record(
            str(original["comparison_block_id"]),
            str(original["condition_id"]),
            str(original["case_id"]),
            int(original["replicate"]),
            attempt=2,
        )
        original["run_status"] = "provider_error"
        self.fixture.strip_outcome_fields(original)
        self.fixture.recompute_identity(original)
        records.append(retry)
        result = self.fixture.score(records)
        self.assertTrue(result["valid"])
        self.assertTrue(result["evidence_index_sha256"].startswith("sha256:"))
        summary = next(
            item
            for item in result["condition_summaries"]
            if item["suite_id"] == "trigger"
            and item["comparison_block_id"] == original["comparison_block_id"]
            and item["condition_id"] == original["condition_id"]
        )
        self.assertEqual(summary["diagnostics"]["infrastructure_retry_count"], 1)

    def test_nonretryable_terminal_infrastructure_failure_remains_unresolved(self) -> None:
        trigger_suite = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "trigger"
        )
        trigger_suite["failure_retry_policy"]["retry_eligible_statuses"] = [
            "provider_error"
        ]
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        self.fixture.protocol = score._load_protocol(self.fixture.manifest_path)
        records = self.fixture.all_records()
        record = next(
            item
            for item in records
            if item["suite_id"] == "trigger"
            and item["condition_id"] == "target"
        )
        record["run_status"] = "harness_error"
        self.fixture.strip_outcome_fields(record)
        self.fixture.recompute_identity(record)
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "comparison_incomplete")
        block_result = next(
            item
            for item in result["block_results"]
            if item["comparison_block_id"] == record["comparison_block_id"]
        )
        self.assertTrue(block_result["unresolved_infrastructure_cells"])
        self.assertFalse(block_result["paired_deltas_reported"])

    def test_delayed_score_bearing_retry_invalidates_block(self) -> None:
        records = self.fixture.all_records()
        original = records[0]
        retry = self.fixture.trigger_record(
            str(original["comparison_block_id"]),
            str(original["condition_id"]),
            str(original["case_id"]),
            int(original["replicate"]),
            attempt=2,
        )
        original["run_status"] = "provider_error"
        self.fixture.strip_outcome_fields(original)
        self.fixture.recompute_identity(original)
        delayed_start = datetime.fromisoformat(str(original["started_at"])) + timedelta(
            hours=1
        )
        retry["started_at"] = delayed_start.isoformat()
        retry["completed_at"] = (delayed_start + timedelta(seconds=2)).isoformat()
        retry["scored_at"] = retry["completed_at"]
        self.fixture.recompute_identity(retry)
        records.append(retry)
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(
            any("selected score-bearing attempts" in item for item in result["errors"])
        )

    def test_retry_cannot_start_before_prior_attempt_finishes(self) -> None:
        records = self.fixture.all_records()
        original = records[0]
        retry = self.fixture.trigger_record(
            str(original["comparison_block_id"]),
            str(original["condition_id"]),
            str(original["case_id"]),
            int(original["replicate"]),
            attempt=2,
        )
        original["run_status"] = "provider_error"
        self.fixture.strip_outcome_fields(original)
        self.fixture.recompute_identity(original)
        retry["started_at"] = original["started_at"]
        self.fixture.recompute_identity(retry)
        records.append(retry)
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(any("started before attempt" in item for item in result["errors"]))

    def test_infrastructure_retry_limit_is_enforced(self) -> None:
        records = self.fixture.all_records()
        base = records[0]
        base["run_status"] = "provider_error"
        self.fixture.strip_outcome_fields(base)
        self.fixture.recompute_identity(base)
        second = self.fixture.trigger_record(
            str(base["comparison_block_id"]),
            str(base["condition_id"]),
            str(base["case_id"]),
            int(base["replicate"]),
            attempt=2,
            run_status="provider_error",
        )
        third = self.fixture.trigger_record(
            str(base["comparison_block_id"]),
            str(base["condition_id"]),
            str(base["case_id"]),
            int(base["replicate"]),
            attempt=3,
        )
        records.extend([second, third])
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(any("retry limit" in item for item in result["errors"]))

    def test_pair_then_replicate_then_case_macro(self) -> None:
        result = self.fixture.score(self.fixture.all_records())
        comparison = self.comparison(result, "behavior", "target-minus-legacy")
        self.assertEqual(comparison["point_estimates"]["behavioral_case_macro_delta"], 1.0)
        self.assertEqual(comparison["win_loss_tie"]["wins"], 2)
        self.assertEqual(comparison["win_loss_tie"]["losses"], 0)

    def test_critical_violation_discordance_is_explicit(self) -> None:
        result = self.fixture.score(self.fixture.all_records())
        comparison = self.comparison(result, "behavior", "target-minus-no-skill")
        discordance = comparison["critical_violation_discordance"]
        self.assertEqual(discordance["reference_only"], 4)
        self.assertEqual(discordance["target_only"], 0)

    def test_single_judge_uncertainty_is_not_estimable(self) -> None:
        result = self.fixture.score(self.fixture.all_records())
        comparison = self.comparison(result, "behavior", "target-minus-previous")
        self.assertEqual(
            comparison["judge_uncertainty"], "not_estimable_under_current_design"
        )

    def test_multiple_blocks_are_never_pooled(self) -> None:
        self.fixture.close()
        self.fixture = BenchmarkFixture(block_copies=2)
        result = self.fixture.score(self.fixture.all_records())
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["block_results"]), 4)
        self.assertEqual(
            {item["comparison_block_id"] for item in result["paired_comparisons"]},
            set(self.fixture.block_ids("trigger") + self.fixture.block_ids("behavior")),
        )
        self.assertIn("never pooled", result["pooling_policy"])

    def test_schema_2_0_record_is_rejected_explicitly(self) -> None:
        records = self.fixture.all_records()
        records[0]["record_schema_version"] = "2.0.0"
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(any("unsupported record_schema_version" in item for item in result["errors"]))

    def test_boolean_replicate_does_not_alias_integer_one(self) -> None:
        records = self.fixture.all_records()
        records[0]["replicate"] = True
        self.fixture.recompute_identity(records[0])
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(any("replicate must be an integer" in item for item in result["errors"]))

    def test_unhashable_replicate_is_rejected_without_crash(self) -> None:
        records = self.fixture.all_records()
        records[0]["replicate"] = []
        self.fixture.recompute_identity(records[0])
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(
            any("replicate must be an integer" in item for item in result["errors"])
        )

    def test_string_judge_panel_size_is_rejected_without_crash(self) -> None:
        records = self.fixture.all_records()
        record = next(item for item in records if item["suite_id"] == "behavior")
        record["judge"]["panel_size"] = "1"
        self.fixture.recompute_identity(record)
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(
            any("judge.panel_size" in item for item in result["errors"])
        )

    def test_single_judge_record_rejects_unknown_metadata(self) -> None:
        records = self.fixture.all_records()
        record = next(item for item in records if item["suite_id"] == "behavior")
        record["judge"]["target_temperature"] = 1
        self.fixture.recompute_identity(record)
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(
            any("judge metadata does not use" in item for item in result["errors"])
        )

    def test_nonfinite_tie_threshold_is_rejected(self) -> None:
        text = json.dumps(self.fixture.manifest)
        text = text.replace('"absolute_delta_threshold": 0.0', '"absolute_delta_threshold": 1e309')
        self.fixture.manifest_path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "tie rule"):
            score._load_protocol(self.fixture.manifest_path)

    def test_behavioral_assertion_ids_must_be_nonempty_strings(self) -> None:
        behavior = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "behavior"
        )
        case_path = self.fixture.repo / behavior["case_source"]["path"]
        cases = json.loads(case_path.read_text(encoding="utf-8"))
        cases["evals"][0]["assertion_ids"] = [1]
        cases["evals"][0]["critical_assertion_ids"] = [1]
        case_path.write_text(json.dumps(cases), encoding="utf-8")
        behavior["case_source"]["sha256"] = self.fixture.prefixed_sha(case_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "assertion IDs"):
            score._load_protocol(self.fixture.manifest_path)

    def test_case_source_role_is_closed(self) -> None:
        self.fixture.manifest["suites"][0]["case_source"]["role"] = "private"
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "invalid role"):
            score._load_protocol(self.fixture.manifest_path)

    def test_trigger_truth_stratum_needs_two_cases(self) -> None:
        trigger = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "trigger"
        )
        case_path = self.fixture.repo / trigger["case_source"]["path"]
        cases = json.loads(case_path.read_text(encoding="utf-8"))
        retained_positive = next(item for item in cases if item["should_trigger"])
        retained_negative = [item for item in cases if not item["should_trigger"]]
        case_path.write_text(
            json.dumps([retained_positive, *retained_negative]), encoding="utf-8"
        )
        trigger["case_source"]["sha256"] = self.fixture.prefixed_sha(case_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "two cases in each truth class"):
            score._load_protocol(self.fixture.manifest_path)

    def test_trigger_one_case_per_truth_class_is_not_estimable(self) -> None:
        trigger = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "trigger"
        )
        case_path = self.fixture.repo / trigger["case_source"]["path"]
        cases = json.loads(case_path.read_text(encoding="utf-8"))
        retained = [
            next(item for item in cases if item["should_trigger"]),
            next(item for item in cases if not item["should_trigger"]),
        ]
        case_path.write_text(json.dumps(retained), encoding="utf-8")
        trigger["case_source"]["sha256"] = self.fixture.prefixed_sha(case_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "two cases in each truth class"):
            score._load_protocol(self.fixture.manifest_path)

    def test_collection_key_requires_object_case_registry(self) -> None:
        behavior = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "behavior"
        )
        case_path = self.fixture.repo / behavior["case_source"]["path"]
        case_path.write_text(json.dumps([]), encoding="utf-8")
        behavior["case_source"]["sha256"] = self.fixture.prefixed_sha(case_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "collection_key is set"):
            score._load_protocol(self.fixture.manifest_path)

    def test_single_behavioral_case_cannot_claim_case_cluster_uncertainty(self) -> None:
        behavior = next(
            item
            for item in self.fixture.manifest["suites"]
            if item["suite_id"] == "behavior"
        )
        case_path = self.fixture.repo / behavior["case_source"]["path"]
        cases = json.loads(case_path.read_text(encoding="utf-8"))
        cases["evals"] = cases["evals"][:1]
        case_path.write_text(json.dumps(cases), encoding="utf-8")
        behavior["case_source"]["sha256"] = self.fixture.prefixed_sha(case_path)
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "at least two cases"):
            score._load_protocol(self.fixture.manifest_path)

    def test_retry_status_container_is_rejected_without_crash(self) -> None:
        self.fixture.manifest["suites"][0]["failure_retry_policy"][
            "retry_eligible_statuses"
        ] = [{}]
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "invalid retry statuses"):
            score._load_protocol(self.fixture.manifest_path)

    def test_reused_session_is_rejected(self) -> None:
        records = self.fixture.all_records()
        records[1]["session_identity_sha256"] = records[0]["session_identity_sha256"]
        self.fixture.recompute_identity(records[1])
        result = self.fixture.score(records)
        self.assertEqual(result["scoring_status"], "invalidated")
        self.assertTrue(any("session identity was reused" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
