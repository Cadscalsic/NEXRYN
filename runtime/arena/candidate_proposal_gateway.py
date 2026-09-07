"""Candidate proposal gateway for governed arena entry."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping

from runtime.telemetry.route_contribution import ROUTE_LINEAGE_FIELDS


SUPPORTED_SOURCES = {
    "semantic_compiler",
    "normalized_program_candidates",
    "program_synthesis",
    "adaptive_reuse",
    "transformation_matcher",
    "rule_engine",
    "hypothesis_engine",
    "repair_engine",
    "transfer_learning",
    "dependency_guided_reasoning",
    "truth_guided_reasoning",
}

SOURCE_ALIASES = {
    "program_generation": "normalized_program_candidates",
    "semantic_to_transformation_compiler": "semantic_compiler",
    "compiler": "semantic_compiler",
    "transformation_synthesis": "program_synthesis",
    "adaptive_reuse_layer": "adaptive_reuse",
    "repair": "repair_engine",
}

WINNER_DECLARATION_FIELDS = {
    "winner",
    "winner_source",
    "selected",
    "selected_candidate",
    "declared_winner",
}


class CandidateProposalGateway:
    """Normalize and gate raw source proposals before arena competition."""

    system_name = "candidate_proposal_gateway"

    def submit(
        self,
        proposals: list[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        raw = self._as_list(proposals)
        accepted = []
        rejected = []
        for index, proposal in enumerate(raw):
            normalized = self._proposal(proposal, index)
            if normalized["proposal_status"] == "PROPOSED":
                accepted.append(normalized)
            else:
                rejected.append(normalized)
        return {
            "system": self.system_name,
            "gateway_success": bool(accepted),
            "proposal_count": len(raw),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "proposals": accepted,
            "rejected_proposals": rejected,
            "timestamp": str(datetime.utcnow()),
        }

    def _proposal(self, proposal: Mapping[str, Any], index: int) -> dict[str, Any]:
        if not isinstance(proposal, Mapping):
            return self._rejected(index, "malformed_proposal_not_mapping", proposal)
        data = deepcopy(dict(proposal))
        original_source = _normalize(str(data.get("source") or "unknown"))
        source = self._source(data.get("source"))
        reasons = []
        if source not in SUPPORTED_SOURCES:
            reasons.append("unsupported_source")
        if self._declares_winner(data):
            reasons.append("source_attempted_direct_winner_declaration")
        program = data.get("program") or data.get("compiled_program") or {}
        if not isinstance(program, Mapping):
            reasons.append("program_not_mapping")
            program = {}
        steps = program.get("steps") or []
        if not isinstance(steps, list):
            reasons.append("program_steps_not_list")
            steps = []
        operation = data.get("operation") or self._operation_from_steps(steps)
        if not operation:
            reasons.append("missing_operation")
        status = "REJECTED" if reasons else "PROPOSED"
        candidate_id = data.get("candidate_id") or f"candidate:{source}:{index}"
        metadata = (
            deepcopy(data.get("metadata", {}))
            if isinstance(data.get("metadata", {}), Mapping)
            else {}
        )
        provenance_fields = self._provenance_fields(data, metadata)
        return {
            "candidate_id": _normalize_id(candidate_id),
            "source": source,
            "origin_source": original_source,
            "normalized_source": source,
            "hypothesis_id": data.get("hypothesis_id"),
            "intent": data.get("intent"),
            "operation": _normalize_operation(operation),
            "program": {
                "step_count": int(program.get("step_count", len(steps)) or 0),
                "steps": deepcopy(steps),
            },
            "source_confidence": _score(data.get("source_confidence", data.get("confidence", 0.0))),
            "semantic_support": _score(data.get("semantic_support", 0.0)),
            "truth_support": _score(data.get("truth_support", 0.0)),
            "context_support": _score(data.get("context_support", 0.0)),
            "dependency_support": _score(data.get("dependency_support", 0.0)),
            "identity_support": _score(data.get("identity_support", data.get("identity_confidence", 0.0))),
            "localization_support": _score(data.get("localization_support", 0.0)),
            "proposal_status": status,
            "rejection_reasons": reasons,
            **provenance_fields,
            "metadata": metadata,
            "provenance": {
                "original_source": data.get("source"),
                "origin_source": original_source,
                "normalized_source": source,
                "gateway_index": index,
                "received_fields": sorted(str(key) for key in data),
                **{
                    key: value
                    for key, value in provenance_fields.items()
                    if value is not None
                },
            },
        }

    def _rejected(self, index: int, reason: str, proposal: Any) -> dict[str, Any]:
        return {
            "candidate_id": f"candidate:rejected:{index}",
            "source": "unknown",
            "hypothesis_id": None,
            "intent": None,
            "operation": None,
            "program": {"step_count": 0, "steps": []},
            "source_confidence": 0.0,
            "semantic_support": 0.0,
            "truth_support": 0.0,
            "context_support": 0.0,
            "dependency_support": 0.0,
            "identity_support": 0.0,
            "localization_support": 0.0,
            "proposal_status": "REJECTED",
            "rejection_reasons": [reason],
            "metadata": {"raw_type": type(proposal).__name__},
            "provenance": {"gateway_index": index},
        }

    def _as_list(self, proposals: list[Mapping[str, Any]] | Mapping[str, Any] | None) -> list[Any]:
        if proposals is None:
            return []
        if isinstance(proposals, Mapping):
            return [proposals]
        if isinstance(proposals, (list, tuple)):
            return list(proposals)
        return [proposals]

    def _source(self, source: Any) -> str:
        normalized = _normalize(str(source or "unknown"))
        return SOURCE_ALIASES.get(normalized, normalized)

    def _operation_from_steps(self, steps: list[Any]) -> str | None:
        if steps and isinstance(steps[0], Mapping):
            return steps[0].get("operation") or steps[0].get("primitive")
        return None

    def _declares_winner(self, proposal: Mapping[str, Any]) -> bool:
        return any(field in proposal for field in WINNER_DECLARATION_FIELDS)

    def _provenance_fields(
        self,
        data: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        learned_object_id = (
            data.get("learned_object_id")
            or data.get("source_learned_object_id")
            or metadata.get("learned_object_id")
            or metadata.get("source_learned_object_id")
        )
        return {
            "learned_object_id": learned_object_id,
            "source_learned_object_id": (
                data.get("source_learned_object_id")
                or metadata.get("source_learned_object_id")
                or learned_object_id
            ),
            "learned_object_type": (
                data.get("learned_object_type")
                or metadata.get("learned_object_type")
            ),
            "reuse_proposal_id": (
                data.get("reuse_proposal_id")
                or metadata.get("reuse_proposal_id")
            ),
            "source_run_id": (
                data.get("source_run_id")
                or metadata.get("source_run_id")
            ),
            "target_run_id": (
                data.get("target_run_id")
                or metadata.get("target_run_id")
            ),
            "authority": data.get("authority") or metadata.get("authority"),
            "behavioral_authority": (
                data.get("behavioral_authority")
                or metadata.get("behavioral_authority")
            ),
            **self._route_lineage_fields(data, metadata),
        }

    def _route_lineage_fields(
        self,
        data: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        fields = {}
        for field in ROUTE_LINEAGE_FIELDS:
            value = data.get(field)
            if value is None:
                value = metadata.get(field)
            if value is not None:
                fields[field] = deepcopy(value)
        return fields


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_id(value: Any) -> str:
    return _normalize(value).replace(":", "_")


def _normalize_operation(value: Any) -> str | None:
    token = _normalize(value)
    aliases = {
        "remap_colors": "replace_color",
        "global_recolor": "replace_color",
        "preserve_input": "preserve_grid",
        "identity": "preserve_grid",
        "preserve_color": "preserve_colors",
        "preserve_color_mapping": "preserve_colors",
        "duplicate": "duplicate_object",
        "replicate": "duplicate_object",
        "translate_object": "translate",
    }
    return aliases.get(token, token) if token else None


candidate_proposal_gateway = CandidateProposalGateway()

__all__ = ["CandidateProposalGateway", "candidate_proposal_gateway"]
