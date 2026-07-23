# Domain Adapter and Data-Support Checks

Use this reference only when scientific validity depends on domain semantics that the generic workflow cannot infer, such as independent units, repeated or nested observations, identifier reconciliation, joins, measurement tolerances, admissible estimands, or specialized falsification rules. A simple analysis whose relevant units and assumptions fit directly in the compact scientific plan needs no separate adapter.

## 1. State the Domain Semantics

Record only what changes scientific meaning:

```text
applicable analysis family
analysis unit
scientifically independent unit
dependence handling
partition or resampling unit
admissible estimands
domain-specific support rules
domain-specific falsifiers
required scientific review
```

Use the smallest coherent analysis family governed by the same rules. Independently executable families do not block one another: a shared input or calibration blocks only its dependents, and a joint rule blocks only the joint comparison or conclusion.

Keep reusable domain semantics separate from project-specific table names, aliases, sample counts, connection methods, or one study's null construction.

## 2. Run a Proportionate Data-Support Check

Run a response-blind data-support check when identifiers, aliases, multi-table joins, repeated rows, numerical reconciliation, expected counts, or grouped partitions can change support or independence. Use only the applicable rules:

```text
identifier integrity
alias resolution
join cardinality
numeric consistency
expected count
independent-unit count
partition leakage
measurement support
```

For each rule, record its stable name, affected inputs and fields, expected relation or tolerance, observed status, and failure action. Alias decisions need an authoritative source or an explicitly unresolved state; do not guess from similar strings. A many-to-many join, tolerance failure, count mismatch, or cross-partition overlap is not automatically invalid, but it must match the scientific rule or block the affected result.

Let project code perform the checks. The generic skill cannot infer whether a scientific identifier, tolerance, or domain assumption is correct. Use `passed`, `failed`, or `inconclusive`; `passed` requires every blocking rule for that family to pass.

Once the relevant rules pass, begin or resume that family's science. Do not add more blocking checks for general reassurance. If a response-blind repair changes an identifier mapping, join, support rule, unit, or quality rule, rerun only the affected checks. Create a new scientific batch only when the change can alter the supported sample, estimand, candidate value, ranking, inference, or interpretation.

## 3. Review Material Semantic Judgments

When a scientific decision depends on a judgment that structure checks cannot establish, record its reason, scope, evidence reviewed, status, and unresolved objections in the compact research record. Use `not_required` with a reason for low-consequence or directly testable decisions; otherwise use `pending`, `passed`, `passed_with_reservations`, `failed`, or `inconclusive`.

Do not call a review independent merely because it used another person, model, or label. Disclose shared evidence, context, methods, or personnel. Semantic review does not turn same-data exploration into independent verification or establish empirical operating characteristics.

## 4. Add Machine Bindings Only on Explicit Request

Ordinary work needs no adapter artifact, hash, immutable version, schema-specific project contract, or validator report. If machine-readable audit, formal handoff or recovery, or an existing structured run separately requires those bindings, read `report-contract.md` and `status-schema.md` and represent the same scientific checks there. The formal representation does not add scientific validity by itself.
