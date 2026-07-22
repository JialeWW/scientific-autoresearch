# Profile-Aware Round Gate

Use this checklist for machine-artifact audit or validator diagnosis after an executed round. `design_only` and `audit_only` have no round gate. Apply the shared items and only the recorded execution profile; do not create placeholder work for an inapplicable gate.

## Every Executed Profile

- **Identity and scope**: Are run, profile, profile history, stage, round lineage, scientific scope, data versions, and governance boundaries recorded?
- **Frozen work**: Were the claim or decision, supported sample, estimand, analysis, meaningful scale, decision rule, falsifier, inputs, parameters, exclusions, and seed policy fixed at the correct time?
- **Units and dependence**: Were the analysis and independence units, dependence handling, and partition or resampling unit frozen and followed?
- **Domain adapter**: Was the need for a domain adapter or project data preflight assessed before affected outcomes, with every required hash-bound check passed or transparently blocking the result?
- **Exposure and evidence**: Are earlier overlapping analyses and outcome views represented, and are specification timing, evidence stage, and verification status honest?
- **Support and validity**: Are unavailable, unsupported, missing, censored, ineligible, invalid, and true-zero cases separated when relevant? Could the analysis detect or exclude a meaningful effect?
- **Result**: Are effect, uncertainty, assumptions, diagnostics, falsification outcome, execution status, result status, limitations, and weak or unfavorable evidence retained?
- **Stochasticity**: Were seeds, realizations, checkpoints, and failed runs handled under the frozen policy without favorable selection?
- **Reproduction**: Are exact secret-free steps, actual input/code/environment state, seeds, tolerances, and expected outputs recorded? Are metadata consistency and numerical agreement reported separately?
- **Preservation**: Are terminal round artifacts indexed in `round_artifacts` with matching SHA-256 values, with amendments stored as successors rather than overwrites? This establishes internal consistency; tamper evidence requires an append-only or externally anchored store.
- **Consistency**: Does the profile-aware validator report no unresolved error before a bounded, pause, or completion claim?

## `fixed_test`

- Does `claim_card.json` describe one prespecified claim and sample with either one analysis or a finite frozen analysis family under a joint decision rule?
- For a frozen family, are member IDs, member methods or roles, the multiplicity or joint inference rule, and discordance/reporting rule fixed and complete?
- Did execution apply only the frozen family, including its prespecified gates, assumption, falsification, robustness, screening, or ranking rules, without outcome-informed changes to membership, methods, thresholds, subgroups, rules, or reporting?
- If the result motivated any addition or modification, was the run upgraded to `adaptive_search` before continuing, with the original result and exposure preserved?
- Is the report called a completed frozen analysis rather than a completed search?

## `adaptive_search`

- **Decision Contract**: Were eligibility, four population roles, comparison keys, estimands, ranking evidence, tie and inconclusive rules, evidence partitions, and applicable gates frozen before the outcomes they govern?
- **Prior exposure**: Does the audit cover overlapping analyses, parameter attempts, screens, data looks, selections, holdout use, and unknown gaps?
- **Ledger**: Does it retain every selection-influencing generation, modification, screen, retry, failure, retention, ranking, verification target, and promotion?
- **Typed candidates**: Does every candidate have a valid type and substantive-eligibility decision? Is `mechanism_alignment` decision-bearing only for mechanistic candidates, with justified `not_applicable` otherwise?
- **Families and comparability**: Do directly compared candidates share target, supported sample, estimand, evidence stage, and material data quality? Are incompatible or untransported results parallel or support limited?
- **Conditional gates**: If uncertainty can affect selection, did measurement-error sensitivity pass? If populations differ, did required transport pass? If screen and decision evidence differ, was their mapping and discordance rule followed?
- **Selection-path inference**: Does each decision family use a method covering the complete influential path, including adaptive additions and repeated looks, rather than nominal p-values from surviving candidates?
- **Decision**: Were substantive eligibility and applicable gates passed before ranking? Does the result allow `tie`, `inconclusive`, or `no_eligible_candidate` instead of forcing a smallest-p winner?
- **Bounded status**: If this stage ends, does its report preserve open work and avoid claims of inventory saturation or coverage completion?

## `coverage_search`

Complete every adaptive item, then check:

- **Inventory**: Is one active typed inventory version frozen, with substantive roles, support, distinctness, eligibility, and parent/duplicate history? Did outcome-motivated additions create a successor version?
- **Coverage**: Is each finite cell linked to an eligible candidate, supported data and sample, observable or test role, formulation, meaningful effect, sensitivity requirement, falsifier, family, and ledger entries?
- **Scientific versus scheduling state**: Did priority change only order? Are unrun, invalid, resource-blocked, and governance-blocked cells still open and present in the denominator and queue?
- **Saturation**: After the latest eligible addition, did the complementary, separately scoped candidate-forward and data-product-reverse audits find no new eligible nonduplicate entry? Was each conditionally declared third source completed, with starting basis, procedure, scope, shared context, additions, and unresolved gaps recorded?
- **Closure**: Is every eligible cell `tested_valid`, auditable noncyclic `covered_by`, or `not_testable_current_data`, with weak, null, failed, invalid, and unfavorable branches still visible? Are tested, equivalence-closed, not-testable, classified-closed, and open fractions reported separately?
- **Pause**: If limits ended work with open cells, does `pause_report.md` preserve the complete queue, blockers, versions, resource state, and exact resume point?

## Reporting Gate

`stage_status=completed_as_scoped` may close a fixed test, adaptive stage, or bounded coverage stage. It is not scientific search completion.

Use `search_status=complete_within_scope` and issue `final_report.md` only when the same coverage version has audited inventory saturation, complete coverage, an audited ledger and selection path, an applied Decision Contract with a terminal decision, an adequate prior-exposure audit, and a validator report with no errors.

A completed round, promoted candidate, favorable threshold, final deliverable, or exhausted resource envelope never establishes scientific completion. Schema `<=1.4` retains its legacy full-run gate.
