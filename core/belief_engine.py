import json

from core.confidence_calibration import ConfidenceCalibrator
from core.learning.curriculum_manager import LearningCurriculumManager
from core.learning.evidence_integration_engine import (
    LearningEvidenceIntegrationEngine,
)
from core.learning.experience_replay_buffer import ExperienceReplayBuffer
from core.epistemic_models import Belief, BeliefState, Hypothesis, clamp, utcnow
from core.epistemic_trials import EpistemicTrialEngine
from core.evidence_registry import EvidenceRegistry
from runtime.belief_registry import BeliefRegistry
from runtime.belief_promotion_engine import BeliefPromotionEngine
from runtime.active_knowledge_acquisition_engine import (
    ActiveKnowledgeAcquisitionEngine,
)
from runtime.evidence_gap_analyzer import EvidenceGapAnalyzer
from runtime.causal_effect_analyzer import CausalEffectAnalyzer
from runtime.counterexample_engine import CounterexampleEngine
from runtime.curriculum_manager import CurriculumManager
from runtime.boundary_refinement_engine import BoundaryRefinementEngine
from runtime.evidence_integration_engine import EvidenceIntegrationEngine
from runtime.experiment_result_evaluator import ExperimentResultEvaluator
from runtime.causal_evidence_arbitration_engine import (
    CausalEvidenceArbitrationEngine,
)
from runtime.causal_attestation_engine import CausalAttestationEngine
from runtime.contradiction_resolution_engine import (
    ContradictionResolutionEngine,
)
from runtime.truth_candidate_engine import TruthCandidateEngine
from runtime.truth_advancement_planner import TruthAdvancementPlanner
from runtime.truth_commitment_engine import TruthCommitmentEngine
from runtime.identity_safe_truth_integration import (
    IdentitySafeTruthIntegrationEngine,
)
from runtime.adaptive_identity_integration_engine import (
    AdaptiveIdentityIntegrationEngine,
)
from runtime.truth_internalization_engine import (
    TruthInternalizationEngine,
)
from runtime.identity_repair_engine import IdentityRepairEngine
from runtime.semantic_spine_recovery_engine import (
    SemanticSpineRecoveryEngine,
)
from runtime.reversible_rehearsal_executor import (
    ReversibleRehearsalExecutor,
)
from runtime.experiment_hypothesis_generator import (
    ExperimentHypothesisGenerator,
)
from runtime.epistemic_weight_recalibration_engine import (
    EpistemicWeightRecalibrationEngine,
)
from runtime.epistemic_evidence_fusion_engine import (
    EpistemicEvidenceFusionEngine,
)
from runtime.evidence_replication_engine import EvidenceReplicationEngine
from runtime.knowledge_replication_ledger import KnowledgeReplicationLedger
from runtime.knowledge_generalization_engine import (
    KnowledgeGeneralizationEngine,
)
from runtime.sandbox_experiment_executor import SandboxExperimentExecutor
from runtime.sandbox_experiment_runner import SandboxExperimentRunner
from core.knowledge.truth_state_authority import TruthStateAuthority
from core.causality.causal_alignment_engine import CausalAlignmentEngine
from core.causality.causal_evidence_accumulator import (
    CausalEvidenceAccumulator,
)
from core.causality.causal_graph_validator import CausalGraphValidator
from core.causal_graph import CausalGraph
from core.causal_validation import CausalValidationEngine
from core.context_discovery import ContextDiscoveryEngine
from core.context import ContextConsistencyEngine
from core.contextual_truth import ContextualTruthEngine
from core.context_hierarchy import ContextDifferentiationEngine, ContextHierarchy
from core.semantic_context import SemanticContextReasoner
from core.identity.identity_continuity_engine import IdentityContinuityEngine
from core.perception import SceneGraphEngine
from runtime.causal import RuntimeCausalAlignmentEngine
from core.dependency.process_dependency_graph import ProcessDependencyGraph


class BeliefEngine:
    def __init__(self):
        self.registry = BeliefRegistry()
        self.beliefs = self.registry.registry
        self.promotion_engine = BeliefPromotionEngine()

    def update(self, hypothesis, aggregate, trials, calibrated_confidence):
        belief = self.registry.get_or_create(
            hypothesis.concept,
            hypothesis.claim,
        )
        promotion = self.promotion_engine.evaluate(
            aggregate,
            trials,
            calibrated_confidence,
        )
        state = promotion["state"]

        belief.state = state
        belief.confidence = clamp(calibrated_confidence)
        belief.evidence_strength = aggregate.evidence_strength
        belief.contradiction_score = aggregate.contradiction_score
        belief.trial_count = len(trials)
        belief.updated_at = utcnow()
        belief.history.append({
            "state": state.value,
            "confidence": belief.confidence,
            "evidence_strength": belief.evidence_strength,
            "trial_count": belief.trial_count,
            "timestamp": belief.updated_at.isoformat(),
            "promotion": {
                "blocked_gates":
                promotion["blocked_gates"],
                "trial_counts": {
                    "total": promotion["total_trials"],
                    "passed": promotion["passed_trials"],
                    "failed": promotion["failed_trials"],
                    "inconclusive": promotion["inconclusive_trials"],
                },
                "gate_diagnostics":
                promotion["gate_diagnostics"],
            },
        })
        belief.history = belief.history[-64:]
        self.beliefs[belief.concept] = belief
        return belief, promotion

    def decay(self, concept, decay_rate=0.05):
        belief = self.beliefs[concept]
        belief.confidence = clamp(belief.confidence - decay_rate)
        belief.updated_at = utcnow()
        if (
            belief.state
            in [
                BeliefState.ESTABLISHED,
                BeliefState.VALIDATED,
                BeliefState.TRUTH_CANDIDATE,
            ]
            and belief.confidence < 0.78
        ):
            belief.state = BeliefState.SUPPORTED
        elif belief.state == BeliefState.SUPPORTED and belief.confidence < 0.64:
            belief.state = BeliefState.PROBATION
        return belief

    def revoke(self, concept):
        return self.registry.revoke(concept)

    def archive(self, concept):
        return self.registry.archive(concept)


