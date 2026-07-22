---
name: scientific-autoresearch
description: "Use this skill when scientific work requires formal audit or provenance, when outcome-informed choices generate, modify, screen, compare, rank, or promote data-supported candidates, or when systematic coverage of a finite data-supported candidate space is requested. It provides proportionate profiles for research design, read-only audit, frozen analyses, adaptive search, and coverage search, with safeguards requiring inference to account for the actual selection path."
license: MIT
metadata:
  version: "0.2.6"
---

# Scientific Autoresearch

Match process weight to outcome adaptivity, not to the number of analyses alone. Search actively when requested, but infer conservatively from every outcome-dependent choice. Bound execution by authorized scope and resources; bound scientific claims by the data-supported search space.

## 1. Select and Freeze a Profile

Choose the least expansive profile that covers the requested work. Record the profile before inspecting new outcomes.

- `design_only`: Prospectively design work without inspecting completed outcomes or executing analysis.
- `audit_only`: Inspect completed work read-only, without producing new outcomes or changing candidate selection.
- `fixed_test`: Execute one frozen claim through one prespecified analysis or a finite prespecified family under frozen joint rules.
- `adaptive_search`: Let outcome-informed choices generate, modify, screen, compare, rank, or promote candidates, without claiming coverage completion.
- `coverage_search`: Systematically cover the finite candidate and observable space supported by available data and assess scoped completion.

The number of frozen analyses does not by itself create adaptivity. Keep a prespecified finite comparison in `fixed_test` when its membership, methods, multiplicity or joint rule, and reporting rule were fixed before outcomes. Treat any outcome-informed change to those elements as `adaptive_search` or `coverage_search`.

Choose record mode separately from research profile:

- `conceptual_record` is the default. Preserve required decisions and provenance in the working report or existing project records; prescribed JSON and CSV filenames are not required.
- `machine_audited` applies when the user requests structured machine audit, an existing run already uses the schema, a formal handoff or resume requires it, or `coverage_search` is ready to claim `complete_within_scope`. Initialize an empty run path with `scripts/validate_run.py --init RUN_DIR --profile PROFILE`, complete only generated profile artifacts, and validate before a machine-audited bounded, pause, or completion report.

`audit_only` may validate an existing machine-audited run read-only, but it does not initialize or upgrade an execution run unless new analysis is separately authorized.

For an authorized execution or resume of a schema-1.5.2-or-later run, call `scripts/validate_run.py --record-skill-provenance RUN_DIR` before producing new outcomes. The command is idempotent and appends only a changed skill identity; ordinary validation remains read-only.

## 2. Preserve History When the Profile Changes

Upgrade the profile before continuing whenever the work exceeds its frozen boundary.

- Move `design_only` to `audit_only` before inspecting completed results, or to an execution profile before generating new results.
- Move `audit_only` to an execution profile before running a new analysis or making an outcome-informed candidate change.
- Upgrade `fixed_test` to `adaptive_search` when its outcome motivates a new candidate, formulation, threshold, sample, model, statistic, or ranking. Preserve the original test and label the addition post-result adaptive.
- Upgrade `adaptive_search` to `coverage_search` only when systematic scoped coverage becomes the goal. Seed the inventory and ledger with the complete earlier history; do not claim retrospective saturation.
- Never downgrade a run to erase selection, exposure, failed branches, or stricter obligations.

Record each profile transition, reason, timing, and prior outcome access. Changing data subsets, code, models, tools, workflows, or skill versions does not restore confirmatory status after overlapping data were inspected.

For a `machine_audited` execution run, record any changed skill identity, validate the current profile, and use `scripts/validate_run.py --snapshot-upgrade RUN_DIR --to-profile PROFILE` before migration. Review its non-overwriting, hash-bound preservation snapshot, add the returned `profile_history` entry, create only the newly required profile artifacts, and validate again. A preservation attestation without the referenced evidence is insufficient.

## 3. Pass Scope and Governance Gates

Before execution, record the scientific scope, authorized data and actions, output boundary, resource envelope, data-use constraints, and required human oversight. Keep raw inputs read-only when practical, minimize sensitive outputs, and redact credentials, private identifiers, and restricted information.

Do not infer approval. Do not trigger costly, shared, regulated, hazardous, prospective, or physical actions outside explicit authorization. If a prerequisite is absent, stop execution and preserve a useful design or blocked report. Treat persistence requests as persistence only within the recorded boundaries.

## 4. Apply the Chosen Workflow

### `design_only`

State the question, claim, estimand, supported data, proposed test, falsifier, assumptions, uncertainty sources, and next decision. Clearly label every unexecuted result as expected or hypothetical. Create only the requested planning artifact.

