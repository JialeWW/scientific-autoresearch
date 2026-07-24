---
name: scientific-autoresearch
description: "Use when asked to design, execute, audit, or iteratively extend an evidence-generating scientific analysis where falsification, outcome-informed choices, data support, or selection-path validity are material. Supports prespecified programs, explicitly autonomous multi-round research, and explicitly requested finite coverage. Do not use for routine scientific explanation, literature-only review, manuscript editing, or ordinary engineering and one-off calculations without scientific decision design."
license: MIT
metadata:
  version: "0.3.3"
---

# Scientific Autoresearch

Use an active evidence loop:

```text
question -> candidate -> supported test -> interpretation
         -> next candidate or refinement -> final scientific audit
```

Start after the proportionate support, data-semantic, execution-risk, and, when applicable, governance checks needed to interpret the work. Freeze the full required protocol for confirmatory, blinded, costly, irreversible, regulated, safety-sensitive, or jointly inferred work. Otherwise, do not design an imagined entire future project before the first informative result.

Continue across multiple result–decision rounds only when the user explicitly authorizes autonomous or iterative investigation. For design, read-only audit, or one named test, stay within that request and report further scientific tests as proposals rather than silently running them. Inside an authorized iterative scope, a round is a scientific checkpoint, not a tool call, retry, job, or automatic request for confirmation; seek new authorization when scope, cost, risk, data access, or external action would change.

## 1. Build a compact candidate board

For open or adaptive investigation, state the question, target population, estimand, meaningful effect scale, authorized data, supported sample, and scientifically independent unit. Define support and meaningful scale for the planned inference. For a fully specified test or read-only audit, keep only the entries needed for that request.

When identifiers, joins, duplicates, units, censoring, support, or leakage could alter the sample, estimand, or dependence, preflight them before production. Keep related units together across partitions and resample or permute at the independent unit unless dependence is explicitly modeled.

For a mechanism question, begin with physical, causal, biological, or process mechanisms. Otherwise use substantively distinct models, relations, features, simulations, designs, interventions, methods, or failure modes. Generate candidates from mechanisms (question -> prediction -> observable) and, when useful, from authorized measurements (data product -> plausible candidate). Label outcome-prompted candidates exploratory. Use literature, theory, expert knowledge, or failure-mode review when needed for plausibility, prior evidence, safety, or test choice.

Keep each entry compact and record at least its rationale, distinct prediction, required support, observable and scale, expected signature, falsifier, status, and next action. Keep plausible but unsupported candidates as `needs_data`. Do not turn proxies, thresholds, parameter values, or a naive Cartesian product into separate scientific candidates without distinct scientific roles.

## 2. Freeze and run the next informative test

Freeze the next executable test or coherent prespecified batch. If a complete multi-stage data-to-decision mapping can already be fixed, freeze it once rather than creating result-by-result successors. Specify formulations, data and exclusions, support, observable, method, scale rule, comparator, uncertainty, falsifier, decision role, stopping, and reporting. A finite family or automated procedure may be one batch when its complete mapping is fixed before outcomes.

Data-dependent steps inside a frozen mapping remain prespecified; outcome-driven discretion outside it creates a successor. Before the first decision-bearing outcome, also freeze the comparison family, evidence partitions, tie, inconclusive, and promotion rules, and the selection-path or untouched-evaluation strategy needed for the claim.

Choose the unresolved candidate, falsifier, validation, or refinement most likely to change scientific understanding. Run the simplest valid supported test that distinguishes plausible alternatives with different observable predictions. Do not choose by nominal significance or convenience alone.

Prespecify and justify numerical thresholds that could materially affect eligibility, support, ranking, or conclusion using science, design, precision, power, or operating characteristics. Label operational heuristics and test reasonable alternatives when consequential. Never choose a threshold merely to retain or exclude available candidates or data families.

Before stochastic execution, freeze a reproducible randomization policy appropriate to the design. For simulation or optimization, record deterministic seeds or stream state and choose common, paired, or independent streams by the comparison design. For treatment or operational allocation, use a separate validated concealed scheme and restrict its state until disclosure is authorized. Freeze realization, aggregation, retry, and precision-expansion rules that can affect the conclusion; never select or change randomness after outcomes.

## 3. Interpret and continue

