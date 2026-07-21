#!/usr/bin/env python3
"""Validate the profile-proportionate consistency of an autoresearch run.

The validator uses only the Python standard library. It checks the frozen
claim and provenance for fixed tests, adds complete adaptive-path artifacts
for adaptive search, and adds inventory, coverage, saturation, and queue
consistency for coverage search.

Usage:
    python validate_run.py RUN_DIR
    python validate_run.py RUN_DIR --output RUN_DIR/consistency_report.json
    python validate_run.py --init RUN_DIR --profile PROFILE
    python validate_run.py --snapshot-upgrade RUN_DIR --to-profile PROFILE
    python validate_run.py --self-test
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import tempfile
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


VALIDATOR_VERSION = "1.5.0"
ARTIFACT_SCHEMA_VERSION = "1.5.0"
STRICT_BASELINE_SCHEMA_VERSION = "1.4.0"
REPORT_SCHEMA_VERSION = "1.0"
REQUIRED_SENTINEL = "__REQUIRED__"

RESEARCH_PROFILES = {"fixed_test", "adaptive_search", "coverage_search"}
PROFILE_RANK = {"fixed_test": 0, "adaptive_search": 1, "coverage_search": 2}
STAGE_STATUSES = {"planned", "in_progress", "completed_as_scoped", "blocked", "abandoned"}
CANDIDATE_TYPES = {"mechanism", "model", "feature", "simulation", "design", "other"}
SUBSTANTIVE_ELIGIBILITY_STATUSES = {"eligible", "ineligible", "not_assessed"}
PROFILE_HISTORY_REQUIRED_FIELDS = {"profile", "started_at"}
ROUND_RECORD_STATUSES = {"planned", "completed", "failed", "blocked", "abandoned"}

GOVERNANCE_STATUSES = {"not_assessed", "cleared", "restricted", "blocked"}
EXECUTION_MODES = {"design_only", "single_round", "multi_round"}
INVENTORY_STATUSES = {
    "draft",
    "frozen",
    "expanded",
    "saturation_audit",
    "saturated",
    "reopened",
}
COVERAGE_STATUSES = {
    "unassessed",
    "eligible_untested",
    "scheduled",
    "in_progress",
    "tested_valid",
    "covered_by",
    "not_testable_current_data",
    "invalid_open",
    "resource_blocked",
    "governance_blocked",
}
CLOSED_COVERAGE_STATUSES = {
    "tested_valid",
    "covered_by",
    "not_testable_current_data",
}
SEARCH_STATUSES = {
    "inventory_building",
    "coverage_in_progress",
    "verification_ready",
    "resource_limited_pause",
    "user_limited_stop",
    "governance_blocked",
    "human_decision_required",
    "complete_within_scope",
}
EXECUTION_STATUSES = {"planned", "completed", "failed", "abandoned", "blocked"}
RESULT_STATUSES = {
    "not_run",
    "supported",
    "null",
    "inconclusive",
    "artifact",
    "invalid",
}
SPECIFICATION_TIMINGS = {"pre_result_frozen", "post_result_adaptive"}
EVIDENCE_STAGES = {
    "exploratory",
    "internal_validation",
    "independent_verification",
    "diagnostic",
}
VERIFICATION_STATUSES = {
    "unverified",
    "internal_only",
    "holdout_verified",
    "externally_replicated",
    "compromised",
    "not_applicable",
}
COMPARISON_STATUSES = {
    "comparable_within_family",
    "parallel_conclusion",
    "support_limited_candidate",
    "not_eligible_for_decision",
}
PRIOR_EXPOSURE_STATUSES = {
    "not_assessed",
    "no_known_exposure",
    "known_overlap",
    "unknown",
    "not_applicable",
}
EXECUTION_TIERS = {"uniform_screen", "deep_test", "verification", "diagnostic"}
CONFIRMATORY_STATUSES = {
    "unrestricted_by_prior_exposure",
    "exploratory",
    "internal_validation_only",
    "compromised",
    "unknown",
    "not_applicable",
}
FUTURE_VERIFICATION_STATUSES = {
    "eligible_if_untouched",
    "needs_new_independent_data",
    "not_applicable",
}
MECHANISM_STATUSES = {
    "active",
    "provisionally_supported",
    "weakened",
    "rejected",
    "needs_data",
    "needs_human_judgment",
}
DECISION_STATUSES = {
    "not_evaluated",
    "eligible",
    "leading",
    "tie",
    "inconclusive",
    "no_eligible_candidate",
    "excluded",
}
TERMINAL_RUN_DECISION_STATUSES = {
    "leading",
    "tie",
    "inconclusive",
    "no_eligible_candidate",
}
PROMOTED_DECISION_STATUSES = {"eligible", "leading", "tie"}
TRANSPORTABILITY_REQUIREMENTS = {
    "same_population",
    "validation_required",
    "parallel_only",
}
TRANSPORTABILITY_STATUSES = {
    "not_required",
    "planned",
    "passed",
    "failed",
    "inconclusive",
}
MECHANISM_ALIGNMENTS = {
    "direct",
    "calibrated_proxy",
    "diagnostic_only",
    "unsupported",
    "not_assessed",
    "not_applicable",
}
PROMOTABLE_MECHANISM_ALIGNMENTS = {"direct", "calibrated_proxy", "not_applicable"}
DATA_SUPPORT_STATUSES = {
    "supported",
    "support_limited",
    "diagnostic_only",
    "unsupported",
    "not_assessed",
    "not_applicable",
}
COVERAGE_ELIGIBLE_MECHANISM_STATUSES = {
    "active",
    "provisionally_supported",
    "weakened",
}
DECISION_ELIGIBLE_DATA_SUPPORT_STATUSES = {"supported"}
MEASUREMENT_ERROR_SENSITIVITIES = {
    "not_applicable",
    "not_required",
    "planned",
    "passed",
    "failed",
    "inconclusive",
}
PROMOTABLE_MEASUREMENT_ERROR_SENSITIVITIES = {
    "not_applicable",
    "not_required",
    "passed",
}
EVIDENCE_SCALE_RELATIONS = {
    "same_scale",
    "monotone_only",
    "calibrated_mapping",
    "separate_roles",
    "not_applicable",
}
EVIDENCE_SCALE_MAPPING_FIELDS = {
    "screening_statistic",
    "screening_estimand_and_scale",
    "decision_model_or_statistic",
    "decision_estimand_and_scale",
    "scale_relation",
    "validation_or_calibration_rule",
    "discordance_rule",
}

STATUS_VALUES = {
    "governance_status": GOVERNANCE_STATUSES,
    "inventory_status": INVENTORY_STATUSES,
    "coverage_status": COVERAGE_STATUSES,
    "search_status": SEARCH_STATUSES,
    "execution_status": EXECUTION_STATUSES,
    "result_status": RESULT_STATUSES,
    "specification_timing": SPECIFICATION_TIMINGS,
    "evidence_stage": EVIDENCE_STAGES,
    "verification_status": VERIFICATION_STATUSES,
    "comparison_status": COMPARISON_STATUSES,
    "comparability_status": COMPARISON_STATUSES,
    "prior_exposure_status": PRIOR_EXPOSURE_STATUSES,
    "execution_tier": EXECUTION_TIERS,
    "mechanism_status": MECHANISM_STATUSES,
    "candidate_status": MECHANISM_STATUSES,
    "substantive_eligibility": SUBSTANTIVE_ELIGIBILITY_STATUSES,
    "decision_status": DECISION_STATUSES,
    "confirmatory_status": CONFIRMATORY_STATUSES,
    "future_verification_status": FUTURE_VERIFICATION_STATUSES,
    "data_support_status": DATA_SUPPORT_STATUSES,
    "mechanism_alignment": MECHANISM_ALIGNMENTS,
    "measurement_error_sensitivity": MEASUREMENT_ERROR_SENSITIVITIES,
    "transportability_requirement": TRANSPORTABILITY_REQUIREMENTS,
    "transportability_status": TRANSPORTABILITY_STATUSES,
}

STRICT_TRANSITION_STATUS_FIELDS = {
    "data_support_status",
    "mechanism_alignment",
    "measurement_error_sensitivity",
    "transportability_requirement",
    "transportability_status",
}
FROZEN_CLASSIFICATION_FIELDS = {
    "data_support_status",
    "mechanism_alignment",
    "transportability_requirement",
    "substantive_eligibility",
}

# These maps reject scientifically impossible shortcuts while preserving
# explicit block/resume, correction, and reopened-version paths.
ALLOWED_STATUS_TRANSITIONS: dict[str, dict[str, set[str]]] = {
    "governance_status": {
        "not_assessed": {"cleared", "restricted", "blocked"},
        "cleared": {"restricted", "blocked"},
        "restricted": {"cleared", "blocked"},
        "blocked": {"cleared", "restricted"},
    },
    "inventory_status": {
        "draft": {"frozen", "expanded", "reopened"},
        "frozen": {"saturation_audit", "expanded", "reopened"},
        "saturation_audit": {"saturated", "frozen", "expanded", "reopened"},
        "saturated": {"reopened", "expanded"},
        "expanded": {"draft", "frozen", "reopened"},
        "reopened": {"draft", "frozen", "expanded"},
    },
    "coverage_status": {
        "unassessed": {
            "eligible_untested",
            "not_testable_current_data",
            "resource_blocked",
            "governance_blocked",
        },
        "eligible_untested": {
            "scheduled",
            "covered_by",
            "not_testable_current_data",
            "resource_blocked",
            "governance_blocked",
        },
        "scheduled": {
            "eligible_untested",
            "in_progress",
            "invalid_open",
            "resource_blocked",
            "governance_blocked",
        },
        "in_progress": {
            "scheduled",
            "tested_valid",
            "invalid_open",
            "resource_blocked",
            "governance_blocked",
        },
        "invalid_open": {
            "eligible_untested",
            "scheduled",
            "in_progress",
            "not_testable_current_data",
            "resource_blocked",
            "governance_blocked",
        },
        "resource_blocked": {
            "eligible_untested",
            "scheduled",
            "in_progress",
            "not_testable_current_data",
            "governance_blocked",
        },
        "governance_blocked": {
            "eligible_untested",
            "scheduled",
            "in_progress",
            "not_testable_current_data",
            "resource_blocked",
        },
        "tested_valid": {"invalid_open"},
        "covered_by": {"invalid_open"},
        "not_testable_current_data": {"eligible_untested"},
    },
    "search_status": {
        "inventory_building": {
            "coverage_in_progress",
            "resource_limited_pause",
            "user_limited_stop",
            "governance_blocked",
            "human_decision_required",
        },
        "coverage_in_progress": {
            "inventory_building",
            "verification_ready",
            "resource_limited_pause",
            "user_limited_stop",
            "governance_blocked",
            "human_decision_required",
            "complete_within_scope",
        },
        "verification_ready": {
            "inventory_building",
            "coverage_in_progress",
            "resource_limited_pause",
            "user_limited_stop",
            "governance_blocked",
            "human_decision_required",
            "complete_within_scope",
        },
        "resource_limited_pause": {
            "inventory_building",
            "coverage_in_progress",
            "verification_ready",
            "user_limited_stop",
            "governance_blocked",
            "human_decision_required",
        },
        "user_limited_stop": {
            "inventory_building",
            "coverage_in_progress",
            "verification_ready",
            "resource_limited_pause",
            "governance_blocked",
            "human_decision_required",
        },
        "governance_blocked": {
            "inventory_building",
            "coverage_in_progress",
            "verification_ready",
            "resource_limited_pause",
            "user_limited_stop",
            "human_decision_required",
        },
        "human_decision_required": {
            "inventory_building",
            "coverage_in_progress",
            "verification_ready",
            "resource_limited_pause",
            "user_limited_stop",
            "governance_blocked",
        },
        "complete_within_scope": {"inventory_building", "coverage_in_progress"},
    },
    "execution_status": {
        "planned": {"completed", "failed", "abandoned", "blocked"},
        "blocked": {"planned", "abandoned"},
        "failed": {"planned", "abandoned"},
        "abandoned": {"planned"},
        "completed": set(),
    },
    "result_status": {
        "not_run": {"supported", "null", "inconclusive", "artifact", "invalid"},
        "invalid": {"not_run"},
        "supported": {"invalid"},
        "null": {"invalid"},
        "inconclusive": {"invalid"},
        "artifact": {"invalid"},
    },
    "specification_timing": {
        "pre_result_frozen": {"post_result_adaptive"},
        "post_result_adaptive": set(),
    },
    "prior_exposure_status": {
        "not_assessed": {"no_known_exposure", "known_overlap", "unknown"},
        "no_known_exposure": {"known_overlap", "unknown"},
        "known_overlap": {"unknown"},
        "unknown": {"no_known_exposure", "known_overlap"},
    },
    "evidence_stage": {
        "exploratory": {"internal_validation", "independent_verification", "diagnostic"},
        "internal_validation": {"exploratory", "independent_verification", "diagnostic"},
        "independent_verification": set(),
        "diagnostic": {"exploratory", "internal_validation"},
    },
    "verification_status": {
        "unverified": {
            "internal_only",
            "holdout_verified",
            "externally_replicated",
            "compromised",
            "not_applicable",
        },
        "internal_only": {"holdout_verified", "externally_replicated", "compromised"},
        "holdout_verified": {"externally_replicated", "compromised"},
        "externally_replicated": {"compromised"},
        "compromised": {"externally_replicated"},
        "not_applicable": {"unverified"},
    },
    "mechanism_status": {
        "active": {
            "provisionally_supported",
            "weakened",
            "rejected",
            "needs_data",
            "needs_human_judgment",
        },
        "provisionally_supported": {
            "active",
            "weakened",
            "rejected",
            "needs_data",
            "needs_human_judgment",
        },
        "weakened": {
            "active",
            "provisionally_supported",
            "rejected",
            "needs_data",
            "needs_human_judgment",
        },
        "rejected": {"needs_human_judgment"},
        "needs_data": {"active", "needs_human_judgment"},
        "needs_human_judgment": {"active", "needs_data", "weakened"},
    },
    "decision_status": {
        "not_evaluated": {
            "eligible",
            "inconclusive",
            "no_eligible_candidate",
            "excluded",
        },
        "eligible": {"leading", "tie", "inconclusive", "excluded"},
        "leading": {"tie", "inconclusive", "excluded"},
        "tie": {"leading", "inconclusive", "excluded"},
        "inconclusive": {"eligible", "leading", "tie", "excluded"},
        "no_eligible_candidate": {"eligible", "inconclusive"},
        "excluded": {"eligible"},
    },
    "execution_tier": {
        "uniform_screen": {"deep_test", "verification", "diagnostic"},
        "deep_test": {"verification", "diagnostic"},
        "verification": {"diagnostic"},
        "diagnostic": {"deep_test", "verification"},
    },
    "confirmatory_status": {
        "unrestricted_by_prior_exposure": {
            "exploratory",
            "internal_validation_only",
            "compromised",
            "unknown",
            "not_applicable",
        },
        "exploratory": {"internal_validation_only", "compromised", "unknown"},
        "internal_validation_only": {"exploratory", "compromised", "unknown"},
        "compromised": {"unknown"},
        "unknown": {
            "unrestricted_by_prior_exposure",
            "exploratory",
            "internal_validation_only",
            "compromised",
        },
        "not_applicable": {"unrestricted_by_prior_exposure", "exploratory"},
    },
    "future_verification_status": {
        "eligible_if_untouched": {"needs_new_independent_data", "not_applicable"},
        "needs_new_independent_data": {"eligible_if_untouched", "not_applicable"},
        "not_applicable": {"eligible_if_untouched", "needs_new_independent_data"},
    },
}

# Comparison classifications can legitimately change after documented support,
# calibration, or eligibility updates; every change still needs evidence.
ALLOWED_STATUS_TRANSITIONS["comparability_status"] = {
    state: COMPARISON_STATUSES - {state} for state in COMPARISON_STATUSES
}
ALLOWED_STATUS_TRANSITIONS["comparison_status"] = ALLOWED_STATUS_TRANSITIONS[
    "comparability_status"
]
ALLOWED_STATUS_TRANSITIONS["mechanism_alignment"] = {
    state: set() for state in MECHANISM_ALIGNMENTS
}
ALLOWED_STATUS_TRANSITIONS["data_support_status"] = {
    state: set() for state in DATA_SUPPORT_STATUSES
}
ALLOWED_STATUS_TRANSITIONS["transportability_requirement"] = {
    state: set() for state in TRANSPORTABILITY_REQUIREMENTS
}
ALLOWED_STATUS_TRANSITIONS["measurement_error_sensitivity"] = {
    "planned": {"passed", "failed", "inconclusive"},
    "not_applicable": set(),
    "not_required": set(),
    "passed": set(),
    "failed": set(),
    "inconclusive": set(),
}
ALLOWED_STATUS_TRANSITIONS["transportability_status"] = {
    "planned": {"passed", "failed", "inconclusive"},
    "not_required": set(),
    "passed": set(),
    "failed": set(),
    "inconclusive": set(),
}
ALLOWED_STATUS_TRANSITIONS["candidate_status"] = ALLOWED_STATUS_TRANSITIONS[
    "mechanism_status"
]
ALLOWED_STATUS_TRANSITIONS["substantive_eligibility"] = {
    state: set() for state in SUBSTANTIVE_ELIGIBILITY_STATUSES
}

INVENTORY_REQUIRED_FIELDS = {
    "inventory_version",
    "mechanism_id",
    "mechanism",
    "distinct_pathway",
    "inclusion_rationale",
    "generation_lens",
    "applicable_regime",
    "predicted_signature",
    "required_data_products",
    "data_support_status",
    "mechanism_status",
    "specification_timing",
}
INVENTORY_REQUIRED_COLUMNS = INVENTORY_REQUIRED_FIELDS | {
    "parent_mechanism_id",
    "duplicate_of",
}
GENERIC_INVENTORY_REQUIRED_FIELDS = {
    "inventory_version",
    "candidate_id",
    "candidate_type",
    "candidate",
    "distinct_role",
    "inclusion_rationale",
    "generation_lens",
    "applicable_regime",
    "predicted_signature",
    "required_data_products",
    "data_support_status",
    "candidate_status",
    "specification_timing",
}
GENERIC_INVENTORY_REQUIRED_COLUMNS = GENERIC_INVENTORY_REQUIRED_FIELDS | {
    "parent_candidate_id",
    "duplicate_of",
}
COVERAGE_REQUIRED_FIELDS = {
    "coverage_cell_id",
    "inventory_version",
    "mechanism_id",
    "observable_id",
    "formulation_id",
    "data_product_id",
    "data_version_id",
    "supported_sample_id",
    "parameter_or_scale_domain",
    "comparator",
    "expected_signature",
    "minimum_meaningful_effect",
    "sensitivity_requirement",
    "falsifier",
    "selection_family_id",
    "selection_family_version",
    "comparison_key",
    "comparability_status",
    "specification_timing",
    "evidence_stage",
    "execution_tier",
    "coverage_status",
    "execution_status",
    "result_status",
    "verification_status",
    "ledger_entry_ids",
}
COVERAGE_REQUIRED_COLUMNS = COVERAGE_REQUIRED_FIELDS | {"round_id", "blocker"}
STRICT_COVERAGE_REQUIRED_FIELDS = {
    "mechanism_alignment",
    "measurement_error_sensitivity",
}
GENERIC_COVERAGE_REQUIRED_FIELDS = (
    (COVERAGE_REQUIRED_FIELDS - {"mechanism_id"})
    | {"candidate_id", "substantive_eligibility", "measurement_error_sensitivity"}
)
GENERIC_COVERAGE_REQUIRED_COLUMNS = (
    (COVERAGE_REQUIRED_COLUMNS - {"mechanism_id"})
    | {
        "candidate_id",
        "substantive_eligibility",
        "mechanism_alignment",
        "measurement_error_sensitivity",
    }
)
STRICT_DECISION_CONTRACT_FIELDS = {
    "target_population",
    "analysis_population",
    "selection_population",
    "reporting_population",
    "substantive_eligibility_rule",
    "measurement_error_policy",
    "transportability_requirement",
    "transportability_status",
    "evidence_scale_mapping",
}
STRICT_SELECTION_FAMILY_FIELDS = {
    "target_population",
    "supported_sample_id",
    "estimand",
    "data_quality_regime",
    "evidence_stage",
    "transportability_requirement",
    "transportability_status",
}
CANDIDATE_REQUIRED_FIELDS = {
    "candidate_id",
    "inventory_version",
    "mechanism_id",
    "coverage_cell_ids",
    "selection_family_id",
    "selection_family_version",
    "comparison_key",
    "comparability_status",
    "decision_status",
    "specification_timing",
    "prior_exposure_status",
    "confirmatory_status",
    "future_verification_status",
    "evidence_stage",
    "verification_status",
    "effect_summary",
    "uncertainty_summary",
    "support_summary",
    "ledger_entry_ids",
    "decision_reason",
}
V15_COVERAGE_CANDIDATE_FIELDS = {
    "candidate_type",
    "substantive_eligibility",
}
ADAPTIVE_CANDIDATE_REQUIRED_FIELDS = {
    "candidate_id",
    "candidate_type",
    "substantive_eligibility",
    "mechanism_alignment",
    "measurement_error_relevant",
    "measurement_error_sensitivity",
    "selection_family_id",
    "selection_family_version",
    "comparison_key",
    "comparability_status",
    "decision_status",
    "specification_timing",
    "prior_exposure_status",
    "confirmatory_status",
    "future_verification_status",
    "evidence_stage",
    "verification_status",
    "effect_summary",
    "uncertainty_summary",
    "support_summary",
    "ledger_entry_ids",
    "decision_reason",
}
ADAPTIVE_CANDIDATE_ROW_REQUIRED_FIELDS = (
    ADAPTIVE_CANDIDATE_REQUIRED_FIELDS
    - {"mechanism_alignment", "measurement_error_sensitivity"}
)
FIXED_CLAIM_REQUIRED_FIELDS = {
    "claim_id",
    "claim",
    "target_population",
    "analysis_population",
    "supported_sample_id",
    "estimand",
    "minimum_meaningful_effect",
    "analysis_or_test",
    "decision_rule",
    "falsifier",
    "specification_timing",
    "prior_exposure_status",
    "evidence_stage",
    "result_status",
    "effect_summary",
    "uncertainty_summary",
    "main_caveat",
    "data_version_ids",
    "completed_as_scoped",
}
EXECUTION_QUEUE_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "coverage_cell_id": ("coverage_cell_id",),
    "execution_tier": ("execution_tier", "tier"),
    "dependencies": ("dependency", "dependencies"),
    "priority": ("priority",),
    "priority_basis": ("priority_basis",),
    "estimated_resources": ("estimated_resources", "resource_estimate"),
    "authorization_envelope_fit": (
        "authorization_envelope_fit",
        "envelope_fit",
    ),
    "blocker": ("blocker",),
    "next_admissible_action": (
        "next_admissible_action",
        "next_action",
        "resume_action",
    ),
}
FIXED_INIT_FILES = {
    "run_manifest.json",
    "claim_card.json",
    "data_versions.json",
    "rounds/round_000/report.md",
    "rounds/round_000/reproduce_commands.txt",
    "consistency_report.json",
}
ADAPTIVE_INIT_FILES = {
    "run_manifest.json",
    "decision_contract.json",
    "prior_exposure_audit.json",
    "data_versions.json",
    "search_ledger.jsonl",
    "selection_families.json",
    "status_transitions.jsonl",
    "candidate_registry.csv",
    "rounds/round_000/report.md",
    "rounds/round_000/reproduce_commands.txt",
    "consistency_report.json",
}
COVERAGE_INIT_FILES = {
    "run_manifest.json",
    "decision_contract.json",
    "prior_exposure_audit.json",
    "data_versions.json",
    "inventories/candidate_inventory_v001.csv",
    "inventories/coverage_matrix_v001.csv",
    "inventories/saturation_audit_v001.json",
    "search_ledger.jsonl",
    "selection_families.json",
    "execution_queue.csv",
    "status_transitions.jsonl",
    "candidate_registry.csv",
    "rounds/round_000/report.md",
    "rounds/round_000/inventory.json",
    "rounds/round_000/summary.csv",
    "rounds/round_000/reproduce_commands.txt",
    "rounds/round_000/round_gate.md",
    "consistency_report.json",
}
ROUND_SUMMARY_COLUMNS = (
    "inventory_version",
    "coverage_cell_id",
    "mechanism_id",
    "observable_id",
    "formulation_id",
    "mechanism_alignment",
    "measurement_error_sensitivity",
    "selection_family_id",
    "selection_family_version",
    "comparison_key",
    "comparability_status",
    "transportability_requirement",
    "transportability_status",
    "prior_exposure_status",
    "data_support_status",
    "effect_summary",
    "uncertainty_summary",
    "sensitivity_summary",
    "specification_timing",
    "evidence_stage",
    "execution_tier",
    "governance_status",
    "inventory_status",
    "coverage_status",
    "search_status",
    "execution_status",
    "result_status",
    "mechanism_status",
    "verification_status",
    "main_caveat",
)
GENERIC_ROUND_SUMMARY_COLUMNS = tuple(
    "candidate_id"
    if field == "mechanism_id"
    else "candidate_status"
    if field == "mechanism_status"
    else field
    for field in ROUND_SUMMARY_COLUMNS
) + ("candidate_type", "substantive_eligibility")


@dataclass(frozen=True)
class Issue:
    code: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "location": self.location, "message": self.message}


def _blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip() == REQUIRED_SENTINEL
    if isinstance(value, Mapping) and value:
        return all(_blank(item) for item in value.values())
    if isinstance(value, (list, tuple, set)) and value:
        return all(_blank(item) for item in value)
    return False


def _first(record: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in record and not _blank(record[key]):
            return record[key]
    return default


def _bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return None


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return parsed
        return [part.strip() for part in re.split(r"[;,|]", text) if part.strip()]
    return [value]


def _ids(value: Any) -> list[str]:
    return [str(item).strip() for item in _list(value) if not _blank(item)]


def _normalized_screening_statistic(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", text).strip().casefold()


def _version(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"^version[_-]?", "", text)
    text = re.sub(r"^v", "", text)
    if text.isdigit():
        return str(int(text))
    return text


def _parse_schema_version(value: Any) -> tuple[int, int, int] | None:
    match = re.fullmatch(
        r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+][0-9A-Za-z.-]+)?",
        str(value or "").strip(),
    )
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def _schema_at_least(value: Any, minimum: str) -> bool:
    parsed = _parse_schema_version(value)
    threshold = _parse_schema_version(minimum)
    return parsed is not None and threshold is not None and parsed >= threshold


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse an offset-aware ISO-8601 timestamp and normalize it to UTC."""

    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _lens(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).lower()


