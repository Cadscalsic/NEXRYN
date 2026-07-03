"""Runtime layer for dynamic process context understanding."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping

from core.epistemic_models import clamp
from runtime.memory.process_context_memory import process_context_memory
from runtime.process.process_context_registry import (
    ProcessContext,
    ProcessContextRegistry,
)
from runtime.process.process_simulator import process_simulator
from runtime.process.state_transition_engine import state_transition_engine


@dataclass
class ProcessContextModel:
    context_name: str
    process_family: str
    initial_state: dict[str, Any]
    intermediate_states: list[dict[str, Any]]
    final_state: dict[str, Any]
    transition_sequence: list[str]
    dependencies: list[str]
    constraints: list[str]
    expected_outcomes: list[str]
    confidence: float
    concept: str = ""
    transition_events: list[dict[str, Any]] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)
    simulation: dict[str, Any] = field(default_factory=dict)
    reuse_hit: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["confidence"] = clamp(self.confidence)
        data["process_context_confidence"] = data["confidence"]
        data["process_depth"] = len(self.transition_sequence)
        data["state_count"] = 2 + len(self.intermediate_states)
        return data


class ProcessContextRuntime:
    """Transform concepts and dependencies into executable process models."""

    system_name = "process_context_runtime"

    FAMILY_KEYWORDS = {
        "path_finding": {"path", "route", "reachability"},
        "route_completion": {"route_completion", "completion", "selected_path"},
        "bridge_creation": {"bridge", "connector", "component_connection"},
        "growth": {"growth", "expanded", "area"},
        "containment": {"containment", "inside", "outside"},
        "propagation": {"propagation", "spread", "neighbor"},
        "gravity": {"gravity", "support", "fall", "rest_state"},
        "support": {"support", "unsupported", "rest_state"},
        "occlusion": {"occlusion", "hidden", "covered"},
        "relative_movement": {"relative_position", "spatial_relation", "moved"},
        "transformation_sequence": {"sequence", "transform_a", "transform_b"},
        "multi_step_reasoning": {"multi_step", "intermediate_state"},
    }

    def __init__(
        self,
        transition_engine=None,
        simulator=None,
        memory=None,
        registry: ProcessContextRegistry | None = None,
    ):
        self.transition_engine = transition_engine or state_transition_engine
        self.simulator = simulator or process_simulator
        self.memory = memory or process_context_memory
        self.registry = registry or ProcessContextRegistry()
        self.runtime_history = []

    def run(
        self,
        input_grid=None,
        output_grid=None,
        detected_concepts: list[str] | None = None,
        dependency_activation_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        if input_grid is None:
            input_grid = runtime_context.get("input_grid")
        if output_grid is None:
            output_grid = runtime_context.get("output_grid")
        if output_grid is None:
            output_grid = runtime_context.get("target_grid")
        concepts = self._collect_concepts(
            detected_concepts,
            dependency_activation_report,
            runtime_context,
        )
        dependency_chains = self._dependency_chains(
            dependency_activation_report,
            runtime_context,
        )
        families = self._discover_families(concepts, dependency_chains)
        models = self._generate_hypotheses(
            families,
            concepts,
            dependency_chains,
            input_grid,
            output_grid,
        )
        models.extend(self._memory_hypotheses(families))
        evaluated = self._evaluate_models(models, input_grid, output_grid)
        selected = evaluated[0] if evaluated else None
        registered = []
        if selected:
            registered.append(self._register_model(selected))
            self.memory.remember(
                selected,
                simulation_accuracy=selected.get("simulation", {}).get(
                    "simulation_accuracy",
                    0.0,
                ),
                success=selected.get("validation", {}).get(
                    "process_validated",
                    False,
                ),
                evidence={
                    "concepts": concepts,
                    "families": families,
                },
            )

        process_context_count = len(evaluated)
        transition_count = sum(
            len(model.get("transition_sequence", []) or [])
            for model in evaluated
        )
        state_count = sum(
            model.get("state_count", 0)
            for model in evaluated
        )
        process_depth = max(
            [model.get("process_depth", 0) for model in evaluated] or [0]
        )
        process_confidence = (
            selected.get("confidence", 0.0)
            if selected
            else 0.0
        )
        simulation_accuracy = (
            selected.get("simulation", {}).get("simulation_accuracy", 0.0)
            if selected
            else 0.0
        )
        reuse_hits = len([model for model in evaluated if model.get("reuse_hit")])
        promotion_status = (
            "PROCESS_CONTEXT_PROMOTED"
            if selected and selected.get("validation", {}).get("process_validated")
            else "PROCESS_CONTEXT_SUPPORTED"
            if selected
            else "PROCESS_CONTEXT_NOT_GENERATED"
        )
        success_count = len(
            [
                model
                for model in evaluated
                if model.get("validation", {}).get("process_validated")
            ]
        )

        report = {
            "system": self.system_name,
            "process_contexts": evaluated,
            "selected_process_context": selected or {},
            "registered_contexts": registered,
            "process_contexts_generated": process_context_count,
            "process_families_detected": families,
            "transition_count": transition_count,
            "state_count": state_count,
            "process_depth": process_depth,
            "process_confidence": round(float(process_confidence), 4),
            "simulation_accuracy": round(float(simulation_accuracy), 4),
            "reuse_hits": reuse_hits,
            "promotion_status": promotion_status,
            "process_context_count": process_context_count,
            "process_context_depth": process_depth,
            "process_context_confidence": round(float(process_confidence), 4),
            "process_simulation_time": 0.0001 if evaluated else 0.0,
            "state_transition_count": transition_count,
            "process_reuse_rate": round(reuse_hits / max(process_context_count, 1), 4),
            "process_success_rate": round(success_count / max(process_context_count, 1), 4),
            "timestamp": str(datetime.utcnow()),
        }
        report["PROCESS_CONTEXT_REPORT"] = {
            key: report[key]
            for key in [
                "process_contexts_generated",
                "process_families_detected",
                "transition_count",
                "state_count",
                "process_depth",
                "process_confidence",
                "simulation_accuracy",
                "reuse_hits",
                "promotion_status",
            ]
        }
        self.runtime_history.append(report)
        return report

    def _generate_hypotheses(
        self,
        families,
        concepts,
        dependency_chains,
        input_grid,
        output_grid,
    ):
        models = []
        for family in families:
            relevant_chain = self._best_chain_for_family(family, dependency_chains)
            transition_report = self.transition_engine.infer(
                input_grid=input_grid,
                output_grid=output_grid,
                dependency_chain=relevant_chain,
                concepts=concepts + [family],
            )
            base_model = self._model_from_transition_report(
                family,
                concepts,
                transition_report,
                relevant_chain,
                "observed_transition_hypothesis",
            )
            models.append(base_model)
            alternate = self._alternate_model(
                family,
                concepts,
                transition_report,
                relevant_chain,
            )
            if alternate:
                models.append(alternate)
        return models

    def _evaluate_models(self, models, input_grid, output_grid):
        evaluated = []
        for model in models:
            model_dict = model.as_dict() if hasattr(model, "as_dict") else dict(model)
            simulation = self.simulator.simulate(
                model_dict,
                input_grid=input_grid,
                output_grid=output_grid,
            )
            validation = self.simulator.validate(model_dict, simulation)
            confidence = clamp(
                model_dict.get("confidence", 0.0) * 0.35
                + simulation.get("simulation_accuracy", 0.0) * 0.30
                + validation.get("process_validation_score", 0.0) * 0.25
                + min(model_dict.get("process_depth", 0) / 4.0, 1.0) * 0.10
            )
            model_dict["simulation"] = simulation
            model_dict["validation"] = validation
            model_dict["confidence"] = round(confidence, 4)
            model_dict["process_context_confidence"] = round(confidence, 4)
            evaluated.append(model_dict)
        return sorted(
            evaluated,
            key=lambda item: (
                item.get("confidence", 0.0),
                item.get("simulation", {}).get("simulation_accuracy", 0.0),
            ),
            reverse=True,
        )

    def _model_from_transition_report(
        self,
        family,
        concepts,
        transition_report,
        dependency_chain,
        hypothesis_type,
    ):
        states = list(transition_report.get("states", []) or [])
        if not states:
            states = [
                {"state_name": "initial_state", "state_role": "initial_state"},
                {"state_name": "final_state", "state_role": "final_state"},
            ]
        initial = states[0]
        final = states[-1]
        intermediate = states[1:-1]
        dependencies = self._dependency_items(dependency_chain)
        transition_sequence = list(transition_report.get("transition_sequence", []) or [])
        return ProcessContextModel(
            context_name=f"{family}_runtime_context",
            concept=concepts[0] if concepts else family,
            process_family=family,
            initial_state=initial,
            intermediate_states=intermediate,
            final_state=final,
            transition_sequence=transition_sequence,
            dependencies=dependencies,
            constraints=self._constraints_for(family, transition_sequence),
            expected_outcomes=self._expected_outcomes_for(family, final),
            confidence=transition_report.get("transition_confidence", 0.0),
            transition_events=list(transition_report.get("transitions", []) or []),
            validation={"hypothesis_type": hypothesis_type},
        )

    def _alternate_model(self, family, concepts, transition_report, dependency_chain):
        transitions = list(transition_report.get("transitions", []) or [])
        if len(transitions) <= 1:
            return None
        reordered = sorted(
            transitions,
            key=lambda item: item.get("confidence", 0.0),
            reverse=True,
        )
        alternate_report = {
            **transition_report,
            "transitions": reordered,
            "transition_sequence": [
                item.get("transition")
                for item in reordered
            ],
            "transition_confidence": max(
                transition_report.get("transition_confidence", 0.0) - 0.04,
                0.0,
            ),
        }
        return self._model_from_transition_report(
            family,
            concepts,
            alternate_report,
            dependency_chain,
            "confidence_ordered_hypothesis",
        )

    def _memory_hypotheses(self, families):
        models = []
        for family in families:
            for record in self.memory.retrieve_successful(family):
                process_model = dict(record.get("process_model", {}))
                if process_model:
                    process_model["reuse_hit"] = True
                    process_model["confidence"] = max(
                        process_model.get("confidence", 0.0),
                        record.get("simulation_accuracy", 0.0),
                    )
                    models.append(process_model)
        return models

    def _register_model(self, model):
        context = ProcessContext(
            name=model.get("context_name", ""),
            concept=model.get("concept", ""),
            process_family=model.get("process_family", ""),
            preconditions=[
                model.get("initial_state", {}).get("state_name", "initial_state")
            ],
            transition_signature=list(model.get("transition_sequence", []) or []),
            postconditions=[
                model.get("final_state", {}).get("state_name", "final_state")
            ],
            invariants=[
                "dependency_consistency",
                "transition_consistency",
            ],
            dependency_links=list(model.get("dependencies", []) or []),
            temporal_signature={
                "model": "PROCESS_CONTEXT_RUNTIME",
                "state_count": model.get("state_count", 0),
                "transition_count": len(model.get("transition_sequence", []) or []),
            },
            context_strength=model.get("confidence", 0.0),
            identity_continuity=model.get("validation", {}).get(
                "object_identity_preservation",
                0.90,
            ),
            causal_alignment=model.get("validation", {}).get(
                "dependency_consistency",
                0.90,
            ),
            constraints=list(model.get("constraints", []) or []),
        )
        return self.registry.register(context)

    def _discover_families(self, concepts, dependency_chains):
        text = " ".join(
            concepts
            + [
                " ".join(self._dependency_items(chain))
                for chain in dependency_chains
            ]
        ).lower()
        families = []
        for family, keywords in self.FAMILY_KEYWORDS.items():
            if family in text or any(keyword in text for keyword in keywords):
                families.append(family)
        if not families and concepts:
            families.append("multi_step_reasoning")
        return list(dict.fromkeys(families))

    def _best_chain_for_family(self, family, dependency_chains):
        if not dependency_chains:
            return {}
        for chain in dependency_chains:
            concept = str(chain.get("concept", "")).lower()
            if family in concept:
                return chain
            if family == "relative_movement" and concept in {
                "relative_position",
                "spatial_relation",
            }:
                return chain
            if family == "bridge_creation" and "component" in concept:
                return chain
        return dependency_chains[0]

    def _dependency_chains(self, dependency_activation_report, runtime_context):
        candidates = []
        if isinstance(dependency_activation_report, Mapping):
            candidates.extend(
                dependency_activation_report.get(
                    "dependency_graph_report",
                    {},
                ).get("dependency_chains", []) or []
            )
        candidates.extend(runtime_context.get("dependency_chains", []) or [])
        return [dict(item) for item in candidates if isinstance(item, Mapping)]

    def _dependency_items(self, dependency_chain):
        if isinstance(dependency_chain, Mapping):
            items = (
                dependency_chain.get("chain")
                or dependency_chain.get("resolved_dependency_chain")
                or dependency_chain.get("dependencies")
                or []
            )
        else:
            items = dependency_chain or []
        return [str(item) for item in items if item is not None]

    def _collect_concepts(self, detected_concepts, dependency_activation_report, runtime_context):
        concepts = []

        def add(value):
            token = str(value).lower().replace("-", "_").replace(" ", "_").strip()
            if token and token not in concepts:
                concepts.append(token)

        for concept in detected_concepts or []:
            add(concept)
        if isinstance(dependency_activation_report, Mapping):
            for concept in dependency_activation_report.get("detected_concepts", []) or []:
                add(concept)

        def visit(value):
            if isinstance(value, str):
                token = value.lower().replace("-", "_").replace(" ", "_")
                if any(keyword in token for keywords in self.FAMILY_KEYWORDS.values() for keyword in keywords):
                    add(token)
            elif isinstance(value, Mapping):
                for key, item in value.items():
                    if key in {
                        "concept",
                        "concepts",
                        "detected_concepts",
                        "suspected_concepts",
                        "semantic_context",
                        "symbolic_type",
                        "abstract_rule",
                        "type",
                    }:
                        visit(item)
                    elif isinstance(item, (Mapping, list, tuple, set)):
                        visit(item)
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        for key in [
            "detected_concepts",
            "suspected_concepts",
            "semantic_abstractions",
            "concept_attribution_report",
            "semantic_attribution_report",
            "tool_selection_report",
            "pre_reasoning_task_profile",
            "task_profile",
        ]:
            visit(runtime_context.get(key))
        return concepts

    def _constraints_for(self, family, transitions):
        constraints = ["dependency_consistency_required"]
        if any("connect" in transition or "path" in transition for transition in transitions):
            constraints.append("connectivity_preservation_required")
        if family in {"relative_movement", "gravity", "support"}:
            constraints.append("spatial_consistency_required")
        return constraints

    def _expected_outcomes_for(self, family, final_state):
        outcome = final_state.get("state_name", "final_state")
        return [
            f"{family}_completed",
            str(outcome),
        ]


process_context_runtime = ProcessContextRuntime()


__all__ = [
    "ProcessContextModel",
    "ProcessContextRuntime",
    "process_context_runtime",
]
