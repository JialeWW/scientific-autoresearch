# Statistical and Adaptive-Search Discipline

Use this file before repeated testing, adaptive scans, stochastic comparisons, candidate ranking, or promotion. Also read `decision-selection.md`.

## 1. Freeze the Decision and Audit Exposure

Before candidate-specific outcomes, freeze a Decision Contract that states:

- the decision and eligible candidate classes;
- which candidates share a justified selection family and comparison key;
- the estimand, ranking evidence, decision rule, minimum meaningful difference, and treatment of robustness, complexity, and data quality;
- the mapping between any screening statistic and the final decision or prediction scale;
- tie, practical-equivalence, and inconclusive rules;
- the inference strategy that will cover the complete selection path.

Nominal p-values may contribute to an evidence rule, but the smallest p-value is not a default winner. When the rule does not separate candidates, report `tie` or `inconclusive`.

A Decision Contract first written or revised after relevant outcomes were inspected is `post_result_adaptive`. It may govern future untouched evidence, but it does not retrospectively make the exposed comparison confirmatory.

Complete a Prior-exposure Audit covering same or overlapping data, earlier analyses, parameter attempts, data looks, holdouts, and candidate decisions. Evidence exposure follows the underlying information. A changed sample, codebase, model, repository, workflow, or skill version does not restore confirmatory status. If exposure is uncertain, record `prior_exposure_status=unknown` and do not claim pristine confirmation.

## 2. Map Screening Evidence to the Decision Scale

Before screening outcomes, record the screening statistic, final decision model or statistic, both estimands and scales, the assumed relation between them, any calibration or validation test, and the rule for discordant evidence. Use `same_scale`, `monotone_only`, `calibrated_mapping`, `separate_roles`, or `not_applicable` as the declared scale relation.

Rank statistics encode ordering, not raw-scale slope or calibration. Therefore a rank-based screen may prioritize a candidate but cannot establish raw-scale slope, calibration, residual adequacy, or predictive performance unless the registered mapping supports that inference. If screening and decision evidence disagree, retain both and apply the frozen discordance rule; do not choose the more favorable scale after inspection.

## 3. Freeze Each Coverage Cell

Record:

```text
inventory_version
coverage_cell_id
claim_id
claim_type
mechanism_id
observable_id
formulation_id
target_population_or_system
unit_of_inference
supported_sample
exposure_or_model
comparator
outcome
time_horizon_or_scale
summary_measure
expected_direction
minimum_meaningful_effect
assumptions
specification_timing
evidence_stage
selection_family_id
comparison_key
freeze_time
```

A substantive change to sample, outcome, formula, scale, threshold, model, or estimand creates a new formulation ID. A change motivated by related outcomes is `post_result_adaptive` and exploratory.

## 4. Establish Sensitivity Before Null Interpretation

Before testing, state the smallest scientifically meaningful effect and estimate attainable precision, power, detectable-effect limits, upper-limit sensitivity, or recovery performance.

After testing:

- use intervals, upper limits, equivalence bounds, posterior mass, or another claim-appropriate measure;
- use `null` only when valid, supported, sensitive data can exclude or constrain meaningful effects;
- use `inconclusive` when uncertainty remains too wide;
- separate statistical thresholds from practical or physical importance.

## 5. Cover the Complete Selection Path

Every test or choice capable of influencing the same candidate generation, modification, screening, retention, ranking, verification targeting, promotion, or headline decision belongs to that decision's complete selection path.

Before outcomes, register:

- family scope, version, decision, comparison key, and inferential target;
- all included mechanisms, observables, formulations, thresholds, subgroups, transformations, models, parameter regions, and data looks;
- the dependence structure and error criterion;
- how the candidate-generation and selection algorithm is reproduced or conditioned upon;
- the end-to-end null, sealed holdout, multiplicity, max-statistic, hierarchical, selective, sequential, online, false-discovery, Bayesian comparison or averaging, shrinkage, or other justified method;
- discovery, internal-validation, and independent-verification evidence.

Append every attempted branch, including weak, null, invalid, failed, and abandoned work. Never reset or shrink a family when a winner appears.

No single global-null method is mandatory. Choose the method whose assumptions and target match the actual selection path:

