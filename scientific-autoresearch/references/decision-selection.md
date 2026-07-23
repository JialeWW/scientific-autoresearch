# Decision, Exposure, and Selection Protocol

Use this protocol when an inspected outcome can alter an unprespecified scientific choice. A prespecified comparison or bounded automated procedure executes directly when its candidate domain, proposal and evaluation rules, evidence partitions, metric, randomization, budget, stopping, joint inference, decision, and reporting rules cannot change after outcomes. If an outcome motivates discretion outside that frozen mapping, preserve the result, record the resulting choice, and freeze the successor before continuing.

Create or reuse one lightweight append-only or versioned record before the first outcome that can influence an unprespecified choice. A pre-existing project ledger is not required. Use this path whenever one persistent compact record can faithfully preserve the selection path, including ordinary work that spans sessions. Do not create parallel registries or reconstruct omitted history later.

The lightweight record may be Markdown, JSONL, or an equivalent project record. Freeze its task scope, candidate or formulation boundary, data-to-decision rule, prior-exposure audit scope, and evidence partitions. Append one timestamped entry for each selection-influencing outcome or decision with an event ID, outcome accessed, resulting change or decision, reason, status, and affected candidate or family. End with the complete selection path and unresolved branches. Preserve weak, failed, invalid, and abandoned paths; compact storage does not reduce inferential obligations.

Write those events when they occur. At a declared checkpoint such as pause, handoff, a change from frozen to outcome-guided work, sealed-evidence opening, external decision release, a resource checkpoint, or bounded completion, summarize the compact record. Do not turn every analysis call into a reporting or validation checkpoint.

## Contents

