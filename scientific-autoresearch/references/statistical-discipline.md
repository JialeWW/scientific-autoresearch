# Statistical and Adaptive-Search Discipline

Use this file before confirmatory inference, repeated testing, adaptive scans, stochastic comparisons, or any result that may be promoted.

## 1. Freeze a Claim Card

For each claim, record:

```text
claim_id
claim_type
target_population_or_system
unit_of_inference
mechanism
exposure_or_model
comparator
outcome_or_observable
time_horizon_or_scale
summary_measure
expected_direction
minimum_meaningful_effect
supported_sample
assumptions
primary_or_exploratory
freeze_time
```

A substantive change to the sample, outcome, formula, threshold, model, or estimand creates a new formulation ID. A post-result formulation is exploratory.

## 2. Establish Sensitivity Before Interpreting a Null

Before testing, state the smallest effect that would matter scientifically and estimate the attainable precision, power, detectable-effect curve, upper-limit sensitivity, or simulation recovery rate.

After testing:

- use intervals, upper limits, equivalence bounds, posterior mass, or another claim-appropriate measure;
- call a result `null` only when the data were capable of detecting or excluding a meaningful effect;
- use `inconclusive` when uncertainty remains too wide;
- keep statistical significance separate from practical or physical importance.

## 3. Maintain a Search and Inference Ledger

Before looking at outcomes, register:

- claim families and primary, secondary, or exploratory status;
- planned outcomes, transformations, models, thresholds, subgroups, windows, and robustness checks;
- the number and timing of data looks;
- the error criterion and multiplicity, selective-inference, or sequential method;
- the discovery, validation, and sealed verification evidence;
- finite success, futility, safety, inconclusive, and resource boundaries.

Append every attempted branch, including failures and abandoned variants. Do not reset the ledger when a new formulation looks promising.

When many choices are scanned, use a method appropriate to the claim and dependence structure, such as family-wise control, false-discovery control, max-stat randomization, hierarchical testing, multilevel shrinkage, or a sealed verification sample. Conservative wording alone does not turn a scan winner into confirmation.

## 4. Protect Verification Evidence

- Keep verification data, labels, benchmark servers, or experimental outcomes sealed until preprocessing, feature selection, model, hyperparameters, sample, seed policy, and decision rule are frozen.
- Fit imputation, scaling, feature selection, and tuning only inside training folds or discovery data.
- Split by the independent unit: participant, site, batch, field, time block, spatial block, family, object, or another scientifically justified unit.
- Use nested validation when model selection and performance estimation would otherwise reuse the same folds.
- Evaluate a sealed holdout once. If its feedback changes development, mark it `compromised` and obtain new verification evidence.
- Treat bootstrap, alternate proxy, alternate model, resampling, and same-data cross-validation as internal evidence, not replication.

When data are too small for a useful holdout, state `verification_status=internal_only`, quantify instability, and require future independent verification for promotion.

## 5. Handle Stochasticity Honestly

- Use one fixed seed only for debugging or exact reproduction.
- Predeclare multiple seeds or independent realizations when stochastic variation could change ranking, sign, uncertainty, or scientific interpretation.
- Report the seed set, aggregation rule, between-seed variation, failed runs, and convergence failures.
- Select models by a frozen aggregate criterion, never by the luckiest seed.
- Distinguish Monte Carlo error from data uncertainty, model uncertainty, and sample variance.

## 6. Stop Without Outcome Shopping

Freeze the maximum rounds, candidate count, looks, compute, cost, and mutation count before outcomes. Stop at a predeclared success, futility, safety, inconclusive, or resource boundary.

Do not stop only because a favorable threshold was reached unless a valid sequential rule allows it. Do not continue only because results are null. Any unplanned continuation creates exploratory evidence and consumes the registered budget.

## 7. Promotion Checklist

Before promotion, verify:

- the estimand computed matches the claim stated;
- sensitivity was sufficient for the interpretation;
- all searches and data looks are recorded;
- multiplicity or adaptive selection is handled;
- verification evidence remained sealed;
- stochastic variation is quantified when relevant;
- the effect exceeds a meaningful scale and dominant systematic floor;
- the result is labeled frozen, exploratory, internally validated, holdout-verified, or externally replicated correctly.
