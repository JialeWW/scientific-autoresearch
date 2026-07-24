from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts" / "build_installable_skill.py"
SKILL_DIR = ROOT / "scientific-autoresearch"
COMPLETION_REFERENCE = SKILL_DIR / "references" / "completion-review.md"
V033_CASES = ROOT / "benchmarks" / "development-cases" / "v0.3.3-scientific-stop-challenge.json"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_installable_skill", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load installable-skill builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LightweightInstallSurfaceTests(unittest.TestCase):
    def test_stochastic_policy_is_design_appropriate(self) -> None:
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("master random seed `42`", content)
        self.assertIn("reproducible randomization policy appropriate to the design", content)
        self.assertIn("never select or change randomness after outcomes", content)
        self.assertIn("separate validated concealed scheme", content)

    def test_runtime_file_list_excludes_formal_audit(self) -> None:
        builder = load_builder()
        relative = {
            path.relative_to(SKILL_DIR).as_posix()
            for path in builder.runtime_files(SKILL_DIR)
        }
        self.assertIn("SKILL.md", relative)
        self.assertTrue(any(path.startswith("references/") for path in relative))
        self.assertFalse(any(path.startswith("scripts/") for path in relative))
        self.assertFalse(relative & builder.FORBIDDEN_RUNTIME_MEMBERS)

    def test_scientific_stop_challenge_is_routed_and_client_neutral(self) -> None:
        core = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        reference = COMPLETION_REFERENCE.read_text(encoding="utf-8")

        self.assertIn("references/completion-review.md", core)
        self.assertIn("Only when preparing to set `search_stop_admissible=true`", core)
        self.assertIn("registered-batch completion without a search-stop claim", core)
        self.assertIn("Use one fresh reviewer context when available", core)
        self.assertNotIn("spawn_agent", core + reference)

    def test_completion_review_preserves_staged_and_adjudicated_boundary(self) -> None:
        content = COMPLETION_REFERENCE.read_text(encoding="utf-8")

        for required in (
            "deterministic only over declared identifiers",
            "product_role: inferential | diagnostic | qa | intermediate | provenance",
            "Source reconstruction",
            "design assumptions or measurement semantics",
            "Reconciliation challenge",
            "registry_visible_during_reconstruction: true",
            "potentially_material_open_tests",
            "verdict: no_blocker_found | potential_findings_present | inconclusive",
            "Preserve the reviewer's issued verdict",
            "leave the affected finding explicitly unresolved",
            "search_stop_admissible=indeterminate",
            "a reviewer must not propose one",
            "authorization merely defining a completed request does not turn `request_complete` into `user_boundary`",
            "Run one challenge per stopping episode",
        ):
            self.assertIn(required, content)

        state_block = re.search(
            r"request_execution_complete: true \| false\n"
            r"scientific_mapping_complete: true \| false \| not_assessed\n"
            r"search_stop_admissible: true \| false \| indeterminate \| not_assessed\n"
            r"complete_within_scope: true \| false \| not_assessed\n"
            r"termination_reason: scientific_stop \| request_complete \| user_boundary \| resource_boundary \| safety_boundary \| governance_boundary",
            content,
        )
        self.assertIsNotNone(state_block)
        self.assertIn("execution_status: registered_batch_complete", content)
        self.assertNotIn("`request_execution_complete` may use", content)

    def test_v033_development_cases_cover_new_failure_modes(self) -> None:
        value = json.loads(V033_CASES.read_text(encoding="utf-8"))
        self.assertEqual(value["skill_release"], "0.3.3")
        self.assertFalse(value["contains_scored_results"])
        ids = {case["id"] for case in value["cases"]}
        self.assertTrue(
            {
                "declared-role-orphan-blocks-mapping",
                "staged-disclosure-reduces-registry-anchoring",
                "scope-change-invalidates-delta-review",
                "reviewer-hallucination-does-not-veto-stop",
                "stop-challenge-does-not-replace-coverage",
            }.issubset(ids)
        )

    def test_archive_is_deterministic_and_lightweight(self) -> None:
        builder = load_builder()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.zip"
            second = root / "second.zip"
            first_receipt = builder.build(SKILL_DIR, first)
            second_receipt = builder.build(SKILL_DIR, second)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                first_receipt["runtime_package_sha256"],
                second_receipt["runtime_package_sha256"],
            )
            self.assertFalse(first_receipt["historical_evals_included"])
            self.assertFalse(first_receipt["formal_machine_audit_included"])

            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
            self.assertIn("scientific-autoresearch/SKILL.md", names)
            self.assertIn("scientific-autoresearch/LICENSE", names)
            self.assertFalse(any("/evals/" in name for name in names))
            self.assertFalse(any("/scripts/" in name for name in names))
            self.assertFalse(
                {
                    f"scientific-autoresearch/{path}"
                    for path in builder.FORBIDDEN_RUNTIME_MEMBERS
                }
                & names
            )


if __name__ == "__main__":
    unittest.main()