- sealed holdout when all development choices can be frozen before one untouched evaluation;
- end-to-end null or randomization when the complete generation, screening, and selection pipeline can be replayed under an appropriate null;
- selective inference when the selection event is characterized;
- sequential or always-valid inference for prospectively governed repeated looks;
- hierarchical multiplicity when the scientific family structure is prespecified;
- Bayesian model comparison or averaging when the candidate set, priors, likelihood, decision rule, and sensitivity analyses are declared.

Document what the chosen method covers and omits. Bayesian analysis does not erase prior exposure or outcome-driven expansion of the model set.

Direct ranking requires a common scientific decision, target population, supported sample, estimand, evidence stage, and materially comparable data-quality regime, or a prespecified validated mapping to a common scale. Otherwise retain results as `parallel_conclusion` or `support_limited_candidate`. Do not mechanically combine scientifically unrelated estimands, samples, quality regimes, or null distributions. When mechanisms legitimately compete for one headline conclusion, use a justified cross-mechanism gate or omnibus family, followed by prespecified within-mechanism localization. An omnibus rejection says only that some signal exists; it does not identify a mechanism.

When an adaptive mechanism or formulation is added:

1. record it before execution;
2. version the inventory and affected family;
3. update inference using a valid adaptive method, or keep the result exploratory;
4. preserve the original family and every prior branch.

Technical failures without a statistic remain in the ledger but receive no fabricated inferential value. Predeclare replacement and retry rules when failures could affect selection.

## 6. Separate Evidence Stages

- `exploratory`: candidate generation, adaptive formulations, model search, screening, and ranking.
- `internal_validation`: same-source resampling, cross-validation, alternate models, proxy changes, or robustness checks.
- `independent_verification`: a sealed holdout or independent dataset or experiment tests a fully frozen candidate.

Keep verification data, labels, benchmark evaluators, or experimental outcomes sealed until sample, preprocessing, features, formula, model, hyperparameters, seed policy, statistic, and decision rule are frozen.

Fit imputation, scaling, feature selection, and tuning only inside discovery folds or discovery data. Split by the independent scientific unit. Use nested validation when selection and performance estimation would otherwise reuse folds.

Evaluate a sealed holdout once. If its feedback changes development, mark it `compromised`. When data are too small for a useful holdout, use `internal_only`, quantify instability, and require future untouched evidence for promotion.

Earlier inspection of the same or overlapping verification units compromises independence even if the split, code, or skill version later changes. Link evidence-stage assignments to the Prior-exposure Audit.

## 7. Handle Stochasticity Honestly

- Use one fixed seed only for debugging or exact reproduction.
- Predeclare a common seed or realization set when randomness could change ranking, sign, uncertainty, or interpretation.
- Freeze the aggregation, pairing, retry, failure, and precision-based seed-expansion rules.
- Report actual seeds, failed or nonconverged runs, between-seed variation, and aggregation.
- Never add, remove, select, or report seeds because they improve effect direction, significance, or rank.
- Do not treat seeds as independent scientific sample units.
- Separate optimization noise and Monte Carlo error from data, model, and sample uncertainty.

## 8. Stop by Saturation and Coverage

Do not use a universal round, mechanism, or candidate count as the scientific stopping rule.

Freeze:

- the inventory-audit protocol and saturation sequence;
- the eligibility and coverage-cell closure rules;
- selection-family and evidence-separation rules;
- safety, governance, user-specified, data-look, and execution-resource limits.

Scientific completion requires `inventory_saturated`, `coverage_complete`, `search_ledger_audited`, and `decision_contract_applied` for the same inventory version.

If user limits, compute, cost, storage, time, or authorization end first, pause or stop execution with every open cell listed. Do not call the search saturated or complete. Do not stop merely because a favorable threshold was crossed or continue merely because results are null.

## 9. Promotion Checklist

Before promotion, verify:

- the computed estimand matches the stated claim;
- screening evidence and decision-scale evidence follow the frozen mapping and discordance rule;
- support and sensitivity justify the interpretation;
- every selection-influencing branch and data look is recorded;
- inference covers the complete generation-to-promotion selection path and its adaptive versions;
- the Decision Contract, comparison key, tie rule, and inconclusive rule were applied;
- prior exposure is audited and evidence-stage claims respect it;
- the formulation's timing and evidence stage are labeled correctly;
- verification evidence remained untouched;
- stochastic variation is quantified without favorable-seed selection;
- the effect exceeds a meaningful scale and dominant systematic floor;
- weak, failed, null, inconclusive, artifact, and invalid branches remain visible;
- any completeness statement is restricted to the current data-supported inventory version.
