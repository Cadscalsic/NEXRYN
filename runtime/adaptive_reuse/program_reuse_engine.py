"""Compose executable program fragments from previous experience."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.adaptive_reuse.program_memory import ProgramFragmentMemory


PRIMITIVE_OPERATIONS = {
    "rotate",
    "mirror",
    "grow_until_contact",
    "fill_holes",
    "recolor",
    "connect_components",
    "find_objects",
    "path_search",
    "replace_color",
    "expand_pattern",
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
        return {
            "program_reuse_attempted": True,
            "program_reuse_success": bool(composed.get("program_steps")),
            "program_hits": len(selected),
            "program_misses": 0 if selected else 1,
            "reused_programs": selected,
            "composed_program": composed,
        }

    def _program_from_strategy(self, strategy: Mapping[str, Any]) -> dict[str, Any]:
        operation = (
            strategy.get("operation")
            or strategy.get("primitive")
            or strategy.get("type")
            or strategy.get("adapted_strategy_type")
        )
        if not operation:
            return {}
        operation = str(operation)
        return {
            "program_id": f"strategy_program:{operation}",
            "program": {"program_steps": [{"operation": operation, "parameters": {}}]},
            "operation_sequence": [{"operation": operation}],
            "confidence": float(strategy.get("confidence", 0.7) or 0.7),
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
                operation = step.get("operation") or step.get("operator")
                if not operation:
                    continue
                normalized = str(operation)
                if normalized not in PRIMITIVE_OPERATIONS and not normalized:
                    continue
                key = (normalized, str(step.get("parameters", {})))
                if key in seen:
                    continue
                seen.add(key)
                steps.append({
                    "operation": normalized,
                    "parameters": dict(step.get("parameters", {}))
                    if isinstance(step.get("parameters"), Mapping)
                    else {},
                })
        return {
            "program_steps": steps,
            "step_count": len(steps),
            "composition_state": "COMPOSED_FROM_EXPERIENCE" if steps else "NO_PROGRAM_REUSE",
        }


def _tokens(value: Any) -> set[str]:
    text = str(value).lower().replace("_", " ")
    return {token for token in text.split() if len(token) > 2}


def _overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
