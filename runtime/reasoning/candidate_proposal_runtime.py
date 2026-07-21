"""Collect candidate proposals before arena selection."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


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
        for source_name in sorted(sources):
            source = sources.get(source_name)
            records = self._records(source)
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
            if source.get("semantic_to_transformation_compilation_success"):
                return [source]
            if source.get("selected_program") or source.get("compiled_program"):
                return [source]
            if source.get("reuse_success_rate") or source.get("reuse_rate"):
                return [source]
        return []

    def _has_candidate(self, value: Any) -> bool:
        if not isinstance(value, Mapping):
            return value is not None
        program = value.get("program") or value.get("compiled_program") or value
        if isinstance(program, Mapping):
            steps = program.get("steps")
            if isinstance(steps, list) and steps:
                return True
        return bool(
            value.get("candidate_id")
            or value.get("operation")
            or value.get("reuse_success_rate")
            or value.get("reuse_rate")
        )

    def _rejection_reason(self, source: Any) -> str:
        if not isinstance(source, Mapping):
            return "source_not_available"
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
        return {
            "source": source,
            "proposal_id": proposal_id,
            "proposal_status": status,
            "operation": operation,
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
        }

    def _operation(self, candidate: Any) -> Any:
        if not isinstance(candidate, Mapping):
            return None
        program = candidate.get("program") or candidate.get("compiled_program") or candidate
        if isinstance(program, Mapping):
            steps = program.get("steps") or []
            if steps and isinstance(steps[0], Mapping):
                return steps[0].get("operation")
        return candidate.get("operation")

    def _candidate_field(self, candidate: Any, key: str) -> Any:
        if not isinstance(candidate, Mapping):
            return None
        metadata = candidate.get("metadata")
        if key in candidate:
            return candidate.get(key)
        if isinstance(metadata, Mapping):
            return metadata.get(key)
        return None

    def _investment_tier_counts(self, proposals: list[dict[str, Any]]) -> dict[str, int]:
        counts = {"HIGH_VALUE": 0, "MEDIUM_VALUE": 0, "LOW_VALUE": 0}
        for proposal in proposals:
            tier = str(proposal.get("investment_tier") or "LOW_VALUE")
            counts[tier if tier in counts else "LOW_VALUE"] += 1
        return counts


candidate_proposal_runtime = CandidateProposalRuntime()
