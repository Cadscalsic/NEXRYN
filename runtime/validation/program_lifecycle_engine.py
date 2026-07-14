"""Program validation lifecycle engine for synthesized NEXRYN programs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping


PRIMARY_LIFECYCLE = (
    "NEW",
    "GENERATED",
    "STRUCTURALLY_VALIDATED",
    "SEMANTICALLY_VALIDATED",
    "EXECUTION_VALIDATED",
    "GENERALIZATION_VALIDATED",
    "APPROVED",
    "CANONICAL",
)

ALTERNATIVE_STATES = (
    "REJECTED",
    "MERGED",
    "SUPERSEDED",
    "DUPLICATE",
    "OBSOLETE",
    "EXPERIMENTAL",
    "PENDING",
    "FAILED",
    "ARCHIVED",
)

PROGRAM_LIFECYCLE_STATES = PRIMARY_LIFECYCLE + ALTERNATIVE_STATES
TERMINAL_STATES = {
    "CANONICAL",
    "REJECTED",
    "MERGED",
    "SUPERSEDED",
    "DUPLICATE",
    "OBSOLETE",
    "FAILED",
    "ARCHIVED",
}

VALIDATION_STAGE_TO_STATE = {
    "structural": "STRUCTURALLY_VALIDATED",
    "semantic": "SEMANTICALLY_VALIDATED",
    "execution": "EXECUTION_VALIDATED",
    "generalization": "GENERALIZATION_VALIDATED",
}


@dataclass(frozen=True)
class ProgramIdentity:
    program_id: str
    program_hash: str
    program_signature: str
    generation_episode: str | None = None
    generation_runtime: str = "program_synthesis_runtime"
    generation_timestamp: str = field(default_factory=lambda: _now())
    origin_concepts: tuple[str, ...] = ()
    origin_rules: tuple[str, ...] = ()
    origin_transformations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationEvent:
    program_id: str
    previous_state: str
    current_state: str
    validation_stage: str
    validation_timestamp: str
    validator: str
    validation_reason: str
    validation_result: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProgramLifecycleError(ValueError):
    """Raised when a program lifecycle transition is invalid."""


class ProgramValidationLifecycleEngine:
    """Authoritative registry and lifecycle engine for synthesized programs."""

    system_name = "program_validation_lifecycle_engine"

    def __init__(
        self,
        registry: dict[str, dict[str, Any]] | None = None,
        events: list[dict[str, Any]] | None = None,
        failures: list[dict[str, Any]] | None = None,
    ) -> None:
        self.registry = registry if registry is not None else {}
        self.events = events if events is not None else []
        self.failures = failures if failures is not None else []

    def register_program(
        self,
        program: Mapping[str, Any],
        *,
        generation_episode: str | None = None,
        generation_runtime: str = "program_synthesis_runtime",
        state: str = "GENERATED",
    ) -> dict[str, Any]:
        identity = self._identity(
            program,
            generation_episode=generation_episode,
            generation_runtime=generation_runtime,
        )
        existing_id = self._program_id_by_signature(identity.program_signature)
        if existing_id and existing_id != identity.program_id:
            record = self._new_record(identity, program)
            self.registry[identity.program_id] = record
            self.transition(
                identity.program_id,
                "GENERATED",
                validator=generation_runtime,
                reason="program_synthesized",
                result="registered",
                stage="generation",
            )
            return self.mark_duplicate(
                identity.program_id,
                duplicate_of=existing_id,
                reason="program_signature_already_registered",
            )

        if identity.program_id in self.registry:
            return dict(self.registry[identity.program_id])

        record = self._new_record(identity, program)
        self.registry[identity.program_id] = record
        self.transition(
            identity.program_id,
            state,
            validator=generation_runtime,
            reason="program_synthesized",
            result="registered",
            stage="generation",
        )
        return dict(self.registry[identity.program_id])

    def register_from_synthesis_report(
        self,
        report: Mapping[str, Any],
        *,
        generation_episode: str | None = None,
    ) -> dict[str, Any]:
        runtime = "program_synthesis_runtime"
        registered = []
        for program in _program_items(report):
            record = self.register_program(
                program,
                generation_episode=generation_episode,
                generation_runtime=runtime,
            )
            registered.append(record["program_id"])
            self._apply_existing_validation(record["program_id"], program)

        for rejection in _as_list(report.get("rejected_programs")):
            if not isinstance(rejection, Mapping):
                continue
            rejected = self.register_program(
                rejection,
                generation_episode=generation_episode,
                generation_runtime=runtime,
            )
            self.reject_program(
                rejected["program_id"],
                reason=str(rejection.get("reason") or "program_rejected_by_synthesis_competition"),
                failed_stage=str(rejection.get("failed_validation_stage") or "generation_competition"),
                failed_constraints=_string_tuple(rejection.get("failed_constraints")),
                alternative_candidates=_string_tuple(rejection.get("alternative_candidates")),
                possible_recovery=str(rejection.get("possible_recovery") or "revise_candidate_constraints"),
            )

        lifecycle_report = self.build_report()
        return {
            **dict(report),
            "PROGRAM_VALIDATION_LIFECYCLE_REPORT": lifecycle_report,
            "program_lifecycle_registry": lifecycle_report["program_registry"],
            "program_lifecycle_states": lifecycle_report["lifecycle_states"],
            "program_lifecycle_history": lifecycle_report["program_history"],
            "program_evolution_graph": lifecycle_report["program_evolution_graph"],
            "approved_programs": lifecycle_report["approved_programs"],
            "canonical_programs": lifecycle_report["canonical_programs"],
            "pending_programs": lifecycle_report["pending_programs"],
            "experimental_programs": lifecycle_report["experimental_programs"],
            "rejected_programs": lifecycle_report["rejected_programs"],
            "merged_programs": lifecycle_report["merged_programs"],
            "duplicate_programs": lifecycle_report["duplicate_programs"],
            "failed_programs": lifecycle_report["failed_programs"],
            "obsolete_programs": lifecycle_report["obsolete_programs"],
            "generalization_validated_programs": lifecycle_report[
                "generalization_validated_programs"
            ],
            "validation_success_rate": lifecycle_report["validation_success_rate"],
            "validation_failure_rate": lifecycle_report["validation_failure_rate"],
        }

    def validate_structural(
        self,
        program_id: str,
        *,
        result: bool = True,
        reason: str = "structural_validation_passed",
        validator: str = "structural_validator",
        details: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._validate_stage(
            program_id,
            "structural",
            result=result,
            reason=reason,
            validator=validator,
            details=details,
        )

    def validate_semantic(
        self,
        program_id: str,
        *,
        result: bool = True,
        reason: str = "semantic_validation_passed",
        validator: str = "semantic_validator",
        details: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._validate_stage(
            program_id,
            "semantic",
            result=result,
            reason=reason,
            validator=validator,
            details=details,
        )

    def validate_execution(
        self,
        program_id: str,
        *,
        result: bool = True,
        reason: str = "execution_validation_passed",
        validator: str = "execution_validator",
        details: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._validate_stage(
            program_id,
            "execution",
            result=result,
            reason=reason,
            validator=validator,
            details=details,
        )

    def validate_generalization(
        self,
        program_id: str,
        *,
        result: bool = True,
        reason: str = "generalization_validation_passed",
        validator: str = "generalization_validator",
        details: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._validate_stage(
            program_id,
            "generalization",
            result=result,
            reason=reason,
            validator=validator,
            details=details,
        )

    def approve_program(
        self,
        program_id: str,
        *,
        validator: str = "program_approval_gate",
        reason: str = "program_approved",
    ) -> dict[str, Any]:
        return self.transition(
            program_id,
            "APPROVED",
            validator=validator,
            reason=reason,
            result="passed",
            stage="approval",
        )

    def canonicalize_program(
        self,
        program_id: str,
        *,
        validator: str = "program_repository",
        reason: str = "program_promoted_to_canonical_repository",
    ) -> dict[str, Any]:
        return self.transition(
            program_id,
            "CANONICAL",
            validator=validator,
            reason=reason,
            result="passed",
            stage="canonicalization",
        )

    def reject_program(
        self,
        program_id: str,
        *,
        reason: str,
        failed_stage: str,
        failed_constraints: tuple[str, ...] | list[str] = (),
        alternative_candidates: tuple[str, ...] | list[str] = (),
        replacement_program: str | None = None,
        possible_recovery: str | None = None,
        validator: str = "program_validation_lifecycle_engine",
    ) -> dict[str, Any]:
        record = self.transition(
            program_id,
            "REJECTED",
            validator=validator,
            reason=reason,
            result="failed",
            stage=failed_stage,
        )
        record["rejection_analysis"] = {
            "rejection_reason": reason,
            "failed_validation_stage": failed_stage,
            "failed_constraints": list(failed_constraints),
            "alternative_candidates": list(alternative_candidates),
            "replacement_program": replacement_program,
            "possible_recovery": possible_recovery,
        }
        self.registry[program_id].update(record)
        return dict(self.registry[program_id])

    def replace_program(
        self,
        parent_program: str,
        child_program: str,
        *,
        reason: str = "program_replaced_by_evolved_child",
    ) -> dict[str, Any]:
        self._require(parent_program)
        self._require(child_program)
        parent = self.registry[parent_program]
        child = self.registry[child_program]
        parent["replacement_program"] = child_program
        parent["child_programs"] = _unique((*_string_tuple(parent.get("child_programs")), child_program))
        child["parent_program"] = parent_program
        child["derived_program"] = parent_program
        self.transition(
            parent_program,
            "SUPERSEDED",
            validator=self.system_name,
            reason=reason,
            result="replaced",
            stage="evolution",
        )
        self._edge(parent_program, child_program, "replaced_by")
        return dict(self.registry[parent_program])

    def merge_programs(
        self,
        source_programs: tuple[str, ...] | list[str],
        merged_program: str,
        *,
        reason: str = "programs_merged_into_replacement",
    ) -> dict[str, Any]:
        self._require(merged_program)
        for source in source_programs:
            self._require(source)
            self.registry[source]["merged_program"] = merged_program
            self.transition(
                source,
                "MERGED",
                validator=self.system_name,
                reason=reason,
                result="merged",
                stage="evolution",
            )
            self._edge(source, merged_program, "merged_into")
        self.registry[merged_program]["merged_from"] = list(source_programs)
        return dict(self.registry[merged_program])

    def mark_duplicate(
        self,
        program_id: str,
        *,
        duplicate_of: str,
        reason: str = "duplicate_program_signature",
    ) -> dict[str, Any]:
        self._require(program_id)
        self._require(duplicate_of)
        self.registry[program_id]["duplicate_of"] = duplicate_of
        self.transition(
            program_id,
            "DUPLICATE",
            validator=self.system_name,
            reason=reason,
            result="duplicate",
            stage="deduplication",
        )
        self._edge(program_id, duplicate_of, "duplicates")
        return dict(self.registry[program_id])

    def transition(
        self,
        program_id: str,
        target_state: str,
        *,
        validator: str,
        reason: str,
        result: str,
        stage: str,
        details: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._require(program_id)
        target_state = str(target_state)
        if target_state not in PROGRAM_LIFECYCLE_STATES:
            return self._illegal(program_id, "unknown_lifecycle_state", target_state)

        record = self.registry[program_id]
        current = str(record["current_state"])
        if current == target_state:
            return self._illegal(program_id, "duplicate_transition", target_state)
        if not self._can_transition(current, target_state):
            return self._illegal(program_id, "illegal_transition", f"{current} -> {target_state}")

        event = ValidationEvent(
            program_id=program_id,
            previous_state=current,
            current_state=target_state,
            validation_stage=stage,
            validation_timestamp=_now(),
            validator=validator,
            validation_reason=reason,
            validation_result=result,
            details=dict(details or {}),
        ).to_dict()
        record["previous_state"] = current
        record["current_state"] = target_state
        record["validation_timestamp"] = event["validation_timestamp"]
        record["validator"] = validator
        record["validation_reason"] = reason
        record["validation_result"] = result
        record["validation_history"].append(event)
        record["state_history"].append(target_state)
        self._apply_status(record, target_state, result)
        self.events.append(event)
        return dict(record)

    def validate_registry_consistency(self) -> dict[str, Any]:
        failures = []
        signatures = {}
        for program_id, record in self.registry.items():
            if program_id != record.get("program_id"):
                failures.append(self._failure(program_id, "program_id_mismatch", record.get("program_id")))
            if record.get("current_state") not in PROGRAM_LIFECYCLE_STATES:
                failures.append(self._failure(program_id, "invalid_state", record.get("current_state")))
            if not record.get("validation_history"):
                failures.append(self._failure(program_id, "missing_validation_history", None))
            signature = record.get("program_signature")
            if signature in signatures and record.get("current_state") != "DUPLICATE":
                failures.append(self._failure(program_id, "duplicate_signature_not_marked", signature))
            signatures[signature] = program_id
            for key in ("parent_program", "child_program", "merged_program", "replacement_program", "derived_program"):
                value = record.get(key)
                if value and value not in self.registry:
                    failures.append(self._failure(program_id, "broken_evolution_reference", {key: value}))
        return {
            "valid": not failures and not self.failures,
            "failure_count": len(failures) + len(self.failures),
            "failures": (self.failures + failures)[-200:],
        }

    def build_report(self) -> dict[str, Any]:
        states = self._state_counts()
        generated = len(self.registry)
        rejected = states.get("REJECTED", 0)
        failed = states.get("FAILED", 0)
        successes = sum(
            states.get(state, 0)
            for state in (
                "STRUCTURALLY_VALIDATED",
                "SEMANTICALLY_VALIDATED",
                "EXECUTION_VALIDATED",
                "GENERALIZATION_VALIDATED",
                "APPROVED",
                "CANONICAL",
            )
        )
        failures = rejected + failed + states.get("DUPLICATE", 0)
        return {
            "system": self.system_name,
            "PROGRAM_VALIDATION_LIFECYCLE_REPORT": True,
            "authoritative_registry": True,
            "lifecycle_states": states,
            "generated_programs": generated,
            "validated_programs": successes,
            "approved_programs": states.get("APPROVED", 0) + states.get("CANONICAL", 0),
            "canonical_programs": states.get("CANONICAL", 0),
            "pending_programs": states.get("PENDING", 0) + states.get("NEW", 0) + states.get("GENERATED", 0),
            "experimental_programs": states.get("EXPERIMENTAL", 0),
            "rejected_programs": rejected,
            "merged_programs": states.get("MERGED", 0),
            "duplicate_programs": states.get("DUPLICATE", 0),
            "failed_programs": failed,
            "obsolete_programs": states.get("OBSOLETE", 0) + states.get("SUPERSEDED", 0),
            "generalization_validated_programs": (
                states.get("GENERALIZATION_VALIDATED", 0)
                + states.get("APPROVED", 0)
                + states.get("CANONICAL", 0)
            ),
            "validation_success_rate": round(successes / max(generated, 1), 4),
            "validation_failure_rate": round(failures / max(generated, 1), 4),
            "program_registry": {
                program_id: self.lookup(program_id)
                for program_id in sorted(self.registry)
            },
            "program_history": {
                program_id: list(record.get("state_history", []))
                for program_id, record in sorted(self.registry.items())
            },
            "program_evolution_graph": self.evolution_graph(),
            "registry_consistency": self.validate_registry_consistency(),
            "generated_at": _now(),
        }

    def lookup(self, program_id: str) -> dict[str, Any]:
        self._require(program_id)
        record = dict(self.registry[program_id])
        return {
            "identity": {
                "program_id": record.get("program_id"),
                "program_hash": record.get("program_hash"),
                "program_signature": record.get("program_signature"),
                "generation_episode": record.get("generation_episode"),
                "generation_runtime": record.get("generation_runtime"),
                "generation_timestamp": record.get("generation_timestamp"),
                "origin_concepts": record.get("origin_concepts", []),
                "origin_rules": record.get("origin_rules", []),
                "origin_transformations": record.get("origin_transformations", []),
            },
            "current_lifecycle_state": record.get("current_state"),
            "current_state": record.get("current_state"),
            "validation_history": list(record.get("validation_history", [])),
            "confidence": record.get("confidence", 0.0),
            "execution_history": list(record.get("execution_history", [])),
            "generalization_history": list(record.get("generalization_history", [])),
            "replacement_history": list(record.get("replacement_history", [])),
            **record,
        }

    def evolution_graph(self) -> dict[str, Any]:
        nodes = [
            {
                "id": program_id,
                "state": record.get("current_state"),
                "signature": record.get("program_signature"),
            }
            for program_id, record in sorted(self.registry.items())
        ]
        edges = []
        for program_id, record in sorted(self.registry.items()):
            for key, relation in (
                ("parent_program", "parent"),
                ("child_program", "child"),
                ("merged_program", "merged_into"),
                ("replacement_program", "replaced_by"),
                ("derived_program", "derived_from"),
                ("duplicate_of", "duplicates"),
            ):
                value = record.get(key)
                if value:
                    edges.append({"from": program_id, "to": value, "relation": relation})
            for child in _string_tuple(record.get("child_programs")):
                edges.append({"from": program_id, "to": child, "relation": "parent_of"})
            for variant in _string_tuple(record.get("experimental_variants")):
                edges.append({"from": program_id, "to": variant, "relation": "variant"})
        return {
            "nodes": nodes,
            "edges": _dedupe_edges(edges),
            "node_count": len(nodes),
            "edge_count": len(_dedupe_edges(edges)),
        }

    def _validate_stage(
        self,
        program_id: str,
        stage: str,
        *,
        result: bool,
        reason: str,
        validator: str,
        details: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        if not result:
            return self.reject_program(
                program_id,
                reason=reason,
                failed_stage=stage,
                failed_constraints=_string_tuple((details or {}).get("failed_constraints")),
                possible_recovery=(details or {}).get("possible_recovery"),
                validator=validator,
            )
        return self.transition(
            program_id,
            VALIDATION_STAGE_TO_STATE[stage],
            validator=validator,
            reason=reason,
            result="passed",
            stage=stage,
            details=details,
        )

    def _apply_existing_validation(self, program_id: str, program: Mapping[str, Any]) -> None:
        validation = program.get("validation_results")
        if isinstance(validation, Mapping) and validation.get("accepted"):
            if self.registry[program_id]["current_state"] == "GENERATED":
                self.validate_structural(program_id, details={"source": "synthesis_validation"})
                self.validate_semantic(program_id, details={"source": "synthesis_validation"})
            lifecycle = str(program.get("lifecycle") or "")
            if lifecycle in {"GENERALIZED", "STABLE"}:
                self.validate_execution(program_id, details={"source": "synthesis_validation"})
                self.validate_generalization(program_id, details={"source": "synthesis_validation"})
            if lifecycle in {"PROMOTED", "REUSED", "STABLE"}:
                if self.registry[program_id]["current_state"] == "SEMANTICALLY_VALIDATED":
                    self.validate_execution(program_id, details={"source": "synthesis_validation"})
                    self.validate_generalization(program_id, details={"source": "synthesis_validation"})
                self.approve_program(program_id, reason="synthesis_lifecycle_promoted_program")
        elif isinstance(validation, Mapping) and validation.get("accepted") is False:
            self.reject_program(
                program_id,
                reason=str(validation.get("validation_reason") or "candidate_program_rejected"),
                failed_stage="semantic",
                failed_constraints=_string_tuple(program.get("required_constraints")),
            )

    def _new_record(self, identity: ProgramIdentity, program: Mapping[str, Any]) -> dict[str, Any]:
        source = dict(program)
        return {
            **identity.to_dict(),
            "program_payload": source,
            "program_name": source.get("program_name") or source.get("name"),
            "program_type": source.get("program_type") or source.get("type"),
            "current_state": "NEW",
            "previous_state": None,
            "validation_history": [],
            "state_history": ["NEW"],
            "validation_timestamp": None,
            "validator": None,
            "validation_reason": None,
            "validation_result": None,
            "approval_status": "UNAPPROVED",
            "generalization_status": "UNVALIDATED",
            "execution_status": "UNVALIDATED",
            "confidence": _number(source.get("confidence")),
            "execution_history": [],
            "generalization_history": [],
            "replacement_history": [],
            "parent_program": source.get("parent_program"),
            "child_program": source.get("child_program"),
            "child_programs": _string_tuple(source.get("child_programs")),
            "merged_program": source.get("merged_program"),
            "replacement_program": source.get("replacement_program"),
            "derived_program": source.get("derived_program"),
            "experimental_variants": _string_tuple(source.get("experimental_variants")),
            "rejection_analysis": None,
        }

    def _identity(
        self,
        program: Mapping[str, Any],
        *,
        generation_episode: str | None,
        generation_runtime: str,
    ) -> ProgramIdentity:
        signature = str(
            program.get("program_signature")
            or _digest({
                "name": program.get("program_name") or program.get("name"),
                "type": program.get("program_type") or program.get("type"),
                "concepts": _string_tuple(program.get("required_concepts") or program.get("origin_concepts")),
                "transformations": _string_tuple(program.get("required_transformations")),
                "strategy": program.get("execution_strategy") or program.get("strategy"),
            })
        )
        program_hash = _digest(program)
        program_id = str(program.get("program_id") or program.get("id") or f"program:{signature[:16]}")
        return ProgramIdentity(
            program_id=program_id,
            program_hash=program_hash,
            program_signature=signature,
            generation_episode=generation_episode,
            generation_runtime=generation_runtime,
            generation_timestamp=str(program.get("generation_timestamp") or program.get("creation_timestamp") or _now()),
            origin_concepts=_string_tuple(program.get("origin_concepts") or program.get("required_concepts")),
            origin_rules=_string_tuple(program.get("origin_rules") or program.get("required_constraints")),
            origin_transformations=_string_tuple(program.get("origin_transformations") or program.get("required_transformations")),
        )

    def _program_id_by_signature(self, signature: str) -> str | None:
        for program_id, record in self.registry.items():
            if record.get("program_signature") == signature:
                return program_id
        return None

    def _can_transition(self, current: str, target: str) -> bool:
        if current in TERMINAL_STATES:
            return target == "ARCHIVED" and current != "ARCHIVED"
        if target in ALTERNATIVE_STATES:
            return current not in {"NEW"}
        if current not in PRIMARY_LIFECYCLE or target not in PRIMARY_LIFECYCLE:
            return False
        return PRIMARY_LIFECYCLE.index(target) == PRIMARY_LIFECYCLE.index(current) + 1

    def _apply_status(self, record: dict[str, Any], state: str, result: str) -> None:
        if state == "EXECUTION_VALIDATED":
            record["execution_status"] = result.upper()
            record["execution_history"].append(record["validation_history"][-1])
        if state == "GENERALIZATION_VALIDATED":
            record["generalization_status"] = result.upper()
            record["generalization_history"].append(record["validation_history"][-1])
        if state in {"APPROVED", "CANONICAL"}:
            record["approval_status"] = "APPROVED"
        if state in {"REJECTED", "FAILED"}:
            record["approval_status"] = "REJECTED"

    def _state_counts(self) -> dict[str, int]:
        counts = {state: 0 for state in PROGRAM_LIFECYCLE_STATES}
        for record in self.registry.values():
            state = record.get("current_state", "PENDING")
            counts[state] = counts.get(state, 0) + 1
        return {key: value for key, value in counts.items() if value}

    def _edge(self, source: str, target: str, relation: str) -> None:
        self.events.append({
            "program_id": source,
            "target_program_id": target,
            "relation": relation,
            "event_type": "program_evolution",
            "timestamp": _now(),
        })

    def _require(self, program_id: str) -> None:
        if program_id not in self.registry:
            raise ProgramLifecycleError(f"unknown program: {program_id}")

    def _illegal(self, program_id: str, failure: str, detail: Any) -> dict[str, Any]:
        self.failures.append(self._failure(program_id, failure, detail))
        raise ProgramLifecycleError(f"{failure}: {detail}")

    def _failure(self, program_id: str, failure: str, detail: Any) -> dict[str, Any]:
        return {
            "program_id": program_id,
            "failure": failure,
            "detail": detail,
            "timestamp": _now(),
        }


def _program_items(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    items = report.get("generated_program_objects") or report.get("winning_programs") or report.get("programs")
    count = int(_number(report.get("generated_programs")))
    rejected_count = len(_as_list(report.get("rejected_programs")))
    if isinstance(items, Mapping):
        output = [item for item in items.values() if isinstance(item, Mapping)]
    elif isinstance(items, list):
        output = [item for item in items if isinstance(item, Mapping)]
    else:
        output = []
    missing = max(count - len(output) - rejected_count, 0)
    output.extend(
        {
            "id": f"program:generated:{index}",
            "program_signature": f"generated-placeholder:{index}",
            "placeholder": True,
        }
        for index in range(missing)
    )
    return output


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        values = [value.get("id") or value.get("program_id") or value.get("name")]
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = [value]
    return tuple(dict.fromkeys(str(item) for item in values if item is not None and item != ""))


def _unique(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if value))


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for edge in edges:
        marker = (edge.get("from"), edge.get("to"), edge.get("relation"))
        if marker in seen or edge.get("from") == edge.get("to"):
            continue
        seen.add(marker)
        output.append(edge)
    return output


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _digest(value: Any) -> str:
    return hashlib.sha1(
        json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


program_validation_lifecycle_engine = ProgramValidationLifecycleEngine()


__all__ = [
    "ALTERNATIVE_STATES",
    "PRIMARY_LIFECYCLE",
    "PROGRAM_LIFECYCLE_STATES",
    "ProgramIdentity",
    "ProgramLifecycleError",
    "ProgramValidationLifecycleEngine",
    "ValidationEvent",
    "program_validation_lifecycle_engine",
]
