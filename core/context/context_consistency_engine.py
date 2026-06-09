from copy import deepcopy
from datetime import datetime

from core.epistemic_models import clamp


class ContextConsistencyEngine:
    """Measures how strongly a concept or truth belongs to a context."""

    def __init__(self):
        self.context_memory = {}
        self.binding_history = {}
        self.consistency_thresholds = {
            "commit_truth": 0.85,
            "commit_contextual_truth": 0.75,
            "review": 0.55,
            "block": 0.45,
        }
        self.concept_context_priors = {
            "shape_preservation": [
                "shape_equivalence",
                "structural_integrity",
                "size_preserved",
                "topology_preserved",
                "topology_splitting_allowed_if_shape_stable",
            ],
            "color_preservation": [
                "color_behavior",
                "no_color_reassignment",
                "valid_color_mapping_rule",
            ],
            "position_preservation": [
                "spatial_alignment",
                "coordinate_stability",
                "no_translation",
                "stable_reference_frame",
            ],
            "symmetry_preservation": [
                "symmetry_axis",
                "mirror_consistency",
                "symmetry_behavior",
            ],
            "topology_preservation": [
                "topology_behavior",
                "connectivity_state",
                "topology_preserved",
            ],
            "object_identity_preservation": [
                "identity_behavior",
                "lineage_continuity",
                "identity_preserved",
                "identity_split_with_lineage",
            ],
            "identity_preservation": [
                "identity_behavior",
                "lineage_continuity",
                "identity_preserved",
                "identity_split_with_lineage",
            ],
            "symmetry_reasoning": [
                "symmetry_evidence",
                "axis_detection",
                "relational_balance",
            ],
        }
        self.context_family_weights = {
            "duplication": 0.85,
            "structural_transformation": 0.80,
            "recoloring": 0.65,
            "topology_splitting": 0.65,
            "identity_split": 0.60,
            "unknown": 0.50,
        }

    def _read(self, report, *keys, default="unknown"):
        if not isinstance(report, dict):
            return default
        for key in keys:
            if key in report and report[key] is not None:
                return report[key]
        return default

    def _list(self, report, key):
        value = report.get(key, []) if isinstance(report, dict) else []
        if isinstance(value, str):
            return [value]
        return list(value or [])

    def normalize_context(
        self,
        context_report=None,
        semantic_context_report=None,
        contextual_truth_report=None,
        scene_graph_report=None,
    ):
        context_report = deepcopy(dict(context_report or {}))
        semantic_context_report = deepcopy(dict(semantic_context_report or {}))
        contextual_truth_report = deepcopy(dict(contextual_truth_report or {}))
        scene_graph_report = deepcopy(dict(scene_graph_report or {}))
        topology_behavior = self._read(
            context_report,
            "topology_behavior",
            "topology",
        )
        transformation_family = self._read(
            context_report,
            "transformation_family",
            "transformation",
            default=self._read(
                semantic_context_report,
                "context",
                default=topology_behavior,
            ),
        )
        task_cluster = self._read(
            context_report,
            "task_cluster",
            "cluster",
            default=transformation_family,
        )
        confidence = max(
            clamp(context_report.get("confidence", 0.0)),
            clamp(semantic_context_report.get("confidence", 0.0)),
            clamp(contextual_truth_report.get("context_confidence", 0.0)),
        )
        if confidence == 0.0:
            confidence = 0.5
        return {
            "transformation_family": transformation_family,
            "task_cluster": task_cluster,
            "object_count": self._read(context_report, "object_count"),
            "topology_behavior": topology_behavior,
            "color_behavior": self._read(
                context_report,
                "color_behavior",
                "color",
            ),
            "identity_behavior": self._read(
                context_report,
                "identity_behavior",
                "identity",
            ),
            "symmetry_behavior": self._read(
                context_report,
                "symmetry_behavior",
                "symmetry",
            ),
            "size_behavior": self._read(context_report, "size_behavior", "size"),
            "propagation_behavior": self._read(
                context_report,
                "propagation_behavior",
                "propagation",
            ),
            "confidence": confidence,
            "context_family": self._context_family(
                transformation_family,
                task_cluster,
            ),
            "semantic_properties": self._list(
                semantic_context_report,
                "properties",
            ),
            "semantic_capabilities": self._list(
                semantic_context_report,
                "capabilities",
            ),
            "semantic_constraints": self._list(
                semantic_context_report,
                "constraints",
            ),
            "semantic_implications": self._list(
                semantic_context_report,
                "implications",
            ),
            "contextual_truth": contextual_truth_report,
            "scene_graph": scene_graph_report,
            "scene_graph_consistency": self._scene_graph_consistency(
                scene_graph_report,
            ),
        }

    def _context_family(self, transformation_family, task_cluster):
        family = str(transformation_family or task_cluster or "unknown").lower()
        if "duplication" in family:
            return "duplication"
        if "structural" in family:
            return "structural_transformation"
        if "color" in family or "recolor" in family:
            return "recoloring"
        if "topology" in family or "split" in family:
            return "topology_splitting"
        if "identity" in family:
            return "identity_split"
        return family or "unknown"

    def expected_context_profile(self, concept):
        return {
            "concept": concept,
            "expected_dependencies": list(
                self.concept_context_priors.get(concept, [])
            ),
        }

    def score_context_support(self, concept, normalized_context):
        context = normalized_context or {}
        signals = set(
            str(item)
            for item in (
                context.get("semantic_properties", [])
                + context.get("semantic_capabilities", [])
                + context.get("semantic_constraints", [])
                + context.get("semantic_implications", [])
            )
        )
        score = self.context_family_weights.get(
            context.get("context_family", "unknown"),
            0.55,
        )
        if concept == "shape_preservation":
            if {
                "preserves_shape",
                "structural_replication",
                "structure_preservation",
            } & signals:
                score += 0.25
            if context.get("size_behavior") in {"size_preserved", "stable"}:
                score += 0.10
        elif concept == "color_preservation":
            if context.get("color_behavior") == "color_reassigned":
                score -= 0.25
            if {"color_mapping_rule", "attribute_remapping"} & signals:
                score += 0.15
            if "changes_color" in signals:
                score -= 0.10
        elif concept in {
            "object_identity_preservation",
            "identity_preservation",
        }:
            if context.get("identity_behavior") == "identity_split":
                score -= 0.25
            if {"lineage_continuity", "identity_continuity"} & signals:
                score += 0.20
        elif concept == "topology_preservation":
            if context.get("topology_behavior") == "topology_splitting":
                score -= 0.25
            if {"connectivity_state", "topology_continuity"} & signals:
                score += 0.20
        elif concept == "symmetry_preservation":
            if {"mirror_consistency", "symmetry_axis"} & signals:
                score += 0.20
        elif concept == "position_preservation":
            if {"coordinate_stability", "stable_reference_frame"} & signals:
                score += 0.20
        scene_score = context.get("scene_graph_consistency", 0.0)
        if scene_score:
            if concept == "shape_preservation":
                score += scene_score * 0.12
            elif concept == "color_preservation":
                score += scene_score * 0.08
            elif concept in {
                "object_identity_preservation",
                "identity_preservation",
            }:
                score += scene_score * 0.10
            elif concept == "topology_preservation":
                score += scene_score * 0.08
        return clamp(score * context.get("confidence", 0.5))

    def score_context_transferability(
        self,
        concept,
        contextual_truth_report=None,
        normalized_context=None,
    ):
        report = contextual_truth_report or (
            normalized_context or {}
        ).get("contextual_truth", {})
        report = report if isinstance(report, dict) else {}
        valid = list(report.get("valid_contexts", []) or [])
        invalid = list(report.get("invalid_contexts", []) or [])
        transfer = clamp(report.get("transfer_reliability", 0.5))
        context_confidence = clamp(report.get("context_confidence", 0.5))
        task_cluster_stability = 0.75
        if normalized_context:
            signature = self._context_signature(normalized_context)
            if signature in valid:
                task_cluster_stability = 0.85
            if signature in invalid:
                task_cluster_stability = 0.35
        breadth = clamp(len(valid) / max(len(valid) + len(invalid), 1))
        if not valid and not invalid:
            breadth = 0.5
        return clamp(
            (
                transfer
                + breadth
                + context_confidence
                + task_cluster_stability
            )
            / 4.0
        )

    def score_context_specificity(self, concept, normalized_context):
        context = normalized_context or {}
        known_fields = [
            key
            for key in [
                "transformation_family",
                "topology_behavior",
                "color_behavior",
                "identity_behavior",
                "symmetry_behavior",
                "size_behavior",
                "propagation_behavior",
            ]
            if context.get(key) not in {None, "unknown"}
        ]
        semantic_count = len(
            context.get("semantic_properties", [])
            + context.get("semantic_capabilities", [])
            + context.get("semantic_constraints", [])
            + context.get("semantic_implications", [])
        )
        scene_bonus = context.get("scene_graph_consistency", 0.0) * 1.25
        specificity = clamp(
            (len(known_fields) + semantic_count / 3.0 + scene_bonus) / 8.0
        )
        if not known_fields and semantic_count == 0:
            state = "UNDERDETERMINED"
        elif specificity < 0.35:
            state = "GENERAL"
        elif specificity < 0.70:
            state = "CONTEXT_SPECIFIC"
        else:
            state = "HIGHLY_CONTEXT_BOUND"
        return {
            "specificity_score": specificity,
            "specificity_state": state,
        }

    def score_context_stability(self, concept, normalized_context):
        signature = self._context_signature(normalized_context or {})
        history = self.binding_history.get(concept, [])
        if not history:
            return 0.60
        matching = [
            item
            for item in history
            if item.get("context_signature") == signature
        ]
        values = [
            item.get("consistency_score", 0.0)
            for item in (matching or history)
        ]
        average = sum(values) / max(len(values), 1)
        if len(values) == 1:
            return clamp((average + 0.60) / 2.0)
        drift = sum(abs(value - average) for value in values) / len(values)
        return clamp(average * (1.0 - drift))

    def detect_context_mismatch(self, concept, normalized_context):
        context = normalized_context or {}
        signals = set(
            str(item)
            for item in (
                context.get("semantic_properties", [])
                + context.get("semantic_capabilities", [])
                + context.get("semantic_constraints", [])
                + context.get("semantic_implications", [])
            )
        )
        reasons = []
        if (
            concept == "color_preservation"
            and context.get("color_behavior") == "color_reassigned"
            and not ({"color_mapping_rule", "attribute_remapping"} & signals)
        ):
            reasons.append("color_reassigned_without_mapping_rule")
        if (
            concept == "topology_preservation"
            and context.get("topology_behavior") == "topology_splitting"
            and "topology_continuity" not in signals
        ):
            reasons.append("topology_splitting_without_continuity_rule")
        if (
            concept in {"identity_preservation", "object_identity_preservation"}
            and context.get("identity_behavior") == "identity_split"
            and not ({"lineage_continuity", "identity_continuity"} & signals)
        ):
            reasons.append("identity_split_without_lineage_rule")
        return {
            "mismatch_detected": bool(reasons),
            "mismatch_reasons": reasons,
        }

    def compute_context_consistency(
        self,
        support_score,
        transferability_score,
        specificity_report,
        stability_score,
        mismatch_report,
        scene_graph_score=0.0,
    ):
        specificity_clarity = 1.0
        if specificity_report.get("specificity_state") == "UNDERDETERMINED":
            specificity_clarity = 0.30
        elif specificity_report.get("specificity_state") == "HIGHLY_CONTEXT_BOUND":
            specificity_clarity = 0.80
        mismatch_component = (
            0.0 if mismatch_report.get("mismatch_detected") else 1.0
        )
        if clamp(scene_graph_score) == 0.0:
            return clamp(
                support_score * 0.35
                + transferability_score * 0.25
                + stability_score * 0.20
                + specificity_clarity * 0.10
                + mismatch_component * 0.10
            )
        return clamp(
            support_score * 0.35
            + transferability_score * 0.25
            + stability_score * 0.20
            + specificity_clarity * 0.08
            + mismatch_component * 0.10
            + clamp(scene_graph_score) * 0.02
        )

    def update_memory(self, concept, normalized_context, consistency_score):
        signature = self._context_signature(normalized_context)
        now = datetime.utcnow().isoformat()
        record = self.context_memory.setdefault(
            concept,
            {
                "concept": concept,
                "contexts": {},
            },
        )
        context_record = record["contexts"].setdefault(
            signature,
            {
                "context_signature": signature,
                "consistency_history": [],
                "support_history": [],
                "transfer_history": [],
                "last_seen": None,
            },
        )
        context_record["consistency_history"].append(consistency_score)
        context_record["support_history"].append(
            normalized_context.get("last_support_score", 0.0)
        )
        context_record["transfer_history"].append(
            normalized_context.get("last_transferability_score", 0.0)
        )
        context_record["last_seen"] = now
        self.binding_history.setdefault(concept, []).append({
            "context_signature": signature,
            "consistency_score": consistency_score,
            "last_seen": now,
        })
        return context_record

    def recommend_action(
        self,
        consistency_score,
        mismatch_report,
        specificity_report,
    ):
        reasons = mismatch_report.get("mismatch_reasons", [])
        if any("color" in reason for reason in reasons):
            return "REQUIRE_MAPPING_RULE"
        if any("identity" in reason for reason in reasons):
            return "REQUIRE_IDENTITY_LINEAGE"
        if any("topology" in reason for reason in reasons):
            return "HOLD_FOR_CONTEXT_REVIEW"
        if consistency_score < self.consistency_thresholds["block"]:
            return "BLOCK_TRUTH_COMMIT"
        if specificity_report.get("specificity_state") == "UNDERDETERMINED":
            return "REQUIRE_CONTEXT_DISCOVERY"
        if (
            consistency_score >= self.consistency_thresholds["commit_truth"]
            and specificity_report.get("specificity_state") == "GENERAL"
        ):
            return "COMMIT_TRUTH"
        if (
            consistency_score
            >= self.consistency_thresholds["commit_contextual_truth"]
            and specificity_report.get("specificity_state")
            in {"CONTEXT_SPECIFIC", "HIGHLY_CONTEXT_BOUND"}
        ):
            return "COMMIT_CONTEXTUAL_TRUTH"
        if consistency_score >= self.consistency_thresholds["review"]:
            return "HOLD_FOR_CONTEXT_REVIEW"
        return "BLOCK_TRUTH_COMMIT"

    def build_report(
        self,
        concept,
        normalized_context,
        support_score,
        transferability_score,
        specificity_report,
        stability_score,
        mismatch_report,
        consistency_score,
        recommended_action,
    ):
        explanation = [
            f"context support={support_score}",
            f"transferability={transferability_score}",
            f"stability={stability_score}",
            f"scene_graph_consistency={normalized_context.get('scene_graph_consistency', 0.0)}",
            (
                "mismatch: "
                + ", ".join(mismatch_report.get("mismatch_reasons", []))
                if mismatch_report.get("mismatch_detected")
                else "no context mismatch detected"
            ),
        ]
        return {
            "system": "context_consistency_engine",
            "concept": concept,
            "context_signature": self._context_signature(normalized_context),
            "normalized_context": deepcopy(normalized_context),
            "context_support_strength": support_score,
            "context_transferability": transferability_score,
            "context_specificity": specificity_report,
            "context_stability": stability_score,
            "context_mismatch": mismatch_report,
            "scene_graph_consistency": normalized_context.get(
                "scene_graph_consistency",
                0.0,
            ),
            "context_consistency": consistency_score,
            "recommended_action": recommended_action,
            "explanation": explanation,
        }

    def analyze(
        self,
        concept,
        context_report=None,
        semantic_context_report=None,
        contextual_truth_report=None,
        scene_graph_report=None,
    ):
        normalized = self.normalize_context(
            context_report,
            semantic_context_report,
            contextual_truth_report,
            scene_graph_report,
        )
        self.expected_context_profile(concept)
        support = self.score_context_support(concept, normalized)
        transfer = self.score_context_transferability(
            concept,
            contextual_truth_report,
            normalized,
        )
        specificity = self.score_context_specificity(concept, normalized)
        stability = self.score_context_stability(concept, normalized)
        mismatch = self.detect_context_mismatch(concept, normalized)
        consistency = self.compute_context_consistency(
            support,
            transfer,
            specificity,
            stability,
            mismatch,
            normalized.get("scene_graph_consistency", 0.0),
        )
        normalized["last_support_score"] = support
        normalized["last_transferability_score"] = transfer
        self.update_memory(concept, normalized, consistency)
        action = self.recommend_action(consistency, mismatch, specificity)
        return self.build_report(
            concept,
            normalized,
            support,
            transfer,
            specificity,
            stability,
            mismatch,
            consistency,
            action,
        )

    def _context_signature(self, context):
        fields = [
            "task_cluster",
            "transformation_family",
            "object_count",
            "topology_behavior",
            "color_behavior",
            "identity_behavior",
        ]
        return "|".join(
            f"{field}:{context.get(field, 'unknown')}"
            for field in fields
        )

    def _scene_graph_consistency(self, scene_graph_report):
        report = scene_graph_report if isinstance(scene_graph_report, dict) else {}
        summary = report.get("summary", {})
        if not summary.get("object_level_ready"):
            return 0.0
        input_count = summary.get("input_object_count", 0)
        output_count = summary.get("output_object_count", 0)
        matches = report.get("object_matches", []) or []
        match_coverage = (
            len(matches) / max(min(input_count, output_count), 1)
            if input_count or output_count
            else 0.0
        )
        preserved_shape = sum(
            item.get("shape_preserved") is True
            for item in matches
        )
        shape_preservation = (
            preserved_shape / max(len(matches), 1)
            if matches
            else 0.0
        )
        event_signal = clamp(len(report.get("object_events", []) or []) / 3.0)
        relation_changes = report.get("relation_changes", {})
        relation_signal = clamp(
            (
                len(relation_changes.get("relations_preserved", []) or [])
                + len(relation_changes.get("relations_added", []) or [])
            )
            / 4.0
        )
        return clamp(
            0.30
            + match_coverage * 0.26
            + shape_preservation * 0.22
            + event_signal * 0.12
            + relation_signal * 0.10
        )


__all__ = [
    "ContextConsistencyEngine",
]
