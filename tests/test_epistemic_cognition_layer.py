from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from core.belief_engine import EpistemicCognitionLayer
from core.evidence_registry import EvidenceRegistry
from core.epistemic_decision_engine import EpistemicDecisionEngine
from core.epistemic_models import (
    Belief,
    BeliefState,
    Evidence,
    EvidenceAggregate,
    EpistemicTrial,
    TrialResult,
    utcnow,
)
from core.governance_compression.governance_kernel import GovernanceKernel
from core.civilization.identity_continuity_engine import IdentityContinuityEngine
from core.memory.compression import MemoryCompressionLayer
from core.truth import TruthCommitEngine as ProvisionalTruthCommitEngine
from core.truth import TruthRecord as ProvisionalTruthRecord
from core.truth import TruthRegistry as ProvisionalTruthRegistry
from runtime.semantic_drift_monitor import SemanticDriftMonitor
from runtime.epistemic_promotion_engine import EpistemicPromotionEngine
from runtime.ambiguity_resolution_engine import AmbiguityResolutionEngine
from runtime.truth_gate_remediation_engine import TruthGateRemediationEngine
from runtime.truth_candidate_engine import TruthCandidateEngine
from runtime.epistemic.belief_promotion_engine import BeliefPromotionEngine
from runtime.identity_safe_truth_integration import (
    IdentitySafeTruthIntegrationEngine,
)
from runtime.adaptive_identity_integration_engine import (
    AdaptiveIdentityIntegrationEngine,
)
from runtime.truth_internalization_engine import TruthInternalizationEngine
from runtime.identity_repair_engine import IdentityRepairEngine
from runtime.semantic_spine_recovery_engine import (
    SemanticSpineRecoveryEngine,
)
from runtime.reversible_rehearsal_executor import (
    ReversibleRehearsalExecutor,
)
from runtime.semantic_drift_controller import SemanticDriftController
from runtime.truth_registry import TruthRegistry
from runtime.truth_registry import TruthRetrievalEngine
from runtime.truth_registry import TruthReinforcementEngine
from runtime.contradiction_resolution_engine import (
    ContradictionResolutionEngine,
)
from runtime.contradiction_attribution_engine import (
    ContradictionAttributionEngine,
)
from runtime.trial_resolution_engine import TrialResolutionEngine
from runtime.truth_advancement_planner import TruthAdvancementPlanner
from runtime.active_knowledge_acquisition_engine import (
    ActiveKnowledgeAcquisitionEngine,
)
from runtime.causal_effect_analyzer import CausalEffectAnalyzer
from runtime.causal_evidence_arbitration_engine import (
    CausalEvidenceArbitrationEngine,
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
from runtime.knowledge_replication_ledger import (
    KnowledgeReplicationLedger,
    ReplicationRecord,
)
from runtime.cross_task_replication_collector import (
    CrossTaskReplicationCollector,
)
from runtime.counterexample_engine import CounterexampleEngine
from runtime.evidence_gap_analyzer import EvidenceGapAnalyzer
from runtime.knowledge_generalization_engine import (
    KnowledgeGeneralizationEngine,
)
from runtime.concept_schema_validator import ConceptSchemaValidator
from runtime.sandbox_experiment_executor import SandboxExperimentExecutor
from runtime.sandbox_experiment_runner import SandboxExperimentRunner
from runtime.experiment_result_evaluator import ExperimentResultEvaluator
from runtime.task_generator import TaskGenerator
from runtime.boundary_refinement_engine import BoundaryRefinementEngine
from core.learning.experiment_scheduler import ExperimentScheduler
from core.learning.synthetic_task_generator import SyntheticTaskGenerator
from core.extinction_engine import ExtinctionEngine


def strong_evidence(concept, source):
    return {
        "concept": concept,
        "source": source,
        "support_score": 0.98,
        "contradiction_score": 0.01,
        "reliability": 1.0,
        "causal_alignment": 1.0,
        "semantic_consistency": 1.0,
    }


def test_high_confidence_without_evidence_does_not_commit_truth():
    layer = EpistemicCognitionLayer()

    report = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "survival_only_claim",
            "prior_confidence": 0.99,
        }],
        "survival_score": 1.0,
        "average_reputation": 1.0,
    })

    evaluation = report["evaluations"][0]
    assert evaluation["runtime_state"] == "CANDIDATE"
    assert evaluation["truth_commit"]["decision"] == "REMAIN_BELIEF"
    assert evaluation["truth_commit"]["constitutional_invariants"][
        "survival_is_not_truth"
    ] is True
    assert evaluation["calibration"]["calibrated_confidence"] < 0.85


def test_validated_evidence_promotes_belief_and_commits_truth():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "topology_preservation",
            "prior_confidence": 0.95,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("topology_preservation", "causal_observation"),
            strong_evidence("topology_preservation", "semantic_anchor_graph"),
            strong_evidence("topology_preservation", "mutation_rehearsal"),
        ],
        "identity_stable": True,
        "semantic_consistency": True,
        "mutation_rehearsal_safe": True,
    }

    first = layer.run_cycle(context)
    second = layer.run_cycle(context)

    assert first["evaluations"][0]["runtime_state"] == "SUPPORTED"
    evaluation = second["evaluations"][0]
    assert evaluation["runtime_state"] == "TRUTH_COMMITTED"
    assert evaluation["truth_commit"]["decision"] == "TRUTH_COMMITTED"
    assert len(second["truth_commitments"]) == 1
    assert second["evidence_registry"]["evidence_count"] == 3
    candidate = second["truth_candidate_engine"]["evaluations"][0]
    assert candidate["candidate_state"] == "READY_FOR_TRUTH_COMMIT_REVIEW"
    assert candidate["eligible_for_truth_candidate"] is True
    assert candidate["blocked_metrics"] == []
    commitment_layer = second["truth_commitment_layer"]
    assert commitment_layer["active_truth_count"] == 1
    assert commitment_layer["active_truth_objects"][0]["concept"] == (
        "topology_preservation"
    )
    assert second["reusable_truth_commitments"][0]["reusable"] is True


def test_contradictory_evidence_rejects_belief():
    layer = EpistemicCognitionLayer()

    report = layer.run_cycle({
        "epistemic_hypotheses": [{"concept": "unstable_claim"}],
        "epistemic_evidence": [{
            "concept": "unstable_claim",
            "source": "causal_observation",
            "support_score": 0.10,
            "contradiction_score": 0.90,
            "reliability": 1.0,
        }],
    })

    assert report["evaluations"][0]["runtime_state"] == "REJECTED"
    assert report["truth_commitments"] == []


def test_later_contradiction_requires_review_without_auto_revocation():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{"concept": "revisable_claim"}],
        "epistemic_evidence": [
            strong_evidence("revisable_claim", "source_a"),
            strong_evidence("revisable_claim", "source_b"),
            strong_evidence("revisable_claim", "source_c"),
        ],
    }
    layer.run_cycle(context)
    layer.run_cycle(context)

    report = layer.run_cycle({
        "epistemic_hypotheses": [{"concept": "revisable_claim"}],
        "epistemic_evidence": [{
            "concept": "revisable_claim",
            "source": "disconfirming_observation",
            "support_score": 0.0,
            "contradiction_score": 1.0,
            "reliability": 1.0,
            "causal_alignment": 1.0,
            "semantic_consistency": 1.0,
        }],
    })

    assert report["evaluations"][0]["truth_commit"]["decision"] == (
        "TRUTH_REVOCATION_REVIEW_REQUIRED"
    )
    assert report["truth_commitments"][0]["concept"] == "revisable_claim"
    commitment_layer = report["truth_commitment_layer"]
    assert commitment_layer["active_truth_count"] == 1
    assert commitment_layer["truth_objects"][0]["status"] == "ACTIVE"
    assert commitment_layer["truth_objects"][0]["reusable"] is True
    final_commit = report["evaluations"][0]["truth_commit"]["metadata"][
        "final_commit_decision"
    ]
    assert final_commit["forbid_automatic_truth_revocation"] is True
    assert final_commit["manual_review_required"] is True


def test_incomplete_rehearsal_holds_committed_truth_without_revocation():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{"concept": "rehearsal_pending_truth"}],
        "epistemic_evidence": [
            strong_evidence("rehearsal_pending_truth", "source_a"),
            strong_evidence("rehearsal_pending_truth", "source_b"),
            strong_evidence("rehearsal_pending_truth", "source_c"),
        ],
    }
    layer.run_cycle(context)
    layer.run_cycle(context)

    report = layer.run_cycle({
        **context,
        "mutation_rehearsal_safe": False,
    })
    evaluation = report["evaluations"][0]

    assert evaluation["truth_candidate"][
        "truth_candidate_evaluation_skipped"
    ] is True
    assert evaluation["truth_candidate"]["blocked_metrics"] == []
    assert evaluation["truth_commit"]["decision"] == "TRUTH_COMMIT_HELD"
    assert evaluation["runtime_state"] == "TRUTH_COMMITTED"
    assert report["reusable_truth_commitments"][0]["status"] == "ACTIVE"
    assert report["reusable_truth_commitments"][0]["reusable"] is True


