# Report and Artifact Contract

Apply the full contract to executed rounds. In `design_only` mode, return advice or one design report unless the user requests artifacts.

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

## 3. Decision and Exposure Artifacts

`decision_contract.json` records:

```text
decision_contract_version
decision_id
decision_question
eligible_candidate_classes
eligible_selection_family_ids
declared_selection_family_ids       # parallel, support-limited, or excluded families when present
selection_family_comparison_keys    # family ID -> frozen comparison key when not carried by a group
comparison_groups
ranked_selection_family_ids
comparison_key_definition
comparability_rule
estimand
ranking_evidence
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

`coverage_matrix_vNNN.csv` must include:

```text
coverage_cell_id
inventory_version
mechanism_id
observable_id
formulation_id
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

`selection_families.json` records the decision, comparison key, included cells, inferential target, complete-selection-path method, dependence assumptions, error or decision criterion, method assumptions, family versions, and handling of adaptive additions. Use `families` for exactly one current record per `selection_family_id` and `history` for immutable superseded records. The pair `(selection_family_id, selection_family_version)` must be unique across both arrays. A legacy file containing only `families` remains valid and treats those records as current.

Coverage cells, ledger entries, and candidates must pin both family ID and version. Active coverage and active candidates reference the current record; preserved historical coverage and ledger entries reference their historical composite key. A current family's complete `selection_path_ledger_entry_ids` may accumulate ledger entries from its historical versions, but every such ledger entry retains its actual family version. Never remove failed or unfavorable branches from family history. Do not make incompatible targets, supported samples, estimands, evidence stages, or material data-quality regimes directly compete without a prespecified validated mapping.

For every family, record `selection_family_id`, `selection_family_version`, `decision_id`, `comparability_status`, `comparison_key`, `included_cell_ids`, `selection_path_ledger_entry_ids`, `selection_path_complete`, and `inference_method` or an explicit equivalent.

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

## 6. Round Report

Include:

1. **Identity**: run, round, parent, inventory, coverage-cell, and family versions.
2. **Question and claim**: mechanism, estimand, expected signature, meaningful scale, and supported sample.
3. **Inputs and lineage**: data, code, environment, units, transformations, hashes when allowed, and actual seeds.
4. **Governance and resources**: permissions, reusable authorization envelope, cumulative use, remaining use, and oversight.
5. **Method**: exact sample, formulation, statistic, uncertainty, seed, sensitivity, and falsifier.
6. **Result**: effect, uncertainty, sensitivity, sample size, diagnostics, execution status, and result status.
7. **Coverage update**: cells opened, closed, invalidated, deferred, or added; denominator and coverage fraction.
8. **Inventory audit**: additions, merges, exclusions, saturation progress, and reset events.
9. **Selection audit**: all generation, modification, screening, ranking, verification-targeting, and promotion steps; family changes; and complete-selection-path inference.
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

Redact secrets and protected values. Use placeholders and explain how an authorized user supplies them securely.

## 10. Consistency, Pause, and Final Reports

Run:

```text
python scientific-autoresearch/scripts/validate_run.py runs/<run_id> --output runs/<run_id>/consistency_report.json
```

before resuming an existing run and before a pause or final report. The report must identify the validator version, checked artifact versions, errors, warnings, and timestamp. A failed check prevents `complete_within_scope`.

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
