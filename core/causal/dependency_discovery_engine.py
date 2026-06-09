from core.epistemic_models import clamp


class DependencyDiscoveryEngine:
    """Discovers dependency candidates from concept, context, and reports."""

    def __init__(self):
        self.concept_dependency_templates = {
            "shape_preservation": [
                "structural_integrity",
                "shape_equivalence",
                "object_boundary_consistency",
            ],
            "color_preservation": [
                "color_behavior",
                "color_mapping_rule",
                "recolor_condition",
                "attribute_remapping",
            ],
            "topology_preservation": [
                "topology_behavior",
                "connectivity_state",
                "topology_change_condition",
            ],
            "position_preservation": [
                "spatial_alignment",
                "translation_behavior",
                "coordinate_stability",
            ],
            "symmetry_preservation": [
                "symmetry_axis",
                "symmetry_behavior",
                "mirror_consistency",
            ],
            "symmetry_reasoning": [
                "symmetry_evidence",
                "axis_detection",
                "relational_balance",
            ],
            "object_identity_preservation": [
                "identity_behavior",
                "lineage_continuity",
                "causal_continuity",
                "topology_continuity",
            ],
            "density_modulation": [
                "density_behavior",
                "fill_pattern",
                "occupancy_change",
            ],
        }
        self.transformation_dependency_templates = {
            "duplication": [
                "object_count_increase",
                "identity_split",
                "topology_splitting",
                "shape_preservation_expected",
                "color_change_possible",
            ],
            "color_reassigned": [
                "color_mapping_rule",
                "recolor_condition",
                "attribute_remapping",
            ],
            "topology_splitting": [
                "topology_change_condition",
                "connectivity_change",
                "object_boundary_shift",
            ],
        }
        self.identity_dependency_templates = {
            "identity_split": [
                "lineage_continuity",
                "identity_branching",
                "descendant_identity_mapping",
            ],
            "identity_preserved": [
                "identity_continuity",
                "semantic_identity_stability",
            ],
        }
        self.semantic_dependency_templates = {
            "modifies_identity": [
                "identity_continuity_may_change",
                "identity_split_possible",
            ],
            "modifies_topology": [
                "topology_change_possible",
                "connectivity_state_required",
            ],
            "changes_color": [
                "color_mapping_rule",
                "recolor_condition",
            ],
            "preserves_shape": [
                "structural_integrity",
                "shape_equivalence",
            ],
        }
        self.discovery_thresholds = {
            "candidate": 0.50,
            "strong": 0.78,
            "low_coherence": 0.75,
            "alignment_ready": 0.85,
        }
        self.known_dependency_memory = {}

    def _candidate(
        self,
        source,
        target,
        relation="depends_on",
        dependency_type="observational_dependency",
        confidence=0.6,
        supporting_signals=None,
        risk_factors=None,
        context=None,
        missing_critical=False,
    ):
        return {
            "source": source,
            "target": target,
            "relation": relation,
            "dependency_type": dependency_type,
            "confidence": clamp(confidence),
            "supporting_signals": list(supporting_signals or []),
            "risk_factors": list(risk_factors or []),
            "context": dict(context or {}),
            "missing_critical": bool(missing_critical),
            "recommended_action": "VALIDATE_DEPENDENCY",
        }

    def _read(self, report, *keys, default=None):
        if not isinstance(report, dict):
            return default
        for key in keys:
            if key in report:
                return report[key]
        return default

    def discover(
        self,
        concept,
        context_report=None,
        semantic_context_report=None,
        truth_candidate_report=None,
        causal_validation_report=None,
        identity_report=None,
    ):
        context_report = dict(context_report or {})
        semantic_context_report = dict(semantic_context_report or {})
        truth_candidate_report = dict(truth_candidate_report or {})
        causal_validation_report = dict(causal_validation_report or {})
        identity_report = dict(identity_report or {})

        dependencies = []
        dependencies.extend(self.discover_concept_dependencies(concept))
        dependencies.extend(self.discover_context_dependencies(context_report))
        dependencies.extend(
            self.discover_semantic_dependencies(semantic_context_report)
        )
        dependencies.extend(
            self.discover_causal_dependencies(causal_validation_report)
        )
        dependencies.extend(
            self.discover_identity_dependencies(
                identity_report=identity_report,
                context_report=context_report,
            )
        )
        if truth_candidate_report.get("contradiction_review_required"):
            dependencies.append(
                self._candidate(
                    concept,
                    "contradiction_review",
                    relation="invalidates",
                    dependency_type="contradiction_dependency",
                    confidence=0.78,
                    supporting_signals=["truth_candidate_review_required"],
                    risk_factors=["contradiction_above_threshold"],
                    context=truth_candidate_report,
                )
            )

        dependencies = [
            {**item, "source": item.get("source") or concept}
            for item in dependencies
        ]
        merged = self.merge_dependencies(dependencies)
        ranked = self.rank_dependencies(merged)
        missing = self.identify_critical_missing_dependencies(
            concept,
            ranked,
        )
        return self.build_report(concept, ranked, missing)

    def discover_concept_dependencies(self, concept):
        return [
            self._candidate(
                concept,
                dependency,
                dependency_type=self._type_for_dependency(dependency),
                confidence=0.72,
                supporting_signals=["concept_template"],
                missing_critical=True,
            )
            for dependency in self.concept_dependency_templates.get(
                concept,
                [],
            )
        ]

    def discover_context_dependencies(self, context_report):
        context_report = context_report or {}
        dependencies = []
        transformation = self._read(
            context_report,
            "transformation",
            "transformation_family",
        )
        color = self._read(context_report, "color", "color_behavior")
        topology = self._read(context_report, "topology", "topology_behavior")
        identity = self._read(context_report, "identity", "identity_behavior")
        for signal in [transformation, color, topology]:
            for dependency in self.transformation_dependency_templates.get(
                signal,
                [],
            ):
                dependencies.append(
                    self._candidate(
                        signal or "context",
                        dependency,
                        dependency_type=self._type_for_dependency(dependency),
                        confidence=0.78,
                        supporting_signals=[f"context:{signal}"],
                        risk_factors=self._risk_for_dependency(dependency),
                        context=context_report,
                    )
                )
        for dependency in self.identity_dependency_templates.get(identity, []):
            dependencies.append(
                self._candidate(
                    identity,
                    dependency,
                    dependency_type="identity_dependency",
                    confidence=0.80,
                    supporting_signals=[f"context:{identity}"],
                    risk_factors=self._risk_for_dependency(dependency),
                    context=context_report,
                )
            )
        return dependencies

    def discover_semantic_dependencies(self, semantic_context_report):
        semantic_context_report = semantic_context_report or {}
        signals = []
        for key in ["properties", "capabilities", "constraints", "implications"]:
            values = semantic_context_report.get(key, [])
            if isinstance(values, str):
                values = [values]
            signals.extend(values or [])
        dependencies = []
        confidence = clamp(semantic_context_report.get("confidence", 0.7))
        for signal in signals:
            for dependency in self.semantic_dependency_templates.get(
                signal,
                [],
            ):
                dependencies.append(
                    self._candidate(
                        semantic_context_report.get("context", "semantic"),
                        dependency,
                        dependency_type=self._type_for_dependency(dependency),
                        confidence=max(confidence, 0.75),
                        supporting_signals=[f"semantic:{signal}"],
                        risk_factors=self._risk_for_dependency(dependency),
                        context=semantic_context_report,
                    )
                )
        return dependencies

    def discover_causal_dependencies(self, causal_validation_report):
        causal_validation_report = causal_validation_report or {}
        dependencies = []
        dependency_coherence = clamp(
            causal_validation_report.get("dependency_coherence", 1.0)
        )
        graph_alignment = clamp(
            causal_validation_report.get("causal_graph_alignment", 1.0)
        )
        context_consistency = clamp(
            causal_validation_report.get("context_consistency", 1.0)
        )
        if dependency_coherence < self.discovery_thresholds["low_coherence"]:
            dependencies.extend([
                self._candidate(
                    "causal_validation",
                    "missing_dependency_search_required",
                    dependency_type="causal_dependency",
                    confidence=0.82,
                    supporting_signals=["low_dependency_coherence"],
                    risk_factors=["dependency_gap"],
                    context=causal_validation_report,
                ),
                self._candidate(
                    "causal_validation",
                    "causal_link_strengthening_required",
                    dependency_type="causal_dependency",
                    confidence=0.80,
                    supporting_signals=["low_dependency_coherence"],
                    risk_factors=["weak_dependency_links"],
                    context=causal_validation_report,
                ),
            ])
        if graph_alignment < self.discovery_thresholds["alignment_ready"]:
            dependencies.extend([
                self._candidate(
                    "causal_validation",
                    "causal_graph_alignment_support",
                    dependency_type="causal_dependency",
                    confidence=0.78,
                    supporting_signals=["causal_alignment_below_target"],
                    risk_factors=["alignment_gap"],
                    context=causal_validation_report,
                ),
                self._candidate(
                    "causal_validation",
                    "root_cause_link_required",
                    dependency_type="causal_dependency",
                    confidence=0.78,
                    supporting_signals=["causal_alignment_below_target"],
                    risk_factors=["root_cause_gap"],
                    context=causal_validation_report,
                ),
            ])
        if context_consistency < self.discovery_thresholds["low_coherence"]:
            dependencies.extend([
                self._candidate(
                    "causal_validation",
                    "context_transfer_validation",
                    dependency_type="contextual_dependency",
                    confidence=0.80,
                    supporting_signals=["low_context_consistency"],
                    risk_factors=["context_transfer_gap"],
                    context=causal_validation_report,
                ),
                self._candidate(
                    "causal_validation",
                    "context_boundary_condition",
                    dependency_type="contextual_dependency",
                    confidence=0.80,
                    supporting_signals=["low_context_consistency"],
                    risk_factors=["context_boundary_unclear"],
                    context=causal_validation_report,
                ),
            ])
        return dependencies

    def discover_identity_dependencies(self, identity_report=None, context_report=None):
        identity_report = identity_report or {}
        context_report = context_report or {}
        identity = self._read(
            identity_report,
            "identity",
            "identity_behavior",
            "identity_status",
            default=self._read(context_report, "identity", "identity_behavior"),
        )
        dependencies = []
        for dependency in self.identity_dependency_templates.get(identity, []):
            dependencies.append(
                self._candidate(
                    identity,
                    dependency,
                    dependency_type="identity_dependency",
                    confidence=0.82,
                    supporting_signals=[f"identity:{identity}"],
                    risk_factors=self._risk_for_dependency(dependency),
                    context=identity_report or context_report,
                )
            )
        if identity_report.get("identity_governance_review_required"):
            for dependency in [
                "identity_repair_signal",
                "semantic_drift_containment",
                "identity_continuity_evidence",
            ]:
                dependencies.append(
                    self._candidate(
                        "identity_governance",
                        dependency,
                        dependency_type="identity_dependency",
                        confidence=0.76,
                        supporting_signals=["identity_review_required"],
                        risk_factors=["identity_governance_review"],
                        context=identity_report,
                    )
                )
        return dependencies

    def merge_dependencies(self, dependencies):
        merged = {}
        for dependency in list(dependencies or []):
            key = (
                dependency.get("source"),
                dependency.get("target"),
                dependency.get("relation"),
            )
            if key not in merged:
                merged[key] = {
                    **dependency,
                    "supporting_signals": list(
                        dependency.get("supporting_signals", [])
                    ),
                    "risk_factors": list(dependency.get("risk_factors", [])),
                    "_confidence_values": [dependency.get("confidence", 0.0)],
                }
                continue
            current = merged[key]
            current["_confidence_values"].append(
                dependency.get("confidence", 0.0)
            )
            current["confidence"] = clamp(
                sum(current["_confidence_values"])
                / len(current["_confidence_values"])
            )
            current["supporting_signals"] = sorted(set(
                current["supporting_signals"]
                + list(dependency.get("supporting_signals", []))
            ))
            current["risk_factors"] = sorted(set(
                current["risk_factors"]
                + list(dependency.get("risk_factors", []))
            ))
            current["missing_critical"] = (
                current.get("missing_critical")
                or dependency.get("missing_critical")
            )
        for dependency in merged.values():
            dependency.pop("_confidence_values", None)
        return list(merged.values())

    def rank_dependencies(self, dependencies):
        def risk_score(item):
            return len(item.get("risk_factors", [])) * 0.03

        return sorted(
            list(dependencies or []),
            key=lambda item: (
                item.get("missing_critical", False),
                item.get("confidence", 0.0) + risk_score(item),
                len(item.get("supporting_signals", [])),
            ),
            reverse=True,
        )

    def identify_critical_missing_dependencies(self, concept, dependencies):
        observed = {
            dependency.get("target")
            for dependency in list(dependencies or [])
        }
        required = set(self.concept_dependency_templates.get(concept, []))
        return sorted(required - observed)

    def build_report(self, concept, dependencies, missing_critical):
        top = list(dependencies or [])[:5]
        report = {
            "system": "dependency_discovery_engine",
            "concept": concept,
            "candidate_count": len(dependencies or []),
            "dependencies": list(dependencies or []),
            "critical_missing_dependencies": list(missing_critical or []),
            "top_candidates": top,
        }
        report["recommended_action"] = self.recommend_action(
            report["dependencies"],
            report["critical_missing_dependencies"],
        )
        self.known_dependency_memory[concept] = report
        return report

    def recommend_action(self, dependencies, missing_critical):
        dependencies = list(dependencies or [])
        if not dependencies:
            return "BLOCK_UNDERDETERMINED_DEPENDENCY"
        if missing_critical and not dependencies:
            return "BLOCK_UNDERDETERMINED_DEPENDENCY"
        if missing_critical:
            if any("identity" in item for item in missing_critical):
                return "REQUIRE_IDENTITY_DISCOVERY"
            return "REQUIRE_MORE_CONTEXT"
        if any(
            item.get("dependency_type") == "causal_dependency"
            and item.get("confidence", 0.0) < 0.65
            for item in dependencies
        ):
            return "REQUIRE_CAUSAL_DISCOVERY"
        return "SEND_TO_DEPENDENCY_KNOWLEDGE_ENGINE"

    def _type_for_dependency(self, dependency):
        if "identity" in dependency or "lineage" in dependency:
            return "identity_dependency"
        if "color" in dependency or "topology" in dependency:
            return "contextual_dependency"
        if "semantic" in dependency or "shape" in dependency:
            return "semantic_dependency"
        if "structural" in dependency or "boundary" in dependency:
            return "structural_dependency"
        if "causal" in dependency:
            return "causal_dependency"
        return "observational_dependency"

    def _risk_for_dependency(self, dependency):
        risks = []
        if "split" in dependency or "change" in dependency:
            risks.append("contextual_instability")
        if "identity" in dependency or "lineage" in dependency:
            risks.append("identity_review")
        if "mapping" in dependency or "recolor" in dependency:
            risks.append("contextual_truth_required")
        return risks


__all__ = [
    "DependencyDiscoveryEngine",
]
