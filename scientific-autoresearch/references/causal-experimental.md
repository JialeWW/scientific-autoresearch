# Causal and Experimental Adapter

Use this adapter for causal language, interventions, randomized or quasi-experimental studies, longitudinal designs, human or animal records, or experimental data.

## 1. Separate Claim Types

- Association: quantities vary together in the supported sample.
- Mechanism-consistency: direction, scale, controls, and predictions fit a mechanism but do not identify causality.
- Causal effect: an intervention or exposure changes an outcome under explicit identification assumptions.
- Mechanistic necessity or sufficiency: stronger claims requiring targeted interventions or decisive predictions.

If identification is not justified, use association or mechanism-consistency language.

## 2. Define the Causal Estimand

Record:

- target population and unit of inference;
- time zero and assignment mechanism;
- intervention or exposure and relevant versions;
- comparator;
- outcome and time horizon;
- intercurrent events and missing outcomes;
- effect measure and summary population;
- identification assumptions.

Separate identification from estimation. Address exchangeability, positivity, consistency, interference, temporal ordering, selection, and missingness as relevant. Predeclare confounders and distinguish them from mediators and colliders. Check overlap and sensitivity to unmeasured confounding.

Do not adjust mechanically for every available covariate. Do not treat post-treatment variables as ordinary baseline confounders.

## 3. Audit Experimental Design

For experimental records or protocol design, specify:

- experimental unit and unit of inference;
- biological versus technical replicates;
- sample-size, precision, or power rationale;
- random allocation and allocation concealment;
- blinding of intervention, measurement, and analysis where possible;
- positive, negative, sham, vehicle, baseline, and process controls as applicable;
- batch, order, site, operator, instrument, reagent, lot, and environmental effects;
- protocol version, deviations, exclusions, and stopping rules;
- instrument calibration, reagent or model-system identity, contamination checks, and raw-record linkage;
- adverse-event, humane, biosafety, and containment boundaries when applicable.

Analyze according to the frozen design before exploring alternate exclusions, subgroups, endpoints, or covariate sets.

## 4. Require Governance for Live or Regulated Work

Read `references/governance-safety.md`. Do not independently execute, expand, or modify live human, animal, clinical, field, wet-lab, hazardous, or dual-use procedures. Require documented authorization, an approved protocol, and competent human oversight.

Preserve the approved primary analysis as the primary result. Treat subgroup, endpoint, model, or protocol variants chosen after inspection as exploratory and require independent verification.

## 5. Falsify Causal and Mechanistic Explanations

Use controls that distinguish competing explanations, such as negative-control outcomes or exposures, placebo timing, pre-trend checks, balance and overlap diagnostics, dose or timing predictions, mediation tests with justified assumptions, intervention specificity, or novel predictions beyond fitted data.

State what each result would imply under the claim and under its main alternative. A robustness variant that leaves the estimate unchanged is not automatically a mechanistic falsifier.

## 6. Report Boundaries

State what is measured, what is identified only under assumptions, what is mechanism-consistent, and what remains speculative. Report protocol deviations, missingness, harms or adverse signals, sensitivity analyses, and whether evidence is internal, holdout-verified, or independently replicated.