class EpistemicCognitionLayer:
    def __init__(
        self,
        truth_registry_path=None,
        provisional_truth_registry_path=None,
        knowledge_replication_ledger_path=None,
        semantic_spine_recovery_path=None,
        reversible_rehearsal_state_path=None,
        causal_evidence_ledger_path=None,
        causal_validation_ledger_path=None,
    ):
        self.evidence_registry = EvidenceRegistry()
        self.knowledge_replication_ledger = KnowledgeReplicationLedger(
            storage_path=knowledge_replication_ledger_path
        )
        self.knowledge_generalization_engine = (
            KnowledgeGeneralizationEngine(
                self.knowledge_replication_ledger
            )
        )
        self.epistemic_evidence_fusion_engine = (
            EpistemicEvidenceFusionEngine(
                self.knowledge_replication_ledger
            )
        )
        self.evidence_registry.fusion_engine = (
            self.epistemic_evidence_fusion_engine
        )
        self.hydrated_replication_evidence_count = 0
        for evidence in self.knowledge_replication_ledger.evidence_exports():
            self.evidence_registry.collect(evidence)
            self.hydrated_replication_evidence_count += 1
        self.trial_engine = EpistemicTrialEngine(self.evidence_registry)
        self.confidence_calibrator = ConfidenceCalibrator()
        self.belief_engine = BeliefEngine()
        self.causal_attestation_engine = CausalAttestationEngine()
        self.contradiction_resolution_engine = (
            ContradictionResolutionEngine()
        )
        self.truth_candidate_engine = TruthCandidateEngine()
        self.identity_safe_truth_integration_engine = (
            IdentitySafeTruthIntegrationEngine()
        )
        self.adaptive_identity_integration_engine = (
            AdaptiveIdentityIntegrationEngine()
        )
        self.truth_internalization_engine = TruthInternalizationEngine()
        self.identity_repair_engine = IdentityRepairEngine()
        self.semantic_spine_recovery_engine = SemanticSpineRecoveryEngine(
            storage_path=semantic_spine_recovery_path
        )
        self.reversible_rehearsal_executor = ReversibleRehearsalExecutor(
            storage_path=reversible_rehearsal_state_path
        )
        self.truth_advancement_planner = TruthAdvancementPlanner()
        self.experiment_hypothesis_generator = (
            ExperimentHypothesisGenerator()
        )
        self.active_knowledge_acquisition_engine = (
            ActiveKnowledgeAcquisitionEngine()
        )
        self.evidence_gap_analyzer = EvidenceGapAnalyzer()
        self.sandbox_experiment_executor = SandboxExperimentExecutor()
        self.causal_effect_analyzer = CausalEffectAnalyzer()
        self.experiment_result_evaluator = ExperimentResultEvaluator(
            self.causal_effect_analyzer
        )
        self.sandbox_experiment_runner = SandboxExperimentRunner(
            self.sandbox_experiment_executor,
            self.experiment_result_evaluator,
        )
        self.curriculum_manager = CurriculumManager()
        self.boundary_refinement_engine = BoundaryRefinementEngine()
        self.experience_replay_buffer = ExperienceReplayBuffer()
        self.learning_curriculum_manager = LearningCurriculumManager()
        self.learning_evidence_integration_engine = (
            LearningEvidenceIntegrationEngine(
                self.experience_replay_buffer
            )
        )
        self.causal_evidence_arbitration_engine = (
            CausalEvidenceArbitrationEngine()
        )
        self.epistemic_weight_recalibration_engine = (
            EpistemicWeightRecalibrationEngine()
        )
        self.evidence_replication_engine = EvidenceReplicationEngine(
            ledger=self.knowledge_replication_ledger
        )
        self.evidence_integration_engine = EvidenceIntegrationEngine(
            self.active_knowledge_acquisition_engine,
            self.evidence_registry,
        )
        self.counterexample_engine = CounterexampleEngine(
            self.knowledge_replication_ledger
        )
        self.truth_commit_engine = TruthCommitmentEngine(
            truth_registry_path=truth_registry_path,
            provisional_truth_registry_path=
            provisional_truth_registry_path,
        )
        self.truth_state_authority = TruthStateAuthority()
        self.causal_alignment_engine = CausalAlignmentEngine()
        self.runtime_causal_alignment_engine = (
            RuntimeCausalAlignmentEngine()
        )
        self.process_dependency_graph = ProcessDependencyGraph()
        self.causal_graph = CausalGraph()
        self.causal_validation_engine = CausalValidationEngine(
            storage_path=causal_validation_ledger_path
        )
        self.context_discovery_engine = ContextDiscoveryEngine()
        self.context_consistency_engine = ContextConsistencyEngine()
        self.contextual_truth_engine = ContextualTruthEngine()
        self.context_hierarchy = ContextHierarchy()
        self.context_differentiation_engine = ContextDifferentiationEngine(
            self.context_hierarchy
        )
        self.semantic_context_reasoner = SemanticContextReasoner()
        self.scene_graph_engine = SceneGraphEngine()
        self.identity_continuity_engine = IdentityContinuityEngine()
        self.causal_graph_validator = CausalGraphValidator(
            evidence_accumulator=CausalEvidenceAccumulator(
                storage_path=causal_evidence_ledger_path
            )
        )

    def _hypotheses(self, context):
        hypotheses = context.get("epistemic_hypotheses", [])
        if isinstance(hypotheses, dict):
            hypotheses = [hypotheses]
        return [
            item if isinstance(item, Hypothesis) else Hypothesis(**item)
            for item in hypotheses
        ]

    def _scene_graph_comparison(self, context):
        existing = context.get("scene_graph_comparison")
        if isinstance(existing, dict):
            return existing
        input_grid = context.get("input_grid")
        output_grid = context.get("output_grid")
        if input_grid is None or output_grid is None:
            task = context.get("task", {})
            if isinstance(task, dict):
                input_grid = input_grid if input_grid is not None else task.get(
                    "input_grid",
                )
                output_grid = (
                    output_grid
                    if output_grid is not None
                    else task.get("output_grid")
                )
        if input_grid is None or output_grid is None:
            return {}
        try:
            return self.scene_graph_engine.compare_scene_graphs(
                input_grid,
                output_grid,
            )
        except (TypeError, ValueError, KeyError):
            return {}

    def _grid_pair(self, context):
        input_grid = context.get("input_grid")
        output_grid = context.get("output_grid")
        if input_grid is None or output_grid is None:
            task = context.get("task", {})
            if isinstance(task, dict):
                input_grid = input_grid if input_grid is not None else task.get(
                    "input_grid",
                )
                output_grid = (
                    output_grid
                    if output_grid is not None
                    else task.get("output_grid")
                )
        if input_grid is None or output_grid is None:
            task_path = context.get("task_path")
            if task_path:
                try:
                    with open(task_path, "r", encoding="utf-8") as handle:
                        task_data = json.load(handle)
                    train_examples = task_data.get("train", [])
                    if train_examples:
                        first = train_examples[0]
                        input_grid = (
                            input_grid
                            if input_grid is not None
                            else first.get("input")
                        )
                        output_grid = (
                            output_grid
                            if output_grid is not None
                            else first.get("output")
                        )
                except (OSError, TypeError, ValueError, KeyError):
                    return None
        if input_grid is None or output_grid is None:
            return None
        return input_grid, output_grid

    IDENTITY_RUNTIME_TRANSFORMATION_FAMILIES = {
        "identity_preservation",
        "growth",
        "duplication",
        "replication",
        "propagation",
        "topological_growth",
        "topology_expansion",
    }
    IDENTITY_RUNTIME_BEHAVIORS = {
        "identity_modified",
        "identity_split",
        "identity_merged",
        "identity_propagated",
        "object_split",
        "object_merge",
    }
    IDENTITY_RUNTIME_CONCEPTS = {
        "object_identity_preservation",
        "identity_preservation",
        "growth",
        "topological_growth",
        "duplication",
        "replication",
        "propagation",
    }

    def _should_run_identity_runtime(
        self,
        context,
        concept,
        context_discovery,
    ):
        context = context if isinstance(context, dict) else {}
        context_discovery = (
            context_discovery
            if isinstance(context_discovery, dict)
            else {}
        )
        signature = context_discovery.get("context_signature", {})
        signature = signature if isinstance(signature, dict) else {}
        concept = str(concept or "").lower()
        family = str(
            context_discovery.get(
                "transformation_family",
                signature.get("transformation_family", ""),
            )
            or ""
        ).lower()
        identity_behavior = str(
            context_discovery.get(
                "identity_behavior",
                signature.get(
                    "identity_behavior",
                    context.get("identity_behavior", context.get("identity", "")),
                ),
            )
            or ""
        ).lower()
        return (
            concept in self.IDENTITY_RUNTIME_CONCEPTS
            or family in self.IDENTITY_RUNTIME_TRANSFORMATION_FAMILIES
            or identity_behavior in self.IDENTITY_RUNTIME_BEHAVIORS
        )

    def _identity_runtime_context(self, context, concept, context_discovery):
        if not self._should_run_identity_runtime(
            context,
            concept,
            context_discovery,
        ):
            return {}
        grid_pair = self._grid_pair(context)
        if grid_pair is None:
            return {}
        try:
            report = self.identity_continuity_engine.run_identity_runtime(
                list(grid_pair),
                concept=concept,
            )
        except (TypeError, ValueError, KeyError):
            return {}
        return {
            "identity_runtime_report": report,
            "identity_continuity_runtime_report": report,
            **report.get("truth_commit_context_patch", {}),
        }

    def run_cycle(self, context):
        context = context if isinstance(context, dict) else {}
        scene_graph_comparison = self._scene_graph_comparison(context)
        if scene_graph_comparison:
            context = {
                **context,
                "scene_graph_comparison": scene_graph_comparison,
            }
        self.sandbox_experiment_runner.register(
            context.get("sandbox_execution_requests", [])
        )
        curriculum = self.curriculum_manager.plan(
            self.sandbox_experiment_executor.pending_requests.values(),
            [
                self.boundary_refinement_engine.report_for(
                    request["concept"]
                )
                for request
                in self.sandbox_experiment_executor.pending_requests.values()
            ],
        )
        learning_curriculum = self.learning_curriculum_manager.plan(
            self.sandbox_experiment_executor.pending_requests.values(),
            [
                self.boundary_refinement_engine.report_for(
                    request["concept"]
                )
                for request
                in self.sandbox_experiment_executor.pending_requests.values()
            ],
        )
        sandbox_cases = self.curriculum_manager.merge_cases(
            context.get("autonomous_sandbox_experiment_cases", []),
            curriculum["sandbox_cases"],
        )
        sandbox_experimentation = self.sandbox_experiment_runner.run(
            None,
            context.get("sandbox_experiment_worlds", {}),
            sandbox_cases,
        )
        sandbox_execution = sandbox_experimentation["sandbox_execution"]
        experiment_result_evaluation = sandbox_experimentation[
            "result_evaluation"
        ]
        causal_effect_analysis = experiment_result_evaluation[
            "causal_effect_analysis"
        ]
        weight_recalibration = (
            self.epistemic_weight_recalibration_engine.evaluate(
                self.evidence_registry,
                causal_effect_analysis["measurements"],
            )
        )
        supplied_sandbox_results = context.get(
            "sandbox_experiment_results",
            [],
        )
        if isinstance(supplied_sandbox_results, dict):
            supplied_sandbox_results = [supplied_sandbox_results]
        sandbox_results = [
            *causal_effect_analysis["measurements"],
            *supplied_sandbox_results,
        ]
        evidence_integration = self.evidence_integration_engine.integrate(
            sandbox_results
        )
        learning_evidence_integration = (
            self.learning_evidence_integration_engine.record(
                evidence_integration["integrated_evidence"]
            )
        )
        acquisition_ingestion = evidence_integration["ingestion"]
        replication_ingestion = self.evidence_replication_engine.ingest_results(
            context.get("arc_replication_results", [])
        )
        for item in replication_ingestion["epistemic_evidence_exports"]:
            self.evidence_registry.collect(item)
        for item in context.get("epistemic_evidence", []):
            self.evidence_registry.collect(item)

        hypotheses = self._hypotheses(context)
        arbitration_evaluations = []
        arbitration_by_concept = {}
        for concept in dict.fromkeys(
            hypothesis.concept
            for hypothesis in hypotheses
        ):
            arbitration = (
                self.causal_evidence_arbitration_engine.evaluate(
                    self.evidence_registry,
                    concept,
                )
            )
            arbitration_evaluations.append(arbitration)
            arbitration_by_concept[concept] = arbitration

        evaluations = []
        for hypothesis in hypotheses:
            trial = self.trial_engine.run_trial(hypothesis)
            aggregate = self.evidence_registry.aggregate(hypothesis.concept)
            evidence_fusion = (
                self.epistemic_evidence_fusion_engine.report_for(
                    hypothesis.concept
                )
            )
            trials = self.trial_engine.trials_for(hypothesis.concept)
            trial_resolution = self.trial_engine.latest_resolution(
                hypothesis.concept,
            )
            causal_attestation = self.causal_attestation_engine.evaluate(
                hypothesis.concept,
                aggregate,
                self.evidence_registry.evidence_for(
                    hypothesis.concept,
                ),
                self.evidence_registry.epistemic_partition(
                    hypothesis.concept,
                ),
                arbitration_by_concept.get(hypothesis.concept),
            )
            concept_evidence = self.evidence_registry.evidence_for(
                hypothesis.concept,
            )
            causal_spine = self.causal_graph.build_causal_spine(
                hypothesis.concept,
                observations=concept_evidence,
                truth_claim=f"{hypothesis.concept} is stable",
                confidence=aggregate.causal_alignment,
                originating_tasks=context.get(
                    "originating_tasks",
                    context.get("task_ids", []),
                ),
                context=context,
            )
            causal_graph_alignment = (
                self.causal_graph.compute_causal_alignment(
                    hypothesis.concept,
                )
            )
            causal_explanation = self.causal_graph.explain_truth(
                hypothesis.concept,
            )
            process_dependency_memory = (
                self.process_dependency_graph.resolve_dependency_chain(
                    hypothesis.concept,
                )
            )
            causal_validation = (
                self.causal_validation_engine.validate_hypothesis(
                    {
                        "source_concept": hypothesis.concept,
                        "target_concept": hypothesis.concept,
                        "confidence": aggregate.causal_alignment,
                    },
                    concept_evidence,
                    {
                        **context,
                        "process_dependency_memory":
                        process_dependency_memory,
                        "dependency_confidence":
                        process_dependency_memory.get(
                            "dependency_confidence",
                            0.0,
                        ),
                        "dependency_chain_depth":
                        process_dependency_memory.get(
                            "dependency_chain_depth",
                            0,
                        ),
                        "dependency_chain_coverage":
                        process_dependency_memory.get(
                            "dependency_chain_coverage",
                            0.0,
                        ),
                        "missing_dependencies":
                        process_dependency_memory.get(
                            "missing_dependencies",
                            [],
                        ),
                        "causal_graph_alignment":
                        causal_graph_alignment,
                        "dependency_coherence":
                        causal_graph_alignment.get(
                            "components",
                            {},
                        ).get("dependency_coherence", 0.0),
                        "identity_compatibility":
                        context.get(
                            "identity_continuity",
                            context.get("identity_compatibility", 1.0),
                        ),
                        "scene_graph_comparison": scene_graph_comparison,
                    },
                    self.causal_graph,
                )
            )
            context_discovery = (
                self.context_discovery_engine.discover_context(
                    {
                        **context,
                        "task_id": context.get(
                            "task_id",
                            hypothesis.concept,
                        ),
                        "concept": hypothesis.concept,
                    }
                )
            )
            identity_runtime_context = self._identity_runtime_context(
                context,
                hypothesis.concept,
                context_discovery,
            )
            discovered_context_context = {
                **context,
                **identity_runtime_context,
                "context_discovery": context_discovery,
            }
            if (
                context_discovery["transformation_family"] != "unknown"
                or context_discovery["confidence"] >= 0.50
            ):
                discovered_context_context[
                    "discovered_context_signature"
                ] = context_discovery["context_signature"]
            context_hierarchy = (
                self.context_differentiation_engine.refine_clusters([
                    context_discovery
                ])
            )
            semantic_context = (
                self.semantic_context_reasoner.generate_semantic_profile(
                    context_discovery,
                    concept_evidence,
                )
            )
            context_consistency = {}
            if scene_graph_comparison:
                context_consistency = self.context_consistency_engine.analyze(
                    hypothesis.concept,
                    context_report=context_discovery.get(
                        "context_signature",
                        context_discovery,
                    ),
                    semantic_context_report=semantic_context,
                    contextual_truth_report={},
                    scene_graph_report=scene_graph_comparison,
                )
            discovered_context_context[
                "context_hierarchy"
            ] = context_hierarchy
            discovered_context_context[
                "semantic_context"
            ] = semantic_context
            if context_consistency:
                discovered_context_context[
                    "context_consistency"
                ] = context_consistency
            contextual_truth = (
                self.contextual_truth_engine.generate_contextual_truth_report(
                    hypothesis.concept,
                    discovered_context_context,
                    causal_validation,
                    identity_runtime_context.get(
                        "identity_continuity",
                        context.get(
                            "identity_continuity",
                            context.get("identity_compatibility", 1.0),
                        ),
                    ),
                )
            )
            context_binding = contextual_truth.get("context_binding", {})
            if context_consistency:
                causal_validation["context_consistency"] = max(
                    causal_validation.get("context_consistency", 0.0),
                    context_consistency.get("context_consistency", 0.0),
                )
            if context_binding:
                causal_validation["context_binding"] = context_binding
                causal_validation["context_consistency"] = max(
                    causal_validation.get("context_consistency", 0.0),
                    context_binding.get("context_binding_score", 0.0),
                )
            causal_spine_alignment = self.causal_alignment_engine.evaluate(
                hypothesis.concept,
                max(
                    aggregate.causal_alignment,
                    causal_graph_alignment["alignment_score"],
                ),
                self.truth_commit_engine.registry,
                {
                    **context,
                    **identity_runtime_context,
                    "process_dependency_memory":
                    process_dependency_memory,
                    "causal_graph_alignment": causal_graph_alignment,
                    "causal_validation": causal_validation,
                    "contextual_truth": contextual_truth,
                    "context_discovery": context_discovery,
                    "context_hierarchy": context_hierarchy,
                    "semantic_context": semantic_context,
                },
            )
            causal_boundary_alignment = (
                self.runtime_causal_alignment_engine.evaluate(
                    hypothesis.concept,
                    aggregate,
                    context,
                )
            )
            causal_graph_validation = self.causal_graph_validator.evaluate(
                hypothesis.concept,
                context.get("semantic_graph", {}),
                {
                    **context,
                    "causal_graph_alignment": causal_graph_alignment,
                    "causal_explanation": causal_explanation,
                    "causal_validation": causal_validation,
                    "process_dependency_memory":
                    process_dependency_memory,
                    "contextual_truth": contextual_truth,
                    "context_discovery": context_discovery,
                    "context_hierarchy": context_hierarchy,
                    "semantic_context": semantic_context,
                },
            )
            contradiction_resolution = (
                self.contradiction_resolution_engine.evaluate(
                    hypothesis.concept,
                    aggregate,
                    self.evidence_registry.evidence_for(
                        hypothesis.concept,
                    ),
                    self.evidence_registry.effective_evidence_weight,
                    self.evidence_registry.epistemic_partition(
                        hypothesis.concept,
                    ),
                )
            )
            aggregate.contradiction_score = contradiction_resolution[
                "effective_contradiction_score"
            ]
            calibration = self.confidence_calibrator.calibrate(
                hypothesis, aggregate, trials
            )
            belief, promotion = self.belief_engine.update(
                hypothesis,
                aggregate,
                trials,
                calibration["calibrated_confidence"],
            )
            active_truth = self.truth_commit_engine.registry.retrieve_record(
                hypothesis.concept,
            )
            self.truth_state_authority.lock_belief_state(
                belief,
                active_truth,
            )
            knowledge_generalization = (
                self.knowledge_generalization_engine.evaluate(
                    hypothesis.concept,
                    aggregate.evidence_strength,
                    replication_bonus_already_applied=True,
                )
            )
            contextual_truth_authority = {}
            candidate = self.truth_candidate_engine.evaluate(
                belief,
                aggregate,
                {
                    **context,
                    "knowledge_generalization":
                    knowledge_generalization,
                    "process_dependency_memory":
                    process_dependency_memory,
                    "causal_boundary_alignment":
                    causal_boundary_alignment,
                    "causal_graph_alignment":
                    causal_graph_alignment,
                    "causal_explanation":
                    causal_explanation,
                    "causal_validation":
                    causal_validation,
                    "contextual_truth":
                    contextual_truth,
                    "contextual_truth_authority":
                    contextual_truth_authority,
                    "context_discovery":
                    context_discovery,
                    "context_hierarchy":
                    context_hierarchy,
                    "semantic_context":
                    semantic_context,
                },
            )
            contextual_truth = candidate.get(
                "contextual_truth",
                contextual_truth,
            )
            contextual_truth_authority = candidate.get(
                "contextual_truth_authority",
                {},
            )
            context_hierarchy = candidate.get(
                "context_hierarchy",
                context_hierarchy,
            )
            semantic_context = candidate.get(
                "semantic_context",
                semantic_context,
            )
            causal_failure_analysis = self.counterexample_engine.evaluate(
                hypothesis.concept
            )
            boundary_refinement = self.boundary_refinement_engine.evaluate(
                hypothesis.concept,
                causal_failure_analysis,
            )
            evidence_gap_analysis = self.evidence_gap_analyzer.evaluate(
                hypothesis.concept,
                knowledge_generalization,
                causal_failure_analysis,
                candidate,
            )
            adaptive_identity_integration = (
                self.adaptive_identity_integration_engine.evaluate(
                    hypothesis.concept,
                    aggregate,
                    candidate,
                    sum(
                        item.state == BeliefState.TRUTH_CANDIDATE
                        for item in self.belief_engine.beliefs.values()
                    ),
                    {
                        **context,
                        "knowledge_generalization":
                        knowledge_generalization,
                        "process_dependency_memory":
                        process_dependency_memory,
                    },
                    self.truth_commit_engine.registry,
                )
            )
            semantic_spine_recovery = (
                self.semantic_spine_recovery_engine.report_for(
                    belief.concept,
                )
            )
            integration_context = {
                **context,
                **identity_runtime_context,
                "process_dependency_memory":
                process_dependency_memory,
                "causal_graph_validation":
                causal_graph_validation,
                "causal_evidence_accumulator":
                self.causal_graph_validator.evidence_accumulator.report(),
                "causal_graph_alignment":
                causal_graph_alignment,
                "causal_explanation":
                causal_explanation,
                "causal_validation":
                causal_validation,
                "contextual_truth":
                contextual_truth,
                "contextual_truth_authority":
                contextual_truth_authority,
                "context_discovery":
                context_discovery,
                "context_hierarchy":
                context_hierarchy,
                "semantic_context":
                semantic_context,
                "semantic_spine_recovery_report":
                semantic_spine_recovery,
                "adaptive_identity_integration_policy":
                adaptive_identity_integration,
            }
            identity_safe_truth_integration = (
                self.identity_safe_truth_integration_engine.evaluate(
                    belief,
                    aggregate,
                    candidate,
                    integration_context,
                )
            )
            truth_internalization = (
                self.truth_internalization_engine.evaluate(
                    belief,
                    aggregate,
                    identity_safe_truth_integration,
                    context,
                )
            )
            reversible_rehearsal_execution = (
                self.reversible_rehearsal_executor.execute(
                    truth_internalization.get(
                        "reversible_internalization_rehearsal"
                    ),
                    context,
                )
            )
            generated_rehearsal_result = (
                reversible_rehearsal_execution.get("result")
            )
            repair_context = {
                **context,
                "truth_internalization_rehearsal_results":
                generated_rehearsal_result
                or context.get(
                    "truth_internalization_rehearsal_results",
                    [],
                ),
            }
            identity_repair = self.identity_repair_engine.evaluate(
                belief,
                truth_internalization,
                repair_context,
            )
            semantic_spine_recovery = (
                self.semantic_spine_recovery_engine.evaluate(
                    belief,
                    identity_safe_truth_integration,
                    identity_repair,
                )
            )
            if semantic_spine_recovery[
                "semantic_spine_recovery_confirmed"
            ]:
                integration_context[
                    "semantic_spine_recovery_report"
                ] = semantic_spine_recovery
                identity_safe_truth_integration = (
                    self.identity_safe_truth_integration_engine.evaluate(
                        belief,
                        aggregate,
                        candidate,
                        integration_context,
                    )
                )
                truth_internalization = (
                    self.truth_internalization_engine.evaluate(
                        belief,
                        aggregate,
                        identity_safe_truth_integration,
                        integration_context,
                    )
                )
            evidence_replication = self.evidence_replication_engine.propose(
                hypothesis.concept,
                belief,
                candidate,
                context,
            )
            advancement = self.truth_advancement_planner.evaluate(
                hypothesis.concept,
                trial_resolution,
                causal_attestation,
                contradiction_resolution,
                candidate,
                causal_failure_analysis,
                evidence_gap_analysis,
            )
            experiment_hypothesis = (
                self.experiment_hypothesis_generator.generate(
                    advancement.get("experiment_proposal")
                )
            )
            acquisition_request = (
                self.active_knowledge_acquisition_engine.prepare_request(
                    advancement.get("experiment_proposal"),
                    experiment_hypothesis,
                )
            )
            if belief.history:
                belief.history[-1]["trial_resolution"] = trial_resolution
                belief.history[-1]["causal_attestation"] = causal_attestation
                belief.history[-1][
                    "causal_spine_alignment"
                ] = causal_spine_alignment
                belief.history[-1][
                    "causal_graph_validation"
                ] = causal_graph_validation
                belief.history[-1][
                    "causal_graph_alignment"
                ] = causal_graph_alignment
                belief.history[-1][
                    "causal_explanation"
                ] = causal_explanation
                belief.history[-1][
                    "causal_validation"
                ] = causal_validation
                belief.history[-1][
                    "process_dependency_memory"
                ] = process_dependency_memory
                belief.history[-1][
                    "contextual_truth"
                ] = contextual_truth
                belief.history[-1][
                    "contextual_truth_authority"
                ] = contextual_truth_authority
                belief.history[-1][
                    "context_discovery"
                ] = context_discovery
                belief.history[-1]["epistemic_evidence_fusion"] = (
                    evidence_fusion
                )
                belief.history[-1][
                    "context_hierarchy"
                ] = context_hierarchy
                belief.history[-1][
                    "semantic_context"
                ] = semantic_context
                belief.history[-1][
                    "contradiction_resolution"
                ] = contradiction_resolution
                belief.history[-1]["truth_candidate"] = candidate
                belief.history[-1][
                    "identity_safe_truth_integration"
                ] = identity_safe_truth_integration
                belief.history[-1][
                    "identity_runtime_report"
                ] = identity_runtime_context.get(
                    "identity_runtime_report",
                    {},
                )
                belief.history[-1][
                    "adaptive_identity_integration"
                ] = adaptive_identity_integration
                belief.history[-1][
                    "truth_internalization"
                ] = truth_internalization
                belief.history[-1]["identity_repair"] = identity_repair
                belief.history[-1][
                    "reversible_rehearsal_execution"
                ] = reversible_rehearsal_execution
                belief.history[-1][
                    "semantic_spine_recovery"
                ] = semantic_spine_recovery
                belief.history[-1]["evidence_replication"] = (
                    evidence_replication
                )
                belief.history[-1]["knowledge_generalization"] = (
                    knowledge_generalization
                )
                belief.history[-1]["causal_failure_analysis"] = (
                    causal_failure_analysis
                )
                belief.history[-1]["evidence_gap_analysis"] = (
                    evidence_gap_analysis
                )
                belief.history[-1]["truth_advancement"] = advancement
                belief.history[-1][
                    "experiment_hypothesis"
                ] = experiment_hypothesis
                belief.history[-1][
                    "active_knowledge_acquisition"
                ] = acquisition_request
            commit = self.truth_commit_engine.evaluate(
                belief,
                aggregate,
                trials,
                {
                    **context,
                    **identity_runtime_context,
                    "truth_commit_evidence":
                    self.evidence_registry.evidence_for(
                        hypothesis.concept,
                    ),
                    "identity_safe_truth_integration":
                    identity_safe_truth_integration,
                    "truth_candidate":
                    candidate,
                    "semantic_spine_recovery_report":
                    semantic_spine_recovery,
                    "knowledge_generalization":
                    knowledge_generalization,
                    "process_dependency_memory":
                    process_dependency_memory,
                    "adaptive_identity_integration_policy":
                    adaptive_identity_integration,
                    "causal_attestation":
                    causal_attestation,
                    "causal_spine_alignment":
                    causal_spine_alignment,
                    "causal_boundary_alignment":
                    causal_boundary_alignment,
                    "causal_graph_validation":
                    causal_graph_validation,
                    "causal_graph_alignment":
                    causal_graph_alignment,
                    "causal_explanation":
                    causal_explanation,
                    "causal_validation":
                    causal_validation,
                    "process_dependency_memory":
                    process_dependency_memory,
                    "contextual_truth":
                    contextual_truth,
                    "contextual_truth_authority":
                    contextual_truth_authority,
                    "context_discovery":
                    context_discovery,
                    "context_hierarchy":
                    context_hierarchy,
                    "semantic_context":
                    semantic_context,
                    "causal_spine":
                    causal_spine,
                },
            )
            evaluations.append({
                "concept": hypothesis.concept,
                "runtime_state": belief.state.value,
                "evidence": aggregate.as_dict(),
                "trial": trial.as_dict(),
                "trial_resolution": trial_resolution,
                "causal_attestation": causal_attestation,
                "causal_spine_alignment": causal_spine_alignment,
                "causal_boundary_alignment": causal_boundary_alignment,
                "causal_graph_validation": causal_graph_validation,
                "causal_graph_alignment": causal_graph_alignment,
                "causal_explanation": causal_explanation,
                "causal_validation": causal_validation,
                "process_dependency_memory": process_dependency_memory,
                "contextual_truth": contextual_truth,
                "contextual_truth_authority": contextual_truth_authority,
                "context_discovery": context_discovery,
                "context_hierarchy": context_hierarchy,
                "semantic_context": semantic_context,
                "causal_spine": causal_spine,
                "epistemic_evidence_fusion": evidence_fusion,
                "causal_evidence_arbitration":
                arbitration_by_concept.get(hypothesis.concept, {}),
                "contradiction_resolution": contradiction_resolution,
                "contradiction_attribution":
                contradiction_resolution["contradiction_attribution"],
                "calibration": calibration,
                "belief": belief.as_dict(),
                "belief_promotion": {
                    key: value
                    for key, value in promotion.items()
                    if key != "state"
                },
                "truth_candidate": candidate,
                "identity_safe_truth_integration":
                identity_safe_truth_integration,
                "identity_runtime_report":
                identity_runtime_context.get("identity_runtime_report", {}),
                "adaptive_identity_integration":
                adaptive_identity_integration,
                "truth_internalization": truth_internalization,
                "identity_repair": identity_repair,
                "reversible_rehearsal_execution":
                reversible_rehearsal_execution,
                "semantic_spine_recovery": semantic_spine_recovery,
                "evidence_replication": evidence_replication,
                "knowledge_generalization": knowledge_generalization,
                "process_dependency_memory": process_dependency_memory,
                "causal_failure_analysis": causal_failure_analysis,
                "boundary_refinement": boundary_refinement,
                "evidence_gap_analysis": evidence_gap_analysis,
                "truth_advancement": advancement,
                "experiment_hypothesis": experiment_hypothesis,
                "active_knowledge_acquisition": acquisition_request,
                "truth_commit": commit.as_dict(),
            })

        promotion_evaluations = [
            {
                "concept": item["concept"],
                **item["belief_promotion"],
            }
            for item in evaluations
        ]
        promotion_states = [
            item["promotion_state"]
            for item in promotion_evaluations
        ]
        remediation_evaluations = [
            {
                "concept": item["concept"],
                **item["truth_commit"]["metadata"][
                    "remediation"
                ],
            }
            for item in evaluations
        ]
        candidate_evaluations = [
            item["truth_candidate"]
            for item in evaluations
        ]
        identity_safe_truth_integrations = [
            item["identity_safe_truth_integration"]
            for item in evaluations
        ]
        adaptive_identity_integrations = [
            item["adaptive_identity_integration"]
            for item in evaluations
        ]
        truth_internalizations = [
            item["truth_internalization"]
            for item in evaluations
        ]
        identity_repairs = [
            item["identity_repair"]
            for item in evaluations
        ]
        reversible_rehearsal_executions = [
            item["reversible_rehearsal_execution"]
            for item in evaluations
        ]
        semantic_spine_recoveries = [
            item["semantic_spine_recovery"]
            for item in evaluations
        ]
        resolution_evaluations = [
            item["trial_resolution"]
            for item in evaluations
        ]
        attestation_evaluations = [
            item["causal_attestation"]
            for item in evaluations
        ]
        causal_spine_alignment_evaluations = [
            item["causal_spine_alignment"]
            for item in evaluations
        ]
        causal_boundary_alignment_evaluations = [
            item["causal_boundary_alignment"]
            for item in evaluations
        ]
        causal_graph_validation_evaluations = [
            item["causal_graph_validation"]
            for item in evaluations
        ]
        causal_graph_alignment_evaluations = [
            item["causal_graph_alignment"]
            for item in evaluations
        ]
        causal_explanations = [
            item["causal_explanation"]
            for item in evaluations
        ]
        causal_validation_evaluations = [
            item["causal_validation"]
            for item in evaluations
        ]
        contextual_truth_evaluations = [
            item["contextual_truth"]
            for item in evaluations
        ]
        context_discovery_evaluations = [
            item["context_discovery"]
            for item in evaluations
        ]
        context_hierarchy_evaluations = [
            item["context_hierarchy"]
            for item in evaluations
        ]
        semantic_context_evaluations = [
            item["semantic_context"]
            for item in evaluations
        ]
        fusion_evaluations = [
            item["epistemic_evidence_fusion"]
            for item in evaluations
        ]
        contradiction_evaluations = [
            item["contradiction_resolution"]
            for item in evaluations
        ]
        contradiction_attribution_evaluations = [
            item["contradiction_attribution"]
            for item in evaluations
        ]
        advancement_evaluations = [
            item["truth_advancement"]
            for item in evaluations
        ]
        experiment_hypotheses = [
            item["experiment_hypothesis"]
            for item in evaluations
            if item["experiment_hypothesis"]
        ]
        replication_evaluations = [
            item["evidence_replication"]
            for item in evaluations
        ]
        generalization_evaluations = [
            item["knowledge_generalization"]
            for item in evaluations
        ]
        causal_failure_evaluations = [
            item["causal_failure_analysis"]
            for item in evaluations
        ]
        boundary_refinement_evaluations = [
            item["boundary_refinement"]
            for item in evaluations
        ]
        evidence_gap_evaluations = [
            item["evidence_gap_analysis"]
            for item in evaluations
        ]
        acquisition_requests = [
            item["active_knowledge_acquisition"]
            for item in evaluations
            if item["active_knowledge_acquisition"]
        ]
        self.sandbox_experiment_runner.register(acquisition_requests)
        sandbox_execution["pending_experiment_ids"] = sorted(
            self.sandbox_experiment_executor.pending_requests
        )
        sandbox_experimentation["pending_experiment_ids"] = sorted(
            self.sandbox_experiment_executor.pending_requests
        )

        return {
            "system": "epistemic_cognition_layer",
            "evaluations": evaluations,
            "beliefs": [
                belief.as_dict()
                for belief in self.belief_engine.beliefs.values()
            ],
            "truth_commitments": [
                commit.as_dict()
                for commit in self.truth_commit_engine.truth_registry.values()
            ],
            "truth_commitment_layer":
            self.truth_commit_engine.report(),
            "truth_registry":
            self.truth_commit_engine.registry.report(),
            "provisional_truth_registry":
            self.truth_commit_engine
            .provisional_truth_commit_engine
            .registry
            .report(),
            "provisional_truth_commit_engine":
            self.truth_commit_engine
            .provisional_truth_commit_engine
            .report(),
            "truth_retrieval_engine":
            self.truth_commit_engine.retrieval_engine.report(),
            "truth_lineage_graph":
            self.truth_commit_engine.registry.lineage_graph.report(),
            "truth_reinforcement_engine":
            self.truth_commit_engine.reinforcement_engine.report(),
            "reusable_truth_commitments":
            self.truth_commit_engine.reusable_truths(),
            "truth_gate_remediation": {
                "system": "truth_gate_remediation_report",
                "evaluations": remediation_evaluations,
                "automatic_bypass_forbidden": True,
            },
            "truth_candidate_engine": {
                "system": "truth_candidate_engine",
                "transition": "VALIDATED -> TRUTH_CANDIDATE",
                "evaluations": candidate_evaluations,
                "dominant_bottlenecks": [
                    {
                        "concept": item["concept"],
                        **item["dominant_bottleneck"],
                    }
                    for item in candidate_evaluations
                    if item["dominant_bottleneck"]
                ],
                "ready_count": sum(
                    item["eligible_for_truth_candidate"]
                    for item in candidate_evaluations
                ),
                "metric_gap_blocked_count": sum(
                    item["eligibility_reason"]
                    == "truth_candidate_metric_gaps"
                    for item in candidate_evaluations
                ),
                "metric_gap_blocked_concepts": [
                    item["concept"]
                    for item in candidate_evaluations
                    if item["eligibility_reason"]
                    == "truth_candidate_metric_gaps"
                ],
                "contradiction_review_required_count": sum(
                    item["eligibility_reason"]
                    == "truth_candidate_contradiction_review_required"
                    for item in candidate_evaluations
                ),
                "contradiction_review_required_concepts": [
                    item["concept"]
                    for item in candidate_evaluations
                    if item["eligibility_reason"]
                    == "truth_candidate_contradiction_review_required"
                ],
                "automatic_truth_commit_forbidden": True,
            },
            "identity_safe_truth_integration_engine": {
                "system": "identity_safe_truth_integration_engine",
                "transition":
                "TRUTH_CANDIDATE -> IDENTITY_SAFE_TRUTH -> TRUTH_COMMITMENT",
                "evaluations": identity_safe_truth_integrations,
                "identity_reinforcing_concepts": [
                    item["concept"]
                    for item in identity_safe_truth_integrations
                    if item["strengthens_identity"]
                ],
                "automatic_identity_safety_bypass_forbidden": True,
            },
            "adaptive_identity_integration_engine": {
                "system": "adaptive_identity_integration_engine",
                "phase": "6.6",
                "evaluations": adaptive_identity_integrations,
                "adapted_concepts": [
                    item["concept"]
                    for item in adaptive_identity_integrations
                    if item["adaptive_tolerance_enabled"]
                ],
                "bounded_adaptation_only": True,
                "semantic_containment_bypass_forbidden": True,
                "high_drift_rehearsal_bypass_forbidden": True,
                "high_drift_recovery_bypass_forbidden": True,
                "automatic_truth_commit_forbidden": True,
            },
            "truth_internalization_engine": {
                "system": "truth_internalization_engine",
                "transition":
                "IDENTITY_SAFETY_HOLD -> REVERSIBLE_REHEARSAL -> REEVALUATION",
                "evaluations": truth_internalizations,
                "internalization_required_concepts": [
                    item["concept"]
                    for item in truth_internalizations
                    if item["knowledge_internalization_required"]
                ],
                "persistent_identity_write_forbidden": True,
                "automatic_truth_commit_forbidden": True,
            },
            "identity_repair_engine": {
                "system": "identity_repair_engine",
                "evaluations": identity_repairs,
                "rehearsal_requests": [
                    item["reversible_internalization_rehearsal_request"]
                    for item in identity_repairs
                    if item[
                        "reversible_internalization_rehearsal_request"
                    ]
                ],
                "persistent_identity_write_forbidden": True,
            },
            "reversible_rehearsal_executor": {
                "system": "reversible_rehearsal_executor",
                "phase": "6.1",
                "evaluations": reversible_rehearsal_executions,
                "completed_rehearsals": [
                    item["result"]
                    for item in reversible_rehearsal_executions
                    if item["result"]
                ],
                "persistent_identity_write_forbidden": True,
                "automatic_truth_commit_forbidden": True,
            },
            "semantic_drift_controller": {
                "system": "semantic_drift_controller",
                "phase": "6.2",
                "evaluations": [
                    item["result"]["semantic_drift_control"]
                    for item in reversible_rehearsal_executions
                    if item["result"]
                ],
                "persistent_identity_write_forbidden": True,
            },
            "semantic_spine_recovery_engine": {
                "system": "semantic_spine_recovery_engine",
                "evaluations": semantic_spine_recoveries,
                "stable_semantic_spine_concepts": [
                    item["concept"]
                    for item in semantic_spine_recoveries
                    if item["semantic_spine_recovery_confirmed"]
                ],
                "required_recovery_cycles": 3,
            },
            "trial_resolution_engine": {
                "system": "trial_resolution_engine",
                "evaluations": resolution_evaluations,
                "stalled_concepts": [
                    item["concept"]
                    for item in resolution_evaluations
                    if item["stalled_inconclusive_pattern"]
                ],
            },
            "causal_attestation_engine": {
                "system": "causal_attestation_engine",
                "evaluations": attestation_evaluations,
                "trial_blocked_concepts": [
                    item["concept"]
                    for item in attestation_evaluations
                    if item["trial_resolution_gap"] > 0
                ],
                "truth_candidate_blocked_concepts": [
                    item["concept"]
                    for item in attestation_evaluations
                    if item["truth_candidate_gap"] > 0
                ],
            },
            "causal_alignment_engine": {
                "system": "causal_alignment_engine",
                "transition":
                "LOCAL_CAUSAL_ATTESTATION -> SEMANTIC_SPINE_ALIGNMENT",
                "evaluations": causal_spine_alignment_evaluations,
                "blocked_concepts": [
                    item["concept"]
                    for item in causal_spine_alignment_evaluations
                    if not item["alignment_ready"]
                ],
                "local_causal_evidence_is_not_spine_alignment": True,
                "automatic_truth_commit_forbidden": True,
            },
            "runtime_causal_alignment_engine": {
                "system": "runtime_causal_alignment_engine",
                "transition":
                "RAW_CONTRADICTION -> CONTEXTUAL_CAUSAL_BOUNDARY",
                "evaluations": causal_boundary_alignment_evaluations,
                "contextually_explained_concepts": [
                    item["concept"]
                    for item in causal_boundary_alignment_evaluations
                    if item["contradiction_interpretable"]
                ],
                "boundary_required_concepts": [
                    item["concept"]
                    for item in causal_boundary_alignment_evaluations
                    if (
                        item["alignment_state"]
                        == "CONTEXTUAL_BOUNDARY_REQUIRED"
                    )
                ],
                "preservation_and_transform_are_contextual_not_absolute":
                True,
                "automatic_truth_commit_forbidden": True,
            },
            "core_truth_registry":
            self.causal_alignment_engine.core_truth_registry.report(
                self.truth_commit_engine.registry,
            ),
            "causal_graph_validator": {
                "system": "causal_graph_validator",
                "evaluations": causal_graph_validation_evaluations,
                "causal_graph_structure":
                self.causal_graph.export_graph(),
                "causal_graph_foundation_validation":
                self.causal_graph.validate_causal_graph(),
                "causal_graph_alignment_evaluations":
                causal_graph_alignment_evaluations,
                "causal_explanations": causal_explanations,
                "causal_evidence_accumulator":
                self.causal_graph_validator.evidence_accumulator.report(),
                "blocked_concepts": [
                    item["concept"]
                    for item in causal_graph_validation_evaluations
                    if not item["validation_ready"]
                ],
                "semantic_sequence_is_not_causal_proof": True,
                "automatic_truth_commit_forbidden": True,
            },
            "causal_validation_engine": {
                "system": "causal_validation_engine",
                "phase": "5.3",
                "evaluations": causal_validation_evaluations,
                "validation_report":
                self.causal_validation_engine.generate_validation_report(),
                "validated_concepts": [
                    item["hypothesis"]["target_concept"]
                    for item in causal_validation_evaluations
                    if item["validation_ready"]
                ],
                "rejected_hypotheses": [
                    item["hypothesis"]
                    for item in causal_validation_evaluations
                    if item["validation_state"] == "REJECTED"
                ],
                "correlation_is_not_causation": True,
                "counterfactual_testing_enabled": True,
                "automatic_truth_commit_forbidden": True,
            },
            "contextual_truth_engine": {
                "system": "contextual_truth_engine",
                "phase": "5.4",
                "evaluations": contextual_truth_evaluations,
                "context_validated_concepts": [
                    item["truth"]
                    for item in contextual_truth_evaluations
                    if item["contextual_consistency"]
                ],
                "context_review_required_concepts": [
                    item["truth"]
                    for item in contextual_truth_evaluations
                    if not item["contextual_consistency"]
                ],
                "truths_are_contextual": True,
                "context_transfer_reliability_measured": True,
                "automatic_truth_commit_forbidden": True,
            },
            "context_discovery_engine": {
                "system": "context_discovery_engine",
                "phase": "5.5",
                "evaluations": context_discovery_evaluations,
                "clusters":
                self.context_discovery_engine.cluster_contexts()["clusters"],
                "unknown_context_count": sum(
                    item["transformation_family"] == "unknown"
                    for item in context_discovery_evaluations
                ),
                "automatic_context_discovery_enabled": True,
            },
            "context_hierarchy_engine": {
                "system": "context_hierarchy_engine",
                "phase": "5.6",
                "evaluations": context_hierarchy_evaluations,
                "hierarchy":
                self.context_hierarchy.report(),
                "hierarchy_ready_count": sum(
                    item["hierarchy_ready"]
                    for item in context_hierarchy_evaluations
                ),
                "advanced_contextual_truth_promotion_threshold": 0.75,
                "context_hierarchy_metric": (
                    "context_hierarchy_score = "
                    "(context_stability + specialization_consistency + "
                    "differentiation_confidence + "
                    "inheritance_integrity) / 4"
                ),
                "automatic_context_hierarchy_enabled": True,
            },
            "semantic_context_reasoner": {
                "system": "semantic_context_reasoner",
                "phase": "5.7",
                "evaluations": semantic_context_evaluations,
                "semantic_context_report":
                self.semantic_context_reasoner.report(),
                "semantically_validated_contexts": [
                    item["context"]
                    for item in semantic_context_evaluations
                    if item["semantically_validated"]
                ],
                "semantic_review_required_contexts": [
                    item["context"]
                    for item in semantic_context_evaluations
                    if not item["semantically_validated"]
                ],
                "contexts_are_explainable_entities": True,
                "context_labels_are_not_semantic_meaning": True,
                "automatic_semantic_context_enabled": True,
            },
            "epistemic_evidence_fusion_engine": {
                "system": "epistemic_evidence_fusion_engine",
                "phase": "5.8.5",
                "evaluations": fusion_evaluations,
                "direct_causal_channel_concepts": [
                    item["concept"]
                    for item in fusion_evaluations
                    if item["causal_fusion_policy"]
                    == "DIRECT_CAUSAL_CHANNEL_PREVAILS"
                ],
                "weak_context_cannot_reduce_direct_causal_alignment": True,
                "lower_priority_causal_sources_cannot_reduce_stronger_proof":
                True,
                "automatic_truth_promotion_forbidden": True,
            },
            "causal_evidence_arbitration_engine": {
                "system": "causal_evidence_arbitration_engine",
                "phase": "5.8",
                "evaluations": arbitration_evaluations,
                "conflicted_concepts": [
                    item["concept"]
                    for item in arbitration_evaluations
                    if item["conflict_detected"]
                ],
                "direct_causal_evidence_precedes_survival_context": True,
                "automatic_truth_promotion_forbidden": True,
            },
            "contradiction_resolution_engine": {
                "system": "contradiction_resolution_engine",
                "evaluations": contradiction_evaluations,
                "trial_blocked_concepts": [
                    item["concept"]
                    for item in contradiction_evaluations
                    if item["trial_resolution_gap"] > 0
                ],
                "near_resolution_concepts": [
                    item["concept"]
                    for item in contradiction_evaluations
                    if item["resolution_state"]
                    == "NEAR_TRIAL_RESOLUTION"
                ],
            },
            "contradiction_attribution_engine": {
                "system": "contradiction_attribution_engine",
                "phase": "6.92",
                "evaluations": contradiction_attribution_evaluations,
                "survival_context_attenuated_concepts": [
                    item["concept"]
                    for item in contradiction_attribution_evaluations
                    if item["survival_context_attenuated"]
                ],
                "direct_execution_contradiction_precedes_survival_context":
                True,
                "survival_is_not_truth": True,
                "automatic_truth_promotion_forbidden": True,
            },
            "truth_advancement_planner": {
                "system": "truth_advancement_planner",
                "phase": "5.1",
                "evaluations": advancement_evaluations,
                "proposed_experiments": [
                    item["experiment_proposal"]
                    for item in advancement_evaluations
                    if item["experiment_proposal"]
                ],
                "autonomous_execution_forbidden": True,
            },
            "experiment_hypothesis_generator": {
                "system": "experiment_hypothesis_generator",
                "phase": "5.3",
                "hypotheses": experiment_hypotheses,
                "falsifiable_hypothesis_required": True,
            },
            "active_knowledge_acquisition_engine": {
                "system": "active_knowledge_acquisition_engine",
                "phase": "6.94",
                "transport_phase": "5.4",
                "sandbox_execution_requests": acquisition_requests,
                "result_ingestion": acquisition_ingestion,
                "sandbox_only": True,
                "autonomous_sandbox_execution_permitted": True,
                "automatic_truth_commit_forbidden": True,
            },
            "evidence_gap_analyzer": {
                "system": "evidence_gap_analyzer",
                "phase": "6.94",
                "evaluations": evidence_gap_evaluations,
                "acquisition_required_concepts": [
                    item["concept"]
                    for item in evidence_gap_evaluations
                    if item["acquisition_required"]
                ],
                "knowledge_acquisition_is_evidence_not_truth": True,
                "automatic_truth_promotion_forbidden": True,
            },
            "evidence_replication_engine": {
                "system": "evidence_replication_engine",
                "phase": "5.9",
                "evaluations": replication_evaluations,
                "sandbox_replication_requests": [
                    request
                    for item in replication_evaluations
                    for request in item["sandbox_replication_requests"]
                ],
                "result_ingestion": replication_ingestion,
                "independent_cross_task_validation_required": True,
                "duplicate_task_replication_forbidden": True,
                "automatic_truth_promotion_forbidden": True,
            },
            "knowledge_replication_ledger": {
                **self.knowledge_replication_ledger.report(),
                "phase": "5.9",
            },
            "knowledge_generalization_engine": {
                "system": "knowledge_generalization_engine",
                "phase": "6.5",
                "evaluations": generalization_evaluations,
                "generalized_concepts": [
                    item["concept"]
                    for item in generalization_evaluations
                    if item["generalization_state"]
                    == "CROSS_TASK_GENERALIZED"
                ],
                "task_learning_to_concept_learning": True,
                "cross_task_replication_is_evidence_not_truth": True,
                "duplicate_task_replication_forbidden": True,
                "automatic_truth_promotion_forbidden": True,
            },
            "counterexample_engine": {
                "system": "counterexample_engine",
                "phase": "6.93",
                "evaluations": causal_failure_evaluations,
                "boundary_refinement_concepts": [
                    item["concept"]
                    for item in causal_failure_evaluations
                    if item["mixed_outcomes_detected"]
                ],
                "counterexample_analysis_precedes_truth_registry": True,
                "boundary_explanation_is_not_automatic_truth_promotion": True,
            },
            "boundary_refinement_engine": {
                "system": "boundary_refinement_engine",
                "phase": "6.96",
                "evaluations": boundary_refinement_evaluations,
                "matched_boundary_replication_concepts": [
                    item["concept"]
                    for item in boundary_refinement_evaluations
                    if item["refinement_state"]
                    == "MATCHED_BOUNDARY_REPLICATION_REQUIRED"
                ],
                "refined_scope_requires_measured_replication": True,
                "automatic_truth_promotion_forbidden": True,
            },
            "sandbox_experiment_executor": sandbox_execution,
            "sandbox_experiment_runner": sandbox_experimentation,
            "curriculum_manager": curriculum,
            "learning_curriculum_manager": learning_curriculum,
            "experiment_result_evaluator": experiment_result_evaluation,
            "evidence_integration_engine": evidence_integration,
            "learning_evidence_integration_engine":
            learning_evidence_integration,
            "experience_replay_buffer":
            self.experience_replay_buffer.report(),
            "causal_effect_analyzer": causal_effect_analysis,
            "epistemic_weight_recalibration_engine": weight_recalibration,
            "evidence_registry": self.evidence_registry.report(),
            "hydrated_replication_evidence_count":
            self.hydrated_replication_evidence_count,
            "belief_promotion_engine": {
                "system": "belief_promotion_engine",
                "diagnostics_system": "promotion_diagnostics_engine",
                "promotion_path": [
                    "CANDIDATE",
                    "PROBATION",
                    "SUPPORTED",
                    "VALIDATED",
                    "TRUTH_CANDIDATE",
                    "TRUTH_COMMITTED",
                ],
                "evaluations": promotion_evaluations,
                "state_counts": {
                    state: promotion_states.count(
                        state,
                    )
                    for state in [
                        "CANDIDATE",
                        "PROBATION",
                        "SUPPORTED",
                        "VALIDATED",
                        "TRUTH_CANDIDATE",
                    ]
                },
            },
            "constitutional_invariants": {
                "survival_is_not_truth": True,
                "high_reputation_is_not_truth": True,
                "confidence_is_not_truth": True,
                "truth_requires_evidence": True,
                "truth_requires_trials": True,
                "truth_requires_validation": True,
            },
            "integration_contract": {
                "semantic_anchor_graph": "truth_commitments_are_protected_anchors",
                "governance_kernel": "truth_commits_require_constitutional_gates",
                "reputation_engine": "reputation_informs_but_cannot_commit_truth",
                "identity_continuity_engine": "identity_instability_blocks_truth_commit",
                "mutation_rehearsal_sandbox": "rehearsal_informs_but_cannot_commit_truth",
                "active_knowledge_acquisition": "sandbox_results_require_validation_before_epistemic_ingestion",
                "evidence_gap_analyzer": "missing_success_counterexample_and_task_regions_drive_targeted_sandbox_acquisition",
                "sandbox_experiment_executor": "isolated_reversible_experiments_only",
                "sandbox_experiment_runner": "declared_isolated_cases_are_matched_to_pending_experiments_without_fabricating_results",
                "curriculum_manager": "missing_evidence_requests_generate_in_memory_synthetic_arc_probes_for_isolated_sandbox_execution_only",
                "learning_curriculum_manager": "scheduled_synthetic_probes_expand_experience_coverage_without_claiming_independent_validation",
                "experiment_result_evaluator": "sandbox_outcomes_are_measured_before_epistemic_integration",
                "evidence_integration_engine": "validated_sandbox_measurements_enter_the_evidence_registry_without_automatic_truth_commitment",
                "experience_replay_buffer": "measured_sandbox_experiences_are_replayable_while_synthetic_probes_remain_non_independent",
                "epistemic_weight_recalibration": "verified_interventions_reduce_survival_noise_without_truth_promotion",
                "causal_evidence_arbitration": "direct_execution_evidence_precedes_conflicting_survival_context",
                "contradiction_attribution": "source_weighted_contradiction_preserves_context_without_equating_survival_with_truth",
                "epistemic_evidence_fusion": "causal_proof_is_fused_independently_from_semantic_and_evolutionary_context",
                "evidence_replication": "independent_cross_task_replications_raise_coverage_without_automatic_truth_promotion",
                "knowledge_replication_ledger": "cross_task_replication_records_are_unique_quality_weighted_evidence",
                "knowledge_generalization_engine": "independent_task_observations_raise_concept_support_without_duplicate_bonus_or_automatic_truth_promotion",
                "counterexample_engine": "mixed_cross_task_outcomes_are_mapped_into_explicit_concept_boundaries_before_truth_promotion",
                "boundary_refinement_engine": "provisional_scope_midpoints_drive_matched_boundary_probes_without_unmeasured_evidence_inflation",
                "adaptive_identity_integration_engine": "high_quality_truth_candidates_receive_bounded_identity_tolerance_without_rehearsal_or_recovery_bypass",
                "truth_internalization": "identity_safety_holds_produce_reversible_internalization_rehearsals",
                "identity_repair": "only_validated_reversible_rehearsals_can_drive_identity_repair",
                "semantic_spine_recovery": "three_safe_recovery_cycles_precede_truth_commit",
                "reversible_rehearsal_executor": "internalization_rehearsals_execute_in_reversible_isolated_simulation",
                "semantic_drift_controller": "drift_repair_interventions_are_simulated_before_persistent_identity_write",
                "truth_registry": "committed_truths_are_indexed_with_lineage_and_verification_history",
                "provisional_truth_registry": "identity_safe_schema_valid_truth_candidates_are_persisted_before_final_truth_review",
                "truth_lineage_graph": "committed_truths_preserve_parent_child_lineage_across_runtime_restarts",
                "truth_retrieval_engine": "committed_truths_support_direct_related_and_ranked_retrieval",
                "truth_reinforcement_engine": "existing_truths_accumulate_reviewable_reinforcement_without_new_truth_ids",
                "memory_compression_layer": "beliefs_decay_but_truth_commits_are_preserved",
            },
            "runtime_state": (
                evaluations[-1]["runtime_state"]
                if evaluations
                else "CANDIDATE"
            ),
        }


epistemic_cognition_layer = EpistemicCognitionLayer()
