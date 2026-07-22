# Canonical Status Schema

This is an audit and validator-diagnosis reference, not default Agent context. For schema `1.5.4`, the initializer and `scripts/validate_run.py` are authoritative for fields, enums, and transition checks. Do not copy this page into every run.

## Profile and Stage

`design_only` and `audit_only` create no execution-run artifacts by default; `audit_only` may validate an existing run read-only. Executed runs use one `research_profile`:

- `fixed_test`: one claim and sample use either one prespecified analysis or a finite prespecified analysis family under a frozen joint decision rule.
- `adaptive_search`: candidate generation, modification, screening, retention, ranking, or promotion can depend on viewed results.
- `coverage_search`: the run additionally claims systematic coverage of a finite, versioned, data-supported candidate space.

Profiles are ordered `fixed_test < adaptive_search < coverage_search`. A frozen family remains `fixed_test` unless outcomes change its membership, methods, thresholds, sample, multiplicity or joint rule, or reporting rule. `profile_history` is append-only and its offset-aware `started_at` values are strictly increasing. Before an upgrade, validate the source and run `scripts/validate_run.py --snapshot-upgrade RUN_DIR --to-profile PROFILE`. The returned upgrade entry records `preservation_snapshot_path` and `preservation_snapshot_sha256`; append it only after reviewing the non-overwriting copy. A preservation snapshot declares the prior profile, capture time, target profile, and an artifact list whose entries contain `logical_path`, internal nonsymlink `snapshot_path`, and verified `sha256`. It must include the prior manifest, that profile's required artifacts, and every round report and reproduction record indexed by the prior manifest. Boolean preservation attestations alone are insufficient. A downgrade is invalid. A changed sample, codebase, model, tool, workflow, or skill version never restores confirmatory status.

Schema 1.5.2 `skill_provenance` is an ordered history automatically seeded by initialization. Before authorized execution or resume, use `scripts/validate_run.py --record-skill-provenance RUN_DIR`; unchanged identity is a no-op and changed identity appends a new entry. Read-only validation never edits it. Each entry records the skill name, release version, deterministic behavior-package SHA-256, offset-aware capture time, and an optional source revision. The digest binds `SKILL.md`, bundled references, scripts, and evaluation specifications while excluding run outputs; symbolic links on that surface are invalid. It identifies content but does not prove compliance or independent timing.

Schema 1.5.3 adds a one-time domain-adapter assessment, unit and dependence fields in claim or decision records, an optional hash-bound adapter and project data-preflight interface, auditable equivalence closure, and a basis-specific coverage summary. Keep `domain_adapter_required=false` for tasks whose relevant semantics fit directly in the frozen claim or Decision Contract, but assess rather than assume this state before outcome-bearing execution.

Schema 1.5.4 conditionally binds a passed automated, decision-bearing data preflight to a preserved procedure artifact, the complete input-version set and immutable bindings, its execution outcome, and the hash-bound report. Other evidence modes do not require executable fields. Schema 1.5.3 remains valid as a legacy assurance level; relabeling it does not assert that executable evidence existed.

Use `stage_status` independently of scientific completion:

- `planned`: frozen work has not started.
- `in_progress`: work is active.
- `completed_as_scoped`: this profile's bounded work ended as declared.
- `blocked`: execution cannot continue under current authority or resources.
- `abandoned`: the stage ended without completing its declared work, with a reason.

`completed_as_scoped` means a fixed test, adaptive stage, or bounded coverage stage ended as declared; it does not imply inventory saturation or coverage completion. Only `coverage_search` can use `search_status=complete_within_scope`, under the closure gate below.

`round_artifacts` is the manifest index of closed round records. Each entry carries `round_id`, `status`, `report_path`, and `reproduce_path`; `completed` also requires `sealed_at`, `report_sha256`, and `reproduce_sha256`. Once a round is terminal, do not overwrite its indexed artifacts or hashes. Create an amendment or successor round. Hash reconciliation detects internal mismatch, not coordinated rewriting of both an artifact and its mutable manifest; use an append-only or externally anchored store when tamper evidence is required.

