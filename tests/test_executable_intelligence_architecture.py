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
from runtime.arena import ArenaMemory, CognitiveCandidateArena
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _proposal(source, operation, steps, confidence=0.9, **extra):
    return {
        "source": source,
        "hypothesis_id": f"hypothesis:{source}:{operation}",
        "intent": operation,
        "operation": operation,
        "program": {"step_count": len(steps), "steps": steps},
        "source_confidence": confidence,
        "semantic_support": extra.pop("semantic_support", 0.9),
        "truth_support": extra.pop("truth_support", 0.9),
        "context_support": extra.pop("context_support", 0.9),
        "dependency_support": extra.pop("dependency_support", 0.9),
        "identity_support": extra.pop("identity_support", 0.9),
        "localization_support": extra.pop("localization_support", 0.9),
        **extra,
    }


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
    assert report["object_grounding_infrastructure_operational"] is True
    assert report["object_grounding_produced"] is True
    assert report["object_grounding_flow_state"] == "OBJECT_GROUNDING_PRODUCED"
    assert report["object_grounding_blocked_stage"] == "none"
    assert report["validation_probe_grounding_context_received"] is False
    assert report["object_grounding_input_source"] == "runtime_input_grid"
    assert report["grounded_target_object_count"] == 1
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


def test_executable_intelligence_consumes_arena_validation_probe_without_prediction_authority():
    arena_report = CognitiveCandidateArena(memory=ArenaMemory()).run(
        [
            _proposal(
                "semantic_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
            ),
            _proposal(
                "rule_engine",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
                confidence=0.6,
            ),
        ],
        input_grid=[[1, 1], [0, 0]],
        target_grid=[[2, 2], [2, 2]],
    )

    result = ExecutableIntelligenceEngine(memory=ExecutionMemory()).run(
        semantic_intent="replace_color",
        operation="replace_color",
        input_grid=[[1, 1], [0, 0]],
        predicted_output=[[2, 2], [0, 0]],
        target_grid=[[2, 2], [2, 2]],
        arena_execution_recommendation=arena_report["execution_recommendation"],
    )

    report = result["EXECUTABLE_INTELLIGENCE_REPORT"]
    recommendation = result["final_execution_recommendation"]

    assert arena_report["selection_state"] == "NO_SAFE_WINNER"
    assert arena_report["winner_selected_from_evidence"] is False
    assert arena_report["arena_to_compiled_bridge_state"] == (
        "VALIDATION_PROBE_AVAILABLE"
    )
    assert report["validation_probe_consumed"] is True
    assert report["validation_probe_compiler_participation"] == 1
    assert report["validation_probe_admission_state"] == "VALIDATION_PROBE_COMPILED"
    assert report["validation_probe_authority"] == "SANDBOX_VALIDATION_ONLY"
    assert report["compiled_programs"] == 1
    assert report["compiled_execution_programs"] == 0
    assert report["validation_probe_compiled_programs"] == 1
    assert report["compiler_participation"] == 1
    assert report["validation_probe_sandbox_validation_invoked"] is True
    assert report["validation_probe_validation_result_captured"] is True
    assert report["validation_probe_comparable_output_captured"] is True
    assert report["validation_probe_evidence_acceptance_evaluated"] is True
    assert report["validation_probe_evidence_acceptance_state"] == "ACCEPTED"
    assert report["validation_probe_evidence_insufficiency_cause"] == "NONE"
    assert report["validation_probe_required_evidence"] == (
        "evidence_contract_satisfied"
    )
    assert report["validation_probe_recommended_validation_action"] == (
        "retain_validation_evidence"
    )
    assert report["compiled_to_validated_probe_state"] == "VALIDATION_PROBE_VALIDATED"
    assert recommendation["execution_mode"] == "sandbox_validation_only"
    assert recommendation["validation_probe_consumed"] is True
    assert recommendation["validation_probe_authority"] == "SANDBOX_VALIDATION_ONLY"
    assert recommendation["validation_probe_evidence_acceptance_state"] == "ACCEPTED"


