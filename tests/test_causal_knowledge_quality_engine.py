from runtime.causal import CausalKnowledgeQualityEngine


def _causal_report():
    return {
        "CAUSAL_CONTEXT_REPORT": True,
        "execution_id": "episode:quality",
        "timestamp": "2026-07-14T00:00:00",
        "causal_simulation_accuracy": 0.82,
        "cause_effect_pairs": [
            {
                "relation_id": "causal:a",
                "cause": "remove_noise",
                "effect": "clean_grid",
                "mechanism": (
                    "remove_noise causes clean_grid because isolated artifacts "
                    "are filtered through neighborhood consistency"
                ),
                "conditions": ["isolated_noise_present", "stable_background"],
                "exceptions": ["noise_is_target_object"],
                "supporting_evidence": ["evidence:1", "evidence:2", "evidence:3"],
                "support_count": 5,
                "contradicting_evidence": [],
                "confidence": 0.91,
                "validation_status": "validated",
                "prediction_accuracy": 0.88,
                "domains": ["denoising", "object_cleanup"],
                "tasks": ["task:1", "task:2", "task:3"],
            },
            {
                "relation_id": "causal:b",
                "cause": "mirror_left",
                "effect": "symmetry_created",
                "mechanism": "",
                "conditions": [],
                "exceptions": [],
                "supporting_evidence": ["evidence:4"],
                "support_count": 1,
                "contradicting_evidence": [],
                "confidence": 0.38,
                "validation_status": "unvalidated",
                "prediction_accuracy": 0.31,
            },
            {
                "relation_id": "causal:c",
                "cause": "color_change",
                "effect": "object_identity_preserved",
                "mechanism": "color_change leads to identity preservation via shape invariance",
                "conditions": ["shape_constant"],
                "supporting_evidence": ["evidence:5", "evidence:6"],
                "support_count": 2,
                "contradicting_evidence": ["evidence:contra"],
                "confidence": 0.62,
                "validation_status": "validated",
                "prediction_accuracy": 0.55,
            },
            {
                "relation_id": "causal:d",
                "cause": "clean_grid",
                "effect": "remove_noise",
                "mechanism": "clean_grid causes remove_noise through reverse cleanup observation",
                "conditions": ["post_state_observed"],
                "supporting_evidence": ["evidence:7", "evidence:8"],
                "support_count": 2,
                "confidence": 0.58,
                "validation_status": "validated",
                "prediction_accuracy": 0.6,
            },
        ],
    }


def _assessment(report, causal_id):
    return next(
        item for item in report["quality_assessments"]
        if item["causal_id"] == causal_id
    )


def test_evidence_validation_scores_supported_relationships_higher():
    report = CausalKnowledgeQualityEngine().build_report(_causal_report())

    strong = _assessment(report, "causal:a")
    weak = _assessment(report, "causal:b")

    assert strong["evidence_score"] > weak["evidence_score"]
    assert "causal:b" in report["consistency_analysis"]["weak_evidence"]


def test_mechanism_validation_blocks_full_maturity_without_explanation():
    report = CausalKnowledgeQualityEngine().build_report(_causal_report())

    strong = _assessment(report, "causal:a")
    missing = _assessment(report, "causal:b")

    assert strong["mechanism_score"] >= 0.85
    assert missing["mechanism_score"] == 0.0
    assert missing["maturity_state"] in {"WEAK", "QUESTIONABLE"}
    assert "causal:b" in report["missing_mechanisms"]


def test_generalization_validation_uses_tasks_domains_and_repeated_support():
    report = CausalKnowledgeQualityEngine().build_report(_causal_report())

    strong = _assessment(report, "causal:a")
    weak = _assessment(report, "causal:b")

    assert strong["generalization_score"] > weak["generalization_score"]
    assert "remove_noise->clean_grid" in report["candidate_generalizations"]


def test_prediction_validation_contributes_to_quality():
    report = CausalKnowledgeQualityEngine().build_report(_causal_report())

    strong = _assessment(report, "causal:a")
    weak = _assessment(report, "causal:b")

    assert strong["prediction_score"] == 0.88
    assert weak["prediction_score"] == 0.31
    assert strong["overall_causal_quality"] > weak["overall_causal_quality"]


def test_contradiction_detection_marks_relationships():
    report = CausalKnowledgeQualityEngine().build_report(_causal_report())

    contradicted = _assessment(report, "causal:c")

    assert contradicted["maturity_state"] == "CONTRADICTED"
    assert "causal:c" in report["contradicted_relationships"]
    assert "causal:c" in report["consistency_analysis"]["contradictory_observations"]


def test_circular_causality_detection():
    report = CausalKnowledgeQualityEngine().build_report(_causal_report())

    circles = report["consistency_analysis"]["circular_causality"]

    assert ["clean_grid", "remove_noise"] in circles
    assert ["remove_noise", "clean_grid"] in circles


def test_lifecycle_progression_reaches_canonical_for_mature_links():
    report = CausalKnowledgeQualityEngine().build_report(_causal_report())

    strong = _assessment(report, "causal:a")

    assert strong["maturity_state"] == "CANONICAL"
    assert report["canonical_causal_links"] == 1
    assert report["validated_causal_links"] >= 1


def test_quality_score_consistency_and_reproducibility():
    engine = CausalKnowledgeQualityEngine()
    first = engine.build_report(_causal_report())
    second = engine.build_report(_causal_report())

    assert 0.0 <= first["causal_quality"] <= 1.0
    assert 0.0 <= first["mechanism_completeness"] <= 1.0
    assert 0.0 <= first["generalization_quality"] <= 1.0
    assert first["reproducibility_signature"] == second["reproducibility_signature"]


def test_enrich_report_exposes_execution_report_fields():
    enriched = CausalKnowledgeQualityEngine().enrich_report(_causal_report())

    assert enriched["CAUSAL_CONTEXT_REPORT"] is True
    assert enriched["CAUSAL_KNOWLEDGE_QUALITY_REPORT"][
        "CAUSAL_KNOWLEDGE_QUALITY_REPORT"
    ] is True
    assert enriched["generated_causal_links"] == 4
    assert enriched["causal_quality"] > 0.0
    assert "contradicted_relationships" in enriched
