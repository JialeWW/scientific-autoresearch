# Report and Artifact Contract

Apply the full contract to executed rounds. In `design_only` mode, return advice or one design report unless the user requests artifacts.

Before filling metadata, run `scripts/validate_run.py --init <run_dir>` to create the canonical schema skeleton. Initialization refuses to overwrite an existing file or nonempty target; it supplies structure, not scientific content or approval, and intentionally remains invalid until required records are completed.

## 1. Canonical Immutable Layout

Use an equivalent project convention if one exists; otherwise use:

```text
runs/<run_id>/
  run_manifest.json
  decision_contract.json
  prior_exposure_audit.json
  data_versions.json
  inventories/
    mechanism_inventory_v001.csv
    coverage_matrix_v001.csv
    saturation_audit_v001.json
  search_ledger.jsonl
  selection_families.json
  execution_queue.csv
  status_transitions.jsonl
  candidate_registry.csv
  rounds/
    round_000/
      report.md
      inventory.json
      summary.csv
      diagnostics.<csv|parquet|jsonl>   # conditional
      figures/                          # conditional
      reproduce_commands.txt
      round_gate.md
  pause_report.md                       # conditional
  consistency_report.json
  final_report.md                       # only for complete_within_scope
```

Never overwrite or silently amend a contract, exposure audit, inventory, ledger entry, coverage matrix, data-version record, or closed round. Create a successor version or amendment with explicit parent lineage.

## 2. Run Manifest

Record:

```text
run_id
artifact_schema_version
question
scientific_scope
execution_mode
created_at
output_root
governance_status
authorized_inputs
authorized_actions
prohibited_actions
data_product_scope
data_versions_file
data_version_set_id
decision_contract_version
prior_exposure_audit_version
inventory_version
inventory_status
search_status
inventory_saturated
coverage_complete
search_ledger_audited
decision_contract_applied
decision_status
inventory_audit_protocol
inventory_generation_lenses
coverage_unit_definition
coverage_closure_rules
saturation_rule
saturation_required_sources
selection_family_policy
complete_selection_path_policy
evidence_partition_policy
data_look_policy
compute_authorization_id
execution_resource_envelope
resource_pause_policy
user_specified_limits
safety_boundary
verification_policy
consistency_validator_version
last_consistency_check
```

Execution resources schedule work; they do not define scientific coverage.

New runs use `artifact_schema_version=1.4.0`. The validator keeps earlier schema versions readable under one compatibility warning; a legacy manifest must not be relabeled without migrating its artifacts.

## 3. Decision and Exposure Artifacts

`decision_contract.json` records:

```text
decision_contract_version
decision_id
decision_question
target_population
analysis_population
selection_population
reporting_population
eligible_candidate_classes
substantive_eligibility_rule
measurement_error_policy
transportability_requirement
transportability_status
eligible_selection_family_ids
declared_selection_family_ids       # parallel, support-limited, or excluded families when present
selection_family_comparison_keys    # family ID -> frozen comparison key when not carried by a group
comparison_groups
ranked_selection_family_ids
comparison_key_definition
comparability_rule
estimand
ranking_evidence
evidence_scale_mapping
decision_rule
minimum_meaningful_difference
complexity_and_data_quality_rule
tie_rule
inconclusive_rule
complete_selection_path_method
specification_timing
freeze_time
amendment_policy
```

`evidence_scale_mapping` is one record or a nonempty list of records. Use one record per distinct screening-to-decision relation:

```text
mapping_id                         # required and unique when multiple records exist
selection_family_ids              # required when multiple records exist
screening_statistic
screening_estimand_and_scale
decision_model_or_statistic
decision_estimand_and_scale
scale_relation                    # same_scale | monotone_only | calibrated_mapping | separate_roles | not_applicable
validation_or_calibration_rule
discordance_rule
```

