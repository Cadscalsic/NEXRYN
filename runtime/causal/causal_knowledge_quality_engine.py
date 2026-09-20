"""Quality evaluation for existing NEXRYN causal knowledge."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


PRIMARY_MATURITY_STATES = (
    "DISCOVERED",
    "SUPPORTED",
    "VALIDATED",
    "GENERALIZED",
    "ESTABLISHED",
    "CANONICAL",
)

ALTERNATIVE_MATURITY_STATES = (
    "QUESTIONABLE",
    "WEAK",
    "CONTRADICTED",
    "DEPRECATED",
    "SUPERSEDED",
    "ARCHIVED",
)


@dataclass(frozen=True)
class CausalObject:
    causal_id: str
    cause: str
    effect: str
    mechanism: str | None
    conditions: tuple[str, ...]
    exceptions: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    support_count: int
    contradicting_evidence: tuple[str, ...]
    creation_episode: str | None
    last_validation: str | None
    confidence: float
    validation_status: str
    prediction_accuracy: float
    domains: tuple[str, ...]
    tasks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CausalQualityAssessment:
    causal_id: str
    maturity_state: str
    overall_causal_quality: float
    causal_confidence: float
    mechanism_score: float
    evidence_score: float
    generalization_score: float
    stability_score: float
    prediction_score: float
    consistency_score: float
    novelty_score: float
    explainability_score: float
    quality_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CausalKnowledgeQualityEngine:
    """Authoritative evaluator for produced causal knowledge quality."""

    system_name = "causal_knowledge_quality_engine"

    def build_report(
        self,
        causal_report: Mapping[str, Any] | None = None,
        *,
        causal_objects: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        report = causal_report if isinstance(causal_report, Mapping) else {}
        objects = self._causal_objects(report, causal_objects)
        consistency = self._consistency(objects)
        assessments = [
            self._assessment(causal_object, objects, consistency)
            for causal_object in objects
        ]
        maturity_counts = _counts(item["maturity_state"] for item in assessments)
        learning = self._learning(objects, assessments, consistency)
        generated = len(objects)
        validated = sum(
            1 for item in assessments
            if item["maturity_state"] in {
                "VALIDATED",
                "GENERALIZED",
                "ESTABLISHED",
                "CANONICAL",
            }
        )
        canonical = maturity_counts.get("CANONICAL", 0)
        return {
            "system": self.system_name,
            "CAUSAL_KNOWLEDGE_QUALITY_REPORT": True,
            "causal_quality_authority": True,
            "does_not_generate_causal_knowledge": True,
            "causal_object_model": [item.to_dict() for item in objects],
            "quality_assessments": assessments,
            "maturity_states": maturity_counts,
            "consistency_analysis": consistency,
            "generalization_analysis": self._generalization(objects, assessments),
            "learning_output": learning,
            "generated_causal_links": generated,
            "validated_causal_links": validated,
            "canonical_causal_links": canonical,
            "causal_quality": _average(
                item["overall_causal_quality"] for item in assessments
            ),
            "overall_causal_quality": _average(
                item["overall_causal_quality"] for item in assessments
            ),
            "average_causal_confidence": _average(
                item["causal_confidence"] for item in assessments
            ),
            "mechanism_completeness": _average(
                item["mechanism_score"] for item in assessments
            ),
            "generalization_quality": _average(
                item["generalization_score"] for item in assessments
            ),
            "prediction_accuracy": _average(
                item["prediction_score"] for item in assessments
            ),
            "contradicted_relationships": learning["contradicted_relationships"],
            "weak_relationships": learning["weak_patterns"],
            "strong_causal_patterns": learning["strong_causal_patterns"],
            "missing_mechanisms": learning["missing_mechanisms"],
            "high_value_causal_models": learning["high_value_causal_models"],
            "candidate_generalizations": learning["candidate_generalizations"],
            "reproducibility_signature": _digest({
                "objects": [
                    {
                        "causal_id": item.causal_id,
                        "cause": item.cause,
                        "effect": item.effect,
                        "support_count": item.support_count,
                        "confidence": item.confidence,
                    }
                    for item in objects
                ],
                "maturity": maturity_counts,
            })[:16],
        }

    def enrich_report(self, causal_report: Mapping[str, Any] | None) -> dict[str, Any]:
        report = dict(causal_report or {})
        quality = self.build_report(report)
        report["CAUSAL_KNOWLEDGE_QUALITY_REPORT"] = quality
        for key in (
            "generated_causal_links",
            "validated_causal_links",
            "canonical_causal_links",
            "causal_quality",
            "average_causal_confidence",
            "mechanism_completeness",
            "generalization_quality",
            "prediction_accuracy",
            "contradicted_relationships",
            "weak_relationships",
        ):
            report[key] = quality[key]
        return report

    def _causal_objects(
        self,
        report: Mapping[str, Any],
        causal_objects: Iterable[Mapping[str, Any]] | None,
    ) -> list[CausalObject]:
        raw = [
            item for item in causal_objects or []
            if isinstance(item, Mapping)
        ]
        if not raw:
            raw = [
                item for item in report.get("cause_effect_pairs", []) or []
                if isinstance(item, Mapping)
            ]
        contexts = [
            item for item in (
                report.get("generated_contexts")
                or report.get("causal_contexts")
                or []
            )
            if isinstance(item, Mapping)
        ]
        context_by_pair = {
            (
                str(context.get("cause") or context.get("cause_id") or ""),
                str(context.get("effect") or context.get("effect_id") or ""),
            ): context
            for context in contexts
        }
        objects = []
        for index, item in enumerate(raw):
            cause = str(item.get("cause") or item.get("cause_id") or "")
            effect = str(item.get("effect") or item.get("effect_id") or "")
            context = context_by_pair.get((cause, effect), {})
            mechanism = (
                item.get("mechanism")
                or item.get("mechanism_summary")
                or item.get("activation_reason")
                or context.get("mechanism")
                or context.get("reasoning_summary")
                or context.get("activation_reason")
            )
            evidence = _strings(
                item.get("supporting_evidence")
                or item.get("evidence")
                or context.get("evidence")
                or context.get("supporting_dependencies")
                or context.get("supporting_processes")
            )
            contradictions = _strings(
                item.get("contradicting_evidence")
                or item.get("contradictions")
                or context.get("contradictions")
            )
            support_count = int(max(
                _number(item.get("support_count")),
                len(evidence),
                _number(context.get("support_count")),
            ))
            confidence = _clamp(
                item.get("confidence")
                if item.get("confidence") is not None
                else context.get("confidence", report.get("average_confidence", 0.0))
            )
            prediction_accuracy = _clamp(
                item.get("prediction_accuracy")
                if item.get("prediction_accuracy") is not None
                else item.get("causal_simulation_accuracy")
                if item.get("causal_simulation_accuracy") is not None
                else context.get("simulation", {}).get(
                    "causal_simulation_accuracy",
                    report.get("causal_simulation_accuracy", 0.0),
                )
            )
            objects.append(CausalObject(
                causal_id=str(
                    item.get("causal_id")
                    or item.get("relation_id")
                    or f"causal:{_digest([cause, effect, index])[:12]}"
                ),
                cause=cause,
                effect=effect,
                mechanism=str(mechanism) if mechanism else None,
                conditions=tuple(_strings(item.get("conditions") or context.get("conditions"))),
                exceptions=tuple(_strings(item.get("exceptions") or context.get("exceptions"))),
                supporting_evidence=tuple(evidence),
                support_count=support_count,
                contradicting_evidence=tuple(contradictions),
                creation_episode=_optional_str(
                    item.get("creation_episode")
                    or context.get("creation_episode")
                    or report.get("execution_id")
                ),
                last_validation=_optional_str(
                    item.get("last_validation")
                    or item.get("validation_timestamp")
                    or report.get("timestamp")
                ),
                confidence=confidence,
                validation_status=str(
                    item.get("validation_status")
                    or context.get("validation_status")
                    or "unknown"
                ),
                prediction_accuracy=prediction_accuracy,
                domains=tuple(_strings(item.get("domains") or context.get("domains") or context.get("causal_family"))),
                tasks=tuple(_strings(item.get("tasks") or context.get("tasks") or context.get("task_id"))),
            ))
        return objects

    def _assessment(
        self,
        causal_object: CausalObject,
        objects: list[CausalObject],
        consistency: Mapping[str, Any],
    ) -> dict[str, Any]:
        mechanism_score = self._mechanism_score(causal_object)
        evidence_score = _clamp(
            min(causal_object.support_count, 6) / 6
            + (0.15 if causal_object.supporting_evidence else 0.0)
            - min(len(causal_object.contradicting_evidence), 4) * 0.12
        )
        generalization_score = _clamp(
            min(len(causal_object.domains), 3) / 3 * 0.35
            + min(len(causal_object.tasks), 4) / 4 * 0.25
            + min(causal_object.support_count, 5) / 5 * 0.25
            + (0.15 if causal_object.validation_status == "validated" else 0.0)
        )
        related = [
            item for item in objects
            if item.causal_id != causal_object.causal_id
            and item.cause == causal_object.cause
            and item.effect == causal_object.effect
        ]
        stability_score = _clamp(
            causal_object.confidence * 0.45
            + evidence_score * 0.25
            + min(len(related) + 1, 4) / 4 * 0.20
            - min(len(causal_object.contradicting_evidence), 4) * 0.10
        )
        consistency_score = self._consistency_score(causal_object, consistency)
        novelty_score = _clamp(
            1.0 / max(
                sum(
                    1 for item in objects
                    if item.cause == causal_object.cause
                    and item.effect == causal_object.effect
                ),
                1,
            )
        )
        explainability_score = _clamp(
            mechanism_score * 0.70
            + (0.15 if causal_object.conditions else 0.0)
            + (0.15 if causal_object.exceptions else 0.0)
        )
        overall = _clamp(
            causal_object.confidence * 0.17
            + evidence_score * 0.15
            + mechanism_score * 0.15
            + generalization_score * 0.12
            + causal_object.prediction_accuracy * 0.12
            + stability_score * 0.10
            + consistency_score * 0.10
            + explainability_score * 0.06
            + novelty_score * 0.03
        )
        reasons = []
        if mechanism_score < 0.55:
            reasons.append("missing_or_incomplete_mechanism")
        if evidence_score < 0.45:
            reasons.append("weak_evidence")
        if causal_object.contradicting_evidence:
            reasons.append("contradictory_observations_present")
        if causal_object.prediction_accuracy < 0.45:
            reasons.append("low_prediction_accuracy")
        if generalization_score >= 0.65:
            reasons.append("generalizes_across_observations")
        maturity = self._maturity(
            causal_object,
            overall,
            mechanism_score,
            evidence_score,
            generalization_score,
            consistency_score,
        )
        return CausalQualityAssessment(
            causal_id=causal_object.causal_id,
            maturity_state=maturity,
            overall_causal_quality=overall,
            causal_confidence=causal_object.confidence,
            mechanism_score=mechanism_score,
            evidence_score=evidence_score,
            generalization_score=generalization_score,
            stability_score=stability_score,
            prediction_score=causal_object.prediction_accuracy,
            consistency_score=consistency_score,
            novelty_score=novelty_score,
            explainability_score=explainability_score,
            quality_reasons=tuple(reasons or ["causal_quality_supported"]),
        ).to_dict()

    def _mechanism_score(self, causal_object: CausalObject) -> float:
        mechanism = causal_object.mechanism or ""
        has_why = bool(mechanism.strip())
        has_how = any(
            token in mechanism.lower()
            for token in ("because", "through", "via", "leads", "causes", "propagat")
        )
        has_conditions = bool(causal_object.conditions)
        has_failures = bool(causal_object.exceptions)
        return _clamp(
            (0.40 if has_why else 0.0)
            + (0.25 if has_how else 0.0)
            + (0.20 if has_conditions else 0.0)
            + (0.15 if has_failures else 0.0)
        )

    def _maturity(
        self,
        causal_object: CausalObject,
        overall: float,
        mechanism: float,
        evidence: float,
        generalization: float,
        consistency: float,
    ) -> str:
        if causal_object.contradicting_evidence or consistency < 0.35:
            return "CONTRADICTED"
        if overall < 0.35 or evidence < 0.25:
            return "WEAK"
        if mechanism < 0.45:
            return "QUESTIONABLE"
        if overall >= 0.88 and generalization >= 0.72 and mechanism >= 0.75:
            return "CANONICAL"
        if overall >= 0.78 and evidence >= 0.65 and consistency >= 0.70:
            return "ESTABLISHED"
        if generalization >= 0.62 and overall >= 0.62:
            return "GENERALIZED"
        if causal_object.validation_status == "validated" or overall >= 0.56:
            return "VALIDATED"
        if evidence >= 0.35 or causal_object.support_count > 0:
            return "SUPPORTED"
        return "DISCOVERED"

    def _consistency(self, objects: list[CausalObject]) -> dict[str, Any]:
        by_cause: dict[str, set[str]] = {}
        by_effect: dict[str, set[str]] = {}
        edges = set()
        contradictions = []
        weak = []
        missing_mechanisms = []
        for item in objects:
            by_cause.setdefault(item.cause, set()).add(item.effect)
            by_effect.setdefault(item.effect, set()).add(item.cause)
            edges.add((item.cause, item.effect))
            if item.contradicting_evidence:
                contradictions.append(item.causal_id)
            if item.support_count <= 1 or item.confidence < 0.45:
                weak.append(item.causal_id)
            if not item.mechanism:
                missing_mechanisms.append(item.causal_id)
        conflicting_causes = {
            effect: sorted(causes)
            for effect, causes in by_effect.items()
            if len(causes) > 1
        }
        conflicting_effects = {
            cause: sorted(effects)
            for cause, effects in by_cause.items()
            if len(effects) > 1
        }
        circular = sorted(
            [source, target]
            for source, target in edges
            if (target, source) in edges
        )
        unstable = sorted({
            item.causal_id
            for item in objects
            if item.confidence < 0.5 and item.support_count > 1
        })
        return {
            "conflicting_causes": conflicting_causes,
            "conflicting_effects": conflicting_effects,
            "circular_causality": circular,
            "weak_evidence": weak,
            "contradictory_observations": contradictions,
            "missing_mechanisms": missing_mechanisms,
            "unstable_causal_behaviour": unstable,
            "has_conflicts": bool(
                conflicting_causes
                or conflicting_effects
                or circular
                or contradictions
            ),
        }

    def _consistency_score(
        self,
        causal_object: CausalObject,
        consistency: Mapping[str, Any],
    ) -> float:
        score = 1.0
        if causal_object.causal_id in consistency.get("contradictory_observations", []):
            score -= 0.45
        if causal_object.causal_id in consistency.get("weak_evidence", []):
            score -= 0.20
        if causal_object.causal_id in consistency.get("missing_mechanisms", []):
            score -= 0.15
        for source, target in consistency.get("circular_causality", []):
            if causal_object.cause == source and causal_object.effect == target:
                score -= 0.35
        return _clamp(score)

    def _generalization(
        self,
        objects: list[CausalObject],
        assessments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "cross_task_validity": _average(
                min(len(item.tasks), 4) / 4 for item in objects
            ),
            "cross_domain_validity": _average(
                min(len(item.domains), 3) / 3 for item in objects
            ),
            "repeated_confirmation": _average(
                min(item.support_count, 6) / 6 for item in objects
            ),
            "transfer_success": _average(
                item["generalization_score"] for item in assessments
            ),
            "long_term_stability": _average(
                item["stability_score"] for item in assessments
            ),
        }

    def _learning(
        self,
        objects: list[CausalObject],
        assessments: list[dict[str, Any]],
        consistency: Mapping[str, Any],
    ) -> dict[str, Any]:
        by_id = {item.causal_id: item for item in objects}
        strong = [
            item for item in assessments
            if item["maturity_state"] in {"ESTABLISHED", "CANONICAL"}
        ]
        weak = [
            item for item in assessments
            if item["maturity_state"] in {"WEAK", "QUESTIONABLE"}
        ]
        generalizations = [
            item for item in assessments
            if item["generalization_score"] >= 0.62
        ]
        return {
            "strong_causal_patterns": [
                self._pattern(by_id[item["causal_id"]]) for item in strong
            ],
            "weak_patterns": [
                item["causal_id"] for item in weak
            ],
            "missing_mechanisms": list(consistency["missing_mechanisms"]),
            "contradicted_relationships": list(
                consistency["contradictory_observations"]
            ),
            "high_value_causal_models": [
                item["causal_id"]
                for item in sorted(
                    assessments,
                    key=lambda value: value["overall_causal_quality"],
                    reverse=True,
                )[:10]
            ],
            "candidate_generalizations": [
                self._pattern(by_id[item["causal_id"]])
                for item in generalizations
            ],
        }

    def _pattern(self, causal_object: CausalObject) -> str:
        return f"{causal_object.cause}->{causal_object.effect}"


def _strings(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, Mapping):
        refs = []
        for key in ("id", "evidence_id", "source", "dependency_source", "process_source", "truth_source"):
            if value.get(key):
                refs.append(str(value[key]))
        if refs:
            return refs
        return [str(key) for key in sorted(value.keys())]
    if isinstance(value, (list, tuple, set)):
        output = []
        for item in value:
            output.extend(_strings(item))
        return list(dict.fromkeys(output))
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _counts(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


def _average(values: Iterable[float]) -> float:
    items = [float(value or 0.0) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: Any) -> float:
    return round(max(0.0, min(1.0, _number(value))), 4)


def _optional_str(value: Any) -> str | None:
    return str(value) if value is not None and value != "" else None


def _digest(value: Any) -> str:
    return hashlib.sha1(
        json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


causal_knowledge_quality_engine = CausalKnowledgeQualityEngine()


__all__ = [
    "ALTERNATIVE_MATURITY_STATES",
    "PRIMARY_MATURITY_STATES",
    "CausalKnowledgeQualityEngine",
    "CausalObject",
    "CausalQualityAssessment",
    "causal_knowledge_quality_engine",
]
