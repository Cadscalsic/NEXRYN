from runtime.semantic.executable_coverage import ExecutableCoverageTracker
from runtime.semantic.executable_semantics import ExecutableSemanticIntelligence
from runtime.semantic.semantic_operation_mapper import SemanticOperationMapper
from runtime.semantic_routing import CognitiveContextRouter, SemanticIntentRouter
from runtime.memory.transformation_memory import TransformationMemory
from runtime.reasoning.transformation_synthesis_engine import TransformationSynthesisEngine
from runtime.transformation_compilation import SemanticToTransformationCompiler
from runtime.transforms.primitive_executor import PrimitiveExecutor


def test_executable_semantic_intelligence_classifies_concepts():
    executable = ExecutableSemanticIntelligence().evaluate("replication")
    non_executable = ExecutableSemanticIntelligence().evaluate("context_support")

    assert executable["is_executable"] is True
    assert executable["required_primitives"] == ["duplicate_object"]
    assert executable["execution_path"] == "object_duplication"
    assert executable["coverage_state"] == "EXECUTABLE"
    assert non_executable["is_executable"] is False
    assert non_executable["coverage_state"] == "NON_EXECUTABLE_SEMANTIC_CONTEXT"


def test_semantic_operation_mapper_maps_concepts_to_operations():
    report = SemanticOperationMapper().map("symbolic_remapping")

    assert report["operation_name"] == "remap_symbols"
    assert report["primitive_family"] == "symbolic_operations"
    assert report["confidence"] > 0.0


def test_executable_coverage_tracks_supported_and_unsupported_concepts():
    report = ExecutableCoverageTracker().evaluate([
        "replication",
        "symmetry_preservation",
        "growth",
        "context_support",
    ])

    assert report["total_concepts"] == 4
    assert report["executable_concepts"] == 3
    assert report["coverage_percentage"] == 75.0
    assert report["unsupported_concepts"] == ["context_support"]


def test_router_outputs_executable_semantic_proposals():
    report = SemanticIntentRouter().route(
        detected_concepts=["color_preservation", "replication", "context_support"],
        runtime_context={
            "truth_governance_report": {"validation_success": True},
            "identity_governance_report": {"validation_success": True},
            "contextual_truth_report": {"validation_success": True},
            "dependency_graph_validation": {"validation_success": True},
        },
    )

    proposals = {
        proposal["concept"]: proposal
        for proposal in report["execution_proposals"]
    }

    assert report["semantic_intent_routing_success"] is True
    assert proposals["color_preservation"]["semantic_intent"] == "preserve_color_mapping"
    assert proposals["color_preservation"]["operation_family"] == "color_operations"
    assert proposals["color_preservation"]["intent_ready"] is True
    assert proposals["replication"]["semantic_intent"] == "duplicate_object"
    assert "context_support" in report["unrouted_concepts"]


def test_router_governance_blocks_execution_pipeline_entry():
    report = SemanticIntentRouter().route(
        detected_concepts=["replication"],
        runtime_context={
            "truth_governance_report": {"validation_success": False},
        },
    )

    assert report["semantic_intent_routing_success"] is False
    assert report["execution_intents"] == []
    assert report["blocked_concepts"][0]["blocked_reason"] == "governance_rejected"


def test_routes_rotation_concepts_and_tools_to_execution_intent():
    report = SemanticIntentRouter().route(
        detected_concepts=[
            "rotation_reflection",
            "rotation",
            "reflection",
            "orientation_change",
        ],
        runtime_context={
            "rotation_signature": "clockwise_90",
            "tool_selection_report": {
                "enabled_tools": [
                    "semantic_to_transformation_compiler",
                    "rotation_execution",
                    "reflection_execution",
                ],
            },
        },
    )

    intents = report["execution_intents"]
    intent_names = {intent["intent"] for intent in intents}

    assert report["semantic_intent_routing_success"] is True
    assert "rotation_reflection" in intent_names
    assert intents[0]["operation"] == "rotate_clockwise_90"
    assert "rotation_execution" in intents[0]["matched_tools"]


