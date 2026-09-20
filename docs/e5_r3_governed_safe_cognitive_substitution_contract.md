# E5.R3 Governed Safe Cognitive Substitution Contract

## 1. E5.R3 Status

```text
E5_R3_STATUS: CLOSED_FOR_DESIGN
MODE: DESIGN_ONLY
PRODUCTION_CODE_PATCHED: NO
SHORT_CIRCUIT_EXECUTION_ENABLED: NO
EXECUTION_AUTHORITY_CHANGED: NO
SELECTOR_POLICY_CHANGED: NO
HIGHEST_PROVEN_LEARNING_LEVEL: L4
DESIGN_DECISION_GATE: E5.R3-C
```

## 2. Design Justification

E5.R2 established that NEXRYN has reuse signals but no canonical owner for the
transition from reusable cognitive material to skipped downstream cognition.
This contract creates that missing scheduling boundary without turning reuse
confidence, historical success, arena eligibility, or validation output into
execution authority.

`CognitiveSubstitutionDecision` is a current-run scheduling artifact only. It
may admit omission of specific redundant cognitive stages when reuse is
exactly compatible, semantically complete, applicable, conflict-free, and
bound to the current task. It cannot authorize execution, truth, evidence,
budget, validation, arena bypass, identity promotion, or future-run reuse.

## 3. Contract Owner

```text
OWNER: runtime.cognition.cognitive_substitution_policy.CognitiveSubstitutionPolicy
CALL_SITE: runtime.pipeline.legacy_pipeline.AdaptiveCognitivePipeline.run
PRODUCER_INPUT: adaptive reuse report plus current task/run context
CONSUMER: CognitivePipelineOrchestrator.execute through typed should_skip hook
```

The owner should be a new narrow policy object. `AdaptiveReuseEngine` remains a
reuse signal producer. `AdaptiveCognitivePipeline.run` remains the production
scheduling coordinator and should call the policy after adaptive reuse
evaluation and before stage execution. `CognitivePipelineOrchestrator.execute`
should consume the typed decision through its existing skip hook; it should not
invent substitution policy.

Input contract:

- Current run identity, current task identity, current task input context, and
  current stage.
- Reuse candidate identity and source experience identity.
- Reuse report fields, including executable payload and arena eligibility when
  available.
- Semantic completeness, exact compatibility, applicability, conflict, prior
  outcome, and optional validation observations.
- Stage cost estimate only as advisory metadata.

Output contract:

- `CognitiveSubstitutionDecision` with `scheduling_authority =
  LIMITED_COGNITIVE_STAGE_ADMISSION`.
- `execution_authority = NONE`, `validation_authority = NONE`,
  `arena_authority = NONE`, `truth_authority = NONE`, `evidence_authority =
  NONE`, `identity_authority = NONE`, and `budget_authority = NONE`.
- Per-stage decisions: `RUN`, `SKIP_BY_SAFE_SUBSTITUTION`,
  `SKIP_BY_EXISTING_POLICY`, or `NOT_APPLICABLE`.

## 4. State Machine

```text
NO_REUSE
  -> REUSE_AVAILABLE
  -> REUSE_SEMANTICALLY_COMPLETE
  -> REUSE_APPLICABILITY_PENDING
  -> REUSE_SUFFICIENT_FOR_SUBSTITUTION
  -> SUBSTITUTION_ADMITTED

REUSE_AVAILABLE
  -> REUSE_NOT_SUFFICIENT
  -> FALLBACK_TO_NORMAL_COGNITION

REUSE_APPLICABILITY_PENDING
  -> REUSE_CONFLICT_DETECTED
  -> SUBSTITUTION_REJECTED
  -> FALLBACK_TO_NORMAL_COGNITION

REUSE_APPLICABILITY_PENDING
  -> REUSE_NOT_SUFFICIENT
  -> FALLBACK_TO_NORMAL_COGNITION
```

Forbidden direct transition:

```text
REUSE_AVAILABLE -> SUBSTITUTION_ADMITTED
```

Only `SUBSTITUTION_ADMITTED` may produce `SKIP_BY_SAFE_SUBSTITUTION`, and only
for explicitly substitutable stages.

## 5. Required Inputs