def test_pipeline_injects_reusable_truths_into_next_task_context():
    from runtime.pipeline import AdaptiveCognitivePipeline

    pipeline = AdaptiveCognitivePipeline(
        epistemic_engine=EpistemicDecisionEngine()
    )
    layer = pipeline.epistemic_decision_engine.cognition_layer
    context = {
        "epistemic_hypotheses": [{
            "concept": "reusable_topology",
            "prior_confidence": 0.95,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("reusable_topology", "causal_observation"),
            strong_evidence("reusable_topology", "semantic_anchor_graph"),
            strong_evidence("reusable_topology", "mutation_rehearsal"),
        ],
    }
    layer.run_cycle(context)
    layer.run_cycle(context)

    pipeline.boot_runtime = lambda: None
    pipeline.run_stage_cycle = lambda: None
    pipeline.run_reasoning_cycle = lambda: None
    pipeline.run_governance_cycle = lambda: None
    pipeline.run_health_cycle = lambda: None
    pipeline.finalize_runtime = lambda: None
    report = pipeline.run(task_path="data/training/task_002.json")

    reusable = report["reusable_truth_commitments"]
    assert reusable[0]["concept"] == "reusable_topology"
    assert reusable[0]["status"] == "ACTIVE"


def test_pipeline_returns_truths_committed_during_current_run():
    from runtime.pipeline import AdaptiveCognitivePipeline

    pipeline = AdaptiveCognitivePipeline(
        epistemic_engine=EpistemicDecisionEngine()
    )
    truth_engine = (
        pipeline.epistemic_decision_engine
        .cognition_layer
        .truth_commit_engine
    )
    snapshots = iter([
        [],
        [{
            "truth_id": "truth:current_run",
            "concept": "current_run_truth",
            "status": "ACTIVE",
            "reusable": True,
        }],
    ])
    truth_engine.reusable_truths = lambda: next(snapshots)
    pipeline.boot_runtime = lambda: None
    pipeline.run_stage_cycle = lambda: None
    pipeline.run_reasoning_cycle = lambda: None
    pipeline.run_governance_cycle = lambda: None
    pipeline.run_health_cycle = lambda: None
    pipeline.finalize_runtime = lambda: None

    report = pipeline.run(task_path="data/training/task_003.json")

    assert report["reusable_truth_commitments"][0]["concept"] == (
        "current_run_truth"
    )
    assert report["truth_commitments"][0]["truth_id"] == (
        "truth:current_run"
    )


def test_evidence_aging_reduces_weight():
    registry = EvidenceRegistry(half_life_days=10)
    recent = Evidence(concept="claim", source="recent", reliability=1.0)
    old = Evidence(
        concept="claim",
        source="old",
        reliability=1.0,
        observed_at=utcnow() - timedelta(days=10),
    )

    assert registry.evidence_weight(old) < registry.evidence_weight(recent)


def test_consistent_evidence_repetition_reinforces_reliability():
    registry = EvidenceRegistry()
    first = registry.collect({
        "concept": "shape_preservation",
        "source": "semantic_observation",
        "support_score": 0.82,
        "contradiction_score": 0.08,
        "reliability": 0.58,
        "metadata": {
            "evidence_id": "shape:1",
            "semantic_key": "shape_preservation",
        },
    })
    second = registry.collect({
        "concept": "shape_preservation",
        "source": "semantic_observation",
        "support_score": 0.84,
        "contradiction_score": 0.07,
        "reliability": 0.58,
        "metadata": {
            "evidence_id": "shape:2",
            "semantic_key": "shape_preservation",
        },
    })

    assert second.reliability > first.reliability
    assert second.metadata["reinforcement_applied"] is True
    assert registry.report()["reinforced_evidence_count"] == 1


def test_evolutionary_fitness_cannot_dominate_epistemic_truth_aggregate():
    registry = EvidenceRegistry()
    for index in range(10):
        registry.collect({
            "concept": "color_preservation",
            "source": "evolutionary_trait_survival_history",
            "support_score": 0.92,
            "contradiction_score": 0.32,
            "reliability": 0.90,
            "causal_alignment": 0.10,
            "semantic_consistency": 0.80,
            "metadata": {
                "evidence_id": f"survival:{index}",
                "survival_is_not_truth": True,
            },
        })
    registry.collect({
        "concept": "color_preservation",
        "source": "execution_validation",
        "support_score": 0.98,
        "contradiction_score": 0.01,
        "reliability": 1.0,
        "causal_alignment": 1.0,
        "semantic_consistency": 1.0,
        "metadata": {
            "evidence_id": "execution:color_preservation",
        },
    })

    aggregate = registry.aggregate("color_preservation")
    partition = registry.epistemic_partition("color_preservation")

    assert partition["evolutionary_fitness_raw_ratio"] > 0.80
    assert partition["evolutionary_fitness_effective_ratio"] <= 0.25
    assert partition["cap_applied"] is True
    assert aggregate.causal_alignment > 0.70
    assert registry.report()["evolutionary_fitness_policy"]["policy"] == (
        "evolutionary_fitness_informs_but_cannot_dominate_epistemic_truth"
    )


def test_governance_kernel_exposes_epistemic_cognition_layer():
    report = GovernanceKernel().run_cycle({
        "epistemic_hypotheses": [{"concept": "candidate"}],
    })

    assert report["epistemic_cognition_layer"]["system"] == (
        "epistemic_cognition_layer"
    )
    assert "truth_requires_evidence" in report["policies"]
    assert "confidence_is_not_truth" in report["policies"]


def test_decision_engine_forms_belief_from_ambiguous_rehearsal():
    engine = EpistemicDecisionEngine()
    report = engine.run_cycle({
        "causal_rehearsal_report": {
            "mutation_simulator": {
                "simulations": [{
                    "simulation_id": "mutation_rehearsal:ambiguous",
                    "candidate_type": "invariant",
                    "source": {
                        "concept": "topology_preservation",
                        "confidence": 0.97,
                    },
                    "predicted_entropy_delta": 0.38,
                    "predicted_identity_delta": 0.34,
                    "predicted_utility": 0.49,
                    "causal_alignment": 0.78,
                    "simulation_state": "ambiguous",
                }],
            },
            "evidence_exports": {
                "causal_attestation_score": 0.58,
                "identity_attestation_score": 0.64,
            },
        },
    })

    assert report["belief_registry"]["belief_count"] == 1
    assert report["beliefs"][0]["concept"] == "topology_preservation"
    assert report["beliefs"][0]["state"] in ["PROBATION", "SUPPORTED"]
    assert report["truth_commitments"] == []


def test_decision_engine_commits_only_after_repeated_validated_trials():
    engine = EpistemicDecisionEngine()
    simulation = {
        "simulation_id": "mutation_rehearsal:validated",
        "candidate_type": "invariant",
        "source": {
            "concept": "topology_preservation",
            "confidence": 0.98,
        },
        "predicted_entropy_delta": 0.02,
        "predicted_identity_delta": 0.02,
        "predicted_utility": 0.98,
        "causal_alignment": 0.99,
        "simulation_state": "constructive",
    }
    assessment = {
        "simulation": simulation,
        "constructive_score": 0.98,
        "causal_gain_estimate": {"causal_gain": 0.96},
        "constructive_signal": {
            "reasoning": {
                "identity_preservation": 0.98,
                "entropy_bound": 0.98,
            },
        },
    }
    context = {
        "causal_rehearsal_report": {
            "mutation_simulator": {"simulations": [simulation]},
            "evidence_exports": {
                "causal_attestation_score": 0.98,
                "identity_attestation_score": 0.98,
            },
        },
        "constructive_reasoning_report": {
            "all_assessments": [assessment],
        },
    }

    first = engine.run_cycle(context)
    second = engine.run_cycle(context)

    assert first["truth_commitments"] == []
    assert second["truth_commitments"][0]["concept"] == (
        "topology_preservation"
    )
    assert second["beliefs"][0]["state"] == "TRUTH_COMMITTED"


def test_critical_semantic_drift_suppresses_weak_belief_flood():
    engine = EpistemicDecisionEngine()
    simulations = [
        {
            "simulation_id": f"mutation_rehearsal:weak:{index}",
            "candidate_type": "hypothesis",
            "source": {
                "concept": f"weak_claim_{index}",
                "confidence": 0.98,
            },
            "predicted_entropy_delta": 0.48,
            "predicted_identity_delta": 0.38,
            "predicted_utility": 0.54,
            "causal_alignment": 0.58,
            "simulation_state": "ambiguous",
        }
        for index in range(50)
    ]
    report = engine.run_cycle({
        "semantic_drift": 0.9446,
        "identity_continuity": 0.74,
        "causal_rehearsal_report": {
            "mutation_simulator": {"simulations": simulations},
            "evidence_exports": {
                "causal_attestation_score": 0.54,
                "identity_attestation_score": 0.62,
            },
        },
    })

    regulation = report["epistemic_drift_regulation"]
    assert regulation["regulation_mode"] == "semantic_containment"
    assert report["epistemic_transition_summary"][
        "total_suppressed_count"
    ] == 50
    assert report["belief_registry"]["belief_count"] == 0


def test_critical_semantic_drift_blocks_truth_commit():
    engine = EpistemicDecisionEngine()
    simulation = {
        "simulation_id": "mutation_rehearsal:drifted_truth",
        "candidate_type": "invariant",
        "source": {
            "concept": "drifted_truth_claim",
            "confidence": 0.99,
        },
        "predicted_entropy_delta": 0.01,
        "predicted_identity_delta": 0.01,
        "predicted_utility": 0.99,
        "causal_alignment": 0.99,
        "simulation_state": "constructive",
    }
    context = {
        "semantic_drift": 0.9446,
        "identity_continuity": 0.74,
        "causal_rehearsal_report": {
            "mutation_simulator": {"simulations": [simulation]},
            "evidence_exports": {
                "causal_attestation_score": 0.99,
                "identity_attestation_score": 0.99,
            },
        },
        "constructive_reasoning_report": {
            "all_assessments": [{
                "simulation": simulation,
                "constructive_score": 0.99,
                "causal_gain_estimate": {"causal_gain": 0.99},
                "constructive_signal": {
                    "reasoning": {
                        "identity_preservation": 0.99,
                        "entropy_bound": 0.99,
                    },
                },
            }],
        },
    }

    engine.run_cycle(context)
    report = engine.run_cycle(context)

    assert report["truth_commitments"] == []
    commit = report["evaluations"][0]["truth_commit"]
    assert commit["decision"] == "REMAIN_BELIEF"
    assert commit["metadata"]["gates"]["semantic_drift_below_limit"] is False


def test_governance_kernel_announces_semantic_containment():
    report = GovernanceKernel().run_cycle({
        "semantic_drift": 0.9446,
        "identity_continuity": 0.74,
    })

    assert "freeze_weak_belief_birth" in report["policies"]
    assert any(
        signal["signal"] == "semantic_drift_epistemic_containment"
        for signal in report["signals"]
    )


def test_verdict_engine_records_ambiguous_to_probation_transition():
    engine = EpistemicDecisionEngine()
    report = engine.run_cycle({
        "identity_continuity": 0.74,
        "causal_rehearsal_report": {
            "mutation_simulator": {
                "simulations": [{
                    "simulation_id": "mutation_rehearsal:verdict",
                    "candidate_type": "invariant",
                    "source": {
                        "concept": "verdict_transition_probe",
                        "confidence": 0.95,
                    },
                    "predicted_entropy_delta": 0.30,
                    "predicted_identity_delta": 0.20,
                    "predicted_utility": 0.62,
                    "causal_alignment": 0.76,
                    "simulation_state": "ambiguous",
                }],
            },
            "evidence_exports": {
                "causal_attestation_score": 0.68,
                "identity_attestation_score": 0.80,
            },
        },
    })

    verdict = report["epistemic_verdict_engine"]["verdicts"][0]
    assert verdict["simulation_state"] == "ambiguous"
    assert verdict["verdict"] in ["PROBATION", "SUPPORTED"]
    assert verdict["register_belief"] is True
    assert report["belief_registry"]["belief_count"] == 1


def test_semantic_drift_monitor_separates_instantaneous_and_history():
    monitor = SemanticDriftMonitor()
    first = monitor.measure({"semantic_drift": 0.9446})
    second = monitor.measure({"semantic_drift": 0.18})

    assert first["instantaneous_drift"] == 0.9446
    assert second["instantaneous_drift"] == 0.18
    assert second["historical_pressure"] > second["instantaneous_drift"]


def test_identity_engine_distinguishes_drift_from_fragmentation():
    report = IdentityContinuityEngine().prevent_fragmentation({
        "stability_field_report": {
            "identity_fragmentation": {
                "fragmentation_detected": False,
            },
            "semantic_drift": {
                "semantic_drift": 0.9446,
            },
        },
    })

    assert report["fragmentation_detected"] is False
    assert report["fragmentation_state"] == (
        "semantic_drift_intervention_required"
    )


def test_trait_candidate_promotes_to_probationary_belief_request():
    report = EpistemicPromotionEngine().run_cycle({
        "evolutionary_memory_report": {
            "adaptive_trait_memory": {
                "traits": [{
                    "id": "position_preservation",
                    "trait_state": "candidate",
                    "fitness": 0.68,
                    "semantic_alignment": 0.82,
                    "stability_score": 0.78,
                    "observations": 2,
                    "survival_history": [
                        {
                            "constructive_score": 0.72,
                            "identity_continuity": 0.80,
                        },
                        {
                            "constructive_score": 0.76,
                            "identity_continuity": 0.82,
                        },
                    ],
                }],
            },
        },
    })

    promotion = report["promotions"][0]
    assert promotion["promotion_state"] == "SUPPORTED_BELIEF"
    assert promotion["promote_to_epistemic_trial"] is True
    assert report["epistemic_hypotheses"][0]["concept"] == (
        "position_preservation"
    )
    assert report["constitutional_invariants"]["survival_is_not_truth"] is True


def test_decision_engine_registers_promoted_trait_belief():
    report = EpistemicDecisionEngine().run_cycle({
        "evolutionary_memory_report": {
            "adaptive_trait_memory": {
                "traits": [{
                    "id": "shape_preservation",
                    "trait_state": "candidate",
                    "fitness": 0.70,
                    "semantic_alignment": 0.86,
                    "stability_score": 0.82,
                    "observations": 2,
                    "survival_history": [
                        {
                            "constructive_score": 0.78,
                            "identity_continuity": 0.84,
                        },
                        {
                            "constructive_score": 0.80,
                            "identity_continuity": 0.86,
                        },
                    ],
                }],
            },
        },
    })

    assert report["epistemic_transition_summary"]["trait_promotion_count"] == 1
    assert report["belief_registry"]["belief_count"] == 1
    assert report["beliefs"][0]["concept"] == "shape_preservation"
    assert report["truth_commitments"] == []


def test_governance_routes_trait_candidates_through_promotion():
    report = GovernanceKernel().run_cycle({})

    assert "route_trait_candidates_through_epistemic_promotion" in (
        report["policies"]
    )
    assert "trait_survival_is_not_belief" in report["policies"]


def test_ambiguity_resolution_routes_supported_ambiguity_to_probation():
    report = AmbiguityResolutionEngine().run_cycle({
        "causal_rehearsal_report": {
            "mutation_simulator": {
                "simulations": [{
                    "simulation_id": "mutation_rehearsal:ambiguity",
                    "simulation_state": "ambiguous",
                    "predicted_entropy_delta": 0.30,
                    "predicted_identity_delta": 0.20,
                    "causal_alignment": 0.74,
                }],
            },
            "evidence_exports": {
                "causal_attestation_score": 0.68,
                "identity_attestation_score": 0.80,
            },
        },
    })

    assert report["resolutions"][0]["resolution"] == "PROBATIONARY_PATH"
    assert report["probationary_count"] == 1


def test_epistemic_trial_grace_delays_extinction():
    engine = ExtinctionEngine(
        decay_threshold=0,
        suppressed_threshold=0,
    )
    trait = {
        "id": "shape_preservation",
        "trait_state": "decaying",
        "fitness": 0.58,
        "semantic_alignment": 0.82,
        "stability_score": 0.76,
        "observations": 3,
        "survival_history": [
            {
                "constructive_score": 0.72,
                "identity_continuity": 0.80,
            },
            {
                "constructive_score": 0.74,
                "identity_continuity": 0.82,
            },
            {
                "constructive_score": 0.76,
                "identity_continuity": 0.84,
            },
        ],
    }
    context = {
        "cognitive_natural_selection_report": {
            "selected_traits": [],
            "decaying_traits": [trait],
            "suppressed_traits": [],
            "extinct_traits": [],
        },
        "epistemic_promotion_grace_report": {
            "traits": ["shape_preservation"],
        },
    }

    report = engine.run_cycle(context)

    assert report["extinct_count"] == 0
    assert report["surviving_traits"][0]["epistemic_trial_grace"] is True
    assert report["selection_actions"][0]["action"] == (
        "delay_extinction_for_epistemic_trial"
    )


def test_decaying_trait_can_enter_recovery_probation():
    report = EpistemicPromotionEngine().run_cycle({
        "cognitive_natural_selection_report": {
            "selected_traits": [],
            "decaying_traits": [{
                "id": "object_identity_preservation",
                "trait_state": "decaying",
                "fitness": 0.62,
                "semantic_alignment": 0.82,
                "stability_score": 0.76,
                "observations": 3,
                "survival_history": [
                    {
                        "constructive_score": 0.74,
                        "identity_continuity": 0.82,
                    },
                    {
                        "constructive_score": 0.76,
                        "identity_continuity": 0.84,
                    },
                    {
                        "constructive_score": 0.78,
                        "identity_continuity": 0.86,
                    },
                ],
            }],
            "suppressed_traits": [],
        },
    })

    assert report["promotions"][0]["promotion_state"] == "RECOVERY_PROBATION"
    assert report["promotion_grace_traits"] == [
        "object_identity_preservation"
    ]


def test_natural_selection_queues_extinction_before_epistemic_trial():
    from core.natural_selection import CognitiveNaturalSelection

    report = CognitiveNaturalSelection().run_cycle({
        "runtime_entropy": 0.90,
        "evolutionary_memory_report": {
            "adaptive_trait_memory": {
                "traits": [{
                    "id": "weak_shape_guess",
                    "trait_state": "candidate",
                    "fitness": 0.04,
                    "semantic_alignment": 0.12,
                    "stability_score": 0.18,
                    "survival_history": [
                        {"constructive_score": 0.08},
                        {"constructive_score": 0.10},
                        {"constructive_score": 0.06},
                    ],
                }],
            },
        },
    })

    assert report["extinct_count"] == 1
    assert report["extinction_archive"] == []
    assert report["selection_actions"][0]["action"] == (
        "queue_extinction_pending_epistemic_trial"
    )


def test_extinct_trait_with_evidence_receives_epistemic_trial_grace():
    trait = {
        "id": "position_preservation",
        "trait_state": "extinct",
        "fitness": 0.70,
        "net_fitness": 0.70,
        "semantic_alignment": 0.86,
        "stability_score": 0.82,
        "survival_history": [
            {
                "constructive_score": 0.78,
                "identity_continuity": 0.84,
            },
            {
                "constructive_score": 0.80,
                "identity_continuity": 0.86,
            },
        ],
    }
    promotion = EpistemicPromotionEngine().run_cycle({
        "cognitive_natural_selection_report": {
            "extinct_traits": [trait],
        },
    })
    extinction = ExtinctionEngine().run_cycle({
        "cognitive_natural_selection_report": {
            "extinct_traits": [trait],
        },
        "epistemic_promotion_grace_report": {
            "traits": promotion["promotion_grace_traits"],
        },
    })

    assert promotion["epistemic_trials"][0]["trial"]["trial_result"] == (
        "PASSED"
    )
    assert promotion["promotion_grace_traits"] == [
        "position_preservation"
    ]
    assert extinction["extinct_count"] == 0
    assert extinction["surviving_traits"][0]["epistemic_trial_grace"] is True


def test_failed_epistemic_trial_allows_extinction_archive():
    trait = {
        "id": "weak_shape_guess",
        "trait_state": "extinct",
        "fitness": 0.04,
        "semantic_alignment": 0.12,
        "stability_score": 0.18,
        "survival_history": [
            {"constructive_score": 0.08},
            {"constructive_score": 0.10},
            {"constructive_score": 0.06},
        ],
    }
    promotion = EpistemicPromotionEngine().run_cycle({
        "cognitive_natural_selection_report": {
            "extinct_traits": [trait],
        },
    })
    extinction = ExtinctionEngine().run_cycle({
        "cognitive_natural_selection_report": {
            "extinct_traits": [trait],
        },
        "epistemic_promotion_grace_report": {
            "traits": promotion["promotion_grace_traits"],
        },
    })

    assert promotion["epistemic_trials"][0]["trial"]["trial_result"] == (
        "FAILED"
    )
    assert promotion["promotion_grace_traits"] == []
    assert extinction["extinct_count"] == 1
    assert extinction["extinction_archive"]


def test_semantic_observation_births_probation_but_not_truth():
    report = EpistemicDecisionEngine().run_cycle({
        "semantic_abstractions": [{
            "semantic_concept": "topology_preservation",
            "confidence": 0.98,
            "semantic_consistency": True,
        }],
        "evolutionary_memory_report": {
            "adaptive_trait_memory": {
                "traits": [{
                    "id": "topology_preservation",
                    "trait_state": "decaying",
                    "fitness": 0.21,
                    "semantic_alignment": 0.38,
                    "stability_score": 0.52,
                    "survival_history": [
                        {
                            "constructive_score": 0.39,
                            "identity_continuity": 0.50,
                        },
                        {
                            "constructive_score": 0.40,
                            "identity_continuity": 0.51,
                        },
                    ],
                }],
            },
        },
    })

    promotion = report["epistemic_promotion_engine"]["promotions"][0]
    assert promotion["promotion_state"] == "OBSERVATIONAL_PROBATION"
    assert promotion["epistemic_trial"]["trial"]["trial_result"] == (
        "INCONCLUSIVE"
    )
    assert report["beliefs"][0]["state"] == "PROBATION"
    assert report["truth_commitments"] == []


def test_semantic_containment_allows_only_quarantined_probation_birth():
    report = EpistemicDecisionEngine().run_cycle({
        "semantic_drift": 0.80,
        "identity_continuity": 0.50,
        "semantic_abstractions": [
            {
                "semantic_concept": "symbolic_remapping",
                "confidence": 0.99,
                "semantic_consistency": True,
            },
            {
                "semantic_concept": "symbolic_remapping",
                "confidence": 0.98,
                "semantic_consistency": True,
            },
        ],
        "evolutionary_memory_report": {
            "adaptive_trait_memory": {
                "traits": [{
                    "id": "symbolic_remapping",
                    "trait_state": "decaying",
                    "fitness": 0.32,
                    "semantic_alignment": 0.55,
                    "stability_score": 0.65,
                    "survival_history": [
                        {
                            "constructive_score": 0.58,
                            "identity_continuity": 0.65,
                        },
                        {
                            "constructive_score": 0.60,
                            "identity_continuity": 0.66,
                        },
                    ],
                }],
            },
        },
    })

    quarantine = report["epistemic_quarantine"]
    assert quarantine["active"] is True
    assert quarantine["truth_commit_blocked"] is True
    assert quarantine["active_quarantined_beliefs"] == [
        "symbolic_remapping"
    ]
    assert report["beliefs"][0]["state"] == "PROBATION"
    assert report["truth_commitments"] == []


def test_belief_promotion_exposes_validated_stage_before_truth_candidate():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "validated_but_not_truth",
            "prior_confidence": 0.88,
            "semantic_consistency": 0.88,
            "causal_alignment": 0.82,
        }],
        "epistemic_evidence": [{
            "concept": "validated_but_not_truth",
            "source": source,
            "support_score": 0.88,
            "contradiction_score": 0.14,
            "reliability": 0.92,
            "causal_alignment": 0.82,
            "semantic_consistency": 0.88,
        } for source in [
            "causal_observation",
            "semantic_validation",
            "identity_validation",
        ]],
    }

    first = layer.run_cycle(context)
    second = layer.run_cycle(context)

    assert first["beliefs"][0]["state"] == "SUPPORTED"
    assert second["beliefs"][0]["state"] == "VALIDATED"
    assert second["truth_commitments"] == []
    promotion = second["belief_promotion_engine"]["evaluations"][0]
    assert promotion["promotion_state"] == "VALIDATED"
    assert "truth_candidate_contradiction" in promotion["blocked_gates"]
    candidate = second["truth_candidate_engine"]["evaluations"][0]
    contradiction = next(
        item
        for item in candidate["metrics"]
        if item["metric"] == "contradiction_score"
    )
    assert candidate["candidate_state"] == "ADVANCING_TO_TRUTH_CANDIDATE"
    assert candidate["validated_knowledge"] is True
    assert candidate["stage_eligible_for_truth_candidate"] is True
    assert candidate["metrics_eligible_for_truth_candidate"] is False
    assert candidate["eligibility_reason"] == "truth_candidate_metric_gaps"
    assert "contradiction_score" in candidate["blocked_metrics"]
    assert second["truth_candidate_engine"]["dominant_bottlenecks"][0][
        "metric"
    ] == "contradiction_score"
    assert contradiction["current_value"] == 0.14
    assert contradiction["threshold"] == {
        "comparator": "<",
        "required": 0.10,
    }
    assert contradiction["required_action"] == (
        "resolve_or_explain_contradictory_evidence"
    )
    assert second["beliefs"][0]["history"][-1]["truth_candidate"] == (
        candidate
    )