def _comparison_key_value(value: Any) -> str:
    """Canonicalize a scalar or structured comparison key for exact matching."""

    if _blank(value):
        return ""
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") or text.startswith("["):
            try:
                return _json_text(json.loads(text))
            except json.JSONDecodeError:
                pass
        return re.sub(r"\s+", " ", text).strip().lower()
    return _json_text(value)


class RunValidator:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir.resolve()
        self.errors: list[Issue] = []
        self.warnings: list[Issue] = []
        self.checked_files: dict[str, str] = {}
        self.csv_headers: dict[str, set[str]] = {}
        self.counts: dict[str, int] = {}
        self.manifest: dict[str, Any] = {}
        self.strict_schema = False
        self.profile_schema = False
        self.research_profile = ""
        self.generic_inventory_schema = False
        self.active_version = ""
        self.active_inventory: list[dict[str, str]] = []
        self.active_coverage: list[dict[str, str]] = []
        self.all_inventory: list[dict[str, str]] = []
        self.all_coverage: list[dict[str, str]] = []
        self.ledger: list[dict[str, Any]] = []
        self.families: list[dict[str, Any]] = []
        self.family_history: list[dict[str, Any]] = []
        self.all_family_records: list[dict[str, Any]] = []
        self.family_registry: dict[str, Any] = {}
        self.decision_contract: dict[str, Any] = {}
        self.prior_exposure: dict[str, Any] = {}
        self.prior_audit_status = ""
        self.prior_exposure_status = ""
        self.data_registry: dict[str, Any] = {}
        self.data_versions: list[dict[str, Any]] = []
        self.saturation_audit: dict[str, Any] = {}
        self.candidate_registry: list[dict[str, str]] = []

    def error(self, code: str, location: str, message: str) -> None:
        self.errors.append(Issue(code, location, message))

    def warn(self, code: str, location: str, message: str) -> None:
        self.warnings.append(Issue(code, location, message))

    def rel(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.run_dir))
        except ValueError:
            return path.name

    def _safe_internal_file(
        self,
        value: Any,
        location: str,
        *,
        expected_sha256: Any = None,
        kind: str = "artifact",
        required: bool = True,
    ) -> Path | None:
        """Resolve a regular file below the run root without following symlinks.

        Hashes in a mutable run cannot prove adversarial immutability.  They do,
        however, bind the locally preserved snapshot and catch accidental edits;
        callers that need stronger guarantees must anchor the digest externally.
        """

        if _blank(value):
            if required:
                self.error(
                    "missing_required_field",
                    location,
                    f"{kind.capitalize()} path is missing.",
                )
            return None
        relative = Path(str(value))
        if relative.is_absolute() or ".." in relative.parts:
            self.error(
                "unsafe_artifact_path",
                location,
                f"{kind.capitalize()} path must be relative to the run directory and cannot contain '..'.",
            )
            return None
        lexical = self.run_dir / relative
        cursor = self.run_dir
        for part in relative.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                self.error(
                    "symlink_artifact_path",
                    location,
                    f"{kind.capitalize()} path cannot traverse a symbolic link.",
                )
                return None
        try:
            resolved = lexical.resolve()
            resolved.relative_to(self.run_dir)
        except (OSError, ValueError):
            self.error(
                "unsafe_artifact_path",
                location,
                f"{kind.capitalize()} path escapes the run directory.",
            )
            return None
        if not resolved.is_file():
            if required:
                self.error(
                    "missing_artifact",
                    str(relative),
                    f"Required {kind} file is missing.",
                )
            return None
        expected = str(expected_sha256 or "").strip().lower()
        if expected_sha256 is not None:
            if not re.fullmatch(r"[0-9a-f]{64}", expected):
                self.error(
                    "invalid_sha256",
                    location,
                    f"{kind.capitalize()} SHA-256 must be a 64-character hexadecimal digest.",
                )
            else:
                actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
                if actual != expected:
                    self.error(
                        "preserved_artifact_hash_mismatch",
                        location,
                        f"Preserved {kind} does not match its bound SHA-256 digest.",
                    )
        self.checked_files[str(relative)] = kind
        return resolved

    def load_json(self, path: Path, *, required: bool = True) -> Any:
        location = self.rel(path)
        if not path.is_file():
            if required:
                self.error("missing_artifact", location, "Required JSON artifact is missing.")
            return None
        self.checked_files[location] = "json"
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            self.error("invalid_json", location, f"Cannot parse JSON: {exc}")
            return None

    def load_jsonl(self, path: Path, *, required: bool = True) -> list[dict[str, Any]]:
        location = self.rel(path)
        if not path.is_file():
            if required:
                self.error("missing_artifact", location, "Required JSONL artifact is missing.")
            return []
        self.checked_files[location] = "jsonl"
        rows: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line_number, raw in enumerate(handle, start=1):
                    if not raw.strip():
                        continue
                    try:
                        item = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        self.error(
                            "invalid_jsonl",
                            f"{location}:{line_number}",
                            f"Cannot parse JSON object: {exc}",
                        )
                        continue
                    if not isinstance(item, dict):
                        self.error(
                            "invalid_jsonl_record",
                            f"{location}:{line_number}",
                            "Each JSONL record must be an object.",
                        )
                        continue
                    item = dict(item)
                    item["__source__"] = f"{location}:{line_number}"
                    rows.append(item)
        except OSError as exc:
            self.error("unreadable_artifact", location, f"Cannot read JSONL: {exc}")
        return rows

    def load_csv(self, path: Path, *, required: bool = True) -> list[dict[str, str]]:
        location = self.rel(path)
        if not path.is_file():
            if required:
                self.error("missing_artifact", location, "Required CSV artifact is missing.")
            return []
        self.checked_files[location] = "csv"
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    self.error("invalid_csv", location, "CSV has no header row.")
                    return []
                self.csv_headers[location] = {
                    str(field).strip() for field in reader.fieldnames if field is not None
                }
                rows = []
                for row_number, row in enumerate(reader, start=2):
                    cleaned = {str(key).strip(): str(value or "").strip() for key, value in row.items()}
                    cleaned["__source__"] = f"{location}:{row_number}"
                    rows.append(cleaned)
                return rows
        except (OSError, csv.Error) as exc:
            self.error("invalid_csv", location, f"Cannot parse CSV: {exc}")
            return []

    def select_versioned(self, prefix: str, extension: str, *, required: bool = True) -> Path | None:
        directory = self.run_dir / "inventories"
        candidates = sorted(directory.glob(f"{prefix}*{extension}"))
        if not candidates:
            if required:
                self.error(
                    "missing_artifact",
                    self.rel(directory / f"{prefix}<inventory_version>{extension}"),
                    "No versioned artifact was found.",
                )
            return None
        matches = []
        for candidate in candidates:
            suffix = candidate.name[len(prefix) : -len(extension)]
            if _version(suffix) == self.active_version:
                matches.append(candidate)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            self.error(
                "ambiguous_versioned_artifact",
                self.rel(directory),
                f"Multiple artifacts match active inventory version: {[p.name for p in matches]}",
            )
            return matches[-1]
        self.error(
            "active_version_artifact_missing",
            self.rel(directory),
            f"No {prefix} artifact matches active inventory version {self.manifest.get('inventory_version')!r}.",
        )
        return candidates[-1]

    def load_all_versioned_csv(self, prefix: str) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for path in sorted((self.run_dir / "inventories").glob(f"{prefix}*.csv")):
            suffix = path.stem[len(prefix) :]
            file_version = _version(suffix)
            loaded = self.load_csv(path, required=False)
            for row in loaded:
                row["__file_version__"] = file_version
            rows.extend(loaded)
        return rows

    def validate(self) -> dict[str, Any]:
        if not self.run_dir.is_dir():
            self.error("missing_run_directory", self.run_dir.name, "Run directory does not exist.")
            return self.report()

        manifest = self.load_json(self.run_dir / "run_manifest.json")
        if isinstance(manifest, dict):
            self.manifest = manifest
        elif manifest is not None:
            self.error("invalid_manifest", "run_manifest.json", "Run manifest must be a JSON object.")

        self._validate_manifest()
        if self.profile_schema and self.research_profile == "fixed_test":
            self._validate_fixed_profile()
        elif self.profile_schema and self.research_profile == "adaptive_search":
            self._validate_adaptive_profile()
        elif not self.profile_schema or self.research_profile == "coverage_search":
            self._load_core_artifacts()
            self._validate_inventory()
            self._validate_coverage()
            self._validate_data_versions()
            self._validate_ledger()
            self._validate_selection_families()
            self._validate_decision_contract()
            self._validate_prior_exposure()
            self._validate_candidate_registry()
            self._validate_saturation()
            self._validate_transitions()
            self._validate_completion_and_pause()
            if self.profile_schema:
                self._validate_round_artifacts()
                self._validate_profile_underfit()
        elif self.profile_schema:
            # An invalid profile is already reported by _validate_manifest. Load
            # only profile-neutral artifacts so malformed metadata cannot select
            # a less demanding validation path.
            self._load_data_registry()
            self._validate_data_versions()
            self._validate_round_artifacts()

        inventory_count_label = (
            "active_candidates"
            if self.generic_inventory_schema
            or (
                self.profile_schema
                and self.research_profile in {"fixed_test", "adaptive_search"}
            )
            else "active_mechanisms"
        )
        self.counts.update(
            {
                inventory_count_label: len(self.active_inventory),
                "active_coverage_cells": len(self.active_coverage),
                "ledger_entries": len(self.ledger),
                "selection_families": len(self.families),
                "selection_family_history_records": len(self.family_history),
                "data_versions": len(self.data_versions),
                "candidates": len(self.candidate_registry),
            }
        )
        return self.report()

    def report(self) -> dict[str, Any]:
        return {
            "report_schema_version": REPORT_SCHEMA_VERSION,
            "validator_version": VALIDATOR_VERSION,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "run_directory_label": self.run_dir.name,
            "run_id": self.manifest.get("run_id"),
            "research_profile": self.research_profile or None,
            "inventory_version": self.manifest.get("inventory_version"),
            "artifact_versions": {
                "artifact_schema": self.manifest.get("artifact_schema_version"),
                "inventory": self.manifest.get("inventory_version"),
                "decision_contract": _first(
                    self.manifest,
                    "decision_contract_version",
                    "decision_contract_id",
                ),
                "prior_exposure_audit": _first(
                    self.manifest,
                    "prior_exposure_audit_version",
                    "prior_exposure_audit_id",
                ),
                "data_version_set": _first(
                    self.manifest,
                    "data_version_set_id",
                    "data_versions_version",
                ),
            },
            "valid": not self.errors,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [issue.as_dict() for issue in self.errors],
            "warnings": [issue.as_dict() for issue in self.warnings],
            "counts": dict(sorted(self.counts.items())),
            "checked_files": dict(sorted(self.checked_files.items())),
        }

    def _required(self, record: Mapping[str, Any], location: str, fields: Iterable[str]) -> None:
        for field in sorted(fields):
            if _blank(record.get(field)):
                self.error("missing_required_field", location, f"Required field {field!r} is missing or blank.")

    def _require_one(self, record: Mapping[str, Any], location: str, concept: str, keys: Sequence[str]) -> Any:
        value = _first(record, *keys)
        if _blank(value):
            self.error(
                "missing_required_field",
                location,
                f"Required {concept} is missing; use one of {', '.join(keys)}.",
            )
        return value

    def _status(self, value: Any, allowed: set[str], location: str, field: str) -> str:
        status = str(value or "").strip()
        if status not in allowed:
            self.error(
                "invalid_status",
                location,
                f"{field}={status!r} is not one of {sorted(allowed)}.",
            )
        return status

    def _manifest_bool(self, field: str) -> bool | None:
        value = self.manifest.get(field)
        parsed = _bool(value)
        if parsed is None:
            self.error("invalid_boolean", "run_manifest.json", f"{field} must be a JSON boolean.")
        elif not isinstance(value, bool):
            self.warn("noncanonical_boolean", "run_manifest.json", f"{field} should be stored as a JSON boolean.")
        return parsed

    def _validate_manifest(self) -> None:
        location = "run_manifest.json"
        schema_value = self.manifest.get("artifact_schema_version")
        parsed_schema = _parse_schema_version(schema_value)
        self.strict_schema = _schema_at_least(
            schema_value, STRICT_BASELINE_SCHEMA_VERSION
        )
        self.profile_schema = _schema_at_least(
            schema_value, ARTIFACT_SCHEMA_VERSION
        )
        supported_schema = _parse_schema_version(ARTIFACT_SCHEMA_VERSION)
        if not _blank(schema_value) and parsed_schema is None:
            self.error(
                "invalid_artifact_schema_version",
                location,
                "artifact_schema_version must be a parseable semantic version such as '1.5.0'.",
            )
        elif (
            parsed_schema is not None
            and supported_schema is not None
            and parsed_schema > supported_schema
        ):
            self.error(
                "unsupported_artifact_schema_version",
                location,
                f"Artifact schema {schema_value!r} is newer than validator support {ARTIFACT_SCHEMA_VERSION!r}; use a compatible validator rather than silently applying older rules.",
            )
        elif not self.strict_schema:
            self.warn(
                "legacy_artifact_schema",
                location,
                f"Artifact schema {STRICT_BASELINE_SCHEMA_VERSION} gates were not checked; keep the run legacy or migrate its current artifacts before declaring artifact_schema_version>={STRICT_BASELINE_SCHEMA_VERSION}.",
            )
        common_fields = {
                "run_id",
                "question",
                "scientific_scope",
                "execution_mode",
                "governance_status",
        }
        if self.profile_schema:
            common_fields |= {
                "research_profile",
                "stage_status",
                "profile_history",
                "round_artifacts",
            }
        self._required(self.manifest, location, common_fields)
        if self.profile_schema:
            self.research_profile = str(
                self.manifest.get("research_profile", "")
            ).strip()
            self._status(
                self.research_profile,
                RESEARCH_PROFILES,
                location,
                "research_profile",
            )
            self._status(
                self.manifest.get("stage_status"),
                STAGE_STATUSES,
                location,
                "stage_status",
            )
            self._validate_profile_history()

        if not self.profile_schema or self.research_profile == "coverage_search":
            self._required(
                self.manifest,
                location,
                {
                "inventory_version",
                "inventory_status",
                "search_status",
                "inventory_saturated",
                "coverage_complete",
                "search_ledger_audited",
                "decision_contract_applied",
                "decision_status",
                },
            )
        elif self.research_profile == "adaptive_search":
            self._required(
                self.manifest,
                location,
                {
                    "search_ledger_audited",
                    "decision_contract_applied",
                    "decision_status",
                },
            )

        if not self.profile_schema or self.research_profile in {
            "adaptive_search",
            "coverage_search",
        }:
            self._require_one(
                self.manifest,
                location,
                "decision-contract version",
                ("decision_contract_version", "decision_contract_id"),
            )
            self._require_one(
                self.manifest,
                location,
                "prior-exposure-audit version",
                ("prior_exposure_audit_version", "prior_exposure_audit_id"),
            )
        self._require_one(
            self.manifest,
            location,
            "data-version-set identifier",
            ("data_version_set_id", "data_versions_version"),
        )
        self.active_version = _version(self.manifest.get("inventory_version"))
        if (not self.profile_schema or self.research_profile == "coverage_search") and not self.active_version:
            self.error("invalid_inventory_version", location, "inventory_version cannot be empty.")
        self._status(
            self.manifest.get("execution_mode"),
            EXECUTION_MODES,
            location,
            "execution_mode",
        )
        self._status(self.manifest.get("governance_status"), GOVERNANCE_STATUSES, location, "governance_status")
        if not self.profile_schema or self.research_profile == "coverage_search":
            self._status(self.manifest.get("inventory_status"), INVENTORY_STATUSES, location, "inventory_status")
            self._status(self.manifest.get("search_status"), SEARCH_STATUSES, location, "search_status")
            self._status(self.manifest.get("decision_status"), DECISION_STATUSES, location, "decision_status")
            self._manifest_bool("inventory_saturated")
            self._manifest_bool("coverage_complete")
            self._manifest_bool("search_ledger_audited")
            self._manifest_bool("decision_contract_applied")
        elif self.research_profile == "adaptive_search":
            self._status(self.manifest.get("decision_status"), DECISION_STATUSES, location, "decision_status")
            self._manifest_bool("search_ledger_audited")
            self._manifest_bool("decision_contract_applied")

    def _validate_profile_history(self) -> None:
        location = "run_manifest.json#profile_history"
        raw = self.manifest.get("profile_history")
        if not isinstance(raw, list) or not raw:
            self.error(
                "invalid_profile_history",
                location,
                "Schema 1.5 profile_history must be a nonempty ordered list.",
            )
            return
        previous_rank = -1
        previous_profile = ""
        previous_started_at: datetime | None = None
        for index, entry in enumerate(raw, start=1):
            entry_location = f"{location}[{index}]"
            if not isinstance(entry, Mapping):
                self.error("invalid_profile_history", entry_location, "Profile history entry must be an object.")
                continue
            self._required(entry, entry_location, PROFILE_HISTORY_REQUIRED_FIELDS)
            profile = str(entry.get("profile", "")).strip()
            if profile not in RESEARCH_PROFILES:
                self.error("invalid_research_profile", entry_location, f"profile={profile!r} is not canonical.")
                continue
            started_at = _parse_timestamp(entry.get("started_at"))
            if started_at is None:
                self.error(
                    "invalid_profile_history_timestamp",
                    entry_location,
                    "started_at must be an offset-aware ISO-8601 timestamp.",
                )
            elif previous_started_at is not None and started_at <= previous_started_at:
                self.error(
                    "profile_history_timestamp_order",
                    entry_location,
                    "Profile-history started_at timestamps must be strictly increasing.",
                )
            rank = PROFILE_RANK[profile]
            if rank < previous_rank:
                self.error(
                    "research_profile_downgrade",
                    entry_location,
                    f"Profile history downgrades from {previous_profile!r} to {profile!r}; profile downgrades are forbidden.",
                )
            if rank > previous_rank and previous_rank >= 0:
                preserved_logical_paths = self._validate_profile_upgrade_snapshot(
                    entry,
                    entry_location,
                    previous_profile,
                    previous_started_at,
                    started_at,
                )
                if not preserved_logical_paths:
                    # Retain the pre-1.5.0 diagnostic names for consumers while
                    # making clear that booleans are no longer sufficient proof.
                    self.error(
                        "profile_upgrade_history_not_preserved",
                        entry_location,
                        "A profile upgrade requires a hash-bound preservation snapshot; history_preserved=true alone is not evidence.",
                    )
                    self.error(
                        "profile_upgrade_exposure_not_preserved",
                        entry_location,
                        "A profile upgrade requires hash-bound prior-exposure evidence inside the preservation snapshot; prior_exposure_preserved=true alone is not evidence.",
                    )
                if (
                    previous_profile == "fixed_test"
                    and "claim_card.json" not in preserved_logical_paths
                ):
                    self.error(
                        "profile_upgrade_fixed_claim_not_preserved",
                        entry_location,
                        "An upgrade from fixed_test must include a hash-bound, nonsymlink claim_card.json snapshot.",
                    )
            previous_rank = max(previous_rank, rank)
            previous_profile = profile
            if started_at is not None:
                previous_started_at = started_at
        final_profile = str(raw[-1].get("profile", "")).strip() if isinstance(raw[-1], Mapping) else ""
        if final_profile and final_profile != self.research_profile:
            self.error(
                "profile_history_current_mismatch",
                location,
                "The final profile_history entry must equal research_profile.",
            )

    def _validate_profile_upgrade_snapshot(
        self,
        entry: Mapping[str, Any],
        location: str,
        previous_profile: str,
        previous_started_at: datetime | None,
        upgrade_started_at: datetime | None,
    ) -> set[str]:
        """Validate concrete, hash-bound evidence for a profile upgrade."""

        snapshot_path = entry.get("preservation_snapshot_path")
        snapshot_hash = entry.get("preservation_snapshot_sha256")
        if _blank(snapshot_path) or _blank(snapshot_hash):
            self.error(
                "profile_upgrade_snapshot_missing",
                location,
                "Profile upgrade requires preservation_snapshot_path and preservation_snapshot_sha256.",
            )
            return set()
        snapshot_file = self._safe_internal_file(
            snapshot_path,
            f"{location}#preservation_snapshot_path",
            expected_sha256=snapshot_hash,
            kind="profile preservation snapshot",
        )
        if snapshot_file is None:
            return set()
        snapshot = self.load_json(snapshot_file, required=False)
        if not isinstance(snapshot, Mapping):
            self.error(
                "invalid_profile_upgrade_snapshot",
                str(snapshot_path),
                "Profile preservation snapshot must be a JSON object.",
            )
            return set()
        snapshot_profile = str(
            _first(snapshot, "profile", "research_profile", default="")
        ).strip()
        if snapshot_profile != previous_profile:
            self.error(
                "profile_upgrade_snapshot_profile_mismatch",
                str(snapshot_path),
                f"Snapshot profile {snapshot_profile!r} does not match prior profile {previous_profile!r}.",
            )
        captured_at = _parse_timestamp(snapshot.get("captured_at"))
        if captured_at is None:
            self.error(
                "invalid_profile_upgrade_snapshot_timestamp",
                str(snapshot_path),
                "captured_at must be an offset-aware ISO-8601 timestamp.",
            )
        elif (
            previous_started_at is not None
            and captured_at < previous_started_at
        ) or (
            upgrade_started_at is not None
            and captured_at > upgrade_started_at
        ):
            self.error(
                "profile_upgrade_snapshot_timestamp_order",
                str(snapshot_path),
                "Snapshot capture time must fall between the prior-profile start and upgrade start.",
            )
        artifacts = snapshot.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            self.error(
                "invalid_profile_upgrade_snapshot",
                str(snapshot_path),
                "Snapshot requires a nonempty artifacts list.",
            )
            return set()
        expected_by_profile = {
            "fixed_test": {
                "run_manifest.json",
                "claim_card.json",
                "data_versions.json",
            },
            "adaptive_search": {
                "run_manifest.json",
                "decision_contract.json",
                "prior_exposure_audit.json",
                "data_versions.json",
                "search_ledger.jsonl",
                "selection_families.json",
                "status_transitions.jsonl",
                "candidate_registry.csv",
            },
        }
        logical_paths: set[str] = set()
        preserved_files: dict[str, Path] = {}
        for index, artifact in enumerate(artifacts, start=1):
            artifact_location = f"{snapshot_path}#artifacts[{index}]"
            if not isinstance(artifact, Mapping):
                self.error(
                    "invalid_profile_upgrade_snapshot_artifact",
                    artifact_location,
                    "Snapshot artifact entry must be an object.",
                )
                continue
            self._required(
                artifact,
                artifact_location,
                {"logical_path", "snapshot_path", "sha256"},
            )
            logical_path = str(artifact.get("logical_path", "")).strip()
            if logical_path in logical_paths:
                self.error(
                    "duplicate_profile_upgrade_snapshot_artifact",
                    artifact_location,
                    f"logical_path {logical_path!r} is duplicated.",
                )
            logical_paths.add(logical_path)
            preserved_file = self._safe_internal_file(
                artifact.get("snapshot_path"),
                f"{artifact_location}#snapshot_path",
                expected_sha256=artifact.get("sha256"),
                kind=f"preserved {logical_path or 'profile artifact'}",
            )
            if logical_path and preserved_file is not None:
                preserved_files[logical_path] = preserved_file
        missing = expected_by_profile.get(previous_profile, set()) - logical_paths
        if missing:
            self.error(
                "incomplete_profile_upgrade_snapshot",
                str(snapshot_path),
                f"Snapshot omits required prior-profile artifacts {sorted(missing)}.",
            )
        prior_manifest_path = preserved_files.get("run_manifest.json")
        if prior_manifest_path is not None:
            prior_manifest = self.load_json(prior_manifest_path, required=False)
            if not isinstance(prior_manifest, Mapping):
                self.error(
                    "invalid_profile_upgrade_manifest_snapshot",
                    str(snapshot_path),
                    "Preserved run_manifest.json must be a JSON object.",
                )
            else:
                prior_manifest_profile = str(
                    prior_manifest.get("research_profile", "")
                ).strip()
                if prior_manifest_profile != previous_profile:
                    self.error(
                        "profile_upgrade_manifest_profile_mismatch",
                        str(snapshot_path),
                        f"Preserved manifest profile {prior_manifest_profile!r} does not match {previous_profile!r}.",
                    )
                required_round_paths: set[str] = set()
                round_records = prior_manifest.get("round_artifacts")
                if not isinstance(round_records, list) or not round_records:
                    self.error(
                        "invalid_profile_upgrade_manifest_snapshot",
                        str(snapshot_path),
                        "Preserved manifest must retain its nonempty round_artifacts list.",
                    )
                else:
                    for round_index, record in enumerate(round_records, start=1):
                        if not isinstance(record, Mapping):
                            self.error(
                                "invalid_profile_upgrade_manifest_snapshot",
                                f"{snapshot_path}#round_artifacts[{round_index}]",
                                "Preserved round record must be an object.",
                            )
                            continue
                        for field in ("report_path", "reproduce_path"):
                            path_value = str(record.get(field, "")).strip()
                            if not path_value:
                                self.error(
                                    "invalid_profile_upgrade_manifest_snapshot",
                                    f"{snapshot_path}#round_artifacts[{round_index}]",
                                    f"Preserved round record requires {field}.",
                                )
                            else:
                                required_round_paths.add(path_value)
                missing_round_paths = required_round_paths - logical_paths
                if missing_round_paths:
                    self.error(
                        "incomplete_profile_upgrade_round_snapshot",
                        str(snapshot_path),
                        f"Snapshot omits hash-bound prior round artifacts {sorted(missing_round_paths)}.",
                    )
        return logical_paths

    def _artifact_path(self, value: Any, location: str) -> Path | None:
        return self._safe_internal_file(
            value,
            location,
            kind="round artifact",
        )

    def _validate_round_artifacts(self) -> None:
        location = "run_manifest.json#round_artifacts"
        records = self.manifest.get("round_artifacts")
        if not isinstance(records, list) or not records:
            self.error(
                "invalid_round_artifacts",
                location,
                "Schema 1.5 requires at least one round-artifact record.",
            )
            return
        seen: set[str] = set()
        completed = 0
        terminal_records = 0
        previous_sealed_at: datetime | None = None
        for index, record in enumerate(records, start=1):
            item_location = f"{location}[{index}]"
            if not isinstance(record, Mapping):
                self.error("invalid_round_artifact", item_location, "Round-artifact record must be an object.")
                continue
            self._required(
                record,
                item_location,
                {"round_id", "status", "report_path", "reproduce_path"},
            )
            round_id = str(record.get("round_id", "")).strip()
            if round_id in seen:
                self.error("duplicate_round_id", item_location, f"round_id {round_id!r} is duplicated.")
            seen.add(round_id)
            status = self._status(
                record.get("status"), ROUND_RECORD_STATUSES, item_location, "status"
            )
            report_path = self._artifact_path(
                record.get("report_path"), f"{item_location}#report_path"
            )
            reproduce_path = self._artifact_path(
                record.get("reproduce_path"), f"{item_location}#reproduce_path"
            )
            if status != "planned":
                terminal_records += 1
                if status == "completed":
                    completed += 1
                self._required(
                    record,
                    item_location,
                    {"sealed_at", "report_sha256", "reproduce_sha256"},
                )
                sealed_at = _parse_timestamp(record.get("sealed_at"))
                if sealed_at is None:
                    self.error(
                        "invalid_round_seal_timestamp",
                        item_location,
                        "sealed_at must be an offset-aware ISO-8601 timestamp for every nonplanned round.",
                    )
                elif previous_sealed_at is not None and sealed_at < previous_sealed_at:
                    self.error(
                        "round_seal_timestamp_order",
                        item_location,
                        "Round records must preserve nondecreasing sealed_at order.",
                    )
                if sealed_at is not None:
                    previous_sealed_at = sealed_at
                for label, path, field in (
                    ("report", report_path, "report_sha256"),
                    ("reproduction", reproduce_path, "reproduce_sha256"),
                ):
                    expected = str(record.get(field, "")).strip().lower()
                    if expected and not re.fullmatch(r"[0-9a-f]{64}", expected):
                        self.error("invalid_sha256", item_location, f"{field} must be a 64-character hexadecimal SHA-256 digest.")
                    elif path is not None and expected:
                        actual = hashlib.sha256(path.read_bytes()).hexdigest()
                        if actual != expected:
                            self.error(
                                "sealed_round_hash_mismatch",
                                item_location,
                                f"Sealed {label} artifact hash does not match {field}.",
                            )
        if self.manifest.get("stage_status") == "completed_as_scoped" and completed == 0:
            self.error(
                "stage_completion_without_sealed_round",
                location,
                "completed_as_scoped requires at least one completed, hash-sealed round record.",
            )
        if (
            self.research_profile == "fixed_test"
            and completed
            and self.manifest.get("stage_status") != "completed_as_scoped"
        ):
            self.error(
                "fixed_completion_state_regression",
                location,
                "A fixed_test with a completed, sealed round cannot return to a noncompleted stage status.",
            )
        elif (
            self.research_profile == "fixed_test"
            and terminal_records
            and self.manifest.get("stage_status") == "planned"
        ):
            self.error(
                "fixed_stage_status_regression",
                location,
                "A fixed_test with a sealed terminal round cannot return to stage_status=planned.",
            )

    def _validate_profile_underfit(self) -> None:
        profile = self.research_profile
        saturation_claim = (
            _bool(self.manifest.get("inventory_saturated")) is True
            or _bool(self.manifest.get("coverage_complete")) is True
            or self.manifest.get("inventory_status") == "saturated"
            or self.manifest.get("search_status") == "complete_within_scope"
        )
        if profile in {"fixed_test", "adaptive_search"} and saturation_claim:
            self.error(
                "profile_underfit_saturation_claim",
                "run_manifest.json",
                f"{profile} cannot claim inventory saturation or complete_within_scope; upgrade to coverage_search while preserving history.",
            )
        if (
            profile == "coverage_search"
            and self.manifest.get("stage_status") == "completed_as_scoped"
            and _bool(self.manifest.get("search_ledger_audited")) is not True
        ):
            self.error(
                "coverage_stage_completion_unreviewed",
                "run_manifest.json",
                "Coverage stage completion requires search_ledger_audited=true; it still does not imply inventory saturation.",
            )
        if profile == "fixed_test":
            expanded_artifacts = [
                "decision_contract.json",
                "prior_exposure_audit.json",
                "search_ledger.jsonl",
                "selection_families.json",
                "candidate_registry.csv",
                "status_transitions.jsonl",
                "execution_queue.csv",
            ]
            expanded_artifacts.extend(
                str(path.relative_to(self.run_dir))
                for path in sorted((self.run_dir / "inventories").glob("*"))
                if path.is_file()
            )
            for pattern in ("*/inventory.json", "*/summary.csv", "*/round_gate.md"):
                expanded_artifacts.extend(
                    str(path.relative_to(self.run_dir))
                    for path in sorted((self.run_dir / "rounds").glob(pattern))
                    if path.is_file() or path.is_symlink()
                )
            present = [name for name in expanded_artifacts if (self.run_dir / name).is_file()]
            if present:
                self.error(
                    "profile_underfit_adaptive_artifacts",
                    "run_manifest.json",
                    f"fixed_test contains adaptive/coverage artifacts {present}; upgrade the profile instead of validating under reduced gates.",
                )
        elif profile == "adaptive_search":
            coverage_manifest_fields = {
                "inventory_version",
                "inventory_status",
                "search_status",
                "inventory_saturated",
                "coverage_complete",
                "inventory_audit_protocol",
                "inventory_generation_lenses",
                "coverage_unit_definition",
                "coverage_closure_rules",
                "saturation_rule",
                "saturation_required_sources",
            }
            present_fields = sorted(
                field for field in coverage_manifest_fields if field in self.manifest
            )
            coverage_artifacts: list[str] = []
            inventory_root = self.run_dir / "inventories"
            if inventory_root.is_symlink():
                coverage_artifacts.append("inventories/ (symlink)")
            if inventory_root.is_dir():
                coverage_artifacts.extend(
                    str(path.relative_to(self.run_dir))
                    for path in sorted(inventory_root.rglob("*"))
                    if path.is_file() or path.is_symlink()
                )
            for candidate in (self.run_dir / "execution_queue.csv",):
                if candidate.is_file() or candidate.is_symlink():
                    coverage_artifacts.append(str(candidate.relative_to(self.run_dir)))
            for pattern in ("*/inventory.json", "*/summary.csv", "*/round_gate.md"):
                coverage_artifacts.extend(
                    str(path.relative_to(self.run_dir))
                    for path in sorted((self.run_dir / "rounds").glob(pattern))
                    if path.is_file() or path.is_symlink()
                )
            if present_fields or coverage_artifacts:
                self.error(
                    "profile_underfit_coverage_evidence",
                    "run_manifest.json",
                    "adaptive_search contains coverage-search state or artifacts "
                    f"(manifest fields={present_fields}, artifacts={sorted(set(coverage_artifacts))}); "
                    "upgrade to coverage_search so these artifacts cannot bypass coverage validation.",
                )

    def _validate_fixed_profile(self) -> None:
        self._load_data_registry()
        self._validate_data_versions()
        claim = self.load_json(self.run_dir / "claim_card.json")
        if isinstance(claim, Mapping):
            location = "claim_card.json"
            self._required(claim, location, FIXED_CLAIM_REQUIRED_FIELDS)
            self._status(
                claim.get("specification_timing"),
                SPECIFICATION_TIMINGS,
                location,
                "specification_timing",
            )
            self._status(
                claim.get("prior_exposure_status"),
                PRIOR_EXPOSURE_STATUSES,
                location,
                "prior_exposure_status",
            )
            self._status(
                claim.get("evidence_stage"),
                EVIDENCE_STAGES,
                location,
                "evidence_stage",
            )
            result_status = self._status(
                claim.get("result_status"), RESULT_STATUSES, location, "result_status"
            )
            completed = _bool(claim.get("completed_as_scoped"))
            if completed is None:
                self.error("invalid_boolean", location, "completed_as_scoped must be a boolean.")
            if completed is True and result_status == "not_run":
                self.error("fixed_completion_without_result", location, "A completed fixed test must record a result.")
            if completed is True and self.manifest.get("stage_status") != "completed_as_scoped":
                self.error(
                    "fixed_completion_state_regression",
                    location,
                    "claim_card completed_as_scoped=true is one-way within this run and requires manifest stage_status=completed_as_scoped.",
                )
            claim_data_versions = _ids(claim.get("data_version_ids"))
            if completed is True and not claim_data_versions:
                self.error(
                    "fixed_completion_without_data_version",
                    location,
                    "A completed fixed test must pin at least one registered data_version_id.",
                )
            if self.manifest.get("stage_status") == "completed_as_scoped" and completed is not True:
                self.error("stage_completion_mismatch", location, "Manifest completion requires claim_card completed_as_scoped=true.")
            registered = {
                str(_first(item, "data_version_id", "version_id", default=""))
                for item in self.data_versions
            }
            for version_id in claim_data_versions:
                if version_id not in registered:
                    self.error("unknown_claim_data_version", location, f"Claim references unregistered data version {version_id!r}.")
        elif claim is not None:
            self.error("invalid_claim_card", "claim_card.json", "claim_card must be an object.")
        self._validate_round_artifacts()
        self._validate_profile_underfit()

    def _load_adaptive_artifacts(self) -> None:
        self._load_data_registry()
        self.ledger = self.load_jsonl(self.run_dir / "search_ledger.jsonl")
        raw_families = self.load_json(self.run_dir / "selection_families.json")
        if isinstance(raw_families, dict):
            self.family_registry = raw_families
            self.families = self._normalize_records(
                raw_families, ("families", "selection_families", "current"), "selection_family_id"
            )
            self.family_history = self._normalize_records(
                raw_families.get("history", []), ("history", "records", "families"), "selection_family_id"
            )
        else:
            self.families = self._normalize_records(
                raw_families, ("families", "selection_families"), "selection_family_id"
            )
        for family in self.families:
            family["__family_record_role__"] = "current"
        for family in self.family_history:
            family["__family_record_role__"] = "history"
        self.all_family_records = self.family_history + self.families
        contract = self.load_json(self.run_dir / "decision_contract.json")
        if isinstance(contract, dict):
            self.decision_contract = contract
        elif contract is not None:
            self.error("invalid_decision_contract", "decision_contract.json", "Decision contract must be an object.")
        exposure = self.load_json(self.run_dir / "prior_exposure_audit.json")
        if isinstance(exposure, dict):
            self.prior_exposure = exposure
        elif exposure is not None:
            self.error("invalid_prior_exposure_audit", "prior_exposure_audit.json", "Prior-exposure audit must be an object.")
        self.candidate_registry = self.load_csv(self.run_dir / "candidate_registry.csv")

    def _validate_adaptive_profile(self) -> None:
        self._load_adaptive_artifacts()
        self._validate_data_versions()
        self._validate_adaptive_ledger()
        self._validate_adaptive_families()
        self._validate_decision_contract()
        self._validate_prior_exposure()
        self._validate_adaptive_candidates()
        self._validate_adaptive_transitions()
        self._validate_round_artifacts()
        self._validate_profile_underfit()
        if self.manifest.get("stage_status") == "completed_as_scoped":
            if _bool(self.manifest.get("search_ledger_audited")) is not True:
                self.error("adaptive_completion_gate_failed", "run_manifest.json", "Adaptive stage completion requires search_ledger_audited=true.")
            if self.prior_audit_status not in {"complete", "unknown", "not_applicable"} or self.prior_exposure_status == "not_assessed":
                self.error("adaptive_completion_gate_failed", "prior_exposure_audit.json", "Adaptive stage completion requires an assessed prior-exposure audit.")

    def _validate_adaptive_ledger(self) -> None:
        location = "search_ledger.jsonl"
        registered_versions = {
            str(_first(item, "data_version_id", "version_id", default=""))
            for item in self.data_versions
        }
        seen: set[str] = set()
        for index, entry in enumerate(self.ledger, start=1):
            item_location = entry.get("__source__", f"{location}:{index}")
            if not _blank(entry.get("coverage_cell_id")):
                self.error(
                    "profile_underfit_coverage_behavior",
                    item_location,
                    "adaptive_search ledger entries cannot claim coverage cells; upgrade to coverage_search and validate the complete coverage state.",
                )
            self._required(
                entry,
                item_location,
                {
                    "ledger_entry_id",
                    "decision_influence",
                    "input_and_code_state",
                    "execution_status",
                    "result_status",
                },
            )
            entry_id = str(entry.get("ledger_entry_id", "")).strip()
            if entry_id in seen:
                self.error("duplicate_ledger_entry_id", item_location, f"Duplicate ledger_entry_id {entry_id!r}.")
            seen.add(entry_id)
            influence = _bool(entry.get("decision_influence"))
            if influence is None:
                self.error("invalid_boolean", item_location, "decision_influence must be a boolean.")
            if influence:
                for field in (
                    "selection_family_id",
                    "selection_family_version",
                    "selection_path_stage",
                    "data_look_id",
                    "seed_policy_id",
                    "artifact_paths",
                ):
                    if field not in entry or _blank(entry.get(field)):
                        self.error("incomplete_selection_path_entry", item_location, f"Selection-influencing entry requires {field}.")
                candidate_refs = _ids(
                    _first(entry, "candidate_ids", "candidate_id", default=[])
                )
                if not candidate_refs:
                    self.error(
                        "influential_entry_without_candidate",
                        item_location,
                        "Adaptive selection-influencing entry requires candidate_id or candidate_ids.",
                    )
            execution = self._status(entry.get("execution_status"), EXECUTION_STATUSES, item_location, "execution_status")
            result = self._status(entry.get("result_status"), RESULT_STATUSES, item_location, "result_status")
            if execution in {"failed", "abandoned", "blocked"} and result in {"supported", "null"}:
                self.error("invalid_execution_result_pair", item_location, "Failed, abandoned, or blocked entry cannot carry supported/null.")
            if execution == "completed" and result == "not_run":
                self.error("completed_without_result", item_location, "Completed ledger entry must record a result.")
            refs = _ids(entry.get("data_version_ids"))
            state = entry.get("input_and_code_state")
            if isinstance(state, Mapping):
                refs.extend(_ids(_first(state, "data_version_ids", "data_versions", default=[])))
            for ref in set(refs):
                if ref not in registered_versions:
                    self.error("unknown_ledger_data_version", item_location, f"Ledger data version {ref!r} is not registered.")
            if influence and execution != "planned" and not refs:
                severity = self.error if _bool(self.manifest.get("search_ledger_audited")) else self.warn
                severity("ledger_data_version_unpinned", item_location, "Executed selection-influencing entry must pin data-version identifiers.")

    def _validate_adaptive_families(self) -> None:
        location = "selection_families.json"
        ledger_by_id = {
            str(entry.get("ledger_entry_id", "")): entry for entry in self.ledger
        }
        influencing_by_family: dict[str, set[str]] = defaultdict(set)
        for entry in self.ledger:
            if _bool(entry.get("decision_influence")):
                influencing_by_family[str(entry.get("selection_family_id", ""))].add(
                    str(entry.get("ledger_entry_id", ""))
                )
        seen_current: set[str] = set()
        seen_versions: set[tuple[str, str]] = set()
        current_decision_id = str(_first(self.decision_contract, "decision_id", "decision_contract_id", default="")).strip()
        for index, family in enumerate(self.all_family_records, start=1):
            role = str(family.get("__family_record_role__", "current"))
            item_location = f"{location}#{role}[{index}]"
            family_id = self._family_id(family)
            family_version = str(_first(family, "selection_family_version", "family_version", default="")).strip()
            self._required(
                family,
                item_location,
                {
                    "selection_family_id",
                    "selection_family_version",
                    "decision_id",
                    "candidate_ids",
                    "selection_path_ledger_entry_ids",
                    "inference_method",
                    "comparability_status",
                }
                | STRICT_SELECTION_FAMILY_FIELDS,
            )
            if (family_id, family_version) in seen_versions:
                self.error("duplicate_selection_family_version", item_location, f"Duplicate family version {(family_id, family_version)!r}.")
            seen_versions.add((family_id, family_version))
            if role == "current" and family_id in seen_current:
                self.error("duplicate_current_selection_family", item_location, f"Current family {family_id!r} is duplicated.")
            if role == "current":
                seen_current.add(family_id)
            family_decision = str(_first(family, "decision_id", "decision_contract_id", default="")).strip()
            if role == "current" and current_decision_id and family_decision != current_decision_id:
                self.error("family_decision_id_mismatch", item_location, "Family decision identifier differs from the current Decision Contract.")
            comparison = self._status(
                _first(family, "comparison_status", "comparability_status"),
                COMPARISON_STATUSES,
                item_location,
                "comparability_status",
            )
            self._status(family.get("evidence_stage"), EVIDENCE_STAGES, item_location, "evidence_stage")
            requirement = self._status(family.get("transportability_requirement"), TRANSPORTABILITY_REQUIREMENTS, item_location, "transportability_requirement")
            transport = self._status(family.get("transportability_status"), TRANSPORTABILITY_STATUSES, item_location, "transportability_status")
            if requirement == "same_population":
                if _comparison_key_value(family.get("target_population")) != _comparison_key_value(self.decision_contract.get("target_population")):
                    self.error("family_same_population_mismatch", item_location, "same_population family target differs from Decision Contract target.")
                if transport != "not_required":
                    self.error("invalid_family_transportability_status", item_location, "same_population requires transportability_status=not_required.")
            elif requirement == "validation_required" and transport == "not_required":
                self.error("invalid_family_transportability_status", item_location, "validation_required cannot be not_required.")
            elif requirement == "parallel_only":
                if transport != "not_required" or comparison == "comparable_within_family":
                    self.error("parallel_only_family_comparable", item_location, "parallel_only must remain noncomparable and use transportability_status=not_required.")
            path_ids = set(self._family_ledger_ids(family))
            unknown = path_ids - set(ledger_by_id)
            if unknown:
                self.error("unknown_family_ledger_entry", item_location, f"Selection path references unknown ledger entries {sorted(unknown)}.")
            for ledger_id in path_ids & set(ledger_by_id):
                if str(ledger_by_id[ledger_id].get("selection_family_id", "")) != family_id:
                    self.error("family_ledger_id_mismatch", item_location, f"Ledger {ledger_id!r} belongs to a different family.")
            if role == "current":
                missing = influencing_by_family.get(family_id, set()) - path_ids
                if missing:
                    severity = self.error if _bool(self.manifest.get("search_ledger_audited")) else self.warn
                    severity("incomplete_selection_path", item_location, f"Family omits influencing ledger entries {sorted(missing)}.")

    def _validate_adaptive_candidates(self) -> None:
        path = self.run_dir / "candidate_registry.csv"
        location = self.rel(path)
        missing_headers = ADAPTIVE_CANDIDATE_REQUIRED_FIELDS - self.csv_headers.get(location, set())
        if missing_headers:
            self.error("missing_candidate_columns", location, f"Adaptive registry header is missing columns {sorted(missing_headers)}.")
        family_by_key = {
            (self._family_id(family), str(_first(family, "selection_family_version", "family_version", default="")).strip()): family
            for family in self.all_family_records
        }
        current_family_by_id = {self._family_id(family): family for family in self.families}
        ledger_by_id = {str(entry.get("ledger_entry_id", "")): entry for entry in self.ledger}
        eligible_family_ids, declared_family_ids, contract_keys = self._contract_selection_family_policy()
        seen: set[str] = set()
        candidates_by_id: dict[str, dict[str, str]] = {}
        for index, row in enumerate(self.candidate_registry, start=1):
            item_location = row.get("__source__", f"{location}:{index + 1}")
            self._required(row, item_location, ADAPTIVE_CANDIDATE_ROW_REQUIRED_FIELDS)
            candidate_id = str(row.get("candidate_id", "")).strip()
            if candidate_id in seen:
                self.error("duplicate_candidate_id", item_location, f"candidate_id {candidate_id!r} is duplicated.")
            seen.add(candidate_id)
            candidates_by_id[candidate_id] = row
            candidate_type = self._status(row.get("candidate_type"), CANDIDATE_TYPES, item_location, "candidate_type")
            substantive = self._status(row.get("substantive_eligibility"), SUBSTANTIVE_ELIGIBILITY_STATUSES, item_location, "substantive_eligibility")
            alignment = str(row.get("mechanism_alignment", "")).strip()
            if candidate_type == "mechanism":
                self._status(alignment, MECHANISM_ALIGNMENTS, item_location, "mechanism_alignment")
                if alignment == "not_applicable":
                    self.error(
                        "candidate_type_alignment_mismatch",
                        item_location,
                        "A mechanism candidate requires a mechanism-bearing alignment status; not_applicable is reserved for nonmechanism candidates.",
                    )
            elif alignment:
                self._status(alignment, MECHANISM_ALIGNMENTS, item_location, "mechanism_alignment")
                if alignment != "not_applicable":
                    self.error(
                        "candidate_type_alignment_mismatch",
                        item_location,
                        "mechanism_alignment applies only to mechanism candidates; nonmechanism candidates must leave it empty or use not_applicable.",
                    )
            error_relevant = _bool(row.get("measurement_error_relevant"))
            if error_relevant is None:
                self.error("invalid_boolean", item_location, "measurement_error_relevant must be a boolean-like value.")
            error_sensitivity = str(row.get("measurement_error_sensitivity", "")).strip()
            if error_relevant or error_sensitivity:
                self._status(error_sensitivity, MEASUREMENT_ERROR_SENSITIVITIES, item_location, "measurement_error_sensitivity")
            if error_relevant is True and error_sensitivity in {
                "",
                "not_applicable",
                "not_required",
            }:
                self.error(
                    "measurement_error_relevance_mismatch",
                    item_location,
                    "measurement_error_relevant=true requires planned, passed, failed, or inconclusive sensitivity status.",
                )
            elif error_relevant is False and error_sensitivity not in {
                "",
                "not_applicable",
                "not_required",
            }:
                self.error(
                    "measurement_error_relevance_mismatch",
                    item_location,
                    "measurement_error_relevant=false cannot carry a substantive sensitivity result; leave it empty or use not_required or justified not_applicable.",
                )
            family_id = str(row.get("selection_family_id", "")).strip()
            family_version = str(row.get("selection_family_version", "")).strip()
            family = family_by_key.get((family_id, family_version))
            if family is None:
                self.error("unknown_candidate_family_version", item_location, f"Candidate references missing family {(family_id, family_version)!r}.")
            elif current_family_by_id.get(family_id) is not family:
                self.error("active_candidate_family_version_mismatch", item_location, "Adaptive candidate must reference the current family version.")
            if family_id not in declared_family_ids:
                self.error("candidate_family_not_declared_in_contract", item_location, f"Family {family_id!r} is not declared by the Decision Contract.")
            comparability = self._status(row.get("comparability_status"), COMPARISON_STATUSES, item_location, "comparability_status")
            decision = self._status(row.get("decision_status"), DECISION_STATUSES, item_location, "decision_status")
            self._status(row.get("specification_timing"), SPECIFICATION_TIMINGS, item_location, "specification_timing")
            prior = self._status(row.get("prior_exposure_status"), PRIOR_EXPOSURE_STATUSES, item_location, "prior_exposure_status")
            confirmatory = self._status(row.get("confirmatory_status"), CONFIRMATORY_STATUSES, item_location, "confirmatory_status")
            self._status(row.get("future_verification_status"), FUTURE_VERIFICATION_STATUSES, item_location, "future_verification_status")
            self._status(row.get("evidence_stage"), EVIDENCE_STAGES, item_location, "evidence_stage")
            self._status(row.get("verification_status"), VERIFICATION_STATUSES, item_location, "verification_status")
            promoted = decision in PROMOTED_DECISION_STATUSES
            if promoted and family_id not in eligible_family_ids:
                self.error("candidate_family_not_eligible_for_decision", item_location, f"Promoted candidate family {family_id!r} is not decision eligible.")
            if promoted and substantive != "eligible":
                self.error("candidate_substantive_eligibility_gate_failed", item_location, "Promoted candidate must be substantively eligible.")
            if promoted and candidate_type == "mechanism" and alignment not in {"direct", "calibrated_proxy"}:
                self.error("candidate_mechanism_alignment_gate_failed", item_location, "Promoted mechanism requires direct or calibrated_proxy mechanism alignment.")
            if promoted and error_relevant is True and error_sensitivity != "passed":
                self.error("candidate_measurement_error_gate_failed", item_location, "Measurement-error-relevant promotion requires sensitivity status passed.")
            if promoted and family is not None:
                transport_ok, reason = self._family_transport_gate(family)
                if not transport_ok:
                    self.error("candidate_family_transport_gate_failed", item_location, f"Candidate transport gate failed: {reason}.")
            if decision in {"leading", "tie"} and comparability != "comparable_within_family":
                self.error("incomparable_candidate_selected", item_location, "Leading/tied candidate must be comparable within family.")
            if prior in {"known_overlap", "unknown", "not_assessed"} and confirmatory == "unrestricted_by_prior_exposure":
                self.error("candidate_prior_exposure_conflict", item_location, "Candidate confirmatory status conflicts with prior exposure.")
            for ledger_id in _ids(row.get("ledger_entry_ids")):
                entry = ledger_by_id.get(ledger_id)
                if entry is None:
                    self.error("unknown_candidate_ledger_entry", item_location, f"Unknown ledger entry {ledger_id!r}.")
                elif str(entry.get("selection_family_id", "")) != family_id:
                    self.error("candidate_ledger_family_mismatch", item_location, f"Ledger {ledger_id!r} belongs to another family.")
            candidate_key = _comparison_key_value(row.get("comparison_key"))
            family_key = self._comparison_key(family) if family is not None else ""
            if candidate_key and family_key and candidate_key != family_key:
                self.error("candidate_family_comparison_key_mismatch", item_location, "Candidate comparison key differs from family key.")
            allowed_keys = contract_keys.get(family_id, set())
            if candidate_key and allowed_keys and candidate_key not in allowed_keys:
                self.error("candidate_contract_comparison_key_mismatch", item_location, "Candidate comparison key differs from Decision Contract.")

        for index, family in enumerate(self.families, start=1):
            unknown = set(_ids(family.get("candidate_ids"))) - set(candidates_by_id)
            if unknown:
                self.error("unknown_family_candidate", f"selection_families.json#families[{index}]", f"Family references unknown candidates {sorted(unknown)}.")

        applied = _bool(self.manifest.get("decision_contract_applied"))
        run_decision = str(self.manifest.get("decision_status", ""))
        leading_count = sum(
            row.get("decision_status") == "leading"
            for row in self.candidate_registry
        )
        tie_count = sum(
            row.get("decision_status") == "tie"
            for row in self.candidate_registry
        )
        if applied is True and run_decision not in TERMINAL_RUN_DECISION_STATUSES:
            self.error("decision_contract_application_mismatch", "run_manifest.json", "Applied Decision Contract requires terminal decision status.")
        if applied is False and run_decision in TERMINAL_RUN_DECISION_STATUSES:
            self.error("decision_contract_application_mismatch", "run_manifest.json", "Terminal decision requires decision_contract_applied=true.")
        if applied is not True and (leading_count or tie_count):
            self.error("candidate_decision_mismatch", location, "An unapplied Decision Contract cannot contain a leading or tied candidate.")
        if run_decision == "leading" and (leading_count != 1 or tie_count):
            self.error("candidate_decision_mismatch", location, "Run decision leading requires exactly one leading candidate and no tied candidate.")
        elif run_decision == "tie" and (tie_count < 2 or leading_count):
            self.error("candidate_decision_mismatch", location, "Run decision tie requires at least two tied candidates and no leading candidate.")
        elif run_decision not in {"leading", "tie"} and (leading_count or tie_count):
            self.error("candidate_decision_mismatch", location, "A non-leading, non-tie run decision cannot contain an active winner.")

    def _validate_adaptive_transitions(self) -> None:
        transitions = self.load_jsonl(self.run_dir / "status_transitions.jsonl")
        seen: set[str] = set()
        for index, item in enumerate(transitions, start=1):
            location = item.get("__source__", f"status_transitions.jsonl:{index}")
            self._required(
                item,
                location,
                {"transition_id", "entity_type", "entity_id", "status_field", "from_status", "to_status", "changed_at", "evidence"},
            )
            transition_id = str(item.get("transition_id", "")).strip()
            if transition_id in seen:
                self.error("duplicate_transition_id", location, f"transition_id {transition_id!r} is duplicated.")
            seen.add(transition_id)
            entity_type = str(item.get("entity_type", "")).strip()
            status_field = str(item.get("status_field", "")).strip()
            if entity_type in {
                "inventory",
                "mechanism_inventory",
                "candidate_inventory",
                "coverage_cell",
                "cell",
                "coverage",
            } or status_field in {"inventory_status", "coverage_status", "search_status"}:
                self.error(
                    "profile_underfit_coverage_behavior",
                    location,
                    "adaptive_search cannot record coverage-search status transitions; upgrade to coverage_search.",
                )

    def _load_core_artifacts(self) -> None:
        generic_paths = sorted(
            (self.run_dir / "inventories").glob("candidate_inventory_*.csv")
        )
        legacy_paths = sorted(
            (self.run_dir / "inventories").glob("mechanism_inventory_*.csv")
        )
        self.generic_inventory_schema = self.profile_schema and bool(generic_paths)
        if self.profile_schema and generic_paths and legacy_paths:
            self.error(
                "ambiguous_inventory_schema",
                "inventories/",
                "Schema 1.5 coverage_search must use candidate_inventory or the legacy mechanism_inventory, not both.",
            )
        inventory_prefix = (
            "candidate_inventory_"
            if self.generic_inventory_schema
            else "mechanism_inventory_"
        )
        inventory_path = self.select_versioned(inventory_prefix, ".csv")
        coverage_path = self.select_versioned("coverage_matrix_", ".csv")
        saturation_path = self.select_versioned("saturation_audit_", ".json", required=False)
        self.all_inventory = self.load_all_versioned_csv(inventory_prefix)
        if self.generic_inventory_schema:
            for row in self.all_inventory:
                row["mechanism_id"] = row.get("candidate_id", "")
                row["parent_mechanism_id"] = row.get("parent_candidate_id", "")
                row["mechanism"] = row.get("candidate", "")
                row["distinct_pathway"] = row.get("distinct_role", "")
                row["mechanism_status"] = row.get("candidate_status", "")
        self.all_coverage = self.load_all_versioned_csv("coverage_matrix_")
        if self.generic_inventory_schema:
            for row in self.all_coverage:
                row["mechanism_id"] = row.get("candidate_id", "")
        self.active_inventory = [
            row for row in self.all_inventory if row.get("__file_version__") == self.active_version
        ]
        self.active_coverage = [
            row for row in self.all_coverage if row.get("__file_version__") == self.active_version
        ]
        saturation = self.load_json(saturation_path, required=False) if saturation_path else None
        if isinstance(saturation, dict):
            self.saturation_audit = saturation
        elif saturation is not None:
            self.error("invalid_saturation_audit", self.rel(saturation_path), "Saturation audit must be an object.")

        self.ledger = self.load_jsonl(self.run_dir / "search_ledger.jsonl")
        raw_families = self.load_json(self.run_dir / "selection_families.json")
        if isinstance(raw_families, dict):
            self.family_registry = raw_families
            self.families = self._normalize_records(
                raw_families,
                ("families", "selection_families", "current"),
                "selection_family_id",
            )
            self.family_history = self._normalize_records(
                raw_families.get("history", []),
                ("history", "records", "families"),
                "selection_family_id",
            )
        else:
            self.families = self._normalize_records(
                raw_families,
                ("families", "selection_families"),
                "selection_family_id",
            )
            self.family_history = []
        for family in self.families:
            family["__family_record_role__"] = "current"
        for family in self.family_history:
            family["__family_record_role__"] = "history"
        self.all_family_records = self.family_history + self.families

        contract = self.load_json(self.run_dir / "decision_contract.json")
        if isinstance(contract, dict):
            self.decision_contract = contract
        elif contract is not None:
            self.error("invalid_decision_contract", "decision_contract.json", "Decision contract must be an object.")

        exposure = self.load_json(self.run_dir / "prior_exposure_audit.json")
        if isinstance(exposure, dict):
            self.prior_exposure = exposure
        elif exposure is not None:
            self.error("invalid_prior_exposure_audit", "prior_exposure_audit.json", "Prior-exposure audit must be an object.")

        self._load_data_registry()
        candidate_required = str(self.manifest.get("execution_mode", "")).strip() != "design_only"
        self.candidate_registry = self.load_csv(
            self.run_dir / "candidate_registry.csv",
            required=candidate_required,
        )

    def _load_data_registry(self) -> None:
        data_registry = self.load_json(self.run_dir / "data_versions.json")
        if isinstance(data_registry, dict):
            self.data_registry = data_registry
        elif isinstance(data_registry, list):
            self.data_registry = {"data_versions": data_registry}
        elif data_registry is not None:
            self.error("invalid_data_versions", "data_versions.json", "Data versions must be an object or list.")
        self.data_versions = self._normalize_records(
            self.data_registry,
            ("data_versions", "data_products", "versions"),
            "data_product_id",
        )

    def _normalize_records(
        self,
        raw: Any,
        collection_keys: Sequence[str],
        identifier_key: str,
    ) -> list[dict[str, Any]]:
        if raw is None:
            return []
        value = raw
        if isinstance(raw, dict):
            for key in collection_keys:
                if key in raw:
                    value = raw[key]
                    break
        if isinstance(value, list):
            records = value
        elif isinstance(value, dict):
            records = []
            for key, item in value.items():
                if not isinstance(item, dict):
                    continue
                record = dict(item)
                record.setdefault(identifier_key, key)
                records.append(record)
        else:
            return []
        return [dict(item) for item in records if isinstance(item, dict)]

    def _validate_versioned_headers(self, prefix: str, required_fields: set[str]) -> None:
        for path in sorted((self.run_dir / "inventories").glob(f"{prefix}*.csv")):
            location = self.rel(path)
            headers = self.csv_headers.get(location, set())
            missing = required_fields - headers
            if missing:
                self.error(
                    "missing_snapshot_columns",
                    location,
                    f"Snapshot header is missing required columns {sorted(missing)}.",
                )

    def _validate_inventory(self) -> None:
        if self.generic_inventory_schema:
            self._validate_versioned_headers(
                "candidate_inventory_", GENERIC_INVENTORY_REQUIRED_COLUMNS
            )
        else:
            self._validate_versioned_headers("mechanism_inventory_", INVENTORY_REQUIRED_COLUMNS)
        data_products = {
            str(_first(item, "data_product_id", "product_id", default="")).strip()
            for item in self.data_versions
        }
        ids_by_version: dict[str, set[str]] = defaultdict(set)
        all_ids = {row.get("mechanism_id", "") for row in self.all_inventory}

        for index, row in enumerate(self.all_inventory, start=1):
            location = row.get("__source__", f"inventory row {index}")
            self._required(
                row,
                location,
                GENERIC_INVENTORY_REQUIRED_FIELDS
                if self.generic_inventory_schema
                else INVENTORY_REQUIRED_FIELDS,
            )
            if self.generic_inventory_schema:
                self._status(
                    row.get("candidate_type"),
                    CANDIDATE_TYPES,
                    location,
                    "candidate_type",
                )
            file_version = row.get("__file_version__", "")
            row_version = _version(row.get("inventory_version"))
            if row_version != file_version:
                self.error(
                    "snapshot_version_mismatch",
                    location,
                    f"Row inventory_version {row.get('inventory_version')!r} does not match file version {file_version!r}.",
                )
            mechanism_id = row.get("mechanism_id", "")
            if mechanism_id and mechanism_id in ids_by_version[file_version]:
                self.error(
                    "duplicate_candidate_id" if self.generic_inventory_schema else "duplicate_mechanism_id",
                    location,
                    f"candidate identifier {mechanism_id!r} is duplicated within inventory version {file_version!r}.",
                )
            ids_by_version[file_version].add(mechanism_id)
            self._status(
                row.get("specification_timing"),
                SPECIFICATION_TIMINGS,
                location,
                "specification_timing",
            )
            mechanism_status = self._status(
                row.get("mechanism_status"),
                MECHANISM_STATUSES,
                location,
                "candidate_status" if self.generic_inventory_schema else "mechanism_status",
            )
            if self.strict_schema:
                data_support = self._status(
                    row.get("data_support_status"),
                    DATA_SUPPORT_STATUSES,
                    location,
                    "data_support_status",
                )
                if (
                    mechanism_status == "needs_data"
                    and data_support in {"supported", "not_assessed"}
                ):
                    self.error(
                        "invalid_candidate_data_support_pair"
                        if self.generic_inventory_schema
                        else "invalid_mechanism_data_support_pair",
                        location,
                        f"{'candidate_status' if self.generic_inventory_schema else 'mechanism_status'}='needs_data' requires an assessed noneligible data-support classification, not 'supported' or 'not_assessed'.",
                    )
            for product_id in _ids(row.get("required_data_products")):
                if product_id not in data_products:
                    self.error(
                        "unknown_data_product",
                        location,
                        f"Required data product {product_id!r} is absent from data_versions.json.",
                    )
            duplicate_of = row.get("duplicate_of", "")
            if duplicate_of and duplicate_of == mechanism_id:
                self.error(
                    "self_duplicate",
                    location,
                    f"A {'candidate' if self.generic_inventory_schema else 'mechanism'} cannot be its own duplicate_of target.",
                )

        for row in self.all_inventory:
            location = row.get("__source__", "inventory")
            file_version = row.get("__file_version__", "")
            duplicate_of = row.get("duplicate_of", "")
            if duplicate_of and duplicate_of not in ids_by_version[file_version]:
                self.error(
                    "unknown_duplicate_candidate"
                    if self.generic_inventory_schema
                    else "unknown_duplicate_mechanism",
                    location,
                    f"duplicate_of target {duplicate_of!r} is absent from inventory version {file_version!r}.",
                )
            parent_id = row.get("parent_mechanism_id", "")
            if parent_id and parent_id not in all_ids:
                self.error(
                    "unknown_parent_candidate"
                    if self.generic_inventory_schema
                    else "unknown_parent_mechanism",
                    location,
                    f"{'parent_candidate_id' if self.generic_inventory_schema else 'parent_mechanism_id'} {parent_id!r} is absent from all preserved inventories.",
                )

    def _validate_coverage(self) -> None:
        if self.generic_inventory_schema:
            required_columns = GENERIC_COVERAGE_REQUIRED_COLUMNS
            required_fields = GENERIC_COVERAGE_REQUIRED_FIELDS
        else:
            required_columns = COVERAGE_REQUIRED_COLUMNS | (
                STRICT_COVERAGE_REQUIRED_FIELDS if self.strict_schema else set()
            )
            required_fields = COVERAGE_REQUIRED_FIELDS | (
                STRICT_COVERAGE_REQUIRED_FIELDS if self.strict_schema else set()
            )
        self._validate_versioned_headers("coverage_matrix_", required_columns)
        mechanism_ids_by_version: dict[str, set[str]] = defaultdict(set)
        candidate_type_by_key: dict[tuple[str, str], str] = {}
        for row in self.all_inventory:
            mechanism_ids_by_version[row.get("__file_version__", "")].add(
                row.get("mechanism_id", "")
            )
            candidate_type_by_key[
                (row.get("__file_version__", ""), row.get("mechanism_id", ""))
            ] = str(row.get("candidate_type", "mechanism")).strip() or "mechanism"
        data_by_product: dict[str, set[str]] = defaultdict(set)
        for item in self.data_versions:
            product_id = str(_first(item, "data_product_id", "product_id", default="")).strip()
            version_id = str(_first(item, "data_version_id", "version_id", default="")).strip()
            if product_id and version_id:
                data_by_product[product_id].add(version_id)

        cells_by_version: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
        for index, row in enumerate(self.all_coverage, start=1):
            location = row.get("__source__", f"coverage row {index}")
            status_raw = row.get("coverage_status", "")
            if status_raw.startswith("covered_by:"):
                row["covered_by_cell_id"] = status_raw.split(":", 1)[1].strip()
                row["coverage_status"] = "covered_by"
            self._required(row, location, required_fields)
            file_version = row.get("__file_version__", "")
            row_version = _version(row.get("inventory_version"))
            if row_version != file_version:
                self.error(
                    "snapshot_version_mismatch",
                    location,
                    f"Row inventory_version {row.get('inventory_version')!r} does not match file version {file_version!r}.",
                )
            cell_id = row.get("coverage_cell_id", "")
            if cell_id and cell_id in cells_by_version[file_version]:
                self.error(
                    "duplicate_coverage_cell_id",
                    location,
                    f"coverage_cell_id {cell_id!r} is duplicated within inventory version {file_version!r}.",
                )
            cells_by_version[file_version][cell_id] = row
            if row.get("mechanism_id") not in mechanism_ids_by_version[file_version]:
                self.error(
                    "unknown_candidate" if self.generic_inventory_schema else "unknown_mechanism",
                    location,
                    f"{'candidate_id' if self.generic_inventory_schema else 'mechanism_id'} {row.get('mechanism_id')!r} is absent from inventory version {file_version!r}.",
                )
            candidate_type = candidate_type_by_key.get(
                (file_version, row.get("mechanism_id", "")), ""
            )

            products = _ids(row.get("data_product_id"))
            version_ids = _ids(row.get("data_version_id"))
            for product_id in products:
                if product_id not in data_by_product:
                    self.error(
                        "unknown_data_product",
                        location,
                        f"data_product_id {product_id!r} is absent from data_versions.json.",
                    )
                    continue
                for version_id in version_ids:
                    if version_id not in data_by_product[product_id]:
                        self.error(
                            "unknown_data_version",
                            location,
                            f"data_version_id {version_id!r} is not registered for {product_id!r}.",
                        )

            coverage_status = self._status(
                row.get("coverage_status"), COVERAGE_STATUSES, location, "coverage_status"
            )
            execution_status = self._status(
                row.get("execution_status"), EXECUTION_STATUSES, location, "execution_status"
            )
            result_status = self._status(
                row.get("result_status"), RESULT_STATUSES, location, "result_status"
            )
            timing = self._status(
                row.get("specification_timing"),
                SPECIFICATION_TIMINGS,
                location,
                "specification_timing",
            )
            stage = self._status(
                row.get("evidence_stage"), EVIDENCE_STAGES, location, "evidence_stage"
            )
            verification = self._status(
                row.get("verification_status"),
                VERIFICATION_STATUSES,
                location,
                "verification_status",
            )
            self._status(
                row.get("comparability_status"),
                COMPARISON_STATUSES,
                location,
                "comparability_status",
            )
            self._status(
                row.get("execution_tier"), EXECUTION_TIERS, location, "execution_tier"
            )
            if self.strict_schema:
                if self.generic_inventory_schema:
                    self._status(
                        row.get("substantive_eligibility"),
                        SUBSTANTIVE_ELIGIBILITY_STATUSES,
                        location,
                        "substantive_eligibility",
                    )
                    mechanism_alignment = str(
                        row.get("mechanism_alignment", "")
                    ).strip()
                    if candidate_type == "mechanism":
                        self._status(
                            mechanism_alignment,
                            MECHANISM_ALIGNMENTS,
                            location,
                            "mechanism_alignment",
                        )
                        if mechanism_alignment == "not_applicable":
                            self.error(
                                "candidate_type_alignment_mismatch",
                                location,
                                "A mechanism coverage cell requires a mechanism-bearing alignment status; not_applicable is reserved for nonmechanism candidates.",
                            )
                    elif mechanism_alignment:
                        self._status(
                            mechanism_alignment,
                            MECHANISM_ALIGNMENTS,
                            location,
                            "mechanism_alignment",
                        )
                        if mechanism_alignment != "not_applicable":
                            self.error(
                                "candidate_type_alignment_mismatch",
                                location,
                                "mechanism_alignment applies only to mechanism candidates; nonmechanism coverage cells must leave it empty or use not_applicable.",
                            )
                else:
                    self._status(
                        row.get("mechanism_alignment"),
                        MECHANISM_ALIGNMENTS,
                        location,
                        "mechanism_alignment",
                    )
                self._status(
                    row.get("measurement_error_sensitivity"),
                    MEASUREMENT_ERROR_SENSITIVITIES,
                    location,
                    "measurement_error_sensitivity",
                )

            valid_results = {"supported", "null", "inconclusive", "artifact"}
            if coverage_status == "tested_valid":
                if execution_status != "completed":
                    self.error(
                        "invalid_coverage_execution_pair",
                        location,
                        "tested_valid requires execution_status=completed.",
                    )
                if result_status not in valid_results:
                    self.error(
                        "invalid_tested_result",
                        location,
                        "tested_valid requires a valid scientific result status.",
                    )
            if execution_status in {"failed", "abandoned", "blocked"} and result_status not in {
                "not_run",
                "invalid",
            }:
                self.error(
                    "invalid_execution_result_pair",
                    location,
                    "Failed, abandoned, or blocked execution cannot carry a scientific result.",
                )
            if execution_status == "planned" and coverage_status == "tested_valid":
                self.error(
                    "unrun_cell_marked_closed",
                    location,
                    "A merely planned cell cannot be marked tested_valid.",
                )
            if result_status == "not_run" and execution_status == "completed":
                self.error(
                    "completed_without_result",
                    location,
                    "Completed execution must record a result status other than not_run.",
                )
            if result_status in valid_results and execution_status != "completed":
                self.error(
                    "result_without_completed_execution",
                    location,
                    "A scientific result requires execution_status=completed.",
                )
            if result_status == "invalid" and coverage_status == "tested_valid":
                self.error(
                    "invalid_result_marked_valid",
                    location,
                    "An invalid result cannot close a cell as tested_valid.",
                )
            if stage == "independent_verification" and timing != "pre_result_frozen":
                self.error(
                    "adaptive_independent_verification",
                    location,
                    "Independent verification requires a pre-result-frozen specification.",
                )
            if verification in {"holdout_verified", "externally_replicated"} and stage != "independent_verification":
                self.error(
                    "verification_stage_mismatch",
                    location,
                    "Verified status requires evidence_stage=independent_verification.",
                )
            if coverage_status == "resource_blocked" and execution_status not in {
                "planned",
                "blocked",
                "abandoned",
            }:
                self.error(
                    "invalid_resource_block",
                    location,
                    "resource_blocked is inconsistent with the execution status.",
                )

        for file_version, rows_by_id in cells_by_version.items():
            for row in rows_by_id.values():
                if row.get("coverage_status") != "covered_by":
                    continue
                location = row.get("__source__", "coverage")
                target = _first(
                    row,
                    "covered_by_cell_id",
                    "coverage_equivalent_to",
                    default="",
                )
                if not target:
                    self.error(
                        "missing_covered_by_target",
                        location,
                        "covered_by requires a named equivalent coverage cell.",
                    )
                elif target not in rows_by_id:
                    self.error(
                        "unknown_covered_by_target",
                        location,
                        f"covered_by target {target!r} is absent from inventory version {file_version!r}.",
                    )
                elif target == row.get("coverage_cell_id"):
                    self.error(
                        "self_coverage_reference",
                        location,
                        "A coverage cell cannot cover itself.",
                    )
                elif rows_by_id[target].get("coverage_status") not in CLOSED_COVERAGE_STATUSES:
                    self.error(
                        "open_covered_by_target",
                        location,
                        "covered_by target must itself be closed.",
                    )

    def _validate_data_versions(self) -> None:
        location = "data_versions.json"
        manifest_set = _first(self.manifest, "data_version_set_id", "data_versions_version")
        registry_set = _first(self.data_registry, "data_version_set_id", "data_versions_version")
        if not _blank(manifest_set) and not _blank(registry_set) and str(manifest_set) != str(registry_set):
            self.error("data_version_set_mismatch", location, "Data-version-set identifier does not match the run manifest.")
        if _blank(registry_set):
            self.error("missing_required_field", location, "data_version_set_id is required.")

        by_product: dict[str, list[dict[str, Any]]] = defaultdict(list)
        pairs: set[tuple[str, str]] = set()
        for index, item in enumerate(self.data_versions, start=1):
            item_location = f"{location}#data_version[{index}]"
            product = str(_first(item, "data_product_id", "product_id", default="")).strip()
            version_id = str(_first(item, "data_version_id", "version_id", default="")).strip()
            if not product:
                self.error("missing_required_field", item_location, "data_product_id is required.")
            if not version_id:
                self.error("missing_required_field", item_location, "data_version_id is required.")
            if product and version_id:
                pair = (product, version_id)
                if pair in pairs:
                    self.error("duplicate_data_version", item_location, f"Duplicate data version pair {pair!r}.")
                pairs.add(pair)
                by_product[product].append(item)

        for row in self.active_coverage:
            location_row = row.get("__source__", "coverage")
            products = _ids(row.get("data_product_id"))
            declared_versions = _ids(row.get("data_version_id"))
            for product in products:
                matches = by_product.get(product, [])
                if not matches:
                    self.error("unknown_data_product", location_row, f"data_product_id {product!r} is absent from data_versions.json.")
                elif declared_versions:
                    known_versions = {str(_first(item, "data_version_id", "version_id")) for item in matches}
                    for version_id in declared_versions:
                        if version_id not in known_versions:
                            self.error("unknown_data_version", location_row, f"data_version_id {version_id!r} is not registered for {product!r}.")
                elif len(matches) > 1:
                    self.error("ambiguous_data_version", location_row, f"Multiple versions exist for {product!r}; coverage cell must pin data_version_id.")

    def _validate_ledger(self) -> None:
        all_cells = {
            (row.get("__file_version__", ""), row.get("coverage_cell_id", "")): row
            for row in self.all_coverage
        }
        seen: set[str] = set()
        ledger_by_cell: dict[tuple[str, str], list[str]] = defaultdict(list)
        registered_versions = {
            str(_first(item, "data_version_id", "version_id", default="")) for item in self.data_versions
        }

        for index, entry in enumerate(self.ledger, start=1):
            location = entry.get("__source__", f"search ledger entry {index}")
            self._required(
                entry,
                location,
                {
                    "ledger_entry_id",
                    "inventory_version",
                    "decision_influence",
                    "input_and_code_state",
                    "execution_status",
                    "result_status",
                },
            )
            entry_id = str(entry.get("ledger_entry_id", "")).strip()
            if entry_id in seen:
                self.error("duplicate_ledger_entry_id", location, f"Duplicate ledger_entry_id {entry_id!r}.")
            seen.add(entry_id)
            influence = _bool(entry.get("decision_influence"))
            if influence is None:
                self.error("invalid_boolean", location, "decision_influence must be a boolean.")
            cell_id = str(entry.get("coverage_cell_id", "") or "").strip()
            entry_version = _version(entry.get("inventory_version"))
            family_id = str(entry.get("selection_family_id", "") or "").strip()
            if influence:
                if not cell_id:
                    self.error("influential_entry_without_cell", location, "Selection-influencing ledger entry requires coverage_cell_id.")
                if not family_id:
                    self.error("influential_entry_without_family", location, "Selection-influencing ledger entry requires selection_family_id.")
                for field in (
                    "selection_family_version",
                    "selection_path_stage",
                    "data_look_id",
                    "seed_policy_id",
                    "artifact_paths",
                ):
                    if field not in entry or _blank(entry.get(field)):
                        self.error("incomplete_selection_path_entry", location, f"Selection-influencing ledger entry requires {field}.")
            if cell_id:
                cell_key = (entry_version, cell_id)
                if cell_key not in all_cells:
                    self.error(
                        "unknown_coverage_cell",
                        location,
                        f"coverage_cell_id {cell_id!r} is absent from inventory version {entry.get('inventory_version')!r}.",
                    )
                ledger_by_cell[cell_key].append(entry_id)

            execution = self._status(entry.get("execution_status"), EXECUTION_STATUSES, location, "execution_status")
            result = self._status(entry.get("result_status"), RESULT_STATUSES, location, "result_status")
            if execution in {"failed", "abandoned", "blocked"} and result in {"supported", "null"}:
                self.error("invalid_execution_result_pair", location, "Failed, abandoned, or blocked ledger entry cannot be supported or null.")
            if execution == "completed" and result == "not_run":
                self.error("completed_without_result", location, "Completed ledger entry must record a result.")

            data_refs = _ids(entry.get("data_version_ids"))
            state = entry.get("input_and_code_state")
            if isinstance(state, dict):
                data_refs.extend(_ids(_first(state, "data_version_ids", "data_versions")))
            for data_ref in set(data_refs):
                if data_ref not in registered_versions:
                    self.error("unknown_ledger_data_version", location, f"Ledger data version {data_ref!r} is not registered.")
            if influence and execution != "planned" and not data_refs:
                severity = self.error if _bool(self.manifest.get("search_ledger_audited")) else self.warn
                severity("ledger_data_version_unpinned", location, "Executed selection-influencing entry must pin data-version identifiers.")

        for (cell_version, cell_id), row in all_cells.items():
            location = row.get("__source__", "coverage")
            declared = set(_ids(row.get("ledger_entry_ids")))
            actual = set(ledger_by_cell.get((cell_version, cell_id), []))
            missing = actual - declared
            unknown = declared - seen
            if missing:
                self.error("coverage_ledger_backreference_missing", location, f"Coverage cell omits ledger entries {sorted(missing)}.")
            if unknown:
                self.error("unknown_ledger_entry", location, f"Coverage cell references unknown ledger entries {sorted(unknown)}.")
            execution = row.get("execution_status")
            if execution in {"completed", "failed", "abandoned"} and not actual:
                self.error(
                    "executed_cell_without_ledger",
                    location,
                    "Executed, failed, or abandoned coverage cell has no same-version ledger entry.",
                )

    def _family_id(self, family: Mapping[str, Any]) -> str:
        return str(_first(family, "selection_family_id", "family_id", default="")).strip()

    def _family_cells(self, family: Mapping[str, Any]) -> list[str]:
        return _ids(_first(family, "included_cell_ids", "coverage_cell_ids", "selection_path_cell_ids"))

    def _family_ledger_ids(self, family: Mapping[str, Any]) -> list[str]:
        return _ids(
            _first(
                family,
                "selection_path_ledger_entry_ids",
                "included_ledger_entry_ids",
                "full_selection_path_ledger_entry_ids",
            )
        )

    def _comparison_key(self, family: Mapping[str, Any]) -> str:
        key = _first(family, "comparison_key", "comparability_key")
        if not _blank(key):
            return _comparison_key_value(key)
        components = {
            name: family.get(name)
            for name in (
                "target_population",
                "supported_sample_id",
                "estimand",
                "data_quality_regime",
                "evidence_stage",
            )
        }
        if all(not _blank(value) for value in components.values()):
            return _comparison_key_value(components)
        return ""

    def _family_transport_gate(
        self, family: Mapping[str, Any] | None
    ) -> tuple[bool, str]:
        if family is None:
            return False, "selection-family record is missing"
        requirement = str(family.get("transportability_requirement", "")).strip()
        status = str(family.get("transportability_status", "")).strip()
        same_target = _comparison_key_value(family.get("target_population")) == (
            _comparison_key_value(self.decision_contract.get("target_population"))
        )
        if requirement == "same_population":
            if not same_target:
                return False, "family and decision target populations differ"
            if status != "not_required":
                return False, "same_population requires transportability_status=not_required"
            return True, ""
        if requirement == "validation_required":
            if status != "passed":
                return False, "required transport validation has not passed"
            return True, ""
        if requirement == "parallel_only":
            return False, "parallel_only families cannot enter the decision"
        return False, "transportability requirement is missing or invalid"

    def _validate_selection_families(self) -> None:
        known_cell_ids = {row.get("coverage_cell_id", "") for row in self.all_coverage}
        ledger_by_id = {
            str(entry.get("ledger_entry_id", "")): entry for entry in self.ledger
        }
        influencing_by_family: dict[str, set[str]] = defaultdict(set)
        current_decision_id = str(
            _first(
                self.decision_contract,
                "decision_id",
                "decision_contract_id",
                default="",
            )
        ).strip()
        for entry in self.ledger:
            if _bool(entry.get("decision_influence")):
                influencing_by_family[str(entry.get("selection_family_id", ""))].add(
                    str(entry.get("ledger_entry_id", ""))
                )

        current_by_id: dict[str, dict[str, Any]] = {}
        records_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for index, family in enumerate(self.all_family_records, start=1):
            role = str(family.get("__family_record_role__", "current"))
            location = f"selection_families.json#{role}[{index}]"
            family_id = self._family_id(family)
            if not family_id:
                self.error("missing_required_field", location, "selection_family_id is required.")
                continue
            family_version = str(
                self._require_one(
                    family,
                    location,
                    "selection-family version",
                    ("selection_family_version", "family_version"),
                )
                or ""
            ).strip()
            family_key = (family_id, family_version)
            if family_version and family_key in records_by_key:
                self.error(
                    "duplicate_selection_family_version",
                    location,
                    f"Duplicate selection-family record {family_key!r}.",
                )
            records_by_key[family_key] = family
            if role == "current":
                if family_id in current_by_id:
                    self.error(
                        "duplicate_current_selection_family",
                        location,
                        f"Current selection_family_id {family_id!r} is not unique.",
                    )
                current_by_id[family_id] = family
            family_decision_id = str(
                self._require_one(
                    family,
                    location,
                    "decision identifier",
                    ("decision_id", "decision_contract_id"),
                )
                or ""
            ).strip()
            if (
                role == "current"
                and current_decision_id
                and family_decision_id
                and family_decision_id != current_decision_id
            ):
                self.error(
                    "family_decision_id_mismatch",
                    location,
                    f"Family decision identifier {family_decision_id!r} does not match current Decision Contract {current_decision_id!r}.",
                )
            self._require_one(family, location, "inference method or policy", ("inference_method", "inference_policy", "adaptive_inference_policy"))
            status = str(_first(family, "comparison_status", "comparability_status", default="")).strip()
            self._status(status, COMPARISON_STATUSES, location, "comparison_status")
            if self.strict_schema:
                self._required(family, location, STRICT_SELECTION_FAMILY_FIELDS)
                self._status(
                    family.get("evidence_stage"),
                    EVIDENCE_STAGES,
                    location,
                    "evidence_stage",
                )
                requirement = self._status(
                    family.get("transportability_requirement"),
                    TRANSPORTABILITY_REQUIREMENTS,
                    location,
                    "transportability_requirement",
                )
                transport_status = self._status(
                    family.get("transportability_status"),
                    TRANSPORTABILITY_STATUSES,
                    location,
                    "transportability_status",
                )
                decision_target = self.decision_contract.get("target_population")
                family_target = family.get("target_population")
                if requirement == "same_population":
                    if (
                        role == "current"
                        and not _blank(decision_target)
                        and _comparison_key_value(family_target)
                        != _comparison_key_value(decision_target)
                    ):
                        self.error(
                            "family_same_population_mismatch",
                            location,
                            "same_population is invalid when family and Decision Contract target populations differ.",
                        )
                    if transport_status != "not_required":
                        self.error(
                            "invalid_family_transportability_status",
                            location,
                            "same_population requires transportability_status=not_required.",
                        )
                if requirement == "validation_required" and transport_status == "not_required":
                    self.error(
                        "invalid_family_transportability_status",
                        location,
                        "validation_required cannot use transportability_status=not_required.",
                    )
                if requirement == "parallel_only":
                    if transport_status != "not_required":
                        self.error(
                            "invalid_family_transportability_status",
                            location,
                            "parallel_only requires transportability_status=not_required.",
                        )
                    if status not in {
                        "parallel_conclusion",
                        "support_limited_candidate",
                        "not_eligible_for_decision",
                    }:
                        self.error(
                            "parallel_only_family_comparable",
                            location,
                            "parallel_only family must remain parallel, support-limited, or not eligible for the decision.",
                        )
            if status == "comparable_within_family" and not self._comparison_key(family):
                self.error("missing_comparison_key", location, "Comparable family requires a comparison key or all comparison-key components.")

            cells = self._family_cells(family)
            if not cells:
                self.warn("empty_selection_family", location, "Selection family has no included coverage cells.")
            for cell_id in cells:
                if cell_id not in known_cell_ids:
                    self.error("unknown_family_cell", location, f"Included coverage cell {cell_id!r} does not exist.")
                elif not any(
                    row.get("coverage_cell_id") == cell_id
                    and row.get("selection_family_id") == family_id
                    and str(row.get("selection_family_version", "")) == family_version
                    for row in self.all_coverage
                ):
                    self.error(
                        "family_cell_version_mismatch",
                        location,
                        f"Coverage cell {cell_id!r} does not reference selection-family version {family_key!r}.",
                    )

            path_ids = set(self._family_ledger_ids(family))
            unknown_path = path_ids - set(ledger_by_id)
            if unknown_path:
                self.error("unknown_family_ledger_entry", location, f"Selection path references unknown ledger entries {sorted(unknown_path)}.")
            for ledger_id in path_ids & set(ledger_by_id):
                ledger_family_id = str(
                    ledger_by_id[ledger_id].get("selection_family_id", "")
                )
                if ledger_family_id != family_id:
                    self.error(
                        "family_ledger_id_mismatch",
                        location,
                        f"Selection path ledger {ledger_id!r} belongs to family {ledger_family_id!r}, not {family_id!r}.",
                    )
            if role == "current":
                missing_path = influencing_by_family.get(family_id, set()) - path_ids
                if missing_path:
                    severity = (
                        self.error
                        if _bool(self.manifest.get("search_ledger_audited"))
                        else self.warn
                    )
                    severity(
                        "incomplete_selection_path",
                        location,
                        f"Current family path omits influencing ledger entries {sorted(missing_path)} across preserved family versions.",
                    )
            path_complete = _bool(_first(family, "selection_path_complete", "full_selection_path_audited"))
            if (
                role == "current"
                and family_id
                in {row.get("selection_family_id", "") for row in self.active_coverage}
                and _bool(self.manifest.get("search_ledger_audited"))
                and path_complete is not True
            ):
                self.error("selection_path_not_audited", location, "Audited ledger requires selection_path_complete=true for every active family.")

        for entry in self.ledger:
            family_id = str(entry.get("selection_family_id", "")).strip()
            if not family_id:
                continue
            location = entry.get("__source__", "search ledger")
            ledger_family_version = str(entry.get("selection_family_version", "")).strip()
            if not ledger_family_version:
                self.error(
                    "missing_ledger_family_version",
                    location,
                    "Ledger entry with a selection family must pin selection_family_version.",
                )
            elif (family_id, ledger_family_version) not in records_by_key:
                self.error(
                    "unknown_ledger_family_version",
                    location,
                    f"Ledger references unknown selection-family version {(family_id, ledger_family_version)!r}.",
                )

        for row in self.all_coverage:
            family_id = row.get("selection_family_id", "")
            family_version = str(row.get("selection_family_version", ""))
            location = row.get("__source__", "coverage")
            family = records_by_key.get((family_id, family_version))
            if family is None:
                self.error(
                    "unknown_coverage_family_version",
                    location,
                    f"Coverage references unknown selection-family version {(family_id, family_version)!r}.",
                )
                continue
            if (
                row.get("__file_version__") == self.active_version
                and current_by_id.get(family_id) is not family
            ):
                self.error(
                    "active_coverage_family_version_mismatch",
                    location,
                    "Active coverage must reference the uniquely current selection-family version.",
                )
            if row.get("coverage_cell_id") not in self._family_cells(family):
                self.error("family_cell_backreference_missing", location, "Selection family omits this coverage cell.")

        for entry in self.ledger:
            if not _bool(entry.get("decision_influence")):
                continue
            family_id = str(entry.get("selection_family_id", ""))
            family_version = str(entry.get("selection_family_version", ""))
            if (family_id, family_version) not in records_by_key:
                self.error(
                    "unknown_selection_family",
                    entry.get("__source__", "ledger"),
                    f"Ledger references missing family version {(family_id, family_version)!r}.",
                )

    def _extract_comparison_groups(self) -> list[dict[str, Any]]:
        raw = _first(
            self.decision_contract,
            "comparison_groups",
            "comparable_sets",
            "selection_family_comparison_groups",
            default=[],
        )
        if isinstance(raw, dict):
            groups = []
            for key, item in raw.items():
                if isinstance(item, dict):
                    group = dict(item)
                    group.setdefault("comparison_group_id", key)
                else:
                    group = {"comparison_group_id": key, "selection_family_ids": _list(item)}
                groups.append(group)
            return groups
        return [dict(item) for item in _list(raw) if isinstance(item, dict)]

    def _contract_selection_family_policy(
        self,
    ) -> tuple[set[str], set[str], dict[str, set[str]]]:
        """Return eligible families, explicitly declared families, and their keys."""

        eligible = set(
            _ids(
                _first(
                    self.decision_contract,
                    "eligible_selection_family_ids",
                    "eligible_selection_families",
                    "selection_family_ids",
                    default=[],
                )
            )
        )
        declared = set(eligible)
        keys_by_family: dict[str, set[str]] = defaultdict(set)

        for field in (
            "declared_selection_family_ids",
            "defined_selection_family_ids",
            "parallel_selection_family_ids",
            "support_limited_selection_family_ids",
            "excluded_selection_family_ids",
        ):
            declared.update(_ids(self.decision_contract.get(field)))

        raw_key_map = _first(
            self.decision_contract,
            "selection_family_comparison_keys",
            "family_comparison_keys",
            default={},
        )
        if isinstance(raw_key_map, dict):
            for family_id, key in raw_key_map.items():
                normalized_id = str(family_id).strip()
                if not normalized_id:
                    continue
                declared.add(normalized_id)
                normalized_key = _comparison_key_value(key)
                if normalized_key:
                    keys_by_family[normalized_id].add(normalized_key)

        raw_definitions = _first(
            self.decision_contract,
            "selection_family_definitions",
            "family_definitions",
            default=[],
        )
        definitions: list[dict[str, Any]] = []
        if isinstance(raw_definitions, dict):
            for family_id, item in raw_definitions.items():
                if isinstance(item, dict):
                    definition = dict(item)
                else:
                    definition = {"comparison_key": item}
                definition.setdefault("selection_family_id", family_id)
                definitions.append(definition)
        else:
            definitions = [
                dict(item) for item in _list(raw_definitions) if isinstance(item, dict)
            ]
        for definition in definitions:
            family_id = str(
                _first(definition, "selection_family_id", "family_id", default="")
            ).strip()
            if not family_id:
                continue
            declared.add(family_id)
            key = _comparison_key_value(
                _first(definition, "comparison_key", "comparability_key")
            )
            if key:
                keys_by_family[family_id].add(key)

        for group in self._extract_comparison_groups():
            member_ids = _ids(
                _first(group, "selection_family_ids", "family_ids", "members")
            )
            group_key = _comparison_key_value(
                _first(group, "comparison_key", "comparability_key")
            )
            for family_id in member_ids:
                declared.add(family_id)
                if group_key:
                    keys_by_family[family_id].add(group_key)

        return eligible, declared, dict(keys_by_family)

    def _validate_decision_contract(self) -> None:
        location = "decision_contract.json"
        self._require_one(self.decision_contract, location, "decision-contract version", ("decision_contract_version", "contract_version"))
        self._require_one(self.decision_contract, location, "decision identifier", ("decision_id", "decision_contract_id"))
        self._require_one(self.decision_contract, location, "decision question", ("decision_question", "decision"))
        self._require_one(self.decision_contract, location, "eligible candidate classes", ("eligible_candidate_classes", "candidate_classes"))
        self._require_one(self.decision_contract, location, "ranking evidence", ("ranking_evidence", "evidence_ranking_rule", "ranking_rule"))
        self._require_one(
            self.decision_contract,
            location,
            "decision rule",
            ("decision_rule", "selection_rule"),
        )
        self._require_one(self.decision_contract, location, "estimand", ("estimand", "decision_estimand"))
        self._require_one(
            self.decision_contract,
            location,
            "minimum meaningful difference",
            ("minimum_meaningful_difference", "minimum_meaningful_effect"),
        )
        self._require_one(
            self.decision_contract,
            location,
            "complexity and data-quality rule",
            ("complexity_and_data_quality_rule", "quality_and_complexity_rule"),
        )
        self._require_one(self.decision_contract, location, "tie rule", ("tie_rule", "equivalence_rule"))
        self._require_one(self.decision_contract, location, "inconclusive rule", ("inconclusive_rule", "no_decision_rule"))
        self._require_one(
            self.decision_contract,
            location,
            "comparison-key definition",
            ("comparison_key_definition", "comparability_rule", "selection_family_policy"),
        )
        self._require_one(
            self.decision_contract,
            location,
            "comparability rule",
            ("comparability_rule", "selection_family_policy"),
        )
        self._require_one(
            self.decision_contract,
            location,
            "complete-selection-path method",
            ("complete_selection_path_method", "selection_path_method"),
        )
        decision_timing = self._require_one(
            self.decision_contract,
            location,
            "specification timing",
            ("specification_timing",),
        )
        self._status(decision_timing, SPECIFICATION_TIMINGS, location, "specification_timing")
        self._require_one(self.decision_contract, location, "freeze time", ("frozen_at", "freeze_time"))
        self._require_one(self.decision_contract, location, "amendment policy", ("amendment_policy", "contract_amendment_policy"))

        if self.strict_schema:
            self._required(
                self.decision_contract, location, STRICT_DECISION_CONTRACT_FIELDS
            )
            scale_mapping = self.decision_contract.get("evidence_scale_mapping")
            if not _blank(scale_mapping):
                if isinstance(scale_mapping, Mapping):
                    scale_mappings = [scale_mapping]
                elif isinstance(scale_mapping, list) and scale_mapping:
                    scale_mappings = scale_mapping
                else:
                    scale_mappings = []
                    self.error(
                        "invalid_evidence_scale_mapping",
                        location,
                        "evidence_scale_mapping must be one object or a nonempty list of objects.",
                    )
                for index, mapping in enumerate(scale_mappings, start=1):
                    mapping_location = (
                        f"{location}#evidence_scale_mapping[{index}]"
                        if isinstance(scale_mapping, list)
                        else f"{location}#evidence_scale_mapping"
                    )
                    if not isinstance(mapping, Mapping):
                        self.error(
                            "invalid_evidence_scale_mapping",
                            mapping_location,
                            "Each evidence-scale mapping must be an object.",
                        )
                        continue
                    scale_relation = str(
                        mapping.get("scale_relation", "")
                    ).strip()
                    required_scale_fields = (
                        {"scale_relation", "reason"}
                        if scale_relation == "not_applicable"
                        else EVIDENCE_SCALE_MAPPING_FIELDS
                    )
                    missing_scale_fields = sorted(
                        field
                        for field in required_scale_fields
                        if _blank(mapping.get(field))
                    )
                    if missing_scale_fields:
                        self.error(
                            "incomplete_evidence_scale_mapping",
                            mapping_location,
                            f"Evidence-scale mapping has blank or missing fields {missing_scale_fields}.",
                        )
                    if (
                        not _blank(scale_relation)
                        and scale_relation not in EVIDENCE_SCALE_RELATIONS
                    ):
                        self.error(
                            "invalid_evidence_scale_relation",
                            mapping_location,
                            f"scale_relation={scale_relation!r} is not one of {sorted(EVIDENCE_SCALE_RELATIONS)}.",
                        )
                if isinstance(scale_mapping, list) and len(scale_mapping) > 1:
                    eligible_families, declared_families, _ = (
                        self._contract_selection_family_policy()
                    )
                    mapping_ids: set[str] = set()
                    mapped_families: set[str] = set()
                    mapping_scopes_by_family: dict[
                        str, list[tuple[str, str]]
                    ] = defaultdict(list)
                    active_scopes_by_family_and_statistic: dict[
                        tuple[str, str], list[str]
                    ] = defaultdict(list)
                    for index, mapping in enumerate(scale_mappings, start=1):
                        if not isinstance(mapping, Mapping):
                            continue
                        mapping_location = (
                            f"{location}#evidence_scale_mapping[{index}]"
                        )
                        mapping_id = str(mapping.get("mapping_id", "")).strip()
                        family_ids = set(_ids(mapping.get("selection_family_ids")))
                        if _blank(mapping_id) or not family_ids:
                            self.error(
                                "incomplete_evidence_scale_mapping_scope",
                                mapping_location,
                                "Multiple mappings require a nonempty mapping_id and selection_family_ids.",
                            )
                        elif mapping_id in mapping_ids:
                            self.error(
                                "duplicate_evidence_scale_mapping_id",
                                mapping_location,
                                f"mapping_id {mapping_id!r} is duplicated.",
                            )
                        else:
                            mapping_ids.add(mapping_id)
                        scope_label = mapping_id or f"mapping[{index}]"
                        scale_relation = str(
                            mapping.get("scale_relation", "")
                        ).strip()
                        normalized_statistic = _normalized_screening_statistic(
                            mapping.get("screening_statistic")
                        )
                        for family_id in family_ids:
                            mapping_scopes_by_family[family_id].append(
                                (scope_label, scale_relation)
                            )
                            if (
                                scale_relation != "not_applicable"
                                and normalized_statistic
                            ):
                                active_scopes_by_family_and_statistic[
                                    (family_id, normalized_statistic)
                                ].append(scope_label)
                        unknown_families = family_ids - declared_families
                        if unknown_families:
                            self.error(
                                "unknown_evidence_scale_mapping_family",
                                mapping_location,
                                f"Mapping references undeclared selection families {sorted(unknown_families)}.",
                            )
                        mapped_families.update(family_ids & eligible_families)
                    for (
                        family_id,
                        normalized_statistic,
                    ), scope_labels in active_scopes_by_family_and_statistic.items():
                        if len(scope_labels) > 1:
                            self.error(
                                "ambiguous_evidence_scale_mapping_scope",
                                location,
                                "Selection family "
                                f"{family_id!r} has multiple mappings for normalized "
                                f"screening_statistic={normalized_statistic!r}: "
                                f"{scope_labels}.",
                            )
                    for family_id, scopes in mapping_scopes_by_family.items():
                        if len(scopes) > 1 and any(
                            relation == "not_applicable" for _, relation in scopes
                        ):
                            self.error(
                                "ambiguous_evidence_scale_mapping_scope",
                                location,
                                "Selection family "
                                f"{family_id!r} has a not_applicable mapping together "
                                f"with another mapping: {[label for label, _ in scopes]}.",
                            )
                    unmapped_families = eligible_families - mapped_families
                    if unmapped_families:
                        self.error(
                            "unmapped_eligible_selection_family",
                            location,
                            f"Eligible selection families lack an evidence-scale mapping: {sorted(unmapped_families)}.",
                        )
                elif scale_mappings and isinstance(scale_mappings[0], Mapping):
                    mapping = scale_mappings[0]
                    if "selection_family_ids" in mapping:
                        eligible_families, declared_families, _ = (
                            self._contract_selection_family_policy()
                        )
                        family_ids = set(_ids(mapping.get("selection_family_ids")))
                        mapping_location = (
                            f"{location}#evidence_scale_mapping[1]"
                            if isinstance(scale_mapping, list)
                            else f"{location}#evidence_scale_mapping"
                        )
                        unknown_families = family_ids - declared_families
                        if unknown_families:
                            self.error(
                                "unknown_evidence_scale_mapping_family",
                                mapping_location,
                                f"Mapping references undeclared selection families {sorted(unknown_families)}.",
                            )
                        unmapped_families = eligible_families - (
                            family_ids & eligible_families
                        )
                        if unmapped_families:
                            self.error(
                                "unmapped_eligible_selection_family",
                                location,
                                f"Eligible selection families lack an evidence-scale mapping: {sorted(unmapped_families)}.",
                            )
            requirement = self._status(
                self.decision_contract.get("transportability_requirement"),
                TRANSPORTABILITY_REQUIREMENTS,
                location,
                "transportability_requirement",
            )
            transport_status = self._status(
                self.decision_contract.get("transportability_status"),
                TRANSPORTABILITY_STATUSES,
                location,
                "transportability_status",
            )
            populations = {
                _comparison_key_value(self.decision_contract.get(field))
                for field in (
                    "target_population",
                    "analysis_population",
                    "selection_population",
                    "reporting_population",
                )
            }
            if requirement == "same_population":
                if len(populations) != 1:
                    self.error(
                        "same_population_mismatch",
                        location,
                        "same_population requires identical target, analysis, selection, and reporting populations.",
                    )
                if transport_status != "not_required":
                    self.error(
                        "invalid_transportability_status",
                        location,
                        "same_population requires transportability_status=not_required.",
                    )
            if requirement == "validation_required" and transport_status == "not_required":
                self.error(
                    "invalid_transportability_status",
                    location,
                    "validation_required cannot use transportability_status=not_required.",
                )
            if requirement == "parallel_only" and transport_status != "not_required":
                self.error(
                    "invalid_transportability_status",
                    location,
                    "parallel_only requires transportability_status=not_required.",
                )
            run_decision = str(self.manifest.get("decision_status", "")).strip()
            if (
                requirement == "validation_required"
                and run_decision in {"leading", "tie"}
                and transport_status != "passed"
            ):
                self.error(
                    "transport_validation_not_passed",
                    location,
                    "A terminal leading or tie decision requires passed transport validation.",
                )
            if requirement == "parallel_only" and run_decision in {"leading", "tie"}:
                self.error(
                    "parallel_only_terminal_decision",
                    location,
                    "parallel_only cannot yield a terminal leading or tie decision.",
                )

        manifest_version = _first(self.manifest, "decision_contract_version", "decision_contract_id")
        contract_version = _first(self.decision_contract, "decision_contract_version", "contract_version", "decision_contract_id")
        if not _blank(manifest_version) and not _blank(contract_version) and str(manifest_version) != str(contract_version):
            self.error("decision_contract_version_mismatch", location, "Decision-contract version differs from the run manifest.")

        ranking = _json_text(_first(self.decision_contract, "ranking_evidence", "evidence_ranking_rule", "ranking_rule"))
        if re.search(r"\b(smallest|minimum|minimize|minimised|minimized|lowest)\b.{0,20}\bp[- _-]?value", ranking):
            self.error("minimum_p_value_rule", location, "Decision ranking cannot define the smallest p-value as the best candidate.")

        current_families_by_id = {
            self._family_id(family): family for family in self.families
        }
        eligible_ids = _ids(
            _first(
                self.decision_contract,
                "eligible_selection_family_ids",
                "eligible_selection_families",
                "selection_family_ids",
            )
        )
        if current_families_by_id and not eligible_ids:
            self.error("missing_eligible_families", location, "Decision contract must name eligible selection families.")
        for family_id in eligible_ids:
            if family_id not in current_families_by_id:
                self.error("unknown_decision_family", location, f"Eligible selection family {family_id!r} does not exist.")

        groups = self._extract_comparison_groups()
        grouped: set[str] = set()
        for index, group in enumerate(groups, start=1):
            group_location = f"{location}#comparison_group[{index}]"
            member_ids = _ids(_first(group, "selection_family_ids", "family_ids", "members"))
            if not member_ids:
                self.error("empty_comparison_group", group_location, "Comparison group must name at least one family.")
                continue
            grouped.update(member_ids)
            member_families = []
            for family_id in member_ids:
                family = current_families_by_id.get(family_id)
                if family is None:
                    self.error("unknown_decision_family", group_location, f"Comparison group references missing family {family_id!r}.")
                    continue
                member_families.append(family)
                status = str(_first(family, "comparison_status", "comparability_status", default=""))
                if len(member_ids) > 1 and status in {
                    "parallel_conclusion",
                    "support_limited_candidate",
                    "not_eligible_for_decision",
                }:
                    self.error("incomparable_family_ranked", group_location, f"Family {family_id!r} cannot be directly ranked in this group.")
            if len(member_families) > 1:
                keys = {self._comparison_key(family) for family in member_families}
                if "" in keys:
                    self.error("missing_comparison_key", group_location, "Every directly compared family requires a comparison key.")
                if len(keys - {""}) > 1 and _blank(_first(group, "standardization_rule", "transport_rule", "harmonization_rule")):
                    self.error("incompatible_comparison_keys", group_location, "Families with different comparison keys require a prespecified valid harmonization rule or separate conclusions.")

        directly_ranked = set(
            _ids(
                _first(
                    self.decision_contract,
                    "ranked_selection_family_ids",
                    "directly_compared_selection_family_ids",
                    default=[],
                )
            )
        )
        if directly_ranked and not directly_ranked.issubset(grouped):
            self.error("ranked_family_without_group", location, f"Directly ranked families lack a comparison group: {sorted(directly_ranked - grouped)}.")
        comparable_eligible = [
            family_id
            for family_id in eligible_ids
            if family_id in current_families_by_id
            and str(
                _first(
                    current_families_by_id[family_id],
                    "comparison_status",
                    "comparability_status",
                    default="",
                )
            )
            == "comparable_within_family"
        ]
        if len(comparable_eligible) > 1 and not groups:
            self.error(
                "missing_comparison_groups",
                location,
                "Directly comparable eligible families require explicit comparison groups; parallel or support-limited families do not.",
            )

    def _validate_prior_exposure(self) -> None:
        location = "prior_exposure_audit.json"
        self._require_one(self.prior_exposure, location, "prior-exposure-audit version", ("prior_exposure_audit_version", "audit_version"))
        audit_status = str(self.prior_exposure.get("audit_status", "")).strip()
        accepted_audit_statuses = {
            "complete",
            "incomplete",
            "unknown",
            "not_applicable",
        }
        if audit_status not in accepted_audit_statuses:
            self.error("invalid_prior_exposure_status", location, f"audit_status must be one of {sorted(accepted_audit_statuses)}.")
        self.prior_audit_status = audit_status
        explicit_prior_status = str(
            self._require_one(
                self.prior_exposure,
                location,
                "prior-exposure finding",
                ("prior_exposure_status",),
            )
            or ""
        ).strip()
        if explicit_prior_status:
            self._status(
                explicit_prior_status,
                PRIOR_EXPOSURE_STATUSES,
                location,
                "prior_exposure_status",
            )
        confirmatory_status = str(
            self._require_one(
                self.prior_exposure,
                location,
                "current-evidence status",
                ("confirmatory_status", "current_evidence_status", "evidence_eligibility"),
            )
            or ""
        ).strip()
        if confirmatory_status and confirmatory_status not in CONFIRMATORY_STATUSES:
            self.error("invalid_confirmatory_status", location, f"confirmatory_status must be one of {sorted(CONFIRMATORY_STATUSES)}.")
        future_status = str(
            self._require_one(
                self.prior_exposure,
                location,
                "future-verification status",
                ("future_verification_status", "prospective_verification_status"),
            )
            or ""
        ).strip()
        if future_status and future_status not in FUTURE_VERIFICATION_STATUSES:
            self.error(
                "invalid_future_verification_status",
                location,
                f"future_verification_status must be one of {sorted(FUTURE_VERIFICATION_STATUSES)}.",
            )

        manifest_version = _first(self.manifest, "prior_exposure_audit_version", "prior_exposure_audit_id")
        audit_version = _first(self.prior_exposure, "prior_exposure_audit_version", "audit_version")
        if not _blank(manifest_version) and not _blank(audit_version) and str(manifest_version) != str(audit_version):
            self.error("prior_exposure_version_mismatch", location, "Prior-exposure-audit version differs from the run manifest.")

        required_records = {
            "prior_analyses": ("prior_analyses", "analysis_history"),
            "parameter_attempts": ("prior_parameter_attempts", "parameter_attempts"),
            "result_views": ("prior_data_looks", "result_views", "prior_result_views", "data_looks"),
            "overlapping_data": ("overlapping_data_products", "overlapping_data", "data_overlap"),
        }
        values: dict[str, Any] = {}
        for concept, keys in required_records.items():
            value = _first(self.prior_exposure, *keys)
            if value is None:
                self.error("missing_prior_exposure_record", location, f"Prior-exposure audit must explicitly record {concept}, even when empty.")
            values[concept] = value

        for concept, keys in {
            "sources_checked": ("sources_checked",),
            "overlap_unit": ("overlap_unit",),
            "prior_holdout_exposure": ("prior_holdout_exposure", "holdout_exposure"),
            "unknown_gaps": ("unknown_gaps", "uncertain_gaps"),
            "resulting_evidence_stage_limits": ("resulting_evidence_stage_limits", "evidence_stage_limits"),
            "audited_at": ("audited_at", "audit_time"),
        }.items():
            if not any(key in self.prior_exposure for key in keys):
                self.error("missing_prior_exposure_record", location, f"Prior-exposure audit must explicitly record {concept}, even when empty.")

        has_exposure = any(bool(_list(values[name])) for name in ("prior_analyses", "parameter_attempts", "result_views"))
        overlap_value = values["overlapping_data"]
        overlap_bool = _bool(overlap_value)
        has_overlap = overlap_bool is True or (overlap_bool is None and bool(_list(overlap_value)))
        prior_status = explicit_prior_status or "not_assessed"
        self.prior_exposure_status = prior_status
        if prior_status == "no_known_exposure" and (has_exposure or has_overlap):
            self.error("prior_exposure_status_mismatch", location, "no_known_exposure conflicts with recorded overlap or prior outcome exposure.")
        if prior_status in {"unknown", "not_assessed", "not_applicable"} and audit_status == "complete":
            self.error("prior_exposure_status_mismatch", location, "audit_status=complete requires a resolved no-known-exposure or known-overlap finding.")
        if audit_status == "unknown":
            if prior_status != "unknown":
                self.error(
                    "prior_exposure_status_mismatch",
                    location,
                    "audit_status=unknown requires prior_exposure_status=unknown.",
                )
            if not _list(_first(self.prior_exposure, "unknown_gaps", "uncertain_gaps")):
                self.error(
                    "unjustified_unknown_exposure",
                    location,
                    "audit_status=unknown requires explicit unresolved exposure gaps.",
                )
        if audit_status == "not_applicable":
            if prior_status != "not_applicable":
                self.error(
                    "prior_exposure_status_mismatch",
                    location,
                    "audit_status=not_applicable requires prior_exposure_status=not_applicable.",
                )
            if confirmatory_status != "not_applicable":
                self.error(
                    "invalid_confirmatory_status",
                    location,
                    "A not-applicable exposure audit requires confirmatory_status=not_applicable.",
                )
            if _blank(
                _first(
                    self.prior_exposure,
                    "not_applicable_reason",
                    "applicability_reason",
                )
            ):
                self.error(
                    "missing_prior_exposure_record",
                    location,
                    "audit_status=not_applicable requires a reason.",
                )
        if (has_exposure or has_overlap or prior_status in {"known_overlap", "unknown", "not_assessed", "not_applicable"}) and confirmatory_status in {
            "unrestricted_by_prior_exposure",
        }:
            self.error("confirmatory_status_not_restored", location, "Prior looks, overlap, or unknown exposure prevent confirmatory status on the exposed evidence.")

        restoration = _first(
            self.prior_exposure,
            "sample_code_or_skill_change_restores_confirmatory",
            "version_change_restores_confirmatory",
            "confirmatory_status_restored",
        )
        if _bool(restoration) is True:
            self.error("invalid_confirmatory_restoration", location, "Changing sample, code, workflow, or skill version cannot restore confirmatory status.")
        text = _json_text(self.prior_exposure)
        if "restore" in text and "confirmatory" in text and any(term in text for term in ("code version", "skill version", "sample change", "workflow version")):
            self.warn("review_confirmatory_restoration_text", location, "Audit text mentions restoring confirmatory status through a version or sample change; review manually.")

    def _validate_candidate_registry(self) -> None:
        path = self.run_dir / "candidate_registry.csv"
        location = self.rel(path)
        if not path.is_file():
            return
        required_candidate_fields = set(CANDIDATE_REQUIRED_FIELDS)
        if self.profile_schema:
            required_candidate_fields |= V15_COVERAGE_CANDIDATE_FIELDS
            if self.generic_inventory_schema:
                required_candidate_fields.discard("mechanism_id")
        missing_headers = required_candidate_fields - self.csv_headers.get(location, set())
        if missing_headers:
            self.error(
                "missing_candidate_columns",
                location,
                f"Candidate-registry header is missing required columns {sorted(missing_headers)}.",
            )

        mechanisms = {
            (row.get("__file_version__", ""), row.get("mechanism_id", ""))
            for row in self.all_inventory
        }
        inventory_by_key = {
            (row.get("__file_version__", ""), row.get("mechanism_id", "")): row
            for row in self.all_inventory
        }
        coverage_cells = {
            (row.get("__file_version__", ""), row.get("coverage_cell_id", "")): row
            for row in self.all_coverage
        }
        current_families_by_id = {
            self._family_id(family): family for family in self.families
        }
        families_by_key = {
            (
                self._family_id(family),
                str(
                    _first(
                        family,
                        "selection_family_version",
                        "family_version",
                        default="",
                    )
                ).strip(),
            ): family
            for family in self.all_family_records
        }
        ledger_by_id = {
            str(entry.get("ledger_entry_id", "")): entry for entry in self.ledger
        }
        eligible_family_ids, declared_family_ids, contract_keys_by_family = (
            self._contract_selection_family_policy()
        )
        seen: set[str] = set()

        for index, row in enumerate(self.candidate_registry, start=1):
            row_location = row.get("__source__", f"{location}:{index + 1}")
            self._required(row, row_location, required_candidate_fields)
            candidate_id = row.get("candidate_id", "")
            if candidate_id in seen:
                self.error(
                    "duplicate_candidate_id",
                    row_location,
                    f"candidate_id {candidate_id!r} is duplicated.",
                )
            seen.add(candidate_id)
            version = _version(row.get("inventory_version"))
            mechanism_id = (
                row.get("candidate_id", "")
                if self.generic_inventory_schema
                else row.get("mechanism_id", "")
            )
            candidate_type = (
                self._status(
                    row.get("candidate_type"),
                    CANDIDATE_TYPES,
                    row_location,
                    "candidate_type",
                )
                if self.profile_schema
                else "mechanism"
            )
            substantive_eligibility = (
                self._status(
                    row.get("substantive_eligibility"),
                    SUBSTANTIVE_ELIGIBILITY_STATUSES,
                    row_location,
                    "substantive_eligibility",
                )
                if self.profile_schema
                else "eligible"
            )
            family_id = row.get("selection_family_id", "")
            family_version = str(row.get("selection_family_version", "")).strip()
            family = families_by_key.get((family_id, family_version))
            active_candidate = version == self.active_version
            if (version, mechanism_id) not in mechanisms:
                self.error(
                    "unknown_candidate_inventory_id"
                    if self.generic_inventory_schema
                    else "unknown_candidate_mechanism",
                    row_location,
                    f"{'candidate_id' if self.generic_inventory_schema else 'mechanism_id'} {mechanism_id!r} is absent from inventory version {version!r}.",
                )
            elif self.generic_inventory_schema:
                inventory_type = str(
                    inventory_by_key[(version, mechanism_id)].get(
                        "candidate_type", ""
                    )
                ).strip()
                if candidate_type and inventory_type != candidate_type:
                    self.error(
                        "candidate_type_mismatch",
                        row_location,
                        f"Registry candidate_type={candidate_type!r} differs from inventory candidate_type={inventory_type!r}.",
                    )
            candidate_cell_ids = _ids(row.get("coverage_cell_ids"))
            candidate_coverage_rows: list[dict[str, str]] = []
            for cell_id in candidate_cell_ids:
                coverage_row = coverage_cells.get((version, cell_id))
                if coverage_row is None:
                    self.error(
                        "unknown_candidate_coverage_cell",
                        row_location,
                        f"coverage cell {cell_id!r} is absent from inventory version {version!r}.",
                    )
                    continue
                candidate_coverage_rows.append(coverage_row)
                if coverage_row.get("selection_family_id") != family_id:
                    self.error(
                        "candidate_coverage_family_mismatch",
                        row_location,
                        f"Coverage cell {cell_id!r} belongs to family {coverage_row.get('selection_family_id')!r}, not candidate family {family_id!r}.",
                    )
                if str(coverage_row.get("selection_family_version", "")) != family_version:
                    self.error(
                        "candidate_coverage_family_version_mismatch",
                        row_location,
                        f"Coverage cell {cell_id!r} references family version {coverage_row.get('selection_family_version')!r}, not candidate family version {family_version!r}.",
                    )
                if coverage_row.get("mechanism_id") != mechanism_id:
                    self.error(
                        "candidate_coverage_inventory_mismatch"
                        if self.generic_inventory_schema
                        else "candidate_coverage_mechanism_mismatch",
                        row_location,
                        f"Coverage cell {cell_id!r} belongs to {'candidate' if self.generic_inventory_schema else 'mechanism'} {coverage_row.get('mechanism_id')!r}, not registry candidate {mechanism_id!r}.",
                    )
                if family is not None and cell_id not in set(self._family_cells(family)):
                    self.error(
                        "candidate_coverage_not_in_family",
                        row_location,
                        f"Candidate coverage cell {cell_id!r} is absent from family {family_id!r}.",
                    )
            if family is None:
                self.error(
                    "unknown_candidate_family_version",
                    row_location,
                    f"Candidate references missing selection-family version {(family_id, family_version)!r}.",
                )
            elif (
                active_candidate
                and current_families_by_id.get(family_id) is not family
            ):
                self.error(
                    "active_candidate_family_version_mismatch",
                    row_location,
                    "Active candidate must reference the uniquely current selection-family version.",
                )
            if active_candidate and family_id not in declared_family_ids:
                self.error(
                    "candidate_family_not_declared_in_contract",
                    row_location,
                    f"Candidate family {family_id!r} is not explicitly declared by the current Decision Contract.",
                )

            candidate_ledger_ids = _ids(row.get("ledger_entry_ids"))
            for ledger_id in candidate_ledger_ids:
                ledger_entry = ledger_by_id.get(ledger_id)
                if ledger_entry is None:
                    self.error(
                        "unknown_candidate_ledger_entry",
                        row_location,
                        f"Candidate references missing ledger entry {ledger_id!r}.",
                    )
                    continue
                ledger_family_id = str(ledger_entry.get("selection_family_id", ""))
                if ledger_family_id != family_id:
                    self.error(
                        "candidate_ledger_family_mismatch",
                        row_location,
                        f"Ledger entry {ledger_id!r} belongs to family {ledger_family_id!r}, not candidate family {family_id!r}.",
                    )
                if family is not None and ledger_id not in set(
                    self._family_ledger_ids(family)
                ):
                    self.error(
                        "candidate_ledger_not_in_family",
                        row_location,
                        f"Candidate ledger entry {ledger_id!r} is absent from family {family_id!r}'s declared selection path.",
                    )

            comparability = self._status(
                row.get("comparability_status"),
                COMPARISON_STATUSES,
                row_location,
                "comparability_status",
            )
            decision = self._status(
                row.get("decision_status"),
                DECISION_STATUSES,
                row_location,
                "decision_status",
            )
            self._status(
                row.get("specification_timing"),
                SPECIFICATION_TIMINGS,
                row_location,
                "specification_timing",
            )
            prior_status = self._status(
                row.get("prior_exposure_status"),
                PRIOR_EXPOSURE_STATUSES,
                row_location,
                "prior_exposure_status",
            )
            self._status(
                row.get("evidence_stage"),
                EVIDENCE_STAGES,
                row_location,
                "evidence_stage",
            )
            self._status(
                row.get("verification_status"),
                VERIFICATION_STATUSES,
                row_location,
                "verification_status",
            )
            confirmatory = self._status(
                row.get("confirmatory_status"),
                CONFIRMATORY_STATUSES,
                row_location,
                "confirmatory_status",
            )
            self._status(
                row.get("future_verification_status"),
                FUTURE_VERIFICATION_STATUSES,
                row_location,
                "future_verification_status",
            )
            if (
                active_candidate
                and decision in PROMOTED_DECISION_STATUSES
                and family_id not in eligible_family_ids
            ):
                self.error(
                    "candidate_family_not_eligible_for_decision",
                    row_location,
                    f"Candidate decision_status={decision!r} requires family {family_id!r} in eligible_selection_family_ids.",
                )
            if self.strict_schema and decision in PROMOTED_DECISION_STATUSES:
                if self.profile_schema and substantive_eligibility != "eligible":
                    self.error(
                        "candidate_substantive_eligibility_gate_failed",
                        row_location,
                        f"Promoted candidate requires substantive_eligibility='eligible', not {substantive_eligibility!r}.",
                    )
                inventory_row = inventory_by_key.get((version, mechanism_id))
                data_support = (
                    str(inventory_row.get("data_support_status", "")).strip()
                    if inventory_row is not None
                    else ""
                )
                if data_support not in DECISION_ELIGIBLE_DATA_SUPPORT_STATUSES:
                    self.error(
                        "candidate_data_support_gate_failed",
                        row_location,
                        f"Candidate cannot be promoted with data_support_status={data_support!r}; direct decision eligibility requires 'supported'.",
                    )
                for coverage_row in candidate_coverage_rows:
                    cell_id = coverage_row.get("coverage_cell_id", "")
                    alignment = (
                        coverage_row.get("mechanism_alignment", "")
                        if candidate_type == "mechanism"
                        else coverage_row.get("substantive_eligibility", "")
                    )
                    promotable_alignments = (
                        {"direct", "calibrated_proxy"}
                        if self.profile_schema and candidate_type == "mechanism"
                        else {"eligible"}
                        if self.profile_schema
                        else PROMOTABLE_MECHANISM_ALIGNMENTS
                    )
                    if alignment not in promotable_alignments:
                        self.error(
                            "candidate_mechanism_alignment_gate_failed"
                            if candidate_type == "mechanism"
                            else "candidate_substantive_alignment_gate_failed",
                            row_location,
                            f"Candidate cannot be promoted from coverage cell {cell_id!r} with applicable alignment={alignment!r}.",
                        )
                    sensitivity = coverage_row.get(
                        "measurement_error_sensitivity", ""
                    )
                    if sensitivity not in PROMOTABLE_MEASUREMENT_ERROR_SENSITIVITIES:
                        self.error(
                            "candidate_measurement_error_gate_failed",
                            row_location,
                            f"Candidate cannot be promoted from coverage cell {cell_id!r} with measurement_error_sensitivity={sensitivity!r}.",
                        )
                if active_candidate:
                    transport_passed, reason = self._family_transport_gate(family)
                    if not transport_passed:
                        self.error(
                            "candidate_family_transport_gate_failed",
                            row_location,
                            f"Candidate cannot be promoted because its family transport gate failed: {reason}.",
                        )

            candidate_key = _comparison_key_value(row.get("comparison_key"))
            family_key = self._comparison_key(family) if family is not None else ""
            if candidate_key and family_key and candidate_key != family_key:
                self.error(
                    "candidate_family_comparison_key_mismatch",
                    row_location,
                    "Candidate comparison_key does not match its selection-family comparison_key.",
                )
            contract_keys = contract_keys_by_family.get(family_id, set())
            if active_candidate and family_id in declared_family_ids and not contract_keys:
                self.error(
                    "candidate_contract_comparison_key_missing",
                    row_location,
                    f"Decision Contract does not declare a comparison key for candidate family {family_id!r}.",
                )
            elif (
                active_candidate
                and candidate_key
                and contract_keys
                and candidate_key not in contract_keys
            ):
                self.error(
                    "candidate_contract_comparison_key_mismatch",
                    row_location,
                    "Candidate comparison_key does not match the key declared for its family by the Decision Contract.",
                )
            if prior_status in {"known_overlap", "unknown", "not_assessed"} and confirmatory in {
                "unrestricted_by_prior_exposure",
            }:
                self.error(
                    "candidate_prior_exposure_conflict",
                    row_location,
                    "Candidate current-evidence status is incompatible with its prior exposure.",
                )
            if decision in {"leading", "tie"} and comparability not in {
                "comparable_within_family",
            }:
                self.error(
                    "incomparable_candidate_selected",
                    row_location,
                    "A leading or tied candidate must be comparable within its declared family.",
                )

        applied = _bool(self.manifest.get("decision_contract_applied"))
        run_decision = str(self.manifest.get("decision_status", ""))
        active_candidates = [
            row
            for row in self.candidate_registry
            if _version(row.get("inventory_version")) == self.active_version
        ]
        leading = [
            row for row in active_candidates if row.get("decision_status") == "leading"
        ]
        tied = [
            row for row in active_candidates if row.get("decision_status") == "tie"
        ]
        if applied is True and run_decision not in TERMINAL_RUN_DECISION_STATUSES:
            self.error(
                "decision_contract_application_mismatch",
                "run_manifest.json",
                "decision_contract_applied=true requires a terminal run decision status.",
            )
        if applied is False and run_decision in TERMINAL_RUN_DECISION_STATUSES:
            self.error(
                "decision_contract_application_mismatch",
                "run_manifest.json",
                "A terminal run decision requires decision_contract_applied=true.",
            )
        if applied is not True and (leading or tied):
            self.error(
                "candidate_decision_mismatch",
                location,
                "An unapplied Decision Contract cannot contain an active leading or tied candidate.",
            )
        if run_decision == "leading":
            if len(leading) != 1 or tied:
                self.error(
                    "candidate_decision_mismatch",
                    location,
                    "Run decision_status=leading requires exactly one active leading candidate and no tied candidate.",
                )
        elif run_decision == "tie":
            if len(tied) < 2 or leading:
                self.error(
                    "candidate_decision_mismatch",
                    location,
                    "Run decision_status=tie requires at least two active tied candidates and no leading candidate.",
                )
            elif tied:
                tied_family_ids = {
                    row.get("selection_family_id", "") for row in tied
                }
                declared_groups = [
                    set(
                        _ids(
                            _first(
                                group,
                                "selection_family_ids",
                                "family_ids",
                                "members",
                            )
                        )
                    )
                    for group in self._extract_comparison_groups()
                ]
                if not any(tied_family_ids.issubset(group) for group in declared_groups):
                    self.error(
                        "tie_candidates_not_in_common_comparison_group",
                        location,
                        "All tied candidates must belong to one comparison group declared by the Decision Contract.",
                    )
        elif leading or tied:
            self.error(
                "candidate_decision_mismatch",
                location,
                "A non-leading, non-tie run decision cannot contain an active winner.",
            )
        if run_decision == "no_eligible_candidate" and any(
            row.get("decision_status") in {"eligible", "leading", "tie"}
            for row in active_candidates
        ):
            self.error(
                "candidate_decision_mismatch",
                location,
                "no_eligible_candidate conflicts with active eligible candidates.",
            )

    def _validate_saturation(self) -> None:
        saturated = _bool(self.manifest.get("inventory_saturated")) is True
        if not self.saturation_audit:
            if saturated or self.manifest.get("search_status") == "complete_within_scope":
                self.error("missing_saturation_audit", "inventories/", "Saturated or complete run requires the active saturation-audit artifact.")
            else:
                self.warn("saturation_audit_not_yet_present", "inventories/", "No active saturation-audit artifact exists yet.")
            return
        location = "active saturation audit"
        audit_version = _first(self.saturation_audit, "inventory_version", "version")
        if _version(audit_version) != self.active_version:
            self.error("saturation_version_mismatch", location, "Saturation audit does not match the active inventory version.")
        audit_flag = _bool(_first(self.saturation_audit, "inventory_saturated", "saturated"))
        if audit_flag is not None and audit_flag != saturated:
            self.error("saturation_flag_mismatch", location, "Saturation-audit flag differs from the run manifest.")

        default_forward_source = (
            "candidate_forward" if self.generic_inventory_schema else "mechanism_forward"
        )
        required_sources = {
            _lens(item)
            for item in _ids(
                _first(
                    self.manifest,
                    "saturation_required_sources",
                    "required_saturation_audits",
                    default=[default_forward_source, "data_product_reverse"],
                )
            )
        }
        required_sources.update({default_forward_source, "data_product_reverse"})
        audits_raw = _first(self.saturation_audit, "audits", "audit_sources", "passes", default=[])
        audits: list[dict[str, Any]] = []
        if isinstance(audits_raw, dict):
            for key, item in audits_raw.items():
                record = dict(item) if isinstance(item, dict) else {"completed": item}
                record.setdefault("source", key)
                audits.append(record)
        else:
            audits.extend(dict(item) for item in _list(audits_raw) if isinstance(item, dict))
        for source in required_sources:
            top_level = self.saturation_audit.get(source)
            if isinstance(top_level, dict) and not any(_lens(_first(item, "source", "lens", "audit_type")) == source for item in audits):
                record = dict(top_level)
                record.setdefault("source", source)
                audits.append(record)

        by_source = {_lens(_first(item, "source", "lens", "audit_type")): item for item in audits}
        if saturated:
            for source in sorted(required_sources):
                record = by_source.get(source)
                if record is None:
                    self.error("missing_saturation_source", location, f"Required saturation source {source!r} is absent.")
                    continue
                completed = _bool(_first(record, "completed", "passed", "audit_complete"))
                if completed is not True:
                    self.error("incomplete_saturation_source", location, f"Saturation source {source!r} is not complete.")
                additions = _first(
                    record,
                    "new_eligible_candidates",
                    "new_eligible_mechanisms",
                    "eligible_additions",
                    "new_eligible_count",
                    default=[],
                )
                if isinstance(additions, int):
                    has_additions = additions > 0
                else:
                    has_additions = bool(_list(additions))
                if has_additions:
                    self.error("saturation_with_new_candidates", location, f"Saturation source {source!r} produced new eligible candidates.")

    def _load_transitions(self) -> list[dict[str, Any]]:
        transitions = self.load_jsonl(self.run_dir / "status_transitions.jsonl", required=False)
        for path in sorted((self.run_dir / "rounds").glob("*/inventory.json")):
            raw = self.load_json(path, required=False)
            if not isinstance(raw, dict):
                continue
            for index, item in enumerate(_list(raw.get("status_transitions")), start=1):
                if isinstance(item, dict):
                    record = dict(item)
                    record["__source__"] = f"{self.rel(path)}#status_transition[{index}]"
                    transitions.append(record)
        return transitions

    def _validate_transitions(self) -> None:
        transitions = self._load_transitions()
        self.counts["status_transitions"] = len(transitions)
        if not transitions:
            if self.manifest.get("search_status") == "complete_within_scope" and self.active_coverage:
                self.error("missing_status_transitions", "status_transitions.jsonl", "Complete run requires an auditable status-transition history.")
            else:
                self.warn("missing_status_transitions", "status_transitions.jsonl", "No machine-readable status-transition history was found.")
            return

        chains: dict[tuple[str, str, str, str], str] = {}
        final_states: dict[tuple[str, str, str, str], str] = {}
        final_transition_records: dict[
            tuple[str, str, str, str], Mapping[str, Any]
        ] = {}
        transition_ids: set[str] = set()
        for index, transition in enumerate(transitions, start=1):
            location = transition.get("__source__", f"transition {index}")
            transition_id = str(transition.get("transition_id", "")).strip()
            entity_type = str(_first(transition, "entity_type", "entity", default="")).strip()
            entity_id = str(_first(transition, "entity_id", "id", default="")).strip()
            field = str(_first(transition, "status_field", "field", default="")).strip()
            transition_version = _version(
                _first(transition, "inventory_version", "version", default="")
            )
            old = str(
                _first(
                    transition,
                    "previous_value",
                    "from_status",
                    "from",
                    "old_status",
                    default="",
                )
            ).strip()
            new = str(
                _first(
                    transition,
                    "new_value",
                    "to_status",
                    "to",
                    "new_status",
                    default="",
                )
            ).strip()
            reason = _first(transition, "evidence", "reason", "decision_reason")
            if not transition_id:
                self.error("transition_without_id", location, "Transition must have a nonempty transition_id.")
            elif transition_id in transition_ids:
                self.error("duplicate_transition_id", location, f"Duplicate transition_id {transition_id!r}.")
            else:
                transition_ids.add(transition_id)
            if not entity_type or not entity_id or not field or not new:
                self.error("incomplete_status_transition", location, "Transition requires entity_type, entity_id, status field, and new status.")
                continue
            if _blank(_first(transition, "inventory_version", "version")):
                self.error("transition_without_inventory_version", location, "Transition must pin inventory_version.")
            if _blank(_first(transition, "round_id", "round", "event_id")):
                self.error("transition_without_round", location, "Transition must pin round_id or event_id.")
            if _blank(_first(transition, "changed_at", "timestamp", "transition_time", "created_at")):
                self.error("transition_without_timestamp", location, "Transition must record a timestamp.")
            if _blank(reason):
                self.error("transition_without_evidence", location, "Transition must record evidence or a decision reason.")
            if not any(key in transition for key in ("evidence_paths", "artifact_paths", "evidence_artifacts")):
                self.error("transition_without_evidence_paths", location, "Transition must explicitly record evidence paths, even when the list is empty.")
            allowed = STATUS_VALUES.get(field)
            if field in STRICT_TRANSITION_STATUS_FIELDS and not self.strict_schema:
                allowed = None
            if allowed is None:
                self.warn("unknown_transition_field", location, f"No canonical status vocabulary is registered for {field!r}.")
            else:
                if old and old not in allowed:
                    self.error("invalid_transition_status", location, f"Old {field} value {old!r} is invalid.")
                if new not in allowed:
                    self.error("invalid_transition_status", location, f"New {field} value {new!r} is invalid.")
                transition_map = ALLOWED_STATUS_TRANSITIONS.get(field)
                if old and old in allowed and new in allowed and transition_map is not None:
                    if old == new:
                        self.error(
                            "no_op_status_transition",
                            location,
                            f"{field} transition must change state; both values are {old!r}.",
                        )
                    elif new not in transition_map.get(old, set()):
                        version_note = (
                            " This classification is frozen; record a changed value in a successor version."
                            if field in FROZEN_CLASSIFICATION_FIELDS
                            else ""
                        )
                        self.error(
                            "illegal_status_transition",
                            location,
                            f"Illegal {field} transition {old!r} -> {new!r}.{version_note}",
                        )
            key = (entity_type, entity_id, field, transition_version)
            if key in chains and old != chains[key]:
                self.error("broken_transition_chain", location, f"Transition starts at {old!r}, but previous state was {chains[key]!r}.")
            chains[key] = new
            final_states[key] = new
            final_transition_records[key] = transition

        run_id = str(self.manifest.get("run_id", ""))
        for key, final in final_states.items():
            entity_type, entity_id, field, transition_version = key
            current: str | None = None
            if (
                transition_version == self.active_version
                and entity_type in {"run", "search"}
                and entity_id == run_id
                and field in self.manifest
            ):
                current = str(self.manifest.get(field, ""))
            elif (
                transition_version == self.active_version
                and entity_type in {"inventory", "mechanism_inventory"}
                and _version(entity_id) == self.active_version
                and field in self.manifest
            ):
                current = str(self.manifest.get(field, ""))
            elif (
                self.generic_inventory_schema
                and transition_version == self.active_version
                and entity_type in {"candidate", "inventory_candidate"}
            ):
                inventory_row = next(
                    (
                        item
                        for item in self.active_inventory
                        if item.get("mechanism_id") == entity_id
                    ),
                    None,
                )
                normalized_field = (
                    "mechanism_status" if field == "candidate_status" else field
                )
                if inventory_row and normalized_field in inventory_row:
                    current = str(inventory_row.get(normalized_field, ""))
            elif transition_version == self.active_version and entity_type in {
                "coverage_cell",
                "cell",
                "coverage",
            }:
                row = next((item for item in self.active_coverage if item.get("coverage_cell_id") == entity_id), None)
                if row and field in row:
                    current = str(row.get(field, ""))
            elif transition_version == self.active_version and entity_type in {
                "selection_family",
                "selection-family",
                "family",
            }:
                transition = final_transition_records[key]
                requested_family_version = str(
                    _first(
                        transition,
                        "selection_family_version",
                        "family_version",
                        "entity_version",
                        default="",
                    )
                ).strip()
                family = next(
                    (
                        item
                        for item in self.families
                        if self._family_id(item) == entity_id
                        and (
                            not requested_family_version
                            or str(
                                _first(
                                    item,
                                    "selection_family_version",
                                    "family_version",
                                    default="",
                                )
                            ).strip()
                            == requested_family_version
                        )
                    ),
                    None,
                )
                if family and field in family:
                    current = str(family.get(field, ""))
            if current is not None and current != final:
                self.error("transition_final_state_mismatch", "status transitions", f"Final transition for {key!r} is {final!r}, current artifact says {current!r}.")

        if self.manifest.get("search_status") == "complete_within_scope":
            for row in self.active_coverage:
                cell_id = row.get("coverage_cell_id", "")
                if not any(
                    key[0] in {"coverage_cell", "cell", "coverage"}
                    and key[1] == cell_id
                    and key[2] == "coverage_status"
                    and key[3] == self.active_version
                    for key in final_states
                ):
                    self.error("coverage_transition_missing", row.get("__source__", "coverage"), "Complete run lacks a coverage-status transition for this cell.")

    def _validate_open_execution_queue(
        self, open_rows: Sequence[Mapping[str, Any]]
    ) -> None:
        queue_path = self.run_dir / "execution_queue.csv"
        queue = self.load_csv(queue_path)
        queue_location = self.rel(queue_path)
        selected_columns: dict[str, str] = {}
        if queue_path.is_file():
            headers = self.csv_headers.get(queue_location, set())
            for concept, aliases in EXECUTION_QUEUE_COLUMN_ALIASES.items():
                column = next((alias for alias in aliases if alias in headers), "")
                if not column:
                    self.error(
                        "missing_execution_queue_column",
                        queue_location,
                        f"Execution queue lacks {concept!r}; accepted columns are {list(aliases)}.",
                    )
                else:
                    selected_columns[concept] = column

        queue_by_cell: dict[str, Mapping[str, Any]] = {}
        for index, row in enumerate(queue, start=1):
            location = row.get("__source__", f"{queue_location}:{index + 1}")
            for concept, column in selected_columns.items():
                if _blank(row.get(column)):
                    self.error(
                        "incomplete_execution_queue_row",
                        location,
                        f"Execution queue must explicitly record {concept!r}; use 'none' or 'not_applicable' when appropriate.",
                    )
            cell_column = selected_columns.get("coverage_cell_id", "coverage_cell_id")
            cell_id = str(row.get(cell_column, "")).strip()
            if cell_id:
                if cell_id in queue_by_cell:
                    self.error(
                        "duplicate_execution_queue_cell",
                        location,
                        f"coverage_cell_id {cell_id!r} appears more than once in the execution queue.",
                    )
                queue_by_cell[cell_id] = row
            tier_column = selected_columns.get("execution_tier")
            if tier_column and not _blank(row.get(tier_column)):
                self._status(
                    row.get(tier_column),
                    EXECUTION_TIERS,
                    location,
                    "execution_tier",
                )

        open_by_id = {
            str(row.get("coverage_cell_id", "")): row for row in open_rows
        }
        queued_ids = set(queue_by_cell)
        open_ids = set(open_by_id)
        missing = open_ids - queued_ids
        if missing:
            self.error(
                "open_queue_incomplete",
                queue_location,
                f"Execution queue omits open cells {sorted(missing)}.",
            )
        closed_or_unknown = queued_ids - open_ids
        if closed_or_unknown:
            self.error(
                "closed_cell_in_open_queue",
                queue_location,
                f"Execution queue contains closed or unknown cells {sorted(closed_or_unknown)}.",
            )
        for cell_id in open_ids & queued_ids:
            row = queue_by_cell[cell_id]
            tier_column = selected_columns.get("execution_tier")
            if tier_column:
                queued_tier = str(row.get(tier_column, "")).strip()
                coverage_tier = str(open_by_id[cell_id].get("execution_tier", "")).strip()
                if queued_tier and coverage_tier and queued_tier != coverage_tier:
                    self.error(
                        "execution_queue_tier_mismatch",
                        row.get("__source__", queue_location),
                        f"Queue tier {queued_tier!r} differs from coverage tier {coverage_tier!r} for {cell_id!r}.",
                    )

        pause_path = self.run_dir / "pause_report.md"
        pause_location = self.rel(pause_path)
        if not pause_path.is_file():
            self.error(
                "missing_pause_report",
                pause_location,
                "An open-cell stop state requires pause_report.md.",
            )
        else:
            self.checked_files[pause_location] = "markdown"
            try:
                if not pause_path.read_text(encoding="utf-8").strip():
                    self.error(
                        "empty_pause_report",
                        pause_location,
                        "pause_report.md must record the blocker and exact resume point.",
                    )
            except OSError as exc:
                self.error(
                    "unreadable_artifact",
                    pause_location,
                    f"Cannot read pause report: {exc}",
                )

    def _validate_completion_and_pause(self) -> None:
        closed = [row for row in self.active_coverage if row.get("coverage_status") in CLOSED_COVERAGE_STATUSES]
        open_rows = [row for row in self.active_coverage if row.get("coverage_status") not in CLOSED_COVERAGE_STATUSES]
        computed_complete = not open_rows and (
            bool(self.active_coverage)
            or self.manifest.get("inventory_status") == "saturated"
        )
        manifest_complete = _bool(self.manifest.get("coverage_complete"))
        inventory_saturated = _bool(self.manifest.get("inventory_saturated"))
        ledger_audited = _bool(self.manifest.get("search_ledger_audited"))
        decision_applied = _bool(self.manifest.get("decision_contract_applied"))
        decision_status = str(self.manifest.get("decision_status", ""))
        search_status = self.manifest.get("search_status")
        self.counts["closed_coverage_cells"] = len(closed)
        self.counts["open_coverage_cells"] = len(open_rows)

        if (
            self.strict_schema
            and self.manifest.get("inventory_status") == "saturated"
            and manifest_complete is True
        ):
            covered_mechanism_ids = {
                str(row.get("mechanism_id", "")).strip()
                for row in self.active_coverage
                if not _blank(row.get("mechanism_id"))
            }
            preserved_coverage_by_key = {
                (
                    str(row.get("__file_version__", "")),
                    str(row.get("coverage_cell_id", "")).strip(),
                ): row
                for row in self.all_coverage
                if not _blank(row.get("coverage_cell_id"))
            }

            def has_closed_rejection_evidence(
                coverage_row: Mapping[str, Any],
                seen: set[tuple[str, str]] | None = None,
            ) -> bool:
                status = str(coverage_row.get("coverage_status", ""))
                if status == "tested_valid":
                    return True
                if status != "covered_by":
                    return False
                source_key = (
                    str(coverage_row.get("__file_version__", "")),
                    str(coverage_row.get("coverage_cell_id", "")).strip(),
                )
                visited = set(seen or set())
                if source_key in visited:
                    return False
                visited.add(source_key)
                target_id = str(
                    _first(
                        coverage_row,
                        "covered_by_cell_id",
                        "coverage_equivalent_to",
                        default="",
                    )
                ).strip()
                target = preserved_coverage_by_key.get(
                    (source_key[0], target_id)
                )
                return target is not None and has_closed_rejection_evidence(
                    target, visited
                )

            rejection_evidence_mechanism_ids = {
                str(row.get("mechanism_id", "")).strip()
                for row in self.all_coverage
                if not _blank(row.get("mechanism_id"))
                and has_closed_rejection_evidence(row)
            }
            for row in self.active_inventory:
                mechanism_id = str(row.get("mechanism_id", "")).strip()
                entity_label = "candidate" if self.generic_inventory_schema else "mechanism"
                status_field = (
                    "candidate_status" if self.generic_inventory_schema else "mechanism_status"
                )
                source_label = f"active {entity_label} inventory"
                data_support = _lens(row.get("data_support_status"))
                mechanism_status = str(row.get("mechanism_status", "")).strip()
                requires_coverage = (
                    bool(mechanism_id)
                    and mechanism_status in COVERAGE_ELIGIBLE_MECHANISM_STATUSES
                    and _blank(row.get("duplicate_of"))
                )
                if requires_coverage and mechanism_id not in covered_mechanism_ids:
                    self.error(
                        "eligible_candidate_without_coverage"
                        if self.generic_inventory_schema
                        else "eligible_mechanism_without_coverage",
                        row.get("__source__", source_label),
                        f"Active, nonduplicate {entity_label} {mechanism_id!r} has no finite coverage cell in the active inventory version.",
                    )
                if (
                    mechanism_status == "rejected"
                    and mechanism_id
                    and mechanism_id not in rejection_evidence_mechanism_ids
                ):
                    self.error(
                        "rejected_candidate_without_coverage_history"
                        if self.generic_inventory_schema
                        else "rejected_mechanism_without_coverage_history",
                        row.get("__source__", source_label),
                        f"Rejected {entity_label} {mechanism_id!r} has no preserved tested_valid coverage or covered_by chain to tested_valid evidence.",
                    )
                if mechanism_status == "needs_human_judgment":
                    self.error(
                        "unresolved_candidate_judgment_at_completion"
                        if self.generic_inventory_schema
                        else "unresolved_human_judgment_at_completion",
                        row.get("__source__", source_label),
                        f"{entity_label.capitalize()} {mechanism_id!r} still needs human judgment and cannot be included in saturated coverage completion.",
                    )
                if data_support == "not_assessed" and _blank(
                    row.get("duplicate_of")
                ):
                    self.error(
                        "unresolved_data_support_at_completion",
                        row.get("__source__", source_label),
                        f"{entity_label.capitalize()} {mechanism_id!r} has data_support_status='not_assessed' at saturated coverage completion ({status_field}={mechanism_status!r}).",
                    )

        if manifest_complete is not None and manifest_complete != computed_complete:
            self.error(
                "coverage_completion_mismatch",
                "run_manifest.json",
                f"coverage_complete={manifest_complete} but active matrix has {len(open_rows)} open cell(s).",
            )
        if self.manifest.get("inventory_status") == "saturated" and inventory_saturated is not True:
            self.error("inventory_saturation_mismatch", "run_manifest.json", "inventory_status=saturated requires inventory_saturated=true.")
        if inventory_saturated is True and self.manifest.get("inventory_status") != "saturated":
            self.error("inventory_saturation_mismatch", "run_manifest.json", "inventory_saturated=true requires inventory_status=saturated.")

        if search_status == "complete_within_scope":
            if inventory_saturated is not True:
                self.error("premature_completion", "run_manifest.json", "Complete status requires inventory saturation.")
            if computed_complete is not True or manifest_complete is not True:
                self.error("premature_completion", "run_manifest.json", "Complete status requires every eligible coverage cell to be closed.")
            if ledger_audited is not True:
                self.error("premature_completion", "run_manifest.json", "Complete status requires search_ledger_audited=true.")
            if decision_applied is not True:
                self.error(
                    "premature_completion",
                    "run_manifest.json",
                    "Complete status requires decision_contract_applied=true.",
                )
            if decision_status not in TERMINAL_RUN_DECISION_STATUSES:
                self.error(
                    "premature_completion",
                    "run_manifest.json",
                    "Complete status requires a terminal decision status.",
                )
            if self.prior_audit_status not in {"complete", "unknown", "not_applicable"}:
                self.error(
                    "prior_exposure_completion_blocked",
                    "prior_exposure_audit.json",
                    "complete_within_scope requires a complete audit or an explicitly justified unknown/not_applicable audit.",
                )
            if self.prior_exposure_status == "not_assessed":
                self.error(
                    "prior_exposure_completion_blocked",
                    "prior_exposure_audit.json",
                    "complete_within_scope is forbidden while prior_exposure_status=not_assessed.",
                )
            comparable_families = [
                family
                for family in self.families
                if str(_first(family, "comparison_status", "comparability_status", default=""))
                == "comparable_within_family"
            ]
            if self.decision_contract and not self._extract_comparison_groups() and len(comparable_families) > 1:
                self.error(
                    "premature_completion",
                    "decision_contract.json",
                    "Complete decision with multiple directly comparable families requires explicit comparison groups.",
                )

        open_stop_statuses = {
            "resource_limited_pause",
            "user_limited_stop",
            "governance_blocked",
            "human_decision_required",
        }
        if search_status in {"resource_limited_pause", "user_limited_stop"} and not open_rows:
            self.error(
                "pause_without_open_work",
                "run_manifest.json",
                "Resource- or user-limited stop requires at least one open coverage cell.",
            )
        if search_status in open_stop_statuses and open_rows:
            self._validate_open_execution_queue(open_rows)
            if search_status == "resource_limited_pause":
                resource_blocked = any(
                    row.get("coverage_status") == "resource_blocked"
                    for row in open_rows
                )
                envelope_exhausted = (
                    _bool(self.manifest.get("resource_envelope_exhausted")) is True
                )
                if not resource_blocked and not envelope_exhausted:
                    self.error(
                        "resource_pause_without_resource_condition",
                        "run_manifest.json",
                        "Resource-limited pause requires resource-blocked work or resource_envelope_exhausted=true.",
                    )
            if search_status == "governance_blocked":
                governance_condition = any(
                    row.get("coverage_status") == "governance_blocked"
                    for row in open_rows
                ) or self.manifest.get("governance_status") == "blocked"
                if not governance_condition:
                    self.error(
                        "governance_stop_without_governance_condition",
                        "run_manifest.json",
                        "governance_blocked requires a blocked governance status or governance-blocked coverage cell.",
                    )
        elif (self.run_dir / "execution_queue.csv").is_file():
            queue = self.load_csv(self.run_dir / "execution_queue.csv", required=False)
            closed_ids = {row.get("coverage_cell_id", "") for row in closed}
            bad = {row.get("coverage_cell_id", "") for row in queue} & closed_ids
            if bad:
                self.error("closed_cell_in_open_queue", "execution_queue.csv", f"Execution queue contains closed cells {sorted(bad)}.")


