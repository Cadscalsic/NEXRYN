"""Program fragment memory facade over the existing meta-supervisor store."""

from __future__ import annotations

from typing import Any, Mapping


class ProgramFragmentMemory:
    def load(self) -> list[dict[str, Any]]:
        try:
            from runtime.meta.supervisor.program_memory import ProgramMemory

            records = ProgramMemory().records
        except Exception:
            records = []
        fragments = []
        for record in records:
            if getattr(record, "stale", False):
                continue
            if getattr(record, "validation_state", "") not in {"validated", "stable"}:
                continue
            if not getattr(record, "integrity_verified", False):
                continue
            program = getattr(record, "program", {}) or {}
            operation_sequence = getattr(record, "operation_sequence", []) or []
            metadata = getattr(record, "metadata", {}) or {}
            fragments.append({
                "program_id": getattr(record, "program_id", ""),
                "task_signature_id": getattr(record, "task_signature_id", ""),
                "program": dict(program) if isinstance(program, Mapping) else {},
                "operation_sequence": list(operation_sequence),
                "metadata": dict(metadata) if isinstance(metadata, Mapping) else {},
                "confidence": float(getattr(record, "match_confidence", 0.0) or 0.0),
                "validation_state": getattr(record, "validation_state", ""),
                "integrity_verified": getattr(record, "integrity_verified", False),
            })
        return fragments
