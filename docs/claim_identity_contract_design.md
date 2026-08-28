# NEXRYN Claim Identity Contract Design

## Status

```text
PHASE: CLAIM_IDENTITY_CONTRACT_DESIGN
BASELINE: 21ee8b5
CLAIM_IDENTITY_PRIMITIVES: CLOSED
IMPLEMENTATION: MINIMAL_CONTRACT_PRIMITIVES_ONLY
RUNTIME_BINDING: NO
NEW_ENGINE: NO
CLAIM_IDENTITY_NAMESPACE: CREATED_BY_DETERMINISTIC_CONTRACT_ONLY
AUTHORITY_SURFACE: UNCHANGED
IMPLEMENTATION_CONFORMANCE: PASSED_BY_GOLDEN_VECTORS
```

This document defines the design boundary for the minimal claim identity
contract. The current implementation is limited to `ClaimSubject`
canonicalization and deterministic `claim_id` derivation. It does not introduce
runtime binding, persistence, authority, or a new cognitive engine.

The primitive implementation is considered conformant when focused golden-vector
tests prove canonical bytes, `claim_id` derivation, fail-closed validation,
cross-run reference restrictions, and identity stability under caller-side
mutation.

## Constitutional Rule

```text
ClaimIdentity identifies.
ClaimEvidenceBinding projects.
Evidence/Truth systems decide.
```

Claim identity equality means two records refer to the same canonical semantic
subject. It does not transfer authority between evidence, arena, truth, trust,
graduation, compilation, execution, or deployment stages.

```text
Claim Identity Equality != Authority Equality
Evidence Binding != Evidence Acceptance
Evidence Acceptance != Truth Eligibility
Truth Eligibility != Truth Commitment
```

## Design Goal

Create the smallest stable identity contract that can connect existing NEXRYN
primitives without replacing them:

- candidate and arena hypotheses
- evidence acquisition plans
- raw validation result provenance
- evidence decisions and accepted evidence artifacts
- concept and truth governance records
- confidence and authority states produced by their owning systems

The contract must describe what the system currently knows about a claim. It
must not decide whether the claim is true.

## Non-Goals

- Do not create a `ClaimToEvidenceEngine`.
- Do not grant evidence acceptance, truth eligibility, truth commitment, trust,
  graduation, candidate selection, execution, compilation, or deployment
  authority.
- Do not infer claim equivalence from shared text, shared concept, shared task,
  shared operation, or lifecycle proximity alone.
- Do not reuse `candidate_id`, `evidence_plan_id`, `raw_validation_result_id`,
  `evidence_decision_id`, `accepted_evidence_id`, `concept_id`, or `truth_id`
  as the canonical claim identity.
- Do not make claim binding mutable lifecycle state owned by the binding layer.

## ClaimSubject Schema

`ClaimSubject` is the canonical semantic input to claim identity derivation.
It is not a runtime artifact and does not own lifecycle transitions.

```text
ClaimSubject
  schema_version: "1.0"
  kind: one of
    candidate_operation
    concept_truth
    capability_statement
    contextual_assertion
  semantic_scope: one of
    task
    run
    cross_run
    global
  subject_ref: optional stable semantic reference string
  operation: optional normalized operation string
  normalized_statement: optional normalized statement string
  qualifiers: optional sorted key/value map
```

Minimum field requirements:

| kind | required fields | notes |
| --- | --- | --- |
| `candidate_operation` | `semantic_scope`, `subject_ref`, `operation` | `subject_ref` is usually a candidate reference, not a truth identity. If the reference is run-local, the claim cannot be reused outside that run without an explicit durable semantic reference. |
| `concept_truth` | `semantic_scope`, `subject_ref`, `normalized_statement` | `subject_ref` is a concept reference when available. |
| `capability_statement` | `semantic_scope`, `subject_ref`, `normalized_statement` | Use only for capability-level assertions, not candidate outcomes. |
| `contextual_assertion` | `semantic_scope`, `normalized_statement`, `qualifiers` | Qualifiers must carry the context boundary. |

`subject_ref` must identify the semantic subject, not merely the artifact that
first mentioned it. Artifact-local identifiers may participate in provenance,
but they are not sufficient for cross-run or global claim reuse unless a
governed derivation binds them to a durable semantic reference.

