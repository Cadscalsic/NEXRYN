# Integrated Capability Qualification Contract

## A. CapabilitySubject

`CapabilitySubject` is the semantic object being qualified. It identifies a
capability by stable semantic fields such as `capability_name`, `operation`,
`domain`, and optional `qualifiers`.

It is not a run, task, accepted evidence artifact, claim, metric, score, or
truth object.

## B. capability_id

`capability_id` is derived deterministically from the canonical
`CapabilitySubject` payload. The same capability subject yields the same
`capability_id`; different subjects yield different IDs.

Evidence IDs and run/task IDs are never part of capability identity.

## C. Canonical Qualification Levels

The canonical levels are:

- `ARCHITECTURALLY_PRESENT`
- `RUNTIME_REACHABLE`
- `OPERATIONALLY_OBSERVED`
- `CAUSALLY_DEMONSTRATED`
- `REPRODUCIBLY_SUPPORTED`

`NOT_QUALIFIED` is the initial non-qualified state, and `UNDER_REVIEW` /
`QUALIFICATION_INVALIDATED` are review states.

## D. Qualification Authority

The only authority for qualification state transitions is the integrated
capability qualification engine.

Telemetry, report rendering, metric thresholds, raw validation results,
evaluation results, task counts, run counts, truth promotion, and persisted
state files have no qualification authority.

## E. Qualification Decision Contract

A `QualificationDecision` must include:

- `qualification_decision_id`
- `capability_id`
- `current_level`
- `requested_level`
- `granted_level`
- `decision_state`
- `accepted_evidence_ids`
- `independent_source_count`
- `causal_support_state`
- `reproducibility_state`
- `decision_reason`
- `authority`
- `created_at`

## F. Accepted Evidence Requirements

Qualification may consume only governed accepted evidence. Accepted evidence
must have an accepted state, decision identity, bound claim evidence binding,
claim ID, accepted evidence ID, and valid source provenance.

Raw results, evaluation reports, rejected evidence, unaccepted artifacts,
telemetry, and historical unbound artifacts cannot qualify a capability.

## G. Source Independence

Source independence is delegated to the existing source independence engine.

New runs, tasks, artifacts, and accepted evidence IDs do not by themselves
create independent sources.

## H. Causal Evidence Requirements

`CAUSALLY_DEMONSTRATED` requires at least one governed accepted evidence item
whose causal support state is causally supported. Observation or reachability
alone cannot cross this boundary.

## I. Reproducibility Requirements

`REPRODUCIBLY_SUPPORTED` requires causal support plus the configured minimum
number of proven independent supporting sources. The default requirement is
two independent sources for capability qualification.

## J. Promotion Rules

Promotion is monotonic only when every semantic requirement for the requested
level and lower levels is satisfied.

Higher levels are not granted merely because they are the next level, because a
metric is high, or because a single strong event occurred.

## K. Invalidation / Review Semantics

Contradictory evidence, revoked evidence, invalid provenance, failed
reproducibility, or capability regression results in denied promotion and may
place a capability under review. Complex demotion policy is outside this
minimal contract.

## L. Persistence Semantics

The engine may persist qualification decisions and current qualification state.
Persistence records what the authority decided; persistence alone cannot grant
qualification.

Current state is selected by `capability_id` and the latest authoritative
decision for that capability.

## M. Downstream Consumption Contract

Qualification artifacts are observational or advisory unless a separate
pre-existing governed consumer contract grants a narrow behavior.

They do not grant truth, knowledge commitment, runtime execution authority,
identity authority, route admission, planner priority, or budget authority.

## N. Forbidden Authority Paths

Forbidden paths include:

- raw result directly to qualification
- evaluation directly to qualification
- metric threshold directly to qualification
- task count or run count as source independence
- accepted evidence directly to truth through qualification
- persisted state without qualification decision authority

## O. Fail-Closed Behavior

Promotion must fail closed on missing capability identity, missing accepted
evidence, invalid accepted evidence, claim/capability mismatch, invalid
provenance, missing decision identity, insufficient causality, insufficient
independence, historical/current ambiguity, or missing qualification authority.

## P. Lifecycle Invariants

Capability presence, reachability, observation, causality, and reproducibility
are distinct. Accepted evidence is necessary for governed qualification but is
not sufficient for every level. Qualification is not truth, knowledge,
confidence, trust, runtime authority, or budget authority.
