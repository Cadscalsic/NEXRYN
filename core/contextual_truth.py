from dataclasses import asdict, dataclass, field
from uuid import uuid4

from core.context.context_binding_engine import ContextBindingEngine
from core.context_discovery import ContextDiscoveryEngine
from core.epistemic_models import clamp


def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


def _is_unspecified_signature(signature):
    return all(
        getattr(signature, field_name) == "unknown"
        for field_name in ContextSignature.FIELDS
    )


def _discovered_signature(discovered_context):
    discovered_context = (
        discovered_context if isinstance(discovered_context, dict) else {}
    )
    signature = discovered_context.get("context_signature", {})
    signature = dict(signature) if isinstance(signature, dict) else {}
    family = (
        signature.get("transformation_family")
        or discovered_context.get("transformation_family")
        or discovered_context.get("context_name")
        or discovered_context.get("discovered_context")
    )
    if family and family != "unknown":
        signature.setdefault("transformation_family", family)
        signature.setdefault("task_cluster", family)
    for key in [
        "topology_behavior",
        "color_behavior",
        "identity_behavior",
        "symmetry_behavior",
        "size_behavior",
        "propagation_behavior",
    ]:
        if discovered_context.get(key) and key not in signature:
            signature[key] = discovered_context[key]
    return signature


@dataclass
class ContextSignature:
    signature_id: str = ""
    task_cluster: str = "unknown"
    transformation_family: str = "unknown"
    object_count: str = "unknown"
    topology_behavior: str = "unknown"
    color_behavior: str = "unknown"
    symmetry_behavior: str = "unknown"
    size_behavior: str = "unknown"
    identity_behavior: str = "unknown"
    propagation_behavior: str = "unknown"

    FIELDS = (
        "task_cluster",
        "transformation_family",
        "object_count",
        "topology_behavior",
        "color_behavior",
        "symmetry_behavior",
        "size_behavior",
        "identity_behavior",
        "propagation_behavior",
    )

    def __post_init__(self):
        for field_name in self.FIELDS:
            setattr(self, field_name, _normalize(getattr(self, field_name)))
        if not self.signature_id:
            self.signature_id = self.serialize()

    def serialize(self):
        return "|".join(
            f"{field_name}:{getattr(self, field_name)}"
            for field_name in self.FIELDS
        )

    def compare(self, other):
        other = (
            other
            if isinstance(other, ContextSignature)
            else ContextSignature.from_context(other)
        )
        return {
            field_name: getattr(self, field_name) == getattr(
                other,
                field_name,
            )
            for field_name in self.FIELDS
        }

    def similarity(self, other):
        comparison = self.compare(other)
        return clamp(
            sum(1 for matched in comparison.values() if matched)
            / len(comparison)
        )

    def as_dict(self):
        return asdict(self)

    @classmethod
    def from_context(cls, context=None):
        if isinstance(context, cls):
            return context
        context = context if isinstance(context, dict) else {}
        discovered_context = context.get("context_discovery", {})
        if not isinstance(discovered_context, dict):
            discovered_context = {}
        discovered_signature = context.get(
            "discovered_context_signature",
            _discovered_signature(discovered_context),
        )
        if not isinstance(discovered_signature, dict):
            discovered_signature = {}
        discovered_signature = {
            **_discovered_signature(discovered_context),
            **discovered_signature,
        }
        if (
            discovered_context.get("transformation_family") == "unknown"
            and discovered_context.get("confidence", 1.0) < 0.50
            and "discovered_context_signature" not in context
        ):
            discovered_signature = {}
        if not discovered_signature:
            has_context_fields = any(
                key in context
                for key in [
                    "task_cluster",
                    "transformation_family",
                    "topology_behavior",
                    "color_behavior",
                    "identity_behavior",
                    "input_grid",
                    "output_grid",
                    "active_concepts",
                ]
            )
            if has_context_fields:
                discovered_signature = (
                    ContextDiscoveryEngine()
                    .generate_context_signature(context)
                )
        behavior = context.get("behavior", {})
        if not isinstance(behavior, dict):
            behavior = {}
        causal_conditions = context.get("causal_conditions", {})
        if not isinstance(causal_conditions, dict):
            causal_conditions = {}
        active_concepts = context.get("active_concepts", [])
        if isinstance(active_concepts, dict):
            active_concepts = active_concepts.keys()
        active_concepts = {
            str(item).lower()
            for item in active_concepts
            if item is not None
        }
        transformation_family = _infer_transformation_family(
            context,
            active_concepts,
        )
        return cls(
            signature_id=context.get(
                "signature_id",
                discovered_signature.get("signature_id", ""),
            ),
            task_cluster=context.get(
                "task_cluster",
                discovered_signature.get(
                    "task_cluster",
                    context.get("task_context", transformation_family),
                ),
            ),
            transformation_family=context.get(
                "transformation_family",
                discovered_signature.get(
                    "transformation_family",
                    transformation_family,
                ),
            ),
            object_count=context.get(
                "object_count",
                discovered_signature.get(
                    "object_count",
                    behavior.get("object_count", "unknown"),
                ),
            ),
            topology_behavior=context.get(
                "topology_behavior",
                discovered_signature.get(
                    "topology_behavior",
                    causal_conditions.get(
                        "topology_mode",
                        behavior.get("topology", "unknown"),
                    ),
                ),
            ),
            color_behavior=context.get(
                "color_behavior",
                discovered_signature.get(
                    "color_behavior",
                    causal_conditions.get(
                        "color_mode",
                        behavior.get("color", "unknown"),
                    ),
                ),
            ),
            symmetry_behavior=context.get(
                "symmetry_behavior",
                discovered_signature.get(
                    "symmetry_behavior",
                    causal_conditions.get(
                        "symmetry_mode",
                        behavior.get("symmetry", "unknown"),
                    ),
                ),
            ),
            size_behavior=context.get(
                "size_behavior",
                discovered_signature.get(
                    "size_behavior",
                    causal_conditions.get(
                        "size_mode",
                        behavior.get("size", "unknown"),
                    ),
                ),
            ),
            identity_behavior=context.get(
                "identity_behavior",
                discovered_signature.get(
                    "identity_behavior",
                    causal_conditions.get(
                        "identity_mode",
                        behavior.get("identity", "unknown"),
                    ),
                ),
            ),
            propagation_behavior=context.get(
                "propagation_behavior",
                discovered_signature.get(
                    "propagation_behavior",
                    causal_conditions.get(
                        "propagation_mode",
                        behavior.get("propagation", "unknown"),
                    ),
                ),
            ),
        )


