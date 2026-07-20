---
name: scientific-autoresearch
description: "Use this skill when an agent must run a bounded, iterative scientific investigation over data, code, models, simulations, or approved experimental records: turn an open-ended question into mechanism-based claims, test and falsify them, learn from nulls, and preserve reproducible evidence across rounds. Do not use it for literature-only review, manuscript editing, routine execution of a fixed pipeline, or unauthorized live human, animal, clinical, field, or wet-lab actions."
license: MIT
metadata:
  version: "0.2.0"
---

# Scientific Autoresearch

Treat autoresearch as a bounded evidence loop:

```text
question -> mechanism -> claim -> test -> falsification -> interpretation -> decision
```

Optimize belief, not significance. Preserve negative results, failed branches, and uncertainty. Never turn repeated search on the same evidence into confirmation.

## 1. Select the Execution Mode

Choose the least expansive mode that satisfies the request and record it before acting.

- `design_only`: Form hypotheses, review an analysis design, or propose tests. Do not execute analyses or create a run directory unless the user requests an artifact.
- `single_round`: Execute one bounded analysis round and report. Use this by default when the user asks to test or analyze but does not request autonomous iteration.
- `multi_round`: Iterate autonomously within a finite frozen budget. Use only when the user asks for an autonomous, iterative, or open-ended investigation.

For `multi_round`, obey any user budget. If none is supplied, freeze this conservative default before viewing outcomes:

- at most 3 executed rounds,
- at most 4 active candidate mechanisms,
- at most 1 post-result formulation mutation for any null formulation,
- no new data acquisition, paid or nontrivial external compute, external submissions, live experiments, or changes to shared systems without explicit approval.

Never interpret “continue,” “do not stop,” or similar persistence language as permission to exceed safety, governance, data-access, compute, cost, or external-action boundaries.

## 2. Pass the Scope and Governance Gate

Before Round 0, classify the work as computation-only, ordinary existing data, sensitive or regulated existing data, or prospective/live experimental work.

Record:

- authorized data, tools, systems, actions, output locations, and resource limits;
- data-use, consent, privacy, licensing, confidentiality, and retention constraints;
- required protocol, ethics, safety, institutional, or domain approvals;
- the responsible human decision-maker for regulated, hazardous, clinical, animal, or live experimental work.

Keep raw inputs read-only. Write only to a dedicated output root. Minimize or de-identify case-level artifacts, and redact credentials, tokens, signed links, private identifiers, and secrets from logs and reproduction commands.

Do not infer that an approval exists. Do not recruit participants, alter approved protocols, operate instruments, submit cluster or paid jobs, trigger external systems, or perform hazardous or regulated actions without explicit authorization and competent human oversight. If a required prerequisite is absent, set `governance_status=blocked`, preserve a design-only report if useful, and stop.

Read `references/governance-safety.md` whenever data are sensitive, actions affect external systems, compute is costly, or the work is regulated or physical.

## 3. Freeze Round 0 Before Looking at Outcomes

Create a finite research plan before adaptive testing:

1. State the scientific question and classify each claim using `references/claim-types.md`.
2. Define a versioned claim card: claim ID, mechanism, target population or system, unit of inference, observable or outcome, comparator, expected direction, minimum meaningful effect, supported sample, assumptions, and primary or exploratory status.
3. Register a small candidate portfolio. Do not generate an unlimited feature or model menu.
4. Freeze the round, data-look, compute, cost, and candidate budgets plus success, futility, inconclusive, safety, and stopping boundaries.
5. Separate discovery data from sealed verification data when possible. State what would compromise the seal.
6. Register the search and inference ledger: claim families, planned variants, thresholds, number and timing of looks, multiplicity strategy, and every attempted branch.
7. Estimate sensitivity, precision, power, or detectable-effect limits where inference depends on a null or small effect.
8. Inventory data, code, model, environment, versions, hashes when practical, lineage, units, exclusions, and randomization sources.
9. Select only the applicable domain adapters:
   - observational, catalog, censoring, support, or geometry questions: `references/observational-data.md`;
   - machine learning, benchmark optimization, or stochastic simulation: `references/ml-simulation.md`;
   - causal claims, randomized or longitudinal designs, or experimental records: `references/causal-experimental.md`;
   - novelty or literature-dependent premises: `references/literature-evidence.md`.

Read `references/statistical-discipline.md` before any adaptive scan, repeated testing, stochastic comparison, or confirmatory inference.

## 4. Execute One Scientific Round

For each executed round:

