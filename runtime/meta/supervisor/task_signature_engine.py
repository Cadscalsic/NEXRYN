"""Stable signatures for meta-cognitive reuse decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class TaskSignature:
    concepts: tuple[str, ...] = field(default_factory=tuple)
    contexts: tuple[str, ...] = field(default_factory=tuple)
    transformations: tuple[str, ...] = field(default_factory=tuple)
    constraints: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "concepts": list(self.concepts),
            "contexts": list(self.contexts),
            "transformations": list(self.transformations),
            "constraints": list(self.constraints),
        }

    def stable_id(self) -> str:
        encoded = json.dumps(self.as_dict(), sort_keys=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class TaskSignatureEngine:
    """Build canonical signatures that remain stable across similar tasks."""

    TRANSFORMATION_ALIASES = {
        "translate_object": "horizontal_translation",
        "object_translation": "horizontal_translation",
        "translation": "horizontal_translation",
        "move_object": "horizontal_translation",
        "replace_color": "object_color_mapping",
        "color_transformation": "object_color_mapping",
        "duplicate": "duplicate_object",
        "replication": "duplicate_object",
    }

    CONSTRAINT_KEYS = {
        "preserve_topology",
        "identity_preservation",
        "integrity_verified",
        "world_model_fit",
        "locked_truth_preserved",
    }

    def build_signature(
        self,
        runtime_context: Mapping[str, Any] | None,
    ) -> TaskSignature:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = set()
        contexts = set()
        transformations = set()
        constraints = set()

        self._collect_values(
            runtime_context,
            keys=("concept", "concept_name", "canonical_concept", "task_concept"),
            target=concepts,
        )
        self._collect_values(
            runtime_context,
            keys=("context_name", "canonical_context_name", "process_context"),
            target=contexts,
        )
        self._collect_values(
            runtime_context,
            keys=("transformation", "transformation_family", "primitive", "operator"),
            target=transformations,
        )

        for key, value in runtime_context.items():
            normalized_key = self._normalize_token(key)
            if normalized_key in self.CONSTRAINT_KEYS and bool(value):
                constraints.add(normalized_key)

        for report_key in (
            "process_context_discovery_report",
            "context_report",
            "transformation_report",
            "inference_report",
            "reasoning_report",
            "world_model_gate_report",
        ):
            report = runtime_context.get(report_key)
            if isinstance(report, Mapping):
                self._collect_values(
                    report,
                    keys=("concept", "concept_name", "canonical_concept"),
                    target=concepts,
                )
                self._collect_values(
                    report,
                    keys=("context_name", "canonical_context_name", "process_context"),
                    target=contexts,
                )
                self._collect_values(
                    report,
                    keys=("transformation", "transformation_family", "primitive", "operator"),
                    target=transformations,
                )

        if runtime_context.get("topology_preserved") is True:
            constraints.add("preserve_topology")

        if not concepts and runtime_context.get("task_path"):
            concepts.add(self._normalize_token(str(runtime_context["task_path"]).split("\\")[-1]))

        normalized_transformations = {
            self.TRANSFORMATION_ALIASES.get(item, item)
            for item in transformations
        }

        return TaskSignature(
            concepts=tuple(sorted(self._stable_items(concepts))),
            contexts=tuple(sorted(self._stable_items(contexts))),
            transformations=tuple(sorted(self._stable_items(normalized_transformations))),
            constraints=tuple(sorted(self._stable_items(constraints))),
        )

    def _collect_values(
        self,
        source: Any,
        keys: Iterable[str],
        target: set[str],
    ) -> None:
        if isinstance(source, Mapping):
            for key, value in source.items():
                if key in keys:
                    self._add_value(value, target)
                if isinstance(value, (Mapping, list, tuple)):
                    self._collect_values(value, keys, target)
        elif isinstance(source, (list, tuple)):
            for item in source:
                self._collect_values(item, keys, target)

    def _add_value(self, value: Any, target: set[str]) -> None:
        if isinstance(value, str):
            normalized = self._normalize_token(value)
            if normalized:
                target.add(normalized)
        elif isinstance(value, Mapping):
            for nested in value.values():
                self._add_value(nested, target)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                self._add_value(item, target)

    def _stable_items(self, values: Iterable[str]) -> list[str]:
        return [
            value
            for value in values
            if value and not value.startswith("unknown")
        ]

    def _normalize_token(self, value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value


task_signature_engine = TaskSignatureEngine()


__all__ = [
    "TaskSignature",
    "TaskSignatureEngine",
    "task_signature_engine",
]
