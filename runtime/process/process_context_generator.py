"""Generate executable process contexts from dependency graphs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from time import perf_counter
from typing import Any, Mapping

from runtime.memory.process_context_memory import ProcessContextMemory
from runtime.process.process_context_simulator import ProcessContextSimulator
from runtime.process.process_context_validator import ProcessContextValidator
from runtime.process.state_transition_builder import StateTransitionBuilder


@dataclass
class ProcessContext:
    process_id: str
    process_family: str
    source_graph: dict[str, Any]
    initial_state: dict[str, Any]
    intermediate_states: list[dict[str, Any]]
    final_state: dict[str, Any]
    transition_sequence: list[str]
    constraints: list[str]
    expected_outcomes: list[str]
    confidence: float
    transition_events: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    transition_confidence: float = 0.0
    state_confidence: float = 0.0
    process_confidence: float = 0.0
    support_score: float = 0.0
    contradiction_score: float = 0.0
    validation: dict[str, Any] = field(default_factory=dict)
    simulation: dict[str, Any] = field(default_factory=dict)
    reuse_hit: bool = False
    concept: str = ""

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["context_name"] = self.process_id
        data["process_context_confidence"] = round(float(self.confidence or 0.0), 4)
        data["state_count"] = 2 + len(self.intermediate_states)
        data["process_depth"] = len(self.transition_sequence)
        return data


class ProcessContextGenerator:
    """Transform dependency graphs into executable process models."""

    system_name = "process_context_generator"

    FAMILY_KEYWORDS = {
        "gravity_process": {"gravity", "fall", "unsupported", "collision", "rest"},
        "path_process": {"path", "route", "reachable", "goal"},
        "bridge_process": {"bridge", "component", "connector", "connect"},
        "growth_process": {"growth", "expand", "area"},
        "containment_process": {"containment", "inside", "outside"},
        "propagation_process": {"propagation", "spread", "neighbor"},
        "mapping_process": {"mapping", "color", "source_color", "target_color"},
        "movement_process": {"move", "position", "spatial", "translation"},
        "rotation_process": {"rotation", "rotate"},
        "reflection_process": {"reflection", "mirror"},
        "multi_step_process": {"multi_step", "sequence", "intermediate", "step"},
    }

    def __init__(
        self,
        transition_builder: StateTransitionBuilder | None = None,
        simulator: ProcessContextSimulator | None = None,
        validator: ProcessContextValidator | None = None,
        memory: ProcessContextMemory | None = None,
    ):
        self.transition_builder = transition_builder or StateTransitionBuilder()
        self.simulator = simulator or ProcessContextSimulator()
        self.validator = validator or ProcessContextValidator()
        self.memory = memory or ProcessContextMemory()

    def generate(
        self,
        dependency_graph_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        input_grid=None,
        output_grid=None,
    ) -> dict[str, Any]:
        started = perf_counter()
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        graphs = self._graphs_from_report(dependency_graph_report)
        contexts = []
        reuse_hits = 0
        for graph in graphs:
            family = self._classify_family(graph)
            reused = self._reuse_context(family)
            if reused:
                reused["reuse_hit"] = True
                contexts.append(reused)
                reuse_hits += 1
            transition_report = self.transition_builder.build(graph, family)
            context = self._context_from_graph(graph, family, transition_report)
            simulation = self.simulator.simulate(
                context.as_dict(),
                input_grid=input_grid,
                output_grid=output_grid,
            )
            validation = self.validator.validate_generated(
                context.as_dict(),
                simulation,
                graph,
            )
            context.simulation = simulation
            context.validation = validation
            context.confidence = round(
                max(
                    context.confidence,
                    validation.get("process_validation_score", 0.0) * 0.45
                    + simulation.get("process_reproduction_score", 0.0) * 0.35
                    + context.support_score * 0.20,
                ),
                4,
            )
            contexts.append(context.as_dict())
            self.memory.remember(
                context.as_dict(),
                simulation_accuracy=simulation.get("process_reproduction_score", 0.0),
                success=validation.get("process_validated", False),
                evidence={
                    "source": self.system_name,
                    "source_graph": graph.get("graph_id"),
                },
            )

        contexts = sorted(
            contexts,
            key=lambda item: (
                item.get("confidence", 0.0),
                item.get("simulation", {}).get("process_reproduction_score", 0.0),
            ),
            reverse=True,
        )
        families = list(dict.fromkeys(item.get("process_family") for item in contexts))
        states_generated = sum(item.get("state_count", 0) for item in contexts)
        transitions_generated = sum(
            len(item.get("transition_sequence", []) or [])
            for item in contexts
        )
        process_depth = max(
            [item.get("process_depth", 0) for item in contexts] or [0]
        )
        process_confidence = (
            contexts[0].get("confidence", 0.0)
            if contexts
            else 0.0
        )
        validation_score = (
            contexts[0].get("validation", {}).get("process_validation_score", 0.0)
            if contexts
            else 0.0
        )
        report = {
            "system": self.system_name,
            "process_contexts": contexts,
            "selected_process_context": contexts[0] if contexts else {},
            "process_contexts_generated": len(contexts),
            "process_families_detected": families,
            "states_generated": states_generated,
            "transitions_generated": transitions_generated,
            "process_depth": process_depth,
            "process_confidence": round(float(process_confidence or 0.0), 4),
            "reuse_hits": reuse_hits,
            "validation_score": round(float(validation_score or 0.0), 4),
            "process_context_count": len(contexts),
            "process_state_count": states_generated,
            "process_transition_count": transitions_generated,
            "process_reuse_rate": round(reuse_hits / max(len(contexts), 1), 4),
            "process_validation_score": round(float(validation_score or 0.0), 4),
            "process_generation_time": round(perf_counter() - started, 6),
            "process_memory_report": self.memory.build_report(),
            "timestamp": str(datetime.utcnow()),
        }
        report["PROCESS_CONTEXT_GENERATION_REPORT"] = {
            key: report[key]
            for key in [
                "process_contexts_generated",
                "process_families_detected",
                "states_generated",
                "transitions_generated",
                "process_depth",
                "process_confidence",
                "reuse_hits",
                "validation_score",
            ]
        }
        return report

    def _context_from_graph(self, graph, family, transition_report):
        dependencies = [
            str(edge.get("source")) + "->" + str(edge.get("target"))
            for edge in graph.get("edges", []) or []
            if isinstance(edge, Mapping)
        ]
        support_score = float(graph.get("support_score", 0.0) or 0.0)
        contradiction_score = float(graph.get("contradiction_score", 0.0) or 0.0)
        transition_confidence = transition_report.get("transition_confidence", 0.0)
        state_confidence = transition_report.get("state_confidence", 0.0)
        confidence = round(
            max(0.0, (transition_confidence + state_confidence + support_score) / 3 - contradiction_score),
            4,
        )
        return ProcessContext(
            process_id=f"{family}:{graph.get('graph_id', 'graph')}",
            process_family=family,
            source_graph=dict(graph),
            initial_state=transition_report.get("initial_state", {}),
            intermediate_states=list(transition_report.get("intermediate_states", []) or []),
            final_state=transition_report.get("final_state", {}),
            transition_sequence=list(transition_report.get("transition_sequence", []) or []),
            constraints=self._constraints_for(family, graph),
            expected_outcomes=self._expected_outcomes_for(family, transition_report),
            confidence=confidence,
            transition_events=list(transition_report.get("transitions", []) or []),
            dependencies=dependencies,
            transition_confidence=transition_confidence,
            state_confidence=state_confidence,
            process_confidence=confidence,
            support_score=support_score,
            contradiction_score=contradiction_score,
            concept=(graph.get("root_concepts", []) or [family])[0],
        )

    def _graphs_from_report(self, report):
        report = report if isinstance(report, Mapping) else {}
        if report.get("dependency_graphs"):
            return [
                dict(graph)
                for graph in report.get("dependency_graphs", [])
                if isinstance(graph, Mapping)
            ]
        if report.get("dependency_graph"):
            return [dict(report["dependency_graph"])]
        discovery = report.get("dependency_graph_discovery_report", {})
        if isinstance(discovery, Mapping):
            return self._graphs_from_report(discovery)
        return []

    def _classify_family(self, graph):
        text = " ".join(
            [
                *[str(item) for item in graph.get("root_concepts", []) or []],
                *[
                    str(node.get("label") or node.get("name") or "")
                    for node in graph.get("nodes", []) or []
                    if isinstance(node, Mapping)
                ],
                *[
                    str(edge.get("edge_type") or edge.get("relation") or "")
                    for edge in graph.get("edges", []) or []
                    if isinstance(edge, Mapping)
                ],
            ]
        ).lower()
        for family, keywords in self.FAMILY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return family
        return "multi_step_process"

    def _reuse_context(self, family):
        for record in self.memory.retrieve_successful(family, limit=1):
            model = dict(record.get("process_model", {}))
            if model:
                return model
        return None

    def _constraints_for(self, family, graph):
        constraints = ["dependency_consistency"]
        if family in {"path_process", "bridge_process"}:
            constraints.append("topology_consistency")
        if family in {"gravity_process", "movement_process"}:
            constraints.append("identity_consistency")
        if graph.get("contradiction_score", 0.0):
            constraints.append("contradiction_monitoring")
        return constraints

    def _expected_outcomes_for(self, family, transition_report):
        final = transition_report.get("final_state", {}).get("state_name", "final_state")
        return [f"{family}_completed", str(final)]


process_context_generator = ProcessContextGenerator()


__all__ = ["ProcessContext", "ProcessContextGenerator", "process_context_generator"]
