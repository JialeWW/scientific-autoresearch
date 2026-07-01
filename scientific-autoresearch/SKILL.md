---
name: scientific-autoresearch
description: "Use for general scientific autoresearch: guiding an agent through mechanism-first hypothesis generation, testable claims, falsification, evidence review, autonomous next-step decisions, and reproducible reports in empirical or computational science."
---

# Scientific Autoresearch

Use this skill for research tasks that require hypothesis formation, mechanism design, iterative testing, failure analysis, and next-step decisions. Apply it as a research posture for turning scientific questions into testable claims and evidence-based decisions.

## Core Idea

Autoresearch is a loop:

```text
question -> mechanism -> testable claim -> data/model -> falsification -> interpretation -> next question
```

The agent should not ask "what test can produce significance?" It should ask:

1. What is the scientific claim?
2. Why would it be true physically, biologically, statistically, or mechanistically?
3. What observation, experiment, simulation, or model output would change belief?
4. What would make this claim fail?
5. Is the expected effect large enough to matter in physical, instrumental, or domain units?
6. Which statistical, systematic, model-choice, and sample-variance uncertainties could dominate?
7. What must be recorded so another agent can reproduce the step?

## Claim-First Workflow

Before doing analysis, classify the current step:

- Detection: Does a phenomenon, feature, signal, event, or component exist?
- Measurement: What is the value and uncertainty of a quantity?
- Association: Does one quantity vary with another in a physically or mechanistically meaningful way?
- Causal/mechanistic inference: Is the proposed mechanism necessary, sufficient, or merely consistent?
- Model comparison: Which model explains or predicts the data better?
- Population inference: What distribution, rate, scaling law, or latent structure describes the sample?
- Method validation: Does the pipeline recover known truth on controls, mocks, or simulations?
- Anomaly discovery: Which objects or cases violate the current model, and are they real?

The statistic, plot, and robustness tests must match the claim type.

## Observable Geometry

The observable must match the mechanism's geometry, not merely use convenient columns.

- If the mechanism is **nearest-neighbor or triggering**, proximity, minimum distance, or presence/absence tests may be appropriate.
- If the mechanism is **additive, cumulative, or line/path/volume integrated**, test cumulative weighted observables. A nearest-object or detection/non-detection test is not sufficient.
- If the mechanism is **background-relative**, compare the target measurement to a matched local or global background, and state what is being normalized away.
- If the mechanism is **threshold-like**, define the threshold before scanning, or label the scan exploratory.
- If the mechanism is **distributional**, compare full distributions and not only means or correlations.
- If the objects have an **object-specific natural scale**, fixed apertures are only sanity checks. Test at least one scale-normalized observable when scientifically justified: distance/radius, time/period, wavelength/linewidth, dose/body mass, count/exposure, signal/resolution element, or another natural unit. If scale normalization is impossible, ambiguous, or unreliable, record why.

Any support flag or match definition must pass a physical-scale audit before it is treated as evidence. Do not accept "matched", "covered", "detected", or "supported" as physically meaningful just because at least one object, feature, event, or catalog entry was found. Summarize the match geometry: number of matches per target, nearest-match distance/window distribution, median or typical match distance/window, upper-tail distance/window, and the conversion into the relevant physical, temporal, spectral, instrumental, or natural units. If the matched objects are mostly outside the scale where the proposed mechanism can operate, relabel the variable as footprint, background, environment, or selection support rather than mechanism support.

Before declaring a mechanism exhausted, check that the tested formulations span the expected geometry: proximity, cumulative contribution, weighting, scale/window, support/missingness, and background contrast when relevant. Use the **Mechanism Coverage Checklist** in `references/round-gate-checklist.md` before labeling a mechanism `null_result`, `rejected`, or exhausted. If a relevant geometry class is untested but feasible with current data, the mechanism should usually be labeled `active_needs_better_observable`, `weakened`, or `support_limited_candidate` rather than `null_result`.

## Data Availability and Support Audit

Before testing a scientific association, detection, or model improvement, establish whether the available data can actually support the question. Do not infer coverage from successful matches alone.

For every dataset or catalog used, separate:

- in-footprint / observable / exposed cases,
- out-of-footprint / unobservable / unexposed cases,
- in-footprint but nondetected cases,
- detected cases,
- cases excluded by quality, redshift, time, wavelength, sensitivity, resolution, or eligibility rules,
- true zeros if they are scientifically meaningful.

