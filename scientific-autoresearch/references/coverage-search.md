# Coverage-Based Scientific Search

Use this reference only when the semantic objective is systematic coverage of a finite data-supported search space, assessment of saturation, or scoped completion. Do not infer that objective from requests for depth, autonomy, thoroughness, optimization, a final report, or many analyses. Execute a fully frozen optimization procedure directly. If inspected outcomes change unfrozen scientific choices, keep a contemporaneous selection ledger and return a bounded result unless systematic coverage was independently requested; a ledger alone does not justify inventory saturation or coverage completion.

When the user explicitly requests full systematic coverage or scoped completion, advance autonomously toward inventory saturation and cell closure until completion or a real authorization, resource, governance, or scientific boundary is reached. If the user requests only a bounded coverage stage or coverage design, stop at that boundary with an exact open-queue report.

## Contents

- [1. Version a Typed Candidate Inventory](#1-version-a-typed-candidate-inventory)
- [2. Enumerate Through Complementary Lenses](#2-enumerate-through-complementary-lenses)
- [3. Define Finite Coverage Cells](#3-define-finite-coverage-cells)
- [4. Define Selection Families](#4-define-selection-families)
- [5. Audit Inventory Saturation](#5-audit-inventory-saturation)
- [6. Close Coverage](#6-close-coverage)
- [7. Schedule Without Shrinking Coverage](#7-schedule-without-shrinking-coverage)
- [8. State the Scope Honestly](#8-state-the-scope-honestly)

## 1. Version a Typed Candidate Inventory

Do not impose an arbitrary total limit on scientifically distinct candidates. At any execution point, however, the current inventory version must be finite, explicit, deduplicated, and version-frozen. Declare `candidate_type` as `mechanism`, `model`, `feature`, `simulation`, `design`, or another justified type.

Record at least:

```text
inventory_version
candidate_id
parent_candidate_id
candidate_type
candidate
distinct_role
inclusion_rationale
generation_lens
applicable_regime
predicted_signature
required_data_products
data_support_status
candidate_status
specification_timing
duplicate_of
```

Use `pre_result_frozen` when the entry was fixed before related outcomes were inspected and `post_result_adaptive` otherwise. Preserve every prior inventory version. Batch additions discovered at one audit checkpoint into one successor version and record the diff; never silently insert them into an old version. A legacy record may retain a mechanism-specific column name, but it must not force nonmechanistic candidates to make mechanistic claims.

Keep scientifically plausible but currently untestable entries with `candidate_status=needs_data`. They document the boundary of the available data but do not enter the executable coverage denominator.

Record data support as `supported`, `support_limited`, `diagnostic_only`, `unsupported`, or `not_assessed`. Direct promotion requires `supported`, but every nonduplicate `active`, `provisionally_supported`, or `weakened` candidate must still receive finite coverage; a limited, diagnostic, or unsupported role changes the cell's role or closure, not whether the active candidate is represented in the search map.

## 2. Enumerate Through Complementary Lenses

Freeze the inventory-audit protocol before outcomes. Use complementary lenses rather than one unconstrained brainstorming pass:

- candidate-forward decomposition of the substantive mechanisms, models, features, simulations, designs, or other declared candidate classes;
- data-product-reverse mapping from each authorized field, table, image, time series, model output, or experimental record to the candidates and alternatives it can test;
- scale, geometry, timing, regime, interaction, and boundary-condition predictions;
- measurement, calibration, selection, support, confounding, leakage, and numerical-artifact alternatives;
- residual and failure-mode review at declared audit checkpoints, with any additions marked adaptive.

The saturation audit always has two complementary, separately scoped directions:

1. candidate-forward: start from the declared candidate classes and enumerate distinct roles and predictions;
2. data-product-reverse: start from every authorized data product and ask which pathways, alternatives, and artifacts it can distinguish.

For a mechanistic search, candidate-forward is specifically a mechanism-forward audit; for other declared classes, use the corresponding model-, feature-, simulation-, or design-forward audit rather than forcing mechanistic language.

These directions are different enumeration procedures, not automatically statistically independent reviews. Freeze their starting bases and scopes separately, and disclose shared executor, context, prior-inventory visibility, or source material. A high-consequence run may add separated contexts or reviewers, but different people or models are not a universal minimum.

At Round 0, decide whether the problem warrants a third separately declared source, such as a targeted literature audit, formal theory or model enumeration, structured expert elicitation, or a failure-mode catalogue. If declared applicable, freeze its scope and completion rule and require it for saturation. Literature review is conditional: use it when premise, novelty, or inventory coverage depends on literature, not as a ritual for every run.

Track mechanisms separately from measurement, selection, quality, model, feature, simulation, design, and method candidates. Merge semantic duplicates within the appropriate type and record the surviving ID and justification.

A proposed addition is eligible as a new candidate only when it has all three: a distinct substantive role, at least one distinct prediction that current authorized data can test, and a possible effect on the frozen decision. A parameter value, threshold, proxy, or implementation variant without a distinct role remains a formulation under its parent candidate. Otherwise retain the proposal as a formulation, duplicate, out of scope, or needs data.

## 3. Define Finite Coverage Cells

For every eligible candidate, predefine a finite set of substantively matched cells:

```text
coverage_cell_id
inventory_version
candidate_id
observable_id
formulation_id
substantive_eligibility
mechanism_alignment              # required only for mechanism candidates
measurement_error_sensitivity
data_product_id
data_version_id
supported_sample_id
parameter_or_scale_domain
comparator
expected_signature
minimum_meaningful_effect
sensitivity_requirement
falsifier
selection_family_id
comparison_key
comparability_status
evidence_stage
execution_tier
specification_timing
```

The scientific space may contain any number of candidates over time, but each inventory version and each candidate's executable formulation set must be finite and auditable.

Construct cells through `candidate -> observable or test role -> formulation`. Use the coarsest cell that preserves a distinct scientific falsifier or decision role. One cell may cover a finite parameter domain under a frozen grid, sampling, marginalization, integration, recovery, or convergence rule; do not create one scientific cell per trivial parameter value. A constrained or full product is valid only when each axis and resulting cell has a frozen substantive, control, or diagnostic role; only decision-eligible cells enter ranking. Do not flatten unrelated candidate types, proxies, and parameter combinations into one ranked pool. For continuous spaces, freeze a substantively justified range plus one of:

- a finite grid and resolution;
- a sampling distribution and draw count;
- a marginalization or integration rule;
- an injection/recovery or response-surface map;
- a convergence tolerance and adaptive refinement rule.

Outcome-driven threshold nudging, proxy swaps, subgroup slicing, or parameter zooming create new exploratory formulation IDs. They expand the relevant selection family and cannot erase the original cell.

## 4. Define Selection Families

Every test capable of influencing the same candidate-generation, modification, screening, retention, ranking, verification targeting, promotion, or headline decision belongs to that decision's complete selection path. Read `decision-selection.md` before freezing these families.

Freeze family boundaries and an end-to-end null, hierarchical, max-statistic, selective, sequential, false-discovery, Bayesian model-comparison or model-averaging, sealed-holdout, or other justified inference method before outcomes when possible. Preserve the dependence structure when calibrating a family. The skill does not prescribe one universal global-null construction.

Direct comparison also requires a common decision, target population, supported sample, estimand, evidence stage, and materially comparable data-quality regime, or a prespecified validated mapping to a common scale. Store these as structured family fields together with `transportability_requirement` and `transportability_status`; an opaque comparison key is not enough. Do not force unrelated estimands, samples, quality regimes, candidate types, or null distributions into one universal family. Preserve noncomparable results as parallel conclusions or `support_limited_candidate`. If distinct candidates legitimately compete for one headline conclusion, define a cross-candidate gate or omnibus family, then use prespecified within-family localization.

When an adaptive inventory or formulation addition affects selection:

1. append it to the existing ledger before execution;
2. version the affected family;
3. update error allocation with a valid adaptive method or keep the result exploratory;
4. preserve all prior weak, failed, invalid, and abandoned branches.

Production technical failures that can affect which scientific cell is run, retained, ranked, or reported remain in the ledger and execution accounting; do not fabricate inferential values for them. Development and response-blind qualification failures stay in the engineering record unless they expose candidate outcomes or influence scientific selection.

## 5. Audit Inventory Saturation

Set `inventory_saturated=true` only when all conditions hold:

1. the question, scope, authorized data products, support rules, and eligibility rules have remained unchanged;
2. after the most recent eligible addition, one complete candidate-forward audit and one complete data-product-reverse audit have each covered every in-scope regime and data product;
3. every additional source or lens declared applicable at the audit checkpoint has completed its frozen audit;
4. all required audits produced zero new eligible, nonredundant, data-supported candidates;
5. every proposed addition, duplicate, exclusion, and needs-data decision is recorded with a reason.

The required audits must be distinct, prespecified inventory passes; ordinary execution rounds that happen not to suggest a new candidate do not count. Record each audit ID, source, starting basis, procedure, scope, prior-inventory visibility, shared-context disclosure, date, inventory version, additions, duplicate decisions, and unresolved gaps. Do not call the audits independent unless their actual separation supports that description.

A batch containing one or more new eligible candidates increments `inventory_version`, expands the coverage denominator, and resets the saturation sequence. Carry forward still-valid closed cells with explicit predecessor links; reopen only cells or families whose scientific meaning, support, formulation, or inference changed. New data products or a changed scientific question require a new inventory version and a recorded affected-scope assessment.

## 6. Close Coverage

A coverage cell closes only as:

- `tested_valid`: a valid test was completed and its result status recorded;
- `covered_by:<cell_id>`: another cell provides equivalent coverage under a recorded equivalence type, scope, assumptions, supporting evidence, and passing review; equivalence chains must terminate at a non-equivalence closure and may not cycle;
- `not_testable_current_data`: support, sensitivity, or identifiability was assessed and current data cannot test it.

`eligible_untested`, `scheduled`, `in_progress`, `invalid_open`, `resource_blocked`, and `governance_blocked` are open. An invalid test stays open whenever a feasible valid replacement exists.

Report closure by basis rather than one ambiguous coverage percentage:

```text
tested_valid_fraction
equivalence_closed_fraction
not_testable_fraction
classified_closed_fraction
open_fraction
```

Use the same eligible-cell denominator and active inventory version for every fraction. `classified_closed_fraction` is the legacy overall closure concept; it is not empirical testing coverage. Declare `coverage_complete=true` only when every eligible cell in that version is closed and the ledger and family-level inference are audited.

Scientific completion requires a contemporaneously preserved and internally consistent coverage record and:

```text
inventory_saturated
AND coverage_complete
AND search_ledger_audited
AND final_decision_rule_applied
AND terminal_decision_status
AND prior_exposure_audit_adequate_for_claim
AND coverage_record_consistency_reviewed
```

Resource, time, cost, authorization, or user-limit exhaustion does not close cells. Use `resource_limited_pause`, `governance_blocked`, or `user_limited_stop`, report every open cell, and preserve an exact resume point.

Use a persistent lightweight append-only or versioned ledger that captures every selection-influencing event contemporaneously. A compact coverage record is sufficient when it faithfully preserves the inventory, cells, saturation audits, ledger, decision, and open queue. Before claiming `complete_within_scope`, review that record for internal consistency. Retrospective reconstruction cannot supply omitted attempts or create pre-result status.

## 7. Schedule Without Shrinking Coverage

Scientific eligibility and execution priority are separate fields. A scheduler may first run one or more prespecified, low-cost screening stages within declared comparable screening families and then allocate deeper tests by dependency, cost, expected information gain, or feasibility. Record every screen rule, threshold, sensitivity or recovery check, and false-negative risk before use.

Qualify and execute independent analysis families separately. A family whose science-critical gates pass may produce a bounded result while unrelated families remain open. Shared inputs or calibrations block only dependent cells; a frozen joint decision rule blocks the joint comparison, promotion, or conclusion, not otherwise standalone family results. Never relabel an unfinished family or cell as covered.

Every screen and outcome that can influence progression enters the ledger and its selection path. A cell that fails a valid prespecified screen may close only if the screen itself provides the substantively matched sensitivity required by the cell; otherwise it remains open or is replaced by an explicitly justified coverage cell.

Queued, deferred, and resource-blocked cells remain in the coverage denominator. When resources end, serialize the full open queue, priority basis, dependencies, estimated resource need, and next admissible action.

## 8. State the Scope Honestly

When supported by the recorded audit, use:

> We systematically searched a versioned inventory of candidate classes and observables or tests supported by the available data products.

If the same inventory version met both stopping conditions, add:

> The inventory met its prespecified saturation criterion, and every eligible cell in that version was tested or explicitly classified.

Always preserve the boundary:

> This search does not establish exhaustiveness beyond the data-supported search space.

When the declared candidate class is mechanistic, the more specific wording “mechanisms and observables” is appropriate. In reports, summarize candidate and branch classes with counts and representative conclusions, and link the complete inventory, registry, and ledger; do not narrate every row in prose. Do not write “all possible mechanisms,” “all possible models,” “exhaustive scientific search,” or an equivalent universal claim.
