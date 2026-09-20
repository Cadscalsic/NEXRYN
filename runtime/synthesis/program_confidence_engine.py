"""Post-synthesis confidence evaluation for already generated programs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from typing import Any, Iterable, Mapping


CONFIDENCE_LEVELS = (
    "UNKNOWN",
    "VERY_LOW",
    "LOW",
    "MEDIUM",
    "HIGH",
    "VERY_HIGH",
    "CANONICAL",
)

CONFIDENCE_COMPONENTS = (
    "structural_confidence",
    "reasoning_confidence",
    "evidence_confidence",
    "execution_confidence",
    "constraint_confidence",
    "transfer_confidence",
    "historical_confidence",
    "generalization_confidence",
)

COMPONENT_WEIGHTS = {
    "structural_confidence": 0.16,
    "reasoning_confidence": 0.14,
    "evidence_confidence": 0.14,
    "execution_confidence": 0.14,
    "constraint_confidence": 0.12,
    "transfer_confidence": 0.10,
    "historical_confidence": 0.10,
    "generalization_confidence": 0.10,
}


@dataclass(frozen=True)
class ProgramConfidenceAssessment:
    program_id: str
    confidence: float
    confidence_level: str
    confidence_components: dict[str, float]
    confidence_reason: str
    validation_status: str
    stability_score: float
    generalization_score: float
    transfer_score: float
    reuse_score: float
    validation_errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProgramConfidenceEngine:
    """Authoritative confidence source for synthesized program objects."""

    system_name = "program_confidence_engine"

    def evaluate_program(
        self,
        program: Mapping[str, Any],
        *,
        episode_history: Iterable[Mapping[str, Any]] | None = None,
        reuse_history: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = program if isinstance(program, Mapping) else {}
        program_id = str(data.get("program_id") or f"program:{_signature(data)}")
        components = self._components(
            data,
            episode_history=list(episode_history or []),
            reuse_history=reuse_history if isinstance(reuse_history, Mapping) else {},
        )
        errors = self._validate_components(components)
        confidence = self._weighted_confidence(components) if not errors else 0.0
        confidence_errors = self._validate_confidence(confidence)
        errors.extend(confidence_errors)
        validation_status = (
            "VALIDATED"
            if not errors and _accepted(data) and confidence >= 0.35
            else "REJECTED"
            if errors
            else "SUPPORTED"
        )
        assessment = ProgramConfidenceAssessment(
            program_id=program_id,
            confidence=round(confidence, 4),
            confidence_level=self._level(confidence) if not errors else "UNKNOWN",
            confidence_components={key: round(value, 4) for key, value in components.items()},
            confidence_reason=self._reason(components, confidence, errors),
            validation_status=validation_status,
            stability_score=round(self._stability_score(data, components), 4),
            generalization_score=round(components["generalization_confidence"], 4),
            transfer_score=round(components["transfer_confidence"], 4),
            reuse_score=round(components["historical_confidence"], 4),
            validation_errors=errors,
        )
        return assessment.as_dict()

    def annotate_programs(
        self,
        programs: Iterable[Mapping[str, Any]],
        *,
        episode_history: Iterable[Mapping[str, Any]] | None = None,
        reuse_history: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        annotated = []
        for program in programs:
            if not isinstance(program, Mapping):
                continue
            assessment = self.evaluate_program(
                program,
                episode_history=episode_history,
                reuse_history=reuse_history,
            )
            annotated.append({**dict(program), **assessment})
        return annotated

    def build_report(
        self,
        programs: Iterable[Mapping[str, Any]],
        *,
        episode_history: Iterable[Mapping[str, Any]] | None = None,
        reuse_history: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        annotated = self.annotate_programs(
            programs,
            episode_history=episode_history,
            reuse_history=reuse_history,
        )
        confidences = [item["confidence"] for item in annotated]
        failures = [
            {
                "program_id": item["program_id"],
                "validation_errors": list(item.get("validation_errors", [])),
            }
            for item in annotated
            if item.get("validation_errors")
        ]
        return {
            "system": self.system_name,
            "PROGRAM_CONFIDENCE_REPORT": True,
            "program_confidence_authority": True,
            "programs_evaluated": len(annotated),
            "program_confidence_assessments": annotated,
            "average_program_confidence": round(
                sum(confidences) / max(len(confidences), 1),
                4,
            ),
            "highest_program_confidence": round(max(confidences or [0.0]), 4),
            "lowest_program_confidence": round(min(confidences or [0.0]), 4),
            "confidence_distribution": self._distribution(annotated),
            "validated_program_count": sum(
                1 for item in annotated
                if item.get("validation_status") in {"VALIDATED", "SUPPORTED"}
            ),
            "low_confidence_program_count": sum(
                1 for item in annotated
                if item.get("confidence_level") in {"VERY_LOW", "LOW"}
            ),
            "high_confidence_program_count": sum(
                1 for item in annotated
                if item.get("confidence_level") in {"HIGH", "VERY_HIGH", "CANONICAL"}
            ),
            "confidence_generation_failures": failures,
            "confidence_generation_success": bool(annotated) and not failures,
            "confidence_components": list(CONFIDENCE_COMPONENTS),
            "confidence_levels": list(CONFIDENCE_LEVELS),
        }

    def _components(
        self,
        program: Mapping[str, Any],
        *,
        episode_history: list[Mapping[str, Any]],
        reuse_history: Mapping[str, Any],
    ) -> dict[str, float]:
        validation = (
            program.get("validation_results")
            if isinstance(program.get("validation_results"), Mapping)
            else {}
        )
        strategy = (
            program.get("execution_strategy")
            if isinstance(program.get("execution_strategy"), Mapping)
            else {}
        )
        steps = strategy.get("steps") if isinstance(strategy.get("steps"), list) else []
        required_concepts = _as_list(program.get("required_concepts"))
        transformations = _as_list(program.get("required_transformations"))
        constraints = _as_list(program.get("required_constraints"))
        execution_success = _bool_score(
            validation.get("execution_success"),
            default=_number(validation.get("correctness"), 0.5),
        )
        reuse_count = _number(program.get("reuse_count"), 0.0)
        if reuse_count <= 0.0:
            reuse_count = _number(reuse_history.get(str(program.get("program_id"))), 0.0)
        episode_success = _episode_success(program, episode_history)
        return {
            "structural_confidence": min(
                1.0,
                0.25
                + (0.20 if program.get("program_id") else 0.0)
                + (0.20 if steps else 0.0)
                + (0.15 if required_concepts else 0.0)
                + (0.10 if transformations else 0.0)
                + (0.10 if program.get("program_signature") else 0.0),
            ),
            "reasoning_confidence": _average([
                _number(validation.get("consistency"), 0.5),
                _number(validation.get("concept_alignment"), 0.5),
                _number(program.get("utility"), 0.5),
            ]),
            "evidence_confidence": _average([
                _number(validation.get("truth_alignment"), 0.5),
                min(1.0, len(required_concepts) / 4),
                _number(validation.get("completeness"), 0.5),
            ]),
            "execution_confidence": execution_success,
            "constraint_confidence": _average([
                _number(validation.get("constraint_satisfaction"), 0.5),
                0.75 if constraints else 0.55,
            ]),
            "transfer_confidence": _average([
                _number(program.get("transfer_score"), 0.0),
                1.0 if program.get("lifecycle") in {"GENERALIZED", "STABLE"} else 0.45,
                episode_success,
            ]),
            "historical_confidence": max(
                _number(program.get("historical_success"), 0.0),
                min(1.0, reuse_count / 5),
                episode_success,
            ),
            "generalization_confidence": _number(
                program.get("generalization_score"),
                _number(validation.get("generalization"), 0.5),
            ),
        }

    def _weighted_confidence(self, components: Mapping[str, float]) -> float:
        return round(
            sum(
                _number(components.get(component), 0.0) * weight
                for component, weight in COMPONENT_WEIGHTS.items()
            ),
            4,
        )

    def _validate_components(self, components: Mapping[str, Any]) -> list[str]:
        errors = []
        for component in CONFIDENCE_COMPONENTS:
            if component not in components:
                errors.append(f"{component}_missing")
                continue
            errors.extend(
                f"{component}_{error}"
                for error in self._validate_confidence(components[component])
            )
        return errors

    def _validate_confidence(self, value: Any) -> list[str]:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return ["not_numeric"]
        if math.isnan(float(value)):
            return ["nan"]
        if math.isinf(float(value)):
            return ["infinite"]
        if float(value) < 0.0:
            return ["below_zero"]
        if float(value) > 1.0:
            return ["above_one"]
        return []

    def _level(self, confidence: float) -> str:
        if confidence <= 0.0:
            return "UNKNOWN"
        if confidence < 0.2:
            return "VERY_LOW"
        if confidence < 0.4:
            return "LOW"
        if confidence < 0.6:
            return "MEDIUM"
        if confidence < 0.78:
            return "HIGH"
        if confidence < 0.92:
            return "VERY_HIGH"
        return "CANONICAL"

    def _reason(
        self,
        components: Mapping[str, float],
        confidence: float,
        errors: list[str],
    ) -> str:
        if errors:
            return f"confidence rejected: {', '.join(errors)}"
        strongest = max(components, key=lambda key: components[key])
        weakest = min(components, key=lambda key: components[key])
        return (
            f"confidence {round(confidence, 4)} from weighted components; "
            f"strongest={strongest}, weakest={weakest}"
        )

    def _stability_score(
        self,
        program: Mapping[str, Any],
        components: Mapping[str, float],
    ) -> float:
        lifecycle = str(program.get("lifecycle") or "")
        lifecycle_bonus = 0.15 if lifecycle in {"STABLE", "REUSED", "GENERALIZED"} else 0.0
        return min(
            1.0,
            _average([
                components["historical_confidence"],
                components["constraint_confidence"],
                components["reasoning_confidence"],
            ]) + lifecycle_bonus,
        )

    def _distribution(self, annotated: list[Mapping[str, Any]]) -> dict[str, int]:
        distribution = {level: 0 for level in CONFIDENCE_LEVELS}
        for item in annotated:
            level = str(item.get("confidence_level") or "UNKNOWN")
            distribution[level if level in distribution else "UNKNOWN"] += 1
        return distribution


def _accepted(program: Mapping[str, Any]) -> bool:
    validation = program.get("validation_results")
    if isinstance(validation, Mapping) and "accepted" in validation:
        return bool(validation.get("accepted"))
    return str(program.get("lifecycle") or "") in {
        "VALIDATED",
        "PROMOTED",
        "REUSED",
        "GENERALIZED",
        "STABLE",
    }


def _episode_success(
    program: Mapping[str, Any],
    episode_history: list[Mapping[str, Any]],
) -> float:
    program_id = str(program.get("program_id") or "")
    if not program_id or not episode_history:
        return 0.0
    matches = [
        item for item in episode_history
        if program_id in json.dumps(item, sort_keys=True, default=str)
    ]
    if not matches:
        return 0.0
    return _average([
        _number(item.get("success"), 1.0 if item.get("status") == "SUCCESS" else 0.5)
        for item in matches
    ])


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    return []


def _average(values: Iterable[float]) -> float:
    items = [float(item) for item in values if isinstance(item, (int, float))]
    return round(sum(items) / max(len(items), 1), 4) if items else 0.0


def _bool_score(value: Any, default: float = 0.5) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return _number(value, default)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or isinstance(value, bool):
            return default
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return max(0.0, min(1.0, number))


def _signature(value: Any) -> str:
    return hashlib.sha1(
        json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]


program_confidence_engine = ProgramConfidenceEngine()


__all__ = [
    "CONFIDENCE_COMPONENTS",
    "CONFIDENCE_LEVELS",
    "ProgramConfidenceAssessment",
    "ProgramConfidenceEngine",
    "program_confidence_engine",
]
