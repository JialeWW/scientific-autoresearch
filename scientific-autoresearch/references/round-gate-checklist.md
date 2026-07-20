# Round Gate Checklist

Complete this checklist at the end of every executed round. Answer concisely and mark non-applicable adapter items with a reason.

## Universal Round Gate

- **Identity**: Are run ID, round ID, parent round, claim IDs, inputs, code state, parameters, and actual seed set frozen and recorded?
- **Governance**: Is the work inside authorized data, action, output, cost, and oversight boundaries?
- **Claim fit**: Does the statistic or model estimate the stated claim and estimand?
- **Support**: Which cases or conditions can and cannot test the claim? Are missing, unsupported, censored, low-quality, ineligible, and true-zero states separated when relevant?
- **Plan status**: Which choices were frozen before the result, and which are exploratory or scan-selected?
- **Search ledger**: Are all related tests, variants, thresholds, data looks, and failed branches recorded?
- **Evidence scale**: What is the effect in meaningful units, and how does it compare with the minimum meaningful effect and dominant systematic floor?
- **Sensitivity**: Could the design detect or exclude a meaningful effect? Is the result `null` or `inconclusive`?
- **Uncertainty**: Are statistical, systematic, calibration, model-choice, stochastic, and sample-variance components handled as applicable?
- **Falsification**: What result could have weakened the claim, and what happened?
- **Verification**: Is evidence unverified, internal-only, holdout-verified, externally replicated, compromised, or not applicable?
- **Privacy and reproducibility**: Are artifacts sufficient to audit the result while minimizing sensitive data and redacting secrets?
- **Statuses**: Are governance, mechanism, formulation, evidence-role, verification, and next-action fields taken from `references/status-schema.md`?
- **Budget**: What rounds, candidates, mutations, data looks, compute, cost, and time remain?
- **Decision**: Does the next action follow from the evidence and stay inside the frozen budget?

## Conditional Adapter Gates

### Observational Data

- Were availability, support, nondetection, censoring, and true zero separated?
- Does the observable match the mechanism's scale and geometry?
- Are match distances or windows, natural units, support completeness, background construction, and predictor-versus-response contrast handled correctly?

### Machine Learning or Simulation

- Did discovery remain separate from sealed test or benchmark evidence?
- Were preprocessing and tuning confined to discovery data?
- Is stochastic or numerical variation quantified with a frozen seed or realization policy?
- Are search size, compute cost, convergence, leakage, and baseline comparisons recorded?

### Causal or Experimental Work

- Is the causal estimand or experimental unit explicit?
- Are identification assumptions, randomization, blinding, controls, batches, replicates, protocol deviations, and stopping rules handled as applicable?
- Are live or regulated actions covered by documented authorization and competent oversight?

### Literature-Dependent Claims

- Are search scope, dates, source verification, conflicting or null evidence, and novelty boundaries recorded?

## Mechanism Rejection Gate

Before using `mechanism_status=rejected`, confirm:

- the formulation was mechanism-matched and valid;
- support and sensitivity were adequate;
- the main relevant scale, geometry, timing, background, interaction, or prediction classes were tested or declared irrelevant;
- dominant confounders, selection effects, leakage, and systematics were addressed;
- a decisive falsifier or several independent, adequately sensitive failures support rejection.

If not, use `active`, `weakened`, `needs_data`, or `needs_human_judgment`.

## Trial Completion Gate

Stop when at least one frozen condition applies:

- the round, candidate, mutation, data-look, compute, cost, or time budget is exhausted;
- a predeclared success, futility, safety, or inconclusive boundary is reached;
- a candidate is frozen for verification or write-up;
- every registered candidate has a justified terminal or blocked status;
- continuation requires new data, authorization, resources, assumptions, or human judgment.

Do not require “every feasible mutation”; require resolution of the finite registered portfolio. Do not continue only because no favorable result appeared.

The final report must list the strongest candidate, all terminal and blocked statuses, verification level, remaining uncertainty, untested questions, search scope, and exact requirements for continuation.
