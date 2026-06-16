"""Math-aware process context generation for passive reasoning evidence."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp
from core.process_abstraction import ProcessAbstractionLayer


PROCESS_CONTEXTS = {
    "growth",
    "replication",
    "propagation",
    "topological_growth",
    "directional_motion",
}

PROCESS_CONTEXT_STATUSES = {
    "PROCESS_CONTEXT_CANDIDATE",
    "PROCESS_CONTEXT_SUPPORTED",
    "PROCESS_CONTEXT_VALIDATED",
}


class ProcessContextGenerationEngine:
    """Generate process-native contexts from mathematical reasoning evidence."""

    system_name = "process_context_generation_engine"

    def generate(
        self,
        concept: str,
        math_reasoning_report: Mapping[str, Any] | None = None,
        dependency_semantics_report: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concept = _normalize(concept)
        abstraction = ProcessAbstractionLayer.get(concept)
        if abstraction is not None:
            concept = abstraction.concept
        if concept not in PROCESS_CONTEXTS:
            return {
                "system": self.system_name,
                "concept": concept,
                "process_context_generated": False,
                "process_context_ready": False,
                "status": "PROCESS_CONTEXT_REJECTED",
                "reason": "unsupported_process_concept",
            }
        return getattr(self, f"generate_{concept}_context")(
            math_reasoning_report,
            dependency_semantics_report=dependency_semantics_report,
            context=context,
        )

    def generate_context(
        self,
        concept: str,
        evidence: Mapping[str, Any] | None = None,
        math_reasoning_report: Mapping[str, Any] | None = None,
        dependency_semantics_report: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = math_reasoning_report or evidence or {}
        return self.generate(
            concept,
            report,
            dependency_semantics_report=dependency_semantics_report,
            context=context,
        )

    def generate_growth_context(
        self,
        math_reasoning_report,
        dependency_semantics_report=None,
        context=None,
    ):
        return self._build_context(
            "growth",
            math_reasoning_report,
            dependency_semantics_report,
            context,
        )

    def generate_replication_context(
        self,
        math_reasoning_report,
        dependency_semantics_report=None,
        context=None,
    ):
        return self._build_context(
            "replication",
            math_reasoning_report,
            dependency_semantics_report,
            context,
        )

    def generate_propagation_context(
        self,
        math_reasoning_report,
        dependency_semantics_report=None,
        context=None,
    ):
        return self._build_context(
            "propagation",
            math_reasoning_report,
            dependency_semantics_report,
            context,
        )

    def generate_topological_growth_context(
        self,
        math_reasoning_report,
        dependency_semantics_report=None,
        context=None,
    ):
        return self._build_context(
            "topological_growth",
            math_reasoning_report,
            dependency_semantics_report,
            context,
        )

    def generate_directional_motion_context(
        self,
        math_reasoning_report,
        dependency_semantics_report=None,
        context=None,
    ):
        return self._build_context(
            "directional_motion",
            math_reasoning_report,
            dependency_semantics_report,
            context,
        )

    def compute_process_context_confidence(self, context_report):
        evidence = context_report.get("supporting_math_evidence", {})
        dependency_score = clamp(evidence.get("dependency_semantics_score", 0.0))
        signal_count = sum(
            1
            for key in [
                "set_changes_detected",
                "graph_growth_detected",
                "transformations_detected",
                "typed_dependencies_generated",
                "transformation_algebra_generated",
                "process_signature_generated",
                "context_surface_promotion_ready",
            ]
            if evidence.get(key)
        )
        transfer_ratio = self._transfer_condition_ratio(context_report)
        algebra_match_bonus = 0.05 if evidence.get("process_algebra_match") else 0.0
        return clamp(
            dependency_score * 0.55
            + min(signal_count / 6.0, 1.0) * 0.30
            + transfer_ratio * 0.15
            + algebra_match_bonus
            + (0.06 if evidence.get("process_signature_match") else 0.0)
        )

    def validate_process_context(self, context_report):
        evidence = context_report.get("supporting_math_evidence", {})
        dependency_score = clamp(evidence.get("dependency_semantics_score", 0.0))
        evidence_sources = sum(
            1
            for key in [
                "set_changes_detected",
                "graph_growth_detected",
                "transformations_detected",
                "typed_dependencies_generated",
                "transformation_algebra_generated",
                "process_signature_generated",
                "context_surface_promotion_ready",
            ]
            if evidence.get(key)
        )
        identity_scope_leakage = bool(evidence.get("identity_scope_leakage_detected"))
        transfer_satisfied = self._transfer_condition_ratio(context_report) >= 1.0
        if not any(evidence.values()):
            return "PROCESS_CONTEXT_REJECTED"
        if (
            dependency_score >= 0.85
            and evidence.get("graph_growth_detected")
            and evidence.get("set_changes_detected")
            and evidence.get("transformations_detected")
            and evidence.get("transformation_algebra_generated")
            and evidence.get("process_signature_generated")
            and transfer_satisfied
            and (
                evidence.get("process_signature_match")
                or evidence.get("process_algebra_match")
                or evidence.get("context_surface_promotion_ready")
                or context_report.get("source_concept") == "directional_motion"
            )
            and not identity_scope_leakage
        ):
            return "PROCESS_CONTEXT_VALIDATED"
        if (
            evidence.get("typed_dependencies_generated")
            and dependency_score >= 0.75
            and evidence_sources >= 2
        ):
            return "PROCESS_CONTEXT_SUPPORTED"
        return "PROCESS_CONTEXT_CANDIDATE"

    def process_context_signature(self, context_report):
        return {
            "context_name": context_report.get("context_name"),
            "source_concept": context_report.get("source_concept"),
            "status": context_report.get("status"),
            "confidence": context_report.get("confidence", 0.0),
            "capability_count": len(context_report.get("capabilities", [])),
            "constraint_count": len(context_report.get("constraints", [])),
            "transfer_condition_count": len(
                context_report.get("transfer_conditions", [])
            ),
        }

    def explain_process_context(self, context_report):
        return {
            "system": self.system_name,
            "context_name": context_report.get("context_name"),
            "status": context_report.get("status"),
            "explanation": (
                f"{context_report.get('context_name')} is generated for "
                f"{context_report.get('source_concept')} with confidence "
                f"{context_report.get('confidence')}."
            ),
            "supporting_math_evidence": dict(
                context_report.get("supporting_math_evidence", {})
            ),
        }

    def generate_contexts(self, concepts=None):
        concepts = concepts or sorted(PROCESS_CONTEXTS)
        return [self.generate(concept) for concept in concepts]

    @classmethod
    def discovery_surfaces(cls):
        engine = cls()
        return {
            item["concept"]: {
                **item.get("discovery_surface", {}),
                "process_context": item.get("context_name"),
                "process_context_generated": item.get("process_context_generated"),
            }
            for item in engine.generate_contexts()
            if item.get("process_context_generated")
        }

    @classmethod
    def semantic_contexts(cls):
        engine = cls()
        contexts = {}
        for item in engine.generate_contexts():
            if not item.get("process_context_generated"):
                continue
            semantic = {
                "definition": item["definition"],
                "properties": list(item["properties"]),
                "capabilities": list(item["capabilities"]),
                "constraints": list(item["constraints"]),
                "implications": list(item["implications"]),
                "transfer_conditions": list(item["transfer_conditions"]),
                "validation_criteria": list(item.get("validation_criteria", [])),
                "process_context_generated": True,
                "process_context": item["context_name"],
            }
            contexts[item["concept"]] = semantic
            contexts[item["context_name"]] = semantic
        return contexts

    @classmethod
    def report(cls, concepts=None):
        contexts = cls().generate_contexts(concepts)
        generated = [
            item
            for item in contexts
            if item.get("process_context_generated")
        ]
        return {
            "system": "process_context_generation_engine",
            "process_context_count": len(generated),
            "process_contexts": generated,
            "process_context_generation_ready": bool(generated),
        }

    def _build_context(
        self,
        concept,
        math_reasoning_report=None,
        dependency_semantics_report=None,
        context=None,
    ):
        abstraction = ProcessAbstractionLayer.get(concept)
        math_report = math_reasoning_report if isinstance(math_reasoning_report, Mapping) else {}
        dependency_report = (
            dependency_semantics_report
            if isinstance(dependency_semantics_report, Mapping)
            else math_report.get("dependency_semantics_report", {})
        )
        supporting_evidence = self._supporting_math_evidence(
            math_report,
            dependency_report=dependency_report,
            context=context,
            source_concept=concept,
        )
        report = {
            "system": self.system_name,
            "concept": concept,
            "source_concept": concept,
            "generated_context": abstraction.context_id,
            "process_operator": abstraction.concept,
            "process_context": abstraction.context_id,
            "context_id": abstraction.context_id,
            "context_name": abstraction.context_id,
            "context_family": abstraction.context_family,
            "context_surface": abstraction.surface,
            "definition": abstraction.definition,
            "properties": list(abstraction.properties),
            "capabilities": list(abstraction.capabilities),
            "constraints": list(abstraction.constraints),
            "implications": list(abstraction.implications),
            "transfer_conditions": list(abstraction.transfer_conditions),
            "validation_criteria": list(abstraction.validation_criteria),
            "native_contexts": list(abstraction.native_contexts),
            "dependency_contexts": list(abstraction.dependency_contexts),
            "inherited_features": list(abstraction.inherited_features),
            "supporting_math_evidence": supporting_evidence,
            "concept_signature": supporting_evidence.get(
                "concept_signature",
            ),
            "signature_confidence": supporting_evidence.get(
                "signature_confidence",
                0.0,
            ),
            "signature_constraints": supporting_evidence.get(
                "signature_constraints",
                [],
            ),
            "signature_capabilities": supporting_evidence.get(
                "signature_capabilities",
                [],
            ),
            "signature_invariants": supporting_evidence.get(
                "signature_invariants",
                [],
            ),
            "confidence": 0.0,
            "status": "PROCESS_CONTEXT_CANDIDATE",
            "process_context_generated": True,
            "process_context_ready": True,
            "discovery_surface": abstraction.discovery_surface(),
            "semantic_context": abstraction.semantic_context(),
            "hierarchy_root": abstraction.context_id,
            "hierarchy_children": sorted(
                set(abstraction.native_contexts + (abstraction.concept,))
            ),
            "evidence": dict(supporting_evidence),
            "dependency_semantics_report": dict(dependency_report or {}),
        }
        report["confidence"] = self.compute_process_context_confidence(report)
        report["status"] = self.validate_process_context(report)
        report["signature"] = self.process_context_signature(report)
        return report

    def _supporting_math_evidence(
        self,
        math_report,
        dependency_report=None,
        context=None,
        source_concept=None,
    ):
        signature = math_report.get("math_reasoning_signature", {})
        graph_report = math_report.get("graph_report", {})
        set_report = math_report.get("set_report", {})
        transformation_report = math_report.get("transformation_report", {})
        process_signature_report = math_report.get("process_signature_report", {})
        dependency_report = (
            dependency_report
            if isinstance(dependency_report, Mapping)
            else math_report.get("dependency_semantics_report", {})
        )
        dependency_signature = dependency_report.get(
            "semantic_dependency_signature",
            {},
        )
        comparison = graph_report.get("comparison", {})
        context = context if isinstance(context, Mapping) else {}
        if (
            not process_signature_report
            and isinstance(context.get("process_signature_report"), Mapping)
        ):
            process_signature_report = context.get("process_signature_report", {})
        context_surface_report = (
            context.get("context_surface_report", {})
            if isinstance(context.get("context_surface_report"), Mapping)
            else {}
        )
        transformation_signature = transformation_report.get(
            "transformation_signature",
            {},
        )
        transformation_algebra = transformation_report.get(
            "transformation_algebra",
            {},
        )
        transformation_types = list(
            transformation_signature.get(
                "transformation_types",
                transformation_algebra.get("transformation_types", []),
            )
            or []
        )
        process_signature_report = (
            process_signature_report
            if isinstance(process_signature_report, Mapping)
            else {}
        )
        signature_id = process_signature_report.get("signature_id")
        signature_context = process_signature_report.get(
            "canonical_process_context",
            process_signature_report.get("signature_context"),
        )
        concept = _normalize(
            source_concept
            or
            math_report.get(
                "concept",
                context.get("concept", context.get("source_concept")),
            )
        )
        return {
            "set_changes_detected": bool(
                signature.get("set_changes_detected")
                or set_report.get("set_changes_detected")
                or set_report.get("added_items")
            ),
            "graph_growth_detected": bool(
                comparison.get("node_count_change", 0) > 0
                or comparison.get("edge_count_change", 0) > 0
            ),
            "typed_dependencies_generated": bool(
                signature.get("typed_dependencies_generated")
                or dependency_report.get("typed_dependencies")
            ),
            "transformations_detected": bool(
                signature.get("transformations_detected")
                or transformation_report.get("operators")
            ),
            "transformation_algebra_generated": bool(
                transformation_algebra.get("transformation_algebra_generated")
                or transformation_signature.get("algebraic_signature")
            ),
            "transformation_types": transformation_types,
            "primary_transformation_type": transformation_signature.get(
                "primary_transformation_type",
                transformation_algebra.get("primary_transformation_type"),
            ),
            "transformation_invariants": dict(
                transformation_signature.get(
                    "invariants",
                    transformation_algebra.get("invariants", {}),
                )
            ),
            "algebraic_signature": transformation_signature.get(
                "algebraic_signature",
                transformation_algebra.get("algebraic_signature"),
            ),
            "process_algebra_match": self._process_algebra_match(
                concept,
                transformation_types,
            ),
            "process_signature_generated": bool(
                process_signature_report.get("process_signature_generated")
            ),
            "process_signature_id": signature_id,
            "process_signature_context": signature_context,
            "process_signature_strength": clamp(
                process_signature_report.get(
                    "signature_confidence",
                    process_signature_report.get("signature_strength", 0.0),
                )
            ),
            "concept_signature": process_signature_report.get(
                "concept_signature",
            ),
            "signature_confidence": clamp(
                process_signature_report.get(
                    "signature_confidence",
                    process_signature_report.get("signature_strength", 0.0),
                )
            ),
            "signature_constraints": list(
                process_signature_report.get("signature_constraints", [])
            ),
            "signature_capabilities": list(
                process_signature_report.get("signature_capabilities", [])
            ),
            "signature_invariants": list(
                process_signature_report.get("signature_invariants", [])
            ),
            "process_signature_tokens": list(
                process_signature_report.get("signature_tokens", [])
            ),
            "process_signature_match": self._process_signature_match(
                concept,
                signature_id,
                signature_context,
            ),
            "context_surface_score": clamp(
                context_surface_report.get("context_surface_score", 0.0)
            ),
            "context_surface_saturation": clamp(
                context_surface_report.get("context_saturation", 0.0)
            ),
            "context_surface_promotion_ready": bool(
                context_surface_report.get("promotion_readiness")
            ),
            "context_surface_missing_contexts": list(
                context_surface_report.get("missing_contexts", [])
            ),
            "dependency_semantics_score": clamp(
                dependency_report.get("dependency_semantics_score", 0.0)
            ),
            "has_causal_chain": bool(
                dependency_signature.get("has_causal_chain")
            ),
            "identity_scope_leakage_detected": bool(
                context.get("identity_scope_leakage_detected", False)
                or transformation_algebra.get(
                    "identity_scope_leakage_detected",
                    False,
                )
                or process_signature_report.get(
                    "identity_scope_leakage_detected",
                    False,
                )
            ),
        }

    def _transfer_condition_ratio(self, context_report):
        evidence = context_report.get("supporting_math_evidence", {})
        conditions = context_report.get("transfer_conditions", [])
        if not conditions:
            return 1.0
        satisfied = 0
        for condition in conditions:
            normalized = _normalize(condition)
            if "dependency" in normalized and evidence.get("typed_dependencies_generated"):
                satisfied += 1
            elif "object_count" in normalized and (
                evidence.get("graph_growth_detected")
                or evidence.get("set_changes_detected")
            ):
                satisfied += 1
            elif "source" in normalized and evidence.get("typed_dependencies_generated"):
                satisfied += 1
            elif "direction" in normalized and evidence.get("transformations_detected"):
                satisfied += 1
            elif "shape" in normalized and evidence.get("set_changes_detected"):
                satisfied += 1
            elif "growth" in normalized and evidence.get("set_changes_detected"):
                satisfied += 1
        return clamp(satisfied / len(conditions))

    def _process_algebra_match(self, concept, transformation_types):
        type_set = {str(item) for item in transformation_types or [] if item}
        if concept == "directional_motion":
            return bool(type_set & {"translation", "propagation"})
        if concept == "growth":
            return bool(type_set & {"growth", "topology_expansion"})
        if concept == "topological_growth":
            return bool(type_set & {"topological_growth", "topology_expansion"})
        return concept in type_set

    def _process_signature_match(self, concept, signature_id, signature_context):
        expected_context = f"{concept}_context"
        expected_signature = f"{concept}_signature"
        return bool(
            signature_context == expected_context
            or signature_id == expected_signature
        )

def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


__all__ = [
    "PROCESS_CONTEXT_STATUSES",
    "PROCESS_CONTEXTS",
    "ProcessContextGenerationEngine",
]
