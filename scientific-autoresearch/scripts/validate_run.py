#!/usr/bin/env python3
"""Validate the internal consistency of a scientific-autoresearch run.

The validator uses only the Python standard library. It checks the active
inventory and coverage matrix, preserved historical references, the complete
search ledger, selection families, the decision contract, prior-exposure
audit, data-version registry, status transitions, and stop-state claims.

Usage:
    python validate_run.py RUN_DIR
    python validate_run.py RUN_DIR --output RUN_DIR/consistency_report.json
    python validate_run.py --self-test
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


VALIDATOR_VERSION = "1.3.0"
REPORT_SCHEMA_VERSION = "1.0"

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
    "decision_status": DECISION_STATUSES,
    "confirmatory_status": CONFIRMATORY_STATUSES,
    "future_verification_status": FUTURE_VERIFICATION_STATUSES,
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


@dataclass(frozen=True)
class Issue:
    code: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "location": self.location, "message": self.message}


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


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


def _version(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"^version[_-]?", "", text)
    text = re.sub(r"^v", "", text)
    if text.isdigit():
        return str(int(text))
    return text


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

        self.counts.update(
            {
                "active_mechanisms": len(self.active_inventory),
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
            "inventory_version": self.manifest.get("inventory_version"),
            "artifact_versions": {
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
        self._required(
            self.manifest,
            location,
            {
                "run_id",
                "question",
                "scientific_scope",
                "execution_mode",
                "governance_status",
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
        if not self.active_version:
            self.error("invalid_inventory_version", location, "inventory_version cannot be empty.")
        self._status(
            self.manifest.get("execution_mode"),
            EXECUTION_MODES,
            location,
            "execution_mode",
        )
        self._status(self.manifest.get("governance_status"), GOVERNANCE_STATUSES, location, "governance_status")
        self._status(self.manifest.get("inventory_status"), INVENTORY_STATUSES, location, "inventory_status")
        self._status(self.manifest.get("search_status"), SEARCH_STATUSES, location, "search_status")
        self._status(self.manifest.get("decision_status"), DECISION_STATUSES, location, "decision_status")
        self._manifest_bool("inventory_saturated")
        self._manifest_bool("coverage_complete")
        self._manifest_bool("search_ledger_audited")
        self._manifest_bool("decision_contract_applied")

    def _load_core_artifacts(self) -> None:
        inventory_path = self.select_versioned("mechanism_inventory_", ".csv")
        coverage_path = self.select_versioned("coverage_matrix_", ".csv")
        saturation_path = self.select_versioned("saturation_audit_", ".json", required=False)
        self.all_inventory = self.load_all_versioned_csv("mechanism_inventory_")
        self.all_coverage = self.load_all_versioned_csv("coverage_matrix_")
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
        candidate_required = str(self.manifest.get("execution_mode", "")).strip() != "design_only"
        self.candidate_registry = self.load_csv(
            self.run_dir / "candidate_registry.csv",
            required=candidate_required,
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
        self._validate_versioned_headers("mechanism_inventory_", INVENTORY_REQUIRED_COLUMNS)
        data_products = {
            str(_first(item, "data_product_id", "product_id", default="")).strip()
            for item in self.data_versions
        }
        ids_by_version: dict[str, set[str]] = defaultdict(set)
        all_ids = {row.get("mechanism_id", "") for row in self.all_inventory}

        for index, row in enumerate(self.all_inventory, start=1):
            location = row.get("__source__", f"inventory row {index}")
            self._required(row, location, INVENTORY_REQUIRED_FIELDS)
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
                    "duplicate_mechanism_id",
                    location,
                    f"mechanism_id {mechanism_id!r} is duplicated within inventory version {file_version!r}.",
                )
            ids_by_version[file_version].add(mechanism_id)
            self._status(
                row.get("specification_timing"),
                SPECIFICATION_TIMINGS,
                location,
                "specification_timing",
            )
            self._status(
                row.get("mechanism_status"),
                MECHANISM_STATUSES,
                location,
                "mechanism_status",
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
                self.error("self_duplicate", location, "A mechanism cannot be its own duplicate_of target.")

        for row in self.all_inventory:
            location = row.get("__source__", "inventory")
            file_version = row.get("__file_version__", "")
            duplicate_of = row.get("duplicate_of", "")
            if duplicate_of and duplicate_of not in ids_by_version[file_version]:
                self.error(
                    "unknown_duplicate_mechanism",
                    location,
                    f"duplicate_of target {duplicate_of!r} is absent from inventory version {file_version!r}.",
                )
            parent_id = row.get("parent_mechanism_id", "")
            if parent_id and parent_id not in all_ids:
                self.error(
                    "unknown_parent_mechanism",
                    location,
                    f"parent_mechanism_id {parent_id!r} is absent from all preserved inventories.",
                )

    def _validate_coverage(self) -> None:
        self._validate_versioned_headers("coverage_matrix_", COVERAGE_REQUIRED_COLUMNS)
        mechanism_ids_by_version: dict[str, set[str]] = defaultdict(set)
        for row in self.all_inventory:
            mechanism_ids_by_version[row.get("__file_version__", "")].add(
                row.get("mechanism_id", "")
            )
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
            self._required(row, location, COVERAGE_REQUIRED_FIELDS)
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
                    "unknown_mechanism",
                    location,
                    f"mechanism_id {row.get('mechanism_id')!r} is absent from inventory version {file_version!r}.",
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
        missing_headers = CANDIDATE_REQUIRED_FIELDS - self.csv_headers.get(location, set())
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
            self._required(row, row_location, CANDIDATE_REQUIRED_FIELDS)
            candidate_id = row.get("candidate_id", "")
            if candidate_id in seen:
                self.error(
                    "duplicate_candidate_id",
                    row_location,
                    f"candidate_id {candidate_id!r} is duplicated.",
                )
            seen.add(candidate_id)
            version = _version(row.get("inventory_version"))
            mechanism_id = row.get("mechanism_id", "")
            family_id = row.get("selection_family_id", "")
            family_version = str(row.get("selection_family_version", "")).strip()
            family = families_by_key.get((family_id, family_version))
            active_candidate = version == self.active_version
            if (version, mechanism_id) not in mechanisms:
                self.error(
                    "unknown_candidate_mechanism",
                    row_location,
                    f"mechanism_id {mechanism_id!r} is absent from inventory version {version!r}.",
                )
            candidate_cell_ids = _ids(row.get("coverage_cell_ids"))
            for cell_id in candidate_cell_ids:
                coverage_row = coverage_cells.get((version, cell_id))
                if coverage_row is None:
                    self.error(
                        "unknown_candidate_coverage_cell",
                        row_location,
                        f"coverage cell {cell_id!r} is absent from inventory version {version!r}.",
                    )
                    continue
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
                        "candidate_coverage_mechanism_mismatch",
                        row_location,
                        f"Coverage cell {cell_id!r} belongs to mechanism {coverage_row.get('mechanism_id')!r}, not candidate mechanism {mechanism_id!r}.",
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
                and decision in {"eligible", "leading", "tie"}
                and family_id not in eligible_family_ids
            ):
                self.error(
                    "candidate_family_not_eligible_for_decision",
                    row_location,
                    f"Candidate decision_status={decision!r} requires family {family_id!r} in eligible_selection_family_ids.",
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
        if run_decision == "leading" and not any(
            row.get("decision_status") == "leading" for row in active_candidates
        ):
            self.error(
                "candidate_decision_mismatch",
                location,
                "Run decision_status=leading requires an active leading candidate row.",
            )
        if run_decision == "tie":
            tied = [row for row in active_candidates if row.get("decision_status") == "tie"]
            if len(tied) < 2:
                self.error(
                    "candidate_decision_mismatch",
                    location,
                    "Run decision_status=tie requires at least two active tied candidate rows.",
                )
            else:
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
        if run_decision in {"inconclusive", "no_eligible_candidate"} and any(
            row.get("decision_status") in {"leading", "tie"} for row in active_candidates
        ):
            self.error(
                "candidate_decision_mismatch",
                location,
                "Inconclusive or no-eligible-candidate run cannot contain an active winner.",
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

        required_sources = {
            _lens(item)
            for item in _ids(
                _first(
                    self.manifest,
                    "saturation_required_sources",
                    "required_saturation_audits",
                    default=["mechanism_forward", "data_product_reverse"],
                )
            )
        }
        required_sources.update({"mechanism_forward", "data_product_reverse"})
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
                additions = _first(record, "new_eligible_mechanisms", "eligible_additions", "new_eligible_count", default=[])
                if isinstance(additions, int):
                    has_additions = additions > 0
                else:
                    has_additions = bool(_list(additions))
                if has_additions:
                    self.error("saturation_with_new_mechanisms", location, f"Saturation source {source!r} produced new eligible mechanisms.")

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
                        self.error(
                            "illegal_status_transition",
                            location,
                            f"Illegal {field} transition {old!r} -> {new!r}.",
                        )
            key = (entity_type, entity_id, field, transition_version)
            if key in chains and old != chains[key]:
                self.error("broken_transition_chain", location, f"Transition starts at {old!r}, but previous state was {chains[key]!r}.")
            chains[key] = new
            final_states[key] = new

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
            elif transition_version == self.active_version and entity_type in {
                "coverage_cell",
                "cell",
                "coverage",
            }:
                row = next((item for item in self.active_coverage if item.get("coverage_cell_id") == entity_id), None)
                if row and field in row:
                    current = str(row.get(field, ""))
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
        computed_complete = not open_rows
        manifest_complete = _bool(self.manifest.get("coverage_complete"))
        inventory_saturated = _bool(self.manifest.get("inventory_saturated"))
        ledger_audited = _bool(self.manifest.get("search_ledger_audited"))
        decision_applied = _bool(self.manifest.get("decision_contract_applied"))
        decision_status = str(self.manifest.get("decision_status", ""))
        search_status = self.manifest.get("search_status")
        self.counts["closed_coverage_cells"] = len(closed)
        self.counts["open_coverage_cells"] = len(open_rows)

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


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_self_test_fixture(root: Path) -> None:
    (root / "inventories").mkdir(parents=True)
    manifest = {
        "run_id": "self-test-run",
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

        if not all(
            (
                family_detected,
                transition_detected,
                history_detected,
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
            )
        ):
            return {
                "self_test": "failed",
                "reason": "one or more injected faults were not detected",
                "faults_detected": {
                    "broken_family_reference": family_detected,
                    "illegal_status_transition": transition_detected,
                    "corrupt_historical_snapshot": history_detected,
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
                },
                "family_fixture_report": family_report,
                "transition_fixture_report": transition_report,
                "history_fixture_report": history_report,
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
            }
        return {
            "self_test": "passed",
            "validator_version": VALIDATOR_VERSION,
            "valid_fixture_error_count": valid_report["error_count"],
            "valid_family_version_history": True,
            "valid_unknown_exposure_error_count": unknown_exposure_report["error_count"],
            "faults_detected": {
                "broken_family_reference": True,
                "illegal_status_transition": True,
                "corrupt_historical_snapshot": True,
                "candidate_contract_family_mismatch": True,
                "candidate_comparison_key_mismatch": True,
                "mixed_exposure_schema": True,
                "invalid_execution_mode": True,
                "incomplete_governance_pause": True,
                "family_metadata_mismatch": True,
                "incomplete_prior_exposure_completion": True,
                "legacy_comparability_status": True,
                "tie_without_common_group": True,
            },
            "fault_error_codes": {
                "broken_family_reference": sorted(family_codes),
                "illegal_status_transition": sorted(transition_codes),
                "corrupt_historical_snapshot": sorted(history_codes),
                "candidate_contract_family_mismatch": sorted(candidate_contract_codes),
                "candidate_comparison_key_mismatch": sorted(comparison_codes),
                "mixed_exposure_schema": sorted(exposure_codes),
                "invalid_execution_mode": sorted(mode_codes),
                "incomplete_governance_pause": sorted(pause_codes),
                "family_metadata_mismatch": sorted(family_metadata_codes),
                "incomplete_prior_exposure_completion": sorted(prior_completion_codes),
                "legacy_comparability_status": sorted(comparability_codes),
                "tie_without_common_group": sorted(tie_codes),
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
    parser.add_argument("--self-test", action="store_true", help="Run built-in positive and negative fixtures.")
    args = parser.parse_args(argv)
    if args.self_test:
        report = run_self_test()
        _emit(report, args.output)
        return 0 if report.get("self_test") == "passed" else 1
    if args.run_dir is None:
        parser.error("run_dir is required unless --self-test is used")
    report = validate_run(args.run_dir)
    _emit(report, args.output)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
