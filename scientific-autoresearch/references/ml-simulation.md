# Machine Learning and Simulation Adapter

Use this adapter for benchmark optimization, predictive modeling, algorithm comparison, stochastic simulation, numerical convergence, surrogate models, or parameter sweeps.

## 1. State the Scientific Role

Classify the round as prediction, model comparison, method validation, parameter measurement, mechanism-consistency, or numerical-convergence testing. Do not treat benchmark improvement alone as a scientific mechanism.

Define the unit of generalization, target distribution, metric, baseline, minimum meaningful improvement, compute budget, and failure criterion.

## 2. Seal Test and Benchmark Evidence

- Identify training, tuning, validation, and sealed test evidence before development.
- Remove duplicate or related units across splits using the scientifically independent unit.
- Fit preprocessing, normalization, imputation, feature selection, augmentation, and hyperparameters using discovery data only.
- Do not query test labels, hidden evaluators, or leaderboards repeatedly.
- Freeze the complete pipeline and evaluate the sealed test once.
- If test feedback changes the pipeline, mark verification `compromised` and require a new untouched holdout.

Use nested validation when tuning and estimating generalization would otherwise reuse the same folds. Report distribution shift, support gaps, leakage checks, and extrapolation limits.

## 3. Register a Finite Search

Start from a reproducible baseline. Register a finite set of mechanism- or failure-motivated model, feature, architecture, resolution, or solver families. State the resource allocation and promotion rule before running them.

Do not search an unlimited menu. Log every trial, configuration, early stop, failure, and compute cost. Use a frozen aggregate criterion rather than choosing the best observed seed or checkpoint.

Residual or error analysis may motivate one exploratory mutation, but that mutation must not be evaluated as if it were predeclared.

## 4. Quantify Stochastic and Numerical Variation

- Use a predeclared seed or realization set when randomness can change the conclusion.
- Report the mean or other frozen aggregate, between-run variation, convergence failures, and the aggregation rule.
- Separate optimization noise, Monte Carlo error, finite-sample uncertainty, initialization variance, and model-choice uncertainty.
- For simulations, test resolution, timestep, domain size, softening, solver tolerance, conservation, and initial-condition variation when relevant.
- Use convergence curves, recovery tests, known-truth cases, or analytic limits rather than relying on a single run.

A single seed supports a smoke test or exact reproduction, not stochastic robustness.

## 5. Use Scientific Falsifiers

Choose controls that target the proposed explanation:

- shuffled targets or randomized pairings;
- known-truth simulation or injection/recovery;
- invariance and symmetry tests;
- negative and positive controls;
- ablation of the mechanism-matched component;
- out-of-distribution or stress tests tied to the claim;
- comparison with an interpretable baseline under a matched budget.

State the expected outcome under the claim and under the alternative before running the check.

## 6. Report Reproducibly

Record data versions and split logic, code commit and dirty state, environment, hardware, precision, seed set, training or simulation budget, stopping rules, all tried configurations, metric definition, uncertainty, and final sealed-test policy.

Use `verification_status=internal_only` for cross-validation or resampling. Use `holdout_verified` only after a truly sealed evaluation. Never report the luckiest run as the result.
