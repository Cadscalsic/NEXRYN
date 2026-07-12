from runtime.knowledge import CognitiveKnowledgeIntegrationLayer, UnifiedCognitiveBus
from runtime.reflection import ReflectionEngine


def _runtime_reports():
    return {
        "reasoning_runtime": {
            "reasoning_artifacts": [
                {"object_id": "reasoning:reflect", "confidence": 0.76}
            ]
        },
        "search_runtime": {
            "cognitive_routes": {
                "route:reflect": {
                    "route_id": "route:reflect",
                    "supporting_concepts": ["concept:reflect"],
                    "current_confidence": 0.73,
                }
            }
        },
        "concept_formation_runtime": {
            "discovered_concepts": [
                {
                    "concept_id": "concept:reflect",
                    "concept_name": "reflection-ready symmetry",
                    "confidence": 0.82,
                    "supporting_evidence": [{"id": "evidence:reflect"}],
                }
            ]
        },
        "program_synthesis_runtime": {
            "generated_program_objects": [
                {
                    "program_id": "program:reflect",
                    "required_concepts": ["concept:reflect"],
                    "confidence": 0.78,
                }
            ]
        },
        "evidence_builder_runtime": {
            "evidence_objects": [
                {
                    "id": "evidence:reflect",
                    "supporting_concepts": ["concept:reflect"],
                    "confidence": 0.86,
                    "reliability": 0.81,
                }
            ]
        },
        "truth_runtime": {
            "truth_candidates": [
                {"truth_id": "truth:reflect", "confidence": 0.91}
            ]
        },
    }


def test_completed_episode_automatically_enters_reflection_before_experience():
    bus = UnifiedCognitiveBus()
    publication = bus.publish_many_from_runtime_reports(
        _runtime_reports(),
        execution_id="exec:reflection-required",
    )

    episode = publication["snapshot"]["primary_episode"]
    reflection = episode["reflection"]

    assert episode["reflection_id"] == reflection["reflection_id"]
    assert episode["reflection_status"] == "COMPLETED"
    assert episode["stages"]["Reflection"]["observed"] is True
    assert reflection["episode_id"] == episode["episode_id"]
    assert reflection["execution_id"] == "exec:reflection-required"
    assert reflection["reflection_confidence"] > 0
    assert reflection["reflection_quality"] > 0
    assert reflection["reflection_report"]["REFLECTION_REPORT"] is True
    assert reflection["reflection_report"]["Reasoning Review"]["evaluated"] is True
    assert reflection["reflection_report"]["Search Review"]["evaluated"] is True
    assert reflection["reflection_report"]["Concept Review"]["evaluated"] is True
    assert reflection["reflection_report"]["Program Review"]["evaluated"] is True
    assert reflection["reflection_report"]["Evidence Review"]["evaluated"] is True
    assert reflection["reflection_report"]["Truth Review"]["evaluated"] is True
    assert reflection["reflection_report"]["Decision Review"]["evaluated"] is True
    assert reflection["reflection_report"]["Resource Review"]["evaluated"] is True
    assert reflection["second_order_cognition"]["second_order_cognition"] is True
    assert reflection["second_order_cognition"]["reflection_is_replay"] is False
    assert reflection["second_order_cognition"]["historical_execution_modified"] is False
    assert reflection["causal_analysis"]["causal_chain_reconstruction"]
    assert reflection["strategy_analysis"]["alternative_strategies"]
    assert reflection["learning_value"]["learning_value_score"] >= 0
    assert reflection["self_improvement_report"]["SELF_IMPROVEMENT_REPORT"] is True
    assert reflection["self_improvement_report"]["reflection_proposes_improvements_only"] is True
    assert reflection["self_improvement_report"]["cognitive_objects_mutated"] is False
    assert reflection["reflection_memory_update"]["reflection_memory_enabled"] is True
    assert reflection["reflective_synthesis_report"]["REFLECTIVE_SYNTHESIS_REPORT"] is True
    assert reflection["reflective_synthesis_report"]["writes_permanent_memory"] is False
    assert reflection["abstraction_registry_update"]["complete_lineage_preserved"] is True
    assert reflection["reflection_intelligence_report"]["REFLECTION_INTELLIGENCE_REPORT"] is True
    assert reflection["reflection_intelligence_report"]["reflection_advises_governance_only"] is True
    assert reflection["reflection_knowledge_graph"]["architectural_memory_of_reflective_intelligence"] is True
    assert episode["experience_eligibility"]["reflection_required"] is True
    assert episode["experience_eligibility"]["reflection_completed"] is True
    assert episode["experience_eligibility"]["experience_engine_may_consume"] is True


