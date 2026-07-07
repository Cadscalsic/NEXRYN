"""Runtime layer for causal context understanding."""

from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any, Mapping

from runtime.causal.causal_inference_engine import (
    CausalContextModel,
    causal_inference_engine,
)
from runtime.causal.causal_simulator import causal_simulator
from runtime.memory.causal_context_memory import causal_context_memory


class CausalContextRuntime:
    """Convert process contexts into active causal contexts."""

    system_name = "causal_context_runtime"

    def __init__(self, inference_engine=None, simulator=None, memory=None):
        self.inference_engine = inference_engine or causal_inference_engine
        self.simulator = simulator or causal_simulator
        self.memory = memory or causal_context_memory
        self.runtime_history = []

    def run(
        self,
        input_grid=None,
        output_grid=None,
        process_context_report: Mapping[str, Any] | None = None,
        dependency_activation_report: Mapping[str, Any] | None = None,
        transformation_report: Mapping[str, Any] | None = None,
        color_mapping_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        started_at = perf_counter()
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        if input_grid is None:
            input_grid = runtime_context.get("input_grid")
        if output_grid is None:
            output_grid = runtime_context.get("output_grid")
        if output_grid is None:
            output_grid = runtime_context.get("target_grid")

        inference = self.inference_engine.infer(
            process_context_report=process_context_report,
            dependency_activation_report=dependency_activation_report,
            transformation_report=transformation_report,
            color_mapping_report=color_mapping_report,
            input_grid=input_grid,
            output_grid=output_grid,
            runtime_context=runtime_context,
        )
        inference_time = round(perf_counter() - started_at, 6)
        contexts = list(inference.get("causal_contexts", []) or [])
        contexts.extend(self._memory_contexts(inference.get("causal_families_detected", [])))
        simulation_started = perf_counter()
        evaluated = self._evaluate_contexts(
            contexts,
            input_grid,
            output_grid,
            process_context_report or {},
        )
        simulation_time = round(perf_counter() - simulation_started, 6)
        selected = evaluated[0] if evaluated else {}
        for context in evaluated:
            self.memory.remember(
                context,
                simulation_accuracy=context.get(
                    "simulation",
                    {},
                ).get("causal_simulation_accuracy", 0.0),
                success=context.get("validation", {}).get(
                    "causal_context_validated",
                    False,
                ),
                evidence={
                    "runtime": self.system_name,
                },
            )

        causal_context_count = len(evaluated)
        causal_families = sorted(
            {context.get("causal_family") for context in evaluated if context.get("causal_family")}
        )
        cause_effect_pairs = [
            context.get("cause_effect_pair", {
                "cause": context.get("cause"),
                "effect": context.get("effect"),
                "confidence": context.get("confidence", 0.0),
                "evidence": context.get("evidence", {}),
                "dependency_source": context.get("dependency_source", ""),
                "process_source": context.get("process_source", ""),
                "truth_source": context.get("truth_source", ""),
                "temporal_order": context.get("temporal_order", 0),
                "activation_reason": context.get("activation_reason", ""),
            })
            for context in evaluated
        ]
        confidence = selected.get("confidence", 0.0) if selected else 0.0
        validation_score = (
            selected.get("validation", {}).get("causal_validation_score", 0.0)
            if selected
            else 0.0
        )
        simulation_accuracy = (
            selected.get("simulation", {}).get("causal_simulation_accuracy", 0.0)
            if selected
            else 0.0
        )
        reuse_hits = len([context for context in evaluated if context.get("reuse_hit")])
        failures = [
            context
            for context in evaluated
            if not context.get("validation", {}).get("causal_context_validated")
        ]
        success_count = causal_context_count - len(failures)
        prediction_gain = max(
            [
                context.get("simulation", {}).get("causal_prediction_gain", 0.0)
                for context in evaluated
            ]
            or [0.0]
        )
        report = {
            "system": self.system_name,
            "causal_runtime_called": True,
            "causal_generation_attempted": True,
            "causal_contexts": evaluated,
            "selected_causal_context": selected,
            "causal_context_count": causal_context_count,
            "causal_graph_count": 1 if evaluated else 0,
            "causal_families_detected": causal_families,
            "cause_effect_pairs": cause_effect_pairs,
            "causal_graph": inference.get("causal_graph", self._causal_graph(evaluated)),
            "event_transitions": inference.get("event_transitions", []),
            "root_cause_candidates": inference.get("root_cause_candidates", []),
            "propagation_chains": inference.get("propagation_chains", []),
            "causal_confidence": round(float(confidence), 4),
            "causal_validation_score": round(float(validation_score), 4),
            "causal_simulation_accuracy": round(float(simulation_accuracy), 4),
            "causal_reuse_hits": reuse_hits,
            "causal_failures": failures,
            "blocked_contexts": inference.get("blocked_contexts", []),
            "block_reasons": inference.get("block_reasons", []),
            "causal_context_depth": max(
                [
                    len(
                        context.get("causal_chain", [])
                        or context.get("supporting_dependencies", [])
                        or []
                    )
                    for context in evaluated
                ]
                or [0]
            ),
            "causal_chain_depth": max(
                [
                    len(context.get("causal_chain", []) or [])
                    for context in evaluated
                ]
                or [0]
            ),
            "causal_inference_time": max(inference_time, 0.0001) if evaluated else inference_time,
            "causal_simulation_time": max(simulation_time, 0.0001) if evaluated else simulation_time,
            "generation_time": round(perf_counter() - started_at, 6),
            "causal_success_rate": round(success_count / max(causal_context_count, 1), 4),
            "causal_reuse_rate": round(reuse_hits / max(causal_context_count, 1), 4),
            "causal_prediction_gain": round(float(prediction_gain), 4),
            "confidence_distribution": self._confidence_distribution(evaluated),
            "generation_summary": self._generation_summary(
                causal_context_count,
                inference.get("block_reasons", []),
            ),
            "timestamp": str(datetime.utcnow()),
        }
        report["CAUSAL_CONTEXT_REPORT"] = {
            "causal_runtime_called": report["causal_runtime_called"],
            "causal_generation_attempted": report["causal_generation_attempted"],
            "causal_context_count": report["causal_context_count"],
            "causal_graph_count": report["causal_graph_count"],
            "cause_effect_pairs": report["cause_effect_pairs"],
            "causal_chain_depth": report["causal_chain_depth"],
            "root_causes": report["root_cause_candidates"],
            "propagation_paths": report["propagation_chains"],
            "generated_contexts": report["causal_contexts"],
            "blocked_contexts": report["blocked_contexts"],
            "block_reasons": report["block_reasons"],
            "generation_time": report["generation_time"],
            "confidence_distribution": report["confidence_distribution"],
            "generation_summary": report["generation_summary"],
            "causal_families_detected": report["causal_families_detected"],
            "causal_confidence": report["causal_confidence"],
            "causal_validation_score": report["causal_validation_score"],
            "causal_simulation_accuracy": report["causal_simulation_accuracy"],
            "causal_reuse_hits": report["causal_reuse_hits"],
            "causal_failures": report["causal_failures"],
        }
        self.runtime_history.append(report)
        return report

    def _evaluate_contexts(
        self,
        contexts,
        input_grid,
        output_grid,
        process_context_report,
    ):
        evaluated = []
        for context in contexts:
            context = dict(context)
            simulation = self.simulator.simulate(
                context,
                input_grid=input_grid,
                output_grid=output_grid,
            )
            validation = self.simulator.validate(
                context,
                simulation,
                process_context_report=process_context_report,
            )
            confidence = float(context.get("confidence", context.get("causal_confidence", 0.0)) or 0.0)
            context["simulation"] = simulation
            context["validation"] = validation
            context["confidence"] = round(
                min(
                    confidence * 0.40
                    + validation.get("causal_validation_score", 0.0) * 0.35
                    + simulation.get("causal_simulation_accuracy", 0.0) * 0.25,
                    1.0,
                ),
                4,
            )
            context["causal_confidence"] = context["confidence"]
            evaluated.append(context)
        return sorted(
            evaluated,
            key=lambda item: (
                item.get("confidence", 0.0),
                item.get("simulation", {}).get("causal_simulation_accuracy", 0.0),
            ),
            reverse=True,
        )

    def _memory_contexts(self, families):
        contexts = []
        for family in families:
            for record in self.memory.retrieve_successful(family):
                context = dict(record.get("causal_context", {}))
                if context:
                    context["reuse_hit"] = True
                    context["confidence"] = max(
                        context.get("confidence", 0.0),
                        record.get("simulation_accuracy", 0.0),
                    )
                    contexts.append(context)
        return contexts

    def _confidence_distribution(self, contexts):
        low = medium = high = 0
        for context in contexts:
            confidence = float(context.get("confidence", 0.0) or 0.0)
            if confidence >= 0.80:
                high += 1
            elif confidence >= 0.60:
                medium += 1
            else:
                low += 1
        return {
            "high": high,
            "medium": medium,
            "low": low,
        }

    def _generation_summary(self, count, block_reasons):
        if count > 0:
            return "generated_causal_contexts_from_runtime_evidence"
        return {
            "state": "CAUSAL_CONTEXT_BLOCKED",
            "reasons": list(block_reasons or []),
        }

    def _causal_graph(self, contexts):
        nodes = sorted({
            value
            for context in contexts
            for value in (
                context.get("cause"),
                context.get("effect"),
            )
            if value
        })
        edges = [
            {
                "source": context.get("cause"),
                "target": context.get("effect"),
                "confidence": context.get("confidence", 0.0),
                "temporal_order": context.get("temporal_order", 0),
            }
            for context in contexts
        ]
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }


causal_context_runtime = CausalContextRuntime()


__all__ = [
    "CausalContextModel",
    "CausalContextRuntime",
    "causal_context_runtime",
]
