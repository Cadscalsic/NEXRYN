from core.concept_lifecycle.lifecycle_manager import (
    ConceptLifecycleManager,
)
from core.concept_lifecycle.concept_maturity import (
    ConceptMaturityTracker,
)


def maturity_concept(concept, count, successes=None):
    successes = (
        [True] * count
        if successes is None
        else successes
    )
    return {
        "concept": concept,
        "used_task_count": count,
        "used_task_ids": [
            f"data/training/task_{index:03d}.json"
            for index in range(1, count + 1)
        ],
        "independent_success_rate": (
            sum(successes) / len(successes)
            if successes
            else 0.0
        ),
        "cross_task_support": 0.92,
        "records": [
            {
                "success": success,
            }
            for success in successes
        ],
    }


def test_concept_maturity_tracks_discovery_support_and_generalization():
    report = ConceptMaturityTracker().evaluate({
        "concepts": [
            maturity_concept("replication", 1),
            maturity_concept("density_preservation", 3),
            maturity_concept("growth", 5),
        ],
    })
    states = {
        item["concept"]: item["state"]
        for item in report["concepts"]
    }

    assert states == {
        "replication": "DISCOVERING",
        "density_preservation": "SUPPORTED",
        "growth": "GENERALIZING",
    }
    assert report["count_alone_cannot_promote_truth"] is True


def test_concept_maturity_requires_boundary_refinement_for_mixed_outcomes():
    report = ConceptMaturityTracker().evaluate({
        "concepts": [
            maturity_concept(
                "symbolic_remapping",
                5,
                [True, True, True, True, False],
            ),
        ],
    })

    assert report["concepts"][0]["state"] == "BOUNDARY_REFINEMENT"


def test_concept_maturity_uses_truth_gates_for_candidate_and_stable_truth():
    report = ConceptMaturityTracker().evaluate(
        {
            "concepts": [
                maturity_concept("growth", 5),
                maturity_concept("propagation", 5),
            ],
        },
        {
            "evaluations": [{
                "concept": "growth",
                "eligible_for_truth_candidate": True,
            }],
        },
        {
            "truths": [{
                "concept": "propagation",
            }],
        },
    )
    states = {
        item["concept"]: item["state"]
        for item in report["concepts"]
    }

    assert states["growth"] == "TRUTH_CANDIDATE"
    assert states["propagation"] == "STABLE_TRUTH"


def test_concept_maturity_does_not_treat_revoked_truth_as_stable():
    report = ConceptMaturityTracker().evaluate(
        {
            "concepts": [
                maturity_concept("revoked_propagation", 5),
            ],
        },
        truth_registry={
            "truths": [{
                "concept": "revoked_propagation",
                "status": "REVOKED",
                "reusable": False,
            }],
        },
    )

    assert report["concepts"][0]["state"] == "GENERALIZING"


def test_concept_lifecycle_tracks_birth_validation_decay_and_revival():

    manager = ConceptLifecycleManager()

    generated = [
        {
            "concept": f"generated_concept_{index}",
            "origin": "conceptive_neurogenesis",
            "viability": 0.50,
            "status": "sandbox_candidate",
        }
        for index in range(24)
    ]

    context = {
        "conceptive_neurogenesis_report": {
            "generated_concepts": generated,
        },
        "novelty_promotion_gate_report": {
            "evaluations": [
                {
                    "concept": "generated_concept_0",
                    "decision": "promote",
                },
                {
                    "concept": "generated_concept_1",
                    "decision": "reject",
                },
            ],
        },
    }

    report = manager.run_cycle(
        context
    )

    assert report["concept_birth"]["birth_count"] == 24

    assert report["concept_validation"]["validated_count"] == 1

    assert report["concept_validation"]["rejected_count"] == 1

    assert report["concept_validation"]["latent_count"] == 22

    assert report["registry"]["registry_size"] == 24

    concept_id = "concept:generated_concept_2"

    manager.concept_registry[
        concept_id
    ][
        "activation"
    ] = 0.05

    manager.concept_registry[
        concept_id
    ][
        "state"
    ] = "decaying"

    report = manager.run_cycle({
        "conceptive_neurogenesis_report": {
            "generated_concepts": [],
        },
        "active_concept_decay_report": {
            "activation_state": [
                {
                    "concept": "generated_concept_2",
                    "activation_strength": 0.8,
                },
            ],
        },
    })

    assert (
        report["concept_revival"]["revived_count"]
        >=
        1
    )