def test_reflection_answers_required_cognition_questions():
    bus = UnifiedCognitiveBus()
    publication = bus.publish_many_from_runtime_reports(
        _runtime_reports(),
        execution_id="exec:reflection-questions",
    )

    reflection = publication["episode"]["reflection"]
    answers = reflection["answers"]

    assert answers["What happened?"]
    assert answers["Why did it happen?"]
    assert answers["Which reasoning path was chosen?"]
    assert "What should be repeated?" in answers
    assert "What should never be repeated?" in answers
    assert "statistics_considered" in answers


def test_reflection_engine_report_is_exposed_through_episode_and_ckil_reports():
    bus = UnifiedCognitiveBus()
    bus.publish_many_from_runtime_reports(
        _runtime_reports(),
        execution_id="exec:reflection-report",
    )

    episode_report = bus.cognitive_episode_report()

    assert episode_report["reflection_summary"]["reflection_mandatory"] is True
    assert episode_report["reflection_summary"]["reflections_completed"] == 1
    assert episode_report["reflection_summary"]["unreflected_experience_candidates"] == 0
    assert episode_report["reflection_engine_report"]["REFLECTION_ENGINE_REPORT"] is True
    assert episode_report["reflection_engine_report"]["reflections_created"] == 1
    assert episode_report["reflection_engine_report"]["experience_requires_reflection"] is True

    ckil = CognitiveKnowledgeIntegrationLayer()
    ckil_report = ckil.build_unified_cognitive_bus_report(
        execution_id="exec:ckil-reflection",
        runtime_reports=_runtime_reports(),
    )
    ckil_episode_report = ckil_report["cognitive_episode_report"]

    assert ckil_report["primary_cognitive_episode"]["reflection_status"] == "COMPLETED"
    assert ckil_report["primary_reflection"]["reflection_status"] == "COMPLETED"
    assert ckil_report["reflection_engine_report"]["REFLECTION_ENGINE_REPORT"] is True
    assert ckil_episode_report["reflection_engine_report"]["REFLECTION_ENGINE_REPORT"] is True
    assert ckil_episode_report["reflection_summary"]["experience_engine_ready"] is True
    assert ckil_report["future_subsystem_integration"]["experience_engine_requires_reflected_episodes"] is True


def test_reflection_engine_can_analyze_episode_without_solving_problem():
    engine = ReflectionEngine()
    reflection = engine.reflect(
        episode={
            "episode_id": "episode:manual",
            "execution_id": "exec:manual",
            "episode_status": "CLOSED",
            "episode_outcome": "UNRESOLVED",
            "episode_summary": "Manual unresolved episode.",
            "statistics": {"object_count": 1, "reasoning_count": 1},
            "quality": {"episode_quality": 0.4},
        },
        objects=[
            {
                "object_id": "reasoning:manual",
                "object_type": "REASONING_STEP",
                "object_confidence": 0.45,
            }
        ],
    )

    assert reflection.reflection_status == "COMPLETED"
    assert reflection.answers["What happened?"] == "Manual unresolved episode."
    assert reflection.dimensions["Resource Allocation"]["reasoning_limitation_detected"] is True


def test_reflection_produces_second_order_causal_and_strategic_outputs():
    bus = UnifiedCognitiveBus()
    publication = bus.publish_many_from_runtime_reports(
        _runtime_reports(),
        execution_id="exec:reflection-second-order",
    )

    reflection = publication["episode"]["reflection"]
    report = reflection["reflection_report"]

    assert report["Root Cause Report"]["root_causes"]
    assert report["Root Cause Report"]["causal_chain_reconstruction"][-1]["stage"] == "Reflection"
    assert report["Success Analysis"]["success_detected"] is True
    assert report["Failure Analysis"]["failure_detected"] is False
    assert report["Alternative Strategies"]
    assert report["Counterfactual Review"]
    assert report["Assumption Analysis"]
    assert report["Uncertainty Analysis"]["certainty"] >= 0
    assert report["Decision Justifications"][0]["justification_confidence"] >= 0
    assert report["Bias Detection"]["automatic_detection"] is True
    assert report["Strategy Analysis"]["strategy_quality"] >= 0
    assert report["Transfer Opportunities"]
    assert report["Generalization Opportunities"]
    assert report["Learning Value"]["long_term_importance"] in {"low", "medium", "high"}
    assert report["Reflection Recommendations"]
    assert report["SELF_IMPROVEMENT_REPORT"]["Learning Signals"]
    assert report["SELF_IMPROVEMENT_REPORT"]["Improvement Plan"]
    assert report["SELF_IMPROVEMENT_REPORT"]["Reflection Quality Metrics"]["actionability"] > 0
    assert report["REFLECTIVE_SYNTHESIS_REPORT"]["Experience Candidates"]
    assert report["REFLECTIVE_SYNTHESIS_REPORT"]["Lessons Extracted"]


