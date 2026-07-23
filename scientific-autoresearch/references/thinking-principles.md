# Thinking Principles

Use these principles when substantive framing is ambiguous, evidence conflicts, or the next decision is unclear.

## Substance Before Metric

Start with why a candidate bears on the scientific or operational decision and what evidence it predicts. For a mechanistic candidate, state why the effect could occur; for a predictive, computational, or design candidate, state its target role and performance claim. A metric matters only after the rationale, estimand, support, and failure condition are clear.

```text
If candidate C bears on decision Q, then evidence X should meet criterion D by a meaningful scale E in supported sample S.
```

## Result Is Not Claim

A result is a number, fit, feature, detection, or comparison. A claim states what that result changes. Verify that the computed estimand matches the sentence used to describe it.

## Decision Before Ranking

Define the intended decision, comparable candidates, evidence rule, meaningful difference, tie rule, and inconclusive rule before inspecting candidate-specific outcomes. The smallest p-value is not automatically the best scientific explanation.

## Exploration Is Not Confirmation

Exploration is valuable when its search scope and failures remain visible. A data-dependent result becomes a frozen candidate for future verification, not a retrospective confirmatory result.

Exposure follows the underlying information. Changing a sample, codebase, model, repository, workflow, or skill version does not make overlapping evidence untouched again.

## Formulation Is Not Candidate

A formulation combines a candidate, observable or test role, support definition, statistic or model, and analysis choices. A failed formulation may weaken its frozen candidate-level claim only when it was valid and adequately sensitive; weakening a mechanistic candidate additionally requires mechanism-matched evidence.

## Support Is Part of the Science

Rows in a table are not automatically a testable sample. Separate cases that were not observed, observed but nondetected, observed and zero, censored, low quality, ineligible, or excluded by a frozen rule.

Candidates with different target populations, supported samples, estimands, evidence stages, or material data quality are not automatically comparable. Keep them as parallel conclusions or support-limited candidates unless a validated common-scale mapping exists.

## Sensitivity Precedes Null Interpretation

A small p-value is not a meaningful effect, and a large p-value is not evidence of absence. Compare uncertainty with the minimum meaningful effect and ask what the design could detect or exclude.

## Failure Modes Are Features

Name selection, calibration, background, hidden covariates, leakage, outliers, flexible formulas, implementation errors, and proxy mismatch before testing. If no possible result can weaken the explanation, the claim is too vague.

## Evidence Has Levels

Same-data consistency, alternate proxies, cross-validation, simulations, sealed holdouts, and external replication carry different evidential weight. Label them separately.

## Negative Results Must Stay Visible

Preserve null, inconclusive, invalid, and failed branches. They constrain future search and prevent rediscovery of the same mistake.

## Autonomy Must Be Auditable

For explicit systematic coverage, do not cap scientific possibilities with an arbitrary candidate or round count. Version a finite data-supported inventory, make every executable formulation set finite, preserve the full ledger, and stop scientifically only after the complete closure gate passes.

For outcome-informed work without a systematic-coverage objective, preserve the full candidate and selection history and describe its conclusion as bounded rather than inventing saturation. Bounded is a claim level, not a stopping rule; continue under Core Rule 6 while material supported science remains. A fully frozen batch needs neither an inventory nor an adaptive search ledger.

The ledger must cover the complete selection path from candidate generation and modification through screening, ranking, verification targeting, and promotion. Use an inferential strategy suited to that path; no single global-null method fits every domain.

Data looks, governance, compute, cost, time, storage, and external actions still require frozen boundaries. If an execution boundary arrives first, pause with open cells rather than declaring the scientific space complete. Do not optimize until a favorable result appears.

## Coverage Is Not Universal Exhaustiveness

For explicit systematic coverage, the claim describes a versioned search space constructed from the current question and data products. It does not prove that no other physical, causal, computational, measurement, selection, model, simulation, feature, or design candidate exists.

## Governance Is Not an Afterthought

Scientific usefulness does not create authority. Respect data-use, privacy, ethics, safety, resource, and external-action boundaries before execution.
