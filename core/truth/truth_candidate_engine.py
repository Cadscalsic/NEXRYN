from core.epistemic_models import clamp
from core.context.context_strength_engine import ContextStrengthEngine
from core.knowledge.adaptive_contradiction_governance import (
    AdaptiveContradictionGovernance,
)
from core.knowledge.contradiction_review_policy import (
    SOFT_REVIEW_ZONE,
)
from core.process_abstraction import ProcessAbstractionLayer
from core.process_context_generation import ProcessContextGenerationEngine
from core.math_reasoning import MathematicalReasoningLayer
from runtime.context.context_surface_engine import ContextSurfaceEngine
from runtime.context.context_governance_registry import (
    ContextGovernanceRegistry,
)
from runtime.context.process_context_discovery_engine import (
    ProcessContextDiscoveryEngine,
)
from runtime.context.process_context_engine import ProcessContextEngine
from runtime.context.process_semantic_context_engine import (
    ProcessSemanticContextEngine,
)
from runtime.process.process_semantic_context_engine import (
    ProcessSemanticContextEngine as AlphaProcessSemanticContextEngine,
)
from runtime.process.process_dependency_ingestion import (
    ProcessDependencyIngestion,
)
from runtime.process.process_dependency_reasoner import (
    ProcessDependencyReasoner,
)
from runtime.process.process_dependency_validator import (
    ProcessDependencyValidator,
)
from runtime.context.context_taxonomy_engine import ContextTaxonomyEngine
from runtime.context.temporal_process_context_engine import (
    TemporalProcessContextEngine,
)
from runtime.dependency.dependency_coherence_engine import (
    DependencyCoherenceEngine,
)