At each checkpoint, estimate the effect in meaningful units with uncertainty, apply the strongest material challenge allowed by the frozen plan, and update the board. In authorized iterative work, choose the next action inside the authorization envelope without per-round confirmation. For one named test, finish it and only propose successors. Establish unchanged checks once and reuse them.

- If a candidate remains credible, test its next prediction, relevant scale, alternative explanation, or verification need.
- If evidence is weak, null, unstable, or conflicting, check support, sensitivity, observable or scale mismatch, measurement error, model fit, implementation, and systematics; then run another supported candidate or motivated refinement while it could change the conclusion.
- Do not generalize one failed formulation to a broader candidate unless it tested a necessary prediction with adequate support and sensitivity. Do not treat invalid execution, missing support, or inadequate sensitivity as a scientific null.

## 4. Keep one compact scientific record

Use one persistent candidate board and result–decision log. For outcome-adaptive work, make it append-only or versioned before the first potentially selection-influencing outcome. Log each scientific checkpoint and preserve every scientific attempt and result, including weak, null, conflicting, invalid, failed, abandoned, and unfavorable branches. Response-blind operational metadata and QA may be summarized.

When a protocol or builder declares stable scientific identifiers or science-facing data-product families, keep their dispositions in the compact record. Reconcile each declared candidate, prediction, falsifier, control, scientific role, and science-facing product to a test and output, an explicit closure, or the open queue. This reconciliation is deterministic only over declared identifiers and resolvable references; do not infer semantic equivalence from free text. Mark product families by role and whether they are science-facing so QA, intermediate, and provenance fields do not become false scientific blockers. A label such as `sensitivity` or `diagnostic` is a scientific role, not a disposition.

If a viewed outcome motivates an unplanned candidate, formulation, sample, method, threshold, ranking, stopping, or reporting change, preserve the earlier result, record what was seen and why it changed the next step, and freeze the successor before running it. Do not retrospectively call the change prespecified.

Treat code repair, exact reruns, worker or chunk changes, cache moves, scheduling, and equivalent implementations as engineering work only when they preserve the data, sample, estimand, parameters, random streams, and decision rule. If a change could alter scientific meaning, record it and freeze the affected successor before production.

Before first result-producing use, record stable identifiers for inputs and decision-bearing code or procedures. Use a digest only when no adequate identifier exists or exact bytes matter. Reconfirm before reporting or handoff and after mutation risk, opening blinded evidence, transfer across different integrity controls, or a stronger assurance request.

For ordinary research, do not require bespoke audit trees, repeated hashing, or formal run-package validators by default. Reuse required scientific, data-integrity, execution, and provenance controls; add audit artifacts only for a concrete integrity, handoff, governance, or reproducibility need. Publication, runtime, session count, autonomy, or analysis count alone do not trigger formal machine audit.

## 5. Promote conclusions strictly

Test early, but before promoting a conclusion:

- require the claim to match a stated substantive or mechanistic prediction;
- compare or rank candidates only when their targets, samples, estimands, evidence stages, and material data-quality regimes are compatible; otherwise report parallel conclusions;
- examine relevant scale or radius, measurement error, systematics, confounding, controls, alternatives, screening-to-final-model mapping, and transportability when they can change the decision;
- distinguish exploration, same-data internal validation, untouched verification, and independent replication; moving exposed data or code, or making a new split after inspecting overlapping outcomes, does not create untouched evidence;
- never select a favorable seed, scale, subgroup, checkpoint, or branch.

Account for the actual selection path with untouched evaluation, end-to-end resampling or randomization, valid sequential or selective inference, hierarchical control, justified model comparison or averaging, or another suitable method. Otherwise keep the conclusion exploratory rather than promote the selected candidate's unadjusted statistic.

## 6. Use explicit scientific and operational stopping criteria

Within the authorized scope and resource budget, continue while a currently identified, feasible, supported test has a reasonable chance of materially changing the requested decision. Use problem-specific scientific and operational stopping criteria; do not impose one skill-wide candidate or round cap. A useful partial result may be reported without ending an authorized iterative investigation.

Stop when the requested decision is resolved under its declared rule, no currently identified feasible test meets the continuation standard, progress requires new data or assumptions, or a resource, safety, governance, or user boundary is reached. Preserve unresolved candidates and the exact next admissible step; do not stop silently, invent endless refinements, or force a winner. If resources end while admissible work remains, report `resource_limited` or a bounded pause, not completion.

