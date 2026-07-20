# Machine Learning and Simulation Adapter

Use this adapter for benchmark optimization, predictive modeling, algorithm comparison, stochastic simulation, numerical convergence, surrogate models, or parameter sweeps.

## 1. State the Scientific Role

Classify the round as prediction, model comparison, method validation, parameter measurement, mechanism-consistency, or numerical-convergence testing. Do not treat benchmark improvement alone as a scientific mechanism.

Define the unit of generalization, target distribution, metric, baseline, minimum meaningful improvement, compute budget, and failure criterion.

Freeze a Decision Contract before model-specific outcomes: eligible candidates, comparable target and support regimes, ranking evidence beyond a nominal p-value, complexity or compute treatment, practical-equivalence rule, inconclusive rule, and the inference strategy for the complete search path. Audit prior benchmark, validation, leaderboard, simulation, seed, checkpoint, and parameter exposure. A new split, codebase, model family, repository, workflow, or skill version does not restore pristine test status when underlying evidence overlaps.

## 2. Seal Test and Benchmark Evidence

- Identify training, tuning, validation, and sealed test evidence before development.
- Remove duplicate or related units across splits using the scientifically independent unit.
- Fit preprocessing, normalization, imputation, feature selection, augmentation, and hyperparameters using discovery data only.
- Do not query test labels, hidden evaluators, or leaderboards repeatedly.
- Freeze the complete pipeline and evaluate the sealed test once.
- If test feedback changes the pipeline, mark verification `compromised` and require a new untouched holdout.

Use nested validation when tuning and estimating generalization would otherwise reuse the same folds. Report distribution shift, support gaps, leakage checks, and extrapolation limits.

## 3. Build a Versioned Search Inventory

Start from a reproducible baseline. Do not impose an arbitrary total limit on scientifically distinct mechanism, model, feature, architecture, simulation, resolution, or solver families. Keep every inventory version finite, explicit, deduplicated, and linked to current data or known-truth tests.

For each family, freeze a finite execution domain or a deterministic continuous-search rule:

- parameter range and units;
- grid, sampling distribution, or optimizer;
- resolution and refinement rule;
- metric and promotion criterion;
- convergence, precision, early-stop, and termination rules;
- compute estimate and resource priority.

Every objective evaluation, feature choice, architecture, checkpoint, early stop, resolution, solver, threshold, failure, and resource deferral that can affect selection enters the ledger and relevant selection family.

Candidates trained or evaluated on different target populations, supported samples, estimands, metrics, evidence stages, or materially different data quality are not directly ranked without a prespecified validated common-scale mapping. Keep them as parallel conclusions or `support_limited_candidate`.

A scheduler may apply one or more prespecified low-cost screening stages within declared comparable screening families before deeper evaluation. Record each screen's sensitivity, false-negative risk, threshold, and selection consequences. Screening and priority control execution order only; unrun deep-test cells remain open and in the coverage denominator. When resources end, preserve the complete queue and exact resume point.

Choose complete-selection-path inference that matches the workflow: a once-used sealed test set, an end-to-end null that reruns tuning and selection, selective or sequential inference, hierarchical control, Bayesian model comparison or averaging with declared priors and candidate set, or another justified design. Do not force every model or simulation task into one universal global-null method.

Residual or error analysis may motivate new cells. Give them new IDs and versions, mark them post-result adaptive and exploratory, and do not evaluate them as if predeclared.

When a finite compute envelope is explicitly authorized under `references/governance-safety.md`, execute and monitor registered jobs across rounds without repeated approval while they remain inside it. Track cumulative use. If the envelope ends with eligible cells open, use `resource_limited_pause`; do not call scientific coverage complete.

## 4. Quantify Stochastic and Numerical Variation

- Use a predeclared seed or realization set when randomness can change the conclusion.
- Report the mean or other frozen aggregate, between-run variation, convergence failures, and the aggregation rule.
- Use a common or paired seed design when comparing candidates unless another design is justified.
- Add realizations adaptively only through a predeclared precision rule, never because of effect direction, significance, or rank.
- Separate optimization noise, Monte Carlo error, finite-sample uncertainty, initialization variance, and model-choice uncertainty.
- For simulations, test resolution, timestep, domain size, softening, solver tolerance, conservation, and initial-condition variation when relevant.
- Use convergence curves, recovery tests, known-truth cases, or analytic limits rather than relying on a single run.

A single seed supports a smoke test or exact reproduction, not stochastic robustness. Seeds are nuisance realizations, not independent scientific sample units. Never select the luckiest seed, checkpoint, or realization.

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

Record inventory and family versions, data versions and split logic, code state, environment, hardware, precision, actual seeds, search and refinement rules, compute use, every configuration and failure, metric definition, uncertainty, coverage status, and sealed-test policy.

Use `verification_status=internal_only` for cross-validation or resampling. Use `holdout_verified` only after a truly sealed evaluation. Never report the luckiest run as the result.
