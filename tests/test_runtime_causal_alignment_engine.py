from core.epistemic_models import (
    Belief,
    BeliefState,
    EvidenceAggregate,
    EpistemicTrial,
    TrialResult,
)
from core.truth_commit_engine import TruthCommitEngine
from runtime.causal.causal_alignment_engine import RuntimeCausalAlignmentEngine
from runtime.truth_candidate_engine import TruthCandidateEngine


def test_runtime_causal_alignment_explains_preservation_transform_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "color_preservation",
        EvidenceAggregate(
            concept="color_preservation",
            contradiction_score=0.1525,
        ),
        {
            "causal_conditions": {
                "color_mode": "transform",
            },
            "causal_boundary_observations": {
                "color_preservation": [
                    {"outcome": "holds", "conditions": {"color_mode": "preserve"}},
                    {"outcome": "breaks", "conditions": {"color_mode": "transform"}},
                ],
            },
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True
    assert report["raw_contradiction_score"] == 0.1525
    assert report["adjusted_contradiction_score"] == 0.06
    assert report["causal_alignment_supported"] is True


def test_truth_candidate_uses_contextual_boundary_before_review_severity():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="color_preservation",
            claim="color_preservation",
            state=BeliefState.VALIDATED,
            confidence=0.91,
        ),
        EvidenceAggregate(
            concept="color_preservation",
            evidence_strength=0.91,
            contradiction_score=0.1525,
            causal_alignment=0.91,
        ),
        {
            "active_concepts": ["symbolic_remapping"],
            "causal_boundary_observations": {
                "color_preservation": [
                    {"outcome": "holds", "conditions": {"color_mode": "preserve"}},
                    {"outcome": "breaks", "conditions": {"color_mode": "transform"}},
                ],
            },
        },
    )

    assert "contradiction_score" not in report["blocked_metrics"]
    assert report["effective_contradiction_score"] == 0.06
    assert report["raw_contradiction_score"] == 0.1525
    assert report["contradiction_review_required"] is False
    assert report["causal_boundary_alignment"][
        "preservation_and_transform_are_contextual_not_absolute"
    ] is True


