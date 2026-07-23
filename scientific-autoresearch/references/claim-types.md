# Claim Types

Classify each claim before choosing a statistic. Do not combine association, causality, mechanism-consistency, and prediction under one label.

## Detection

Question: Does a feature, signal, object, event, or component exist?

Require a signal model, background or noise model, threshold or decision rule, artifact checks, and sensitivity or an upper limit for nondetection.

## Measurement

Question: What is the value and uncertainty of a quantity?

Require a measurement model, calibration, unit definition, error propagation, supported sample, and sensitivity to defensible method choices.

## Association

Question: Do two supported quantities vary together?

Require a supported sample, confounder and selection checks, an appropriate dependence measure, effect scale, and per-case or aggregate diagnostics. Freeze a sign or shape expectation when the scientific theory supplies one; do not invent mechanistic directionality for a descriptive association.

Do not use causal language.

## Causal Effect

Question: Would an intervention or exposure change an outcome in a defined target population or system?

Require a causal estimand, assignment or identification strategy, comparator, time zero, outcome horizon, confounder strategy, overlap or positivity check, missingness assumptions, and sensitivity to violations or unmeasured confounding.

Read `references/causal-experimental.md`. If identification is not justified, downgrade the claim to association or mechanism-consistency.

## Mechanism Consistency

Question: Are the direction, scale, geometry, controls, and novel predictions consistent with a proposed mechanism?

Require competing mechanisms, mechanism-specific predictions, controls targeting alternatives, and at least one result beyond the fitted or discovery pattern.

Use “mechanism-consistent,” not “mechanism proven,” unless a design tests necessity or sufficiency directly.

## Model Comparison

Question: Which model predicts better, explains a specified structure better, or fits a defined evidence criterion?

State whether the goal is predictive or explanatory. Require comparable data and budgets, a frozen metric, flexibility control, residual or posterior-predictive checks, and sealed or nested evaluation when selection is adaptive.

For a purely predictive or operational decision, apply a frozen substantive eligibility rule tied to the target metric and deployment or scientific use. `mechanism_alignment` may be not applicable with a reason; predictive accuracy does not by itself establish a mechanism.

## Population Inference

Question: What distribution, rate, fraction, scaling relation, or latent structure describes a population?

Require a target population, selection function, censoring or nondetection treatment, measurement-error model, intrinsic variation, clustering or dependence structure, and population-level uncertainty.

## Method Validation

Question: Does a measurement, model, estimator, pipeline, or experimental procedure recover known or defensible truth?

Require known-truth cases, simulations, standards, positive and negative controls, injection/recovery when applicable, failure examples, calibration, and sensitivity to assumptions.

Distinguish structural conformance, behavioral conformance, empirical operating characteristics, and independent or cross-executor validation. A schema check or behavioral specification does not by itself establish error control, power, calibration, or scientific validity.

Before evaluation outcomes, freeze the benchmark task family, comparison conditions, evaluation unit, primary metrics, repetition count or Monte Carlo precision, stopping rule, and pass or interpretation rule. Separate development cases from sealed evaluation cases. If sealed outcomes motivate a method change, treat that split as development evidence and evaluate the changed method on a new sealed split.

When a claim attributes an observed difference to a treatment, method, system, or condition, define comparable blocks before outcomes. Hold fixed or explicitly model every material factor other than the target condition, including the case or sample definition, execution environment, configuration, repetition schedule, and evaluation procedure. Report incompatible blocks in parallel rather than subtracting their summaries. Treat case, execution, or evaluator uncertainty as estimated only when the design contains the corresponding replication.

Support claims about false-positive or false-promotion rates, power, interval coverage, or generalization across executors only with end-to-end known-truth evaluations that reproduce the relevant selection path. Scope conclusions to the tested tasks, conditions, executors, and method version.

## Anomaly Discovery

Question: Which cases violate the current model, and are the deviations real?

Require a frozen baseline, outlier or anomaly definition, multiplicity-aware search, data-quality and influence checks, and plausible physical and nonphysical explanations.

Treat discovered anomalies as exploratory until verified independently.

## Claim Card Check

Before execution, confirm that the compact scientific plan records the claim type, target population or system, unit of inference, observable or outcome, comparator, expected direction when applicable, minimum meaningful effect, supported sample, assumptions, and frozen or exploratory status. A fully frozen batch needs no search inventory or adaptive selection ledger; if an outcome motivates an unprespecified follow-up, record that decision and freeze the successor before continuing.
