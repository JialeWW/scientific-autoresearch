# Report and Artifact Contract

This reference applies to `machine_audited` mode and validator diagnosis. Under `conceptual_record`, keep the same scientific content in a compact working report or existing project records without creating prescribed filenames. From the first selection-influencing outcome, adaptive work still needs a contemporaneous append-only or versioned record; if existing records cannot provide one reliably, enter `machine_audited` before that outcome. A conceptual coverage stage may end with a bounded or pause report, but `complete_within_scope` requires a validated machine-audited record whose adaptive history was preserved contemporaneously. Retrospective migration cannot establish that omitted attempts were recorded. The validator, not prose copied from this page, is authoritative for schema `1.5.3` fields.

`design_only` creates no run directory or artifacts by default. `audit_only` inspects existing material and may validate an existing run read-only; it does not initialize an execution run. When machine-audited execution is requested and authorized, initialize an empty path with:

```text
python scientific-autoresearch/scripts/validate_run.py --init RUN_DIR --profile PROFILE
```

where `PROFILE` is `fixed_test`, `adaptive_search`, or `coverage_search`. Initialization refuses to overwrite a file or nonempty directory. It provides structure, not scientific content, authorization, or a passing run; required placeholders must be resolved and the validator rerun.

## Profile Artifact Sets

All paths below are relative to the run directory. Conditional files are created only when needed.

| Artifact | `fixed_test` | `adaptive_search` | `coverage_search` |
|---|:---:|:---:|:---:|
| `run_manifest.json` | required | required | required |
| `claim_card.json` | required | — | — |
| `decision_contract.json` | — | required | required |
| `prior_exposure_audit.json` | — | required | required |
| `data_versions.json` | required | required | required |
| hash-bound domain-adapter record | conditional | conditional | conditional |
| hash-bound project preflight report | conditional | conditional | conditional |
| versioned `candidate_inventory_vNNN.csv` | — | — | required |
| versioned `coverage_matrix_vNNN.csv` | — | — | required |
| versioned `saturation_audit_vNNN.json` | — | — | required |
| `search_ledger.jsonl` | — | required | required |
| `selection_families.json` | — | required | required |
| `candidate_registry.csv` | — | required | required |
| `status_transitions.jsonl` | — | required | required |
| `execution_queue.csv` | — | — | required |
| `rounds/round_NNN/report.md` | required | required | required |
| `rounds/round_NNN/reproduce_commands.txt` | required | required | required |
| `rounds/round_NNN/inventory.json` | — | — | required |
| `rounds/round_NNN/summary.csv` | — | — | required |
| `rounds/round_NNN/round_gate.md` | — | — | required |
| round diagnostics or figures | conditional | conditional | conditional |
| `pause_report.md` | — | optional bounded stop | conditional with open coverage |
| `final_report.md` | — | — | only `complete_within_scope` |
| `consistency_report.json` | required | required | required |

The schema-1.5.x coverage initializer uses `inventories/candidate_inventory_vNNN.csv`. `mechanism_inventory_vNNN.csv` remains a legacy-compatible input, but do not maintain both as competing active inventories.

Schema `<=1.4` remains readable with its legacy full-run behavior. Do not change only `artifact_schema_version`; migrate profile metadata and artifacts or leave the run legacy.

## Shared Manifest and Versioned Rounds

Every schema-1.5.x run manifest records at least run identity, question, scientific scope, `artifact_schema_version`, `research_profile`, `stage_status`, ordered `profile_history`, execution mode, governance status, data-version-set ID, and `round_artifacts`. Schema 1.5.2 additionally records ordered `skill_provenance`; each entry contains the skill name, release version, deterministic behavior-package SHA-256, capture time, and a source revision when locally available. The digest covers `SKILL.md`, bundled Markdown references, Python scripts, and JSON evaluation specifications. Run outputs are excluded so a run nested under the skill root cannot change its own skill identity; symbolic links on the hashed surface are rejected. The initializer creates the first entry automatically. Before authorized execution or resume, run `scripts/validate_run.py --record-skill-provenance RUN_DIR`; it makes no change when the identity is unchanged and appends rather than overwrites when it changed. Ordinary validation and `audit_only` remain read-only. Adaptive and coverage profiles add their contract and audit versions; coverage adds its inventory and search fields.

Schema 1.5.3 additionally records an explicit domain-adapter assessment and the analysis, independence, dependence-handling, and partition or resampling units in the frozen claim or Decision Contract. If a domain adapter is required, `run_manifest.json#domain_adapter_ref` binds an internal JSON record by path and SHA-256. That record may contain a project data contract, a hash-bound preflight report, and a proportionate semantic review. The generic validator checks binding and cross-record consistency; it does not infer domain truth.

