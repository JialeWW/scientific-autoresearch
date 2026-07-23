# Execution Lifecycle

Use this reference only when development, execution qualification, resource feasibility, or implementation equivalence is material. It prevents engineering changes from being mistaken for scientific adaptation.

## Default Risk Model

Ordinary research protects against accidental error and ordinary infrastructure failure. Do not add adversarial supply-chain, tamper-resistance, exact-byte, process-tree, or emergency-receipt controls unless the user requests them or a documented consequence model requires them.

Scientific-search breadth and engineering burden are independent. A broad coverage study may use ordinary reproducibility controls; a narrow frozen test may require stronger controls when its consequences warrant them.

## Lifecycle Boundary

Keep three stages distinct:

1. **Development** is mutable. Repair code, tests, fixtures, caches, paths, and execution settings here. Candidate-specific outcomes must not be used to tune these choices unless the work is already recorded as adaptive science.
2. **Execution qualification** is response-blind. Check input identity, safe data projection, software operation, numerical equivalence, and resource feasibility without inspecting candidate effects, scores, ranks, or selections.
3. **Production science** begins when candidate-specific outcomes can affect the scientific decision. Preserve its scientific definitions and outcome-driven history; do not import failed development attempts as scientific rounds.

A qualification failure creates an engineering repair or amendment. Re-freeze the affected science only when the repair changes scientific meaning or was chosen in response to candidate-specific outcomes.

## Bound Qualification

Before qualification starts, define its smallest scientifically coherent executable analysis family, minimum science-critical checks, pass/fail criteria, resource bound, and failure action. Checks should address identified ways that execution could alter the sample, estimand, ranking, or conclusion.

When the criteria pass, accept the execution state and begin production science for that family. Do not keep adding checks for general reassurance, recursively audit the validator or audit procedure, or require a stronger equivalence claim than the science needs. Reopen qualification only for a newly identified concrete failure mode within that scientific-impact boundary; record the reason and keep the new check proportionate.

Qualify independent families separately. A pending or failed check for one family remains open and does not block a qualified family. A shared input, calibration, or dependency blocks only affected families; a joint decision rule may delay the joint comparison, promotion, or conclusion without suppressing otherwise valid family-level results.

If the resource bound is reached before the criteria pass, report the unresolved blocker or simplify the execution design. Do not silently expand qualification or substitute administrative completeness for scientific readiness.

## Classify the Change by Effect

Classify by effect; do not create separate contracts or announce category names in ordinary work:

- A **scientific-meaning change** affects candidates, estimand, scientific population or support, feature meaning, model or statistic, validation design, multiplicity, decision rule, stopping, or reporting role. Outcome-driven changes enter the selection path.
- A **data-or-support change** affects input identity, versions, joins, quality rules, units, support, or dependence. Repeat the affected data checks. Re-freeze science only if the change alters eligibility, sample, estimand, interpretation, or decision use.
- An **execution change** affects workers, chunk size, scheduling, cache location, parallelism, runtime implementation, or equivalent resource controls. It is not a scientific change when an agreed equivalence check passes.

Classify code edits by their effect, not their filename. A production-script edit can be an execution repair; a small configuration edit can be scientific if it changes a threshold, feature, sample, or model.

## Equivalent Execution

Before expensive execution, state which ordinary implementation settings may vary and how equivalence will be judged. Use the weakest sufficient gate:

- byte equality when exact serialization is scientifically required;
- value-and-schema equality when order or packaging may differ but scientific values may not;
- a declared numerical tolerance when floating-point or algorithmic equivalence is appropriate.

Aggregation order, randomization, and partition membership remain scientific when they can change inference. Workers, chunks, caches, and scheduling remain engineering when the equivalence gate shows they do not.

If equivalence passes, record one execution amendment and continue. If it fails, stop before opening decision-bearing outcomes and determine whether the difference is a data, execution, or scientific change.

## Smoke Before Expensive Full-Scale Work

When memory, I/O, duration, or long-tail behavior presents a material risk, run a response-blind smoke on the worst plausible component before expensive upstream full-scale stages. The smoke should answer only the feasibility questions needed to choose an execution profile, using safe projected inputs or noncandidate fixtures where possible.

Freeze production execution settings only after the relevant smoke passes. Low-risk work does not need a ceremonial smoke test or a `not_applicable` record.

## Records and Checkpoints

Development files may be edited normally. Once an outcome-bearing contract, result, or report has been shared or used as evidence, preserve it and create an amendment or successor rather than silently rewriting history.

Record engineering failures only to the degree needed for diagnosis and reproducibility. Do not add worker, chunk, cache, deployment, or retry events to the scientific selection ledger unless they exposed candidate outcomes or influenced a scientific choice.

Run only the scientific or execution checks needed at meaningful delivery, pause, handoff, material decision-bearing resume, or scientific-plan-change boundaries—not after every script or result. Do not build a general validator for ordinary work. Ordinary retries, engineering resumes, and accepted execution amendments do not require repeated full validation. Continue automatically inside the recorded authorization and equivalence envelope.