Then report the supported sample for each candidate separately. A target can be available for one mechanism and unavailable for another. If footprint, exposure, depth, completeness, or support masks are missing, build the most conservative support proxy possible and label it as approximate. Do not treat "no detected object" as "physical zero" unless the survey sensitivity and support are adequate for that claim.

A data-availability audit should be completed before running correlation, classification, regression, or model-comparison tests. If the supported sample is small, biased, or ambiguous, the correct status may be `support_limited_candidate`, `needs_data`, or `diagnostic`, even if the statistic is numerically strong.

Availability, support, footprint, exposure, or missingness classes are diagnostic strata by default, not physical control samples. Do not subtract, normalize, residualize, calibrate, or otherwise transform the scientific response using unsupported, unavailable, missing, or out-of-footprint cases unless there is an explicit scientific or instrumental reason that those cases represent the same physical background or calibration state. Otherwise, the analysis can turn selection effects into the response variable. Use such classes first for stratification, sensitivity tests, and confounder audits.

## Failure-Mode Driven Observable Redesign

When a physically motivated raw observable weakens under sample expansion, has many zeros, depends strongly on survey support, or fails in a structured way, do not immediately demote the mechanism. First ask whether the observable is measuring the wrong quantity. This is a diagnostic prompt, not a license to rescue every null result with a new transformation.

Run an observable-redesign audit:

1. Are zeros true physical absence, nondetections, unsupported regions, censored values, or below-background cases?
2. Does the mechanism predict an absolute amount, or an excess/deficit relative to a local, survey, model, or matched-control background?
3. Would a background-relative observable better match the claim: observed-minus-expected, observed-over-expected, residual from matched controls, random-point subtraction, continuum/background subtraction, or signed excess/deficit?
4. Should the redesigned observable be allowed to take negative values because the mechanism includes deficit, avoidance, underdensity, suppression, or lack of signal?
5. Does sample expansion weaken the raw signal because the new sample changes support, background, depth, resolution, or selection rather than because the mechanism disappeared?

If current data can support a matched background or random-control estimate, and the mechanism genuinely involves background, baseline, exposure, support, or contrast, consider testing one background-relative redesign before declaring the mechanism null. Label the redesign exploratory unless the transformation was frozen before looking at the result.

### Background / Contrast Redesign Trigger

If a raw absolute observable is weak or null but fails in a structured way, do not declare the broader mechanism exhausted until a background/contrast audit has been completed or explicitly ruled impossible.

Triggers include:

- many zeros or nondetections inside the otherwise supported sample,
- signal disappears or reverses after sample expansion,
- different quality, localization, instrument, exposure, or support classes show different signs,
- the observable correlates strongly with redshift, volume, depth, exposure, survey support, or selection,
- a unit/physical-scale repair reduces but does not remove confounding,
- raw absolute amount is plausibly less relevant than excess, deficit, residual, contrast, percentile, or expected-vs-observed structure.

When a trigger is present, ask whether the mechanism predicts an absolute amount or a deviation relative to an expected background. If a valid background can be built from in-support, matched, randomized, modeled, continuum, exposure, or otherwise scientifically defensible controls, test one pre-declared background/contrast formulation. If no valid background can be built, state why and keep the mechanism status limited rather than pretending the raw observable exhausts the mechanism.

Distinguish **predictor-side contrast** from **response-side residualization**. If the scientific mechanism says the exposure, foreground, environment, input, treatment, or stimulus is above or below its expected background, then construct the contrast on that predictor side, for example:

```text
observed predictor - expected predictor from matched/random/control cases
```

or an explicitly justified ratio, percentile, or standardized residual. Residualizing the response variable against redshift, time, baseline, continuum, batch, calibration, or matched controls can be a useful robustness check, but it is not the same as testing whether the predictor itself is an excess or deficit. Report which side was contrasted. Do not call a response-side correction a foreground/background, exposure/background, or environment/background contrast unless the response itself is the object whose background is being modeled.

## Multi-Factor Mechanisms

Many scientific effects are not controlled by a single variable. If the proposed mechanism plausibly depends on multiple necessary or modulating factors, do not only rank each feature independently. Ask whether the observable should combine factors in a mechanism-matched way.

Examples of physically motivated combinations include:

- amplitude x path length,
- density x volume,
- mass or luminosity weighted by impact parameter,
- rate or count normalized by exposure,
- signal divided by noise or instrumental resolution,
- response as a function of dose and body mass,
- interaction terms that represent a specific mechanism.

