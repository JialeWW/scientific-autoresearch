# Benchmark Evidence Boundary

This directory is repository-maintenance infrastructure, not part of an ordinary scientific run. It separates:

1. package and run-record consistency checks;
2. behavioral evaluation on isolated executions;
3. empirical operating-characteristic studies under known or defensible truth.

Passing deterministic checks does not establish behavioral or empirical validity. The frozen v0.2.8 result remains `not_evaluated`. Protocol/scorer 2.1.2 repairs the execution boundary and replays a non-development canary shakedown, but no frozen development suite or scored development case has been run. Skill v0.3.2 is a later installable release, has no result in this frozen protocol line, and is also `not_evaluated`.

## Immutable protocol lines

`manifest.json`, `score.py`, and `results/v0.2.8.json` remain the byte-frozen 2.1.0 chain. The reviewed 2.1.1 files are retained byte-for-byte as a superseded, unevaluated no-go snapshot. Protocol/scorer 2.1.2 is the benchmark-only successor whose release under test remains Skill 0.2.8. It does not evaluate or describe v0.3.x. `protocol-index.json` resolves every result or execution through explicit artifact hashes; it never infers a historical manifest from the current Skill version.

Any scorer, protocol, or result-schema correction requires a new patch version. Do not overwrite a frozen scorer, manifest, result, execution manifest, or execution directory.

## v0.3.x development specifications

`development-cases/v0.3.0-routing-efficiency.json` is an unfrozen, unscored development specification for a future successor protocol. It targets active continuation after weak results, premature scientific stopping, lightweight omission review, false workflow and adaptivity escalation, unnecessary formal-audit escalation, false coverage triggers, correct explicit scoped-completion routing, delay and artifact count before the first scientific result, governance overhead, continuous execution, bounded qualification, family-local release, infrastructure reuse under result blinding, engineering/scientific separation, scale sensitivity, systematics, and selection-path completeness. Assertions judge observable behavior; they do not require an ordinary Agent response to recite profile, record-mode, contract-type, or completion-status labels. Draft event definitions and provisional acceptance targets make future collection requirements explicit, while the end-to-end surrogate checks local family release, join repair, equivalent worker changes, nonselection QA exposure, and later selection correction together. The case definitions and targets are not a frozen protocol or benchmark result. A future frozen comparison should include v0.2.1, v0.2.8, v0.3.0, v0.3.1, and v0.3.2 under the same cases and execution conditions; no such comparison is reported here.

`development-runs/v0.3.0-active-continuation-probe.md` and `v0.3.0-scoped-coverage-probe.md` preserve two isolated qualitative Agent responses. The first specified that it would continue through remaining candidates and a falsifier after a weak result without creating formal artifacts. The second preserved inventory, coverage-cell, dual-audit, selection-path and open-queue semantics while declining to fabricate a missing scope or require a machine schema. The runner, model, sampling, timing and judge protocols were not frozen, and no scientific computation or infrastructure failure was executed. These are development diagnostics only: they do not change `not_evaluated`, establish a release comparison or support superiority over v0.2.1.

`development-cases/v0.3.1-lightweight-runtime.json` remains the historical unfrozen, unscored specification for the reduced runtime surface. `development-cases/v0.3.2-boundary-corrections.json` adds current unscored cases for trigger scope, authorization-bounded autonomy, coherent prespecification, costly or irreversible work, design-appropriate randomization, complete compact logging, dependence and leakage, required project validation, and resource-limited stopping. These definitions are not observations or a behavioral result.

The historical files under `scientific-autoresearch/evals/` remain at their original paths only because the immutable v0.2.8 protocol manifests bind those exact paths and hashes. They are legacy benchmark case sources, not current v0.3.2 runtime guidance. A successor protocol may relocate its own copied case source, but must not rewrite the frozen 2.1.2 manifests or imply that the old cases describe v0.3.2.

## Protocol 2.1.2 comparison unit

Protocol 2.1.2 remains comparison-block-first. The paired identity is:

```text
comparison_block_id + case_id + replicate
```

`condition` is the treatment varied inside that pair. A frozen block binds the complete condition set and contrasts, executor identity, one shared execution configuration, seed-control status and schedule, balanced within-pair order schedule, isolated-session policy, retry policy, and a routing-extraction or behavioral-judge protocol. The scorer will not compute a condition delta unless every scheduled condition has a selected score-bearing attempt for every case and replicate.

The development template freezes the cases, all four required conditions, every planned contrast, repetitions, estimands, aggregation, interval, tie, missing-run, failure, retry, interpretation, and governance rules before execution. The separate shakedown template freezes only the non-development canary design. A 2.1.2 execution manifest must bind its parent template by contained path, raw SHA-256, and schema version, reproduce the parent's canonical immutable projection, and match the projection digest built into the scorer. It may add execution identity, time, runtime, schedules, routing or judge artifacts, and block identity; it cannot select a smaller condition family or change the scientific comparison design.

