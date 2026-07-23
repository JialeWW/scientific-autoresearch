# Statistical Method Selection

Use this reference only when the multiplicity, selection path, evidence partition, or stochastic method is not already clear. `decision-selection.md` contains the detailed rules for prior exposure, comparability, and the compact selection record. Do not recreate those records here.

## 1. Handle a Frozen Analysis Family Without Adaptive Machinery

A fully frozen batch may contain a finite prespecified family or bounded automated procedure when its candidate domain, proposal and evaluation rules, evidence partitions, methods, exclusions, randomization, budget, stopping, multiplicity or joint inference, decision, and reporting rules were frozen before outcomes. Record:

- stable member IDs and the claim or estimand each member addresses;
- the joint, omnibus, familywise, hierarchical, false-discovery, or model-based rule appropriate to the frozen decision;
- dependence assumptions or a resampling design when they affect calibration;
- the rule for discordant members and the joint decision.

Prespecified assumption checks, falsifiers, robustness checks, and frozen algorithmic search transitions belong to the frozen procedure. They do not create an adaptive ledger. Report the members and search state needed to reconstruct the joint decision. If an outcome changes the candidate domain, method, threshold, sample, stopping, decision, or reporting outside the frozen rules, append the outcome and decision contemporaneously, preserve the original result, and freeze the successor before continuing.

## 2. Choose an Adaptive-Path Method by Design

Cover the actual outcome-informed path using the simplest defensible option:

1. Use a sealed holdout once when all development choices can be frozen before untouched evidence is opened.
2. Use an end-to-end null or randomization when the complete generation, screening, and selection pipeline can be rerun under a scientifically valid null.
3. Use sequential or always-valid inference when repeated looks are prospectively governed and the stopping process is part of the design.
4. Use selective inference when the relevant selection event can be characterized and its assumptions are credible.
5. Use hierarchical multiplicity control when scientific families and their testing order were prespecified.
6. Use Bayesian model comparison or averaging when the candidate set, priors, likelihood, decision rule, and sensitivity analysis are scientifically defensible.

Another method is acceptable when it provides equivalent path coverage. State what the method covers, what it omits, its dependence assumptions, and how failed or invalid runs enter the procedure. If no valid method covers retrospective adaptation, keep the affected conclusion exploratory; do not manufacture confirmatory status.

## 3. Establish Support and Sensitivity

Before a decision-bearing test, freeze the supported sample, estimand, meaningful effect, statistic or model, assumptions, and falsifier. Estimate attainable precision, power, detectable-effect limits, recovery performance, or another claim-appropriate sensitivity measure.

- Use `null` only for valid, supported evidence that can exclude or meaningfully constrain the declared effect.
- Use `inconclusive` when uncertainty, support, or sensitivity cannot distinguish relevant alternatives.
- Use `artifact` or `invalid` for measurement, leakage, implementation, or assumption failures.

Run measurement-error sensitivity only when uncertainty can change support, matching, subgroup membership, thresholds, eligibility, ranking, or interpretation. Run transport analysis only when evidence is used beyond its analysis or selection population. Do not create placeholder records for irrelevant gates.

## 4. Protect Evidence Partitions

Distinguish `exploratory`, `internal_validation`, `independent_verification`, and `diagnostic` evidence. Fit preprocessing, imputation, scaling, feature selection, and tuning within discovery data or folds. Split by the independent scientific unit and use nested validation when tuning and performance estimation would otherwise reuse folds.

Evaluate sealed evidence once under its frozen rule. If its outcome changes development, mark verification compromised. Earlier inspection of overlapping units remains exposure even when the split, code, model, repository, workflow, or skill version changes.

State whether independence concerns evidence, prior-result blinding, implementation, or review. Untouched evidence can support independent verification with reused outcome-neutral software; a same-data blind rerun remains reproduction or internal validation. Require separate implementation only when implementation independence is itself part of the claim.

## 5. Handle Stochasticity Without Seed Selection

- Unless the user or an established project has fixed another value, use master seed `42` for exact reproduction and as the root of every stochastic stream.
- Reuse the same seed or stream rule across comparable candidates. Do not assign a fresh arbitrary seed to each run.
- When randomness could change ranking or interpretation, predeclare a common or paired realization set deterministically generated from master `42`, together with its derivation, aggregation, retry rule, and precision-based expansion rule.
- Retain actual seeds, failures, nonconvergence, and between-run variation.
- Never select seeds, checkpoints, or realizations because they improve direction, significance, or rank.
- Do not treat seeds as independent scientific sample units.

Native optimizer or simulation logs may remain in their reproducible system of record. Reference them from the compact scientific record and summarize selection-influencing state changes; do not copy noninfluential telemetry for ceremony.

## 6. Stop at the Correct Claim Level

A frozen analysis family can end with its prespecified joint decision. Outcome-informed work may issue a stage or bounded report, but whether execution ends is governed by Core Rule 6: continue while a material supported test could change the conclusion. Explicit systematic coverage uses the saturation and closure rules in `coverage-search.md`. A favorable result, promoted candidate, round count, or resource limit is not scientific completion.