1. Freeze the exact claim card, inputs, code state, parameters, seed set, sample, exclusions, statistic, model, and planned falsifier before inspecting the result.
2. Verify that the available data can test the claim. Separate unavailable, unsupported, missing, censored, nondetected, low-quality, ineligible, and true-zero cases when those distinctions matter.
3. Match the observable, scale, representation, and statistic to the mechanism. Do not promote a convenient proxy as a direct measurement without calibration.
4. Run the simplest test capable of changing belief. Add model flexibility only for a stated scientific reason.
5. Estimate the effect in meaningful units and decompose statistical, systematic, calibration, model-choice, Monte Carlo, and sample-variance uncertainty as applicable.
6. Run at least one falsification check that could genuinely weaken the claim. Read `references/falsification-toolkit.md` before selecting it.
7. Save enough data-minimized diagnostics to reconstruct reported statistics and plots. Use aggregate or de-identified diagnostics when case-level data are sensitive.
8. Interpret the result using the canonical fields in `references/status-schema.md`. Distinguish association, mechanism-consistency, causal evidence, internal validation, holdout verification, and external replication.
9. If the result is weak or null, read `references/null-triage.md`. Preserve the frozen primary result. Any post-result redesign is exploratory and consumes the registered mutation budget.
10. Complete `references/round-gate-checklist.md`, write immutable round artifacts, and select the next action only within the remaining budget.

Do not inspect a sealed holdout repeatedly. Freeze preprocessing, feature selection, formula, sample, model, hyperparameters, seed policy, and decision rule before one final verification evaluation. If verification evidence influenced development, mark it `compromised` and do not call it independent.

One seed may support deterministic reproduction or a smoke test. When stochastic variation could change the conclusion, use a predeclared seed set or another justified variance estimate; never select the luckiest seed.

## 5. Promote, Mutate, or Stop

Promote a candidate only after recording:

- the exact estimand or scientific claim;
- effect size, uncertainty, minimum meaningful scale, and dominant systematics;
- supported sample and treatment of missing, censored, nondetected, or excluded cases;
- complete search history and multiplicity handling;
- whether the analysis was frozen, exploratory, scan-selected, internally checked, holdout-verified, or externally replicated;
- a falsification result that could have hurt the claim;
- literature context when novelty or prior evidence matters.

Do not promote a same-data mutation as confirmation. Require untouched verification evidence or a valid selective or sequential inference method.

Stop when any of these applies:

- the frozen round, data-look, compute, cost, or mutation budget is exhausted;
- a predeclared success, futility, safety, or inconclusive boundary is reached;
- a candidate is frozen for verification or write-up;
- all registered candidates are resolved as supported, null, inconclusive, invalid, rejected, or blocked;
- continuation needs new data, a new scientific assumption, a new authorization, or human scientific judgment.

Never stop merely because a favorable threshold was crossed. Never continue merely because no favorable result appeared.

## 6. Preserve Immutable Outputs

Use this layout for executed runs unless the project defines an equivalent immutable convention:

```text
runs/<run_id>/
  run_manifest.json
  candidate_registry.csv
  rounds/round_000/
    report.md
    inventory.json
    summary.csv
    diagnostics.<csv|parquet|jsonl>   # only when needed and safe
    figures/                          # only when needed
    reproduce_commands.txt
    round_gate.md
  final_report.md
```

Never overwrite an earlier round. Record parent round, claim IDs, input hashes, code state, environment, actual seed set, artifact paths, and status fields in each inventory. Redact secrets and sensitive identifiers. Read `references/report-contract.md` before creating executed-run artifacts.

## Non-Negotiable Guardrails

- Do not remove or redefine data because they weaken the result.
- Do not hide attempted tests, thresholds, models, subgroups, transformations, or failed branches.
- Do not confuse missingness, lack of support, or inadequate sensitivity with evidence for a null.
- Do not call a broad mechanism rejected because one formulation failed.
- Do not use post-hoc choices as confirmatory evidence.
- Do not call same-data variants independent validation.
- Do not call a support, quality, coverage, or availability variable a mechanism without a defensible scientific link.
- Do not fabricate data, citations, approvals, provenance, commands, or results.
- Do not expose personal data, credentials, confidential paths, or restricted information in artifacts.

## Reference Router

- Every executed run: `references/status-schema.md`, `references/report-contract.md`, and `references/round-gate-checklist.md`.
- Claim classification: `references/claim-types.md`.
- Adaptive search, multiple testing, holdouts, sensitivity, or stochasticity: `references/statistical-discipline.md`.
- Null, weak, or sign-inconsistent result: `references/null-triage.md`.
- Falsification design: `references/falsification-toolkit.md`.
- Observational support, censoring, match geometry, or background contrast: `references/observational-data.md`.
- Machine learning, benchmark, or stochastic simulation: `references/ml-simulation.md`.
- Causal or experimental claims: `references/causal-experimental.md`.
- Sensitive, regulated, costly, external, or physical work: `references/governance-safety.md`.
- Literature-dependent premise or novelty claim: `references/literature-evidence.md`.
- Promotion or write-up review: `references/scientific-review-lens.md`.
- Difficult research judgment: `references/thinking-principles.md`.
