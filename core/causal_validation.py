import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4

from core.epistemic_models import clamp


class CausalValidationState(str, Enum):
    DISCOVERED = "DISCOVERED"
    UNDER_REVIEW = "UNDER_REVIEW"
    PARTIALLY_VALIDATED = "PARTIALLY_VALIDATED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


def _stable_id(source_concept, target_concept):
    return (
        "causal:"
        f"{str(source_concept).strip()}->"
        f"{str(target_concept).strip()}"
    )


@dataclass
class CausalEvidence:
    evidence_id: str
    originating_task: str
    context_signature: str
    support_strength: float = 0.0
    contradiction_strength: float = 0.0

    def __post_init__(self):
        self.evidence_id = self.evidence_id or f"evidence:{uuid4().hex}"
        self.originating_task = str(self.originating_task or "unknown")
        self.context_signature = str(self.context_signature or "unknown")
        self.support_strength = clamp(self.support_strength)
        self.contradiction_strength = clamp(self.contradiction_strength)

    def supports(self):
        return (
            self.support_strength > self.contradiction_strength
            and self.support_strength >= 0.50
        )

    def contradicts(self):
        return (
            self.contradiction_strength >= self.support_strength
            and self.contradiction_strength >= 0.30
        )

    def as_dict(self):
        return asdict(self)


@dataclass
class CausalHypothesis:
    hypothesis_id: str
    source_concept: str
    target_concept: str
    evidence_count: int = 0
    confidence: float = 0.0
    validation_state: str = CausalValidationState.DISCOVERED.value
    contradiction_score: float = 0.0
    supporting_tasks: list = field(default_factory=list)
    rejecting_tasks: list = field(default_factory=list)

    def __post_init__(self):
        self.hypothesis_id = self.hypothesis_id or _stable_id(
            self.source_concept,
            self.target_concept,
        )
        self.source_concept = str(self.source_concept)
        self.target_concept = str(self.target_concept)
        self.confidence = clamp(self.confidence)
        self.contradiction_score = clamp(self.contradiction_score)
        self.supporting_tasks = sorted(set(self.supporting_tasks or []))
        self.rejecting_tasks = sorted(set(self.rejecting_tasks or []))
        valid_states = {item.value for item in CausalValidationState}
        if self.validation_state not in valid_states:
            raise ValueError(
                f"invalid causal validation state: {self.validation_state}"
            )

    def as_dict(self):
        return asdict(self)


