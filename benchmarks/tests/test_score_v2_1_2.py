from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock


BENCHMARKS = Path(__file__).resolve().parents[1]
MODULE_PATH = BENCHMARKS / "score-v2.1.2.py"
LEGACY_TEST_PATH = Path(__file__).with_name("test_score_v2_1_1.py")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


score = load_module("scientific_autoresearch_score_2_1_2_tests", MODULE_PATH)
legacy_tests = load_module("scientific_autoresearch_score_2_1_1_fixture", LEGACY_TEST_PATH)


class Protocol212Fixture:
    """Upgrade the mature 2.1.1 synthetic fixture to a bound 2.1.2 pair."""

    def __init__(self, *, block_copies: int = 2) -> None:
        self.legacy = legacy_tests.BenchmarkFixture(block_copies=block_copies)
        self.repo = self.legacy.repo
        self.evidence = self.legacy.evidence
        self.execution_path = self.legacy.benchmarks / "execution-v2.1.2.json"
        self.template_path = self.legacy.benchmarks / "template-v2.1.2.json"

        execution = copy.deepcopy(self.legacy.manifest)
        execution.update(
            {
                "benchmark_schema_version": "2.1.2",
                "benchmark_protocol_version": "2.1.2",
                "protocol_id": score.PROTOCOL_ID_BY_SCOPE["development_evaluation"],
                "protocol_scope": "development_evaluation",
                "release_under_test": "test-target",
                "benchmark_status": "development_execution_frozen_not_evaluated",
                "manifest_kind": "execution",
                "execution_manifest_id": "fixture-development-v2.1.2",
                "execution_purpose": "development_evaluation",
                "frozen_at": "2000-01-01T00:00:00Z",
                "protocol_template_artifact": None,
                "protocol_projection_profile": score.PROTOCOL_PROJECTION_PROFILE,
                "protocol_projection_sha256": None,
                "record_schema_version": score.RECORD_SCHEMA_VERSION,
                "scorer_sha256": hashlib.sha256(MODULE_PATH.read_bytes()).hexdigest(),
                "evaluation_state_vocabulary": score.EVALUATION_STATE_VOCABULARY,
                "result_policy": score.RESULT_POLICY,
                "sealed_suite_policy": score.SEALED_SUITE_POLICY,
                "protocol_invalidation_policy": score.PROTOCOL_INVALIDATION_POLICY,
            }
        )
        for suite in execution["suites"]:
            suite["required_condition_ids"] = list(self.legacy.conditions)
            suite["required_contrasts"] = copy.deepcopy(
                suite["comparison_blocks"][0]["contrasts"]
            )

        template = copy.deepcopy(execution)
        template.update(
            {
                "benchmark_status": "development_protocol_2_1_2_defined_not_evaluated",
                "manifest_kind": "protocol_template",
                "execution_manifest_id": None,
                "execution_purpose": None,
                "frozen_at": None,
                "protocol_template_artifact": None,
            }
        )
        for suite in template["suites"]:
            suite["protocol_status"] = "awaiting_execution_freeze"
            suite["comparison_blocks"] = []

        self.projection = score._canonical_hash(
            score._immutable_protocol_projection(template)
        )
        template["protocol_projection_sha256"] = self.projection
        execution["protocol_projection_sha256"] = self.projection
        self.template = template
        self.execution = execution
        self.write_pair()
        with self.context():
            self.protocol = score._load_protocol(
                self.execution_path, artifact_root=self.repo
            )
        self.legacy.protocol = self.protocol
        self.legacy.manifest = self.execution
        self.legacy.manifest_path = self.execution_path

    def close(self) -> None:
        self.legacy.close()

    @contextlib.contextmanager
    def context(self):
        with (
            mock.patch.object(score, "TARGET_CONDITION_ID", "target"),
            mock.patch.object(score, "RELEASE_UNDER_TEST", "test-target"),
            mock.patch.dict(
                score.EXPECTED_TEMPLATE_PROJECTION_BY_SCOPE,
                {"development_evaluation": self.projection},
                clear=False,
            ),
        ):
            yield

    def write_pair(self) -> None:
        self.template_path.write_text(
            json.dumps(self.template, sort_keys=True), encoding="utf-8"
        )
        self.execution["protocol_template_artifact"] = {
            "path": str(self.template_path.relative_to(self.repo)),
            "sha256": "sha256:"
            + hashlib.sha256(self.template_path.read_bytes()).hexdigest(),
            "schema_version": "2.1.2",
        }
        self.execution_path.write_text(
            json.dumps(self.execution, sort_keys=True), encoding="utf-8"
        )

    def load(self):
        with self.context():
            return score._load_protocol(self.execution_path, artifact_root=self.repo)

    def records(self):
        return self.legacy.all_records()

    def score(self, records):
        with self.context():
            return score.score_records(
                records,
                self.execution_path,
                self.evidence,
                artifact_root=self.repo,
            )


