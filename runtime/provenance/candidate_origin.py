"""Observation-only provenance for the candidate handed to repair."""

from __future__ import annotations

from typing import Any, Mapping


OBSERVATION_AUTHORITY = "OBSERVATION_ONLY"
NO_BEHAVIORAL_AUTHORITY = "NONE"
UNKNOWN = "UNKNOWN"
NOT_OBSERVABLE = "NOT_OBSERVABLE"


def _public_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _public_value(item)
            for key, item in value.items()
            if isinstance(item, (str, int, float, bool, type(None), Mapping))
        }
    return str(value)


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def build_candidate_origin_report(
    *,
    producer_component: str,
    producer_operation_id: str | None = None,
    parent_candidate_id: str | None = None,
    candidate_id: str = "current_candidate",
    program_id: str | None = None,
    strategy_id: str | None = None,
    learned_object_id: str | None = None,
    learned_object_type: str | None = None,
    reuse_proposal_id: str | None = None,
    retrieval_source: str | None = None,
    transformation_source: str | None = None,
    prediction_source: str | None = None,
    source_report: Mapping[str, Any] | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Build a non-authoritative report for a produced prediction candidate."""

    source_report = source_report if isinstance(source_report, Mapping) else {}
    return {
        "system": "candidate_origin_provenance",
        "report_state": "OBSERVED",
        "authority": OBSERVATION_AUTHORITY,
        "behavioral_authority": NO_BEHAVIORAL_AUTHORITY,
        "candidate_id": str(candidate_id or "current_candidate"),
        "producer_component": str(producer_component or UNKNOWN),
        "producer_operation_id": producer_operation_id or UNKNOWN,
        "parent_candidate_id": parent_candidate_id,
        "program_id": program_id,
        "strategy_id": strategy_id,
        "learned_object_id": learned_object_id or program_id or strategy_id,
        "source_learned_object_id": learned_object_id or program_id or strategy_id,
        "learned_object_type": learned_object_type,
        "reuse_proposal_id": reuse_proposal_id,
        "retrieval_source": retrieval_source,
        "transformation_source": transformation_source,
        "prediction_source": prediction_source,
        "run_id": run_id,
        "task_id": task_id,
        "source_report_summary": {
            key: _public_value(source_report.get(key))
            for key in sorted(source_report)
            if key
            in {
                "status",
                "executed_steps",
                "strategy_count",
                "transformation_confidence",
                "transformation_complexity",
                "execution_aborted",
                "hypothesis_count",
                "reasoning_depth",
                "raw_reasoning_depth",
                "reasoning_depth_limit",
                "global_confidence",
                "prediction_accuracy",
                "accuracy",
                "prediction_source",
            }
        },
    }


def build_current_candidate_origin_report(
    *,
    context: Mapping[str, Any] | None,
    residual_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project the origin visible at the repair handoff."""

    context = context if isinstance(context, Mapping) else {}
    residual_evidence = (
        residual_evidence if isinstance(residual_evidence, Mapping) else {}
    )
    origin = context.get("candidate_origin_report")
    origin = origin if isinstance(origin, Mapping) else {}
    candidate_id = str(
        _first_present(
            residual_evidence.get("source_candidate_id"),
            origin.get("candidate_id"),
            context.get("candidate_id"),
            "current_candidate",
        )
    )
    observed = bool(origin)
    return {
        "system": "current_candidate_origin_report",
        "report_state": "OBSERVED" if observed else "ORIGIN_NOT_OBSERVABLE",
        "authority": OBSERVATION_AUTHORITY,
        "behavioral_authority": NO_BEHAVIORAL_AUTHORITY,
        "candidate_id": candidate_id,
        "current_candidate_handoff_observed": True,
        "construction_observable": observed,
        "producer_component": origin.get("producer_component", NOT_OBSERVABLE),
        "producer_operation_id": origin.get("producer_operation_id", NOT_OBSERVABLE),
        "parent_candidate_id": origin.get("parent_candidate_id"),
        "program_id": origin.get("program_id"),
        "strategy_id": origin.get("strategy_id"),
        "learned_object_id": origin.get("learned_object_id"),
        "source_learned_object_id": origin.get("source_learned_object_id"),
        "learned_object_type": origin.get("learned_object_type"),
        "reuse_proposal_id": origin.get("reuse_proposal_id"),
        "retrieval_source": origin.get("retrieval_source"),
        "transformation_source": origin.get("transformation_source"),
        "prediction_source": origin.get("prediction_source"),
        "run_id": _first_present(origin.get("run_id"), context.get("run_id")),
        "task_id": _first_present(origin.get("task_id"), context.get("task_id")),
        "handoff_evidence": {
            "source_candidate_id": residual_evidence.get("source_candidate_id"),
            "source_execution_id": residual_evidence.get("source_execution_id"),
            "prediction_accuracy": residual_evidence.get("prediction_accuracy"),
            "structural_score": residual_evidence.get("structural_score"),
            "residual_difference_count": residual_evidence.get(
                "residual_difference_count"
            ),
            "residual_type": residual_evidence.get("residual_type"),
            "validation_state": residual_evidence.get("validation_state"),
        },
        "origin_report": dict(origin) if origin else None,
    }
