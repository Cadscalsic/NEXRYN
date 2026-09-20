"""Memory for reusable dynamic concept simulations."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Mapping


class DynamicConceptMemory:
    """Store successful and failed dynamic simulations by concept signature."""

    system_name = "dynamic_concept_memory"

    def __init__(self):
        self.successful_simulations = []
        self.failed_simulations = []
        self.signature_index = {}
        self.dynamic_process_patterns = {}
        self.state_transition_patterns = {}

    def build_signature(self, model: Mapping[str, Any] | None = None) -> str:
        model = model if isinstance(model, Mapping) else {}
        return "|".join([
            str(model.get("concept_family", "unknown")),
            str(model.get("dynamic_concept", "unknown")),
            ",".join(str(item) for item in model.get("state_transitions", []) or []),
        ])

    def remember(
        self,
        model: Mapping[str, Any],
        simulation_report: Mapping[str, Any] | None = None,
        success: bool | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        simulation_report = (
            simulation_report
            if isinstance(simulation_report, Mapping)
            else {}
        )
        accuracy = float(simulation_report.get("simulation_accuracy", 0.0) or 0.0)
        success = bool(accuracy >= 0.80) if success is None else bool(success)
        signature = self.build_signature(model)
        record = {
            "signature": signature,
            "dynamic_model": copy.deepcopy(dict(model)),
            "simulation_report": copy.deepcopy(dict(simulation_report)),
            "success": success,
            "evidence": copy.deepcopy(dict(evidence or {})),
            "timestamp": str(datetime.utcnow()),
        }
        target = self.successful_simulations if success else self.failed_simulations
        target.append(record)
        self.signature_index[signature] = record
        family = str(model.get("concept_family", "unknown"))
        self.dynamic_process_patterns.setdefault(family, [])
        self.dynamic_process_patterns[family].append(signature)
        self.state_transition_patterns[signature] = list(
            model.get("state_transitions", []) or []
        )
        return record

    def retrieve_successful(
        self,
        concept_family: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not concept_family:
            return [
                copy.deepcopy(record)
                for record in self.successful_simulations[-limit:]
            ]
        matches = [
            record
            for record in self.successful_simulations
            if record.get("dynamic_model", {}).get("concept_family") == concept_family
        ]
        return [copy.deepcopy(record) for record in matches[-limit:]]

    def build_report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "successful_simulations": len(self.successful_simulations),
            "failed_simulations": len(self.failed_simulations),
            "known_signatures": len(self.signature_index),
            "dynamic_process_patterns": dict(self.dynamic_process_patterns),
            "state_transition_patterns": dict(self.state_transition_patterns),
        }


dynamic_concept_memory = DynamicConceptMemory()


__all__ = ["DynamicConceptMemory", "dynamic_concept_memory"]
