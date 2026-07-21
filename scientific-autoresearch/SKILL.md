---
name: scientific-autoresearch
description: "Use this skill when scientific work requires formal audit or provenance, or when agents generate, modify, screen, compare, rank, or systematically cover data-supported candidates. It provides proportionate profiles for research design, audited fixed tests, adaptive search, and coverage search, with conservative inference across the complete selection path."
license: MIT
metadata:
  version: "0.2.4"
---

# Scientific Autoresearch

Match process weight to scientific adaptivity. Search actively when requested, but infer conservatively from every outcome-dependent choice. Bound execution by authorized scope and resources; bound scientific claims by the data-supported search space.

## 1. Select and Freeze a Profile

Choose the least expansive profile that covers the requested work. Record the profile before inspecting new outcomes.

- `design_only`: Design or audit a question, claim, test, inventory, or analysis plan. Do not execute an analysis.
- `fixed_test`: Run exactly one prespecified test of one claim on one frozen sample with one frozen analysis and decision rule. Use no candidate generation, outcome-dependent modification, screening, or ranking.
- `adaptive_search`: Generate, modify, screen, retain, compare, rank, or promote candidates. Audit the complete adaptive path, but make no saturation or coverage-completion claim.
- `coverage_search`: Systematically search the finite candidate and observable space supported by available data. Maintain typed inventory, coverage cells, an open queue, saturation audits, and full selection-path inference.

Do not choose `fixed_test` merely because only one result will be reported. Choose it only when the test and decision rule were fixed independently of the inspected outcome. Treat any data-informed candidate choice as `adaptive_search` or `coverage_search`.

When formal machine-audited artifacts are requested, initialize an empty run path with `scripts/validate_run.py --init RUN_DIR --profile PROFILE`, complete only the generated profile artifacts, and validate before a bounded, pause, or completion report.

## 2. Preserve History When the Profile Changes

Upgrade the profile before continuing whenever the work exceeds its frozen boundary.

- Upgrade `design_only` to an execution profile before viewing results.
- Upgrade `fixed_test` to `adaptive_search` when its outcome motivates a new candidate, formulation, threshold, sample, model, statistic, or ranking. Preserve the original test and label the addition post-result adaptive.
- Upgrade `adaptive_search` to `coverage_search` only when systematic scoped coverage becomes the goal. Seed the inventory and ledger with the complete earlier history; do not claim retrospective saturation.
- Never downgrade a run to erase selection, exposure, failed branches, or stricter obligations.

Record each profile transition, reason, timing, and prior outcome access. Changing data subsets, code, models, tools, workflows, or skill versions does not restore confirmatory status after overlapping data were inspected.

For a formal artifact run, validate the current profile and use `scripts/validate_run.py --snapshot-upgrade RUN_DIR --to-profile PROFILE` before migration. Review its non-overwriting, hash-bound preservation snapshot, add the returned `profile_history` entry, create only the newly required profile artifacts, and validate again. A preservation attestation without the referenced evidence is insufficient.

## 3. Pass Scope and Governance Gates

Before execution, record the scientific scope, authorized data and actions, output boundary, resource envelope, data-use constraints, and required human oversight. Keep raw inputs read-only when practical, minimize sensitive outputs, and redact credentials, private identifiers, and restricted information.

Do not infer approval. Do not trigger costly, shared, regulated, hazardous, prospective, or physical actions outside explicit authorization. If a prerequisite is absent, stop execution and preserve a useful design or blocked report. Treat persistence requests as persistence only within the recorded boundaries.

Read `references/governance-safety.md` only when work is sensitive, regulated, costly, prospective, physical, or capable of affecting external systems.

## 4. Apply the Chosen Workflow

### `design_only`

State the question, claim, estimand, supported data, proposed test, falsifier, assumptions, uncertainty sources, and next decision. Clearly label every unexecuted result as expected or hypothetical. Create only the requested planning artifact.

### `fixed_test`

Before outcomes, freeze a compact claim card containing:

- claim, estimand, target and analysis population, supported sample, and meaningful effect scale;
- input versions, exclusions, statistic or model, parameters, seed policy when relevant, decision rule, and falsifier;
- specification timing, prior exposure to overlapping data, and intended evidence stage.

Run the simplest valid test. Report the effect in meaningful units, uncertainty, assumption checks, falsification result, limitations, actual inputs and parameters, code or procedure state, seeds when used, and reproduction command or equivalent recipe. Preserve the result even when weak, null, failed, or unfavorable.

Do not build an inventory, coverage matrix, saturation audit, selection family, or full run schema for a genuine `fixed_test`. Call the result a completed prespecified test, not a completed search.

### `adaptive_search`

Read `references/decision-selection.md`. Before adaptive outcomes, freeze:

1. a Decision Contract defining the decision, candidate eligibility, target, analysis, selection, and reporting populations, comparison rules, estimands, ranking evidence, tie and inconclusive rules, evidence partitions, and applicable conditional gates;
2. a prior-exposure audit covering overlapping analyses, data looks, parameter attempts, selections, and viewed results;
3. selection families that separate candidates with incompatible targets, samples, estimands, evidence stages, or data-quality regimes;
4. a search ledger that receives every choice or test capable of changing candidate generation, modification, screening, retention, ranking, verification targeting, or promotion.

Version outcome-motivated additions, retain failed branches, and label their timing and evidence stage. Use an inference strategy that covers the actual selection path. Issue a stage or bounded report when execution ends; never claim inventory saturation or coverage completion from this profile.

Read `references/statistical-discipline.md` only when multiplicity, repeated looks, candidate ranking, selective or sequential inference, holdouts, or stochastic comparisons are applicable.

### `coverage_search`

Read `references/coverage-search.md` and `references/decision-selection.md`. Complete the `adaptive_search` requirements, then:

1. Build and version a typed candidate inventory. Declare each entry as a mechanism, model, feature, simulation, design, or another justified type; record its rationale, distinct pathway or role, supported regimes, required data, redundancy, testability, and support status.
2. Map eligible entries into finite cells through `candidate -> observable or test role -> formulation`. Freeze supported sample, parameter or scale regime, expected signature, meaningful effect, sensitivity requirement, and falsifier. Do not create an unrelated Cartesian ranking pool.
3. Generate inventory through candidate-forward and data-product-reverse audits. Add an independent third lens such as theory, literature, expert knowledge, or failure modes only when informative for the question.
4. Separate scientific coverage from scheduling. Permit uniform low-cost screening before deeper tests, but let priority change only execution order. Keep every unrun eligible cell open and preserve the queue when resources end.
5. Audit inventory saturation after the latest eligible addition and close each eligible cell under frozen rules. Do not impose a universal round or candidate cap.

Treat unsupported but plausible entries as `needs_data`, not as executed coverage or evidence against them. Rank only substantively eligible and mutually comparable candidates.

## 5. Activate Gates Only When Applicable

Record one reason when a gate is not applicable; do not manufacture repeated placeholder work.

- Apply substantive alignment before statistical ranking. Require a candidate to support the frozen scientific or operational decision; allow mechanism alignment to be not applicable for a nonmechanistic task only with a stated reason.
- Apply measurement-error sensitivity only when uncertainty could change support, matching, thresholds, subgroup membership, eligibility, ranking, or interpretation. Complete the frozen perturbation, propagation, recovery, or equivalent check before using that variable for selection or promotion.
- Apply transportability requirements only when evidence is used beyond its analysis or selection population, or when target, analysis, selection, and reporting populations differ materially. Keep unsupported populations parallel rather than silently generalizing.
- Apply screening-to-decision mapping only when screening and final evidence differ in statistic, estimand, scale, or role. Freeze the mapping, validation or calibration, and discordance rule. A rank association does not establish raw-scale prediction.
- Apply multiplicity or complete-selection-path inference whenever more than one data-informed test can influence the same decision, or whenever generation, adaptation, screening, ranking, or repeated looks occur. Choose a domain-appropriate method; do not force unrelated families into one universal null.
- Apply a frozen common seed or realization design when stochastic variation could change ranking or interpretation. Never select favorable seeds, checkpoints, or realizations.

