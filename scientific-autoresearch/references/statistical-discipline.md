# Statistical Discipline for Adaptive Search

Use this file for `adaptive_search` or `coverage_search` when repeated tests, outcome-dependent choices, screening, ranking, selective or sequential inference, holdouts, or stochastic comparisons can affect one decision. A genuine `fixed_test` does not acquire a search family merely because it estimates uncertainty or runs prespecified numerical replicates.

Read `decision-selection.md` first. It is the source of truth for the Decision Contract, Prior-exposure Audit, comparability, and complete selection path; do not duplicate those records here.

## 1. Map Screening to Decision Evidence Only When Needed

When a screen and the final decision use different statistics, models, estimands, scales, or roles, freeze before screening:

- both evidence definitions and estimands;
- `same_scale`, `monotone_only`, `calibrated_mapping`, or `separate_roles`;
- the calibration or validation test; and
- the discordance rule.

A rank statistic can support ordering or monotone association without establishing a raw-scale slope, calibration, residual adequacy, or predictive loss. A screen may prioritize work without becoming decision evidence. Preserve discordance and apply the frozen rule; never select whichever scale looks favorable.

When no selection-influencing screen-to-decision transfer occurs, record one compact not-applicable reason rather than creating full placeholder mapping work.

## 2. Establish Support and Sensitivity

Before a decision-bearing test, freeze the candidate or formulation, supported sample, estimand, meaningful effect, statistic or model, assumptions, and falsifier. A result-motivated change to the sample, outcome, formula, scale, threshold, parameter, or model is a new post-result-adaptive entry, not a repair of the earlier result.

Estimate attainable precision, power, detectable-effect limits, upper-limit sensitivity, recovery performance, or another claim-appropriate measure. After testing:

- use `null` only when valid, supported, adequately sensitive evidence is compatible with no meaningful effect;
- use `inconclusive` when uncertainty, support, or sensitivity cannot distinguish meaningful alternatives;
- use `artifact` or `invalid` for measurement, leakage, implementation, or assumption failures; and
- separate statistical thresholds from practical, physical, or operational importance.

Run a measurement-error sensitivity analysis only when uncertainty can change support, matching, subgroup membership, thresholds, eligibility, ranking, or interpretation. Run transport analysis only when a result is used beyond its analysis or selection population. A not-applicable gate requires one explicit rationale, not repeated placeholder work.

## 3. Cover the Complete Selection Path

The inferential target is the procedure that produced the reported candidate, not only its last test. The ledger and family record must retain every selection-influencing generation, modification, screen, repeated look, retention, rank, verification-target choice, promotion, weak result, failure, invalid branch, and abandonment.

Choose a strategy whose assumptions and target match that path:

- one sealed holdout after all development choices are frozen;
- an end-to-end null or randomization that reruns the selection procedure;
- selective inference for a characterized selection event;
- sequential or always-valid inference for prospectively governed looks;
- hierarchical multiplicity control aligned with prespecified families;
- Bayesian model comparison or averaging with a declared candidate set, priors, likelihood, decision rule, and sensitivity analysis; or
- another justified procedure with equivalent path coverage.

No global-null construction is universal. Document what the method covers, what it omits, the dependence assumptions, and how failures are treated. Bayesian analysis does not erase earlier data exposure or an adaptively assembled candidate set.

Direct ranking requires a common decision, target population, supported sample, estimand, evidence stage, and materially comparable data-quality regime, or a prespecified validated mapping. Keep other results parallel or support limited. Do not create narrow families merely to exclude unfavorable branches, or one artificial family across unrelated targets.

When an adaptive candidate or formulation is added, record it before execution, version the affected family, update inference or retain exploratory status, and preserve every earlier branch. In `coverage_search`, also version the inventory and affected cells; `adaptive_search` does not need an inventory or saturation claim.

## 4. Separate Evidence Stages

- `exploratory`: candidate generation, outcome-driven formulation, model search, screening, and ranking.
- `internal_validation`: same-source resampling, cross-validation, alternate models, proxies, or robustness checks.
- `independent_verification`: a sealed holdout or independent dataset or experiment tests a fully frozen candidate.
- `diagnostic`: support, quality, calibration, leakage, or failure-mode evidence that does not promote the claim.

Fit preprocessing, imputation, scaling, feature selection, and tuning only within discovery data or folds. Split by the independent scientific unit and use nested validation when tuning and performance estimation would otherwise reuse folds.

Evaluate sealed evidence once under its frozen rule. If feedback changes development, mark verification compromised. Earlier inspection of overlapping units remains exposure even if the split, code, model, repository, workflow, or skill version changes.

## 5. Handle Stochasticity Without Seed Selection

- Use one fixed seed only for debugging or exact reproduction.
- When randomness could change ranking or interpretation, predeclare a common or paired seed or realization set, aggregate, retry rule, and precision-based expansion rule.
- Retain actual seeds, failures, nonconvergence, and between-run variation.
- Never add, remove, select, or report seeds, checkpoints, or realizations because they improve direction, significance, or rank.
- Do not treat seeds as independent scientific sample units.
- Separate optimization and Monte Carlo variation from data, model, and sample uncertainty.

Native optimizer, tuner, or simulation logs may remain in their reproducible system of record. The search ledger must still reference that write-once-by-policy or versioned log and summarize every selection-influencing state transition; do not copy millions of noninfluential telemetry rows merely for ceremony.

## 6. Stop at the Correct Claim Level

For `adaptive_search`, end with a stage or bounded report that states the searched candidates, unresolved paths, and inference limits. It cannot claim inventory saturation or coverage completion.

For `coverage_search`, use the saturation and coverage rules in `coverage-search.md`. A universal round or candidate cap, a favorable result, a promoted candidate, or resource exhaustion is not scientific completion. If resources or authorization end with eligible cells open, preserve the queue and issue a bounded pause.

Before promotion, confirm that substantive eligibility and every applicable measurement, transport, mapping, multiplicity, and stochastic gate passed; the Decision Contract's tie and inconclusive rules were applied; prior exposure and evidence stage are honest; weak and failed branches remain visible; and no winner was chosen from the smallest nominal p-value alone.