When a claim's meaning depends on conditions, input domain, expected behavior,
or operating context, those terms must appear in `qualifiers`. Two subjects with
the same `subject_ref` and `operation` are not identical if their omitted
conditions would change the claim being made.

## Canonicalization Contract

The future canonicalizer must be deterministic:

1. Trim leading and trailing whitespace.
2. Normalize internal whitespace to a single ASCII space.
3. Normalize enum-like values to lowercase snake case.
4. Normalize operation names with the existing operation vocabulary where one
   exists.
5. Sort qualifier keys lexicographically.
6. Drop empty optional fields.
7. Serialize with the byte-level rules below.
8. Reject ambiguous subjects instead of inventing missing identity.

Canonical bytes are defined as follows:

1. Normalize every string value to Unicode NFC before any hashing.
2. Emit UTF-8 encoded JSON.
3. Emit object keys in lexicographic order by normalized key string.
4. Emit no insignificant whitespace. Separators are exactly `,` and `:`.
5. Omit absent optional fields and fields whose normalized value is empty.
6. Treat explicit `null` for optional fields as absent.
7. Reject explicit `null` for required fields.
8. Preserve list order only when the list is semantically ordered.
9. Sort semantically unordered lists by their canonical JSON representation.
10. Preserve booleans as JSON `true` and `false`.
11. Avoid floating-point values in `ClaimSubject`. If a future field requires a
    numeric value, its canonical representation must be specified before the
    field can participate in identity.
12. Do not include runtime timestamps, file paths, object memory addresses,
    process-local counters, or other execution-local values.

The v1 `ClaimSubject` schema does not define any semantically ordered list
field. Lists inside `qualifiers` are therefore treated as unordered sets for
identity purposes. A future ordered list field must update this contract before
it can participate in `claim_id` derivation.

The stable identity form is:

```text
claim_id = claim_sha256_<64 lowercase hex chars>
```

The digest input is the canonical JSON representation of `ClaimSubject`.
`schema_version` participates in the canonical payload. A major schema version
change creates a new identity namespace unless a future migration contract
explicitly maps old and new canonical forms.

Collision handling is fail-closed. If two non-identical canonical
`ClaimSubject` payloads ever resolve to the same `claim_id`, the system must
report `CLAIM_ID_COLLISION_DETECTED`, refuse to merge the records, and require a
governed migration or namespace revision.

## Identity Relation Classes

Every relation between existing identities and `claim_id` must be classified
explicitly:

```text
DIRECT_IDENTITY
EXPLICIT_DERIVATION
REFERENCE_TO
SHARED_SOURCE
SEMANTIC_OVERLAP_ONLY
NO_PROVEN_RELATION
```

Allowed meanings:

| relation | meaning |
| --- | --- |
| `DIRECT_IDENTITY` | Two records carry the same claim identity under this contract. |
| `EXPLICIT_DERIVATION` | One identity is deterministically derived from the other through a governed rule. |
| `REFERENCE_TO` | A record points at another artifact or semantic subject without becoming identical to it. |
| `SHARED_SOURCE` | Records share a producer, run, task, or upstream artifact only. |
| `SEMANTIC_OVERLAP_ONLY` | Records look related by concept, text, operation, or task but lack governed linkage. |
| `NO_PROVEN_RELATION` | No reliable relation is established. |

No relation may be upgraded by naming similarity alone.

## Current Identity Inventory

| Identity | Current semantic object | Claim relation |
| --- | --- | --- |
| `candidate_id` | Arena candidate or program hypothesis | `REFERENCE_TO` or `SEMANTIC_OVERLAP_ONLY` |
| `target_candidate` | Evidence target candidate reference | `REFERENCE_TO` |
| `target_operation` | Evidence target operation reference | `REFERENCE_TO` |
| `evidence_plan_id` | Durable evidence acquisition plan | `REFERENCE_TO` |
| `raw_validation_result_id` | Captured raw validation artifact | `REFERENCE_TO` |
| `evidence_decision_id` | Evidence evaluation decision | `REFERENCE_TO` |
| `accepted_evidence_id` | Accepted evidence artifact | `REFERENCE_TO` |
| `concept_id` | Cognitive concept identity | `SEMANTIC_OVERLAP_ONLY` unless linked |
| `truth_id` | Truth governance record identity | `REFERENCE_TO` after explicit claim linkage only |

