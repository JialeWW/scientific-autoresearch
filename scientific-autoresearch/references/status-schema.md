# Canonical Status Schema

Use separate fields for governance, inventory, coverage, execution, specification timing, evidence stage, scientific result, mechanism interpretation, and verification. Do not collapse them into one overloaded status.

## Governance Status

- `not_assessed`: Scope and permissions have not been assessed.
- `cleared`: Required permissions and controls are documented.
- `restricted`: Work may proceed only inside recorded constraints.
- `blocked`: A required approval, authorization, control, or responsible human is absent.

## Inventory Status

- `draft`: Inventory construction is in progress.
- `frozen`: The current version and eligibility rules are fixed for execution.
- `expanded`: A new mechanism or data-supported domain created a successor version.
- `saturation_audit`: A prespecified inventory audit is being performed.
- `saturated`: The current version passed every prespecified complementary saturation audit with no new eligible mechanism.
- `reopened`: New scope, data, or an eligible mechanism invalidated the prior saturation state.

## Coverage Status

- `unassessed`: No support or eligibility decision exists.
- `eligible_untested`: Current data support a finite test, but it has not run.
- `scheduled`: An eligible cell is queued.
- `in_progress`: Execution has started but no terminal test record exists.
- `tested_valid`: A valid test completed and has a result status.
- `covered_by`: Another named cell provides equivalent coverage with a recorded justification.
- `not_testable_current_data`: Support, sensitivity, or identifiability is inadequate with current data.
- `invalid_open`: The attempted test was invalid and a feasible valid replacement may exist.
- `resource_blocked`: Execution is deferred only by compute, cost, storage, time, or user limits.
- `governance_blocked`: Execution lacks required authorization or oversight.

Only `tested_valid`, justified `covered_by`, and `not_testable_current_data` close a coverage cell.

## Search Status

- `inventory_building`: Mechanisms and eligible cells are being enumerated.
- `coverage_in_progress`: Eligible cells remain open.
- `verification_ready`: A candidate is frozen for untouched verification.
- `resource_limited_pause`: Resources or an execution envelope ended with eligible cells open.
- `user_limited_stop`: A user-defined execution limit ended with eligible cells open.
- `governance_blocked`: Authorization or oversight prevents continuation.
- `human_decision_required`: A scientific or strategic choice cannot be resolved computationally.
- `complete_within_scope`: Inventory saturation, coverage completion, ledger audit, Decision Contract application, prior-exposure audit, and a passing machine consistency check all hold for the same version.

## Specification Timing

- `pre_result_frozen`: The mechanism, observable, formulation, sample, and decision rule were fixed before related outcomes were inspected.
- `post_result_adaptive`: At least one defining choice was motivated or changed after related evidence was inspected.

Specification timing never becomes pre-result frozen retroactively. A post-result candidate requires a new prospective test on untouched evidence.

## Prior-Exposure Status

- `audit_status=complete`: Required records and disclosures were checked.
- `audit_status=incomplete`: Known sources remain unchecked.
- `audit_status=unknown`: Available records cannot reconstruct the exposure history.
- `audit_status=not_applicable`: No outcome-bearing evidence is used; state why.

Record the exposure finding separately:

- `not_assessed`: No prior-exposure audit exists; pristine confirmation cannot be claimed.
- `no_known_exposure`: The recorded audit found no earlier outcome exposure on the same or overlapping evidence.
- `known_overlap`: Earlier analyses, parameter attempts, selection, or outcome views overlap the current evidence.
- `unknown`: Available records cannot establish whether relevant prior exposure occurred.
- `not_applicable`: No outcome-bearing evidence is used; record why the audit and confirmation labels do not apply.

`complete_within_scope` forbids `audit_status=incomplete`, `audit_status=not_assessed`, or `prior_exposure_status=not_assessed`. It may use `audit_status=complete`; a justified `unknown` requires `prior_exposure_status=unknown`, explicit unresolved gaps, and no pristine-confirmation claim. `not_applicable` requires matching prior-exposure and confirmatory statuses plus an explicit reason.