def test_compiler_uses_semantic_router_for_duplication_candidate():
    router_report = SemanticIntentRouter().route(
        detected_concepts=["replication"],
        runtime_context={"enabled_tools": ["semantic_to_transformation_compiler"]},
    )

    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 0, 0],
            [0, 0, 0],
        ],
        output_grid=[
            [1, 0, 1],
            [0, 0, 0],
        ],
        detected_concepts=["replication"],
        execution_intents=router_report["execution_intents"],
        semantic_intent_report=router_report,
    )

    step = report["compiled_program"]["steps"][0]

    assert report["semantic_to_transformation_compilation_success"] is True
    assert report["compiler_triggered_by_intents"] is True
    assert step["operation"] == "duplicate_object"
    assert report["validation"]["exact_match"] is True


def test_compiler_uses_execution_intent_for_rotation():
    router_report = SemanticIntentRouter().route(
        detected_concepts=["rotation", "orientation_change"],
        runtime_context={
            "rotation_signature": "clockwise_90",
            "enabled_tools": ["rotation_execution"],
        },
    )

    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 0],
            [0, 0],
        ],
        output_grid=[
            [0, 1],
            [0, 0],
        ],
        detected_concepts=["rotation", "orientation_change"],
        execution_intents=router_report["execution_intents"],
        semantic_intent_report=router_report,
    )

    step = report["compiled_program"]["steps"][0]

    assert report["semantic_to_transformation_compilation_success"] is True
    assert report["compiler_triggered_by_intents"] is True
    assert report["semantic_intent_routing_report"]["semantic_intent_routing_success"] is True
    assert report["selected_intent"] == "rotation"
    assert step["operation"] == "rotate"
    assert step["parameters"]["degrees"] == 270
    assert report["validation"]["exact_match"] is True


def test_compiler_reports_intent_trigger_when_no_supported_program_matches():
    router_report = SemanticIntentRouter().route(
        detected_concepts=["hole_removal", "topology_repair"],
        runtime_context={"enabled_tools": ["transformation_execution"]},
    )

    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 1],
            [1, 1],
        ],
        output_grid=[
            [1, 1],
            [1, 1],
        ],
        detected_concepts=["hole_removal", "topology_repair"],
        execution_intents=router_report["execution_intents"],
        semantic_intent_report=router_report,
    )

    assert report["semantic_to_transformation_compilation_success"] is False
    assert report["compiler_triggered_by_intents"] is True
    assert report["failure_reason"] == "no_supported_compiler_for_execution_intents"
    assert report["execution_intents"][0]["intent"] == "topology_repair"


def test_router_builds_bridge_execution_intents_from_nested_semantics():
    report = SemanticIntentRouter().route(
        runtime_context={
            "semantic_concepts": [
                {"concept": "Bridge Creation"},
                {"concept": "component-connection"},
                {"concept": "connectivity_change"},
                {"concept": "topology_change"},
            ],
            "tool_selection_report": {
                "enabled_tools": [
                    "semantic_to_transformation_compiler",
                    "transformation_execution",
                ],
            },
        },
    )

    intents = report["execution_intents"]
    intent_names = {intent["intent"] for intent in intents}
    operations = {intent["operation"] for intent in intents}

    assert report["semantic_intent_routing_success"] is True
    assert "component_connection" in intent_names
    assert "connect_components" in operations
    assert report["execution_intent_count"] >= 1
    assert report["unrouted_concepts"] == []


def test_compiler_uses_bridge_execution_intent_for_component_connection():
    router_report = SemanticIntentRouter().route(
        detected_concepts=[
            "bridge_creation",
            "component_connection",
            "connectivity_change",
        ],
        runtime_context={
            "tool_selection_report": {
                "enabled_tools": [
                    "semantic_to_transformation_compiler",
                    "transformation_execution",
                ],
            },
        },
    )

    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 0, 1],
            [0, 0, 0],
            [0, 0, 0],
        ],
        output_grid=[
            [1, 1, 1],
            [0, 0, 0],
            [0, 0, 0],
        ],
        detected_concepts=["bridge_creation", "component_connection"],
        execution_intents=router_report["execution_intents"],
        semantic_intent_report=router_report,
    )

    step = report["compiled_program"]["steps"][0]

    assert report["semantic_to_transformation_compilation_success"] is True
    assert report["compiler_triggered_by_intents"] is True
    assert step["operation"] == "connect_components"
    assert report["validation"]["exact_match"] is True