The package digest identifies the installed skill content; it does not prove that the instructions were followed or externally timestamp the run. A newer validator may read a run recorded under an older skill identity. Such a mismatch is a warning for read-only audit and must be recorded before new authorized outcomes are produced. Schema 1.5.0 and 1.5.1 runs remain readable without `skill_provenance`; do not fabricate retrospective identity for an old run.

Profiles may only upgrade:

```text
fixed_test -> adaptive_search -> coverage_search
```

Append the transition and preserve prior exposure, weak results, failures, selections, and earlier artifacts. Never reinitialize or downgrade to erase history.

For an existing schema-1.5.2-or-later machine-audited execution run, first record the current skill identity, validate the current profile, then create the upgrade evidence without overwriting it:

```text
python scientific-autoresearch/scripts/validate_run.py \
  --record-skill-provenance RUN_DIR
```

```text
python scientific-autoresearch/scripts/validate_run.py \
  --snapshot-upgrade RUN_DIR --to-profile TARGET_PROFILE
```

The helper copies the prior manifest, required profile artifacts, and every indexed round report and reproduction record into a new internal snapshot, verifies their hashes, and returns the exact next `profile_history` entry. It refuses an invalid source, downgrade, unsafe or symbolic-link path, or existing snapshot target. Review the copy, add the target profile's new artifacts, and append the returned entry; the helper deliberately does not rewrite the manifest or perform the scientific migration. Each upgrade entry requires strictly increasing offset-aware time plus `preservation_snapshot_path` and `preservation_snapshot_sha256`. The snapshot lists each prior artifact's logical path, copied path, and digest. Preservation booleans alone do not establish history.

Each `round_artifacts` entry requires `round_id`, `status`, `report_path`, and `reproduce_path`. A `completed` entry additionally requires `sealed_at`, `report_sha256`, and `reproduce_sha256`. Compute hashes after closing the round. A later validation must reconcile the files with the recorded hashes. Do not overwrite or silently amend an indexed artifact; add an amendment or successor round and preserve lineage. This is an internal consistency check, not proof against coordinated rewriting of both files and manifest; use an append-only or externally anchored store when tamper evidence is required.

Top-level registries are append-only or versioned. If a frozen contract, family, inventory, coverage cell, data record, or scientific meaning changes, create a successor version and record the transition.

## `fixed_test`: Compact Claim and Result

`claim_card.json` is the sole scientific contract for a true frozen analysis. The initialized schema includes the required fields; scientifically, it freezes:

- claim, target and analysis populations, supported sample, estimand, and minimum meaningful effect;
- `analysis_scope=single_test` or `frozen_family`; for a family, stable member IDs, each member's prespecified role or method, a multiplicity or joint inference rule, and one joint decision rule;
- data-version IDs, exclusions and transformations, parameters, seed policy when stochastic, prespecified checks and falsifier, specification timing, and prior exposure to overlapping evidence;
- result status, effect and uncertainty summaries, main caveat, and whether the test completed as scoped.

The round report states the actual inputs, methods, assumptions, every member needed to reconstruct a joint decision, effects in meaningful units, uncertainty, falsification outcomes, result status, limitations, and reproduction recipe. A prespecified check remains inside the frozen family. Preserve null, weak, invalid, failed, or unfavorable outcomes. `stage_status=completed_as_scoped` closes the bounded analysis, not a search.

For `analysis_scope=frozen_family`, `analysis_family` records `multiplicity_or_joint_inference_rule`, `reporting_rule`, and at least two uniquely identified `members`. Each member records its role, claim or estimand, analysis or test, result status, effect summary, and uncertainty summary. Schema 1.5.0 fixed-test records without `analysis_scope` remain valid as single analyses; frozen families require schema 1.5.1 or later.

If an inspected outcome motivates another candidate, formulation, threshold, sample, statistic, model, or ranking, upgrade before continuing. Preserve the fixed-test record as prior exposure; do not rewrite it as adaptive discovery or independent confirmation.

## `adaptive_search`: Complete Adaptive Path

Before adaptive outcome access, freeze the Decision Contract, bounded prior-exposure audit, selection families, and data versions. Bound the audit by declared projects or repositories, sources, overlap unit, date range or effort budget, and completion rule. Append to the ledger every generation, modification, screen, data look, retry, failure, retention, ranking, verification-targeting, or promotion step that can influence the decision.

The typed `candidate_registry.csv` declares `candidate_type`, substantive eligibility, selection-family identity and version, comparison key, comparability, specification timing, prior-exposure and evidence stages, verification, effects, uncertainty, supporting ledger entries, decision status, and reason. `mechanism_alignment` is decision-bearing only for `candidate_type=mechanism`; nonmechanistic candidates use justified `not_applicable` and still pass the general substantive-eligibility rule.