| Input | Classification | Reason |
| --- | --- | --- |
| reuse candidate identity | REQUIRED | Decision must name the materialized candidate. |
| source experience identity | REQUIRED | Historical source must remain traceable. |
| exact semantic compatibility | REQUIRED | Operation-name equality is insufficient. |
| executable parameter completeness | REQUIRED | Operation-only reuse cannot skip cognition. |
| parameter provenance validity | REQUIRED | Parameters must be original, governed learning data. |
| prior outcome class | REQUIRED | Failure, rejected, or unknown outcomes cannot support positive substitution. |
| current task applicability | REQUIRED | Scheduling sufficiency is current-run specific. |
| conflict status | REQUIRED | Conflict must be observed before suppression. |
| candidate materialization status | REQUIRED | Nothing may be skipped for an absent candidate. |
| current run and task identity | REQUIRED | No cross-run scheduling authority reuse. |
| current cognitive stage | REQUIRED | Decision is per-stage, not global. |
| validation status if available | OPTIONAL | Useful telemetry, but not a validation bypass. |
| arena admission eligibility if applicable | OPTIONAL | Candidate admission signal, not arena bypass. |
| stage cost estimate | OPTIONAL | Budget metadata only. |
| reuse confidence alone | NOT_ALLOWED | Confidence is not authority. |
| repeated experience count alone | NOT_ALLOWED | Repetition cannot create applicability. |
| persisted substitution decision | NOT_ALLOWED | Prior decisions have no future-run authority. |

## 6. Exact Compatibility Contract

`is_exact_reuse_compatible(source_experience, reuse_candidate, current_task)`
is true only when all canonical semantic dimensions match or are positively
proven compatible:

- Same normalized operation type.
- Same parameter mapping, including source and target values.
- Same object and value bindings needed by the operation.
- Same structural constraints required for correctness.
- Current task input satisfies the source experience applicability predicate.
- Source experience semantics and current task semantics have no unresolved
  divergence.

For `replace_color`, compatibility distinguishes `1 -> 2` from `1 -> 3`.
Matching only `replace_color` is `SEMANTIC_OVERLAP_ONLY` and cannot admit
substitution.

## 7. Applicability Contract

`ReuseApplicabilityAssessment` must emit exactly one class:

```text
APPLICABLE
NOT_APPLICABLE
CONFLICT
INSUFFICIENT_INFORMATION
UNKNOWN
```

Only `APPLICABLE` may advance toward substitution. Every other class maps to
`FALLBACK_TO_NORMAL_COGNITION` and does not fail the task.

## 8. Conflict Gate

Conflict must be checked before any stage is skipped:

```text
conflict_detected = TRUE
  -> substitution_admitted = FALSE
  -> normal cognition continues
```

Known negative case:

```text
source experience: replace_color 1 -> 2
current task: replace_color 1 -> 3
result: CONFLICT, FALLBACK_TO_NORMAL_COGNITION
```

## 9. Semantic Completeness Gate

Required:

- Operation present.
- Executable parameters present.
- Parameter provenance valid.
- Candidate payload materialized.

Operation-only reuse is `REUSE_NOT_SUFFICIENT`. Missing parameters,
untrusted parameter provenance, or absent executable payload produces
`FALLBACK_TO_NORMAL_COGNITION`. The policy must not guess parameters.

## 10. Prior Outcome Policy

| Prior outcome | Substitution policy |
| --- | --- |
| `SUCCESS` | May qualify after all current-run gates pass. |
| `PARTIAL_SUCCESS` | Not sufficient by default. |
| `FAILURE` | Never sufficient for positive substitution. |
| `INVALID_OUTCOME` | Reject. |
| `GOVERNANCE_REJECTED` | Reject. |
| `UNKNOWN` | Reject. |

Prior outcome is a scheduling input only. It never grants execution authority.

## 11. Validation Boundary

Substitution may skip only redundant cognitive construction stages after reuse
semantic sufficiency, applicability, and conflict status are proven. Required
validation and qualification remain independent and must still occur before
any execution authority is granted.

Substitution is not validation bypass.

## 12. Arena Boundary

The arena does not own search admission and the substitution policy does not
own arena bypass. Substitution may reduce candidate generation, broad search,
synthesis, or repair exploration. Any candidate that proceeds through an arena
governed path must still satisfy the arena contract where applicable.

```text
reuse_sufficient != arena_bypass
```

## 13. Budget Interface

Normal cognition budget:

```text
B_normal =
    retrieval
  + search
  + synthesis
  + repair
  + validation
  + execution
```

Substitution-requested budget:

```text
B_substitution =
    retrieval
  + applicability
  + required validation
  + execution
```

`CognitiveSubstitutionDecision` may reduce requested stages. It cannot grant
budget, increase budget, override budget denial, or admit execution when the
budget system rejects the remaining requested work.

## 14. Stage-Skip Matrix