Top-level governance is semantic, not decorative. `protocol_id`, `protocol_scope`, `release_under_test`, `benchmark_status`, the complete evidence-state vocabulary, and all three policy objects are exact purpose-specific constants. A mutually forged template and execution still fail unless their canonical projection matches the scorer's frozen anchor.

## Pre-outcome estimands

Primary estimands are frozen before execution:

- trigger routing: paired balanced-accuracy difference;
- behavioral conformance: paired case-macro score difference;
- behavioral safeguards: paired critical-violation risk difference.

The aggregation path is:

```text
case × replicate paired difference
→ mean across replicates within case
→ macro summary across cases
→ case-cluster bootstrap
```

Trigger intervals resample positive and negative cases separately. Win/loss/tie is decided on case means under the frozen tolerance. Critical violations are binary per selected execution and include discordant-pair counts. Absolute condition scores remain visible, but summaries from different blocks are never pooled or subtracted.

Case variation is estimable from the frozen case bootstrap only when the design includes at least two behavioral cases, or at least two cases in each truth stratum for trigger balanced accuracy. Execution stochasticity is estimated only when a case has repeated paired executions. A single final judgment cannot identify judge uncertainty; the result states `not_estimable_under_current_design` rather than treating it as zero.

## Frozen execution artifacts

A real comparison block binds JSON artifacts by contained relative path, schema version, and SHA-256:

- shared execution configuration: harness identity plus either a recomputable artifact or a hash-bound attestation; generation settings; tool policy; context policy; timeout; and isolated-session requirement;
- seed schedule: every `case_id + replicate`, with status `enforced`, `requested_not_guaranteed`, or `unavailable`;
- order schedule: a seeded balanced rotation for every pair, verified from its generation method and seed;
- trigger-routing protocol: frozen extractor identity and decision rule;
- behavioral judge protocol: judge identity/version, prompt artifact and hash, rubric version, blinding, adjudication policy, and judgment repetition design.

The execution configuration has a closed shared schema and recursively rejects recognized condition-keyed branches. Optional `redactions` are annotation-only: they must be a unique list of nonempty strings, cannot contain a condition identifier, and must never affect execution. Skill packages are bound separately by the manifest. The scorer binds the complete shared execution-config artifact, but arbitrary nested values and free-text policies remain subject to semantic review or runner attestation; artifact verification does not prove semantic uniformity or actual runtime use.

Protocol 2.1.2 separates material assurance from run validity and evidence status:

- `artifact_verified`: the scorer reads the contained artifact and recomputes its bound digest. Package ZIPs are recomputed with `scientific-autoresearch-behavior-package-v1`; harness files or bundles are checked by raw SHA-256.
- `attested`: the scorer verifies a closed, hash-bound attestation artifact but does not claim to have inspected the subject bytes.
- `not_applicable`: allowed only for the no-skill package.

The block level is the minimum across the harness and all non-null packages; the result level is the minimum across frozen blocks. The scorer leaves `runtime_use_assurance=unreported` because material verification alone cannot prove that a process used those bytes. A separately hash-bound execution receipt may record `runner_attested`, but it remains an attestation rather than independent or cryptographic assurance. Artifact failure is fatal and never silently downgraded to attested. When seed control is unavailable, the pair and interleaved order remain frozen, but the report does not claim exact random-stream pairing.

Each condition starts in a clean session. The first attempts for one pair must follow the frozen order inside the declared adjacent-time window. If a retry becomes the selected score-bearing attempt, the selected attempts across conditions must also remain inside that same window; a delayed retry invalidates the block rather than silently breaking comparability. Each attempt has a unique session and evidence path, and its raw output or failure log is hash-bound.

The complete evidence tree is closed: every regular file must be referenced by the submitted records, every reference must resolve to a file with the recorded digest, and symbolic links, special files, missing files, and orphan files are rejected. The canonical tree digest is bound by the result, execution receipt, and protocol index.

## Attempts, failures, and retries

All attempts are retained. `run_status` distinguishes:

```text
completed
agent_timeout
agent_error
policy_refusal
invalid_output
harness_error
provider_error
cancelled_before_execution
```

Agent-side failures are outcomes of the tested condition. They receive zero credit and cannot be retried. A complete refusal response that is intended for evaluation should be recorded as `completed` and judged normally; `policy_refusal` means no scoreable response was produced.

Infrastructure and scheduling failures may be retried only under the frozen limit. Attempts are contiguous, retain the same pair/config/seed request, and a retry cannot start before the preceding attempt has completed. The first non-retry-eligible non-infrastructure outcome is selected; an infrastructure status remains unresolved even when that particular status is not retry-enabled. A retry after an Agent outcome, an exceeded retry limit, a selected-attempt window violation, a reused session, or overwritten evidence invalidates the affected block while leaving unrelated complete blocks reportable. If infrastructure retries end without a score-bearing outcome, the cell remains unresolved and paired deltas are suppressed. No attempt record at all is reported separately as missing. Retry counts are computed from all retained attempts, not only selected outcomes.

## Record outline

A protocol-2.1 record includes:

```json
{
  "record_schema_version": "2.1.0",
  "manifest_sha256": "sha256:...",
  "suite_id": "trigger-routing",
  "comparison_block_id": "...",
  "run_batch_id": "...",
  "condition_id": "skill-v0.2.8",
  "case_id": "trigger-001",
  "replicate": 1,
  "attempt": 1,
  "agent": "frozen identity",
  "model": "frozen identity",
  "runtime": "frozen identity",
  "execution_config_path": "relative/path.json",
  "execution_config_schema_version": "1.1.0",
  "execution_config_sha256": "sha256:...",
  "generation_seed": 1234,
  "seed_control_status": "enforced",
  "run_status": "completed",
  "run_order_index": 1,
  "started_at": "...",
  "completed_at": "...",
  "session_identity_sha256": "sha256:...",
  "execution_identity_sha256": "sha256:...",
  "evidence_path": "relative/raw-output.txt",
  "evidence_sha256": "sha256:..."
}
```

Completed trigger records add `predicted_trigger`, routing-protocol and extractor bindings, scoring time, and a structured hash-bound routing judgment; truth comes only from the frozen case registry. Completed behavioral records add the exact assertion map, rubric hash, judge-protocol binding, scoring time, and a hash-bound judgment. Attempt records use a closed schema, so unbound execution settings cannot be added per condition and silently ignored. The current record schema supports one final adjudicated judgment per output and therefore reports judge uncertainty as not estimable. Noncompleted attempts must not carry a synthetic prediction or assertion score.

The scorer follows neither absolute paths nor parent traversal or symbolic links. It verifies the scorer, manifest, cases, package or attestation artifacts, config, schedules, routing or judge protocol, prompts, raw attempt evidence, and judgments before scoring. It rejects non-finite numeric values and malformed case or assertion identifiers. Material verification and runtime-use assurance remain separate rather than projecting one into the other.

## Result states

Data completeness and evidence level remain separate:

```text
scoring_status:
  not_evaluated | complete | comparison_incomplete | invalid | invalidated

evidence_status:
  not_evaluated
  development_suite_evaluated
  sealed_suite_baseline_established
  prospective_release_gate_evaluated
  empirical_method_evaluated
```

Each block carries its own evidence status. The top-level `evidence_status` is populated only when completed blocks have one common level; otherwise it is null with `evidence_status_scope=block_specific` and the distinct levels remain in `evidence_statuses`. No highest-level status is projected over lower-level blocks.

Public cases are development cases. Their first real run can support only `development_suite_evaluated`. A sealed suite requires a pre-run case/rubric commitment, custodian and access policy, retirement/rotation policy, and frozen scorer and condition hashes. Exposure during tuning converts a future sealed suite to development evidence.

The committed `execution-manifest-shakedown-v2.1.2.json` inherits `manifest-shakedown-v2.1.2.json` and uses only `fixtures/shakedown-v2.1.2/`. Its two frozen blocks exercise four package conditions, balanced order, isolated sessions, one infrastructure retry, one Agent failure, evidence and judgment binding, and result replay. Shakedown blocks require `execution_purpose=execution_shakedown`, case role `shakedown`, and `evidence_status_on_complete=not_evaluated`; the scorer suppresses condition summaries and paired deltas even when the pipeline completes.

A scorer- or manifest-level defect makes the submitted evaluation unscorable. A record, retry, order, session, judgment, or output-capture deviation that can be assigned to one execution block invalidates that entire block while leaving unrelated complete blocks reportable. This includes a claimed file that is missing, content-mismatched, reused, linked, special, or otherwise unreadable. An orphan file, unsafe evidence root, unassignable special entry, unknown suite/block, or globally unparseable schema remains submission-fatal. A malformed frozen config, schedule, or protocol artifact is rejected when the manifest is loaded, before block scoring begins. Preserve every defect and attempt with the reason and rerun under a new protocol or scorer patch version; do not repair only favorable or unfavorable records.

## Running deterministic checks

The following commands test scorer logic only; they do not run the behavioral benchmark:

```bash
python benchmarks/score.py --self-test
python benchmarks/score-v2.1.1.py --self-test
python benchmarks/score-v2.1.2.py --self-test
python -m unittest discover -s benchmarks/tests -v
python benchmarks/shakedown-harness.py --output-root /tmp/scientific-autoresearch-shakedown
python benchmarks/shakedown-harness-v2.1.2.py --output-root /tmp/scientific-autoresearch-shakedown-2.1.2
```

After a separately authorized execution has produced a frozen records file and evidence tree:

```bash
python benchmarks/score-v2.1.2.py eval-results/records.jsonl \
  --manifest eval-results/frozen-manifest.json \
  --evidence-root eval-results/evidence \
  --output eval-results/scored.json
```

Do not upgrade the result state because a protocol, fixture, package validator, or scorer exists. Publish only the blocks, conditions, cases, attempts, executors, models, runtimes, configurations, seeds, judges, and uncertainty levels actually evaluated.
