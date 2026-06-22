"""Object-centric change detection for localized ARC transformations."""

from __future__ import annotations

import math
from typing import Any, Mapping


class ChangeDetectionEngine:
    """Compute per-object deltas before global invariants are considered."""

    system_name = "change_detection_engine"

    def detect_changes(
        self,
        input_objects: list[Mapping[str, Any]] | None,
        output_objects: list[Mapping[str, Any]] | None,
    ) -> dict[str, Any]:
        input_objects = self._safe_objects(input_objects)
        output_objects = self._safe_objects(output_objects)
        total_differences = max(len(input_objects), len(output_objects), 1)
        reports = []

        for index, input_object in enumerate(input_objects):
            output_object = output_objects[index] if index < len(output_objects) else None
            reports.append(
                self._object_delta(
                    input_object=input_object,
                    output_object=output_object,
                    index=index,
                    total_differences=total_differences,
                )
            )

        for index in range(len(input_objects), len(output_objects)):
            reports.append(
                self._added_object_delta(
                    output_object=output_objects[index],
                    index=index,
                    total_differences=total_differences,
                )
            )

        changed_count = sum(1 for report in reports if report["changed"])
        return {
            "system": self.system_name,
            "OBJECT_CHANGE_REPORT": reports,
            "object_change_report": reports,
            "changed_object_count": changed_count,
            "unchanged_object_count": len(reports) - changed_count,
            "total_differences": total_differences,
        }

    def _object_delta(
        self,
        input_object: Mapping[str, Any],
        output_object: Mapping[str, Any] | None,
        index: int,
        total_differences: int,
    ) -> dict[str, Any]:
        object_id = str(
            input_object.get("object_id")
            or input_object.get("id")
            or f"object_{index + 1}"
        )
        if output_object is None:
            return self._report(
                object_id=object_id,
                changed=True,
                change_type="topology_change",
                change_magnitude=1.0,
                resolved_differences=1,
                total_differences=total_differences,
                object_delta={"removed": True},
            )

        translation = self._translation(input_object, output_object)
        color_changed = input_object.get("color") != output_object.get("color")
        size_changed = self._size(input_object) != self._size(output_object)
        shape_changed = self._shape_signature(input_object) != self._shape_signature(output_object)
        topology_changed = self._topology_signature(input_object) != self._topology_signature(output_object)

        change_types = []
        magnitudes = []
        if translation != (0, 0):
            change_types.append("translation")
            magnitudes.append(min(math.dist((0, 0), translation) / 10.0, 1.0))
        if color_changed:
            change_types.append("color_change")
            magnitudes.append(1.0)
        if size_changed:
            change_types.append("size_change")
            magnitudes.append(
                min(
                    abs(self._size(output_object) - self._size(input_object))
                    / max(self._size(input_object), self._size(output_object), 1),
                    1.0,
                )
            )
        if shape_changed:
            change_types.append("scaling" if size_changed else "reflection")
            magnitudes.append(0.75)
        if topology_changed:
            change_types.append("topology_change")
            magnitudes.append(0.85)

        changed = bool(change_types)
        change_type = self._dominant_change_type(change_types)
        magnitude = max(magnitudes) if magnitudes else 0.0
        return self._report(
            object_id=object_id,
            changed=changed,
            change_type=change_type,
            change_magnitude=magnitude,
            resolved_differences=1 if changed else 0,
            total_differences=total_differences,
            object_delta={
                "translation": translation,
                "rotation": "unknown",
                "reflection": shape_changed and not size_changed,
                "scaling": size_changed,
                "color_change": color_changed,
                "topology_change": topology_changed,
                "size_change": size_changed,
            },
        )

    def _added_object_delta(
        self,
        output_object: Mapping[str, Any],
        index: int,
        total_differences: int,
    ) -> dict[str, Any]:
        object_id = str(
            output_object.get("object_id")
            or output_object.get("id")
            or f"object_{index + 1}"
        )
        return self._report(
            object_id=object_id,
            changed=True,
            change_type="topology_change",
            change_magnitude=1.0,
            resolved_differences=1,
            total_differences=total_differences,
            object_delta={"added": True},
        )

    def _report(
        self,
        object_id: str,
        changed: bool,
        change_type: str,
        change_magnitude: float,
        resolved_differences: int,
        total_differences: int,
        object_delta: Mapping[str, Any],
    ) -> dict[str, Any]:
        explanatory_power = (
            resolved_differences / total_differences
            if total_differences
            else 0.0
        )
        return {
            "object_id": object_id,
            "changed": changed,
            "change_type": change_type,
            "change_magnitude": round(self._clamp(change_magnitude), 4),
            "explanatory_power": round(self._clamp(explanatory_power), 4),
            "resolved_differences": resolved_differences,
            "total_differences": total_differences,
            "object_delta": dict(object_delta),
        }

    def _dominant_change_type(self, change_types: list[str]) -> str:
        if not change_types:
            return "unchanged"
        priority = [
            "translation",
            "rotation",
            "reflection",
            "scaling",
            "color_change",
            "topology_change",
            "size_change",
        ]
        for change_type in priority:
            if change_type in change_types:
                return change_type
        return change_types[0]

    def _safe_objects(self, objects: Any) -> list[Mapping[str, Any]]:
        if not isinstance(objects, list):
            return []
        return [obj for obj in objects if isinstance(obj, Mapping)]

    def _position(self, obj: Mapping[str, Any]) -> tuple[float, float]:
        for key in ["centroid", "center", "position"]:
            value = obj.get(key)
            if isinstance(value, Mapping):
                row = value.get("row")
                col = value.get("col")
                if row is not None and col is not None:
                    return (float(row), float(col))
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                return (float(value[0]), float(value[1]))
        bbox = obj.get("bbox") or obj.get("bounding_box")
        if isinstance(bbox, Mapping):
            row = bbox.get("min_row")
            col = bbox.get("min_col")
            if row is not None and col is not None:
                return (float(row), float(col))
        return (0.0, 0.0)

    def _translation(
        self,
        input_object: Mapping[str, Any],
        output_object: Mapping[str, Any],
    ) -> tuple[int, int]:
        input_position = self._position(input_object)
        output_position = self._position(output_object)
        return (
            int(round(output_position[0] - input_position[0])),
            int(round(output_position[1] - input_position[1])),
        )

    def _size(self, obj: Mapping[str, Any]) -> int:
        value = obj.get("size", 1)
        return int(value) if isinstance(value, (int, float)) else 1

    def _shape_signature(self, obj: Mapping[str, Any]) -> Any:
        return (
            obj.get("canonical_shape_signature")
            or obj.get("shape_signature")
            or obj.get("normalized_shape")
        )

    def _topology_signature(self, obj: Mapping[str, Any]) -> tuple[Any, Any]:
        return (obj.get("holes"), obj.get("is_solid"))

    def _clamp(self, value: float) -> float:
        return max(0.0, min(float(value), 1.0))


change_detection_engine = ChangeDetectionEngine()


__all__ = [
    "ChangeDetectionEngine",
    "change_detection_engine",
]