### `audit_only`

Inspect the supplied results, methods, provenance, and existing artifacts without producing new scientific outcomes. Identify the recorded or effective execution profile, then apply its scientific checks read-only: fixed-scope integrity for a frozen analysis, selection-path and comparability checks for adaptive work, and saturation and closure checks for a coverage claim. State what was checked, what remains unknown, whether the claim matches the estimand and evidence stage, and which conclusions are supported. Recommend future work without executing, repairing, or silently reclassifying it.

### `fixed_test`

Before outcomes, freeze a compact claim card containing:

- claim, estimand, target and analysis population, supported sample, and meaningful effect scale;
- `analysis_scope=single_test` or `analysis_scope=frozen_family`; for a family, its finite member IDs, member methods, multiplicity or joint inference rule, joint decision rule, and reporting rule;
- input versions, exclusions, statistics or models, parameters, seed policy when relevant, decision rule, prespecified checks, and falsifier;
- specification timing, prior exposure to overlapping data, and intended evidence stage.

Run only the frozen analysis or family. Report each prespecified member needed to reconstruct the joint decision, the effect in meaningful units, uncertainty, assumption and falsification results, limitations, actual inputs and parameters, code or procedure state, seeds when used, and reproduction command or equivalent recipe. A prespecified falsifier or robustness check is part of the frozen family and does not trigger an upgrade. Preserve every member even when weak, null, failed, or unfavorable.

Do not build a candidate inventory, adaptive selection ledger, saturation audit, or coverage matrix for a genuine `fixed_test`. Call the result a completed frozen analysis, not a completed search.

### `adaptive_search`

Before adaptive outcomes, freeze compact records for:

1. a Decision Contract defining the decision, candidate eligibility, target and any distinct analysis, selection, or reporting populations, comparison rules, estimands, ranking evidence, tie and inconclusive rules, evidence partitions, and applicable conditional gates;
2. a bounded prior-exposure audit with declared projects, sources, time range or search budget, overlap unit, uncertain gaps, and completion rule;
3. selection families that separate candidates with incompatible targets, samples, estimands, evidence stages, or data-quality regimes;
4. a search ledger that receives every choice or test capable of changing candidate generation, modification, screening, retention, ranking, verification targeting, or promotion.

Version outcome-motivated additions, retain failed branches, and label their timing and evidence stage. Use an inference strategy that covers the actual selection path. Issue a stage or bounded report when execution ends; never claim inventory saturation or coverage completion from this profile.

### `coverage_search`

Complete the `adaptive_search` requirements, then:

1. Build and version a typed candidate inventory. Admit a new candidate only when it has a distinct substantive role, a distinct data-testable signature, and a possible effect on the frozen decision; otherwise classify it as a formulation or duplicate.
2. Map eligible entries into finite cells through `candidate -> observable or test role -> formulation`. Let one cell represent a frozen finite parameter domain or integration rule when scientifically coherent; do not split trivial parameter values into separate scientific candidates or create an unrelated Cartesian ranking pool.
3. Generate inventory through candidate-forward and data-product-reverse audits. Add an independent third lens such as theory, literature, expert knowledge, or failure modes only when informative for the question.
4. Separate scientific coverage from scheduling. Permit uniform low-cost screening before deeper tests, but let priority change only execution order. Keep every unrun eligible cell open and preserve the queue when resources end.
5. Batch additions found in one audit checkpoint into a successor inventory version. Reopen only affected families and cells, retain valid closure of unaffected cells, then repeat the required saturation audits after the latest batch. Do not impose a universal round or candidate cap.

Treat unsupported but plausible entries as `needs_data`, not as executed coverage or evidence against them. Rank only substantively eligible and mutually comparable candidates.

## 5. Activate Gates Only When Applicable

Record one reason when a gate is not applicable; do not manufacture repeated placeholder work.

- Apply substantive alignment before statistical ranking. Require a candidate to support the frozen scientific or operational decision; allow mechanism alignment to be not applicable for a nonmechanistic task only with a stated reason.
- Apply measurement-error sensitivity only when uncertainty could change support, matching, thresholds, subgroup membership, eligibility, ranking, or interpretation. Complete the frozen perturbation, propagation, recovery, or equivalent check before using that variable for selection or promotion.
- Apply transportability requirements only when evidence is used beyond its analysis or selection population, or when target, analysis, selection, and reporting populations differ materially. Keep unsupported populations parallel rather than silently generalizing.
- Apply screening-to-decision mapping only when screening and final evidence differ in statistic, estimand, scale, or role. Freeze the mapping, validation or calibration, and discordance rule. A rank association does not establish raw-scale prediction.
- Apply a prespecified joint or multiplicity rule when a frozen finite family informs one decision. Apply complete-selection-path inference when outcome-informed generation, modification, screening, ranking, or repeated looks can influence a decision. Choose a domain-appropriate method; do not force unrelated families into one universal null.
- Apply a frozen common seed or realization design when stochastic variation could change ranking or interpretation. Never select favorable seeds, checkpoints, or realizations.

