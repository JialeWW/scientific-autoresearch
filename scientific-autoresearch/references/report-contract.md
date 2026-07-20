# Report and Artifact Contract

Apply the full contract to executed rounds. In `design_only` mode, return advice or a single design report unless the user requests more artifacts.

## 1. Canonical Immutable Layout

Use an equivalent project convention if one already exists; otherwise use:

```text
runs/<run_id>/
  run_manifest.json
  candidate_registry.csv
  rounds/
    round_000/
      report.md
      inventory.json
      summary.csv
      diagnostics.<csv|parquet|jsonl>   # conditional
      figures/                          # conditional
      reproduce_commands.txt
      round_gate.md
  final_report.md
```

Never overwrite or silently amend a closed round. Write a new round or amendment with a parent reference.

## 2. Run Manifest

Record at least:

```text
run_id
question
execution_mode
created_at
output_root
governance_status
authorized_inputs
authorized_actions
prohibited_actions
round_budget
candidate_budget
mutation_budget
data_look_budget
compute_and_cost_budget
success_boundary
futility_boundary
inconclusive_boundary
safety_boundary
verification_policy
```

## 3. Round Report

Include:

1. **Question and claim card**: claim ID, type, mechanism, estimand, expected direction, minimum meaningful effect, supported sample, and frozen or exploratory status.
2. **Inputs and lineage**: data, code, model, environment, versions, hashes when allowed, units, transformations, and parent round.
3. **Governance**: permissions, restrictions, privacy controls, resource limits, and required oversight.
4. **Method**: exact sample rules, formula or model, statistic, seed set, uncertainty plan, search-ledger entry, and planned falsifier.
5. **Result**: effect, uncertainty, sensitivity, sample size, diagnostic paths, and practical or physical magnitude.
6. **Falsification**: alternative explanation, expected outcomes, observed result, and status consequence.
7. **Search and evidence audit**: all related attempts, data looks, multiplicity handling, and verification status.
8. **Interpretation**: what is measured or supported, what is not proven, main systematics, literature context when needed, and limitations.
9. **Decision**: canonical statuses, next action, reason, remaining budget, and next frozen question if continuing.

## 4. Inventory

Record actual values, not defaults:

```json
{
  "run_id": "",
  "round_id": "",
  "parent_round_id": null,
  "claim_ids": [],
  "inputs": [],
  "code_state": {},
  "environment": {},
  "parameters": {},
  "seed_set": [],
  "sample_counts": {},
  "search_ledger_entries": [],
  "uncertainty_components": [],
  "governance_status": "",
  "mechanism_status": "",
  "formulation_status": "",
  "evidence_role": "",
  "verification_status": "",
  "next_action": "",
  "outputs": {}
}
```

## 5. Summary and Diagnostics

`summary.csv` must contain every tested formulation, including failed and invalid branches. Include claim ID, formulation ID, role, supported sample, effect, uncertainty, sensitivity, search status, canonical statuses, and main caveat.

Create diagnostics only when they add reconstruction or audit value. Use CSV, Parquet, JSONL, or another suitable machine-readable format. For large or sensitive data, use aggregate, sampled, or de-identified diagnostics rather than copying raw records.

Never include direct identifiers, unnecessary quasi-identifiers, credentials, restricted paths, or secrets. Record the transformation from raw to diagnostic data without exposing protected values.

## 6. Reproduction Record

Record exact commands or equivalent steps, code commit and dirty state, environment or dependency lock, hardware or numerical precision when relevant, seed set, and expected output paths.

Redact tokens, passwords, signed links, private endpoints, personal identifiers, and confidential filesystem details. Use placeholders and document how an authorized user supplies them securely.

## 7. Final Report

Build the final report only from closed rounds. List:

- strongest supported or provisionally supported candidate;
- null, inconclusive, artifact, invalid, weakened, and rejected results;
- active or data-limited candidates;
- verification and replication status;
- complete search scope and remaining multiplicity concerns;
- dominant uncertainty and systematics;
- governance or resource constraints;
- what remains untested;
- the exact data, approval, assumption, or resource required to continue.

Complete the Trial Completion Gate in `references/round-gate-checklist.md`.
