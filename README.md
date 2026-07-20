# Scientific Autoresearch

![Coverage-guided scientific autoresearch workflow](figures/scientific-autoresearch-workflow-v0.2.1.png)

[Vector PDF](figures/scientific-autoresearch-workflow-v0.2.1.pdf) · [Vector SVG](figures/scientific-autoresearch-workflow-v0.2.1.svg)

`scientific-autoresearch` is an agent-independent [Agent Skill](https://agentskills.io) for mechanism-first scientific investigation over a finite, data-supported search space. It helps an agent define the decision before seeing outcomes, search systematically without arbitrary mechanism or round caps, learn from weak and null results, and preserve an auditable path from candidate generation to final inference.

Current version: **0.2.1**.

## Scope

Use the skill for research that requires several of these capabilities:

- build and version a mechanism inventory from what the available data can test;
- translate each mechanism into finite observables, formulations, parameters, supported samples, estimands, and falsifiers;
- define comparable selection families and retain incomparable or support-limited candidates as parallel conclusions;
- freeze a Decision Contract covering the final decision, admissible evidence, ranking rule, tie rule, and inconclusive rule;
- audit prior exposure to the same or overlapping data, including earlier analyses, parameter trials, and result views;
- separate exploratory analysis, internal validation, independent verification, and replication;
- cover the complete candidate-generation, modification, filtering, and promotion path with an appropriate inferential design;
- stop on coverage completion and inventory saturation, or pause with an open queue when execution resources end;
- produce immutable evidence, state transitions, and reproducible decisions.

Do not use it for literature-only review, manuscript editing, routine execution of a fixed pipeline, or unauthorized live human, animal, clinical, field, wet-lab, hazardous, or external-system actions.

## Version 0.2.1 Highlights

- Replaced fixed mechanism and round caps with a versioned `mechanism_inventory` and finite coverage cells.
- Added coverage completion plus inventory saturation as the scientific stopping rule.
- Added a pre-search Decision Contract; the smallest `p` value is never a default winner.
- Added a Prior-exposure Audit. Changing a sample, codebase, or skill version does not restore confirmatory status after overlapping data have been examined.
- Added explicit selection families and comparability gates for target population, supported sample, estimand, evidence stage, and data quality.
- Expanded inference to cover the complete selection path. Valid strategies include sealed holdouts, end-to-end null procedures, selective or sequential inference, hierarchical multiplicity control, and Bayesian model comparison or averaging.
- Kept method choice domain-sensitive rather than imposing one universal global-null procedure.
- Strengthened saturation auditing with mechanism-forward and data-product-reverse reviews, plus a question-dependent third independent source when useful.
- Separated scientific coverage from compute scheduling: priority controls execution order only, and unrun cells remain open.
- Added reusable compute authorization envelopes, resource-limited pause reports, and persistent open queues.
- Added a machine consistency validator for inventories, coverage matrices, ledgers, selection families, candidate decisions, data versions, and status transitions.
- Preserved weak, null, inconclusive, invalid, and failed results alongside supported findings.

## Core Loop

```text
decision -> prior exposure -> inventory -> coverage cells -> tests -> ledger
         -> selection-path inference -> saturation audit -> decision or open queue
```

The search space is bounded by the available data products and explicit formulations, not by a universal number of mechanisms or rounds. Rounds are immutable execution checkpoints. A run may use inexpensive uniform screening before deeper tests, but scheduling priority never counts as scientific coverage.

Scientific completion requires inventory saturation, closure of every eligible coverage cell, an audited complete selection ledger, and application of the frozen Decision Contract. The machine consistency check must also pass before `complete_within_scope` is reported.

Inventory saturation requires both a mechanism-forward audit and a data-product-reverse audit to produce no unresolved additions. A third independent audit source—such as literature, theory, expert knowledge, or known failure modes—is added when the scientific question makes it informative. Literature review is therefore conditional, not mandatory for every run.

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
Prior-exposure Audit, mechanism inventory, coverage matrix, and falsifiers.
Do not execute an analysis.
```

### One execution checkpoint

```text
Use the scientific-autoresearch skill to execute the next eligible coverage cells
over the approved local data. Preserve immutable outputs and the open queue.
```

### Coverage-based autonomous run

```text
Use the scientific-autoresearch skill to search the mechanisms and observables
supported by the approved data products. Stop scientifically only when coverage
is complete and the inventory is saturated. If the authorized compute envelope
ends first, pause and save every unrun coverage cell in the open queue.
```

## Executed-Run Outputs

A run records the decision and the complete selection history, for example:

```text
runs/<run_id>/
  run_manifest.json
  decision_contract.json
  prior_exposure_audit.json
  data_versions.json
  inventories/mechanism_inventory_vNNN.csv
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

Run the repository validator:

```bash
python scripts/validate_skill.py scientific-autoresearch
```

Validate a run before resuming it and before issuing a pause or final report:

```bash
python scientific-autoresearch/scripts/validate_run.py runs/<run_id> \
  --output runs/<run_id>/consistency_report.json
```

The run validator checks referential integrity and state consistency across the inventory, coverage matrix, search ledger, selection families, candidate registry, data versions, decision artifacts, and status transitions. A failed consistency audit blocks a scientific-completion claim.

## Evaluation

The behavioral evals cover design-only work, observational support, coverage-based machine learning and simulation, compute authorization and resource pauses, sensitive data, null triage, causal identification, Decision Contracts, prior exposure, candidate comparability, full selection-path inference, saturation audits, and consistency checks.

Trigger evals contain balanced should-trigger and should-not-trigger prompts. Run evals in isolated contexts and compare v0.2.1 with the previous version or a no-skill baseline.

## Scientific Interpretation Standard

A final ranking or selection must follow the frozen Decision Contract and apply only within a valid selection family. Candidates with different target populations, support samples, estimands, evidence stages, or materially different data quality are not directly ranked unless a defensible comparison was declared in advance.

Inference must account for every step that influenced candidate generation, modification, filtering, and promotion. The skill selects an appropriate method for the scientific design; it does not force all fields into one global-null technique. Weak and failed results remain in the ledger, and random seeds may not be chosen by outcome.

Recommended manuscript language is:

> We systematically searched a versioned inventory of mechanisms and observables testable with the available data products.

Add the boundary statement:

> This search does not establish exhaustiveness beyond the data-supported search space.

## Inspiration

This project was inspired by Andrej Karpathy's [`autoresearch`](https://github.com/karpathy/autoresearch) project and adapts iterative agent-run experimentation to general scientific inference, with additional emphasis on governance, coverage, falsification, adaptive-search control, and reproducibility.

## Citation

Use the metadata in [`CITATION.cff`](CITATION.cff) or [`CITATION.bib`](CITATION.bib). For manuscripts, cite the tagged release.

## License

MIT License. See `LICENSE`.