def validate_run(run_dir: Path) -> dict[str, Any]:
    return RunValidator(run_dir).validate()


def _output_input_collision(
    run_dir: Path,
    output: Path | None,
    report: Mapping[str, Any],
) -> str | None:
    """Return the run-input label that --output would overwrite, if any."""

    if output is None:
        return None
    try:
        output_resolved = output.resolve()
        root = run_dir.resolve()
    except OSError:
        return None
    checked = report.get("checked_files", {})
    if not isinstance(checked, Mapping):
        return None
    for label in checked:
        candidate = Path(str(label))
        if not candidate.is_absolute():
            candidate = root / candidate
        try:
            candidate_resolved = candidate.resolve()
        except OSError:
            continue
        if output_resolved == candidate_resolved:
            return str(label)
    return None


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_upgrade_snapshot(run_dir: Path, to_profile: str) -> dict[str, Any]:
    """Create a non-overwriting, hash-bound snapshot for a profile upgrade.

    The helper deliberately does not edit run_manifest.json.  It returns the
    exact profile_history entry to append after the caller reviews the copied
    evidence and performs the profile migration.
    """

    root = run_dir.resolve()
    if not root.is_dir():
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": "Run directory does not exist.",
        }
    validator = RunValidator(root)
    manifest_path = validator._safe_internal_file(
        "run_manifest.json",
        "run_manifest.json",
        kind="current run manifest",
    )
    if manifest_path is None:
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": "Current run manifest is unavailable or unsafe.",
            "errors": [issue.as_dict() for issue in validator.errors],
        }
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": f"Cannot parse run_manifest.json: {exc}",
        }
    if not isinstance(manifest, Mapping):
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": "run_manifest.json must be an object.",
        }
    current_profile = str(manifest.get("research_profile", "")).strip()
    if current_profile not in RESEARCH_PROFILES or to_profile not in RESEARCH_PROFILES:
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": f"Both current and target profiles must be one of {sorted(RESEARCH_PROFILES)}.",
        }
    if PROFILE_RANK[to_profile] <= PROFILE_RANK[current_profile]:
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": f"Target {to_profile!r} must be stricter than current profile {current_profile!r}.",
        }
    current_report = validate_run(root)
    if not current_report.get("valid"):
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": "Current profile must pass validation before its history can be sealed for upgrade.",
            "validation_errors": current_report.get("errors", []),
        }
    history = manifest.get("profile_history")
    if not isinstance(history, list) or not history:
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": "Current manifest requires a nonempty profile_history before upgrade.",
        }
    required_by_profile = {
        "fixed_test": {
            "run_manifest.json",
            "claim_card.json",
            "data_versions.json",
        },
        "adaptive_search": {
            "run_manifest.json",
            "decision_contract.json",
            "prior_exposure_audit.json",
            "data_versions.json",
            "search_ledger.jsonl",
            "selection_families.json",
            "status_transitions.jsonl",
            "candidate_registry.csv",
        },
    }
    logical_paths = set(required_by_profile[current_profile])
    round_records = manifest.get("round_artifacts")
    if not isinstance(round_records, list) or not round_records:
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": "Current manifest must retain a nonempty round_artifacts list.",
        }
    for record in round_records:
        if not isinstance(record, Mapping):
            return {
                "snapshot": "refused",
                "run_directory": str(root),
                "reason": "Every round_artifacts entry must be an object.",
            }
        for field in ("report_path", "reproduce_path"):
            value = str(record.get(field, "")).strip()
            if not value:
                return {
                    "snapshot": "refused",
                    "run_directory": str(root),
                    "reason": f"Every round record must define {field}.",
                }
            logical_paths.add(value)

    sources: dict[str, Path] = {}
    for logical_path in sorted(logical_paths):
        source = validator._safe_internal_file(
            logical_path,
            f"upgrade source {logical_path}",
            kind="upgrade source artifact",
        )
        if source is not None:
            sources[logical_path] = source
    if validator.errors or set(sources) != logical_paths:
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": "One or more required prior-profile artifacts are missing or unsafe.",
            "errors": [issue.as_dict() for issue in validator.errors],
        }

    sequence = len(history) + 1
    history_root = root / "history"
    if history_root.is_symlink():
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": "history/ cannot be a symbolic link.",
        }
    snapshot_root = history_root / (
        f"profile_upgrade_{sequence:03d}_{current_profile}_to_{to_profile}"
    )
    if snapshot_root.exists() or snapshot_root.is_symlink():
        return {
            "snapshot": "refused",
            "run_directory": str(root),
            "reason": f"Snapshot target {snapshot_root.relative_to(root)!s} already exists; no files were changed.",
        }
    created_at = datetime.now(timezone.utc).isoformat()
    artifact_records: list[dict[str, str]] = []
    created_files: list[str] = []
    try:
        snapshot_root.mkdir(parents=True, exist_ok=False)
        for logical_path, source in sorted(sources.items()):
            destination = snapshot_root / "artifacts" / logical_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
            relative_destination = str(destination.relative_to(root))
            created_files.append(relative_destination)
            artifact_records.append(
                {
                    "logical_path": logical_path,
                    "snapshot_path": relative_destination,
                    "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                }
            )
        snapshot = {
            "snapshot_schema_version": "1.0",
            "profile": current_profile,
            "captured_at": created_at,
            "target_profile": to_profile,
            "artifacts": artifact_records,
        }
        snapshot_path = snapshot_root / "preservation_snapshot.json"
        _write_json(snapshot_path, snapshot)
        snapshot_relative = str(snapshot_path.relative_to(root))
        created_files.append(snapshot_relative)
        snapshot_sha256 = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
    except OSError as exc:
        return {
            "snapshot": "failed",
            "run_directory": str(root),
            "reason": f"Snapshot creation stopped: {exc}",
            "created_files": sorted(created_files),
        }
    return {
        "snapshot": "created",
        "run_directory": str(root),
        "from_profile": current_profile,
        "to_profile": to_profile,
        "created_files": sorted(created_files),
        "next_profile_history_entry": {
            "profile": to_profile,
            "started_at": created_at,
            "preservation_snapshot_path": snapshot_relative,
            "preservation_snapshot_sha256": snapshot_sha256,
        },
        "next_action": "Review the snapshot, migrate profile artifacts, then append the returned entry to profile_history without deleting earlier entries.",
    }


def initialize_run(run_dir: Path, profile: str) -> dict[str, Any]:
    if profile not in RESEARCH_PROFILES:
        return {
            "init": "refused",
            "run_directory": str(run_dir.resolve()),
            "reason": f"profile must be one of {sorted(RESEARCH_PROFILES)}.",
        }
    root = run_dir.resolve()
    if root.exists():
        if not root.is_dir():
            return {
                "init": "refused",
                "run_directory": str(root),
                "reason": "Target exists and is not a directory.",
            }
        try:
            if any(root.iterdir()):
                return {
                    "init": "refused",
                    "run_directory": str(root),
                    "reason": "Target directory is not empty; no files were changed.",
                }
        except OSError as exc:
            return {
                "init": "failed",
                "run_directory": str(root),
                "reason": f"Cannot inspect target directory: {exc}",
            }
    else:
        try:
            root.mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            return {
                "init": "failed",
                "run_directory": str(root),
                "reason": f"Cannot create target directory: {exc}",
            }

    created_at = datetime.now(timezone.utc).isoformat()
    run_id = root.name or "TODO-run-id"
    todo = REQUIRED_SENTINEL
    created: list[str] = []

    def write_text(relative: str, payload: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="") as handle:
            handle.write(payload)
        created.append(relative)

    def write_json(relative: str, value: Any) -> None:
        write_text(relative, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def write_jsonl(relative: str, rows: Sequence[Mapping[str, Any]]) -> None:
        write_text(relative, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))

    def write_csv(
        relative: str,
        fieldnames: Sequence[str],
        rows: Sequence[Mapping[str, Any]] = (),
    ) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        created.append(relative)

    round_record = {
        "round_id": "round_000",
        "status": "planned",
        "report_path": "rounds/round_000/report.md",
        "reproduce_path": "rounds/round_000/reproduce_commands.txt",
        "sealed_at": None,
        "report_sha256": todo,
        "reproduce_sha256": todo,
    }
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "research_profile": profile,
        "profile_history": [{"profile": profile, "started_at": created_at}],
        "stage_status": "planned",
        "round_artifacts": [round_record],
        "question": todo,
        "scientific_scope": todo,
        "execution_mode": "single_round" if profile == "fixed_test" else "multi_round",
        "created_at": created_at,
        "output_root": str(root),
        "governance_status": "not_assessed",
        "authorized_inputs": [todo],
        "authorized_actions": [todo],
        "prohibited_actions": [todo],
        "data_product_scope": [todo],
        "data_versions_file": "data_versions.json",
        "data_version_set_id": "data-v001",
        "safety_boundary": todo,
        "consistency_validator_version": VALIDATOR_VERSION,
        "last_consistency_check": None,
    }
    if profile in {"adaptive_search", "coverage_search"}:
        manifest.update(
            {
                "decision_contract_version": "dc-v001",
                "prior_exposure_audit_version": "pe-v001",
                "search_ledger_audited": False,
                "decision_contract_applied": False,
                "decision_status": "not_evaluated",
                "selection_family_policy": todo,
                "complete_selection_path_policy": todo,
                "evidence_partition_policy": todo,
                "data_look_policy": todo,
                "verification_policy": todo,
            }
        )
    if profile == "coverage_search":
        manifest.update(
            {
                "inventory_version": "v001",
                "inventory_status": "draft",
                "search_status": "inventory_building",
                "inventory_saturated": False,
                "coverage_complete": False,
                "inventory_audit_protocol": todo,
                "inventory_generation_lenses": ["candidate_forward", "data_product_reverse"],
                "coverage_unit_definition": todo,
                "coverage_closure_rules": sorted(CLOSED_COVERAGE_STATUSES),
                "saturation_rule": todo,
                "saturation_required_sources": ["candidate_forward", "data_product_reverse"],
                "compute_authorization_id": todo,
                "execution_resource_envelope": {"status": "not_assessed", "details": todo},
                "resource_pause_policy": todo,
                "user_specified_limits": {"status": "not_assessed", "details": todo},
            }
        )
    decision_contract = {
        "decision_contract_version": "dc-v001",
        "decision_id": todo,
        "decision_question": todo,
        "target_population": todo,
        "analysis_population": todo,
        "selection_population": todo,
        "reporting_population": todo,
        "eligible_candidate_classes": [todo],
        "substantive_eligibility_rule": todo,
        "measurement_error_policy": todo,
        "transportability_requirement": todo,
        "transportability_status": todo,
        "eligible_selection_family_ids": [],
        "declared_selection_family_ids": [],
        "selection_family_comparison_keys": {},
        "comparison_groups": [],
        "ranked_selection_family_ids": [],
        "comparison_key_definition": todo,
        "comparability_rule": todo,
        "estimand": todo,
        "ranking_evidence": {"criterion": todo},
        "evidence_scale_mapping": {
            "screening_statistic": todo,
            "screening_estimand_and_scale": todo,
            "decision_model_or_statistic": todo,
            "decision_estimand_and_scale": todo,
            "scale_relation": todo,
            "validation_or_calibration_rule": todo,
            "discordance_rule": todo,
            "reason": todo,
        },
        "decision_rule": todo,
        "minimum_meaningful_difference": todo,
        "complexity_and_data_quality_rule": todo,
        "tie_rule": todo,
        "inconclusive_rule": todo,
        "complete_selection_path_method": todo,
        "specification_timing": todo,
        "freeze_time": todo,
        "amendment_policy": todo,
    }
    prior_exposure = {
        "prior_exposure_audit_version": "pe-v001",
        "audit_status": "incomplete",
        "prior_exposure_status": "not_assessed",
        "confirmatory_status": "unknown",
        "future_verification_status": todo,
        "sources_checked": [],
        "overlap_unit": todo,
        "overlapping_data": [],
        "prior_analyses": [],
        "prior_parameter_attempts": [],
        "prior_data_looks": [],
        "prior_holdout_exposure": todo,
        "unknown_gaps": [todo],
        "resulting_evidence_stage_limits": [todo],
        "audited_at": todo,
        "sample_code_or_skill_change_restores_confirmatory": False,
    }
    data_versions = {
        "data_version_set_id": "data-v001",
        "data_versions": [],
    }
    claim_card = {
        "claim_id": todo,
        "claim": todo,
        "target_population": todo,
        "analysis_population": todo,
        "supported_sample_id": todo,
        "estimand": todo,
        "minimum_meaningful_effect": todo,
        "analysis_or_test": todo,
        "decision_rule": todo,
        "falsifier": todo,
        "specification_timing": todo,
        "prior_exposure_status": "not_assessed",
        "evidence_stage": "exploratory",
        "result_status": "not_run",
        "effect_summary": todo,
        "uncertainty_summary": todo,
        "main_caveat": todo,
        "data_version_ids": [],
        "completed_as_scoped": False,
    }
    selection_families = {"families": [], "history": []}
    saturation_audit = {
        "inventory_version": "v001" if profile == "coverage_search" else None,
        "inventory_saturated": False,
        "audits": [],
    }
    round_inventory = {
        "run_id": run_id,
        "round_id": "round_000",
        "parent_round_id": None,
        "inventory_version": "v001",
        "decision_contract_version": "dc-v001",
        "prior_exposure_audit_version": "pe-v001",
        "coverage_cell_ids": [],
        "selection_family_versions": [],
        "inputs": [],
        "data_version_ids": [],
        "code_state": {"status": todo},
        "environment": {"status": todo},
        "parameters": {},
        "seed_set": [],
        "sample_counts": {},
        "ledger_entry_ids": [],
        "uncertainty_components": [],
        "resource_use": {},
        "status_transitions": [],
        "outputs": {},
    }
    consistency_placeholder = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "checked_at": None,
        "run_directory_label": root.name,
        "run_id": run_id,
        "inventory_version": "v001",
        "artifact_versions": {
            "artifact_schema": ARTIFACT_SCHEMA_VERSION,
            "data_version_set": "data-v001",
        },
        "valid": False,
        "error_count": 1,
        "warning_count": 0,
        "errors": [
            {
                "code": "not_yet_validated",
                "location": "consistency_report.json",
                "message": "TODO: replace by running the validator.",
            }
        ],
        "warnings": [],
        "counts": {},
        "checked_files": {},
    }
    if profile in {"adaptive_search", "coverage_search"}:
        consistency_placeholder["artifact_versions"].update(
            {
                "decision_contract": "dc-v001",
                "prior_exposure_audit": "pe-v001",
            }
        )
    if profile == "coverage_search":
        consistency_placeholder["artifact_versions"]["inventory"] = "v001"

    try:
        write_json("run_manifest.json", manifest)
        write_json("data_versions.json", data_versions)
        if profile == "fixed_test":
            write_json("claim_card.json", claim_card)
        else:
            write_json("decision_contract.json", decision_contract)
            write_json("prior_exposure_audit.json", prior_exposure)
            write_jsonl("search_ledger.jsonl", [])
            write_json("selection_families.json", selection_families)
            write_jsonl("status_transitions.jsonl", [])
            if profile == "adaptive_search":
                write_csv("candidate_registry.csv", sorted(ADAPTIVE_CANDIDATE_REQUIRED_FIELDS))
            else:
                write_csv(
                    "inventories/candidate_inventory_v001.csv",
                    sorted(GENERIC_INVENTORY_REQUIRED_COLUMNS),
                )
                write_csv(
                    "inventories/coverage_matrix_v001.csv",
                    sorted(GENERIC_COVERAGE_REQUIRED_COLUMNS),
                )
                write_json("inventories/saturation_audit_v001.json", saturation_audit)
                write_csv("execution_queue.csv", tuple(EXECUTION_QUEUE_COLUMN_ALIASES))
                generic_registry_fields = (
                    (CANDIDATE_REQUIRED_FIELDS - {"mechanism_id"})
                    | V15_COVERAGE_CANDIDATE_FIELDS
                )
                write_csv("candidate_registry.csv", sorted(generic_registry_fields))
        write_text(
            "rounds/round_000/report.md",
            f"# Round 000 draft\n\n- Research profile: {profile}\n- Question: TODO\n- Scope and governance: TODO\n- Result or next action: TODO\n",
        )
        write_text(
            "rounds/round_000/reproduce_commands.txt",
            "TODO: record exact, secret-free reproduction commands before execution.\n",
        )
        if profile == "coverage_search":
            write_json("rounds/round_000/inventory.json", round_inventory)
            write_csv("rounds/round_000/summary.csv", GENERIC_ROUND_SUMMARY_COLUMNS)
            write_text(
                "rounds/round_000/round_gate.md",
                "# Round 000 gate\n\n- [ ] Freeze scope and governance.\n- [ ] Complete the Decision Contract and prior-exposure audit.\n- [ ] Freeze candidate inventory, coverage, selection-family, and evidence-scale rules.\n- [ ] Run the consistency validator before execution.\n",
            )
        write_json("consistency_report.json", consistency_placeholder)
    except (OSError, csv.Error, ValueError) as exc:
        return {
            "init": "failed",
            "run_directory": str(root),
            "reason": f"Initialization stopped without overwriting any file: {exc}",
            "created_files": sorted(created),
        }

    return {
        "init": "created",
        "run_directory": str(root),
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "research_profile": profile,
        "created_files": sorted(created),
        "next_command": f"{Path(__file__).name} {root}",
    }