def test_validation_probe_uses_arena_grounding_context_when_runtime_input_is_empty():
    arena_report = CognitiveCandidateArena(memory=ArenaMemory()).run(
        [
            _proposal(
                "semantic_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
            ),
        ],
        input_grid=[[1, 1], [0, 0]],
        target_grid=[[2, 2], [2, 2]],
        analysis_only=True,
    )

    result = ExecutableIntelligenceEngine(memory=ExecutionMemory()).run(
        semantic_intent="replace_color",
        operation="replace_color",
        input_grid=[],
        predicted_output=[],
        target_grid=[[2, 2], [2, 2]],
        arena_execution_recommendation=arena_report["execution_recommendation"],
    )

    report = result["EXECUTABLE_INTELLIGENCE_REPORT"]

    assert report["object_grounding_infrastructure_operational"] is True
    assert report["object_grounding_produced"] is True
    assert report["object_grounding_flow_state"] == "OBJECT_GROUNDING_PRODUCED"
    assert report["object_grounding_blocked_stage"] == "none"
    assert report["validation_probe_grounding_context_received"] is True
    assert report["validation_probe_grounding_context_input_available"] is True
    assert report["object_grounding_input_source"] == (
        "validation_probe_grounding_context"
    )
    assert report["grounded_target_object_count"] == 1
    assert report["validation_probe_consumed"] is True
    assert report["validation_probe_compiler_participation"] == 1
    assert report["validation_probe_sandbox_validation_invoked"] is True
    assert report["validation_probe_validation_result_captured"] is True
    assert report["validation_probe_evidence_acceptance_evaluated"] is True
    assert report["validation_probe_evidence_acceptance_state"] == "ACCEPTED"
    assert report["validation_probe_evidence_insufficiency_cause"] == "NONE"
    assert report["validation_probe_required_evidence"] == (
        "evidence_contract_satisfied"
    )
    assert report["compiled_to_validated_probe_state"] == "VALIDATION_PROBE_VALIDATED"


def test_validation_probe_without_arena_grounding_context_remains_insufficient():
    result = ExecutableIntelligenceEngine(memory=ExecutionMemory()).run(
        semantic_intent="replace_color",
        operation="replace_color",
        input_grid=[],
        predicted_output=[],
        target_grid=[[2, 2], [2, 2]],
        arena_execution_recommendation={
            "validation_probe_candidate": _proposal(
                "semantic_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
            ),
            "validation_probe_mode": "sandbox_validation_only",
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
        },
    )

    report = result["EXECUTABLE_INTELLIGENCE_REPORT"]

    assert report["object_grounding_infrastructure_operational"] is True
    assert report["object_grounding_produced"] is False
    assert report["object_grounding_flow_state"] == "GROUNDING_INPUT_MISSING"
    assert report["object_grounding_blocked_stage"] == (
        "validation_probe_grounding_context"
    )
    assert report["object_grounding_flow_action"] == (
        "forward_validation_probe_grounding_context"
    )
    assert report["validation_probe_grounding_context_received"] is False
    assert report["validation_probe_grounding_context_input_available"] is False
    assert report["object_grounding_input_source"] == "missing_input_grid"
    assert report["grounded_target_object_count"] == 0
    assert report["validation_probe_evidence_acceptance_state"] == "INSUFFICIENT"
    assert report["validation_probe_evidence_insufficiency_cause"] == (
        "missing_object_grounding"
    )
    assert report["validation_probe_required_evidence"] == (
        "grounded_target_object_evidence"
    )
    assert report["validation_probe_recommended_validation_action"] == (
        "select_object_grounded_validation_task"
    )
    assert report["compiled_to_validated_probe_state"] == (
        "SANDBOX_VALIDATION_EVIDENCE_INSUFFICIENT"
    )


