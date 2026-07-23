---
name: scientific-autoresearch
description: "Use this skill to investigate scientific questions autonomously through a lightweight evidence loop: build data-supported mechanisms or substantive candidates, run the next informative test, learn from weak or null results, and preserve the selection path behind the conclusion. Use it for frozen analyses, open multi-round research, or explicitly requested finite coverage across empirical, computational, and experimental sciences."
license: MIT
metadata:
  version: "0.3.1"
---

# Scientific Autoresearch

Use an active evidence loop:

```text
question -> candidate -> supported test -> interpretation
         -> next candidate or refinement -> final scientific audit
```

Start scientific work after the minimum support and data-semantic checks needed for the next test. Do not design every possible future analysis before producing the first result. Unless the request is limited to design, read-only review, or one named test, continue autonomously inside the authorized scientific, data, resource, safety, and external-action boundaries. A round is a result–interpretation–decision checkpoint, not a tool call, retry, job, or mandatory request for confirmation.

## 1. Build a compact candidate board

State the question, target system or population, decision target or estimand, meaningful effect scale, authorized data, supported sample, and scientifically independent unit.

For a mechanism question, begin with physical, causal, biological, or process mechanisms. Otherwise use substantively distinct models, empirical relations, features, simulations, designs, interventions, methods, or failure modes. Generate candidates both candidate-forward and data-product-reverse. Add literature, theory, expert knowledge, or failure-mode review only when it can materially change the board.

For each candidate, record only its rationale, distinct prediction, required support, observable and scale, expected signature, falsifier, status, and next action. Keep plausible but unsupported candidates as `needs_data`. Do not turn proxies, thresholds, parameter values, or a naive Cartesian product into separate scientific candidates without distinct scientific roles.

## 2. Freeze and run the next informative test

Freeze only the next executable test or coherent prespecified batch: candidates or formulations, data and exclusions, support, observable, method, scale or parameter rule, comparator, uncertainty, falsifier, decision role, stopping, and reporting. A finite family, cross-validation, simulation program, parameter scan, or automated search may be one batch when its complete data-to-decision mapping is fixed before its outcomes are inspected.

Choose the unresolved candidate, falsifier, validation, or refinement most likely to change scientific understanding. Run the simplest valid supported test that distinguishes serious alternatives. Do not choose by nominal significance or convenience alone.

Give every numerical eligibility, support, or comparison threshold a scientific, design, precision, power, or operating-characteristic basis before outcomes. If a threshold is only heuristic, label it, test reasonable alternatives, and never choose it merely to retain or exclude available candidates or data families.

Unless the user or an established project fixes another value, use master random seed `42` for stochastic execution. Reuse the same seed or stream rule across comparable candidates and exact reruns. If the conclusion requires multiple realizations, freeze a deterministic realization set generated from master `42`, retain every realization, and aggregate by the prespecified rule; never change or select seeds after viewing outcomes.

## 3. Interpret and continue

At each result checkpoint, estimate the effect in meaningful units with uncertainty, apply the material challenge most capable of weakening the interpretation, update the board, and choose the next action without per-round confirmation. Establish unchanged support, sensitivity, and challenge checks once and reuse them.

- If a candidate remains credible, test its next prediction, relevant scale, alternative explanation, or verification need.
- If evidence is weak, null, unstable, or conflicting, check support, sensitivity, observable or scale mismatch, measurement error, model fit, implementation, and systematics; then run another supported candidate or motivated refinement while it could change the conclusion.
- Do not reject a broader candidate because one formulation failed, or treat missing support and inadequate sensitivity as a scientific null.

## 4. Keep one compact scientific record

Use one persistent candidate board and result–decision log. Append one short entry per scientific checkpoint: test, result, interpretation, caveat, outcome-informed change, and next action. Preserve weak, null, conflicting, invalid, failed, abandoned, and unfavorable branches when they influenced the work.

If a viewed outcome motivates an unplanned candidate, formulation, sample, method, threshold, ranking, stopping, or reporting change, preserve the earlier result, record what was seen and why it changed the next step, and freeze the successor before running it. Do not retrospectively call the change prespecified.

Treat code repair, exact reruns, worker or chunk changes, cache moves, scheduling, and scientifically equivalent implementations as engineering work when they preserve scientific values and meaning. If they can change the sample, estimand, candidate values, ranking, or conclusion, record the affected scientific change.

