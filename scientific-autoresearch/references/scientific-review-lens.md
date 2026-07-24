# Scientific Review Lens

Use this lens before promoting a candidate, claiming verification, or writing a final scientific interpretation.

First identify the actual scientific path: fully frozen before outcomes, outcome-informed, or explicitly systematic coverage. These paths make different completion claims.

## Contents

- [Question and Significance](#question-and-significance)
- [Method Fit](#method-fit)
- [Evidence Strength](#evidence-strength)
- [Adaptive-Path Audit](#adaptive-path-audit)
- [Scientific-Stop Audit](#scientific-stop-audit)
- [Coverage-Scope Audit](#coverage-scope-audit)
- [Evidence Independence](#evidence-independence)
- [Interpretation Boundary](#interpretation-boundary)
- [Literature and Novelty](#literature-and-novelty)
- [Coverage Wording](#coverage-wording)
- [Promotion Audit](#promotion-audit)

## Question and Significance

- State the question and claim type in one sentence.
- State the gap, decision, uncertainty, anomaly, calibration, or mechanism the result addresses.
- Explain why the minimum meaningful effect matters.
- For a fully frozen batch, state its compact scientific plan and decision rule. For outcome-informed or coverage work, state the decision, eligible comparisons, ranking evidence, and tie or inconclusive rule frozen before the applicable outcomes.

## Method Fit

- Verify that the supported sample, unit of inference, proxy, model, statistic, scale, control, and uncertainty model test the stated estimand.
- Separate causal identification from estimation.
- Prefer a minimal test; justify every added degree of freedom.
- Check that governance and resource limits did not distort the design silently.

## Evidence Strength

- Report direction, magnitude, interval or uncertainty, sensitivity, sample support, and failure cases.
- Compare the effect with measurement precision, intrinsic variation, calibration limits, and the dominant systematic floor.
- For outcome-informed or coverage work, record prior exposure, data looks, the generation-to-promotion selection path, adaptive additions, and stochastic variation. Add the complete versioned search space only for explicit systematic coverage.
- State which observation would reduce belief.

## Adaptive-Path Audit

For outcome-informed and systematic-coverage work:

- Did every generation, modification, screening, ranking, verification-targeting, and promotion step enter the correct complete path?
- Does the selected holdout, end-to-end null, selective, sequential, hierarchical, Bayesian, or other method match the path, dependence structure, and decision?
- Are directly ranked candidates genuinely comparable in target population, supported sample, estimand, evidence stage, and material data quality?
- Were actual seeds and failed realizations handled under the frozen policy?

A bounded report limits claim strength; it is not a stopping rule. Continue while Core Rule 6 identifies a material supported next test. Preserve unresolved work, and never claim saturation or coverage completion unless systematic coverage was explicitly requested and its closure conditions passed.

## Scientific-Stop Audit

Before claiming that no material test remains or ending open or adaptive research on a scientific-stop basis, use `completion-review.md`. Check declared identifiers and science-facing products deterministically, then challenge the stop rationale from source material before comparing it with the registry. Keep execution completion, scientific mapping, search-stop admissibility, and explicit coverage completion separate. A reviewer finding is only potentially material until the primary agent adjudicates it against support, feasibility, authorization, the current decision boundary, and the recorded selection path.

## Coverage-Scope Audit

For explicit systematic coverage only:

- Which inventory version and data-product scope were searched?
- Which complementary generation lenses were completed?
- Were candidate-forward and data-product-reverse audits separately scoped and both completed, and was every conditionally required complementary third source completed?
- Which candidates and coverage cells were eligible, unsupported, duplicate, invalid, blocked, or resource-deferred?
- What are the coverage numerator, denominator, and closure rules?
- What evidence supports inventory saturation?
- Did any result add a post-result candidate or formulation and reset the relevant audit?
- Is the scientific coverage record internally consistent across inventory versions, cells, ledger, families, queue, and decisions?

Resource-deferred or governance-blocked cells prevent coverage completion. Inventory saturation and coverage completion are separate claims.

## Evidence Independence

Classify support correctly:

```text
same-data consistency
alternate proxy
alternate model
resampling or cross-validation
known-truth simulation or control
sealed holdout
independent sample or experiment
```

Do not present internal checks as replication. If verification evidence influenced development, mark it compromised.

Call outcome-influenced choices exploratory. Call same-source resampling, cross-validation, alternate models, and robustness checks internal validation. Reserve independent verification for untouched evidence testing a fully frozen candidate.

Audit earlier use of the same or overlapping evidence. Changing samples, code, models, repositories, workflows, or skill versions does not reseal exposed data or restore confirmatory status.

## Interpretation Boundary

Use language that matches the design:

- measurement: a quantity was estimated under an uncertainty model;
- association: supported quantities vary together;
- mechanism-consistent: direction, scale, controls, and predictions fit a mechanism without proving it;
- causal: a defined effect is identified under explicit assumptions;
- selection or artifact concern: support, leakage, calibration, quality, or measurement may explain the result;
- verified or replicated: untouched or independent evidence tested a frozen claim.

## Literature and Novelty

- When a premise, novelty claim, or inventory source depends on literature, verify the search scope and include conflicting or null evidence.
- State whether novelty lies in data, measurement, method, population, scale, mechanism test, or replication.
- Do not claim novelty from an incomplete search.

## Coverage Wording

For completed mechanistic systematic coverage, when supported, use:

> We systematically searched a versioned inventory of mechanisms and observables testable with the available data products.

Always retain:

> This search does not establish exhaustiveness beyond the data-supported search space.

For other candidate classes, replace “mechanisms and observables” with the exact searched class and tests. Do not claim all possible mechanisms or models, universal exhaustiveness, or mechanism proof from coverage completion.

## Promotion Audit

Before promotion, answer:

1. What exact claim or estimand is promoted?
2. Which sample and support conditions does it cover?
3. What does the Prior-exposure Audit permit this evidence to be called?
4. Was the formulation frozen or discovered through search?
5. Was sensitivity adequate, and did inference cover the complete selection path rather than only winners?
6. Is comparison restricted to a justified family, with noncomparable results parallel or support limited?
7. Did the frozen ranking, tie, and inconclusive rules support the decision without a min-p default?
8. What falsifier could have hurt it?
9. What is the verification status?
10. What dominant limitation must remain in the headline sentence?
11. What evidence would change the decision?
12. If systematic coverage was explicitly requested, did the inventory actually meet saturation and coverage criteria, or did execution merely stop? Otherwise is the output clearly a bounded scientific result?