def test_promotion_diagnostics_distinguish_total_from_passed_trials():
    layer = EpistemicCognitionLayer()

    report = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "weak_shape_preservation",
            "prior_confidence": 0.82,
        }],
        "epistemic_evidence": [{
            "concept": "weak_shape_preservation",
            "source": "semantic_observation",
            "support_score": 0.62,
            "contradiction_score": 0.08,
            "reliability": 0.72,
            "causal_alignment": 0.62,
            "semantic_consistency": 0.70,
        }],
    })

    belief = report["beliefs"][0]
    promotion = report["belief_promotion_engine"]["evaluations"][0]
    supported_trial = next(
        item
        for item in promotion["gate_diagnostics"]
        if item["gate_name"] == "supported_trial"
    )

    assert belief["trial_count"] == 1
    assert promotion["total_trials"] == 1
    assert promotion["passed_trials"] == 0
    assert promotion["inconclusive_trials"] == 1
    assert supported_trial["source_metric"] == "passed_trials"
    assert supported_trial["current_value"] == 0
    assert supported_trial["gate_threshold"] == {
        "comparator": ">=",
        "required": 1,
    }
    assert supported_trial["status"] == "FAILED"
    assert supported_trial["failure_reason"] == "insufficient_passed_trials"
    assert belief["history"][0]["promotion"]["trial_counts"] == {
        "total": 1,
        "passed": 0,
        "failed": 0,
        "inconclusive": 1,
    }


def test_truth_candidate_engine_ranks_causal_alignment_as_dominant_gap():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="causal_gap_claim",
            claim="causal_gap_claim",
            state=BeliefState.VALIDATED,
            confidence=0.7938,
        ),
        EvidenceAggregate(
            concept="causal_gap_claim",
            evidence_strength=0.7336,
            contradiction_score=0.176,
            causal_alignment=0.6084,
        ),
        {
            "semantic_spine_report": {
                "semantic_spine_state": "semantic_spine_recovering",
                "recovery_streak": 1,
                "required_recovery_cycles": 3,
            },
        },
    )

    assert [
        item["metric"]
        for item in report["ranked_bottlenecks"]
    ] == [
        "confidence",
        "evidence_strength",
        "contradiction_score",
        "causal_alignment",
    ]
    assert report["dominant_bottleneck"]["metric"] == "causal_alignment"
    assert report["dominant_bottleneck"]["gap"] == 0.1916
    assert report["stage_eligible_for_truth_candidate"] is True
    assert report["metrics_eligible_for_truth_candidate"] is False
    assert report["eligibility_reason"] == "truth_candidate_metric_gaps"
    assert report["metric_progress"] == {
        "passed_count": 0,
        "required_count": 4,
        "progress_ratio": 0.0,
    }
    assert report["semantic_spine_recovery"] == {
        "stability_state": "semantic_spine_recovering",
        "recovery_streak": 1,
        "required_recovery_cycles": 3,
        "remaining_recovery_cycles": 2,
        "recovery_confirmation_pending": True,
    }


def test_truth_candidate_engine_marks_soft_contradiction_review_zone():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="near_threshold_claim",
            claim="near_threshold_claim",
            state=BeliefState.VALIDATED,
            confidence=0.90,
        ),
        EvidenceAggregate(
            concept="near_threshold_claim",
            evidence_strength=0.90,
            contradiction_score=0.1114,
            causal_alignment=0.90,
        ),
    )

    assert report["eligible_for_truth_candidate"] is True
    assert report["metrics_eligible_for_truth_candidate"] is True
    assert report["strict_qualified_metrics"] is False
    assert report["eligibility_reason"] == (
        "truth_candidate_contradiction_review_required"
    )
    assert report["candidate_state"] == (
        "ADVANCING_TO_TRUTH_CANDIDATE_REVIEW"
    )
    assert report["promotion_review_required"] is True
    assert report["soft_contradiction_review_only"] is True
    assert report["contradiction_review_required"] is True
    assert report["within_soft_review_zone"] is True
    assert report["contradiction_review_severity"] == "LOW_RISK_REVIEW"
    assert report["contradiction_review_zone"] == 0.02
    assert report["contradiction_gap"] == 0.0114


def test_truth_candidate_uses_adaptive_contradiction_threshold():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="symmetry_reasoning",
            claim="symmetry_reasoning",
            state=BeliefState.VALIDATED,
            confidence=0.90,
        ),
        EvidenceAggregate(
            concept="symmetry_reasoning",
            evidence_strength=0.90,
            contradiction_score=0.1159,
            causal_alignment=0.8164,
        ),
        {
            "knowledge_generalization": {
                "used_task_count": 31,
            },
            "causal_validation": {
                "validation_score": 0.8004,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.8164,
            },
            "contextual_truth": {
                "contextual_truth_score": 0.6907,
            },
            "contextual_truth_authority": {
                "effective_contextual_truth": 0.6907,
                "contextual_truth_supported": True,
            },
            "context_hierarchy": {
                "score": 0.94,
            },
            "semantic_context": {
                "confidence": 0.90,
            },
            "causal_explanation": {
                "why": ["observed in 31 tasks"],
            },
            "causal_validation_report": {
                "how_we_know": ["validated across 34 tasks"],
            },
        },
    )

    assert report["eligible_for_truth_candidate"] is True
    assert report["eligibility_reason"] == "truth_candidate_ready"
    assert report["blocked_metrics"] == []
    assert report["contradiction_threshold"] >= 0.1159
    assert report["adaptive_contradiction_governance"][
        "base_threshold"
    ] == 0.10
    assert report["adaptive_contradiction_governance"][
        "contradiction_below_dynamic_threshold"
    ] is True


def test_truth_candidate_uses_dependency_promotion_bonus_for_process_concept():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="growth",
            claim="growth",
            state=BeliefState.VALIDATED,
            confidence=0.90,
        ),
        EvidenceAggregate(
            concept="growth",
            evidence_strength=0.90,
            contradiction_score=0.05,
            causal_alignment=0.82,
        ),
        {
            "knowledge_generalization": {
                "used_task_count": 8,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.74,
            },
            "causal_validation": {
                "validation_score": 0.70,
                "promotion_dependency_score": 0.91,
                "dependency_promotion_evidence": {
                    "dependency_confidence": 0.9017,
                    "dependency_chain_depth": 5,
                    "dependency_chain_coverage": 0.8556,
                    "missing_dependencies": [],
                },
            },
        },
    )

    metrics = {
        item["metric"]: item
        for item in report["metrics"]
    }

    assert report["eligible_for_truth_candidate"] is True
    assert report["promotion_dependency_score"] >= 0.90
    assert report["promotion_dependency_bonus"] > 0.0
    assert metrics["causal_validation_score"]["passed"] is True
    assert report["dependency_promotion_blockers"] == []


def test_belief_promotion_allows_soft_contradiction_truth_candidate_review():
    report = BeliefPromotionEngine().evaluate(
        EvidenceAggregate(
            concept="near_threshold_claim",
            evidence_count=3,
            evidence_strength=0.90,
            contradiction_score=0.1114,
            semantic_consistency=0.90,
            causal_alignment=0.90,
        ),
        [
            EpistemicTrial(
                concept="near_threshold_claim",
                support_score=0.90,
                contradiction_score=0.1114,
                evidence_strength=0.90,
                semantic_consistency=0.90,
                causal_alignment=0.90,
                trial_result=TrialResult.PASSED,
                evidence_count=3,
                trial_number=1,
            ),
            EpistemicTrial(
                concept="near_threshold_claim",
                support_score=0.90,
                contradiction_score=0.1114,
                evidence_strength=0.90,
                semantic_consistency=0.90,
                causal_alignment=0.90,
                trial_result=TrialResult.PASSED,
                evidence_count=3,
                trial_number=2,
            ),
        ],
        0.90,
    )
    contradiction_gate = next(
        item
        for item in report["gate_diagnostics"]
        if item["gate_name"] == "truth_candidate_contradiction"
    )

    assert report["promotion_state"] == "TRUTH_CANDIDATE"
    assert contradiction_gate["passed"] is True
    assert contradiction_gate["contradiction_review_required"] is True
    assert contradiction_gate["within_soft_review_zone"] is True
    assert contradiction_gate[
        "soft_review_permits_truth_candidate_promotion"
    ] is True
    assert contradiction_gate["truth_commit_review_still_required"] is True


def test_locked_truth_candidate_exposes_runtime_contradiction_snapshot():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="locked_truth",
            claim="locked_truth",
            state=BeliefState.TRUTH_COMMITTED,
            confidence=0.90,
        ),
        EvidenceAggregate(
            concept="locked_truth",
            contradiction_score=0.1114,
        ),
    )

    assert report["truth_candidate_evaluation_skipped"] is True
    assert report["effective_contradiction_score"] == 0.1114
    assert report["contradiction_threshold"] == 0.10
    assert report["contradiction_review_required"] is True


def test_locked_truth_candidate_marks_medium_contradiction_review():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="locked_topology",
            claim="locked_topology",
            state=BeliefState.TRUTH_COMMITTED,
            confidence=0.90,
        ),
        EvidenceAggregate(
            concept="locked_topology",
            contradiction_score=0.122,
        ),
    )

    assert report["contradiction_gap"] == 0.022
    assert report["contradiction_review_required"] is True
    assert report["within_soft_review_zone"] is False
    assert report["contradiction_review_severity"] == (
        "MEDIUM_RISK_REVIEW"
    )


def test_truth_candidate_consumes_context_hierarchy_and_authority_reports():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="shape_preservation",
            claim="shape_preservation",
            state=BeliefState.VALIDATED,
            confidence=0.90,
        ),
        EvidenceAggregate(
            concept="shape_preservation",
            evidence_strength=0.90,
            contradiction_score=0.05,
            causal_alignment=0.82,
        ),
        {
            "context_discovery": {
                "transformation_family": "duplication",
            },
            "context_hierarchy": {
                "score": 0.94,
                "hierarchy_ready": True,
            },
            "semantic_context": {
                "confidence": 0.90,
                "status": "SEMANTICALLY_VALIDATED",
            },
            "causal_validation": {
                "validation_score": 0.80,
                "context_consistency": 0.765,
                "dependency_coherence": 0.70,
                "contradiction_resistance": 0.90,
                "identity_compatibility": 1.0,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.83,
            },
            "contextual_truth": {
                "contextual_truth_score": 0.6874,
                "context_confidence": 0.8228,
                "transfer_reliability": 0.4444,
            },
        },
    )

    assert report["context_discovery"]["transformation_family"] == (
        "duplication"
    )
    assert report["context_hierarchy"]["context_hierarchy_score"] == 0.94
    assert report["contextual_truth_authority"][
        "contextual_truth_authority"
    ] >= 0.60
    assert "context_hierarchy_score" not in report["blocked_metrics"]


def test_truth_candidate_uses_effective_contextual_truth_alpha_threshold():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="symmetry_reasoning",
            claim="symmetry_reasoning",
            state=BeliefState.VALIDATED,
            confidence=0.90,
        ),
        EvidenceAggregate(
            concept="symmetry_reasoning",
            evidence_strength=0.90,
            contradiction_score=0.05,
            causal_alignment=0.82,
        ),
        {
            "context_discovery": {
                "transformation_family": "duplication",
            },
            "context_hierarchy": {
                "score": 0.94,
                "hierarchy_ready": True,
            },
            "semantic_context": {
                "confidence": 0.90,
                "status": "SEMANTICALLY_VALIDATED",
            },
            "causal_validation": {
                "validation_score": 0.80,
                "context_consistency": 0.5589,
                "dependency_coherence": 0.70,
                "contradiction_resistance": 0.90,
                "identity_compatibility": 1.0,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.83,
            },
            "contextual_truth": {
                "contextual_truth_score": 0.6907,
                "context_confidence": 0.8228,
                "transfer_reliability": 1.0,
            },
        },
    )

    contextual_metric = next(
        item
        for item in report["metrics"]
        if item["metric"] == "contextual_truth_score"
    )

    assert report["contextual_truth_authority"][
        "effective_contextual_truth"
    ] == 0.6907
    assert report["contextual_truth_authority"][
        "contextual_truth_supported"
    ] is True
    assert contextual_metric["passed"] is True
    assert "contextual_truth_score" not in report["blocked_metrics"]


def test_locked_truth_candidate_still_reports_contextual_authority():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="color_preservation",
            claim="color_preservation",
            state=BeliefState.TRUTH_COMMITTED,
            confidence=0.90,
        ),
        EvidenceAggregate(
            concept="color_preservation",
            evidence_strength=0.90,
            contradiction_score=0.05,
            causal_alignment=0.82,
        ),
        {
            "context_discovery": {
                "transformation_family": "duplication",
            },
            "context_hierarchy": {
                "score": 0.94,
                "hierarchy_ready": True,
            },
            "semantic_context": {
                "confidence": 0.90,
                "status": "SEMANTICALLY_VALIDATED",
            },
            "causal_validation": {
                "validation_score": 0.80,
                "context_consistency": 0.5589,
                "dependency_coherence": 0.70,
                "contradiction_resistance": 0.90,
                "identity_compatibility": 1.0,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.83,
            },
            "contextual_truth": {
                "contextual_truth_score": 0.6907,
                "context_confidence": 0.8228,
                "transfer_reliability": 1.0,
            },
        },
    )

    assert report["truth_candidate_evaluation_skipped"] is True
    assert report["contextual_truth_authority"][
        "contextual_truth_authority"
    ] is not None
    assert report["context_discovery"]["transformation_family"] == (
        "duplication"
    )


