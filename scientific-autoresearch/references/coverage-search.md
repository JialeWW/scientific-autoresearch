# Coverage-Based Scientific Search

Use this reference to construct the data-supported search space, audit its saturation, close coverage cells, and state the scope of the result.

## 1. Version the Mechanism Inventory

Do not impose an arbitrary numeric limit on mechanisms. At any execution point, however, the current inventory version must be finite, explicit, deduplicated, and immutable.

Record at least:

```text
inventory_version
mechanism_id
parent_mechanism_id
mechanism
distinct_pathway
inclusion_rationale
generation_lens
applicable_regime
predicted_signature
required_data_products
data_support_status
mechanism_status
specification_timing
duplicate_of
```

Use `pre_result_frozen` when the entry was fixed before related outcomes were inspected and `post_result_adaptive` otherwise. Preserve every prior inventory version. A new eligible mechanism creates a new version and a recorded diff; never silently insert it into an old version.

Keep scientifically plausible but currently untestable mechanisms with `mechanism_status=needs_data`. They document the boundary of the available data but do not enter the executable coverage denominator.

Use the canonical `data_support_status` values in `status-schema.md`. Direct promotion requires `supported`, but every nonduplicate `active`, `provisionally_supported`, or `weakened` mechanism must still receive finite coverage; a limited, diagnostic, or unsupported role changes the cell's role or closure, not whether the active mechanism is represented in the search map.

## 2. Enumerate Through Complementary Lenses

Freeze the inventory-audit protocol before outcomes. Use complementary lenses rather than one unconstrained brainstorming pass:

- mechanism-forward decomposition of physical, causal, computational, or measurement pathways;
- data-product-reverse mapping from each authorized field, catalog, image, time series, model output, or experimental record to the mechanisms it can test;
- scale, geometry, timing, regime, interaction, and boundary-condition predictions;
- measurement, calibration, selection, support, confounding, leakage, and numerical-artifact alternatives;
- residual and failure-mode review after each closed round, with any additions marked adaptive.

The saturation audit always has two independent directions:

1. mechanism-forward: start from the substantive system and enumerate distinct pathways and predictions;
2. data-product-reverse: start from every authorized data product and ask which pathways, alternatives, and artifacts it can distinguish.

At Round 0, decide whether the problem warrants a third independent source, such as a targeted literature audit, formal theory or model enumeration, structured expert elicitation, or a failure-mode catalogue. If declared applicable, freeze its scope and completion rule and require it for saturation. Literature review is conditional: use it when premise, novelty, or inventory coverage depends on literature, not as a ritual for every run.

Track physical or substantive mechanisms separately from measurement, selection, quality, and method explanations. Merge semantic duplicates and record the surviving ID and justification.

A proposed addition is eligible only when it is nonredundant and has at least one distinct prediction that current authorized data can test. Otherwise retain it as duplicate, out of scope, or needs data.

## 3. Define Finite Coverage Cells

For every eligible mechanism, predefine a finite set of mechanism-matched cells:

