from core.concept_lifecycle.concept_maturity import ConceptMaturityTracker
from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.truth.truth_candidate_engine import TruthCandidatePromotionEngine
from runtime.context.process_context_discovery_engine import (
    ProcessContextDiscoveryEngine,
)


PROCESS_CONCEPTS = [
    "growth",
    "propagation",
    "replication",
    "directional_motion",
    "topological_growth",
]


def mature_ledger(concept, context_strength=0.50):
    return {
        "concept": concept,
        "used_task_count": 8,
        "cross_task_support": 0.84,
        "records": [
            {
                "success": True,
                "contradiction_score": 0.05,
                "causal_alignment": 0.82,
            }
            for _ in range(8)
        ],
        "context_strength": context_strength,
        "identity_strength": 0.75,
    }


def runtime_evaluation(concept):
    process_memory = ProcessDependencyMemory(
        seed_defaults=True,
    ).resolve_chain(concept)
    return {
        "concept": concept,
        "process_dependency_memory": process_memory,
        "causal_validation": {
            "promotion_dependency_score": 0.92,
            "dependency_promotion_evidence": process_memory,
        },
        "identity_safe_truth_integration": {
            "integration_safe": True,
            "identity_continuity": 0.82,
        },
    }


def test_process_context_discovery_generates_required_context_definitions():
    memory = ProcessDependencyMemory(seed_defaults=True)

    report = ProcessContextDiscoveryEngine().report(
        PROCESS_CONCEPTS,
        dependency_resolver=memory,
    )

    assert report["process_context_count"] == 5
    assert report["process_context_count"] > 2
    assert set(report["discovered_context_names"]) == {
        "growth_context",
        "propagation_context",
        "replication_context",
        "motion_context",
        "topological_growth_context",
    }
    for context in report["process_contexts"]:
        assert set(
            [
                "concept",
                "context_name",
                "preconditions",
                "transition_family",
                "expected_outcomes",
                "context_confidence",
            ]
        ).issubset(context)
        assert context["preconditions"]
        assert context["transition_family"]
        assert context["expected_outcomes"]
        assert context["context_confidence"] > 0.90


def test_discovered_process_context_flows_into_temporal_promotion_report():
    promotion = TruthCandidatePromotionEngine().evaluate(
        mature_ledger("growth", context_strength=0.50),
        {"evaluations": [runtime_evaluation("growth")]},
    )

    discovery = promotion["process_context_discovery_report"]
    assert discovery["context_name"] == "growth_context"
    assert discovery["process_context_discovered"] is True
    assert promotion["temporal_process_context_report"][
        "process_context_discovery_report"
    ]["context_name"] == "growth_context"
    assert promotion["readiness_gates"]["context_strength"] is True
    assert "promotion_gate_blocked:context_strength" not in (
        promotion["dependency_promotion_blockers"]
    )
    assert promotion["candidate_ready"] is True


def test_discovered_process_contexts_make_core_processes_candidate_ready():
    report = ConceptMaturityTracker().evaluate(
        {
            "concepts": [
                mature_ledger(concept, context_strength=0.50)
                for concept in ["growth", "propagation", "replication"]
            ],
        },
        {
            "evaluations": [
                runtime_evaluation(concept)
                for concept in ["growth", "propagation", "replication"]
            ],
        },
    )

    for item in report["concepts"]:
        promotion = item["truth_candidate_promotion"]
        assert item["state"] == "TRUTH_CANDIDATE"
        assert promotion["process_context_discovery_report"][
            "process_context_discovered"
        ] is True
        assert promotion["readiness_gates"]["context_strength"] is True
        assert "promotion_gate_blocked:context_strength" not in (
            promotion["dependency_promotion_blockers"]
        )
        assert promotion["candidate_ready"] is True