def test_semantic_gc_constructively_forgets_dead_bridges():

    manager = ConceptLifecycleManager()

    manager.concept_registry = {
        "concept:dead_bridge": {
            "concept": "dead_bridge_failed_overlap",
            "state": "retired",
            "activation": 0.02,
            "viability": 0.04,
            "lineage": [
                "concept:missing_parent",
            ],
        },
        "concept:useful_identity": {
            "concept": "identity",
            "state": "validated",
            "activation": 0.90,
            "viability": 0.90,
        },
    }

    report = manager.run_cycle({
        "conceptive_neurogenesis_report": {
            "generated_concepts": [],
        },
    })

    assert report["concept_energy_economics"]["evaluated_count"] == 2

    assert report["semantic_gc"]["collected_count"] == 1

    assert (
        report["semantic_gc"]["collected_concepts"][0]["reason"]
        ==
        "dead_concept"
    )

    assert "concept:dead_bridge" not in manager.concept_registry

    assert "concept:useful_identity" in manager.concept_registry


def test_bridge_hallucinations_are_quarantined_before_birth():

    manager = ConceptLifecycleManager()

    context = {
        "conceptive_neurogenesis_report": {
            "generated_concepts": [
                {
                    "concept": (
                        "bridge_object_identity_preservation_"
                        "topological_growth"
                    ),
                    "viability": 0.62,
                },
                {
                    "concept": "bridge_replication_topological_growth",
                    "viability": 0.58,
                },
                {
                    "concept": (
                        "bridge_object_identity_preservation_"
                        "propagation"
                    ),
                    "viability": 0.59,
                },
                {
                    "concept": "causal_color_mapping",
                    "viability": 0.66,
                },
            ],
        },
        "cognitive_immune_system_report": {
            "latent_conflict_count": 56,
            "repair_required_count": 118,
        },
    }

    report = manager.run_cycle(
        context
    )

    hallucination_filter = report[
        "bridge_hallucination_filter"
    ]

    assert hallucination_filter["quarantined_count"] == 3

    assert report["concept_birth"]["birth_count"] == 1

    assert (
        report["concept_validation"]["validated_concepts"][0][
            "concept"
        ]
        ==
        "causal_color_mapping"
    )

    assert (
        "concept:bridge_object_identity_preservation_topological_growth"
        not in manager.concept_registry
    )


def test_admission_pipeline_blocks_survival_only_commit_under_drift():

    manager = ConceptLifecycleManager()

    context = {
        "runtime_entropy": 0.81,
        "semantic_drift": 0.9194,
        "identity_continuity_engine_report": {
            "identity_state": "identity_fragile",
            "semantic_drift": 0.9194,
        },
        "memory_compression_report": {
            "original_item_count": 169,
            "retained_item_count": 24,
            "compression_ratio": 0.142,
        },
        "sandbox_policy": "deny_commit",
        "mutation_rehearsal_report": {
            "simulation_state": "ambiguous",
        },
        "conceptive_neurogenesis_report": {
            "generated_concepts": [
                {
                    "concept": "causal_structure_refinement",
                    "origin": "conceptive_neurogenesis",
                    "viability": 0.82,
                    "rehearsal_state": "survived_rehearsal",
                },
            ],
        },
        "novelty_promotion_gate_report": {
            "evaluations": [
                {
                    "concept": "causal_structure_refinement",
                    "decision": "promote",
                    "task_count": 3,
                    "average_execution_usefulness": 0.80,
                    "average_identity_continuity": 0.80,
                },
            ],
        },
        "cognitive_reputation": {
            "average_reputation": 0.12,
        },
    }

    report = manager.run_cycle(
        context
    )

    admission = report[
        "concept_admission_pipeline"
    ]

    evaluation = admission[
        "evaluations"
    ][0]

    assert admission["semantic_drift"] == 0.9194

    assert (
        admission["compression"]["overcompression_state"]
        ==
        "semantic_bone_loss_risk"
    )

    assert (
        evaluation["sandboxed_evolution"][
            "requires_rehearsal_before_commit"
        ]
        is True
    )

    assert (
        evaluation["historical_reputation"][
            "survival_is_not_truth"
        ]
        is True
    )

    assert (
        evaluation["controlled_integration"]["decision"]
        ==
        "staged_rehearsal"
    )

    assert report["concept_validation"]["validated_count"] == 0

    assert report["concept_validation"]["latent_count"] == 1