At first production use, record each input's stable version or snapshot identifier. Use a digest only when no adequate stable identifier exists or exact byte identity matters. Confirm the same identity once before final reporting or handoff. Recheck earlier only after a source change, suspected mutation, sealed-evidence opening, material trust-boundary transfer, or an explicitly stronger assurance request.

For ordinary research, do not create manifest trees, checksum indexes, receipts, immutable round snapshots, status-transition files, or run validators. Do not repeatedly hash unchanged inputs, code, or intermediate outputs. Formal machine-readable audit is a separate workflow, not an automatic escalation of scientific research.

## 5. Promote conclusions strictly

Test early, but before promoting a conclusion:

- require substantive or mechanism alignment;
- directly rank only compatible targets, supported samples, estimands, evidence stages, and material data quality;
- examine relevant scale or radius, measurement error, systematics, confounding, controls, alternatives, screening-to-final-model mapping, and transportability when they can change the decision;
- distinguish exploration, same-data internal validation, untouched verification, and independent replication; new code, splits, repositories, workflows, or skill versions do not erase prior exposure;
- never select a favorable seed, scale, subgroup, checkpoint, or branch.

Cover the actual selection path with an appropriate design or inference method, such as untouched evaluation, end-to-end resampling or randomization, valid sequential or selective inference, hierarchical control, or justified model comparison or averaging. If the path cannot be covered validly, keep the conclusion exploratory rather than promoting the survivor's nominal statistic.

## 6. Stop scientifically, not administratively

Continue while a distinct supported candidate, falsifier, validation, or refinement could materially change the conclusion and the work remains authorized and feasible. A useful partial result may be reported without ending the investigation. Do not impose a universal candidate or round cap.

Stop when the requested scientific decision is resolved and no remaining supported test could materially alter it, no distinct supported test remains, progress requires new data or assumptions, or a real resource, safety, governance, or user boundary is reached. Preserve unresolved candidates and the exact next admissible step; do not stop silently or force a winner.

Before ending ordinary open research, review the question once candidate-forward and data-product-reverse for an obvious supported omission. Test it or leave it explicitly open. This is a lightweight omission review, not inventory saturation.

## 7. Use full coverage only when explicitly requested

When the user requests systematic coverage, saturation, exhaustion of a declared data-supported space, or `complete_within_scope`, read `references/coverage-search.md`. Use a finite versioned inventory, data-supported coverage cells, candidate-forward and data-product-reverse saturation audits, a complete selection ledger, and an exact open queue. Unrun, invalid, blocked, and resource-deferred cells remain open.

Claim `complete_within_scope` only when the declared inventory satisfies its saturation rule, every eligible cell is validly tested or explicitly closed, the complete selection path is reviewed, and the final decision rule is applied. Resource exhaustion is a pause, not completion. Scope the claim to the candidate classes, observables, and data products actually covered.

## Report

Report the supported conclusion and effect scale; uncertainty and sample support; the strongest falsifier, systematics, and alternatives; candidates and formulations attempted; outcome-informed changes and selection-path treatment; evidence status and prior exposure; data and procedure versions; a practical reproduction recipe; and the strongest unresolved candidate or open queue. Use `tie`, `inconclusive`, `null`, `support_limited`, or `needs_data` when justified.

Never hide or redefine data, attempts, candidates, scales, models, or results because they weaken a claim; rank by nominal p-value alone; present same-data adaptation as untouched confirmation; fabricate evidence or coverage; exceed authorization; or expose restricted information.

## Load references only when needed

- Explicit finite coverage or scoped completion: `references/coverage-search.md`.
- Candidate comparison, prior exposure, or selection-path inference: `references/decision-selection.md` and `references/statistical-discipline.md`.
- Weak or null evidence and falsification: `references/null-triage.md` and `references/falsification-toolkit.md`.
- Data support and domain semantics: `references/domain-adapter.md` plus the applicable `references/observational-data.md`, `references/ml-simulation.md`, or `references/causal-experimental.md`.
- Literature, safety, claim framing, or difficult interpretation: the applicable `references/literature-evidence.md`, `references/governance-safety.md`, `references/claim-types.md`, `references/scientific-review-lens.md`, or `references/thinking-principles.md`.
- A concrete execution or resource risk: `references/execution-lifecycle.md`.
