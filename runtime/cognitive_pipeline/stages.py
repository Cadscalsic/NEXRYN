"""Default cognitive stage declarations for solver execution."""

from __future__ import annotations

from typing import Any

import numpy as np

from .context import CognitiveContext
from .stage import CognitiveStage, CognitiveStageSpec


DEFAULT_COGNITIVE_STAGE_IDS = (
    "input_normalization",
    "scene_analysis",
    "object_extraction",
    "object_representation",
    "relationship_discovery",
    "spatial_analysis",
    "topological_analysis",
    "color_analysis",
    "pattern_analysis",
    "rule_discovery",
    "hypothesis_generation",
    "hypothesis_expansion",
    "transformation_discovery",
    "transformation_ranking",
    "program_synthesis",
    "program_ranking",
    "candidate_validation",
    "solution_selection",
    "final_verification",
    "output",
)


def _grid_data(grid: Any) -> Any:
    return getattr(grid, "grid", grid)


def _normalize(context: CognitiveContext) -> dict[str, Any]:
    context.input_grid = np.array(_grid_data(context.input_grid), copy=True)
    context.add_concept("normalized_input_grid")
    return {"normalized_shape": list(context.input_grid.shape)}


def _scene(context: CognitiveContext) -> dict[str, Any]:
    colors = sorted(int(value) for value in np.unique(context.input_grid))
    context.evidence.append({"type": "scene_colors", "colors": colors})
    context.add_concept("scene")
    return {"colors": colors}


def _objects(context: CognitiveContext) -> dict[str, Any]:
    objects = []
    for color in sorted(int(value) for value in np.unique(context.input_grid)):
        if color == 0:
            continue
        cells = np.argwhere(context.input_grid == color).tolist()
        objects.append({"id": f"color_{color}", "color": color, "cells": cells})
    context.perceived_objects.extend(objects)
    context.add_concept("objects")
    return {"object_count": len(objects)}


def _represent(context: CognitiveContext) -> dict[str, Any]:
    for obj in context.perceived_objects:
        cells = obj.get("cells", [])
        obj["size"] = len(cells)
    context.add_concept("object_representation")
    return {"represented_objects": len(context.perceived_objects)}


def _relationships(context: CognitiveContext) -> dict[str, Any]:
    colors = [obj.get("color") for obj in context.perceived_objects]
    relationships = [
        {"type": "co_present", "source": left, "target": right}
        for index, left in enumerate(colors)
        for right in colors[index + 1 :]
    ]
    context.relationships.extend(relationships)
    return {"relationship_count": len(relationships)}


def _analysis_concept(name: str):
    def handler(context: CognitiveContext) -> dict[str, Any]:
        context.add_concept(name)
        return {"concept": name}

    return handler


def _rules(context: CognitiveContext) -> dict[str, Any]:
    for rule in context.rules:
        context.knowledge_candidates.append({"type": "rule", "rule": dict(rule)})
    return {"rule_count": len(context.rules)}


def _hypotheses(context: CognitiveContext) -> dict[str, Any]:
    for rule in context.rules:
        hypothesis = {
            "type": rule.get("rule", "rule_application"),
            "confidence": 1.0,
            "source": "legacy_solver_rule",
        }
        context.hypotheses.append(hypothesis)
        context.confidence_scores[hypothesis["type"]] = 1.0
    return {"hypothesis_count": len(context.hypotheses)}


def _expand(context: CognitiveContext) -> dict[str, Any]:
    context.reasoning_history.append({
        "stage": "hypothesis_expansion",
        "expanded_hypotheses": len(context.hypotheses),
    })
    return {"expanded_hypotheses": len(context.hypotheses)}


def _transformations(context: CognitiveContext) -> dict[str, Any]:
    for rule in context.rules:
        if rule.get("rule") == "color_changes":
            context.transformations.append({
                "type": "color_change",
                "removed_colors": list(rule.get("removed_colors", [])),
                "added_colors": list(rule.get("added_colors", [])),
                "confidence": 1.0,
            })
    return {"transformation_count": len(context.transformations)}


def _rank_transformations(context: CognitiveContext) -> dict[str, Any]:
    context.transformations.sort(key=lambda item: item.get("confidence", 0), reverse=True)
    return {"ranked_transformations": len(context.transformations)}


