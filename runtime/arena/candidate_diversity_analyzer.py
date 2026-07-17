"""Diversity analysis for candidate competition."""

from __future__ import annotations

from typing import Any, Mapping


class CandidateDiversityAnalyzer:
    """Measure meaningful diversity without counting identical programs twice."""

    system_name = "candidate_diversity_analyzer"

    def analyze(self, candidates: list[Mapping[str, Any]] | None) -> dict[str, Any]:
        rows = [dict(item) for item in candidates or [] if isinstance(item, Mapping)]
        candidate_count = len(rows)
        program_signatures = {item.get("program_signature") for item in rows if item.get("program_signature")}
        sources = {
            source
            for item in rows
            for source in item.get("sources", [item.get("source")])
            if source
        }
        operations = {item.get("operation") for item in rows if item.get("operation")}
        semantics = {
            item.get("intent") or item.get("metadata", {}).get("semantic_interpretation")
            for item in rows
            if item.get("intent") or item.get("metadata", {}).get("semantic_interpretation")
        }
        families = {
            item.get("metadata", {}).get("transformation_family") or item.get("operation")
            for item in rows
            if item.get("metadata", {}).get("transformation_family") or item.get("operation")
        }
        unique_program_count = len(program_signatures)
        operation_diversity = _ratio(len(operations), candidate_count)
        program_diversity = _ratio(unique_program_count, candidate_count)
        semantic_diversity = _ratio(len(semantics), candidate_count)
        source_diversity = _ratio(len(sources), candidate_count)
        family_diversity = _ratio(len(families), candidate_count)
        competition_diversity = round(
            operation_diversity * 0.22
            + program_diversity * 0.25
            + semantic_diversity * 0.18
            + source_diversity * 0.25
            + family_diversity * 0.10,
            4,
        )
        return {
            "system": self.system_name,
            "candidate_count": candidate_count,
            "unique_program_count": unique_program_count,
            "source_count": len(sources),
            "operation_diversity": round(operation_diversity, 4),
            "program_diversity": round(program_diversity, 4),
            "semantic_diversity": round(semantic_diversity, 4),
            "competition_diversity": competition_diversity,
            "diversity_sufficient": candidate_count >= 2 and len(sources) >= 2 and unique_program_count >= 2,
        }


def _ratio(numerator: int, denominator: int) -> float:
    return float(numerator) / max(int(denominator), 1)


candidate_diversity_analyzer = CandidateDiversityAnalyzer()

__all__ = ["CandidateDiversityAnalyzer", "candidate_diversity_analyzer"]