Changing a sample definition, codebase, model, repository, workflow, or skill version does not change `known_overlap` to `no_known_exposure`. Record overlap at the observation, participant, simulation, benchmark, label, or other scientifically relevant unit.

Use `confirmatory_status` only as evidence eligibility:

- `unrestricted_by_prior_exposure`: The audit found no known overlap; confirmation still requires a prospectively frozen design and valid untouched verification.
- `exploratory`: Outcome exposure or adaptive development limits the evidence to exploration.
- `internal_validation_only`: Same-source checks may assess stability but not independent confirmation.
- `compromised`: Intended verification evidence influenced development or was repeatedly viewed.
- `unknown`: Exposure uncertainty prevents a pristine claim.
- `not_applicable`: Confirmatory status is irrelevant to this diagnostic or design-only step.

Record a separate `future_verification_status`:

- `eligible_if_untouched`: A prospectively frozen candidate may be tested on genuinely untouched evidence.
- `needs_new_independent_data`: Current evidence is exposed or compromised and no untouched partition remains.
- `not_applicable`: No future confirmation decision is being made.

Thus a candidate developed on overlapping data can have `confirmatory_status=exploratory` and `future_verification_status=eligible_if_untouched` for a new independent dataset; the future status never upgrades the current evidence.

## Evidence Stage

- `exploratory`: Generates, adapts, ranks, or filters candidates.
- `internal_validation`: Same-source resampling, cross-validation, alternate models, or robustness checks evaluate stability.
- `independent_verification`: A sealed holdout or independent dataset or experiment tests a fully frozen candidate.
- `diagnostic`: Evaluates support, measurement, leakage, calibration, assumptions, or failure modes without directly promoting a scientific claim.

Evidence stage describes analytical role. Use verification status below to record actual independence.

## Execution Status

- `planned`: Registered but not started.
- `completed`: Execution finished as specified.
- `failed`: Code, numerical, convergence, instrument, or pipeline failure prevented a valid result.
- `abandoned`: Work stopped with a recorded reason before completion.
- `blocked`: Governance or resources prevented execution.

## Result Status

- `not_run`: No scientific result exists.
- `supported`: The frozen formulation met its evidential criterion.
- `null`: Adequately supported and sensitive data are compatible with no meaningful effect.
- `inconclusive`: Support, sensitivity, precision, validity, or sample size cannot distinguish meaningful alternatives.
- `artifact`: Measurement, selection, leakage, implementation, or processing best explains the result.
- `invalid`: The result cannot support interpretation because the test or assumptions are invalid.

`failed` and `abandoned` are execution states, not scientific nulls.

## Mechanism Status

- `active`: Plausible and still testable.
- `provisionally_supported`: Mechanism-matched evidence supports untouched verification without establishing proof.
- `weakened`: Adequately sensitive evidence reduced belief.
- `rejected`: A decisive falsifier or several independent, adequately sensitive tests contradict the mechanism.
- `needs_data`: Current data cannot test the mechanism adequately.
- `needs_human_judgment`: Progress requires a scientific, ethical, or strategic choice.

## Evidence Role

- `primary_candidate`
- `secondary_candidate`
- `diagnostic`
- `confounder_check`
- `method_validation`
- `case_atlas`
- `support_limited_candidate`

## Comparability Status

Use only these four canonical values; do not emit legacy aliases.

- `comparable_within_family`: The candidate shares the frozen comparison key or a validated common-scale mapping.
- `parallel_conclusion`: The result answers a different target, sample, estimand, evidence stage, or material data-quality regime and is reported separately.
- `support_limited_candidate`: The result is scientifically interesting but its support or quality prevents direct ranking in the intended family.
- `not_eligible_for_decision`: The result fails a frozen eligibility condition.

## Decision Status

- `not_evaluated`: The frozen Decision Contract has not yet been applied.
- `eligible`: The candidate may enter its declared selection family.
- `leading`: The candidate leads under the declared evidence rule, subject to its evidence stage and verification status.
- `tie`: Eligible candidates are practically or statistically equivalent under the frozen tie rule.
- `inconclusive`: Available evidence cannot support the intended distinction or action.
- `no_eligible_candidate`: No candidate satisfied the frozen eligibility and support requirements.
- `excluded`: A frozen eligibility, support, validity, or governance rule excludes the candidate from the decision, without erasing it.