def test_identity_integration_consumes_contextual_truth_authority_support():
    report = IdentitySafeTruthIntegrationEngine().evaluate(
        Belief(
            concept="shape_preservation",
            claim="shape_preservation",
            state=BeliefState.TRUTH_CANDIDATE,
            confidence=0.95,
        ),
        EvidenceAggregate(
            concept="shape_preservation",
            semantic_consistency=1.0,
            causal_alignment=1.0,
        ),
        {"eligible_for_truth_candidate": True},
        {
            "identity_continuity": 0.82,
            "contextual_truth": {
                "contextual_truth_score": 0.68,
            },
            "contextual_truth_authority": {
                "contextual_truth_supported": True,
                "contextual_truth_authority": 0.78,
            },
            "context_hierarchy": {
                "score": 0.94,
                "hierarchy_required": True,
            },
        },
    )

    assert "contextual_truth_supported" not in report["failed_checks"]
    assert "context_hierarchy_supported" not in report["failed_checks"]


def test_repeated_color_trials_report_stalled_causal_attestation_gap():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "color_preservation",
            "prior_confidence": 0.82,
            "semantic_consistency": 0.86,
            "causal_alignment": 0.4985,
        }],
        "epistemic_evidence": [{
            "concept": "color_preservation",
            "source": "semantic_abstraction_observation",
            "support_score": 0.90,
            "contradiction_score": 0.1949,
            "reliability": 0.90,
            "causal_alignment": 0.4985,
            "semantic_consistency": 0.86,
        }],
    }

    for _ in range(3):
        layer.run_cycle(context)
    report = layer.run_cycle(context)

    resolution = report["trial_resolution_engine"]["evaluations"][0]
    attestation = report["causal_attestation_engine"]["evaluations"][0]

    assert resolution["trial_result"] == "INCONCLUSIVE"
    assert resolution["inconclusive_streak"] == 4
    assert resolution["stalled_inconclusive_pattern"] is True
    assert resolution["dominant_unresolved_gate"]["gate_name"] == (
        "causal_alignment"
    )
    assert report["trial_resolution_engine"]["stalled_concepts"] == [
        "color_preservation"
    ]
    assert attestation["architecture_state"] == (
        "CAUSAL_ATTESTATION_INSUFFICIENT_FOR_TRIAL"
    )
    assert attestation["current_causal_alignment"] == 0.4985
    assert attestation["trial_resolution_gap"] == 0.1015
    assert attestation["truth_candidate_gap"] == 0.3015
    assert attestation["direct_causal_source_count"] == 0
    assert report["causal_attestation_engine"]["trial_blocked_concepts"] == [
        "color_preservation"
    ]
    advancement = report["truth_advancement_planner"]
    assert advancement["phase"] == "5.1"
    assert advancement["proposed_experiments"][0]["phase"] == "5.2"
    assert advancement["proposed_experiments"][0]["target_metric"] == (
        "causal_alignment"
    )
    hypotheses = report["experiment_hypothesis_generator"]["hypotheses"]
    requests = report[
        "active_knowledge_acquisition_engine"
    ]["sandbox_execution_requests"]
    assert hypotheses[0]["target_metric"] == "causal_alignment"
    assert hypotheses[0]["sandbox_only"] is True
    assert requests[0]["execution_permission"] == "sandbox_only"


def test_truth_advancement_planner_avoids_duplicate_stalled_experiments():
    planner = TruthAdvancementPlanner()
    trial_resolution = {
        "stalled_inconclusive_pattern": True,
        "dominant_unresolved_gate": {
            "gate_name": "causal_alignment",
        },
    }
    attestation = {
        "architecture_state": "CAUSAL_ATTESTATION_INSUFFICIENT_FOR_TRIAL",
    }
    contradiction = {
        "resolution_state": "CONTRADICTION_CLEAR_FOR_TRIAL",
    }
    candidate = {
        "dominant_bottleneck": {
            "metric": "causal_alignment",
        },
    }

    first = planner.evaluate(
        "color_preservation",
        trial_resolution,
        attestation,
        contradiction,
        candidate,
    )
    second = planner.evaluate(
        "color_preservation",
        trial_resolution,
        attestation,
        contradiction,
        candidate,
    )

    first_experiment = first["experiment_proposal"]
    second_experiment = second["experiment_proposal"]
    assert first_experiment["strategy"] == "controlled_feature_ablation"
    assert second_experiment["strategy"] == "counterfactual_feature_swap"
    assert first_experiment["fingerprint"] != second_experiment["fingerprint"]
    assert second["proposal_count"] == 2
    assert second["duplicate_experiment_forbidden"] is True
    assert second["autonomous_execution_forbidden"] is True


def test_truth_advancement_planner_targets_validated_truth_metric_gap():
    planner = TruthAdvancementPlanner()
    report = planner.evaluate(
        "shape_preservation",
        {
            "stalled_inconclusive_pattern": False,
            "dominant_unresolved_gate": None,
        },
        {
            "architecture_state": "CAUSAL_ATTESTATION_FORMING",
        },
        {
            "resolution_state": "CONTRADICTION_CLEAR_FOR_TRIAL",
        },
        {
            "eligibility_reason": "truth_candidate_metric_gaps",
            "stage_eligible_for_truth_candidate": True,
            "dominant_bottleneck": {
                "metric": "causal_alignment",
            },
        },
    )

    assert report["planner_state"] == "EXPERIMENT_PROPOSED"
    assert report["advancement_trigger"] == "truth_candidate_metric_gaps"
    assert report["experiment_proposal"]["target_metric"] == (
        "causal_alignment"
    )


def test_truth_advancement_planner_targets_soft_contradiction_review():
    report = TruthAdvancementPlanner().evaluate(
        "position_preservation",
        {
            "stalled_inconclusive_pattern": False,
            "dominant_unresolved_gate": None,
        },
        {},
        {},
        {
            "eligibility_reason":
            "truth_candidate_contradiction_review_required",
            "dominant_bottleneck": {
                "metric": "contradiction_score",
            },
        },
    )

    assert report["planner_state"] == "EXPERIMENT_PROPOSED"
    assert report["advancement_trigger"] == (
        "truth_candidate_contradiction_review_required"
    )
    assert report["experiment_proposal"]["target_metric"] == (
        "contradiction_score"
    )


def test_experiment_hypothesis_routes_only_to_sandbox_acquisition():
    planner = TruthAdvancementPlanner()
    advancement = planner.evaluate(
        "color_preservation",
        {
            "stalled_inconclusive_pattern": True,
            "dominant_unresolved_gate": {
                "gate_name": "causal_alignment",
            },
        },
        {
            "architecture_state": "CAUSAL_ATTESTATION_INSUFFICIENT_FOR_TRIAL",
        },
        {
            "resolution_state": "CONTRADICTION_CLEAR_FOR_TRIAL",
        },
        {
            "dominant_bottleneck": {
                "metric": "causal_alignment",
            },
        },
    )
    proposal = advancement["experiment_proposal"]
    hypothesis = ExperimentHypothesisGenerator().generate(proposal)
    request = ActiveKnowledgeAcquisitionEngine().prepare_request(
        proposal,
        hypothesis,
    )

    assert hypothesis["phase"] == "5.3"
    assert hypothesis["falsification_criterion"]
    assert request["phase"] == "5.4"
    assert request["execution_permission"] == "sandbox_only"
    assert request["execution_contract"]["persistent_commit_forbidden"] is True
    assert request["execution_contract"][
        "automatic_truth_commit_forbidden"
    ] is True


def test_active_acquisition_ingests_only_validated_sandbox_results():
    engine = ActiveKnowledgeAcquisitionEngine()
    unvalidated = {
        "experiment_id": "experiment:1",
        "concept": "shape_preservation",
        "baseline_execution_result": 0.55,
        "intervention_execution_result": 0.91,
        "causal_effect_delta": 0.36,
        "contradiction_delta": 0.04,
        "measured_causal_alignment": 0.91,
        "measured_contradiction_score": 0.06,
        "reversible": True,
    }
    rejected = engine.ingest_results(unvalidated)
    assert rejected["epistemic_evidence_exports"] == []
    assert rejected["rejected_results"][0]["reason"] == (
        "sandbox_validation_required"
    )

    accepted = engine.ingest_results({
        **unvalidated,
        "sandbox_validated": True,
    })
    export = accepted["epistemic_evidence_exports"][0]
    assert export["source"] == "sandbox_causal_intervention"
    assert export["causal_alignment"] == 0.91
    assert export["metadata"]["truth_commit_forbidden"] is True
    assert accepted["reevaluate_truth_candidate_after_ingestion"] is True


def test_layer_ingests_sandbox_attestation_before_truth_reevaluation():
    layer = EpistemicCognitionLayer()
    report = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "sandbox_attested_shape",
            "prior_confidence": 0.82,
            "semantic_consistency": 0.86,
            "causal_alignment": 0.50,
        }],
        "sandbox_experiment_results": [{
            "experiment_id": "sandbox:shape:1",
            "concept": "sandbox_attested_shape",
            "baseline_execution_result": 0.40,
            "intervention_execution_result": 0.95,
            "causal_effect_delta": 0.55,
            "contradiction_delta": 0.03,
            "measured_causal_alignment": 0.95,
            "measured_contradiction_score": 0.04,
            "measured_support_score": 0.92,
            "semantic_consistency": 0.90,
            "sandbox_validated": True,
            "reversible": True,
        }],
    })

    acquisition = report["active_knowledge_acquisition_engine"]
    attestation = report["causal_attestation_engine"]["evaluations"][0]
    assert acquisition["result_ingestion"]["accepted_results"]
    assert attestation["direct_causal_source_count"] == 1
    assert attestation["source_diagnostics"][0]["source"] == (
        "sandbox_causal_intervention"
    )


def test_sandbox_executor_analyzes_effect_and_recalibrates_survival_noise():
    planner = TruthAdvancementPlanner()
    advancement = planner.evaluate(
        "shape_preservation",
        {
            "stalled_inconclusive_pattern": True,
            "dominant_unresolved_gate": {
                "gate_name": "causal_alignment",
            },
        },
        {
            "architecture_state": "CAUSAL_ATTESTATION_INSUFFICIENT_FOR_TRIAL",
        },
        {
            "resolution_state": "CONTRADICTION_CLEAR_FOR_TRIAL",
        },
        {
            "dominant_bottleneck": {
                "metric": "causal_alignment",
            },
        },
    )
    proposal = advancement["experiment_proposal"]
    hypothesis = ExperimentHypothesisGenerator().generate(proposal)
    request = ActiveKnowledgeAcquisitionEngine().prepare_request(
        proposal,
        hypothesis,
    )
    executor = SandboxExperimentExecutor()
    executor.register([request])
    execution = executor.run({
        proposal["experiment_id"]: {
            "isolated_world": True,
            "reversible": True,
            "baseline_execution_result": 0.96,
            "intervention_execution_result": 0.18,
            "baseline_contradiction_score": 0.04,
            "intervention_contradiction_score": 0.09,
        },
    })
    analysis = CausalEffectAnalyzer().analyze(
        execution["completed_experiments"]
    )
    registry = EvidenceRegistry()
    recalibration = EpistemicWeightRecalibrationEngine().evaluate(
        registry,
        analysis["measurements"],
    )

    measurement = analysis["measurements"][0]
    assert execution["phase"] == "5.5"
    assert measurement["causal_effect_delta"] == 0.78
    assert measurement["analysis_state"] == "DIRECT_CAUSAL_EFFECT_OBSERVED"
    assert recalibration["phase"] == "5.7"
    assert registry.fitness_ratio_for("shape_preservation") == 0.20
    assert recalibration["direct_metric_inflation_forbidden"] is True


def test_layer_executes_queued_epistemic_experiment_in_isolated_sandbox():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "color_preservation",
            "prior_confidence": 0.82,
            "semantic_consistency": 0.86,
            "causal_alignment": 0.4985,
        }],
        "epistemic_evidence": [{
            "concept": "color_preservation",
            "source": "semantic_abstraction_observation",
            "support_score": 0.90,
            "contradiction_score": 0.1949,
            "reliability": 0.90,
            "causal_alignment": 0.4985,
            "semantic_consistency": 0.86,
        }],
    }

    for _ in range(3):
        report = layer.run_cycle(context)
    request = report[
        "active_knowledge_acquisition_engine"
    ]["sandbox_execution_requests"][0]
    experiment_id = request["experiment_id"]
    report = layer.run_cycle({
        **context,
        "sandbox_experiment_worlds": {
            experiment_id: {
                "isolated_world": True,
                "reversible": True,
                "baseline_execution_result": 0.94,
                "intervention_execution_result": 0.14,
                "baseline_contradiction_score": 0.03,
                "intervention_contradiction_score": 0.07,
                "semantic_consistency": 0.91,
            },
        },
    })

    execution = report["sandbox_experiment_executor"]
    analyzer = report["causal_effect_analyzer"]
    recalibration = report["epistemic_weight_recalibration_engine"]
    ingestion = report[
        "active_knowledge_acquisition_engine"
    ]["result_ingestion"]
    assert execution["completed_experiments"][0]["experiment_id"] == (
        experiment_id
    )
    assert analyzer["direct_causal_effect_count"] == 1
    assert recalibration["recalibrations"][0][
        "recalibrated_evolutionary_fitness_ratio"
    ] == 0.20
    assert ingestion["accepted_results"][0]["experiment_id"] == experiment_id


def test_sandbox_executor_rejects_non_isolated_world():
    executor = SandboxExperimentExecutor()
    executor.register([{
        "experiment_id": "unsafe:experiment",
        "concept": "shape_preservation",
        "execution_permission": "sandbox_only",
        "execution_contract": {
            "isolated_world_required": True,
        },
        "experiment_proposal": {
            "strategy": "controlled_feature_ablation",
        },
    }])
    report = executor.run({
        "unsafe:experiment": {
            "isolated_world": False,
            "reversible": True,
            "baseline_execution_result": 0.90,
            "intervention_execution_result": 0.10,
        },
    })

    assert report["completed_experiments"] == []
    assert report["blocked_experiments"][0]["reason"] == (
        "isolated_world_validation_required"
    )


def test_sandbox_runner_waits_for_declared_case_without_fabricating_result():
    runner = SandboxExperimentRunner(
        SandboxExperimentExecutor(),
        ExperimentResultEvaluator(),
    )
    report = runner.run([{
        "experiment_id": "sandbox:awaiting_case",
        "concept": "symbolic_remapping",
        "execution_permission": "sandbox_only",
        "execution_contract": {
            "isolated_world_required": True,
        },
        "experiment_proposal": {
            "strategy": "discover_supported_region",
        },
    }])

    assert report["runner_state"] == "AWAITING_DECLARED_SANDBOX_CASES"
    assert report["completed_experiment_count"] == 0
    assert report["automatic_case_bindings"] == []
    assert report["fabricated_experiment_results_forbidden"] is True


def test_layer_autonomously_runs_declared_sandbox_case_and_integrates_result():
    layer = EpistemicCognitionLayer()
    first = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "symbolic_remapping",
        }],
        "arc_replication_results": [{
            "concept": "symbolic_remapping",
            "task_path": "data/training/task_001.json",
            "sandbox_validated": True,
            "isolated_world": True,
            "independent_task": True,
            "accuracy": 0.55,
            "structural_score": 0.58,
            "final_score": 0.59,
            "conditions": {"symbol_mapping": "ambiguous"},
            "failure_reason": "symbol_collision",
        }],
    })
    request = first[
        "active_knowledge_acquisition_engine"
    ]["sandbox_execution_requests"][0]

    second = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "symbolic_remapping",
        }],
        "autonomous_sandbox_experiment_cases": [{
            "case_id": "symbolic_remapping:supported:1",
            "concept": "symbolic_remapping",
            "strategy": "discover_supported_region",
            "isolated_world": True,
            "reversible": True,
            "baseline_execution_result": 0.92,
            "intervention_execution_result": 0.18,
            "baseline_contradiction_score": 0.04,
            "intervention_contradiction_score": 0.06,
            "semantic_consistency": 0.91,
        }],
    })

    runner = second["sandbox_experiment_runner"]
    evaluator = second["experiment_result_evaluator"]
    integration = second["evidence_integration_engine"]

    assert runner["phase"] == "6.95"
    assert runner["automatic_case_bindings"][0]["experiment_id"] == (
        request["experiment_id"]
    )
    assert runner["completed_experiment_count"] == 1
    assert evaluator["direct_causal_effect_count"] == 1
    assert integration["integrated_evidence_count"] == 1
    assert integration["integrated_evidence"][0]["source"] == (
        "sandbox_causal_intervention"
    )


