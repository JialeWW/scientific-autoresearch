from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "score.py"
SPEC = importlib.util.spec_from_file_location("scientific_autoresearch_benchmark_score", MODULE_PATH)
assert SPEC and SPEC.loader
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)


class BenchmarkFixture:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="benchmark-score-test-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.benchmarks = self.repo / "benchmarks"
        self.cases = self.repo / "cases"
        self.evidence = self.root / "evidence"
        self.benchmarks.mkdir(parents=True)
        self.cases.mkdir()
        self.evidence.mkdir()
        self.package_hash = "sha256:" + "1" * 64
        self.trigger_cases = [
            {"id": "positive", "query": "positive prompt", "should_trigger": True},
            {"id": "negative", "query": "negative prompt", "should_trigger": False},
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

    def write_protocol(self, repetitions: int = 1) -> None:
        trigger_path = self.cases / "trigger.json"
        behavior_path = self.cases / "behavior.json"
        trigger_path.write_text(json.dumps(self.trigger_cases), encoding="utf-8")
        behavior_path.write_text(json.dumps(self.behavior_cases), encoding="utf-8")
        self.manifest = {
            "benchmark_schema_version": "2.0.0",
            "record_schema_version": "2.0.0",
            "scorer_sha256": self.raw_sha(MODULE_PATH),
            "suites": [
                {
                    "suite_id": "trigger",
                    "protocol_status": "frozen",
                    "record_type": "trigger",
                    "scoring_backend": "score.py",
                    "case_source": {
                        "path": "cases/trigger.json",
                        "sha256": self.raw_sha(trigger_path),
                        "collection_key": None,
                        "case_id_field": "id",
                        "prompt_field": "query",
                    },
                    "conditions": [
                        {
                            "condition_id": "current",
                            "skill_release": "test",
                            "skill_package_sha256": self.package_hash,
                        }
                    ],
                    "repetitions": repetitions,
                    "interval_rule": {
                        "method": "stratified_case_cluster_bootstrap",
                        "draws": 30,
                        "seed": 1,
                        "confidence": 0.95,
                    },
                },
                {
                    "suite_id": "behavior",
                    "protocol_status": "frozen",
                    "record_type": "behavioral",
                    "scoring_backend": "score.py",
                    "case_source": {
                        "path": "cases/behavior.json",
                        "sha256": self.raw_sha(behavior_path),
                        "collection_key": "evals",
                        "case_id_field": "id",
                        "prompt_field": "prompt",
                    },
                    "conditions": [
                        {
                            "condition_id": "current",
                            "skill_release": "test",
                            "skill_package_sha256": self.package_hash,
                        }
                    ],
                    "repetitions": repetitions,
                    "interval_rule": {
                        "method": "case_cluster_bootstrap",
                        "draws": 30,
                        "seed": 1,
                        "confidence": 0.95,
                    },
                },
                {
                    "suite_id": "empirical",
                    "protocol_status": "draft",
                    "record_type": "empirical",
                    "scoring_backend": "external",
                    "conditions": [
                        {
                            "condition_id": "current",
                            "skill_release": "test",
                            "skill_package_sha256": self.package_hash,
                        }
                    ],
                },
            ],
        }
        self.manifest_path = self.benchmarks / "manifest.json"
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.protocol = score._load_protocol(self.manifest_path)

    def common(self, model: str = "model-a") -> dict[str, object]:
        return {
            "record_schema_version": "2.0.0",
            "manifest_sha256": self.protocol["manifest_sha256"],
            "condition_id": "current",
            "skill_release": "test",
            "skill_package_sha256": self.package_hash,
            "replicate": 1,
            "agent": "agent-a",
            "model": model,
            "runtime": "runtime-a",
            "execution_config_sha256": "sha256:" + "3" * 64,
            "generation_seed": 1,
            "seed_control_status": "controlled",
        }

    def trigger_records(self, model: str = "model-a") -> list[dict[str, object]]:
        records = []
        for case_id, prediction in (("positive", True), ("negative", False)):
            case = self.protocol["suites"]["trigger"]["cases_by_id"][case_id]
            output = self.evidence / f"trigger-{model}-{case_id}.txt"
            output.write_text(f"{model}:{case_id}", encoding="utf-8")
            record = {
                **self.common(model),
                "suite_id": "trigger",
                "record_type": "trigger",
                "case_id": case_id,
                "case_spec_sha256": case["case_spec_sha256"],
                "prompt_sha256": case["prompt_sha256"],
                "evidence_path": output.name,
                "evidence_sha256": score._sha256_file(output),
                "predicted_trigger": prediction,
            }
            record["execution_identity_sha256"] = score._execution_identity_hash(record)
            records.append(record)
        return records

    def behavior_record(
        self,
        case_id: str,
        assertion_scores: dict[str, bool],
        model: str = "model-a",
    ) -> dict[str, object]:
        case = self.protocol["suites"]["behavior"]["cases_by_id"][case_id]
        output = self.evidence / f"behavior-{model}-{case_id}.txt"
        output.write_text(f"{model}:{case_id}", encoding="utf-8")
        judge = {"kind": "deterministic", "id": "judge", "version": "1", "panel_size": 1}
        judge_prompt_hash = "sha256:" + "2" * 64
        scored_at = "2000-01-01T00:00:00Z"
        record = {
            **self.common(model),
            "suite_id": "behavior",
            "record_type": "behavioral",
            "case_id": case_id,
            "case_spec_sha256": case["case_spec_sha256"],
            "prompt_sha256": case["prompt_sha256"],
            "evidence_path": output.name,
            "evidence_sha256": score._sha256_file(output),
            "rubric_sha256": case["rubric_sha256"],
            "assertion_scores": assertion_scores,
            "judge": judge,
            "judge_prompt_sha256": judge_prompt_hash,
            "scored_at": scored_at,
        }
        record["execution_identity_sha256"] = score._execution_identity_hash(record)
        judgment = {
            "execution_identity_sha256": record["execution_identity_sha256"],
            "evidence_sha256": score._sha256_file(output),
            "case_spec_sha256": case["case_spec_sha256"],
            "rubric_sha256": case["rubric_sha256"],
            "judge_prompt_sha256": judge_prompt_hash,
            "assertion_scores": assertion_scores,
            "judge": judge,
            "scored_at": scored_at,
        }
        judgment_path = self.evidence / f"behavior-{model}-{case_id}-judgment.json"
        judgment_path.write_text(json.dumps(judgment), encoding="utf-8")
        return {
            **record,
            "judgment_path": judgment_path.name,
            "judgment_sha256": score._sha256_file(judgment_path),
        }

    def behavior_records(self, model: str = "model-a") -> list[dict[str, object]]:
        return [
            self.behavior_record("short", {"a01": False}, model),
            self.behavior_record("long", {"a01": True, "a02": True, "a03": True}, model),
        ]

    def all_records(self, model: str = "model-a") -> list[dict[str, object]]:
        return self.trigger_records(model) + self.behavior_records(model)

    def score(self, records: list[dict[str, object]]) -> dict[str, object]:
        return score.score_records(records, self.manifest_path, self.evidence)


class ScoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = BenchmarkFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_complete_records_are_scored(self) -> None:
        result = self.fixture.score(self.fixture.all_records())
        self.assertTrue(result["valid"])
        self.assertEqual(result["evaluation_status"], "complete")

    def test_repository_manifest_loads(self) -> None:
        protocol = score._load_protocol(MODULE_PATH.with_name("manifest.json"))
        self.assertEqual(protocol["manifest"]["release_under_test"], "0.2.7")

    def test_empty_records_are_not_evaluated(self) -> None:
        result = self.fixture.score([])
        self.assertFalse(result["valid"])
        self.assertEqual(result["evaluation_status"], "not_evaluated")

    def test_incomplete_matrix_is_partial(self) -> None:
        result = self.fixture.score(self.fixture.trigger_records()[:1])
        self.assertFalse(result["valid"])
        self.assertEqual(result["evaluation_status"], "partial")

    def test_duplicate_identity_is_invalid(self) -> None:
        records = self.fixture.all_records()
        records.append(copy.deepcopy(records[0]))
        result = self.fixture.score(records)
        self.assertFalse(result["valid"])
        self.assertEqual(result["evaluation_status"], "invalid")

    def test_provenance_dimensions_do_not_mix(self) -> None:
        records = self.fixture.all_records("model-a") + self.fixture.all_records("model-b")
        result = self.fixture.score(records)
        self.assertTrue(result["valid"])
        self.assertEqual({item["model"] for item in result["summaries"]}, {"model-a", "model-b"})

    def test_truth_cannot_be_supplied_by_record(self) -> None:
        records = self.fixture.trigger_records()
        records[0]["expected_trigger"] = False
        result = self.fixture.score(records)
        self.assertFalse(result["valid"])
        self.assertTrue(any("truth must come from" in error for error in result["errors"]))

    def test_single_class_trigger_protocol_is_invalid(self) -> None:
        self.fixture.trigger_cases = [self.fixture.trigger_cases[0]]
        with self.assertRaisesRegex(ValueError, "both positive and negative"):
            self.fixture.write_protocol()

    def test_missing_declared_condition_is_partial(self) -> None:
        for suite in self.fixture.manifest["suites"]:
            if suite.get("scoring_backend") == "score.py":
                suite["conditions"].append(
                    {
                        "condition_id": "baseline",
                        "skill_release": "test",
                        "skill_package_sha256": self.fixture.package_hash,
                    }
                )
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        self.fixture.protocol = score._load_protocol(self.fixture.manifest_path)
        result = self.fixture.score(self.fixture.all_records())
        self.assertFalse(result["valid"])
        self.assertEqual(result["evaluation_status"], "partial")
        self.assertEqual(
            len(result["protocol_coverage"]["missing_suite_conditions"]), 2
        )

    def test_judgment_cannot_be_reused_across_executions(self) -> None:
        records = self.fixture.behavior_records()
        records[1]["judgment_path"] = records[0]["judgment_path"]
        records[1]["judgment_sha256"] = records[0]["judgment_sha256"]
        result = self.fixture.score(records)
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("judgment does not bind" in error for error in result["errors"])
        )

    def test_invalid_interval_configuration_is_rejected(self) -> None:
        self.fixture.manifest["suites"][0]["interval_rule"]["method"] = "unsupported"
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "interval method"):
            score._load_protocol(self.fixture.manifest_path)

    def test_release_package_hash_must_be_consistent_across_suites(self) -> None:
        self.fixture.manifest["suites"][1]["conditions"][0][
            "skill_package_sha256"
        ] = "sha256:" + "4" * 64
        self.fixture.manifest_path.write_text(
            json.dumps(self.fixture.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "inconsistent package hashes"):
            score._load_protocol(self.fixture.manifest_path)

    def test_behavioral_primary_metric_weights_cases_equally(self) -> None:
        result = self.fixture.score(self.fixture.behavior_records())
        summary = result["summaries"][0]
        self.assertEqual(summary["metrics"]["case_mean_assertion_pass_rate"], 0.5)
        self.assertEqual(summary["metrics"]["assertion_micro_pass_rate_diagnostic"], 0.75)

    def test_assertion_ids_must_match_rubric(self) -> None:
        records = self.fixture.behavior_records()
        records[0]["assertion_scores"] = {"wrong": True}
        result = self.fixture.score(records)
        self.assertFalse(result["valid"])
        self.assertTrue(any("assertion_scores IDs" in error for error in result["errors"]))

    def test_evidence_hash_is_verified(self) -> None:
        records = self.fixture.trigger_records()
        records[0]["evidence_sha256"] = "sha256:" + "0" * 64
        result = self.fixture.score(records)
        self.assertFalse(result["valid"])
        self.assertTrue(any("evidence SHA-256 mismatch" in error for error in result["errors"]))

    def test_unknown_case_is_rejected(self) -> None:
        records = self.fixture.trigger_records()
        records[0]["case_id"] = "unknown"
        result = self.fixture.score(records)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown case_id" in error for error in result["errors"]))

    def test_external_suite_is_not_scored(self) -> None:
        record = {
            **self.fixture.common(),
            "suite_id": "empirical",
            "record_type": "empirical",
            "case_id": "scenario",
            "case_spec_sha256": "sha256:" + "0" * 64,
            "prompt_sha256": "sha256:" + "0" * 64,
            "evidence_path": "missing.txt",
            "evidence_sha256": "sha256:" + "0" * 64,
        }
        record["execution_identity_sha256"] = score._execution_identity_hash(record)
        result = self.fixture.score([record])
        self.assertFalse(result["valid"])
        self.assertTrue(any("external scorer" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