| Stage | Decision under safe substitution | Notes |
| --- | --- | --- |
| candidate generation | `SKIP_BY_SAFE_SUBSTITUTION` when exact candidate is sufficient | Otherwise `RUN`. |
| broad search | `SKIP_BY_SAFE_SUBSTITUTION` when exact compatibility is proven | Otherwise `RUN`. |
| synthesis | `SKIP_BY_SAFE_SUBSTITUTION` when reusable candidate is semantically complete | Otherwise `RUN`. |
| repair exploration | `SKIP_BY_SAFE_SUBSTITUTION` when no conflict and prior success is complete | Otherwise `RUN`. |
| required validation | `RUN` | Non-substitutable. |
| governance checks | `RUN` | Non-substitutable. |
| qualification | `RUN` | Non-substitutable. |
| fresh E4 grant | `RUN` | Non-substitutable. |
| current budget admission | `RUN` | Non-substitutable. |
| arena where applicable | `RUN` | Non-substitutable unless existing arena policy says otherwise. |

## 15. Orchestrator Interface

The orchestrator should consume a typed decision, not a raw boolean:

```text
should_skip(stage, context, substitution_decision)
```

Required decision fields:

```text
decision_id
decision_version
current_run_id
current_task_id
source_experience_id
reuse_candidate_id
stage
stage_decision
reason
applicability_assessment
semantic_completeness
exact_compatibility
conflict_status
provenance
authority = STAGE_SCHEDULING_ONLY
```

`CognitivePipelineOrchestrator.execute` may record skipped stage telemetry, but
policy ownership remains in `CognitiveSubstitutionPolicy`.

## 16. Fail-Open Semantics

When substitution cannot be proven safe, normal cognition continues:

- Uncertainty -> normal cognition.
- Conflict -> normal cognition.
- Missing parameters -> normal cognition.
- Invalid provenance -> normal cognition.
- Unsupported operation -> normal cognition.
- Stale or copied decision -> normal cognition.

Fail-open here means opening the normal cognition path. It does not mean
opening execution.

## 17. Negative Transfer Protection

The policy protects against:

- Stale parameters.
- Wrong parameter mapping.
- Superficially similar operation.
- Partial semantic match.
- Low-confidence or repeated-only experience.
- Hidden conflict.
- Cross-task or cross-run copied decision.

No substitution is admitted unless current applicability is positively proven.

## 18. Current-Run Binding

Every decision must bind:

```text
current_run_id
current_task_id
current_task_input_fingerprint
reuse_candidate_id
source_experience_id
applicability_assessment
semantic_completeness
conflict_result
decision_version
decision_timestamp_or_logical_clock
```

No decision may be replayed across runs or tasks. A new run must produce a new
decision from current inputs.

## 19. Persistence Policy

Substitution decisions may be persisted as telemetry of runtime scheduling.
Persisted records have:

```text
authority = NONE_FOR_FUTURE_RUNS
replay_authority = NONE
execution_authority = NONE
```

A historical substitution decision is evidence that a prior schedule occurred;
it is not an instruction for a future run.

## 20. Observability Contract

Telemetry fields:

```text
substitution_considered
substitution_decision
decision_id
candidate_id
experience_id
current_run_id
current_task_id
applicability
semantic_completeness
exact_compatibility
conflict
stages_skipped
stages_retained
estimated_cost_avoided
realized_cost_avoided
fallback_reason
authority = OBSERVATION_ONLY
behavioral_authority = NONE
```

These fields are required for later L5 causality experiments and must not
become runtime authority.

## 21. Authority Attack Matrix

| Attack | Required response |
| --- | --- |
| forged substitution decision | Reject decision; normal cognition. |
| wrong run | Reject decision; normal cognition. |
| wrong task | Reject decision; normal cognition. |
| wrong experience | Reject decision; normal cognition. |
| wrong candidate | Reject decision; normal cognition. |
| stale decision | Reject decision; normal cognition. |
| copied decision | Treat as telemetry only; no authority. |
| altered decision | Reject by fingerprint/signature mismatch. |
| incomplete parameters | No substitution. |
| conflict hidden | No substitution unless conflict check is complete. |
| historical success used as execution authority | Reject authority escalation. |
| substitution decision reused as grant | Reject; only E4 grant may authorize execution. |

## 22. Full Contract Chain