Do not infer scientific stopping from completion of the requested execution or a registered batch. Keep `request_execution_complete`, `scientific_mapping_complete`, `search_stop_admissible`, and, only for explicit coverage, `complete_within_scope` separate. Use `not_assessed` when a gate was not invoked and `indeterminate` when a required stop challenge cannot resolve a material dispute. Use only the state and termination vocabularies in `references/completion-review.md`; do not invent compound status labels. When the task actually terminates, record exactly one primary reason. Use `termination_reason=request_complete` when the bounded request finished as authorized; use a user, resource, safety, or governance boundary only when that boundary interrupts otherwise unfinished authorized work.

Only when preparing to set `search_stop_admissible=true`, claim that no material test remains, or end open or adaptive research on a scientific-stop basis, read `references/completion-review.md` and run one scientific stop challenge. Reconstruct expected work candidate-forward, from declared protocol roles, and data-product-reverse before accepting the test registry as complete. Use one fresh reviewer context when available; otherwise perform the same source-first pass as an explicitly non-independent self-review. Adjudicate every finding and test or leave open every accepted, supported, feasible, authorized, potentially material omission. Do not recursively review the reviewer. A named-test result, registered-batch completion without a search-stop claim, or boundary-forced termination does not trigger this challenge.

## 7. Use full coverage only when explicitly requested

When the user requests systematic coverage, saturation, exhaustion of a declared data-supported space, or `complete_within_scope`, read `references/coverage-search.md`. Use a finite versioned inventory, data-supported coverage cells, candidate-forward and data-product-reverse saturation audits, a complete selection ledger, and an exact open queue. Unrun, invalid, blocked, and resource-deferred cells remain open.

Claim `complete_within_scope` only when the declared inventory satisfies its saturation rule, every eligible cell is validly tested or explicitly closed, the complete selection path is reviewed, and the final decision rule is applied. Resource exhaustion makes the search resource-limited or incomplete, not complete. Scope the claim to the candidate classes, observables, and data products actually covered.

A scientific stop challenge may review the coverage record and expose inconsistencies, but it cannot replace inventory saturation, cell closure, selection-ledger review, or the final decision rule.

## Report

Report, as applicable, the supported conclusion and effect scale; uncertainty and sample support; the strongest falsifier, systematics, and alternatives; candidates and formulations attempted; outcome-informed changes and selection-path treatment; evidence status and prior exposure; data, code, and procedure versions; a practical reproduction recipe; the strongest unresolved candidate or open queue; the applicable completion states; and the termination reason.

Define any status labels used. Reserve `null` for a prespecified null or equivalence decision with adequate support and sensitivity; use `inconclusive` or `support_limited` when absence of evidence is the issue. Use `tie`, `needs_data`, `no_eligible_candidate`, or `resource_limited` when their stated conditions apply. `resource_limited_pause` is the systematic-coverage form of `resource_limited` when open cells and an exact resume point must be preserved.

Never omit, relabel, redefine, or selectively report data, attempts, candidates, scales, thresholds, subgroups, transformations, models, or results to conceal evidence that weakens a claim. Never rank by nominal p-value alone; present outcome-driven adaptation as confirmation or same-data variants as independent verification; fabricate data, citations, approvals, provenance, commands, results, evidence, or coverage; exceed authorization; or expose restricted information. Document legitimate corrections and definition changes.

## Load references only when needed

- Explicit finite coverage or scoped completion: `references/coverage-search.md`.
- Scientific-stop or no-material-test claim: `references/completion-review.md`.
- Material candidate ranking, prior exposure, adaptive choice, or a promoted selection claim: `references/decision-selection.md`; add `references/statistical-discipline.md` when multiplicity, evidence partitions, stochastic calibration, or path inference is not already clear.
- Weak or null evidence: `references/null-triage.md`; concrete falsification design: `references/falsification-toolkit.md`.
- Data support and domain semantics: `references/domain-adapter.md` plus the applicable `references/observational-data.md`, `references/ml-simulation.md`, or `references/causal-experimental.md`.
- Sensitive, regulated, costly, prospective, physical, or external actions: `references/governance-safety.md`.
- Literature, claim framing, or difficult interpretation: the applicable `references/literature-evidence.md`, `references/claim-types.md`, `references/scientific-review-lens.md`, or `references/thinking-principles.md`.
- A concrete execution or resource risk: `references/execution-lifecycle.md`.