def _build_self_test_fixture(root: Path) -> None:
    (root / "inventories").mkdir(parents=True)
    round_root = root / "rounds" / "round_001"
    round_root.mkdir(parents=True)
    report_path = round_root / "report.md"
    reproduce_path = round_root / "reproduce_commands.txt"
    report_path.write_text("# Sealed synthetic round\n", encoding="utf-8")
    reproduce_path.write_text("synthetic-command --frozen\n", encoding="utf-8")
    manifest = {
        "run_id": "self-test-run",
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "research_profile": "coverage_search",
        "profile_history": [
            {"profile": "coverage_search", "started_at": "2000-01-01T00:00:00Z"}
        ],
        "stage_status": "completed_as_scoped",
        "round_artifacts": [
            {
                "round_id": "round_001",
                "status": "completed",
                "report_path": "rounds/round_001/report.md",
                "reproduce_path": "rounds/round_001/reproduce_commands.txt",
                "sealed_at": "2000-01-01T00:00:00Z",
                "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
                "reproduce_sha256": hashlib.sha256(reproduce_path.read_bytes()).hexdigest(),
            }
        ],
        "question": "Does the test mechanism predict the registered observable?",
        "scientific_scope": "synthetic self-test",
        "execution_mode": "multi_round",
        "governance_status": "cleared",
        "inventory_version": "v001",
        "inventory_status": "saturated",
        "search_status": "complete_within_scope",
        "inventory_saturated": True,
        "coverage_complete": True,
        "search_ledger_audited": True,
        "decision_contract_applied": True,
        "decision_status": "leading",
        "decision_contract_version": "dc-v001",
        "prior_exposure_audit_version": "pe-v001",
        "data_version_set_id": "data-v001",
        "saturation_required_sources": ["mechanism_forward", "data_product_reverse"],
    }
    _write_json(root / "run_manifest.json", manifest)

    inventory_fields = [
        "inventory_version",
        "mechanism_id",
        "parent_mechanism_id",
        "mechanism",
        "distinct_pathway",
        "inclusion_rationale",
        "generation_lens",
        "applicable_regime",
        "predicted_signature",
        "required_data_products",
        "data_support_status",
        "mechanism_status",
        "specification_timing",
        "duplicate_of",
    ]
    _write_csv(
        root / "inventories" / "mechanism_inventory_v001.csv",
        inventory_fields,
        [
            {
                "inventory_version": "v001",
                "mechanism_id": "M001",
                "parent_mechanism_id": "",
                "mechanism": "synthetic mechanism",
                "distinct_pathway": "registered pathway",
                "inclusion_rationale": "self-test",
                "generation_lens": "mechanism_forward",
                "applicable_regime": "synthetic",
                "predicted_signature": "positive registered effect",
                "required_data_products": "D001",
                "data_support_status": "supported",
                "mechanism_status": "provisionally_supported",
                "specification_timing": "pre_result_frozen",
                "duplicate_of": "",
            }
        ],
    )
    coverage_fields = [
        "coverage_cell_id",
        "inventory_version",
        "mechanism_id",
        "observable_id",
        "formulation_id",
        "data_product_id",
        "data_version_id",
        "supported_sample_id",
        "parameter_or_scale_domain",
        "comparator",
        "expected_signature",
        "minimum_meaningful_effect",
        "sensitivity_requirement",
        "mechanism_alignment",
        "measurement_error_sensitivity",
        "falsifier",
        "selection_family_id",
        "selection_family_version",
        "comparison_key",
        "comparability_status",
        "specification_timing",
        "evidence_stage",
        "execution_tier",
        "coverage_status",
        "execution_status",
        "result_status",
        "verification_status",
        "round_id",
        "ledger_entry_ids",
        "blocker",
        "covered_by_cell_id",
    ]
    _write_csv(
        root / "inventories" / "coverage_matrix_v001.csv",
        coverage_fields,
        [
            {
                "coverage_cell_id": "C001",
                "inventory_version": "v001",
                "mechanism_id": "M001",
                "observable_id": "O001",
                "formulation_id": "F001",
                "data_product_id": "D001",
                "data_version_id": "DV001",
                "supported_sample_id": "S001",
                "parameter_or_scale_domain": "registered point",
                "comparator": "registered synthetic null",
                "expected_signature": "positive",
                "minimum_meaningful_effect": "0.1",
                "sensitivity_requirement": "power at least 0.8 at effect 0.1",
                "mechanism_alignment": "direct",
                "measurement_error_sensitivity": "passed",
                "falsifier": "effect below registered threshold",
                "selection_family_id": "SF001",
                "selection_family_version": "sf-v001",
                "comparison_key": "synthetic-population|S001|registered-effect|clean|exploratory",
                "comparability_status": "comparable_within_family",
                "specification_timing": "pre_result_frozen",
                "evidence_stage": "exploratory",
                "execution_tier": "deep_test",
                "coverage_status": "tested_valid",
                "execution_status": "completed",
                "result_status": "supported",
                "verification_status": "unverified",
                "round_id": "round_001",
                "ledger_entry_ids": "L001",
                "blocker": "",
                "covered_by_cell_id": "",
            }
        ],
    )
    previous_inventory = list(
        csv.DictReader(
            (root / "inventories" / "mechanism_inventory_v001.csv").open(
                "r", encoding="utf-8", newline=""
            )
        )
    )
    previous_inventory[0]["inventory_version"] = "v000"
    _write_csv(
        root / "inventories" / "mechanism_inventory_v000.csv",
        inventory_fields,
        previous_inventory,
    )
    previous_coverage = list(
        csv.DictReader(
            (root / "inventories" / "coverage_matrix_v001.csv").open(
                "r", encoding="utf-8", newline=""
            )
        )
    )
    previous_coverage[0]["inventory_version"] = "v000"
    previous_coverage[0]["selection_family_version"] = "sf-v000"
    previous_coverage[0]["coverage_status"] = "eligible_untested"
    previous_coverage[0]["execution_status"] = "planned"
    previous_coverage[0]["result_status"] = "not_run"
    previous_coverage[0]["round_id"] = "round_000"
    previous_coverage[0]["ledger_entry_ids"] = "L000"
    _write_csv(
        root / "inventories" / "coverage_matrix_v000.csv",
        coverage_fields,
        previous_coverage,
    )
    _write_json(
        root / "inventories" / "saturation_audit_v001.json",
        {
            "inventory_version": "v001",
            "inventory_saturated": True,
            "audits": [
                {"source": "mechanism_forward", "completed": True, "new_eligible_mechanisms": []},
                {"source": "data_product_reverse", "completed": True, "new_eligible_mechanisms": []},
            ],
        },
    )
    ledger_entry_v000 = {
        "ledger_entry_id": "L000",
        "inventory_version": "v000",
        "coverage_cell_id": "C001",
        "selection_family_id": "SF001",
        "selection_family_version": "sf-v000",
        "decision_influence": True,
        "selection_path_stage": "generation",
        "data_look_id": "look-000",
        "seed_policy_id": "deterministic",
        "data_version_ids": ["DV001"],
        "input_and_code_state": {"data_version_ids": ["DV001"], "code_state": "self-test"},
        "execution_status": "planned",
        "result_status": "not_run",
        "artifact_paths": [],
    }
    ledger_entry = {
        "ledger_entry_id": "L001",
        "inventory_version": "v001",
        "coverage_cell_id": "C001",
        "selection_family_id": "SF001",
        "selection_family_version": "sf-v001",
        "decision_influence": True,
        "selection_path_stage": "deep_test",
        "data_look_id": "look-001",
        "seed_policy_id": "deterministic",
        "input_and_code_state": {"data_version_ids": ["DV001"], "code_state": "self-test"},
        "execution_status": "completed",
        "result_status": "supported",
        "artifact_paths": [],
    }
    (root / "search_ledger.jsonl").write_text(
        json.dumps(ledger_entry_v000) + "\n" + json.dumps(ledger_entry) + "\n",
        encoding="utf-8",
    )
    current_family = {
        "selection_family_id": "SF001",
        "selection_family_version": "sf-v001",
        "decision_id": "DEC001",
        "comparability_status": "comparable_within_family",
        "comparison_key": "synthetic-population|S001|registered-effect|clean|exploratory",
        "target_population": "synthetic-population",
        "supported_sample_id": "S001",
        "estimand": "registered synthetic effect",
        "data_quality_regime": "clean",
        "evidence_stage": "exploratory",
        "transportability_requirement": "same_population",
        "transportability_status": "not_required",
        "included_cell_ids": ["C001"],
        "selection_path_ledger_entry_ids": ["L000", "L001"],
        "selection_path_complete": True,
        "inference_method": "end-to-end null calibration",
    }
    historical_family = dict(current_family)
    historical_family["selection_family_version"] = "sf-v000"
    historical_family["selection_path_ledger_entry_ids"] = ["L000"]
    _write_json(
        root / "selection_families.json",
        {
            "families": [current_family],
            "history": [historical_family],
        },
    )
    _write_json(
        root / "decision_contract.json",
        {
            "decision_contract_version": "dc-v001",
            "decision_id": "DEC001",
            "decision_question": "Which eligible candidate is supported?",
            "eligible_candidate_classes": ["data-supported mechanism candidates"],
            "eligible_selection_family_ids": ["SF001"],
            "comparison_key_definition": "target population, sample, estimand, quality, and evidence stage",
            "comparability_rule": "compare only candidates with the same registered comparison key",
            "estimand": "registered synthetic effect",
            "target_population": "synthetic-population",
            "analysis_population": "synthetic-population",
            "selection_population": "synthetic-population",
            "reporting_population": "synthetic-population",
            "substantive_eligibility_rule": "candidate must address the registered target population",
            "measurement_error_policy": "promotion requires a passed registered sensitivity analysis",
            "transportability_requirement": "same_population",
            "transportability_status": "not_required",
            "evidence_scale_mapping": [
                {
                    "mapping_id": "ESM001",
                    "selection_family_ids": ["SF001"],
                    "screening_statistic": "registered synthetic screen score",
                    "screening_estimand_and_scale": "screen score on its registered unitless calibration scale",
                    "decision_model_or_statistic": "registered synthetic effect",
                    "decision_estimand_and_scale": "registered synthetic effect in outcome units",
                    "scale_relation": "calibrated_mapping",
                    "validation_or_calibration_rule": "use the frozen synthetic calibration",
                    "discordance_rule": "decision-scale evidence governs when screening and decision evidence disagree",
                }
            ],
            "ranking_evidence": {"criterion": "effect size with calibrated uncertainty and falsifier performance"},
            "decision_rule": "select a leading candidate only when the registered evidence threshold is met",
            "minimum_meaningful_difference": 0.1,
            "complexity_and_data_quality_rule": "prefer adequate quality and penalize unsupported complexity",
            "tie_rule": "report equivalent candidates as tied",
            "inconclusive_rule": "report inconclusive when evidence cannot separate decisions",
            "complete_selection_path_method": "end-to-end null calibration",
            "specification_timing": "pre_result_frozen",
            "comparison_groups": [
                {
                    "comparison_group_id": "CG001",
                    "selection_family_ids": ["SF001"],
                    "comparison_key": "synthetic-population|S001|registered-effect|clean|exploratory",
                }
            ],
            "freeze_time": "2000-01-01T00:00:00Z",
            "amendment_policy": "version amendments and mark outcome-driven changes adaptive",
        },
    )
    _write_json(
        root / "prior_exposure_audit.json",
        {
            "prior_exposure_audit_version": "pe-v001",
            "audit_status": "complete",
            "prior_exposure_status": "no_known_exposure",
            "sources_checked": ["synthetic run records"],
            "overlap_unit": "synthetic observation",
            "overlapping_data": [],
            "prior_analyses": [],
            "prior_parameter_attempts": [],
            "prior_data_looks": [],
            "prior_holdout_exposure": False,
            "unknown_gaps": [],
            "resulting_evidence_stage_limits": [],
            "audited_at": "2000-01-01T00:00:00Z",
            "confirmatory_status": "unrestricted_by_prior_exposure",
            "future_verification_status": "eligible_if_untouched",
            "sample_code_or_skill_change_restores_confirmatory": False,
        },
    )
    _write_json(
        root / "data_versions.json",
        {
            "data_version_set_id": "data-v001",
            "data_versions": [
                {"data_product_id": "D001", "data_version_id": "DV001", "source": "synthetic self-test"}
            ],
        },
    )
    candidate_fields = [
        "candidate_id",
        "candidate_type",
        "substantive_eligibility",
        "inventory_version",
        "mechanism_id",
        "coverage_cell_ids",
        "selection_family_id",
        "selection_family_version",
        "comparison_key",
        "comparability_status",
        "decision_status",
        "specification_timing",
        "prior_exposure_status",
        "confirmatory_status",
        "future_verification_status",
        "evidence_stage",
        "verification_status",
        "effect_summary",
        "uncertainty_summary",
        "support_summary",
        "ledger_entry_ids",
        "decision_reason",
    ]
    _write_csv(
        root / "candidate_registry.csv",
        candidate_fields,
        [
            {
                "candidate_id": "CAN001",
                "candidate_type": "mechanism",
                "substantive_eligibility": "eligible",
                "inventory_version": "v001",
                "mechanism_id": "M001",
                "coverage_cell_ids": "C001",
                "selection_family_id": "SF001",
                "selection_family_version": "sf-v001",
                "comparison_key": "synthetic-population|S001|registered-effect|clean|exploratory",
                "comparability_status": "comparable_within_family",
                "decision_status": "leading",
                "specification_timing": "pre_result_frozen",
                "prior_exposure_status": "no_known_exposure",
                "confirmatory_status": "unrestricted_by_prior_exposure",
                "future_verification_status": "eligible_if_untouched",
                "evidence_stage": "exploratory",
                "verification_status": "unverified",
                "effect_summary": "registered synthetic effect exceeded 0.1",
                "uncertainty_summary": "calibrated synthetic interval",
                "support_summary": "supported in the registered sample",
                "ledger_entry_ids": "L000;L001",
                "decision_reason": "met the frozen decision rule",
            }
        ],
    )
    transitions = [
        {
            "entity_type": "inventory",
            "entity_id": "v001",
            "status_field": "inventory_status",
            "from_status": "frozen",
            "to_status": "saturation_audit",
            "inventory_version": "v001",
            "round_id": "round_001",
            "evidence": "saturation audit opened",
        },
        {
            "entity_type": "inventory",
            "entity_id": "v001",
            "status_field": "inventory_status",
            "from_status": "saturation_audit",
            "to_status": "saturated",
            "inventory_version": "v001",
            "round_id": "round_001",
            "evidence": "both required audits passed",
        },
        {
            "entity_type": "coverage_cell",
            "entity_id": "C001",
            "status_field": "coverage_status",
            "from_status": "in_progress",
            "to_status": "tested_valid",
            "inventory_version": "v001",
            "round_id": "round_001",
            "evidence": "valid test completed",
        },
        {
            "entity_type": "coverage_cell",
            "entity_id": "C001",
            "status_field": "execution_status",
            "from_status": "planned",
            "to_status": "completed",
            "inventory_version": "v001",
            "round_id": "round_001",
            "evidence": "execution record",
        },
        {
            "entity_type": "coverage_cell",
            "entity_id": "C001",
            "status_field": "result_status",
            "from_status": "not_run",
            "to_status": "supported",
            "inventory_version": "v001",
            "round_id": "round_001",
            "evidence": "registered criterion met",
        },
        {
            "entity_type": "run",
            "entity_id": "self-test-run",
            "status_field": "search_status",
            "from_status": "coverage_in_progress",
            "to_status": "complete_within_scope",
            "inventory_version": "v001",
            "round_id": "round_001",
            "evidence": "saturation, coverage, and ledger gates passed",
        },
    ]
    for index, transition in enumerate(transitions, start=1):
        transition["transition_id"] = f"T{index:03d}"
        transition["changed_at"] = "2000-01-01T00:00:00Z"
        transition["evidence_paths"] = []
    with (root / "status_transitions.jsonl").open("w", encoding="utf-8") as handle:
        for transition in transitions:
            handle.write(json.dumps(transition) + "\n")


