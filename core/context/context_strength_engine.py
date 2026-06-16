"""Optional additive context strength from math reasoning evidence."""

from __future__ import annotations

from typing import Any, Mapping

from core.context.process_context_generation import PROCESS_CONTEXT_STATUSES
from core.epistemic_models import clamp
from runtime.context.context_governance_registry import (
    context_from_governance_report,
    governance_process_report,
)
from runtime.context.process_context_registry import (
    context_from_registry_report,
    process_report_from_registry_context,
)


PRESERVATION_CONTEXTS = {
    "shape_context",
    "color_context",
    "symmetry_context",
    "position_context",
    "topology_context",
}

PROCESS_CONTEXTS = {
    "growth_context",
    "replication_context",
    "propagation_context",
    "topological_growth_context",
    "directional_motion_context",
    "motion_context",
}


class ContextStrengthEngine:
    """Combine existing context strength with passive process-context evidence."""

    system_name = "context_strength_engine"

    def consume_math_reasoning(
        self,
        base_context_strength: float,
        math_reasoning_report: Mapping[str, Any] | None = None,
        process_context_report: Mapping[str, Any] | None = None,
        dependency_semantics_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        base = clamp(base_context_strength)
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        rejection_reasons = []
        used_evidence = []
        math_report = math_reasoning_report if isinstance(math_reasoning_report, Mapping) else {}
        process_report = process_context_report if isinstance(process_context_report, Mapping) else {}
        dependency_report = dependency_semantics_report if isinstance(dependency_semantics_report, Mapping) else {}
        registry_context = self._registry_context(runtime_context)
        if not process_report and registry_context:
            process_report = process_report_from_registry_context(registry_context)
        governance_context = self._governance_context(runtime_context)
        if not process_report and governance_context:
            process_report = governance_process_report(governance_context)
        if not dependency_report and process_report:
            dependency_report = self._registry_dependency_report(process_report)

        if self._global_identity_split(runtime_context):
            rejection_reasons.append("identity_runtime_split_is_global")
        if not process_report:
            rejection_reasons.append("process_context_report_missing")
        elif process_report.get("status") not in PROCESS_CONTEXT_STATUSES:
            rejection_reasons.append("process_context_status_invalid")
        elif self._process_context_conflicts(process_report, runtime_context):
            rejection_reasons.append("process_context_conflicts_with_preservation_context")
        elif self._identity_scope_leakage(process_report):
            rejection_reasons.append("identity_scope_leakage_detected")
        dependency_score = dependency_report.get("dependency_semantics_score")
        if dependency_score is None:
            rejection_reasons.append("dependency_semantics_score_missing")
        signature = math_report.get("math_reasoning_signature", {})
        if not signature.get("typed_dependencies_generated"):
            rejection_reasons.append("typed_dependencies_not_generated")

        process_context_strength = 0.0
        if not rejection_reasons:
            dependency_score = clamp(dependency_score)
            context_surface_report = self._context_surface_report(runtime_context)
            dependency_coherence_report = self._dependency_coherence_report(
                runtime_context
            )
            if dependency_score > 0:
                used_evidence.append("typed_dependencies")
            if self._graph_growth(math_report):
                used_evidence.append("graph_growth")
            if self._set_growth(math_report):
                used_evidence.append("set_growth")
            if signature.get("transformations_detected"):
                used_evidence.append("transformation_signature")
            if self._transformation_algebra_generated(process_report, math_report):
                used_evidence.append("transformation_algebra")
            if self._process_signature_generated(process_report, math_report):
                used_evidence.append("process_signature")
            if self._concept_signature_generated(process_report, math_report):
                used_evidence.append("canonical_signature")
            if self._context_surface_ready(context_surface_report):
                used_evidence.append("context_surface")
            if self._dependency_coherence_ready(dependency_coherence_report):
                used_evidence.append("dependency_coherence")
            if self._transition_sequence_generated(process_report):
                used_evidence.append("process_transition_sequence")
            if self._preconditions_identified(process_report):
                used_evidence.append("process_preconditions")
            if self._postconditions_identified(process_report):
                used_evidence.append("process_postconditions")
            if self._temporal_state_sequence_generated(process_report):
                used_evidence.append("temporal_state_sequence")
            if self._final_state_identified(process_report):
                used_evidence.append("temporal_final_state")
            process_context_strength = self._process_context_strength(
                dependency_score,
                used_evidence,
                process_report,
                context_surface_report,
                dependency_coherence_report,
            )

        final_strength = clamp(min(base + process_context_strength, 0.97))
        return {
            "system": self.system_name,
            "base_context_strength": base,
            "process_context_strength": process_context_strength,
            "final_context_strength": final_strength,
            "math_reasoning_used": process_context_strength > 0.0,
            "used_evidence": used_evidence,
            "math_reasoning_consumed": process_context_strength > 0.0,
            "process_context_generated": bool(
                process_report.get("process_context_generated")
            ),
            "process_context_status": process_report.get("status"),
            "dependency_semantics_score": clamp(dependency_score or 0.0),
            "context_strength_before_math": base,
            "context_strength_after_math": final_strength,
            "math_reasoning_evidence_used": used_evidence,
            "math_reasoning_evidence_rejected": bool(rejection_reasons),
            "evidence_used": used_evidence,
            "evidence_rejected": bool(rejection_reasons),
            "rejection_reasons": rejection_reasons,
            "context_surface_report": self._context_surface_report(
                runtime_context
            ),
            "dependency_coherence_report": self._dependency_coherence_report(
                runtime_context
            ),
        }

    def _process_context_strength(
        self,
        dependency_score,
        used_evidence,
        process_report,
        context_surface_report=None,
        dependency_coherence_report=None,
    ):
        evidence_score = min(len(used_evidence) / 10.0, 1.0)
        status_bonus = {
            "PROCESS_CONTEXT_CANDIDATE": 0.03,
            "PROCESS_CONTEXT_SUPPORTED": 0.06,
            "PROCESS_CONTEXT_VALIDATED": 0.08,
        }.get(process_report.get("status"), 0.0)
        process_confidence = clamp(process_report.get("confidence", 0.0))
        signature_strength = clamp(
            process_report.get(
                "supporting_math_evidence",
                {},
            ).get("process_signature_strength", 0.0)
        )
        surface_strength = clamp(
            (context_surface_report or {}).get(
                "context_strength_estimate",
                0.0,
            )
        )
        coherence_strength = clamp(
            (dependency_coherence_report or {}).get(
                "dependency_coherence",
                0.0,
            )
        ) if self._dependency_coherence_ready(
            dependency_coherence_report or {}
        ) else 0.0
        temporal_strength = clamp(
            process_report.get(
                "process_context_strength",
                process_report.get(
                    "temporal_consistency",
                    process_report.get("temporal_ordering", 0.0),
                ),
            )
        )
        temporal_consistency = clamp(
            process_report.get("temporal_consistency", 0.0)
        )
        return clamp(
            min(
                dependency_score * 0.10
                + evidence_score * 0.08
                + process_confidence * 0.05
                + status_bonus
                + signature_strength * 0.04
                + surface_strength * 0.10
                + coherence_strength * 0.08
                + temporal_strength * 0.12
                + temporal_consistency * 0.04,
                0.48,
            )
        )

    def _context_surface_report(self, runtime_context):
        report = runtime_context.get("context_surface_report", {})
        return report if isinstance(report, Mapping) else {}

    def _context_surface_ready(self, report):
        if not isinstance(report, Mapping):
            return False
        return bool(
            report.get("promotion_readiness") is True
            and not report.get("identity_scope_leakage_detected", False)
            and clamp(report.get("context_surface_score", 0.0)) >= 0.68
        )

    def _dependency_coherence_report(self, runtime_context):
        report = runtime_context.get("dependency_coherence_report", {})
        return report if isinstance(report, Mapping) else {}

    def _dependency_coherence_ready(self, report):
        if not isinstance(report, Mapping):
            return False
        return bool(
            clamp(report.get("dependency_coherence", 0.0)) >= 0.90
            and not report.get("hidden_contradictions")
            and report.get("stable_dependencies")
        )

    def _registry_context(self, runtime_context):
        report = runtime_context.get("process_context_registry_report", {})
        if not isinstance(report, Mapping):
            return {}
        return context_from_registry_report(
            report,
            concept=runtime_context.get("concept"),
            context_name=runtime_context.get("process_context"),
        )

    def _governance_context(self, runtime_context):
        report = runtime_context.get("context_governance_report", {})
        if not isinstance(report, Mapping):
            return {}
        return context_from_governance_report(
            report,
            concept=runtime_context.get("concept"),
            context_id=runtime_context.get("process_context"),
        )

    def _registry_dependency_report(self, process_report):
        transitions = [
            item
            for item in process_report.get("transitions", [])
            if isinstance(item, Mapping)
        ]
        typed_dependencies = [
            {
                "source": item.get("from"),
                "target": item.get("to"),
                "relation": item.get("transition", "transitions_to"),
                "confidence": item.get("confidence", 0.0),
                "contexts": [process_report.get("context_name")],
                "temporal_step": item.get("step"),
            }
            for item in transitions
        ]
        return {
            "system": "process_context_registry",
            "dependency_semantics_score": clamp(
                process_report.get("process_context_strength", 0.0)
            ),
            "typed_dependencies": typed_dependencies,
            "semantic_dependency_signature": {
                "relation_types": sorted(
                    {
                        str(item.get("relation"))
                        for item in typed_dependencies
                        if item.get("relation")
                    }
                ),
                "process_context": process_report.get("context_name"),
                "has_causal_chain": bool(typed_dependencies),
                "temporal_transition_context": True,
                "state_transition_state_model": True,
                "registry_consolidated_context": True,
            },
        }

    def _transformation_algebra_generated(self, process_report, math_report):
        evidence = process_report.get("supporting_math_evidence", {})
        if evidence.get("transformation_algebra_generated"):
            return True
        transformation_report = math_report.get("transformation_report", {})
        algebra = transformation_report.get("transformation_algebra", {})
        signature = transformation_report.get("transformation_signature", {})
        return bool(
            algebra.get("transformation_algebra_generated")
            or signature.get("algebraic_signature")
        )

    def _process_signature_generated(self, process_report, math_report):
        evidence = process_report.get("supporting_math_evidence", {})
        if evidence.get("process_signature_generated"):
            return True
        signature_report = math_report.get("process_signature_report", {})
        if not isinstance(signature_report, Mapping):
            return False
        return bool(signature_report.get("process_signature_generated"))

    def _concept_signature_generated(self, process_report, math_report):
        evidence = process_report.get("supporting_math_evidence", {})
        if evidence.get("concept_signature"):
            return True
        signature_report = math_report.get("process_signature_report", {})
        if not isinstance(signature_report, Mapping):
            return False
        return bool(signature_report.get("concept_signature"))

    def _transition_sequence_generated(self, process_report):
        evidence = process_report.get("supporting_math_evidence", {})
        return bool(
            process_report.get("transition_steps")
            or process_report.get("transitions")
            or evidence.get("transition_sequence_generated")
            or evidence.get("temporal_transitions_identified")
        )

    def _preconditions_identified(self, process_report):
        evidence = process_report.get("supporting_math_evidence", {})
        return bool(
            process_report.get("preconditions")
            or process_report.get("initial_state")
            or evidence.get("preconditions_identified")
            or evidence.get("initial_state_identified")
        )

    def _postconditions_identified(self, process_report):
        evidence = process_report.get("supporting_math_evidence", {})
        return bool(
            process_report.get("postconditions")
            or evidence.get("postconditions_identified")
        )

    def _temporal_state_sequence_generated(self, process_report):
        evidence = process_report.get("supporting_math_evidence", {})
        return bool(
            process_report.get("initial_state")
            and process_report.get("transitions")
            and process_report.get("final_state")
        ) or bool(evidence.get("temporal_state_sequence_generated"))

    def _final_state_identified(self, process_report):
        evidence = process_report.get("supporting_math_evidence", {})
        return bool(
            process_report.get("final_state")
            or evidence.get("final_state_identified")
        )

    def _identity_scope_leakage(self, process_report):
        evidence = process_report.get("supporting_math_evidence", {})
        if evidence.get("identity_scope_leakage_detected"):
            return True
        invariants = evidence.get("transformation_invariants", {})
        if not isinstance(invariants, Mapping):
            return False
        return bool(
            invariants.get("preserves_identity")
            and invariants.get("forks_identity")
        )

    def _global_identity_split(self, runtime_context):
        if runtime_context.get("identity_runtime_split") == "global":
            return True
        identity_report = runtime_context.get("identity_runtime_report", {})
        if not isinstance(identity_report, Mapping):
            return False
        return identity_report.get("identity_runtime_split") == "global"

    def _graph_growth(self, math_report):
        comparison = math_report.get("graph_report", {}).get("comparison", {})
        return (
            comparison.get("node_count_change", 0) > 0
            or comparison.get("edge_count_change", 0) > 0
        )

    def _set_growth(self, math_report):
        set_report = math_report.get("set_report", {})
        return bool(
            set_report.get("set_changes_detected")
            or set_report.get("added_items")
            or set_report.get("relation") == "expanded"
        )

    def _process_context_conflicts(self, process_report, runtime_context):
        process_context = str(
            process_report.get(
                "context_name",
                process_report.get("generated_context", ""),
            )
        )
        if process_context in PRESERVATION_CONTEXTS:
            return True
        active_contexts = runtime_context.get("active_contexts", [])
        if isinstance(active_contexts, str):
            active_contexts = [active_contexts]
        semantic_context = runtime_context.get("semantic_context", {})
        if isinstance(semantic_context, Mapping):
            active_contexts = list(active_contexts) + [
                semantic_context.get("context"),
                semantic_context.get("semantic_context"),
            ]
        active_context_set = {
            str(context)
            for context in active_contexts
            if context
        }
        if process_context in PROCESS_CONTEXTS:
            return bool(active_context_set & PRESERVATION_CONTEXTS)
        return False


__all__ = ["ContextStrengthEngine"]