class CausalValidationEngine:
    """Validates proposed causal links before they influence truth."""

    SPURIOUS_RELATIONSHIP = "SPURIOUS_RELATIONSHIP"
    VALID_CAUSAL_RELATIONSHIP = "VALID_CAUSAL_RELATIONSHIP"

    def __init__(
        self,
        storage_path=None,
        minimum_validation_score=0.75,
        minimum_supporting_tasks=3,
    ):
        self.storage_path = Path(
            storage_path
            if storage_path is not None
            else Path("memory") / "causal_ledger.json"
        )
        self.minimum_validation_score = clamp(minimum_validation_score)
        self.minimum_supporting_tasks = minimum_supporting_tasks
        self.hypotheses = {}
        self.confidence_history = {}
        self.contradiction_history = {}
        self.recovery_history = {}
        self.last_persistence_error = None
        self.load()

    def load(self):
        if self.storage_path is None or not self.storage_path.exists():
            return 0
        try:
            with self.storage_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            self.hypotheses = {
                item["hypothesis_id"]: item
                for item in payload.get("hypotheses", [])
            }
            self.confidence_history = dict(
                payload.get("confidence_history", {})
            )
            self.contradiction_history = dict(
                payload.get("contradiction_history", {})
            )
            self.recovery_history = dict(payload.get("recovery_history", {}))
            self.last_persistence_error = None
            return len(self.hypotheses)
        except (
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            self.last_persistence_error = repr(error)
            return 0

    def _persist(self):
        if self.storage_path is None:
            return False
        temporary_path = self.storage_path.with_suffix(
            f"{self.storage_path.suffix}.tmp"
        )
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema_version": 1,
                "hypotheses": list(self.hypotheses.values()),
                "validated_hypotheses": [
                    item
                    for item in self.hypotheses.values()
                    if item.get("validation_state")
                    == CausalValidationState.VALIDATED.value
                ],
                "rejected_hypotheses": [
                    item
                    for item in self.hypotheses.values()
                    if item.get("validation_state")
                    == CausalValidationState.REJECTED.value
                ],
                "confidence_history": self.confidence_history,
                "contradiction_history": self.contradiction_history,
                "recovery_history": self.recovery_history,
            }
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2, ensure_ascii=True)
            temporary_path.replace(self.storage_path)
            self.last_persistence_error = None
            return True
        except (OSError, TypeError, ValueError) as error:
            self.last_persistence_error = repr(error)
            return False

    def _evidence_from_dict(self, item):
        if isinstance(item, CausalEvidence):
            return item
        if hasattr(item, "as_dict"):
            item = item.as_dict()
        item = dict(item or {})
        metadata = item.get("metadata", {})
        return CausalEvidence(
            evidence_id=item.get("evidence_id", item.get("source", "")),
            originating_task=item.get(
                "originating_task",
                item.get(
                    "task_id",
                    item.get(
                        "task",
                        metadata.get(
                            "task_id",
                            item.get("source", "unknown"),
                        ),
                    ),
                ),
            ),
            context_signature=item.get(
                "context_signature",
                metadata.get(
                    "context_signature",
                    metadata.get("task_context", "runtime"),
                ),
            ),
            support_strength=item.get(
                "support_strength",
                item.get("support_score", item.get("reliability", 0.0)),
            ),
            contradiction_strength=item.get(
                "contradiction_strength",
                item.get("contradiction_score", 0.0),
            ),
        )

    def evaluate_evidence(self, evidence):
        evidence = self._evidence_from_dict(evidence)
        return {
            **evidence.as_dict(),
            "supports": evidence.supports(),
            "contradicts": evidence.contradicts(),
        }

    def _normalize_hypothesis(self, hypothesis):
        if isinstance(hypothesis, CausalHypothesis):
            return hypothesis
        hypothesis = dict(hypothesis or {})
        return CausalHypothesis(
            hypothesis_id=hypothesis.get(
                "hypothesis_id",
                _stable_id(
                    hypothesis.get("source_concept", ""),
                    hypothesis.get("target_concept", ""),
                ),
            ),
            source_concept=hypothesis.get("source_concept", ""),
            target_concept=hypothesis.get("target_concept", ""),
            evidence_count=hypothesis.get("evidence_count", 0),
            confidence=hypothesis.get("confidence", 0.0),
            validation_state=hypothesis.get(
                "validation_state",
                CausalValidationState.DISCOVERED.value,
            ),
            contradiction_score=hypothesis.get("contradiction_score", 0.0),
            supporting_tasks=hypothesis.get("supporting_tasks", []),
            rejecting_tasks=hypothesis.get("rejecting_tasks", []),
        )

    def _relation_observed(self, hypothesis, causal_graph):
        if causal_graph is None:
            return False
        export = (
            causal_graph.export_graph()
            if hasattr(causal_graph, "export_graph")
            else causal_graph
        )
        relations = export.get("relations", export.get("edges", []))
        expected_source = f"concept:{hypothesis.source_concept}"
        expected_target = f"concept:{hypothesis.target_concept}"
        expected_truth_target = f"truth:{hypothesis.target_concept}"
        expected_source_truth = f"truth:{hypothesis.source_concept}"
        for relation in relations:
            source = relation.get("source")
            target = relation.get("target")
            if (
                source in [hypothesis.source_concept, expected_source]
                and target in [
                    hypothesis.target_concept,
                    expected_target,
                    expected_truth_target,
                    expected_source_truth,
                ]
            ):
                return True
        return False

    def _metric_scores(self, hypothesis, evidence, context):
        supporting = [item for item in evidence if item.supports()]
        rejecting = [item for item in evidence if item.contradicts()]
        supporting_tasks = {
            item.originating_task
            for item in supporting
            if item.originating_task != "unknown"
        }
        rejecting_tasks = {
            item.originating_task
            for item in rejecting
            if item.originating_task != "unknown"
        }
        contexts = {
            item.context_signature
            for item in supporting
            if item.context_signature != "unknown"
        }
        dependency_promotion = self._dependency_promotion(context)
        dependency_coherence = context.get(
            "dependency_coherence",
            context.get(
                "causal_graph_alignment",
                {},
            ).get(
                "components",
                {},
            ).get(
                "dependency_coherence",
                0.0,
            ),
        )
        dependency_coherence = max(
            clamp(dependency_coherence),
            clamp(
                dependency_coherence
                + dependency_promotion["promotion_dependency_bonus"]
            ),
        )
        identity_compatibility = context.get(
            "identity_compatibility",
            context.get(
                "identity_safe_truth_integration",
                {},
            ).get(
                "identity_continuity",
                context.get("identity_continuity", 0.0),
            ),
        )
        total_evidence = max(len(evidence), 1)
        contradiction_load = (
            sum(item.contradiction_strength for item in evidence)
            / total_evidence
        )
        context_binding = context.get("context_binding", {})
        if not isinstance(context_binding, dict):
            context_binding = context.get(
                "contextual_truth",
                {},
            ).get("context_binding", {})
        binding_consistency = (
            context_binding.get("context_binding_score")
            if isinstance(context_binding, dict)
            else None
        )
        inferred_context_consistency = (
            clamp(len(contexts) / 2.0)
            if contexts
            else 0.0
        )
        if binding_consistency is not None:
            inferred_context_consistency = max(
                inferred_context_consistency,
                clamp(binding_consistency),
            )
        explicit_context_consistency = context.get("context_consistency")
        if isinstance(explicit_context_consistency, dict):
            explicit_context_consistency = explicit_context_consistency.get(
                "context_consistency",
            )
        if explicit_context_consistency is not None:
            inferred_context_consistency = max(
                inferred_context_consistency,
                clamp(explicit_context_consistency),
            )
        scene_context_consistency = self._scene_context_consistency(context)
        inferred_context_consistency = max(
            inferred_context_consistency,
            scene_context_consistency,
        )
        return {
            "cross_task_stability": clamp(
                len(supporting_tasks) / self.minimum_supporting_tasks
            ),
            "contradiction_resistance":
            clamp(1.0 - contradiction_load),
            "dependency_coherence": clamp(dependency_coherence),
            "promotion_dependency_score":
            dependency_promotion["promotion_dependency_score"],
            "promotion_dependency_bonus":
            dependency_promotion["promotion_dependency_bonus"],
            "dependency_promotion_blockers":
            dependency_promotion["dependency_promotion_blockers"],
            "dependency_promotion_evidence":
            dependency_promotion["dependency_promotion_evidence"],
            "context_consistency": inferred_context_consistency,
            "identity_compatibility": clamp(identity_compatibility),
            "scene_context_consistency": scene_context_consistency,
            "supporting_tasks": sorted(supporting_tasks),
            "rejecting_tasks": sorted(rejecting_tasks),
        }

    def _dependency_promotion(self, context):
        evidence = {}
        for key in [
            "process_dependency_memory",
            "dependency_reasoning",
            "dependency_reasoning_report",
            "dependency_chain_resolution",
        ]:
            candidate = context.get(key)
            if isinstance(candidate, dict):
                evidence = candidate
                break
        causal_validation = context.get("causal_validation", {})
        if not evidence and isinstance(causal_validation, dict):
            evidence = causal_validation.get("dependency_promotion_evidence", {})
        confidence = clamp(
            context.get(
                "dependency_confidence",
                evidence.get("dependency_confidence", 0.0),
            )
        )
        coverage = clamp(
            context.get(
                "dependency_chain_coverage",
                evidence.get("dependency_chain_coverage", 0.0),
            )
        )
        try:
            depth = int(
                context.get(
                    "dependency_chain_depth",
                    evidence.get("dependency_chain_depth", 0),
                )
                or 0
            )
        except Exception:
            depth = 0
        missing_dependencies = list(
            context.get(
                "missing_dependencies",
                evidence.get("missing_dependencies", []),
            )
            or []
        )
        blockers = []
        if confidence <= 0.85:
            blockers.append("dependency_confidence_below_promotion_floor")
        if missing_dependencies:
            blockers.append("dependency_chain_missing_dependencies")
        if depth < 4:
            blockers.append("dependency_chain_depth_below_promotion_floor")
        depth_score = clamp(depth / 5.0)
        promotion_dependency_score = clamp(
            confidence * 0.46
            + coverage * 0.34
            + depth_score * 0.20
        )
        complete = (
            confidence > 0.85
            and not missing_dependencies
            and depth >= 4
        )
        promotion_dependency_bonus = (
            round(min((promotion_dependency_score - 0.80) * 0.25, 0.08), 4)
            if complete and promotion_dependency_score > 0.80
            else 0.0
        )
        return {
            "promotion_dependency_score":
            round(promotion_dependency_score, 4),
            "promotion_dependency_bonus": promotion_dependency_bonus,
            "dependency_promotion_blockers": blockers,
            "dependency_promotion_evidence": {
                "dependency_confidence": confidence,
                "dependency_chain_depth": depth,
                "dependency_chain_coverage": coverage,
                "missing_dependencies": missing_dependencies,
                "dependency_chain_complete_for_promotion": complete,
            },
        }

    def _scene_context_consistency(self, context):
        comparison = context.get("scene_graph_comparison", {})
        if not isinstance(comparison, dict):
            return 0.0
        summary = comparison.get("summary", {})
        if not summary.get("object_level_ready"):
            return 0.0
        input_count = summary.get("input_object_count", 0)
        output_count = summary.get("output_object_count", 0)
        matched = len(comparison.get("object_matches", []) or [])
        match_coverage = (
            matched / max(min(input_count, output_count), 1)
            if input_count or output_count
            else 0.0
        )
        event_signal = clamp(
            len(comparison.get("object_events", []) or []) / 3.0
        )
        relation_changes = comparison.get("relation_changes", {})
        relation_signal = clamp(
            (
                len(relation_changes.get("relations_preserved", []) or [])
                + len(relation_changes.get("relations_added", []) or [])
            )
            / 4.0
        )
        return clamp(
            0.42
            + match_coverage * 0.26
            + event_signal * 0.18
            + relation_signal * 0.14
        )

    def compute_validation_score(self, metrics):
        return clamp(
            (
                metrics.get("cross_task_stability", 0.0)
                + metrics.get("contradiction_resistance", 0.0)
                + metrics.get("dependency_coherence", 0.0)
                + metrics.get("context_consistency", 0.0)
                + metrics.get("identity_compatibility", 0.0)
            )
            / 5.0
        )

    def counterfactual_validation(
        self,
        hypothesis,
        context=None,
        causal_graph=None,
    ):
        context = context if isinstance(context, dict) else {}
        hypothesis = self._normalize_hypothesis(hypothesis)
        key = (
            f"{hypothesis.source_concept}->"
            f"{hypothesis.target_concept}"
        )
        counterfactuals = context.get("counterfactual_results", {})
        result = counterfactuals.get(
            key,
            counterfactuals.get(hypothesis.hypothesis_id, {}),
        )
        if result.get("effect_absent_without_source") is True:
            score = 1.0
            state = "COUNTERFACTUAL_SUPPORTS_CAUSE"
        elif result.get("effect_preserved_without_source") is True:
            score = 0.0
            state = "COUNTERFACTUAL_WEAKENS_CAUSE"
        elif self._relation_observed(hypothesis, causal_graph):
            score = 0.70
            state = "COUNTERFACTUAL_PENDING_GRAPH_RELATION_OBSERVED"
        else:
            score = 0.35
            state = "COUNTERFACTUAL_PENDING"
        return {
            "hypothesis_id": hypothesis.hypothesis_id,
            "counterfactual_score": clamp(score),
            "counterfactual_state": state,
            "tested_question": (
                f"if {hypothesis.source_concept} disappears, "
                f"does {hypothesis.target_concept} remain?"
            ),
        }

    def detect_spurious_causality(
        self,
        hypothesis,
        evidence=None,
        context=None,
        causal_graph=None,
    ):
        context = context if isinstance(context, dict) else {}
        hypothesis = self._normalize_hypothesis(hypothesis)
        evidence = [
            self._evidence_from_dict(item)
            for item in list(evidence or [])
        ]
        metrics = self._metric_scores(hypothesis, evidence, context)
        counterfactual = self.counterfactual_validation(
            hypothesis,
            context,
            causal_graph,
        )
        relation_observed = self._relation_observed(hypothesis, causal_graph)
        support_observed = bool(metrics["supporting_tasks"])
        spurious = (
            support_observed
            and not relation_observed
            and (
                metrics["dependency_coherence"] < 0.50
                or counterfactual["counterfactual_score"] < 0.50
            )
        )
        return {
            "hypothesis_id": hypothesis.hypothesis_id,
            "relationship_state": (
                self.SPURIOUS_RELATIONSHIP
                if spurious
                else self.VALID_CAUSAL_RELATIONSHIP
            ),
            "spurious": spurious,
            "explicit_graph_relation_observed": relation_observed,
            "counterfactual_validation": counterfactual,
            "diagnostic_metrics": {
                key: value
                for key, value in metrics.items()
                if key not in ["supporting_tasks", "rejecting_tasks"]
            },
        }

    def _state_for_score(self, score, spurious):
        if spurious:
            return CausalValidationState.REJECTED.value
        if score >= self.minimum_validation_score:
            return CausalValidationState.VALIDATED.value
        if score >= 0.55:
            return CausalValidationState.PARTIALLY_VALIDATED.value
        if score >= 0.30:
            return CausalValidationState.UNDER_REVIEW.value
        return CausalValidationState.REJECTED.value

    def validate_hypothesis(
        self,
        hypothesis,
        evidence=None,
        context=None,
        causal_graph=None,
    ):
        context = context if isinstance(context, dict) else {}
        hypothesis = self._normalize_hypothesis(hypothesis)
        evidence = [
            self._evidence_from_dict(item)
            for item in list(evidence or [])
        ]
        metrics = self._metric_scores(hypothesis, evidence, context)
        spurious_report = self.detect_spurious_causality(
            hypothesis,
            evidence,
            context,
            causal_graph,
        )
        counterfactual = spurious_report["counterfactual_validation"]
        metrics["dependency_coherence"] = clamp(
            (
                metrics["dependency_coherence"]
                + counterfactual["counterfactual_score"]
            )
            / 2.0
        )
        validation_score = self.compute_validation_score(metrics)
        state = self._state_for_score(
            validation_score,
            spurious_report["spurious"],
        )
        contradiction_score = clamp(
            1.0 - metrics["contradiction_resistance"]
        )
        record = CausalHypothesis(
            hypothesis_id=hypothesis.hypothesis_id,
            source_concept=hypothesis.source_concept,
            target_concept=hypothesis.target_concept,
            evidence_count=len(evidence),
            confidence=validation_score,
            validation_state=state,
            contradiction_score=contradiction_score,
            supporting_tasks=metrics["supporting_tasks"],
            rejecting_tasks=metrics["rejecting_tasks"],
        ).as_dict()
        self.hypotheses[record["hypothesis_id"]] = record
        self.confidence_history.setdefault(
            record["hypothesis_id"],
            [],
        ).append(validation_score)
        self.contradiction_history.setdefault(
            record["hypothesis_id"],
            [],
        ).append(contradiction_score)
        if state == CausalValidationState.VALIDATED.value:
            self.recovery_history.setdefault(
                record["hypothesis_id"],
                [],
            ).append("validated_causal_relationship")
        self._persist()
        how_we_know = [
            (
                f"validated across "
                f"{len(metrics['supporting_tasks'])} tasks"
            ),
            "survived contradiction review"
            if metrics["contradiction_resistance"] >= 0.75
            else "contradiction review still active",
            "passed counterfactual testing"
            if counterfactual["counterfactual_score"] >= 0.75
            else "counterfactual testing remains provisional",
            "maintained dependency coherence"
            if metrics["dependency_coherence"] >= 0.75
            else "dependency coherence requires more evidence",
            "validated by causal graph analysis"
            if not spurious_report["spurious"]
            else "rejected as spurious correlation",
        ]
        return {
            "system": "causal_validation_engine",
            "hypothesis": record,
            "validation_score": validation_score,
            "validation_ready":
            validation_score >= self.minimum_validation_score
            and state == CausalValidationState.VALIDATED.value,
            "validation_state": state,
            "minimum_validation_score": self.minimum_validation_score,
            "cross_task_stability": metrics["cross_task_stability"],
            "contradiction_resistance":
            metrics["contradiction_resistance"],
            "dependency_coherence": metrics["dependency_coherence"],
            "promotion_dependency_score":
            metrics["promotion_dependency_score"],
            "promotion_dependency_bonus":
            metrics["promotion_dependency_bonus"],
            "dependency_promotion_blockers":
            metrics["dependency_promotion_blockers"],
            "dependency_promotion_evidence":
            metrics["dependency_promotion_evidence"],
            "context_consistency": metrics["context_consistency"],
            "identity_compatibility": metrics["identity_compatibility"],
            "counterfactual_validation": counterfactual,
            "spurious_causality": spurious_report,
            "supporting_tasks": metrics["supporting_tasks"],
            "rejecting_tasks": metrics["rejecting_tasks"],
            "how_we_know": how_we_know,
        }

    def generate_validation_report(self):
        hypotheses = list(self.hypotheses.values())
        return {
            "system": "causal_validation_engine",
            "hypotheses": hypotheses,
            "validated_hypotheses": [
                item
                for item in hypotheses
                if item.get("validation_state")
                == CausalValidationState.VALIDATED.value
            ],
            "rejected_hypotheses": [
                item
                for item in hypotheses
                if item.get("validation_state")
                == CausalValidationState.REJECTED.value
            ],
            "confidence_history": self.confidence_history,
            "contradiction_history": self.contradiction_history,
            "recovery_history": self.recovery_history,
            "persistent_storage_enabled": self.storage_path is not None,
            "storage_path": (
                str(self.storage_path)
                if self.storage_path is not None
                else None
            ),
            "last_persistence_error": self.last_persistence_error,
            "minimum_validation_score": self.minimum_validation_score,
        }


__all__ = [
    "CausalEvidence",
    "CausalHypothesis",
    "CausalValidationEngine",
    "CausalValidationState",
]
