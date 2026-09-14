# Governed Causal Validation Evidence Contract

This contract defines the minimum evidence path for treating validation output
as causal support for a capability-operation qualification claim.

## Scope

The path answers whether a target capability operation materially caused a
validated outcome. It does not grant truth, budget, production execution,
task-selection, or qualification authority.

## Method

The initial governed method is `CONTROLLED_TRANSFORMATION_EFFECT`.

The unit of analysis is one sandbox validation case with:

- identical input for treatment and control
- identical non-target operations
- treatment execution of the target operation
- control/counterfactual with only the target operation removed or disabled
- same evaluation contract for treatment and control

## Causal Support

`CAUSALLY_SUPPORTED` requires all of the following:

- target capability id is present
- qualification claim id is present
- target operation is explicit
- target operation executed
- target operation output was consumed
- counterfactual is valid
- treatment and control use the same input
- treatment and control preserve non-target operations
- control is not an unrelated candidate
- measured treatment effect is greater than or equal to the contract minimum

Validation success, accepted evidence, task success, accuracy, or an operation
label alone are not causal support.

## Authorities

`ValidationTaskExecutionPipeline` may produce a raw causal validation result in
sandbox validation scope.

`CausalValidationEvidenceEvaluator` owns causal support classification and has
`CAUSAL_VALIDATION_EVIDENCE_EVALUATOR` authority only.

`ValidationEvidenceEvaluator` owns evidence acceptance.

`IntegratedCapabilityQualificationEngine` owns qualification decisions and only
consumes accepted causal evidence after governed acceptance.

## Artifact

A causal evidence artifact includes:

- `causal_evidence_id`
- `capability_id`
- `operation`
- `qualification_claim_id`
- `validation_request_id`
- `evidence_plan_id`
- `validation_execution_id`
- `treatment_execution_id`
- `counterfactual_id`
- treatment and control outcomes
- `causal_effect`
- `causal_support_state`
- source provenance
- authority fields

## Invariants

Accepted evidence may remain non-causal.

Causal evidence may come from a dependent source.

N10 eligibility remains downstream of qualification reassessment and source
independence accounting.