def test_concept_reputation_engine_separates_survival_from_legitimacy():

    manager = ConceptLifecycleManager()

    context = {
        "runtime_entropy": 0.30,
        "semantic_drift": 0.22,
        "conceptive_neurogenesis_report": {
            "generated_concepts": [
                {
                    "concept": "causal_structure_refinement",
                    "origin": "conceptive_neurogenesis",
                    "viability": 0.88,
                    "rehearsal_state": "survived_rehearsal",
                },
            ],
        },
        "novelty_promotion_gate_report": {
            "evaluations": [
                {
                    "concept": "causal_structure_refinement",
                    "decision": "promote",
                    "task_count": 3,
                    "average_execution_usefulness": 0.20,
                    "average_identity_continuity": 0.25,
                },
            ],
        },
        "concept_reputation_events": [
            {
                "concept": "causal_structure_refinement",
                "historical_consistency": 0.18,
                "causal_reliability": 0.16,
                "long_term_usefulness": 0.14,
                "contradiction": True,
                "recovery_success": 0.05,
                "failure_propagation_score": 0.82,
            },
        ],
    }

    report = manager.run_cycle(
        context
    )

    reputation = report[
        "concept_reputation_engine"
    ][
        "concept_reputations"
    ][0]

    admission = report[
        "concept_admission_pipeline"
    ][
        "evaluations"
    ][0]

    assert reputation["reputation_state"] == "weak"

    assert reputation["failure_propagation_score"] == 0.82

    assert (
        admission["historical_reputation"][
            "survival_is_not_truth"
        ]
        is True
    )

    assert report["concept_validation"]["validated_count"] == 0

    assert report["concept_validation"]["latent_count"] == 1

    assert (
        report["concept_validation"]["validated_concepts"][0][
            "admission_decision"
        ]
        ==
        "historical_reputation_required"
    )


def test_concept_reputation_engine_supports_established_concepts():

    manager = ConceptLifecycleManager()

    context = {
        "runtime_entropy": 0.22,
        "semantic_drift": 0.18,
        "conceptive_neurogenesis_report": {
            "generated_concepts": [
                {
                    "concept": "causal_color_mapping",
                    "origin": "conceptive_neurogenesis",
                    "viability": 0.80,
                },
            ],
        },
        "novelty_promotion_gate_report": {
            "evaluations": [
                {
                    "concept": "causal_color_mapping",
                    "decision": "promote",
                    "task_count": 3,
                    "average_execution_usefulness": 0.82,
                    "average_identity_continuity": 0.78,
                },
            ],
        },
        "concept_reputation_events": [
            {
                "concept": "causal_color_mapping",
                "historical_consistency": 0.86,
                "causal_reliability": 0.84,
                "long_term_usefulness": 0.82,
                "contradiction": False,
                "recovery_success": 0.72,
                "failure_propagation_score": 0.08,
            },
        ],
    }

    report = manager.run_cycle(
        context
    )

    reputation = report[
        "concept_reputation_engine"
    ][
        "concept_reputations"
    ][0]

    assert reputation["reputation_state"] == "established"

    assert report["concept_validation"]["validated_count"] == 1

    assert (
        manager.concept_registry[
            "concept:causal_color_mapping"
        ][
            "concept_reputation"
        ][
            "causal_reliability"
        ]
        >=
        0.84
    )
