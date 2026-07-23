# Null Triage

Use this file after a null, weak, unstable, or sign-inconsistent result. Preserve the frozen result before redesigning anything. If it motivates a new sample, observable, threshold, statistic, model, or formulation, record the outcome and decision and freeze a successor before running it; the original batch remains unchanged.

## 1. Write the Narrow Result

Use this form:

```text
This formulation, in this supported sample, with this estimand, statistic, sensitivity, and frozen choices, did not support the predicted effect.
```

Do not broaden a formulation-level result to rejection of a wider candidate or mechanism class without additional evidence.

## 2. Check Validity, Support, and Sensitivity

Ask:

- Could the available data detect or exclude the minimum meaningful effect?
- Were unavailable, unsupported, missing, censored, nondetected, low-quality, and true-zero cases treated correctly?
- Did the implementation compute the stated estimand?
- Did convergence, calibration, leakage, measurement, or data-quality failures invalidate the test?
- Are uncertainty intervals wide enough that meaningful effects remain compatible?

Use:

- `null` only for an adequately supported and sensitive formulation compatible with no meaningful effect;
- `inconclusive` when precision or support is inadequate;
- `artifact` or `invalid` for measurement, selection, leakage, implementation, or assumption failures;
- `needs_data` at candidate level when current data cannot test its frozen claim.

## 3. Check Candidate-Test Fit

For a mechanistic claim, ask whether the observable represented the mechanism's scale, geometry, timing, background, sign, cumulative structure, natural unit, or interacting factors. For a model, feature, simulation, design, or operational claim, ask whether the test represented its frozen estimand, target use, support, and failure criterion. Check whether the statistic or model was sensitive to the expected signal shape.

For observational support, geometry, censoring, or background questions, read `references/observational-data.md`.

## 4. Expand Formulations Without Result Shopping

For explicit systematic coverage, continue through remaining pre-result-frozen coverage cells when they represent distinct, scientifically justified observables, tests, scales, support sets, or parameter regimes. For other outcome-informed work, preserve unresolved candidates and tests in the ledger without claiming a coverage denominator or saturation.

Add a new formulation only when it addresses a named failure mode without changing the scientific question or adding unauthorized data. Freeze a finite batch of new cells before inspecting their outcomes. Examples include:

- replace an indirect proxy with a more direct existing measurement;
- change an absolute quantity to a scientifically justified contrast;
- replace a fixed scale with a natural scale;
- repair a statistic that was insensitive to the predicted shape;
- test a finite preregistered set of substantively justified interactions or composites;
- correct a documented support, unit, or calibration error.

Specify every addition before running it, assign a new candidate or formulation ID, record its parent and rationale, and label it `post_result_adaptive` and exploratory. Version the affected selection family and update the registered inference method. In explicit systematic coverage, also assign a coverage-cell ID and version the coverage matrix. Do not rewrite the original frozen result.

Update the complete selection path, not only the final test count. A null-triggered proxy, sample, scale, threshold, model, or parameter change can affect generation, screening, ranking, and promotion even when it receives a new filename or code version. The Prior-exposure Audit remains in force.

Do not add variants merely to find significance. Stop expanding a candidate family when no substantively distinct observable, test role, formulation, or parameter regime remains supported by current data, later variants are only threshold nudges or duplicates, the data cannot identify the distinction, or governance blocks the work.

Compute scarcity may defer valid cells, but it does not make the formulation space scientifically complete.

## 5. Decide the Candidate or Mechanism Status

For a mechanism candidate:

- Keep `active` when the formulation poorly represented the mechanism and a registered better formulation remains.
- Use `needs_data` when the required support, precision, measurement, or independent verification is absent.
- Use `weakened` when one or more adequately sensitive mechanism-matched formulations fail.
- Use `rejected` only after a decisive falsifier or several adequately sensitive, mechanism-matched tests contradict the mechanism.
- Use `needs_human_judgment` when plausible next formulations require different scientific assumptions.

For a model, feature, simulation, design, or other candidate, apply `candidate_status` only to its frozen candidate-level estimand, performance standard, or failure criterion. Do not turn failure of one configuration into rejection of a broader candidate or mechanism class.

Missing data, small samples, or invalid tests do not weaken a candidate by themselves.

## 6. Stop Correctly

Stop expanding the affected candidate when its remaining variants are redundant or unsupported, its required verification data are unavailable, or progress needs new data or assumptions. In authorized iterative work, continue through other candidates only while they meet Core Rule 6's continuation standard; one candidate's blocker does not end otherwise admissible work. A bounded report describes claim strength rather than overriding that standard.

Explicit systematic coverage reaches scientific closure only after inventory saturation, coverage completion, an audited selection ledger, an applied final decision rule, adequate prior-exposure handling, and an internally consistent scientific coverage record.

If resources end first, preserve an exact resume point. In systematic coverage, use `resource_limited_pause` and list every deferred coverage cell in the open queue. In other outcome-informed work, preserve unresolved candidates and tests in the bounded report without inventing coverage cells.

Apply the frozen decision rule without promoting the least unfavorable nominal p-value. Report the frozen result, sensitivity, support limits, complete formulation history, selection-path handling, comparability, the applicable candidate or mechanism status, and the exact evidence needed to change belief.
