# Thinking Principles

Use these principles when substantive framing is ambiguous, evidence conflicts, or the next decision is unclear.

## Scientific Relevance and Metric Choice

Start with why a candidate bears on the scientific or operational decision and what evidence it predicts. For a mechanistic candidate, state why the effect could occur; for a predictive, computational, or design candidate, state its target role and performance claim. A metric matters only after the rationale, estimand, support, and failure condition are clear.

```text
If candidate C bears on decision Q, then evidence X should meet criterion D by a meaningful scale E in supported sample S.
```

## Result–Claim Alignment

A result is a number, fit, feature, detection, or comparison. A claim states what that result changes. Verify that the computed estimand matches the sentence used to describe it.

## Prespecification of Decision and Ranking Rules

Define the intended decision, comparable candidates, evidence rule, meaningful difference, tie rule, and inconclusive rule before inspecting candidate-specific outcomes. Apply the prespecified decision rule; nominal p-value alone is insufficient for scientific ranking.

## Evidence Stages for Exploration and Confirmation

Exploration is valuable when its search scope and failures remain visible. Classify a data-dependent result as exploratory and freeze it as a candidate for future verification.

Exposure follows the underlying information. Changing a sample, codebase, model, repository, workflow, or skill version does not make overlapping evidence untouched again.

## Candidate and Formulation Distinctions

A formulation combines a candidate, observable or test role, support definition, statistic or model, and analysis choices. A failed formulation may weaken its frozen candidate-level claim only when it was valid and adequately sensitive; weakening a mechanistic candidate additionally requires mechanism-matched evidence.

## Data Support as an Inferential Requirement

Define the testable sample from observation and support status. Separate cases that were not observed, observed but nondetected, observed and zero, censored, low quality, ineligible, or excluded by a frozen rule.

Direct comparison requires compatible target populations, supported samples, estimands, evidence stages, and material data quality, or a validated common-scale mapping. Otherwise, keep candidates as parallel conclusions or support-limited candidates.

## Sensitivity Requirements for Null Interpretation

Interpret p-values together with effect magnitude, uncertainty, and design sensitivity. Evidence of absence requires sufficient precision to exclude the minimum meaningful effect.

## Failure-Mode Analysis

Name selection, calibration, background, hidden covariates, leakage, outliers, flexible formulas, implementation errors, and proxy mismatch before testing. If no possible result can weaken the explanation, the claim lacks a discriminating falsification criterion.

## Evidence-Stage Classification

Same-data consistency, alternate proxies, cross-validation, simulations, sealed holdouts, and external replication carry different evidential weight. Label them separately.

## Retention of Negative and Invalid Results

Preserve null, inconclusive, invalid, and failed branches. They constrain future search and prevent repeated evaluation of an invalidated branch.

## Audit Requirements for Autonomous Research

For explicit systematic coverage, do not cap scientific possibilities with an arbitrary candidate or round count. Version a finite data-supported inventory, make every executable formulation set finite, preserve the full ledger, and stop scientifically only after the complete closure gate passes.

For outcome-informed work without a systematic-coverage objective, preserve the full candidate and selection history and classify its conclusion as bounded. A bounded classification defines claim level and leaves Core Rule 6's continuation standard unchanged. A fully frozen batch needs neither an inventory nor an adaptive search ledger.

The ledger must cover the complete selection path from candidate generation and modification through screening, ranking, verification targeting, and promotion. Use an inferential strategy suited to that path; no single global-null method fits every domain.

Data looks, governance, compute, cost, time, storage, and external actions require frozen boundaries. If an execution boundary is reached first, preserve all open cells and report the boundary. Outcome-dependent continuation aimed at obtaining a favorable result is prohibited.

## Scope of Coverage Claims

For explicit systematic coverage, the claim is limited to the declared versioned search space constructed from the current question and data products and does not establish open-world completeness.

## Governance and Authorization Requirements

Scientific utility does not confer execution authority. Respect data-use, privacy, ethics, safety, resource, and external-action boundaries before execution.
