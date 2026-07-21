# Decision, Exposure, and Selection Protocol

Use this protocol for `adaptive_search` and `coverage_search`: whenever a run generates, modifies, screens, compares, ranks, retains, or promotes candidates. A genuinely prespecified `fixed_test` does not need this protocol; if its result motivates another choice, preserve that result and upgrade the run before continuing. This protocol prevents a broad search from becoming an implicit contest for the smallest p-value.

## 1. Freeze a Decision Contract

Before candidate-specific outcomes are inspected, write `decision_contract.json`. Define:

- the decision that the search is intended to support;
- the target, analysis, selection, and reporting populations;
- the candidate classes eligible for that decision;
- the substantive eligibility rule applied before statistical ranking;
- the measurement-error policy, including the pathway that makes a sensitivity analysis required, or a reason it is not applicable;
- the transportability requirement when populations differ, the evidence needed to pass it, or a reason no transport claim is made;
- the selection families within which candidates may be compared;
- the evidence used for eligibility, ranking, falsification, and promotion;
- the mapping from a screening statistic to the decision or prediction scale when those evidence roles differ, including what happens when they disagree;
- the decision rule that maps that evidence to an action or status;
- the estimand and minimum scientifically meaningful difference;
- how uncertainty, robustness, predictive adequacy, mechanistic specificity, complexity, and data quality enter the decision;
- the tie or practical-equivalence rule;
- the inconclusive rule and the action it triggers;
- the treatment of candidates that are not mutually comparable;
- the complete-selection-path inference strategy;
- the freeze time, version, and conditions under which the contract may be amended.

The contract may choose a frequentist, Bayesian, predictive, decision-theoretic, or hybrid rule, but it must be interpretable for the scientific question. The smallest nominal p-value is never a default ranking rule.

Here, population means the scientific target domain, system class, distribution, or ensemble—not a particular dataset split. Record concrete support with `supported_sample_id`; train/test or discovery/verification partitions may share one population when they sample the same target definition.

Substantive eligibility is a gate, not a post-result plausibility score. Declare each candidate type, such as mechanism, model, feature, simulation, or design. For mechanistic candidates, freeze `mechanism_alignment` as `direct`, `calibrated_proxy`, `diagnostic_only`, `unsupported`, or `not_assessed`. For a nonmechanistic scientific or operational decision, use `not_applicable` with a reason and apply the declared `substantive_eligibility` rule instead. Diagnostics and unsupported proxies remain in the record but cannot become a substantive leader through statistical strength alone.

When screening and decision evidence differ, freeze one `evidence_scale_mapping` record per distinct family and screening-statistic relation: both statistics or models, their estimands and scales, the scale relation, the validation or calibration rule, and the discordance rule. A family may have multiple records for genuinely different screening statistics, but each `(selection_family_id, screening_statistic)` pair must have exactly one mapping. When there is no selection-influencing screen, use one compact `not_applicable` record with a reason instead of manufacturing full mapping work. A rank statistic can support monotone association while remaining silent about raw-scale slope, calibration, residual structure, or predictive loss. Unless a prespecified mapping is validated, a screen may prioritize execution but cannot substitute for the decision-scale test. Preserve disagreements and apply the frozen tie, inconclusive, parallel, or rejection rule rather than selecting whichever scale looks favorable.

If the contract changes after outcome inspection, preserve the earlier version, record the trigger, mark the change `post_result_adaptive`, and treat decisions affected by the change as exploratory unless a valid adaptive procedure already covered it. If no contract existed before outcomes were viewed, the first retrospective contract is also `post_result_adaptive`; it cannot create a pre-result freeze retroactively.

## 2. Audit Prior Exposure

Before assigning an evidence stage, write `prior_exposure_audit.json`. Search project records, notebooks, reports, issue histories, code, logs, prior runs, and available human disclosures for:

- earlier analyses using the same or overlapping observations, participants, simulations, benchmarks, or labels;
- parameter, feature, sample, exclusion, threshold, model, seed, checkpoint, or formulation attempts;
- interim or final outcome views;
- earlier candidate selection, ranking, or reporting decisions;
- previous data splits or holdouts and whether they remained sealed;
- undocumented or uncertain exposure.

Record what was checked, who or what supplied the information, overlap scope, known attempts, uncertain gaps, and the resulting evidence-stage restriction.

Keep the current evidence label separate from future verification eligibility. Exposed evidence remains exploratory or internal-only even when a prospectively frozen candidate could later be tested on genuinely untouched data.

Exposure follows the information, not the filename or tool. Changing the sample definition, codebase, model, repository, workflow, or skill version does not restore confirmatory status when overlapping outcome information influenced the new analysis. A formerly inspected holdout is not sealed again. When exposure cannot be reconstructed, label it `unknown` and do not claim pristine confirmation.

## 3. Define Comparable Selection Families

Candidates may be directly ranked only inside a justified selection family. Freeze a comparison key that includes, as applicable:

- scientific decision and target population;
- unit of analysis and supported sample;
- estimand and outcome definition;
- data product, measurement regime, quality, and sensitivity;
- evidence stage;
- comparator and loss or utility scale.

Different target populations, supported samples, estimands, or materially different data quality are not directly comparable merely because they produce the same statistic. Either:

1. prespecify and validate a transport, standardization, calibration, or common predictive-loss mapping;
2. retain them as parallel conclusions; or
3. label a promising but noncomparable result `support_limited_candidate`.

Record the family fields separately rather than hiding them in an opaque key: target population, supported sample, estimand, data-quality regime, evidence stage, and transportability requirement and status. If analysis, selection, or reporting populations differ from the frozen target, validate the declared transport before a terminal ranking; otherwise report the result in parallel or as support limited. A result-inspired target change creates a new Decision Contract version and cannot replace the original decision.

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
- candidates or tests not yet run remain open; in `coverage_search`, their coverage cells stay `planned` or `resource_blocked`, never `covered`.

Priority is an execution property, not scientific evidence. When resources end, save the open candidate or test queue, dependencies, priority basis, and next admissible action. In `coverage_search`, do not shrink the inventory or coverage denominator. In `adaptive_search`, report a bounded stage rather than implying saturation.

## 6. Decide Conservatively

At decision time:

1. exclude candidates that fail substantive alignment, required measurement-error sensitivity, support, or transportability gates, without erasing them;
2. compare only within frozen, justified selection families;
3. apply the declared selection-path inference;
4. use the Decision Contract's ranking, tie, and inconclusive rules;
5. preserve parallel or support-limited conclusions outside the comparison family;
6. report sensitivity to reasonable contract, prior, model, and data-quality choices;
7. distinguish exploratory preference, internally validated evidence, and independent verification.

Write the candidate-level outcomes to `candidate_registry.csv` and set the run manifest's `decision_contract_applied` and terminal `decision_status`. If evidence does not separate eligible candidates by the declared rule, report `tie` or `inconclusive`. If none pass eligibility, use `no_eligible_candidate`. Do not force a winner for narrative convenience.
