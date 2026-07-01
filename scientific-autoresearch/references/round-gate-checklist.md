# Round Gate Checklist

Use this checklist at the end of every autoresearch round. It is meant to prevent premature stopping and unexamined null conclusions.

## Round Gate

Before ending a round, answer each item briefly in the round report:

- Mechanism stated: What mechanism or claim did this round test?
- Observable fit: Why does the observable match the mechanism's geometry?
- Data availability: Which cases are in-footprint/observable/exposed, out-of-footprint/unobservable, in-footprint but nondetected, detected, excluded, ineligible, or true zero?
- Supported sample: Were available, missing, unsupported, ineligible, nondetected, censored, and true-zero cases separated?
- Support/match scale audit: What are the number of matches per target, nearest-match distance/window, typical match distance/window, upper-tail distance/window, and physical/natural-unit conversion? Are the matches within the scale where the mechanism can operate?
- Response-correction guardrail: Did the analysis avoid using availability, support, footprint, exposure, or missingness classes to subtract/normalize/residualize the scientific response unless independently justified?
- Evidence scale: What is the effect size in meaningful units, and is it large enough to matter?
- Uncertainty/systematics: What statistical, model-choice, calibration, selection, or sample-variance uncertainty could dominate?
- Falsification: What check could have hurt the claim, and what happened?
- Null triage: If weak/null, is the failure specific to a proxy, window, threshold, support definition, statistic, or quality cut?
- Multi-factor mechanism: If single variables are weak, do they point in a consistent direction that justifies a mechanism-matched composite observable?
- Observable redesign: If weak/null with structured failures, many zeros, or support/background dependence, is a background-relative, normalized, signed, residualized, or matched-control observable scientifically justified?
- Background/contrast trigger: If raw absolute observables are weak/null with structured zeros, support dependence, sample-expansion failure, quality-class sign changes, or redshift/volume/depth confounding, was a background/contrast audit completed or explicitly ruled impossible?
- Contrast side: If a contrast was used, was it constructed on the side required by the mechanism? State whether it is predictor-side contrast, response-side residualization, or both. Do not treat response-side residualization as proof of predictor-side excess or deficit.
- Candidate status: Which label applies now: `primary_candidate`, `active_needs_better_observable`, `support_limited_candidate`, `diagnostic`, `confounder_check`, `null_result`, `rejected`, or `needs_human_judgment`?
- Next mutation: What feasible same-data mutation remains, or why is none scientifically justified?
- Reproducibility: Were report, diagnostics, inventory/parameters, outputs, and reproduce commands saved?

## Mechanism Coverage Checklist

Before labeling a mechanism `null_result`, `rejected`, or exhausted, include this checklist:

- Proximity / nearest-triggering geometry tested or scientifically irrelevant.
- Cumulative / additive / path-integrated weighting tested or scientifically irrelevant.
- Physically normalized scale, resolution element, or natural unit tested when the mechanism has one; fixed apertures alone are not enough to exhaust such a mechanism unless scale normalization is impossible or scientifically unjustified.
- Data availability, footprint, exposure, sensitivity, completeness, or support mask assessed. If unavailable, the support proxy is labeled approximate.
- Support/match geometry is compatible with the mechanism's physical, temporal, spectral, instrumental, or natural scale. If matches are mostly outside that scale, the variable is treated as footprint/background/environment/selection support rather than mechanism support.
- Support, missingness, nondetection, censoring, and true-zero cases separated.
- Background-relative, contrast, residual, or matched-control formulation considered when support/background/exposure varies.
- Predictor-side contrast tested when the mechanism predicts excess/deficit in the predictor, foreground, exposure, environment, treatment, stimulus, or input. If only the response was residualized, label it as a robustness check rather than mechanism-complete contrast.
- If a background/contrast trigger is present and current data can support a valid background, at least one pre-declared contrast formulation is tested before declaring the mechanism exhausted. If not, the report explains why no valid background exists.
- Dominant systematics, selection effects, and confounders checked.

If a relevant geometry class is untested but feasible with current data, do not mark the mechanism exhausted. Use `active_needs_better_observable`, `weakened`, or `support_limited_candidate`.

## Trial Completion Gate

A trial can stop only when one of these is true:

- A candidate is strong enough to freeze for verification or write-up.
- All active candidates are promoted, rejected, blocked by missing data, or downgraded with a completed Mechanism Coverage Checklist.
- Every feasible same-data mutation has been run or explicitly documented as scientifically unjustified.
- Continuing requires new data, a new scientific assumption, a safety/quality fix, or human scientific judgment.
- The user-specified round budget is exhausted.

The final report must list:

- strongest current candidate,
- rejected/null mechanisms and their coverage-checklist status,
- active exploratory or support-limited candidates,
- what remains untested,
- what new data or assumptions would be required to continue.
