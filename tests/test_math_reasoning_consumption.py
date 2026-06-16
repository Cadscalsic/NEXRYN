from core.context.context_strength_engine import ContextStrengthEngine
from core.context.process_context_generation import ProcessContextGenerationEngine
from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.math_reasoning import MathematicalReasoningLayer
from core.context_discovery import ContextDiscoveryEngine
from core.truth.truth_candidate_engine import TruthCandidatePromotionEngine


def math_report(concept="growth", dependency_score=0.86):
    return {
        "system": "mathematical_reasoning_pipeline",
        "concept": concept,
        "graph_report": {
            "system": "graph_relations_engine",
            "comparison": {
                "node_count_change": 1,
                "edge_count_change": 1,
            },
        },
        "set_report": {
            "system": "set_operations_engine",
            "set_changes_detected": True,
            "relation": "expanded",
            "added_items": [[0, 1]],
            "removed_items": [],
            "preserved_items": [[0, 0]],
        },
        "transformation_report": {
            "system": "transformation_algebra_engine",
            "operators": [{"operator": "duplicate"}],
            "transformation_signature": {
                "operator_types": ["duplicate"],
                "changes_object_count": True,
                "preserves_shape": True,
                "preserves_position": False,
                "preserves_color": True,
            },
        },
        "dependency_semantics_report": {
            "system": "dependency_semantics_engine",
            "dependency_semantics_score": dependency_score,
            "typed_dependencies": [
                {
                    "source": concept,
                    "target": "topology_expansion",
                    "relation": "expands",
                    "confidence": dependency_score,
                    "evidence": {},
                    "contexts": [f"{concept}_context"],
                }
            ],
            "semantic_dependency_signature": {
                "relation_types": ["expands"],
                "process_context": f"{concept}_context",
                "has_causal_chain": True,
            },
        },
        "math_reasoning_signature": {
            "spatial_relations_detected": True,
            "graph_relations_detected": True,
            "set_changes_detected": True,
            "transformations_detected": True,
            "typed_dependencies_generated": True,
            "process_context_hint": f"{concept}_context",
        },
    }


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


def test_process_context_generation_engine_generates_growth_context():
    reasoning_report = math_report("growth")
    report = ProcessContextGenerationEngine().generate(
        "growth",
        {
            **reasoning_report,
            "dependency_semantics_report": {},
        },
        dependency_semantics_report=reasoning_report["dependency_semantics_report"],
    )

    assert report["context_name"] == "growth_context"
    assert report["source_concept"] == "growth"
    assert report["status"] in {
        "PROCESS_CONTEXT_CANDIDATE",
        "PROCESS_CONTEXT_SUPPORTED",
        "PROCESS_CONTEXT_VALIDATED",
    }
    assert report["supporting_math_evidence"]["typed_dependencies_generated"] is True
    assert report["supporting_math_evidence"]["dependency_semantics_score"] == 0.86


def test_process_context_generation_engine_generates_replication_context():
    report = ProcessContextGenerationEngine().generate(
        "replication",
        math_report("replication"),
    )

    assert report["context_name"] == "replication_context"
    assert "identity_forking" in report["properties"]


def test_process_context_generation_engine_rejects_unknown_process_concept():
    report = ProcessContextGenerationEngine().generate("unknown_process", math_report())

    assert report["process_context_generated"] is False
    assert report["status"] == "PROCESS_CONTEXT_REJECTED"


def test_preservation_concepts_do_not_receive_process_contexts():
    process_report = ProcessContextGenerationEngine().generate(
        "replication",
        math_report("replication"),
    )
    discovery = ContextDiscoveryEngine().discover_context({
        "task_id": "task",
        "concept": "shape_preservation",
        "active_concepts": ["shape_preservation", "replication"],
        "process_context_report": process_report,
    })

    assert discovery["discovered_context"]["context_name"] == "shape_context"


