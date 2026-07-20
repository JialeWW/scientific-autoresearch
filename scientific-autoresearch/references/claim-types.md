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

Require a mechanistic sign or shape expectation, supported sample, confounder and selection checks, an appropriate dependence measure, effect scale, and per-case or aggregate diagnostics.

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

## Population Inference

Question: What distribution, rate, fraction, scaling relation, or latent structure describes a population?

Require a target population, selection function, censoring or nondetection treatment, measurement-error model, intrinsic variation, clustering or dependence structure, and population-level uncertainty.

## Method Validation

Question: Does a measurement, model, estimator, pipeline, or experimental procedure recover known or defensible truth?

Require known-truth cases, simulations, standards, positive and negative controls, injection/recovery when applicable, failure examples, calibration, and sensitivity to assumptions.

## Anomaly Discovery

Question: Which cases violate the current model, and are the deviations real?

Require a frozen baseline, outlier or anomaly definition, multiplicity-aware search, data-quality and influence checks, and plausible physical and nonphysical explanations.

Treat discovered anomalies as exploratory until verified independently.

## Claim Card Check

Before execution, confirm that the claim card records the claim type, target population or system, unit of inference, observable or outcome, comparator, expected direction, minimum meaningful effect, supported sample, assumptions, and frozen or exploratory status.
