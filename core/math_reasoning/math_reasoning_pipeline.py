"""Passive integrated mathematical reasoning pipeline for ARC observations."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.math_reasoning.dependency_semantics import DependencySemanticsEngine
from core.math_reasoning.graph_relations import GraphRelationsEngine
from core.math_reasoning.process_signature import ProcessSignatureEngine
from core.math_reasoning.set_operations import SetOperationsEngine
from core.math_reasoning.spatial_relations import SpatialRelationsEngine
from core.math_reasoning.transformation_algebra import TransformationAlgebraEngine


class MathematicalReasoningPipeline:
    """Run the five mathematical reasoning engines as passive evidence layers."""

    system_name = "mathematical_reasoning_pipeline"

    def __init__(
        self,
        spatial_engine: SpatialRelationsEngine | None = None,
        graph_engine: GraphRelationsEngine | None = None,
        set_engine: SetOperationsEngine | None = None,
        transformation_engine: TransformationAlgebraEngine | None = None,
        process_signature_engine: ProcessSignatureEngine | None = None,
        dependency_engine: DependencySemanticsEngine | None = None,
        object_extractor: Any | None = None,
    ) -> None:
        self.spatial_engine = spatial_engine or SpatialRelationsEngine()
        self.graph_engine = graph_engine or GraphRelationsEngine()
        self.set_engine = set_engine or SetOperationsEngine()
        self.transformation_engine = (
            transformation_engine or TransformationAlgebraEngine()
        )
        self.process_signature_engine = (
            process_signature_engine or ProcessSignatureEngine()
        )
        self.dependency_engine = dependency_engine or DependencySemanticsEngine()
        self.object_extractor = object_extractor

    def analyze_task(
        self,
        task_id: str,
        input_grid: Any,
        output_grid: Any | None = None,
        input_objects: Iterable[Mapping[str, Any]] | None = None,
        output_objects: Iterable[Mapping[str, Any]] | None = None,
        concept: str | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        input_object_list = self._objects_from(input_objects, input_grid)
        output_object_list = self._objects_from(output_objects, output_grid)
        reports = self.analyze_objects(
            input_object_list,
            output_object_list if output_grid is not None or output_objects is not None else None,
            input_grid=input_grid,
            output_grid=output_grid,
            concept=concept,
            context=context,
        )
        return {
            "system": self.system_name,
            "task_id": str(task_id),
            "concept": concept,
            **reports,
        }

    def analyze_objects(
        self,
        input_objects: Iterable[Mapping[str, Any]],
        output_objects: Iterable[Mapping[str, Any]] | None = None,
        input_grid: Any | None = None,
        output_grid: Any | None = None,
        concept: str | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        input_object_list = list(input_objects or [])
        output_object_list = list(output_objects or []) if output_objects is not None else None
        spatial_report = self.build_spatial_reports(input_object_list, output_object_list)
        graph_report = self.build_graph_reports(
            input_object_list,
            output_object_list,
            spatial_reports=spatial_report,
        )
        set_report = self.build_set_reports(
            input_grid,
            output_grid,
            input_object_list,
            output_object_list,
        )
        transformation_report = self.build_transformation_reports(
            input_object_list,
            output_object_list,
        )
        reports = {
            "spatial_report": spatial_report,
            "graph_report": graph_report,
            "set_report": set_report,
            "transformation_report": transformation_report,
        }
        dependency_report = self.build_dependency_semantics(
            concept,
            reports,
            context=context,
        )
        reports["dependency_semantics_report"] = dependency_report
        reports["math_reasoning_signature"] = self.build_math_reasoning_signature(reports)
        return reports

    def build_spatial_reports(
        self,
        input_objects: Iterable[Mapping[str, Any]],
        output_objects: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        input_report = self.spatial_engine.analyze(list(input_objects or []))
        report = {
            **input_report,
            "input_spatial_report": input_report,
            "output_spatial_report": None,
        }
        if output_objects is not None:
            output_report = self.spatial_engine.analyze(list(output_objects or []))
            report["output_spatial_report"] = output_report
        return report

    def build_graph_reports(
        self,
        input_objects: Iterable[Mapping[str, Any]],
        output_objects: Iterable[Mapping[str, Any]] | None = None,
        spatial_reports: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        input_spatial = (
            spatial_reports.get("input_spatial_report")
            if isinstance(spatial_reports, Mapping)
            else None
        )
        input_graph = self.graph_engine.build_graph(list(input_objects or []), input_spatial)
        report = {
            **input_graph,
            "input_graph": input_graph,
            "output_graph": None,
            "comparison": {},
        }
        if output_objects is not None:
            output_spatial = (
                spatial_reports.get("output_spatial_report")
                if isinstance(spatial_reports, Mapping)
                else None
            )
            output_graph = self.graph_engine.build_graph(list(output_objects or []), output_spatial)
            comparison = self.graph_engine.compare_graphs(input_graph, output_graph)
            report["output_graph"] = output_graph
            report["comparison"] = comparison["comparison"]
        return report

    def build_set_reports(
        self,
        input_grid: Any,
        output_grid: Any | None = None,
        input_objects: Iterable[Mapping[str, Any]] | None = None,
        output_objects: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        reports: dict[str, Any] = {}
        if input_grid is not None and output_grid is not None:
            reports["color_comparison"] = self.set_engine.compare_input_output_colors(
                input_grid,
                output_grid,
            )
        elif input_grid is not None:
            reports["input_colors"] = self.set_engine.set_signature(
                self.set_engine.colors_of_grid(input_grid)
            )
        if input_objects is not None and output_objects is not None:
            reports["cell_comparison"] = self.set_engine.compare_input_output_cells(
                list(input_objects),
                list(output_objects),
            )
            reports["object_group_comparison"] = self.set_engine.compare_object_groups(
                list(input_objects),
                list(output_objects),
            )
        elif input_objects is not None:
            reports["input_object_ids"] = self.set_engine.set_signature(
                self.set_engine.object_ids(list(input_objects))
            )

        primary = reports.get("cell_comparison") or reports.get("color_comparison") or {}
        return {
            "system": "set_operations_engine",
            "reports": reports,
            "added_items": primary.get("added_items", []),
            "removed_items": primary.get("removed_items", []),
            "preserved_items": primary.get("preserved_items", []),
            "relation": primary.get("relation"),
            "color_change": reports.get("color_comparison", {}).get("color_change", False),
            "set_changes_detected": bool(
                primary.get("added_items") or primary.get("removed_items")
            ),
        }

    def build_transformation_reports(
        self,
        input_objects: Iterable[Mapping[str, Any]],
        output_objects: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if output_objects is None:
            return {
                "system": "transformation_algebra_engine",
                "transformation_count": 0,
                "operators": [],
                "transformation_signature": {
                    "operator_types": [],
                    "has_composition": False,
                    "preserves_shape": True,
                    "preserves_position": True,
                    "preserves_color": True,
                    "changes_object_count": False,
                },
            }
        return self.transformation_engine.transformation_signature(
            list(input_objects or []),
            list(output_objects or []),
        )

    def build_process_signature_report(
        self,
        concept: str,
        dependency_chain: Iterable[Any] | None = None,
        typed_dependencies: Iterable[Mapping[str, Any]] | None = None,
        process_dependency_memory: Mapping[str, Any] | None = None,
        transformation_report: Mapping[str, Any] | None = None,
        semantic_context: Mapping[str, Any] | None = None,
        dependency_semantics_score: float = 0.0,
    ) -> dict[str, Any]:
        return self.process_signature_engine.extract_signature(
            concept,
            dependency_chain=dependency_chain,
            typed_dependencies=typed_dependencies,
            process_dependency_memory=process_dependency_memory,
            transformation_report=transformation_report,
            semantic_context=semantic_context,
            dependency_semantics_score=dependency_semantics_score,
        )

    def build_dependency_semantics(
        self,
        concept: str | None,
        reports: Mapping[str, Any],
        context: str | None = None,
    ) -> dict[str, Any]:
        return self.dependency_engine.analyze(
            concept or "mathematical_reasoning",
            spatial_report=reports.get("spatial_report"),
            graph_report=reports.get("graph_report"),
            set_report=reports.get("set_report"),
            transformation_report=reports.get("transformation_report"),
            context=context,
        )

    def build_math_reasoning_signature(self, reports: Mapping[str, Any]) -> dict[str, Any]:
        spatial_report = reports.get("spatial_report", {})
        graph_report = reports.get("graph_report", {})
        set_report = reports.get("set_report", {})
        transformation_report = reports.get("transformation_report", {})
        dependency_report = reports.get("dependency_semantics_report", {})
        process_signature_report = reports.get("process_signature_report", {})
        return {
            "spatial_relations_detected": bool(spatial_report.get("relations")),
            "graph_relations_detected": bool(graph_report.get("edges")),
            "set_changes_detected": bool(set_report.get("set_changes_detected")),
            "transformations_detected": bool(transformation_report.get("operators")),
            "typed_dependencies_generated": bool(
                dependency_report.get("typed_dependencies")
            ),
            "process_signature_generated": bool(
                process_signature_report.get("process_signature_generated")
            ),
            "process_context_hint": dependency_report.get(
                "semantic_dependency_signature",
                {},
            ).get("process_context"),
            "process_signature_hint": process_signature_report.get(
                "signature_id",
            ),
            "concept_signature": process_signature_report.get(
                "concept_signature",
            ),
            "signature_confidence": process_signature_report.get(
                "signature_confidence",
                process_signature_report.get("signature_strength", 0.0),
            ),
        }

    def analyze_dependency_chain(
        self,
        concept: str,
        process_dependency_memory: Mapping[str, Any] | None = None,
        dependency_chain: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Interpret resolved dependency chains as passive process evidence."""
        process_memory = (
            process_dependency_memory
            if isinstance(process_dependency_memory, Mapping)
            else {}
        )
        chain = list(
            dependency_chain
            or process_memory.get("resolved_dependency_chain")
            or []
        )
        typed_dependencies = self._typed_dependencies_from_memory(
            concept,
            process_memory,
            chain,
        )
        nodes = sorted(
            {
                str(node)
                for dependency in typed_dependencies
                for node in (
                    dependency.get("source"),
                    dependency.get("target"),
                )
                if node
            }
            | {str(node) for node in chain if node}
        )
        evidence = self._chain_process_evidence(concept, nodes)
        spatial_report = self._chain_spatial_report(concept, evidence)
        graph_report = self._chain_graph_report(nodes, typed_dependencies)
        set_report = self._chain_set_report(concept, evidence, nodes)
        transformation_report = self._chain_transformation_report(
            concept,
            evidence,
        )
        score = max(
            self.dependency_engine.semantic_dependency_score(typed_dependencies),
            _clamp(process_memory.get("relation_semantics_score", 0.0)),
            _clamp(process_memory.get("dependency_confidence", 0.0)),
        )
        process_signature_report = self.build_process_signature_report(
            concept,
            dependency_chain=chain,
            typed_dependencies=typed_dependencies,
            process_dependency_memory=process_memory,
            transformation_report=transformation_report,
            dependency_semantics_score=score,
        )
        semantic_score = max(
            score,
            _clamp(process_signature_report.get("signature_strength", 0.0)),
        )
        dependency_report = {
            "system": "dependency_semantics_engine",
            "concept": str(concept),
            "typed_dependencies": typed_dependencies,
            "dependency_semantics_score": semantic_score,
            "raw_dependency_semantics_score": score,
            "process_signature_semantics_bonus": round(
                semantic_score - score,
                4,
            ),
            "dependency_chain_interpreted": bool(chain or typed_dependencies),
            "semantic_dependency_signature": (
                self.dependency_engine.semantic_dependency_signature(
                    typed_dependencies,
                    process_context=f"{concept}_context",
                )
            ),
            "dependency_chain_explanation": (
                self.dependency_engine.explain_dependency_chain(
                    typed_dependencies,
                )
            ),
        }
        reports = {
            "spatial_report": spatial_report,
            "graph_report": graph_report,
            "set_report": set_report,
            "transformation_report": transformation_report,
            "process_signature_report": process_signature_report,
            "dependency_semantics_report": dependency_report,
        }
        reports["math_reasoning_signature"] = self.build_math_reasoning_signature(
            reports,
        )
        return {
            "system": "mathematical_reasoning_layer",
            "source": "process_dependency_chain",
            "concept": str(concept),
            "process_dependency_chain": chain,
            "process_native_context": f"{concept}_context",
            **reports,
        }

    def export_to_process_dependency_memory(
        self,
        memory: Any,
        report: Mapping[str, Any],
        export_typed_dependencies: bool = False,
    ) -> dict[str, Any]:
        dependencies = (
            report.get("dependency_semantics_report", {})
            .get("typed_dependencies", [])
        )
        if not export_typed_dependencies:
            return {
                "system": self.system_name,
                "export_enabled": False,
                "ingested_links": 0,
            }
        export_report = self.dependency_engine.export_to_process_dependency_memory(
            memory,
            dependencies,
        )
        return {
            "system": self.system_name,
            "export_enabled": True,
            **export_report,
        }

    def _objects_from(
        self,
        objects: Iterable[Mapping[str, Any]] | None,
        grid: Any | None,
    ) -> list[dict[str, Any]]:
        if objects is not None:
            return [dict(obj) for obj in objects]
        if grid is None:
            return []
        extractor = self.object_extractor
        if extractor is None:
            from core.perception import ObjectExtractor

            extractor = ObjectExtractor()
        return extractor.extract_objects(grid)

    def _typed_dependencies_from_memory(
        self,
        concept: str,
        process_memory: Mapping[str, Any],
        chain: list[str],
    ) -> list[dict[str, Any]]:
        context = f"{concept}_context"
        dependencies = []
        for item in process_memory.get("typed_dependency_relations", []) or []:
            if not isinstance(item, Mapping):
                continue
            metadata = item.get("metadata", {})
            evidence = metadata if isinstance(metadata, Mapping) else {}
            dependencies.append(
                {
                    "source": str(item.get("source")),
                    "target": str(item.get("target")),
                    "relation": str(
                        evidence.get(
                            "original_relation",
                            evidence.get("relation", item.get("relation")),
                        )
                    ),
                    "confidence": _clamp(item.get("confidence", 0.0)),
                    "evidence": {
                        "process_dependency_chain": True,
                        **dict(evidence),
                    },
                    "contexts": sorted(
                        {
                            context,
                            *[
                                str(value)
                                for value in evidence.get("contexts", [])
                                if value
                            ],
                        }
                    ),
                }
            )
        if not dependencies and len(chain) > 1:
            for source, target in zip(chain, chain[1:]):
                dependencies.append(
                    self.dependency_engine.build_typed_dependency(
                        str(source),
                        str(target),
                        "derives_from",
                        process_memory.get("dependency_confidence", 0.86),
                        {"process_dependency_chain": True},
                        contexts=[context],
                    )
                )
        return self.dependency_engine._dedupe_dependencies(dependencies)

    def _chain_process_evidence(self, concept: str, nodes: list[str]) -> dict[str, bool]:
        node_set = {str(node) for node in nodes}
        return {
            "object_count_change": bool(
                node_set
                & {
                    "object_count_increase",
                    "identity_split",
                    "identity_forking",
                    "object_creation",
                }
            ),
            "object_count_increase": bool(
                node_set
                & {
                    "object_count_increase",
                    "object_creation",
                    "identity_split",
                    "identity_forking",
                }
            ),
            "topology_expansion": bool(
                node_set
                & {
                    "topology_expansion",
                    "topological_growth",
                    "topology_splitting",
                    "growth",
                }
            ),
            "position_change": bool(
                node_set
                & {
                    "position_change",
                    "position_delta",
                    "directional_motion",
                }
            ),
            "directional_motion": "directional_motion" in node_set,
            "source_pattern_preserved": "source_pattern_preserved" in node_set,
            "shape_preservation": bool(
                node_set
                & {
                    "local_shape",
                    "shape_preservation",
                    "source_pattern_preserved",
                }
            ),
            "object_count_constant": bool(
                "position_change" in node_set
                and not (
                    node_set
                    & {
                        "object_count_increase",
                        "object_creation",
                        "identity_split",
                        "identity_forking",
                    }
                )
            ),
            "identity_continuity": bool(
                node_set
                & {
                    "identity_persistence",
                    "identity_continuity",
                    "object_persistence",
                    "object_core",
                }
            ),
            "identity_forking": bool(
                node_set
                & {
                    "identity_forking",
                    "identity_split",
                }
                or (
                    concept == "topological_growth"
                    and "topology_splitting" in node_set
                )
            ),
            "concept_is_process": concept
            in {
                "growth",
                "replication",
                "propagation",
                "directional_motion",
                "topological_growth",
            },
        }

    def _chain_spatial_report(
        self,
        concept: str,
        evidence: Mapping[str, bool],
    ) -> dict[str, Any]:
        relations = []
        if evidence.get("position_change") or evidence.get("directional_motion"):
            relations.append({"relation": "shifted_by"})
        if evidence.get("source_pattern_preserved"):
            relations.append({"relation": "relative_position"})
        return {
            "system": "spatial_relations_engine",
            "concept": str(concept),
            "objects_analyzed": 0,
            "relations": relations,
            "spatial_signature": {
                "chain_derived": True,
                "directional_motion": evidence.get("directional_motion", False),
            },
        }

    def _chain_graph_report(
        self,
        nodes: list[str],
        typed_dependencies: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        edges = [
            {
                "source": item.get("source"),
                "target": item.get("target"),
                "relation": item.get("relation"),
            }
            for item in typed_dependencies
        ]
        return {
            "system": "graph_relations_engine",
            "nodes": nodes,
            "edges": edges,
            "comparison": {
                "node_count_change": max(len(nodes) - 1, 0),
                "edge_count_change": len(edges),
                "added_nodes": nodes[1:],
                "removed_nodes": [],
            },
            "graph_signature": {
                "relation_types": sorted(
                    {str(edge["relation"]) for edge in edges}
                ),
                "connected_components": 1 if nodes else 0,
            },
        }

    def _chain_set_report(
        self,
        concept: str,
        evidence: Mapping[str, bool],
        nodes: list[str],
    ) -> dict[str, Any]:
        expanded = bool(
            evidence.get("object_count_change")
            or evidence.get("topology_expansion")
            or evidence.get("source_pattern_preserved")
        )
        return {
            "system": "set_operations_engine",
            "reports": {},
            "added_items": nodes[1:] if expanded else [],
            "removed_items": [],
            "preserved_items": [
                node
                for node in nodes
                if node
                in {
                    "local_shape",
                    "shape_preservation",
                    "source_pattern_preserved",
                    "identity_continuity",
                    "identity_persistence",
                }
            ],
            "relation": "expanded" if expanded else "same",
            "color_change": False,
            "set_changes_detected": expanded,
            "concept": str(concept),
        }

    def _chain_transformation_report(
        self,
        concept: str,
        evidence: Mapping[str, bool],
    ) -> dict[str, Any]:
        operators = []
        if concept == "replication" or evidence.get("object_count_change"):
            operators.append({"operator": "duplicate"})
        if evidence.get("topology_expansion"):
            operators.append({"operator": "expand"})
        if evidence.get("position_change") or evidence.get("directional_motion"):
            operators.append({"operator": "translate"})
        operator_types = [item["operator"] for item in operators]
        algebra = self.transformation_engine.classify_transformation(
            {
                "concept": concept,
                "operator_types": operator_types,
                **dict(evidence),
            }
        )
        return {
            "system": "transformation_algebra_engine",
            "transformation_count": len(operators),
            "operators": operators,
            "transformation_algebra": algebra,
            "transformation_signature": {
                "operator_types": operator_types,
                "has_composition": len(operators) > 1,
                "preserves_shape": evidence.get("shape_preservation", False),
                "preserves_position": not bool(evidence.get("position_change")),
                "preserves_color": True,
                "changes_object_count": evidence.get("object_count_change", False),
                "transformation_types": algebra["transformation_types"],
                "primary_transformation_type": algebra[
                    "primary_transformation_type"
                ],
                "invariants": algebra["invariants"],
                "algebraic_signature": algebra["algebraic_signature"],
            },
        }


class MathematicalReasoningLayer(MathematicalReasoningPipeline):
    """Named layer facade for process-native mathematical reasoning."""

    system_name = "mathematical_reasoning_layer"


def _clamp(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return round(max(0.0, min(1.0, number)), 4)


__all__ = ["MathematicalReasoningLayer", "MathematicalReasoningPipeline"]
