# Benchmark Evidence Boundary

This directory is repository-maintenance infrastructure, not part of an ordinary scientific run. Keep three states visible and separate:

1. `package_validation`: deterministic package or run-record structure checks;
2. `behavioral_evaluation`: isolated executions scored against frozen routing and safeguard cases;
3. `empirical_method_validation`: repeated end-to-end known-truth studies of error control, power, calibration, stopping, reproducibility, and record completeness.

A green package check does not imply either evaluation state passed. The current release remains `not_evaluated` until hash-bound records from a frozen protocol are actually scored.

## Protocol lifecycle

`manifest.json` is the frozen protocol registry, not an execution log. A `draft` suite may keep repetitions, seed, aggregation, interval, or pass rules unresolved and cannot be scored. A `frozen` suite must define them before outcomes. Public cases have `role=development`; they do not become sealed merely because their files are hashed.

The built-in scorer supports only `trigger` and `behavioral` records. Empirical operating-characteristic suites use an external, separately frozen harness because their scenario generation and scientific truth cannot be reduced to the behavioral record schema.

## Hash-bound records

`score.py` reads the manifest and case registry itself. The manifest binds the exact scorer SHA-256 as well as the case registries and evaluated packages. The scorer rejects record-supplied gold labels, unknown suites, conditions, releases, cases, record types, incomplete suite-condition or case-by-replicate matrices, reused execution identities or judgments, inconsistent package hashes, mismatched package/case/prompt/rubric hashes, unsupported interval rules, and missing or hash-mismatched evidence. Repository validation also checks that the scorer and current-release condition match their bound digests.

A version-2 trigger record contains:

```json
{
  "record_schema_version": "2.0.0",
  "manifest_sha256": "sha256:...",
  "suite_id": "trigger-routing",
  "condition_id": "skill-v0.2.7",
  "skill_release": "0.2.7",
  "skill_package_sha256": "sha256:...",
  "case_id": "trigger-001",
  "replicate": 1,
  "agent": "recorded executor",
  "model": "recorded model",
  "runtime": "recorded runtime",
  "execution_config_sha256": "sha256:...",
  "generation_seed": 1234,
  "seed_control_status": "controlled",
  "record_type": "trigger",
  "execution_identity_sha256": "sha256:...",
  "case_spec_sha256": "sha256:...",
  "prompt_sha256": "sha256:...",
  "evidence_path": "relative/path/to/raw-output.txt",
  "evidence_sha256": "sha256:...",
  "predicted_trigger": true
}
```

Use `generation_seed=null` with `seed_control_status=uncontrolled` or `not_applicable` when no controllable seed exists; do not invent one. `execution_config_sha256` binds the frozen harness and generation settings, and `execution_identity_sha256` binds the complete execution identity.

Behavioral records replace `predicted_trigger` with an exact assertion-ID-to-Boolean map and add `rubric_sha256`, judge identity and version, judge-prompt hash, scoring time, and a hash-bound judgment JSON. The judgment must bind the execution identity, raw evidence, case, rubric, judge prompt, final scores, judge metadata, and scoring time. Multi-reviewer judgments additionally record panel size, agreement, and adjudication; a single judge is permitted but remains visible as such.

Store raw outputs under an ignored evidence directory or stage immutable external evidence into a local read-only tree before scoring. The scorer never follows absolute paths, parent traversal, or symbolic links.

Run:

```bash
python benchmarks/score.py eval-results/records.jsonl \
  --manifest benchmarks/manifest.json \
  --evidence-root eval-results/evidence \
  --output eval-results/scored.json
```

Behavioral primary metrics weight cases equally: assertions are averaged within an execution, replicates within a case, then cases within a provenance stratum. The assertion-micro rate is diagnostic. Intervals use the frozen case-cluster bootstrap after within-case replication and quantify case-level variation under that rule; they do not separately estimate execution-level stochastic variance. Trigger balanced accuracy requires both positive and negative frozen cases.

Run deterministic scorer and unit tests with:

```bash
python benchmarks/score.py --self-test
python -m unittest discover -s benchmarks/tests -v
```

Do not publish a stronger result status because the protocol, self-tests, or package validator exists. Publish only the conditions, executors, models, runtimes, cases, repetitions, evidence, judges, and metrics that were actually scored.