`selection_families.json` separates incompatible targets, supported samples, estimands, evidence stages, or material data-quality regimes. Version families and retain history. Each family records the complete influential ledger path and its domain-appropriate inference method. Do not rank parallel or support-limited candidates against a direct decision family.

Record conditional policies only when a pathway exists:

- `measurement_error_relevant=true` and a passing sensitivity result when uncertainty can affect support or selection;
- transportability when populations materially differ;
- screen-to-decision mapping when screening and final evidence differ;
- selection-path or multiplicity inference whenever adaptive or repeated selection occurs.

The final round may serve as the bounded stage report, or a separate `pause_report.md` may be used. It must state what ran, what remains open, the Decision Contract outcome so far, prior exposure, applicable gate results, ledger/family versions, failures and weak results, limitations, and exact continuation point. It must not claim saturation or coverage completion.

## `coverage_search`: Inventory, Coverage, and Saturation

In addition to every adaptive artifact, keep one active versioned typed inventory and matching coverage matrix. Candidate types are `mechanism`, `model`, `feature`, `simulation`, `design`, or justified `other`. Each inventory entry records its substantive role, distinctness, supported regimes and data, expected signature, testability, support, timing, status, and duplicate/parent lineage. A mechanistic inventory additionally records its pathway and mechanism interpretation.

Each coverage cell freezes the candidate, observable or test role, formulation, data and supported sample, parameter or scale domain, comparator, expected signature, meaningful effect, sensitivity requirement, falsifier, selection family, timing, evidence stage, execution tier, coverage/execution/result/verification status, and ledger links. Every candidate uses `substantive_eligibility`; only mechanistic candidates use `mechanism_alignment`. Apply measurement-error sensitivity only when relevant.

For schema 1.5.3, a `covered_by` closure also records the target cell, equivalence type and scope, assumptions, evidence, and review status. Equivalence chains must be noncyclic and may close only the declared scope. Report separately the counts and fractions that are `tested_valid`, equivalence-closed, `not_testable_current_data`, classified closed in total, and still open; do not present classified closure as if every cell received a direct test.

The saturation audit records the complementary, separately scoped candidate-forward and data-product-reverse audits after the latest eligible addition, plus any separately declared third source that is applicable. An eligible addition creates a successor inventory version and resets the affected saturation audit.

`execution_queue.csv` contains every open eligible cell exactly once when work pauses: execution tier, dependencies, priority, resource estimate, authorization fit, blocker, and next admissible action. Priority changes order only; no unrun cell is marked covered.

Issue `pause_report.md` when user, resource, governance, or other limits end execution with open cells. Include the active version, saturation state, closed/open/invalid/blocked counts, full queue, ledger/family versions, resource use, blocker, and resume requirements. This can be the final deliverable for the authorization window but is not scientific completion.

Issue `final_report.md` only when the validator accepts `search_status=complete_within_scope`. Report the frozen decision outcome, including ties, inconclusive or no eligible candidate; summarize counts and conclusions for weak, null, invalid, failed, support-limited, parallel, needs-data, and blocked classes; link the complete registry and ledger; and state selection-path inference, prior exposure, evidence stage, dominant uncertainties, scope boundaries, and what new data or assumptions could extend the search.

## Round Reports and Reproduction

Use a profile-proportional report:

1. identity, profile, stage, round lineage, governance, and data/code versions;
2. frozen question, claim or decision, supported sample, estimand, meaningful effect, and falsifier;
3. exact method, parameters, transformations, seeds or realizations, uncertainty, and applicable conditional gates;
4. effect, uncertainty, diagnostics, execution and result statuses, weak/failed branches, and caveats;
5. for adaptive work, selection changes, family and ledger links, comparability, prior exposure, evidence stage, and current decision;
6. for coverage work, inventory/coverage changes, saturation evidence, open queue, and closure or pause state;
7. reproduction steps and consistency-validator outcome.

The reproduction record gives exact secret-free commands or equivalent steps, code state, environment or dependency lock, hardware/precision when material, actual seeds, expected outputs, and tolerances. Report metadata consistency separately from numerical reproduction. Matching SHA-256 values demonstrate byte identity only for the checked files under matched conditions; they do not repair an incomplete ledger or invalid scientific design.

Before authorized resume, record the current skill identity for schema 1.5.2 or later. Before a bounded, pause, or completion report, run the read-only consistency check:

```text
python scientific-autoresearch/scripts/validate_run.py RUN_DIR --output RUN_DIR/consistency_report.json
```

Classify validator errors by what they establish. Schema inconsistency blocks an audited claim; numerical mismatch challenges computational reproduction. Neither finding should be silently converted into the other.
