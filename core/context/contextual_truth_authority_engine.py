from copy import deepcopy
from datetime import datetime

from core.epistemic_models import clamp


def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().upper().replace(" ", "_") or default


def _as_dict(value):
    if isinstance(value, dict):
        return deepcopy(value)
    return {}


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return list(value.keys())
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _read_number(report, keys, default=0.0):
    report = report if isinstance(report, dict) else {}
    for key in keys:
        if key in report and report[key] is not None:
            return clamp(report[key])
    return clamp(default)


class ContextualTruthAuthorityEngine:
    """Scores whether a contextual truth can support truth governance."""

    def __init__(self):
        self.authority_thresholds = {
            "authoritative": 0.85,
            "supported": 0.75,
            "provisional": 0.60,
            "review": 0.45,
        }
        self.authority_memory = {}
        self.support_history = {}
        self.penalty_weights = {
            "effective_contradiction": 0.45,
            "contradiction_gap": 0.25,
            "review_required": 0.15,
            "review_severity": 0.15,
        }
        self.concept_authority_priors = {
            "shape_preservation": 0.04,
            "position_preservation": 0.04,
            "symmetry_preservation": 0.03,
            "object_identity_preservation": 0.03,
            "identity_preservation": 0.03,
            "color_preservation": 0.02,
            "topology_preservation": 0.02,
        }

    def normalize_inputs(
        self,
        concept,
        truth_candidate_report=None,
        context_consistency_report=None,
        contextual_truth_report=None,
        semantic_context_report=None,
        context_hierarchy_report=None,
        causal_validation_report=None,
        identity_report=None,
    ):
        truth_candidate = _as_dict(truth_candidate_report)
        context_consistency = _as_dict(context_consistency_report)
        contextual_truth = _as_dict(contextual_truth_report)
        semantic_context = _as_dict(semantic_context_report)
        context_hierarchy = _as_dict(context_hierarchy_report)
        causal_validation = _as_dict(causal_validation_report)
        identity = _as_dict(identity_report)

        context_signature = (
            context_consistency.get(
                "context_signature",
                contextual_truth.get(
                    "context_signature",
                    context_hierarchy.get("context_signature", "unknown"),
                ),
            )
            or "unknown"
        )
        hierarchy_score = _read_number(
            context_hierarchy,
            ["context_hierarchy_score", "score", "confidence"],
            0.5,
        )
        semantic_score = _read_number(
            semantic_context,
            ["semantic_context_score", "confidence", "score"],
            0.5,
        )
        if _normalize(semantic_context.get("status")) == "SEMANTICALLY_VALIDATED":
            semantic_score = max(semantic_score, 0.85)
        causal_graph_alignment = _read_number(
            causal_validation,
            ["causal_graph_alignment", "alignment_score"],
            causal_validation.get("causal_alignment", 0.5),
        )
        if isinstance(causal_validation.get("causal_graph_alignment"), dict):
            causal_graph_alignment = _read_number(
                causal_validation["causal_graph_alignment"],
                ["alignment_score", "causal_graph_alignment"],
                0.5,
            )
        identity_compatibility = _read_number(
            causal_validation,
            ["identity_compatibility"],
            identity.get("identity_compatibility", identity.get(
                "identity_continuity",
                1.0,
            )),
        )
        return {
            "concept": str(concept or "unknown"),
            "context_signature": str(context_signature),
            "context_consistency": _read_number(
                context_consistency,
                ["context_consistency", "consistency_score"],
                contextual_truth.get("context_binding_score", 0.5),
            ),
            "contextual_truth_score": _read_number(
                contextual_truth,
                ["contextual_truth_score"],
                truth_candidate.get("contextual_truth_score", 0.5),
            ),
            "semantic_context_score": semantic_score,
            "context_hierarchy_score": hierarchy_score,
            "transfer_reliability": _read_number(
                contextual_truth,
                ["transfer_reliability", "context_transfer_reliability"],
                0.5,
            ),
            "context_confidence": _read_number(
                contextual_truth,
                ["context_confidence", "confidence"],
                0.5,
            ),
            "causal_validation_score": _read_number(
                causal_validation,
                ["causal_validation_score", "validation_score"],
                0.5,
            ),
            "causal_graph_alignment": causal_graph_alignment,
            "dependency_coherence": _read_number(
                causal_validation,
                ["dependency_coherence"],
                0.5,
            ),
            "contradiction_resistance": _read_number(
                causal_validation,
                ["contradiction_resistance"],
                0.5,
            ),
            "identity_compatibility": identity_compatibility,
            "identity_governance_state": _normalize(
                identity.get("identity_governance_state")
            ),
            "identity_state": _normalize(identity.get("identity_state")),
            "failed_identity_governance_gates": _as_list(
                identity.get("failed_identity_governance_gates")
            ),
            "identity_failed_checks": _as_list(
                identity.get("identity_failed_checks")
            ),
            "effective_contradiction": _read_number(
                truth_candidate,
                ["effective_contradiction", "effective_contradiction_score"],
                truth_candidate.get("contradiction_score", 0.0),
            ),
            "contradiction_threshold": _read_number(
                truth_candidate,
                ["contradiction_threshold"],
                0.10,
            ),
            "contradiction_gap": _read_number(
                truth_candidate,
                ["contradiction_gap"],
                max(
                    truth_candidate.get(
                        "effective_contradiction",
                        truth_candidate.get(
                            "effective_contradiction_score",
                            0.0,
                        ),
                    )
                    - truth_candidate.get("contradiction_threshold", 0.10),
                    0.0,
                ),
            ),
            "contradiction_review_required": bool(
                truth_candidate.get("contradiction_review_required", False)
            ),
            "contradiction_review_severity": _normalize(
                truth_candidate.get("contradiction_review_severity")
            ),
            "contextual_truth_status": _normalize(
                contextual_truth.get("status")
            ),
            "hierarchy_ready": context_hierarchy.get(
                "hierarchy_ready",
                True,
            )
            is not False,
            "raw_reports": {
                "truth_candidate": truth_candidate,
                "context_consistency": context_consistency,
                "contextual_truth": contextual_truth,
                "semantic_context": semantic_context,
                "context_hierarchy": context_hierarchy,
                "causal_validation": causal_validation,
                "identity": identity,
            },
        }

    def compute_context_authority_score(self, data):
        score = (
            data["context_consistency"] * 0.30
            + data["contextual_truth_score"] * 0.20
            + data["semantic_context_score"] * 0.15
            + data["context_hierarchy_score"] * 0.10
            + data["transfer_reliability"] * 0.15
            + data["context_confidence"] * 0.10
        )
        score += self.concept_authority_priors.get(data["concept"], 0.0)
        if not data.get("hierarchy_ready", True):
            score -= 0.08
        return clamp(score)

    def compute_causal_support_score(self, data):
        return clamp(
            data["causal_validation_score"] * 0.35
            + data["causal_graph_alignment"] * 0.25
            + data["dependency_coherence"] * 0.20
            + data["contradiction_resistance"] * 0.20
        )

    def compute_identity_safety_score(self, data):
        score = data["identity_compatibility"]
        governance_state = data["identity_governance_state"]
        identity_state = data["identity_state"]
        if governance_state == "IDENTITY_GOVERNANCE_STABLE":
            score = max(score, 0.95)
        elif "REVIEW" in governance_state:
            score = min(score, 0.78)
        elif governance_state not in {"UNKNOWN", ""}:
            score = min(score, 0.82)
        if identity_state in {
            "IDENTITY_REINFORCING_TRUTH",
            "IDENTITY_STABLE",
        }:
            score = max(score, 0.90)
        elif "HOLD" in identity_state or "REVIEW" in identity_state:
            score = min(score, 0.78)
        failures = (
            len(data["failed_identity_governance_gates"])
            + len(data["identity_failed_checks"])
        )
        score -= min(failures * 0.08, 0.32)
        return clamp(score)

    def compute_contradiction_penalty(self, data):
        threshold = max(data["contradiction_threshold"], 0.0001)
        contradiction_pressure = clamp(
            data["effective_contradiction"] / threshold
        )
        gap_pressure = clamp(data["contradiction_gap"] / threshold)
        severity = data["contradiction_review_severity"]
        severity_penalty = {
            "LOW_RISK_REVIEW": 0.20,
            "MEDIUM_RISK_REVIEW": 0.45,
            "HIGH_RISK_REVIEW": 0.75,
            "CRITICAL_REVIEW": 1.0,
        }.get(severity, 0.10 if data["contradiction_review_required"] else 0.0)
        review_penalty = 1.0 if data["contradiction_review_required"] else 0.0
        return clamp(
            contradiction_pressure
            * self.penalty_weights["effective_contradiction"]
            + gap_pressure * self.penalty_weights["contradiction_gap"]
            + review_penalty * self.penalty_weights["review_required"]
            + severity_penalty * self.penalty_weights["review_severity"]
        )

    def compute_authority_score(
        self,
        context_score,
        causal_score,
        identity_score,
        contradiction_penalty,
    ):
        return clamp(
            context_score * 0.45
            + causal_score * 0.25
            + identity_score * 0.20
            - contradiction_penalty * 0.10
        )

    def classify_authority(self, authority_score, data):
        if authority_score >= self.authority_thresholds["authoritative"]:
            return "AUTHORITATIVE_CONTEXTUAL_TRUTH"
        if authority_score >= self.authority_thresholds["supported"]:
            return "SUPPORTED_CONTEXTUAL_TRUTH"
        if authority_score >= self.authority_thresholds["provisional"]:
            return "PROVISIONAL_CONTEXTUAL_TRUTH"
        if authority_score >= self.authority_thresholds["review"]:
            return "CONTEXT_REVIEW_REQUIRED"
        return "BLOCKED_CONTEXTUAL_TRUTH"

    def recommend_truth_governance_action(self, authority_status, data):
        if data["identity_failed_checks"] or (
            data["failed_identity_governance_gates"]
            and data["identity_safety_score"] < 0.60
        ):
            return "REQUIRE_IDENTITY_REVIEW"
        if data["causal_support_score"] < 0.55:
            return "REQUIRE_CAUSAL_REVIEW"
        if data["contradiction_penalty"] >= 0.70:
            return "BLOCK_TRUTH_COMMIT"
        if authority_status == "AUTHORITATIVE_CONTEXTUAL_TRUTH":
            return (
                "COMMIT_TRUTH"
                if data["context_consistency"] >= 0.85
                else "COMMIT_CONTEXTUAL_TRUTH"
            )
        if authority_status == "SUPPORTED_CONTEXTUAL_TRUTH":
            return "COMMIT_CONTEXTUAL_TRUTH"
        if authority_status == "PROVISIONAL_CONTEXTUAL_TRUTH":
            return "HOLD_FOR_CONTEXT_REVIEW"
        if authority_status == "CONTEXT_REVIEW_REQUIRED":
            return "REQUIRE_MORE_CONTEXT_EVIDENCE"
        return "BLOCK_TRUTH_COMMIT"

    def update_memory(self, concept, authority_report):
        timestamp = datetime.utcnow().isoformat()
        record = {
            "concept": concept,
            "context_signature": authority_report["context_signature"],
            "authority_score":
            authority_report["contextual_truth_authority"],
            "authority_status": authority_report["authority_status"],
            "timestamp": timestamp,
        }
        history = self.support_history.setdefault(concept, [])
        history.append(record)
        self.support_history[concept] = history[-128:]
        self.authority_memory[concept] = {
            **record,
            "history": list(self.support_history[concept]),
        }
        return self.authority_memory[concept]

    def build_report(
        self,
        concept,
        data,
        context_score,
        causal_score,
        identity_score,
        contradiction_penalty,
        authority_score,
        authority_status,
        recommended_action,
    ):
        contextual_truth_supported = authority_status in {
            "AUTHORITATIVE_CONTEXTUAL_TRUTH",
            "SUPPORTED_CONTEXTUAL_TRUTH",
        }
        explanation = [
            f"context_authority_score={round(context_score, 4)}",
            f"causal_support_score={round(causal_score, 4)}",
            f"identity_safety_score={round(identity_score, 4)}",
            f"contradiction_penalty={round(contradiction_penalty, 4)}",
            f"authority_status={authority_status}",
            f"truth_governance_action={recommended_action}",
        ]
        return {
            "system": "contextual_truth_authority_engine",
            "concept": concept,
            "context_signature": data["context_signature"],
            "context_authority_score": context_score,
            "causal_support_score": causal_score,
            "identity_safety_score": identity_score,
            "contradiction_penalty": contradiction_penalty,
            "contextual_truth_authority": authority_score,
            "authority_status": authority_status,
            "truth_governance_action": recommended_action,
            "contextual_truth_supported": contextual_truth_supported,
            "support_threshold":
            self.authority_thresholds["supported"],
            "authority_components": {
                "context_consistency": data["context_consistency"],
                "contextual_truth_score": data["contextual_truth_score"],
                "semantic_context_score": data["semantic_context_score"],
                "context_hierarchy_score": data["context_hierarchy_score"],
                "transfer_reliability": data["transfer_reliability"],
                "context_confidence": data["context_confidence"],
                "causal_validation_score":
                data["causal_validation_score"],
                "causal_graph_alignment": data["causal_graph_alignment"],
                "dependency_coherence": data["dependency_coherence"],
                "contradiction_resistance":
                data["contradiction_resistance"],
                "identity_compatibility": data["identity_compatibility"],
            },
            "explanation": explanation,
        }

    def analyze(
        self,
        concept,
        truth_candidate_report=None,
        context_consistency_report=None,
        contextual_truth_report=None,
        semantic_context_report=None,
        context_hierarchy_report=None,
        causal_validation_report=None,
        identity_report=None,
    ):
        data = self.normalize_inputs(
            concept,
            truth_candidate_report,
            context_consistency_report,
            contextual_truth_report,
            semantic_context_report,
            context_hierarchy_report,
            causal_validation_report,
            identity_report,
        )
        context_score = self.compute_context_authority_score(data)
        causal_score = self.compute_causal_support_score(data)
        identity_score = self.compute_identity_safety_score(data)
        contradiction_penalty = self.compute_contradiction_penalty(data)
        data = {
            **data,
            "causal_support_score": causal_score,
            "identity_safety_score": identity_score,
            "contradiction_penalty": contradiction_penalty,
        }
        authority_score = self.compute_authority_score(
            context_score,
            causal_score,
            identity_score,
            contradiction_penalty,
        )
        authority_status = self.classify_authority(authority_score, data)
        recommended_action = self.recommend_truth_governance_action(
            authority_status,
            data,
        )
        report = self.build_report(
            data["concept"],
            data,
            context_score,
            causal_score,
            identity_score,
            contradiction_penalty,
            authority_score,
            authority_status,
            recommended_action,
        )
        self.update_memory(data["concept"], report)
        return report


__all__ = [
    "ContextualTruthAuthorityEngine",
]
