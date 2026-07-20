# Round Gate Checklist

Complete this checklist after every executed round. Mark non-applicable adapter items with a reason.

## Universal Round Gate

- **Identity**: Are run, round, parent, inventory, coverage-cell, ledger, and selection-family versions recorded?
- **Governance**: Is work inside authorized data, action, output, compute, cost, storage, time, and oversight boundaries?
- **Authorization reuse**: If a compute envelope exists, is it still valid, and does the next job remain wholly inside it?
- **Decision Contract**: Was the final decision, eligibility, comparison key, ranking evidence, meaningful difference, tie rule, inconclusive rule, and complete-selection-path method frozen before relevant outcomes?
- **Prior exposure**: Does the audit cover earlier overlapping analyses, parameter attempts, data looks, holdout use, and uncertain history? Do evidence-stage claims respect it?
- **Claim fit**: Does each statistic estimate the frozen cell's claim and estimand?
- **Support**: Are unavailable, unsupported, missing, censored, low-quality, ineligible, and true-zero cases separated where relevant?
- **Specification timing**: Which choices were pre-result frozen and which are post-result adaptive?
- **Evidence stage**: Is each result exploratory, internal validation, independent verification, or diagnostic?
- **Search ledger**: Are all tests, variants, looks, retries, weak outcomes, and failed branches recorded?
- **Selection family**: Does every generation, modification, screening, ranking, verification-targeting, and promotion step belong to the correct complete path? Were adaptive additions versioned and inference updated with a domain-appropriate method?
- **Comparability**: Do directly ranked candidates share the frozen target population, supported sample, estimand, evidence stage, and material data-quality regime or a validated common-scale mapping? Are other results parallel or support limited?
- **Evidence scale**: What is the effect in meaningful units relative to the minimum meaningful effect and systematic floor?
- **Sensitivity**: Could the cell detect or exclude a meaningful effect? Is the result null or inconclusive?
- **Uncertainty**: Are statistical, systematic, calibration, model-choice, stochastic, and sample-variance components handled?
- **Seeds**: Does the actual seed or realization set follow the frozen policy, including failed runs, without favorable selection?
- **Falsification**: What result could have weakened the claim, and what happened?
- **Coverage**: Which cells opened, closed, remained invalid, or became blocked? What are the denominator and fraction?
- **Scheduling**: Did priority change only execution order? Do unrun screen or deep-test cells remain open, and is the complete queue preserved?
- **Inventory**: Did the round produce a new eligible, nonredundant mechanism or formulation? If so, were inventory and family versions advanced?
- **Saturation**: If this round claims an inventory audit, did it execute a prespecified complete audit lens rather than merely fail to notice a new mechanism?
- **Verification**: Is evidence unverified, internal-only, holdout-verified, externally replicated, compromised, or not applicable?
- **Privacy and reproducibility**: Are artifacts auditable, minimized, and secret-free?
- **Consistency**: Did the machine validator reconcile contract, exposure, inventory, coverage, ledger, families, data versions, queue, and status transitions?
- **Decision**: Was the frozen rule applied without defaulting to the smallest p-value or forcing a winner? Does the next action follow from evidence without treating resource limits as scientific completion?

## Conditional Adapter Gates

### Observational Data

- Were availability, support, nondetection, censoring, and true zero separated?
- Does each observable match the mechanism's scale, geometry, timing, and support?
- Are proximity, cumulative contribution, weighting, natural scale, background contrast, and selection classes mapped into coverage cells or declared irrelevant?

### Machine Learning or Simulation

- Did discovery remain separate from sealed benchmark or test evidence?
- Were preprocessing and tuning confined to discovery data?
- Are continuous search ranges, refinement, convergence, and precision rules frozen?
- Is stochastic or numerical variation quantified with a common seed or realization design?
- Are all configurations, checkpoints, early stops, failures, compute use, and resource-deferred cells recorded?

### Causal or Experimental Work

- Is the causal estimand or experimental unit explicit?
- Are identification assumptions, controls, randomization, blinding, batches, replicates, deviations, and stopping rules handled?
- Are live or regulated actions covered by authorization and competent oversight?

### Literature-Dependent Claims

- Are search scope, dates, source verification, conflicting or null evidence, and novelty boundaries recorded?

## Mechanism Rejection Gate

Before `mechanism_status=rejected`, confirm:

- all relevant testable prediction classes in the current inventory were covered;
- formulations were valid, mechanism-matched, supported, and sensitive;
- dominant confounders, selection effects, leakage, and systematics were addressed;
- a decisive falsifier or several independent, adequately sensitive failures support rejection.

Otherwise use `active`, `weakened`, `needs_data`, or `needs_human_judgment`.

## Inventory Saturation Gate

Before `inventory_status=saturated`, confirm:

- the saturation rule was frozen before the audited outcomes;
- scope, data products, support rules, and eligibility rules did not change;
- one complete mechanism-forward and one complete data-product-reverse audit occurred after the latest eligible addition;
- every third independent audit source declared applicable at Round 0 was completed;
- all required audits found zero new eligible, nonredundant mechanisms;
- every addition, duplicate, exclusion, and needs-data decision has a reason.

Any eligible addition resets this gate for the new inventory version.

## Coverage Completion Gate

Before `coverage_complete=true`, confirm:

- every eligible cell is `tested_valid`, justified `covered_by`, or `not_testable_current_data`;
- no `eligible_untested`, `scheduled`, `in_progress`, `invalid_open`, `resource_blocked`, or `governance_blocked` cell was counted as closed;
- the complete ledger is audited;
- every selection family and adaptive version has registered inference that covers its complete selection path;
- weak, null, invalid, failed, and unfavorable branches remain visible.

## Trial Completion Gate

Use `search_status=complete_within_scope` only when inventory saturation, coverage completion, and ledger audit hold for the same version, `decision_contract_applied=true` has a terminal decision status consistent with the candidate registry, prior exposure has been audited, and the machine consistency check reports no errors.

If user limits, compute, cost, storage, time, or authorization end while eligible cells remain, use `user_limited_stop`, `resource_limited_pause`, or `governance_blocked`. Report the exact open queue and resume requirements. A favorable result, promoted candidate, completed round, or exhausted resource envelope never establishes scientific completion.