def _convert_self_test_fixture_to_zero_coverage(
    root: Path,
    *,
    data_support_status: str,
    mechanism_status: str = "active",
) -> None:
    manifest_path = root / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["decision_status"] = "no_eligible_candidate"
    _write_json(manifest_path, manifest)

    inventory_path = root / "inventories" / "mechanism_inventory_v001.csv"
    with inventory_path.open("r", encoding="utf-8", newline="") as handle:
        inventory_rows = list(csv.DictReader(handle))
    inventory_rows[0]["data_support_status"] = data_support_status
    inventory_rows[0]["mechanism_status"] = mechanism_status
    _write_csv(inventory_path, list(inventory_rows[0]), inventory_rows)

    coverage_path = root / "inventories" / "coverage_matrix_v001.csv"
    with coverage_path.open("r", encoding="utf-8", newline="") as handle:
        coverage_headers = list(csv.DictReader(handle).fieldnames or [])
    _write_csv(coverage_path, coverage_headers, [])

    ledger_path = root / "search_ledger.jsonl"
    ledger_entries = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    historical_ledger_entries = [
        item
        for item in ledger_entries
        if _version(item.get("inventory_version")) == "0"
    ]
    ledger_path.write_text(
        "".join(json.dumps(item) + "\n" for item in historical_ledger_entries),
        encoding="utf-8",
    )

    families_path = root / "selection_families.json"
    families = json.loads(families_path.read_text(encoding="utf-8"))
    families["families"][0]["included_cell_ids"] = []
    families["families"][0]["selection_path_ledger_entry_ids"] = ["L000"]
    _write_json(families_path, families)

    candidate_path = root / "candidate_registry.csv"
    with candidate_path.open("r", encoding="utf-8", newline="") as handle:
        candidate_headers = list(csv.DictReader(handle).fieldnames or [])
    _write_csv(candidate_path, candidate_headers, [])

    transition_path = root / "status_transitions.jsonl"
    transitions = [
        json.loads(line)
        for line in transition_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    transitions = [
        item
        for item in transitions
        if item.get("entity_type") not in {"coverage_cell", "cell", "coverage"}
    ]
    transition_path.write_text(
        "".join(json.dumps(item) + "\n" for item in transitions),
        encoding="utf-8",
    )


def _seal_initialized_round(root: Path) -> None:
    report_path = root / "rounds" / "round_000" / "report.md"
    reproduce_path = root / "rounds" / "round_000" / "reproduce_commands.txt"
    report_path.write_text("# Completed synthetic round\n", encoding="utf-8")
    reproduce_path.write_text("synthetic-command --frozen\n", encoding="utf-8")
    manifest_path = root / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["stage_status"] = "completed_as_scoped"
    manifest["round_artifacts"] = [
        {
            "round_id": "round_000",
            "status": "completed",
            "report_path": "rounds/round_000/report.md",
            "reproduce_path": "rounds/round_000/reproduce_commands.txt",
            "sealed_at": "2000-01-01T00:00:00Z",
            "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            "reproduce_sha256": hashlib.sha256(reproduce_path.read_bytes()).hexdigest(),
        }
    ]
    _write_json(manifest_path, manifest)


def _build_fixed_profile_fixture(root: Path) -> None:
    result = initialize_run(root, "fixed_test")
    if result.get("init") != "created":
        raise RuntimeError(f"cannot create fixed fixture: {result}")
    manifest_path = root / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "question": "Does the prespecified synthetic effect meet its rule?",
            "scientific_scope": "one synthetic fixed test",
            "governance_status": "cleared",
        }
    )
    _write_json(manifest_path, manifest)
    _write_json(
        root / "data_versions.json",
        {
            "data_version_set_id": "data-v001",
            "data_versions": [
                {"data_product_id": "D001", "data_version_id": "DV001", "source": "synthetic"}
            ],
        },
    )
    _write_json(
        root / "claim_card.json",
        {
            "claim_id": "CL001",
            "claim": "The prespecified synthetic effect meets the decision rule.",
            "target_population": "synthetic population",
            "analysis_population": "synthetic population",
            "supported_sample_id": "S001",
            "estimand": "synthetic mean difference",
            "minimum_meaningful_effect": 0.1,
            "analysis_or_test": "prespecified synthetic test",
            "decision_rule": "support at or above 0.1 with registered uncertainty",
            "falsifier": "effect below 0.1",
            "specification_timing": "pre_result_frozen",
            "prior_exposure_status": "no_known_exposure",
            "evidence_stage": "exploratory",
            "result_status": "supported",
            "effect_summary": "effect 0.2",
            "uncertainty_summary": "registered interval excludes 0.1",
            "main_caveat": "synthetic fixture",
            "data_version_ids": ["DV001"],
            "completed_as_scoped": True,
        },
    )
    _seal_initialized_round(root)