Do not build arbitrary total scores merely to improve a metric. A composite observable should have a clear estimand, stated units or scaling, and a failure mode. If single-factor tests are weak but point in a consistent physical direction, a mechanism-matched composite can be tested as an exploratory mutation. Label it exploratory unless pre-specified or externally validated.

## Candidate Portfolio

Do not collapse a research project into the first promising feature. Maintain a small candidate portfolio when multiple mechanisms, data layers, models, or observable families could explain the result.

For each candidate, record:

- **Mechanism**: why it could matter.
- **Observable family**: what proxy or measurement represents it.
- **Supported sample**: where the candidate can actually be tested.
- **Role**: primary candidate, support-limited candidate, diagnostic, confounder check, method validation, anomaly/case-atlas feature, needs data, or null.
- **Evidence**: effect size, uncertainty, sample size, search history, and strongest failure mode.
- **Next decision**: promote, freeze for verification, mutate formulation, keep as diagnostic, demote, reject, or request data.

The strongest numerical association is not automatically the best scientific candidate. A support/coverage/quality channel can be the strongest signal and still remain a confounder check. A weaker but mechanism-matched channel can be more scientifically important if it survives controls and has a clearer estimand.

When a confounder channel is stronger than a mechanism channel, decide whether it is itself physically meaningful. If yes, reframe it as a candidate mechanism and test it honestly. If it is only coverage, selection, quality, or availability, freeze both channels and seek a cleaner subsample, external data, or a stronger control before promoting either.

When a candidate begins to dominate attention, run a board-level check:

1. Are other plausible mechanisms still untested?
2. Is the apparent winner a physical observable or a support/selection proxy?
3. Does the result survive in its supported sample, not only in the full table?
4. Do related channels converge, contradict, or merely share missingness?
5. Should the next round stress-test the current candidate or explore a different family?

## Scientific Review Lens

Do not wait for a separate review skill. At each round, briefly review the work as a scientist would:

1. **Question and significance**: What gap, uncertainty, or decision does this test address?
2. **Method fit**: Do the sample, proxy, model, statistic, and control actually test that claim?
3. **Evidence strength**: Record effect scale, uncertainty, support, search space, and what would change belief.
4. **Interpretation boundary**: Separate measurement, proxy, association, mechanism-consistency, and proof.
5. **Systematics and scale**: Ask whether calibration error, model choice, selection, or sample variance is larger than the claimed effect.
6. **Literature context**: Check whether the result is novel, consistent with prior work, or apparently contradictory before promotion.
7. **Limitations and next gap**: Name what remains untested before proposing the next round.

For a fuller review prompt, read `references/scientific-review-lens.md`.

## Mechanism Versus Formulation

A null result usually rejects only the current formulation:

```text
mechanism + observable/proxy + support definition + statistic + quality cuts
```

It does not automatically reject the broader mechanism. Track both:

- **Mechanism-level status**: active, support-limited, weakened, rejected, needs data, or needs human judgment.
- **Formulation-level status**: untested, exploratory, primary candidate, null, artifact, or frozen.

Before demoting a mechanism, ask whether the observable actually represented the mechanism. If not, mutate the observable within the same mechanism before asking the user to choose a new direction.

Read `references/null-triage.md` when a round returns a null or weak result.

## Autonomous Mutation Before Asking

Do not stop after a null formulation just because the next formulation is not obvious. First run a null triage:

1. Is the null specific to one proxy, window, threshold, statistic, support definition, or quality cut?
2. Can the current data support a simpler, more direct, or more mechanism-matched observable?
3. Is there a scientific reason to suspect the raw observable failed because it should be background-relative, signed, normalized, residualized, matched-control corrected, or a mechanism-matched multi-factor composite?
4. Can a reasonable next formulation be tested without adding data or changing the scientific question?
5. If yes, run the next round autonomously and label it exploratory if choices are scanned.
6. Ask for human judgment only when the next step needs new data, a new scientific assumption, a changed claim, or a choice among multiple equally plausible interpretations.

## Autoresearch Loop

Before starting a multi-round run, respect any user-specified round budget. If the user explicitly asks for a budgeted run but gives no number, ask:

```text
How many autonomous rounds should I run before stopping to report back?
```

