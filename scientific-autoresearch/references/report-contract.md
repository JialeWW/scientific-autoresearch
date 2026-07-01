# Report Contract

Every autoresearch step should be understandable without the conversation.

## Required Sections

1. **Question**
   - What is being tested?
   - What scientific claim type is it?
   - Why does this test matter for the larger scientific question?

2. **Mechanism**
   - Why might the claim be true?
   - What sign, scale, or qualitative behavior is expected?
   - Mechanism-level status before and after this round.

3. **Inputs**
   - Files, versions, hashes when practical.
   - Sample definition and support logic.
   - Data availability audit: in-footprint/observable/exposed, out-of-footprint/unobservable, nondetected, detected, excluded, ineligible, and true-zero cases.
   - Units and coordinate/time/feature conventions.
   - Support/match scale audit: number of matches per target, nearest-match distance/window, typical match distance/window, upper-tail distance/window, and physical/natural-unit conversion.

4. **Method**
   - Formula or model.
   - Statistic or fitting method.
   - Random seed.
   - Inclusion/exclusion criteria.
   - Estimand: exactly what comparison, relation, detection, or prediction is being measured?
   - Formulation-level status: untested, exploratory, null, artifact, primary candidate, or frozen.

5. **Result**
   - Main metric.
   - Sample size.
   - Uncertainty or p-value if relevant.
   - Figure and table paths.
   - Effect scale or practical/scientific magnitude when it can be estimated.

6. **Falsification / Robustness**
   - What could have killed the result?
   - What happened under those checks?
   - Did any raw absolute observable trigger a background/contrast redesign audit? If yes, what contrast was tested or why was no valid background available?

7. **Evidence Audit**
   - Is the result frozen, exploratory, scan-selected, or a follow-up to a prior scan?
   - Were zeros, nondetections, unsupported cases, or low-quality cases excluded, and does that change the claim?
   - Were availability/support/footprint/missingness classes used only for diagnosis and stratification, or were they used to correct the response? If used for correction, what independent physical or instrumental justification supports that choice?
   - Label supporting checks as same-data internal consistency, alternate proxy, alternate sample, external validation, simulation, or control.

8. **Interpretation**
   - What the result supports.
   - What it does not prove.
   - Main limitations.

9. **Decision**
   - Continue, freeze, demote, reject, or ask for judgment.
   - Next step if continuing.
   - If the result is null, state whether the next action is mechanism demotion or formulation mutation, and why.

## Minimal Inventory JSON

```json
{
  "question": "",
  "claim_type": "",
  "inputs": [],
  "sample_counts": {},
  "main_method": "",
  "estimand": "",
  "mechanism_status_before": "",
  "mechanism_status_after": "",
  "formulation_status": "",
  "random_seed": 42,
  "main_result": {},
  "evidence_status": "",
  "robustness_checks": [],
  "decision": "",
  "outputs": {}
}
```

## Reproducibility Checklist

- Can another agent rebuild every plotted point?
- Are missing, zero, and unsupported cases distinguished?
- Was data availability checked before interpreting nondetections or missing matches?
- Does every support flag or match definition have a unit-checked physical-scale audit?
- Were support or missingness classes kept out of response correction unless independently justified?
- Are random seeds and random counts recorded?
- Are failed tests visible?
- Is the claimed estimand the one actually computed?
- Is a scan-selected result labeled as such?
- Are internal consistency checks distinguished from independent validation?
- If null, is it clear whether only the formulation failed or the broader mechanism is weakened?
- Did the agent attempt a same-data formulation mutation before asking for user direction?
- If raw observables failed structurally, did the agent complete or rule out a background/contrast redesign before declaring the mechanism exhausted?
- Is the next step justified by the result?
