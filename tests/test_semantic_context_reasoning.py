from core.belief_engine import EpistemicCognitionLayer
from core.epistemic_models import (
    Belief,
    BeliefState,
    EpistemicTrial,
    EvidenceAggregate,
    TrialResult,
)
from core.semantic_context import (
    SemanticContextReasoner,
    explain_context,
    semantic_context_similarity,
)
from core.truth_commit_engine import TruthCommitEngine
from runtime.memory.semantic_memory import SemanticMemory


def duplication_context():
    return {
        "transformation_family": "duplication",
        "confidence": 0.95,
        "context_signature": {
            "transformation_family": "duplication",
            "object_dynamics": "object_created",
            "topology_behavior": "topology_splitting",
            "color_behavior": "color_preserved",
            "identity_behavior": "identity_split",
            "size_behavior": "size_preserved",
            "confidence": 0.95,
        },
    }


def recoloring_context():
    return {
        "transformation_family": "recoloring",
        "confidence": 0.95,
        "context_signature": {
            "transformation_family": "recoloring",
            "object_dynamics": "object_preserved",
            "topology_behavior": "topology_preserved",
            "color_behavior": "color_changed",
            "identity_behavior": "identity_modified",
            "size_behavior": "size_preserved",
            "confidence": 0.95,
        },
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


def passing_trials(concept="duplication_rule"):
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


def test_semantic_profile_assigns_meaning_to_duplication():
    reasoner = SemanticContextReasoner()
    profile = reasoner.generate_semantic_profile(duplication_context())
    properties = {
        item["property_name"]
        for item in profile["properties"]
    }

    assert "Creates one or more additional object instances" in (
        profile["semantic_definition"]
    )
    assert "creates_objects" in properties
    assert "preserves_shape" in properties
    assert "object_creation" in profile["capabilities"]
    assert "object_count_changes" in profile["constraints"]
    assert "object_count_increase" in profile["implications"]
    assert profile["status"] == "SEMANTICALLY_VALIDATED"


def test_property_discovery_reads_observed_context_features():
    reasoner = SemanticContextReasoner()
    profile = reasoner.generate_semantic_profile(recoloring_context())
    properties = {
        item["property_name"]
        for item in profile["properties"]
    }

    assert "changes_color" in properties
    assert "preserves_topology" in properties
    assert "color_mapping_changes" in profile["constraints"]
    assert "color_change" in profile["implications"]


def test_semantic_context_similarity_uses_meaning_not_only_labels():
    assert semantic_context_similarity("duplication", "replication") == 0.82
    assert semantic_context_similarity("duplication", "reflection") < 0.25


def test_explain_context_answers_semantic_questions():
    explanation = explain_context(duplication_context())

    assert explanation["what_is_this_context"]
    assert "object_creation" in explanation["what_can_it_do"]
    assert "object_count_changes" in explanation["what_limits_does_it_have"]
    assert "object_count_increase" in explanation["what_consequences_follow"]


def test_runtime_report_exposes_semantic_context_report():
    layer = EpistemicCognitionLayer()
    report = layer.run_cycle({
        "task_id": "task_duplication_semantics",
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

    semantic = report["semantic_context_reasoner"]["evaluations"][0]
    candidate = report["evaluations"][0]["truth_candidate"]

    assert semantic["context"] == "duplication"
    assert semantic["semantically_validated"] is True
    assert "object_creation" in semantic["capabilities"]
    assert candidate["semantic_context"]["status"] == "SEMANTICALLY_VALIDATED"


def test_semantic_memory_stores_context_semantic_profile():
    memory = SemanticMemory()
    memory.store_concept(
        "duplication_rule",
        {
            "active_concepts": ["duplication"],
            "confidence": 0.95,
            "supporting_evidence": [
                strong_evidence("duplication_rule", "task_a"),
            ],
            "originating_tasks": ["task_a"],
        },
    )
    stored = memory.retrieve_concept("duplication_rule")

    assert stored["semantic_context_profile"]["context_name"] == "duplication"
    assert "object_creation" in stored["context_capabilities"]
    assert stored["property_confidence_history"]


def test_truth_governance_consumes_semantic_context_support_links():
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
    semantic = SemanticContextReasoner().generate_semantic_profile(
        duplication_context()
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
                "context_hierarchy_score": 1.0,
                "hierarchy_ready": True,
            },
            "semantic_context": semantic,
        },
    )
    links = commit.metadata["semantic_context_support_links"]

    assert commit.metadata["semantic_context"]["context"] == "duplication"
    assert any(
        item["context_property"] == "creates_objects"
        for item in links
    )
