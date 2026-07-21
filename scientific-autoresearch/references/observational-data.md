# Observational Data Adapter

Use this adapter for catalogs, surveys, sensor records, remote observations, detection-limited samples, censored data, spatial or temporal matching, environmental exposures, or background-relative observables.

## 1. Audit Availability and Support

Separate, as applicable:

- in-footprint, observable, exposed, or eligible cases;
- out-of-footprint, unobservable, unexposed, or ineligible cases;
- supported but nondetected cases;
- detected cases;
- censored or thresholded measurements;
- cases excluded by predeclared quality, time, redshift, wavelength, sensitivity, resolution, or eligibility rules;
- true zeros with adequate support and sensitivity.

Do not infer coverage from successful matches. Do not turn “no detected object” into a physical zero unless support, completeness, and sensitivity justify it.

Treat availability, support, exposure, footprint, quality, and missingness classes as diagnostic strata by default. Do not use unsupported or out-of-footprint cases to subtract, normalize, residualize, or calibrate a scientific response unless an independent physical or instrumental argument makes them a valid background.

If measurement uncertainty can change support, matching, subgroup membership, thresholds, eligibility, or candidate ranking, propagate or perturb it through the relevant selection path before that quantity can control promotion. A recovery study, measurement model, resampling scheme, calibration analysis, or another domain-appropriate sensitivity design may satisfy the gate. Until it passes, keep quality-defined strata diagnostic or support limited. This conditional gate is method- and execution-context agnostic.

## 2. Match the Observable to the Mechanism

- For nearest-neighbor or triggering mechanisms, test proximity, minimum distance, or presence within a predeclared scale.
- For additive, cumulative, path-integrated, line-integrated, or volume-integrated mechanisms, test an appropriately weighted cumulative observable.
- For distributional mechanisms, compare the relevant distributions rather than only means or correlations.
- For threshold mechanisms, freeze the threshold before testing or label the scan exploratory.
- For object-specific natural scales, test a normalized quantity such as distance/radius, time/period, wavelength/linewidth, count/exposure, or signal/resolution element.
- For shells, outskirts, interfaces, boundary layers, transition zones, or edges, test a physically motivated annular or shell observable rather than only enclosed apertures.

A fixed scale that wins a scan is a diagnostic unless it maps to a consistent physical regime. Compare it with natural-scale formulations before calling it preferred.

## 3. Audit Match Geometry

For each match or support definition, report:

- number of matches per target;
- nearest-match distance or window;
- median or typical distance or window;
- upper-tail distance or window;
- units and conversion to the mechanism's physical, temporal, spectral, or instrumental scale;
- support completeness and sensitivity across the sample.

If matches lie outside the scale on which the mechanism can operate, relabel the variable as footprint, environment, background, coverage, or selection support rather than mechanism support.

## 4. Build Background or Contrast Observables Carefully

When a raw observable has structured zeros, support dependence, sample-expansion failure, depth trends, or quality-class sign changes, ask whether the mechanism predicts an absolute amount or a deviation from an expected background.

Construct a contrast only from scientifically defensible in-support matched, randomized, modeled, local, exposure-adjusted, or continuum/background controls. Freeze the contrast prospectively when possible; otherwise label it exploratory.

Distinguish:

- predictor-side contrast: observed exposure, foreground, environment, treatment, or input minus its expected background;
- response-side residualization: response corrected for baseline, calibration, redshift, time, batch, or another response model.

Response residualization does not prove predictor-side excess or deficit. State which side was contrasted.

## 5. Multi-Factor Mechanisms

Combine factors only when the mechanism defines the estimand and units, for example amplitude x path length, density x volume, signal weighted by distance or exposure, count/exposure, or a justified interaction.

Do not build an arbitrary score from weak variables merely to improve a metric. Register any post-result composite as exploratory.

## 6. Observational Completion Check

Map scientifically relevant classes of proximity, cumulative contribution, weighting, natural scale, support, censoring, background contrast, interaction, and selection effects into finite coverage cells or record why they are duplicate, unsupported, or irrelevant.

Before promotion or mechanism rejection, confirm that every eligible observational cell in the current inventory version was validly tested or explicitly classified under the coverage rules. If a feasible mechanism-matched class remains untested or only resource-deferred, use `active`, `weakened`, or `needs_data`, not `rejected`, and do not claim coverage completion.
