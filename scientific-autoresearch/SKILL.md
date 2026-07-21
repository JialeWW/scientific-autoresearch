---
name: scientific-autoresearch
description: "Use this skill when an agent must systematically investigate mechanisms, observables, models, or simulations testable with current data: freeze a Decision Contract and prior-exposure audit, gate candidates by substantive alignment, measurement-error sensitivity, and population transport, search versioned finite coverage, cover the complete selection path, learn from nulls, and stop only at audited inventory saturation plus coverage completion. Do not use it for literature-only review, manuscript editing, routine execution of a fixed pipeline, or unauthorized live human, animal, clinical, field, or wet-lab actions."
license: MIT
metadata:
  version: "0.2.2"
---

# Scientific Autoresearch

Treat autoresearch as a coverage-guided evidence loop:

```text
question -> decision contract -> exposure audit -> inventory -> eligibility -> test -> audit
```

Search broadly within the finite space supported by current data; infer conservatively from the full search history. Bound the work by scientific scope, authorized data, governance, and reproducible execution—not by an arbitrary round or mechanism count.

## 1. Select the Execution Mode

Choose the least expansive mode that satisfies the request and record it before acting.

- `design_only`: Build or review an inventory, coverage plan, claim card, or test. Do not execute analyses or create a run directory unless the user requests an artifact.
- `single_round`: Execute one bounded analysis round and report. Use this by default when the user asks to test or analyze but does not request autonomous iteration.
- `multi_round`: Iterate autonomously through the data-supported coverage space. Use only when the user asks for an autonomous, iterative, systematic, or open-ended investigation.

For `multi_round`, obey any explicit user limit, but do not impose a universal numeric cap on scientific rounds or mechanism count. Before viewing outcomes, freeze:

- the scientific scope and authorized data products;
- the final decision, population roles, comparable families, ranking evidence, screening-to-decision scale mapping, transport requirements, and tie or inconclusive rules;
- the prior-exposure audit and resulting restrictions on evidence stage;
- the protocol for constructing, deduplicating, versioning, and auditing the mechanism inventory;
- the rule that makes each mechanism's observable and formulation set finite;
- the evidence partitions, complete-selection-path inference strategy, and stopping rules;
- the execution envelope for systems, data looks, compute, cost, time, storage, and external actions.

Rounds are immutable result-review-decision checkpoints, not the scientific stopping criterion. An execution limit controls what may run now; it does not shrink the scientific search space or convert untested cells into completed coverage. If a user limit or resource envelope is reached first, preserve the open queue and use a pause or bounded-stop status rather than claiming saturation.

Never interpret “continue,” “do not stop,” or similar persistence language as permission to exceed safety, governance, data-access, compute, cost, or external-action boundaries.

## 2. Pass the Scope and Governance Gate

Before Round 0, classify the work as computation-only, ordinary existing data, sensitive or regulated existing data, or prospective/live experimental work.

Record:

- authorized data, tools, systems, actions, output locations, and resource limits;
- data-use, consent, privacy, licensing, confidentiality, and retention constraints;
- required protocol, ethics, safety, institutional, or domain approvals;
- the responsible human decision-maker for regulated, hazardous, clinical, animal, or live experimental work.

Keep raw inputs read-only. Write only to a dedicated output root. Minimize or de-identify case-level artifacts, and redact credentials, tokens, signed links, private identifiers, and secrets from logs and reproduction commands.

Do not infer that an approval exists. Do not recruit participants, alter approved protocols, operate instruments, submit shared or paid jobs, trigger external systems, or perform hazardous or regulated actions without explicit authorization and competent human oversight. If a prerequisite is absent, set `governance_status=blocked`, preserve a design-only report if useful, and stop.

An explicit compute approval may cover a finite multi-round authorization envelope. Record its systems, account or project, job classes, data and output scope, total and concurrent use, cost, storage, validity window, and stop mechanism. Do not request approval again for work wholly inside that envelope. Request renewed authorization before exceeding or changing a boundary, or if authorization expires, is revoked, or becomes unsafe.

