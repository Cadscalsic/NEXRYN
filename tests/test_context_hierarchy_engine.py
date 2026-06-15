from core.belief_engine import EpistemicCognitionLayer
from core.context_hierarchy import (
    ContextDifferentiationEngine,
    ContextHierarchy,
    context_inheritance,
    detect_context_conflicts,
)
from core.epistemic_models import (
    Belief,
    BeliefState,
    EpistemicTrial,
    EvidenceAggregate,
    TrialResult,
)
from core.truth_commit_engine import TruthCommitEngine


def context(name, **features):
    return {
        "transformation_family": name,
        "context_signature": {
            "transformation_family": name,
            "confidence": features.pop("confidence", 0.95),
            **features,
        },
        "confidence": 0.95,
    }


def strong_evidence(concept, source):
    return {
        "concept": concept,
        "source": source,
        "support_score": 1.0,
        "contradiction_score": 0.0,
        "reliability": 1.0,
        "semantic_consistency": 1.0,
        "causal_alignment": 1.0,
    }


def passing_trials():
    return [
        EpistemicTrial(
            concept="duplication_rule",
            support_score=1.0,
            contradiction_score=0.0,
            evidence_strength=1.0,
            semantic_consistency=1.0,
            causal_alignment=1.0,
            trial_result=TrialResult.PASSED,
            evidence_count=3,
            trial_number=number,
        )
        for number in [1, 2]
    ]


def test_context_hierarchy_links_specializations_to_general_families():
    hierarchy = ContextHierarchy()

    duplication = hierarchy.add_context(context("duplication"))
    translation = hierarchy.add_context(context("translation"))
    recoloring = hierarchy.add_context(context("recoloring"))
    identity = hierarchy.add_context(context("identity_preservation"))

    assert duplication.parent_context == "structural_transformation"
    assert translation.parent_context == "geometric_transformation"
    assert recoloring.parent_context == "color_transformation"
    assert identity.parent_context == "structural_transformation"


def test_context_distance_differentiates_near_and_far_contexts():
    engine = ContextDifferentiationEngine()

    assert engine.compute_context_distance("translation", "reflection") <= 0.30
    assert engine.compute_context_distance("translation", "recoloring") >= 0.90
    assert engine.compute_context_distance("duplication", "propagation") == 0.40
    assert engine.compute_context_distance("duplication", "rotation") >= 0.90


def test_context_inheritance_exposes_parent_features():
    inheritance = context_inheritance(context("duplication"))

    assert inheritance["parent_context"] == "structural_transformation"
    assert "topology_change" in inheritance["inherited_features"]
    assert inheritance["inheritance_integrity"] == 1.0


def test_identity_preservation_context_inherits_structural_hierarchy():
    layer = EpistemicCognitionLayer()
    discovery = layer.context_discovery_engine.discover_context({
        "task_id": "task_identity_preservation",
        "concept": "object_identity_preservation",
        "input_grid": [[1]],
        "output_grid": [[1]],
    })

    report = layer.context_differentiation_engine.refine_clusters([
        discovery,
    ])
    inheritance = report["inheritance"][0]

    assert discovery["transformation_family"] == "identity_preservation"
    assert inheritance["parent_context"] == "structural_transformation"
    assert "object_identity_preservation" in (
        inheritance["process_dependency_contexts"]
    )
    assert "structural_identity_preserved" in (
        inheritance["inherited_features"]
    )
    assert report["context_hierarchy_score"] >= 0.75
    assert report["hierarchy_ready"] is True


def test_process_contexts_inherit_process_native_hierarchies():
    layer = EpistemicCognitionLayer()

    expected = {
        "growth": ("growth_context", "topology_expansion"),
        "propagation": ("propagation_context", "directional_spread"),
        "replication": ("replication_context", "structural_copying"),
        "topological_growth": (
            "topological_growth_context",
            "topology_splitting",
        ),
        "directional_motion": (
            "directional_motion_context",
            "directional_displacement",
        ),
    }

    for concept, (parent, inherited_feature) in expected.items():
        discovery = layer.context_discovery_engine.discover_context({
            "task_id": f"task_{concept}",
            "concept": concept,
            "active_concepts": [concept],
        })
        report = layer.context_differentiation_engine.refine_clusters([
            discovery,
        ])
        inheritance = report["inheritance"][0]

        assert discovery["cluster"] in {
            "Growth Context",
            "Propagation Context",
            "Replication Context",
            "Topological Growth Context",
            "Directional Motion Context",
        }
        assert inheritance["context"] == parent
        assert inheritance["parent_context"] is None
        assert inheritance["process_dependency_contexts"]
        assert inherited_feature in inheritance["inherited_features"]
        assert report["context_hierarchy_score"] >= 0.75
        assert report["hierarchy_ready"] is True


def test_context_conflict_detection_separates_hybrid_contexts():
    conflict = detect_context_conflicts([
        context("translation"),
        context("rotation"),
    ])
    hybrid = detect_context_conflicts([
        context("translation", active_concepts=["hybrid_motion"]),
        context("rotation", active_concepts=["hybrid_motion"]),
    ])

    assert conflict["conflict_state"] == "CONTEXT_CONFLICT"
    assert hybrid["conflict_state"] == "CONTEXT_COMPATIBLE"


def test_runtime_report_exposes_context_hierarchy_section():
    layer = EpistemicCognitionLayer()
    report = layer.run_cycle({
        "task_id": "task_duplication",
        "active_concepts": ["duplication"],
        "epistemic_hypotheses": [{
            "concept": "duplication_rule",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("duplication_rule", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
    })

    hierarchy = report["context_hierarchy_engine"]["evaluations"][0]
    candidate = report["evaluations"][0]["truth_candidate"]

    assert hierarchy["context_hierarchy_score"] >= 0.75
    assert hierarchy["inheritance"][0]["parent_context"] == (
        "structural_transformation"
    )
    assert candidate["context_hierarchy"]["hierarchy_ready"] is True


def test_truth_commit_requires_context_hierarchy_score_when_reported():
    engine = TruthCommitEngine()
    belief = Belief(
        concept="duplication_rule",
        claim="duplication_rule is stable",
        state=BeliefState.TRUTH_CANDIDATE,
        confidence=0.95,
    )
    aggregate = EvidenceAggregate(
        concept="duplication_rule",
        evidence_count=3,
        evidence_strength=0.95,
        contradiction_score=0.0,
        semantic_consistency=1.0,
        causal_alignment=1.0,
    )

    commit = engine.evaluate(
        belief,
        aggregate,
        passing_trials(),
        {
            "identity_continuity": 1.0,
            "semantic_drift": 0.0,
            "identity_safe_truth_integration": {
                "integration_safe": True,
                "semantic_containment": {
                    "integration_allowed": True,
                },
                "epistemic_drift_containment": {
                    "integration_allowed": True,
                },
            },
            "causal_spine_alignment": {
                "alignment_ready": True,
                "compatible_with_core_truths": True,
            },
            "causal_graph_validation": {
                "validation_ready": True,
            },
            "causal_graph_alignment": {
                "alignment_ready": True,
            },
            "causal_validation": {
                "validation_score": 1.0,
                "validation_ready": True,
            },
            "contextual_truth": {
                "contextual_truth_score": 1.0,
                "contextual_consistency": True,
            },
            "context_hierarchy": {
                "context_hierarchy_score": 0.61,
                "hierarchy_ready": False,
            },
        },
    )

    assert commit.decision == "REMAIN_BELIEF"
    assert "context_hierarchy_score" in commit.reasons