def test_runtime_causal_alignment_handles_shape_transformation_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "shape_preservation",
        EvidenceAggregate(
            concept="shape_preservation",
            contradiction_score=0.12,
        ),
        {
            "active_concepts": ["shape_transformation"],
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True


def test_runtime_causal_alignment_handles_topology_growth_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "topology_preservation",
        EvidenceAggregate(
            concept="topology_preservation",
            contradiction_score=0.11,
        ),
        {
            "active_concepts": ["grow_topology"],
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True


def test_runtime_causal_alignment_handles_symmetry_reasoning_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "symmetry_preservation",
        EvidenceAggregate(
            concept="symmetry_preservation",
            contradiction_score=0.13,
        ),
        {
            "active_concepts": ["symmetry_reasoning"],
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True


def test_runtime_causal_alignment_handles_attribute_remapping_as_color_transform_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "color_preservation",
        EvidenceAggregate(
            concept="color_preservation",
            contradiction_score=0.14,
        ),
        {
            "active_concepts": ["attribute_remapping"],
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True


def passed_trials(concept):
    return [
        EpistemicTrial(
            concept=concept,
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


def color_context():
    process_memory = {
        "resolved_dependency_chain": [
            "color_preservation",
            "color_behavior",
            "color_mapping_rule",
            "recolor_condition",
        ],
        "dependency_confidence": 0.94,
        "dependency_chain_coverage": 1.0,
        "missing_dependencies": [],
    }
    return {
        "process_dependency_memory": process_memory,
        "dependency_coherence_report": {
            "dependency_coherence": 0.94,
            "stable_dependencies": [
                "color_behavior",
                "color_mapping_rule",
                "no_color_reassignment",
            ],
            "hidden_contradictions": [],
        },
        "semantic_context": {
            "context_name": "color_context",
            "semantically_validated": True,
            "properties": [
                {"property_name": "color_behavior", "confidence": 0.95},
                {
                    "property_name": "color_mapping_rule",
                    "confidence": 0.95,
                },
                {
                    "property_name": "no_color_reassignment",
                    "confidence": 0.95,
                },
                {"property_name": "color_stability", "confidence": 0.95},
                {
                    "property_name": "attribute_mapping_preservation",
                    "confidence": 0.95,
                },
            ],
            "implications": ["color_preservation_expected"],
            "confidence": 0.95,
        },
        "context_hierarchy": {
            "hierarchy_ready": True,
            "context_hierarchy_score": 0.95,
        },
        "contextual_truth": {
            "contextual_truth_supported": True,
            "contextual_truth_score": 0.94,
        },
        "contextual_truth_authority": {
            "contextual_truth_supported": True,
            "contextual_truth_authority": 0.94,
        },
        "causal_graph_alignment": {
            "alignment_score": 0.7871,
            "alignment_ready": False,
            "components": {
                "evidence_consistency": 0.95,
                "cross_task_stability": 1.0,
                "contradiction_resistance": 0.96,
                "dependency_coherence": 0.7681,
            },
            "explanation_path": [
                "color_observation",
                "color_behavior",
            ],
        },
        "causal_validation": {
            "validation_ready": True,
            "validation_score": 0.94,
        },
        "causal_spine_alignment": {
            "alignment_ready": True,
            "compatible_with_core_truths": True,
        },
        "causal_graph_validation": {
            "validation_ready": True,
        },
        "identity_runtime_report": {
            "runtime_ready": True,
            "runtime_state": "IDENTITY_RUNTIME_STABLE",
            "identity_split": False,
            "identity_merged": False,
            "identity_runtime_continuity": 0.86,
        },
        "identity_continuity": 0.86,
        "identity_safe_truth_integration": {
            "integration_safe": True,
            "semantic_containment": {"integration_allowed": True},
            "epistemic_drift_containment": {"integration_allowed": True},
        },
    }


def test_runtime_causal_alignment_builds_explicit_path_above_threshold():
    context = color_context()
    report = RuntimeCausalAlignmentEngine().build_explicit_causal_alignment(
        "color_preservation",
        context["process_dependency_memory"],
        context,
    )

    assert report["concept"] == "color_preservation"
    assert report["causal_alignment"] > 0.82
    assert report["causal_reliability"] > 0.82
    assert report["causal_path"] == [
        "color_observation",
        "color_behavior",
        "color_mapping_rule",
        "no_color_reassignment",
        "color_preservation",
    ]
    assert report["causal_gaps"] == []
    assert report["alignment_ready"] is True
    assert report["dependency_coherence"] > 0.90


def test_runtime_causal_alignment_reports_gaps_and_weak_links():
    context = color_context()
    context["semantic_context"] = {"properties": []}
    context["dependency_coherence_report"] = {"dependency_coherence": 0.42}
    context["process_dependency_memory"] = {
        "resolved_dependency_chain": ["color_preservation"],
        "dependency_confidence": 0.40,
        "dependency_chain_coverage": 0.25,
    }

    report = RuntimeCausalAlignmentEngine().build_explicit_causal_alignment(
        "color_preservation",
        context["process_dependency_memory"],
        context,
    )

    assert report["alignment_ready"] is False
    assert report["causal_gaps"]
    assert report["unexplained_nodes"]
    assert report["causal_alignment"] < 0.82


def test_truth_commit_uses_causal_explainability_without_forcing_commit():
    engine = TruthCommitEngine()
    engine.truth_registry["color_preservation"] = {
        "concept": "color_preservation",
        "status": "ACTIVE",
        "reusable": True,
    }
    belief = Belief(
        concept="color_preservation",
        claim="color_preservation is stable",
        state=BeliefState.TRUTH_COMMITTED,
        confidence=0.95,
    )
    aggregate = EvidenceAggregate(
        concept="color_preservation",
        evidence_count=6,
        evidence_strength=0.94,
        contradiction_score=0.04,
        semantic_consistency=0.97,
        causal_alignment=0.96,
    )

    commit = engine.evaluate(
        belief,
        aggregate,
        passed_trials("color_preservation"),
        color_context(),
    )

    alignment = commit.metadata["causal_graph_alignment"]
    explainability = commit.metadata["causal_explainability_report"]

    assert commit.decision == "TRUTH_COMMITTED"
    assert alignment["alignment_ready"] is True
    assert alignment["alignment_score"] > 0.82
    assert alignment["components"]["dependency_coherence"] > 0.90
    assert explainability["causal_gaps"] == []
    assert explainability["causal_reliability"] > 0.82
