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

## 4. Permit Only a Bounded Exploratory Mutation

Use one registered mutation only when it addresses a named failure mode without changing the scientific question, adding unauthorized data, or exceeding the mutation budget. Examples include:

- replace an indirect proxy with a more direct existing measurement;
- change an absolute quantity to a scientifically justified contrast;
- replace a fixed scale with a natural scale;
- repair a statistic that was insensitive to the predicted shape;
- test one mechanism-justified interaction or composite;
- correct a documented support, unit, or calibration error.

Specify the mutation before running it, assign a new formulation ID, and label it `exploratory`. Do not rewrite the original frozen result.

Do not mutate merely to find significance. Do not scan unregistered thresholds, subgroups, transformations, or models after a clean and sensitive null.

## 5. Decide the Mechanism Status

- Keep `active` when the formulation poorly represented the mechanism and a registered better formulation remains.
- Use `needs_data` when the required support, precision, measurement, or independent verification is absent.
- Use `weakened` when one or more adequately sensitive mechanism-matched formulations fail.
- Use `rejected` only after a decisive falsifier or several adequately sensitive, mechanism-matched tests contradict the mechanism.
- Use `needs_human_judgment` when plausible next formulations require different scientific assumptions.

Missing data, small samples, or invalid tests do not weaken a mechanism by themselves.

## 6. Stop Correctly

Stop when the registered mutation budget is exhausted, the remaining mutations change the question, verification data are unavailable, governance blocks the work, or further progress needs new data or assumptions.

Report the frozen result, sensitivity, support limits, mutation history, mechanism status, and the exact evidence needed to change belief.
