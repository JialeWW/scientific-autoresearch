# Domain Adapter and Data-Contract Interface

Use this reference only when scientific validity depends on domain semantics that the generic workflow cannot infer, such as independent units, repeated or nested observations, identifier reconciliation, joins, measurement tolerances, admissible estimands, or specialized falsification rules. Do not create an adapter for a simple analysis whose relevant units and assumptions fit directly in the claim card or Decision Contract.

## 1. Keep Three Layers Separate

- The core skill controls profiles, selection history, evidence stages, inference over the actual selection path, and honest closure.
- A domain adapter declares how a class of tasks instantiates units, dependence, admissible methods, data checks, and scientific review.
- A project contract binds that adapter to actual data versions, identifiers, rules, tolerances, and expected counts.

Never place project table names, object aliases, sample counts, connection methods, or one study's null construction in the reusable adapter.

## 2. Freeze the Adapter Reference

Before affected outcomes, record an adapter or equivalent existing protocol with:

```text
adapter_name
adapter_version
adapter_artifact_path_or_locator
adapter_sha256_or_immutable_version
applicable_scope
analysis_unit
independence_unit
dependence_handling
partition_or_resampling_unit
admissible_estimands
domain_specific_gates
validation_procedures
falsification_requirements
completion_additions
required_human_review
```

In the machine schema, an attached adapter is run-scoped: `applicable_scope` states which part of the declared run it governs, and any blocking preflight must pass before that run produces affected outcomes. Use a separate successor run or contract when a narrower adapter should not gate unrelated work. An adapter may narrow an analysis or add safeguards. It may not waive core selection-path, provenance, evidence-stage, governance, or reporting requirements.

## 3. Freeze a Project Data Contract When Needed

Activate a data-contract preflight when identifiers, aliases, multi-table joins, repeated rows, numerical reconciliation, expected counts, or grouped partitions can change support or independence. Version and bind the contract to registered input versions. Express only applicable rules, chosen from or extending:

```text
identifier_integrity
alias_resolution
join_cardinality
numeric_consistency
expected_count
independent_unit_count
partition_group_leakage
measurement_support
```

Each rule records a stable ID, affected inputs and fields, expected relation or tolerance, failure action, and the procedure that evaluates it. Alias decisions require an authoritative source or an explicitly unresolved state; do not guess from similar strings. A many-to-many join, tolerance failure, count mismatch, or cross-partition group overlap is not automatically invalid, but it must match the frozen rule or block the affected result.

Let project code perform the actual checks. The generic validator can verify only that the declared adapter, contract, report, versions, hashes, statuses, and objections agree; it cannot infer whether a scientific identifier or domain tolerance is correct.

## 4. Bind the Preflight Report

For a machine-audited run, preserve a report or equivalent record with this shape:

```text
contract_version
checked_data_version_ids
overall_status
checks[]:
  check_id
  check_type
  status
  observed_summary
  evidence_path_or_locator  # optional when no separate evidence artifact exists
checked_at
```

Require every applicable frozen rule to have exactly one entry in `checks[]`. The top-level `overall_status` may be `passed`, `failed`, or `inconclusive`; `passed` requires all blocking checks to pass. A `failed` or `inconclusive` overall status, or any unresolved required check, blocks affected outcome-bearing execution but may support a transparent blocked report.

## 5. Record Semantic Review Proportionately

When a decision depends on a semantic judgment that structure checks cannot establish, record:

```text
required
reason
review_scope
reviewed_artifact_hashes
reviewer_identity_or_procedure
reviewer_relation_to_generation
status
unresolved_objections
human_signoff_required
human_signoff_status
human_signoff_evidence
```

Use `not_required` with one reason for low-consequence or directly testable decisions. Otherwise distinguish `pending`, `passed`, `passed_with_reservations`, `failed`, and `inconclusive`. If human signoff is required, distinguish `pending`, `passed`, and `declined`, and preserve the evidence or locator; a decision-bearing or completed state requires `passed`. Do not call a review independent merely because it used a different label; disclose shared evidence, context, methods, or personnel.

Semantic review does not turn same-data exploration into independent verification and does not establish empirical operating characteristics. It records which judgments received domain scrutiny and which remain self-assessed.