def test_task_generator_builds_in_memory_arc_probes_without_results():
    tasks = TaskGenerator().generate_tasks(
        concept="density_preservation",
        count=20,
    )

    assert len(tasks) == 20
    assert tasks[0]["concept"] == "density_preservation"
    assert tasks[0]["train"][0]["input"]
    assert tasks[0]["train"][0]["output"]
    assert tasks[0]["test"][0]["input"]
    assert tasks[0]["independent_task_replication"] is False
    assert tasks[0]["persistent_task_write_forbidden"] is True
    template = tasks[0]["sandbox_case_template"]
    assert template["execution_result_required"] is True
    assert "baseline_execution_result" not in template
    assert "intervention_execution_result" not in template


def test_curriculum_generates_probe_without_automatic_evidence_inflation():
    layer = EpistemicCognitionLayer()
    first = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "symbolic_remapping",
        }],
        "arc_replication_results": [{
            "concept": "symbolic_remapping",
            "task_path": "data/training/task_001.json",
            "sandbox_validated": True,
            "isolated_world": True,
            "independent_task": True,
            "accuracy": 0.55,
            "structural_score": 0.58,
            "final_score": 0.59,
        }],
    })
    initial_evidence_count = first["evidence_registry"]["evidence_count"]

    second = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "symbolic_remapping",
        }],
    })
    curriculum = second["curriculum_manager"]

    assert curriculum["generated_task_count"] == 1
    assert curriculum["sandbox_cases"] == []
    assert curriculum["generated_probe_results_must_be_measured"] is True
    assert second["sandbox_experiment_runner"]["runner_state"] == (
        "AWAITING_DECLARED_SANDBOX_CASES"
    )
    assert second["evidence_integration_engine"][
        "integrated_evidence_count"
    ] == 0
    assert second["evidence_registry"]["evidence_count"] == (
        initial_evidence_count
    )


def test_boundary_refinement_builds_midpoints_and_matched_probe_pairs():
    report = BoundaryRefinementEngine().evaluate(
        "density_preservation",
        {
            "mixed_outcomes_detected": True,
            "boundary_conditions": [{
                "metric": "causal_alignment",
                "holds_average": 0.8938,
                "fails_average": 0.5719,
                "direction": "higher_when_holds",
            }],
        },
    )

    target = report["boundary_targets"][0]
    probes = report["matched_boundary_probes"]

    assert report["refinement_state"] == (
        "MATCHED_BOUNDARY_REPLICATION_REQUIRED"
    )
    assert target["decision_midpoint"] == 0.7329
    assert target["probe_lower_bound"] < target["decision_midpoint"]
    assert target["probe_upper_bound"] > target["decision_midpoint"]
    assert len(probes) == 2
    assert probes[0]["pair_id"] == probes[1]["pair_id"]
    assert {
        item["probe_side"]
        for item in probes
    } == {
        "below_boundary",
        "above_boundary",
    }


def test_curriculum_generates_matched_boundary_tasks_without_evidence():
    layer = EpistemicCognitionLayer()
    first = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "density_preservation",
        }],
        "arc_replication_results": [
            {
                "concept": "density_preservation",
                "task_path": "data/training/task_001.json",
                "sandbox_validated": True,
                "isolated_world": True,
                "independent_task": True,
                "accuracy": 0.55,
                "structural_score": 0.58,
                "final_score": 0.59,
            },
            {
                "concept": "density_preservation",
                "task_path": "data/training/task_002.json",
                "sandbox_validated": True,
                "isolated_world": True,
                "independent_task": True,
                "accuracy": 0.92,
                "structural_score": 0.90,
                "final_score": 0.91,
            },
        ],
    })
    initial_evidence_count = first["evidence_registry"]["evidence_count"]
    refinement = first["boundary_refinement_engine"]["evaluations"][0]

    second = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "density_preservation",
        }],
    })
    curriculum = second["curriculum_manager"]

    assert refinement["matched_boundary_runner"]["matched_pair_count"] == 3
    assert curriculum["generated_task_count"] == 6
    assert curriculum["boundary_targeted_task_count"] == 6
    assert curriculum["sandbox_case_templates"][0]["boundary_probe"]
    assert second["evidence_integration_engine"][
        "integrated_evidence_count"
    ] == 0
    assert second["evidence_registry"]["evidence_count"] == (
        initial_evidence_count
    )


def test_synthetic_task_generator_never_claims_independent_experience():
    task = SyntheticTaskGenerator().generate_tasks(
        "density_preservation",
        count=1,
    )[0]

    assert task["system"] == "synthetic_task_generator"
    assert task["learning_phase"] == "7-prelude"
    assert task["experience_class"] == "synthetic_probe"
    assert task["independent_experience"] is False
    assert task["independent_task_replication"] is False


def test_experiment_scheduler_prioritizes_high_value_requests():
    schedule = ExperimentScheduler().schedule([
        {
            "request_id": "request:low",
            "experiment_proposal": {
                "priority": "low",
            },
        },
        {
            "request_id": "request:high",
            "experiment_proposal": {
                "priority": "high",
            },
        },
    ])

    assert schedule["scheduled_requests"][0]["request_id"] == "request:high"
    assert schedule["scheduled_request_count"] == 2


def test_measured_synthetic_probe_enters_replay_without_independence_credit():
    layer = EpistemicCognitionLayer()
    first = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "symbolic_remapping",
        }],
        "arc_replication_results": [{
            "concept": "symbolic_remapping",
            "task_path": "data/training/task_001.json",
            "sandbox_validated": True,
            "isolated_world": True,
            "independent_task": True,
            "accuracy": 0.55,
            "structural_score": 0.58,
            "final_score": 0.59,
        }],
    })
    request = first[
        "active_knowledge_acquisition_engine"
    ]["sandbox_execution_requests"][0]
    task_id = "synthetic_arc_probe:symbolic_remapping:measured:1"

    second = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "symbolic_remapping",
        }],
        "autonomous_sandbox_experiment_cases": [{
            "case_id": task_id,
            "concept": "symbolic_remapping",
            "strategy": request["experiment_proposal"]["strategy"],
            "isolated_world": True,
            "reversible": True,
            "synthetic_sandbox_probe": True,
            "generated_task_id": task_id,
            "baseline_execution_result": 0.92,
            "intervention_execution_result": 0.18,
            "baseline_contradiction_score": 0.04,
            "intervention_contradiction_score": 0.06,
        }],
    })
    replay = second["experience_replay_buffer"]

    assert replay["experience_count"] == 1
    assert replay["synthetic_experience_count"] == 1
    assert replay["independent_experience_count"] == 0
    assert replay["synthetic_experiences_are_not_independent"] is True


def test_causal_arbitration_prefers_execution_over_survival_context():
    registry = EvidenceRegistry()
    for index in range(6):
        registry.collect({
            "concept": "shape_preservation",
            "source": "evolutionary_trait_survival_history",
            "support_score": 0.62,
            "contradiction_score": 0.20,
            "reliability": 0.76,
            "causal_alignment": 0.2966,
            "semantic_consistency": 0.72,
            "metadata": {
                "evidence_id": f"survival:{index}",
                "survival_is_not_truth": True,
            },
        })
    registry.collect({
        "concept": "shape_preservation",
        "source": "execution_validation",
        "support_score": 0.96,
        "contradiction_score": 0.03,
        "reliability": 0.98,
        "causal_alignment": 0.9469,
        "semantic_consistency": 0.94,
        "metadata": {
            "evidence_id": "execution:shape",
        },
    })

    before = registry.aggregate("shape_preservation")
    arbitration = CausalEvidenceArbitrationEngine().evaluate(
        registry,
        "shape_preservation",
    )
    after = registry.aggregate("shape_preservation")

    assert arbitration["decision"] == "DIRECT_CAUSAL_EVIDENCE_PREVAILS"
    assert arbitration["winning_source"] == "execution_validation"
    assert arbitration["conflict_gap"] == 0.6503
    assert arbitration["effective_evolutionary_fitness_ratio"] == 0.10
    assert after.causal_alignment > before.causal_alignment
    assert arbitration["direct_metric_inflation_forbidden"] is True


def test_layer_reports_causal_arbitration_before_trial_resolution():
    layer = EpistemicCognitionLayer()
    report = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "color_preservation",
            "prior_confidence": 0.82,
            "semantic_consistency": 0.86,
            "causal_alignment": 0.54,
        }],
        "epistemic_evidence": [
            {
                "concept": "color_preservation",
                "source": "evolutionary_trait_survival_history",
                "support_score": 0.65,
                "contradiction_score": 0.18,
                "reliability": 0.76,
                "causal_alignment": 0.2966,
                "semantic_consistency": 0.72,
                "metadata": {
                    "evidence_id": "survival:color",
                    "survival_is_not_truth": True,
                },
            },
            {
                "concept": "color_preservation",
                "source": "execution_validation",
                "support_score": 0.96,
                "contradiction_score": 0.03,
                "reliability": 0.98,
                "causal_alignment": 0.9469,
                "semantic_consistency": 0.94,
                "metadata": {
                    "evidence_id": "execution:color",
                },
            },
        ],
    })

    arbitration = report[
        "causal_evidence_arbitration_engine"
    ]["evaluations"][0]
    attestation = report["causal_attestation_engine"]["evaluations"][0]
    assert report[
        "causal_evidence_arbitration_engine"
    ]["conflicted_concepts"] == ["color_preservation"]
    assert arbitration["decision"] == "DIRECT_CAUSAL_EVIDENCE_PREVAILS"
    assert attestation["causal_evidence_arbitration"] == arbitration
    assert attestation["current_causal_alignment"] > 0.80


def test_evidence_fusion_separates_direct_causality_from_survival_context():
    registry = EvidenceRegistry()
    fusion = EpistemicEvidenceFusionEngine()
    registry.fusion_engine = fusion
    registry.collect({
        "concept": "shape_preservation",
        "source": "execution_validation",
        "support_score": 0.96,
        "contradiction_score": 0.03,
        "reliability": 0.98,
        "causal_alignment": 0.9575,
        "semantic_consistency": 0.94,
    })
    registry.collect({
        "concept": "shape_preservation",
        "source": "evolutionary_trait_survival_history",
        "support_score": 0.62,
        "contradiction_score": 0.20,
        "reliability": 0.76,
        "causal_alignment": 0.3544,
        "semantic_consistency": 0.72,
        "metadata": {
            "survival_is_not_truth": True,
        },
    })
    registry.collect({
        "concept": "shape_preservation",
        "source": "causal_attestation",
        "support_score": 0.70,
        "contradiction_score": 0.12,
        "reliability": 0.78,
        "causal_alignment": 0.51,
        "semantic_consistency": 0.74,
    })

    aggregate = registry.aggregate("shape_preservation")
    report = fusion.report_for("shape_preservation")

    assert aggregate.causal_alignment == 0.9575
    assert report["causal_fusion_policy"] == "DIRECT_CAUSAL_CHANNEL_PREVAILS"
    assert report["selected_direct_causal_source"] == "execution_validation"
    assert report["channels"]["direct_causal"][
        "average_causal_alignment"
    ] == 0.9575
    assert report["channels"]["evolutionary_context"][
        "average_causal_alignment"
    ] == 0.3544
    assert report["weak_context_cannot_reduce_direct_causal_alignment"] is True


def test_layer_reports_fused_direct_causal_channel_to_trial_resolution():
    layer = EpistemicCognitionLayer()
    report = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "shape_preservation",
            "prior_confidence": 0.82,
            "semantic_consistency": 0.86,
            "causal_alignment": 0.54,
        }],
        "epistemic_evidence": [
            {
                "concept": "shape_preservation",
                "source": "execution_validation",
                "support_score": 0.96,
                "contradiction_score": 0.03,
                "reliability": 0.98,
                "causal_alignment": 0.9575,
                "semantic_consistency": 0.94,
            },
            {
                "concept": "shape_preservation",
                "source": "evolutionary_trait_survival_history",
                "support_score": 0.62,
                "contradiction_score": 0.20,
                "reliability": 0.76,
                "causal_alignment": 0.3544,
                "semantic_consistency": 0.72,
                "metadata": {
                    "survival_is_not_truth": True,
                },
            },
        ],
    })

    fusion = report["epistemic_evidence_fusion_engine"]
    evaluation = report["evaluations"][0]
    assert fusion["direct_causal_channel_concepts"] == [
        "shape_preservation"
    ]
    assert evaluation["evidence"]["causal_alignment"] == 0.9575
    assert evaluation["trial"]["causal_alignment"] == 0.9575


def test_evidence_replication_requests_new_arc_tasks_for_strength_only_gap():
    engine = EvidenceReplicationEngine()
    report = engine.propose(
        "shape_preservation",
        Belief(
            concept="shape_preservation",
            claim="shape_preservation",
            state=BeliefState.VALIDATED,
        ),
        {
            "stage_eligible_for_truth_candidate": True,
            "blocked_metrics": ["evidence_strength"],
            "metrics": [
                {
                    "metric": "causal_alignment",
                    "current_value": 0.9589,
                },
                {
                    "metric": "contradiction_score",
                    "current_value": 0.0705,
                },
            ],
        },
        {
            "arc_replication_candidates": [
                {"task_path": "data/training/arc_shape_01.json"},
                {"task_path": "data/training/arc_shape_02.json"},
            ],
        },
    )

    assert report["replication_state"] == "INDEPENDENT_REPLICATION_REQUESTED"
    assert len(report["sandbox_replication_requests"]) == 2
    assert report["sandbox_replication_requests"][0][
        "execution_permission"
    ] == "sandbox_only"
    assert report["duplicate_task_replication_forbidden"] is True


def test_knowledge_replication_ledger_tracks_unique_cross_task_support():
    ledger = KnowledgeReplicationLedger()
    record = ReplicationRecord(
        concept="shape_preservation",
        task_id="task_001",
        task_path="data/training/task_001.json",
        success=True,
        causal_alignment=0.96,
        contradiction_score=0.04,
        confidence=0.94,
        timestamp="2026-05-31T12:00:00",
    )
    assert ledger.add_record(record) is True
    assert ledger.add_record(record) is False
    assert ledger.get_replication_count("shape_preservation") == 1
    assert ledger.get_cross_task_support("shape_preservation") == 0.94
    assert ledger.get_independent_success_rate("shape_preservation") == 1.0
    assert ledger.get_replication_bonus("shape_preservation") == 0.0235


def test_knowledge_replication_ledger_persists_cross_process_records(
    tmp_path,
):
    storage_path = tmp_path / "knowledge_replication_ledger.json"
    first = KnowledgeReplicationLedger(storage_path=storage_path)
    record = ReplicationRecord(
        concept="growth",
        task_id="task_001",
        task_path="data/training/task_001.json",
        success=True,
        causal_alignment=0.96,
        contradiction_score=0.04,
        confidence=0.94,
        timestamp="2026-06-01T12:00:00",
    )

    assert first.add_record(record) is True

    hydrated = KnowledgeReplicationLedger(storage_path=storage_path)
    report = hydrated.concept_report("growth")

    assert report["used_task_count"] == 1
    assert report["used_task_ids"] == ["task_001"]
    assert hydrated.report()["persistent_storage_enabled"] is True
    assert hydrated.report()["hydrated_record_count"] == 1


def test_cognition_layer_hydrates_persisted_replication_evidence(tmp_path):
    storage_path = tmp_path / "knowledge_replication_ledger.json"
    ledger = KnowledgeReplicationLedger(storage_path=storage_path)
    ledger.add_record(ReplicationRecord(
        concept="growth",
        task_id="task_001",
        task_path="data/training/task_001.json",
        success=True,
        causal_alignment=0.96,
        contradiction_score=0.04,
        confidence=0.94,
        timestamp="2026-06-01T12:00:00",
        reliability=0.95,
        semantic_consistency=0.93,
    ))

    layer = EpistemicCognitionLayer(
        knowledge_replication_ledger_path=storage_path
    )
    evidence = layer.evidence_registry.evidence_for("growth")

    assert layer.hydrated_replication_evidence_count == 1
    assert len(evidence) == 1
    assert evidence[0].source == "independent_execution_replication"
    assert evidence[0].metadata["hydrated_from_persistent_ledger"] is True