def _synthesize(context: CognitiveContext) -> dict[str, Any]:
    predicted = np.array(context.input_grid, copy=True)
    steps = []
    for rule in context.rules:
        if rule.get("rule") != "color_changes":
            continue
        removed = list(rule.get("removed_colors", []))
        added = list(rule.get("added_colors", []))
        if not removed or not added:
            continue
        old_color = removed[0]
        new_color = added[0]
        predicted[predicted == old_color] = new_color
        steps.append({
            "operation": "replace_color",
            "old_color": old_color,
            "new_color": new_color,
        })
    program = {"step_count": len(steps), "steps": steps, "confidence": 1.0}
    context.solution = predicted
    context.candidate_programs.append(program)
    return {"program_step_count": len(steps)}


def _rank_programs(context: CognitiveContext) -> dict[str, Any]:
    context.candidate_programs.sort(
        key=lambda item: item.get("confidence", 0),
        reverse=True,
    )
    return {"program_count": len(context.candidate_programs)}


def _validate(context: CognitiveContext) -> dict[str, Any]:
    validation = {"status": "not_applicable", "success": None}
    if context.output_grid is not None and context.solution is not None:
        expected = np.asarray(_grid_data(context.output_grid))
        validation = {
            "status": "completed",
            "success": bool(np.array_equal(context.solution, expected)),
        }
    context.validation_results.append(validation)
    return validation


def _select(context: CognitiveContext) -> dict[str, Any]:
    context.final_output = context.solution
    return {"solution_selected": context.final_output is not None}


def _verify(context: CognitiveContext) -> dict[str, Any]:
    verified = context.final_output is not None
    context.confidence_scores["final_verification"] = 1.0 if verified else 0.0
    return {"verified": verified}


def _output(context: CognitiveContext) -> dict[str, Any]:
    return {"output_ready": context.final_output is not None}


def build_default_stages() -> list[CognitiveStage]:
    definitions: list[tuple[str, str, Any, tuple[str, ...], tuple[str, ...]]] = [
        ("input_normalization", "Input Normalization", _normalize, ("input_grid",), ("input_grid",)),
        ("scene_analysis", "Scene Analysis", _scene, ("input_grid",), ("evidence",)),
        ("object_extraction", "Object Extraction", _objects, ("input_grid",), ("perceived_objects",)),
        ("object_representation", "Object Representation", _represent, ("perceived_objects",), ("perceived_objects",)),
        ("relationship_discovery", "Relationship Discovery", _relationships, ("perceived_objects",), ("relationships",)),
        ("spatial_analysis", "Spatial Analysis", _analysis_concept("spatial_analysis"), ("perceived_objects",), ("concept_graph",)),
        ("topological_analysis", "Topological Analysis", _analysis_concept("topological_analysis"), ("perceived_objects",), ("concept_graph",)),
        ("color_analysis", "Color Analysis", _analysis_concept("color_analysis"), ("input_grid",), ("concept_graph",)),
        ("pattern_analysis", "Pattern Analysis", _analysis_concept("pattern_analysis"), ("input_grid",), ("concept_graph",)),
        ("rule_discovery", "Rule Discovery", _rules, ("rules",), ("knowledge_candidates",)),
        ("hypothesis_generation", "Hypothesis Generation", _hypotheses, ("rules",), ("hypotheses",)),
        ("hypothesis_expansion", "Hypothesis Expansion", _expand, ("hypotheses",), ("reasoning_history",)),
        ("transformation_discovery", "Transformation Discovery", _transformations, ("rules",), ("transformations",)),
        ("transformation_ranking", "Transformation Ranking", _rank_transformations, ("transformations",), ("transformations",)),
        ("program_synthesis", "Program Synthesis", _synthesize, ("input_grid", "rules"), ("candidate_programs", "solution")),
        ("program_ranking", "Program Ranking", _rank_programs, ("candidate_programs",), ("candidate_programs",)),
        ("candidate_validation", "Candidate Validation", _validate, ("candidate_programs",), ("validation_results",)),
        ("solution_selection", "Solution Selection", _select, ("candidate_programs",), ("final_output",)),
        ("final_verification", "Final Verification", _verify, ("final_output",), ("confidence_scores",)),
        ("output", "Output", _output, ("final_output",), ("final_output",)),
    ]
    stages = []
    previous: tuple[str, ...] = ()
    for stage_id, name, handler, required, outputs in definitions:
        stages.append(CognitiveStage(
            spec=CognitiveStageSpec(
                stage_id=stage_id,
                stage_name=name,
                required_inputs=required,
                generated_outputs=outputs,
                consumed_outputs=required,
                dependent_stages=previous,
            ),
            handler=handler,
            dependencies=previous,
        ))
        previous = (stage_id,)
    return stages


__all__ = ["DEFAULT_COGNITIVE_STAGE_IDS", "build_default_stages"]