## Typed Candidates and Substantive Eligibility

Use `candidate_type` = `mechanism`, `model`, `feature`, `simulation`, `design`, or `other` with a reason. Every candidate receives `substantive_eligibility` = `eligible`, `ineligible`, or `not_assessed` under the frozen decision.

`mechanism_alignment` applies only to a mechanistic candidate:

- `direct`, `calibrated_proxy`: may pass the alignment gate.
- `diagnostic_only`, `unsupported`, `not_assessed`: cannot be promoted as mechanism evidence.
- `not_applicable`: valid only for a nonmechanistic candidate, with its general substantive-eligibility rule still applied.

In a generic coverage inventory, use `candidate_id`, `candidate_type`, and `candidate_status`; a legacy mechanistic inventory may retain `mechanism_id` and `mechanism_status`. `candidate_status` uses `active`, `provisionally_supported`, `weakened`, `rejected`, `needs_data`, or `needs_human_judgment`. Here `rejected` means that adequately sensitive evidence falsified the frozen candidate-level claim or performance standard; it does not reject a broader mechanism. Rejecting a mechanistic candidate additionally requires mechanism-matched evidence. Do not turn a Cartesian combination into a scientific candidate without a recorded substantive role and eligibility rationale.

## Conditional Gates

Activate a gate only when its stated pathway exists; record why it is not applicable.

- Measurement error is applicable when uncertainty can change support, eligibility, subgroup membership, thresholding, ranking, or interpretation. In adaptive candidates, record this as `measurement_error_relevant=true`. Use `measurement_error_sensitivity` = `planned`, `passed`, `failed`, or `inconclusive`; otherwise use `not_required` after assessment or justified `not_applicable`. An applicable gate must pass before promotion.
- Transportability is applicable when evidence is used across materially different target, analysis, selection, or reporting populations. Use requirement `same_population`, `validation_required`, or `parallel_only`, with status `not_required`, `planned`, `passed`, `failed`, or `inconclusive`. Required validation must pass before direct comparison; unsupported transport remains parallel.
- Evidence-scale mapping is applicable when screening and decision evidence differ in statistic, estimand, scale, or role. Use relation `same_scale`, `monotone_only`, `calibrated_mapping`, `separate_roles`, or justified `not_applicable`, and freeze validation and discordance rules. Rank association alone does not establish raw-scale prediction.
- A frozen finite analysis family uses its prespecified joint or multiplicity rule without an adaptive ledger. Complete-selection-path inference is applicable whenever outcome-informed generation, modification, screening, ranking, or repeated looks can influence one decision. The method is domain-specific; the complete influential path is not optional.

## Shared Scientific Statuses

Keep these dimensions separate.

### Specification and evidence

- `specification_timing`: `pre_result_frozen` or `post_result_adaptive`; the latter never becomes frozen retroactively on the same evidence.
- `evidence_stage`: `exploratory`, `internal_validation`, `independent_verification`, or `diagnostic`.
- `verification_status`: `unverified`, `internal_only`, `holdout_verified`, `externally_replicated`, `compromised`, or `not_applicable`.
- `prior_exposure_status`: `not_assessed`, `no_known_exposure`, `known_overlap`, `unknown`, or `not_applicable`.
- `confirmatory_status`: `unrestricted_by_prior_exposure`, `exploratory`, `internal_validation_only`, `compromised`, `unknown`, or `not_applicable`.
- `future_verification_status`: `eligible_if_untouched`, `needs_new_independent_data`, or `not_applicable`.

A sealed holdout or independent source supports verification only when the candidate and rule were prospectively frozen and that evidence was not used in development. Same-source variants are internal validation. Repeatedly viewed or tuned verification evidence is `compromised`.

### Execution and result

- `execution_status`: `planned`, `completed`, `failed`, `abandoned`, or `blocked`.
- `result_status`: `not_run`, `supported`, `null`, `inconclusive`, `artifact`, `invalid`.