class TruthCandidatePromotionEngine:
    MINIMUM_OBSERVED_TASKS = 8
    MINIMUM_CROSS_TASK_SUPPORT = 0.80
    MINIMUM_CAUSAL_STABILITY = 0.80
    MINIMUM_CONTEXT_STRENGTH = 0.69
    MINIMUM_IDENTITY_STRENGTH = 0.62
    MAXIMUM_CONTRADICTION = 0.10
    CONTRADICTION_REVIEW_ZONE = SOFT_REVIEW_ZONE

    WEIGHTS = {
        "observation_strength": 0.18,
        "cross_task_support": 0.20,
        "contradiction_governance": 0.18,
        "causal_stability": 0.18,
        "context_strength": 0.14,
        "identity_strength": 0.12,
    }
    PROCESS_CONCEPTS = {
        "growth",
        "propagation",
        "replication",
        "topological_growth",
        "directional_motion",
        "identity_persistence",
        "identity_forking",
        "duplication",
        "symmetry_reasoning",
    }

    def __init__(self):
        self.adaptive_contradiction_governance = (
            AdaptiveContradictionGovernance()
        )
        self.context_strength_engine = ContextStrengthEngine()
        self.context_surface_engine = ContextSurfaceEngine()
        self.context_governance_registry = ContextGovernanceRegistry()
        self.process_context_discovery_engine = ProcessContextDiscoveryEngine()
        self.process_context_engine = ProcessContextEngine()
        self.process_semantic_context_engine = ProcessSemanticContextEngine()
        self.alpha_process_semantic_context_engine = (
            AlphaProcessSemanticContextEngine()
        )
        self.process_dependency_ingestion = ProcessDependencyIngestion()
        self.process_dependency_validator = ProcessDependencyValidator()
        self.process_dependency_reasoner = ProcessDependencyReasoner()
        self.context_taxonomy_engine = ContextTaxonomyEngine()
        self.temporal_process_context_engine = TemporalProcessContextEngine()
        self.dependency_coherence_engine = DependencyCoherenceEngine()

    def _records(self, ledger_item):
        return [
            record
            for record in ledger_item.get("records", [])
            if isinstance(record, dict)
        ]

    def _average(self, records, key, default):
        values = [
            clamp(record.get(key))
            for record in records
            if record.get(key) is not None
        ]
        if not values:
            return clamp(default)
        return clamp(sum(values) / len(values))

    def _success_counts(self, records):
        successes = sum(record.get("success") is True for record in records)
        counterexamples = sum(
            record.get("success") is False
            for record in records
        )
        return successes, counterexamples

    def _runtime_evaluation(self, concept, truth_candidate_report):
        for item in truth_candidate_report.get("evaluations", []):
            if (
                isinstance(item, dict)
                and str(item.get("concept")) == concept
            ):
                return item
        return {}

    def _first_clamped(self, *values):
        for value in values:
            if value is not None:
                return clamp(value)
        return 0.0

    def _first_int(self, *values):
        for value in values:
            if value is None:
                continue
            try:
                return int(value or 0)
            except (TypeError, ValueError):
                continue
        return 0

    def _first_list(self, *values):
        for value in values:
            if isinstance(value, list):
                return list(value)
            if value:
                return list(value)
        return []

    def _nested_score(self, report, *paths, default=0.0):
        for path in paths:
            data = report
            for key in path:
                if not isinstance(data, dict):
                    data = None
                    break
                data = data.get(key)
            if data is not None:
                return clamp(data)
        return clamp(default)

    def _context_strength(self, runtime):
        process_semantic_models = runtime.get("process_semantic_models", {})
        process_semantic_strengths = []
        if isinstance(process_semantic_models, dict):
            process_semantic_strengths = [
                clamp(model.get("process_context_strength", 0.0))
                for model in process_semantic_models.values()
                if isinstance(model, dict)
            ]
        return max(
            self._nested_score(
                runtime,
                ("contextual_truth_authority", "effective_contextual_truth"),
                ("contextual_truth", "effective_contextual_truth"),
                ("contextual_truth", "contextual_truth_score"),
                default=0.0,
            ),
            self._nested_score(
                runtime,
                ("context_hierarchy", "context_hierarchy_score"),
                ("context_hierarchy", "score"),
                default=0.0,
            ),
            self._nested_score(
                runtime,
                ("semantic_context", "semantic_context_score"),
                ("semantic_context", "confidence"),
                default=0.0,
            ),
            *process_semantic_strengths,
        )

    def _identity_strength(self, runtime, ledger_item):
        return max(
            self._nested_score(
                runtime,
                ("identity_safe_truth_integration", "identity_continuity"),
                ("identity_safe_truth_integration", "identity_strength"),
                default=0.0,
            ),
            clamp(ledger_item.get("identity_strength", 0.0)),
        )

    def _causal_stability(self, records, ledger_item, runtime):
        return max(
            self._average(
                records,
                "causal_alignment",
                ledger_item.get("cross_task_support", 0.0),
            ),
            self._nested_score(
                runtime,
                ("causal_validation", "validation_score"),
                ("causal_graph_alignment", "alignment_score"),
                default=0.0,
            ),
        )

    def _dependency_promotion(self, concept, runtime):
        runtime = runtime if isinstance(runtime, dict) else {}
        causal_validation = runtime.get("causal_validation", {})
        causal_validation = (
            causal_validation
            if isinstance(causal_validation, dict)
            else {}
        )
        evidence = causal_validation.get("dependency_promotion_evidence", {})
        if not isinstance(evidence, dict):
            evidence = {}
        process_memory = runtime.get("process_dependency_memory", {})
        process_memory = (
            process_memory
            if isinstance(process_memory, dict)
            else {}
        )
        alignment = runtime.get("dependency_chain_alignment", {})
        alignment = alignment if isinstance(alignment, dict) else {}
        confidence = self._first_clamped(
            process_memory.get("dependency_confidence"),
            runtime.get("dependency_confidence"),
            causal_validation.get("dependency_confidence"),
            evidence.get("dependency_confidence"),
        )
        coverage = self._first_clamped(
            process_memory.get("dependency_chain_coverage"),
            runtime.get("dependency_chain_coverage"),
            causal_validation.get("dependency_chain_coverage"),
            evidence.get("dependency_chain_coverage"),
        )
        depth = self._first_int(
            process_memory.get("dependency_chain_depth"),
            runtime.get("dependency_chain_depth"),
            causal_validation.get("dependency_chain_depth"),
            evidence.get("dependency_chain_depth"),
        )
        missing_dependencies = self._first_list(
            process_memory.get("missing_dependencies"),
            runtime.get("missing_dependencies"),
            causal_validation.get("missing_dependencies"),
            evidence.get("missing_dependencies"),
        )
        blockers = []
        if confidence <= 0.85:
            blockers.append("dependency_confidence_below_promotion_floor")
        if missing_dependencies:
            blockers.append("dependency_chain_missing_dependencies")
        if depth < 4:
            blockers.append("dependency_chain_depth_below_promotion_floor")
        complete = (
            confidence > 0.85
            and not missing_dependencies
            and depth >= 4
        )
        depth_score = clamp(depth / 5.0)
        score = max(
            clamp(
                confidence * 0.46
                + coverage * 0.34
                + depth_score * 0.20
            ),
            clamp(runtime.get("promotion_dependency_score", 0.0)),
            clamp(causal_validation.get("promotion_dependency_score", 0.0)),
        )
        bonus = max(
            clamp(runtime.get("promotion_dependency_bonus", 0.0)),
            clamp(causal_validation.get("promotion_dependency_bonus", 0.0)),
            (
                round(min((score - 0.80) * 0.25, 0.08), 4)
                if complete and score > 0.80
                else 0.0
            ),
        )
        return {
            "promotion_dependency_score": round(score, 4),
            "promotion_dependency_bonus": bonus,
            "dependency_promotion_blockers": blockers,
            "dependency_confidence": confidence,
            "dependency_chain_depth": depth,
            "dependency_chain_coverage": coverage,
            "missing_dependencies": missing_dependencies,
            "dependency_alignment_ready":
            alignment.get("alignment_ready", False),
            "dependency_alignment_confidence":
            clamp(alignment.get("alignment_confidence", 0.0)),
            "process_dependency_memory": process_memory,
            "typed_process_dependencies_enabled": bool(
                process_memory.get("typed_dependency_relations")
                or (
                    runtime.get("typed_dependency_report", {}).get(
                        "typed_process_dependencies_enabled"
                    )
                    if isinstance(runtime.get("typed_dependency_report"), dict)
                    else False
                )
            ),
            "typed_dependency_relation_count": len(
                process_memory.get("typed_dependency_relations", [])
                if isinstance(process_memory, dict)
                else []
            ),
            "process_dependency_links_used":
            process_memory.get("process_dependency_links_used", depth)
            if isinstance(process_memory, dict)
            else depth,
            "process_dependency_links_loaded":
            process_memory.get("process_dependency_links_loaded", depth)
            if isinstance(process_memory, dict)
            else depth,
            "dependency_chain_complete_for_promotion": complete,
            "dependency_aware_promotion_applicable":
            concept in self.PROCESS_CONCEPTS,
        }

    def _consumable_process_context(self, report):
        if not isinstance(report, dict) or not report:
            return False
        return bool(
            report.get("process_context_generated")
            and (
                report.get("transition_steps")
                or report.get("transition_signature")
                or report.get("transitions")
            )
            and (
                report.get("postconditions")
                or report.get("final_state")
                or report.get("expected_outcomes")
            )
            and (
                report.get("preconditions")
                or report.get("initial_state")
            )
        )

    def _contradiction_governance(
        self,
        contradiction_score,
        cross_task_support,
        causal_stability,
        context_strength,
        context,
    ):
        governance = self.adaptive_contradiction_governance.evaluate(
            contradiction_score,
            context,
        )
        adaptive_soft_review_zone = (
            contradiction_score > self.MAXIMUM_CONTRADICTION
            and governance["contradiction_below_dynamic_threshold"]
        )
        soft_review_acceptable = (
            (
                governance["within_soft_review_zone"]
                or adaptive_soft_review_zone
            )
            and cross_task_support >= self.MINIMUM_CROSS_TASK_SUPPORT
            and causal_stability >= self.MINIMUM_CAUSAL_STABILITY
            and context_strength >= self.MINIMUM_CONTEXT_STRENGTH
        )
        passed = (
            governance["contradiction_below_dynamic_threshold"]
            or soft_review_acceptable
        )
        return {
            **governance,
            "contradiction_score": contradiction_score,
            "contradiction_threshold": governance["dynamic_threshold"],
            "base_contradiction_threshold": self.MAXIMUM_CONTRADICTION,
            "adaptive_soft_review_zone": adaptive_soft_review_zone,
            "soft_review_acceptable_for_candidate_promotion":
            soft_review_acceptable,
            "passed": passed,
        }

    def _observed_contradictions(self, records, runtime):
        observed = []
        for record in records:
            for key in (
                "contradiction_target",
                "contradiction_concept",
                "conflicting_dependency",
                "conflict",
            ):
                if record.get(key):
                    observed.append(str(record[key]))
            if record.get("identity_runtime_split") is True:
                observed.append("identity_split")
        runtime_items = runtime.get("observed_contradictions", [])
        if isinstance(runtime_items, str):
            observed.append(runtime_items)
        else:
            try:
                observed.extend(str(item) for item in runtime_items if item)
            except TypeError:
                pass
        return observed

    def _typed_dependency_report(self, concept, runtime):
        existing = runtime.get("typed_dependency_report", {})
        if isinstance(existing, dict) and existing.get(
            "typed_process_dependencies_enabled"
        ):
            return existing
        process_memory = runtime.get("process_dependency_memory", {})
        if isinstance(process_memory, dict) and process_memory.get(
            "typed_dependency_relations"
        ):
            links = process_memory.get("typed_dependency_relations", [])
            return {
                **process_memory,
                "typed_process_dependencies": "enabled",
                "typed_process_dependencies_enabled": True,
                "typed_dependency_relations": links,
                "process_dependency_links_used":
                process_memory.get("process_dependency_links_used", len(links)),
                "process_dependency_links_loaded":
                process_memory.get("process_dependency_links_loaded", len(links)),
                "relevant_process_dependency_links": len(links),
            }
        if concept in self.PROCESS_CONCEPTS:
            return self.process_dependency_ingestion.resolve_for_process(concept)
        return {}

    def _dependency_aware_contradiction_score(
        self,
        concept,
        contradiction_score,
        typed_dependency_reasoning,
    ):
        if concept not in self.PROCESS_CONCEPTS:
            return contradiction_score
        if typed_dependency_reasoning.get("exact_blocker"):
            return contradiction_score
        if typed_dependency_reasoning.get("typed_process_dependencies") == "enabled":
            return min(contradiction_score, 0.08)
        return contradiction_score

    def _normalized_task_score(self, observed_task_count):
        return clamp(observed_task_count / self.MINIMUM_OBSERVED_TASKS)

    def evaluate(
        self,
        ledger_item,
        truth_candidate_report=None,
    ):
        truth_candidate_report = truth_candidate_report or {}
        concept = str(ledger_item.get("concept", ""))
        process_abstraction = ProcessAbstractionLayer.get(concept)
        records = self._records(ledger_item)
        runtime = self._runtime_evaluation(concept, truth_candidate_report)
        math_reasoning_report = runtime.get("math_reasoning_report", {})
        math_reasoning_report = (
            math_reasoning_report
            if isinstance(math_reasoning_report, dict)
            else {}
        )
        if not math_reasoning_report and isinstance(
            runtime.get("process_dependency_memory"),
            dict,
        ):
            math_reasoning_report = (
                MathematicalReasoningLayer().analyze_dependency_chain(
                    concept,
                    process_dependency_memory=runtime.get(
                        "process_dependency_memory",
                        {},
                    ),
                )
            )
        process_context_generation = runtime.get("process_context_report", {})
        process_context_generation = (
            process_context_generation
            if isinstance(process_context_generation, dict)
            else {}
        )
        process_context_engine_report = runtime.get(
            "process_context_engine_report",
            {},
        )
        process_context_engine_report = (
            process_context_engine_report
            if isinstance(process_context_engine_report, dict)
            else {}
        )
        temporal_process_context_report = runtime.get(
            "temporal_process_context_report",
            {},
        )
        temporal_process_context_report = (
            temporal_process_context_report
            if isinstance(temporal_process_context_report, dict)
            else {}
        )
        process_semantic_context_report = runtime.get(
            "process_semantic_context_report",
            {},
        )
        process_semantic_context_report = (
            process_semantic_context_report
            if isinstance(process_semantic_context_report, dict)
            else {}
        )
        dependency_semantics_report = runtime.get(
            "dependency_semantics_report",
            math_reasoning_report.get("dependency_semantics_report", {}),
        )
        dependency_semantics_report = (
            dependency_semantics_report
            if isinstance(dependency_semantics_report, dict)
            else {}
        )
        if not dependency_semantics_report:
            dependency_semantics_report = math_reasoning_report.get(
                "dependency_semantics_report",
                {},
            )
        process_context_discovery_report = runtime.get(
            "process_context_discovery_report",
            {},
        )
        process_context_discovery_report = (
            process_context_discovery_report
            if isinstance(process_context_discovery_report, dict)
            else {}
        )
        typed_dependency_report = self._typed_dependency_report(concept, runtime)
        typed_dependency_validation_report = (
            self.process_dependency_validator.validate(typed_dependency_report)
            if typed_dependency_report
            else {}
        )
        typed_dependency_reasoning_report = (
            self.process_dependency_reasoner.reason(
                concept,
                typed_dependency_report,
                observed_contradictions=self._observed_contradictions(
                    records,
                    runtime,
                ),
            )
            if typed_dependency_report
            else {}
        )
        if typed_dependency_report:
            runtime = {
                **runtime,
                "typed_dependency_report": typed_dependency_report,
                "typed_dependency_validation_report":
                typed_dependency_validation_report,
                "typed_dependency_reasoning_report":
                typed_dependency_reasoning_report,
                "process_dependency_memory": {
                    **(
                        runtime.get("process_dependency_memory", {})
                        if isinstance(
                            runtime.get("process_dependency_memory"),
                            dict,
                        )
                        else {}
                    ),
                    **typed_dependency_report,
                },
            }
            if not dependency_semantics_report:
                dependency_semantics_report = {
                    "system": "typed_process_dependency_memory",
                    "typed_process_dependencies": "enabled",
                    "dependency_semantics_score":
                    typed_dependency_reasoning_report.get(
                        "dependency_semantics_score",
                        typed_dependency_report.get(
                            "dependency_confidence",
                            0.0,
                        ),
                    ),
                    "typed_dependencies":
                    typed_dependency_report.get(
                        "typed_dependency_relations",
                        [],
                    ),
                    "semantic_dependency_signature": {
                        "typed_process_dependencies": True,
                        "dependency_type_coverage":
                        typed_dependency_report.get(
                            "dependency_type_coverage",
                            [],
                        ),
                    },
                }
        if not process_context_discovery_report and process_abstraction:
            process_context_discovery_report = (
                self.process_context_discovery_engine.discover(
                    concept,
                    dependency_chain=runtime.get(
                        "process_dependency_memory",
                        {},
                    ),
                    runtime_context=runtime,
                )
            )
            runtime = {
                **runtime,
                "process_context_discovery_report":
                process_context_discovery_report,
            }
        if (
            not self._consumable_process_context(process_context_generation)
            and process_context_discovery_report.get(
                "process_context_discovered"
            )
        ):
            process_context_generation = (
                self.process_context_discovery_engine.as_process_context_report(
                    process_context_discovery_report,
                )
            )
            runtime = {
                **runtime,
                "process_context_report": process_context_generation,
            }
        if not process_context_engine_report and process_abstraction:
            process_context_engine_report = self.process_context_engine.evaluate(
                concept,
                dependency_chain=runtime.get("process_dependency_memory", {}),
                transformational_identity=runtime.get(
                    "transformational_identity",
                    runtime.get(
                        "identity_runtime_report",
                        runtime.get("identity_safe_truth_integration", {}),
                    ),
                ),
                runtime_context=runtime,
            )
            runtime = {
                **runtime,
                "process_context_engine_report":
                process_context_engine_report,
            }
        if not temporal_process_context_report and process_abstraction:
            temporal_process_context_report = (
                self.temporal_process_context_engine.evaluate(
                    concept,
                    dependency_chain=runtime.get("process_dependency_memory", {}),
                    transformational_identity=runtime.get(
                        "transformational_identity",
                        runtime.get(
                            "identity_runtime_report",
                            runtime.get("identity_safe_truth_integration", {}),
                        ),
                    ),
                    runtime_context={
                        **runtime,
                        "process_context_engine_report":
                        process_context_engine_report,
                    },
                )
            )
            runtime = {
                **runtime,
                "temporal_process_context_report":
                temporal_process_context_report,
            }
        if (
            not dependency_semantics_report
            and (
                temporal_process_context_report.get(
                    "process_context_ready",
                )
                is True
                or process_context_engine_report.get(
                    "process_context_ready",
                )
                is True
            )
        ):
            dependency_semantics_report = (
                self.temporal_process_context_engine.dependency_semantics_report(
                    temporal_process_context_report,
                )
                if temporal_process_context_report.get(
                    "process_context_ready",
                )
                is True
                else self.process_context_engine.dependency_semantics_report(
                    process_context_engine_report,
                )
            )
            runtime = {
                **runtime,
                "dependency_semantics_report": dependency_semantics_report,
            }
        if not process_semantic_context_report and process_abstraction:
            process_semantic_context_report = (
                self.process_semantic_context_engine.synthesize(
                    concept,
                    dependency_chain=runtime.get("process_dependency_memory", {}),
                    transformational_identity=runtime.get(
                        "transformational_identity",
                        runtime.get(
                            "identity_runtime_report",
                            runtime.get("identity_safe_truth_integration", {}),
                        ),
                    ),
                    runtime_context={
                        **runtime,
                        "process_context_discovery_report":
                        process_context_discovery_report,
                        "process_context_engine_report":
                        process_context_engine_report,
                        "temporal_process_context_report":
                        temporal_process_context_report,
                    },
                )
            )
            runtime = {
                **runtime,
                "process_semantic_context_report":
                process_semantic_context_report,
            }
        if process_semantic_context_report.get(
            "process_semantic_context_synthesized"
        ):
            process_context_generation = {
                **process_context_generation,
                **process_semantic_context_report,
                "supporting_math_evidence": {
                    **process_context_generation.get(
                        "supporting_math_evidence",
                        {},
                    ),
                    **process_semantic_context_report.get(
                        "supporting_math_evidence",
                        {},
                    ),
                },
                "process_context_generated": True,
            }
            runtime = {
                **runtime,
                "process_context_report": process_context_generation,
            }
            if not dependency_semantics_report:
                dependency_semantics_report = (
                    self.process_semantic_context_engine
                    .dependency_semantics_report(process_semantic_context_report)
                )
                runtime = {
                    **runtime,
                    "dependency_semantics_report": dependency_semantics_report,
                }
        if (
            process_abstraction
            and concept in self.PROCESS_CONCEPTS
            and not self._consumable_process_context(process_context_generation)
            and runtime.get("process_dependency_memory")
        ):
            dependency_signal = self._dependency_promotion(concept, runtime)
            alpha_process_context_report = (
                self.alpha_process_semantic_context_engine.synthesize(
                    concept,
                    dependency_chain=runtime.get("process_dependency_memory", {}),
                    runtime_context={
                        **runtime,
                        "dependency_confidence":
                        dependency_signal["dependency_confidence"],
                        "promotion_dependency_score":
                        dependency_signal["promotion_dependency_score"],
                        "identity_runtime_continuity":
                        self._identity_strength(runtime, ledger_item),
                        "causal_alignment":
                        self._causal_stability(records, ledger_item, runtime),
                        "contradiction_score":
                        self._average(
                            records,
                            "contradiction_score",
                            runtime.get(
                                "effective_contradiction_score",
                                ledger_item.get(
                                    "average_contradiction_score",
                                    1.0,
                                ),
                            ),
                        ),
                    },
                )
            )
            if alpha_process_context_report.get("process_context_generated"):
                process_context_generation = {
                    **process_context_generation,
                    **alpha_process_context_report,
                    "supporting_math_evidence": {
                        **process_context_generation.get(
                            "supporting_math_evidence",
                            {},
                        ),
                        **alpha_process_context_report.get(
                            "supporting_math_evidence",
                            {},
                        ),
                    },
                    "process_context_generated": True,
                }
                runtime = {
                    **runtime,
                    "process_context_report": process_context_generation,
                    "alpha_process_context_report":
                    alpha_process_context_report,
                }
        context_surface_report = runtime.get("context_surface_report", {})
        context_surface_report = (
            context_surface_report
            if isinstance(context_surface_report, dict)
            else {}
        )
        if not context_surface_report and process_abstraction:
            context_surface_report = (
                self.context_surface_engine.evaluate(
                    concept,
                    dependency_chain=(
                        runtime.get("process_dependency_memory", {})
                        .get("resolved_dependency_chain", [])
                        if isinstance(
                            runtime.get("process_dependency_memory"),
                            dict,
                        )
                        else []
                    ),
                    process_signature=math_reasoning_report.get(
                        "process_signature_report",
                        {},
                    ),
                    semantic_context=runtime.get("semantic_context", {}),
                    task_metadata=runtime.get("task_metadata", {}),
                    transformation_traces=runtime.get(
                        "transformation_execution_trace",
                        runtime.get("execution_trace", []),
                    ),
                    execution_histories=runtime.get(
                        "execution_histories",
                        runtime.get("execution_history", []),
                    ),
                    object_statistics=runtime.get("object_statistics", {}),
                    spatial_relations=runtime.get("spatial_relations", {}),
                    topology_descriptors=runtime.get(
                        "topology_descriptors",
                        {},
                    ),
                    runtime_context=runtime,
                )
            )
            runtime = {
                **runtime,
                "context_surface_report": context_surface_report,
            }
        if not process_context_generation:
            process_context_generation = (
                ProcessContextGenerationEngine().generate_context(
                    concept,
                    math_reasoning_report=math_reasoning_report,
                    dependency_semantics_report=dependency_semantics_report,
                    context=runtime,
                )
            )
        context_taxonomy_report = runtime.get("context_taxonomy_report", {})
        context_taxonomy_report = (
            context_taxonomy_report
            if isinstance(context_taxonomy_report, dict)
            else {}
        )
        if not context_taxonomy_report:
            context_taxonomy_report = (
                self.context_taxonomy_engine.classify_runtime_context({
                    **runtime,
                    "concept": concept,
                    "semantic_context": runtime.get("semantic_context", {}),
                    "process_context_report": process_context_generation,
                })
            )
            runtime = {
                **runtime,
                "context_taxonomy_report": context_taxonomy_report,
            }
            known_contexts = context_taxonomy_report.get("known_contexts", [])
            if known_contexts and not runtime.get("semantic_context"):
                runtime = {
                    **runtime,
                    "semantic_context": known_contexts[0],
                }
        if (
            process_context_engine_report.get("process_context_ready") is True
        ):
            process_context_generation = {
                **process_context_generation,
                **process_context_engine_report,
                "supporting_math_evidence": {
                    **process_context_generation.get(
                        "supporting_math_evidence",
                        {},
                    ),
                    **process_context_engine_report.get(
                        "supporting_math_evidence",
                        {},
                    ),
                },
                "process_context_generated": True,
                "process_context_ready": True,
            }
            runtime = {
                **runtime,
                "process_context_report": process_context_generation,
            }
        if (
            temporal_process_context_report.get("process_context_ready") is True
        ):
            process_context_generation = {
                **process_context_generation,
                **temporal_process_context_report,
                "supporting_math_evidence": {
                    **process_context_generation.get(
                        "supporting_math_evidence",
                        {},
                    ),
                    **temporal_process_context_report.get(
                        "supporting_math_evidence",
                        {},
                    ),
                },
                "process_context_generated": True,
                "process_context_ready": True,
            }
            runtime = {
                **runtime,
                "process_context_report": process_context_generation,
            }
        context_governance_report = runtime.get(
            "context_governance_report",
            {},
        )
        context_governance_report = (
            context_governance_report
            if isinstance(context_governance_report, dict)
            else {}
        )
        if not context_governance_report:
            context_governance_report = (
                self.context_governance_registry.register_runtime_contexts(
                    runtime
                )
            )
            runtime = {
                **runtime,
                "context_governance_report":
                context_governance_report,
            }
        governance_process_context = (
            self.context_governance_registry.process_context_report(concept)
        )
        if governance_process_context:
            process_context_generation = {
                **process_context_generation,
                **governance_process_context,
                "supporting_math_evidence": {
                    **process_context_generation.get(
                        "supporting_math_evidence",
                        {},
                    ),
                    **governance_process_context.get(
                        "supporting_math_evidence",
                        {},
                    ),
                },
                "process_context_generated": True,
                "process_context_ready": True,
            }
            runtime = {
                **runtime,
                "process_context_report": process_context_generation,
                "context_governance_report": context_governance_report,
            }
        dependency_coherence_report = runtime.get(
            "dependency_coherence_report",
            {},
        )
        dependency_coherence_report = (
            dependency_coherence_report
            if isinstance(dependency_coherence_report, dict)
            else {}
        )
        if not dependency_coherence_report and process_abstraction:
            process_memory = runtime.get("process_dependency_memory", {})
            process_memory = (
                process_memory
                if isinstance(process_memory, dict)
                else {}
            )
            dependency_coherence_report = (
                self.dependency_coherence_engine.evaluate(
                    concept,
                    dependency_chain=(
                        process_memory
                        or math_reasoning_report.get(
                            "process_dependency_chain",
                            [],
                        )
                    ),
                    semantic_contexts=[
                        runtime.get("semantic_context", {}),
                        process_context_generation,
                    ],
                    contextual_truth_reports=[
                        runtime.get("contextual_truth", {}),
                        runtime.get("contextual_truth_authority", {}),
                    ],
                    transformation_traces=runtime.get(
                        "transformation_execution_trace",
                        runtime.get("execution_trace", []),
                    ),
                    task_metadata=runtime.get("task_metadata", {}),
                    process_signature=math_reasoning_report.get(
                        "process_signature_report",
                        {},
                    ),
                    runtime_context={
                        **runtime,
                        "context_surface_report": context_surface_report,
                    },
                )
            )
            runtime = {
                **runtime,
                "dependency_coherence_report": dependency_coherence_report,
            }
        successful_tasks, counterexample_tasks = self._success_counts(
            records,
        )
        observed_task_count = int(ledger_item.get("used_task_count", 0))
        cross_task_support = clamp(
            ledger_item.get(
                "cross_task_support",
                ledger_item.get("independent_success_rate", 0.0),
            )
        )
        contradiction_score = self._average(
            records,
            "contradiction_score",
            runtime.get(
                "effective_contradiction_score",
                ledger_item.get("average_contradiction_score", 1.0),
            ),
        )
        raw_contradiction_score = contradiction_score
        contradiction_score = self._dependency_aware_contradiction_score(
            concept,
            contradiction_score,
            typed_dependency_reasoning_report,
        )
        base_context_strength = max(
            self._context_strength(runtime),
            clamp(ledger_item.get("context_strength", 0.0)),
        )
        math_context_strength = (
            self.context_strength_engine.consume_math_reasoning(
                base_context_strength,
                math_reasoning_report=math_reasoning_report,
                process_context_report=process_context_generation,
                dependency_semantics_report=dependency_semantics_report,
                runtime_context=runtime,
            )
        )
        context_strength = math_context_strength["final_context_strength"]
        process_context_ready = (
            concept not in self.PROCESS_CONCEPTS
            or bool(
                process_context_generation.get("process_context_ready")
                and math_context_strength["process_context_strength"] > 0.0
            )
        )
        identity_strength = self._identity_strength(runtime, ledger_item)
        identity_observed = identity_strength > 0.0
        if not identity_observed:
            identity_strength = 0.75
        causal_stability = self._causal_stability(
            records,
            ledger_item,
            runtime,
        )
        dependency_promotion = self._dependency_promotion(concept, runtime)
        dependency_bonus = (
            dependency_promotion["promotion_dependency_bonus"]
            if dependency_promotion["dependency_aware_promotion_applicable"]
            else 0.0
        )
        raw_causal_stability = causal_stability
        causal_stability = max(
            causal_stability,
            clamp(causal_stability + dependency_bonus),
            (
                dependency_promotion["promotion_dependency_score"]
                if (
                    dependency_promotion[
                        "dependency_chain_complete_for_promotion"
                    ]
                    and dependency_promotion[
                        "dependency_aware_promotion_applicable"
                    ]
                )
                else 0.0
            ),
        )
        contradiction_governance = self._contradiction_governance(
            contradiction_score,
            cross_task_support,
            causal_stability,
            context_strength,
            {
                "knowledge_generalization": ledger_item,
                "truth_candidate": runtime,
                **runtime,
            },
        )
        readiness_gates = {
            "observed_task_count":
            observed_task_count >= self.MINIMUM_OBSERVED_TASKS,
            "cross_task_support":
            cross_task_support >= self.MINIMUM_CROSS_TASK_SUPPORT,
            "contradiction_governance":
            contradiction_governance["passed"],
            "causal_stability":
            causal_stability >= self.MINIMUM_CAUSAL_STABILITY,
            "context_strength":
            context_strength >= self.MINIMUM_CONTEXT_STRENGTH,
            "process_context_ready":
            process_context_ready,
            "identity_strength":
            identity_strength >= self.MINIMUM_IDENTITY_STRENGTH,
        }
        dependency_promotion_blockers = list(
            dependency_promotion["dependency_promotion_blockers"]
        )
        component_scores = {
            "observation_strength":
            self._normalized_task_score(observed_task_count),
            "cross_task_support": cross_task_support,
            "contradiction_governance": (
                1.0
                if contradiction_governance["passed"]
                else clamp(
                    1.0
                    - contradiction_governance["contradiction_gap"]
                    / max(self.CONTRADICTION_REVIEW_ZONE, 0.0001)
                )
            ),
            "causal_stability": causal_stability,
            "context_strength": context_strength,
            "identity_strength": identity_strength,
        }
        promotion_score = clamp(
            sum(
                component_scores[name] * weight
                for name, weight in self.WEIGHTS.items()
            )
        )
        candidate_ready = all(readiness_gates.values())
        remaining_blockers_after_dependency = [
            gate
            for gate, passed in readiness_gates.items()
            if not passed
        ]
        if (
            dependency_promotion["dependency_chain_complete_for_promotion"]
            and dependency_promotion[
                "dependency_aware_promotion_applicable"
            ]
            and not candidate_ready
        ):
            dependency_promotion_blockers.extend(
                f"promotion_gate_blocked:{gate}"
                for gate in remaining_blockers_after_dependency
            )
        mixed_outcomes = bool(successful_tasks and counterexample_tasks)
        decision = (
            "PROMOTE_TO_TRUTH_CANDIDATE"
            if candidate_ready
            else "CONTINUE_BOUNDARY_REFINEMENT"
            if mixed_outcomes
            else "CONTINUE_GENERALIZATION"
            if observed_task_count >= self.MINIMUM_OBSERVED_TASKS
            else "CONTINUE_DISCOVERY"
        )

        return {
            "system": "truth_candidate_promotion_engine",
            "phase": "5.6",
            "concept": concept,
            "decision": decision,
            "candidate_ready": candidate_ready,
            "promotion_score": promotion_score,
            "promotion_dependency_score":
            dependency_promotion["promotion_dependency_score"],
            "promotion_dependency_bonus": dependency_bonus,
            "dependency_promotion_blockers":
            dependency_promotion_blockers,
            "dependency_confidence":
            dependency_promotion["dependency_confidence"],
            "dependency_chain_depth":
            dependency_promotion["dependency_chain_depth"],
            "dependency_chain_coverage":
            dependency_promotion["dependency_chain_coverage"],
            "missing_dependencies":
            dependency_promotion["missing_dependencies"],
            "process_dependency_memory":
            dependency_promotion["process_dependency_memory"],
            "dependency_alignment_ready":
            dependency_promotion["dependency_alignment_ready"],
            "dependency_alignment_confidence":
            dependency_promotion["dependency_alignment_confidence"],
            "dependency_chain_complete_for_promotion":
            dependency_promotion["dependency_chain_complete_for_promotion"],
            "readiness_gates": readiness_gates,
            "failed_gates": [
                gate
                for gate, passed in readiness_gates.items()
                if not passed
            ],
            "component_scores": component_scores,
            "observed_task_count": observed_task_count,
            "successful_task_count": successful_tasks,
            "counterexample_task_count": counterexample_tasks,
            "mixed_outcomes_detected": mixed_outcomes,
            "cross_task_support": cross_task_support,
            "average_contradiction_score": contradiction_score,
            "raw_average_contradiction_score": raw_contradiction_score,
            "typed_dependency_contradiction_adjusted":
            contradiction_score != raw_contradiction_score,
            "causal_stability": causal_stability,
            "raw_causal_stability": raw_causal_stability,
            "context_strength": context_strength,
            "base_context_strength": base_context_strength,
            "process_context_strength":
            math_context_strength["process_context_strength"],
            "math_reasoning_consumed":
            math_context_strength["math_reasoning_consumed"],
            "process_context_status":
            math_context_strength["process_context_status"],
            "process_context_ready": process_context_ready,
            "dependency_semantics_score":
            math_context_strength["dependency_semantics_score"],
            "context_strength_before_math":
            math_context_strength["context_strength_before_math"],
            "context_strength_after_math":
            math_context_strength["context_strength_after_math"],
            "math_reasoning_evidence_used":
            math_context_strength["math_reasoning_evidence_used"],
            "math_reasoning_evidence_rejected":
            math_context_strength["math_reasoning_evidence_rejected"],
            "evidence_used":
            math_context_strength["evidence_used"],
            "evidence_rejected":
            math_context_strength["evidence_rejected"],
            "rejection_reasons":
            math_context_strength["rejection_reasons"],
            "process_abstraction_ready": bool(process_abstraction),
            "process_abstraction": (
                process_abstraction.as_dict()
                if process_abstraction
                else {}
            ),
            "process_context_generation": process_context_generation,
            "context_governance_report": context_governance_report,
            "context_taxonomy_report": context_taxonomy_report,
            "process_context_discovery_report":
            process_context_discovery_report,
            "process_context_engine_report": process_context_engine_report,
            "temporal_process_context_report":
            temporal_process_context_report,
            "process_semantic_context_report":
            process_semantic_context_report,
            "typed_dependency_report": typed_dependency_report,
            "typed_dependency_validation_report":
            typed_dependency_validation_report,
            "typed_dependency_reasoning_report":
            typed_dependency_reasoning_report,
            "typed_process_dependencies":
            typed_dependency_report.get("typed_process_dependencies"),
            "architecture_bottleneck":
            typed_dependency_report.get("architecture_bottleneck", False),
            "recommended_next_step":
            typed_dependency_report.get(
                "recommended_next_step",
                "consume_reasoned_dependency_chains",
            ),
            "exact_blocker":
            typed_dependency_reasoning_report.get("exact_blocker", []),
            "process_dependency_links_used":
            typed_dependency_reasoning_report.get(
                "process_dependency_links_used",
                dependency_promotion.get("process_dependency_links_used", 0),
            ),
            "process_dependency_links_loaded":
            typed_dependency_report.get(
                "process_dependency_links_loaded",
                dependency_promotion.get("process_dependency_links_loaded", 0),
            ),
            "process_dependency_relevance_rate":
            typed_dependency_reasoning_report.get(
                "process_dependency_relevance_rate",
                0.0,
            ),
            "process_dependency_links_used_above_threshold":
            typed_dependency_reasoning_report.get(
                "process_dependency_links_used_above_threshold",
                False,
            ),
            "reasoned_dependency_chain":
            typed_dependency_report.get("reasoned_dependency_chain", {}),
            "reasoned_dependency_chain_available":
            bool(typed_dependency_report.get("reasoned_dependency_chain")),
            "reasoned_dependency_coherence_average":
            typed_dependency_report.get(
                "dependency_coherence_average",
                0.0,
            ),
            "dependency_explanation_quality":
            typed_dependency_report.get(
                "dependency_explanation_quality",
                typed_dependency_reasoning_report.get(
                    "dependency_explanation_quality",
                    0.0,
                ),
            ),
            "explanation_quality":
            typed_dependency_report.get(
                "explanation_quality",
                typed_dependency_report.get(
                    "dependency_explanation_quality",
                    0.0,
                ),
            ),
            "dependency_reasoning_report":
            typed_dependency_report.get("dependency_reasoning_report", ""),
            "process_context_generated": bool(
                process_context_generation.get("process_context_generated")
            ),
            "context_surface_report": context_surface_report,
            "dependency_coherence_report": dependency_coherence_report,
            "dependency_coherence":
            dependency_coherence_report.get("dependency_coherence", 0.0),
            "stable_dependencies":
            dependency_coherence_report.get("stable_dependencies", []),
            "fragile_dependencies":
            dependency_coherence_report.get("fragile_dependencies", []),
            "hidden_dependency_contradictions":
            dependency_coherence_report.get("hidden_contradictions", []),
            "context_surface_score":
            context_surface_report.get("context_surface_score", 0.0),
            "context_saturation":
            context_surface_report.get("context_saturation", 0.0),
            "context_surface_promotion_readiness":
            context_surface_report.get("promotion_readiness", False),
            "context_strength_evidence": {
                "contextual_truth": self._nested_score(
                    runtime,
                    (
                        "contextual_truth_authority",
                        "effective_contextual_truth",
                    ),
                    ("contextual_truth", "effective_contextual_truth"),
                    ("contextual_truth", "contextual_truth_score"),
                    default=0.0,
                ),
                "context_hierarchy": self._nested_score(
                    runtime,
                    ("context_hierarchy", "context_hierarchy_score"),
                    ("context_hierarchy", "score"),
                    default=0.0,
                ),
                "semantic_context": self._nested_score(
                    runtime,
                    ("semantic_context", "semantic_context_score"),
                    ("semantic_context", "confidence"),
                    default=0.0,
                ),
                "ledger_context_strength":
                clamp(ledger_item.get("context_strength", 0.0)),
                "process_context_strength":
                math_context_strength["process_context_strength"],
                "math_reasoning_used":
                math_context_strength["math_reasoning_used"],
                "context_surface":
                context_surface_report.get("context_strength_estimate", 0.0),
                "dependency_coherence":
                dependency_coherence_report.get("dependency_coherence", 0.0),
            },
            "identity_strength": identity_strength,
            "identity_strength_observed": identity_observed,
            "contradiction_governance": contradiction_governance,
            "formal_lifecycle_path": [
                "DISCOVERING",
                "BOUNDARY_REFINEMENT",
                "TRUTH_CANDIDATE",
                "STABLE_TRUTH",
            ],
            "truth_commit_still_requires_identity_and_trials": True,
        }


__all__ = [
    "TruthCandidatePromotionEngine",
]
