from collections import Counter
from typing import Any, Mapping

from core.epistemic_models import clamp
from core.perception.object_tracker import ObjectTracker


class IdentityContinuityEngine:
    """Forecasts whether a new truth can join the existing identity spine."""

    def __init__(
        self,
        minimum_continuity=0.62,
        maximum_semantic_drift=0.58,
        object_tracker: ObjectTracker | None = None,
    ):
        self.minimum_continuity = minimum_continuity
        self.maximum_semantic_drift = maximum_semantic_drift
        self.minimum_semantic_spine_score = 1.0 - maximum_semantic_drift
        self.object_tracker = object_tracker or ObjectTracker()

    def evaluate(
        self,
        concept,
        old_spine_continuity,
        new_truth_delta=0.0,
        minimum_continuity=None,
        breaks_core_truths=False,
    ):
        threshold = (
            self.minimum_continuity
            if minimum_continuity is None
            else clamp(minimum_continuity)
        )
        old_spine_continuity = clamp(old_spine_continuity)
        try:
            new_truth_delta = float(new_truth_delta)
        except (TypeError, ValueError):
            new_truth_delta = 0.0
        new_truth_delta = max(min(new_truth_delta, 1.0), -1.0)
        continuity_score = clamp(old_spine_continuity + new_truth_delta)
        core_truths_preserved = breaks_core_truths is not True
        allowed_transition = (
            core_truths_preserved
            and continuity_score >= threshold
        )

        return {
            "system": "identity_continuity_engine",
            "concept": concept,
            "old_spine_continuity": old_spine_continuity,
            "new_truth_identity_delta": round(new_truth_delta, 4),
            "continuity_score": continuity_score,
            "minimum_continuity": threshold,
            "core_truths_preserved": core_truths_preserved,
            "allowed_transition": allowed_transition,
            "transition_state": (
                "IDENTITY_CONTINUITY_PRESERVED"
                if allowed_transition
                else "CORE_TRUTH_CONFLICT"
                if not core_truths_preserved
                else "IDENTITY_CONTINUITY_HOLD"
            ),
        }

    def evaluate_objects(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str = "object_identity_preservation",
    ) -> dict[str, Any]:
        """Evaluate whether perceived objects preserve identity across states."""

        tracking = self.object_tracker.track(input_grid, output_grid)
        mappings = self._temporal_mappings(tracking)
        transition_counts = Counter(
            mapping["identity_transition"]
            for mapping in mappings
        )
        continuity_score = self._object_continuity_score(mappings)
        continuity_state = self._object_continuity_state(
            continuity_score,
            transition_counts,
        )
        report = {
            "system": "object_identity_continuity_engine",
            "source": source,
            "input_object_count": tracking.get("input_object_count", 0),
            "output_object_count": tracking.get("output_object_count", 0),
            "object_temporal_mappings": mappings,
            "transition_counts": dict(sorted(transition_counts.items())),
            "continuity_score": continuity_score,
            "continuity_state": continuity_state,
            "identity_preserved": continuity_state in {
                "OBJECT_IDENTITY_CONTINUOUS",
                "OBJECT_IDENTITY_TRANSFORMED",
            },
            "identity_split": transition_counts.get("IdentitySplit", 0) > 0,
            "identity_merged": transition_counts.get("IdentityMerged", 0) > 0,
            "identity_created": transition_counts.get("IdentityCreated", 0) > 0,
            "identity_destroyed": transition_counts.get("IdentityDestroyed", 0) > 0,
            "tracking": tracking,
        }
        report["dependency_evidence"] = self._object_dependency_evidence(report)
        return report

    def evaluate_sequence(
        self,
        states: list[Any],
        source: str = "object_identity_preservation",
    ) -> dict[str, Any]:
        """Evaluate Object(t0) -> Object(t1) -> ... identity continuity."""

        if len(states) < 2:
            return {
                "system": "identity_continuity_engine",
                "mode": "temporal_identity_sequence",
                "source": source,
                "state_count": len(states),
                "step_reports": [],
                "identity_chains": [],
                "transition_counts": {},
                "identity_continuity": 1.0,
                "continuity_score": 1.0,
                "identity_continuity_preserved": True,
                "identity_preserved": True,
                "identity_split": False,
                "identity_merged": False,
                "continuity_state": "IDENTITY_SEQUENCE_TRIVIAL",
                "identity_governance_gates": {
                    "identity_stable": True,
                    "semantic_spine_stable": True,
                    "identity_continuity_above_limit": True,
                },
                "dependency_evidence": [],
            }

        step_reports = [
            self.evaluate_objects(
                states[index],
                states[index + 1],
                source=source,
            )
            for index in range(len(states) - 1)
        ]
        temporal_edges = self._temporal_edges(step_reports)
        chains = self._identity_chains(temporal_edges)
        transition_counts = Counter(
            edge["identity_transition"]
            for edge in temporal_edges
        )
        continuity_score = self._sequence_continuity_score(
            step_reports,
            chains,
        )
        raw_semantic_spine_score = self._sequence_semantic_spine_score(
            step_reports,
        )
        has_split = transition_counts.get("IdentitySplit", 0) > 0
        has_merge = transition_counts.get("IdentityMerged", 0) > 0
        has_interruption = any(
            transition_counts.get(kind, 0) > 0
            for kind in ["IdentityCreated", "IdentityDestroyed"]
        )
        identity_preserved = (
            continuity_score >= self.minimum_continuity
            and not has_interruption
        )
        semantic_spine_score = (
            max(raw_semantic_spine_score, continuity_score)
            if identity_preserved
            else raw_semantic_spine_score
        )
        semantic_drift = clamp(1.0 - semantic_spine_score)
        semantic_spine_stable = (
            semantic_spine_score >= self.minimum_semantic_spine_score
        )
        gates = {
            "identity_stable": identity_preserved
            and not has_split
            and not has_merge,
            "semantic_spine_stable": semantic_spine_stable,
            "semantic_drift_below_limit":
            semantic_drift < self.maximum_semantic_drift,
            "identity_continuity_above_limit":
            continuity_score >= self.minimum_continuity,
        }
        report = {
            "system": "identity_continuity_engine",
            "mode": "temporal_identity_sequence",
            "source": source,
            "state_count": len(states),
            "step_reports": step_reports,
            "identity_temporal_edges": temporal_edges,
            "identity_chains": chains,
            "transition_counts": dict(sorted(transition_counts.items())),
            "identity_continuity": continuity_score,
            "continuity_score": continuity_score,
            "raw_semantic_spine_score": raw_semantic_spine_score,
            "semantic_spine_score": semantic_spine_score,
            "semantic_drift": semantic_drift,
            "minimum_continuity": self.minimum_continuity,
            "maximum_semantic_drift": self.maximum_semantic_drift,
            "minimum_semantic_spine_score":
            self.minimum_semantic_spine_score,
            "identity_continuity_preserved": identity_preserved,
            "identity_preserved": identity_preserved,
            "identity_split": has_split,
            "identity_merged": has_merge,
            "identity_created": transition_counts.get("IdentityCreated", 0) > 0,
            "identity_destroyed":
            transition_counts.get("IdentityDestroyed", 0) > 0,
            "continuity_state": self._sequence_continuity_state(
                identity_preserved,
                has_split,
                has_merge,
                has_interruption,
                continuity_score,
            ),
            "identity_governance_gates": gates,
        }
        report["dependency_evidence"] = self._sequence_dependency_evidence(report)
        return report

    def run_identity_runtime(
        self,
        states: list[Any],
        concept: str = "object_identity_preservation",
        source: str = "object_identity_preservation",
    ) -> dict[str, Any]:
        """Produce a governance-ready identity runtime report."""

        sequence = self.evaluate_sequence(states, source=source)
        gates = sequence.get("identity_governance_gates", {})
        identity_stable = gates.get("identity_stable", False) is True
        semantic_spine_stable = (
            gates.get("semantic_spine_stable", False) is True
        )
        identity_continuity = clamp(sequence.get("identity_continuity", 0.0))
        semantic_spine_score = clamp(sequence.get("semantic_spine_score", 0.0))
        semantic_drift = clamp(
            sequence.get("semantic_drift", 1.0 - semantic_spine_score)
        )
        runtime_ready = (
            sequence.get("identity_continuity_preserved") is True
            and gates.get("identity_continuity_above_limit", False) is True
            and semantic_spine_stable
        )
        runtime_state = (
            "IDENTITY_RUNTIME_STABLE"
            if runtime_ready and identity_stable
            else "IDENTITY_RUNTIME_TRANSFORMED"
            if runtime_ready
            else "IDENTITY_RUNTIME_REVIEW_REQUIRED"
        )
        context_patch = {
            "identity_continuity": identity_continuity,
            "semantic_drift": semantic_drift,
            "identity_continuity_engine_report": sequence,
            "identity_stability_report": {
                "identity_stability_state":
                self._runtime_identity_stability_state(
                    sequence,
                    identity_stable,
                    runtime_ready,
                ),
                "identity_runtime_state": runtime_state,
                "identity_continuity": identity_continuity,
            },
            "semantic_spine_report": {
                "semantic_spine_state": (
                    "stable_semantic_spine"
                    if semantic_spine_stable
                    else "semantic_spine_recovering"
                ),
                "semantic_spine_score": semantic_spine_score,
            },
        }
        return {
            "system": "identity_runtime",
            "concept": concept,
            "source": source,
            "runtime_state": runtime_state,
            "runtime_ready": runtime_ready,
            "identity_stable": identity_stable,
            "semantic_spine_stable": semantic_spine_stable,
            "identity_continuity": identity_continuity,
            "semantic_drift": semantic_drift,
            "identity_continuity_preserved": sequence.get(
                "identity_continuity_preserved",
                False,
            ),
            "minimum_continuity": self.minimum_continuity,
            "maximum_semantic_drift": self.maximum_semantic_drift,
            "minimum_semantic_spine_score":
            self.minimum_semantic_spine_score,
            "identity_split": sequence.get("identity_split", False),
            "identity_merged": sequence.get("identity_merged", False),
            "identity_governance_gates": gates,
            "truth_commit_context_patch": context_patch,
            "sequence": sequence,
            "dependency_evidence": sequence.get("dependency_evidence", []),
        }

    def _runtime_identity_stability_state(
        self,
        sequence: Mapping[str, Any],
        identity_stable: bool,
        runtime_ready: bool,
    ) -> str:
        if identity_stable:
            return "stable"
        if sequence.get("identity_split") is True:
            return "identity_branching_tracked"
        if sequence.get("identity_merged") is True:
            return "identity_convergence_tracked"
        if runtime_ready:
            return "identity_transformation_tracked"
        return "fragile_semantic_spine"

    def _temporal_mappings(
        self,
        tracking: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        mappings = []
        for transition in tracking.get("identity_transitions", []):
            targets = list(transition.get("targets", []))
            if transition.get("target"):
                targets.append(transition["target"])
            if not targets:
                targets = [None]
            for target in sorted(set(targets), key=lambda item: str(item)):
                mappings.append({
                    "object_t0": transition.get("source"),
                    "object_t1": target,
                    "identity_transition": transition.get(
                        "identity_transition",
                        transition.get("transition_kind", "IdentityPreserved"),
                    ),
                    "transition_type": transition.get("transition_type"),
                    "continuity": clamp(transition.get("confidence", 0.0)),
                    "evidence": dict(transition.get("evidence", {})),
                })
        return mappings

    def _object_continuity_score(
        self,
        mappings: list[Mapping[str, Any]],
    ) -> float:
        if not mappings:
            return 1.0
        weights = {
            "IdentityPreserved": 1.0,
            "IdentitySplit": 0.72,
            "IdentityMerged": 0.68,
            "IdentityCreated": 0.38,
            "IdentityDestroyed": 0.20,
        }
        scores = [
            clamp(mapping.get("continuity", 0.0))
            * weights.get(str(mapping.get("identity_transition")), 0.45)
            for mapping in mappings
        ]
        return clamp(sum(scores) / len(scores))

    def _object_continuity_state(
        self,
        continuity_score: float,
        transition_counts: Mapping[str, int],
    ) -> str:
        if transition_counts.get("IdentityDestroyed", 0) > 0:
            return "OBJECT_IDENTITY_INTERRUPTED"
        if transition_counts.get("IdentityCreated", 0) > 0:
            return "OBJECT_IDENTITY_CREATED"
        if transition_counts.get("IdentitySplit", 0) > 0:
            return "OBJECT_IDENTITY_SPLIT"
        if transition_counts.get("IdentityMerged", 0) > 0:
            return "OBJECT_IDENTITY_MERGED"
        if continuity_score >= 0.82:
            return "OBJECT_IDENTITY_CONTINUOUS"
        if continuity_score >= 0.58:
            return "OBJECT_IDENTITY_TRANSFORMED"
        return "OBJECT_IDENTITY_WEAK"

    def _object_dependency_evidence(
        self,
        report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        source = str(report.get("source", "object_identity_preservation"))
        evidence = [
            self._dependency(
                source,
                f"object_continuity:{report.get('continuity_state')}",
                report.get("continuity_score", 0.0),
                {
                    "transition_counts": report.get("transition_counts", {}),
                    "object_temporal_mappings": report.get(
                        "object_temporal_mappings",
                        [],
                    ),
                },
            )
        ]
        for transition, count in sorted(report.get("transition_counts", {}).items()):
            evidence.append(
                self._dependency(
                    source,
                    f"identity_transition:{transition}",
                    0.90 if transition == "IdentityPreserved" else 0.76,
                    {"transition": transition, "count": count},
                )
            )
        return evidence

    def _temporal_edges(
        self,
        step_reports: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        edges = []
        for step_index, report in enumerate(step_reports):
            for mapping in report.get("object_temporal_mappings", []):
                edges.append({
                    "step": step_index,
                    "object_from": self._phase_object_id(
                        step_index,
                        mapping.get("object_t0"),
                    ),
                    "object_to": self._phase_object_id(
                        step_index + 1,
                        mapping.get("object_t1"),
                    ),
                    "identity_transition": mapping.get(
                        "identity_transition",
                        "IdentityPreserved",
                    ),
                    "transition_type": mapping.get("transition_type"),
                    "continuity": clamp(mapping.get("continuity", 0.0)),
                    "evidence": dict(mapping.get("evidence", {})),
                })
        return edges

    def _phase_object_id(self, phase: int, object_id: Any) -> str | None:
        if object_id is None:
            return None
        return f"t{phase}:{object_id}"

    def _identity_chains(
        self,
        temporal_edges: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        outgoing: dict[str, list[Mapping[str, Any]]] = {}
        incoming: set[str] = set()
        for edge in temporal_edges:
            source = edge.get("object_from")
            target = edge.get("object_to")
            if source is not None:
                outgoing.setdefault(str(source), []).append(edge)
            if target is not None:
                incoming.add(str(target))

        roots = sorted(set(outgoing) - incoming)
        if not roots:
            roots = sorted(outgoing)

        chains = []
        for root in roots:
            self._walk_identity_chain(
                root,
                outgoing,
                [root],
                [],
                chains,
            )
        return chains

    def _walk_identity_chain(
        self,
        current: str,
        outgoing: Mapping[str, list[Mapping[str, Any]]],
        path: list[str],
        transitions: list[str],
        chains: list[dict[str, Any]],
    ) -> None:
        edges = outgoing.get(current, [])
        if not edges:
            chains.append({
                "chain": list(path),
                "transition_path": list(transitions),
                "chain_length": len(path),
                "identity_preserved": all(
                    transition == "IdentityPreserved"
                    for transition in transitions
                ),
            })
            return
        for edge in edges:
            target = edge.get("object_to")
            next_path = list(path)
            if target is not None:
                next_path.append(str(target))
            else:
                chains.append({
                    "chain": next_path,
                    "transition_path": [
                        *transitions,
                        str(edge.get("identity_transition")),
                    ],
                    "chain_length": len(next_path),
                    "identity_preserved": False,
                })
                continue
            self._walk_identity_chain(
                str(target),
                outgoing,
                next_path,
                [
                    *transitions,
                    str(edge.get("identity_transition")),
                ],
                chains,
            )

    def _sequence_continuity_score(
        self,
        step_reports: list[Mapping[str, Any]],
        chains: list[Mapping[str, Any]],
    ) -> float:
        if not step_reports:
            return 1.0
        step_score = sum(
            clamp(report.get("continuity_score", 0.0))
            for report in step_reports
        ) / len(step_reports)
        chain_score = (
            sum(1.0 if chain.get("identity_preserved") else 0.64 for chain in chains)
            / len(chains)
            if chains
            else 0.0
        )
        return clamp(step_score * 0.72 + chain_score * 0.28)

    def _sequence_semantic_spine_score(
        self,
        step_reports: list[Mapping[str, Any]],
    ) -> float:
        scores = []
        for report in step_reports:
            tracking = report.get("tracking", {})
            runtime = tracking.get("identity_runtime", {})
            scores.append(
                clamp(
                    runtime.get(
                        "identity_spine_continuity",
                        report.get("continuity_score", 0.0),
                    )
                )
            )
        if not scores:
            return 1.0
        return clamp(sum(scores) / len(scores))

    def _sequence_continuity_state(
        self,
        identity_preserved: bool,
        has_split: bool,
        has_merge: bool,
        has_interruption: bool,
        continuity_score: float,
    ) -> str:
        if has_interruption:
            return "IDENTITY_SEQUENCE_INTERRUPTED"
        if has_split:
            return "IDENTITY_SEQUENCE_SPLIT"
        if has_merge:
            return "IDENTITY_SEQUENCE_MERGED"
        if identity_preserved and continuity_score >= 0.82:
            return "IDENTITY_SEQUENCE_PRESERVED"
        if identity_preserved:
            return "IDENTITY_SEQUENCE_TRANSFORMED"
        return "IDENTITY_SEQUENCE_WEAK"

    def _sequence_dependency_evidence(
        self,
        report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        source = str(report.get("source", "object_identity_preservation"))
        evidence = [
            self._dependency(
                source,
                f"identity_sequence:{report.get('continuity_state')}",
                report.get("continuity_score", 0.0),
                {
                    "identity_chains": report.get("identity_chains", []),
                    "transition_counts": report.get("transition_counts", {}),
                    "identity_continuity_preserved": report.get(
                        "identity_continuity_preserved",
                        False,
                    ),
                },
            )
        ]
        for transition, count in sorted(report.get("transition_counts", {}).items()):
            evidence.append(
                self._dependency(
                    source,
                    f"temporal_identity_transition:{transition}",
                    0.92 if transition == "IdentityPreserved" else 0.78,
                    {"transition": transition, "count": count},
                )
            )
        return evidence

    def _dependency(
        self,
        source: str,
        target: str,
        confidence: float,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "source": source,
            "target": target,
            "relation": "depends_on",
            "confidence": clamp(confidence),
            "dependency_type": "object_identity_continuity_dependency",
            "required": True,
            "supported": True,
            "transfer_success": True,
            "metadata": metadata,
        }


identity_continuity_engine = IdentityContinuityEngine()


__all__ = [
    "IdentityContinuityEngine",
    "identity_continuity_engine",
]