Read `references/governance-safety.md` whenever data are sensitive, actions affect external systems, compute is costly, or work is regulated or physical.

## 3. Freeze the Data-Supported Search Space

Read `references/coverage-search.md` and `references/decision-selection.md`, then create Round 0:

1. State the scientific question and classify each claim using `references/claim-types.md`.
2. Freeze `decision_contract.json`: the final decision; target, analysis, selection, and reporting populations; eligible candidate classes; substantive eligibility, measurement-error, transport, and evidence-scale rules; comparable families; estimand; ranking evidence; tie and inconclusive rules; and complete-selection-path inference. If screening and decision evidence use different statistics or scales, preregister their mapping, validation, and discordance rule. Never default to the smallest nominal p-value. A contract created after outcomes were viewed is `post_result_adaptive`.
3. Complete `prior_exposure_audit.json` for analyses, parameter attempts, data looks, selections, and results involving the same or overlapping data. Changing a sample, codebase, model, repository, workflow, or skill version does not restore confirmatory status.
4. Build a versioned `mechanism_inventory`. For every proposed mechanism, record its distinct pathway, inclusion rationale, generation source, applicable regimes, required data products, support status, and whether it is nonredundant and testable with current data.
5. Map every eligible mechanism through `mechanism -> observable role -> formulation` into finite coverage cells. Record the mechanism or claim alignment, supported sample, parameter or scale regime, expected signature, meaningful effect, sensitivity requirement, and falsifier.
6. Use a constrained or full product only when every axis and cell has a frozen substantive, control, or diagnostic role; rank only decision-eligible cells. Do not flatten unrelated mechanisms into one statistical pool or claim pointwise coverage of a continuum.
7. Keep plausible mechanisms unsupported by current data in the inventory with `mechanism_status=needs_data`. Do not count them as executed coverage or evidence against the mechanism.
8. Freeze complementary inventory-generation lenses, including mechanism-forward decomposition and data-product-to-mechanism reverse mapping. Add an independent third lens—such as literature, theory, expert elicitation, or failure-mode analysis—when the question makes it informative. Literature review is conditional, not universal.
9. Separate exploratory development, internal validation, sealed-holdout verification, and independent external verification before candidate-specific results are inspected.
10. Define every selection family with structured target population, supported sample, estimand, evidence stage, data-quality regime, and transport status. Keep noncomparable results parallel or `support_limited_candidate` unless a prespecified valid mapping makes comparison possible.
11. Append every test or choice capable of influencing candidate generation, modification, screening, retention, ranking, verification targeting, or promotion to the ledger. Choose a method that covers this complete selection path; do not force unrelated domains into one universal global-null method.
12. Freeze a domain-appropriate measurement-error policy. If uncertainty can change support, matching, subgroup membership, thresholds, eligibility, or ranking, require perturbation, propagation, recovery, or another justified sensitivity analysis before promotion.
13. Select only applicable adapters:
   - observational support, censoring, geometry, or background: `references/observational-data.md`;
   - machine learning, benchmark optimization, or simulation: `references/ml-simulation.md`;
   - causal, randomized, longitudinal, or experimental claims: `references/causal-experimental.md`;
   - literature-dependent premise or novelty: `references/literature-evidence.md`.

Read `references/statistical-discipline.md` before adaptive scans, repeated testing, stochastic comparisons, candidate ranking, or promotion.

## 4. Execute One Coverage Round

For each round:

1. Select unresolved coverage cells without changing their frozen scientific meaning. A scheduler may run one or more frozen, sensitivity-audited low-cost screening stages within declared comparable screening families before deeper tests, but priority changes only execution order: unrun cells remain open.
2. Freeze the exact claim card, inventory and family versions, inputs, code state, parameters, seed set, sample, exclusions, statistic, model, and falsifier before inspecting results.
3. Verify that available data can test the cell. Separate unavailable, unsupported, missing, censored, nondetected, low-quality, ineligible, and true-zero cases when those distinctions matter.
4. Apply the frozen substantive-alignment and evidence-scale gates before ranking. Match the observable, representation, statistic, and estimand to the claim. A rank-based association screen does not validate raw-scale prediction without the registered mapping; keep uncalibrated proxies and diagnostics in their declared roles.
5. Complete any required measurement-error sensitivity analysis before using a quality or uncertainty variable for eligibility, subgroup selection, ranking, or promotion. The skill does not prescribe one computational method or access route.
6. Run the simplest valid test capable of changing belief. Add flexibility only for a stated scientific reason.
7. Estimate effects in meaningful units and decompose statistical, systematic, calibration, model-choice, stochastic, and sample-variance uncertainty as applicable.
8. Run at least one falsification check that could genuinely weaken the claim. Read `references/falsification-toolkit.md`.
9. Save enough data-minimized diagnostics to reconstruct reported statistics and plots.
10. Record specification timing, evidence stage, comparability, decision, result, coverage, verification, and execution statuses from `references/status-schema.md`. Preserve weak, null, inconclusive, invalid, failed, abandoned, and unfavorable branches.
11. If evidence motivates a new mechanism, formulation, or target population, preserve the original result, assign a new ID or version, label the addition post-result adaptive and exploratory, extend the complete selection path, and reset affected audits.
12. Complete `references/round-gate-checklist.md`, write immutable round artifacts, run the consistency validator, and select the next unresolved cells.

Do not inspect a sealed holdout repeatedly. Freeze preprocessing, feature selection, formula, sample, model, hyperparameters, seed policy, and decision rule before one final verification evaluation. If verification evidence influenced development, mark it `compromised`.

One seed may support a smoke test or exact reproduction. When stochastic variation could change ranking or interpretation, use a predeclared common seed or realization set, or another justified variance design. Never select the luckiest seed, checkpoint, or realization.

## 5. Audit Saturation, Coverage, and Evidence

Set `inventory_saturated=true` only after the prespecified complementary audits find no new eligible, nonredundant, data-supported mechanism. Require one complete mechanism-forward audit and one complete data-product-reverse audit after the most recent eligible addition. When Round 0 declared an independent third lens informative, it must also be completed. Any new eligible mechanism increments the inventory version and resets the affected audit sequence.

Set `coverage_complete=true` only when every eligible cell in that same inventory version is closed under the rules in `references/coverage-search.md`, and the full ledger and complete-selection-path inference have been audited.

Scientific completion requires all four:

```text
inventory_saturated
AND coverage_complete
AND search_ledger_audited
AND decision_contract_applied
```

Compute, cost, time, authorization, or user-limit exhaustion produces `resource_limited_pause`, `governance_blocked`, or `user_limited_stop` when eligible cells remain. These states are not scientific completion.

Promote a candidate only after recording:

- the exact claim, estimand, supported sample, effect, uncertainty, and minimum meaningful scale;
- passed substantive-alignment and any required measurement-error and transportability gates;
- its comparability key and selection family, or a parallel or `support_limited_candidate` status;
- the full generation, modification, screening, ranking, and promotion history and the inference that covers that path;
- specification timing and evidence stage;
- an actual falsifier and dominant alternatives or systematics;
- verification status based on untouched evidence.

Apply the frozen Decision Contract, update `candidate_registry.csv`, and record `decision_contract_applied` plus the terminal `decision_status`. If its evidence rule does not separate eligible candidates, report `tie` or `inconclusive`; if none pass eligibility, use `no_eligible_candidate`. Do not force a winner. Do not promote a same-data adaptive formulation as confirmation. Require untouched verification evidence or a valid end-to-end null, selective, sequential, hierarchical, Bayesian model-comparison or model-averaging, or other justified method that covers the actual selection path.

## 6. Preserve Immutable Outputs

Use this layout unless the project defines an equivalent immutable convention:

```text
runs/<run_id>/
  run_manifest.json
  decision_contract.json
  prior_exposure_audit.json
  data_versions.json
  inventories/
    mechanism_inventory_v001.csv
    coverage_matrix_v001.csv
    saturation_audit_v001.json
  search_ledger.jsonl
  selection_families.json
  execution_queue.csv
  status_transitions.jsonl
  candidate_registry.csv
  rounds/round_000/
    report.md
    inventory.json
    summary.csv
    diagnostics.<csv|parquet|jsonl>   # only when needed and safe
    figures/                          # only when needed
    reproduce_commands.txt
    round_gate.md
  pause_report.md                     # only when paused or blocked
  consistency_report.json
  final_report.md                     # only after complete_within_scope
```

Never overwrite an earlier contract, audit, inventory, coverage matrix, ledger entry, or round. Record lineage, data versions, hashes when permitted, code state, environment, actual seeds, family versions, resource use, artifact paths, and status transitions. Redact secrets and sensitive identifiers. Read `references/report-contract.md` before creating executed-run artifacts; use `scripts/validate_run.py --init <run_dir>` to create a non-overwriting schema skeleton instead of hand-copying metadata.

Run `scripts/validate_run.py <run_dir> --output <run_dir>/consistency_report.json` before resuming an existing run and before issuing any pause or final report. Fix consistency errors or report the run as blocked or incomplete; a large collection of artifacts is not evidence that the search history is complete.

## Non-Negotiable Guardrails

- Do not remove, redefine, or hide data because they weaken a result.
- Do not hide attempted tests, data looks, thresholds, models, subgroups, transformations, weak effects, or failed branches.
- Do not correct only the visible winners; account for every evaluable test that influenced the same selection or promotion decision.
- Do not rank candidates before substantive eligibility, by nominal p-value alone, across incompatible targets, or when required measurement-error or transportability checks remain open.
- Do not use association evidence on one scale as predictive evidence on another without a frozen, validated mapping and discordance rule.
- Do not silently replace the frozen target population with a convenient subgroup. Create a new decision version and keep the original decision visible.
- Do not force scientifically unrelated claims into one unjustified universal null. Freeze and justify selection-family boundaries.
- Do not restore confirmatory status merely by changing a sample, codebase, model, repository, workflow, or skill version after overlapping data were inspected.
- Do not confuse missingness, lack of support, invalid execution, or inadequate sensitivity with evidence for a null.
- Do not call a mechanism rejected because one formulation failed.
- Do not use post-result choices as confirmatory evidence or same-data variants as independent validation.
- Do not select seeds, checkpoints, or realizations because they improve the result.
- Do not treat resource exhaustion, a favorable threshold, a completed round, or one promoted candidate as coverage completion.
- Do not claim all possible mechanisms or models were exhausted. Scope statements to the versioned search space testable with the available data products.
- Do not fabricate data, citations, approvals, provenance, commands, results, or coverage.
- Do not expose personal data, credentials, confidential paths, or restricted information.
- Do not equate incomplete metadata with numerical nonreproducibility. Report structural audit status and same-input, same-code, same-seed reproduction evidence separately.

## Reference Router

- Coverage inventory, saturation, closure, and publication scope: `references/coverage-search.md`.
- Decision Contract, prior exposure, comparability, and complete selection path: `references/decision-selection.md`.
- Every executed run: `references/status-schema.md`, `references/report-contract.md`, and `references/round-gate-checklist.md`.
- Claim classification: `references/claim-types.md`.
- Selection families, multiplicity, holdouts, sensitivity, and stochasticity: `references/statistical-discipline.md`.
- Null, weak, or sign-inconsistent result: `references/null-triage.md`.
- Falsification design: `references/falsification-toolkit.md`.
- Observational support, censoring, geometry, or background contrast: `references/observational-data.md`.
- Machine learning, benchmark, or simulation: `references/ml-simulation.md`.
- Causal or experimental claims: `references/causal-experimental.md`.
- Sensitive, regulated, costly, external, or physical work: `references/governance-safety.md`.
- Literature-dependent premise or novelty claim: `references/literature-evidence.md`.
- Promotion or write-up review: `references/scientific-review-lens.md`.
- Difficult research judgment: `references/thinking-principles.md`.
- Machine consistency check before resume, pause, or finalization: `scripts/validate_run.py`.