def test_failure_reflection_extracts_lessons_and_blocks_easy_promotion():
    engine = ReflectionEngine()
    reflection = engine.reflect(
        episode={
            "episode_id": "episode:failure",
            "execution_id": "exec:failure",
            "episode_status": "CLOSED",
            "episode_outcome": "FAILURE",
            "episode_summary": "Failure episode.",
            "statistics": {
                "object_count": 3,
                "reasoning_count": 1,
                "search_count": 1,
                "failure_count": 1,
            },
            "quality": {"episode_quality": 0.2, "efficiency": 0.3},
        },
        objects=[
            {
                "object_id": "reasoning:weak",
                "object_type": "REASONING_STEP",
                "object_confidence": 0.3,
            },
            {
                "object_id": "route:weak",
                "object_type": "SEARCH_ROUTE",
                "object_confidence": 0.35,
            },
            {
                "object_id": "failure:weak",
                "object_type": "FAILURE",
                "object_confidence": 0.2,
            },
        ],
    )

    report = reflection.reflection_report

    assert report["Failure Analysis"]["failure_detected"] is True
    assert report["Failure Analysis"]["lessons_extracted"]
    assert "episode_failed_before_reusable_truth_or_experience" in report["Root Cause Report"]["root_causes"]
    assert reflection.learning_value["learning_value_score"] >= 0


def test_self_improvement_report_generates_learning_signals_and_plan():
    bus = UnifiedCognitiveBus()
    publication = bus.publish_many_from_runtime_reports(
        _runtime_reports(),
        execution_id="exec:self-improvement",
    )

    reflection = publication["episode"]["reflection"]
    report = reflection["self_improvement_report"]

    assert report["SELF_IMPROVEMENT_REPORT"] is True
    assert report["Strengths"]
    assert "Weaknesses" in report
    assert "Recurring Patterns" in report
    assert report["Knowledge Promotions"]
    assert "Knowledge Demotions" in report
    assert "Detected Conflicts" in report
    assert report["Consistency Analysis"]["cognitive_drift_detected"] in {True, False}
    assert report["Learning Signals"]
    assert all(signal["priority"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "OPTIONAL"} for signal in report["Learning Signals"])
    assert report["Improvement Priorities"]
    assert report["Improvement Plan"]
    assert all(item["advisory_only"] is True for item in report["Improvement Plan"])
    assert report["Evolution Metrics"]["trajectory"] in {"Improving", "Stable", "Regressing", "Unexpectedly Changing"}
    assert report["Reflection Memory Updates"]["duplicates_episodic_memory"] is False
    assert report["Self Assessment"]["recommendations_actionable"] is True


def test_reflection_memory_compares_current_and_previous_reflections():
    engine = ReflectionEngine()
    first = engine.reflect(
        episode={
            "episode_id": "episode:first",
            "execution_id": "exec:first",
            "episode_status": "CLOSED",
            "episode_outcome": "FAILURE",
            "episode_summary": "FAILURE: first reflection.",
            "statistics": {"object_count": 1, "reasoning_count": 1, "failure_count": 1},
            "quality": {"episode_quality": 0.2},
        },
        objects=[
            {
                "object_id": "reasoning:first",
                "object_type": "REASONING_STEP",
                "object_confidence": 0.25,
            }
        ],
    )
    second = engine.reflect(
        episode={
            "episode_id": "episode:second",
            "execution_id": "exec:second",
            "episode_status": "CLOSED",
            "episode_outcome": "SUCCESS",
            "episode_summary": "SUCCESS: second reflection.",
            "statistics": {
                "object_count": 2,
                "reasoning_count": 1,
                "evidence_count": 1,
                "truth_count": 1,
            },
            "quality": {"episode_quality": 0.75, "evidence_quality": 0.5, "truth_quality": 0.5},
        },
        objects=[
            {
                "object_id": "evidence:second",
                "object_type": "EVIDENCE",
                "object_confidence": 0.8,
            },
            {
                "object_id": "truth:second",
                "object_type": "TRUTH",
                "object_confidence": 0.85,
            },
        ],
    )

    assert first.reflection_memory_update["memory_size_after_update"] == 1
    assert second.reflection_memory_update["memory_size_after_update"] == 2
    assert second.self_improvement_report["Recurring Patterns"]["previous_reflections_considered"] == 1
    assert second.self_improvement_report["Evolution Metrics"]["historical_reflections_considered"] == 1
    assert engine.report()["self_improvement_reports_created"] == 2
    assert engine.report()["adaptive_learning_signals_created"] >= 2


