# Falsification Toolkit

Choose checks that could change the conclusion. Distinguish falsification from generic specification robustness.

## Falsification Matrix

Register each important check before running it:

```text
claim_or_mechanism
main_alternative
test_or_control
prediction_under_claim
prediction_under_alternative
decision_consequence
sensitivity_or_power
result
status_change
```

A useful check has different expected outcomes under the claim and its main alternative. If every outcome can be rationalized as support, the claim is not falsifiable enough.

## Randomization and Placebos

- Shuffle labels, responses, positions, times, identities, or pairings according to the null-generating process.
- Preserve field, site, batch, redshift, exposure, time, clustering, or other dependence when required.
- Use placebo timing, locations, outcomes, or exposures that target the proposed pathway.
- Use a random control only when the random process represents the scientific null.

## Matched and Negative Controls

- Match on predeclared confounders and support conditions.
- Use negative-control outcomes or exposures to expose confounding, leakage, or selection.
- Use positive controls to verify that the design can recover a known effect.
- Keep control construction independent of the observed target result when possible.

## Influence and Stability

- Leave one independent unit, site, field, batch, or time block out.
- Report whether sign, scale, uncertainty, or status changes.
- Remove special cases only under a predeclared criterion; otherwise report the analysis as exploratory.
- Examine leverage and influence without deleting inconvenient cases.

Influence analysis diagnoses dependence on cases. It is not independent verification.

## Alternative Models and Measurements

- Change a defensible baseline, calibration, background, likelihood, measurement method, scale, or proxy.
- State which assumption the alternative tests.
- Keep the estimand fixed when calling the change a robustness check.
- If the estimand changes, create a new formulation ID.

## Simulation, Injection, and Known Truth

- Generate null data with the relevant dependence and support structure.
- Generate known nonzero effects over a meaningful scale range.
- Inject signals into realistic backgrounds.
- Measure bias, coverage, calibration, false-positive rate, recovery, and failure regions.
- Verify that the pipeline fails when the mechanism-specific component is removed.

## Invariance and Conservation

Test invariances, symmetries, units, conservation laws, monotonicity, or limiting behavior predicted by the claim. A violation may reveal implementation error or a false mechanism.

## Multiple Testing and Adaptive Search

- Record the complete selection path and all data looks, including generation, modification, screening, ranking, verification targeting, and promotion.
- Save complete grids, not only the winner.
- Use a justified end-to-end null, multiplicity, selective, sequential, hierarchical, Bayesian, or other path-covering method, or reserve sealed verification evidence.
- Keep a scan winner exploratory until verified.
- Do not use favorable physical storytelling as a substitute for selection control.

## Promotion Audit

Before promotion, ask:

1. What exact result would have weakened the claim?
2. Was the check frozen before the result it evaluates?
3. Was support and sensitivity sufficient for the check to fail meaningfully?
4. Does the check target the main alternative or only reproduce the same assumptions?
5. Is the evidence same-data consistency, alternate proxy, alternate sample, holdout verification, simulation truth, or external replication?
6. Did the candidate survive because the mechanism predicted the result, or because the explanation changed afterward?

Record the answer and its consequence for `mechanism_status`, `formulation_status`, and `verification_status`.
