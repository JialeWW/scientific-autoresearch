# Benchmark Evidence Boundary

This directory is repository-maintenance infrastructure, not part of an ordinary scientific run. It separates:

1. package and run-record consistency checks;
2. behavioral evaluation on isolated executions;
3. empirical operating-characteristic studies under known or defensible truth.

Passing deterministic checks does not establish behavioral or empirical validity. The v0.2.8 result remains `not_evaluated`: no real comparison block, executor, model, runtime, configuration, schedule, or judge has been frozen or run.

## Protocol 2.1 comparison unit

Protocol 2.1 is comparison-block-first. The paired identity is:

```text
comparison_block_id + case_id + replicate
```

`condition` is the treatment varied inside that pair. A frozen block binds the complete condition set and contrasts, executor identity, one shared execution configuration, seed-control status and schedule, balanced within-pair order schedule, isolated-session policy, retry policy, and a routing-extraction or behavioral-judge protocol. The scorer will not compute a condition delta unless every scheduled condition has a selected score-bearing attempt for every case and replicate.

The repository manifest freezes the cases, conditions, estimands, aggregation, interval, tie, missing-run, failure, and retry rules that can be defined before compute-specific choices exist. Its built-in suites use `protocol_status=awaiting_execution_freeze` and contain no fake placeholder block. Before a real run, create a successor immutable execution manifest with actual hash-bound artifacts and `protocol_status=frozen`.

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

- shared execution configuration: harness identity plus an artifact digest, immutable version, or runner attestation; generation settings; tool policy; context policy; timeout; and isolated-session requirement;
- seed schedule: every `case_id + replicate`, with status `enforced`, `requested_not_guaranteed`, or `unavailable`;
- order schedule: a seeded balanced rotation for every pair, verified from its generation method and seed;
- trigger-routing protocol: frozen extractor identity and decision rule;
- behavioral judge protocol: judge identity/version, prompt artifact and hash, rubric version, blinding, adjudication policy, and judgment repetition design.

The execution configuration has a closed shared schema and recursively rejects condition-keyed branches. Optional `redactions` are annotation-only: they must be a unique list of nonempty strings, cannot contain a condition identifier, and must never affect execution. Skill packages are bound separately by the manifest, so condition-specific temperature, tools, context, or timeout cannot hide inside the config. The scorer binds the package digest declared by the runner to the frozen manifest; it cannot reconstruct a historical package from that declaration alone. Preserve or independently attest the evaluated package outside the score file. When seed control is unavailable, the pair and interleaved order remain frozen, but the report does not claim exact random-stream pairing.

Each condition starts in a clean session. The first attempts for one pair must follow the frozen order inside the declared adjacent-time window. If a retry becomes the selected score-bearing attempt, the selected attempts across conditions must also remain inside that same window; a delayed retry invalidates the block rather than silently breaking comparability. A session identity, raw output or failure log, and evidence hash are unique to every attempt.

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
  "execution_config_schema_version": "1.0.0",
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

The scorer follows neither absolute paths nor parent traversal or symbolic links. It verifies the scorer, manifest, cases, declared package bindings, config, schedules, routing or judge protocol, prompts, raw attempt evidence, and judgments before scoring. It rejects non-finite numeric values and malformed case or assertion identifiers. These hashes establish internal binding, not that a declared extractor, judge, package, or service actually produced the artifact; the runner or evaluation custodian must preserve and attest that execution boundary.

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

Public cases are development cases. Their first real run can support only `development_suite_evaluated`. A sealed suite requires a pre-run case/rubric commitment, custodian and access policy, retirement/rotation policy, and frozen scorer and condition hashes. Protocol 2.1 records this governance requirement but intentionally refuses sealed execution until a successor scorer implements and validates the commitment schema. Exposure during tuning converts a future sealed suite to development evidence.

A scorer- or manifest-level defect makes the submitted evaluation unscorable. A record, retry, order, session, judgment, or output-capture deviation that can be assigned to one execution block invalidates that entire block while leaving unrelated complete blocks reportable. A malformed frozen config, schedule, or protocol artifact is rejected when the manifest is loaded, before block scoring begins. Preserve every defect and attempt with the reason and rerun under a new protocol or scorer patch version; do not repair only favorable or unfavorable records.

## Running deterministic checks

The following commands test scorer logic only; they do not run the behavioral benchmark:

```bash
python benchmarks/score.py --self-test
python -m unittest discover -s benchmarks/tests -v
```

After a separately authorized execution has produced a frozen records file and evidence tree:

```bash
python benchmarks/score.py eval-results/records.jsonl \
  --manifest eval-results/frozen-manifest.json \
  --evidence-root eval-results/evidence \
  --output eval-results/scored.json
```

Do not upgrade the result state because a protocol, fixture, package validator, or scorer exists. Publish only the blocks, conditions, cases, attempts, executors, models, runtimes, configurations, seeds, judges, and uncertainty levels actually evaluated.
