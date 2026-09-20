"""Runtime coordinator for dynamic ARC concept intelligence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.dynamic_concepts.dynamic_concept_registry import (
    dynamic_concept_registry,
)
from runtime.dynamic_concepts.dynamic_simulation_engine import (
    dynamic_simulation_engine,
)
from runtime.dynamic_concepts.dynamic_topology_reasoning import (
    dynamic_topology_reasoning,
)
from runtime.dynamic_concepts.gravity_reasoning import gravity_reasoning
from runtime.dynamic_concepts.multi_step_reasoning import multi_step_reasoning
from runtime.dynamic_concepts.path_reasoning import path_reasoning
from runtime.dynamic_concepts.propagation_reasoning import propagation_reasoning
from runtime.dynamic_concepts.reachability_reasoning import reachability_reasoning
from runtime.dynamic_concepts.state_evolution_reasoning import (
    state_evolution_reasoning,
)
from runtime.dynamic_concepts.support_reasoning import support_reasoning
from runtime.memory.dynamic_concept_memory import dynamic_concept_memory


class DynamicConceptRuntime:
    """Turn dynamic concepts into simulated evolving systems."""

    system_name = "dynamic_concept_runtime"

    def __init__(
        self,
        reasoners=None,
        simulator=None,
        memory=None,
        registry=None,
    ):
        self.reasoners = reasoners or [
            gravity_reasoning,
            path_reasoning,
            propagation_reasoning,
            support_reasoning,
            state_evolution_reasoning,
            reachability_reasoning,
            multi_step_reasoning,
            dynamic_topology_reasoning,
        ]
        self.simulator = simulator or dynamic_simulation_engine
        self.memory = memory or dynamic_concept_memory
        self.registry = registry or dynamic_concept_registry
        self.runtime_history = []

    def run(
        self,
        input_grid=None,
        output_grid=None,
        detected_concepts: list[str] | None = None,
        dependency_activation_report: Mapping[str, Any] | None = None,
        process_context_report: Mapping[str, Any] | None = None,
        causal_context_report: Mapping[str, Any] | None = None,
        transformation_report: Mapping[str, Any] | None = None,
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
            process_context_report,
            causal_context_report,
            transformation_report,
            runtime_context,
        )
        runtime_payload = {
            **runtime_context,
            "detected_concepts": sorted(concepts),
        }
        models = []
        for reasoner in self.reasoners:
            models.extend(
                reasoner.reason(
                    input_grid=input_grid,
                    output_grid=output_grid,
                    causal_context_report=causal_context_report,
                    process_context_report=process_context_report,
                    runtime_context=runtime_payload,
                )
            )
        models.extend(self._memory_models({m.get("concept_family") for m in models}))
        evaluated = self._evaluate_models(
            models,
            input_grid,
            output_grid,
            dependency_activation_report,
            process_context_report,
            causal_context_report,
        )
        selected = evaluated[0] if evaluated else {}
        for model in evaluated:
            simulation = model.get("simulation", {})
            self.memory.remember(
                model,
                simulation,
                success=simulation.get("simulation_accuracy", 0.0) >= 0.80,
                evidence={
                    "concepts": sorted(concepts),
                    "runtime": self.system_name,
                },
            )
            self.registry.register(
                model,
                simulation,
                reused=bool(model.get("reuse_hit")),
            )

        dynamic_concepts = sorted(
            {
                model.get("dynamic_concept")
                for model in evaluated
                if model.get("dynamic_concept")
            }
        )
        simulations_executed = len(
            [model for model in evaluated if model.get("simulation", {}).get("simulation_executed")]
        )
        state_transitions = sum(
            len(model.get("state_transitions", []) or [])
            for model in evaluated
        )
        reuse_hits = len([model for model in evaluated if model.get("reuse_hit")])
        simulation_accuracy = selected.get("simulation", {}).get(
            "simulation_accuracy",
            0.0,
        ) if selected else 0.0
        prediction_gain = selected.get("simulation", {}).get(
            "prediction_gain",
            0.0,
        ) if selected else 0.0
        dependency_support = max(
            [model.get("dependency_support", 0.0) for model in evaluated] or [0.0]
        )
        process_support = max(
            [model.get("process_support", 0.0) for model in evaluated] or [0.0]
        )
        causal_support = max(
            [model.get("causal_support", 0.0) for model in evaluated] or [0.0]
        )
        report = {
            "system": self.system_name,
            "dynamic_models": evaluated,
            "selected_dynamic_model": selected,
            "dynamic_concepts_detected": dynamic_concepts,
            "simulations_executed": simulations_executed,
            "simulation_accuracy": round(float(simulation_accuracy), 4),
            "state_transitions_generated": state_transitions,
            "dependency_support": round(float(dependency_support), 4),
            "process_support": round(float(process_support), 4),
            "causal_support": round(float(causal_support), 4),
            "prediction_gain": round(float(prediction_gain), 4),
            "reuse_hits": reuse_hits,
            "dynamic_concept_count": len(dynamic_concepts),
            "dynamic_simulation_time": 0.0001 if evaluated else 0.0,
            "dynamic_prediction_gain": round(float(prediction_gain), 4),
            "gravity_reasoning_count": self._count_family(evaluated, "gravity"),
            "path_reasoning_count": self._count_family(evaluated, "path_finding"),
            "propagation_reasoning_count": self._count_family(evaluated, "propagation"),
            "multi_step_reasoning_count": self._count_family(
                evaluated,
                "multi_step_reasoning",
            ),
            "state_transition_count": state_transitions,
            "registry_report": self.registry.build_report(),
            "memory_report": self.memory.build_report(),
            "timestamp": str(datetime.utcnow()),
        }
        report["DYNAMIC_CONCEPT_REPORT"] = {
            key: report[key]
            for key in [
                "dynamic_concepts_detected",
                "simulations_executed",
                "simulation_accuracy",
                "state_transitions_generated",
                "dependency_support",
                "process_support",
                "causal_support",
                "prediction_gain",
                "reuse_hits",
            ]
        }
        self.runtime_history.append(report)
        return report

    def _evaluate_models(
        self,
        models,
        input_grid,
        output_grid,
        dependency_activation_report,
        process_context_report,
        causal_context_report,
    ):
        evaluated = []
        for model in models:
            model = dict(model)
            model["dependency_support"] = self._dependency_support(
                model,
                dependency_activation_report,
            )
            model["process_support"] = self._process_support(
                model,
                process_context_report,
            )
            model["causal_support"] = self._causal_support(
                model,
                causal_context_report,
            )
            simulation = self.simulator.simulate(
                model,
                input_grid=input_grid,
                output_grid=output_grid,
            )
            model["simulation"] = simulation
            model["confidence"] = round(
                min(
                    float(model.get("confidence", 0.0) or 0.0) * 0.35
                    + simulation.get("simulation_accuracy", 0.0) * 0.30
                    + model["dependency_support"] * 0.10
                    + model["process_support"] * 0.12
                    + model["causal_support"] * 0.13,
                    1.0,
                ),
                4,
            )
            evaluated.append(model)
        return sorted(
            evaluated,
            key=lambda item: (
                item.get("confidence", 0.0),
                item.get("simulation", {}).get("prediction_gain", 0.0),
                item.get("simulation", {}).get("simulation_accuracy", 0.0),
            ),
            reverse=True,
        )

    def _collect_concepts(self, *sources):
        concepts = set()
        for source in sources:
            if not source:
                continue
            if isinstance(source, (list, tuple, set)):
                concepts.update(str(item) for item in source)
                continue
            if not isinstance(source, Mapping):
                continue
            for key in (
                "detected_concepts",
                "dynamic_concepts_detected",
                "process_families_detected",
                "causal_families_detected",
                "generated_transformations",
            ):
                value = source.get(key, [])
                if isinstance(value, Mapping):
                    value = value.keys()
                if isinstance(value, (list, tuple, set)):
                    concepts.update(str(item) for item in value)
            report = source.get("DYNAMIC_CONCEPT_REPORT", {})
            if isinstance(report, Mapping):
                concepts.update(
                    str(item)
                    for item in report.get("dynamic_concepts_detected", []) or []
                )
        return concepts

    def _dependency_support(self, model, report):
        report = report if isinstance(report, Mapping) else {}
        activated = set(str(item) for item in report.get("activated_tools", []) or [])
        if not report:
            return 0.0
        family = model.get("concept_family")
        if family in {"gravity", "path_finding", "support", "dynamic_topology"}:
            needed = {"dependency_reasoning"}
        else:
            needed = set()
        if needed and needed.intersection(activated):
            return 1.0
        return float(report.get("dependency_chain_coverage", 0.0) or 0.0)

    def _process_support(self, model, report):
        report = report if isinstance(report, Mapping) else {}
        families = set(str(item) for item in report.get("process_families_detected", []) or [])
        family = model.get("concept_family")
        aliases = {
            "path_finding": {"path_finding", "route_completion"},
            "dynamic_topology": {"bridge_creation", "growth"},
            "state_evolution": {"transformation_sequence", "multi_step_reasoning"},
        }.get(family, {family})
        if families.intersection(aliases):
            return max(float(report.get("process_context_confidence", 0.0) or 0.0), 0.85)
        return float(report.get("process_context_confidence", 0.0) or 0.0)

    def _causal_support(self, model, report):
        report = report if isinstance(report, Mapping) else {}
        families = set(str(item) for item in report.get("causal_families_detected", []) or [])
        family = model.get("concept_family")
        aliases = {
            "gravity": {"gravity_cause"},
            "path_finding": {"path_cause"},
            "dynamic_topology": {"bridge_cause"},
            "propagation": {"growth_cause"},
        }.get(family, {f"{family}_cause"})
        if families.intersection(aliases):
            return max(float(report.get("causal_confidence", 0.0) or 0.0), 0.86)
        return float(report.get("causal_confidence", 0.0) or 0.0)

    def _memory_models(self, families):
        models = []
        for family in families:
            if not family:
                continue
            for record in self.memory.retrieve_successful(str(family)):
                model = dict(record.get("dynamic_model", {}))
                if model:
                    model["reuse_hit"] = True
                    model["confidence"] = max(
                        float(model.get("confidence", 0.0) or 0.0),
                        float(
                            record.get("simulation_report", {}).get(
                                "simulation_accuracy",
                                0.0,
                            )
                            or 0.0
                        ),
                    )
                    models.append(model)
        return models

    def _count_family(self, models, family):
        return len([model for model in models if model.get("concept_family") == family])


dynamic_concept_runtime = DynamicConceptRuntime()


__all__ = ["DynamicConceptRuntime", "dynamic_concept_runtime"]
