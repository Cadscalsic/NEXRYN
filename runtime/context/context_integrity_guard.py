"""Runtime context integrity checks for critical pipeline stages."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class ContextIntegrityGuard:
    """Validate and repair required runtime context fields."""

    CRITICAL_STAGE_REQUIREMENTS = {
        "grid_analysis": ("input_grid", "output_grid"),
    }

    @staticmethod
    def _status(value: Any) -> dict[str, Any]:
        return {
            "present": value is not None,
            "type": type(value).__name__ if value is not None else None,
            "has_grid": hasattr(value, "grid"),
            "has_grid_summary": hasattr(value, "grid_summary"),
        }

    @classmethod
    def repair_grids(cls, context: dict[str, Any]) -> list[str]:
        repairs = []
        train_example = context.get("train_example")

        if isinstance(train_example, dict):
            if context.get("input_grid") is None and train_example.get("input") is not None:
                context["input_grid"] = train_example["input"]
                repairs.append("input_grid_from_train_example")

            if context.get("output_grid") is None and train_example.get("output") is not None:
                context["output_grid"] = train_example["output"]
                repairs.append("output_grid_from_train_example")

        return repairs

    @classmethod
    def trace(
        cls,
        context: dict[str, Any],
        stage_name: str,
        required_fields: tuple[str, ...] | None = None,
        repairs: list[str] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(context, dict):
            context = {}

        required = required_fields or cls.CRITICAL_STAGE_REQUIREMENTS.get(
            stage_name,
            (),
        )
        missing = [
            field
            for field in required
            if context.get(field) is None
        ]
        train_example = context.get("train_example")
        task_analysis = context.get("task_analysis")

        return {
            "system": "ContextIntegrityGuard",
            "stage_name": stage_name,
            "timestamp": str(datetime.utcnow()),
            "integrity_ok": not missing,
            "missing_fields": missing,
            "repairs": list(repairs or []),
            "input_grid_status": cls._status(context.get("input_grid")),
            "output_grid_status": cls._status(context.get("output_grid")),
            "task_status": {
                "task_loaded": context.get("task_loaded") is True,
                "task_path_present": context.get("task_path") is not None,
                "task_id_present": context.get("task_id") is not None,
                "task_analysis_present": isinstance(task_analysis, dict),
            },
            "task_data_present": isinstance(train_example, dict),
            "train_example_status": {
                "present": isinstance(train_example, dict),
                "has_input": (
                    isinstance(train_example, dict)
                    and train_example.get("input") is not None
                ),
                "has_output": (
                    isinstance(train_example, dict)
                    and train_example.get("output") is not None
                ),
            },
            "context_key_count": len(context),
            "context_keys_preview": sorted(str(key) for key in context.keys())[:40],
        }

    @classmethod
    def validate(
        cls,
        context: dict[str, Any],
        stage_name: str,
        required_fields: tuple[str, ...] | None = None,
        repair: bool = True,
    ) -> dict[str, Any]:
        if not isinstance(context, dict):
            context = {}

        repairs = cls.repair_grids(context) if repair else []
        report = cls.trace(
            context=context,
            stage_name=stage_name,
            required_fields=required_fields,
            repairs=repairs,
        )
        context["runtime_context_integrity_report"] = report
        trace = context.setdefault("runtime_context_trace", [])
        if isinstance(trace, list):
            trace.append(report)
        return report

    @classmethod
    def require(
        cls,
        context: dict[str, Any],
        stage_name: str,
        required_fields: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        report = cls.validate(
            context=context,
            stage_name=stage_name,
            required_fields=required_fields,
            repair=True,
        )
        if not report["integrity_ok"]:
            raise ValueError(
                f"Missing runtime context fields before {stage_name}: "
                f"{report['missing_fields']}; "
                f"trace={report}"
            )
        return report


context_integrity_guard = ContextIntegrityGuard()


__all__ = [
    "ContextIntegrityGuard",
    "context_integrity_guard",
]
