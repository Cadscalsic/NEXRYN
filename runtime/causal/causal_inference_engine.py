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

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["causal_confidence"] = round(float(self.confidence), 4)
        data["cause_effect_pair"] = {
            "cause": self.cause,
            "effect": self.effect,
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
        process_models = list(process_context_report.get("process_contexts", []) or [])
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
        contexts = self._dedupe(contexts)
        return {
            "system": self.system_name,
            "causal_contexts": [context.as_dict() for context in contexts],
            "causal_context_count": len(contexts),
            "causal_families_detected": sorted(
                {context.causal_family for context in contexts}
            ),
            "cause_effect_pairs": [
                {"cause": context.cause, "effect": context.effect}
                for context in contexts
            ],
            "timestamp": str(datetime.utcnow()),
        }

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
            ))
        return contexts

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
