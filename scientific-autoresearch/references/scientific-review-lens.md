# Scientific Review Lens

Use this lens before promoting a candidate, claiming verification, or writing a final scientific interpretation.

## Question and Significance

- State the question and claim type in one sentence.
- State the gap, decision, uncertainty, anomaly, calibration, or mechanism the result addresses.
- Explain why the minimum meaningful effect matters.

## Method Fit

- Verify that the supported sample, unit of inference, proxy, model, statistic, scale, control, and uncertainty model test the stated estimand.
- Separate causal identification from estimation.
- Prefer a minimal test; justify every added degree of freedom.
- Check that governance and resource limits did not distort the design silently.

## Evidence Strength

- Report direction, magnitude, interval or uncertainty, sensitivity, sample support, and failure cases.
- Compare the effect with measurement precision, intrinsic variation, calibration limits, and the dominant systematic floor.
- Record the complete search space, data looks, multiplicity handling, and stochastic variation.
- State which observation would reduce belief.

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

## Interpretation Boundary

Use language that matches the design:

- measurement: a quantity was estimated under an uncertainty model;
- association: supported quantities vary together;
- mechanism-consistent: direction, scale, controls, and predictions fit a mechanism without proving it;
- causal: a defined effect is identified under explicit assumptions;
- selection or artifact concern: support, leakage, calibration, quality, or measurement may explain the result;
- verified or replicated: untouched or independent evidence tested a frozen claim.

## Literature and Novelty

- Verify the literature premise and include conflicting or null evidence.
- State whether novelty lies in data, measurement, method, population, scale, mechanism test, or replication.
- Do not claim novelty from an incomplete search.

## Promotion Audit

Before promotion, answer:

1. What exact claim or estimand is promoted?
2. Which sample and support conditions does it cover?
3. Was the formulation frozen or discovered through search?
4. Was sensitivity adequate and multiplicity handled?
5. What falsifier could have hurt it?
6. What is the verification status?
7. What dominant limitation must remain in the headline sentence?
8. What evidence would change the decision?
