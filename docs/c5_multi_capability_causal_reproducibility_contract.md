# C5 Multi-Capability Causal Reproducibility Contract

## Purpose
C5 defines a bounded study-grade claim that independently replicated causal validation is demonstrated across multiple exact capability-operation subjects.

## Scope
C5 is not a runtime promotion mechanism and does not execute a campaign. It defines the future contract only.

## Hierarchy
- C1: controlled causal path.
- C2: natural single-context causal validation.
- C3: natural multi-task causal validation.
- C4: exact-subject independent causal replication.
- C5: multi-subject causal reproducibility.

## Exact Subject
`ExactSubject = (capability_id, capability_operation, qualification_claim_id)`.
This preserves the C4 identity model.

## Evidence Unit
The atomic C5 evidence unit is one exact subject with C4 passed. Artifacts, tasks, sources, runs, and scores are not C5 units.

## Distinctness
Subject distinctness is exact-subject distinctness. Capability distinctness is canonical `capability_id`. If one capability has multiple operations, those are multiple subjects but one capability unless the canonical capability identity differs.

## Thresholds
Future C5 requires a frozen target set with at least 3 exact subjects, at least 3 canonical capability IDs, at least 2 distinct operations, and at least 2 proven independent causal sources per subject.

## Source Rules
Each subject must independently satisfy C4. Global source diversity is additionally required as a concentration guard: at least 3 unique canonical source lineages across the campaign and no source-independence inflation.

## Context Rules
Each subject should have at least 2 validation contexts. This is a C5 contract requirement for the future campaign, but it cannot replace source independence.

## Domain Rules
C5 is multi-capability, not multi-domain. Cross-domain generalization is a future contract, not part of C5.

## Causal Rules
Subjects may use operation-appropriate causal estimands under a shared causal-support ontology. Identical instrumentation is not required; valid counterfactuals and governed causal support are required.

## Qualification Rules
Every counted subject must be `REPRODUCIBLY_SUPPORTED` through existing governed qualification. Causally demonstrated but non-reproducible subjects do not count.

## Target Set Rules
The C5 target subject set must be pre-registered before execution. Failed subjects cannot be removed after outcomes are known except for audited contract invalidity, identity corruption, proven architectural unreachability, or eligibility misclassification.

## Failure Semantics
Allowed outcomes are `C5_MULTI_CAPABILITY_REPRODUCIBILITY_PROVEN`, `C4_ONLY_INSUFFICIENT_SUBJECT_BREADTH`, `C4_ONLY_SUBJECT_REPLICATION_MIXED`, `C4_ONLY_SOURCE_DIVERSITY_INSUFFICIENT`, `C4_ONLY_TARGET_SET_NOT_FULLY_REPLICATED`, `ARCHITECTURAL_INTEGRATION_DEFECT_FOUND`, and `CONTRACT_INVALIDATED`.

## Authority
Per-subject qualification remains owned by `IntegratedCapabilityQualificationEngine`. C5 aggregate authority is `OBSERVATION_ONLY` and must not mutate runtime capability state.

## Forbidden Inferences
C5 does not imply general intelligence, broad generalization, learning, transfer, truth completeness, production safety, or execution authority.

## Future Protocol
Freeze the C5 contract, freeze the target set, run natural validation campaigns without synthetic downstream object creation, assess each subject against C4, apply negative controls, and aggregate only over C4-qualified exact subjects.