class Protocol212Tests(unittest.TestCase):
    def test_repository_templates_and_execution_load(self) -> None:
        development = score._load_protocol(BENCHMARKS / "manifest-v2.1.2.json")
        shakedown = score._load_protocol(
            BENCHMARKS / "manifest-shakedown-v2.1.2.json"
        )
        execution = score._load_protocol(
            BENCHMARKS / "execution-manifest-shakedown-v2.1.2.json"
        )
        self.assertEqual(development["manifest"]["protocol_scope"], "development_evaluation")
        self.assertEqual(shakedown["manifest"]["protocol_scope"], "execution_shakedown")
        self.assertEqual(
            execution["parent_protocol"]["manifest_sha256"],
            execution["manifest"]["protocol_template_artifact"]["sha256"],
        )

    def test_governance_claims_are_exact_constants(self) -> None:
        source = json.loads(
            (BENCHMARKS / "execution-manifest-shakedown-v2.1.2.json").read_text()
        )
        cases = {
            "protocol_id": "unrelated-protocol",
            "release_under_test": "999.999.999",
            "benchmark_status": "behavior_validated",
            "evaluation_state_vocabulary": ["made_up"],
            "result_policy": {"allow_unpaired": True},
            "sealed_suite_policy": {"status": "fully_validated"},
            "protocol_invalidation_policy": {"partial_repair": True},
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                mutated = copy.deepcopy(source)
                mutated[field] = value
                path = BENCHMARKS / "executions" / f"mutation-{field}.json"
                path.write_text(json.dumps(mutated), encoding="utf-8")
                try:
                    with self.assertRaises(ValueError):
                        score._load_protocol(path, artifact_root=BENCHMARKS.parent)
                finally:
                    path.unlink()

    def test_execution_cannot_select_a_condition_subset(self) -> None:
        fixture = Protocol212Fixture(block_copies=1)
        try:
            suite = fixture.execution["suites"][0]
            block = suite["comparison_blocks"][0]
            block["condition_ids"] = ["target", "no-skill"]
            block["contrasts"] = [block["contrasts"][-1]]
            fixture.execution_path.write_text(
                json.dumps(fixture.execution), encoding="utf-8"
            )
            with fixture.context(), self.assertRaisesRegex(
                ValueError, "full required condition family"
            ):
                score._load_protocol(fixture.execution_path, artifact_root=fixture.repo)
        finally:
            fixture.close()

    def test_external_draft_cannot_hide_unvalidated_blocks(self) -> None:
        source = json.loads((BENCHMARKS / "manifest-v2.1.2.json").read_text())
        external = next(
            suite for suite in source["suites"] if suite["scoring_backend"] == "external"
        )
        external["comparison_blocks"] = [{"arbitrary": "unvalidated"}]
        path = BENCHMARKS / "executions" / "mutation-external-block.json"
        path.write_text(json.dumps(source), encoding="utf-8")
        try:
            with self.assertRaisesRegex(ValueError, "external draft.*comparison blocks"):
                score._load_protocol(path, artifact_root=BENCHMARKS.parent)
        finally:
            path.unlink()

    def test_forged_parent_and_execution_cannot_replace_frozen_projection(self) -> None:
        fixture = Protocol212Fixture(block_copies=1)
        try:
            fixture.template["suites"][0]["repetitions"] += 1
            fixture.execution["suites"][0]["repetitions"] += 1
            forged = score._canonical_hash(
                score._immutable_protocol_projection(fixture.template)
            )
            fixture.template["protocol_projection_sha256"] = forged
            fixture.execution["protocol_projection_sha256"] = forged
            fixture.write_pair()
            with fixture.context(), self.assertRaisesRegex(ValueError, "frozen 2.1.2"):
                score._load_protocol(fixture.execution_path, artifact_root=fixture.repo)
        finally:
            fixture.close()

    def test_parent_template_hash_is_mandatory(self) -> None:
        fixture = Protocol212Fixture(block_copies=1)
        try:
            fixture.execution["protocol_template_artifact"]["sha256"] = "sha256:" + "0" * 64
            fixture.execution_path.write_text(
                json.dumps(fixture.execution), encoding="utf-8"
            )
            with fixture.context(), self.assertRaisesRegex(ValueError, "SHA-256"):
                score._load_protocol(fixture.execution_path, artifact_root=fixture.repo)
        finally:
            fixture.close()

    def test_one_block_evidence_tamper_preserves_other_block_reports(self) -> None:
        fixture = Protocol212Fixture(block_copies=2)
        try:
            records = fixture.records()
            baseline = fixture.score(records)
            tampered = records[0]
            path = fixture.evidence / str(tampered["evidence_path"])
            path.write_bytes(path.read_bytes() + b"\n")
            result = fixture.score(records)
            bad_block = str(tampered["comparison_block_id"])
            self.assertFalse(result["valid"])
            self.assertEqual(result["scoring_status"], "invalidated")
            status = {
                item["comparison_block_id"]: item["status"]
                for item in result["block_results"]
            }
            self.assertEqual(status[bad_block], "invalidated")
            self.assertTrue(any(value == "complete" for value in status.values()))
            self.assertTrue(result["condition_summaries"])
            self.assertTrue(result["paired_comparisons"])
            self.assertFalse(
                any(
                    item["comparison_block_id"] == bad_block
                    for item in result["condition_summaries"]
                    + result["paired_comparisons"]
                )
            )
            self.assertEqual(
                [
                    item
                    for item in result["condition_summaries"]
                    if item["comparison_block_id"] != bad_block
                ],
                [
                    item
                    for item in baseline["condition_summaries"]
                    if item["comparison_block_id"] != bad_block
                ],
            )
            self.assertEqual(
                [
                    item
                    for item in result["paired_comparisons"]
                    if item["comparison_block_id"] != bad_block
                ],
                [
                    item
                    for item in baseline["paired_comparisons"]
                    if item["comparison_block_id"] != bad_block
                ],
            )
        finally:
            fixture.close()

    def test_claimed_symlink_is_block_local(self) -> None:
        fixture = Protocol212Fixture(block_copies=2)
        try:
            records = fixture.records()
            affected = records[0]
            evidence_path = fixture.evidence / str(affected["evidence_path"])
            outside = fixture.repo / "outside-evidence.json"
            outside.write_bytes(evidence_path.read_bytes())
            evidence_path.unlink()
            evidence_path.symlink_to(outside)
            result = fixture.score(records)
            self.assertEqual(result["scoring_status"], "invalidated")
            self.assertEqual(len(result["block_results"]), 4)
            status = {
                item["comparison_block_id"]: item["status"]
                for item in result["block_results"]
            }
            self.assertEqual(status[str(affected["comparison_block_id"])], "invalidated")
            self.assertIn("complete", status.values())
        finally:
            fixture.close()

    def test_malformed_status_with_judgment_remains_block_local(self) -> None:
        fixture = Protocol212Fixture(block_copies=2)
        try:
            records = fixture.records()
            affected = records[0]
            affected["run_status"] = "bogus"
            result = fixture.score(records)
            self.assertEqual(result["scoring_status"], "invalidated")
            self.assertEqual(len(result["block_results"]), 4)
            self.assertTrue(
                any(item["status"] == "complete" for item in result["block_results"])
            )
            self.assertFalse(
                any("unreferenced files" in item for item in result["errors"])
            )
        finally:
            fixture.close()

    def test_cross_block_path_reuse_invalidates_owners_not_other_blocks(self) -> None:
        fixture = Protocol212Fixture(block_copies=2)
        try:
            records = fixture.records()
            first = records[0]
            second = next(
                record
                for record in records
                if record["suite_id"] == first["suite_id"]
                and record["comparison_block_id"] != first["comparison_block_id"]
            )
            old_path = fixture.evidence / str(second["evidence_path"])
            old_path.unlink()
            second["evidence_path"] = first["evidence_path"]
            second["evidence_sha256"] = first["evidence_sha256"]
            result = fixture.score(records)
            statuses = {
                item["comparison_block_id"]: item["status"]
                for item in result["block_results"]
            }
            self.assertEqual(
                statuses[str(first["comparison_block_id"])], "invalidated"
            )
            self.assertEqual(
                statuses[str(second["comparison_block_id"])], "invalidated"
            )
            self.assertIn("complete", statuses.values())
        finally:
            fixture.close()

    def test_missing_judgment_is_block_local(self) -> None:
        fixture = Protocol212Fixture(block_copies=2)
        try:
            records = fixture.records()
            affected = records[0]
            (fixture.evidence / str(affected["judgment_path"])).unlink()
            result = fixture.score(records)
            self.assertEqual(result["scoring_status"], "invalidated")
            self.assertEqual(len(result["block_results"]), 4)
            self.assertTrue(
                any(item["status"] == "complete" for item in result["block_results"])
            )
        finally:
            fixture.close()

    def test_orphan_evidence_remains_submission_fatal(self) -> None:
        fixture = Protocol212Fixture(block_copies=2)
        try:
            records = fixture.records()
            (fixture.evidence / "orphan.json").write_text("{}", encoding="utf-8")
            result = fixture.score(records)
            self.assertEqual(result["scoring_status"], "invalid")
            self.assertEqual(result["condition_summaries"], [])
            self.assertEqual(result["paired_comparisons"], [])
        finally:
            fixture.close()

    def test_committed_shakedown_replays_without_evidence_claim(self) -> None:
        execution = BENCHMARKS / "executions" / "shakedown-v2.1.2"
        records, digest = score._load_jsonl_with_hash(execution / "records.jsonl")
        result = score.score_records(
            records,
            BENCHMARKS / "execution-manifest-shakedown-v2.1.2.json",
            execution / "evidence",
            records_sha256=digest,
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["evidence_status"], "not_evaluated")
        self.assertEqual(result["condition_summaries"], [])
        self.assertEqual(result["paired_comparisons"], [])


if __name__ == "__main__":
    unittest.main()