## Cross-Run Reuse Rules

Reuse of a `claim_id` across runs is allowed only when canonicalized
`ClaimSubject` is identical, every subject reference used for reuse is stable at
that scope, and no authority boundary is crossed.

Allowed:

- The same candidate-operation subject recurs in another run with identical
  canonical subject fields and a durable semantic reference that survives both
  runs.
- A concept-truth subject is re-evaluated with identical semantic scope and
  normalized statement.
- Evidence from multiple runs references the same claim subject as support,
  contradiction, or inconclusive evidence.

Forbidden:

- Treating shared `claim_id` as proof that evidence is accepted.
- Treating shared `claim_id` as proof that truth eligibility was evaluated.
- Treating shared `claim_id` as proof that a truth was committed.
- Merging candidate-operation and concept-truth claims solely because they share
  a concept or operation.
- Reusing a run-local candidate, task, or plan reference as a cross-run claim
  subject without explicit governed derivation.

## ClaimEvidenceBinding Projection

A future binding record should be an immutable projection over existing records.

```text
ClaimEvidenceBinding
  schema_version: "1.0"
  claim_id
  claim_subject
  evidence_refs
  provenance_refs
  authority_observations
  confidence_observations
  next_governed_gate
  source_records
```

The binding may report:

- which evidence references the claim
- which provenance records connect the claim to evidence or truth artifacts
- which subsystem produced each authority state
- current confidence metrics produced by existing owners
- the next governed gate

The binding must not:

- accept evidence
- mark evidence sufficient
- create truth candidates
- commit truth
- select arena winners
- authorize execution
- mutate source artifacts

## Authority State Projection

Authority state must be structured and source-attributed. It is an observation
about decisions made elsewhere, not a decision made by the binding.

Each authority observation has the following shape:

```text
AuthorityObservation
  state
  source_authority
  source_record_id
  grants_authority: false
```

Example `state` values:

```text
EVIDENCE_REFERENCED
EVIDENCE_ACCEPTED
EVIDENCE_SUFFICIENT
TRUTH_ELIGIBILITY_NOT_EVALUATED
TRUTH_CANDIDATE_CREATED
TRUTH_COMMITTED
```

Every value must include its source authority. For example, evidence acceptance
must point to the validation evidence evaluator, and truth commitment must point
to truth governance. The binding layer is never the source authority for those
states, and `grants_authority` must remain `false`.

## Confidence State Projection

Confidence is a projection over existing metrics, not a new score owner.
`confidence_observations` is intentionally plural because different owners may
produce non-equivalent confidence values.

Possible inputs:

- evidence confidence, reliability, completeness
- evidence sufficiency and direction
- promotion score
- eligibility score
- candidate confidence
- commit score
- mastery score

If multiple confidence values exist, the binding may show them as a structured
set. It must not collapse them into one authoritative truth score unless a
future owner explicitly defines that aggregation outside this binding layer.

## Adversarial Review Checklist

Reject the design or implementation if any answer is yes:

- Does `ClaimIdentity` grant or imply evidence acceptance?
- Does `ClaimEvidenceBinding` create truth candidates or commit truth?
- Does shared `claim_id` cause authority to propagate across systems?
- Does canonicalization depend on timestamps, mutable lifecycle state, or
  artifact-local IDs alone?
- Does cross-run reuse depend on a run-local candidate, task, or plan reference
  without governed derivation?
- Does the design infer equivalence from shared concept, task, operation, or
  text without governed linkage?
- Does the binding mutate source evidence, arena, or truth records?
- Does it hide the owning authority for an evidence or truth state?
- Does any authority or confidence field read like a binding-owned decision
  rather than a source-attributed observation?

## Implementation Gate

Implementation may start only after this document is accepted and the following
are frozen:

```text
ClaimSubject schema
Canonicalization rules
Identity relation classes
Cross-run reuse rules
Authority non-propagation invariants
Adversarial review checklist
```

Preferred future implementation shape:

```text
dataclass ClaimSubject
deterministic canonicalizer
claim_id derivation helper
projection-only ClaimEvidenceBinding serializer
focused tests for identity stability and authority non-propagation
```