## 6. Execute, Falsify, and Preserve

Freeze inputs, code or procedure state, parameters, exclusions, sample, statistic or model, seed policy, decision rule, and falsifier before each decision-bearing result. Verify that the available data can test the claim. Distinguish unavailable, unsupported, missing, censored, ineligible, invalid, and true-zero cases when relevant.

Estimate effects and relevant uncertainty, run the frozen check capable of weakening the claim, and preserve diagnostics sufficient to reconstruct reported results. A prespecified check does not create adaptivity; an outcome-motivated new check does. Use only the applicable references listed in the Reference Router.

Keep records append-only or versioned. Preserve nulls, weak effects, sign conflicts, invalid runs, abandoned paths, and unfavorable results. Inspect sealed evidence once under its frozen rule; mark it compromised if it influenced development.

## 7. Stop and Report Honestly

End `design_only` with a design report, `audit_only` with a read-only audit report, `fixed_test` with a bounded frozen-analysis report, and `adaptive_search` with a stage or bounded report. Distinguish these valid stopping points from scientific completion.

Declare `coverage_search` complete within scope only from a validated `machine_audited` record and when all are true:

```text
inventory_saturated AND coverage_complete
AND search_ledger_audited AND decision_contract_applied
AND terminal_decision_status
AND prior_exposure_audit_adequate_for_claim
AND consistency_validator_passed
```

A passing consistency report establishes only that the recorded artifacts satisfy applicable schema and cross-record checks. It does not establish numerical correctness, completeness of unrecorded history, empirical operating characteristics, or independent scientific verification.

If authorization, compute, cost, time, storage, or a user limit ends first, preserve the open queue and report a bounded pause. Do not relabel open cells as covered. Scope conclusions to the versioned candidate space supported by the available data; never claim exhaustion of all scientific possibilities.

Apply the frozen Decision Contract. Report a tie or inconclusive result when evidence does not separate eligible candidates, and `no_eligible_candidate` when none qualify. Summarize branch classes and link the complete registry or ledger rather than expanding every branch into final-report prose. Do not default to the smallest nominal p-value or force a winner.

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
- For `audit_only`: read no reference for a simple frozen-result audit. When auditing adaptive or coverage work, identify its effective profile and apply the same `decision-selection.md` and, when applicable, `coverage-search.md` checks read-only. For an existing machine-audited run, use its validator and load artifact references only to interpret an error.
- For `fixed_test`: read no reference by default. Load `references/statistical-discipline.md` only when a frozen-family multiplicity or stochastic rule needs design; otherwise load only the claim, falsification, or domain reference needed.
- For `adaptive_search`: read `references/decision-selection.md`; read `references/statistical-discipline.md` only when its method-selection guidance is needed.
- For `coverage_search`: read `references/coverage-search.md` and `references/decision-selection.md`; add `references/statistical-discipline.md` only when its method-selection guidance is needed.
- For `machine_audited` implementation at any executed profile: use `scripts/validate_run.py`; read `references/report-contract.md` only when the initialized schema or an error needs explanation.
- For a full `coverage_search` artifact audit or validator diagnosis: additionally read `references/status-schema.md` and `references/round-gate-checklist.md`.
- For sensitive, regulated, costly, prospective, physical, or external-system work: read `references/governance-safety.md`.
- When the required falsifier or robustness check is unclear: read `references/falsification-toolkit.md`.
- For validation or benchmarking of a method, estimator, pipeline, workflow, or this skill: read `references/claim-types.md`; also read `references/ml-simulation.md` when the benchmark is computational.
- When the scientific claim type or its minimum evidentiary requirements are unclear: read `references/claim-types.md`.
- For observational support, censoring, geometry, or background contrast: read `references/observational-data.md`.
- For machine learning, benchmark optimization, or simulation: read `references/ml-simulation.md`.
- For causal, randomized, longitudinal, or experimental claims: read `references/causal-experimental.md`.
- For literature-dependent premises or novelty: read `references/literature-evidence.md`.
- For null or sign-inconsistent results requiring triage: read `references/null-triage.md`.
- For promotion or scientific write-up review: read `references/scientific-review-lens.md`.
- For difficult research judgment: read `references/thinking-principles.md`.
