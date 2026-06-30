"""Prepare successful strategies for later reuse and graduation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class StrategyGraduationEngine:
    system_name = "strategy_graduation_engine"

    def graduate(
        self,
        strategies: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        records = []
        for item in strategies or []:
            if not isinstance(item, Mapping):
                continue
            effectiveness = _score(
                item.get("effectiveness")
                or item.get("success_rate")
                or item.get("confidence")
            )
            stability = _score(item.get("stability") or effectiveness)
            reusable = effectiveness >= 0.75 and stability >= 0.70
            records.append({
                "strategy": item.get("strategy")
                or item.get("strategy_name")
                or item.get("name")
                or "runtime_strategy",
                "strategy_effectiveness": effectiveness,
                "strategy_stability": stability,
                "reusable_strategy": reusable,
                "graduation_state": (
                    "REUSABLE_STRATEGY"
                    if reusable
                    else "STRATEGY_OBSERVATION"
                ),
            })
        return {
            "system": self.system_name,
            "strategy_count": len(records),
            "reusable_strategy_count": sum(
                item["reusable_strategy"] for item in records
            ),
            "strategy_graduation_records": records,
        }


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


__all__ = ["StrategyGraduationEngine"]