def _build_adaptive_profile_fixture(root: Path) -> None:
    result = initialize_run(root, "adaptive_search")
    if result.get("init") != "created":
        raise RuntimeError(f"cannot create adaptive fixture: {result}")
    manifest_path = root / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "question": "Which synthetic adaptive candidate meets the rule?",
            "scientific_scope": "one synthetic adaptive selection family",
            "governance_status": "cleared",
            "search_ledger_audited": True,
            "decision_contract_applied": True,
            "decision_status": "leading",
        }
    )
    _write_json(manifest_path, manifest)
    _write_json(
        root / "data_versions.json",
        {
            "data_version_set_id": "data-v001",
            "data_versions": [
                {"data_product_id": "D001", "data_version_id": "DV001", "source": "synthetic"}
            ],
        },
    )
    _write_json(
        root / "decision_contract.json",
        {
            "decision_contract_version": "dc-v001",
            "decision_id": "DEC001",
            "decision_question": "Which adaptive candidate meets the frozen rule?",
            "eligible_candidate_classes": ["model"],
            "eligible_selection_family_ids": ["SF001"],
            "declared_selection_family_ids": ["SF001"],
            "ranked_selection_family_ids": ["SF001"],
            "comparison_key_definition": "population|sample|estimand|quality|stage",
            "comparability_rule": "compare only the registered common key",
            "estimand": "synthetic prediction error",
            "target_population": "synthetic population",
            "analysis_population": "synthetic population",
            "selection_population": "synthetic population",
            "reporting_population": "synthetic population",
            "substantive_eligibility_rule": "candidate addresses the frozen target",
            "measurement_error_policy": "not applicable to this synthetic candidate",
            "transportability_requirement": "same_population",
            "transportability_status": "not_required",
            "evidence_scale_mapping": {
                "scale_relation": "not_applicable",
                "reason": "no screen-to-decision scale transfer",
            },
            "ranking_evidence": {"criterion": "registered prediction error"},
            "decision_rule": "select the unique candidate meeting the threshold",
            "minimum_meaningful_difference": 0.1,
            "complexity_and_data_quality_rule": "use registered quality regime",
            "tie_rule": "report a tie within 0.01",
            "inconclusive_rule": "report inconclusive if uncertainty overlaps threshold",
            "complete_selection_path_method": "end-to-end null calibration",
            "specification_timing": "pre_result_frozen",
            "comparison_groups": [
                {
                    "comparison_group_id": "CG001",
                    "selection_family_ids": ["SF001"],
                    "comparison_key": "synthetic-population|S001|prediction-error|clean|exploratory",
                }
            ],
            "freeze_time": "2000-01-01T00:00:00Z",
            "amendment_policy": "version outcome-driven amendments as adaptive",
        },
    )
    _write_json(
        root / "prior_exposure_audit.json",
        {
            "prior_exposure_audit_version": "pe-v001",
            "audit_status": "complete",
            "prior_exposure_status": "no_known_exposure",
            "sources_checked": ["synthetic records"],
            "overlap_unit": "synthetic observation",
            "overlapping_data": [],
            "prior_analyses": [],
            "prior_parameter_attempts": [],
            "prior_data_looks": [],
            "prior_holdout_exposure": False,
            "unknown_gaps": [],
            "resulting_evidence_stage_limits": [],
            "audited_at": "2000-01-01T00:00:00Z",
            "confirmatory_status": "unrestricted_by_prior_exposure",
            "future_verification_status": "eligible_if_untouched",
            "sample_code_or_skill_change_restores_confirmatory": False,
        },
    )
    ledger_entry = {
        "ledger_entry_id": "L001",
        "candidate_id": "A001",
        "selection_family_id": "SF001",
        "selection_family_version": "sf-v001",
        "decision_influence": True,
        "selection_path_stage": "screen",
        "data_look_id": "look-001",
        "seed_policy_id": "deterministic",
        "data_version_ids": ["DV001"],
        "input_and_code_state": {"data_version_ids": ["DV001"], "code_state": "synthetic"},
        "execution_status": "completed",
        "result_status": "supported",
        "artifact_paths": [],
    }
    (root / "search_ledger.jsonl").write_text(json.dumps(ledger_entry) + "\n", encoding="utf-8")
    _write_json(
        root / "selection_families.json",
        {
            "families": [
                {
                    "selection_family_id": "SF001",
                    "selection_family_version": "sf-v001",
                    "decision_id": "DEC001",
                    "candidate_ids": ["A001"],
                    "selection_path_ledger_entry_ids": ["L001"],
                    "selection_path_complete": True,
                    "inference_method": "end-to-end null calibration",
                    "comparability_status": "comparable_within_family",
                    "comparison_key": "synthetic-population|S001|prediction-error|clean|exploratory",
                    "target_population": "synthetic population",
                    "supported_sample_id": "S001",
                    "estimand": "prediction error",
                    "data_quality_regime": "clean",
                    "evidence_stage": "exploratory",
                    "transportability_requirement": "same_population",
                    "transportability_status": "not_required",
                }
            ],
            "history": [],
        },
    )
    candidate = {
        "candidate_id": "A001",
        "candidate_type": "model",
        "substantive_eligibility": "eligible",
        "mechanism_alignment": "",
        "measurement_error_relevant": "false",
        "measurement_error_sensitivity": "not_required",
        "selection_family_id": "SF001",
        "selection_family_version": "sf-v001",
        "comparison_key": "synthetic-population|S001|prediction-error|clean|exploratory",
        "comparability_status": "comparable_within_family",
        "decision_status": "leading",
        "specification_timing": "pre_result_frozen",
        "prior_exposure_status": "no_known_exposure",
        "confirmatory_status": "unrestricted_by_prior_exposure",
        "future_verification_status": "eligible_if_untouched",
        "evidence_stage": "exploratory",
        "verification_status": "unverified",
        "effect_summary": "registered prediction error improved",
        "uncertainty_summary": "registered interval",
        "support_summary": "supported on registered sample",
        "ledger_entry_ids": "L001",
        "decision_reason": "met frozen rule",
    }
    _write_csv(root / "candidate_registry.csv", sorted(ADAPTIVE_CANDIDATE_REQUIRED_FIELDS), [candidate])
    _seal_initialized_round(root)


def _convert_fixture_to_generic_inventory(root: Path) -> None:
    manifest_path = root / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["saturation_required_sources"] = [
        "candidate_forward",
        "data_product_reverse",
    ]
    _write_json(manifest_path, manifest)
    saturation_path = root / "inventories" / "saturation_audit_v001.json"
    saturation = json.loads(saturation_path.read_text(encoding="utf-8"))
    for audit in saturation.get("audits", []):
        if audit.get("source") == "mechanism_forward":
            audit["source"] = "candidate_forward"
    _write_json(saturation_path, saturation)
    for mechanism_path in sorted((root / "inventories").glob("mechanism_inventory_*.csv")):
        with mechanism_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        generic_rows = []
        for row in rows:
            generic_rows.append(
                {
                    "inventory_version": row["inventory_version"],
                    "candidate_id": row["mechanism_id"],
                    "parent_candidate_id": row["parent_mechanism_id"],
                    "candidate_type": "mechanism",
                    "candidate": row["mechanism"],
                    "distinct_role": row["distinct_pathway"],
                    "inclusion_rationale": row["inclusion_rationale"],
                    "generation_lens": row["generation_lens"],
                    "applicable_regime": row["applicable_regime"],
                    "predicted_signature": row["predicted_signature"],
                    "required_data_products": row["required_data_products"],
                    "data_support_status": row["data_support_status"],
                    "candidate_status": row["mechanism_status"],
                    "specification_timing": row["specification_timing"],
                    "duplicate_of": row["duplicate_of"],
                }
            )
        suffix = mechanism_path.name[len("mechanism_inventory_") :]
        _write_csv(root / "inventories" / f"candidate_inventory_{suffix}", sorted(GENERIC_INVENTORY_REQUIRED_COLUMNS), generic_rows)
        mechanism_path.unlink()
    for coverage_path in sorted((root / "inventories").glob("coverage_matrix_*.csv")):
        with coverage_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        generic_rows = []
        for row in rows:
            row = dict(row)
            row["candidate_id"] = row.pop("mechanism_id")
            row["substantive_eligibility"] = "eligible"
            generic_rows.append(row)
        fields = sorted(set(GENERIC_COVERAGE_REQUIRED_COLUMNS) | {"covered_by_cell_id"})
        _write_csv(coverage_path, fields, generic_rows)
    registry_path = root / "candidate_registry.csv"
    with registry_path.open("r", encoding="utf-8", newline="") as handle:
        registry = list(csv.DictReader(handle))
    for row in registry:
        row["candidate_id"] = row.pop("mechanism_id")
        row["candidate_type"] = "mechanism"
        row["substantive_eligibility"] = "eligible"
    fields = sorted((CANDIDATE_REQUIRED_FIELDS - {"mechanism_id"}) | V15_COVERAGE_CANDIDATE_FIELDS)
    _write_csv(registry_path, fields, registry)


def _convert_self_test_fixture_to_v14(root: Path) -> None:
    manifest_path = root / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifact_schema_version"] = "1.4.0"
    for field in ("research_profile", "profile_history", "stage_status", "round_artifacts"):
        manifest.pop(field, None)
    _write_json(manifest_path, manifest)


def _downgrade_self_test_fixture_to_legacy(root: Path) -> None:
    manifest_path = root / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("artifact_schema_version", None)
    _write_json(manifest_path, manifest)

    for path in (root / "inventories").glob("coverage_matrix_*.csv"):
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        fields = [
            field
            for field in rows[0]
            if field not in STRICT_COVERAGE_REQUIRED_FIELDS
        ]
        _write_csv(
            path,
            fields,
            [{field: row[field] for field in fields} for row in rows],
        )

    contract_path = root / "decision_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    for field in STRICT_DECISION_CONTRACT_FIELDS:
        contract.pop(field, None)
    _write_json(contract_path, contract)

    families_path = root / "selection_families.json"
    families = json.loads(families_path.read_text(encoding="utf-8"))
    for record in families["families"] + families["history"]:
        for field in STRICT_SELECTION_FAMILY_FIELDS:
            record.pop(field, None)
    _write_json(families_path, families)