def test_truth_candidate_requires_eight_independent_tasks_when_reported():
    belief = Belief(
        concept="shape_preservation",
        claim="shape_preservation",
        state=BeliefState.VALIDATED,
        confidence=0.94,
    )
    aggregate = EvidenceAggregate(
        concept="shape_preservation",
        evidence_strength=0.94,
        contradiction_score=0.04,
        causal_alignment=0.95,
    )

    blocked = TruthCandidateEngine().evaluate(
        belief,
        aggregate,
        {
            "knowledge_generalization": {
                "used_task_count": 7,
            },
        },
    )
    eligible = TruthCandidateEngine().evaluate(
        belief,
        aggregate,
        {
            "knowledge_generalization": {
                "used_task_count": 8,
            },
        },
    )

    assert "independent_task_coverage" in blocked["blocked_metrics"]
    assert eligible["eligible_for_truth_candidate"] is True


def test_cross_task_collector_populates_ledger_from_completed_arc_tasks():
    ledger = KnowledgeReplicationLedger()
    registry = EvidenceRegistry()
    collector = CrossTaskReplicationCollector(ledger, registry)
    context = {
        "task_path": "data/training/task_001.json",
        "evaluation_result": {
            "accuracy": 0.96,
            "structural_score": 0.94,
            "final_score": 0.95,
        },
        "epistemic_cognition_report": {
            "evaluations": [{
                "concept": "shape_preservation",
            }],
        },
    }

    first = collector.collect(context)
    second = collector.collect({
        **context,
        "task_path": "data/training/task_002.json",
    })
    duplicate = collector.collect(context)
    report = ledger.concept_report("shape_preservation")

    assert first["accepted_count"] == 1
    assert second["accepted_count"] == 1
    assert duplicate["accepted_count"] == 0
    assert duplicate["rejected_records"][0]["reason"] == (
        "duplicate_task_replication_forbidden"
    )
    assert report["used_task_count"] == 2
    assert report["concept_used_task_count"] == 2
    assert report["used_task_count_scope"] == "concept_specific"
    assert report["used_task_ids"] == [
        "data/training/task_001.json",
        "data/training/task_002.json",
    ]
    assert report["independent_replications"] == 2
    assert report["cross_task_support"] == 0.9508
    assert ledger.report()["observed_task_count"] == 2
    assert ledger.report()["observed_task_ids"] == [
        "data/training/task_001.json",
        "data/training/task_002.json",
    ]
    assert registry.evidence_for("shape_preservation")[0].source == (
        "independent_execution_replication"
    )


def test_cross_task_collector_unwraps_structured_runtime_values():
    ledger = KnowledgeReplicationLedger()
    registry = EvidenceRegistry()
    collector = CrossTaskReplicationCollector(ledger, registry)
    wrapped_task = {
        "value": "data/training/task_003.json",
        "priority": "medium",
        "timestamp": "2026-05-31 12:00:00",
    }
    report = collector.collect({
        "task_path": wrapped_task,
        "evaluation_result": {
            "value": {
                "accuracy": 0.96,
                "structural_score": 0.94,
                "final_score": 0.95,
            },
            "priority": "medium",
        },
        "epistemic_cognition_report": {
            "evaluations": [{"concept": "color_preservation"}],
        },
    })

    record = report["accepted_records"][0]
    assert record["task_id"] == "data/training/task_003.json"
    assert record["task_path"] == "data/training/task_003.json"


def test_knowledge_generalization_rises_only_for_independent_tasks():
    ledger = KnowledgeReplicationLedger()
    engine = KnowledgeGeneralizationEngine(ledger)

    def add(task_id):
        return ledger.add_record(ReplicationRecord(
            concept="color_preservation",
            task_id=task_id,
            task_path=task_id,
            success=True,
            causal_alignment=0.94,
            contradiction_score=0.06,
            confidence=0.92,
            timestamp="2026-05-31T12:00:00",
        ))

    assert add("task_001") is True
    first = engine.evaluate("color_preservation", 0.70)
    assert add("task_002") is True
    second = engine.evaluate("color_preservation", 0.70)
    assert add("task_002") is False
    duplicate = engine.evaluate("color_preservation", 0.70)

    assert second["generalization_score"] > first["generalization_score"]
    assert duplicate["generalization_score"] == second["generalization_score"]
    assert duplicate["independent_replications"] == 2
    assert duplicate["replication_bonus_applied_once"] is True
    assert duplicate["projected_evidence_strength"] == 0.746


def test_evidence_replication_rejects_duplicate_task_and_raises_strength():
    engine = EvidenceReplicationEngine()
    registry = EvidenceRegistry()
    fusion = EpistemicEvidenceFusionEngine(engine.ledger)
    registry.fusion_engine = fusion
    registry.collect({
        "concept": "shape_preservation",
        "source": "execution_validation",
        "support_score": 0.90,
        "contradiction_score": 0.04,
        "reliability": 0.96,
        "causal_alignment": 0.9589,
        "semantic_consistency": 0.92,
    })
    before = registry.aggregate("shape_preservation")
    result = {
        "concept": "shape_preservation",
        "task_path": "data/training/arc_shape_03.json",
        "sandbox_validated": True,
        "isolated_world": True,
        "independent_task": True,
        "accuracy": 0.96,
        "structural_score": 0.94,
        "final_score": 0.95,
    }
    ingestion = engine.ingest_results(result)
    for item in ingestion["epistemic_evidence_exports"]:
        registry.collect(item)
    after = registry.aggregate("shape_preservation")
    duplicate = engine.ingest_results(result)

    assert after.evidence_strength > before.evidence_strength
    assert fusion.report_for("shape_preservation")[
        "independent_replication_coverage_bonus"
    ] == 0.0238
    ledger = engine.ledger.concept_report("shape_preservation")
    assert ledger["used_task_count"] == 1
    assert ledger["independent_replications"] == 1
    assert ledger["independent_success_rate"] == 1.0
    assert duplicate["epistemic_evidence_exports"] == []
    assert duplicate["rejected_results"][0]["reason"] == (
        "duplicate_task_replication_forbidden"
    )


def test_layer_exposes_replication_ingestion_and_pipeline_ready_requests():
    layer = EpistemicCognitionLayer()
    layer.belief_engine.registry.get_or_create(
        "shape_preservation",
        "shape_preservation",
    ).state = BeliefState.VALIDATED
    report = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "shape_preservation",
            "prior_confidence": 0.90,
            "semantic_consistency": 0.94,
            "causal_alignment": 0.96,
        }],
        "epistemic_evidence": [
            {
                "concept": "shape_preservation",
                "source": "execution_validation",
                "support_score": 0.90,
                "contradiction_score": 0.04,
                "reliability": 0.96,
                "causal_alignment": 0.9589,
                "semantic_consistency": 0.92,
            },
        ],
        "arc_replication_results": [{
            "concept": "shape_preservation",
            "task_path": "data/training/arc_shape_04.json",
            "sandbox_validated": True,
            "isolated_world": True,
            "independent_task": True,
            "accuracy": 0.96,
            "structural_score": 0.94,
            "final_score": 0.95,
        }],
    })

    replication = report["evidence_replication_engine"]
    assert replication["result_ingestion"]["accepted_results"][0][
        "task_path"
    ] == "data/training/arc_shape_04.json"
    assert report["epistemic_evidence_fusion_engine"]["evaluations"][0][
        "channels"
    ]["independent_replication"]["evidence_count"] == 1


def test_counterexample_engine_maps_mixed_outcomes_into_concept_boundaries():
    ledger = KnowledgeReplicationLedger()
    ledger.add_record(ReplicationRecord(
        concept="density_preservation",
        task_id="task_001",
        task_path="data/training/task_001.json",
        success=False,
        causal_alignment=0.57,
        contradiction_score=0.41,
        confidence=0.61,
        timestamp="2026-06-01T12:00:00",
        conditions={"grid_density": "sparse"},
        failure_reason="density_fragmentation",
    ))
    ledger.add_record(ReplicationRecord(
        concept="density_preservation",
        task_id="task_002",
        task_path="data/training/task_002.json",
        success=True,
        causal_alignment=0.89,
        contradiction_score=0.10,
        confidence=0.91,
        timestamp="2026-06-01T12:01:00",
        conditions={"grid_density": "compact"},
    ))

    report = CounterexampleEngine(ledger).evaluate(
        "density_preservation"
    )

    assert report["analysis_state"] == (
        "COUNTEREXAMPLE_BOUNDARY_ANALYSIS_REQUIRED"
    )
    assert report["mixed_outcomes_detected"] is True
    assert report["counterexample_store"]["counterexample_count"] == 1
    assert report["holds_when"][0]["condition"] == "causal_alignment_region"
    assert {
        item["metric"]
        for item in report["boundary_conditions"]
    } == {
        "causal_alignment",
        "contradiction_score",
        "confidence",
    }
    assert report["required_actions"][0] == (
        "isolate_counterexample_conditions"
    )


def test_layer_exposes_counterexample_analysis_and_boundary_probe():
    layer = EpistemicCognitionLayer()
    report = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "density_preservation",
        }],
        "arc_replication_results": [
            {
                "concept": "density_preservation",
                "task_path": "data/training/task_001.json",
                "sandbox_validated": True,
                "isolated_world": True,
                "independent_task": True,
                "accuracy": 0.55,
                "structural_score": 0.58,
                "final_score": 0.59,
                "conditions": {"grid_density": "sparse"},
                "failure_reason": "density_fragmentation",
            },
            {
                "concept": "density_preservation",
                "task_path": "data/training/task_002.json",
                "sandbox_validated": True,
                "isolated_world": True,
                "independent_task": True,
                "accuracy": 0.92,
                "structural_score": 0.90,
                "final_score": 0.91,
                "conditions": {"grid_density": "compact"},
            },
        ],
    })

    counterexamples = report["counterexample_engine"]
    evaluation = counterexamples["evaluations"][0]
    advancement = report["truth_advancement_planner"]["evaluations"][0]

    assert counterexamples["phase"] == "6.93"
    assert counterexamples["boundary_refinement_concepts"] == [
        "density_preservation",
    ]
    assert evaluation["concept_boundary"]["boundary_state"] == (
        "MIXED_OUTCOMES_REQUIRE_BOUNDARY_REFINEMENT"
    )
    assert advancement["dominant_bottleneck"] == "concept_boundary"
    assert advancement["experiment_proposal"]["strategy"] == (
        "matched_boundary_replication"
    )


def test_evidence_gap_analyzer_identifies_missing_success_region():
    report = EvidenceGapAnalyzer().evaluate(
        "symbolic_remapping",
        {
            "used_task_count": 1,
        },
        {
            "counterexample_store": {
                "supported_observation_count": 0,
                "counterexample_count": 1,
            },
            "mixed_outcomes_detected": False,
        },
        {
            "metrics": [
                {
                    "metric": "evidence_strength",
                    "gap": 0.2152,
                },
                {
                    "metric": "confidence",
                    "gap": 0.126,
                },
            ],
        },
    )

    assert report["analysis_state"] == (
        "ACTIVE_KNOWLEDGE_ACQUISITION_REQUIRED"
    )
    assert report["required_success_examples"] == 4
    assert report["missing_success_examples"] == 4
    assert report["required_counterexamples"] == 2
    assert report["missing_counterexamples"] == 1
    assert report["remaining_independent_tasks"] == 4
    assert report["missing_regions"][0]["region"] == "supported_region"
    assert report["priority"] == "high"


def test_layer_requests_supported_region_after_single_failed_replication():
    layer = EpistemicCognitionLayer()
    report = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "symbolic_remapping",
        }],
        "arc_replication_results": [{
            "concept": "symbolic_remapping",
            "task_path": "data/training/task_001.json",
            "sandbox_validated": True,
            "isolated_world": True,
            "independent_task": True,
            "accuracy": 0.55,
            "structural_score": 0.58,
            "final_score": 0.59,
            "conditions": {"symbol_mapping": "ambiguous"},
            "failure_reason": "symbol_collision",
        }],
    })

    gap = report["evidence_gap_analyzer"]["evaluations"][0]
    advancement = report["truth_advancement_planner"]["evaluations"][0]
    proposal = advancement["experiment_proposal"]
    acquisition = report["active_knowledge_acquisition_engine"]

    assert report["evidence_gap_analyzer"]["phase"] == "6.94"
    assert gap["observed_success_examples"] == 0
    assert gap["observed_counterexamples"] == 1
    assert gap["missing_regions"][0]["region"] == "supported_region"
    assert advancement["dominant_bottleneck"] == "knowledge_acquisition"
    assert proposal["strategy"] == "discover_supported_region"
    assert proposal["goal"] == "acquire_missing_epistemic_evidence"
    assert proposal["priority"] == "high"
    assert proposal["knowledge_acquisition_phase"] == "6.94"
    assert acquisition["sandbox_execution_requests"][0]["concept"] == (
        "symbolic_remapping"
    )


def test_contradiction_attribution_reduces_survival_context_contradiction():
    aggregate = EvidenceAggregate(
        concept="density_preservation",
        contradiction_score=0.24,
    )
    evidence = [
        Evidence(
            concept="density_preservation",
            source="evolutionary_trait_survival_history",
            contradiction_score=0.48,
        ),
        Evidence(
            concept="density_preservation",
            source="execution_validation",
            contradiction_score=0.04,
        ),
    ]

    report = ContradictionAttributionEngine().evaluate(
        "density_preservation",
        aggregate,
        evidence,
    )

    assert report["raw_contradiction_score"] == 0.26
    assert report["effective_contradiction_score"] == 0.1133
    assert report["dominant_raw_contradiction_source"]["source"] == (
        "evolutionary_trait_survival_history"
    )
    assert report["dominant_effective_contradiction_source"]["source"] == (
        "evolutionary_trait_survival_history"
    )
    survival_attribution = next(
        item
        for item in report["source_attributions"]
        if item["source"] == "evolutionary_trait_survival_history"
    )
    assert survival_attribution["source_weight"] == 0.2
    assert report["survival_context_attenuated"] is True


def test_contradiction_resolution_applies_attribution_before_gating():
    aggregate = EvidenceAggregate(
        concept="shape_preservation",
        evidence_count=17,
        support_score=0.82,
        evidence_strength=0.7328,
        contradiction_score=0.1812,
        semantic_consistency=0.8839,
        causal_alignment=0.6271,
    )
    evidence = [
        Evidence(
            concept="shape_preservation",
            source="evolutionary_trait_observation",
            contradiction_score=0.28,
            reliability=0.70,
        ),
        Evidence(
            concept="shape_preservation",
            source="execution_validation",
            contradiction_score=0.01,
            reliability=0.94,
        ),
    ]
    report = ContradictionResolutionEngine().evaluate(
        "shape_preservation",
        aggregate,
        evidence,
    )
    trial_resolution = TrialResolutionEngine().resolve(aggregate)

    assert trial_resolution["trial_result"] == "INCONCLUSIVE"
    assert trial_resolution["near_resolution_threshold"] is True
    assert report["resolution_state"] == "CONTRADICTION_CLEAR_FOR_TRIAL"
    assert report["trial_resolution_gap"] == 0.0
    assert report["truth_candidate_gap"] == 0.0
    assert report["dominant_contradiction_source"]["source"] == (
        "evolutionary_trait_observation"
    )
    assert report["raw_contradiction_score"] == 0.145
    assert report["effective_contradiction_score"] == 0.055
    assert report["contradiction_attribution"][
        "survival_context_attenuated"
    ] is True
    assert report["automatic_contradiction_attenuation_forbidden"] is True


def test_cognition_layer_exposes_contradiction_attribution_report():
    layer = EpistemicCognitionLayer()

    report = layer.run_cycle({
        "epistemic_hypotheses": [{
            "concept": "density_preservation",
        }],
        "epistemic_evidence": [
            {
                "concept": "density_preservation",
                "source": "evolutionary_trait_survival_history",
                "contradiction_score": 0.48,
                "reliability": 1.0,
            },
            {
                "concept": "density_preservation",
                "source": "execution_validation",
                "contradiction_score": 0.04,
                "reliability": 1.0,
            },
        ],
    })

    attribution = report["contradiction_attribution_engine"]
    assert attribution["phase"] == "6.92"
    assert attribution["survival_context_attenuated_concepts"] == [
        "density_preservation",
    ]
    assert attribution["evaluations"][0][
        "effective_contradiction_score"
    ] < attribution["evaluations"][0]["raw_contradiction_score"]