If the user does not specify a budget, do not block on a setup question. Continue autonomously as before: run round by round, report after each round, and stop only at a natural decision boundary such as needing new data, a new scientific assumption, a quality blocker, or human scientific judgment. If the user gives an explicit budget, do not exceed it.

For every iteration:

1. Freeze the state. Record inputs, code, parameters, random seeds, data versions, and the exact question.
2. State the claim. Write one sentence: "If [mechanism] matters, then [observable/model output] should [change/be detected/improve] under [conditions]."
3. Run a data-availability and support audit. Separate in-footprint, out-of-footprint, unsupported, nondetected, detected, censored, low-quality, true-zero, and ineligible cases for each candidate.
4. Define the supported sample. State exactly which cases can test the claim and which cannot.
5. Run a support/match physical-scale audit. Verify units, window sizes, aperture/radius/distance definitions, and the distribution of match distances or windows. Confirm that the supported sample is compatible with the mechanism's operating scale.
6. Freeze the primary analysis plan when the step is confirmatory: sample cuts, statistic, formula, thresholds, transformations, and random seed. Any post-result change downgrades that variant to exploratory.
7. Choose the minimal test. Use the simplest test that could change belief. Do not start with a maximally flexible model.
8. Define failure modes. Name the confounders, artifacts, or alternative explanations before looking at results.
9. Run the test and save per-object/per-case diagnostics. A plotted point should be reconstructable.
10. Decompose uncertainty. Separate statistical error, calibration/systematic error, model-choice uncertainty, and sample variance. If systematics dominate, do not pretend that more samples or more permutations solve the problem.
11. Report effect size in meaningful units or benchmarks, not only p-values. State whether the effect is large enough relative to measurement precision, intrinsic scatter, calibration limits, or known physical scales.
12. Run at least one meaningful falsification or robustness check. Prefer checks that could genuinely hurt the claim.
13. Use holdout, cross-validation, independent samples, mocks, or injection/recovery when sample size and data structure permit. A same-data robustness variant is weaker than out-of-sample validation.
14. Interpret conservatively. Distinguish evidence, proxy, model dependence, selection effect, and speculation.
15. If promoting a result, run a promotion audit. State the estimand, effect size, uncertainty budget, literature context, whether zeros/nondetections/unsupported cases were removed, whether the result was scan-selected or frozen, and how independent the supporting evidence is.
16. If the result is null or weak, run null triage before demoting the mechanism or asking the user.
17. Before declaring a mechanism null or exhausted, include the Mechanism Coverage Checklist and explain any relevant geometry class that was not tested.
18. Complete the Round Gate Checklist from `references/round-gate-checklist.md` in the round report.
19. End the round with a short status note: current best result, main caveat, and the next planned round.
20. Decide the next action: continue within the remaining round budget if one exists, otherwise continue until a natural decision boundary; freeze, mutate formulation, demote, reject, request data, write up, or ask for human scientific judgment.

When the round budget is exhausted, stop and report:

- what was learned so far,
- which candidate or mechanism is currently strongest,
- what failed or weakened,
- the next round you would run if allowed to continue.

Do not silently continue beyond an agreed round budget. If no budget was agreed, do not silently stop before a natural decision boundary.

## Research Heuristics

- Prefer mechanism-first features over p-value-first features.
- Prefer interpretable baselines before complex models.
- Treat negative and null results as information.
- Treat sample support and selection as part of the science, not bookkeeping.
- A support flag is not a mechanism. It becomes mechanism support only after its match geometry and physical scale are shown to fit the claim.
- A nondetection is not a zero unless the data are available, sensitive, and complete enough to make it a zero.
- Availability/support classes are not response-correction baselines unless independently justified as physical or instrumental controls.
- Separate exploration from confirmation.
- Keep failed branches visible in reports.
- Use simulations, randomization, matched controls, or injection/recovery when the null is not obvious.
- Prefer holdout or out-of-sample tests when enough data exist; if not, say that verification is internal only.
- Track an uncertainty budget. A beautiful statistic below the systematic floor is not a discovery.
- Report physical or domain-scale effect sizes. Statistical significance without practical scale is not enough.
- Do not merge many weak effects into a total score unless a model justifies the combination.
- Do not assume a mechanism is single-factor. If multiple weak channels point in the same physical direction, consider whether a mechanism-matched composite observable is justified.
- When a broad scan is necessary, report the scan as a scan; do not pretend the winning choice was pre-declared.
- Classify supporting evidence. Same-data internal consistency, alternate proxy, alternate sample, and external validation do not carry the same weight.
- A failed formulation is not the same as a failed mechanism.
- Prefer one autonomous, documented formulation mutation before asking the user to choose, if current data can support it.
- When raw observables have many zeros, structured failures, or support/background dependence, consider a scientifically justified background-relative or signed redesign before demoting the mechanism.
- If a raw absolute observable triggers the background/contrast redesign gate, do not declare the broader mechanism exhausted until one valid contrast formulation is tested or the absence of a valid background is documented.
- Stop optimizing when three reasonable same-mechanism mutations give diminishing returns, or when further progress requires a new assumption rather than more evidence. Freeze the candidate and write it up or request the missing data.

