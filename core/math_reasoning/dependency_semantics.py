"""Passive dependency semantics over mathematical ARC reasoning reports."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


SUPPORTED_SEMANTIC_RELATIONS = {
    "causes",
    "requires",
    "preserves",
    "transforms",
    "modifies",
    "expands",
    "propagates",
    "contracts",
    "transfers",
    "forks",
    "stabilizes",
    "constrains",
    "derives_from",
    "enables",
    "blocks",
}


PROCESS_TEMPLATES: dict[str, list[tuple[str, str, str, float]]] = {
    "growth": [
        ("growth", "expands", "topology", 0.90),
        ("topology_expansion", "requires", "local_shape", 0.88),
        ("growth", "preserves", "identity_persistence", 0.89),
        ("identity_persistence", "stabilizes", "object_core", 0.88),
    ],
    "replication": [
        ("replication", "requires", "identity_forking", 0.91),
        ("identity_forking", "causes", "object_count_increase", 0.92),
        ("object_count_increase", "requires", "topology_splitting", 0.89),
        ("topology_splitting", "preserves", "local_shape", 0.87),
    ],
    "propagation": [
        ("propagation", "propagates", "source_pattern_preserved", 0.89),
        ("propagation", "requires", "directional_motion", 0.88),
        ("directional_motion", "transforms", "position_change", 0.88),
        ("position_change", "preserves", "position_preservation", 0.84),
    ],
    "topological_growth": [
        ("topological_growth", "expands", "topology_expansion", 0.90),
        ("topology_expansion", "preserves", "local_shape", 0.87),
        ("local_shape", "stabilizes", "shape_preservation", 0.86),
    ],
    "directional_motion": [
        ("directional_motion", "transforms", "position_delta", 0.88),
        ("position_delta", "causes", "position_change", 0.88),
        ("position_change", "constrains", "position_preservation", 0.84),
    ],
}


PROCESS_MEMORY_RELATION_MAP = {
    "causes": "causes",
    "requires": "requires",
    "preserves": "preserves",
    "transforms": "modifies",
    "modifies": "modifies",
    "expands": "modifies",
    "propagates": "enables",
    "contracts": "modifies",
    "transfers": "enables",
    "forks": "causes",
    "stabilizes": "supports",
    "constrains": "depends_on",
    "derives_from": "derived_from",
    "enables": "enables",
    "blocks": "inhibits",
}


class DependencySemanticsEngine:
    """Convert math-layer observations into typed dependency semantics."""

    system_name = "dependency_semantics_engine"

    def analyze(
        self,
        concept: str,
        spatial_report: Mapping[str, Any] | None = None,
        graph_report: Mapping[str, Any] | None = None,
        set_report: Mapping[str, Any] | None = None,
        transformation_report: Mapping[str, Any] | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        evidence = self.merge_dependency_evidence(
            spatial_report,
            graph_report,
            set_report,
            transformation_report,
        )
        process_context = context or self.infer_process_context(concept, evidence)
        typed_dependencies = self._template_dependencies(concept, evidence, process_context)
        typed_dependencies.extend(self._observed_dependencies(concept, evidence, process_context))
        typed_dependencies = self._dedupe_dependencies(typed_dependencies)
        score = self.semantic_dependency_score(typed_dependencies)
        return {
            "system": self.system_name,
            "concept": str(concept),
            "typed_dependencies": typed_dependencies,
            "dependency_semantics_score": score,
            "semantic_dependency_signature": self.semantic_dependency_signature(
                typed_dependencies,
                process_context=process_context,
            ),
        }

    def infer_relation(self, source: str, target: str, evidence: Mapping[str, Any]) -> str:
        source_text = str(source).lower()
        target_text = str(target).lower()
        if evidence.get("blocks") or "block" in source_text or "blocked" in target_text:
            return "blocks"
        if evidence.get("requires") or "require" in target_text:
            return "requires"
        if evidence.get("preserves") or "preservation" in target_text or "preserved" in target_text:
            return "preserves"
        if evidence.get("object_count_change") or evidence.get("identity_split"):
            return "causes"
        if evidence.get("expanded") or evidence.get("added_items"):
            return "expands"
        if evidence.get("reduced") or evidence.get("removed_items"):
            return "contracts"
        if evidence.get("source_pattern_preserved"):
            return "propagates"
        if evidence.get("directional_motion") or evidence.get("position_change"):
            return "transforms"
        if evidence.get("identity_forking"):
            return "forks"
        return "derives_from"

    def build_typed_dependency(
        self,
        source: str,
        target: str,
        relation: str,
        confidence: float,
        evidence: Mapping[str, Any],
        contexts: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        relation_name = str(relation)
        if relation_name not in SUPPORTED_SEMANTIC_RELATIONS:
            relation_name = self.infer_relation(source, target, evidence)
        return {
            "source": str(source),
            "target": str(target),
            "relation": relation_name,
            "confidence": _clamp(confidence),
            "evidence": dict(evidence or {}),
            "contexts": sorted({str(context) for context in contexts or [] if context}),
        }

    def infer_process_context(self, concept: str, evidence: Mapping[str, Any]) -> str:
        concept_name = str(concept or "").strip() or "mathematical_reasoning"
        if concept_name in PROCESS_TEMPLATES:
            return f"{concept_name}_context"
        if evidence.get("object_count_change") or evidence.get("identity_split"):
            return "replication_context"
        if evidence.get("expanded") or evidence.get("topology_expansion"):
            return "growth_context"
        if evidence.get("directional_motion") or evidence.get("position_change"):
            return "propagation_context"
        return f"{concept_name}_context"

    def semantic_dependency_score(self, typed_dependencies: Iterable[Mapping[str, Any]]) -> float:
        dependencies = list(typed_dependencies or [])
        if not dependencies:
            return 0.0
        relation_diversity = len({item.get("relation") for item in dependencies}) / max(
            len(SUPPORTED_SEMANTIC_RELATIONS),
            1,
        )
        average_confidence = sum(float(item.get("confidence", 0.0)) for item in dependencies) / len(dependencies)
        evidence_coverage = sum(1 for item in dependencies if item.get("evidence")) / len(dependencies)
        return round(_clamp(average_confidence * 0.7 + evidence_coverage * 0.2 + relation_diversity * 0.1), 4)

    def semantic_dependency_signature(
        self,
        typed_dependencies: Iterable[Mapping[str, Any]],
        process_context: str | None = None,
    ) -> dict[str, Any]:
        dependencies = list(typed_dependencies or [])
        contexts = sorted(
            {
                context
                for item in dependencies
                for context in item.get("contexts", [])
            }
        )
        relation_types = sorted({str(item.get("relation")) for item in dependencies})
        return {
            "relation_types": relation_types,
            "process_context": process_context or (contexts[0] if contexts else None),
            "has_causal_chain": any(item.get("relation") == "causes" for item in dependencies)
            and len(dependencies) > 1,
        }

    def merge_dependency_evidence(self, *reports: Mapping[str, Any] | None) -> dict[str, Any]:
        evidence: dict[str, Any] = {
            "report_count": 0,
            "relation_types": [],
            "operator_types": [],
        }
        for report in reports:
            if not report:
                continue
            evidence["report_count"] += 1
            self._merge_spatial_evidence(evidence, report)
            self._merge_graph_evidence(evidence, report)
            self._merge_set_evidence(evidence, report)
            self._merge_transformation_evidence(evidence, report)
        evidence["relation_types"] = sorted(set(evidence["relation_types"]))
        evidence["operator_types"] = sorted(set(evidence["operator_types"]))
        return evidence

    def explain_dependency_chain(self, typed_dependencies: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        dependencies = list(typed_dependencies or [])
        steps = [
            {
                "step": index + 1,
                "source": item.get("source"),
                "relation": item.get("relation"),
                "target": item.get("target"),
                "explanation": (
                    f"{item.get('source')} {item.get('relation')} "
                    f"{item.get('target')} with confidence {item.get('confidence')}."
                ),
            }
            for index, item in enumerate(dependencies)
        ]
        return {
            "system": self.system_name,
            "chain_length": len(steps),
            "steps": steps,
            "summary": " -> ".join(
                [str(dependencies[0].get("source"))]
                + [str(item.get("target")) for item in dependencies]
            )
            if dependencies
            else "",
        }

    def export_to_process_dependency_memory(
        self,
        memory: Any,
        typed_dependencies: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        records = [self._memory_record(item) for item in typed_dependencies or []]
        if hasattr(memory, "ingest_chains") and callable(memory.ingest_chains):
            return memory.ingest_chains(records)
        if isinstance(memory, dict):
            memory.setdefault("typed_dependencies", []).extend(records)
            return {
                "system": "process_dependency_memory",
                "ingested_links": len(records),
                "process_dependency_links_loaded": len(memory["typed_dependencies"]),
            }
        if hasattr(memory, "append") and callable(memory.append):
            for record in records:
                memory.append(record)
            return {
                "system": "process_dependency_memory",
                "ingested_links": len(records),
                "process_dependency_links_loaded": len(memory),
            }
        raise TypeError("memory must expose ingest_chains, be a dict, or be appendable")

    def _template_dependencies(
        self,
        concept: str,
        evidence: Mapping[str, Any],
        context: str,
    ) -> list[dict[str, Any]]:
        dependencies = []
        for source, relation, target, confidence in PROCESS_TEMPLATES.get(str(concept), []):
            dependencies.append(
                self.build_typed_dependency(
                    source,
                    target,
                    relation,
                    confidence,
                    evidence,
                    contexts=[context],
                )
            )
        return dependencies

    def _observed_dependencies(
        self,
        concept: str,
        evidence: Mapping[str, Any],
        context: str,
    ) -> list[dict[str, Any]]:
        dependencies = []
        concept_name = str(concept)
        if evidence.get("object_count_change"):
            dependencies.append(
                self.build_typed_dependency(
                    concept_name,
                    "object_count_change",
                    "causes",
                    0.86,
                    evidence,
                    contexts=[context],
                )
            )
        if evidence.get("position_change"):
            dependencies.append(
                self.build_typed_dependency(
                    concept_name,
                    "position_change",
                    "transforms",
                    0.84,
                    evidence,
                    contexts=[context],
                )
            )
        if evidence.get("color_change"):
            dependencies.append(
                self.build_typed_dependency(
                    concept_name,
                    "color_state",
                    "transforms",
                    0.84,
                    evidence,
                    contexts=[context],
                )
            )
        if evidence.get("shape_preservation"):
            dependencies.append(
                self.build_typed_dependency(
                    concept_name,
                    "shape_preservation",
                    "preserves",
                    0.85,
                    evidence,
                    contexts=[context],
                )
            )
        if evidence.get("identity_persistence"):
            dependencies.append(
                self.build_typed_dependency(
                    concept_name,
                    "identity_persistence",
                    "preserves",
                    0.86,
                    evidence,
                    contexts=[context],
                )
            )
        if evidence.get("identity_forking"):
            dependencies.append(
                self.build_typed_dependency(
                    concept_name,
                    "identity_forking",
                    "forks",
                    0.87,
                    evidence,
                    contexts=[context],
                )
            )
        return dependencies

    def _dedupe_dependencies(self, dependencies: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
        for item in dependencies:
            key = (str(item["source"]), str(item["relation"]), str(item["target"]))
            existing = deduped.get(key)
            if existing is None or item.get("confidence", 0) > existing.get("confidence", 0):
                deduped[key] = dict(item)
        return [deduped[key] for key in sorted(deduped)]

    def _memory_record(self, dependency: Mapping[str, Any]) -> dict[str, Any]:
        semantic_relation = str(dependency.get("relation"))
        memory_relation = PROCESS_MEMORY_RELATION_MAP.get(semantic_relation, "supports")
        contexts = list(dependency.get("contexts", []))
        process = contexts[0].removesuffix("_context") if contexts else dependency.get("source")
        return {
            "process": process,
            "source": dependency.get("source"),
            "target": dependency.get("target"),
            "relation": memory_relation,
            "confidence": dependency.get("confidence", 0.0),
            "metadata": {
                "dependency_semantics_engine": True,
                "semantic_relation": semantic_relation,
                "contexts": contexts,
                "evidence": dict(dependency.get("evidence", {})),
            },
        }

    def _merge_spatial_evidence(self, evidence: dict[str, Any], report: Mapping[str, Any]) -> None:
        if report.get("system") != "spatial_relations_engine" and "spatial_signature" not in report:
            return
        relation_names = [item.get("relation") for item in report.get("relations", [])]
        evidence["relation_types"].extend(name for name in relation_names if name)
        evidence["directional_motion"] = any(
            name in {"shifted_by", "direction_vector", "relative_position"} for name in relation_names
        )
        evidence["position_change"] = any(name == "shifted_by" for name in relation_names)

    def _merge_graph_evidence(self, evidence: dict[str, Any], report: Mapping[str, Any]) -> None:
        if report.get("system") != "graph_relations_engine" and "graph_signature" not in report:
            return
        signature = report.get("graph_signature", {})
        evidence["graph_relation_types"] = signature.get("relation_types", [])
        evidence["connected_components"] = signature.get("connected_components")
        comparison = report.get("comparison", {})
        if comparison:
            evidence["object_count_change"] = comparison.get("node_count_change", 0) != 0
            evidence["added_nodes"] = comparison.get("added_nodes", [])
            evidence["removed_nodes"] = comparison.get("removed_nodes", [])

    def _merge_set_evidence(self, evidence: dict[str, Any], report: Mapping[str, Any]) -> None:
        if report.get("system") != "set_operations_engine":
            return
        evidence["added_items"] = report.get("added_items", [])
        evidence["removed_items"] = report.get("removed_items", [])
        evidence["preserved_items"] = report.get("preserved_items", [])
        evidence["expanded"] = report.get("relation") == "expanded"
        evidence["reduced"] = report.get("relation") == "reduced"
        evidence["color_change"] = bool(report.get("color_change", False))
        evidence["shape_preservation"] = bool(
            report.get("use_cases", {}).get("shape_cell_preservation", False)
            or report.get("preserved_items")
        )

    def _merge_transformation_evidence(self, evidence: dict[str, Any], report: Mapping[str, Any]) -> None:
        if report.get("system") != "transformation_algebra_engine":
            return
        signature = report.get("transformation_signature", {})
        algebra = report.get("transformation_algebra", {})
        operator_types = signature.get("operator_types", [])
        transformation_types = signature.get(
            "transformation_types",
            algebra.get("transformation_types", []),
        )
        invariants = signature.get("invariants", algebra.get("invariants", {}))
        evidence["operator_types"].extend(operator_types)
        evidence["transformation_types"] = sorted(
            {
                str(item)
                for item in transformation_types
                if item
            }
        )
        evidence["algebraic_signature"] = signature.get(
            "algebraic_signature",
            algebra.get("algebraic_signature"),
        )
        evidence["transformation_algebra_generated"] = bool(
            algebra.get("transformation_algebra_generated")
            or evidence.get("algebraic_signature")
        )
        evidence["object_count_change"] = bool(signature.get("changes_object_count", False))
        evidence["position_change"] = not bool(signature.get("preserves_position", True))
        evidence["color_change"] = not bool(signature.get("preserves_color", True))
        evidence["shape_preservation"] = bool(signature.get("preserves_shape", False))
        evidence["identity_split"] = bool(
            "duplicate" in operator_types
            or invariants.get("forks_identity")
            or "replication" in evidence["transformation_types"]
        )
        evidence["identity_forking"] = bool(invariants.get("forks_identity"))
        evidence["identity_persistence"] = bool(invariants.get("preserves_identity"))
        evidence["topology_expansion"] = bool(
            "expand" in operator_types
            or "duplicate" in operator_types
            or invariants.get("modifies_topology")
            or (
                set(evidence["transformation_types"])
                & {"growth", "topological_growth", "topology_expansion"}
            )
        )
        evidence["source_pattern_preserved"] = bool(
            evidence.get("shape_preservation")
            or invariants.get("preserves_shape")
            or "propagation" in evidence["transformation_types"]
        )


def _clamp(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return round(max(0.0, min(1.0, number)), 4)


__all__ = ["DependencySemanticsEngine"]
