"""Reason over typed process dependencies for governance."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


class ProcessDependencyReasoner:
    """Explain dependency relevance and dependency-aware contradictions."""

    system_name = "process_dependency_reasoner"

    def reason(
        self,
        process_family: str,
        dependency_report: Mapping[str, Any],
        observed_contradictions: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        links = list(dependency_report.get("typed_dependency_relations", []) or [])
        observed = {str(item) for item in observed_contradictions or [] if item}
        forbids = [
            link for link in links if link.get("dependency_type") == "forbids"
        ]
        exact_blockers = [
            link.get("target")
            for link in forbids
            if link.get("target") in observed
        ]
        support_links = [
            link
            for link in links
            if link.get("dependency_type")
            in {
                "requires",
                "preserves",
                "modifies",
                "enables",
                "causes",
                "constrains",
                "derives_from",
            }
        ]
        confidence = (
            sum(clamp(link.get("confidence", 0.0)) for link in links)
            / len(links)
            if links
            else 0.0
        )
        reasoned_chain = dependency_report.get("reasoned_dependency_chain", {})
        if not isinstance(reasoned_chain, Mapping):
            reasoned_chain = {}
        relevant = len(links)
        loaded = int(
            dependency_report.get(
                "relevant_process_dependency_links",
                relevant,
            )
            or relevant
        )
        used = int(
            reasoned_chain.get(
                "process_dependency_links_used",
                dependency_report.get("process_dependency_links_used", relevant),
            )
            or 0
        )
        usage_rate = used / max(loaded, 1)
        return {
            "system": self.system_name,
            "typed_process_dependencies": "enabled",
            "process_family": process_family,
            "dependency_semantics_score": round(
                clamp(reasoned_chain.get("coherence", confidence)),
                4,
            ),
            "reasoned_dependency_chain": reasoned_chain,
            "dependency_chain_depth": reasoned_chain.get(
                "dependency_chain_depth",
                dependency_report.get("dependency_chain_depth", 0),
            ),
            "dependency_chain_coverage": reasoned_chain.get(
                "dependency_chain_coverage",
                dependency_report.get("dependency_chain_coverage", 0.0),
            ),
            "dependency_coherence_average": reasoned_chain.get(
                "dependency_coherence_average",
                dependency_report.get("dependency_coherence_average", 0.0),
            ),
            "process_dependency_links_used": used,
            "relevant_process_dependency_links": loaded,
            "process_dependency_relevance_rate": round(usage_rate, 4),
            "process_dependency_links_used_above_threshold": usage_rate > 0.75,
            "supporting_typed_dependencies": support_links,
            "forbidden_dependencies": forbids,
            "exact_blocker": exact_blockers,
            "contradiction_governance_blocked_by_typed_dependency":
            bool(exact_blockers),
            "typed_dependency_explanation": [
                f"{link.get('source')} --{link.get('dependency_type')}--> "
                f"{link.get('target')}"
                for link in links
            ],
        }


__all__ = ["ProcessDependencyReasoner"]