@dataclass
class ContextEvidence:
    evidence_id: str
    concept_name: str
    context_signature: ContextSignature
    support_strength: float = 0.0
    contradiction_strength: float = 0.0

    def __post_init__(self):
        self.evidence_id = self.evidence_id or f"context-evidence:{uuid4().hex}"
        self.context_signature = ContextSignature.from_context(
            self.context_signature
        )
        self.support_strength = clamp(self.support_strength)
        self.contradiction_strength = clamp(self.contradiction_strength)

    def supports_truth(self):
        return (
            self.support_strength > self.contradiction_strength
            and self.support_strength >= 0.50
        )

    def contradicts_truth(self):
        return (
            self.contradiction_strength >= self.support_strength
            and self.contradiction_strength >= 0.30
        )

    def as_dict(self):
        report = asdict(self)
        report["context_signature"] = self.context_signature.as_dict()
        return report


@dataclass
class ContextualTruth:
    truth_name: str
    valid_contexts: list = field(default_factory=list)
    invalid_contexts: list = field(default_factory=list)
    confidence: float = 0.0
    stability: float = 0.0
    contradiction_profile: dict = field(default_factory=dict)
    causal_support: dict = field(default_factory=dict)

    def __post_init__(self):
        self.valid_contexts = [
            ContextSignature.from_context(item)
            for item in self.valid_contexts
        ]
        self.invalid_contexts = [
            ContextSignature.from_context(item)
            for item in self.invalid_contexts
        ]
        self.confidence = clamp(self.confidence)
        self.stability = clamp(self.stability)

    def is_valid(self, context):
        signature = ContextSignature.from_context(context)
        if not self.valid_contexts:
            return False
        return max(
            item.similarity(signature)
            for item in self.valid_contexts
        ) >= 0.60

    def is_invalid(self, context):
        signature = ContextSignature.from_context(context)
        if not self.invalid_contexts:
            return False
        return max(
            item.similarity(signature)
            for item in self.invalid_contexts
        ) >= 0.60

    def context_confidence(self, context):
        signature = ContextSignature.from_context(context)
        valid_similarity = max(
            (
                item.similarity(signature)
                for item in self.valid_contexts
            ),
            default=0.0,
        )
        invalid_similarity = max(
            (
                item.similarity(signature)
                for item in self.invalid_contexts
            ),
            default=0.0,
        )
        return clamp(
            self.confidence
            * max(valid_similarity - invalid_similarity, 0.0)
        )

    def generate_context_explanation(self, context=None):
        signature = ContextSignature.from_context(context)
        return {
            "truth": self.truth_name,
            "when_valid": [
                item.signature_id
                for item in self.valid_contexts
            ],
            "when_invalid": [
                item.signature_id
                for item in self.invalid_contexts
            ],
            "context_confidence": self.context_confidence(signature),
            "is_valid": self.is_valid(signature),
            "is_invalid": self.is_invalid(signature),
        }

    def as_dict(self):
        return {
            "truth_name": self.truth_name,
            "valid_contexts": [
                item.as_dict()
                for item in self.valid_contexts
            ],
            "invalid_contexts": [
                item.as_dict()
                for item in self.invalid_contexts
            ],
            "confidence": self.confidence,
            "stability": self.stability,
            "contradiction_profile": dict(self.contradiction_profile),
            "causal_support": dict(self.causal_support),
        }


