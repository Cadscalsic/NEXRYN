"""Compose executable program fragments from previous experience."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.adaptive_reuse.program_memory import ProgramFragmentMemory


PRIMITIVE_OPERATIONS = {
    "construct_path",
    "connect_components",
    "duplicate_object",
    "preserve_colors",
    "preserve_density",
    "preserve_grid",
    "preserve_shape",
    "preserve_size",
    "preserve_symmetry",
    "preserve_topology",
    "rotate",
    "translate",
    "mirror",
    "mirror_horizontal",
    "mirror_object",
    "mirror_vertical",
    "grow_until_contact",
    "fill_holes",
    "recolor",
    "find_objects",
    "path_search",
    "replace_color",
    "expand_pattern",
}

PARAMETER_REQUIRED_OPERATIONS = {
    "replace_color",
}


CONCEPT_OPERATION_ALIASES = {
    "bridge_creation": "connect_components",
    "color_preservation": "preserve_colors",
    "color_replacement": "replace_color",
    "density_preservation": "preserve_density",
    "directional_motion": "translate",
    "growth": "duplicate_object",
    "identity_continuity": "preserve_grid",
    "object_connection": "connect_components",
    "object_identity_preservation": "preserve_grid",
    "object_size": "preserve_size",
    "position_preservation": "preserve_grid",
    "replication": "duplicate_object",
    "shape_preservation": "preserve_shape",
    "size_preservation": "preserve_size",
    "symbolic_remapping": "replace_color",
    "symbolic_surface_remapping": "replace_color",
    "symmetry_preservation": "preserve_symmetry",
    "symmetry_reasoning": "preserve_symmetry",
    "topological_growth": "duplicate_object",
    "topology_preservation": "preserve_topology",
}


class ProgramReuseEngine:
    def __init__(self, memory: ProgramFragmentMemory | None = None) -> None:
        self.memory = memory or ProgramFragmentMemory()

    def retrieve(
        self,
        runtime_context: Mapping[str, Any] | None,
        strategies: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        context_tokens = _tokens(runtime_context or {})
        fragments = self.memory.load()
        ranked = []
        for fragment in fragments:
            score = _overlap(context_tokens, _tokens(fragment))
            if score > 0.0 or fragment.get("confidence", 0.0) >= 0.85:
                ranked.append((round(score + fragment.get("confidence", 0.0) * 0.25, 4), fragment))
        ranked.sort(key=lambda item: (item[0], item[1].get("program_id", "")), reverse=True)
        selected = [fragment for _, fragment in ranked[:8]]
        if not selected and strategies:
            selected = [self._program_from_strategy(strategy) for strategy in strategies]
            selected = [item for item in selected if item]
        composed = self._compose(selected)
        if not composed.get("program_steps") and strategies:
            strategy_programs = [
                item
                for item in (
                    self._program_from_strategy(strategy)
                    for strategy in strategies
                )
                if item
            ]
            if strategy_programs:
                selected = strategy_programs
                composed = self._compose(selected)
        if not composed.get("program_steps"):
            selected = []
        return {
            "program_reuse_attempted": True,
            "program_reuse_success": bool(composed.get("program_steps")),
            "program_hits": len(selected),
            "program_misses": 0 if selected else 1,
            "reused_programs": selected,
            "composed_program": composed,
        }

    def _program_from_strategy(self, strategy: Mapping[str, Any]) -> dict[str, Any]:
        executable_payload = (
            strategy.get("executable_payload")
            if isinstance(strategy.get("executable_payload"), Mapping)
            else {}
        )
        strategy_operation = _canonical_operation(
            strategy.get("operation")
            or strategy.get("primitive")
            or strategy.get("operator")
            or strategy.get("type")
            or strategy.get("adapted_strategy_type")
            or strategy.get("concept")
        )
        payload_operation = _canonical_operation(executable_payload.get("operation"))
        if payload_operation and strategy_operation and payload_operation != strategy_operation:
            executable_payload = {}
        payload_steps = executable_payload.get("steps")
        if isinstance(payload_steps, list) and payload_steps:
            steps = [
                {
                    "operation": _canonical_operation(
                        step.get("operation")
                        or strategy.get("operation")
                        or strategy.get("type")
                    ),
                    "parameters": dict(step.get("parameters"))
                    if isinstance(step.get("parameters"), Mapping)
                    else {},
                    "parameter_provenance": dict(step.get("parameter_provenance"))
                    if isinstance(step.get("parameter_provenance"), Mapping)
                    else {},
                }
                for step in payload_steps
                if isinstance(step, Mapping)
            ]
            steps = [
                step
                for step in steps
                if step["operation"] in PRIMITIVE_OPERATIONS
                and (
                    step["operation"] not in PARAMETER_REQUIRED_OPERATIONS
                    or step["parameters"]
                )
            ]
            if steps:
                return {
                    "program_id": (
                        executable_payload.get("executable_payload_fingerprint")
                        or f"strategy_program:{steps[0]['operation']}"
                    ),
                    "program": {"program_steps": steps},
                    "operation_sequence": [
                        {"operation": step["operation"]} for step in steps
                    ],
                    "confidence": float(strategy.get("confidence", 0.7) or 0.7),
                    "parameter_provenance": {
                        index: step.get("parameter_provenance", {})
                        for index, step in enumerate(steps)
                    },
                    "execution_authority": "NONE",
                }
        operation = strategy_operation
        if not operation:
            return {}
        if operation not in PRIMITIVE_OPERATIONS:
            return {}
        parameters = (
            dict(strategy.get("parameters"))
            if isinstance(strategy.get("parameters"), Mapping)
            else {}
        )
        if operation in PARAMETER_REQUIRED_OPERATIONS and not parameters:
            return {}
        return {
            "program_id": f"strategy_program:{operation}",
            "program": {
                "program_steps": [
                    {
                        "operation": operation,
                        "parameters": parameters,
                        "parameter_provenance": dict(
                            strategy.get("parameter_provenance")
                        )
                        if isinstance(strategy.get("parameter_provenance"), Mapping)
                        else {},
                    }
                ]
            },
            "operation_sequence": [{"operation": operation}],
            "confidence": float(strategy.get("confidence", 0.7) or 0.7),
            "execution_authority": "NONE",
        }

    def _compose(self, fragments: list[Mapping[str, Any]]) -> dict[str, Any]:
        steps = []
        seen = set()
        for fragment in fragments:
            program = fragment.get("program", {})
            program = program if isinstance(program, Mapping) else {}
            candidates = (
                program.get("program_steps")
                or program.get("steps")
                or fragment.get("operation_sequence")
                or []
            )
            for step in candidates:
                if not isinstance(step, Mapping):
                    continue
                operation = (
                    step.get("operation")
                    or step.get("primitive")
                    or step.get("operator")
                )
                if not operation:
                    continue
                normalized = _canonical_operation(operation)
                if not normalized or normalized not in PRIMITIVE_OPERATIONS:
                    continue
                key = (normalized, str(step.get("parameters", {})))
                if key in seen:
                    continue
                seen.add(key)
                composed_step = {
                    "operation": normalized,
                    "parameters": dict(step.get("parameters", {}))
                    if isinstance(step.get("parameters"), Mapping)
                    else {},
                }
                parameter_provenance = (
                    dict(step.get("parameter_provenance", {}))
                    if isinstance(step.get("parameter_provenance"), Mapping)
                    else {}
                )
                if parameter_provenance:
                    composed_step["parameter_provenance"] = parameter_provenance
                steps.append(composed_step)
        return {
            "program_steps": steps,
            "step_count": len(steps),
            "composition_state": "COMPOSED_FROM_EXPERIENCE" if steps else "NO_PROGRAM_REUSE",
        }


def _tokens(value: Any) -> set[str]:
    text = str(value).lower().replace("_", " ")
    return {token for token in text.split() if len(token) > 2}


def _canonical_operation(value: Any) -> str:
    token = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "global_recolor": "replace_color",
        "mirror": "mirror_horizontal",
        "objectconnection": "connect_components",
        "partialcolorreplacement": "replace_color",
        "partial_color_replacement": "replace_color",
        "preserve_color": "preserve_colors",
        "preserve_color_mapping": "preserve_colors",
        "preserve_input": "preserve_grid",
        "remap_colors": "replace_color",
        "replicate": "duplicate_object",
        "rotate90": "rotate",
        "rotate_90": "rotate",
        "translate_object": "translate",
    }
    return aliases.get(token, CONCEPT_OPERATION_ALIASES.get(token, token))


def _overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
