"""Runtime signal ledger for adaptive resource governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class RuntimeSignalType(str, Enum):
    EXACT_SUCCESS = "EXACT_SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    RECOVERABLE_FAILURE = "RECOVERABLE_FAILURE"
    UNRECOVERABLE_FAILURE = "UNRECOVERABLE_FAILURE"
    CONFIDENCE_DROP = "CONFIDENCE_DROP"
    CONFIDENCE_STABILIZED = "CONFIDENCE_STABILIZED"
    RESIDUAL_DETECTED = "RESIDUAL_DETECTED"
    LOCALIZED_RESIDUAL = "LOCALIZED_RESIDUAL"
    RESIDUAL_COUNT_INCREASED = "RESIDUAL_COUNT_INCREASED"
    RESIDUAL_COUNT_DECREASED = "RESIDUAL_COUNT_DECREASED"
    COMPONENT_COUNT_CHANGED = "COMPONENT_COUNT_CHANGED"
    TOPOLOGY_CHANGE_DETECTED = "TOPOLOGY_CHANGE_DETECTED"
    HOLE_CHANGE_DETECTED = "HOLE_CHANGE_DETECTED"
    SYMMETRY_CHANGE_DETECTED = "SYMMETRY_CHANGE_DETECTED"
    SPATIAL_RELATION_DETECTED = "SPATIAL_RELATION_DETECTED"
    ROTATION_SIGNAL_DETECTED = "ROTATION_SIGNAL_DETECTED"
    REFLECTION_SIGNAL_DETECTED = "REFLECTION_SIGNAL_DETECTED"
    SCALING_SIGNAL_DETECTED = "SCALING_SIGNAL_DETECTED"
    PATH_SIGNAL_DETECTED = "PATH_SIGNAL_DETECTED"
    GRAVITY_SIGNAL_DETECTED = "GRAVITY_SIGNAL_DETECTED"
    COLOR_MAPPING_SIGNAL_DETECTED = "COLOR_MAPPING_SIGNAL_DETECTED"
    EXECUTABLE_CONCEPT_DETECTED = "EXECUTABLE_CONCEPT_DETECTED"
    UNSUPPORTED_CONCEPT_DETECTED = "UNSUPPORTED_CONCEPT_DETECTED"
    COMPILER_REJECTED = "COMPILER_REJECTED"
    COMPILER_CANDIDATE_GENERATED = "COMPILER_CANDIDATE_GENERATED"
    CANDIDATE_COUNT_LOW = "CANDIDATE_COUNT_LOW"
    CANDIDATE_COUNT_HIGH = "CANDIDATE_COUNT_HIGH"
    SINGLE_SOURCE_DOMINANCE = "SINGLE_SOURCE_DOMINANCE"
    CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
    DEPENDENCY_GAP_DETECTED = "DEPENDENCY_GAP_DETECTED"
    ROUTING_OVERLOAD = "ROUTING_OVERLOAD"
    LAYER_FAILED = "LAYER_FAILED"
    LAYER_NO_VALUE_PRODUCED = "LAYER_NO_VALUE_PRODUCED"
    LAYER_VALUE_PRODUCED = "LAYER_VALUE_PRODUCED"
    TIME_PRESSURE = "TIME_PRESSURE"
    MEMORY_PRESSURE = "MEMORY_PRESSURE"


class RuntimeSignalSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RuntimeSignal:
    signal_id: str
    execution_id: str
    task_id: str
    signal_type: str
    source_layer: str
    severity: str = RuntimeSignalSeverity.LOW.value
    confidence: float = 1.0
    payload: Mapping[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: str(datetime.utcnow()))
    consumed: bool = False
    activation_effect: str | None = None

    @classmethod
    def create(
        cls,
        execution_id: str,
        task_id: str = "unknown_task",
        signal_type: str | RuntimeSignalType = RuntimeSignalType.PARTIAL_SUCCESS,
        source_layer: str = "runtime",
        severity: str | RuntimeSignalSeverity = RuntimeSignalSeverity.LOW,
        confidence: float = 1.0,
        payload: Mapping[str, Any] | None = None,
        signal_id: str | None = None,
    ) -> "RuntimeSignal":
        signal_value = signal_type.value if isinstance(signal_type, RuntimeSignalType) else str(signal_type)
        severity_value = severity.value if isinstance(severity, RuntimeSignalSeverity) else str(severity)
        return cls(
            signal_id=signal_id or f"signal-{uuid4()}",
            execution_id=str(execution_id or ""),
            task_id=str(task_id or "unknown_task"),
            signal_type=signal_value,
            source_layer=str(source_layer or "runtime"),
            severity=severity_value.upper(),
            confidence=max(0.0, min(1.0, float(confidence))),
            payload=dict(payload or {}),
        )

    def mark_consumed(self, activation_effect: str | None = None) -> None:
        self.consumed = True
        self.activation_effect = activation_effect

    def as_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "signal_type": self.signal_type,
            "source_layer": self.source_layer,
            "severity": self.severity,
            "confidence": self.confidence,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
            "consumed": self.consumed,
            "activation_effect": self.activation_effect,
        }


class RuntimeSignalMonitor:
    def __init__(self):
        self._signals: dict[str, RuntimeSignal] = {}
        self._signal_order: list[str] = []

    def publish(self, signal: RuntimeSignal) -> RuntimeSignal:
        self._signals[signal.signal_id] = signal
        self._signal_order.append(signal.signal_id)
        return signal

    def consume(self, signal_id: str, activation_effect: str | None = None) -> RuntimeSignal | None:
        signal = self._signals.get(str(signal_id))
        if signal is not None:
            signal.mark_consumed(activation_effect)
        return signal

    def get(self, signal_id: str) -> RuntimeSignal | None:
        return self._signals.get(str(signal_id))

    def all_signals(self) -> list[RuntimeSignal]:
        return [self._signals[item] for item in self._signal_order if item in self._signals]

    def repeated_count(self, signal_type: str) -> int:
        return sum(1 for signal in self._signals.values() if signal.signal_type == str(signal_type))


__all__ = [
    "RuntimeSignal",
    "RuntimeSignalMonitor",
    "RuntimeSignalSeverity",
    "RuntimeSignalType",
]
