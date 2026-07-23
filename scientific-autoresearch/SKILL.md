---
name: scientific-autoresearch
description: "Use this skill to investigate scientific questions autonomously by building data-supported mechanisms or substantive candidates, testing and refining them, learning from weak or null results, and auditing the selection path behind the final conclusion. Use it for frozen analyses, open multi-round research, or explicitly requested systematic coverage across empirical, computational, and experimental sciences."
license: MIT
metadata:
  version: "0.3.0"
---

# Scientific Autoresearch

Use an active evidence loop:

```text
question
-> mechanism or substantive candidate
-> supported observable or prediction
-> test
-> scientific interpretation
-> next candidate or refinement
-> final audit
```

Honor requests limited to prospective design, read-only audit, or one named test. Otherwise, when the user authorizes an investigation or autoresearch run, continue autonomously inside the agreed scientific, data, resource, safety, and external-action boundaries. A weak result is information for the next decision, not a default stopping point. A round is a result–interpretation–decision checkpoint, not a tool call, retry, job, or mandatory request for confirmation.

## Seven Core Rules

### 1. Build a compact candidate board

State the question, target population or system, estimand or decision target, meaningful effect scale, authorized data, supported sample, and scientifically independent unit.

For a mechanism question, begin with physical, causal, biological, or process mechanisms. For a nonmechanistic question, use substantively distinct models, empirical relations, features, simulations, designs, interventions, methods, or failure modes. Generate candidates in both directions:

- candidate-forward: what plausible candidates could answer the question?
- data-product-reverse: what scientifically relevant alternatives can each authorized data product distinguish?

Add literature, theory, expert knowledge, or a failure-mode catalogue as another source when the question materially requires it, not as a ritual. For each candidate, keep only the scientific rationale, distinct prediction, required data and support, observable and relevant scale, expected signature, falsifier, current status, and next action. Keep plausible but currently untestable candidates as `needs_data`.

### 2. Test only substantive, supported candidates

A candidate enters testing only when it has a scientific reason, an expectation distinguishable from relevant alternatives, and an observable or test supported by available data. A proxy, threshold, parameter value, or implementation variant is a formulation unless it has a distinct scientific role and prediction. Do not turn a naive Cartesian product into a candidate space.

Before inspecting a coherent batch's outcomes, freeze its candidates or formulations, data and exclusions, observable, sample, method, scale or parameter rule, comparator, uncertainty, falsifier, decision role, stopping, and reporting. Freeze the current executable batch, not every hypothetical future step. A finite family, cross-validation, simulation program, parameter scan, or automated search may be one batch when its complete data-to-decision mapping is fixed in advance.

### 3. Run, interpret, and continue autonomously

Select the unresolved candidate, falsifier, validation, or refinement most likely to change scientific understanding. Run the simplest valid supported test that distinguishes the leading alternatives; do not choose only by nominal significance or convenience.

For each new or materially changed batch, establish the relevant support, sensitivity, and challenge checks once and reuse them until an affected scientific fact changes. At the result checkpoint, estimate the effect in meaningful units with uncertainty, apply the material challenge most capable of weakening the interpretation, interpret the result against serious alternatives, update the board, and choose the next action without per-round confirmation.

- If a candidate remains credible, test its next prediction, alternative explanation, relevant scale, or verification need.
- If evidence is weak, null, unstable, or conflicting, check sensitivity, support, observable or scale mismatch, measurement error, model fit, implementation, and systematics. Continue to another supported candidate or scientifically motivated refinement while it could change the conclusion.
- Do not reject a broader candidate because one formulation failed, and do not treat missing support or inadequate sensitivity as a scientific null.

### 4. Record scientific adaptation, not ordinary engineering

Use one persistent candidate board and compact result–decision record. If a viewed outcome motivates an unplanned candidate, formulation, sample, method, threshold, ranking, stopping, or reporting change, preserve the earlier result, record what was seen and why it changed the next step, freeze the successor before running it, and retain both steps in the final path. Do not retrospectively call the change prespecified or build a new governance system merely because the science learned from a result.

Code repair, exact reruns, worker or chunk changes, cache moves, scheduling changes, and scientifically equivalent implementations are engineering work when they preserve scientific values and meaning. Repair and continue the same frozen test; do not count them as new scientific rounds. If they can change the sample, estimand, candidate values, ranking, or conclusion, treat the affected change scientifically.

At first production use, record each input's stable dataset ID, version, snapshot, or digest. Reuse that identity during the run and verify it again before final reporting or handoff; do not recompute full-data hashes at every batch or round. Recheck earlier only when the source or version changes, mutation is suspected, sealed evidence is opened, data cross a material trust boundary, or stronger assurance was explicitly requested.

### 5. Preserve the full selection path and promote carefully

