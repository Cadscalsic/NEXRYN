"""Infer cause-effect causal contexts from process runtime evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping

import numpy as np


@dataclass
class CausalContextModel:
    causal_family: str
    cause: str
    effect: str
    preconditions: list[str]
    trigger_conditions: list[str]
    state_before: dict[str, Any]
    state_after: dict[str, Any]
    constraints: list[str]
    supporting_process: str
    supporting_dependencies: list[str]
    confidence: float
    contradictions: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    context_id: str = ""
    origin: str = "causal_inference_engine"
    causal_chain: list[str] = field(default_factory=list)
    root_cause: str = ""
    direct_effects: list[str] = field(default_factory=list)
    indirect_effects: list[str] = field(default_factory=list)
    affected_nodes: list[str] = field(default_factory=list)
    supporting_truths: list[str] = field(default_factory=list)
    supporting_processes: list[str] = field(default_factory=list)
    dependency_source: str = ""
    process_source: str = ""
    truth_source: str = ""
    temporal_order: int = 0
    activation_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["context_id"] = self.context_id or (
            f"causal_context:{self.causal_family}:{self.cause}->{self.effect}"
        )
        data["root_cause"] = self.root_cause or self.cause
        data["causal_chain"] = self.causal_chain or [self.cause, self.effect]
        data["direct_effects"] = self.direct_effects or [self.effect]
        data["affected_nodes"] = self.affected_nodes or [self.effect]
        data["supporting_processes"] = (
            self.supporting_processes
            or ([self.supporting_process] if self.supporting_process else [])
        )
        data["dependency_source"] = self.dependency_source or (
            ",".join(self.supporting_dependencies)
            if self.supporting_dependencies
            else ""
        )
        data["process_source"] = self.process_source or self.supporting_process
        data["truth_source"] = self.truth_source or (
            ",".join(self.supporting_truths)
            if self.supporting_truths
            else ""
        )
        data["activation_reason"] = (
            self.activation_reason
            or f"{self.causal_family}_evidence_generated"
        )
        data["causal_confidence"] = round(float(self.confidence), 4)
        data["cause_effect_pair"] = {
            "cause": self.cause,
            "effect": self.effect,
            "confidence": data["causal_confidence"],
            "evidence": self.evidence,
            "dependency_source": data["dependency_source"],
            "process_source": data["process_source"],
            "truth_source": data["truth_source"],
            "temporal_order": self.temporal_order,
            "activation_reason": data["activation_reason"],
        }
        return data


class CausalInferenceEngine:
    """Build causal explanations from process, dependency, and transform evidence."""

    system_name = "causal_inference_engine"

    FAMILY_BY_TRANSITION = {
        "object_moved": "movement_cause",
        "path_constructed": "path_cause",
        "bridge_created": "bridge_cause",
        "object_recolored": "color_cause",
        "object_expanded": "growth_cause",
        "region_filled": "containment_cause",
        "object_removed": "occlusion_cause",
    }

    def infer(
        self,
        process_context_report: Mapping[str, Any] | None = None,
        dependency_activation_report: Mapping[str, Any] | None = None,
        transformation_report: Mapping[str, Any] | None = None,
        color_mapping_report: Mapping[str, Any] | None = None,
        input_grid=None,
        output_grid=None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        process_context_report = (
            process_context_report if isinstance(process_context_report, Mapping) else {}
        )
        dependency_activation_report = (
            dependency_activation_report
            if isinstance(dependency_activation_report, Mapping)
            else {}
        )
        transformation_report = (
            transformation_report if isinstance(transformation_report, Mapping) else {}
        )
        color_mapping_report = (
            color_mapping_report if isinstance(color_mapping_report, Mapping) else {}
        )

        contexts = []
        process_models = self._process_models(process_context_report, runtime_context)
        if process_context_report.get("selected_process_context"):
            process_models.insert(0, process_context_report["selected_process_context"])

        for process_model in process_models:
            contexts.extend(
                self._contexts_from_process(
                    process_model,
                    dependency_activation_report,
                    transformation_report,
                    color_mapping_report,
                    runtime_context,
                )
            )
        contexts.extend(
            self._contexts_from_observations(
                input_grid,
                output_grid,
                transformation_report,
                color_mapping_report,
                runtime_context,
            )
        )
        contexts.extend(
            self._contexts_from_dependency_templates(dependency_activation_report)
        )
        contexts.extend(
            self._contexts_from_dependency_reports(
                dependency_activation_report,
                process_context_report,
                runtime_context,
            )
        )
        contexts.extend(
            self._fallback_contexts_from_runtime_evidence(
                process_context_report,
                dependency_activation_report,
                runtime_context,
            )
        )
        contexts = self._dedupe(contexts)
        block_reasons = self._block_reasons(
            contexts,
            process_context_report,
            dependency_activation_report,
            input_grid,
            output_grid,
        )
        return {
            "system": self.system_name,
            "causal_generation_attempted": True,
            "causal_contexts": [context.as_dict() for context in contexts],
            "causal_context_count": len(contexts),
            "causal_graph_count": 1 if contexts else 0,
            "causal_families_detected": sorted(
                {context.causal_family for context in contexts}
            ),
            "cause_effect_pairs": [
                {"cause": context.cause, "effect": context.effect}
                for context in contexts
            ],
            "causal_graph": self._causal_graph(contexts),
            "event_transitions": self._event_transitions(contexts),
            "root_cause_candidates": sorted(
                {context.root_cause or context.cause for context in contexts}
            ),
            "propagation_chains": [
                (context.causal_chain or [context.cause, context.effect])
                for context in contexts
            ],
            "blocked_contexts": [] if contexts else [{
                "state": "CAUSAL_CONTEXT_BLOCKED",
                "block_reasons": block_reasons,
                "blocking_module": self.system_name,
            }],
            "block_reasons": block_reasons,
            "timestamp": str(datetime.utcnow()),
        }

    def _process_models(self, process_context_report, runtime_context):
        models = []
        models.extend(process_context_report.get("process_contexts", []) or [])
        registry = process_context_report.get("process_context_registry_report", {})
        if isinstance(registry, Mapping):
            models.extend(registry.get("process_contexts", []) or [])
        models.extend(process_context_report.get("registered_contexts", []) or [])
        runtime_registry = runtime_context.get("process_context_registry_report", {})
        if isinstance(runtime_registry, Mapping):
            models.extend(runtime_registry.get("process_contexts", []) or [])
        normalized = []
        for index, model in enumerate(models):
            if not isinstance(model, Mapping):
                continue
            normalized.append(self._normalize_process_model(model, index))
        return normalized

    def _normalize_process_model(self, model, index):
        if model.get("transition_events"):
            return dict(model)
        transition_sequence = (
            model.get("transition_sequence")
            or model.get("transition_signature")
            or model.get("transitions")
            or []
        )
        if isinstance(transition_sequence, str):
            transition_sequence = [transition_sequence]
        events = []
        for order, transition in enumerate(transition_sequence):
            text = str(transition)
            source = (
                model.get("initial_state", {}).get("state_name")
                if isinstance(model.get("initial_state"), Mapping)
                else None
            ) or f"state_{order}"
            target = (
                model.get("final_state", {}).get("state_name")
                if isinstance(model.get("final_state"), Mapping)
                else None
            ) or text or f"state_{order + 1}"
            if "->" in text:
                source, target = [part.strip() for part in text.split("->", 1)]
            events.append({
                "transition": text or f"{source}->{target}",
                "transition_type": self._transition_type(text, model),
                "confidence": model.get("confidence", model.get("context_strength", 0.78)),
                "temporal_order": order,
                "evidence": {
                    "source": source,
                    "target": target,
                    "transition_signature": text,
                },
            })
        if not events:
            preconditions = model.get("preconditions", []) or ["initial_state"]
            postconditions = model.get("postconditions", []) or ["final_state"]
            source = str(preconditions[0]) if preconditions else "initial_state"
            target = str(postconditions[-1]) if postconditions else "final_state"
            events.append({
                "transition": f"{source}->{target}",
                "transition_type": "dependency_step",
                "confidence": model.get("confidence", model.get("context_strength", 0.72)),
                "temporal_order": index,
                "evidence": {"source": source, "target": target},
            })
        normalized = dict(model)
        normalized.setdefault("context_name", model.get("name", f"process_context_{index}"))
        normalized.setdefault("process_family", model.get("process_family", model.get("concept", "process")))
        normalized.setdefault("initial_state", {"state_name": events[0]["evidence"]["source"]})
        normalized.setdefault("final_state", {"state_name": events[-1]["evidence"]["target"]})
        normalized.setdefault("dependencies", model.get("dependency_links", []))
        normalized.setdefault("constraints", model.get("invariants", []))
        normalized["transition_events"] = events
        return normalized

    def _contexts_from_process(
        self,
        process_model,
        dependency_activation_report,
        transformation_report,
        color_mapping_report,
        runtime_context,
    ):
        contexts = []
        family = str(process_model.get("process_family", "process"))
        dependencies = list(process_model.get("dependencies", []) or [])
        transitions = list(process_model.get("transition_events", []) or [])
        for transition in transitions:
            transition_type = transition.get("transition_type", "")
            causal_family = self._family_for(family, transition_type, runtime_context)
            if not causal_family:
                continue
            cause, effect = self._cause_effect_for(
                causal_family,
                transition,
                transformation_report,
                color_mapping_report,
                dependencies,
            )
            contexts.append(CausalContextModel(
                causal_family=causal_family,
                cause=cause,
                effect=effect,
                preconditions=self._preconditions_for(causal_family, process_model),
                trigger_conditions=self._triggers_for(causal_family, transition),
                state_before=dict(process_model.get("initial_state", {}) or {}),
                state_after=dict(process_model.get("final_state", {}) or {}),
                constraints=list(process_model.get("constraints", []) or []),
                supporting_process=family,
                supporting_dependencies=dependencies,
                confidence=self._confidence(
                    transition.get("confidence", 0.0),
                    process_model.get("confidence", 0.0),
                    dependency_activation_report.get("dependency_confidence", 0.0),
                ),
                contradictions=list(runtime_context.get("contradictions", []) or []),
                evidence={
                    "transition": transition,
                    "process_context": process_model.get("context_name"),
                },
                context_id=(
                    f"causal_context:{process_model.get('context_name', family)}:"
                    f"{transition.get('temporal_order', 0)}"
                ),
                causal_chain=[
                    "input",
                    cause,
                    transition.get("transition", transition_type),
                    effect,
                    "output",
                ],
                root_cause=cause,
                direct_effects=[effect],
                indirect_effects=list(process_model.get("expected_outcomes", []) or []),
                affected_nodes=[effect] + list(process_model.get("expected_outcomes", []) or []),
                supporting_truths=self._truth_sources(runtime_context),
                supporting_processes=[family],
                dependency_source=",".join(dependencies),
                process_source=str(process_model.get("context_name", family)),
                truth_source=",".join(self._truth_sources(runtime_context)),
                temporal_order=int(transition.get("temporal_order", 0) or 0),
                activation_reason="process_transition_evidence",
            ))
        return contexts

    def _contexts_from_observations(
        self,
        input_grid,
        output_grid,
        transformation_report,
        color_mapping_report,
        runtime_context,
    ):
        source = self._array(input_grid)
        target = self._array(output_grid)
        contexts = []
        if source.size and target.size and source.shape == target.shape:
            if self._movement_detected(source, target):
                contexts.append(CausalContextModel(
                    causal_family="movement_cause",
                    cause="translation_rule_required_relocation",
                    effect="object_position_changed",
                    preconditions=["object_identity_exists", "target_position_available"],
                    trigger_conditions=["relative_position_changed"],
                    state_before={"grid_shape": list(source.shape)},
                    state_after={"grid_shape": list(target.shape)},
                    constraints=["spatial_consistency_required"],
                    supporting_process="observed_spatial_transition",
                    supporting_dependencies=[],
                    confidence=0.82,
                    evidence={"source": "observed_centroid_delta"},
                    context_id="causal_context:observation:movement",
                    causal_chain=[
                        "input",
                        "translation_rule_required_relocation",
                        "object_position_changed",
                        "output",
                    ],
                    root_cause="translation_rule_required_relocation",
                    direct_effects=["object_position_changed"],
                    affected_nodes=["object_position_changed"],
                    temporal_order=0,
                    activation_reason="world_model_observed_centroid_delta",
                ))
            if color_mapping_report.get("mapping_matrix", {}).get("mapping"):
                contexts.append(CausalContextModel(
                    causal_family="color_cause",
                    cause="symbolic_mapping_changed",
                    effect="object_color_changed",
                    preconditions=["source_color_exists", "target_color_available"],
                    trigger_conditions=["color_mapping_discovered"],
                    state_before={"palette": self._palette(source)},
                    state_after={"palette": self._palette(target)},
                    constraints=["identity_or_symbol_mapping_consistent"],
                    supporting_process="color_mapping_reasoning",
                    supporting_dependencies=[],
                    confidence=max(
                        float(color_mapping_report.get("mapping_confidence", 0.0) or 0.0),
                        0.82,
                    ),
                    evidence={"mapping_matrix": color_mapping_report.get("mapping_matrix", {})},
                    context_id="causal_context:observation:color",
                    causal_chain=[
                        "input",
                        "symbolic_mapping_changed",
                        "object_color_changed",
                        "output",
                    ],
                    root_cause="symbolic_mapping_changed",
                    direct_effects=["object_color_changed"],
                    affected_nodes=["object_color_changed"],
                    activation_reason="color_mapping_evidence",
                ))
            if np.sum(target != 0) > np.sum(source != 0):
                contexts.append(CausalContextModel(
                    causal_family="growth_cause",
                    cause="boundary_or_repetition_rule_applied",
                    effect="object_area_expanded",
                    preconditions=["object_exists"],
                    trigger_conditions=["foreground_area_increased"],
                    state_before={"foreground_area": int(np.sum(source != 0))},
                    state_after={"foreground_area": int(np.sum(target != 0))},
                    constraints=["topology_preservation_or_valid_growth"],
                    supporting_process="observed_growth_transition",
                    supporting_dependencies=[],
                    confidence=0.76,
                    evidence={"source": "foreground_area_delta"},
                    context_id="causal_context:observation:growth",
                    causal_chain=[
                        "input",
                        "boundary_or_repetition_rule_applied",
                        "object_area_expanded",
                        "output",
                    ],
                    root_cause="boundary_or_repetition_rule_applied",
                    direct_effects=["object_area_expanded"],
                    affected_nodes=["object_area_expanded"],
                    activation_reason="world_model_foreground_area_delta",
                ))
        selected_program = transformation_report.get("selected_program", {})
        for step in selected_program.get("steps", []) or []:
            if step.get("operation") == "translate":
                contexts.append(CausalContextModel(
                    causal_family="movement_cause",
                    cause="translation_rule_required_relocation",
                    effect="object_position_changed",
                    preconditions=["translation_program_selected"],
                    trigger_conditions=["translate_operation_present"],
                    state_before={},
                    state_after={},
                    constraints=["translation_vector_consistent"],
                    supporting_process="transformation_synthesis",
                    supporting_dependencies=[],
                    confidence=float(transformation_report.get("transformation_confidence", 0.8) or 0.8),
                    evidence={"program_step": step},
                    context_id="causal_context:program:translate",
                    causal_chain=[
                        "input",
                        "translation_rule_required_relocation",
                        "translate_operation_present",
                        "object_position_changed",
                        "output",
                    ],
                    root_cause="translation_rule_required_relocation",
                    direct_effects=["object_position_changed"],
                    affected_nodes=["object_position_changed"],
                    activation_reason="execution_program_step",
                ))
        return contexts

    def _contexts_from_dependency_templates(self, dependency_activation_report):
        contexts = []
        for item in dependency_activation_report.get("causal_contexts", []) or []:
            concept = str(item.get("concept", "dependency"))
            family = self._family_for(concept, "", {"detected_concepts": [concept]})
            contexts.append(CausalContextModel(
                causal_family=family or "dependency_cause",
                cause=str(item.get("cause", "dependency_cause")),
                effect=str(item.get("effect", "dependency_effect")),
                preconditions=[str(item.get("cause", "dependency_cause"))],
                trigger_conditions=[str(item.get("dependency_relationship", "causes"))],
                state_before={"state": item.get("cause")},
                state_after={"state": item.get("effect")},
                constraints=["dependency_relationship_supported"],
                supporting_process=str(item.get("process_concept", concept)),
                supporting_dependencies=[
                    str(item.get("cause")),
                    str(item.get("effect")),
                ],
                confidence=float(item.get("causal_confidence", 0.82) or 0.82),
                evidence={"dependency_template": item},
                context_id=f"causal_context:dependency_template:{concept}:{item.get('state_transition', '')}",
                causal_chain=[
                    "input",
                    str(item.get("cause", "dependency_cause")),
                    str(item.get("effect", "dependency_effect")),
                    "output",
                ],
                root_cause=str(item.get("cause", "dependency_cause")),
                direct_effects=[str(item.get("effect", "dependency_effect"))],
                affected_nodes=[
                    str(item.get("cause", "dependency_cause")),
                    str(item.get("effect", "dependency_effect")),
                ],
                supporting_processes=[str(item.get("process_concept", concept))],
                dependency_source=str(item.get("dependency_relationship", "causes")),
                process_source=str(item.get("process_concept", concept)),
                temporal_order=len(contexts),
                activation_reason="dependency_causal_template",
            ))
        return contexts

    def _contexts_from_dependency_reports(
        self,
        dependency_activation_report,
        process_context_report,
        runtime_context,
    ):
        contexts = []
        reports = []
        reports.extend(dependency_activation_report.get("dependency_reports", []) or [])
        reports.extend(dependency_activation_report.get("dependency_chains", []) or [])
        reports.extend(runtime_context.get("dependency_chains", []) or [])
        process_family = (
            process_context_report.get("selected_process_context", {})
            if isinstance(process_context_report.get("selected_process_context"), Mapping)
            else {}
        ).get("process_family", "dependency_runtime")
        for report in reports:
            if not isinstance(report, Mapping):
                continue
            chain = (
                report.get("resolved_dependency_chain")
                or report.get("chain")
                or report.get("dependencies")
                or []
            )
            chain = [str(item) for item in chain if item is not None]
            if len(chain) < 2:
                continue
            concept = str(report.get("concept") or chain[0])
            for order, (cause, effect) in enumerate(zip(chain, chain[1:])):
                family = self._family_for(concept, "dependency_step", runtime_context)
                contexts.append(CausalContextModel(
                    causal_family=family or "dependency_cause",
                    cause=cause,
                    effect=effect,
                    preconditions=[cause],
                    trigger_conditions=["dependency_chain_executed"],
                    state_before={"state": cause},
                    state_after={"state": effect},
                    constraints=["dependency_order_preserved"],
                    supporting_process=str(process_family),
                    supporting_dependencies=chain,
                    confidence=float(report.get("dependency_confidence", 0.78) or 0.78),
                    contradictions=list(runtime_context.get("contradictions", []) or []),
                    evidence={"dependency_report": report},
                    context_id=f"causal_context:dependency_report:{concept}:{order}",
                    causal_chain=["input", *chain, "output"],
                    root_cause=chain[0],
                    direct_effects=[effect],
                    indirect_effects=chain[order + 2:],
                    affected_nodes=chain,
                    supporting_truths=self._truth_sources(runtime_context),
                    supporting_processes=[str(process_family)],
                    dependency_source=concept,
                    process_source=str(process_family),
                    truth_source=",".join(self._truth_sources(runtime_context)),
                    temporal_order=order,
                    activation_reason="dependency_chain_executed",
                ))
        return contexts

    def _fallback_contexts_from_runtime_evidence(
        self,
        process_context_report,
        dependency_activation_report,
        runtime_context,
    ):
        if process_context_report.get("process_context_count", 0) <= 0:
            return []
        if (
            dependency_activation_report.get("dependency_chains_executed", 0) <= 0
            and dependency_activation_report.get("dependency_chain_count", 0) <= 0
            and not dependency_activation_report.get("dependency_reports")
        ):
            return []
        selected = process_context_report.get("selected_process_context", {})
        selected = selected if isinstance(selected, Mapping) else {}
        family = str(selected.get("process_family") or "multi_step_reasoning")
        dependencies = list(selected.get("dependencies", []) or [])
        if not dependencies:
            for item in dependency_activation_report.get("dependency_reports", []) or []:
                if isinstance(item, Mapping):
                    dependencies = [
                        str(value)
                        for value in (
                            item.get("resolved_dependency_chain")
                            or item.get("chain")
                            or item.get("dependencies")
                            or []
                        )
                    ]
                    if dependencies:
                        break
        cause = dependencies[0] if dependencies else "dependency_runtime_completed"
        effect = (
            selected.get("final_state", {}).get("state_name")
            if isinstance(selected.get("final_state"), Mapping)
            else None
        ) or "process_outcome_supported"
        return [CausalContextModel(
            causal_family=self._family_for(family, "dependency_step", runtime_context) or "dependency_cause",
            cause=str(cause),
            effect=str(effect),
            preconditions=[str(cause)],
            trigger_conditions=["dependency_and_process_runtime_completed"],
            state_before={"state": str(cause)},
            state_after={"state": str(effect)},
            constraints=["process_dependency_alignment_required"],
            supporting_process=family,
            supporting_dependencies=dependencies,
            confidence=max(float(selected.get("confidence", 0.0) or 0.0), 0.74),
            contradictions=list(runtime_context.get("contradictions", []) or []),
            evidence={
                "process_context_count": process_context_report.get("process_context_count"),
                "dependency_chains_executed": dependency_activation_report.get("dependency_chains_executed"),
            },
            context_id=f"causal_context:fallback:{family}",
            causal_chain=["input", str(cause), family, str(effect), "output"],
            root_cause=str(cause),
            direct_effects=[str(effect)],
            affected_nodes=[str(cause), family, str(effect)],
            supporting_truths=self._truth_sources(runtime_context),
            supporting_processes=[family],
            dependency_source=",".join(dependencies),
            process_source=family,
            truth_source=",".join(self._truth_sources(runtime_context)),
            activation_reason="dependency_process_runtime_alignment",
        )]

    def _family_for(self, process_family, transition_type, runtime_context):
        text = " ".join([
            str(process_family),
            str(transition_type),
            str(runtime_context.get("detected_concepts", "")),
        ]).lower()
        if "gravity" in text or "support" in text or "fall" in text:
            return "gravity_cause"
        if "bridge" in text or "component" in text or transition_type == "bridge_created":
            return "bridge_cause"
        if "path" in text or "route" in text or transition_type == "path_constructed":
            return "path_cause"
        if "contain" in text or "inside" in text or "region" in text:
            return "containment_cause"
        if "occlusion" in text or transition_type == "object_removed":
            return "occlusion_cause"
        if "color" in text or transition_type == "object_recolored":
            return "color_cause"
        if "growth" in text or transition_type == "object_expanded":
            return "growth_cause"
        if "movement" in text or "relative" in text or transition_type == "object_moved":
            return "movement_cause"
        if transition_type == "dependency_step":
            return "dependency_cause"
        return None

    def _transition_type(self, transition_text, process_model):
        text = " ".join([
            str(transition_text),
            str(process_model.get("process_family", "")),
            str(process_model.get("concept", "")),
        ]).lower()
        if "bridge" in text or "connect" in text:
            return "bridge_created"
        if "path" in text or "route" in text:
            return "path_constructed"
        if "color" in text or "recolor" in text:
            return "object_recolored"
        if "growth" in text or "expand" in text:
            return "object_expanded"
        if "move" in text or "position" in text:
            return "object_moved"
        if "remove" in text or "occlusion" in text:
            return "object_removed"
        return "dependency_step"

    def _cause_effect_for(
        self,
        causal_family,
        transition,
        transformation_report,
        color_mapping_report,
        dependencies,
    ):
        if causal_family == "movement_cause":
            return "translation_rule_required_relocation", "object_position_changed"
        if causal_family == "gravity_cause":
            return "unsupported_object", "object_falls_until_support_or_boundary"
        if causal_family == "bridge_cause":
            return "connector_introduced", "components_become_connected"
        if causal_family == "path_cause":
            return "source_and_target_must_be_reachable", "route_created"
        if causal_family == "containment_cause":
            return "region_ownership_changed", "inside_outside_status_changed"
        if causal_family == "occlusion_cause":
            return "mask_or_foreground_removed", "visible_object_changed"
        if causal_family == "color_cause":
            return "identity_or_symbolic_mapping_changed", "object_color_changed"
        if causal_family == "growth_cause":
            return "boundary_or_repetition_rule_applied", "object_expands"
        evidence = transition.get("evidence", {}) or {}
        return (
            str(evidence.get("source", dependencies[0] if dependencies else "cause")),
            str(evidence.get("target", transition.get("transition", "effect"))),
        )

    def _preconditions_for(self, causal_family, process_model):
        initial = process_model.get("initial_state", {}).get("state_name")
        preconditions = [str(initial)] if initial else []
        if causal_family == "gravity_cause":
            preconditions.extend(["object_exists", "support_constraint_evaluated"])
        elif causal_family == "path_cause":
            preconditions.extend(["source_exists", "target_exists"])
        elif causal_family == "bridge_cause":
            preconditions.extend(["components_disconnected"])
        return list(dict.fromkeys(preconditions))

    def _triggers_for(self, causal_family, transition):
        triggers = [str(transition.get("transition", ""))]
        if causal_family == "gravity_cause":
            triggers.append("support_removed_or_absent")
        elif causal_family == "path_cause":
            triggers.append("reachability_required")
        elif causal_family == "bridge_cause":
            triggers.append("connector_cell_introduced")
        return [item for item in dict.fromkeys(triggers) if item]

    def _confidence(self, transition_confidence, process_confidence, dependency_confidence):
        values = [
            float(value or 0.0)
            for value in [
                transition_confidence,
                process_confidence,
                dependency_confidence,
            ]
        ]
        return round(min(sum(values) / max(len(values), 1) + 0.08, 1.0), 4)

    def _dedupe(self, contexts):
        seen = set()
        unique = []
        for context in contexts:
            key = (context.causal_family, context.cause, context.effect)
            if key in seen:
                continue
            seen.add(key)
            unique.append(context)
        return unique

    def _truth_sources(self, runtime_context):
        truths = []
        for key in ("truth_commitments", "reusable_truth_commitments", "truth_candidates"):
            value = runtime_context.get(key, [])
            if isinstance(value, Mapping):
                value = value.values()
            for item in value or []:
                if not isinstance(item, Mapping):
                    continue
                truth = item.get("truth_id") or item.get("concept") or item.get("truth_name")
                if truth:
                    truths.append(str(truth))
        return list(dict.fromkeys(truths))

    def _block_reasons(
        self,
        contexts,
        process_context_report,
        dependency_activation_report,
        input_grid,
        output_grid,
    ):
        if contexts:
            return []
        reasons = []
        if not (
            dependency_activation_report.get("dependency_reports")
            or dependency_activation_report.get("dependency_chains")
            or dependency_activation_report.get("causal_contexts")
            or dependency_activation_report.get("dependency_chains_executed", 0) > 0
        ):
            reasons.append("MISSING_DEPENDENCY_GRAPH")
        if not (
            process_context_report.get("process_contexts")
            or process_context_report.get("selected_process_context")
            or process_context_report.get("registered_contexts")
        ):
            reasons.append("MISSING_PROCESS_TRANSITIONS")
        if input_grid is None or output_grid is None:
            reasons.append("MISSING_EVENT_SEQUENCE")
        if input_grid is not None and output_grid is not None:
            try:
                if np.array(input_grid).shape == np.array(output_grid).shape and np.array_equal(
                    np.array(input_grid),
                    np.array(output_grid),
                ):
                    reasons.append("MISSING_STATE_CHANGE")
            except Exception:
                reasons.append("MISSING_STATE_CHANGE")
        if not reasons:
            reasons.append("NO_CAUSAL_PATTERN_FOUND")
        return list(dict.fromkeys(reasons))

    def _causal_graph(self, contexts):
        nodes = sorted({
            value
            for context in contexts
            for value in (context.cause, context.effect)
            if value
        })
        edges = [
            {
                "source": context.cause,
                "target": context.effect,
                "confidence": round(float(context.confidence), 4),
                "temporal_order": context.temporal_order,
            }
            for context in contexts
        ]
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def _event_transitions(self, contexts):
        return [
            {
                "from": context.cause,
                "to": context.effect,
                "temporal_order": context.temporal_order,
                "activation_reason": context.activation_reason or "causal_relation_generated",
            }
            for context in contexts
        ]

    def _movement_detected(self, source, target):
        for color in [int(item) for item in np.unique(source) if int(item) != 0]:
            if color not in np.unique(target):
                continue
            source_points = np.argwhere(source == color)
            target_points = np.argwhere(target == color)
            if len(source_points) and len(source_points) == len(target_points):
                if not np.array_equal(source_points, target_points):
                    return True
        return False

    def _palette(self, grid):
        return {
            int(color): int(np.sum(grid == color))
            for color in np.unique(grid)
            if int(color) != 0
        }

    def _array(self, grid):
        if grid is None:
            return np.array([])
        if hasattr(grid, "grid"):
            return np.array(grid.grid)
        return np.array(grid)


causal_inference_engine = CausalInferenceEngine()


__all__ = [
    "CausalContextModel",
    "CausalInferenceEngine",
    "causal_inference_engine",
]
