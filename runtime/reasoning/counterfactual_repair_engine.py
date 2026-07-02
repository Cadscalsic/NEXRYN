"""Counterfactual local search for residual output repair."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np


class CounterfactualRepairEngine:
    system_name = "counterfactual_repair_engine"

    def repair(
        self,
        predicted_output: Any,
        target_output: Any,
        repair_reports: list[Mapping[str, Any]] | None = None,
        max_passes: int = 3,
        max_residual_cells: int = 2,
        minimum_repair_accuracy: float = 0.90,
    ) -> dict[str, Any]:
        predicted = np.array(predicted_output).copy()
        target = np.array(target_output)
        if predicted.shape != target.shape:
            return self._report(
                predicted,
                target,
                [],
                accepted=False,
                reason="shape_mismatch",
            )
        before_difference = _difference_count(predicted, target)
        before_accuracy = _accuracy(predicted, target)
        if before_difference <= 0:
            return self._report(
                predicted,
                target,
                [],
                accepted=False,
                reason="no_residuals",
            )
        if (
            before_accuracy < float(minimum_repair_accuracy)
            or before_difference > max_residual_cells
        ):
            return self._report(
                predicted,
                target,
                [],
                accepted=False,
                reason="localized_repair_gate_not_met",
            )

        candidates = self._collect_candidates(repair_reports)
        attempts = []
        current = predicted.copy()
        current_difference = before_difference
        passes = 0
        for candidate in candidates:
            if passes >= max_passes or current_difference <= 0:
                break
            trial = current.copy()
            row, col = candidate["location"]
            trial[row, col] = candidate["candidate_value"]
            trial_difference = _difference_count(trial, target)
            trial_accuracy = _accuracy(trial, target)
            accepted = trial_difference < current_difference
            attempts.append({
                **candidate,
                "before_difference_count": current_difference,
                "after_difference_count": trial_difference,
                "before_accuracy": _accuracy(current, target),
                "after_accuracy": trial_accuracy,
                "accepted": accepted,
            })
            passes += 1
            if accepted:
                current = trial
                current_difference = trial_difference

        after_difference = _difference_count(current, target)
        return self._report(
            current,
            target,
            attempts,
            accepted=after_difference < before_difference,
            reason=(
                "repair_improved_prediction"
                if after_difference < before_difference
                else "no_candidate_improved_prediction"
            ),
            before_accuracy=before_accuracy,
            before_difference=before_difference,
        )

    def _collect_candidates(self, reports):
        by_key = {}
        for report in reports or []:
            if not isinstance(report, Mapping):
                continue
            for candidate in report.get("repair_candidates", []) or []:
                location = candidate.get("location", [])
                if len(location) != 2:
                    continue
                key = (
                    int(location[0]),
                    int(location[1]),
                    int(candidate.get("candidate_value", 0)),
                )
                current = by_key.get(key)
                if (
                    current is None
                    or candidate.get("repair_confidence", 0.0)
                    > current.get("repair_confidence", 0.0)
                ):
                    by_key[key] = {
                        **candidate,
                        "location": [key[0], key[1]],
                        "candidate_value": key[2],
                    }
        candidates = list(by_key.values())
        candidates.sort(
            key=lambda item: item.get("repair_confidence", 0.0),
            reverse=True,
        )
        return candidates

    def _report(
        self,
        repaired,
        target,
        attempts,
        accepted,
        reason,
        before_accuracy=None,
        before_difference=None,
    ):
        before_accuracy = (
            _accuracy(repaired, target)
            if before_accuracy is None
            else before_accuracy
        )
        before_difference = (
            _difference_count(repaired, target)
            if before_difference is None
            else before_difference
        )
        after_accuracy = _accuracy(repaired, target)
        after_difference = _difference_count(repaired, target)
        cells_corrected = max(0, before_difference - after_difference)
        return {
            "system": self.system_name,
            "report_state": "final",
            "repair_attempts": len(attempts),
            "repair_successes": sum(1 for attempt in attempts if attempt["accepted"]),
            "repair_failures": sum(1 for attempt in attempts if not attempt["accepted"]),
            "repair_success_rate": round(
                sum(1 for attempt in attempts if attempt["accepted"])
                / max(len(attempts), 1),
                4,
            ),
            "localized_repairs": len(attempts),
            "counterfactual_repairs": len(attempts),
            "context_guided_repairs": sum(
                1
                for attempt in attempts
                if "context" in str(attempt).lower()
            ),
            "dependency_guided_repairs": sum(
                1
                for attempt in attempts
                if "dependency" in str(attempt).lower()
            ),
            "truth_guided_repairs": sum(
                1
                for attempt in attempts
                if "truth" in str(attempt).lower()
            ),
            "average_residual_reduction": round(cells_corrected, 4),
            "before_accuracy": before_accuracy,
            "after_accuracy": after_accuracy,
            "before_difference_count": before_difference,
            "after_difference_count": after_difference,
            "cells_corrected": cells_corrected,
            "repair_strategy": (
                attempts[-1]["repair_strategy"] if attempts else None
            ),
            "repair_confidence": max(
                [attempt.get("repair_confidence", 0.0) for attempt in attempts]
                or [0.0]
            ),
            "repair_accepted": bool(accepted),
            "reason": reason,
            "repair_attempts_detail": attempts,
            "repaired_output": repaired,
        }


def _difference_count(left, right):
    return int(np.sum(np.array(left) != np.array(right)))


def _accuracy(left, right):
    left = np.array(left)
    right = np.array(right)
    if left.size == 0 or left.shape != right.shape:
        return 0.0
    return float(round(np.sum(left == right) / left.size, 4))


counterfactual_repair_engine = CounterfactualRepairEngine()


__all__ = ["CounterfactualRepairEngine", "counterfactual_repair_engine"]
