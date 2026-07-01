"""Stores validated executable programs for later reuse."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from runtime.meta.supervisor.program_memory import (
    ProgramMemory,
    ProgramRecord,
    program_memory,
)
from runtime.meta.supervisor.task_signature_engine import task_signature_engine


VALIDATED_SUCCESS_STATES = {
    "EXACT_SUCCESS",
    "SUCCESS_WITH_RESIDUALS",
}

MIN_PROMOTABLE_PARTIAL_ACCURACY = 0.95
MAX_PROMOTABLE_RESIDUALS = 1


def remember_validated_program(
    context: Mapping[str, Any] | None,
    memory: ProgramMemory | None = None,
) -> dict[str, Any]:
    """Persist a reusable program only after evidence says it worked."""

    context = context if isinstance(context, Mapping) else {}
    memory = memory or program_memory
    program = context.get("synthesized_program")
    if not isinstance(program, Mapping) or not _program_steps(program):
        return _skipped("missing_synthesized_program")

    evaluation = context.get("evaluation_result")
    evaluation = evaluation if isinstance(evaluation, Mapping) else {}
    accuracy = _number(evaluation.get("accuracy"))
    success_state = str(evaluation.get("success_state") or "")
    residual_count = _residual_count(context, evaluation)
    semantic_contradictions = _semantic_contradictions(context)
    success_ok = (
        success_state in VALIDATED_SUCCESS_STATES
        or evaluation.get("exact_success") is True
        or (evaluation.get("success") is True and accuracy >= 0.97)
    )
    near_success_candidate = (
        success_state == "LEARNING_PROGRESS"
        and accuracy >= MIN_PROMOTABLE_PARTIAL_ACCURACY
        and residual_count <= MAX_PROMOTABLE_RESIDUALS
        and not semantic_contradictions
    )
    if not success_ok and not near_success_candidate:
        return _skipped(
            "evaluation_not_validated_for_program_reuse",
            accuracy=accuracy,
            success_state=success_state,
            residual_count=residual_count,
            semantic_contradictions=semantic_contradictions,
        )

    integrity = context.get("execution_integrity_report")
    integrity = integrity if isinstance(integrity, Mapping) else {}
    if integrity.get("integrity_preserved") is not True:
        return _skipped("execution_integrity_not_verified")

    task_signature = task_signature_engine.build_signature(context)
    signature_id = task_signature.stable_id()
    operation_sequence = _operation_sequence(
        program,
        context.get("execution_plan"),
    )
    concept = _concept_from_context(context, operation_sequence)
    sanitized_program = _json_safe(dict(program))
    if concept and isinstance(sanitized_program, dict):
        sanitized_program.setdefault("concept", concept)
    family_id = _program_family_id(
        sanitized_program,
        operation_sequence,
        concept,
    )
    promotion_evidence = _promotion_evidence(
        memory,
        family_id,
        signature_id,
    )
    should_promote_candidate = (
        near_success_candidate
        and
        len(promotion_evidence) >= 1
    )
    if near_success_candidate and not should_promote_candidate:
        validation_state = "candidate"
    elif (
        success_state == "EXACT_SUCCESS"
        or evaluation.get("exact_success") is True
    ):
        validation_state = "stable"
    else:
        validation_state = "validated"

    record = ProgramRecord(
        program_id=_program_id(signature_id, sanitized_program, operation_sequence),
        task_signature_id=signature_id,
        program=sanitized_program,
        operation_sequence=operation_sequence,
        match_confidence=_confidence(accuracy, context),
        validation_state=validation_state,
        integrity_verified=True,
        stale=False,
        metadata={
            "concept": concept,
            "accuracy": accuracy,
            "residual_count": residual_count,
            "success_state": success_state,
            "task_signature": task_signature.as_dict(),
            "program_family_id": family_id,
            "promotion_evidence": [
                *promotion_evidence,
                signature_id,
            ],
            "semantic_contradictions": semantic_contradictions,
            "source": "evaluation_stage",
        },
    )
    memory.remember(record)
    if should_promote_candidate:
        _promote_family_candidates(
            memory,
            family_id,
            [
                *promotion_evidence,
                signature_id,
            ],
        )
    return {
        "program_memory_updated": True,
        "program_id": record.program_id,
        "task_signature_id": signature_id,
        "validation_state": record.validation_state,
        "integrity_verified": True,
        "operation_count": len(operation_sequence),
        "concept": concept,
        "program_family_id": family_id,
        "promotion_evidence_count": len(
            set(
                [
                    *promotion_evidence,
                    signature_id,
                ]
            )
        ),
        "promotion_rule": (
            "cross_task_near_success"
            if should_promote_candidate
            else "exact_or_validated_success"
            if success_ok
            else "candidate_near_success"
        ),
    }


def _program_steps(program: Mapping[str, Any]) -> list[Any]:
    steps = program.get("steps") or program.get("program_steps") or []
    return steps if isinstance(steps, list) else []


def _operation_sequence(
    program: Mapping[str, Any],
    execution_plan: Any,
) -> list[dict[str, Any]]:
    sequence = []
    for index, step in enumerate(_program_steps(program)):
        if not isinstance(step, Mapping):
            continue
        operation = step.get("operation") or step.get("operator")
        if operation:
            sequence.append(
                {
                    "index": index,
                    "operation": str(operation),
                    "parameters": _json_safe(step.get("parameters", {})),
                }
            )
    if sequence:
        return sequence

    if isinstance(execution_plan, Mapping):
        nodes = execution_plan.get("nodes", [])
        if isinstance(nodes, list):
            for node in nodes:
                if not isinstance(node, Mapping):
                    continue
                operation = node.get("operation") or node.get("operator")
                if operation:
                    sequence.append(
                        {
                            "index": int(node.get("execution_index", len(sequence))),
                            "operation": str(operation),
                            "parameters": _json_safe(node.get("parameters", {})),
                        }
                    )
    return sequence


def _concept_from_context(
    context: Mapping[str, Any],
    operation_sequence: list[Mapping[str, Any]],
) -> str:
    for key in ("semantic_concept", "concept"):
        value = context.get(key)
        if isinstance(value, str) and value:
            return value

    abstractions = context.get("semantic_abstractions", [])
    if isinstance(abstractions, list):
        for item in abstractions:
            if not isinstance(item, Mapping):
                continue
            concept = item.get("semantic_concept") or item.get("concept")
            if isinstance(concept, str) and concept:
                return concept

    winner = context.get("winner_hypothesis")
    if isinstance(winner, Mapping):
        primitive = winner.get("primitive") or winner.get("type")
        if isinstance(primitive, str) and primitive:
            return primitive

    task_concept = context.get("task_concept")
    if isinstance(task_concept, str) and task_concept:
        return task_concept

    operations = [
        str(step.get("operation"))
        for step in operation_sequence
        if step.get("operation")
    ]
    return " ".join(operations)


def _program_id(
    signature_id: str,
    program: Mapping[str, Any],
    operation_sequence: list[Mapping[str, Any]],
) -> str:
    encoded = json.dumps(
        {
            "signature": signature_id,
            "program": program,
            "operations": operation_sequence,
        },
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"program-{digest}"


def _program_family_id(
    program: Mapping[str, Any],
    operation_sequence: list[Mapping[str, Any]],
    concept: str,
) -> str:
    encoded = json.dumps(
        {
            "concept": concept,
            "program": program,
            "operations": operation_sequence,
        },
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"program-family-{digest}"


def _promotion_evidence(
    memory: ProgramMemory,
    family_id: str,
    current_signature_id: str,
) -> list[str]:
    signatures = set()
    for record in memory.records:
        metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
        if metadata.get("program_family_id") != family_id:
            continue
        if record.validation_state not in {"candidate", "validated", "stable"}:
            continue
        if not record.integrity_verified or record.stale:
            continue
        for signature_id in metadata.get("promotion_evidence", []) or []:
            if signature_id:
                signatures.add(str(signature_id))
        if record.task_signature_id:
            signatures.add(str(record.task_signature_id))
    signatures.discard(current_signature_id)
    return sorted(signatures)


def _promote_family_candidates(
    memory: ProgramMemory,
    family_id: str,
    promotion_evidence: list[str],
) -> None:
    updated = False
    for record in memory.records:
        metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
        if metadata.get("program_family_id") != family_id:
            continue
        if record.validation_state != "candidate":
            continue
        record.validation_state = "validated"
        record.metadata = {
            **metadata,
            "promotion_evidence": sorted(set(promotion_evidence)),
            "promotion_rule": "cross_task_near_success",
        }
        updated = True
    if updated:
        memory.save()


def _residual_count(
    context: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> int:
    residual_analysis = context.get("residual_analysis")
    residual_analysis = (
        residual_analysis
        if isinstance(residual_analysis, Mapping)
        else evaluation.get("residual_analysis", {})
    )
    residual_analysis = (
        residual_analysis
        if isinstance(residual_analysis, Mapping)
        else {}
    )
    for value in (
        residual_analysis.get("residual_difference_count"),
        evaluation.get("difference_count"),
    ):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            continue
    return 0


def _semantic_contradictions(
    context: Mapping[str, Any],
) -> list[str]:
    contradictions = []
    direct = context.get("semantic_contradictions", [])
    if isinstance(direct, list):
        contradictions.extend(str(item) for item in direct if item)
    abstractions = context.get("semantic_abstractions", [])
    if isinstance(abstractions, list):
        for abstraction in abstractions:
            if not isinstance(abstraction, Mapping):
                continue
            for item in abstraction.get("semantic_contradictions", []) or []:
                if item:
                    contradictions.append(str(item))
            if abstraction.get("semantic_valid") is False:
                contradictions.append("invalid_semantic_abstraction")
    return sorted(set(contradictions))


def _confidence(accuracy: float, context: Mapping[str, Any]) -> float:
    reward = (
        context.get("operator_reward_report", {})
        if isinstance(context.get("operator_reward_report"), Mapping)
        else {}
    )
    reward_score = _number(
        reward.get("metrics", {}).get("reward_score")
        if isinstance(reward.get("metrics"), Mapping)
        else 0.0
    )
    return round(max(accuracy, reward_score), 4)


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return deepcopy(value)
    except (TypeError, ValueError):
        return json.loads(json.dumps(value, default=str))


def _number(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _skipped(reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "program_memory_updated": False,
        "reason": reason,
        **extra,
    }


__all__ = ["remember_validated_program"]
