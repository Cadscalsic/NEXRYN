from core.concept_lifecycle.concept_maturity import ConceptMaturityTracker
from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.dependency.dependency_graph_engine import DependencyGraphEngine
from core.math_reasoning import MathematicalReasoningLayer, ProcessSignatureEngine
from core.process import ProcessSignatureEngine as CoreProcessSignatureEngine


def mature_concept(concept):
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
        "identity_strength": 0.75,
        "context_strength": 0.50,
    }


def test_replication_signature_from_dependency_nodes():
    report = ProcessSignatureEngine().extract_signature(
        "replication",
        dependency_chain=[
            "identity_forking",
            "object_count_increase",
            "topology_splitting",
        ],
    )

    assert report["signature_id"] == "replication_signature"
    assert report["canonical_process_context"] == "replication_context"
    assert report["process_signature_generated"] is True
    assert report["concept_signature"]["signature_id"] == "replication_signature"
    assert report["signature_confidence"] > 0.0
    assert "identity_split_reasoning" in report["signature_capabilities"]
    assert "requires_source_object" in report["signature_constraints"]
    assert "identity_split" in report["signature_invariants"]
    assert report["identity_scope_leakage_detected"] is False


def test_propagation_signature_from_dependency_nodes():
    report = ProcessSignatureEngine().extract_signature(
        "propagation",
        dependency_chain=[
            "source_pattern_preserved",
            "directional_motion",
            "position_change",
        ],
    )

    assert report["signature_id"] == "propagation_signature"
    assert report["canonical_process_context"] == "propagation_context"
    assert report["missing_features"] == []


def test_growth_signature_from_dependency_nodes():
    report = ProcessSignatureEngine().extract_signature(
        "growth",
        dependency_chain=[
            "identity_persistence",
            "topology_expansion",
            "shape_preservation",
        ],
    )

    assert report["signature_id"] == "growth_signature"
    assert report["canonical_process_context"] == "growth_context"


def test_topological_growth_signature_from_dependency_nodes():
    report = ProcessSignatureEngine().extract_signature(
        "topological_growth",
        dependency_chain=[
            "topology_expansion",
            "local_shape",
            "topology_preservation",
        ],
    )

    assert report["signature_id"] == "topological_growth_signature"
    assert report["canonical_process_context"] == "topological_growth_context"


def test_symmetry_signature_from_relational_context():
    report = ProcessSignatureEngine().extract_signature(
        "symmetry_reasoning",
        dependency_chain=[
            "symmetry_preservation",
            "reflection_relation",
        ],
    )

    assert report["signature_id"] == "symmetry_signature"
    assert report["canonical_process_context"] == "symmetry_context"
    assert report["concept_signature"]["canonical_process_context"] == (
        "symmetry_context"
    )
    assert "relational_symmetry_inference" in report["signature_capabilities"]
    assert "symmetry_preservation" in report["signature_invariants"]


def test_dependency_chain_analysis_emits_process_signature_report():
    memory = ProcessDependencyMemory(seed_defaults=True)
    report = MathematicalReasoningLayer().analyze_dependency_chain(
        "replication",
        process_dependency_memory=memory.resolve_chain("replication"),
    )

    signature = report["process_signature_report"]
    assert signature["system"] == "process_signature_engine"
    assert signature["signature_id"] == "replication_signature"
    assert report["dependency_semantics_report"]["dependency_semantics_score"] > 0.90
    assert report["dependency_semantics_report"]["process_signature_semantics_bonus"] >= 0.0
    assert report["math_reasoning_signature"]["process_signature_generated"] is True
    assert report["math_reasoning_signature"]["concept_signature"]


def test_core_process_signature_engine_extracts_required_process_surfaces():
    memory = ProcessDependencyMemory(seed_defaults=True)
    expected = {
        "growth": "growth_signature",
        "propagation": "propagation_signature",
        "replication": "replication_signature",
        "topological_growth": "topological_growth_signature",
    }

    for concept, signature in expected.items():
        report = CoreProcessSignatureEngine().extract_signature(
            concept,
            process_dependency_memory=memory.resolve_chain(concept),
        )

        assert report["signature"] == signature
        assert report["signature_confidence"] > 0.90
        assert report["context_surface"] == f"{concept}_context"
        assert report["signature_invariants"]
        assert report["signature_constraints"]
        assert report["signature_capabilities"]
        assert report["identity_scope_leakage_detected"] is False


def test_process_signature_evidence_lifts_dependency_coherence_above_point_nine(tmp_path):
    report = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
        dependency_chain_ledger_path=tmp_path / "dependency_chain_ledger.json",
        process_dependency_memory_path=tmp_path / "process_dependency_memory.json",
    ).ingest_process_dependency_memory([
        "growth",
        "propagation",
        "replication",
        "topological_growth",
    ])

    assert report["process_signature_dependency_count"] == 4
    assert report["dependency_coherence_average"] > 0.90
    for concept in [
        "growth",
        "propagation",
        "replication",
        "topological_growth",
    ]:
        assert report["process_signature_reports"][concept]["signature"]
        assert report["coherence_reports"][concept]["dependency_coherence"] > 0.90


def test_process_signatures_clear_context_strength_boundary_refinement():
    memory = ProcessDependencyMemory(seed_defaults=True)
    concepts = [
        "growth",
        "propagation",
        "replication",
        "topological_growth",
    ]
    evaluations = []
    for concept in concepts:
        process_memory = memory.resolve_chain(concept)
        reasoning = MathematicalReasoningLayer().analyze_dependency_chain(
            concept,
            process_dependency_memory=process_memory,
        )
        evaluations.append({
            "concept": concept,
            "process_dependency_memory": process_memory,
            "math_reasoning_report": reasoning,
            "dependency_semantics_report": reasoning[
                "dependency_semantics_report"
            ],
            "causal_validation": {
                "promotion_dependency_score": 0.92,
                "dependency_promotion_evidence": process_memory,
            },
            "identity_safe_truth_integration": {
                "identity_continuity": 0.75,
            },
        })

    report = ConceptMaturityTracker().evaluate(
        {
            "concepts": [
                mature_concept(concept)
                for concept in concepts
            ],
        },
        {"evaluations": evaluations},
    )

    states = {
        item["concept"]: item["state"]
        for item in report["concepts"]
    }
    for item in report["concepts"]:
        promotion = item["truth_candidate_promotion"]
        assert states[item["concept"]] != "BOUNDARY_REFINEMENT"
        assert promotion["readiness_gates"]["context_strength"] is True
        assert "promotion_gate_blocked:context_strength" not in (
            promotion["dependency_promotion_blockers"]
        )
        assert promotion["math_reasoning_consumed"] is True