| Edge | Owner | Authority |
| --- | --- | --- |
| Experience -> ReuseCandidate | `AdaptiveReuseEngine` / adaptive reuse layer | Observation and candidate materialization only. |
| ReuseCandidate -> SemanticCompleteness | `CognitiveSubstitutionPolicy` | Scheduling assessment only. |
| SemanticCompleteness -> ApplicabilityAssessment | `CognitiveSubstitutionPolicy` | Scheduling assessment only. |
| ApplicabilityAssessment -> ConflictCheck | `CognitiveSubstitutionPolicy` | Scheduling assessment only. |
| ConflictCheck -> CognitiveSubstitutionDecision | `CognitiveSubstitutionPolicy` | `LIMITED_COGNITIVE_STAGE_ADMISSION`. |
| CognitiveSubstitutionDecision -> PipelineStageAdmission | `AdaptiveCognitivePipeline.run` | Stage scheduling only. |
| PipelineStageAdmission -> RemainingRequiredCognition | `CognitivePipelineOrchestrator` | Executes or skips declared stages. |
| RemainingRequiredCognition -> Validation/Qualification | Existing validation owners | Validation authority unchanged. |
| Validation/Qualification -> Arena if applicable | Existing arena owners | Arena authority unchanged. |
| Arena -> Fresh E4 Grant | Learned-object execution authority owner | E4 execution grant authority only. |
| Fresh E4 Grant -> BudgetAdmission | Existing budget owner | Budget authority unchanged. |
| BudgetAdmission -> ProductionExecution | `ExecutableIntelligenceEngine` | Execution only with fresh E4 grant. |

## 23. Execution Authority Isolation

```text
CognitiveSubstitutionDecision cannot authorize
ExecutableIntelligenceEngine.execute_production.
```

Only `LearnedObjectExecutionGrant` may carry current-run execution authority.
Historical success, reuse sufficiency, validation telemetry, arena eligibility,
or skipped cognitive stages cannot substitute for the grant.

## 24. Budget Authority Isolation

Substitution may reduce requested cognitive stages. It cannot:

- Increase budget.
- Grant budget.
- Override budget denial.
- Convert saved cost into new execution permission.
- Admit execution when the remaining budget path is denied.

## 25. Epistemic Authority Isolation

Successful reuse does not automatically become:

- Accepted evidence.
- Truth candidate.
- Canonical knowledge.
- Promoted identity.
- Claim-evidence binding.

Substitution is runtime scheduling only.

## 26. Comparable-Quality Baseline Design

Future L5 experiment:

```text
Baseline S:
  no target experience
  normal cognition
  reaches correct result

Treatment R:
  target experience
  safe substitution
  reaches same correct result

Promotion condition:
  C_R < C_S
  Q_R >= Q_S
```

The baseline must be a successful normal-cognition path. Comparing successful
reuse against a failing or non-comparable control cannot support L5.

## 27. Proposed Module Placement

```text
proposed_file: runtime/cognition/cognitive_substitution_policy.py
dataclasses:
  ReuseApplicabilityAssessment
  CognitiveSubstitutionDecision
  PipelineStageAdmission
producer: CognitiveSubstitutionPolicy.evaluate(...)
consumer: AdaptiveCognitivePipeline.run -> CognitivePipelineOrchestrator.execute
```

The placement belongs in `runtime/cognition` because the object owns cognitive
stage admission, not adaptive reuse retrieval, arena selection, validation,
budgeting, or execution.

## 28. Test Plan

Required implementation tests:

1. Exact compatible reuse -> substitution admitted.
2. Operation-only reuse -> normal cognition.
3. Wrong parameters -> normal cognition.
4. Conflict `1 -> 2` vs `1 -> 3` -> normal cognition.
5. Invalid provenance -> normal cognition.
6. Prior failure -> no positive substitution.
7. Stale decision in new run -> rejected.
8. Copied decision -> no authority.
9. Fresh E4 grant still required.
10. Budget denial still blocks execution.
11. Arena semantics unchanged.
12. Validation semantics unchanged.
13. Skipped stages observable.
14. Uncertainty fail-open verified.

## 29. Implementation Scope

Allowed later:

- Add narrow policy dataclasses.
- Add deterministic compatibility and applicability predicates.
- Wire typed stage-skip decisions through existing orchestrator hooks.
- Add telemetry for skipped and retained stages.

Forbidden:

- Enabling execution shortcut from reuse.
- Changing validation, arena, selector, budget, or E4 authority semantics.
- Treating confidence, repetition, or historical success as authority.
- Claiming L5 before a comparable successful baseline experiment.

## 30. Design Decision Gate

```text
E5.R3-C
SAFE_SUBSTITUTION_CONTRACT_FULLY_SPECIFIED
```

The architecture can support safe substitution if the later implementation is
kept to a narrow current-run stage scheduling policy and all authority
boundaries above remain enforced.

## 31. Next Action

Proceed to implementation only as a separate repair phase. The next phase
should implement `runtime/cognition/cognitive_substitution_policy.py` and its
focused tests, then wire it into the production scheduling path without
altering execution authority, validation, arena, selector policy, or budget
ownership.