def test_reflective_synthesis_creates_experience_candidates_and_abstractions():
    bus = UnifiedCognitiveBus()
    publication = bus.publish_many_from_runtime_reports(
        _runtime_reports(),
        execution_id="exec:reflective-synthesis",
    )

    reflection = publication["episode"]["reflection"]
    synthesis = reflection["reflective_synthesis_report"]
    candidate = synthesis["Experience Candidates"][0]

    assert synthesis["REFLECTIVE_SYNTHESIS_REPORT"] is True
    assert synthesis["reflection_constructs_reusable_knowledge"] is True
    assert synthesis["writes_permanent_memory"] is False
    assert synthesis["modifies_world_model"] is False
    assert synthesis["updates_dna_directly"] is False
    assert synthesis["experience_engine_retains_promotion_authority"] is True
    assert candidate["origin_episode"] == publication["episode"]["episode_id"]
    assert candidate["lessons"]
    assert candidate["strategies"]
    assert candidate["generalizations"]
    assert candidate["experience_engine_decides_promotion"] is True
    assert candidate["writes_memory"] is False
    assert "lesson_ids" in candidate["lineage"]
    assert synthesis["Lessons Extracted"]
    assert all(lesson["first_class_cognitive_object"] is True for lesson in synthesis["Lessons Extracted"])
    assert synthesis["Abstractions Created"]
    assert {item["abstraction_level"] for item in synthesis["Abstractions Created"]} >= {
        "Episode",
        "Experience",
        "General Pattern",
        "Strategy",
        "Mental Principle",
        "Cognitive Law",
    }
    assert synthesis["General Principles"]
    assert "Exceptions" in synthesis
    assert synthesis["Transfer Opportunities"]
    assert synthesis["Compression Statistics"]["meaning_preserved"] is True
    assert "Merged Knowledge" in synthesis
    assert "Separated Knowledge" in synthesis
    assert synthesis["Reuse Opportunities"]
    assert synthesis["Knowledge Quality"] >= 0
    assert synthesis["Reflection Contribution"] >= 0


def test_abstraction_registry_preserves_lineage_without_memory_promotion():
    engine = ReflectionEngine()
    reflection = engine.reflect(
        episode={
            "episode_id": "episode:synthesis-registry",
            "execution_id": "exec:synthesis-registry",
            "episode_status": "CLOSED",
            "episode_outcome": "SUCCESS",
            "episode_summary": "SUCCESS: synthesis registry episode.",
            "episode_confidence": 0.8,
            "statistics": {
                "object_count": 3,
                "concept_count": 1,
                "evidence_count": 1,
                "truth_count": 1,
            },
            "quality": {"episode_quality": 0.8, "evidence_quality": 0.4, "truth_quality": 0.4},
            "content": {
                "concept_objects": ["concept:synthesis"],
                "evidence_objects": ["evidence:synthesis"],
                "truth_objects": ["truth:synthesis"],
            },
        },
        objects=[
            {
                "object_id": "concept:synthesis",
                "object_type": "CONCEPT",
                "object_confidence": 0.82,
            },
            {
                "object_id": "evidence:synthesis",
                "object_type": "EVIDENCE",
                "object_confidence": 0.86,
                "evidence_payload": {"reliability": 0.86},
            },
            {
                "object_id": "truth:synthesis",
                "object_type": "TRUTH",
                "object_confidence": 0.9,
            },
        ],
    )

    registry = reflection.abstraction_registry_update
    synthesis = reflection.reflective_synthesis_report

    assert registry["registry_enabled"] is True
    assert registry["stores_permanent_memory"] is False
    assert registry["complete_lineage_preserved"] is True
    assert registry["lineage"]["episode_id"] == ["episode:synthesis-registry"]
    assert registry["abstractions"]
    assert registry["general_principles"]
    assert registry["lessons"]
    assert registry["transfer_rules"]
    assert registry["knowledge_compression_results"]["meaning_preserved"] is True
    assert synthesis["Experience Candidates"][0]["governance_required"] is True
    assert engine.report()["reflective_synthesis_reports_created"] == 1
    assert engine.report()["experience_candidates_created"] == 1
    assert engine.report()["abstractions_created"] >= 6
    assert engine.report()["lessons_extracted"] >= 1


