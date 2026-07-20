"""Canonical candidate normalization and equivalence collapsing."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping


class CandidateNormalizer:
    """Convert proposals into canonical candidates and merge equivalents."""

    system_name = "candidate_normalizer"

    def normalize(self, proposals: list[Mapping[str, Any]] | None) -> dict[str, Any]:
        canonical = [self._candidate(item) for item in proposals or [] if isinstance(item, Mapping)]
        groups: dict[str, list[dict[str, Any]]] = {}
        for candidate in canonical:
            groups.setdefault(candidate["program_signature"], []).append(candidate)
        normalized = []
        equivalent_groups = []
        collapsed = 0
        for signature, group in groups.items():
            if len(group) == 1:
                normalized.append(group[0])
                continue
            merged = self._merge_group(group)
            normalized.append(merged)
            collapsed += len(group) - 1
            equivalent_groups.append({
                "program_signature": signature,
                "candidate_ids": [item["candidate_id"] for item in group],
                "sources": sorted({source for item in group for source in item.get("sources", [item.get("source")])}),
                "merged_candidate_id": merged["candidate_id"],
            })
        normalized.sort(key=lambda item: item["candidate_id"])
        return {
            "system": self.system_name,
            "normalized_candidates": normalized,
            "duplicate_candidates_collapsed": collapsed,
            "equivalent_candidate_groups": equivalent_groups,
            "normalization_success": True,
        }

    def _candidate(self, proposal: Mapping[str, Any]) -> dict[str, Any]:
        program = proposal.get("program") if isinstance(proposal.get("program"), Mapping) else {}
        steps = program.get("steps") if isinstance(program.get("steps"), list) else []
        normalized_steps = [self._step(step) for step in steps if isinstance(step, Mapping)]
        operation = _normalize_operation(proposal.get("operation") or (normalized_steps[0].get("operation") if normalized_steps else None))
        program = {
            "step_count": int(program.get("step_count", len(normalized_steps)) or 0),
            "steps": normalized_steps,
        }
        source = _normalize(proposal.get("source"))
        origin_source = _normalize(
            proposal.get("origin_source")
            or (proposal.get("provenance") or {}).get("origin_source")
            or (proposal.get("provenance") or {}).get("original_source")
            or source
        )
        candidate = deepcopy(dict(proposal))
        candidate.update({
            "candidate_id": str(proposal.get("candidate_id") or f"candidate:{source}:unknown"),
            "source": source,
            "sources": [source] if source else [],
            "origin_source": origin_source,
            "origin_sources": [origin_source] if origin_source else [],
            "normalized_source": source,
            "normalized_sources": [source] if source else [],
            "operation": operation,
            "program": program,
            "source_confidence": _score(proposal.get("source_confidence", 0.0)),
            "semantic_support": _score(proposal.get("semantic_support", 0.0)),
            "truth_support": _score(proposal.get("truth_support", 0.0)),
            "context_support": _score(proposal.get("context_support", 0.0)),
            "dependency_support": _score(proposal.get("dependency_support", 0.0)),
            "identity_support": _score(proposal.get("identity_support", 0.0)),
            "localization_support": _score(proposal.get("localization_support", 0.0)),
            "program_signature": self._program_signature(program),
            "provenance_history": [deepcopy(proposal.get("provenance", {}))],
            "supporting_hypotheses": [
                proposal.get("hypothesis_id")
            ] if proposal.get("hypothesis_id") else [],
            "confidence_contributions": {
                source: _score(proposal.get("source_confidence", 0.0))
            } if source else {},
        })
        return candidate

    def _step(self, step: Mapping[str, Any]) -> dict[str, Any]:
        operation = _normalize_operation(step.get("operation") or step.get("primitive"))
        parameters = step.get("parameters") if isinstance(step.get("parameters"), Mapping) else {}
        return {
            "operation": operation,
            "parameters": deepcopy(dict(parameters)),
        }

    def _merge_group(self, group: list[dict[str, Any]]) -> dict[str, Any]:
        base = deepcopy(group[0])
        sources = sorted({source for item in group for source in item.get("sources", [])})
        origin_sources = sorted({
            source for item in group
            for source in item.get("origin_sources", [item.get("origin_source")])
            if source
        })
        normalized_sources = sorted({
            source for item in group
            for source in item.get("normalized_sources", [item.get("normalized_source")])
            if source
        })
        hypotheses = sorted({
            hypothesis for item in group
            for hypothesis in item.get("supporting_hypotheses", [])
            if hypothesis
        })
        base["candidate_id"] = "merged:" + base["program_signature"][:16]
        base["sources"] = sources
        base["source"] = sources[0] if sources else base.get("source")
        base["origin_sources"] = origin_sources
        base["origin_source"] = origin_sources[0] if origin_sources else base.get("origin_source")
        base["normalized_sources"] = normalized_sources
        base["normalized_source"] = normalized_sources[0] if normalized_sources else base.get("normalized_source")
        base["supporting_hypotheses"] = hypotheses
        base["source_confidence"] = max(_score(item.get("source_confidence")) for item in group)
        for field in (
            "semantic_support",
            "truth_support",
            "context_support",
            "dependency_support",
            "identity_support",
            "localization_support",
        ):
            base[field] = round(sum(_score(item.get(field)) for item in group) / len(group), 4)
        base["provenance_history"] = [
            history for item in group
            for history in item.get("provenance_history", [])
        ]
        base["confidence_contributions"] = {
            item.get("source"): _score(item.get("source_confidence"))
            for item in group
            if item.get("source")
        }
        base["equivalent_candidate_ids"] = [item["candidate_id"] for item in group]
        return base

    def _program_signature(self, program: Mapping[str, Any]) -> str:
        payload = json.dumps(program, sort_keys=True, separators=(",", ":"))
        return str(abs(hash(payload)))


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_operation(value: Any) -> str | None:
    token = _normalize(value)
    aliases = {
        "remap_colors": "replace_color",
        "global_recolor": "replace_color",
        "preserve_input": "preserve_grid",
        "identity": "preserve_grid",
        "duplicate": "duplicate_object",
        "replicate": "duplicate_object",
        "translate_object": "translate",
    }
    return aliases.get(token, token) if token else None


candidate_normalizer = CandidateNormalizer()

__all__ = ["CandidateNormalizer", "candidate_normalizer"]
