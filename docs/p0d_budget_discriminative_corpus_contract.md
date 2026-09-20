# P0d Budget Discriminative Corpus Contract

Status: Gate 1-4 design artifact, no baseline probe executed.

## Scientific Question

P0d asks when additional route or reasoning-depth capacity begins to produce a
reproducible quality effect across broader cognitive demand. It does not assume
one globally optimal budget.

Primary relation under investigation:

`B_min = f(CognitiveDemand)`

This is experimental metadata and measurement design only. It is not production
routing authority.

## Hypotheses

- H0: Quality remains effectively budget-invariant over the tested legal domain.
- H1_ROUTE: Some tasks benefit from additional route capacity at fixed depth.
- H1_DEPTH: Some tasks benefit from additional reasoning depth at fixed route count.
- H1_COUPLED: Some tasks benefit only when route and depth increase together.
- H1_SATURATION: Quality improves up to a capacity level and then stops.
- H1_DILUTION: Additional realized search activity degrades search or task quality.

Dilution cannot be inferred from wall-time increase alone.

## Corpus Inventory

Inventory source: `data/training`.

Executable candidate count: 402 JSON tasks with ARC-style `train` and `test`
sections.

Inventory provenance uses task content plus explicit `nexryn_metadata` when
present. Missing cognitive characteristics remain `UNKNOWN`; they are not
encoded as `FALSE`.

## Cognitive Demand Dimensions

Each dimension uses `LOW`, `MEDIUM`, `HIGH`, or `UNKNOWN` and must carry
`value`, `evidence`, `source`, and `confidence`.

- `route_demand`
- `depth_demand`
- `transformation_composition`
- `candidate_ambiguity`
- `repair_pressure`
- `program_dependency`
- `semantic_novelty`
- `cross_concept_interaction`

The demand profile is experimental metadata only. It must not enter identity
governance, truth promotion, concept promotion, production routing, or production
budget allocation.

## Selected Frozen Corpus

Selected task count: 16.

Task-set fingerprint:
`task_set_sha256_8c2866577f2aaf43d1c67ea8f1842cc9b63535cc3b8ca31f507c03a98c0dc662`

The fingerprint is based on stable task id plus file content SHA256 and is
independent of temporary root, absolute path, experiment directory, and execution
order.

| Stratum | Task id | File | Family | Evidence summary |
| --- | --- | --- | --- | --- |
| LOW | arc_concept_color_mapping_01 | data/training/arc_concept_color_mapping_01.json | color_mapping | explicit metadata concept family plus train color transformation |
| LOW | arc_concept_rotation_reflection_01 | data/training/arc_concept_rotation_reflection_01.json | rotation_reflection | explicit metadata concept family and expected transformations |
| LOW | arc_concept_spatial_reasoning_01 | data/training/arc_concept_spatial_reasoning_01.json | spatial_reasoning | explicit spatial metadata plus observed train transformation |
| LOW | arc_concept_object_counting_01 | data/training/arc_concept_object_counting_01.json | object_counting | explicit object-counting metadata |
| LOW | arc_concept_pattern_completion_01 | data/training/arc_concept_pattern_completion_01.json | pattern_completion | explicit pattern-completion metadata |
| LOW | arc_concept_path_finding_01 | data/training/arc_concept_path_finding_01.json | path_finding | explicit path/route metadata |
| LOW | arc_concept_occlusion_masking_01 | data/training/arc_concept_occlusion_masking_01.json | occlusion_masking | explicit occlusion metadata |
| LOW | arc_concept_scaling_01 | data/training/arc_concept_scaling_01.json | scaling | explicit scaling metadata |
| MEDIUM | task_050.json | data/training/task_050.json | topology_exploration | phase-7 targeted topology metadata |
| MEDIUM | task_067.json | data/training/task_067.json | complex_symbolic_remapping | phase-7 symbolic remapping metadata |
| MEDIUM | task_077.json | data/training/task_077.json | causal_sequence | phase-7 causal sequence metadata |
| MEDIUM | task_101.json | data/training/task_101.json | density_scarcity | phase-7 scarcity/density metadata and higher transformation composition |
| HIGH | elite_cognitive_task_06 | data/training/elite_cognitive_task_06.json | capability_graduation | multi-step, multi-domain, program dependency, candidate ambiguity |
| HIGH | elite_cognitive_task_15 | data/training/elite_cognitive_task_15.json | composite_capability | multi-step, composite capability, program dependency, repair pressure |
| AMBIGUOUS_ADVERSARIAL | elite_cognitive_task_17 | data/training/elite_cognitive_task_17.json | elite_multi_domain | multiple valid solution strategies and six-domain composition |
| AMBIGUOUS_ADVERSARIAL | elite_cognitive_task_20 | data/training/elite_cognitive_task_20.json | elite_multi_domain | boss task metadata with candidate arena and validation pipeline concepts |

Known capability gaps before measurement:

- Candidate counts, route quality, search efficiency, repair attempts, and active
  compute are not available from static task inventory.
- Rotation/reflection/scaling are accepted only where explicit task metadata or
  transformation annotations support them.
- Frontier status remains a selection hypothesis until valid measurements exist.

## State Isolation Contract

Controlled state surfaces:

- `runtime/artifacts/runtime_data`
- `runtime/state/evidence_acquisition_plans`
- `runtime/memory`
- `memory`
- `runtime/cache`

S0 fingerprint before baseline probe:
`state_sha256_85b7f4d5f408abd25be9a24c14180c89769b0623ceaa2fab9b9d737e54ba0b06`

S0 snapshot root: `C:\tmp\amis_p0d_s0_20260830_095620`

S0 snapshot file count: 368.

Before every baseline measurement, restore S0 and verify this fingerprint. If
restoration or verification fails, mark the measurement invalid and stop.

No additional P0d mutable/read state surface is introduced by the design helpers.
If the measurement execution path later introduces one, stop before measurement
and report `STATE_CONTROL_CONTRACT_CHANGE_REQUIRED`.

## Budget Authority Contract

Production default remains:

- `max_active_routes = 2`
- `max_reasoning_depth = 2`

Experimental request:

- `authority = NONE`
- `persistent = FALSE`

Experimental grant:

- `authority = CURRENT_RUN_ONLY`
- `persistent = FALSE`
- `promotable = FALSE`

Accepted runtime authority source: `EXPERIMENTAL_BUDGET_GRANT`.

Every measurement must verify:

- `requested == granted == effective`
- realized route/depth usage is within effective experimental ceilings

## Telemetry Provenance

Realized resources must use only the repaired canonical collector:

- admitted routes: `RUNTIME_BUDGET_ENFORCEMENT_REPORT.admitted_route_count`
- peak concurrent routes: `RUNTIME_BUDGET_ENFORCEMENT_REPORT.peak_concurrent_active_route_count`
- maximum entered depth: `RUNTIME_BUDGET_ENFORCEMENT_REPORT.maximum_entered_reasoning_depth`
- maximum completed depth: `RUNTIME_BUDGET_ENFORCEMENT_REPORT.maximum_completed_reasoning_depth`
- active compute: `performance_report.active_compute_time_seconds`, then
  `runtime_summary.active_compute_time_seconds`, then
  `execution_timing_state.active_compute_time`, otherwise `UNAVAILABLE`

Wall time must not be substituted for active compute.

Primary quality metrics remain individually inspectable:

- `accuracy`
- `final_score`
- `success_state`
- `exact_success`
- `recoverable_failure`

Secondary diagnostics are collected only where canonically available:
`residual_count`, `repair_attempts`, `repair_successes`, `candidate_count`,
`unique_candidate_count`, `route_quality`, `search_efficiency`, `coverage`,
`program_generation_count`, `program_reuse_count`, `programs_executed`,
`arena_state`, `winner_state`, and `validation_state`.

## Screening Configurations

Initial coupled screening configs:

- `1/1`
- `2/2`
- `3/3`
- `4/4`

Repeat policy for the first baseline probe: one staged pass over the frozen
16-task corpus. Do not run the full 8-config x 5-repeat campaign unless Gate 5
detects a scientifically useful signal requiring reproducibility follow-up.

Dimension-isolated follow-up configs are authorized only after a signal:

- route: `1/2`, `2/2`, `3/2`
- depth: `2/1`, `2/2`, `2/3`

## Classification Rules

For every comparison, separate:

- capacity available
- capacity realized
- quality effect

If the effective budget increases but realized usage does not increase:
`MCV = NOT_EXPOSED`.

Only classify `ZERO_WITHIN_RESOLUTION` when realized route/depth activity
increases and quality remains unchanged within measurement resolution.

Allowed task classifications after valid measurement:

- `BUDGET_INVARIANT`
- `ROUTE_SENSITIVE`
- `DEPTH_SENSITIVE`
- `COUPLED_SENSITIVE`
- `SATURATION_OBSERVED`
- `NEGATIVE_MARGINAL_VALUE`
- `CAPACITY_NOT_EXPOSED`
- `MIXED`
- `INCONCLUSIVE`

Search dilution classifications:

- `NO_DILUTION_EVIDENCE`
- `POSSIBLE_DILUTION_SIGNAL`
- `REPRODUCED_DILUTION_SIGNAL`
- `NOT_EXPOSED`
- `INCONCLUSIVE`

## Stop Conditions

Stop and preserve evidence if any of the following occurs:

- production budget policy changes
- experimental authority contract changes
- collector contract changes
- task content changes
- task-set fingerprint changes
- state-control contract changes
- canonical telemetry source changes
- runtime behavior requires a patch
- new invalid measurement class appears
- measurement driver reconstructs observed usage from ceilings
- active compute is substituted with wall time

Do not patch during the experiment.

## Phase Gates

- Gate 1: `CORPUS_INVENTORY_COMPLETE`
- Gate 2: `COGNITIVE_DEMAND_PROFILE_DESIGNED`
- Gate 3: `DISCRIMINATIVE_CORPUS_FROZEN`
- Gate 4: `STATE_AND_AUTHORITY_CONTRACT_VERIFIED`
- Gate 5: `SMALL_BASELINE_PROBE_COMPLETED`

Large reproducibility run authorization remains `NO` until Gate 5 evidence
justifies it.

## Production Non-Mutation Rule

P0d must not alter production budget policy. Even if `1/1` matches production
quality, or `3/3`/`4/4` improves quality, the result becomes a scientific
decision artifact first, not an automatic policy mutation.