## 6. Execute, Falsify, and Preserve

Freeze inputs, code or procedure state, parameters, exclusions, sample, statistic or model, seed policy, decision rule, and falsifier before each decision-bearing result. Verify that the available data can test the claim. Distinguish unavailable, unsupported, missing, censored, ineligible, invalid, and true-zero cases when relevant.

Estimate effects and relevant uncertainty, run at least one check capable of weakening the claim, and preserve diagnostics sufficient to reconstruct reported results. Read `references/falsification-toolkit.md` when the falsifier is not already clear. Use only the applicable domain adapter listed in the Reference Router.

Keep records append-only or versioned. Preserve nulls, weak effects, sign conflicts, invalid runs, abandoned paths, and unfavorable results. Inspect sealed evidence once under its frozen rule; mark it compromised if it influenced development.

## 7. Stop and Report Honestly

End `design_only` with a design report, `fixed_test` with a bounded test report, and `adaptive_search` with a stage or bounded report. Distinguish these valid stopping points from scientific completion.

Declare `coverage_search` complete within scope only when all are true:

```text
inventory_saturated AND coverage_complete
AND search_ledger_audited AND decision_contract_applied
AND terminal_decision_status
AND prior_exposure_audit_adequate_for_claim
AND consistency_validator_passed
```

If authorization, compute, cost, time, storage, or a user limit ends first, preserve the open queue and report a bounded pause. Do not relabel open cells as covered. Scope conclusions to the versioned candidate space supported by the available data; never claim exhaustion of all scientific possibilities.

Apply the frozen Decision Contract. Report a tie or inconclusive result when evidence does not separate eligible candidates, and `no_eligible_candidate` when none qualify. Do not default to the smallest nominal p-value or force a winner.

## Non-Negotiable Guardrails

- Do not remove, redefine, or hide data, attempts, thresholds, models, subgroups, transformations, or results because they weaken a claim.
- Do not rank ineligible candidates, nominal p-values alone, or results with incompatible targets, samples, estimands, or unresolved required gates.
- Do not silently replace the target population with a convenient subset or present post-result adaptation as confirmation.
- Do not treat missing support, invalid execution, inadequate sensitivity, or one failed formulation as rejection of a broader candidate.
- Do not treat one seed as stochastic robustness, same-data variants as independent verification, or metadata completeness as numerical reproducibility.
- Do not treat a completed round, a favorable threshold, a promoted candidate, or exhausted resources as scientific completion.
- Do not fabricate data, citations, approvals, provenance, commands, results, or coverage.
- Do not expose personal data, credentials, confidential paths, or restricted information.

## Reference Router

- For `design_only`: read no reference by default; load only the reference needed by the requested design.
- For `fixed_test`: read no reference by default. Load `references/claim-types.md`, `references/falsification-toolkit.md`, or a domain adapter only when the claim or test needs it.
- For `adaptive_search`: read `references/decision-selection.md`; read `references/statistical-discipline.md` only under its applicability rule.
- For `coverage_search`: read `references/coverage-search.md` and `references/decision-selection.md`; add `references/statistical-discipline.md` only when applicable.
- For formal artifact implementation at any executed profile: use `scripts/validate_run.py`; read `references/report-contract.md` only when the initialized schema or an error needs explanation.
- For a full `coverage_search` artifact audit or validator diagnosis: additionally read `references/status-schema.md` and `references/round-gate-checklist.md`.
- For observational support, censoring, geometry, or background contrast: read `references/observational-data.md`.
- For machine learning, benchmark optimization, or simulation: read `references/ml-simulation.md`.
- For causal, randomized, longitudinal, or experimental claims: read `references/causal-experimental.md`.
- For literature-dependent premises or novelty: read `references/literature-evidence.md`.
- For null or sign-inconsistent results requiring triage: read `references/null-triage.md`.
- For promotion or scientific write-up review: read `references/scientific-review-lens.md`.
- For difficult research judgment: read `references/thinking-principles.md`.