For multiple records, scope every eligible selection family and use unique mapping IDs. A family may have multiple records for distinct screening statistics, but each normalized `(selection_family_id, screening_statistic)` pair must be unique. For `scale_relation=not_applicable`, use the compact form `{ "scale_relation": "not_applicable", "reason": "..." }` when no selection-influencing screening-to-decision transfer occurs; that record is exclusive for its family and cannot coexist with an active mapping. A screening statistic may schedule work without serving as decision evidence; state that as `separate_roles`, define both evidence roles and scales, and test the decision-scale model independently rather than inventing a calibration.

`prior_exposure_audit.json` records:

```text
prior_exposure_audit_version
audit_status
prior_exposure_status
confirmatory_status
future_verification_status
sources_checked
overlap_unit
overlapping_data
prior_analyses
prior_parameter_attempts
prior_data_looks
prior_holdout_exposure
unknown_gaps
resulting_evidence_stage_limits
audited_at
```

Changing code, samples, models, repositories, workflows, or skill versions does not remove a recorded exposure. Preserve all audit versions and amendments.

`data_versions.json` identifies every input product, snapshot, split, transformation, label or simulation source by stable ID, version or hash when permitted, provenance, access date, overlap group, and role. Reference these IDs from coverage cells and ledger entries.

## 4. Inventory Artifacts

`mechanism_inventory_vNNN.csv` must include:

```text
inventory_version
mechanism_id
parent_mechanism_id
mechanism
distinct_pathway
inclusion_rationale
generation_lens
applicable_regime
predicted_signature
required_data_products
data_support_status
mechanism_status
specification_timing
duplicate_of
```

Fill `data_support_status` and `mechanism_status` with the canonical values and completion semantics in `status-schema.md`. In schema 1.4.0, an active nonduplicate mechanism cannot disappear from coverage merely by being labeled support limited, diagnostic, or unsupported.

`coverage_matrix_vNNN.csv` must include:

```text
coverage_cell_id
inventory_version
mechanism_id
observable_id
formulation_id
mechanism_alignment
measurement_error_sensitivity
data_product_id
data_version_id
supported_sample_id
parameter_or_scale_domain
comparator
expected_signature
minimum_meaningful_effect
sensitivity_requirement
falsifier
selection_family_id
selection_family_version
comparison_key
comparability_status
specification_timing
evidence_stage
execution_tier
coverage_status
execution_status
result_status
verification_status
round_id
ledger_entry_ids
blocker
```

`saturation_audit_vNNN.json` records audit lens, source or procedure, scope coverage, proposed additions, duplicate and exclusion decisions, needs-data entries, eligible additions, unresolved gaps, and whether the saturation sequence passed or reset. Include the mechanism-forward and data-product-reverse audits plus every independent third source declared applicable at Round 0.

## 5. Search Ledger, Selection Families, and Queue

Append one immutable ledger entry for every test, data look, adaptive choice, retry, failure, abandonment, or resource decision that can affect coverage or candidate selection.

Record at least:

```text
ledger_entry_id
inventory_version
coverage_cell_id
selection_family_id
selection_family_version
decision_influence
selection_path_stage
data_look_id
seed_policy_id
data_version_ids
input_and_code_state
execution_status
result_status
artifact_paths
```

`selection_families.json` records the decision, structured comparison fields, included cells, inferential target, complete-selection-path method, dependence assumptions, error or decision criterion, method assumptions, family versions, and handling of adaptive additions. Use `families` for exactly one current record per `selection_family_id` and `history` for immutable superseded records. The pair `(selection_family_id, selection_family_version)` must be unique across both arrays. A legacy file containing only `families` remains valid and treats those records as current.

Coverage cells, ledger entries, and candidates must pin both family ID and version. Active coverage and active candidates reference the current record; preserved historical coverage and ledger entries reference their historical composite key. A current family's complete `selection_path_ledger_entry_ids` may accumulate ledger entries from its historical versions, but every such ledger entry retains its actual family version. Never remove failed or unfavorable branches from family history. Do not make incompatible targets, supported samples, estimands, evidence stages, or material data-quality regimes directly compete without a prespecified validated mapping.