def test_fragile_semantic_spine_blocks_truth_commit():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "fragile_spine_claim",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("fragile_spine_claim", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
        "identity_stability_report": {
            "identity_stability_state": "fragile_semantic_spine",
        },
    }

    layer.run_cycle(context)
    report = layer.run_cycle(context)
    commit = report["evaluations"][0]["truth_commit"]

    assert report["truth_commitments"] == []
    assert commit["decision"] == "REMAIN_BELIEF"
    assert commit["metadata"]["gates"]["semantic_spine_stable"] is False


def test_identity_safe_truth_integration_reinforces_fragile_semantic_spine():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "identity_reinforcing_claim",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("identity_reinforcing_claim", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
        "identity_continuity": 0.7391,
        "identity_stability_report": {
            "identity_stability_state": "fragile_semantic_spine",
        },
    }

    layer.run_cycle(context)
    report = layer.run_cycle(context)
    integration = report["evaluations"][0][
        "identity_safe_truth_integration"
    ]
    commit = report["evaluations"][0]["truth_commit"]

    assert integration["integration_state"] == (
        "IDENTITY_REINFORCING_TRUTH"
    )
    assert integration["allow_fragile_semantic_spine_integration"] is True
    assert commit["decision"] == "TRUTH_COMMITTED"
    assert commit["metadata"]["gates"]["semantic_spine_stable"] is True


def test_identity_safe_truth_integration_does_not_bypass_strength_gap():
    belief = Belief(
        concept="execution_validation_gap",
        claim="execution_validation_gap",
        state=BeliefState.VALIDATED,
        confidence=0.90,
    )
    aggregate = EvidenceAggregate(
        concept="execution_validation_gap",
        evidence_count=5,
        evidence_strength=0.7777,
        contradiction_score=0.04,
        semantic_consistency=0.818,
        causal_alignment=0.9483,
    )
    candidate = TruthCandidateEngine().evaluate(
        belief,
        aggregate,
    )
    integration = IdentitySafeTruthIntegrationEngine().evaluate(
        belief,
        aggregate,
        candidate,
        {
            "identity_continuity": 0.7391,
            "identity_stability_report": {
                "identity_stability_state": "fragile_semantic_spine",
            },
        },
    )

    assert candidate["eligible_for_truth_candidate"] is False
    assert candidate["dominant_bottleneck"]["metric"] == (
        "evidence_strength"
    )
    assert candidate["required_actions"] == [
        "collect_execution_validation_evidence",
    ]
    assert integration["integration_state"] == "AWAITING_TRUTH_CANDIDATE"
    assert integration["allow_fragile_semantic_spine_integration"] is False


def test_identity_safe_truth_integration_respects_explicit_identity_block():
    belief = Belief(
        concept="identity_blocked_claim",
        claim="identity_blocked_claim",
        state=BeliefState.VALIDATED,
        confidence=0.90,
    )
    aggregate = EvidenceAggregate(
        concept="identity_blocked_claim",
        evidence_count=5,
        evidence_strength=0.90,
        contradiction_score=0.04,
        semantic_consistency=0.90,
        causal_alignment=0.95,
    )
    candidate = TruthCandidateEngine().evaluate(
        belief,
        aggregate,
    )
    integration = IdentitySafeTruthIntegrationEngine().evaluate(
        belief,
        aggregate,
        candidate,
        {
            "identity_continuity": 0.74,
            "identity_stable": False,
            "identity_stability_report": {
                "identity_stability_state": "fragile_semantic_spine",
            },
        },
    )

    assert candidate["eligible_for_truth_candidate"] is True
    assert integration["integration_state"] == "HOLD_FOR_IDENTITY_SAFETY"
    assert integration["allow_fragile_semantic_spine_integration"] is False


def test_adaptive_identity_integration_rewards_existing_truth_support():
    registry = TruthRegistry()
    root = registry.commit_truth(
        concept="visual_invariance",
        claim="visual invariance is reusable",
        evidence_strength=0.92,
        causal_alignment=0.96,
        contradiction_score=0.02,
        confidence=0.94,
        trial_count=5,
    )
    aggregate = EvidenceAggregate(
        concept="color_preservation",
        evidence_strength=0.90,
        semantic_consistency=0.96,
        causal_alignment=0.95,
        contradiction_score=0.04,
    )
    policy = AdaptiveIdentityIntegrationEngine().evaluate(
        "color_preservation",
        aggregate,
        {"eligible_for_truth_candidate": True},
        truth_candidate_count=3,
        context={
            "knowledge_generalization": {
                "generalization_score": 0.94,
            },
            "truth_lineage": {
                "color_preservation": {
                    "parent_truths": [root.truth_id],
                },
            },
        },
        registry=registry,
    )

    assert policy["adaptive_tolerance_enabled"] is True
    assert policy["concept_strengthens_existing_truths"] is True
    assert policy["effective_maximum_semantic_drift"] > 0.58
    assert policy["effective_maximum_semantic_drift"] <= 0.64
    assert policy["effective_minimum_identity_continuity"] < 0.62
    assert policy["identity_resistance_reduction"] > 0.0
    assert policy["identity_integration_reward"] > 0.0


def test_adaptive_identity_integration_does_not_accept_high_drift():
    aggregate = EvidenceAggregate(
        concept="shape_preservation",
        evidence_strength=0.90,
        semantic_consistency=0.96,
        causal_alignment=0.95,
        contradiction_score=0.04,
    )
    policy = AdaptiveIdentityIntegrationEngine().evaluate(
        "shape_preservation",
        aggregate,
        {"eligible_for_truth_candidate": True},
        truth_candidate_count=4,
        context={
            "concept_strengthens_existing_truths": True,
            "knowledge_generalization": {
                "generalization_score": 0.94,
            },
        },
        registry=TruthRegistry(),
    )
    integration = IdentitySafeTruthIntegrationEngine().evaluate(
        Belief(
            concept="shape_preservation",
            claim="shape preservation is reusable",
            state=BeliefState.TRUTH_CANDIDATE,
        ),
        aggregate,
        {"eligible_for_truth_candidate": True},
        {
            "identity_continuity": 0.72,
            "semantic_drift": 0.7696,
            "identity_stability_report": {
                "identity_stability_state": "fragile_semantic_spine",
            },
            "adaptive_identity_integration_policy": policy,
        },
    )

    assert policy["effective_maximum_semantic_drift"] <= 0.64
    assert integration["integration_safe"] is False
    assert integration["checks"]["semantic_drift_below_limit"] is False
    assert "semantic_drift_below_limit" in integration["failed_checks"]


def test_adaptive_identity_integration_commits_bounded_moderate_drift():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "bounded_identity_growth",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("bounded_identity_growth", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
        "identity_continuity": 0.72,
        "semantic_drift": 0.595,
        "identity_stability_report": {
            "identity_stability_state": "fragile_semantic_spine",
        },
    }

    layer.run_cycle(context)
    report = layer.run_cycle(context)
    evaluation = report["evaluations"][0]
    adaptive = evaluation["adaptive_identity_integration"]

    assert adaptive["adaptive_tolerance_enabled"] is True
    assert adaptive["effective_maximum_semantic_drift"] > 0.595
    assert evaluation["identity_safe_truth_integration"][
        "integration_safe"
    ] is True
    assert evaluation["truth_commit"]["decision"] == "TRUTH_COMMITTED"


def test_truth_internalization_plans_identity_governance_recovery():
    belief = Belief(
        concept="shape_preservation",
        claim="shape_preservation",
        state=BeliefState.TRUTH_CANDIDATE,
        confidence=0.9133,
    )
    aggregate = EvidenceAggregate(
        concept="shape_preservation",
        evidence_count=24,
        evidence_strength=0.8765,
        contradiction_score=0.0937,
        semantic_consistency=0.955,
        causal_alignment=0.9589,
    )
    candidate = TruthCandidateEngine().evaluate(
        belief,
        aggregate,
    )
    integration = IdentitySafeTruthIntegrationEngine().evaluate(
        belief,
        aggregate,
        candidate,
        {
            "identity_continuity": 0.6739,
            "semantic_drift": 0.7689,
            "identity_stability_report": {
                "identity_stability_state": "rollback_required",
            },
        },
    )
    internalization = TruthInternalizationEngine().evaluate(
        belief,
        aggregate,
        integration,
    )

    assert candidate["eligible_for_truth_candidate"] is True
    assert integration["integration_state"] == "HOLD_FOR_IDENTITY_SAFETY"
    assert internalization["internalization_state"] == (
        "IDENTITY_GOVERNANCE_REPAIR_REQUIRED"
    )
    assert internalization["required_actions"] == [
        "reduce_semantic_drift",
        "complete_identity_repair_cycle",
        "reanchor_semantic_spine",
        "confirm_identity_recovery_cycles",
        "run_reversible_truth_internalization_rehearsal",
    ]
    rehearsal = internalization["reversible_internalization_rehearsal"]
    assert rehearsal["sandbox_only"] is True
    assert rehearsal["persistent_identity_write_forbidden"] is True
    assert internalization["automatic_truth_commit_forbidden"] is True


def test_truth_internalization_waits_for_epistemic_candidate():
    internalization = TruthInternalizationEngine().evaluate(
        Belief(
            concept="execution_validation_gap",
            claim="execution_validation_gap",
            state=BeliefState.VALIDATED,
        ),
        EvidenceAggregate(
            concept="execution_validation_gap",
            evidence_strength=0.7777,
        ),
        {
            "checks": {
                "truth_candidate_ready": False,
            },
            "integration_safe": False,
            "failed_checks": [
                "truth_candidate_ready",
            ],
        },
    )

    assert internalization["internalization_state"] == (
        "WAITING_FOR_TRUTH_CANDIDATE"
    )
    assert internalization["knowledge_internalization_required"] is False
    assert internalization["reversible_internalization_rehearsal"] is None


def test_identity_repair_rejects_unvalidated_internalization_result():
    report = IdentityRepairEngine().evaluate(
        Belief(
            concept="unsafe_internalization",
            claim="unsafe_internalization",
        ),
        {
            "knowledge_internalization_required": True,
            "required_actions": [
                "reduce_semantic_drift",
            ],
            "reversible_internalization_rehearsal": {
                "concept": "unsafe_internalization",
            },
        },
        {
            "truth_internalization_rehearsal_results": {
                "concept": "unsafe_internalization",
                "sandbox_validated": False,
                "isolated_world": True,
                "reversible": True,
            },
        },
    )

    assert report["repair_state"] == "REVERSIBLE_REHEARSAL_REQUESTED"
    assert report["accepted_rehearsal_result"] is None
    assert report["rejected_unvalidated_result"] is True
    assert report["persistent_identity_write_forbidden"] is True


def test_semantic_spine_recovery_requires_three_safe_rehearsal_cycles():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "recoverable_truth",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("recoverable_truth", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
        "identity_continuity": 0.6558,
        "semantic_drift": 0.7703,
        "identity_stability_report": {
            "identity_stability_state": "fragile_semantic_spine",
        },
    }
    layer.run_cycle(context)
    first = layer.run_cycle(context)
    second = layer.run_cycle(context)
    third = layer.run_cycle(context)

    assert first["evaluations"][0]["semantic_spine_recovery"][
        "recovery_streak"
    ] == 1
    assert second["evaluations"][0]["semantic_spine_recovery"][
        "recovery_streak"
    ] == 2
    recovery = third["evaluations"][0]["semantic_spine_recovery"]
    assert recovery["recovery_state"] == "STABLE_SEMANTIC_SPINE"
    assert recovery["semantic_spine_recovery_confirmed"] is True
    assert recovery["truth_commit_review_unblocked"] is True
    assert recovery["automatic_truth_commit_forbidden"] is True
    assert third["evaluations"][0][
        "identity_safe_truth_integration"
    ]["integration_safe"] is True
    assert third["evaluations"][0]["truth_commit"]["decision"] == (
        "TRUTH_COMMITTED"
    )
    rehearsal = third["evaluations"][0]["reversible_rehearsal_execution"]
    assert rehearsal["execution_state"] == "REVERSIBLE_REHEARSAL_COMPLETED"
    assert rehearsal["result"]["rehearsal_cycle_id"] == (
        "truth_internalization:recoverable_truth:cycle_3"
    )


def test_semantic_spine_recovery_ignores_duplicate_rehearsal_cycle():
    engine = SemanticSpineRecoveryEngine()
    belief = Belief(
        concept="duplicate_rehearsal",
        claim="duplicate_rehearsal",
    )
    integration = {
        "checks": {
            "truth_candidate_ready": True,
        },
    }
    repair = {
        "accepted_rehearsal_result": {
            "rehearsal_cycle_id": "cycle_1",
            "identity_continuity": 0.74,
            "semantic_drift": 0.20,
            "identity_repair_inactive": True,
            "semantic_containment_inactive": True,
            "semantic_spine_state": "semantic_spine_recovering",
        },
    }

    first = engine.evaluate(belief, integration, repair)
    duplicate = engine.evaluate(belief, integration, repair)

    assert first["recovery_streak"] == 1
    assert duplicate["recovery_streak"] == 1
    assert duplicate["duplicate_rehearsal_cycle_ignored"] is True


def safe_rehearsal_result(cycle_id):
    return {
        "rehearsal_cycle_id": cycle_id,
        "identity_continuity": 0.74,
        "semantic_drift": 0.20,
        "identity_repair_inactive": True,
        "semantic_containment_inactive": True,
        "semantic_spine_state": "semantic_spine_recovering",
    }


def test_semantic_spine_recovery_retains_confirmed_state_without_new_rehearsal():
    engine = SemanticSpineRecoveryEngine()
    belief = Belief(
        concept="stable_recovery",
        claim="stable_recovery",
    )
    integration = {
        "checks": {
            "truth_candidate_ready": True,
        },
    }
    for cycle_id in ["cycle_1", "cycle_2", "cycle_3"]:
        confirmed = engine.evaluate(
            belief,
            integration,
            {
                "accepted_rehearsal_result":
                safe_rehearsal_result(cycle_id),
            },
        )

    retained = engine.evaluate(
        belief,
        integration,
        {"accepted_rehearsal_result": None},
    )

    assert confirmed["semantic_spine_recovery_confirmed"] is True
    assert retained["recovery_state"] == "STABLE_SEMANTIC_SPINE"
    assert retained["semantic_spine_recovery_confirmed"] is True
    assert retained["recovery_streak"] == 3
    assert retained["recovery_cycle_passed"] is False
    assert retained["rehearsal_validation_pending"] is False
    assert retained[
        "confirmed_recovery_retained_without_new_rehearsal"
    ] is True


def test_semantic_spine_recovery_resumes_after_process_restart():
    with TemporaryDirectory() as directory:
        storage_path = Path(directory) / "semantic_spine_recovery.json"
        belief = Belief(
            concept="persistent_recovery",
            claim="persistent_recovery",
        )
        integration = {
            "checks": {
                "truth_candidate_ready": True,
            },
        }

        first_engine = SemanticSpineRecoveryEngine(
            storage_path=storage_path
        )
        first = first_engine.evaluate(
            belief,
            integration,
            {
                "accepted_rehearsal_result":
                safe_rehearsal_result("cycle_1"),
            },
        )
        second_engine = SemanticSpineRecoveryEngine(
            storage_path=storage_path
        )
        second = second_engine.evaluate(
            belief,
            integration,
            {
                "accepted_rehearsal_result":
                safe_rehearsal_result("cycle_2"),
            },
        )

        assert first["recovery_streak"] == 1
        assert second["recovery_streak"] == 2


def test_semantic_spine_recovery_preserves_streak_while_candidate_is_absent():
    engine = SemanticSpineRecoveryEngine()
    belief = Belief(
        concept="intermittent_candidate",
        claim="intermittent_candidate",
    )
    first = engine.evaluate(
        belief,
        {"checks": {"truth_candidate_ready": True}},
        {
            "accepted_rehearsal_result":
            safe_rehearsal_result("cycle_1"),
        },
    )
    waiting = engine.evaluate(
        belief,
        {"checks": {"truth_candidate_ready": False}},
        {"accepted_rehearsal_result": None},
    )

    assert first["recovery_streak"] == 1
    assert waiting["recovery_streak"] == 1
    assert waiting["recovery_state"] == "WAITING_FOR_TRUTH_CANDIDATE"
    assert waiting["identity_continuity"] == first["identity_continuity"]
    assert waiting["semantic_drift"] == first["semantic_drift"]