Keep supported, weak, null, conflicting, invalid, failed, abandoned, and unfavorable branches. Every attempt or viewed outcome that influenced generation, modification, screening, retention, ranking, repeated looks, verification targeting, or promotion belongs to the final selection path.

Before promotion:

- require substantive or mechanism alignment;
- directly rank only candidates with compatible targets, supported samples, estimands, evidence bases, and material data quality;
- examine scale, radius, aperture, binning, threshold, resolution, measurement error, systematics, confounding, controls, alternatives, screening-to-final-model mapping, and transportability when they can change the decision;
- distinguish exploration, same-data internal validation, untouched verification, and independent replication; changing code, sample, split, repository, workflow, or skill version does not erase prior exposure;
- predeclare common seeds or realizations when stochastic variation can change ranking, and never choose a favorable seed, scale, subgroup, checkpoint, or branch.

Use inference that covers the actual selection path, such as untouched evaluation, end-to-end resampling or randomization, valid sequential or selective inference, hierarchical control, or justified model comparison or averaging. No single global-null method fits every domain. If the actual path cannot be covered validly, keep the conclusion exploratory rather than promoting the survivor's nominal statistic.

### 6. Continue while material science remains

Continue while a distinct data-supported candidate, falsifier, validation, or refinement could materially change the conclusion and the work remains authorized and feasible. A useful partial result may be reported without ending the search. Do not impose a universal candidate or round cap.

Stop only when the requested scientific decision is resolved and no remaining supported test could materially alter it, no distinct supported test remains, progress requires new data or assumptions, or a real resource, safety, governance, or user boundary is reached. Preserve unresolved candidates and the exact next admissible step; do not stop silently or force a winner.

### 7. Finish with a scientific audit; use full coverage only when requested

Before ending ordinary open research, review the question once from candidate-forward and data-product-reverse directions for an obvious supported candidate or alternative that could change the conclusion. Test it or leave it explicitly open. This is a lightweight omission review, not inventory saturation. Ordinary work may end with a bounded conclusion and one compact record.

When the user explicitly requests systematic coverage, saturation, exhaustion of a declared data-supported space, or `complete_within_scope`, read `references/coverage-search.md` and use a finite versioned inventory, data-supported coverage cells, candidate-forward and data-product-reverse saturation audits, any additional source declared necessary, a complete selection ledger, and an exact open queue. Compute schedules work; unrun, invalid, blocked, and resource-deferred cells remain open.

Claim `complete_within_scope` only when the same inventory version satisfies its prespecified saturation rule, every eligible cell is validly tested or explicitly closed, the complete selection path is audited, the final decision rule is applied, and the scientific coverage record is internally consistent. Resource exhaustion is a pause, not completion. Scope the claim to the candidate classes, observables, and data products actually covered; never claim all scientific possibilities were exhausted.

The full scientific coverage record may remain compact. Use a machine-audited schema only when the user separately requests machine-readable audit, formal handoff or recovery needs it, or an existing structured run must be continued.

## Report

Report the supported conclusion and effect scale; uncertainty, support, falsifiers, systematics, and alternatives; candidates and formulations attempted; weak, failed, and support-limited branches; outcome-informed changes and selection-path inference; evidence status and prior exposure; data and procedure versions; a practical reproduction recipe; and the strongest unresolved candidate or open queue. Use `tie`, `inconclusive`, `null`, `support_limited`, or `needs_data` when justified.

Never hide or redefine data, attempts, candidates, scales, models, or results because they weaken a claim; rank by nominal p-value alone; present same-data adaptation as untouched confirmation; fabricate evidence, authority, provenance, or coverage; exceed authorization; or expose restricted information.

## Load Detailed References Only When Needed

- Explicit systematic coverage or scoped completion: `references/coverage-search.md`.
- Complex candidate comparison, prior exposure that affects the claim, or final selection-path inference: `references/decision-selection.md` and, when necessary, `references/statistical-discipline.md`.
- Weak or null evidence and falsification design: `references/null-triage.md` and `references/falsification-toolkit.md`.
- Data support and domain semantics: `references/domain-adapter.md` and the applicable `references/observational-data.md`, `references/ml-simulation.md`, or `references/causal-experimental.md`.
- Claim type, literature, safety, or final interpretation: the applicable `references/claim-types.md`, `references/literature-evidence.md`, `references/governance-safety.md`, or `references/scientific-review-lens.md`.
- Difficult substantive framing or conflicting evidence: `references/thinking-principles.md`.
- A concrete execution or resource risk: `references/execution-lifecycle.md`.
- Explicit machine-readable audit, formal recovery, or an existing structured run: `references/report-contract.md`, `references/status-schema.md`, and `references/round-gate-checklist.md`.
