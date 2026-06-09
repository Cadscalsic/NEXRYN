from datetime import datetime

from core.epistemic_models import clamp


class DependencyKnowledgeEngine:
    """Discovers and scores reusable dependency knowledge for truth review."""

    DEPENDENCY_TYPES = {
        "causal_dependency",
        "contextual_dependency",
        "semantic_dependency",
        "identity_dependency",
        "structural_dependency",
        "observational_dependency",
        "contradiction_dependency",
        "weak_dependency",
        "hard_dependency",
        "soft_dependency",
    }

    CONCEPT_REQUIREMENTS = {
        "color_preservation": [
            "color_behavior",
            "color_mapping_rule",
            "recolor_condition",
        ],
        "shape_preservation": [
            "structural_integrity",
            "shape_equivalence",
        ],
        "topology_preservation": [
            "topology_behavior",
            "connectivity_state",
        ],
        "identity_preservation": [
            "identity_behavior",
            "lineage_continuity",
        ],
        "object_identity_preservation": [
            "identity_behavior",
            "lineage_continuity",
        ],
        "position_preservation": [
            "spatial_alignment",
        ],
        "symmetry_preservation": [
            "symmetry_behavior",
        ],
        "symmetry_reasoning": [
            "symmetry_evidence",
        ],
        "density_modulation": [
            "density_behavior",
        ],
    }

    CONCEPT_PRIMARY_DEPENDENCY = {
        "color_preservation": "color_behavior",
        "shape_preservation": "structural_integrity",
        "topology_preservation": "topology_behavior",
        "position_preservation": "spatial_alignment",
        "object_identity_preservation": "identity_behavior",
        "identity_preservation": "identity_behavior",
        "symmetry_preservation": "symmetry_behavior",
        "symmetry_reasoning": "symmetry_evidence",
        "density_modulation": "density_behavior",
    }

    def __init__(self):
        self.dependency_memory = {}
        self.evidence_log = []
        self.dependency_thresholds = {
            "validated": 0.80,
            "partial": 0.60,
            "provisional": 0.35,
            "minimum_transferability": 0.55,
            "critical_missing_penalty": 0.10,
        }
        self.supported_relation_types = {
            "depends_on",
            "supports",
            "causes",
            "explains",
            "invalidates",
            "context_requires",
            "context_strengthens",
            "context_weakens",
        }

    def _read(self, report, *keys, default=None):
        if not isinstance(report, dict):
            return default
        for key in keys:
            if key in report:
                return report[key]
        for value in report.values():
            if isinstance(value, dict):
                nested = self._read(value, *keys, default=None)
                if nested is not None:
                    return nested
        return default

    def _dependency(
        self,
        concept,
        dependency,
        relation="depends_on",
        source="runtime",
        value=None,
        evidence=None,
        required=True,
    ):
        return {
            "concept": concept,
            "dependency": dependency,
            "relation": relation,
            "source": source,
            "value": value,
            "evidence": dict(evidence or {}),
            "required": required,
        }

    def extract_dependencies(
        self,
        concept,
        context_report=None,
        semantic_context_report=None,
        causal_validation_report=None,
        truth_candidate_report=None,
        identity_report=None,
    ):
        context_report = context_report or {}
        semantic_context_report = semantic_context_report or {}
        causal_validation_report = causal_validation_report or {}
        truth_candidate_report = truth_candidate_report or {}
        identity_report = identity_report or {}

        dependencies = []
        primary = self.CONCEPT_PRIMARY_DEPENDENCY.get(concept)
        if primary:
            value = self._context_value(primary, context_report)
            dependencies.append(
                self._dependency(
                    concept,
                    primary,
                    source="concept_requirement",
                    value=value,
                    evidence=context_report,
                    required=True,
                )
            )

        properties = semantic_context_report.get("properties", [])
        if properties:
            dependencies.append(
                self._dependency(
                    concept,
                    "semantic_context",
                    relation="supports",
                    source="semantic_context_report",
                    value=semantic_context_report.get("context"),
                    evidence={
                        "properties": list(properties),
                        "confidence": semantic_context_report.get(
                            "confidence",
                            0.5,
                        ),
                    },
                    required=False,
                )
            )

        if causal_validation_report:
            dependencies.append(
                self._dependency(
                    concept,
                    "causal_graph_alignment",
                    relation="explains",
                    source="causal_validation_report",
                    value=causal_validation_report.get(
                        "causal_graph_alignment",
                    ),
                    evidence=causal_validation_report,
                    required=True,
                )
            )

        if truth_candidate_report.get("contradiction_review_required"):
            dependencies.append(
                self._dependency(
                    concept,
                    "contradiction_review",
                    relation="invalidates",
                    source="truth_candidate_report",
                    value=True,
                    evidence=truth_candidate_report,
                    required=True,
                )
            )

        identity_value = self._read(
            identity_report,
            "identity_behavior",
            "identity_status",
            default=self._context_value("identity_behavior", context_report),
        )
        if identity_value is not None or "identity" in context_report:
            dependencies.append(
                self._dependency(
                    concept,
                    "identity_behavior",
                    relation="depends_on",
                    source="identity_report",
                    value=identity_value or context_report.get("identity"),
                    evidence=identity_report or context_report,
                    required=concept in {
                        "identity_preservation",
                        "object_identity_preservation",
                    },
                )
            )

        return dependencies

    def _context_value(self, dependency, context_report):
        aliases = {
            "color_behavior": ["color_behavior", "color"],
            "structural_integrity": [
                "structural_integrity",
                "structure",
                "transformation",
            ],
            "topology_behavior": ["topology_behavior", "topology"],
            "spatial_alignment": ["spatial_alignment", "position"],
            "identity_behavior": ["identity_behavior", "identity"],
            "symmetry_behavior": ["symmetry_behavior", "symmetry"],
            "symmetry_evidence": ["symmetry_evidence", "symmetry"],
            "density_behavior": ["density_behavior", "density"],
        }
        for key in aliases.get(dependency, [dependency]):
            value = self._read(context_report, key, default=None)
            if value is not None:
                return value
        return None

    def classify_dependency(self, dependency):
        dependency = dependency if isinstance(dependency, dict) else {}
        name = str(dependency.get("dependency", ""))
        relation = dependency.get("relation")
        value = str(dependency.get("value", ""))
        source = dependency.get("source")
        evidence = dependency.get("evidence", {})
        classes = []

        if dependency.get("required"):
            classes.append("hard_dependency")
        else:
            classes.append("soft_dependency")
        if relation in {"causes", "explains"} or "causal" in name:
            classes.append("causal_dependency")
        if "context" in name or source == "semantic_context_report":
            classes.append("contextual_dependency")
        if "semantic" in name or source == "semantic_context_report":
            classes.append("semantic_dependency")
        if "identity" in name or "identity" in value:
            classes.append("identity_dependency")
        if name in {"structural_integrity", "shape_equivalence"}:
            classes.append("structural_dependency")
        if relation == "invalidates" or evidence.get(
            "contradiction_review_required",
        ):
            classes.append("contradiction_dependency")
        if not classes:
            classes.append("observational_dependency")
        if dependency.get("value") is None:
            classes.append("weak_dependency")

        dependency["dependency_types"] = sorted(set(classes))
        dependency["dependency_type"] = dependency["dependency_types"][0]
        return dependency

    def score_dependency(self, dependency):
        dependency = dependency if isinstance(dependency, dict) else {}
        evidence = dependency.get("evidence", {})
        dependency_types = set(dependency.get("dependency_types", []))
        causal_alignment = clamp(
            evidence.get(
                "causal_validation_score",
                evidence.get("causal_graph_alignment", 0.5),
            )
        )
        semantic_confidence = clamp(evidence.get("confidence", 0.5))
        contradiction = clamp(
            evidence.get(
                "effective_contradiction",
                evidence.get("contradiction_score", 0.0),
            )
        )
        value_present = dependency.get("value") is not None
        evidence_support = clamp(
            evidence.get(
                "support_score",
                0.75 if value_present else 0.35,
            )
        )
        dependency_strength = clamp(
            (
                evidence_support
                + causal_alignment
                + (0.8 if dependency.get("required") else 0.6)
            )
            / 3.0
        )
        dependency_stability = clamp(
            evidence.get(
                "dependency_coherence",
                evidence.get("context_consistency", 0.6 if value_present else 0.35),
            )
        )
        transferability = clamp(
            evidence.get(
                "transferability",
                evidence.get(
                    "context_transfer_reliability",
                    0.75 if value_present else 0.40,
                ),
            )
        )
        contradiction_resistance = clamp(1.0 - contradiction)
        if "contradiction_dependency" in dependency_types:
            dependency_strength = clamp(dependency_strength - 0.15)
            transferability = clamp(transferability - 0.20)
        confidence = clamp(
            (
                dependency_strength
                + dependency_stability
                + transferability
                + evidence_support
                + contradiction_resistance
                + semantic_confidence
            )
            / 6.0
        )
        scores = {
            "dependency_strength": dependency_strength,
            "dependency_stability": dependency_stability,
            "transferability": transferability,
            "evidence_support": evidence_support,
            "contradiction_resistance": contradiction_resistance,
            "dependency_confidence": confidence,
        }
        dependency["scores"] = scores
        return scores

    def validate_dependency(self, dependency):
        dependency = dependency if isinstance(dependency, dict) else {}
        scores = dependency.get("scores") or self.score_dependency(dependency)
        score = scores["dependency_confidence"]
        if dependency.get("value") is None and dependency.get("required"):
            status = "BLOCKED"
            reason = "required dependency is missing"
        elif score >= self.dependency_thresholds["validated"]:
            status = "VALIDATED"
            reason = "dependency confidence exceeds validation threshold"
        elif score >= self.dependency_thresholds["partial"]:
            status = "PARTIALLY_VALIDATED"
            reason = "dependency has useful but incomplete support"
        elif score >= self.dependency_thresholds["provisional"]:
            status = "PROVISIONAL"
            reason = "dependency requires more evidence"
        else:
            status = "BLOCKED"
            reason = "dependency evidence is too weak"
        return {
            "validated": status in {"VALIDATED", "PARTIALLY_VALIDATED"},
            "status": status,
            "reason": reason,
            "score": score,
        }

    def update_memory(self, dependency, validation_report):
        dependency = dict(dependency or {})
        key = (
            f"{dependency.get('concept')}::"
            f"{dependency.get('dependency')}::"
            f"{dependency.get('relation')}"
        )
        now = datetime.utcnow().isoformat()
        record = self.dependency_memory.setdefault(
            key,
            {
                "concept": dependency.get("concept"),
                "dependency": dependency.get("dependency"),
                "relation": dependency.get("relation"),
                "evidence_count": 0,
                "confidence": 0.0,
                "last_seen": None,
                "history": [],
            },
        )
        record["evidence_count"] += 1
        record["confidence"] = clamp(
            (
                record["confidence"] * (record["evidence_count"] - 1)
                + validation_report.get("score", 0.0)
            )
            / record["evidence_count"]
        )
        record["last_seen"] = now
        record["history"].append({
            "timestamp": now,
            "dependency": dependency,
            "validation": validation_report,
        })
        self.evidence_log.append(record["history"][-1])
        return {
            **record,
            "history": list(record["history"]),
        }

    def compute_dependency_coherence(self, dependencies):
        dependencies = list(dependencies or [])
        if not dependencies:
            return 0.0
        confidences = [
            item.get("validation", {}).get(
                "score",
                item.get("scores", {}).get("dependency_confidence", 0.0),
            )
            for item in dependencies
        ]
        validated_count = sum(
            1
            for item in dependencies
            if item.get("validation", {}).get("status")
            in {"VALIDATED", "PARTIALLY_VALIDATED"}
        )
        missing_critical = sum(
            1
            for item in dependencies
            if item.get("required") and item.get("value") is None
        )
        contradiction_penalties = sum(
            1
            for item in dependencies
            if "contradiction_dependency" in item.get("dependency_types", [])
        )
        transferability = [
            item.get("scores", {}).get("transferability", 0.0)
            for item in dependencies
        ]
        average_confidence = sum(confidences) / max(len(confidences), 1)
        validation_ratio = validated_count / max(len(dependencies), 1)
        transfer_score = sum(transferability) / max(len(transferability), 1)
        penalty = (
            missing_critical * self.dependency_thresholds[
                "critical_missing_penalty"
            ]
            + contradiction_penalties * 0.05
        )
        return clamp(
            (
                average_confidence
                + validation_ratio
                + transfer_score
            )
            / 3.0
            - penalty
        )

    def identify_missing_dependencies(self, concept, dependencies):
        observed = {
            item.get("dependency")
            for item in dependencies
            if item.get("value") is not None
        }
        required = set(self.CONCEPT_REQUIREMENTS.get(concept, []))
        return sorted(required - observed)

    def recommend_action(self, coherence_report):
        coherence = coherence_report.get("dependency_coherence", 0.0)
        missing = coherence_report.get("missing_dependencies", [])
        blocked = coherence_report.get("blocked_dependencies", [])
        provisional = coherence_report.get("provisional_dependencies", [])
        dependencies = coherence_report.get("dependencies", [])
        if blocked:
            if any(
                "identity_dependency" in item.get("dependency_types", [])
                and item.get("required")
                for item in blocked
            ):
                return "REQUIRE_IDENTITY_REVIEW"
            return "BLOCK_TRUTH_COMMIT"
        if missing and coherence < 0.80:
            if any(
                item in {
                    "color_mapping_rule",
                    "recolor_condition",
                    "connectivity_state",
                }
                for item in missing
            ):
                return "REQUIRE_CONTEXTUAL_TRUTH"
            return "HOLD_FOR_MORE_EVIDENCE"
        if any(
            "identity_dependency" in item.get("dependency_types", [])
            and item.get("required")
            and item.get("validation", {}).get("status") != "VALIDATED"
            for item in dependencies
        ):
            return "REQUIRE_IDENTITY_REVIEW"
        if any(
            "contradiction_dependency" in item.get("dependency_types", [])
            for item in dependencies
        ):
            return "REQUIRE_CAUSAL_REVIEW"
        if coherence >= 0.80 and not provisional and not missing:
            return "PROMOTE_TRUTH"
        if coherence >= 0.65:
            return "HOLD_FOR_MORE_EVIDENCE"
        return "REQUIRE_CAUSAL_REVIEW"

    def build_report(
        self,
        concept,
        dependencies,
        missing_dependencies,
        coherence_score,
    ):
        validated = [
            item
            for item in dependencies
            if item.get("validation", {}).get("status") == "VALIDATED"
        ]
        provisional = [
            item
            for item in dependencies
            if item.get("validation", {}).get("status")
            in {"PARTIALLY_VALIDATED", "PROVISIONAL"}
        ]
        blocked = [
            item
            for item in dependencies
            if item.get("validation", {}).get("status") == "BLOCKED"
        ]
        draft = {
            "system": "dependency_knowledge_engine",
            "concept": concept,
            "dependency_coherence": coherence_score,
            "validated_dependencies": validated,
            "provisional_dependencies": provisional,
            "blocked_dependencies": blocked,
            "missing_dependencies": missing_dependencies,
            "dependencies": dependencies,
            "explanation": [
                f"{len(validated)} dependencies validated",
                f"{len(provisional)} dependencies remain provisional",
                f"{len(blocked)} dependencies are blocked",
                (
                    "missing dependencies: "
                    + ", ".join(missing_dependencies)
                    if missing_dependencies
                    else "no required dependencies missing"
                ),
            ],
        }
        draft["recommended_action"] = self.recommend_action(draft)
        return draft

    def analyze(
        self,
        concept,
        context_report=None,
        semantic_context_report=None,
        causal_validation_report=None,
        truth_candidate_report=None,
        identity_report=None,
    ):
        dependencies = self.extract_dependencies(
            concept,
            context_report=context_report,
            semantic_context_report=semantic_context_report,
            causal_validation_report=causal_validation_report,
            truth_candidate_report=truth_candidate_report,
            identity_report=identity_report,
        )
        enriched = []
        for dependency in dependencies:
            classified = self.classify_dependency(dependency)
            self.score_dependency(classified)
            validation = self.validate_dependency(classified)
            classified["validation"] = validation
            classified["memory"] = self.update_memory(
                classified,
                validation,
            )
            enriched.append(classified)
        missing = self.identify_missing_dependencies(concept, enriched)
        coherence = self.compute_dependency_coherence(enriched)
        return self.build_report(concept, enriched, missing, coherence)


__all__ = [
    "DependencyKnowledgeEngine",
]