def test_reflection_intelligence_report_prepares_governance_and_lifelong_learning():
    bus = UnifiedCognitiveBus()
    publication = bus.publish_many_from_runtime_reports(
        _runtime_reports(),
        execution_id="exec:reflection-intelligence",
    )

    reflection = publication["episode"]["reflection"]
    report = reflection["reflection_intelligence_report"]

    assert report["REFLECTION_INTELLIGENCE_REPORT"] is True
    assert report["reflection_is_permanent_cycle_stage"] is True
    assert report["reflection_advises_governance_only"] is True
    assert report["does_not_bypass_executive_governance"] is True
    assert report["does_not_perform_architectural_evolution"] is True
    assert report["Recommendation Statistics"]["executive_recommendations"] >= 1
    assert "Recommendation Validation" in report
    assert report["Learning Trajectories"]
    assert report["Learning Trajectories"][0]["trajectory"][-1]["stage"] == "DNA Adaptation"
    assert report["Knowledge Preservation Candidates"]
    assert "Knowledge Forgetting Candidates" in report
    assert report["Behavioral Evolution"]["behavioral_trend"] in {"Improving", "Stable", "Regressing", "Unexpectedly Changing"}
    assert report["Cognitive Maturity"]["overall_cognitive_maturity"] >= 0
    assert report["Reflection Confidence"]["overall_reflection_confidence"] >= 0
    assert "Trend Analysis" in report
    assert report["Adaptive Signals"]
    assert report["Executive Recommendations"]
    assert report["World Model Preparation"]["forwards_raw_episodes"] is False
    assert report["World Model Preparation"]["world_model_write_authorized"] is False
    assert report["DNA Preparation"]["modifies_dna_directly"] is False
    assert report["DNA Preparation"]["executive_governance_and_dna_decide"] is True
    assert report["Meta-Cognitive Feedback"]["meta_cognition_should_evaluate"] is True
    assert report["Reflection Knowledge Graph Statistics"]["node_count"] >= 1
    assert report["Reflection Knowledge Graph Statistics"]["edge_count"] >= 1
    assert report["Executive Feedback"]["Strength Reports"]


def test_reflection_intelligence_tracks_confidence_and_graph_across_lifetime():
    engine = ReflectionEngine()
    first = engine.reflect(
        episode={
            "episode_id": "episode:intel-first",
            "execution_id": "exec:intel-first",
            "episode_status": "CLOSED",
            "episode_outcome": "FAILURE",
            "episode_summary": "FAILURE: intelligence first.",
            "episode_confidence": 0.3,
            "statistics": {"object_count": 1, "reasoning_count": 1, "failure_count": 1},
            "quality": {"episode_quality": 0.2},
        },
        objects=[
            {
                "object_id": "reasoning:intel-first",
                "object_type": "REASONING_STEP",
                "object_confidence": 0.25,
            }
        ],
    )
    second = engine.reflect(
        episode={
            "episode_id": "episode:intel-second",
            "execution_id": "exec:intel-second",
            "episode_status": "CLOSED",
            "episode_outcome": "SUCCESS",
            "episode_summary": "SUCCESS: intelligence second.",
            "episode_confidence": 0.85,
            "statistics": {"object_count": 2, "evidence_count": 1, "truth_count": 1},
            "quality": {"episode_quality": 0.8, "evidence_quality": 0.5, "truth_quality": 0.5},
            "content": {"evidence_objects": ["evidence:intel-second"], "truth_objects": ["truth:intel-second"]},
        },
        objects=[
            {
                "object_id": "evidence:intel-second",
                "object_type": "EVIDENCE",
                "object_confidence": 0.86,
            },
            {
                "object_id": "truth:intel-second",
                "object_type": "TRUTH",
                "object_confidence": 0.9,
            },
        ],
    )

    assert first.reflection_intelligence_report["Reflection Confidence"]["trust_direction"] == "initial"
    assert second.reflection_intelligence_report["Reflection Confidence"]["previous_average_confidence"] >= 0
    assert second.reflection_intelligence_report["Learning Trajectories"][0]["historical_reflections_considered"] == 1
    assert any(
        node["id"] == first.reflection_id
        for node in second.reflection_knowledge_graph["nodes"]
    )
    assert engine.report()["reflection_intelligence_reports_created"] == 2
    assert engine.report()["executive_recommendations_created"] >= 2
    assert engine.report()["adaptive_signals_created"] >= 10
    assert engine.report()["reflection_knowledge_graph_nodes"] >= 2