## Output Contract

Every step should produce:

- `report.md`: question, mechanism, method, result, interpretation, caveats, next decision.
- `inventory.json`: inputs, versions, hashes when practical, parameters, random seeds, sample counts, output paths.
- `summary.csv`: tested claims/features/models with metrics and status.
- `diagnostics.csv`: per-object/per-case data needed to rebuild plots and statistics.
- `figures/`: clear diagnostic or result plots.
- `reproduce_commands.txt`: exact commands and environment notes.
- An uncertainty/effect-size note in the report or inventory: statistical error, dominant systematic/model uncertainties, and the effect in meaningful units.
- A round-end status note: current result, current caveat, and proposed next round.
- A completed Round Gate Checklist. For final reports, include the Trial Completion Gate from `references/round-gate-checklist.md`.

For multi-candidate projects, also maintain:

- `candidate_registry.csv` or `.json`: one row per candidate mechanism/formulation with status and caveats.
- `candidate_board.csv` or `.md`: ranked or grouped current candidates, including diagnostics and confounder checks.

## Decision Labels

Use consistent labels:

- `primary_candidate`: worth developing into the main result.
- `support_limited_candidate`: interesting but limited by data coverage or sample support.
- `diagnostic`: useful for understanding, not a headline.
- `confounder_check`: support, coverage, quality, or selection variable that may explain apparent signal.
- `method_validation`: checks whether the measurement, baseline, model, or pipeline is trustworthy.
- `case_atlas`: useful as a small set of influential examples, not a population-level result.
- `selection_or_artifact`: likely caused by data collection, support, or measurement effects.
- `null_result`: physically motivated but unsupported by current data.
- `active_needs_better_observable`: mechanism remains plausible, but the current formulation did not test it well.
- `rejected`: not reproducible, not interpretable, or invalid under controls.
- `needs_human_judgment`: requires a scientific choice, not just computation.

## Guardrails

- Do not remove data because it weakens the result.
- Do not confuse missing data with physical zero.
- Do not call a proxy a direct physical measurement unless calibrated.
- Do not let a flexible model replace scientific explanation.
- Do not hide the number of attempted tests.
- Do not promote a threshold/window/formula winner from a scan as if it were a frozen confirmatory result.
- Do not call same-data variants independent validation.
- Do not promote a support, coverage, quality, or availability variable as a physical mechanism.
- Do not bury weak but mechanism-matched candidates just because a stronger confounder channel exists.
- Do not mark a broad mechanism as `null_result` when only one narrow formulation failed.
- Do not mark a mechanism as exhausted without an explicit Mechanism Coverage Checklist.
- Do not promote a statistically significant result whose effect is physically negligible or below the dominant systematic floor.
- Do not treat post-hoc thresholds, windows, transformations, or subgroup definitions as confirmatory.
- Do not treat zero-valued raw observables as automatically uninformative; audit whether they represent true absence, missing support, or below-background cases.
- Do not ask the user to pick the next step until null triage has tested whether a self-contained formulation mutation is possible.
- Do not continue optimizing once the next step requires new assumptions from the user.
- Default random seed: 42 unless the project specifies otherwise.

## References

Required during autoresearch runs:

- `references/round-gate-checklist.md`: mandatory end-of-round and trial-completion gates.

Read these only when needed:

- `references/thinking-principles.md`: deeper principles for scientific reasoning.
- `references/claim-types.md`: how to match claim types to tests and evidence.
- `references/scientific-review-lens.md`: reviewer-style checks for question, method, evidence, interpretation, and promotion.
- `references/null-triage.md`: how to respond when a formulation fails without over-killing the mechanism.
- `references/falsification-toolkit.md`: practical null tests and robustness checks.
- `references/report-contract.md`: reproducible report template.