The smallest nominal p-value alone cannot assign `leading`.

## Execution Tier

- `uniform_screen`: A frozen low-cost screen used only to prioritize or gate deeper work.
- `deep_test`: A mechanism-matched test with the sensitivity required by its coverage cell.
- `verification`: A fully frozen evaluation under the declared verification design.
- `diagnostic`: A support, quality, assumption, or failure-mode check.

## Verification Status

- `unverified`: No verification beyond discovery.
- `internal_only`: Same-source robustness, resampling, alternate proxy, or cross-validation only.
- `holdout_verified`: A sealed holdout evaluated a frozen candidate once.
- `externally_replicated`: Independent data or an independent experiment tested the frozen claim.
- `compromised`: Verification evidence influenced development or was inspected repeatedly.
- `not_applicable`: Verification is not relevant to the step.

## Next Action

- `expand_inventory`
- `execute_coverage`
- `refine_formulation`
- `audit_saturation`
- `freeze_for_verification`
- `verify`
- `replicate`
- `pause_resources`
- `request_data`
- `request_approval`
- `request_human_judgment`
- `finalize_within_scope`
- `stop_user_limit`

## Required Registry Fields

```text
inventory_version
decision_contract_version
prior_exposure_audit_version
coverage_cell_id
mechanism_id
observable_id
formulation_id
selection_family_id
selection_family_version
comparison_key
comparability_status
decision_status
decision_contract_applied
specification_timing
prior_exposure_status
confirmatory_status
future_verification_status
evidence_stage
execution_tier
governance_status
inventory_status
coverage_status
search_status
execution_status
result_status
mechanism_status
verification_status
supported_sample
data_product_id
data_version_id
effect_summary
uncertainty_summary
ledger_entry_ids
main_caveat
next_action
decision_reason
last_round_id
```

## Transition Rules

- `scripts/validate_run.py` is the machine-readable allowed-transition map for these enums. Any status-schema change must update that map and its positive and fault-injection self-tests in the same revision.
- Append each transition to `status_transitions.jsonl` with unique `transition_id` plus `entity_type`, `entity_id`, `status_field`, `from_status`, `to_status`, `inventory_version`, `round_id`, `changed_at`, `reason`, and `evidence_paths`.
- Every previous and new value must belong to the enum for that field; the previous value must equal the entity's last recorded value in that version.
- Coverage normally moves from `unassessed` to `eligible_untested`, then optionally `scheduled` and `in_progress`, then to one closed state or an explicit open, invalid, or blocked state. A blocked or invalid-open cell may return to `scheduled` when its blocker is resolved.
- A closed coverage cell is not silently reopened or rewritten. Correct it through a recorded transition with evidence and, when scientific meaning changes, a successor coverage-cell or inventory version.
- Inventory normally moves `draft -> frozen -> saturation_audit -> saturated`. A new eligible mechanism, changed question, or changed data support creates `expanded` or `reopened` plus a successor version; it cannot be inserted into the saturated version.
- `resource_blocked` and `governance_blocked` do not become closed coverage merely because the run stops.
- `saturated` does not imply coverage completion; coverage completion does not prove any mechanism.
- `post_result_adaptive` never becomes `pre_result_frozen` on the same evidence.
- `known_overlap` or `unknown` prior exposure does not become pristine confirmation because files, samples, code, models, repositories, workflows, or skill versions changed.
- A tuned holdout is `compromised`, not holdout verified.
- A screen changes scheduling or eligibility only under its frozen rule; it does not mark an unrun deep-test cell covered.
- Candidates with different comparison keys remain `parallel_conclusion` or `support_limited_candidate` unless a prespecified validated mapping applies.
- A final `tie` or `inconclusive` cannot be rewritten as a winner by selecting the smallest nominal p-value.
- Missing data, small samples, failed execution, or invalid tests do not reject a mechanism.
- `complete_within_scope` may be entered only when saturation, coverage completion, ledger audit, `decision_contract_applied=true` with a terminal decision status, prior-exposure audit, and machine consistency checks all pass for the same version.
