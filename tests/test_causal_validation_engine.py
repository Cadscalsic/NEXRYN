from pathlib import Path

from core.causal_graph import CausalGraph
from core.causal_validation import CausalValidationEngine
from core.epistemic_models import (
    Belief,
    BeliefState,
    EpistemicTrial,
    EvidenceAggregate,
    TrialResult,
)
from core.truth_commit_engine import TruthCommitEngine


def evidence(task, support=1.0, contradiction=0.0, context="shape"):
    return {
        "source": task,
        "support_score": support,
        "contradiction_score": contradiction,
        "metadata": {
            "task_id": task,
            "context_signature": context,
        },
    }


def causal_graph_for(concept):
    graph = CausalGraph()
    graph.build_causal_spine(
        concept,
        observations=[
            evidence("task_a", context="small_grid"),
            evidence("task_b", context="large_grid"),
            evidence("task_c", context="rotated_grid"),
        ],
        confidence=1.0,
    )
    return graph


def test_causal_validation_accepts_stable_counterfactual_link(tmp_path):
    graph = causal_graph_for("shape_preservation")
    engine = CausalValidationEngine(
        storage_path=Path(tmp_path) / "causal_ledger.json"
    )

    report = engine.validate_hypothesis(
        {
            "source_concept": "shape_preservation",
            "target_concept": "shape_preservation",
        },
        [
            evidence("task_a", context="small_grid"),
            evidence("task_b", context="large_grid"),
            evidence("task_c", context="rotated_grid"),
        ],
        {
            "causal_graph_alignment":
            graph.compute_causal_alignment("shape_preservation"),
            "dependency_coherence": 1.0,
            "identity_compatibility": 1.0,
            "counterfactual_results": {
                "shape_preservation->shape_preservation": {
                    "effect_absent_without_source": True,
                },
            },
        },
        graph,
    )

    assert report["validation_state"] == "VALIDATED"
    assert report["validation_ready"] is True
    assert report["validation_score"] >= 0.75
    assert "passed counterfactual testing" in report["how_we_know"]
    assert engine.generate_validation_report()[
        "validated_hypotheses"
    ][0]["source_concept"] == "shape_preservation"


def test_spurious_causality_rejects_cooccurrence_without_dependency(tmp_path):
    engine = CausalValidationEngine(
        storage_path=Path(tmp_path) / "causal_ledger.json"
    )

    report = engine.validate_hypothesis(
        {
            "source_concept": "shape_preservation",
            "target_concept": "color_preservation",
        },
        [
            evidence("task_a", context="same_grid"),
            evidence("task_b", context="same_grid"),
            evidence("task_c", context="same_grid"),
        ],
        {
            "dependency_coherence": 0.10,
            "identity_compatibility": 1.0,
            "counterfactual_results": {
                "shape_preservation->color_preservation": {
                    "effect_preserved_without_source": True,
                },
            },
        },
    )

    assert report["validation_state"] == "REJECTED"
    assert report["spurious_causality"]["relationship_state"] == (
        "SPURIOUS_RELATIONSHIP"
    )
    assert report["validation_ready"] is False


def test_counterfactual_validation_decreases_confidence_when_effect_remains(
    tmp_path,
):
    engine = CausalValidationEngine(
        storage_path=Path(tmp_path) / "causal_ledger.json"
    )

    report = engine.counterfactual_validation(
        {
            "source_concept": "topology_preservation",
            "target_concept": "shape_preservation",
        },
        {
            "counterfactual_results": {
                "topology_preservation->shape_preservation": {
                    "effect_preserved_without_source": True,
                },
            },
        },
    )

    assert report["counterfactual_score"] == 0.0
    assert report["counterfactual_state"] == (
        "COUNTERFACTUAL_WEAKENS_CAUSE"
    )


def test_causal_validation_uses_scene_context_consistency(tmp_path):
    engine = CausalValidationEngine(
        storage_path=Path(tmp_path) / "causal_ledger.json"
    )

    report = engine.validate_hypothesis(
        {
            "source_concept": "color_preservation",
            "target_concept": "color_preservation",
        },
        [
            evidence("task_a", context="duplication"),
            evidence("task_b", context="duplication"),
            evidence("task_c", context="duplication"),
        ],
        {
            "dependency_coherence": 0.80,
            "identity_compatibility": 1.0,
            "scene_graph_comparison": {
                "summary": {
                    "object_level_ready": True,
                    "input_object_count": 1,
                    "output_object_count": 2,
                },
                "object_matches": [{
                    "shape_preserved": True,
                }],
                "object_events": [{
                    "event": "object_added",
                    "confidence": 0.82,
                }],
                "relation_changes": {
                    "relations_added": ["left_of"],
                    "relations_preserved": ["same_shape"],
                },
            },
        },
    )

    assert report["context_consistency"] >= 0.70


def test_causal_validation_reports_dependency_promotion_diagnostics(tmp_path):
    engine = CausalValidationEngine(
        storage_path=Path(tmp_path) / "causal_ledger.json"
    )

    report = engine.validate_hypothesis(
        {
            "source_concept": "growth",
            "target_concept": "growth",
        },
        [
            evidence("task_a", context="growth"),
            evidence("task_b", context="growth"),
            evidence("task_c", context="growth"),
        ],
        {
            "dependency_coherence": 0.68,
            "identity_compatibility": 1.0,
            "process_dependency_memory": {
                "dependency_confidence": 0.9017,
                "dependency_chain_depth": 5,
                "dependency_chain_coverage": 0.8556,
                "missing_dependencies": [],
            },
        },
    )

    assert report["promotion_dependency_score"] >= 0.89
    assert report["promotion_dependency_bonus"] > 0.0
    assert report["dependency_promotion_blockers"] == []
    assert report["dependency_coherence"] > 0.34
    assert report["dependency_promotion_evidence"][
        "dependency_chain_complete_for_promotion"
    ] is True


def test_truth_commit_requires_causal_validation_score():
    engine = TruthCommitEngine()
    belief = Belief(
        concept="shape_preservation",
        claim="shape_preservation is stable",
        state=BeliefState.TRUTH_CANDIDATE,
        confidence=0.95,
    )
    aggregate = EvidenceAggregate(
        concept="shape_preservation",
        evidence_count=3,
        evidence_strength=0.95,
        contradiction_score=0.0,
        semantic_consistency=1.0,
        causal_alignment=1.0,
    )
    trials = [
        EpistemicTrial(
            concept="shape_preservation",
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

    commit = engine.evaluate(
        belief,
        aggregate,
        trials,
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
                "validation_score": 0.62,
                "validation_ready": False,
            },
        },
    )

    assert commit.decision == "REMAIN_BELIEF"
    assert "causal_validation_score" in commit.reasons
