# Falsification Toolkit

Use checks that can genuinely change the conclusion.

## Randomization

- Shuffle labels or responses.
- Randomize positions, times, identities, or pairings.
- Preserve relevant structure such as redshift, exposure, batch, field, or support when needed.

## Matched Controls

- Match on known confounders.
- Compare against cases with similar support, quality, redshift, time, or instrument conditions.
- Use random controls only if the random process represents the null hypothesis.

## Jackknife and Influence

- Leave one object/field/batch out.
- Remove known special cases only if the criterion is stated.
- Report whether sign, scale, or significance changes.

## Alternative Models

- Change baseline model.
- Change calibration.
- Change background estimate.
- Change measurement aperture or window.
- Change proxy formula within physically motivated bounds.

## Simulation and Injection

- Generate mock data with no signal.
- Generate mock data with known signal.
- Inject synthetic features or effects into real backgrounds.
- Test recovery, bias, and false-positive rate.

## Quality and Support Splits

- High-quality subset.
- Low-systematic subset.
- Independent instrument/survey/batch.
- Supported-only versus unsupported diagnostic.

## Multiple Testing Discipline

- Record the search space.
- Save full grids when scanning.
- Use max-stat or conservative language for broad searches.
- Do not promote the winner without a physical reason.

## Promotion Audit

Before calling an exploratory branch a primary result:

- Restate the estimand in plain language.
- State whether the result includes supported zeros or only nonzero/detected cases.
- State which choices were fixed before seeing the result and which came from a scan.
- Freeze the promoted formula, window, threshold, sample, and statistic for the next check.
- Rank evidence by independence: same-data variant < alternate proxy < alternate sample < external validation.
- Ask whether the strongest check could have made the candidate worse, not only whether it can agree.

## Before Asking for Human Judgment

Ask only after this checklist:

- Does the next step require new data?
- Does the next step change the scientific question?
- Does the next step require a new scientific assumption rather than a new observable?
- Are multiple interpretations equally plausible and impossible to separate with current data?
- Has at least one same-data formulation mutation been attempted after a null?

If the current data can support a better mechanism-matched observable, run that mutation first and document it as exploratory.