def _infer_transformation_family(context, active_concepts):
    explicit = context.get("transformation_family")
    if explicit:
        return explicit
    conditions = context.get("causal_conditions", {})
    if isinstance(conditions, dict):
        mode = str(conditions.get("transformation_mode", "")).lower()
        if mode:
            return mode
    keyword_map = {
        "recoloring": ("recolor", "color_transform", "color_change"),
        "reflection": ("reflect", "reflection"),
        "translation": ("translate", "translation", "move"),
        "duplication": ("duplicate", "copy", "replicate"),
        "topological_growth": ("grow", "expand", "fill", "topology"),
        "identity_preservation": ("identity", "object_identity"),
        "symmetry": ("symmetry", "mirror"),
    }
    joined = " ".join(sorted(active_concepts)).lower()
    for family, keywords in keyword_map.items():
        if any(keyword in joined for keyword in keywords):
            return family
    return context.get("task_cluster", "unknown")


class ContextualTruthEngine:
    PRESERVATION_INVALID_FAMILIES = {
        "color_preservation": {"recoloring", "color_transform"},
        "shape_preservation": {"shape_transform"},
        "symmetry_preservation": {"symmetry_break", "symmetry"},
        "topology_preservation": {
            "topological_growth",
            "topology_transform",
        },
        "object_identity_preservation": {"object_split", "object_merge"},
    }

    def __init__(self):
        self.truths = {}
        self.context_confidence_history = {}
        self.context_evolution_history = {}
        self.context_binding_engine = ContextBindingEngine()

    def _context_evidence(self, concept_name, item, context=None):
        if hasattr(item, "as_dict"):
            item = item.as_dict()
        item = dict(item or {})
        metadata = item.get("metadata", {})
        evidence_context = {
            **(context or {}),
            **metadata,
        }
        if item.get("context_signature"):
            evidence_context["signature_id"] = item["context_signature"]
        return ContextEvidence(
            evidence_id=item.get("evidence_id", item.get("source", "")),
            concept_name=concept_name,
            context_signature=ContextSignature.from_context(
                evidence_context
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

    def discover_contexts(self, evidence=None, context=None):
        evidence = list(evidence or [])
        contexts = {}
        for item in evidence:
            context_evidence = self._context_evidence(
                item.get("concept", "unknown")
                if isinstance(item, dict)
                else "unknown",
                item,
                context,
            )
            signature = context_evidence.context_signature
            contexts.setdefault(signature.signature_id, {
                "context_signature": signature.as_dict(),
                "evidence_count": 0,
                "support_count": 0,
                "contradiction_count": 0,
                "family": signature.transformation_family,
            })
            contexts[signature.signature_id]["evidence_count"] += 1
            if context_evidence.supports_truth():
                contexts[signature.signature_id]["support_count"] += 1
            if context_evidence.contradicts_truth():
                contexts[signature.signature_id]["contradiction_count"] += 1
        if not contexts:
            signature = ContextSignature.from_context(context)
            contexts[signature.signature_id] = {
                "context_signature": signature.as_dict(),
                "evidence_count": 0,
                "support_count": 0,
                "contradiction_count": 0,
                "family": signature.transformation_family,
            }
        return {
            "system": "contextual_truth_engine",
            "discovered_contexts": list(contexts.values()),
            "context_families": sorted({
                item["family"]
                for item in contexts.values()
            }),
        }

    def specialize_truth(self, truth_name, evidence=None, context=None):
        context_evidence = [
            self._context_evidence(truth_name, item, context)
            for item in list(evidence or [])
        ]
        if not context_evidence:
            context_evidence = [
                ContextEvidence(
                    evidence_id=f"context-evidence:{truth_name}",
                    concept_name=truth_name,
                    context_signature=ContextSignature.from_context(context),
                    support_strength=0.5,
                    contradiction_strength=0.0,
                )
            ]
        valid_contexts = []
        invalid_contexts = []
        for item in context_evidence:
            if item.supports_truth():
                valid_contexts.append(item.context_signature)
            if item.contradicts_truth():
                invalid_contexts.append(item.context_signature)
        current_context = ContextSignature.from_context(context)
        invalid_families = self.PRESERVATION_INVALID_FAMILIES.get(
            truth_name,
            set(),
        )
        if current_context.transformation_family in invalid_families:
            invalid_contexts.append(current_context)
        elif not valid_contexts:
            valid_contexts.append(current_context)

        support_count = sum(item.supports_truth() for item in context_evidence)
        contradiction_count = sum(
            item.contradicts_truth()
            for item in context_evidence
        )
        evidence_count = max(len(context_evidence), 1)
        confidence = clamp(support_count / evidence_count)
        stability = clamp(
            len({item.signature_id for item in valid_contexts}) / 3.0
        )
        truth = ContextualTruth(
            truth_name=truth_name,
            valid_contexts=valid_contexts,
            invalid_contexts=invalid_contexts,
            confidence=confidence,
            stability=stability,
            contradiction_profile={
                "support_count": support_count,
                "contradiction_count": contradiction_count,
                "contradiction_resistance":
                clamp(1.0 - contradiction_count / evidence_count),
            },
        )
        self.truths[truth_name] = truth
        self.context_evolution_history.setdefault(truth_name, []).append(
            truth.as_dict()
        )
        return {
            "system": "contextual_truth_engine",
            "truth": truth.as_dict(),
            "specialized_truths": [
                f"{truth_name} under {item.transformation_family}"
                for item in valid_contexts
            ],
        }

    def compute_context_similarity(self, first, second):
        return ContextSignature.from_context(first).similarity(second)

    def analyze_contextual_contradictions(
        self,
        truth_name,
        evidence=None,
        context=None,
    ):
        specialization = self.specialize_truth(
            truth_name,
            evidence,
            context,
        )
        truth = self.truths[truth_name]
        signature = ContextSignature.from_context(context)
        context_mismatch = truth.is_invalid(signature)
        return {
            "system": "contextual_truth_engine",
            "truth": truth_name,
            "context_signature": signature.as_dict(),
            "context_mismatch": context_mismatch,
            "contradiction_type": (
                "CONTEXT_MISMATCH"
                if context_mismatch
                else "TRUTH_CONTRADICTION_REVIEW"
            ),
            "valid_contexts": [
                item.signature_id
                for item in truth.valid_contexts
            ],
            "invalid_contexts": [
                item.signature_id
                for item in truth.invalid_contexts
            ],
            "specialization": specialization,
        }

    def compute_contextual_confidence(
        self,
        truth_name,
        context=None,
        causal_validation=None,
        identity_compatibility=1.0,
    ):
        truth = self.truths.get(truth_name)
        if truth is None:
            self.specialize_truth(truth_name, context=context)
            truth = self.truths[truth_name]
        signature = ContextSignature.from_context(context)
        causal_validation = causal_validation if isinstance(
            causal_validation,
            dict,
        ) else {}
        causal_validation_score = causal_validation.get(
            "validation_score",
            causal_validation.get("causal_validation_score", 0.0),
        )
        context_stability = truth.stability
        contradiction_resistance = truth.contradiction_profile.get(
            "contradiction_resistance",
            0.0,
        )
        transfer_reliability = max(
            (
                item.similarity(signature)
                for item in truth.valid_contexts
            ),
            default=0.0,
        )
        if (
            _is_unspecified_signature(signature)
            and not truth.invalid_contexts
        ):
            context_stability = max(context_stability, 1.0)
            transfer_reliability = max(transfer_reliability, 1.0)
        context_score = clamp(
            (
                causal_validation_score
                + context_stability
                + transfer_reliability
                + clamp(identity_compatibility)
            )
            / 4.0
        )
        contextual_confidence = clamp(
            (
                context_score
                + contradiction_resistance
            )
            / 2.0
        )
        report = {
            "truth": truth_name,
            "contextual_truth_score": context_score,
            "contextual_confidence": contextual_confidence,
            "causal_validation_score": clamp(causal_validation_score),
            "context_stability": context_stability,
            "contradiction_resistance": contradiction_resistance,
            "transfer_reliability": clamp(transfer_reliability),
            "identity_compatibility": clamp(identity_compatibility),
            "contextual_consistency": context_score >= 0.75,
            "status": (
                "CONTEXT_VALIDATED"
                if context_score >= 0.75
                else "CONTEXT_REVIEW_REQUIRED"
            ),
        }
        self.context_confidence_history.setdefault(
            truth_name,
            [],
        ).append(report)
        return report

    def generate_contextual_truth_report(
        self,
        truth_name,
        context=None,
        causal_validation=None,
        identity_compatibility=1.0,
    ):
        if truth_name not in self.truths:
            self.specialize_truth(truth_name, context=context)
        truth = self.truths[truth_name]
        confidence = self.compute_contextual_confidence(
            truth_name,
            context,
            causal_validation,
            identity_compatibility,
        )
        explanation = truth.generate_context_explanation(context)
        context = context if isinstance(context, dict) else {}
        current_signature = ContextSignature.from_context(context)
        context_binding = self.context_binding_engine.bind(
            truth_name,
            context_report={
                **context,
                "context_discovery": context.get("context_discovery", {}),
            },
            semantic_context_report=context.get("semantic_context", {}),
            context_hierarchy_report=context.get("context_hierarchy", {}),
            contextual_truth_report=confidence,
            causal_validation_report=causal_validation,
        )
        base_contextual_truth_score = confidence["contextual_truth_score"]
        contextual_truth_score = clamp(
            base_contextual_truth_score * 0.65
            + context_binding["context_binding_score"] * 0.35
        )
        contextual_consistency = contextual_truth_score >= 0.75
        status = (
            "CONTEXT_VALIDATED"
            if contextual_consistency
            else "CONTEXT_REVIEW_REQUIRED"
        )
        return {
            "system": "contextual_truth_engine",
            "truth": truth_name,
            "context_signature": current_signature.signature_id,
            "context_signature_fields": current_signature.as_dict(),
            "valid_contexts": explanation["when_valid"],
            "invalid_contexts": explanation["when_invalid"],
            "context_confidence":
            confidence["contextual_confidence"],
            "contextual_truth_score":
            contextual_truth_score,
            "base_contextual_truth_score": base_contextual_truth_score,
            "context_binding_score":
            context_binding["context_binding_score"],
            "transfer_reliability":
            confidence["transfer_reliability"],
            "status": status,
            "contextual_consistency": contextual_consistency,
            "confidence_components": {
                **confidence,
                "contextual_truth_score": contextual_truth_score,
                "base_contextual_truth_score": base_contextual_truth_score,
                "context_binding_score":
                context_binding["context_binding_score"],
                "context_binding_state":
                context_binding["binding_state"],
            },
            "when_valid": explanation["when_valid"],
            "when_invalid": explanation["when_invalid"],
            "why_valid": context_binding["why_valid"],
            "why_invalid": context_binding["why_invalid"],
            "context_binding": context_binding,
            "explainability": {
                "why": (
                    context_binding["why_valid"]
                    or ["Observed repeatedly in matching contexts."]
                ),
                "how_do_we_know":
                "Validated through causal and contextual analysis.",
                "when_is_it_valid": explanation["when_valid"],
                "when_is_it_invalid": explanation["when_invalid"],
                "binding_chain": context_binding["binding_chain"],
            },
            "context_confidence_history":
            self.context_confidence_history.get(truth_name, []),
            "context_evolution_history":
            self.context_evolution_history.get(truth_name, []),
        }


def discover_contexts(evidence=None, context=None):
    return ContextualTruthEngine().discover_contexts(evidence, context)


def specialize_truth(truth_name, evidence=None, context=None):
    return ContextualTruthEngine().specialize_truth(
        truth_name,
        evidence,
        context,
    )


def analyze_contextual_contradictions(
    truth_name,
    evidence=None,
    context=None,
):
    return ContextualTruthEngine().analyze_contextual_contradictions(
        truth_name,
        evidence,
        context,
    )


def compute_context_similarity(first, second):
    return ContextualTruthEngine().compute_context_similarity(first, second)


def compute_contextual_confidence(
    truth_name,
    context=None,
    causal_validation=None,
    identity_compatibility=1.0,
):
    return ContextualTruthEngine().compute_contextual_confidence(
        truth_name,
        context,
        causal_validation,
        identity_compatibility,
    )


__all__ = [
    "ContextEvidence",
    "ContextSignature",
    "ContextualTruth",
    "ContextualTruthEngine",
    "analyze_contextual_contradictions",
    "compute_context_similarity",
    "compute_contextual_confidence",
    "discover_contexts",
    "specialize_truth",
]