def _run_hardening_self_tests(temp_root: Path) -> dict[str, bool]:
    """Exercise profile-boundary and preservation checks added in schema 1.5."""

    results: dict[str, bool] = {}

    future_root = temp_root / "unsupported-future-schema-run"
    future_root.mkdir()
    _build_self_test_fixture(future_root)
    future_manifest_path = future_root / "run_manifest.json"
    future_manifest = json.loads(future_manifest_path.read_text(encoding="utf-8"))
    future_manifest["artifact_schema_version"] = "9.0.0"
    _write_json(future_manifest_path, future_manifest)
    future_report = validate_run(future_root)
    results["unsupported_future_schema"] = (
        not future_report["valid"]
        and any(
            item["code"] == "unsupported_artifact_schema_version"
            for item in future_report["errors"]
        )
    )

    hidden_root = temp_root / "adaptive-hidden-coverage-run"
    _build_adaptive_profile_fixture(hidden_root)
    (hidden_root / "inventories").mkdir()
    (hidden_root / "inventories" / "coverage_matrix_malformed.csv").write_text(
        "not,a,valid,coverage,matrix\n", encoding="utf-8"
    )
    hidden_report = validate_run(hidden_root)
    results["adaptive_hidden_coverage_artifact"] = (
        not hidden_report["valid"]
        and any(
            item["code"] == "profile_underfit_coverage_evidence"
            for item in hidden_report["errors"]
        )
    )

    behavior_root = temp_root / "adaptive-hidden-coverage-behavior-run"
    _build_adaptive_profile_fixture(behavior_root)
    behavior_ledger_path = behavior_root / "search_ledger.jsonl"
    behavior_entry = json.loads(behavior_ledger_path.read_text(encoding="utf-8"))
    behavior_entry["coverage_cell_id"] = "C001"
    behavior_ledger_path.write_text(json.dumps(behavior_entry) + "\n", encoding="utf-8")
    behavior_report = validate_run(behavior_root)
    results["adaptive_hidden_coverage_behavior"] = (
        not behavior_report["valid"]
        and any(
            item["code"] == "profile_underfit_coverage_behavior"
            for item in behavior_report["errors"]
        )
    )

    def mutate_adaptive_candidate(
        root: Path, updates: Mapping[str, str]
    ) -> dict[str, Any]:
        candidate_path = root / "candidate_registry.csv"
        with candidate_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
            fields = list(rows[0])
        rows[0].update(updates)
        _write_csv(candidate_path, fields, rows)
        return validate_run(root)

    alignment_root = temp_root / "nonmechanism-alignment-run"
    _build_adaptive_profile_fixture(alignment_root)
    alignment_report = mutate_adaptive_candidate(
        alignment_root, {"mechanism_alignment": "direct"}
    )
    results["alignment_only_for_mechanisms"] = (
        not alignment_report["valid"]
        and any(
            item["code"] == "candidate_type_alignment_mismatch"
            for item in alignment_report["errors"]
        )
    )

    mechanism_na_root = temp_root / "mechanism-not-applicable-alignment-run"
    _build_adaptive_profile_fixture(mechanism_na_root)
    mechanism_na_report = mutate_adaptive_candidate(
        mechanism_na_root,
        {
            "candidate_type": "mechanism",
            "mechanism_alignment": "not_applicable",
        },
    )
    results["mechanism_alignment_not_applicable_rejected"] = (
        not mechanism_na_report["valid"]
        and any(
            item["code"] == "candidate_type_alignment_mismatch"
            for item in mechanism_na_report["errors"]
        )
    )

    coverage_alignment_root = temp_root / "coverage-nonmechanism-alignment-run"
    coverage_alignment_root.mkdir()
    _build_self_test_fixture(coverage_alignment_root)
    _convert_fixture_to_generic_inventory(coverage_alignment_root)
    inventory_path = (
        coverage_alignment_root
        / "inventories"
        / "candidate_inventory_v001.csv"
    )
    with inventory_path.open("r", encoding="utf-8", newline="") as handle:
        inventory_rows = list(csv.DictReader(handle))
        inventory_fields = list(inventory_rows[0])
    inventory_rows[0]["candidate_type"] = "model"
    _write_csv(inventory_path, inventory_fields, inventory_rows)
    registry_path = coverage_alignment_root / "candidate_registry.csv"
    with registry_path.open("r", encoding="utf-8", newline="") as handle:
        registry_rows = list(csv.DictReader(handle))
        registry_fields = list(registry_rows[0])
    registry_rows[0]["candidate_type"] = "model"
    _write_csv(registry_path, registry_fields, registry_rows)
    coverage_alignment_report = validate_run(coverage_alignment_root)
    results["coverage_alignment_only_for_mechanisms"] = (
        not coverage_alignment_report["valid"]
        and any(
            item["code"] == "candidate_type_alignment_mismatch"
            for item in coverage_alignment_report["errors"]
        )
    )

    coverage_mechanism_na_root = temp_root / "coverage-mechanism-not-applicable-run"
    coverage_mechanism_na_root.mkdir()
    _build_self_test_fixture(coverage_mechanism_na_root)
    _convert_fixture_to_generic_inventory(coverage_mechanism_na_root)
    coverage_mechanism_na_path = (
        coverage_mechanism_na_root
        / "inventories"
        / "coverage_matrix_v001.csv"
    )
    with coverage_mechanism_na_path.open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        coverage_mechanism_na_rows = list(csv.DictReader(handle))
        coverage_mechanism_na_fields = list(coverage_mechanism_na_rows[0])
    coverage_mechanism_na_rows[0]["mechanism_alignment"] = "not_applicable"
    _write_csv(
        coverage_mechanism_na_path,
        coverage_mechanism_na_fields,
        coverage_mechanism_na_rows,
    )
    coverage_mechanism_na_report = validate_run(coverage_mechanism_na_root)
    results["coverage_mechanism_alignment_not_applicable_rejected"] = (
        not coverage_mechanism_na_report["valid"]
        and any(
            item["code"] == "candidate_type_alignment_mismatch"
            for item in coverage_mechanism_na_report["errors"]
        )
    )

    irrelevant_error_root = temp_root / "irrelevant-measurement-error-run"
    _build_adaptive_profile_fixture(irrelevant_error_root)
    irrelevant_error_report = mutate_adaptive_candidate(
        irrelevant_error_root,
        {
            "measurement_error_relevant": "false",
            "measurement_error_sensitivity": "passed",
        },
    )
    results["irrelevant_measurement_error_semantics"] = (
        not irrelevant_error_report["valid"]
        and any(
            item["code"] == "measurement_error_relevance_mismatch"
            for item in irrelevant_error_report["errors"]
        )
    )

    collision_root = temp_root / "output-collision-run"
    _build_fixed_profile_fixture(collision_root)
    collision_report = validate_run(collision_root)
    sealed_report = collision_root / "rounds" / "round_000" / "report.md"
    results["output_collision"] = (
        _output_input_collision(collision_root, sealed_report, collision_report)
        == "rounds/round_000/report.md"
        and _output_input_collision(
            collision_root,
            collision_root / "consistency_report.json",
            collision_report,
        )
        is None
    )

    regression_root = temp_root / "fixed-completion-regression-run"
    _build_fixed_profile_fixture(regression_root)
    regression_manifest_path = regression_root / "run_manifest.json"
    regression_manifest = json.loads(
        regression_manifest_path.read_text(encoding="utf-8")
    )
    regression_manifest["stage_status"] = "in_progress"
    regression_manifest["round_artifacts"][0] = {
        "round_id": "round_000",
        "status": "planned",
        "report_path": "rounds/round_000/report.md",
        "reproduce_path": "rounds/round_000/reproduce_commands.txt",
    }
    _write_json(regression_manifest_path, regression_manifest)
    regression_report = validate_run(regression_root)
    results["fixed_completion_one_way"] = (
        not regression_report["valid"]
        and any(
            item["code"] == "fixed_completion_state_regression"
            for item in regression_report["errors"]
        )
    )

    unordered_root = temp_root / "unordered-profile-history-run"
    _build_adaptive_profile_fixture(unordered_root)
    unordered_manifest_path = unordered_root / "run_manifest.json"
    unordered_manifest = json.loads(unordered_manifest_path.read_text(encoding="utf-8"))
    unordered_manifest["profile_history"] = [
        {"profile": "adaptive_search", "started_at": "2001-01-01T00:00:00Z"},
        {"profile": "adaptive_search", "started_at": "2000-01-01T00:00:00Z"},
    ]
    _write_json(unordered_manifest_path, unordered_manifest)
    unordered_report = validate_run(unordered_root)
    results["profile_history_timestamp_order"] = (
        not unordered_report["valid"]
        and any(
            item["code"] == "profile_history_timestamp_order"
            for item in unordered_report["errors"]
        )
    )

    symlink_root = temp_root / "symlink-upgrade-snapshot-run"
    _build_adaptive_profile_fixture(symlink_root)
    external_snapshot = temp_root / "external-upgrade-snapshot.json"
    external_snapshot.write_text("{}\n", encoding="utf-8")
    symlink_path = symlink_root / "preservation-snapshot-link.json"
    symlink_path.symlink_to(external_snapshot)
    symlink_manifest_path = symlink_root / "run_manifest.json"
    symlink_manifest = json.loads(symlink_manifest_path.read_text(encoding="utf-8"))
    symlink_manifest["profile_history"] = [
        {"profile": "fixed_test", "started_at": "1999-01-01T00:00:00Z"},
        {
            "profile": "adaptive_search",
            "started_at": "2000-01-01T00:00:00Z",
            "preservation_snapshot_path": "preservation-snapshot-link.json",
            "preservation_snapshot_sha256": hashlib.sha256(
                external_snapshot.read_bytes()
            ).hexdigest(),
        },
    ]
    _write_json(symlink_manifest_path, symlink_manifest)
    symlink_report = validate_run(symlink_root)
    results["upgrade_snapshot_rejects_symlink"] = (
        not symlink_report["valid"]
        and any(
            item["code"] == "symlink_artifact_path"
            for item in symlink_report["errors"]
        )
    )

    source_root = temp_root / "upgrade-snapshot-source-fixed-run"
    _build_fixed_profile_fixture(source_root)
    snapshot_result = create_upgrade_snapshot(source_root, "adaptive_search")
    target_root = temp_root / "valid-hash-bound-upgrade-run"
    _build_adaptive_profile_fixture(target_root)
    if snapshot_result.get("snapshot") == "created":
        source_history = source_root / "history"
        for source in sorted(source_history.rglob("*")):
            relative = source.relative_to(source_root)
            destination = target_root / relative
            if source.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
        target_manifest_path = target_root / "run_manifest.json"
        target_manifest = json.loads(target_manifest_path.read_text(encoding="utf-8"))
        source_manifest = json.loads(
            (source_root / "run_manifest.json").read_text(encoding="utf-8")
        )
        target_manifest["profile_history"] = [
            source_manifest["profile_history"][0],
            snapshot_result["next_profile_history_entry"],
        ]
        _write_json(target_manifest_path, target_manifest)
        upgrade_report = validate_run(target_root)
        results["hash_bound_upgrade_snapshot_positive"] = upgrade_report["valid"]

        snapshot_relative = Path(
            snapshot_result["next_profile_history_entry"][
                "preservation_snapshot_path"
            ]
        )
        target_snapshot_path = target_root / snapshot_relative
        target_snapshot = json.loads(
            target_snapshot_path.read_text(encoding="utf-8")
        )
        target_snapshot["artifacts"] = [
            artifact
            for artifact in target_snapshot["artifacts"]
            if artifact["logical_path"]
            != "rounds/round_000/report.md"
        ]
        _write_json(target_snapshot_path, target_snapshot)
        target_manifest = json.loads(target_manifest_path.read_text(encoding="utf-8"))
        target_manifest["profile_history"][-1][
            "preservation_snapshot_sha256"
        ] = hashlib.sha256(target_snapshot_path.read_bytes()).hexdigest()
        _write_json(target_manifest_path, target_manifest)
        missing_round_report = validate_run(target_root)
        results["upgrade_snapshot_requires_round_evidence"] = (
            not missing_round_report["valid"]
            and any(
                item["code"] == "incomplete_profile_upgrade_round_snapshot"
                for item in missing_round_report["errors"]
            )
        )
    else:
        results["hash_bound_upgrade_snapshot_positive"] = False
        results["upgrade_snapshot_requires_round_evidence"] = False

    generic_root = temp_root / "generic-completion-diagnostics-run"
    generic_root.mkdir()
    _build_self_test_fixture(generic_root)
    _convert_self_test_fixture_to_zero_coverage(
        generic_root,
        data_support_status="supported",
        mechanism_status="active",
    )
    _convert_fixture_to_generic_inventory(generic_root)
    generic_report = validate_run(generic_root)
    generic_errors = [
        item
        for item in generic_report["errors"]
        if item["code"] == "eligible_candidate_without_coverage"
    ]
    results["generic_completion_diagnostics"] = (
        not generic_report["valid"]
        and bool(generic_errors)
        and all("mechanism" not in item["message"].lower() for item in generic_errors)
    )

    return results


