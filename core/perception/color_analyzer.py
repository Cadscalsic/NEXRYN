"""Color behavior analysis for ARC-style grids and tracked objects."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from core.epistemic_models import clamp
from core.perception.object_extractor import ObjectExtractor
from core.perception.object_tracker import ObjectTracker


class ColorAnalyzer:
    """Extract palette, recoloring, and color mapping evidence."""

    def __init__(
        self,
        object_extractor: ObjectExtractor | None = None,
        object_tracker: ObjectTracker | None = None,
        background_color: int = 0,
    ) -> None:
        self.object_extractor = object_extractor or ObjectExtractor(
            background_color=background_color,
        )
        self.object_tracker = object_tracker or ObjectTracker(self.object_extractor)
        self.background_color = int(background_color)

    def analyze_grid(
        self,
        grid: Any,
        source: str = "color_preservation",
    ) -> dict[str, Any]:
        normalized = self.object_extractor.normalize_grid(grid)
        palette = self._palette(normalized)
        objects = self.object_extractor.extract_objects(normalized)
        report = {
            "system": "color_analyzer",
            "mode": "grid",
            "source": source,
            "palette": palette,
            "foreground_colors": sorted(
                color
                for color in palette
                if color != self.background_color
            ),
            "object_color_counts": dict(sorted(Counter(
                int(obj.get("color", self.background_color))
                for obj in objects
            ).items())),
            "object_count": len(objects),
        }
        report["dependency_evidence"] = self._grid_dependency_evidence(report)
        return report

    def compare_grids(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str = "color_preservation",
    ) -> dict[str, Any]:
        tracking = self.object_tracker.track(input_grid, output_grid)
        input_objects = {
            obj["id"]: obj
            for obj in self.object_extractor.extract_objects(input_grid)
        }
        output_objects = {
            obj["id"]: obj
            for obj in self.object_extractor.extract_objects(output_grid)
        }
        input_palette = self._palette(
            self.object_extractor.normalize_grid(input_grid),
        )
        output_palette = self._palette(
            self.object_extractor.normalize_grid(output_grid),
        )
        mappings = self._color_mappings(
            tracking,
            input_objects=input_objects,
            output_objects=output_objects,
        )
        behavior = self._color_behavior(
            input_palette=input_palette,
            output_palette=output_palette,
            mappings=mappings,
            tracking=tracking,
        )
        report = {
            "system": "color_analyzer",
            "mode": "comparison",
            "source": source,
            "color_behavior": behavior,
            "input_palette": input_palette,
            "output_palette": output_palette,
            "colors_added": sorted(set(output_palette) - set(input_palette)),
            "colors_removed": sorted(set(input_palette) - set(output_palette)),
            "color_mappings": mappings,
            "recolor_events": [
                mapping
                for mapping in mappings
                if mapping["input_color"] != mapping["output_color"]
            ],
            "tracking": tracking,
        }
        report["mapping_confidence"] = self._mapping_confidence(report)
        report["dependency_evidence"] = self._comparison_dependency_evidence(report)
        return report

    def _palette(self, grid: list[list[int]]) -> dict[int, int]:
        counts: Counter[int] = Counter()
        for row in grid or []:
            for value in row:
                counts[int(value)] += 1
        return dict(sorted(counts.items()))

    def _color_mappings(
        self,
        tracking: Mapping[str, Any],
        input_objects: Mapping[str, Mapping[str, Any]],
        output_objects: Mapping[str, Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        mappings = []
        for match in tracking.get("matches", []):
            input_object = input_objects.get(str(match.get("input_object")))
            output_object = output_objects.get(str(match.get("output_object")))
            input_color = (
                int(input_object["color"])
                if input_object is not None
                else None
            )
            output_color = (
                int(output_object["color"])
                if output_object is not None
                else None
            )
            if input_color is None or output_color is None:
                continue
            mappings.append({
                "input_object": match.get("input_object"),
                "output_object": match.get("output_object"),
                "input_color": input_color,
                "output_color": output_color,
                "mapping": f"{input_color}->{output_color}",
                "preserved": input_color == output_color,
                "confidence": clamp(match.get("match_confidence", 0.0)),
            })
        for event in tracking.get("added_objects", []):
            mappings.append({
                "input_object": event.get("source_candidate"),
                "output_object": event.get("output_object"),
                "input_color": None,
                "output_color": event.get("color"),
                "mapping": f"new->{event.get('color')}",
                "preserved": False,
                "confidence": clamp(event.get("confidence", 0.0)),
            })
        return mappings

    def _color_behavior(
        self,
        input_palette: Mapping[int, int],
        output_palette: Mapping[int, int],
        mappings: list[Mapping[str, Any]],
        tracking: Mapping[str, Any],
    ) -> str:
        if any(not mapping.get("preserved") for mapping in mappings):
            return "color_reassigned"
        if input_palette == output_palette:
            return "color_preserved"
        if tracking.get("added_objects") or tracking.get("removed_objects"):
            return "color_distribution_changed"
        return "color_changed"

    def _mapping_confidence(self, report: Mapping[str, Any]) -> float:
        mappings = list(report.get("color_mappings", []))
        if not mappings:
            return 1.0 if report.get("input_palette") == report.get("output_palette") else 0.0
        return clamp(
            sum(mapping.get("confidence", 0.0) for mapping in mappings)
            / len(mappings)
        )

    def _grid_dependency_evidence(
        self,
        report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        source = str(report.get("source", "color_preservation"))
        return [
            self._dependency(
                source,
                f"foreground_color_count:{len(report.get('foreground_colors', []))}",
                0.86,
                "contextual_dependency",
                {"foreground_colors": report.get("foreground_colors", [])},
            )
        ]

    def _comparison_dependency_evidence(
        self,
        report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        source = str(report.get("source", "color_preservation"))
        behavior = report.get("color_behavior", "color_changed")
        confidence = report.get("mapping_confidence", 0.0)
        dependencies = [
            self._dependency(
                source,
                f"color_behavior:{behavior}",
                max(confidence, 0.82),
                "contextual_dependency",
                {"color_behavior": behavior},
            ),
            self._dependency(
                source,
                "color_mapping_rule",
                max(confidence, 0.80),
                "contextual_dependency",
                {"color_mappings": report.get("color_mappings", [])},
            ),
            self._dependency(
                source,
                "recolor_condition",
                max(confidence, 0.78),
                "contextual_dependency",
                {
                    "colors_added": report.get("colors_added", []),
                    "colors_removed": report.get("colors_removed", []),
                    "recolor_events": report.get("recolor_events", []),
                },
            ),
        ]
        for event in report.get("recolor_events", []):
            dependencies.append(
                self._dependency(
                    source,
                    f"color_mapping:{event['mapping']}",
                    event.get("confidence", confidence),
                    "contextual_dependency",
                    {"recolor_event": event},
                )
            )
        return dependencies

    def _dependency(
        self,
        source: str,
        target: str,
        confidence: float,
        dependency_type: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "source": source,
            "target": target,
            "relation": "depends_on",
            "confidence": clamp(confidence),
            "dependency_type": dependency_type,
            "required": True,
            "supported": True,
            "transfer_success": True,
            "metadata": metadata,
        }


__all__ = [
    "ColorAnalyzer",
]