def test_cognitive_context_router_compresses_overloaded_concepts_to_execution_relevance():
    concepts = [
        "color_preservation",
        "density_preservation",
        "directional_motion",
        "growth",
        "object_identity_preservation",
        "position_preservation",
        "propagation",
        "replication",
        "shape_preservation",
        "size_preservation",
        "symbolic_remapping",
        "symmetry_preservation",
        "symmetry_reasoning",
        "topological_change",
        "topological_growth",
        "bridge_creation",
        "component_connection",
        "connectivity_change",
    ]

    report = CognitiveContextRouter().route(concepts)

    assert report["context_overload_detected"] is True
    assert report["context_routing_status"] == "COMPRESSED"
    assert report["failure_causes"] == ["routing_overload"]
    assert report["input_concept_count"] == 18
    assert report["routed_concept_count"] <= 6
    assert "bridge_creation" in report["routed_concepts"]
    assert "component_connection" in report["routed_concepts"]
    assert "object_identity_preservation" not in report["routed_concepts"]


def test_synthesis_routes_overloaded_context_before_execution_intents():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[
            [1, 0, 1],
            [0, 0, 0],
            [0, 0, 0],
        ],
        output_grid=[
            [1, 1, 1],
            [0, 0, 0],
            [0, 0, 0],
        ],
        detected_concepts=[
            "color_preservation",
            "density_preservation",
            "directional_motion",
            "growth",
            "object_identity_preservation",
            "position_preservation",
            "propagation",
            "replication",
            "shape_preservation",
            "size_preservation",
            "symbolic_remapping",
            "symmetry_preservation",
            "symmetry_reasoning",
            "topological_change",
            "topological_growth",
            "bridge_creation",
            "component_connection",
            "connectivity_change",
        ],
        runtime_context={
            "tool_selection_report": {
                "enabled_tools": [
                    "semantic_to_transformation_compiler",
                    "transformation_execution",
                ],
            },
        },
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    context = synthesis["context_routing_report"]
    proposals = synthesis["candidate_proposal_report"]
    router = synthesis["semantic_intent_routing_report"]
    compiler = synthesis["semantic_to_transformation_compilation_report"]

    assert context["context_overload_detected"] is True
    assert context["routed_concept_count"] < context["input_concept_count"]
    assert "bridge_creation" in context["routed_concepts"]
    assert proposals["proposal_phase_entered"] is True
    assert proposals["proposal_count"] >= 1
    assert "semantic_to_transformation_compiler" in {
        proposal["source"]
        for proposal in proposals["candidate_proposals"]
    }
    assert router["semantic_intent_routing_success"] is True
    assert router["execution_intent_count"] > 0
    assert compiler["compiler_triggered_by_intents"] is True


def test_synthesis_propagates_semantic_execution_intents_to_compiler():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[
            [1, 0],
            [0, 0],
        ],
        output_grid=[
            [0, 1],
            [0, 0],
        ],
        detected_concepts=["rotation", "orientation_change"],
        runtime_context={
            "rotation_signature": "clockwise_90",
            "tool_selection_report": {
                "enabled_tools": [
                    "semantic_to_transformation_compiler",
                    "rotation_execution",
                ],
            },
        },
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    router = synthesis["semantic_intent_routing_report"]
    compiler = synthesis["semantic_to_transformation_compilation_report"]

    assert router["semantic_intent_routing_success"] is True
    assert {
        intent["intent"]
        for intent in router["execution_intents"]
    }.intersection({"rotation", "rotation_reflection"})
    assert compiler["compiler_triggered_by_intents"] is True
    assert compiler["semantic_to_transformation_compilation_success"] is True
    assert synthesis["selected_program"]["steps"][0]["operation"] == "rotate"
    assert synthesis["transformation_accuracy"] == 1.0