For every family, record `selection_family_id`, `selection_family_version`, `decision_id`, `comparability_status`, `comparison_key`, `target_population`, `supported_sample_id`, `estimand`, `data_quality_regime`, `evidence_stage`, `transportability_requirement`, `transportability_status`, `included_cell_ids`, `selection_path_ledger_entry_ids`, `selection_path_complete`, and `inference_method` or an explicit equivalent.

`execution_queue.csv` records every open cell, execution tier, dependency, priority, priority basis, estimated resources, authorization-envelope fit, blocker, and next admissible action. For `resource_limited_pause`, `user_limited_stop`, `governance_blocked`, or `human_decision_required` with open cells, every open cell must appear exactly once and `pause_report.md` must record the blocker and resume point. Priority controls order only. Unrun cells remain open and in the coverage denominator.

Append every state change to `status_transitions.jsonl` with `transition_id`, `entity_type`, `entity_id`, `status_field`, `from_status`, `to_status`, `inventory_version`, `round_id`, `changed_at`, `reason`, and `evidence_paths`. Do not rewrite earlier transitions.

`candidate_registry.csv` records every candidate that entered eligibility, comparison, parallel reporting, or promotion review:

```text
candidate_id
inventory_version
mechanism_id
coverage_cell_ids
selection_family_id
selection_family_version
comparison_key
comparability_status
decision_status
specification_timing
prior_exposure_status
confirmatory_status
future_verification_status
evidence_stage
verification_status
effect_summary
uncertainty_summary
support_summary
ledger_entry_ids
decision_reason
```

The file may contain only its header when no candidate was generated. Every candidate family must be explicitly declared by the Decision Contract; decision-eligible candidates must use an eligible family. Candidate coverage cells and ledger entries must belong to that same family, and the candidate comparison key must match both `selection_families.json` and the contract's family or comparison-group key. At a terminal decision, set `decision_contract_applied=true` and a terminal `decision_status` in the run manifest. A `leading` or `tie` decision must agree with candidate-registry rows, and all tied candidates must share one declared comparison group; `inconclusive` or `no_eligible_candidate` must preserve parallel, support-limited, excluded, null, and failed branches rather than inventing a winner.

In `candidate_registry.csv`, `coverage_cell_ids` lists the decision-bearing cells used for eligibility, ranking, or promotion. Keep diagnostic and control cells linked through their family, ledger, and round report; do not mislabel them as promotion evidence merely to pass an alignment gate.

## 6. Round Report

Include:

1. **Identity**: run, round, parent, inventory, coverage-cell, and family versions.
2. **Question and claim**: mechanism, estimand, expected signature, meaningful scale, substantive alignment, supported sample, and population scope.
3. **Inputs and lineage**: data, code, environment, units, transformations, hashes when allowed, and actual seeds.
4. **Governance and resources**: permissions, reusable authorization envelope, cumulative use, remaining use, and oversight.
5. **Method**: exact sample, formulation, screening statistic, decision model or statistic, evidence-scale mapping, uncertainty, seed, sensitivity, and falsifier.
6. **Result**: screening and decision-scale evidence, their agreement or discordance, effect, uncertainty, sample size, diagnostics, execution status, and result status.
7. **Coverage update**: cells opened, closed, invalidated, deferred, or added; denominator and coverage fraction.
8. **Inventory audit**: additions, merges, exclusions, saturation progress, and reset events.
9. **Selection audit**: all generation, modification, screening, ranking, verification-targeting, and promotion steps; substantive, measurement-error, and transport gates; family changes; and complete-selection-path inference.
10. **Evidence interpretation**: prior exposure, specification timing, evidence stage, comparability, verification status, alternatives, and limitations.
11. **Decision**: application of the frozen ranking, tie, and inconclusive rules; parallel or support-limited candidates; canonical statuses; next cells; and resume condition if pausing.
12. **Consistency**: validator result, unresolved errors or warnings, and artifact version checked.

