# Scientific Autoresearch

![Coverage-guided scientific autoresearch workflow](figures/scientific-autoresearch-workflow-v0.2.1.png)

[Vector PDF](figures/scientific-autoresearch-workflow-v0.2.1.pdf) · [Vector SVG](figures/scientific-autoresearch-workflow-v0.2.1.svg)

`scientific-autoresearch` is an agent-independent [Agent Skill](https://agentskills.io) for auditable scientific investigation. It scales from one formally audited fixed test to adaptive candidate search and coverage-based search over a finite, data-supported space. It helps an agent match procedural overhead to selection risk while preserving conservative inference.

Current version: **0.2.3**.

## Scope

Use the skill when the user requests formal audit artifacts or when the work generates, modifies, filters, ranks, or systematically covers scientific candidates. Depending on profile, it can:

- execute one frozen claim with a proportionate reproducibility record;
- build a typed inventory of mechanisms, models, features, simulation formulations, or design alternatives supported by the available data;
- translate each eligible candidate into finite observables, formulations, parameters, supported samples, estimands, and falsifiers;
- define comparable selection families and retain incomparable or support-limited candidates as parallel conclusions;
- freeze a Decision Contract covering the final decision, admissible evidence, ranking rule, tie rule, and inconclusive rule;
- audit prior exposure to the same or overlapping data, including earlier analyses, parameter trials, and result views;
- separate exploratory analysis, internal validation, independent verification, and replication;
- cover the complete candidate-generation, modification, filtering, and promotion path with an appropriate inferential design;
- claim scoped scientific completion only after the full closure gate passes; otherwise issue a bounded report or pause with an open queue;
- produce versioned evidence, auditable state transitions, and reproducible decisions.

Do not trigger the skill merely to compute one prespecified Pearson or Spearman correlation, evaluate one frozen model, estimate one fixed parameter, or run one fixed convergence check. If the user explicitly requests a formal audited run for such a task, use `fixed_test`; otherwise handle it as ordinary analysis. Also exclude literature-only review, manuscript editing, routine pipeline execution, and unauthorized live human, animal, clinical, field, wet-lab, hazardous, or external-system actions.

## Version 0.2.3 Highlights

- Replaces the one-size-fits-all executed-run workflow with three risk profiles: `fixed_test`, `adaptive_search`, and `coverage_search`; `design_only` remains non-executing.
- Makes candidate inventories typed and applies inventory, saturation, and complete-selection-path machinery only when the chosen profile needs it.
- Activates transport, measurement-error, and screen-to-decision scale gates only when the corresponding risk is present.
- Distinguishes a valid stage report from scientific completion: bounded work may be faithfully finished while an adaptive or coverage queue remains open.
- Upgrades the run schema and validator to 1.5.0 with profile-aware initialization, non-overwriting upgrade snapshots, and checks that reduce metadata burden without weakening applicable safeguards.

## Choose the Smallest Valid Profile

- `design_only`: review or construct a question, claim card, inventory, or analysis design without executing it.
- `fixed_test`: one frozen claim, sample, statistic or model, and decision rule, with no result-dependent candidate generation or selection. Use only when formal audited execution is requested.
- `adaptive_search`: candidates may be generated, modified, screened, tuned, filtered, compared, or promoted. Require a Decision Contract, prior-exposure audit, ledger, selection families, and inference covering the actual selection path.
- `coverage_search`: systematically search a versioned finite data-supported space and assess scoped completion. Add typed inventory coverage, complementary saturation audits, the open queue, and coverage-completion rules.

Escalate the profile when behavior changes; never downgrade after seeing results. A fixed analysis that spawns a new threshold, model, subgroup, or formulation becomes `adaptive_search`. A search becomes `coverage_search` only when it attempts systematic scoped coverage or makes a scientific-completion claim.

Conditional gates remain strict when applicable. Require transport analysis only when evidence is carried across materially different target or reporting populations; measurement-error sensitivity only when uncertainty can affect support, eligibility, selection, ranking, or the conclusion; and a screening-to-decision mapping only when a selection-influencing screen and the final evidence use different statistics, estimands, or scales.

## Coverage-Search Loop

```text
decision -> prior exposure -> inventory -> coverage cells -> tests -> ledger
         -> selection-path inference -> saturation audit -> decision or open queue
```

The search space is bounded by the available data products and explicit formulations, not by a universal number of candidates or rounds. Rounds are write-once-by-policy execution checkpoints. The validator reconciles their recorded hashes; tamper evidence against coordinated rewriting of both files and manifest requires an append-only or externally anchored store. A run may use inexpensive uniform screening before deeper tests, but scheduling priority never counts as scientific coverage.

The workflow figure at the top depicts `coverage_search`, the most expansive profile. It is not the required process for `fixed_test` or every `adaptive_search` run.

A `stage_report` may validly close the work authorized for the current checkpoint: it states what ran, what was learned, which safeguards applied, and what remains open. It is not a claim that the candidate space is saturated or covered. A `fixed_test` can finish when its frozen test and proportionate checks are complete; an `adaptive_search` can report its current decision state without claiming exhaustive coverage. Scientific completion (`complete_within_scope`) is reserved for `coverage_search` and requires inventory saturation, closure of every eligible coverage cell, an audited complete selection ledger, application of the frozen Decision Contract with a terminal decision, an adequate prior-exposure audit for the claim, and a passing consistency check.

Inventory saturation requires both a candidate-forward audit and a data-product-reverse audit to produce no unresolved additions. A third independent audit source—such as literature, theory, expert knowledge, or known failure modes—is added when the scientific question makes it informative. Literature review is therefore conditional, not mandatory for every run.

## Repository Layout

```text
.
├── README.md
├── CHANGELOG.md
├── CITATION.cff
├── CITATION.bib
├── LICENSE
├── figures/
│   ├── scientific-autoresearch-workflow-v0.2.1.pdf
│   ├── scientific-autoresearch-workflow-v0.2.1.png
│   └── scientific-autoresearch-workflow-v0.2.1.svg
├── scripts/
│   └── validate_skill.py
└── scientific-autoresearch/
    ├── SKILL.md
    ├── scripts/
    │   └── validate_run.py
    ├── evals/
    │   ├── evals.json
    │   └── eval_queries.json
    └── references/
        ├── coverage-search.md
        ├── decision-selection.md
        ├── governance-safety.md
        ├── report-contract.md
        ├── statistical-discipline.md
        ├── status-schema.md
        └── ...
```

Only the `scientific-autoresearch/` directory is the installable skill. Repository-level scripts, citation files, and documentation support distribution and maintenance.

## Installation

Copy or link the installable directory into a skills directory recognized by your agent client:

```bash
git clone https://github.com/JialeWW/scientific-autoresearch.git
cp -R scientific-autoresearch/scientific-autoresearch /path/to/your/skills-directory/
```

The installed path must end with:

```text
scientific-autoresearch/SKILL.md
```

Discovery and configuration vary by client. The skill contains no client-specific metadata. Its run validator uses Python 3.10 or later and only the standard library.

## Basic Usage

### Design only

```text
Use the scientific-autoresearch skill to define the Decision Contract,
typed candidate inventory, or falsification plan needed for this question.
Do not execute an analysis or create a run directory.
```

### One formally audited fixed test

```text
Use the scientific-autoresearch skill with the fixed_test profile to execute this
frozen parameter estimate once and produce proportionate audit artifacts.
Do not generate or rank alternatives.
```

### Adaptive candidate search

```text
Use the scientific-autoresearch skill with the adaptive_search profile to compare
these candidate models. Record every selection-influencing test and apply the
predeclared Decision Contract; do not claim coverage saturation.
```

### Coverage-based autonomous run

```text
Use the scientific-autoresearch skill with the coverage_search profile to search
the candidate types, observables, and tests supported by the approved data
products. Stop scientifically only when coverage is complete and the inventory
is saturated, the complete selection ledger is audited, the frozen Decision
Contract yields a terminal decision, prior exposure is adequate for that claim,
and the consistency check passes. If the authorized compute envelope ends first,
pause and save every unrun coverage cell in the open queue.
```

## Executed-Run Outputs

Artifacts are profile-proportionate. `fixed_test` records the frozen claim, versions, result, uncertainty, falsifier where applicable, reproduction information, and consistency status. `adaptive_search` adds the prior-exposure audit, selection families, candidate registry, and complete selection ledger. `coverage_search` uses the full structure below:

```text
runs/<run_id>/
  run_manifest.json
  decision_contract.json
  prior_exposure_audit.json
  data_versions.json
  inventories/candidate_inventory_vNNN.csv
  inventories/coverage_matrix_vNNN.csv
  inventories/saturation_audit_vNNN.json
  execution_queue.csv
  search_ledger.jsonl
  selection_families.json
  status_transitions.jsonl
  candidate_registry.csv
  rounds/round_NNN/
    report.md
    summary.csv
    reproduce_commands.txt
    round_gate.md
  consistency_report.json
  pause_report.md                 # when work remains open
  final_report.md                 # only after completion checks pass
```

Sensitive diagnostics must be minimized or de-identified. Reproduction records must redact credentials, tokens, signed links, private identifiers, and restricted paths.

## Validation

Initialize the canonical metadata skeleton for a new run:

```bash
python scientific-autoresearch/scripts/validate_run.py --init runs/<run_id> \
  --profile <fixed_test|adaptive_search|coverage_search>
```

Initialization never overwrites an existing run or supplies scientific decisions or approvals; the skeleton remains invalid until its required fields and records are completed.

Before upgrading a formal run, validate the source profile and create a non-overwriting, hash-bound history snapshot:

```bash
python scientific-autoresearch/scripts/validate_run.py \
  --snapshot-upgrade runs/<run_id> --to-profile <adaptive_search|coverage_search>
```

Review the copied evidence and append the exact `profile_history` entry returned by the helper while adding the new profile's artifacts. The helper does not edit the manifest or perform the scientific migration for you.

Run the repository validator:

```bash
python scripts/validate_skill.py scientific-autoresearch
```

Validate a run before resuming it and before issuing a pause or final report:

```bash
python scientific-autoresearch/scripts/validate_run.py runs/<run_id> \
  --output runs/<run_id>/consistency_report.json
```

For schema 1.5.0 runs, the validator reads the recorded profile and checks only the structures required by that risk level. It checks fixed claims and provenance for `fixed_test`, adds selection-path integrity for `adaptive_search`, and adds inventory, coverage, saturation, and queue consistency for `coverage_search`. Schema 1.4 and earlier runs retain their legacy full-schema validation and inventory filename. A failed applicable check blocks the corresponding completion claim. Report that separately from numerical rerun agreement: matched inputs, code, environment, seeds, tolerances, and output hashes can support same-condition agreement for the checked outputs without repairing missing metadata. Hash reconciliation provides internal consistency, not proof against coordinated rewriting of every local record; externally anchor the digest when adversarial tamper evidence is required.

## Evaluation

The behavioral evals cover `design_only` and all three execution profiles across observational, machine-learning, simulation, sensitive-data, null-triage, and causal settings. They also test that ordinary one-off statistics, frozen-model evaluations, parameter estimates, and fixed convergence checks do not trigger the skill unless formal audited execution is explicitly requested.

Trigger evals contain balanced should-trigger and should-not-trigger prompts. Run evals in isolated contexts and compare v0.2.3 with the previous version or a no-skill baseline.

## Scientific Interpretation Standard

For `adaptive_search` and `coverage_search`, a final ranking or selection must follow the frozen Decision Contract and apply only within a valid selection family. Candidates with different target populations, support samples, estimands, evidence stages, or materially different data quality are not directly ranked unless a defensible comparison was declared in advance.

Inference must account for every step that influenced candidate generation, modification, filtering, and promotion. The skill selects an appropriate method for the scientific design; it does not force all fields into one global-null technique. Weak and failed results remain in the ledger, and random seeds may not be chosen by outcome.

Recommended manuscript language for a completed `coverage_search` should name the actual candidate type:

> We systematically searched a versioned inventory of [candidate type] and associated tests supported by the available data products.

Add the boundary statement:

> This search does not establish exhaustiveness beyond the data-supported search space.

## Inspiration

This project was inspired by Andrej Karpathy's [`autoresearch`](https://github.com/karpathy/autoresearch) project and adapts iterative agent-run experimentation to general scientific inference, with additional emphasis on governance, coverage, falsification, adaptive-search control, and reproducibility.

## Citation

Use the metadata in [`CITATION.cff`](CITATION.cff) or [`CITATION.bib`](CITATION.bib). For manuscripts, cite the tagged release.

## License

MIT License. See `LICENSE`.
