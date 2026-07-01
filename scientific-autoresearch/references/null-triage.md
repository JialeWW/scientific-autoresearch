# Null Triage

Use this when a round gives a null, weak, or sign-inconsistent result.

## 1. Scope the Null

Write the narrow null:

```text
This observable, in this supported sample, with this statistic and these cuts, is unsupported.
```

Do not broaden it until justified.

## 2. Check Mechanism-Observable Fit

Ask:

- Did the observable directly represent the mechanism?
- Did the chosen window, aperture, threshold, time range, scale, or quality cut match the physical or statistical scale of the mechanism?
- Were zeros, nondetections, unsupported cases, and ineligible cases treated consistently with the claim?
- Was the statistic sensitive to the expected signal shape?

If the answer is no, keep the mechanism active and mutate the formulation.

## 3. Mutation Options

Choose one simple mutation before asking the user:

- Use a more direct proxy already present in the data.
- Change from an absolute observable to a contrast against a meaningful background.
- Change a fixed window to a scale tied to the object, process, instrument, or model.
- Split a broad candidate into formulation-level subclaims.
- Test a minimal statistic before adding model freedom.
- Save the scan grid if multiple choices are explored.

If the null has structured zeros, support/background dependence, sample-expansion failure, quality-class sign changes, or strong redshift/volume/depth confounding, treat this as a background/contrast redesign trigger. Before declaring the broader mechanism exhausted, test one scientifically justified contrast formulation or document why no valid background can be built from the current data.

## 4. Demotion Conditions

Demote a mechanism only when at least one is true:

- Multiple mechanism-matched formulations fail.
- A decisive falsification check contradicts the mechanism.
- The supported sample is too small or biased for the mechanism to be testable.
- The required data are absent.
- Continuing would require a new scientific assumption from the user.

## 5. Report Language

Good:

```text
The fixed-window count formulation is null; the broader mechanism remains active pending a better scale-matched proxy.
```

Bad:

```text
The mechanism is exhausted because one count test is null.
```
