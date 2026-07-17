from runtime.execution import (
    ExecutableIntelligenceEngine,
    ExecutionMemory,
    LocalizedExecutionPlanner,
    ObjectGroundingEngine,
    PrimitiveSelector,
    ProgramCompiler,
    ProgramSynthesisEngine,
    ProgramValidator,
    ResidualLocalizationEngine,
    ResidualRepairEngine,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def test_object_grounding_identifies_local_target_and_preserves_lineage():
    report = ObjectGroundingEngine().ground(
        [[1, 1, 0], [0, 0, 2]],
        semantic_intent="duplicate_object",
        candidate={"operation": "duplicate_object"},
    )

    assert report["object_grounding_operational"] is True
    assert len(report["candidate_objects"]) == 2
    assert report["target_objects"][0]["object_id"] == "obj_1"
    assert report["transformation_scope"] == "local"
    assert report["identity_lineage"]["obj_1"]["lineage_preserved"] is True


def test_localized_planning_and_primitive_selection_are_object_centric():
    grounding = ObjectGroundingEngine().ground(
        [[1, 1, 0], [0, 0, 0]],
        semantic_intent="duplicate_object",
        candidate={"operation": "duplicate_object"},
    )
    plan = LocalizedExecutionPlanner().plan("duplicate_object", grounding)
    primitives = PrimitiveSelector().select("duplicate_object", plan)

    assert plan["localized_execution_planning_operational"] is True
    assert plan["execution_scope"] == "local"
    assert plan["localized_operations"][0]["target_object"] == "obj_1"
    assert primitives["selected_primitives"] == ["duplicate", "preserve"]
    assert primitives["primitive_family"] == "duplication_primitives"


def test_program_synthesis_compilation_and_validation_require_governance():
    grounding = ObjectGroundingEngine().ground(
        [[1, 1]],
        semantic_intent="preserve_color_mapping",
        candidate={"operation": "replace_color"},
    )
    plan = LocalizedExecutionPlanner().plan("replace_color", grounding)
    primitive_selection = PrimitiveSelector().select("replace_color", plan)
    synthesis = ProgramSynthesisEngine().synthesize(
        semantic_intent="preserve_color_mapping",
        validated_candidate={
            "operation": "replace_color",
            "program": {
                "steps": [
                    {
                        "operation": "replace_color",
                        "parameters": {"color_mapping": {1: 2}},
                    }
                ]
            },
        },
        execution_plan=plan,
        primitive_selection=primitive_selection,
    )
    compiled = ProgramCompiler().compile(
        semantic_intent="preserve_color_mapping",
        execution_plan=plan,
        synthesized_program=synthesis,
    )
    valid = ProgramValidator().validate(compiled, grounding_report=grounding)
    blocked = ProgramValidator().validate(
        compiled,
        grounding_report=grounding,
        governance_context={"identity_governance": "BLOCKED"},
    )

    assert synthesis["program_synthesis_operational"] is True
    assert compiled["compiled_successfully"] is True
    assert compiled["compiled_program"]["real_execution_authorized"] is False
    assert valid["validation_success"] is True
    assert valid["governance_decision"] == "ALLOW_GOVERNED_EXECUTION"
    assert blocked["validation_success"] is False
    assert "identity_governance" in blocked["validation_blockers"]


def test_residual_localization_generates_localized_repair_proposals():
    residual = ResidualLocalizationEngine().localize(
        [[1, 1], [0, 0]],
        [[2, 2], [0, 0]],
    )
    repair = ResidualRepairEngine().repair(residual)

    assert residual["residual_localization_operational"] is True
    assert residual["residual_count"] == 2
    assert residual["missing_primitives"] == ["recolor"]
    assert residual["residual_regions"][0]["cell_count"] == 2
    assert repair["residual_repair_operational"] is True
    assert repair["generated_repairs"] == 1
    assert repair["repair_proposals"][0]["operation"] == "add_missing_recolor_step"


def test_executable_intelligence_engine_runs_full_governed_pipeline_without_real_execution():
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    result = engine.run(
        semantic_intent="preserve_color_mapping",
        operation="replace_color",
        input_grid=[[1, 1], [0, 0]],
        predicted_output=[[1, 1], [0, 0]],
        target_grid=[[2, 2], [0, 0]],
        validated_candidate={
            "operation": "replace_color",
            "source": "semantic_compiler",
            "program": {
                "steps": [
                    {
                        "operation": "replace_color",
                        "parameters": {"color_mapping": {1: 2}},
                    }
                ]
            },
        },
    )

    report = result["EXECUTABLE_INTELLIGENCE_REPORT"]
    recommendation = result["final_execution_recommendation"]

    assert report["semantic_intent_operational"] is True
    assert report["object_grounding_operational"] is True
    assert report["program_compilation_operational"] is True
    assert report["program_validation_operational"] is True
    assert report["residual_localization_operational"] is True
    assert report["residual_repair_operational"] is True
    assert report["execution_adaptation_operational"] is True
    assert report["execution_memory_operational"] is True
    assert report["governed_execution_operational"] is True
    assert report["knowledge_feedback_operational"] is True
    assert report["compiled_programs"] == 1
    assert report["validated_programs"] == 1
    assert report["generated_repairs"] == 1
    assert report["execution_adaptations"] == 1
    assert report["real_execution_performed"] is False
    assert recommendation["execution_mode"] == "sandbox"


def test_executable_intelligence_report_is_compact_and_rendered():
    renderer = DeterministicFinalReportRenderer()
    rendered = renderer.render({
        "EXECUTABLE_INTELLIGENCE_REPORT": {
            "semantic_intent_operational": True,
            "object_grounding_operational": True,
            "localized_execution_planning_operational": True,
            "primitive_selection_operational": True,
            "program_synthesis_operational": True,
            "program_compilation_operational": True,
            "program_validation_operational": True,
            "residual_localization_operational": True,
            "residual_repair_operational": True,
            "execution_adaptation_operational": True,
            "execution_memory_operational": True,
            "governed_execution_operational": True,
            "knowledge_feedback_operational": True,
            "executable_concepts": 1,
            "localized_operations": 1,
            "target_objects": 1,
            "synthesized_programs": 1,
            "compiled_programs": 1,
            "validated_programs": 1,
            "residual_regions": 1,
            "generated_repairs": 1,
            "execution_success_rate": 0.5,
            "execution_adaptations": 1,
            "execution_feedback": "AVAILABLE",
        }
    })

    assert "EXECUTABLE INTELLIGENCE REPORT" in rendered
    assert "Object Grounding Operational: TRUE" in rendered
    assert "Generated Repairs: 1" in rendered
    assert "repair_proposals" not in rendered
    assert renderer.validate(rendered) == []
