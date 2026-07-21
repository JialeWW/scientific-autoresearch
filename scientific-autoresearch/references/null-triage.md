# Null Triage

Use this file after a null, weak, unstable, or sign-inconsistent result. Preserve the frozen result before redesigning anything.

## 1. Write the Narrow Result

Use this form:

```text
This formulation, in this supported sample, with this estimand, statistic, sensitivity, and frozen choices, did not support the predicted effect.
```

Do not broaden a formulation-level result to a mechanism-level rejection without additional evidence.

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
- `needs_data` at mechanism level when current data cannot test the mechanism.

## 3. Check Mechanism-Observable Fit

Ask whether the observable represented the mechanism's scale, geometry, timing, background, sign, cumulative structure, natural unit, or interacting factors. Check whether the statistic was sensitive to the expected signal shape.

For observational support, geometry, censoring, or background questions, read `references/observational-data.md`.

## 4. Expand Formulations Without Result Shopping

Continue through remaining pre-result-frozen coverage cells when they represent distinct, scientifically justified observables, scales, support sets, or parameter regimes.

Add a new formulation only when it addresses a named failure mode without changing the scientific question or adding unauthorized data. Freeze a finite batch of new cells before inspecting their outcomes. Examples include:

- replace an indirect proxy with a more direct existing measurement;
- change an absolute quantity to a scientifically justified contrast;
- replace a fixed scale with a natural scale;
- repair a statistic that was insensitive to the predicted shape;
- test a finite preregistered set of mechanism-justified interactions or composites;
- correct a documented support, unit, or calibration error.

Specify every addition before running it, assign a new formulation and coverage-cell ID, record its parent and rationale, and label it `post_result_adaptive` and exploratory. Version the coverage matrix, append it to the existing selection family or a justified child family, and update the registered inference method. Do not rewrite the original frozen result.

Update the complete selection path, not only the final test count. A null-triggered proxy, sample, scale, threshold, model, or parameter change can affect generation, screening, ranking, and promotion even when it receives a new filename or code version. The Prior-exposure Audit remains in force.

Do not add variants merely to find significance. Stop expanding a mechanism when no substantively distinct observable or parameter regime remains supported by current data, later variants are only threshold nudges or duplicate proxies, the data cannot identify the distinction, or governance blocks the work.

Compute scarcity may defer valid cells, but it does not make the formulation space scientifically complete.

## 5. Decide the Mechanism Status

- Keep `active` when the formulation poorly represented the mechanism and a registered better formulation remains.
- Use `needs_data` when the required support, precision, measurement, or independent verification is absent.
- Use `weakened` when one or more adequately sensitive mechanism-matched formulations fail.
- Use `rejected` only after a decisive falsifier or several adequately sensitive, mechanism-matched tests contradict the mechanism.
- Use `needs_human_judgment` when plausible next formulations require different scientific assumptions.

Missing data, small samples, or invalid tests do not weaken a mechanism by themselves.

## 6. Stop Correctly

Stop scientific formulation expansion when the registered data-supported prediction domain is covered, remaining variants are redundant or unsupported, verification data are unavailable, governance blocks the work, or progress needs new data or assumptions.

If execution resources end first, use `resource_limited_pause`, list every deferred cell, and preserve an exact resume point.

Apply the frozen Decision Contract without promoting the least unfavorable nominal p-value. Report the frozen result, sensitivity, support limits, complete formulation history, selection-path handling, comparability status, mechanism status, and exact evidence needed to change belief.
