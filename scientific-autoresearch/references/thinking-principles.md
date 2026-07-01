# Thinking Principles

## Mechanism Before Metric

A useful scientific test begins with a proposed mechanism or explanation. A metric only matters after the mechanism is clear.

Bad:

```text
Find the variable with the smallest p-value.
```

Better:

```text
If mechanism M contributes to observable Y, then proxy X should change Y in direction D, within the supported sample S.
```

## Exploration Versus Confirmation

Exploration is allowed. The danger is pretending exploration was confirmation.

For exploratory steps:

- Report the search space.
- Save failed attempts.
- Use conservative language.
- Use follow-up tests to freeze the result.

For confirmatory steps:

- Predefine formula, sample, statistic, and main robustness checks.
- Do not change them after seeing results unless the result is explicitly reclassified as exploratory.

## Result Versus Claim

A result is a number, fit, feature, detection, or comparison. A scientific claim says what that result changes.

Before elevating a result:

- Check that the computed estimand matches the sentence used to describe it.
- Check whether removing zeros, nondetections, or unsupported cases narrowed the question.
- Check whether the effect has a meaningful scale, not only a small p-value or high score.
- Check whether agreement across variants is internal consistency or genuinely new evidence.

## Formulation Is Not Mechanism

A mechanism can be plausible while one observable fails. A null result should be written as:

```text
This formulation is unsupported under this sample and statistic.
```

Do not write:

```text
This mechanism is false.
```

unless multiple mechanism-matched formulations, controls, and supported samples all fail or a decisive falsifier exists.

Useful status split:

- Mechanism status: active, weakened, support-limited, needs data, rejected.
- Formulation status: untested, exploratory, null, artifact, primary candidate, frozen.

## Support Is Science

A sample is not just rows in a table. It is a set of cases where the claim can be tested.

Always separate:

- Not observed.
- Observed but nondetected.
- Observed and zero.
- Observed but low quality.
- Physically ineligible.
- Excluded by predeclared rule.

Many false discoveries come from confusing these categories.

## Failure Modes Are Features

Before running a test, name what could make it fail:

- A selection effect.
- A calibration artifact.
- A background model.
- A hidden covariate.
- A single outlier.
- A flexible formula.
- A mismatch between proxy and physical quantity.

If no failure mode exists, the claim is too vague.

## Stop Conditions

Stop and ask for human judgment when:

- The next step changes the scientific question.
- The next step requires new data.
- Multiple physical interpretations remain equally plausible.
- The model can be tuned indefinitely.
- The result is ready to freeze into a reproducible claim.

Before stopping after a null, first ask whether a better observable can be constructed from the same data without changing the question. If yes, continue one documented mutation round.