def test_context_strength_engine_consumes_math_reasoning_evidence_safely():
    report = math_report("growth")
    process_report = ProcessContextGenerationEngine().generate("growth", report)
    strength = ContextStrengthEngine().consume_math_reasoning(
        0.62,
        math_reasoning_report=report,
        process_context_report=process_report,
        dependency_semantics_report=report["dependency_semantics_report"],
        runtime_context={},
    )

    assert strength["math_reasoning_used"] is True
    assert strength["process_context_strength"] > 0
    assert strength["final_context_strength"] > 0.62
    assert strength["final_context_strength"] < 1.0
    assert strength["evidence_used"] == strength["math_reasoning_evidence_used"]
    assert strength["evidence_rejected"] is False


def test_context_strength_engine_rejects_invalid_math_evidence():
    strength = ContextStrengthEngine().consume_math_reasoning(
        0.62,
        math_reasoning_report={"math_reasoning_signature": {}},
        process_context_report={"status": "INVALID"},
        dependency_semantics_report={},
        runtime_context={},
    )

    assert strength["math_reasoning_used"] is False
    assert strength["final_context_strength"] == 0.62
    assert "process_context_status_invalid" in strength["rejection_reasons"]
    assert strength["evidence_rejected"] is True


def test_context_strength_engine_rejects_preservation_context_conflict():
    report = math_report("growth")
    process_report = ProcessContextGenerationEngine().generate("growth", report)
    strength = ContextStrengthEngine().consume_math_reasoning(
        0.62,
        math_reasoning_report=report,
        process_context_report=process_report,
        dependency_semantics_report=report["dependency_semantics_report"],
        runtime_context={"active_contexts": ["shape_context"]},
    )

    assert strength["math_reasoning_used"] is False
    assert strength["final_context_strength"] == 0.62
    assert "process_context_conflicts_with_preservation_context" in strength[
        "rejection_reasons"
    ]


def test_context_strength_increases_gradually_not_forcibly():
    report = math_report("growth")
    process_report = ProcessContextGenerationEngine().generate("growth", report)
    strength = ContextStrengthEngine().consume_math_reasoning(
        0.20,
        math_reasoning_report=report,
        process_context_report=process_report,
        dependency_semantics_report=report["dependency_semantics_report"],
        runtime_context={},
    )

    assert 0.20 < strength["final_context_strength"] < 0.60


def test_truth_candidate_promotion_engine_still_respects_all_gates():
    report = math_report("growth")
    process_report = ProcessContextGenerationEngine().generate("growth", report)
    promotion = TruthCandidatePromotionEngine().evaluate(
        {
            **mature_ledger("growth", context_strength=0.20),
            "used_task_count": 1,
        },
        {
            "evaluations": [{
                "concept": "growth",
                "math_reasoning_report": report,
                "process_context_report": process_report,
                "dependency_semantics_report": report["dependency_semantics_report"],
                "identity_safe_truth_integration": {
                    "identity_continuity": 0.75,
                },
            }]
        },
    )

    assert promotion["readiness_gates"]["observed_task_count"] is False
    assert promotion["candidate_ready"] is False
    assert promotion["decision"] != "PROMOTE_TO_TRUTH_CANDIDATE"
    assert promotion["evidence_used"]
    assert promotion["evidence_rejected"] is False


def test_global_runtime_state_is_not_mutated():
    report = math_report("growth")
    process_report = ProcessContextGenerationEngine().generate("growth", report)
    runtime_context = {"identity_runtime_split": "local"}
    before = dict(runtime_context)

    ContextStrengthEngine().consume_math_reasoning(
        0.62,
        math_reasoning_report=report,
        process_context_report=process_report,
        dependency_semantics_report=report["dependency_semantics_report"],
        runtime_context=runtime_context,
    )

    assert runtime_context == before


