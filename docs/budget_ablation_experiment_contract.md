# NEXRYN Budget Ablation Experiment Contract

## Status

```text
PHASE: BUDGET_ABLATION
MODE: SCREENING_ABLATION_FIRST
PRODUCTION_DEFAULT_ROUTES: 2
PRODUCTION_DEFAULT_DEPTH: 2
PRODUCTION_POLICY_MUTATION: FORBIDDEN
RUNTIME_AUTHORITY_CHANGE: NO
ADAPTIVE_BUDGET_IMPLEMENTATION: NO
```

The ablation harness observes budget policy outcomes. It does not become part
of production budget policy and does not grant authority to evidence, truth,
candidate selection, graduation, execution, or reporting.

## Screening Matrix

```text
1/1
1/2
2/1
2/2
2/3
3/2
3/3
4/4
```

The `2/2` configuration is the governed control baseline. Full factorial
ablation is not justified until screening shows reproducible marginal gain.

## Controlled Variables

Every screening run must hold these variables fixed across configurations:

- task set
- task order
- seed
- execution mode
- report policy
- code checkpoint

The task set is materialized once before any configuration executes. Each
configuration must receive the same frozen task identities in the same order:

```text
T_1/1 = T_1/2 = T_2/1 = T_2/2 = T_2/3 = T_3/2 = T_3/3 = T_4/4
```

The seed alone is not sufficient evidence of task-set equality because runtime
randomness may be consumed in different orders under different budget limits.

## Experimental Provenance

Each experiment records non-authoritative provenance:

```text
experiment_id
code_checkpoint
task_set_fingerprint
seed
config
repeat_id
```

The `task_set_fingerprint` identifies the frozen task identities used for the
screening run. The `experiment_id` identifies the measurement context and must
change when the repeat, seed, code checkpoint, report policy, execution mode,
screening matrix, or task-set fingerprint changes.

These fields are experimental evidence labels only. They do not grant runtime
authority and do not mutate production budget defaults.

## Required Per-Task Measurements

Each task/configuration result records:

- experiment identity, repeat identity, and task-set fingerprint
- task identity and task signature
- route and depth budgets
- requested, admitted, and peak active routes
- requested, entered, and completed reasoning depth
- accuracy, final score, and success state
- exact success, recoverable failure, and routing overload flags
- repair attempts, repair successes, and residual count
- wall time and active compute time when available
- realized overrun and reachability gap count

Unavailable metrics are reported as `UNAVAILABLE`. The harness must not
fabricate missing measurements.

## Decision Rule

The screening phase reports primary metrics separately. It does not collapse
them into one opaque composite score.

Budget comparisons are dimension-isolated:

```text
ROUTE_EFFECT:
1/2 -> 2/2
2/2 -> 3/2

DEPTH_EFFECT:
2/1 -> 2/2
2/2 -> 2/3

COUPLED_EFFECT:
2/2 -> 3/3
2/2 -> 4/4
```

The preferred policy is minimal sufficient cognition:

```text
choose the smallest budget whose quality meets the accepted threshold
```

No production policy change may be made from a single unrepeated screening
signal.
