# Multi-Agent Scientific Collaboration

Read when delegation would help. Choose tasks from the current scientific dependencies and expected benefit; the handoff fields below do not prescribe a team or extra paperwork.

## Hand off a bounded task

Use a short task message with the material parts of:

- **Purpose:** the question, decision role, and candidate or test identifiers.
- **Inputs:** authoritative sources and versions, protocol, sample and unit definitions, measurement semantics, and upstream dependencies.
- **Boundaries:** allowed decisions or iteration, prior evidence exposure or blinding, resources, and stopping bounds.
- **Ownership:** output locations or file sections the worker may change and shared inputs other tasks depend on.
- **Return:** checkable findings or artifacts, relevant uncertainty and limitations, and how to report completion, failures, proposed changes, and open issues.

Reference existing definitions and omit irrelevant fields. Give sufficient context for interpretation without priming a desired result. Reuse a worker when its context is appropriate; use a separate context when proposal generation or review needs separation from prior conclusions.

A new scientific choice outside the assigned mapping follows the successor rules in sections 2 and 4 of `../SKILL.md` before execution. Engineering changes that preserve scientific meaning follow section 4 and do not by themselves require a scientific successor. Coordinate further delegation with the primary so the team's scope, dependencies, and total resources remain visible.

## Coordinate execution and changes

Dispatch work with ready inputs and compatible dependencies. While workers run, the primary advances useful work that does not depend on their pending results. Wait for required upstream results before dependent execution, and for the comparison set required by the decision rule before joint selection or conclusion. Report partial results as partial; completion order must not select the favorable branch.

Give concurrent writers separate output ownership or coordinate edits. Keep decision-bearing shared inputs stable during their use. If inputs, protocol, or code change, identify affected workers, stop or redirect stale work, and assess which outputs remain interpretable before integration. Preserve exposed outcomes and their influence on subsequent choices. An unrelated blocked branch need not stop qualified work, but dependencies and joint decision rules still apply.

Maintain the shared sample, evidence partitions, randomization, and aggregation rules. Preserve selection-relevant attempts and exposure across workers under section 4; routine scheduling and retries need only operational records. Ending or combining assignments does not close an unresolved scientific requirement.

## Verify and integrate evidence

Workers return output references and actual input/procedure versions, including unfavorable or failed attempts, deviations, and unresolved issues. A completion message or successful tool exit alone does not establish success.

The primary checks material inputs, sample and estimand compatibility, units, protocol compliance, and actual outputs supporting the claim. Use targeted recomputation or another suitable check when it resolves a concrete concern; do not require an exact rerun of every delegated calculation.

Resolve discrepancies by identifying differences in inputs, implementation, assumptions, or interpretation. Repair errors, retain legitimate sensitivity results, and leave unresolved scientific disagreements explicit. Do not settle them by vote or prefer a favorable result. Apply the existing claim and selection rules to the combined evidence.

Integrate findings, evidence references, adjudication, and next actions into the existing scientific record. Worker notes support that record rather than becoming competing authorities. Account for material unfinished or failed assignments before claiming completion; distinguish them from scientific nulls under `../SKILL.md`. Report the actual division of work and material verification limits when useful.

## Use the appropriate review context

Ordinary delegation does not trigger scientific-stop review. When section 6 of `../SKILL.md` triggers it, follow `completion-review.md` for fresh-context setup, staged disclosure, exposure reporting, and primary adjudication. An ordinary worker's review satisfies that requirement only if the prescribed design was actually followed. Context separation does not create independent scientific evidence.
