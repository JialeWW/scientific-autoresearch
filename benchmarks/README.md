# Benchmark Evidence Boundary

This directory is repository-maintenance infrastructure. It is not part of the installable `scientific-autoresearch/` skill and is never a required step in an ordinary scientific run.

Keep three evidence classes separate:

1. **Behavioral specifications** state expected routing and safeguards. The cases in `scientific-autoresearch/evals/` are specifications until isolated executions are saved and scored.
2. **Package and run-record consistency checks** test deterministic structure, schema, references, and recorded cross-artifact invariants. They do not establish numerical or scientific validity.
3. **Empirical validation** requires repeated end-to-end evaluations with known or defensible truth. Claims about false-promotion rates, error control, power, calibration, reproducibility, or cross-executor performance require results from this class.

`manifest.json` declares the current evaluation surfaces and their status. A suite with `execution_status: not_run` has no benchmark result. Freeze its task family, conditions, evaluation unit, primary metrics, repetition or precision rule, stopping rule, and interpretation rule before inspecting evaluation outcomes.

## Standardized scored records

`score.py` consumes JSON Lines produced by any client or external evaluation harness. It does not call a model or judge outputs. Each record must include:

```json
{
  "suite_id": "behavioral-profile-routing",
  "release": "0.2.6",
  "condition": "skill-v0.2.6",
  "case_id": "3",
  "replicate": 1,
  "agent": "recorded executor",
  "model": "recorded model",
  "runtime": "recorded runtime",
  "output_hash": "sha256:...",
  "record_type": "behavioral",
  "assertion_scores": [true, true, false],
  "critical_violations": 0
}
```

For trigger routing, use `record_type: trigger` with Boolean `expected_trigger` and `predicted_trigger`. Optional `tokens` and `duration_ms` may be recorded but are not interpreted as scientific validity.

Run the deterministic scorer self-test with:

```bash
python benchmarks/score.py --self-test
```

Raw outputs and traces belong in the ignored `eval-results/` directory or an external immutable store. Publish only a versioned result record after the frozen protocol has actually run; do not change `not_evaluated` to a stronger status because the specification files or structural self-tests exist.