```text
coverage_cell_id
inventory_version
mechanism_id
observable_id
formulation_id
mechanism_alignment
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

The scientific space may contain any number of mechanisms over time, but each inventory version and each mechanism's executable formulation set must be finite and auditable.

Construct cells through `mechanism -> observable role -> formulation`. A constrained or full product is valid only when each axis and resulting cell has a frozen substantive, control, or diagnostic role; only decision-eligible cells enter ranking. Do not flatten unrelated mechanisms, proxies, and parameter combinations into one ranked pool. For continuous spaces, freeze a substantively justified range plus one of:

- a finite grid and resolution;
- a sampling distribution and draw count;
- a marginalization or integration rule;
- an injection/recovery or response-surface map;
- a convergence tolerance and adaptive refinement rule.

Outcome-driven threshold nudging, proxy swaps, subgroup slicing, or parameter zooming create new exploratory formulation IDs. They expand the relevant selection family and cannot erase the original cell.

## 4. Define Selection Families

Every test capable of influencing the same candidate-generation, modification, screening, retention, ranking, verification targeting, promotion, or headline decision belongs to that decision's complete selection path. Read `decision-selection.md` before freezing these families.

Freeze family boundaries and an end-to-end null, hierarchical, max-statistic, selective, sequential, false-discovery, Bayesian model-comparison or model-averaging, sealed-holdout, or other justified inference method before outcomes when possible. Preserve the dependence structure when calibrating a family. The skill does not prescribe one universal global-null construction.

Direct comparison also requires a common decision, target population, supported sample, estimand, evidence stage, and materially comparable data-quality regime, or a prespecified validated mapping to a common scale. Store these as structured family fields together with `transportability_requirement` and `transportability_status`; an opaque comparison key is not enough. Do not force unrelated estimands, samples, quality regimes, or null distributions into one universal family. Preserve noncomparable results as parallel conclusions or `support_limited_candidate`. If mechanisms legitimately compete for one headline conclusion, define a cross-mechanism gate or omnibus family, then use prespecified within-mechanism families for localization.

When an adaptive inventory or formulation addition affects selection:

1. append it to the existing ledger before execution;
2. version the affected family;
3. update error allocation with a valid adaptive method or keep the result exploratory;
4. preserve all prior weak, failed, invalid, and abandoned branches.

Technical failures without an evaluable statistic remain in the ledger and execution accounting; do not fabricate inferential values for them.

## 5. Audit Inventory Saturation

Set `inventory_saturated=true` only when all conditions hold:

1. the question, scope, authorized data products, support rules, and eligibility rules have remained unchanged;
2. after the most recent eligible addition, one complete mechanism-forward audit and one complete data-product-reverse audit have each covered every in-scope regime and data product;
3. every additional independent source declared applicable at Round 0 has completed its frozen audit;
4. all required audits produced zero new eligible, nonredundant, data-supported mechanisms;
5. every proposed addition, duplicate, exclusion, and needs-data decision is recorded with a reason.

The required audits must be distinct, prespecified inventory passes; ordinary execution rounds that happen not to suggest a new mechanism do not count. Record each source, reviewer or procedure, search scope, date, inventory version, additions, duplicate decisions, and unresolved gaps.

Any new eligible mechanism increments `inventory_version`, expands the coverage denominator, and resets the saturation sequence. New data products or a changed scientific question require a new inventory version.

## 6. Close Coverage

A coverage cell closes only as:

- `tested_valid`: a valid test was completed and its result status recorded;
- `covered_by:<cell_id>`: another cell provides equivalent coverage, with an explicit nonredundancy argument;
- `not_testable_current_data`: support, sensitivity, or identifiability was assessed and current data cannot test it.

`eligible_untested`, `scheduled`, `in_progress`, `invalid_open`, `resource_blocked`, and `governance_blocked` are open. An invalid test stays open whenever a feasible valid replacement exists.

Compute:

```text
coverage_fraction =
closed eligible cells / all eligible cells in the same inventory version
```

Declare `coverage_complete=true` only when every eligible cell in that version is closed and the ledger and family-level inference are audited.

Scientific completion requires:

```text
inventory_saturated
AND coverage_complete
AND search_ledger_audited
AND decision_contract_applied
```

Resource, time, cost, authorization, or user-limit exhaustion does not close cells. Use `resource_limited_pause`, `governance_blocked`, or `user_limited_stop`, report every open cell, and preserve an exact resume point.

## 7. Schedule Without Shrinking Coverage

Scientific eligibility and execution priority are separate fields. A scheduler may first run one or more prespecified, low-cost screening stages within declared comparable screening families and then allocate deeper tests by dependency, cost, expected information gain, or feasibility. Record every screen rule, threshold, sensitivity or recovery check, and false-negative risk before use.

Every screen and outcome that can influence progression enters the ledger and its selection path. A cell that fails a valid prespecified screen may close only if the screen itself provides the mechanism-matched sensitivity required by the cell; otherwise it remains open or is replaced by an explicitly justified coverage cell.

Queued, deferred, and resource-blocked cells remain in the coverage denominator. When resources end, serialize the full open queue, priority basis, dependencies, estimated resource need, and next admissible action.

## 8. State the Scope Honestly

When supported by the recorded audit, use:

> We systematically searched a versioned inventory of mechanisms and observables testable with the available data products.

If the same inventory version met both stopping conditions, add:

> The inventory met its prespecified saturation criterion, and every eligible cell in that version was tested or explicitly classified.

Always preserve the boundary:

> This search does not establish exhaustiveness beyond the data-supported search space.

Do not write “all possible mechanisms,” “exhaustive physical search,” or an equivalent universal claim.
