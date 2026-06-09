"""Object lineage tracking across ARC-style grid states."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from core.epistemic_models import clamp
from core.perception.object_extractor import ObjectExtractor
from core.perception.spatial_relations import SpatialRelationEngine


class IdentityTransitionKind(str, Enum):
    """Canonical identity transitions emitted by the object tracker."""

    PRESERVED = "IdentityPreserved"
    SPLIT = "IdentitySplit"
    MERGED = "IdentityMerged"
    CREATED = "IdentityCreated"
    DESTROYED = "IdentityDestroyed"


@dataclass
class TrackedObject:
    """Object-level perception record used by identity tracking."""

    object_id: str
    color: int
    size: int
    shape_signature: str
    centroid: tuple[float, float]
    bbox: dict[str, int] = field(default_factory=dict)
    canonical_shape_signature: str = ""

    @classmethod
    def from_extracted(cls, obj: Mapping[str, Any]) -> "TrackedObject":
        center = obj.get("center", {})
        return cls(
            object_id=str(obj.get("id")),
            color=int(obj.get("color", 0)),
            size=int(obj.get("size", 0)),
            shape_signature=str(obj.get("shape_signature", "")),
            centroid=(
                float(center.get("row", 0.0)),
                float(center.get("col", 0.0)),
            ),
            bbox=dict(obj.get("bbox", {})),
            canonical_shape_signature=str(
                obj.get(
                    "canonical_shape_signature",
                    obj.get("shape_signature", ""),
                )
            ),
        )

    def export(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "color": self.color,
            "size": self.size,
            "shape_signature": self.shape_signature,
            "canonical_shape_signature": self.canonical_shape_signature,
            "centroid": self.centroid,
            "bbox": dict(self.bbox),
        }


@dataclass
class ObjectIdentity:
    """Object identity continuity across one transformation step."""

    source_id: str
    transition: str
    continuity_score: float
    transition_kind: IdentityTransitionKind = IdentityTransitionKind.PRESERVED
    target_id: str | None = None
    targets: list[str] = field(default_factory=list)
    confidence: float | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def export(self) -> dict[str, Any]:
        score = clamp(self.continuity_score)
        report = {
            "source_id": self.source_id,
            "continuity_score": score,
            "confidence": clamp(self.confidence if self.confidence is not None else score),
            "transition": self.transition,
            "transition_kind": self.transition_kind.value,
            "identity_transition": self.transition_kind.value,
            "evidence": dict(self.evidence),
        }
        if self.target_id is not None:
            report["target_id"] = self.target_id
        if self.targets:
            report["targets"] = list(self.targets)
        return report


@dataclass
class IdentityTransition:
    """Transition from one tracked object identity to one or more targets."""

    source: str
    transition_type: str
    confidence: float
    transition_kind: IdentityTransitionKind = IdentityTransitionKind.PRESERVED
    target: str | None = None
    targets: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def export(self) -> dict[str, Any]:
        report = {
            "source": self.source,
            "confidence": clamp(self.confidence),
            "transition_type": self.transition_type,
            "transition_kind": self.transition_kind.value,
            "identity_transition": self.transition_kind.value,
            "evidence": dict(self.evidence),
        }
        if self.target is not None:
            report["target"] = self.target
        if self.targets:
            report["targets"] = list(self.targets)
        return report


@dataclass
class IdentityTrack:
    """Runtime lineage for one perceived object identity."""

    track_id: str
    anchor_signature: str
    observations: list[dict[str, Any]] = field(default_factory=list)

    def add_observation(
        self,
        object_id: str,
        phase: str,
        signature: str,
        continuity: float,
        identity_state: str,
    ) -> None:
        self.observations.append({
            "object_id": object_id,
            "phase": phase,
            "identity_signature": signature,
            "continuity": clamp(continuity),
            "identity_state": identity_state,
        })

    @property
    def continuity(self) -> float:
        if not self.observations:
            return 0.0
        return clamp(
            sum(item["continuity"] for item in self.observations)
            / len(self.observations)
        )

    @property
    def stable(self) -> bool:
        if not self.observations:
            return False
        return self.continuity >= 0.80 and all(
            item["identity_state"] != "identity_unresolved"
            for item in self.observations
        )

    def export(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "anchor_signature": self.anchor_signature,
            "observation_count": len(self.observations),
            "continuity": self.continuity,
            "stable": self.stable,
            "observations": list(self.observations),
        }


class ObjectTracker:
    """Track object identity, placement, and lineage between two grids."""

    def __init__(
        self,
        object_extractor: ObjectExtractor | None = None,
        spatial_relation_engine: SpatialRelationEngine | None = None,
        match_threshold: float = 0.58,
    ) -> None:
        self.object_extractor = object_extractor or ObjectExtractor()
        self.spatial_relation_engine = (
            spatial_relation_engine or SpatialRelationEngine()
        )
        self.match_threshold = float(match_threshold)
        self._track_counter = 0
        self._track_index: dict[str, str] = {}

    def track(
        self,
        input_grid: Any,
        output_grid: Any,
    ) -> dict[str, Any]:
        input_objects = self.object_extractor.extract_objects(input_grid)
        output_objects = self.object_extractor.extract_objects(output_grid)
        matches = self._match_objects(input_objects, output_objects)
        matched_input_ids = {match["input_object"] for match in matches}
        matched_output_ids = {match["output_object"] for match in matches}

        added_objects = [
            obj for obj in output_objects if obj["id"] not in matched_output_ids
        ]
        removed_objects = [
            obj for obj in input_objects if obj["id"] not in matched_input_ids
        ]
        added_events = [
            self._added_event(obj, input_objects)
            for obj in added_objects
        ]
        moved_events = [
            match for match in matches if not match["position_preserved"]
        ]
        changed_events = [
            match for match in matches if match["identity_state"] != "identity_stable"
        ]
        removed_events = [
            self._removed_event(obj, output_objects)
            for obj in removed_objects
        ]
        lineage_events = [
            *[
                {
                    "event": "object_persisted",
                    **match,
                }
                for match in matches
            ],
            *added_events,
            *removed_events,
        ]
        identity_runtime = self._identity_runtime_report(
            input_objects,
            output_objects,
            matches,
            added_events,
            removed_events,
        )
        identity_transitions = self._identity_transitions(
            matches,
            added_events,
            removed_events,
        )
        object_identities = self._object_identities(
            matches,
            added_events,
            removed_events,
        )

        return {
            "system": "object_tracker",
            "input_object_count": len(input_objects),
            "output_object_count": len(output_objects),
            "input_tracked_objects": self._tracked_objects(input_objects),
            "output_tracked_objects": self._tracked_objects(output_objects),
            "object_identities": object_identities,
            "identity_transitions": identity_transitions,
            "matches": matches,
            "added_objects": added_events,
            "removed_objects": removed_events,
            "moved_objects": moved_events,
            "changed_objects": changed_events,
            "lineage_events": lineage_events,
            "localized_change_count": len(added_events)
            + len(removed_events)
            + len(moved_events),
            "identity_continuity": self._identity_continuity(matches),
            "identity_continuity_state": self._identity_continuity_state(matches),
            "identity_changes": changed_events,
            "identity_runtime": identity_runtime,
            "identity_runtime_state": identity_runtime["identity_runtime_state"],
            "identity_runtime_confidence": identity_runtime[
                "identity_runtime_confidence"
            ],
            "identity_runtime_gates": identity_runtime["continuity_gates"],
            "tracking_confidence": self._tracking_confidence(
                matches,
                added_events,
                input_objects,
                output_objects,
            ),
        }

    def _match_objects(
        self,
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        candidates = []
        for input_obj in input_objects:
            for output_obj in output_objects:
                structural_score = self.spatial_relation_engine.object_match_score(
                    input_obj,
                    output_obj,
                )
                identity_score = self._identity_match_score(input_obj, output_obj)
                score = max(structural_score, identity_score)
                if score >= self.match_threshold:
                    candidates.append((score, identity_score, input_obj, output_obj))

        candidates.sort(key=lambda item: item[0], reverse=True)
        used_inputs: set[str] = set()
        used_outputs: set[str] = set()
        matches = []
        for score, identity_score, input_obj, output_obj in candidates:
            if input_obj["id"] in used_inputs or output_obj["id"] in used_outputs:
                continue
            used_inputs.add(input_obj["id"])
            used_outputs.add(output_obj["id"])
            vector = self.spatial_relation_engine.placement_vector(
                input_obj,
                output_obj,
            )
            matches.append({
                "input_object": input_obj["id"],
                "output_object": output_obj["id"],
                "track_id": self._track_id_for(input_obj, output_obj),
                "match_confidence": clamp(score),
                "identity_continuity": clamp(identity_score),
                "semantic_spine_stability": self._semantic_spine_stability(
                    input_obj,
                    output_obj,
                ),
                "identity_signature": self._identity_signature(output_obj),
                "identity_state": self._identity_state(input_obj, output_obj),
                "shape_preserved": input_obj.get("canonical_shape_signature")
                == output_obj.get("canonical_shape_signature"),
                "color_preserved": input_obj.get("color") == output_obj.get("color"),
                "size_preserved": input_obj.get("size") == output_obj.get("size"),
                "color_changed": input_obj.get("color") != output_obj.get("color"),
                "size_changed": input_obj.get("size") != output_obj.get("size"),
                "shape_changed": input_obj.get("canonical_shape_signature")
                != output_obj.get("canonical_shape_signature"),
                "position_preserved": vector["delta_row"] == 0
                and vector["delta_col"] == 0,
                "placement_vector": vector,
            })
        return matches

    def _identity_runtime_report(
        self,
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
        matches: list[Mapping[str, Any]],
        added_events: list[Mapping[str, Any]],
        removed_events: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        tracks: dict[str, IdentityTrack] = {}
        output_by_id = {obj["id"]: obj for obj in output_objects}
        input_by_id = {obj["id"]: obj for obj in input_objects}

        for match in matches:
            input_obj = input_by_id.get(match.get("input_object"))
            output_obj = output_by_id.get(match.get("output_object"))
            track_id = str(match.get("track_id"))
            track = tracks.setdefault(
                track_id,
                IdentityTrack(
                    track_id=track_id,
                    anchor_signature=str(
                        self._identity_signature(input_obj)
                        if input_obj
                        else match.get("identity_signature", "")
                    ),
                ),
            )
            if input_obj:
                track.add_observation(
                    object_id=str(input_obj.get("id")),
                    phase="input",
                    signature=self._identity_signature(input_obj),
                    continuity=1.0,
                    identity_state="identity_anchor",
                )
            if output_obj:
                track.add_observation(
                    object_id=str(output_obj.get("id")),
                    phase="output",
                    signature=self._identity_signature(output_obj),
                    continuity=float(match.get("identity_continuity", 0.0)),
                    identity_state=str(match.get("identity_state")),
                )

        continuity = self._identity_continuity(matches)
        spine_stability = self._semantic_spine_continuity(matches)
        gates = {
            "identity_stable": bool(matches)
            and not added_events
            and not removed_events
            and continuity >= 0.80,
            "semantic_spine_stable": spine_stability >= 0.80,
            "identity_continuity_above_limit": continuity >= 0.72,
            "epistemic_drift_containment_inactive": (
                continuity >= 0.72
                and spine_stability >= 0.80
                and not added_events
                and not removed_events
            ),
        }
        gate_ratio = sum(1 for value in gates.values() if value) / max(len(gates), 1)
        runtime_confidence = clamp(
            continuity * 0.50
            + spine_stability * 0.30
            + gate_ratio * 0.20
        )
        return {
            "system": "identity_runtime",
            "active_track_count": len(tracks),
            "tracked_input_count": len({match["input_object"] for match in matches}),
            "tracked_output_count": len({match["output_object"] for match in matches}),
            "untracked_input_count": len(removed_events),
            "untracked_output_count": len(added_events),
            "identity_spine_continuity": spine_stability,
            "continuity_gates": gates,
            "identity_runtime_state": self._identity_runtime_state(
                runtime_confidence,
                gates,
            ),
            "identity_runtime_confidence": runtime_confidence,
            "tracks": [
                tracks[track_id].export()
                for track_id in sorted(tracks)
            ],
        }

    def _tracked_objects(
        self,
        objects: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            TrackedObject.from_extracted(obj).export()
            for obj in objects
        ]

    def _object_identities(
        self,
        matches: list[Mapping[str, Any]],
        added_events: list[Mapping[str, Any]],
        removed_events: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        identities = [
            ObjectIdentity(
                source_id=str(match.get("input_object")),
                target_id=str(match.get("output_object")),
                transition=self._transition_type(match),
                transition_kind=IdentityTransitionKind.PRESERVED,
                continuity_score=float(match.get("identity_continuity", 0.0)),
                confidence=float(match.get("match_confidence", 0.0)),
                evidence={
                    "track_id": match.get("track_id"),
                    "identity_state": match.get("identity_state"),
                    "placement_vector": match.get("placement_vector", {}),
                    "color_changed": match.get("color_changed", False),
                    "size_changed": match.get("size_changed", False),
                    "shape_changed": match.get("shape_changed", False),
                    "position_preserved": match.get("position_preserved", True),
                },
            ).export()
            for match in matches
        ]

        descendants: dict[str, set[str]] = {}
        for match in matches:
            descendants.setdefault(str(match.get("input_object")), set()).add(
                str(match.get("output_object"))
            )
        for event in added_events:
            source = event.get("source_candidate")
            target = event.get("output_object")
            if source and target:
                descendants.setdefault(str(source), set()).add(str(target))

        for source_id, targets in sorted(descendants.items()):
            if len(targets) <= 1:
                continue
            continuity_scores = [
                float(match.get("identity_continuity", 0.0))
                for match in matches
                if str(match.get("input_object")) == source_id
            ]
            continuity_scores.extend(
                float(event.get("confidence", 0.0))
                for event in added_events
                if str(event.get("source_candidate")) == source_id
            )
            continuity_score = (
                sum(continuity_scores) / len(continuity_scores)
                if continuity_scores
                else 0.0
            )
            identities.append(
                ObjectIdentity(
                    source_id=source_id,
                    targets=sorted(targets),
                    transition="identity_split",
                    transition_kind=IdentityTransitionKind.SPLIT,
                    continuity_score=continuity_score,
                    evidence={"descendant_count": len(targets)},
                ).export()
            )

        merge_sources: dict[str, set[str]] = {}
        for match in matches:
            merge_sources.setdefault(str(match.get("output_object")), set()).add(
                str(match.get("input_object"))
            )
        for event in removed_events:
            target = event.get("target_candidate")
            source = event.get("input_object")
            if source and target:
                merge_sources.setdefault(str(target), set()).add(str(source))

        for target_id, sources in sorted(merge_sources.items()):
            if len(sources) <= 1:
                continue
            confidence_values = [
                float(match.get("identity_continuity", 0.0))
                for match in matches
                if str(match.get("output_object")) == target_id
            ]
            confidence_values.extend(
                float(event.get("confidence", 0.0))
                for event in removed_events
                if str(event.get("target_candidate")) == target_id
            )
            continuity_score = (
                sum(confidence_values) / len(confidence_values)
                if confidence_values
                else 0.0
            )
            identities.append(
                ObjectIdentity(
                    source_id=",".join(sorted(sources)),
                    target_id=target_id,
                    transition="identity_merged",
                    transition_kind=IdentityTransitionKind.MERGED,
                    continuity_score=continuity_score,
                    evidence={
                        "source_count": len(sources),
                        "sources": sorted(sources),
                    },
                ).export()
            )

        identities.extend(
            ObjectIdentity(
                source_id="__created__",
                target_id=str(event.get("output_object")),
                transition="created",
                transition_kind=IdentityTransitionKind.CREATED,
                continuity_score=0.0,
                confidence=float(event.get("confidence", 0.0)),
                evidence={"event": "object_created"},
            ).export()
            for event in added_events
            if not event.get("source_candidate")
        )

        identities.extend(
            ObjectIdentity(
                source_id=str(event.get("input_object")),
                transition="removed",
                transition_kind=IdentityTransitionKind.DESTROYED,
                continuity_score=0.0,
                confidence=float(event.get("confidence", 0.0)),
                evidence={
                    "event": "object_removed",
                    "target_candidate": event.get("target_candidate"),
                },
            ).export()
            for event in removed_events
            if not event.get("target_candidate")
        )
        identities.extend(
            ObjectIdentity(
                source_id=str(event.get("input_object")),
                target_id=str(event.get("target_candidate")),
                transition="identity_merged",
                transition_kind=IdentityTransitionKind.MERGED,
                continuity_score=0.0,
                confidence=float(event.get("confidence", 0.0)),
                evidence={
                    "event": "object_removed_into_target",
                    "target_candidate": event.get("target_candidate"),
                },
            ).export()
            for event in removed_events
            if event.get("target_candidate")
        )
        return identities

    def _identity_transitions(
        self,
        matches: list[Mapping[str, Any]],
        added_events: list[Mapping[str, Any]],
        removed_events: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        transitions = [
            IdentityTransition(
                source=str(match.get("input_object")),
                target=str(match.get("output_object")),
                transition_type=self._transition_type(match),
                transition_kind=IdentityTransitionKind.PRESERVED,
                confidence=float(match.get("identity_continuity", 0.0)),
                evidence={
                    "match_confidence": match.get("match_confidence", 0.0),
                    "track_id": match.get("track_id"),
                    "placement_vector": match.get("placement_vector", {}),
                },
            ).export()
            for match in matches
        ]

        descendants: dict[str, set[str]] = {}
        for match in matches:
            descendants.setdefault(str(match.get("input_object")), set()).add(
                str(match.get("output_object"))
            )
        for event in added_events:
            source = event.get("source_candidate")
            target = event.get("output_object")
            if source and target:
                descendants.setdefault(str(source), set()).add(str(target))

        for source, targets in sorted(descendants.items()):
            if len(targets) <= 1:
                continue
            confidence_values = [
                float(match.get("identity_continuity", 0.0))
                for match in matches
                if str(match.get("input_object")) == source
            ]
            confidence_values.extend(
                float(event.get("confidence", 0.0))
                for event in added_events
                if str(event.get("source_candidate")) == source
            )
            confidence = (
                sum(confidence_values) / len(confidence_values)
                if confidence_values
                else 0.0
            )
            transitions.append(
                IdentityTransition(
                    source=source,
                    targets=sorted(targets),
                    transition_type="identity_split",
                    transition_kind=IdentityTransitionKind.SPLIT,
                    confidence=confidence,
                    evidence={"descendant_count": len(targets)},
                ).export()
            )

        merge_sources: dict[str, set[str]] = {}
        for match in matches:
            merge_sources.setdefault(str(match.get("output_object")), set()).add(
                str(match.get("input_object"))
            )
        for event in removed_events:
            source = event.get("input_object")
            target = event.get("target_candidate")
            if source and target:
                merge_sources.setdefault(str(target), set()).add(str(source))

        for target, sources in sorted(merge_sources.items()):
            if len(sources) <= 1:
                continue
            confidence_values = [
                float(match.get("identity_continuity", 0.0))
                for match in matches
                if str(match.get("output_object")) == target
            ]
            confidence_values.extend(
                float(event.get("confidence", 0.0))
                for event in removed_events
                if str(event.get("target_candidate")) == target
            )
            confidence = (
                sum(confidence_values) / len(confidence_values)
                if confidence_values
                else 0.0
            )
            transitions.append(
                IdentityTransition(
                    source=",".join(sorted(sources)),
                    target=target,
                    transition_type="identity_merged",
                    transition_kind=IdentityTransitionKind.MERGED,
                    confidence=confidence,
                    evidence={
                        "source_count": len(sources),
                        "sources": sorted(sources),
                    },
                ).export()
            )

        transitions.extend(
            IdentityTransition(
                source="__created__",
                target=str(event.get("output_object")),
                transition_type="created",
                transition_kind=IdentityTransitionKind.CREATED,
                confidence=float(event.get("confidence", 0.0)),
                evidence={"event": "object_created"},
            ).export()
            for event in added_events
            if not event.get("source_candidate")
        )

        transitions.extend(
            IdentityTransition(
                source=str(event.get("input_object")),
                transition_type="removed",
                transition_kind=IdentityTransitionKind.DESTROYED,
                confidence=float(event.get("confidence", 0.0)),
                evidence={
                    "event": "object_removed",
                    "target_candidate": event.get("target_candidate"),
                },
            ).export()
            for event in removed_events
            if not event.get("target_candidate")
        )
        transitions.extend(
            IdentityTransition(
                source=str(event.get("input_object")),
                target=str(event.get("target_candidate")),
                transition_type="identity_merged",
                transition_kind=IdentityTransitionKind.MERGED,
                confidence=float(event.get("confidence", 0.0)),
                evidence={
                    "event": "object_removed_into_target",
                    "target_candidate": event.get("target_candidate"),
                },
            ).export()
            for event in removed_events
            if event.get("target_candidate")
        )
        return transitions

    def _transition_type(
        self,
        match: Mapping[str, Any],
    ) -> str:
        if match.get("identity_state") == "identity_stable":
            return "preserved"
        if match.get("color_changed"):
            return "color_changed"
        if match.get("size_changed"):
            return "size_changed"
        if match.get("shape_changed"):
            return "shape_changed"
        if not match.get("position_preserved", True):
            return "position_changed"
        return "preserved_with_change"

    def _identity_match_score(
        self,
        input_obj: Mapping[str, Any],
        output_obj: Mapping[str, Any],
    ) -> float:
        input_cells = self._cell_set(input_obj)
        output_cells = self._cell_set(output_obj)
        overlap = len(input_cells & output_cells)
        containment = overlap / max(min(len(input_cells), len(output_cells)), 1)
        union_overlap = overlap / max(len(input_cells | output_cells), 1)
        same_color = 1.0 if input_obj.get("color") == output_obj.get("color") else 0.0
        same_shape = (
            1.0
            if input_obj.get("canonical_shape_signature")
            == output_obj.get("canonical_shape_signature")
            else 0.0
        )
        size_ratio = min(
            float(input_obj.get("size", 0)),
            float(output_obj.get("size", 0)),
        ) / max(
            float(input_obj.get("size", 0)),
            float(output_obj.get("size", 0)),
            1.0,
        )
        center_distance = self.spatial_relation_engine.placement_vector(
            input_obj,
            output_obj,
        )["manhattan_distance"]
        proximity = 1.0 / (1.0 + float(center_distance))
        bbox_related = 1.0 if self._bbox_related(input_obj, output_obj) else 0.0
        return clamp(
            containment * 0.30
            + union_overlap * 0.16
            + same_color * 0.16
            + same_shape * 0.16
            + size_ratio * 0.10
            + proximity * 0.08
            + bbox_related * 0.04
        )

    def _semantic_spine_stability(
        self,
        input_obj: Mapping[str, Any],
        output_obj: Mapping[str, Any],
    ) -> float:
        same_shape = (
            1.0
            if input_obj.get("canonical_shape_signature")
            == output_obj.get("canonical_shape_signature")
            else 0.0
        )
        same_size = 1.0 if input_obj.get("size") == output_obj.get("size") else 0.0
        same_holes = 1.0 if input_obj.get("holes") == output_obj.get("holes") else 0.0
        same_solidity = (
            1.0
            if input_obj.get("is_solid") == output_obj.get("is_solid")
            else 0.0
        )
        return clamp(
            same_shape * 0.52
            + same_size * 0.22
            + same_holes * 0.14
            + same_solidity * 0.12
        )

    def _semantic_spine_continuity(
        self,
        matches: list[Mapping[str, Any]],
    ) -> float:
        if not matches:
            return 0.0
        return clamp(
            sum(match.get("semantic_spine_stability", 0.0) for match in matches)
            / len(matches)
        )

    def _identity_signature(self, obj: Mapping[str, Any] | None) -> str:
        if not obj:
            return "identity:unresolved"
        shape = obj.get(
            "canonical_shape_signature",
            obj.get("shape_signature", "unknown_shape"),
        )
        size = obj.get("size", "unknown_size")
        holes = obj.get("holes", "unknown_holes")
        return f"shape={shape}|size={size}|holes={holes}"

    def _track_id_for(
        self,
        input_obj: Mapping[str, Any],
        output_obj: Mapping[str, Any],
    ) -> str:
        for key in (
            self._identity_signature(input_obj),
            self._identity_signature(output_obj),
        ):
            track_id = self._track_index.get(key)
            if track_id:
                self._track_index[self._identity_signature(output_obj)] = track_id
                return track_id

        self._track_counter += 1
        track_id = f"track_{self._track_counter}"
        self._track_index[self._identity_signature(input_obj)] = track_id
        self._track_index[self._identity_signature(output_obj)] = track_id
        return track_id

    def _identity_runtime_state(
        self,
        runtime_confidence: float,
        gates: Mapping[str, bool],
    ) -> str:
        if all(gates.values()) and runtime_confidence >= 0.82:
            return "IDENTITY_RUNTIME_STABLE"
        if gates.get("identity_continuity_above_limit") and runtime_confidence >= 0.64:
            return "IDENTITY_RUNTIME_PROVISIONAL"
        return "IDENTITY_RUNTIME_WEAK"

    def _identity_state(
        self,
        input_obj: Mapping[str, Any],
        output_obj: Mapping[str, Any],
    ) -> str:
        if input_obj.get("color") != output_obj.get("color"):
            return "identity_preserved_color_changed"
        if input_obj.get("size") != output_obj.get("size"):
            return "identity_preserved_size_changed"
        vector = self.spatial_relation_engine.placement_vector(input_obj, output_obj)
        if vector["delta_row"] != 0 or vector["delta_col"] != 0:
            return "identity_preserved_position_changed"
        if input_obj.get("canonical_shape_signature") != output_obj.get(
            "canonical_shape_signature"
        ):
            return "identity_preserved_shape_changed"
        return "identity_stable"

    def _identity_continuity(
        self,
        matches: list[Mapping[str, Any]],
    ) -> float:
        if not matches:
            return 0.0
        return clamp(
            sum(match.get("identity_continuity", 0.0) for match in matches)
            / len(matches)
        )

    def _identity_continuity_state(
        self,
        matches: list[Mapping[str, Any]],
    ) -> str:
        continuity = self._identity_continuity(matches)
        if continuity >= 0.80:
            return "IDENTITY_CONTINUITY_STABLE"
        if continuity >= 0.58:
            return "IDENTITY_CONTINUITY_PROVISIONAL"
        return "IDENTITY_CONTINUITY_WEAK"

    def _bbox_related(
        self,
        input_obj: Mapping[str, Any],
        output_obj: Mapping[str, Any],
    ) -> bool:
        first = input_obj.get("bbox", {})
        second = output_obj.get("bbox", {})
        if not first or not second:
            return False
        contains = (
            first["min_row"] <= second["min_row"]
            and first["min_col"] <= second["min_col"]
            and first["max_row"] >= second["max_row"]
            and first["max_col"] >= second["max_col"]
        ) or (
            second["min_row"] <= first["min_row"]
            and second["min_col"] <= first["min_col"]
            and second["max_row"] >= first["max_row"]
            and second["max_col"] >= first["max_col"]
        )
        return contains or self.spatial_relation_engine.bbox_gap(first, second) <= 1

    def _cell_set(self, obj: Mapping[str, Any]) -> set[tuple[int, int]]:
        return {(int(row), int(col)) for row, col in obj.get("cells", [])}

    def _added_event(
        self,
        added_object: Mapping[str, Any],
        input_objects: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        description = self.spatial_relation_engine.describe_added_object(
            added_object,
            input_objects,
        )
        transition_kind = (
            IdentityTransitionKind.SPLIT
            if description.get("source_candidate")
            else IdentityTransitionKind.CREATED
        )
        return {
            "event": "object_added",
            "identity_transition": transition_kind.value,
            "output_object": added_object.get("id"),
            "color": added_object.get("color"),
            "shape_signature": added_object.get("shape_signature"),
            "canonical_shape_signature": added_object.get(
                "canonical_shape_signature"
            ),
            "source_candidate": description.get("source_candidate"),
            "placement_vector": description.get("placement_vector", {}),
            "source_relation": description.get("source_relation", {}),
            "confidence": clamp(description.get("confidence", 0.0)),
        }

    def _removed_event(
        self,
        removed_object: Mapping[str, Any],
        output_objects: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        description = self.spatial_relation_engine.describe_added_object(
            removed_object,
            output_objects,
        )
        target_candidate = description.get("source_candidate")
        transition_kind = (
            IdentityTransitionKind.MERGED
            if target_candidate
            else IdentityTransitionKind.DESTROYED
        )
        return {
            "event": "object_removed",
            "identity_transition": transition_kind.value,
            "input_object": removed_object.get("id"),
            "color": removed_object.get("color"),
            "shape_signature": removed_object.get("shape_signature"),
            "canonical_shape_signature": removed_object.get(
                "canonical_shape_signature"
            ),
            "target_candidate": target_candidate,
            "placement_vector": description.get("placement_vector", {}),
            "target_relation": description.get("source_relation", {}),
            "confidence": clamp(description.get("confidence", 0.0))
            if target_candidate
            else 0.86,
        }

    def _tracking_confidence(
        self,
        matches: list[Mapping[str, Any]],
        added_events: list[Mapping[str, Any]],
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
    ) -> float:
        if not input_objects and not output_objects:
            return 1.0
        match_scores = [match.get("match_confidence", 0.0) for match in matches]
        added_scores = [event.get("confidence", 0.0) for event in added_events]
        evidence_scores = match_scores + added_scores
        if not evidence_scores:
            return 0.0
        coverage = len(evidence_scores) / max(len(input_objects), len(output_objects), 1)
        return clamp((sum(evidence_scores) / len(evidence_scores)) * coverage)


__all__ = [
    "IdentityTransitionKind",
    "IdentityTransition",
    "IdentityTrack",
    "ObjectIdentity",
    "ObjectTracker",
    "TrackedObject",
]