def test_semantic_spine_recovery_reports_rehearsal_validation_bottleneck():
    recovery = SemanticSpineRecoveryEngine().evaluate(
        Belief(
            concept="pending_rehearsal",
            claim="pending_rehearsal",
        ),
        {"checks": {"truth_candidate_ready": True}},
        {"accepted_rehearsal_result": None},
    )

    assert recovery["recovery_state"] == "REHEARSAL_VALIDATION_REQUIRED"
    assert recovery["rehearsal_validation_pending"] is True
    assert recovery["recovery_blocker_type"] == (
        "VALIDATED_REVERSIBLE_REHEARSAL_PENDING"
    )
    assert recovery["failed_checks"] == [
        "validated_reversible_rehearsal",
        "identity_continuity_preserved",
        "semantic_drift_below_limit",
        "identity_repair_inactive",
        "semantic_containment_inactive",
        "semantic_spine_recovering",
    ]


def test_reversible_rehearsal_executor_resumes_cycle_ids_after_restart():
    with TemporaryDirectory() as directory:
        storage_path = Path(directory) / "rehearsal_state.json"
        rehearsal = {
            "concept": "persistent_rehearsal",
            "baseline_identity_continuity": 0.6558,
            "baseline_semantic_drift": 0.7703,
            "sandbox_only": True,
            "reversible": True,
            "persistent_identity_write_forbidden": True,
        }

        first = ReversibleRehearsalExecutor(
            storage_path=storage_path
        ).execute(rehearsal)
        second = ReversibleRehearsalExecutor(
            storage_path=storage_path
        ).execute(rehearsal)

        assert first["result"]["rehearsal_cycle_id"].endswith("cycle_1")
        assert second["result"]["rehearsal_cycle_id"].endswith("cycle_2")
        assert second["result"]["identity_continuity"] > (
            first["result"]["identity_continuity"]
        )
        assert second["result"]["semantic_drift"] < (
            first["result"]["semantic_drift"]
        )


def test_reversible_rehearsal_executor_controls_semantic_drift():
    executor = ReversibleRehearsalExecutor(
        SemanticDriftController()
    )
    report = executor.execute({
        "concept": "shape_preservation",
        "baseline_identity_continuity": 0.6558,
        "baseline_semantic_drift": 0.7703,
        "sandbox_only": True,
        "reversible": True,
        "persistent_identity_write_forbidden": True,
    })

    result = report["result"]
    control = result["semantic_drift_control"]
    assert report["execution_state"] == "REVERSIBLE_REHEARSAL_COMPLETED"
    assert result["rehearsal_cycle_id"] == (
        "truth_internalization:shape_preservation:cycle_1"
    )
    assert result["semantic_drift"] < 0.58
    assert result["identity_continuity"] > 0.6558
    assert [
        item["action"]
        for item in control["interventions"]
    ] == [
        "reanchor_semantic_spine",
        "remove_contradictory_identity_edges",
        "compress_non_core_memory",
        "reinforce_causal_anchors",
    ]
    assert result["persistent_identity_write_forbidden"] is True


def test_truth_registry_records_lineage_and_supports_retrieval():
    registry = TruthRegistry()
    first = registry.commit_truth(
        concept="shape_preservation",
        claim="shape preservation is reusable",
        evidence_strength=0.91,
        causal_alignment=0.96,
        contradiction_score=0.04,
        confidence=0.93,
        trial_count=5,
        parent_truths=["truth:geometry"],
        evidence_sources=[
            "execution_validation",
            "semantic_anchor_graph",
        ],
        evidence=[{
            "source": "execution_validation",
            "causal_alignment": 0.96,
        }],
        causal_history=[{
            "source": "execution_validation",
            "causal_alignment": 0.96,
        }],
        generalization_score=0.88,
        identity_impact={
            "integration_safe": True,
            "strengthens_identity": True,
        },
    )
    registry.commit_truth(
        concept="shape_rotation_preservation",
        claim="shape rotation preserves topology",
        evidence_strength=0.88,
        causal_alignment=0.94,
        contradiction_score=0.05,
        confidence=0.90,
        trial_count=4,
        parent_truths=[first.truth_id],
        evidence_sources=["execution_validation"],
    )
    retrieval = TruthRetrievalEngine(registry)

    stored = retrieval.retrieve_truth("shape_preservation")
    assert stored["truth_id"] == first.truth_id
    assert stored["parent_truths"] == ["truth:geometry"]
    assert stored["evidence_sources"] == [
        "execution_validation",
        "semantic_anchor_graph",
    ]
    assert stored["lineage"]["parent_truths"] == ["truth:geometry"]
    assert stored["evidence"][0]["source"] == "execution_validation"
    assert stored["causal_history"][0]["causal_alignment"] == 0.96
    assert stored["generalization_score"] == 0.88
    assert stored["identity_impact"]["strengthens_identity"] is True
    assert stored["commit_timestamp"]
    assert stored["verification_history"][0]["decision"] == (
        "TRUTH_COMMITTED"
    )
    related = retrieval.find_related_truths("shape")
    assert [item["concept"] for item in related] == [
        "shape_preservation",
        "shape_rotation_preservation",
    ]
    ranked = retrieval.rank_truths_by_confidence()
    assert ranked[0]["concept"] == "shape_preservation"


def test_truth_registry_persists_hydrates_lineage_and_reinforcement():
    with TemporaryDirectory() as directory:
        storage_path = f"{directory}/truth_registry.json"
        registry = TruthRegistry(storage_path=storage_path)
        root = registry.commit_truth(
            concept="visual_invariance",
            claim="visual invariance is reusable",
            evidence_strength=0.91,
            causal_alignment=0.96,
            contradiction_score=0.03,
            confidence=0.93,
            trial_count=5,
        )
        child = registry.commit_truth(
            concept="color_preservation",
            claim="color preservation reinforces visual invariance",
            evidence_strength=0.88,
            causal_alignment=0.95,
            contradiction_score=0.04,
            confidence=0.90,
            trial_count=4,
            parent_truths=[root.truth_id],
        )

        hydrated = TruthRegistry(storage_path=storage_path)
        retrieval = TruthRetrievalEngine(hydrated)
        lineage = retrieval.retrieve_truth_lineage(
            "color_preservation"
        )
        reinforcement = TruthReinforcementEngine(hydrated)
        reinforced = reinforcement.reinforce_truth(
            "color_preservation",
            confidence=0.94,
            generalization_score=0.91,
            reasons=["cross_task_replication_confirmed"],
        )
        reloaded = TruthRegistry(storage_path=storage_path)
        stored = reloaded.retrieve_truth("color_preservation")

        assert hydrated.hydrated_truth_count == 2
        assert lineage["truth_id"] == child.truth_id
        assert lineage["ancestors"] == [root.truth_id]
        assert reinforced["revision"] == 2
        assert stored["calibrated_confidence"] == 0.94
        assert stored["generalization_score"] == 0.91
        assert stored["verification_history"][-1]["decision"] == (
            "TRUTH_REINFORCED"
        )
        assert reloaded.report()["persistent_storage_enabled"] is True


def test_provisional_truth_record_has_structured_defaults():
    record = ProvisionalTruthRecord.create("shape_preservation")

    assert record.truth_id.startswith("truth:")
    assert record.concept == "shape_preservation"
    assert record.truth_state == "PROVISIONAL_TRUTH_COMMITMENT"
    assert record.contradiction_score == 1.0
    assert record.semantic_drift == 1.0
    assert record.source_tasks == []
    assert record.evidence_sources == []
    assert record.lineage == {}
    assert record.revision_count == 0


def test_provisional_truth_registry_persists_across_restart():
    with TemporaryDirectory() as directory:
        storage_path = f"{directory}/provisional_truth_registry.json"
        registry = ProvisionalTruthRegistry(storage_path=storage_path)
        first = registry.upsert(
            concept="shape_preservation",
            confidence=0.93,
            evidence_strength=0.91,
            causal_alignment=0.96,
            contradiction_score=0.03,
            semantic_consistency=0.95,
            source_tasks=["data/training/task_001.json"],
            evidence_sources=["execution_validation"],
        )
        hydrated = ProvisionalTruthRegistry(storage_path=storage_path)
        stored = hydrated.retrieve_truth("shape_preservation")

        assert hydrated.hydrated_truth_count == 1
        assert stored["truth_id"] == first.truth_id
        assert stored["truth_state"] == "PROVISIONAL_TRUTH_COMMITMENT"
        assert stored["source_tasks"] == [
            "data/training/task_001.json",
        ]


def test_provisional_truth_commit_requires_candidate_identity_and_schema():
    engine = ProvisionalTruthCommitEngine()
    aggregate = EvidenceAggregate(
        concept="shape_preservation",
        evidence_strength=0.91,
        causal_alignment=0.96,
        contradiction_score=0.03,
        semantic_consistency=0.95,
    )
    accepted = engine.evaluate(
        "shape_preservation",
        aggregate,
        {"eligible_for_truth_candidate": True},
        {
            "integration_safe": True,
            "identity_continuity": 0.74,
            "semantic_drift": 0.22,
        },
        {
            "confidence": 0.93,
            "truth_commit_evidence": [{
                "source": "execution_validation",
            }],
            "knowledge_generalization": {
                "generalization_score": 0.90,
                "records": [{
                    "task_path": "data/training/task_001.json",
                }],
            },
        },
    )
    blocked = engine.evaluate(
        "color_preservation",
        aggregate,
        {"eligible_for_truth_candidate": True},
        {"integration_safe": False},
    )

    assert accepted["decision"] == "PROVISIONAL_TRUTH_COMMITMENT"
    assert accepted["truth_record"]["concept"] == "shape_preservation"
    assert accepted["truth_record"]["evidence_sources"] == [
        "execution_validation",
    ]
    assert blocked["decision"] == "REMAIN_TRUTH_CANDIDATE"
    assert blocked["failed_gates"] == ["identity_safe"]
    assert engine.registry.retrieve_truth("color_preservation") is None


def test_memory_compression_retains_hydrated_registry_truths():
    registry = TruthRegistry()
    registry.commit_truth(
        concept="shape_preservation",
        claim="shape preservation is reusable",
        evidence_strength=0.91,
        causal_alignment=0.96,
        contradiction_score=0.03,
        confidence=0.93,
        trial_count=5,
    )
    report = MemoryCompressionLayer().run_cycle({
        "truth_registry_report": registry.report(),
    })
    truths = report["epistemic_memory"]["truth_commitments"]

    assert truths["original_count"] == 1
    assert truths["retained_count"] == 1
    assert truths["compressed_items"][0]["concept"] == (
        "shape_preservation"
    )


def test_concept_schema_validator_normalizes_strings_and_rejects_invalid():
    report = ConceptSchemaValidator().normalize_items(
        [
            "shape_preservation",
            {"semantic_concept": "color_preservation"},
            17,
        ],
        record_type="semantic_abstraction",
    )

    assert report["accepted_count"] == 2
    assert report["coerced_string_count"] == 1
    assert report["rejected_count"] == 1
    assert report["normalized_items"][0]["concept"] == (
        "shape_preservation"
    )
    assert report["normalized_items"][1]["concept"] == (
        "color_preservation"
    )


def test_truth_registry_rejects_empty_concept_identifier():
    registry = TruthRegistry()
    try:
        registry.commit_truth(
            concept="",
            claim="invalid truth",
            evidence_strength=0.91,
            causal_alignment=0.96,
            contradiction_score=0.03,
            confidence=0.93,
            trial_count=5,
        )
    except ValueError as error:
        assert str(error) == "concept_identifier_required"
    else:
        raise AssertionError("invalid truth concept was accepted")


def test_truth_commitment_layer_writes_registry_after_recovery():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "registered_truth",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("registered_truth", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
        "identity_continuity": 0.6558,
        "semantic_drift": 0.7703,
        "identity_stability_report": {
            "identity_stability_state": "fragile_semantic_spine",
        },
        "truth_lineage": {
            "registered_truth": {
                "parent_truths": ["truth:root"],
            },
        },
    }

    for _ in range(4):
        report = layer.run_cycle(context)

    stored = layer.truth_commit_engine.retrieve_truth("registered_truth")
    assert report["evaluations"][0]["truth_commit"]["decision"] == (
        "TRUTH_COMMITTED"
    )
    assert stored["parent_truths"] == ["truth:root"]
    assert stored["evidence_sources"] == [
        "causal_observation",
        "mutation_rehearsal",
        "semantic_anchor_graph",
    ]
    assert stored["truth_id"].startswith("truth:")
    assert stored["lineage"]["parent_truths"] == ["truth:root"]
    assert len(stored["evidence"]) == 3
    assert stored["causal_history"][-1]["source"] == (
        "truth_commit_aggregate"
    )
    assert stored["generalization_score"] == 0.0
    assert stored["identity_impact"]["integration_safe"] is True
    assert stored["commit_timestamp"]
    assert report["truth_registry"]["active_truth_count"] == 1
    assert report["truth_retrieval_engine"]["retrieval_enabled"] is True


def test_active_cognitive_spine_repair_blocks_truth_commit():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "repairing_spine_claim",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("repairing_spine_claim", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
        "cognitive_spine_stabilizer_report": {
            "cognitive_spine_state": "cognitive_spine_repairing",
        },
    }

    layer.run_cycle(context)
    report = layer.run_cycle(context)
    commit = report["evaluations"][0]["truth_commit"]

    assert report["truth_commitments"] == []
    assert commit["metadata"]["gates"]["semantic_spine_stable"] is False


def test_semantic_spine_recovery_monitoring_blocks_truth_commit():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "recovering_spine_claim",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("recovering_spine_claim", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
        "semantic_spine_report": {
            "semantic_spine_state": "semantic_spine_recovering",
        },
    }

    layer.run_cycle(context)
    report = layer.run_cycle(context)
    commit = report["evaluations"][0]["truth_commit"]
    integration = report["evaluations"][0][
        "identity_safe_truth_integration"
    ]

    assert report["truth_commitments"] == []
    assert commit["metadata"]["gates"]["semantic_spine_stable"] is False
    assert integration["checks"]["semantic_spine_stable"] is False
    assert "semantic_spine_stable" in integration["failed_checks"]
    assert commit["metadata"]["identity_governance"] == (
        integration["identity_governance"]
    )


def test_execution_validation_evidence_opens_trait_trial_gate():
    report = EpistemicPromotionEngine().run_cycle({
        "task_path": "training/execution_validation_case.json",
        "evaluation_result": {
            "accuracy": 0.99,
            "structural_score": 0.98,
            "final_score": 0.99,
        },
        "semantic_abstractions": [{
            "semantic_concept": "execution_validated_pattern",
            "confidence": 0.98,
            "semantic_consistency": True,
        }],
        "evolutionary_memory_report": {
            "adaptive_trait_memory": {
                "traits": [{
                    "id": "execution_validated_pattern",
                    "trait_state": "decaying",
                    "fitness": 0.32,
                    "semantic_alignment": 0.62,
                    "stability_score": 0.66,
                    "survival_history": [{
                        "constructive_score": 0.60,
                        "identity_continuity": 0.65,
                    }],
                }],
            },
        },
    })

    promotion = report["promotions"][0]
    trial = promotion["epistemic_trial"]

    assert trial["execution_validation_count"] == 1
    assert trial["trial"]["trial_result"] == "PASSED"
    assert promotion["promotion_state"] == "EVIDENCE_SUPPORTED_BELIEF"


def test_truth_gate_remediation_reports_actions_without_bypass():
    plan = TruthGateRemediationEngine().build_plan({
        "minimum_trials": False,
        "semantic_spine_stable": False,
        "minimum_evidence": True,
    })

    assert plan["blocked_gates"] == [
        "minimum_trials",
        "semantic_spine_stable",
    ]
    assert plan["required_actions"] == [
        "run_additional_epistemic_trials",
        "stabilize_cognitive_spine",
    ]
    assert plan["automatic_bypass_forbidden"] is True