def run_self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="scientific-autoresearch-validator-") as temp_dir:
        temp_root = Path(temp_dir)

        valid_root = temp_root / "valid-run"
        valid_root.mkdir()
        _build_self_test_fixture(valid_root)
        valid_report = validate_run(valid_root)
        if not valid_report["valid"]:
            return {
                "self_test": "failed",
                "reason": "valid fixture was rejected",
                "valid_fixture_report": valid_report,
            }

        generic_root = temp_root / "valid-generic-coverage-run"
        generic_root.mkdir()
        _build_self_test_fixture(generic_root)
        _convert_fixture_to_generic_inventory(generic_root)
        generic_report = validate_run(generic_root)
        generic_valid = generic_report["valid"]

        fixed_root = temp_root / "valid-fixed-run"
        _build_fixed_profile_fixture(fixed_root)
        fixed_report = validate_run(fixed_root)
        fixed_valid = fixed_report["valid"]

        adaptive_root = temp_root / "valid-adaptive-run"
        _build_adaptive_profile_fixture(adaptive_root)
        adaptive_report = validate_run(adaptive_root)
        adaptive_valid = adaptive_report["valid"]

        v14_root = temp_root / "valid-v14-run"
        v14_root.mkdir()
        _build_self_test_fixture(v14_root)
        _convert_self_test_fixture_to_v14(v14_root)
        v14_report = validate_run(v14_root)
        v14_valid = v14_report["valid"] and v14_report["warning_count"] == 0

        fixed_underfit_root = temp_root / "fixed-underfit-run"
        _build_fixed_profile_fixture(fixed_underfit_root)
        _write_json(fixed_underfit_root / "decision_contract.json", {"unexpected": True})
        fixed_underfit_report = validate_run(fixed_underfit_root)
        fixed_underfit_codes = {
            item["code"] for item in fixed_underfit_report["errors"]
        }
        fixed_underfit_detected = (
            "profile_underfit_adaptive_artifacts" in fixed_underfit_codes
            and not fixed_underfit_report["valid"]
        )

        upgrade_root = temp_root / "unattested-profile-upgrade-run"
        _build_adaptive_profile_fixture(upgrade_root)
        upgrade_manifest_path = upgrade_root / "run_manifest.json"
        upgrade_manifest = json.loads(upgrade_manifest_path.read_text(encoding="utf-8"))
        upgrade_manifest["profile_history"] = [
            {"profile": "fixed_test", "started_at": "1999-01-01T00:00:00Z"},
            {"profile": "adaptive_search", "started_at": "2000-01-01T00:00:00Z"},
        ]
        _write_json(upgrade_manifest_path, upgrade_manifest)
        upgrade_report = validate_run(upgrade_root)
        upgrade_codes = {item["code"] for item in upgrade_report["errors"]}
        upgrade_preservation_detected = {
            "profile_upgrade_history_not_preserved",
            "profile_upgrade_exposure_not_preserved",
        }.issubset(upgrade_codes) and not upgrade_report["valid"]

        upgrade_missing_claim_root = temp_root / "upgrade-missing-fixed-claim-run"
        _build_adaptive_profile_fixture(upgrade_missing_claim_root)
        missing_claim_manifest_path = upgrade_missing_claim_root / "run_manifest.json"
        missing_claim_manifest = json.loads(missing_claim_manifest_path.read_text(encoding="utf-8"))
        missing_claim_manifest["profile_history"] = [
            {"profile": "fixed_test", "started_at": "1999-01-01T00:00:00Z"},
            {
                "profile": "adaptive_search",
                "started_at": "2000-01-01T00:00:00Z",
                "history_preserved": True,
                "prior_exposure_preserved": True,
            },
        ]
        _write_json(missing_claim_manifest_path, missing_claim_manifest)
        upgrade_missing_claim_report = validate_run(upgrade_missing_claim_root)
        upgrade_missing_claim_codes = {
            item["code"] for item in upgrade_missing_claim_report["errors"]
        }
        upgrade_claim_preservation_detected = (
            "profile_upgrade_fixed_claim_not_preserved"
            in upgrade_missing_claim_codes
            and not upgrade_missing_claim_report["valid"]
        )

        round_hash_root = temp_root / "tampered-sealed-round-run"
        _build_fixed_profile_fixture(round_hash_root)
        (round_hash_root / "rounds" / "round_000" / "report.md").write_text(
            "tampered after sealing\n", encoding="utf-8"
        )
        round_hash_report = validate_run(round_hash_root)
        round_hash_codes = {item["code"] for item in round_hash_report["errors"]}
        round_hash_detected = (
            "sealed_round_hash_mismatch" in round_hash_codes
            and not round_hash_report["valid"]
        )

        adaptive_saturation_root = temp_root / "adaptive-saturation-claim-run"
        _build_adaptive_profile_fixture(adaptive_saturation_root)
        adaptive_saturation_path = adaptive_saturation_root / "run_manifest.json"
        adaptive_saturation_manifest = json.loads(adaptive_saturation_path.read_text(encoding="utf-8"))
        adaptive_saturation_manifest["search_status"] = "complete_within_scope"
        adaptive_saturation_manifest["inventory_saturated"] = True
        _write_json(adaptive_saturation_path, adaptive_saturation_manifest)
        adaptive_saturation_report = validate_run(adaptive_saturation_root)
        adaptive_saturation_codes = {
            item["code"] for item in adaptive_saturation_report["errors"]
        }
        stage_vs_saturation_detected = (
            fixed_valid
            and adaptive_valid
            and "profile_underfit_saturation_claim" in adaptive_saturation_codes
            and not adaptive_saturation_report["valid"]
        )

        not_applicable_scale_root = temp_root / "not-applicable-scale-run"
        not_applicable_scale_root.mkdir()
        _build_self_test_fixture(not_applicable_scale_root)
        not_applicable_scale_path = (
            not_applicable_scale_root / "decision_contract.json"
        )
        not_applicable_scale_contract = json.loads(
            not_applicable_scale_path.read_text(encoding="utf-8")
        )
        not_applicable_scale_contract["evidence_scale_mapping"] = {
            "scale_relation": "not_applicable",
            "reason": "no selection-influencing screen-to-decision transfer",
        }
        _write_json(not_applicable_scale_path, not_applicable_scale_contract)
        not_applicable_scale_report = validate_run(not_applicable_scale_root)
        not_applicable_scale_valid = not_applicable_scale_report["valid"]

        distinct_screening_root = temp_root / "distinct-screening-scope-run"
        distinct_screening_root.mkdir()
        _build_self_test_fixture(distinct_screening_root)
        distinct_screening_path = distinct_screening_root / "decision_contract.json"
        distinct_screening_contract = json.loads(
            distinct_screening_path.read_text(encoding="utf-8")
        )
        distinct_first_mapping = distinct_screening_contract[
            "evidence_scale_mapping"
        ][0]
        distinct_second_mapping = dict(distinct_first_mapping)
        distinct_second_mapping["mapping_id"] = "ESM002"
        distinct_second_mapping["screening_statistic"] = (
            "secondary registered synthetic screen score"
        )
        distinct_screening_contract["evidence_scale_mapping"].append(
            distinct_second_mapping
        )
        _write_json(distinct_screening_path, distinct_screening_contract)
        distinct_screening_report = validate_run(distinct_screening_root)
        distinct_screening_valid = distinct_screening_report["valid"]

        zero_eligible_reports: dict[str, dict[str, Any]] = {}
        zero_eligible_cases = {
            "diagnostic_only": ("diagnostic_only", "needs_data"),
            "unsupported": ("unsupported", "needs_data"),
            "not_applicable": ("not_applicable", "needs_data"),
            "support_limited": ("support_limited", "needs_data"),
        }
        for case, (data_support, mechanism_status) in zero_eligible_cases.items():
            zero_eligible_root = temp_root / f"zero-eligible-{case}-run"
            zero_eligible_root.mkdir()
            _build_self_test_fixture(zero_eligible_root)
            _convert_self_test_fixture_to_zero_coverage(
                zero_eligible_root,
                data_support_status=data_support,
                mechanism_status=mechanism_status,
            )
            zero_eligible_reports[case] = validate_run(zero_eligible_root)
        zero_eligible_completion_valid = all(
            report["valid"] for report in zero_eligible_reports.values()
        )

        eligible_without_coverage_root = (
            temp_root / "eligible-mechanism-without-coverage-run"
        )
        eligible_without_coverage_root.mkdir()
        _build_self_test_fixture(eligible_without_coverage_root)
        _convert_self_test_fixture_to_zero_coverage(
            eligible_without_coverage_root,
            data_support_status="supported",
            mechanism_status="weakened",
        )
        eligible_without_coverage_report = validate_run(
            eligible_without_coverage_root
        )
        eligible_without_coverage_codes = {
            item["code"] for item in eligible_without_coverage_report["errors"]
        }
        eligible_without_coverage_detected = (
            "eligible_mechanism_without_coverage"
            in eligible_without_coverage_codes
            and not eligible_without_coverage_report["valid"]
        )

        active_nonsupported_reports: dict[str, dict[str, Any]] = {}
        for data_support in (
            "support_limited",
            "diagnostic_only",
            "unsupported",
            "not_applicable",
        ):
            active_nonsupported_root = (
                temp_root / f"active-{data_support}-without-coverage-run"
            )
            active_nonsupported_root.mkdir()
            _build_self_test_fixture(active_nonsupported_root)
            _convert_self_test_fixture_to_zero_coverage(
                active_nonsupported_root,
                data_support_status=data_support,
                mechanism_status="active",
            )
            active_nonsupported_reports[data_support] = validate_run(
                active_nonsupported_root
            )
        active_nonsupported_detected = all(
            not report["valid"]
            and any(
                item["code"] == "eligible_mechanism_without_coverage"
                for item in report["errors"]
            )
            for report in active_nonsupported_reports.values()
        )
        active_nonsupported_codes = {
            item["code"]
            for report in active_nonsupported_reports.values()
            for item in report["errors"]
        }

        draft_zero_cell_root = temp_root / "draft-zero-cell-complete-run"
        draft_zero_cell_root.mkdir()
        _build_self_test_fixture(draft_zero_cell_root)
        _convert_self_test_fixture_to_zero_coverage(
            draft_zero_cell_root,
            data_support_status="diagnostic_only",
        )
        draft_manifest_path = draft_zero_cell_root / "run_manifest.json"
        draft_manifest = json.loads(
            draft_manifest_path.read_text(encoding="utf-8")
        )
        draft_manifest.update(
            {
                "inventory_status": "draft",
                "inventory_saturated": False,
                "coverage_complete": True,
                "search_status": "inventory_building",
                "decision_contract_applied": False,
                "decision_status": "not_evaluated",
            }
        )
        _write_json(draft_manifest_path, draft_manifest)
        draft_zero_cell_report = validate_run(draft_zero_cell_root)
        draft_zero_cell_codes = {
            item["code"] for item in draft_zero_cell_report["errors"]
        }
        draft_zero_cell_detected = (
            "coverage_completion_mismatch" in draft_zero_cell_codes
            and not draft_zero_cell_report["valid"]
        )

        invalid_data_support_reports: dict[str, dict[str, Any]] = {}
        for invalid_status in ("available", "testable_current_data", "suported"):
            invalid_support_root = temp_root / f"invalid-support-{invalid_status}-run"
            invalid_support_root.mkdir()
            _build_self_test_fixture(invalid_support_root)
            _convert_self_test_fixture_to_zero_coverage(
                invalid_support_root,
                data_support_status=invalid_status,
            )
            invalid_data_support_reports[invalid_status] = validate_run(
                invalid_support_root
            )
        invalid_data_support_detected = all(
            not report["valid"]
            and any(
                item["code"] == "invalid_status"
                and "data_support_status" in item["message"]
                for item in report["errors"]
            )
            for report in invalid_data_support_reports.values()
        )
        invalid_data_support_codes = {
            item["code"]
            for report in invalid_data_support_reports.values()
            for item in report["errors"]
        }

        human_judgment_root = temp_root / "human-judgment-completion-run"
        human_judgment_root.mkdir()
        _build_self_test_fixture(human_judgment_root)
        _convert_self_test_fixture_to_zero_coverage(
            human_judgment_root,
            data_support_status="support_limited",
            mechanism_status="needs_human_judgment",
        )
        human_judgment_report = validate_run(human_judgment_root)
        human_judgment_codes = {
            item["code"] for item in human_judgment_report["errors"]
        }
        human_judgment_detected = (
            "unresolved_human_judgment_at_completion" in human_judgment_codes
            and not human_judgment_report["valid"]
        )

        unassessed_needs_data_root = (
            temp_root / "unassessed-needs-data-completion-run"
        )
        unassessed_needs_data_root.mkdir()
        _build_self_test_fixture(unassessed_needs_data_root)
        _convert_self_test_fixture_to_zero_coverage(
            unassessed_needs_data_root,
            data_support_status="not_assessed",
            mechanism_status="needs_data",
        )
        unassessed_needs_data_report = validate_run(
            unassessed_needs_data_root
        )
        unassessed_needs_data_codes = {
            item["code"] for item in unassessed_needs_data_report["errors"]
        }
        unassessed_needs_data_detected = (
            {
                "invalid_mechanism_data_support_pair",
                "unresolved_data_support_at_completion",
            }.issubset(unassessed_needs_data_codes)
            and not unassessed_needs_data_report["valid"]
        )

        rejected_with_history_root = temp_root / "rejected-with-history-run"
        rejected_with_history_root.mkdir()
        _build_self_test_fixture(rejected_with_history_root)
        _convert_self_test_fixture_to_zero_coverage(
            rejected_with_history_root,
            data_support_status="supported",
            mechanism_status="rejected",
        )
        rejected_evidence_path = (
            rejected_with_history_root
            / "inventories"
            / "coverage_matrix_v000.csv"
        )
        with rejected_evidence_path.open(
            "r", encoding="utf-8", newline=""
        ) as handle:
            rejected_evidence_rows = list(csv.DictReader(handle))
        rejected_evidence_rows[0]["coverage_status"] = "tested_valid"
        rejected_evidence_rows[0]["execution_status"] = "completed"
        rejected_evidence_rows[0]["result_status"] = "null"
        _write_csv(
            rejected_evidence_path,
            list(rejected_evidence_rows[0]),
            rejected_evidence_rows,
        )
        rejected_with_history_report = validate_run(rejected_with_history_root)
        rejected_with_history_valid = rejected_with_history_report["valid"]

        rejected_without_evidence_reports: dict[str, dict[str, Any]] = {}
        for status in ("eligible_untested", "not_testable_current_data"):
            rejected_without_evidence_root = (
                temp_root / f"rejected-with-{status}-only-run"
            )
            rejected_without_evidence_root.mkdir()
            _build_self_test_fixture(rejected_without_evidence_root)
            _convert_self_test_fixture_to_zero_coverage(
                rejected_without_evidence_root,
                data_support_status="supported",
                mechanism_status="rejected",
            )
            rejected_history_coverage_path = (
                rejected_without_evidence_root
                / "inventories"
                / "coverage_matrix_v000.csv"
            )
            with rejected_history_coverage_path.open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                rejected_history_rows = list(csv.DictReader(handle))
            rejected_history_rows[0]["coverage_status"] = status
            _write_csv(
                rejected_history_coverage_path,
                list(rejected_history_rows[0]),
                rejected_history_rows,
            )
            rejected_without_evidence_reports[status] = validate_run(
                rejected_without_evidence_root
            )
        rejected_without_evidence_detected = all(
            not report["valid"]
            and any(
                item["code"]
                == "rejected_mechanism_without_coverage_history"
                for item in report["errors"]
            )
            for report in rejected_without_evidence_reports.values()
        )
        rejected_without_evidence_codes = {
            item["code"]
            for report in rejected_without_evidence_reports.values()
            for item in report["errors"]
        }

        legacy_root = temp_root / "legacy-run"
        legacy_root.mkdir()
        _build_self_test_fixture(legacy_root)
        _downgrade_self_test_fixture_to_legacy(legacy_root)
        legacy_report = validate_run(legacy_root)
        legacy_valid = (
            legacy_report["valid"]
            and legacy_report["warning_count"] == 1
            and [item["code"] for item in legacy_report["warnings"]]
            == ["legacy_artifact_schema"]
        )

        init_root = temp_root / "initialized-run"
        init_report = initialize_run(init_root, "coverage_search")
        initialized_files = {
            str(path.relative_to(init_root))
            for path in init_root.rglob("*")
            if path.is_file()
        }

        def initialized_header(relative: str) -> set[str]:
            with (init_root / relative).open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                return set(next(csv.reader(handle)))

        init_headers_valid = (
            initialized_header("inventories/candidate_inventory_v001.csv")
            == GENERIC_INVENTORY_REQUIRED_COLUMNS
            and initialized_header("inventories/coverage_matrix_v001.csv")
            == GENERIC_COVERAGE_REQUIRED_COLUMNS
            and initialized_header("candidate_registry.csv")
            == (
                (CANDIDATE_REQUIRED_FIELDS - {"mechanism_id"})
                | V15_COVERAGE_CANDIDATE_FIELDS
            )
            and initialized_header("execution_queue.csv")
            == set(EXECUTION_QUEUE_COLUMN_ALIASES)
            and initialized_header("rounds/round_000/summary.csv")
            == set(GENERIC_ROUND_SUMMARY_COLUMNS)
        )
        init_validation_report = validate_run(init_root)
        init_validation_codes = {
            item["code"] for item in init_validation_report["errors"]
        }
        init_consistency_placeholder = json.loads(
            (init_root / "consistency_report.json").read_text(encoding="utf-8")
        )
        init_structure_valid = (
            init_report.get("init") == "created"
            and initialized_files == COVERAGE_INIT_FILES
            and init_headers_valid
            and not init_validation_report["valid"]
            and "missing_required_field" in init_validation_codes
            and init_consistency_placeholder.get("valid") is False
            and not init_validation_codes
            & {
                "missing_artifact",
                "active_version_artifact_missing",
                "missing_snapshot_columns",
                "missing_candidate_columns",
                "invalid_artifact_schema_version",
                "coverage_completion_mismatch",
            }
        )
        manifest_before_refusal = (init_root / "run_manifest.json").read_text(
            encoding="utf-8"
        )
        init_refusal_report = initialize_run(init_root, "coverage_search")
        init_file_target = temp_root / "existing-init-target"
        init_file_target.write_text("preserve me\n", encoding="utf-8")
        init_file_refusal_report = initialize_run(init_file_target, "coverage_search")
        init_overwrite_refused = (
            init_refusal_report.get("init") == "refused"
            and (init_root / "run_manifest.json").read_text(encoding="utf-8")
            == manifest_before_refusal
            and {
                str(path.relative_to(init_root))
                for path in init_root.rglob("*")
                if path.is_file()
            }
            == initialized_files
            and init_file_refusal_report.get("init") == "refused"
            and init_file_target.read_text(encoding="utf-8") == "preserve me\n"
        )

        family_root = temp_root / "broken-family-run"
        family_root.mkdir()
        _build_self_test_fixture(family_root)
        coverage_path = family_root / "inventories" / "coverage_matrix_v001.csv"
        rows = list(csv.DictReader(coverage_path.open("r", encoding="utf-8", newline="")))
        rows[0]["selection_family_id"] = "MISSING_FAMILY"
        _write_csv(coverage_path, list(rows[0].keys()), rows)
        family_report = validate_run(family_root)
        family_codes = {item["code"] for item in family_report["errors"]}
        family_detected = (
            "unknown_coverage_family_version" in family_codes
            and not family_report["valid"]
        )

        transition_root = temp_root / "illegal-transition-run"
        transition_root.mkdir()
        _build_self_test_fixture(transition_root)
        transition_path = transition_root / "status_transitions.jsonl"
        transitions = [
            json.loads(line)
            for line in transition_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        transitions[0]["from_status"] = "draft"
        transitions[0]["to_status"] = "saturated"
        transition_path.write_text(
            "".join(json.dumps(item) + "\n" for item in transitions),
            encoding="utf-8",
        )
        transition_report = validate_run(transition_root)
        transition_codes = {item["code"] for item in transition_report["errors"]}
        transition_detected = (
            "illegal_status_transition" in transition_codes and not transition_report["valid"]
        )

        strict_transition_root = temp_root / "strict-transition-fields-run"
        strict_transition_root.mkdir()
        _build_self_test_fixture(strict_transition_root)
        strict_transition_path = strict_transition_root / "status_transitions.jsonl"
        strict_transitions = [
            json.loads(line)
            for line in strict_transition_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        strict_transition_faults = (
            (
                "data_support_status",
                "mechanism",
                "M001",
                "supported",
                "support_limited",
            ),
            (
                "mechanism_alignment",
                "coverage_cell",
                "C001",
                "direct",
                "diagnostic_only",
            ),
            (
                "measurement_error_sensitivity",
                "coverage_cell",
                "C001",
                "passed",
                "planned",
            ),
            (
                "transportability_requirement",
                "selection_family",
                "SF001",
                "same_population",
                "validation_required",
            ),
            (
                "transportability_status",
                "selection_family",
                "SF001",
                "passed",
                "planned",
            ),
        )
        for index, (
            field,
            entity_type,
            entity_id,
            old,
            new,
        ) in enumerate(strict_transition_faults, start=1):
            strict_transitions.append(
                {
                    "transition_id": f"STRICT-T{index:03d}",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "status_field": field,
                    "from_status": old,
                    "to_status": new,
                    "inventory_version": "v001",
                    "round_id": "round_001",
                    "changed_at": "2000-01-01T00:00:00Z",
                    "evidence": "injected illegal strict transition",
                    "evidence_paths": [],
                }
            )
        strict_transition_path.write_text(
            "".join(json.dumps(item) + "\n" for item in strict_transitions),
            encoding="utf-8",
        )
        strict_transition_report = validate_run(strict_transition_root)
        strict_transition_codes = {
            item["code"] for item in strict_transition_report["errors"]
        }
        strict_transition_messages = " ".join(
            item["message"]
            for item in strict_transition_report["errors"]
            if item["code"] == "illegal_status_transition"
        )
        strict_transition_warning_codes = {
            item["code"] for item in strict_transition_report["warnings"]
        }
        strict_transition_detected = (
            all(
                field in strict_transition_messages
                for field in STRICT_TRANSITION_STATUS_FIELDS
            )
            and "unknown_transition_field" not in strict_transition_warning_codes
            and not strict_transition_report["valid"]
        )

        family_transition_mismatch_root = (
            temp_root / "family-transition-final-state-mismatch-run"
        )
        family_transition_mismatch_root.mkdir()
        _build_self_test_fixture(family_transition_mismatch_root)
        family_transition_families_path = (
            family_transition_mismatch_root / "selection_families.json"
        )
        family_transition_families = json.loads(
            family_transition_families_path.read_text(encoding="utf-8")
        )
        family_transition_families["families"][0][
            "transportability_requirement"
        ] = "validation_required"
        family_transition_families["families"][0][
            "transportability_status"
        ] = "planned"
        _write_json(
            family_transition_families_path, family_transition_families
        )
        family_transition_path = (
            family_transition_mismatch_root / "status_transitions.jsonl"
        )
        family_transition_records = [
            json.loads(line)
            for line in family_transition_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]
        family_transition_records.append(
            {
                "transition_id": "FAMILY-TRANSPORT-T001",
                "entity_type": "selection_family",
                "entity_id": "SF001",
                "selection_family_version": "sf-v001",
                "status_field": "transportability_status",
                "from_status": "planned",
                "to_status": "passed",
                "inventory_version": "v001",
                "round_id": "round_001",
                "changed_at": "2000-01-01T00:00:00Z",
                "evidence": "injected legal transition with stale artifact state",
                "evidence_paths": [],
            }
        )
        family_transition_path.write_text(
            "".join(json.dumps(item) + "\n" for item in family_transition_records),
            encoding="utf-8",
        )
        family_transition_mismatch_report = validate_run(
            family_transition_mismatch_root
        )
        family_transition_mismatch_codes = {
            item["code"] for item in family_transition_mismatch_report["errors"]
        }
        family_transition_mismatch_detected = (
            "transition_final_state_mismatch"
            in family_transition_mismatch_codes
            and "illegal_status_transition"
            not in family_transition_mismatch_codes
            and not family_transition_mismatch_report["valid"]
        )

        history_root = temp_root / "corrupt-history-run"
        history_root.mkdir()
        _build_self_test_fixture(history_root)
        historical_path = history_root / "inventories" / "coverage_matrix_v000.csv"
        historical_rows = list(
            csv.DictReader(historical_path.open("r", encoding="utf-8", newline=""))
        )
        historical_rows[0]["sensitivity_requirement"] = ""
        _write_csv(historical_path, list(historical_rows[0].keys()), historical_rows)
        history_report = validate_run(history_root)
        history_detected = any(
            item["code"] == "missing_required_field"
            and "coverage_matrix_v000.csv" in item["location"]
            for item in history_report["errors"]
        ) and not history_report["valid"]
        history_codes = {item["code"] for item in history_report["errors"]}

        strict_family_history_root = temp_root / "incomplete-family-history-run"
        strict_family_history_root.mkdir()
        _build_self_test_fixture(strict_family_history_root)
        strict_family_history_path = (
            strict_family_history_root / "selection_families.json"
        )
        strict_family_history_value = json.loads(
            strict_family_history_path.read_text(encoding="utf-8")
        )
        for field in STRICT_SELECTION_FAMILY_FIELDS:
            strict_family_history_value["history"][0].pop(field, None)
        _write_json(strict_family_history_path, strict_family_history_value)
        strict_family_history_report = validate_run(strict_family_history_root)
        strict_family_history_errors = [
            item
            for item in strict_family_history_report["errors"]
            if item["code"] == "missing_required_field"
            and "#history" in item["location"]
        ]
        strict_family_history_messages = " ".join(
            item["message"] for item in strict_family_history_errors
        )
        strict_family_history_detected = (
            all(
                field in strict_family_history_messages
                for field in STRICT_SELECTION_FAMILY_FIELDS
            )
            and not strict_family_history_report["valid"]
        )
        strict_family_history_codes = {
            item["code"] for item in strict_family_history_report["errors"]
        }

        candidate_contract_root = temp_root / "candidate-contract-mismatch-run"
        candidate_contract_root.mkdir()
        _build_self_test_fixture(candidate_contract_root)
        families_path = candidate_contract_root / "selection_families.json"
        families_value = json.loads(families_path.read_text(encoding="utf-8"))
        second_family = dict(families_value["families"][0])
        second_family["selection_family_id"] = "SF002"
        second_family["included_cell_ids"] = []
        second_family["selection_path_ledger_entry_ids"] = []
        families_value["families"].append(second_family)
        _write_json(families_path, families_value)
        candidate_path = candidate_contract_root / "candidate_registry.csv"
        candidate_rows = list(
            csv.DictReader(candidate_path.open("r", encoding="utf-8", newline=""))
        )
        candidate_rows[0]["selection_family_id"] = "SF002"
        _write_csv(candidate_path, list(candidate_rows[0].keys()), candidate_rows)
        candidate_contract_report = validate_run(candidate_contract_root)
        candidate_contract_codes = {
            item["code"] for item in candidate_contract_report["errors"]
        }
        candidate_contract_detected = (
            "candidate_family_not_declared_in_contract" in candidate_contract_codes
            and "candidate_coverage_family_mismatch" in candidate_contract_codes
            and "candidate_ledger_family_mismatch" in candidate_contract_codes
            and not candidate_contract_report["valid"]
        )

        comparison_root = temp_root / "candidate-comparison-key-mismatch-run"
        comparison_root.mkdir()
        _build_self_test_fixture(comparison_root)
        comparison_path = comparison_root / "candidate_registry.csv"
        comparison_rows = list(
            csv.DictReader(comparison_path.open("r", encoding="utf-8", newline=""))
        )
        comparison_rows[0]["comparison_key"] = "incompatible-comparison-key"
        _write_csv(comparison_path, list(comparison_rows[0].keys()), comparison_rows)
        comparison_report = validate_run(comparison_root)
        comparison_codes = {item["code"] for item in comparison_report["errors"]}
        comparison_detected = (
            "candidate_family_comparison_key_mismatch" in comparison_codes
            and "candidate_contract_comparison_key_mismatch" in comparison_codes
            and not comparison_report["valid"]
        )

        exposure_root = temp_root / "mixed-exposure-schema-run"
        exposure_root.mkdir()
        _build_self_test_fixture(exposure_root)
        exposure_path = exposure_root / "prior_exposure_audit.json"
        exposure_value = json.loads(exposure_path.read_text(encoding="utf-8"))
        exposure_value["audit_status"] = "known_overlap"
        exposure_value["confirmatory_status"] = "confirmatory"
        _write_json(exposure_path, exposure_value)
        exposure_report = validate_run(exposure_root)
        exposure_codes = {item["code"] for item in exposure_report["errors"]}
        exposure_detected = (
            "invalid_prior_exposure_status" in exposure_codes
            and "invalid_confirmatory_status" in exposure_codes
            and not exposure_report["valid"]
        )

        mode_root = temp_root / "invalid-execution-mode-run"
        mode_root.mkdir()
        _build_self_test_fixture(mode_root)
        mode_path = mode_root / "run_manifest.json"
        mode_value = json.loads(mode_path.read_text(encoding="utf-8"))
        mode_value["execution_mode"] = "execute"
        _write_json(mode_path, mode_value)
        mode_report = validate_run(mode_root)
        mode_codes = {item["code"] for item in mode_report["errors"]}
        mode_detected = "invalid_status" in mode_codes and not mode_report["valid"]

        pause_root = temp_root / "incomplete-governance-pause-run"
        pause_root.mkdir()
        _build_self_test_fixture(pause_root)
        pause_manifest_path = pause_root / "run_manifest.json"
        pause_manifest = json.loads(pause_manifest_path.read_text(encoding="utf-8"))
        pause_manifest["search_status"] = "governance_blocked"
        pause_manifest["governance_status"] = "blocked"
        pause_manifest["coverage_complete"] = False
        _write_json(pause_manifest_path, pause_manifest)
        pause_coverage_path = pause_root / "inventories" / "coverage_matrix_v001.csv"
        pause_rows = list(
            csv.DictReader(
                pause_coverage_path.open("r", encoding="utf-8", newline="")
            )
        )
        pause_rows[0]["coverage_status"] = "governance_blocked"
        pause_rows[0]["execution_status"] = "blocked"
        pause_rows[0]["result_status"] = "not_run"
        _write_csv(pause_coverage_path, list(pause_rows[0].keys()), pause_rows)
        _write_csv(
            pause_root / "execution_queue.csv",
            ["coverage_cell_id"],
            [{"coverage_cell_id": "C001"}],
        )
        pause_report = validate_run(pause_root)
        pause_codes = {item["code"] for item in pause_report["errors"]}
        pause_detected = (
            "missing_execution_queue_column" in pause_codes
            and "missing_pause_report" in pause_codes
            and not pause_report["valid"]
        )

        family_metadata_root = temp_root / "family-metadata-mismatch-run"
        family_metadata_root.mkdir()
        _build_self_test_fixture(family_metadata_root)
        family_metadata_path = family_metadata_root / "selection_families.json"
        family_metadata_value = json.loads(
            family_metadata_path.read_text(encoding="utf-8")
        )
        family_metadata_value["families"][0]["decision_id"] = "OTHER_DECISION"
        _write_json(family_metadata_path, family_metadata_value)
        family_metadata_ledger_path = family_metadata_root / "search_ledger.jsonl"
        family_metadata_ledger = [
            json.loads(line)
            for line in family_metadata_ledger_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]
        family_metadata_ledger[0]["selection_family_version"] = "sf-missing"
        family_metadata_ledger_path.write_text(
            "".join(json.dumps(item) + "\n" for item in family_metadata_ledger),
            encoding="utf-8",
        )
        family_metadata_report = validate_run(family_metadata_root)
        family_metadata_codes = {
            item["code"] for item in family_metadata_report["errors"]
        }
        family_metadata_detected = (
            "unknown_ledger_family_version" in family_metadata_codes
            and "family_decision_id_mismatch" in family_metadata_codes
            and not family_metadata_report["valid"]
        )

        prior_completion_root = temp_root / "incomplete-prior-exposure-completion-run"
        prior_completion_root.mkdir()
        _build_self_test_fixture(prior_completion_root)
        prior_completion_path = prior_completion_root / "prior_exposure_audit.json"
        prior_completion_value = json.loads(
            prior_completion_path.read_text(encoding="utf-8")
        )
        prior_completion_value["audit_status"] = "incomplete"
        prior_completion_value["prior_exposure_status"] = "not_assessed"
        prior_completion_value["confirmatory_status"] = "unknown"
        _write_json(prior_completion_path, prior_completion_value)
        prior_candidate_path = prior_completion_root / "candidate_registry.csv"
        prior_candidate_rows = list(
            csv.DictReader(
                prior_candidate_path.open("r", encoding="utf-8", newline="")
            )
        )
        prior_candidate_rows[0]["prior_exposure_status"] = "not_assessed"
        prior_candidate_rows[0]["confirmatory_status"] = "unknown"
        _write_csv(
            prior_candidate_path,
            list(prior_candidate_rows[0].keys()),
            prior_candidate_rows,
        )
        prior_completion_report = validate_run(prior_completion_root)
        prior_completion_codes = {
            item["code"] for item in prior_completion_report["errors"]
        }
        prior_completion_detected = (
            "prior_exposure_completion_blocked" in prior_completion_codes
            and not prior_completion_report["valid"]
        )

        unknown_exposure_root = temp_root / "justified-unknown-exposure-run"
        unknown_exposure_root.mkdir()
        _build_self_test_fixture(unknown_exposure_root)
        unknown_exposure_path = unknown_exposure_root / "prior_exposure_audit.json"
        unknown_exposure_value = json.loads(
            unknown_exposure_path.read_text(encoding="utf-8")
        )
        unknown_exposure_value["audit_status"] = "unknown"
        unknown_exposure_value["prior_exposure_status"] = "unknown"
        unknown_exposure_value["unknown_gaps"] = ["one legacy analysis log is unavailable"]
        unknown_exposure_value["confirmatory_status"] = "unknown"
        _write_json(unknown_exposure_path, unknown_exposure_value)
        unknown_candidate_path = unknown_exposure_root / "candidate_registry.csv"
        unknown_candidate_rows = list(
            csv.DictReader(
                unknown_candidate_path.open("r", encoding="utf-8", newline="")
            )
        )
        unknown_candidate_rows[0]["prior_exposure_status"] = "unknown"
        unknown_candidate_rows[0]["confirmatory_status"] = "unknown"
        _write_csv(
            unknown_candidate_path,
            list(unknown_candidate_rows[0].keys()),
            unknown_candidate_rows,
        )
        unknown_exposure_report = validate_run(unknown_exposure_root)
        unknown_exposure_valid = unknown_exposure_report["valid"]

        comparability_root = temp_root / "legacy-comparability-status-run"
        comparability_root.mkdir()
        _build_self_test_fixture(comparability_root)
        comparability_path = comparability_root / "selection_families.json"
        comparability_value = json.loads(comparability_path.read_text(encoding="utf-8"))
        comparability_value["families"][0]["comparability_status"] = "comparable"
        _write_json(comparability_path, comparability_value)
        comparability_report = validate_run(comparability_root)
        comparability_codes = {
            item["code"] for item in comparability_report["errors"]
        }
        comparability_detected = (
            "invalid_status" in comparability_codes
            and not comparability_report["valid"]
        )

        tie_root = temp_root / "tie-without-common-group-run"
        tie_root.mkdir()
        _build_self_test_fixture(tie_root)
        tie_manifest_path = tie_root / "run_manifest.json"
        tie_manifest = json.loads(tie_manifest_path.read_text(encoding="utf-8"))
        tie_manifest["decision_status"] = "tie"
        _write_json(tie_manifest_path, tie_manifest)
        tie_candidate_path = tie_root / "candidate_registry.csv"
        tie_rows = list(
            csv.DictReader(tie_candidate_path.open("r", encoding="utf-8", newline=""))
        )
        tie_rows[0]["decision_status"] = "tie"
        second_candidate = dict(tie_rows[0])
        second_candidate["candidate_id"] = "CAN002"
        tie_rows.append(second_candidate)
        _write_csv(tie_candidate_path, list(tie_rows[0].keys()), tie_rows)
        tie_contract_path = tie_root / "decision_contract.json"
        tie_contract = json.loads(tie_contract_path.read_text(encoding="utf-8"))
        tie_contract["comparison_groups"] = []
        _write_json(tie_contract_path, tie_contract)
        tie_report = validate_run(tie_root)
        tie_codes = {item["code"] for item in tie_report["errors"]}
        tie_detected = (
            "tie_candidates_not_in_common_comparison_group" in tie_codes
            and not tie_report["valid"]
        )

        ineligible_support_candidate_reports: dict[str, dict[str, Any]] = {}
        for data_support in ("support_limited", "diagnostic_only"):
            ineligible_support_candidate_root = (
                temp_root / f"{data_support}-promoted-candidate-run"
            )
            ineligible_support_candidate_root.mkdir()
            _build_self_test_fixture(ineligible_support_candidate_root)
            ineligible_support_inventory_path = (
                ineligible_support_candidate_root
                / "inventories"
                / "mechanism_inventory_v001.csv"
            )
            with ineligible_support_inventory_path.open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                ineligible_support_inventory_rows = list(csv.DictReader(handle))
            ineligible_support_inventory_rows[0]["data_support_status"] = (
                data_support
            )
            _write_csv(
                ineligible_support_inventory_path,
                list(ineligible_support_inventory_rows[0]),
                ineligible_support_inventory_rows,
            )
            ineligible_support_candidate_reports[data_support] = validate_run(
                ineligible_support_candidate_root
            )
        support_limited_candidate_codes = {
            item["code"]
            for report in ineligible_support_candidate_reports.values()
            for item in report["errors"]
        }
        support_limited_candidate_detected = (
            all(
                not report["valid"]
                and any(
                    item["code"] == "candidate_data_support_gate_failed"
                    for item in report["errors"]
                )
                for report in ineligible_support_candidate_reports.values()
            )
        )

        alignment_root = temp_root / "misaligned-candidate-run"
        alignment_root.mkdir()
        _build_self_test_fixture(alignment_root)
        alignment_path = alignment_root / "inventories" / "coverage_matrix_v001.csv"
        alignment_rows = list(
            csv.DictReader(alignment_path.open("r", encoding="utf-8", newline=""))
        )
        alignment_rows[0]["mechanism_alignment"] = "diagnostic_only"
        _write_csv(alignment_path, list(alignment_rows[0].keys()), alignment_rows)
        alignment_report = validate_run(alignment_root)
        alignment_codes = {item["code"] for item in alignment_report["errors"]}
        alignment_detected = (
            "candidate_mechanism_alignment_gate_failed" in alignment_codes
            and not alignment_report["valid"]
        )

        measurement_root = temp_root / "planned-measurement-error-run"
        measurement_root.mkdir()
        _build_self_test_fixture(measurement_root)
        measurement_path = (
            measurement_root / "inventories" / "coverage_matrix_v001.csv"
        )
        measurement_rows = list(
            csv.DictReader(measurement_path.open("r", encoding="utf-8", newline=""))
        )
        measurement_rows[0]["measurement_error_sensitivity"] = "planned"
        _write_csv(
            measurement_path, list(measurement_rows[0].keys()), measurement_rows
        )
        measurement_report = validate_run(measurement_root)
        measurement_codes = {item["code"] for item in measurement_report["errors"]}
        measurement_detected = (
            "candidate_measurement_error_gate_failed" in measurement_codes
            and not measurement_report["valid"]
        )

        population_root = temp_root / "same-population-mismatch-run"
        population_root.mkdir()
        _build_self_test_fixture(population_root)
        population_path = population_root / "decision_contract.json"
        population_contract = json.loads(population_path.read_text(encoding="utf-8"))
        population_contract["selection_population"] = "selected-subpopulation"
        _write_json(population_path, population_contract)
        population_report = validate_run(population_root)
        population_codes = {item["code"] for item in population_report["errors"]}
        population_detected = (
            "same_population_mismatch" in population_codes
            and not population_report["valid"]
        )

        family_transport_root = temp_root / "unvalidated-family-transport-run"
        family_transport_root.mkdir()
        _build_self_test_fixture(family_transport_root)
        family_transport_path = family_transport_root / "selection_families.json"
        family_transport_value = json.loads(
            family_transport_path.read_text(encoding="utf-8")
        )
        transported_family = family_transport_value["families"][0]
        transported_family["target_population"] = "transported-population"
        transported_family["transportability_requirement"] = "validation_required"
        transported_family["transportability_status"] = "planned"
        _write_json(family_transport_path, family_transport_value)
        family_transport_report = validate_run(family_transport_root)
        family_transport_codes = {
            item["code"] for item in family_transport_report["errors"]
        }
        family_transport_detected = (
            "candidate_family_transport_gate_failed" in family_transport_codes
            and not family_transport_report["valid"]
        )

        missing_scale_root = temp_root / "missing-evidence-scale-mapping-run"
        missing_scale_root.mkdir()
        _build_self_test_fixture(missing_scale_root)
        missing_scale_path = missing_scale_root / "decision_contract.json"
        missing_scale_contract = json.loads(
            missing_scale_path.read_text(encoding="utf-8")
        )
        missing_scale_contract.pop("evidence_scale_mapping")
        _write_json(missing_scale_path, missing_scale_contract)
        missing_scale_report = validate_run(missing_scale_root)
        missing_scale_detected = any(
            item["code"] == "missing_required_field"
            and "evidence_scale_mapping" in item["message"]
            for item in missing_scale_report["errors"]
        ) and not missing_scale_report["valid"]
        missing_scale_codes = {
            item["code"] for item in missing_scale_report["errors"]
        }

        incomplete_scale_root = temp_root / "incomplete-evidence-scale-mapping-run"
        incomplete_scale_root.mkdir()
        _build_self_test_fixture(incomplete_scale_root)
        incomplete_scale_path = incomplete_scale_root / "decision_contract.json"
        incomplete_scale_contract = json.loads(
            incomplete_scale_path.read_text(encoding="utf-8")
        )
        incomplete_scale_contract["evidence_scale_mapping"][0][
            "discordance_rule"
        ] = ""
        _write_json(incomplete_scale_path, incomplete_scale_contract)
        incomplete_scale_report = validate_run(incomplete_scale_root)
        incomplete_scale_codes = {
            item["code"] for item in incomplete_scale_report["errors"]
        }
        incomplete_scale_detected = (
            "incomplete_evidence_scale_mapping" in incomplete_scale_codes
            and not incomplete_scale_report["valid"]
        )

        incomplete_endpoints_root = temp_root / "incomplete-scale-endpoints-run"
        incomplete_endpoints_root.mkdir()
        _build_self_test_fixture(incomplete_endpoints_root)
        incomplete_endpoints_path = (
            incomplete_endpoints_root / "decision_contract.json"
        )
        incomplete_endpoints_contract = json.loads(
            incomplete_endpoints_path.read_text(encoding="utf-8")
        )
        incomplete_endpoint_mapping = incomplete_endpoints_contract[
            "evidence_scale_mapping"
        ][0]
        incomplete_endpoint_mapping["screening_estimand_and_scale"] = ""
        incomplete_endpoint_mapping["decision_estimand_and_scale"] = ""
        _write_json(incomplete_endpoints_path, incomplete_endpoints_contract)
        incomplete_endpoints_report = validate_run(incomplete_endpoints_root)
        incomplete_endpoints_codes = {
            item["code"] for item in incomplete_endpoints_report["errors"]
        }
        incomplete_endpoints_detected = (
            "incomplete_evidence_scale_mapping" in incomplete_endpoints_codes
            and any(
                "screening_estimand_and_scale" in item["message"]
                and "decision_estimand_and_scale" in item["message"]
                for item in incomplete_endpoints_report["errors"]
            )
            and not incomplete_endpoints_report["valid"]
        )

        mapping_scope_root = temp_root / "invalid-evidence-scale-scope-run"
        mapping_scope_root.mkdir()
        _build_self_test_fixture(mapping_scope_root)
        mapping_scope_path = mapping_scope_root / "decision_contract.json"
        mapping_scope_contract = json.loads(
            mapping_scope_path.read_text(encoding="utf-8")
        )
        first_mapping = mapping_scope_contract["evidence_scale_mapping"][0]
        first_mapping["selection_family_ids"] = ["SF_UNKNOWN"]
        second_mapping = dict(first_mapping)
        second_mapping["mapping_id"] = "ESM002"
        mapping_scope_contract["evidence_scale_mapping"].append(second_mapping)
        _write_json(mapping_scope_path, mapping_scope_contract)
        mapping_scope_report = validate_run(mapping_scope_root)
        mapping_scope_codes = {
            item["code"] for item in mapping_scope_report["errors"]
        }
        mapping_scope_detected = (
            "unknown_evidence_scale_mapping_family" in mapping_scope_codes
            and "unmapped_eligible_selection_family" in mapping_scope_codes
            and not mapping_scope_report["valid"]
        )

        single_mapping_scope_root = (
            temp_root / "invalid-single-evidence-scale-scope-run"
        )
        single_mapping_scope_root.mkdir()
        _build_self_test_fixture(single_mapping_scope_root)
        single_mapping_scope_path = (
            single_mapping_scope_root / "decision_contract.json"
        )
        single_mapping_scope_contract = json.loads(
            single_mapping_scope_path.read_text(encoding="utf-8")
        )
        single_mapping_scope_contract["evidence_scale_mapping"][0][
            "selection_family_ids"
        ] = ["SF_UNKNOWN"]
        _write_json(single_mapping_scope_path, single_mapping_scope_contract)
        single_mapping_scope_report = validate_run(single_mapping_scope_root)
        single_mapping_scope_codes = {
            item["code"] for item in single_mapping_scope_report["errors"]
        }
        single_mapping_scope_detected = (
            "unknown_evidence_scale_mapping_family" in single_mapping_scope_codes
            and "unmapped_eligible_selection_family" in single_mapping_scope_codes
            and not single_mapping_scope_report["valid"]
        )

        duplicate_statistic_root = temp_root / "duplicate-screening-statistic-run"
        duplicate_statistic_root.mkdir()
        _build_self_test_fixture(duplicate_statistic_root)
        duplicate_statistic_path = (
            duplicate_statistic_root / "decision_contract.json"
        )
        duplicate_statistic_contract = json.loads(
            duplicate_statistic_path.read_text(encoding="utf-8")
        )
        duplicate_first_mapping = duplicate_statistic_contract[
            "evidence_scale_mapping"
        ][0]
        duplicate_second_mapping = dict(duplicate_first_mapping)
        duplicate_second_mapping["mapping_id"] = "ESM002"
        duplicate_second_mapping["screening_statistic"] = (
            "  REGISTERED   SYNTHETIC SCREEN SCORE  "
        )
        duplicate_statistic_contract["evidence_scale_mapping"].append(
            duplicate_second_mapping
        )
        _write_json(duplicate_statistic_path, duplicate_statistic_contract)
        duplicate_statistic_report = validate_run(duplicate_statistic_root)
        duplicate_statistic_codes = {
            item["code"] for item in duplicate_statistic_report["errors"]
        }
        duplicate_statistic_detected = (
            "ambiguous_evidence_scale_mapping_scope" in duplicate_statistic_codes
            and not duplicate_statistic_report["valid"]
        )

        not_applicable_collision_root = (
            temp_root / "not-applicable-mapping-collision-run"
        )
        not_applicable_collision_root.mkdir()
        _build_self_test_fixture(not_applicable_collision_root)
        not_applicable_collision_path = (
            not_applicable_collision_root / "decision_contract.json"
        )
        not_applicable_collision_contract = json.loads(
            not_applicable_collision_path.read_text(encoding="utf-8")
        )
        not_applicable_collision_contract["evidence_scale_mapping"].append(
            {
                "mapping_id": "ESM002",
                "selection_family_ids": ["SF001"],
                "scale_relation": "not_applicable",
                "reason": "no additional scale transfer applies",
            }
        )
        _write_json(
            not_applicable_collision_path, not_applicable_collision_contract
        )
        not_applicable_collision_report = validate_run(
            not_applicable_collision_root
        )
        not_applicable_collision_codes = {
            item["code"] for item in not_applicable_collision_report["errors"]
        }
        not_applicable_collision_detected = (
            "ambiguous_evidence_scale_mapping_scope"
            in not_applicable_collision_codes
            and not not_applicable_collision_report["valid"]
        )

        malformed_schema_root = temp_root / "malformed-artifact-schema-run"
        malformed_schema_root.mkdir()
        _build_self_test_fixture(malformed_schema_root)
        malformed_schema_path = malformed_schema_root / "run_manifest.json"
        malformed_schema_manifest = json.loads(
            malformed_schema_path.read_text(encoding="utf-8")
        )
        malformed_schema_manifest["artifact_schema_version"] = "release-candidate"
        _write_json(malformed_schema_path, malformed_schema_manifest)
        malformed_schema_report = validate_run(malformed_schema_root)
        malformed_schema_codes = {
            item["code"] for item in malformed_schema_report["errors"]
        }
        malformed_schema_warning_codes = {
            item["code"] for item in malformed_schema_report["warnings"]
        }
        malformed_schema_detected = (
            "invalid_artifact_schema_version" in malformed_schema_codes
            and "legacy_artifact_schema" not in malformed_schema_warning_codes
            and not malformed_schema_report["valid"]
        )

        hardening_results = _run_hardening_self_tests(temp_root)

        if not all(
            (
                fixed_valid,
                adaptive_valid,
                generic_valid,
                v14_valid,
                fixed_underfit_detected,
                upgrade_preservation_detected,
                upgrade_claim_preservation_detected,
                round_hash_detected,
                stage_vs_saturation_detected,
                family_detected,
                not_applicable_scale_valid,
                distinct_screening_valid,
                zero_eligible_completion_valid,
                eligible_without_coverage_detected,
                active_nonsupported_detected,
                draft_zero_cell_detected,
                invalid_data_support_detected,
                human_judgment_detected,
                unassessed_needs_data_detected,
                rejected_with_history_valid,
                rejected_without_evidence_detected,
                legacy_valid,
                init_structure_valid,
                init_overwrite_refused,
                transition_detected,
                strict_transition_detected,
                family_transition_mismatch_detected,
                history_detected,
                strict_family_history_detected,
                candidate_contract_detected,
                comparison_detected,
                exposure_detected,
                mode_detected,
                pause_detected,
                family_metadata_detected,
                prior_completion_detected,
                unknown_exposure_valid,
                comparability_detected,
                tie_detected,
                support_limited_candidate_detected,
                alignment_detected,
                measurement_detected,
                population_detected,
                family_transport_detected,
                missing_scale_detected,
                incomplete_scale_detected,
                incomplete_endpoints_detected,
                mapping_scope_detected,
                single_mapping_scope_detected,
                duplicate_statistic_detected,
                not_applicable_collision_detected,
                malformed_schema_detected,
                all(hardening_results.values()),
            )
        ):
            return {
                "self_test": "failed",
                "reason": "one or more injected faults were not detected",
                "faults_detected": {
                    "fixed_profile_positive": fixed_valid,
                    "adaptive_profile_positive": adaptive_valid,
                    "generic_coverage_profile_positive": generic_valid,
                    "schema_1_4_positive": v14_valid,
                    "fixed_profile_underfit": fixed_underfit_detected,
                    "profile_upgrade_preservation": upgrade_preservation_detected,
                    "profile_upgrade_claim_preservation": upgrade_claim_preservation_detected,
                    "sealed_round_hash": round_hash_detected,
                    "stage_completion_not_saturation": stage_vs_saturation_detected,
                    "broken_family_reference": family_detected,
                    "not_applicable_scale_positive": not_applicable_scale_valid,
                    "distinct_screening_statistics_positive": distinct_screening_valid,
                    "zero_eligible_completion_positive": zero_eligible_completion_valid,
                    "eligible_mechanism_without_coverage": eligible_without_coverage_detected,
                    "active_nonsupported_without_coverage": active_nonsupported_detected,
                    "draft_zero_cell_not_complete": draft_zero_cell_detected,
                    "canonical_data_support_status": invalid_data_support_detected,
                    "human_judgment_blocks_completion": human_judgment_detected,
                    "unassessed_needs_data_conflict": unassessed_needs_data_detected,
                    "rejected_with_evidence_positive": rejected_with_history_valid,
                    "rejected_without_evidence": rejected_without_evidence_detected,
                    "legacy_schema_positive": legacy_valid,
                    "init_canonical_structure": init_structure_valid,
                    "init_overwrite_refused": init_overwrite_refused,
                    "illegal_status_transition": transition_detected,
                    "strict_status_transition_fields": strict_transition_detected,
                    "family_transition_final_state_mismatch": family_transition_mismatch_detected,
                    "corrupt_historical_snapshot": history_detected,
                    "strict_selection_family_history": strict_family_history_detected,
                    "candidate_contract_family_mismatch": candidate_contract_detected,
                    "candidate_comparison_key_mismatch": comparison_detected,
                    "mixed_exposure_schema": exposure_detected,
                    "invalid_execution_mode": mode_detected,
                    "incomplete_governance_pause": pause_detected,
                    "family_metadata_mismatch": family_metadata_detected,
                    "incomplete_prior_exposure_completion": prior_completion_detected,
                    "justified_unknown_exposure_positive": unknown_exposure_valid,
                    "legacy_comparability_status": comparability_detected,
                    "tie_without_common_group": tie_detected,
                    "ineligible_data_support_candidate": support_limited_candidate_detected,
                    "misaligned_candidate_promoted": alignment_detected,
                    "measurement_error_sensitivity_planned": measurement_detected,
                    "same_population_mismatch": population_detected,
                    "unvalidated_family_transport": family_transport_detected,
                    "missing_evidence_scale_mapping": missing_scale_detected,
                    "incomplete_evidence_scale_mapping": incomplete_scale_detected,
                    "incomplete_evidence_scale_endpoints": incomplete_endpoints_detected,
                    "invalid_evidence_scale_scope": mapping_scope_detected,
                    "invalid_single_evidence_scale_scope": single_mapping_scope_detected,
                    "duplicate_screening_statistic_scope": duplicate_statistic_detected,
                    "not_applicable_mapping_scope_collision": not_applicable_collision_detected,
                    "malformed_artifact_schema_version": malformed_schema_detected,
                    **hardening_results,
                },
                "family_fixture_report": family_report,
                "fixed_fixture_report": fixed_report,
                "adaptive_fixture_report": adaptive_report,
                "generic_coverage_fixture_report": generic_report,
                "schema_1_4_fixture_report": v14_report,
                "fixed_underfit_fixture_report": fixed_underfit_report,
                "upgrade_fixture_report": upgrade_report,
                "upgrade_missing_claim_fixture_report": upgrade_missing_claim_report,
                "round_hash_fixture_report": round_hash_report,
                "adaptive_saturation_fixture_report": adaptive_saturation_report,
                "not_applicable_scale_fixture_report": not_applicable_scale_report,
                "distinct_screening_fixture_report": distinct_screening_report,
                "zero_eligible_fixture_reports": zero_eligible_reports,
                "eligible_without_coverage_fixture_report": eligible_without_coverage_report,
                "active_nonsupported_fixture_reports": active_nonsupported_reports,
                "draft_zero_cell_fixture_report": draft_zero_cell_report,
                "invalid_data_support_fixture_reports": invalid_data_support_reports,
                "human_judgment_fixture_report": human_judgment_report,
                "unassessed_needs_data_fixture_report": unassessed_needs_data_report,
                "rejected_with_history_fixture_report": rejected_with_history_report,
                "rejected_without_evidence_fixture_reports": rejected_without_evidence_reports,
                "legacy_fixture_report": legacy_report,
                "init_report": init_report,
                "init_validation_report": init_validation_report,
                "init_refusal_report": init_refusal_report,
                "init_file_refusal_report": init_file_refusal_report,
                "transition_fixture_report": transition_report,
                "strict_transition_fixture_report": strict_transition_report,
                "family_transition_mismatch_fixture_report": family_transition_mismatch_report,
                "history_fixture_report": history_report,
                "strict_family_history_fixture_report": strict_family_history_report,
                "candidate_contract_fixture_report": candidate_contract_report,
                "comparison_fixture_report": comparison_report,
                "exposure_fixture_report": exposure_report,
                "mode_fixture_report": mode_report,
                "pause_fixture_report": pause_report,
                "family_metadata_fixture_report": family_metadata_report,
                "prior_completion_fixture_report": prior_completion_report,
                "unknown_exposure_fixture_report": unknown_exposure_report,
                "comparability_fixture_report": comparability_report,
                "tie_fixture_report": tie_report,
                "ineligible_support_candidate_fixture_reports": ineligible_support_candidate_reports,
                "alignment_fixture_report": alignment_report,
                "measurement_fixture_report": measurement_report,
                "population_fixture_report": population_report,
                "family_transport_fixture_report": family_transport_report,
                "missing_scale_fixture_report": missing_scale_report,
                "incomplete_scale_fixture_report": incomplete_scale_report,
                "incomplete_endpoints_fixture_report": incomplete_endpoints_report,
                "mapping_scope_fixture_report": mapping_scope_report,
                "single_mapping_scope_fixture_report": single_mapping_scope_report,
                "duplicate_statistic_fixture_report": duplicate_statistic_report,
                "not_applicable_collision_fixture_report": not_applicable_collision_report,
                "malformed_schema_fixture_report": malformed_schema_report,
                "hardening_results": hardening_results,
            }
        return {
            "self_test": "passed",
            "validator_version": VALIDATOR_VERSION,
            "valid_fixture_error_count": valid_report["error_count"],
            "valid_profile_error_counts": {
                "fixed_test": fixed_report["error_count"],
                "adaptive_search": adaptive_report["error_count"],
                "coverage_search_generic": generic_report["error_count"],
                "coverage_search_legacy": valid_report["error_count"],
                "schema_1_4": v14_report["error_count"],
            },
            "valid_not_applicable_scale_error_count": not_applicable_scale_report[
                "error_count"
            ],
            "valid_distinct_screening_error_count": distinct_screening_report[
                "error_count"
            ],
            "valid_legacy_fixture_warning_count": legacy_report["warning_count"],
            "initialized_file_count": len(initialized_files),
            "valid_family_version_history": True,
            "valid_unknown_exposure_error_count": unknown_exposure_report["error_count"],
            "faults_detected": {
                "fixed_profile_positive": True,
                "adaptive_profile_positive": True,
                "generic_coverage_profile_positive": True,
                "schema_1_4_positive": True,
                "fixed_profile_underfit": True,
                "profile_upgrade_preservation": True,
                "profile_upgrade_claim_preservation": True,
                "sealed_round_hash": True,
                "stage_completion_not_saturation": True,
                "broken_family_reference": True,
                "not_applicable_scale_positive": True,
                "distinct_screening_statistics_positive": True,
                "zero_eligible_completion_positive": True,
                "eligible_mechanism_without_coverage": True,
                "active_nonsupported_without_coverage": True,
                "draft_zero_cell_not_complete": True,
                "canonical_data_support_status": True,
                "human_judgment_blocks_completion": True,
                "unassessed_needs_data_conflict": True,
                "rejected_with_evidence_positive": True,
                "rejected_without_evidence": True,
                "legacy_schema_positive": True,
                "init_canonical_structure": True,
                "init_overwrite_refused": True,
                "illegal_status_transition": True,
                "strict_status_transition_fields": True,
                "family_transition_final_state_mismatch": True,
                "corrupt_historical_snapshot": True,
                "strict_selection_family_history": True,
                "candidate_contract_family_mismatch": True,
                "candidate_comparison_key_mismatch": True,
                "mixed_exposure_schema": True,
                "invalid_execution_mode": True,
                "incomplete_governance_pause": True,
                "family_metadata_mismatch": True,
                "incomplete_prior_exposure_completion": True,
                "legacy_comparability_status": True,
                "tie_without_common_group": True,
                "ineligible_data_support_candidate": True,
                "misaligned_candidate_promoted": True,
                "measurement_error_sensitivity_planned": True,
                "same_population_mismatch": True,
                "unvalidated_family_transport": True,
                "missing_evidence_scale_mapping": True,
                "incomplete_evidence_scale_mapping": True,
                "incomplete_evidence_scale_endpoints": True,
                "invalid_evidence_scale_scope": True,
                "invalid_single_evidence_scale_scope": True,
                "duplicate_screening_statistic_scope": True,
                "not_applicable_mapping_scope_collision": True,
                "malformed_artifact_schema_version": True,
                **hardening_results,
            },
            "fault_error_codes": {
                "broken_family_reference": sorted(family_codes),
                "illegal_status_transition": sorted(transition_codes),
                "strict_status_transition_fields": sorted(strict_transition_codes),
                "family_transition_final_state_mismatch": sorted(
                    family_transition_mismatch_codes
                ),
                "corrupt_historical_snapshot": sorted(history_codes),
                "strict_selection_family_history": sorted(
                    strict_family_history_codes
                ),
                "eligible_mechanism_without_coverage": sorted(
                    eligible_without_coverage_codes
                ),
                "active_nonsupported_without_coverage": sorted(
                    active_nonsupported_codes
                ),
                "draft_zero_cell_not_complete": sorted(draft_zero_cell_codes),
                "canonical_data_support_status": sorted(
                    invalid_data_support_codes
                ),
                "human_judgment_blocks_completion": sorted(
                    human_judgment_codes
                ),
                "unassessed_needs_data_conflict": sorted(
                    unassessed_needs_data_codes
                ),
                "rejected_without_evidence": sorted(
                    rejected_without_evidence_codes
                ),
                "candidate_contract_family_mismatch": sorted(candidate_contract_codes),
                "candidate_comparison_key_mismatch": sorted(comparison_codes),
                "mixed_exposure_schema": sorted(exposure_codes),
                "invalid_execution_mode": sorted(mode_codes),
                "incomplete_governance_pause": sorted(pause_codes),
                "family_metadata_mismatch": sorted(family_metadata_codes),
                "incomplete_prior_exposure_completion": sorted(prior_completion_codes),
                "legacy_comparability_status": sorted(comparability_codes),
                "tie_without_common_group": sorted(tie_codes),
                "ineligible_data_support_candidate": sorted(
                    support_limited_candidate_codes
                ),
                "misaligned_candidate_promoted": sorted(alignment_codes),
                "measurement_error_sensitivity_planned": sorted(measurement_codes),
                "same_population_mismatch": sorted(population_codes),
                "unvalidated_family_transport": sorted(family_transport_codes),
                "missing_evidence_scale_mapping": sorted(missing_scale_codes),
                "incomplete_evidence_scale_mapping": sorted(incomplete_scale_codes),
                "incomplete_evidence_scale_endpoints": sorted(
                    incomplete_endpoints_codes
                ),
                "invalid_evidence_scale_scope": sorted(mapping_scope_codes),
                "invalid_single_evidence_scale_scope": sorted(
                    single_mapping_scope_codes
                ),
                "duplicate_screening_statistic_scope": sorted(
                    duplicate_statistic_codes
                ),
                "not_applicable_mapping_scope_collision": sorted(
                    not_applicable_collision_codes
                ),
                "malformed_artifact_schema_version": sorted(malformed_schema_codes),
            },
        }


def _emit(report: Mapping[str, Any], output: Path | None) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", nargs="?", type=Path, help="Run directory to validate.")
    parser.add_argument("--output", type=Path, help="Optional path for the JSON consistency report.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--self-test", action="store_true", help="Run built-in positive and negative fixtures.")
    modes.add_argument(
        "--init",
        metavar="RUN_DIR",
        type=Path,
        help="Create a non-overwriting schema-1.5.0 profile-aware Round-0 draft skeleton.",
    )
    modes.add_argument(
        "--snapshot-upgrade",
        metavar="RUN_DIR",
        type=Path,
        help="Create a non-overwriting hash-bound snapshot before a profile upgrade.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(RESEARCH_PROFILES),
        help="Required with --init; one of fixed_test, adaptive_search, coverage_search.",
    )
    parser.add_argument(
        "--to-profile",
        choices=sorted(RESEARCH_PROFILES),
        help="Required with --snapshot-upgrade; must be stricter than the current profile.",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        report = run_self_test()
        _emit(report, args.output)
        return 0 if report.get("self_test") == "passed" else 1
    if args.init is not None:
        if args.run_dir is not None or args.output is not None or args.to_profile is not None:
            parser.error("--init cannot be combined with run_dir, --output, or --to-profile")
        if args.profile is None:
            parser.error("--profile is required with --init for schema 1.5.0")
        report = initialize_run(args.init, args.profile)
        _emit(report, None)
        return 0 if report.get("init") == "created" else 1
    if args.snapshot_upgrade is not None:
        if args.run_dir is not None or args.output is not None or args.profile is not None:
            parser.error("--snapshot-upgrade cannot be combined with run_dir, --output, or --profile")
        if args.to_profile is None:
            parser.error("--to-profile is required with --snapshot-upgrade")
        report = create_upgrade_snapshot(args.snapshot_upgrade, args.to_profile)
        _emit(report, None)
        return 0 if report.get("snapshot") == "created" else 1
    if args.profile is not None:
        parser.error("--profile is only valid with --init; validation infers the recorded profile")
    if args.to_profile is not None:
        parser.error("--to-profile is only valid with --snapshot-upgrade")
    if args.run_dir is None:
        parser.error("run_dir is required unless --self-test or --init is used")
    report = validate_run(args.run_dir)
    collision = _output_input_collision(args.run_dir, args.output, report)
    if collision is not None:
        report = dict(report)
        errors = list(report.get("errors", []))
        errors.append(
            {
                "code": "output_overwrites_run_input",
                "location": str(args.output),
                "message": f"--output resolves to validated run input {collision!r}; the report was emitted only to stdout.",
            }
        )
        report["errors"] = errors
        report["error_count"] = len(errors)
        report["valid"] = False
        _emit(report, None)
        return 1
    _emit(report, args.output)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
