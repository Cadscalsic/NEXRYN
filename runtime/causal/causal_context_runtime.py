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
from runtime.instrumentation import runtime_lifecycle


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
        lifecycle_execution = runtime_lifecycle.create(
            module_name=self.system_name,
            runtime_name="Causal Runtime",
            caller="reasoning_orchestrator",
            trigger="causal_context_generation",
        )
        runtime_lifecycle.requested(lifecycle_execution)
        runtime_lifecycle.queued(lifecycle_execution)
        runtime_lifecycle.started(lifecycle_execution)
        runtime_lifecycle.running(lifecycle_execution)
        execution_start = lifecycle_execution.start_timestamp
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
        evaluated = self._enrich_contexts(evaluated)
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
        cause_effect_pairs = [context["cause_effect_pair"] for context in evaluated]
        propagation_paths = self._propagation_paths(evaluated)
        root_cause_analysis = self._root_cause_analysis(evaluated)
        causal_graph = inference.get("causal_graph", self._causal_graph(evaluated))
        causal_graph_statistics = self._causal_graph_statistics(
            causal_graph,
            cause_effect_pairs,
        )
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
        execution_end = str(datetime.utcnow())
        elapsed_time = round(max(perf_counter() - started_at, 0.0), 6)
        if causal_context_count > 0 and elapsed_time <= 0.0:
            elapsed_time = 0.0001
        if causal_context_count > 0:
            runtime_lifecycle.completed(
                lifecycle_execution,
                completion_reason="causal_contexts_generated",
                output_count=causal_context_count,
                memory_cost=causal_context_count + len(cause_effect_pairs),
            )
        else:
            runtime_lifecycle.blocked(
                lifecycle_execution,
                "CAUSAL_CONTEXT_NOT_GENERATED",
                metadata={"block_reasons": inference.get("block_reasons", [])},
            )
        runtime_lifecycle.reported(lifecycle_execution)
        lifecycle_data = lifecycle_execution.as_dict()
        execution_end = lifecycle_data["execution_end"]
        elapsed_time = max(lifecycle_data["elapsed_seconds"], elapsed_time)
        report = {
            "system": self.system_name,
            "execution_start": execution_start,
            "execution_end": execution_end,
            "start_timestamp": execution_start,
            "end_timestamp": execution_end,
            "elapsed_time": elapsed_time,
            "duration_seconds": elapsed_time,
            "cpu_cost": lifecycle_data["cpu_cost"],
            "memory_cost": causal_context_count + len(cause_effect_pairs),
            "input_count": len(contexts),
            "output_count": causal_context_count,
            "success": causal_context_count > 0,
            "failure": None if causal_context_count > 0 else "CAUSAL_CONTEXT_NOT_GENERATED",
            "invocation_count": 1,
            "average_duration": elapsed_time,
            "elapsed_seconds": elapsed_time,
            "wall_clock_time": lifecycle_data["wall_clock_time"],
            "cpu_time": lifecycle_data["cpu_time"],
            "exclusive_time": lifecycle_data["exclusive_time"],
            "inclusive_time": lifecycle_data["inclusive_time"],
            "execution_id": lifecycle_data["execution_id"],
            "runtime_lifecycle": lifecycle_data,
            "causal_runtime_called": True,
            "causal_generation_attempted": True,
            "causal_contexts": evaluated,
            "selected_causal_context": selected,
            "causal_context_count": causal_context_count,
            "causal_graph_count": 1 if evaluated else 0,
            "causal_families_detected": causal_families,
            "cause_effect_pairs": cause_effect_pairs,
            "causal_graph": causal_graph,
            "event_transitions": inference.get("event_transitions", []),
            "root_cause_candidates": root_cause_analysis["root_causes"],
            "secondary_causes": root_cause_analysis["secondary_causes"],
            "root_cause_analysis": root_cause_analysis,
            "propagation_chains": [
                context.get("propagation_chain", [])
                for context in evaluated
            ],
            "propagation_paths": propagation_paths,
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
            "causal_generation_time": elapsed_time,
            "generation_time": elapsed_time,
            "causal_success_rate": round(success_count / max(causal_context_count, 1), 4),
            "causal_reuse_rate": round(reuse_hits / max(causal_context_count, 1), 4),
            "causal_prediction_gain": round(float(prediction_gain), 4),
            "confidence_distribution": self._confidence_distribution(evaluated),
            "causal_relation_count": len(cause_effect_pairs),
            "average_chain_depth": self._average_chain_depth(propagation_paths),
            "average_confidence": self._average_confidence(cause_effect_pairs),
            "highest_confidence_relation": self._confidence_extreme(
                cause_effect_pairs,
                highest=True,
            ),
            "lowest_confidence_relation": self._confidence_extreme(
                cause_effect_pairs,
                highest=False,
            ),
            "causal_density": causal_graph_statistics.get("causal_density", 0.0),
            "causal_graph_statistics": causal_graph_statistics,
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
            "secondary_causes": report["secondary_causes"],
            "root_cause_analysis": report["root_cause_analysis"],
            "propagation_paths": report["propagation_paths"],
            "generated_contexts": report["causal_contexts"],
            "blocked_contexts": report["blocked_contexts"],
            "block_reasons": report["block_reasons"],
            "generation_time": report["generation_time"],
            "confidence_distribution": report["confidence_distribution"],
            "causal_relation_count": report["causal_relation_count"],
            "average_chain_depth": report["average_chain_depth"],
            "average_confidence": report["average_confidence"],
            "highest_confidence_relation": report["highest_confidence_relation"],
            "lowest_confidence_relation": report["lowest_confidence_relation"],
            "causal_density": report["causal_density"],
            "causal_graph_statistics": report["causal_graph_statistics"],
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

    def _enrich_contexts(self, contexts):
        enriched = []
        for index, context in enumerate(contexts):
            context = dict(context)
            cause = str(context.get("cause") or "unknown_cause")
            effect = str(context.get("effect") or "unknown_effect")
            confidence = round(float(context.get("confidence", 0.0) or 0.0), 4)
            chain = self._normalized_chain(context, cause, effect)
            supporting_dependencies = self._list_values(
                context.get("supporting_dependencies")
                or context.get("dependency_source")
            )
            supporting_processes = self._list_values(
                context.get("supporting_processes")
                or context.get("supporting_process")
                or context.get("process_source")
            )
            supporting_truths = self._list_values(
                context.get("supporting_truths")
                or context.get("truth_source")
            )
            contradictions = self._list_values(context.get("contradictions"))
            validation = context.get("validation", {})
            validation_status = (
                "validated"
                if validation.get("causal_context_validated")
                else "unvalidated"
            )
            support_count = len([
                item
                for item in [
                    context.get("evidence"),
                    supporting_dependencies,
                    supporting_processes,
                    supporting_truths,
                    context.get("simulation"),
                    validation,
                ]
                if item
            ])
            relation_type = str(
                context.get("relation_type")
                or context.get("causal_family")
                or "causal_relation"
            )
            relation_id = (
                context.get("relation_id")
                or f"causal_relation:{index}:{cause}->{effect}"
            )
            temporal_order = int(context.get("temporal_order", index) or 0)
            direct_effects = self._list_values(context.get("direct_effects")) or [effect]
            indirect_effects = [
                item
                for item in chain[chain.index(effect) + 1:]
                if effect in chain and item not in {"output", "final_state"} and item != effect
            ]
            indirect_effects.extend(self._list_values(context.get("indirect_effects")))
            indirect_effects = list(dict.fromkeys(indirect_effects))
            root_cause = str(context.get("root_cause") or chain[0] or cause)

            context["root_cause"] = root_cause
            context["direct_effects"] = direct_effects
            context["indirect_effects"] = indirect_effects
            context["propagation_chain"] = chain
            context["supporting_dependencies"] = supporting_dependencies
            context["supporting_processes"] = supporting_processes
            context["supporting_truths"] = supporting_truths
            context["confidence"] = confidence
            context["causal_confidence"] = confidence
            context["reasoning_summary"] = self._reasoning_summary(
                root_cause,
                cause,
                effect,
                chain,
                confidence,
                validation_status,
            )
            context["cause_effect_pair"] = {
                "relation_id": relation_id,
                "cause_id": cause,
                "effect_id": effect,
                "cause": cause,
                "effect": effect,
                "relation_type": relation_type,
                "confidence": confidence,
                "support_count": support_count,
                "contradicting_evidence": contradictions,
                "validation_status": validation_status,
                "evidence": context.get("evidence", {}),
                "temporal_order": temporal_order,
                "dependency_reference": (
                    context.get("dependency_source")
                    or ",".join(supporting_dependencies)
                ),
                "process_reference": (
                    context.get("process_source")
                    or ",".join(supporting_processes)
                ),
                "truth_reference": (
                    context.get("truth_source")
                    or ",".join(supporting_truths)
                ),
                "dependency_source": context.get("dependency_source", ""),
                "process_source": context.get("process_source", ""),
                "truth_source": context.get("truth_source", ""),
                "activation_reason": context.get("activation_reason", ""),
            }
            enriched.append(context)
        return enriched

    def _normalized_chain(self, context, cause, effect):
        raw_chain = (
            context.get("propagation_chain")
            or context.get("causal_chain")
            or [cause, effect]
        )
        chain = [str(item) for item in raw_chain if item is not None and str(item)]
        if cause not in chain:
            chain.insert(0, cause)
        if effect not in chain:
            chain.append(effect)
        if chain[0] == "input" and cause != "input":
            chain.insert(1, cause)
        if chain[-1] == "output" and effect != "output" and effect not in chain[:-1]:
            chain.insert(len(chain) - 1, effect)
        return list(dict.fromkeys(chain))

    def _list_values(self, value):
        if not value:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, Mapping):
            return [
                str(item)
                for item in (
                    value.get("id"),
                    value.get("name"),
                    value.get("concept"),
                )
                if item
            ]
        return [str(item) for item in value if item is not None and str(item)]

    def _reasoning_summary(
        self,
        root_cause,
        cause,
        effect,
        chain,
        confidence,
        validation_status,
    ):
        return (
            f"{root_cause} initiated {cause}, which produced {effect} "
            f"through {len(chain)} observed causal steps "
            f"({validation_status}, confidence={confidence:.4f})."
        )

    def _propagation_paths(self, contexts):
        paths = []
        for index, context in enumerate(contexts):
            chain = list(context.get("propagation_chain", []) or [])
            if not chain:
                continue
            paths.append({
                "path_id": f"propagation_path:{index}",
                "root_cause": context.get("root_cause"),
                "observed_effect": context.get("effect"),
                "final_state": chain[-1],
                "chain": chain,
                "chain_depth": len(chain),
                "confidence": context.get("confidence", 0.0),
                "supporting_dependencies": context.get("supporting_dependencies", []),
                "supporting_processes": context.get("supporting_processes", []),
                "supporting_truths": context.get("supporting_truths", []),
            })
        return paths

    def _root_cause_analysis(self, contexts):
        primary = []
        secondary = []
        supporting_conditions = []
        triggering_events = []
        blocking_conditions = []
        for context in contexts:
            root = context.get("root_cause")
            if root:
                primary.append(str(root))
            secondary.extend(context.get("supporting_dependencies", []) or [])
            supporting_conditions.extend(context.get("preconditions", []) or [])
            triggering_events.extend(context.get("trigger_conditions", []) or [])
            blocking_conditions.extend(context.get("contradictions", []) or [])
        root_causes = list(dict.fromkeys(primary))
        secondary_causes = [
            item for item in dict.fromkeys(secondary) if item not in root_causes
        ]
        return {
            "primary_root_cause": root_causes[0] if root_causes else "",
            "root_causes": root_causes,
            "secondary_root_causes": secondary_causes,
            "secondary_causes": secondary_causes,
            "supporting_conditions": list(dict.fromkeys(supporting_conditions)),
            "triggering_events": list(dict.fromkeys(triggering_events)),
            "blocking_conditions": list(dict.fromkeys(blocking_conditions)),
        }

    def _average_chain_depth(self, propagation_paths):
        if not propagation_paths:
            return 0.0
        return round(
            sum(path.get("chain_depth", 0) for path in propagation_paths)
            / len(propagation_paths),
            4,
        )

    def _average_confidence(self, relations):
        if not relations:
            return 0.0
        return round(
            sum(float(relation.get("confidence", 0.0) or 0.0) for relation in relations)
            / len(relations),
            4,
        )

    def _confidence_extreme(self, relations, highest):
        if not relations:
            return {}
        return dict(
            max(
                relations,
                key=lambda relation: float(relation.get("confidence", 0.0) or 0.0),
            )
            if highest
            else min(
                relations,
                key=lambda relation: float(relation.get("confidence", 0.0) or 0.0),
            )
        )

    def _causal_graph_statistics(self, graph, relations):
        nodes = list(graph.get("nodes", []) or [])
        edges = list(graph.get("edges", []) or [])
        node_count = int(graph.get("node_count", len(nodes)) or 0)
        edge_count = int(graph.get("edge_count", len(edges) or len(relations)) or 0)
        possible_edges = node_count * max(node_count - 1, 0)
        sources = {edge.get("source") for edge in edges if edge.get("source")}
        targets = {edge.get("target") for edge in edges if edge.get("target")}
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "relation_count": len(relations),
            "root_node_count": len(sources - targets),
            "leaf_node_count": len(targets - sources),
            "average_out_degree": round(edge_count / max(node_count, 1), 4),
            "causal_density": round(edge_count / possible_edges, 4)
            if possible_edges
            else 0.0,
            "cycles_detected": False,
        }

    def _confidence_distribution(self, contexts):
        low = medium = high = 0
        by_relation = {}
        for context in contexts:
            confidence = float(context.get("confidence", 0.0) or 0.0)
            if confidence >= 0.80:
                high += 1
            elif confidence >= 0.60:
                medium += 1
            else:
                low += 1
            pair = context.get("cause_effect_pair", {})
            relation_id = pair.get("relation_id") or context.get("context_id")
            if relation_id:
                by_relation[str(relation_id)] = round(confidence, 4)
        return {
            "high": high,
            "medium": medium,
            "low": low,
            "by_relation": by_relation,
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
