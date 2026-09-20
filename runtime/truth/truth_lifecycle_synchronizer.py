"""Synchronize locked truth state with recommendations and explanations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class TruthLifecycleSynchronizer:
    """Keep truth, governance, explanation, and learning signals coherent."""

    LOCKED_TRUTH = "LOCKED_TRUTH_PRESERVED"
    CACHE_REUSE = "CACHE_REUSE"
    FULL_VALIDATION = "FULL_VALIDATION"

    OBSOLETE_REASONS = {
        "contradiction requires review":
        "contradiction_review_required",
        "dependency coherence requires more evidence":
        "dependency_evidence_required",
        "truth candidate requires validation":
        "truth_candidate_validation_required",
    }

    def synchronize(
        self,
        concept_name: str | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        truth_record: Mapping[str, Any] | None = None,
        learning_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = deepcopy(runtime_context or {})
        record = truth_record if isinstance(truth_record, Mapping) else {}
        learning = learning_report if isinstance(learning_report, Mapping) else {}
        concept = str(
            concept_name
            or self._deep_get(record, "concept")
            or self._deep_get(context, "concept")
            or "runtime"
        )

        signals = self._signals(context, record)
        flags = self._synchronized_flags(signals)
        removed_reasons: list[str] = []

        dependency_stable = (
            signals["evidence_saturated"]
            and signals["dependency_chain_coverage"] >= 0.90
            and signals["dependency_explanation_quality"] >= 0.90
        )

        if signals["final_commit_state"] == self.LOCKED_TRUTH or dependency_stable:
            context, removed_reasons = self._remove_obsolete_reasons(
                context,
                signals,
            )
        if signals["final_commit_state"] == self.LOCKED_TRUTH:
            flags.update({
                "contradiction_review_required": False,
                "truth_candidate_validation_required": False,
            })
            context["contradiction_review_required"] = False

        saturated_for_freeze = (
            signals["final_commit_state"] == self.LOCKED_TRUTH
            and signals["evidence_saturated"]
            and signals["dependency_chain_coverage"] >= 0.95
            and signals["contradiction_review_required"] is False
        )
        learning_state = learning.get(
            "learning_state",
            "LEARNING_SATURATED" if saturated_for_freeze else "LEARNING_ACTIVE",
        )
        recommendation = (
            "freeze_concept"
            if saturated_for_freeze
            else context.get("recommended_next_step", "continue_adaptive_training")
        )
        if signals["final_commit_state"] == self.LOCKED_TRUTH and recommendation == (
            "continue_adaptive_training"
        ):
            recommendation = "freeze_concept"

        truth_validation_mode = (
            self.CACHE_REUSE
            if self.fast_path_eligible(signals)
            else context.get("truth_validation_mode", self.FULL_VALIDATION)
        )

        context["recommended_next_step"] = recommendation
        context["learning_state"] = learning_state
        context["truth_validation_mode"] = truth_validation_mode
        context["review_flags"] = flags
        context["how_we_know"] = self._how_we_know(context, signals)
        context["why"] = self._why(context, signals)
        context["TRUTH_LIFECYCLE_REPORT"] = {
            "concept_name": concept,
            "final_commit_state": signals["final_commit_state"],
            "learning_state": learning_state,
            "recommendation": recommendation,
            "synchronized_flags": flags,
            "removed_obsolete_reasons": removed_reasons,
            "truth_validation_mode": truth_validation_mode,
        }
        context["truth_lifecycle_report"] = context["TRUTH_LIFECYCLE_REPORT"]
        return context

    def fast_path_eligible(self, signals: Mapping[str, Any]) -> bool:
        return (
            signals.get("final_commit_state") == self.LOCKED_TRUTH
            and signals.get("identity_runtime_state") == "IDENTITY_RUNTIME_STABLE"
            and signals.get("contextual_truth_supported") is True
            and signals.get("contradiction_review_required") is False
            and signals.get("recovery_state") == "STABLE_SEMANTIC_SPINE"
        )

    def _signals(
        self,
        context: Mapping[str, Any],
        record: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "final_commit_state": self._field(record, context, "final_commit_state"),
            "contradiction_review_required": self._field(
                record,
                context,
                "contradiction_review_required",
                False,
            ) is True,
            "contextual_truth_supported": self._field(
                record,
                context,
                "contextual_truth_supported",
                False,
            ) is True,
            "identity_runtime_state": self._field(
                record,
                context,
                "identity_runtime_state",
            ),
            "recovery_state": self._field(record, context, "recovery_state"),
            "evidence_saturated": self._field(
                record,
                context,
                "evidence_saturated",
                False,
            ) is True,
            "dependency_chain_coverage": float(
                self._field(record, context, "dependency_chain_coverage", 0.0)
                or 0.0
            ),
            "dependency_explanation_quality": float(
                self._field(record, context, "dependency_explanation_quality", 0.0)
                or 0.0
            ),
        }

    def _synchronized_flags(self, signals: Mapping[str, Any]) -> dict[str, bool]:
        return {
            "contradiction_review_required":
            bool(signals["contradiction_review_required"]),
            "dependency_evidence_required":
            not (
                signals["dependency_chain_coverage"] >= 0.95
                and signals["dependency_explanation_quality"] >= 0.90
            ),
            "truth_candidate_validation_required":
            signals["final_commit_state"] != self.LOCKED_TRUTH,
            "identity_verification_required":
            signals["identity_runtime_state"] != "IDENTITY_RUNTIME_STABLE",
            "context_reconstruction_required":
            signals["contextual_truth_supported"] is not True,
        }

    def _remove_obsolete_reasons(
        self,
        context: dict[str, Any],
        signals: Mapping[str, Any],
    ) -> tuple[dict[str, Any], list[str]]:
        active = {
            "contradiction requires review":
            signals["contradiction_review_required"],
            "dependency coherence requires more evidence":
            not (
                signals["dependency_chain_coverage"] >= 0.95
                and signals["dependency_explanation_quality"] >= 0.90
            ),
            "truth candidate requires validation":
            signals["final_commit_state"] != self.LOCKED_TRUTH,
        }
        removed: list[str] = []

        def clean(value: Any) -> Any:
            if isinstance(value, dict):
                return {
                    key: clean(item)
                    for key, item in value.items()
                }
            if isinstance(value, list):
                cleaned = []
                for item in value:
                    if isinstance(item, str) and item in active and not active[item]:
                        removed.append(item)
                        continue
                    cleaned.append(clean(item))
                return cleaned
            return value

        cleaned = clean(context)
        return cleaned, sorted(set(removed))

    def _why(
        self,
        context: Mapping[str, Any],
        signals: Mapping[str, Any],
    ) -> list[str]:
        existing = [
            item
            for item in context.get("why", [])
            if isinstance(item, str)
        ]
        if signals["final_commit_state"] == self.LOCKED_TRUTH:
            existing.append("locked truth preserved by verified continuity")
        return self._unique(existing)

    def _how_we_know(
        self,
        context: Mapping[str, Any],
        signals: Mapping[str, Any],
    ) -> list[str]:
        existing = [
            item
            for item in context.get("how_we_know", [])
            if isinstance(item, str)
        ]
        if signals["dependency_chain_coverage"] >= 0.95:
            existing.append("dependency chain coverage is saturated")
        if signals["contextual_truth_supported"]:
            existing.append("contextual truth support is stable")
        if signals["identity_runtime_state"] == "IDENTITY_RUNTIME_STABLE":
            existing.append("identity runtime continuity is stable")
        return self._unique(existing)

    def _field(
        self,
        record: Mapping[str, Any],
        context: Mapping[str, Any],
        key: str,
        default: Any = None,
    ) -> Any:
        value = self._deep_get(record, key)
        if value is not None:
            return value
        value = self._deep_get(context, key)
        return default if value is None else value

    def _deep_get(self, value: Any, key: str) -> Any:
        if isinstance(value, Mapping):
            if key in value:
                return value[key]
            for item in value.values():
                found = self._deep_get(item, key)
                if found is not None:
                    return found
        if isinstance(value, list):
            for item in value:
                found = self._deep_get(item, key)
                if found is not None:
                    return found
        return None

    def _unique(self, items: list[str]) -> list[str]:
        seen = set()
        unique = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            unique.append(item)
        return unique


truth_lifecycle_synchronizer = TruthLifecycleSynchronizer()


__all__ = [
    "TruthLifecycleSynchronizer",
    "truth_lifecycle_synchronizer",
]