## 7. Round Inventory

Record actual values:

```json
{
  "run_id": "",
  "round_id": "",
  "parent_round_id": null,
  "inventory_version": "",
  "decision_contract_version": "",
  "prior_exposure_audit_version": "",
  "coverage_cell_ids": [],
  "selection_family_versions": [],
  "inputs": [],
  "data_version_ids": [],
  "code_state": {},
  "environment": {},
  "parameters": {},
  "seed_set": [],
  "sample_counts": {},
  "ledger_entry_ids": [],
  "uncertainty_components": [],
  "resource_use": {},
  "status_transitions": [],
  "outputs": {}
}
```

## 8. Summary and Diagnostics

`summary.csv` must include every tested, weak, null, inconclusive, artifact, invalid, failed, abandoned, and resource-deferred branch. Include inventory, cell, mechanism, observable, formulation, family, comparison key, comparability, prior exposure, support, effect, uncertainty, sensitivity, all canonical statuses, and main caveat.

Create diagnostics only when they add reconstruction or audit value. For large or sensitive data, use aggregate, sampled, or de-identified outputs rather than raw records.

Never include direct identifiers, unnecessary quasi-identifiers, credentials, signed links, private endpoints, restricted paths, or secrets.

## 9. Reproduction Record

Record exact commands or equivalent steps, code commit and dirty state, environment or dependency lock, hardware or precision, actual seeds, expected outputs, and resource envelope.

Report metadata consistency and numerical reproduction separately. For a numerical rerun, record input, code, environment and seed equivalence; comparison method and tolerances; output hashes such as SHA-256 when byte identity is meaningful; and whether results are exact, within tolerance, different, or not checked. Matching hashes support same-condition byte-level agreement for those checked outputs, but do not repair an incomplete selection ledger, missing provenance, or an invalid scientific design. Conversely, a schema error alone is not evidence that a reported number changed.

Redact secrets and protected values. Use placeholders and explain how an authorized user supplies them securely.

## 10. Consistency, Pause, and Final Reports

Run:

```text
python scientific-autoresearch/scripts/validate_run.py runs/<run_id> --output runs/<run_id>/consistency_report.json
```

before resuming an existing run and before a pause or final report. The report must identify the validator version, checked artifact versions, errors, warnings, and timestamp. A failed check prevents `complete_within_scope`.

Classify failures by what they establish. Missing or inconsistent metadata blocks an audited completion claim; numerical mismatch challenges computational reproduction. Preserve both findings without collapsing one into the other.

A pause report must state:

- current inventory version and saturation status;
- closed, open, invalid, blocked, and resource-deferred cells;
- coverage numerator, denominator, and fraction;
- ledger and selection-family versions;
- frozen Decision Contract, Prior-exposure Audit, and last consistency result;
- complete open execution queue, priorities, dependencies, and next admissible action;
- cumulative resource use and exact resume requirements;
- why the state is not scientific completion.

A final report is issued only for `search_status=complete_within_scope` and must state:

- whether `inventory_saturated`, `coverage_complete`, `search_ledger_audited`, and `decision_contract_applied` hold for the same version;
- strongest supported candidates and every weak or failed branch;
- null, inconclusive, artifact, invalid, weakened, rejected, needs-data, and blocked results;
- complete family-level selection handling;
- the Decision Contract outcome, including ties, inconclusive decisions, parallel conclusions, and support-limited candidates;
- prior-exposure limitations and complete-selection-path inference;
- evidence and verification stages;
- dominant uncertainties, systematics, untested boundaries, and scope limitations;
- the exact data, authorization, assumption, or evidence needed to extend the search.

An explicit user, resource, or governance stop with open cells receives `pause_report.md`, even when it is the final deliverable for the current authorization window. Do not create `final_report.md` for an incomplete search.

Complete the Trial Completion Gate in `references/round-gate-checklist.md`. Do not issue a scoped-completion claim while the consistency validator reports errors.