- [1. Freeze the Data-to-Decision Rule](#1-freeze-the-data-to-decision-rule)
- [2. Audit Prior Exposure](#2-audit-prior-exposure)
- [3. Define Comparable Selection Families](#3-define-comparable-selection-families)
- [4. Cover the Complete Selection Path](#4-cover-the-complete-selection-path)
- [5. Separate Scientific Coverage from Scheduling](#5-separate-scientific-coverage-from-scheduling)
- [6. Decide Conservatively](#6-decide-conservatively)

## 1. Freeze the Data-to-Decision Rule

Before candidate-specific outcomes are inspected, freeze a compact data-to-decision rule inside the single research record. Its core defines:

- the scientific or operational decision, eligible candidate classes, substantive eligibility, target population, supported sample, and estimand;
- the analysis and scientifically independent units, dependence handling, and any partition or resampling unit;
- comparable selection families and the evidence used for screening, ranking, falsification, and promotion;
- the decision, tie or practical-equivalence, inconclusive, and noncomparable-candidate rules;
- the minimum meaningful difference, selection-path inference strategy, freeze time, version, and amendment conditions.

Add conditional clauses only when their pathway exists: distinct analysis, selection, or reporting populations and transport requirements; selection-relevant measurement error; screen-to-decision scale mapping and discordance; stochastic aggregation; or explicit complexity and data-quality tradeoffs. Do not create placeholder clauses for irrelevant gates.

The contract may choose a frequentist, Bayesian, predictive, decision-theoretic, or hybrid rule, but it must be interpretable for the scientific question. The smallest nominal p-value is never a default ranking rule.

Derive numerical eligibility, support, or comparison thresholds from scientific scale, design constraints, precision, power, recovery, or another declared operating characteristic before outcomes. If only a heuristic is possible, label it as such, examine reasonable alternatives, and do not tune it merely to retain or exclude available candidates, samples, or data families.

Here, population means the scientific target domain, system class, distribution, or ensemble—not a particular dataset split. Record concrete support with `supported_sample_id`; train/test or discovery/verification partitions may share one population when they sample the same target definition.

Substantive eligibility is a gate, not a post-result plausibility score. Declare each candidate type, such as mechanism, model, feature, simulation, or design. For mechanistic candidates, freeze `mechanism_alignment` as `direct`, `calibrated_proxy`, `diagnostic_only`, `unsupported`, or `not_assessed`. For a nonmechanistic scientific or operational decision, use `not_applicable` with a reason and apply the declared `substantive_eligibility` rule instead. Diagnostics and unsupported proxies remain in the record but cannot become a substantive leader through statistical strength alone.

When screening and decision evidence differ, freeze one mapping per distinct family and screening-statistic relation: both evidence definitions, estimands and scales, the scale relation, validation or calibration rule, and discordance rule. A rank statistic can support monotone association while remaining silent about raw-scale slope, calibration, residual structure, or predictive loss. Without a validated mapping, a screen may prioritize execution but cannot replace decision-scale evidence.

If the rule changes after outcome inspection, preserve the earlier version, record the trigger, and treat decisions affected by the change as exploratory unless a valid adaptive procedure already covered it. If no rule existed before outcomes were viewed, the first retrospective version is also outcome-informed; it cannot create a pre-result freeze retroactively.

## 2. Audit Prior Exposure

Before assigning an evidence stage, freeze a bounded exposure-audit scope: relevant projects or repositories, sources to inspect, overlap unit, date range or effort budget, available custodians or disclosures, and a completion rule. Then inspect the declared sources for:

- earlier analyses using the same or overlapping observations, participants, simulations, benchmarks, or labels;
- parameter, feature, sample, exclusion, threshold, model, seed, checkpoint, or formulation attempts;
- interim or final outcome views;
- earlier candidate selection, ranking, or reporting decisions;
- previous data splits or holdouts and whether they remained sealed;
- undocumented or uncertain exposure.

Record what was checked, unavailable sources, who or what supplied the information, overlap scope, known attempts, uncertain gaps, and the resulting evidence-stage restriction. Complete the declared audit when every available in-scope source was checked or the frozen effort bound was reached. Do not expand into unrelated project archaeology; unresolved relevant gaps become `unknown` rather than disappearing.

Keep the current evidence label separate from future verification eligibility. Exposed evidence remains exploratory or internal-only even when a prospectively frozen candidate could later be tested on genuinely untouched data.

Exposure follows the information, not the filename or tool. Changing the sample definition, codebase, model, repository, workflow, or skill version does not restore confirmatory status when overlapping outcome information influenced the new analysis. A formerly inspected holdout is not sealed again. When exposure cannot be reconstructed, label it `unknown` and do not claim pristine confirmation.

State what is independent: prior-result blinding, evidence or data, implementation, or review. A result-blind rerun may receive the frozen test specification and reuse validated parsers, data semantics or contracts, deterministic utilities, and tests when they do not encode outcome-informed scientific choices. It must not receive prior numeric outcomes, rankings, conclusions, or discretionary outcome-derived choices outside that specification. Disclose shared infrastructure and do not claim implementation independence unless it is real. Same-data blind reruns remain reproduction or internal validation; untouched-data verification may reuse software unless software independence is the target.

Classify exposure by decision relevance rather than treating every technical view as equivalent. Field names, schemas, and noncandidate operational metadata may be summarized as response-blind QA and do not ordinarily reopen the frozen scientific plan. Record isolated outcome information when it could plausibly affect a choice. Candidate features, effects, scores, ranks, selection states, or any other information that can guide generation, modification, screening, ranking, or promotion must enter the complete selection path and may require genuinely untouched evidence. Exposure relevance never restores status already lost through prior overlapping outcome access.

## 3. Define Comparable Selection Families

Candidates may be directly ranked only inside a justified selection family. Freeze a comparison key that includes, as applicable:

- scientific decision and target population;
- analysis unit, scientifically independent unit, dependence or grouping regime, and supported sample;
- estimand and outcome definition;
- data product, measurement regime, quality, and sensitivity;
- evidence stage;
- comparator and loss or utility scale.

Different target populations, supported samples, estimands, or materially different data quality are not directly comparable merely because they produce the same statistic. Either:

1. prespecify and validate a transport, standardization, calibration, or common predictive-loss mapping;
2. retain them as parallel conclusions; or
3. label a promising but noncomparable result `support_limited_candidate`.

Record the family fields separately rather than hiding them in an opaque key: target population, supported sample, estimand, data-quality regime, evidence stage, and transportability requirement and status. If analysis, selection, or reporting populations differ from the frozen target, validate the declared transport before a terminal ranking; otherwise report the result in parallel or as support limited. A result-inspired target change creates a new frozen rule version and cannot replace the original decision.

Do not create an artificial universal family across unrelated scientific decisions. Conversely, do not split one selection path into narrow families merely to avoid accounting for selection.

## 4. Cover the Complete Selection Path

The inferential target is the procedure that generated the reported result, not only its final test. The ledger must cover every outcome-dependent step that could affect:

- mechanism or model generation;
- formulation, feature, sample, scale, threshold, or parameter modification;
- screen passage or branch termination;
- ranking, retention, reporting, and promotion;
- choice of verification target or final claim.

Choose a strategy that is valid for that path and domain. Acceptable strategies include:

- a sealed holdout used once after all development choices are frozen;
- an end-to-end null or randomization procedure that reruns the complete search and selection pipeline;
- selective inference for the actual selection event;
- sequential or always-valid inference for prospectively governed repeated looks;
- hierarchical multiplicity control aligned with prespecified scientific families;
- Bayesian model comparison or model averaging with a declared candidate set, priors, likelihood, decision rule, and sensitivity analysis;
- another justified procedure with equivalent selection-path coverage.

No single global-null construction is mandatory for all domains. Document why the chosen strategy covers the actual selection path, what it does not cover, and how failed or invalid executions are handled. Bayesian analysis does not erase prior data exposure or an adaptively assembled model set.

## 5. Separate Scientific Coverage from Scheduling

A scheduler may use cost, expected information gain, dependency order, or feasibility to decide what runs next. It may also apply one or more prespecified low-cost screening stages within declared comparable screening families before deeper tests if:

- the screen and its threshold are frozen or explicitly governed adaptively;
- all screened candidates and outcomes enter the ledger;
- the screen's false-negative risk and sensitivity are assessed;
- passing the screen does not itself count as verification;
- candidates or tests not yet run remain open; in an explicit coverage task, their coverage cells stay `planned` or `resource_blocked`, never `covered`.

Priority is an execution property, not scientific evidence. When resources end, save the open candidate or test queue, dependencies, priority basis, and next admissible action. In explicit coverage, do not shrink the inventory or coverage denominator. In bounded outcome-guided work, report the current scientific state rather than implying saturation.

Ordinary changes to workers, chunking, cache placement, scheduling, or an equivalent implementation do not enter the scientific record merely because they occurred during a search. Apply the frozen execution-equivalence gate. Enter them in the selection path only when scientific outcomes motivated the change in a way that could alter which candidate was run, retained, ranked, or reported, or when the equivalence gate failed and scientific values or decision semantics may have changed.

## 6. Decide Conservatively

At decision time:

1. exclude candidates that fail substantive alignment, required measurement-error sensitivity, support, or transportability gates, without erasing them;
2. compare only within frozen, justified selection families;
3. apply the declared selection-path inference;
4. use the frozen ranking, tie, and inconclusive rules;
5. preserve parallel or support-limited conclusions outside the comparison family;
6. report sensitivity to reasonable contract, prior, model, and data-quality choices;
7. distinguish exploratory preference, internally validated evidence, and independent verification.

Record candidate-level outcomes in the compact board or an equivalent table. Summarize outcome classes in prose and link the complete table rather than narrating every branch. If evidence does not separate eligible candidates by the declared rule, report `tie` or `inconclusive`; if none pass, use `no_eligible_candidate`.