Failure or abandonment is not a scientific null. Missing support, inadequate sensitivity, or an invalid test is not evidence against the broader claim.

### Comparison and decision

- `comparability_status`: `comparable_within_family`, `parallel_conclusion`, `support_limited_candidate`, or `not_eligible_for_decision`.
- `decision_status`: `not_evaluated`, `eligible`, `leading`, `tie`, `inconclusive`, `no_eligible_candidate`, or `excluded`.

Directly ranked candidates must share the frozen comparison key: target population, supported sample, estimand, evidence stage, material data-quality regime, and any required validated mapping. The smallest nominal p-value alone cannot assign `leading`.

## Coverage-Only Statuses

These fields are required only for `coverage_search` and legacy schema `<=1.4` full runs.

### Inventory

`inventory_status` = `draft`, `frozen`, `expanded`, `saturation_audit`, `saturated`, or `reopened`.

`data_support_status` = `supported`, `support_limited`, `diagnostic_only`, `unsupported`, `not_assessed`, or `not_applicable`. Only `supported` enters direct decision ranking.

For a mechanistic inventory, `mechanism_status` = `active`, `provisionally_supported`, `weakened`, `rejected`, `needs_data`, or `needs_human_judgment`. Rejection requires preserved, mechanism-matched, adequately sensitive evidence; an unsupported or untestable entry is `needs_data`, not rejected.

### Coverage

`coverage_status` =:

- open: `unassessed`, `eligible_untested`, `scheduled`, `in_progress`, `invalid_open`, `resource_blocked`, `governance_blocked`;
- closed: `tested_valid`, justified `covered_by`, or `not_testable_current_data`.

Priority changes execution order only. Unrun or blocked cells remain open and stay in the denominator.

`execution_tier` = `uniform_screen`, `deep_test`, `verification`, or `diagnostic`.

Report `tested_valid`, `covered_by`, `not_testable_current_data`, all classified-closed, and open counts and fractions separately. `coverage_complete` means every eligible cell was classified closed; it does not mean every cell received an empirical test. Schema 1.5.3 `covered_by` records equivalence type, scope, assumptions, evidence, review status, and a noncyclic target.

### Search

`search_status` = `inventory_building`, `coverage_in_progress`, `verification_ready`, `resource_limited_pause`, `user_limited_stop`, `governance_blocked`, `human_decision_required`, or `complete_within_scope`.

Use `complete_within_scope` only for a validated machine-audited coverage record when, for the same active version:

```text
inventory_saturated
AND coverage_complete
AND search_ledger_audited
AND decision_contract_applied
AND terminal decision_status
AND prior-exposure audit adequate for the claim
AND validator reports no errors
```

A completed round, promoted candidate, stage report, exhausted resource envelope, or favorable result never satisfies this gate.

## Transition and Preservation Rules

- Append status changes to `status_transitions.jsonl`; never rewrite history. The validator defines the required transition record and legal map.
- Frozen classifications such as data support, alignment, or transport requirements change through a successor version, not an in-place edit.
- A closed coverage cell is corrected through an amendment, transition, or successor cell/version.
- An outcome-motivated formulation remains `post_result_adaptive`; the untouched prospective test is a new record.
- Preserve weak, null, invalid, failed, abandoned, blocked, and unfavorable branches.
- Use the validator before resume and before any stage, pause, or completion report. Metadata consistency and numerical reproduction are separate claims.

Schema `<=1.4` remains readable under its legacy full-run behavior. Schema `1.5.0` profile runs remain readable, with a missing fixed-test `analysis_scope` interpreted as `single_test`; schema `1.5.0` and `1.5.1` may omit skill provenance, schemas through `1.5.2` may omit the domain-adapter and equivalence additions, and schema `1.5.3` may omit executable-preflight evidence binding. Do not relabel a legacy run; initialize or migrate profile metadata and artifacts explicitly.
