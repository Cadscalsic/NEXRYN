"""Collect candidate proposals before arena selection."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.telemetry.route_contribution import ROUTE_LINEAGE_FIELDS


class CandidateProposalRuntime:
    """Build a pre-arena ledger of candidate rights, entries, and rejections."""

    system_name = "candidate_proposal_runtime"

    def collect(
        self,
        *,
        candidate_sources: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        sources = candidate_sources if isinstance(candidate_sources, Mapping) else {}
        proposals = []
        source_diagnostics = {}
        for source_name in sorted(sources):
            source = sources.get(source_name)
            records = self._records(source)
            source_diagnostics[source_name] = self._source_diagnostic(
                source,
                records,
            )
            if records:
                for index, record in enumerate(records):
                    proposals.append(self._proposal(
                        source_name,
                        status="PROPOSED",
                        proposal_id=f"{source_name}:{index}",
                        candidate=record,
                    ))
            else:
                proposals.append(self._proposal(
                    source_name,
                    status="REJECTED",
                    proposal_id=f"{source_name}:rejection",
                    rejection_reason=self._rejection_reason(source),
                ))

        proposed = [item for item in proposals if item["proposal_status"] == "PROPOSED"]
        rejected = [item for item in proposals if item["proposal_status"] == "REJECTED"]
        sources_with_proposals = sorted({item["source"] for item in proposed})
        investment_tiers = self._investment_tier_counts(proposed)
        return {
            "system": self.system_name,
            "proposal_phase_entered": True,
            "eligible_source_count": len(sources),
            "proposal_count": len(proposed),
            "explicit_rejection_count": len(rejected),
            "candidate_proposals": proposals,
            "sources_with_proposals": sources_with_proposals,
            "sources_rejected": sorted({item["source"] for item in rejected}),
            "knowledge_investment_policy": "OPERATIONAL_VALUE_PRIORITIZED",
            "knowledge_investment_authority": self.system_name,
            "high_value_knowledge_items": investment_tiers["HIGH_VALUE"],
            "medium_value_knowledge_items": investment_tiers["MEDIUM_VALUE"],
            "low_value_knowledge_items": investment_tiers["LOW_VALUE"],
            "deprioritized_knowledge_items": investment_tiers["LOW_VALUE"],
            "source_diagnostics": source_diagnostics,
            "proposal_phase_status": (
                "COMPETITIVE"
                if len(sources_with_proposals) > 1
                else "SINGLE_SOURCE"
                if sources_with_proposals
                else "EMPTY"
            ),
            "timestamp": str(datetime.utcnow()),
        }

    def _records(self, source: Any) -> list[Any]:
        if source is None:
            return []
        if isinstance(source, list):
            return [item for item in source if self._has_candidate(item)]
        if isinstance(source, tuple):
            return [item for item in source if self._has_candidate(item)]
        if isinstance(source, Mapping):
            for key in (
                "compiler_candidates",
                "ranked_candidates",
                "candidate_rows",
                "candidates",
                "reused_programs",
                "counterfactual_candidates",
                "repair_candidates",
            ):
                value = source.get(key)
                if isinstance(value, (list, tuple)):
                    records = [item for item in value if self._has_candidate(item)]
                    if records:
                        return records
            if self._has_candidate(source.get("composed_program")):
                return [source.get("composed_program")]
            if source.get("semantic_to_transformation_compilation_success"):
                return [source]
            if source.get("selected_program") or source.get("compiled_program"):
                return [source] if self._has_executable_candidate(source) else []
            if source.get("reuse_success_rate") or source.get("reuse_rate"):
                return [source] if self._has_executable_candidate(source) else []
        return []

    def _has_candidate(self, value: Any) -> bool:
        if not isinstance(value, Mapping):
            return value is not None
        program = value.get("program") or value.get("compiled_program") or value
        if isinstance(program, Mapping):
            steps = (
                program.get("steps")
                or program.get("program_steps")
                or program.get("operation_sequence")
            )
            if isinstance(steps, list) and steps:
                return True
        return bool(
            value.get("candidate_id")
            or value.get("operation")
            or value.get("reuse_success_rate")
            or value.get("reuse_rate")
        )

    def _has_executable_candidate(self, value: Any) -> bool:
        if not isinstance(value, Mapping):
            return False
        program = value.get("program") or value.get("compiled_program") or value
        if isinstance(program, Mapping):
            steps = (
                program.get("steps")
                or program.get("program_steps")
                or program.get("operation_sequence")
            )
            if isinstance(steps, list) and steps:
                return True
        return bool(
            value.get("operation")
            or value.get("primitive")
            or value.get("operator")
        )

    def _rejection_reason(self, source: Any) -> str:
        if not isinstance(source, Mapping):
            return "source_not_available"
        if source.get("adaptive_reuse_candidate_materialization_state"):
            return str(source.get("adaptive_reuse_candidate_materialization_state"))
        if self._has_cognitive_reuse_evidence(source):
            return "COGNITIVE_REUSE_ONLY"
        if source.get("reuse_success_rate") or source.get("reuse_rate"):
            composed = source.get("composed_program")
            if isinstance(composed, Mapping):
                steps = composed.get("program_steps") or composed.get("steps") or []
                if not steps:
                    return "REUSE_STEPS_EMPTY"
            if source.get("reused_strategies") and not (
                source.get("reused_programs") or source.get("composed_program")
            ):
                return "NO_EXECUTABLE_REUSE_PAYLOAD"
        return str(
            source.get("failure_reason")
            or source.get("blocked_reason")
            or source.get("rejection_reason")
            or "no_candidate_proposed"
        )

    def _proposal(
        self,
        source: str,
        *,
        status: str,
        proposal_id: str,
        candidate: Any = None,
        rejection_reason: str | None = None,
    ) -> dict[str, Any]:
        operation = self._operation(candidate)
        program = self._program(candidate)
        learned_object = self._learned_object(candidate)
        metadata = self._metadata(candidate)
        metadata.update({
            "learned_object_id": learned_object["learned_object_id"],
            "source_learned_object_id": learned_object["learned_object_id"],
            "learned_object_type": learned_object["learned_object_type"],
            "reuse_proposal_id": proposal_id,
            "reuse_observation_authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
        })
        route_fields = self._route_lineage_fields(candidate, metadata)
        return {
            "source": source,
            "proposal_id": proposal_id,
            "candidate_id": self._candidate_field(candidate, "candidate_id")
            or proposal_id,
            "learned_object_id": learned_object["learned_object_id"],
            "source_learned_object_id": learned_object["learned_object_id"],
            "learned_object_type": learned_object["learned_object_type"],
            "reuse_proposal_id": proposal_id,
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "proposal_status": status,
            **route_fields,
            "intent": self._candidate_field(candidate, "intent") or operation,
            "operation": operation,
            "program": program,
            "operational_value_score": self._candidate_field(
                candidate,
                "operational_value_score",
            ),
            "investment_tier": self._candidate_field(candidate, "investment_tier"),
            "investment_reason": self._candidate_field(
                candidate,
                "investment_reason",
            ),
            "candidate_available": status == "PROPOSED",
            "rejection_reason": rejection_reason,
            "metadata": metadata,
        }

    def _operation(self, candidate: Any) -> Any:
        if not isinstance(candidate, Mapping):
            return None
        program = (
            candidate.get("program")
            or candidate.get("compiled_program")
            or candidate.get("selected_program")
            or candidate
        )
        if isinstance(program, Mapping):
            steps = (
                program.get("steps")
                or program.get("program_steps")
                or program.get("operation_sequence")
                or []
            )
            if steps and isinstance(steps[0], Mapping):
                return (
                    steps[0].get("operation")
                    or steps[0].get("primitive")
                    or steps[0].get("operator")
                )
        return candidate.get("operation") or candidate.get("primitive") or candidate.get("operator")

    def _program(self, candidate: Any) -> dict[str, Any]:
        if not isinstance(candidate, Mapping):
            return {"step_count": 0, "steps": []}
        program = (
            candidate.get("program")
            or candidate.get("compiled_program")
            or candidate.get("selected_program")
            or candidate
        )
        steps = []
        if isinstance(program, Mapping):
            raw_steps = (
                program.get("steps")
                or program.get("program_steps")
                or program.get("operation_sequence")
                or []
            )
            if isinstance(raw_steps, list):
                steps = [dict(step) for step in raw_steps if isinstance(step, Mapping)]
        return {
            "step_count": int(
                self._candidate_field(candidate, "step_count")
                or (program.get("step_count") if isinstance(program, Mapping) else 0)
                or len(steps)
                or 0
            ),
            "steps": steps,
        }

    def _candidate_field(self, candidate: Any, key: str) -> Any:
        if not isinstance(candidate, Mapping):
            return None
        metadata = candidate.get("metadata")
        if key in candidate:
            return candidate.get(key)
        if isinstance(metadata, Mapping):
            return metadata.get(key)
        return None

    def _metadata(self, candidate: Any) -> dict[str, Any]:
        if not isinstance(candidate, Mapping):
            return {}
        metadata = candidate.get("metadata")
        return dict(metadata) if isinstance(metadata, Mapping) else {}

    def _route_lineage_fields(
        self,
        candidate: Any,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        fields = {}
        if not isinstance(candidate, Mapping):
            return fields
        for field in ROUTE_LINEAGE_FIELDS:
            value = candidate.get(field)
            if value is None:
                value = metadata.get(field)
            if value is not None:
                fields[field] = value
                metadata[field] = value
        return fields

    def _learned_object(self, candidate: Any) -> dict[str, Any]:
        if not isinstance(candidate, Mapping):
            return {
                "learned_object_id": None,
                "learned_object_type": None,
            }
        learned_object_id = (
            candidate.get("learned_object_id")
            or candidate.get("source_learned_object_id")
            or candidate.get("program_id")
            or candidate.get("strategy_id")
            or candidate.get("experience_id")
            or candidate.get("truth_id")
            or candidate.get("knowledge_id")
            or candidate.get("concept_id")
        )
        if candidate.get("program_id"):
            object_type = "PROGRAM"
        elif candidate.get("strategy_id"):
            object_type = "STRATEGY"
        elif candidate.get("experience_id"):
            object_type = "EXPERIENCE_RECORD"
        elif candidate.get("truth_id"):
            object_type = "TRUTH_OBJECT"
        elif candidate.get("knowledge_id"):
            object_type = "KNOWLEDGE_OBJECT"
        elif candidate.get("concept_id"):
            object_type = "CONCEPT"
        else:
            object_type = candidate.get("learned_object_type")
        return {
            "learned_object_id": learned_object_id,
            "learned_object_type": object_type,
        }

    def _source_diagnostic(
        self,
        source: Any,
        records: list[Any],
    ) -> dict[str, Any]:
        source_map = source if isinstance(source, Mapping) else {}
        composed = source_map.get("composed_program")
        composed_map = composed if isinstance(composed, Mapping) else {}
        steps = (
            composed_map.get("program_steps")
            or composed_map.get("steps")
            or []
        )
        first_record = records[0] if records else None
        executable_reuse_available = self._has_executable_candidate(source)
        cognitive_reuse_available = self._has_cognitive_reuse_evidence(source)
        return {
            "source_seen": source is not None,
            "source_type": type(source).__name__,
            "candidate_detected": bool(records),
            "candidate_rejected": not bool(records),
            "rejection_reason": None if records else self._rejection_reason(source),
            "reuse_output_mode": (
                "EXECUTABLE_REUSE_AVAILABLE"
                if executable_reuse_available
                else "COGNITIVE_REUSE_ONLY"
                if cognitive_reuse_available
                else "NO_REUSE_EVIDENCE"
            ),
            "executable_reuse_available": executable_reuse_available,
            "cognitive_reuse_available": cognitive_reuse_available,
            "arena_admission_eligible": executable_reuse_available,
            "reused_program_count": len(source_map.get("reused_programs") or [])
            if isinstance(source_map.get("reused_programs"), list)
            else 0,
            "reused_strategy_count": len(source_map.get("reused_strategies") or [])
            if isinstance(source_map.get("reused_strategies"), list)
            else 0,
            "composed_program_present": isinstance(composed, Mapping) and bool(composed),
            "composed_program_type": type(composed).__name__,
            "program_steps_present": bool(steps),
            "program_steps_count": len(steps) if isinstance(steps, list) else 0,
            "resolved_operation": self._operation(first_record),
            "normalized_step_count": self._program(first_record).get("step_count")
            if first_record is not None
            else 0,
        }

    def _has_cognitive_reuse_evidence(self, source: Any) -> bool:
        if not isinstance(source, Mapping):
            return False
        for key in (
            "reused_strategies",
            "reused_contexts",
            "reused_truths",
            "reused_dependencies",
            "retrieved_experiences",
        ):
            value = source.get(key)
            if isinstance(value, list) and value:
                return True
        for key in (
            "strategy_hits",
            "context_hits",
            "truth_hits",
            "dependency_hits",
            "retrieval_successes",
            "operational_independent_reuse_success_count",
            "operational_reuse_evidence_count",
        ):
            try:
                if float(source.get(key) or 0) > 0:
                    return True
            except (TypeError, ValueError):
                continue
        return bool(source.get("reuse_success_rate") or source.get("reuse_rate"))

    def _investment_tier_counts(self, proposals: list[dict[str, Any]]) -> dict[str, int]:
        counts = {"HIGH_VALUE": 0, "MEDIUM_VALUE": 0, "LOW_VALUE": 0}
        for proposal in proposals:
            tier = str(proposal.get("investment_tier") or "LOW_VALUE")
            counts[tier if tier in counts else "LOW_VALUE"] += 1
        return counts


candidate_proposal_runtime = CandidateProposalRuntime()
