# Governed Evidence Acceptance Contract

## A. Acceptance Authority

`ValidationEvidenceEvaluator` is the canonical authority for validation evidence
acceptance. It may evaluate one bound raw validation result against one sealed
reference and produce one `EvidenceDecision`. It may create `AcceptedEvidence`
only when that decision authorizes `ACCEPTED`.

No report renderer, telemetry stream, route predictor, task selector, planner,
arena, metric, or persistence layer may declare evidence accepted.

## B. Required Inputs

Acceptance requires:

- `claim_id` and canonical `claim_subject`
- evidence plan identity
- validation schedule identity
- raw validation result identity
- raw validation result envelope with bound provenance
- comparable result identity
- governed `evidence_decision_id`
- acceptance-authorizing decision state
- source provenance from the raw validation producer
- run/reference context

Missing authority-bearing identity or provenance fails closed.

## C. Canonical Identities

Claim identity is derived by the existing claim identity contract. Evidence
decision identity is derived from the evaluated plan, schedule, raw result,
comparable result, and evaluation contract. Accepted evidence identity is derived
from the authorized decision fingerprint, evidence plan, and raw result.

These identities are distinct and must not be substituted for each other.

## D. Provenance Requirements

Accepted evidence must preserve raw validation producer provenance, including
producer component, source type, producer operation, validation attempt, raw
validation result id, run id, task id, schedule id, and plan id.

Accepted evidence must bind to the same canonical claim as the evidence plan and
the evidence decision.

## E. Acceptance Eligibility

Acceptance is eligible only when:

- the raw result is structurally eligible and provenance-bound
- comparison completed under a persisted evaluation contract
- an authoritative evidence decision exists
- the decision state is `ACCEPTED`
- admissibility is `ADMISSIBLE`
- sufficiency is `SUFFICIENT`
- claim binding can be rebuilt and verified

Metrics may inform the decision. Metrics alone are not acceptance authority.

## F. Rejection Semantics

Supported terminal decision states are `ACCEPTED`, `INSUFFICIENT`, and
`REJECTED`. Invalid or unresolved inputs do not silently become rejected
evidence; they block acceptance and remain non-accepted.

## G. Persistence Semantics

Persistence records state. It does not grant acceptance. A stored raw result,
comparison, decision, or legacy artifact is accepted only when the governed
decision and accepted-evidence binding are valid.

## H. Current-Run vs Historical Semantics

Current-run acceptance is a fresh governed decision and accepted artifact created
for the current plan/run/schedule/raw result. Historical accepted evidence may be
read, but it is not a new current-run acceptance event. Historical artifacts
without the completed contract remain legacy/pre-contract evidence.

## I. Downstream Consumer Contract

Downstream epistemic consumers may consume only bound accepted evidence. They may
not infer acceptance from raw results, comparison metrics, persisted files, high
scores, or successful validation alone.

## J. Fail-Closed Behavior

Acceptance fails closed on missing claim identity, claim mismatch, missing
decision identity, non-accepting decision, broken provenance, invalid source
identity, cross-run mismatch, duplicate conflicting accepted artifact, or any
attempt to directly grant truth/trust/graduation/execution authority.

## K. Forbidden Authority Paths

Forbidden paths include:

- raw result directly to accepted evidence
- evaluated comparison directly to accepted evidence
- persisted artifact directly to accepted evidence
- accepted evidence directly to truth commitment
- report rendering to evidence acceptance
- telemetry or metric threshold to evidence acceptance
- route prediction or task selection to evidence acceptance

## L. Lifecycle Invariants

Evidence binding, evidence production, evidence evaluation, evidence decision,
evidence acceptance, truth eligibility, and truth commitment are separate states.

`AcceptedEvidence` must point to exactly one authoritative `EvidenceDecision`.
Source identity and source independence remain provenance-derived and are not
created by accepted evidence identity, run identity, or task identity.
