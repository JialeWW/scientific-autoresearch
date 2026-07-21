# Scientific Review Lens

Use this lens before promoting a candidate, claiming verification, or writing a final scientific interpretation.

First state the research profile. A bounded `fixed_test` report, an `adaptive_search` stage report, and a scientifically complete `coverage_search` make different completion claims.

## Question and Significance

- State the question and claim type in one sentence.
- State the gap, decision, uncertainty, anomaly, calibration, or mechanism the result addresses.
- Explain why the minimum meaningful effect matters.
- For `fixed_test`, state the frozen claim card and one decision rule. For adaptive or coverage search, state the frozen Decision Contract, eligible comparisons, ranking evidence, and tie or inconclusive rule.

## Method Fit

- Verify that the supported sample, unit of inference, proxy, model, statistic, scale, control, and uncertainty model test the stated estimand.
- Separate causal identification from estimation.
- Prefer a minimal test; justify every added degree of freedom.
- Check that governance and resource limits did not distort the design silently.

## Evidence Strength

- Report direction, magnitude, interval or uncertainty, sensitivity, sample support, and failure cases.
- Compare the effect with measurement precision, intrinsic variation, calibration limits, and the dominant systematic floor.
- For adaptive or coverage search, record prior exposure, data looks, the generation-to-promotion selection path, adaptive additions, and stochastic variation. Add the complete versioned search space only for coverage search.
- State which observation would reduce belief.

## Adaptive-Path Audit

For `adaptive_search` and `coverage_search`:

- Did every generation, modification, screening, ranking, verification-targeting, and promotion step enter the correct complete path?
- Does the selected holdout, end-to-end null, selective, sequential, hierarchical, Bayesian, or other method match the path, dependence structure, and decision?
- Are directly ranked candidates genuinely comparable in target population, supported sample, estimand, evidence stage, and material data quality?
- Were actual seeds and failed realizations handled under the frozen policy?

An `adaptive_search` may stop with a bounded stage report. It must preserve unresolved work and cannot claim saturation or coverage completion.

## Coverage-Scope Audit

For `coverage_search` only:

- Which inventory version and data-product scope were searched?
- Which complementary generation lenses were completed?
- Were candidate-forward and data-product-reverse audits independent, and was every conditionally required third source completed?
- Which candidates and coverage cells were eligible, unsupported, duplicate, invalid, blocked, or resource-deferred?
- What are the coverage numerator, denominator, and closure rules?
- What evidence supports inventory saturation?
- Did any result add a post-result candidate or formulation and reset the relevant audit?
- Did the machine consistency check pass across contracts, versions, ledger, families, queue, and statuses?

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

For a completed mechanistic `coverage_search`, when supported, use:

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
12. If this is `coverage_search`, did the inventory actually meet saturation and coverage criteria, or did execution merely stop? Otherwise is the output clearly a bounded test or stage report?
13. Did the profile-appropriate consistency check pass when artifacts were created?