def test_running_without_math_reasoning_behaves_as_before():
    promotion = TruthCandidatePromotionEngine().evaluate(
        mature_ledger("growth", context_strength=0.50),
        {"evaluations": [{"concept": "growth"}]},
    )

    assert promotion["context_strength"] == 0.50
    assert promotion["math_reasoning_consumed"] is False
    assert promotion["readiness_gates"]["context_strength"] is False


def test_process_dependency_memory_generates_process_context_for_promotion():
    process_memory = ProcessDependencyMemory(seed_defaults=True).resolve_chain(
        "replication",
    )
    promotion = TruthCandidatePromotionEngine().evaluate(
        mature_ledger("replication", context_strength=0.50),
        {
            "evaluations": [{
                "concept": "replication",
                "process_dependency_memory": process_memory,
                "causal_validation": {
                    "promotion_dependency_score": 0.92,
                    "dependency_promotion_evidence": process_memory,
                },
                "identity_safe_truth_integration": {
                    "identity_continuity": 0.75,
                },
            }]
        },
    )

    assert promotion["math_reasoning_consumed"] is True
    assert promotion["process_context_generated"] is True
    assert promotion["process_context_generation"]["process_context"] == (
        "replication_context"
    )
    assert promotion["readiness_gates"]["context_strength"] is True
    assert "promotion_gate_blocked:context_strength" not in (
        promotion["dependency_promotion_blockers"]
    )
    assert promotion["candidate_ready"] is True


def test_process_context_consumes_transformation_algebra_additively():
    process_memory = ProcessDependencyMemory(seed_defaults=True).resolve_chain(
        "propagation",
    )
    reasoning_report = MathematicalReasoningLayer().analyze_dependency_chain(
        "propagation",
        process_dependency_memory=process_memory,
    )
    process_report = ProcessContextGenerationEngine().generate(
        "propagation",
        reasoning_report,
    )
    strength = ContextStrengthEngine().consume_math_reasoning(
        0.50,
        math_reasoning_report=reasoning_report,
        process_context_report=process_report,
        dependency_semantics_report=reasoning_report[
            "dependency_semantics_report"
        ],
        runtime_context={},
    )

    evidence = process_report["supporting_math_evidence"]
    assert evidence["transformation_algebra_generated"] is True
    assert evidence["process_algebra_match"] is True
    assert evidence["process_signature_generated"] is True
    assert evidence["process_signature_id"] == "propagation_signature"
    assert evidence["process_signature_match"] is True
    assert evidence["primary_transformation_type"] == "propagation"
    assert "transformation_algebra" in strength["evidence_used"]
    assert "process_signature" in strength["evidence_used"]
    assert strength["final_context_strength"] > 0.50


def test_identity_scope_leakage_rejects_math_context_strength():
    report = math_report("growth")
    report["transformation_report"]["transformation_algebra"] = {
        "transformation_algebra_generated": True,
        "transformation_types": ["growth"],
        "primary_transformation_type": "growth",
        "identity_scope_leakage_detected": True,
        "invariants": {
            "preserves_identity": True,
            "forks_identity": True,
        },
        "algebraic_signature": "growth|preserves_identity+forks_identity",
    }
    report["transformation_report"]["transformation_signature"].update({
        "transformation_types": ["growth"],
        "primary_transformation_type": "growth",
        "invariants": {
            "preserves_identity": True,
            "forks_identity": True,
        },
        "algebraic_signature": "growth|preserves_identity+forks_identity",
    })
    process_report = ProcessContextGenerationEngine().generate("growth", report)

    strength = ContextStrengthEngine().consume_math_reasoning(
        0.62,
        math_reasoning_report=report,
        process_context_report=process_report,
        dependency_semantics_report=report["dependency_semantics_report"],
        runtime_context={},
    )

    assert strength["math_reasoning_used"] is False
    assert strength["final_context_strength"] == 0.62
    assert "identity_scope_leakage_detected" in strength["rejection_reasons"]