def test_executable_intelligence_report_is_compact_and_rendered():
    renderer = DeterministicFinalReportRenderer()
    rendered = renderer.render({
        "EXECUTABLE_INTELLIGENCE_REPORT": {
            "semantic_intent_operational": True,
            "object_grounding_operational": True,
            "object_grounding_infrastructure_operational": True,
            "object_grounding_produced": True,
            "grounded_target_object_count": 1,
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
            "compiled_execution_programs": 0,
            "validation_probe_compiled_programs": 1,
            "validated_programs": 1,
            "validation_probe_consumed": True,
            "validation_probe_compiler_participation": 1,
            "validation_probe_admission_state": "VALIDATION_PROBE_COMPILED",
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "validation_probe_sandbox_validation_invoked": True,
            "validation_probe_validation_result_captured": True,
            "validation_probe_comparable_output_captured": True,
            "validation_probe_evidence_acceptance_evaluated": True,
            "validation_probe_evidence_acceptance_state": "ACCEPTED",
            "validation_probe_evidence_insufficiency_cause": "NONE",
            "validation_probe_required_evidence": "evidence_contract_satisfied",
            "validation_probe_recommended_validation_action": "retain_validation_evidence",
            "compiled_to_validated_probe_state": "VALIDATION_PROBE_VALIDATED",
            "residual_regions": 1,
            "generated_repairs": 1,
            "execution_success_rate": 0.5,
            "execution_adaptations": 1,
            "execution_feedback": "AVAILABLE",
        }
    })

    assert "EXECUTABLE INTELLIGENCE REPORT" in rendered
    assert "Object Grounding Operational: TRUE" in rendered
    assert "Object Grounding Infrastructure Operational: TRUE" in rendered
    assert "Object Grounding Produced: TRUE" in rendered
    assert "Grounded Target Object Count: 1" in rendered
    assert "Program Validation Infrastructure Available: TRUE" in rendered
    assert "Program Validation Invoked: TRUE" in rendered
    assert "Program Validation Success Count: 1" in rendered
    assert "Program Validation Semantics State: VALIDATION_SEMANTICS_CLEAR" in rendered
    assert "Program Validation Contract State: VALIDATION_CONTRACT_CLEAR" in rendered
    assert "Compiled Execution Programs: 0" in rendered
    assert "Validation Probe Compiled Programs: 1" in rendered
    assert "Validation Probe Consumed: TRUE" in rendered
    assert "Validation Probe Compiler Participation: 1" in rendered
    assert "Validation Probe Admission State: VALIDATION_PROBE_COMPILED" in rendered
    assert "Validation Probe Authority: SANDBOX_VALIDATION_ONLY" in rendered
    assert "Validation Probe Sandbox Validation Invoked: TRUE" in rendered
    assert "Validation Probe Result Captured: TRUE" in rendered
    assert "Validation Probe Comparable Output Captured: TRUE" in rendered
    assert "Validation Probe Evidence Acceptance Evaluated: TRUE" in rendered
    assert "Validation Probe Evidence Acceptance State: ACCEPTED" in rendered
    assert "Validation Probe Evidence Insufficiency Cause: NONE" in rendered
    assert (
        "Validation Probe Required Evidence: evidence_contract_satisfied"
        in rendered
    )
    assert (
        "Validation Probe Recommended Validation Action: retain_validation_evidence"
        in rendered
    )
    assert "Compiled To Validated Probe State: VALIDATION_PROBE_VALIDATED" in rendered
    assert "Generated Repairs: 1" in rendered
    assert "Execution Success Basis: Not Available / 1" in rendered
    assert "Execution Attempt Count: 1" in rendered
    assert "repair_proposals" not in rendered
    assert renderer.validate(rendered) == []


def test_executable_intelligence_report_identifies_validation_semantics_bottleneck():
    renderer = DeterministicFinalReportRenderer()
    rendered = renderer.render({
        "EXECUTABLE_INTELLIGENCE_REPORT": {
            "program_validation_operational": True,
            "compiled_programs": 1,
            "validated_programs": 0,
        }
    })

    assert "Program Validation Infrastructure Available: TRUE" in rendered
    assert "Program Validation Invoked: TRUE" in rendered
    assert "Program Validation Success Count: 0" in rendered
    assert (
        "Program Validation Semantics State: VALIDATION_SEMANTICS_BOTTLENECK"
        in rendered
    )
    assert (
        "Program Validation Contract State: "
        "EVIDENCE_ACCEPTANCE_CONTRACT_UNSATISFIED"
    ) in rendered
    assert (
        "Program Validation Semantics Question: "
        "what_constitutes_acceptable_evidence"
    ) in rendered
