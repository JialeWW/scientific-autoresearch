# Canonical Status Schema

Use these fields exactly in reports, inventories, summaries, and candidate registries. Do not collapse them into one overloaded status.

## Governance Status

- `not_assessed`: The scope and permissions gate has not been completed.
- `cleared`: Required permissions and controls are documented for the planned actions.
- `restricted`: Work may proceed only within stated data, action, output, or oversight constraints.
- `blocked`: A required approval, authorization, safety control, or responsible human is absent.

## Mechanism Status

- `active`: Plausible and still testable; evidence is not yet decisive.
- `provisionally_supported`: Multiple mechanism-matched results support further verification without establishing proof.
- `weakened`: Adequately sensitive evidence reduced belief, but decisive rejection is not justified.
- `rejected`: A decisive falsifier or several adequately sensitive, mechanism-matched tests contradict the mechanism.
- `needs_data`: Current data cannot test the mechanism adequately. This is not evidence against it.
- `needs_human_judgment`: Progress requires a scientific, ethical, or strategic choice that computation cannot settle.

## Formulation Status

- `untested`: Defined but not executed.
- `frozen`: Specification was fixed before the relevant outcome was inspected.
- `exploratory`: Chosen or modified after inspecting related evidence.
- `supported`: The frozen formulation met its evidential criterion.
- `null`: Adequately supported and sensitive data are compatible with no effect or with effects below the minimum meaningful scale.
- `inconclusive`: Support, sensitivity, precision, validity, or sample size is inadequate to distinguish meaningful alternatives.
- `artifact`: The result is best explained by measurement, selection, leakage, implementation, or data-processing effects.
- `invalid`: The test cannot support interpretation because its assumptions, implementation, or data are invalid.

## Evidence Role

- `primary_candidate`: Main candidate being developed toward verification.
- `secondary_candidate`: Scientifically motivated alternative retained in the finite portfolio.
- `diagnostic`: Helps understand the data or failure mode but is not a headline claim.
- `confounder_check`: Tests coverage, quality, selection, support, or another alternative explanation.
- `method_validation`: Tests whether a measurement, model, baseline, or pipeline is trustworthy.
- `case_atlas`: Describes influential or anomalous cases without population-level inference.

## Verification Status

- `unverified`: No verification beyond the discovery analysis.
- `internal_only`: Same-data robustness, resampling, alternate proxy, or cross-validation only.
- `holdout_verified`: A sealed holdout was evaluated after the candidate was frozen.
- `externally_replicated`: Independent data or an independent experiment tested the frozen claim.
- `compromised`: Verification evidence influenced development or was inspected repeatedly.
- `not_applicable`: Verification is not relevant to this diagnostic or design-only step.

## Next Action

- `continue`: Run the next registered round within budget.
- `mutate`: Test one registered exploratory formulation change.
- `freeze`: Lock the candidate specification for verification.
- `verify`: Evaluate sealed verification evidence once.
- `replicate`: Seek or run an independent test under proper authorization.
- `demote`: Reduce priority without claiming rejection.
- `reject`: Mark a mechanism or formulation rejected with stated evidence.
- `request_data`: Stop pending additional data or support information.
- `request_approval`: Stop pending authorization, resources, or responsible oversight.
- `write_up`: Produce the final bounded report.
- `stop`: End because a frozen stopping condition was met.

## Required Candidate Registry Fields

Use at least:

```text
candidate_id
claim_id
mechanism
formulation
evidence_role
governance_status
mechanism_status
formulation_status
verification_status
supported_sample
effect_summary
uncertainty_summary
search_history
main_caveat
next_action
decision_reason
last_round_id
```

## Transition Rules

- Never use `null` when the correct status is `inconclusive`, `needs_data`, `artifact`, or `invalid`.
- Never change `exploratory` back to `frozen` on the same evidence. Create a new claim or formulation ID for prospective verification.
- Never use `holdout_verified` after tuning on the holdout; use `compromised`.
- Never use `rejected` only because data are missing or a sample is small.
- Record the previous status, new status, round ID, and evidence for every transition.
