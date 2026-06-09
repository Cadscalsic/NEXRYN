"""Object-centric dependency graph facade for NEXRYN.

The historical dependency graph implementation lives under ``core.causal``.
This module establishes the Phase 3 architectural path:

``core/perception/perception_engine.py``
``core/perception/scene_graph_engine.py``
``core/dependency/dependency_graph_engine.py``

It keeps the proven persistent graph machinery, while adding direct ingestion
of scene-graph evidence. The module records observed object and relation
dependencies only; it does not perform truth governance or causal commitment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from core.causal.dependency_graph_engine import (
    DEFAULT_DEPENDENCY_GRAPH_PATH,
    DependencyEdge,
    DependencyGraph,
    DependencyGraphEngine as CausalDependencyGraphEngine,
    DependencyNode,
    DependencyPath,
)
from core.dependency.dependency_graph_builder import DependencyGraphBuilder
from core.dependency.dependency_chain_ledger import (
    DependencyChainLedger,
)
from core.dependency.dependency_reasoning_operator import (
    DependencyReasoningOperator,
)
from core.dependency.process_dependency_graph import ProcessDependencyGraph
from core.dependency.process_dependency_memory import (
    DEFAULT_PROCESS_DEPENDENCY_MEMORY_PATH,
    ProcessDependencyMemory,
)
from core.perception.color_analyzer import ColorAnalyzer
from core.perception.identity_tracker import IdentityTracker
from core.perception.scene_graph_engine import SceneGraphEngine


class ObjectCentricDependencyGraphEngine(CausalDependencyGraphEngine):
    """Dependency graph engine fed by object-level scene graph evidence."""

    def __init__(
        self,
        graph_path: str | Path = DEFAULT_DEPENDENCY_GRAPH_PATH,
        autosave: bool = True,
        scene_graph_engine: SceneGraphEngine | None = None,
        placement_reasoner: Any | None = None,
        identity_tracker: IdentityTracker | None = None,
        color_analyzer: ColorAnalyzer | None = None,
        dependency_graph_builder: DependencyGraphBuilder | None = None,
        dependency_reasoning_operator: DependencyReasoningOperator | None = None,
        dependency_chain_ledger: DependencyChainLedger | None = None,
        dependency_chain_ledger_path: str | Path | None = None,
        process_dependency_graph: ProcessDependencyGraph | None = None,
        process_dependency_memory: ProcessDependencyMemory | None = None,
        process_dependency_memory_path: str | Path | None = (
            DEFAULT_PROCESS_DEPENDENCY_MEMORY_PATH
        ),
    ) -> None:
        super().__init__(graph_path=graph_path, autosave=autosave)
        self.scene_graph_engine = scene_graph_engine or SceneGraphEngine()
        self.identity_tracker = identity_tracker or IdentityTracker()
        self.color_analyzer = color_analyzer or ColorAnalyzer()
        self.dependency_graph_builder = (
            dependency_graph_builder
            or DependencyGraphBuilder(self.scene_graph_engine)
        )
        self.dependency_chain_ledger = (
            dependency_chain_ledger
            or DependencyChainLedger(storage_path=dependency_chain_ledger_path)
        )
        self.process_dependency_graph = (
            process_dependency_graph
            or ProcessDependencyGraph(
                process_dependency_memory=(
                    process_dependency_memory
                    or ProcessDependencyMemory(
                        storage_path=process_dependency_memory_path,
                    )
                )
            )
        )
        self.dependency_reasoning_operator = (
            dependency_reasoning_operator
            or DependencyReasoningOperator(
                process_dependency_graph=self.process_dependency_graph,
            )
        )
        if placement_reasoner is None:
            from core.world_model.placement_reasoner import PlacementReasoner

            placement_reasoner = PlacementReasoner()
        self.placement_reasoner = placement_reasoner

    def ingest_scene_graph(
        self,
        grid_or_scene_graph: Any,
        source: str,
    ) -> dict[str, Any]:
        """Ingest object, relation, and scene evidence for a source concept."""

        evidence_report = self._scene_dependency_evidence(
            grid_or_scene_graph,
            source=source,
        )
        ingest_report = self.ingest_dependencies(
            evidence_report["dependency_evidence"],
            default_source=source,
        )

        return {
            "system": "dependency_graph_engine",
            "mode": "object_centric",
            "source": source,
            "ingested_dependencies": ingest_report["ingested_dependencies"],
            "node_count": ingest_report["node_count"],
            "edge_count": ingest_report["edge_count"],
            "scene_graph_summary": evidence_report.get("scene_graph_summary", {}),
            "dependency_evidence": evidence_report["dependency_evidence"],
        }

    def validate_scene_dependency_coherence(
        self,
        source: str,
        grid_or_scene_graph: Any | None = None,
        required_dependencies: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Validate dependency coherence using object-centric evidence."""

        if grid_or_scene_graph is not None:
            evidence_report = self.ingest_scene_graph(
                grid_or_scene_graph,
                source=source,
            )
            inferred_required = [
                item["target"]
                for item in evidence_report["dependency_evidence"]
            ]
        else:
            inferred_required = []

        required = list(required_dependencies or inferred_required)
        report = self.validate_dependency_coherence(
            source,
            required_dependencies=required,
        )
        report["mode"] = "object_centric"
        report["object_level_evidence"] = True
        return report

    def build_scene_dependency_report(
        self,
        source: str,
        grid_or_scene_graph: Any,
        required_dependencies: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Build an end-to-end object dependency report for a scene."""

        ingest_report = self.ingest_scene_graph(
            grid_or_scene_graph,
            source=source,
        )
        required = list(
            required_dependencies
            or [item["target"] for item in ingest_report["dependency_evidence"]]
        )
        coherence = self.validate_dependency_coherence(
            source,
            required_dependencies=required,
        )
        paths = self.find_dependency_paths(source)

        return {
            "system": "dependency_graph_engine",
            "mode": "object_centric",
            "source": source,
            "ingest": ingest_report,
            "coherence": coherence,
            "paths": paths,
            "recommended_action": coherence["recommended_action"],
        }

    def ingest_scene_comparison(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str,
    ) -> dict[str, Any]:
        """Ingest dependency evidence from object-level scene comparison."""

        comparison = self.scene_graph_engine.compare_scene_graphs(
            input_grid,
            output_grid,
        )
        dependencies = [
            {
                **dependency,
                "source": source,
            }
            for dependency in comparison.get("dependency_evidence", [])
        ]
        ingest_report = self.ingest_dependencies(
            dependencies,
            default_source=source,
        )

        return {
            "system": "dependency_graph_engine",
            "mode": "object_centric_comparison",
            "source": source,
            "ingested_dependencies": ingest_report["ingested_dependencies"],
            "node_count": ingest_report["node_count"],
            "edge_count": ingest_report["edge_count"],
            "object_events": comparison.get("object_events", []),
            "relation_changes": comparison.get("relation_changes", {}),
            "dependency_evidence": dependencies,
        }

    def ingest_identity_tracking(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str = "object_identity_preservation",
    ) -> dict[str, Any]:
        """Ingest identity continuity and lineage evidence."""

        identity_report = self.identity_tracker.track_identity(
            input_grid,
            output_grid,
            source=source,
        )
        ingest_report = self.ingest_dependencies(
            identity_report.get("dependency_evidence", []),
            default_source=source,
        )

        return {
            "system": "dependency_graph_engine",
            "mode": "identity_tracking",
            "source": source,
            "identity_report": identity_report,
            "ingested_dependencies": ingest_report["ingested_dependencies"],
            "node_count": ingest_report["node_count"],
            "edge_count": ingest_report["edge_count"],
            "dependency_evidence": identity_report.get("dependency_evidence", []),
        }

    def build_identity_dependency_report(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str = "object_identity_preservation",
        required_dependencies: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Build dependency coherence from object identity evidence."""

        ingest_report = self.ingest_identity_tracking(
            input_grid,
            output_grid,
            source=source,
        )
        required = list(
            required_dependencies
            or [
                item["target"]
                for item in ingest_report["dependency_evidence"]
                if item.get("required", True)
            ]
        )
        coherence = self.validate_dependency_coherence(
            source,
            required_dependencies=required,
        )
        paths = self.find_dependency_paths(source)

        return {
            "system": "dependency_graph_engine",
            "mode": "identity_tracking",
            "source": source,
            "ingest": ingest_report,
            "coherence": coherence,
            "paths": paths,
            "recommended_action": coherence["recommended_action"],
        }

    def ingest_color_analysis(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str = "color_preservation",
    ) -> dict[str, Any]:
        """Ingest color behavior and mapping evidence."""

        color_report = self.color_analyzer.compare_grids(
            input_grid,
            output_grid,
            source=source,
        )
        ingest_report = self.ingest_dependencies(
            color_report.get("dependency_evidence", []),
            default_source=source,
        )

        return {
            "system": "dependency_graph_engine",
            "mode": "color_analysis",
            "source": source,
            "color_report": color_report,
            "ingested_dependencies": ingest_report["ingested_dependencies"],
            "node_count": ingest_report["node_count"],
            "edge_count": ingest_report["edge_count"],
            "dependency_evidence": color_report.get("dependency_evidence", []),
        }

    def build_color_dependency_report(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str = "color_preservation",
        required_dependencies: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Build dependency coherence from color mapping evidence."""

        ingest_report = self.ingest_color_analysis(
            input_grid,
            output_grid,
            source=source,
        )
        required = list(
            required_dependencies
            or [
                item["target"]
                for item in ingest_report["dependency_evidence"]
                if item.get("required", True)
            ]
        )
        coherence = self.validate_dependency_coherence(
            source,
            required_dependencies=required,
        )
        paths = self.find_dependency_paths(source)

        return {
            "system": "dependency_graph_engine",
            "mode": "color_analysis",
            "source": source,
            "ingest": ingest_report,
            "coherence": coherence,
            "paths": paths,
            "recommended_action": coherence["recommended_action"],
        }

    def ingest_dependency_chain(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str | None = None,
    ) -> dict[str, Any]:
        """Ingest an ordered dependency chain built from scene evidence."""

        chain_report = self.dependency_graph_builder.build_from_grids(
            input_grid,
            output_grid,
            source=source,
        )
        ingest_report = self.ingest_dependencies(
            chain_report.get("dependency_evidence", []),
            default_source=chain_report.get("operation"),
        )

        return {
            "system": "dependency_graph_engine",
            "mode": "dependency_chain",
            "source": chain_report.get("operation"),
            "chain_report": chain_report,
            "ingested_dependencies": ingest_report["ingested_dependencies"],
            "node_count": ingest_report["node_count"],
            "edge_count": ingest_report["edge_count"],
            "dependency_evidence": chain_report.get("dependency_evidence", []),
        }

    def build_dependency_chain_report(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str | None = None,
    ) -> dict[str, Any]:
        """Build coherence and path diagnostics for an ordered dependency chain."""

        ingest_report = self.ingest_dependency_chain(
            input_grid,
            output_grid,
            source=source,
        )
        chain = ingest_report["chain_report"].get("dependency_chain", [])
        root = chain[0] if chain else ingest_report.get("source")
        terminal = chain[-1] if chain else None
        required = [chain[1]] if len(chain) > 1 else []
        coherence = self.validate_dependency_coherence(
            root,
            required_dependencies=required,
        )
        paths = self.find_dependency_paths(
            root,
            target=terminal,
        )
        best_path_nodes = paths.get("best_path", {}).get("nodes", [])

        return {
            "system": "dependency_graph_engine",
            "mode": "dependency_chain",
            "source": root,
            "ingest": ingest_report,
            "coherence": coherence,
            "paths": paths,
            "chain_complete": best_path_nodes == chain,
            "dependency_chain": chain,
            "recommended_action": (
                "USE_FOR_CAUSAL_PROMOTION"
                if best_path_nodes == chain
                and coherence["dependency_coherence"] >= 0.80
                else "COLLECT_DEPENDENCY_EVIDENCE"
            ),
        }

    def ingest_reasoned_dependency_chain(
        self,
        signals: Iterable[str],
        source: str | None = None,
        target: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Ingest a reasoned semantic dependency chain into the graph."""

        reasoning_report = self.dependency_reasoning_operator.reason(
            signals,
            source=source,
            target=target,
            evidence=evidence,
        )
        ingest_report = self.ingest_dependencies(
            reasoning_report.get("dependency_evidence", []),
            default_source=reasoning_report.get("source"),
        )
        ledger_record = self.dependency_chain_ledger.record_reasoning_report(
            reasoning_report,
            context=(
                evidence.get("context")
                if isinstance(evidence, dict)
                else None
            ),
        )

        return {
            "system": "dependency_graph_engine",
            "mode": "reasoned_dependency_chain",
            "source": reasoning_report.get("source"),
            "target": reasoning_report.get("target"),
            "reasoning": reasoning_report,
            "dependency_chain_ledger_record": ledger_record,
            "ingested_dependencies": ingest_report["ingested_dependencies"],
            "node_count": ingest_report["node_count"],
            "edge_count": ingest_report["edge_count"],
            "recommended_action": reasoning_report["recommended_action"],
        }

    def ingest_reasoned_dependency_chains(
        self,
        records: Iterable[Any],
    ) -> dict[str, Any]:
        """Ingest reasoned dependency chains from runtime/context records."""

        records = list(records or [])
        reports = []
        for record in records:
            prepared = self._dependency_reasoning_request(record)
            if not prepared["signals"]:
                continue
            report = self.ingest_reasoned_dependency_chain(
                prepared["signals"],
                source=prepared.get("source"),
                target=prepared.get("target"),
                evidence=prepared.get("evidence"),
            )
            source = report.get("source")
            target = report.get("target")
            chain = (
                report.get("reasoning", {})
                .get("dependency_chain", {})
                .get("nodes", [])
            )
            max_depth = max(len(chain) - 1, 4)
            coherence = self.validate_dependency_coherence(
                source,
                required_dependencies=chain[1:2],
            ) if source else {}
            paths = self.find_dependency_paths(
                source,
                target=target,
                max_depth=max_depth,
            ) if source and target else {}
            reports.append({
                **report,
                "input_signals": prepared["signals"],
                "coherence": coherence,
                "paths": paths,
            })

        reasoned_count = sum(
            1
            for report in reports
            if report.get("reasoning", {}).get("chain_complete") is True
        )
        ingested_count = sum(
            int(report.get("ingested_dependencies", 0) or 0)
            for report in reports
        )
        coherence_values = [
            report.get("coherence", {}).get("dependency_coherence")
            for report in reports
            if report.get("coherence", {}).get("dependency_coherence")
            is not None
        ]
        average_coherence = (
            round(sum(coherence_values) / len(coherence_values), 4)
            if coherence_values
            else None
        )

        return {
            "system": "dependency_graph_engine",
            "mode": "reasoned_dependency_chain_ingestion",
            "dependency_chain_ingestion_layer_active": True,
            "dependency_chain_ledger":
            self.dependency_chain_ledger.report(),
            "record_count": len(records),
            "reasoned_chain_count": reasoned_count,
            "ingested_dependencies": ingested_count,
            "dependency_coherence_average": average_coherence,
            "reports": reports,
            "recommended_action": (
                "USE_REASONED_DEPENDENCY_CHAINS_FOR_CAUSAL_PROMOTION"
                if reasoned_count and average_coherence is not None
                and average_coherence >= 0.80
                else "COLLECT_ADDITIONAL_DEPENDENCY_CHAIN_SIGNALS"
            ),
        }

    def ingest_dependency_chain_ledger(self) -> dict[str, Any]:
        """Rehydrate graph edges from stored dependency chain memory."""

        reports = []
        for record in self.dependency_chain_ledger.reasoning_records():
            signals = list(record.get("signals", []))
            dependencies = self._reasoned_chain_dependencies(
                signals,
                confidence=record.get("evidence", {}).get(
                    "confidence",
                    record.get("metadata", {}).get("confidence", 0.86),
                ),
                metadata=record.get("metadata", {}),
            )
            ingest = self.ingest_dependencies(
                dependencies,
                default_source=record.get("source"),
            )
            source = record.get("source")
            target = record.get("target")
            paths = self.find_dependency_paths(
                source,
                target=target,
                max_depth=max(len(signals) - 1, 4),
            ) if source and target else {}
            coherence = self.validate_dependency_coherence(
                source,
                required_dependencies=signals[1:2],
            ) if source else {}
            reports.append({
                "source": source,
                "target": target,
                "signals": signals,
                "ingest": ingest,
                "paths": paths,
                "coherence": coherence,
            })
        coherence_values = [
            report.get("coherence", {}).get("dependency_coherence")
            for report in reports
            if report.get("coherence", {}).get("dependency_coherence")
            is not None
        ]
        return {
            "system": "dependency_graph_engine",
            "mode": "dependency_chain_ledger_rehydration",
            "source_ledger": self.dependency_chain_ledger.report(),
            "record_count": len(reports),
            "reasoned_chain_count": len(reports),
            "ingested_dependencies": sum(
                int(report["ingest"].get("ingested_dependencies", 0) or 0)
                for report in reports
            ),
            "dependency_coherence_average": (
                round(sum(coherence_values) / len(coherence_values), 4)
                if coherence_values
                else None
            ),
            "reports": reports,
        }

    def ingest_process_dependency_graph(
        self,
        processes: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Ingest typed process dependency knowledge into graph and ledger."""

        process_list = list(processes or sorted(
            self.process_dependency_graph.process_dependency_memory.process_links
            or self.process_dependency_graph.process_relations
        ))
        process_report = self.process_dependency_graph.build_report(process_list)
        ingest = self.ingest_dependencies(
            process_report["dependency_evidence"],
        )
        ledger_records = []
        for record in process_report["chain_records"]:
            signals = record.get("signals", [])
            result = self.dependency_chain_ledger.add_chain(
                signals,
                confidence=record.get("evidence", {}).get("confidence", 0.86),
                relation=record.get("metadata", {}).get("relation", "supports"),
                context=record.get("source"),
                evidence=record.get("evidence", {}),
                metadata=record.get("metadata", {}),
                source=record.get("source"),
                target=record.get("target"),
            )
            ledger_records.append(result)
        coherence_reports = {
            process: self.validate_dependency_coherence(
                process,
                required_dependencies=[
                    relation.target
                    for relation in self.process_dependency_graph.relations_for(
                        process
                    )
                    if relation.source == process
                    and relation.relation in {"requires", "causes", "supports"}
                ],
            )
            for process in process_list
        }
        coherence_values = [
            report.get("dependency_coherence")
            for report in coherence_reports.values()
            if report.get("dependency_coherence") is not None
        ]
        debug_reports = {
            process: self.process_dependency_graph.resolve_dependency_chain(
                process,
            )
            for process in process_list
        }
        links_used = sum(
            int(report.get("process_dependency_links_used", 0) or 0)
            for report in debug_reports.values()
        )
        chain_depths = [
            int(report.get("dependency_chain_depth", 0) or 0)
            for report in debug_reports.values()
        ]
        chain_coverages = [
            float(report.get("dependency_chain_coverage", 0.0) or 0.0)
            for report in debug_reports.values()
        ]
        return {
            "system": "dependency_graph_engine",
            "mode": "process_dependency_graph_ingestion",
            "process_dependency_graph": process_report,
            "ingest": ingest,
            "ledger_records": ledger_records,
            "coherence_reports": coherence_reports,
            "boundary_refinement_dependency_debug": list(
                debug_reports.values()
            ),
            "process_dependency_links_loaded":
            process_report.get("process_dependency_links_loaded", 0),
            "process_dependency_links_used": links_used,
            "dependency_chain_depth": (
                max(chain_depths)
                if chain_depths
                else 0
            ),
            "dependency_chain_coverage": (
                round(sum(chain_coverages) / len(chain_coverages), 4)
                if chain_coverages
                else 0.0
            ),
            "dependency_coherence_average": (
                round(sum(coherence_values) / len(coherence_values), 4)
                if coherence_values
                else None
            ),
            "recommended_action": (
                "USE_PROCESS_DEPENDENCIES_FOR_BOUNDARY_REFINEMENT"
                if coherence_values
                else "ADD_PROCESS_DEPENDENCY_KNOWLEDGE"
            ),
        }

    def ingest_process_dependency_memory(
        self,
        processes: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Load typed process chains from memory and ingest them into graph."""

        report = self.ingest_process_dependency_graph(processes)
        return {
            **report,
            "mode": "process_dependency_memory_ingestion",
            "process_dependency_memory_ingestion_layer_active": True,
            "source_memory":
            self.process_dependency_graph.process_dependency_memory.report(),
        }

    def _reasoned_chain_dependencies(
        self,
        signals: list[str],
        confidence: float,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        metadata = dict(metadata or {})
        return [
            {
                "source": source,
                "target": target,
                "relation": "causes",
                "confidence": confidence,
                "dependency_type": "reasoned_dependency_memory",
                "required": True,
                "supported": True,
                "transfer_success": True,
                "metadata": {
                    **metadata,
                    "dependency_chain_ledger": True,
                    "chain": list(signals),
                },
            }
            for source, target in zip(signals, signals[1:])
        ]

    def ingest_dependency_chain_ledger_via_operator(self) -> dict[str, Any]:
        """Re-run stored chain records through the reasoning operator."""

        return {
            **self.ingest_reasoned_dependency_chains(
                self.dependency_chain_ledger.reasoning_records()
            ),
            "mode": "dependency_chain_ledger_operator_rehydration",
            "source_ledger": self.dependency_chain_ledger.report(),
        }

    def _dependency_reasoning_request(self, record: Any) -> dict[str, Any]:
        if isinstance(record, (list, tuple, set)):
            signals = [str(item) for item in record]
            return {
                "signals": signals,
                "source": signals[0] if signals else None,
                "target": signals[-1] if len(signals) > 1 else None,
                "evidence": {},
            }

        record = record if isinstance(record, dict) else {}
        explicit = record.get("signals", record.get("dependency_signals"))
        if explicit:
            signals = [str(item) for item in explicit]
        else:
            signals = self._signals_from_dependency_record(record)
        source = record.get("source") or (signals[0] if signals else None)
        target = record.get("target") or (signals[-1] if len(signals) > 1 else None)
        evidence = record.get("evidence")
        if not isinstance(evidence, dict):
            evidence = self._dependency_reasoning_evidence(record)
        return {
            "signals": signals,
            "source": source,
            "target": target,
            "evidence": evidence,
        }

    def _signals_from_dependency_record(
        self,
        record: dict[str, Any],
    ) -> list[str]:
        signals = []

        def add(value: Any) -> None:
            value = str(value or "").strip()
            if value and value != "unknown" and value not in signals:
                signals.append(value)

        concept = record.get("concept")
        add(concept)
        context = record.get("context_discovery", {})
        signature = {}
        if isinstance(context, dict):
            add(context.get("transformation_family"))
            signature = context.get("context_signature", {})
        signature = signature if isinstance(signature, dict) else {}
        for key in [
            "transformation_family",
            "identity_behavior",
            "topology_behavior",
            "color_behavior",
            "object_dynamics",
            "size_behavior",
            "propagation_behavior",
        ]:
            add(signature.get(key))

        runtime = record.get("identity_runtime_report", {})
        runtime = runtime if isinstance(runtime, dict) else {}
        if runtime.get("identity_split") is True:
            add("identity_split")
            add("object_count_increase")
        if runtime.get("identity_merged") is True:
            add("identity_merged")
            add("object_count_decrease")
        if runtime.get("identity_continuity_preserved") is True:
            add("identity_preserved")
        if runtime.get("runtime_ready") is True:
            add("local_shape")

        family = next(
            (
                signal
                for signal in signals
                if signal in {
                    "growth",
                    "topological_growth",
                    "topology_expansion",
                    "propagation",
                    "replication",
                    "duplication",
                    "object_identity_preservation",
                }
            ),
            None,
        )
        if family in {"growth", "topological_growth", "topology_expansion"}:
            add("growth")
            add("cell_count_increase")
            add("topology_expansion")
            add("shape_preservation")
        elif family == "propagation":
            add("source_pattern_preserved")
            add("directional_motion")
            add("position_preservation")
        elif family in {"replication", "duplication"}:
            add("identity_split")
            add("object_count_increase")
            add("topology_splitting")
            add("shape_preservation")
        elif family == "object_identity_preservation":
            add("identity_preserved")
            add("local_shape")
            add("shape_preservation")

        return signals

    def _dependency_reasoning_evidence(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        context = record.get("context_discovery", {})
        semantic = record.get("semantic_context", {})
        hierarchy = record.get("context_hierarchy", {})
        causal = record.get("causal_graph_alignment", {})
        validation = record.get("causal_validation", {})
        return {
            "context_confidence": (
                context.get("confidence")
                if isinstance(context, dict)
                else None
            ),
            "semantic_context_score": (
                semantic.get("semantic_context_score")
                if isinstance(semantic, dict)
                else None
            ),
            "context_hierarchy_score": (
                hierarchy.get("context_hierarchy_score")
                if isinstance(hierarchy, dict)
                else None
            ),
            "causal_graph_alignment": (
                causal.get("alignment_score")
                if isinstance(causal, dict)
                else None
            ),
            "validation_score": (
                validation.get("validation_score")
                if isinstance(validation, dict)
                else None
            ),
        }

    def ingest_placement_reasoning(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str,
        operation: str = "duplicate_object",
        position_rule: dict[str, Any] | None = None,
        search_radius: int = 1,
    ) -> dict[str, Any]:
        """Ingest why/where placement evidence into dependency coherence."""

        placement_report = self.placement_reasoner.reason(
            input_grid,
            output_grid,
            operation=operation,
            position_rule=position_rule,
            search_radius=search_radius,
        )
        dependencies = self._placement_dependency_evidence(
            placement_report,
            source=source,
            operation=operation,
        )
        ingest_report = self.ingest_dependencies(
            dependencies,
            default_source=source,
        )

        return {
            "system": "dependency_graph_engine",
            "mode": "placement_reasoning",
            "source": source,
            "operation": operation,
            "placement_state": placement_report.get("placement_state"),
            "ingested_dependencies": ingest_report["ingested_dependencies"],
            "node_count": ingest_report["node_count"],
            "edge_count": ingest_report["edge_count"],
            "placement_reasoning": placement_report,
            "dependency_evidence": dependencies,
        }

    def build_placement_dependency_report(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str,
        operation: str = "duplicate_object",
        position_rule: dict[str, Any] | None = None,
        required_dependencies: Iterable[str] | None = None,
        search_radius: int = 1,
    ) -> dict[str, Any]:
        """Build an end-to-end dependency report for placement causality."""

        ingest_report = self.ingest_placement_reasoning(
            input_grid,
            output_grid,
            source=source,
            operation=operation,
            position_rule=position_rule,
            search_radius=search_radius,
        )
        required = list(
            required_dependencies
            or [
                item["target"]
                for item in ingest_report["dependency_evidence"]
                if item.get("required", True)
            ]
        )
        coherence = self.validate_dependency_coherence(
            source,
            required_dependencies=required,
        )
        paths = self.find_dependency_paths(source)

        return {
            "system": "dependency_graph_engine",
            "mode": "placement_reasoning",
            "source": source,
            "operation": operation,
            "ingest": ingest_report,
            "coherence": coherence,
            "paths": paths,
            "recommended_action": coherence["recommended_action"],
        }

    def _scene_dependency_evidence(
        self,
        grid_or_scene_graph: Any,
        source: str,
    ) -> dict[str, Any]:
        if (
            isinstance(grid_or_scene_graph, dict)
            and grid_or_scene_graph.get("system") == "scene_graph_engine"
        ):
            evidence = self.scene_graph_engine.extract_dependency_evidence(
                grid_or_scene_graph,
                source=source,
            )
            return {
                "system": "scene_graph_engine",
                "source": source,
                "dependency_evidence": evidence,
                "evidence_count": len(evidence),
                "scene_graph_summary": grid_or_scene_graph.get("summary", {}),
            }

        return self.scene_graph_engine.build_dependency_evidence(
            grid_or_scene_graph,
            source=source,
        )

    def _placement_dependency_evidence(
        self,
        placement_report: dict[str, Any],
        source: str,
        operation: str,
    ) -> list[dict[str, Any]]:
        graph_dependencies = [
            {
                **dependency,
                "source": source,
                "metadata": {
                    **dict(dependency.get("metadata", {})),
                    "original_source": dependency.get("source"),
                    "placement_reasoner": True,
                },
            }
            for dependency in placement_report.get("dependency_evidence", [])
        ]
        dependencies = list(graph_dependencies)
        placement_state = placement_report.get("placement_state")
        if placement_state:
            dependencies.append(self._placement_dependency(
                source,
                f"placement_state:{placement_state}",
                confidence=0.88,
                metadata={"placement_state": placement_state},
            ))

        mismatch = placement_report.get("position_mismatch", {})
        failure_type = mismatch.get("failure_type")
        if failure_type:
            dependencies.append(self._placement_dependency(
                source,
                f"failure_cause:{failure_type}",
                confidence=0.86,
                metadata={"mismatch": mismatch},
            ))

        rule = (
            placement_report.get("recommended_position_rule")
            or placement_report.get("position_rule")
            or {}
        )
        vector = dict(rule.get("placement_vector", {}))
        direction = vector.get("direction")
        if direction:
            dependencies.append(self._placement_dependency(
                source,
                f"placement:{direction}",
                confidence=rule.get("confidence", 0.84),
                metadata={"placement_vector": vector, "operation": operation},
            ))
        dependencies.append(self._placement_dependency(
            source,
            f"operation:{operation}",
            confidence=0.90,
            metadata={"operation": operation},
        ))

        if placement_report.get(
            "position_counterfactuals",
            {},
        ).get("localized_prediction_mismatch_resolved"):
            dependencies.append(self._placement_dependency(
                source,
                "counterfactual:localized_mismatch_resolved",
                confidence=0.92,
                metadata=placement_report.get("position_counterfactuals", {}),
            ))

        return dependencies

    def _placement_dependency(
        self,
        source: str,
        target: str,
        confidence: float,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "source": source,
            "target": target,
            "confidence": confidence,
            "supported": True,
            "transfer_success": True,
            "dependency_type": "placement_dependency",
            "required": True,
            "metadata": metadata,
        }


DependencyGraphEngine = ObjectCentricDependencyGraphEngine


__all__ = [
    "DependencyEdge",
    "DependencyGraph",
    "DependencyGraphEngine",
    "DependencyNode",
    "DependencyPath",
    "ObjectCentricDependencyGraphEngine",
]
