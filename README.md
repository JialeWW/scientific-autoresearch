# Scientific Autoresearch

![Coverage-guided scientific autoresearch workflow](figures/scientific-autoresearch-workflow-v0.2.1.png)

[Vector PDF](figures/scientific-autoresearch-workflow-v0.2.1.pdf) · [Vector SVG](figures/scientific-autoresearch-workflow-v0.2.1.svg)

`scientific-autoresearch` is an agent-independent [Agent Skill](https://agentskills.io) for mechanism-first scientific investigation over a finite, data-supported search space. It helps an agent define the decision before seeing outcomes, search systematically without arbitrary mechanism or round caps, learn from weak and null results, and preserve an auditable path from candidate generation to final inference.

Current version: **0.2.2**.

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

## Version 0.2.2 Highlights

- Requires frozen substantive eligibility and mechanism alignment before statistical ranking, while retaining justified constrained or factorial designs.
- Separates target, analysis, selection, and reporting populations; cross-population claims require validated transport or remain parallel or support-limited.
- Adds a conditional measurement-error sensitivity gate when uncertainty can affect support, selection, ranking, or promotion, without prescribing one method.
- Requires a frozen mapping and discordance rule when screening statistics and final decision or prediction models use different scales.
- Upgrades the run validator to 1.4.0, adds non-overwriting schema initialization, and keeps legacy artifacts readable while separating metadata consistency from numerical reproduction.

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
over the authorized data. Preserve immutable outputs and the open queue.
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

Initialize the canonical metadata skeleton for a new run:

```bash
python scientific-autoresearch/scripts/validate_run.py --init runs/<run_id>
```

Initialization never overwrites an existing run or supplies scientific decisions or approvals; the skeleton remains invalid until its required fields and records are completed.

Run the repository validator:

```bash
python scripts/validate_skill.py scientific-autoresearch
```

Validate a run before resuming it and before issuing a pause or final report:

```bash
python scientific-autoresearch/scripts/validate_run.py runs/<run_id> \
  --output runs/<run_id>/consistency_report.json
```

The run validator checks referential integrity and state consistency across the inventory, coverage matrix, search ledger, selection families, candidate registry, data versions, decision artifacts, and status transitions. A failed consistency audit blocks a scientific-completion claim. Report that separately from numerical rerun agreement: matched inputs, code, environment, seeds, tolerances, and output hashes can support same-condition agreement for the checked outputs without repairing missing metadata.

## Evaluation

The behavioral evals cover design-only work, observational support, coverage-based machine learning and simulation, compute authorization and resource pauses, sensitive data, null triage, causal identification, Decision Contracts, prior exposure, candidate comparability, full selection-path inference, saturation audits, and consistency checks.

Trigger evals contain balanced should-trigger and should-not-trigger prompts. Run evals in isolated contexts and compare v0.2.2 with the previous version or a no-skill baseline.

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
