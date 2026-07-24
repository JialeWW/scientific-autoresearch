# Scientific Stop Challenge

Use this reference only before claiming `search_stop_admissible=true`, stating that no material test remains, or ending open or adaptive research on a scientific-stop basis. The challenge tries to falsify the stopping rationale; it does not certify open-world scientific completeness or create independent evidence.

Do not trigger it merely because one named test or registered batch finished, or because a user, resource, safety, or governance boundary ended execution. Report the bounded result or boundary honestly and leave `search_stop_admissible` false when a material open test is known, or `not_assessed` when scientific stopping was not evaluated.

## 1. Reconcile Declared Identifiers

The reconciliation is deterministic only over declared identifiers and resolvable references. Seed its expected keys from:

- candidate, prediction, falsifier, material control, and ablation IDs;
- protocol items explicitly assigned a scientific role;
- data-product families explicitly marked as science-facing;
- registered tests and their qualification, output, closure, or open-queue references.

For a science-facing manifest, prefer explicit semantics such as:

```yaml
product_id: stable_id
product_role: inferential | diagnostic | qa | intermediate | provenance
science_facing: true | false
```

Group columns only under an explicit product-family or equivalence declaration. Ordinary raw, QA, cache, intermediate, and provenance fields may then be summarized without turning every field into a candidate. Reject an undeclared semantic-equivalence assumption; free-text predictions and controls belong to the reviewer challenge rather than deterministic reconciliation.

Keep the smallest useful crosswalk:

```text
item_id
source_refs
source_kind
parent_candidate_id
scientific_role
support_status
decision_relevance
disposition
test_or_formulation_id
output_ref
closure_reason
successor_id
```

Every declared key must resolve to one valid disposition. A tested item must resolve to qualification and required output. An untested terminal item needs a supported descriptive, QA/intermediate, current-data limitation, scope, duplicate/equivalence, or successor rationale. A role label such as `sensitivity` or `diagnostic` is not a disposition. Missing mappings, unsupported closures, and successors absent from the open queue make `scientific_mapping_complete=false`.

## 2. Challenge Stopping in Two Stages

Use one fresh reviewer context when available. A different agent or model is process separation, not independent scientific verification. If no fresh reviewer is available, use the same procedure as a clearly labeled self-review and disclose shared context.

Use staged disclosure:

1. **Source reconstruction:** provide only the question, authorized scope, candidate predictions, protocol scientific roles, science-facing manifest, support rules, decision rule, and any design assumptions or measurement semantics needed to interpret those sources. Ask the reviewer to reconstruct the expected scientific set candidate-forward, protocol-forward, and data-product-reverse. If a necessary source is missing or unverifiable, record that limitation rather than inventing its content.
2. **Reconciliation challenge:** after preserving that reconstruction, provide the test registry, output index, closures, open queue, and selection or exposure history. Ask the reviewer to identify mismatches and challenge closure reasons.

Do not provide the primary agent's proposed stop verdict or suspected omission before reconstruction. If the client cannot stage access, record:

```yaml
registry_visible_during_reconstruction: true
anchoring_risk: elevated
```

A same-context self-review that has already seen the registry is not source-isolated merely because it temporarily sets the registry aside. It must record `registry_visible_during_reconstruction: true` and `anchoring_risk: elevated`.

Record `review_mode`, `context_isolation`, source versions, materials reviewed, the preserved reconstructed expected set, missing or unverifiable sources, structural discrepancies, challenged closures, `potentially_material_open_tests`, reviewer verdict, and claim ceiling. The reviewer does not decide whether a proposed test would change the current result. Use this closed reviewer vocabulary:

```yaml
potentially_material_open_tests: []
verdict: no_blocker_found | potential_findings_present | inconclusive
```

`potential_findings_present` means that primary-agent adjudication is required; it does not itself establish a decision-changing blocker. Use `inconclusive` for a material source or reconstruction dispute that the review cannot resolve. Never issue a completeness certificate or invent an additional verdict.

## 3. Adjudicate Every Finding

The primary agent adjudicates each finding against the current result state, decision boundary, support, feasibility, authorization, resources, and selection path:

```yaml
finding_id: stable_id
disposition: accepted | duplicate | out_of_scope | unsupported | infeasible | nonmaterial | already_covered
evidence: []
rationale: text
successor_id: optional
```

Do not silently omit a finding. An accepted finding blocks scientific stopping when it is nonduplicate, in scope, supported, feasible, authorized, and reasonably capable of materially changing the requested interpretation or decision. Put it in the open queue or freeze an outcome-informed successor before execution. A rejected finding needs evidence and rationale; reviewer novelty alone does not make it a blocker.

Preserve the reviewer's issued verdict. If a material dispute, missing source, or unadjudicated finding remains during primary adjudication, leave the affected finding explicitly unresolved and set `search_stop_admissible=indeterminate`; do not rewrite the reviewer verdict unless the reviewer itself revises its report. `no_blocker_found` is only the reviewer result; set `search_stop_admissible=true` only after declared-source reconciliation and all adjudications pass.

## 4. Report Separate States

Use only the applicable values; do not invent compound or interim status labels:

```yaml
request_execution_complete: true | false
scientific_mapping_complete: true | false | not_assessed
search_stop_admissible: true | false | indeterminate | not_assessed
complete_within_scope: true | false | not_assessed
termination_reason: scientific_stop | request_complete | user_boundary | resource_boundary | safety_boundary | governance_boundary
```

Keep the canonical state fields unchanged. A project may add a separate optional label such as `execution_status: registered_batch_complete`; it must not replace or change the type of `request_execution_complete`. That boolean does not imply either mapping completeness or stop admissibility. `complete_within_scope` additionally requires every condition in `coverage-search.md`; this challenge can audit that record but cannot replace it.

Only the primary agent records `termination_reason`, and only when the task actually terminates; a reviewer must not propose one. Record exactly one primary reason then. Use `request_complete` when the bounded request finished as authorized. Use a boundary value only when that boundary interrupts otherwise unfinished authorized work; authorization merely defining a completed request does not turn `request_complete` into `user_boundary`.

## 5. Bound Re-review and Claims

Run one challenge per stopping episode and collect accepted findings into one successor or open queue. A delta review is valid only while the scientific question and authorization, candidate classes, science-facing data products, support rules, and decision rules remain unchanged. If a finding or new data changes any of them, rerun the affected source-reconstruction lanes rather than relying on an ordinary delta.

Do not spawn a reviewer of the reviewer. Do not call a fresh-context review independent replication, inferential validation, or proof that no unimagined candidate exists. It establishes only an evidence-referenced challenge to stopping over the declared and reconstructed sources. It cannot restore pre-result status, reconstruct omitted attempts, reseal exposed evidence, validate unsupported domain assumptions, or upgrade same-data exploration into confirmation.
