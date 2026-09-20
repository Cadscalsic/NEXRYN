import json
from copy import deepcopy

from runtime.adaptive_reuse import AdaptiveReuseLayer
from runtime.adaptive_reuse.episode_memory import EpisodeMemory
from runtime.adaptive_reuse.experience_index import ExperienceIndex
from runtime.adaptive_reuse.program_reuse_engine import ProgramReuseEngine
from runtime.adaptive_reuse.strategy_retriever import StrategyRetriever
from runtime.cache.cache_manager import CacheManager
from runtime.cognition.adaptive_reuse_engine import AdaptiveReuseEngine
from runtime.execution import ExecutableIntelligenceEngine, ExecutionFeedbackEngine, ExecutionMemory
from tests.test_e4_phase2_production_executor_grant_consumption import (
    _arena,
    _budget,
    _candidate,
    _grant,
    _qualification,
)


class _EmptyMemory:
    def load(self):
        return []


def _runtime_context():
    return {
        "concept": "replace_color",
        "winner_hypothesis": {
            "type": "replace_color",
            "operation": "replace_color",
        },
        "semantic_graph": {
            "concept_nodes": [{"concept": "replace_color"}],
        },
        "execution_plan": {
            "nodes": [{"operation": "replace_color"}],
        },
        "truth_commitments": [],
        "task_signature": "e5_phase2_real_runtime_color_task",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_ready": True,
        "semantic_drift": 0.0,
        "effective_contradiction": 0.0,
        "context_compatibility": 1.0,
        "dependency_compatibility": 1.0,
        "world_model_compatibility": 1.0,
        "truth_integrity_preserved": True,
    }


def _isolated_layer(storage_root):
    experiences = storage_root / "experiences"
    experiences.mkdir(parents=True, exist_ok=True)
    index = ExperienceIndex(storage_root)
    return AdaptiveReuseLayer(
        experience_index=index,
        strategy_retriever=StrategyRetriever(
            experience_index=index,
            strategy_memory=_EmptyMemory(),
        ),
        program_reuse_engine=ProgramReuseEngine(_EmptyMemory()),
        episode_memory=EpisodeMemory(experiences),
    )


def _real_runtime_engine(storage_root):
    return AdaptiveReuseEngine(
        cache_manager=CacheManager(cache_dir=storage_root / "cache", auto_migrate=False),
        experience_reuse_layer=_isolated_layer(storage_root),
    )


def _persist_experience(storage_root, experience):
    path = storage_root / "experiences" / f"{experience['experience_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(experience, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _source_experience(storage_root):
    source = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = _candidate()
    grant = _grant(
        engine=source,
        candidate=candidate,
        run_id="run_e5_phase2_source",
        budget=_budget(run_id="run_e5_phase2_source"),
    )
    source_run = source.run(
        semantic_intent="replace_color",
        operation="replace_color",
        input_grid=[[1]],
        predicted_output=[[2]],
        target_grid=[[2]],
        validated_candidate=candidate,
        arena_execution_recommendation=_arena(candidate),
        candidate_qualification=_qualification(),
        execution_grant=grant,
        budget_admission=_budget(run_id="run_e5_phase2_source"),
        governance_context={},
        execution_context={"run_id": "run_e5_phase2_source"},
    )
    feedback = ExecutionFeedbackEngine().process_production_outcome(
        source_run["PRODUCTION_EXECUTION_RESULT"],
        storage_root=storage_root,
        current_run_id="run_e5_phase2_source",
    )
    return source_run, feedback, feedback["experience_record"]


def _failure_source_experience(storage_root):
    source_run, _, _ = _source_experience(storage_root)
    feedback = ExecutionFeedbackEngine().process_production_outcome(
        source_run["PRODUCTION_EXECUTION_RESULT"],
        storage_root=storage_root,
        current_run_id="run_e5_phase2_source",
        evaluation_result={"outcome_class": "FAILURE", "failure_reason": "observed_mismatch"},
    )
    return source_run, feedback, feedback["experience_record"]


def _behavior_vector(report):
    nested = report.get("experience_reuse_report", {})
    strategies = nested.get("reused_strategies", [])
    programs = nested.get("reused_programs", [])
    composed = nested.get("composed_program", {})
    ranked = nested.get("retrieved_experiences", [])
    return {
        "retrieved_experience_ids": [
            item.get("experience_id")
            for item in ranked
            if item.get("experience_id")
        ],
        "reused_strategy_ids": [
            item.get("source_experience_id")
            for item in strategies
            if item.get("source_experience_id")
        ],
        "reused_program_ids": [
            item.get("program_id")
            for item in programs
            if item.get("program_id")
        ],
        "candidate_count": len(strategies) + len(programs),
        "candidate_order": [
            item.get("source_experience_id")
            for item in strategies
            if item.get("source_experience_id")
        ],
        "candidate_source": "adaptive_reuse_engine",
        "selected_candidate": composed.get("composition_state", "UNAVAILABLE"),
        "arena_state": "UNAVAILABLE",
        "arena_winner": "UNAVAILABLE",
        "repair_actions": "UNAVAILABLE",
        "synthesis_actions": composed.get("program_steps", []),
        "execution_plan": composed,
        "execution_operation": (
            composed.get("program_steps", [{}])[0].get("operation")
            if composed.get("program_steps")
            else "UNAVAILABLE"
        ),
        "routes_realized": "UNAVAILABLE",
        "depth_realized": "UNAVAILABLE",
        "budget_requested": "UNAVAILABLE",
        "budget_admitted": "UNAVAILABLE",
        "terminal_state": nested.get("reuse_output_mode"),
    }


def test_real_adaptive_reuse_engine_shows_reproducible_causal_behavior(tmp_path):
    source_root = tmp_path / "source"
    _, feedback, experience = _source_experience(source_root)
    assert feedback["feedback_level"] == "F4"

    repeats = []
    for repeat in range(3):
        control_root = tmp_path / f"control_{repeat}"
        treatment_root = tmp_path / f"treatment_{repeat}"
        removal_root = tmp_path / f"removal_{repeat}"
        _persist_experience(treatment_root, experience)

        control = _real_runtime_engine(control_root).evaluate_reuse(_runtime_context())
        treatment = _real_runtime_engine(treatment_root).evaluate_reuse(_runtime_context())
        removal = _real_runtime_engine(removal_root).evaluate_reuse(_runtime_context())

        behavior_a = _behavior_vector(control)
        behavior_b = _behavior_vector(treatment)
        behavior_removed = _behavior_vector(removal)
        repeats.append((behavior_a, behavior_b, behavior_removed))

        assert control["experience_reuse_report"]["retrieval_successes"] == 0
        assert treatment["experience_reuse_report"]["retrieval_successes"] == 1
        assert treatment["experience_reuse_report"]["reused_strategies"][0][
            "source_experience_id"
        ] == experience["experience_id"]
        assert treatment["program_hits"] > control["program_hits"]
        assert behavior_b != behavior_a
        assert behavior_removed == behavior_a
        assert behavior_b["reused_strategy_ids"] == [experience["experience_id"]]

    assert all(item[1] != item[0] for item in repeats)
    assert all(item[2] == item[0] for item in repeats)


def test_real_null_experience_does_not_reproduce_targeted_effect(tmp_path):
    _, _, experience = _source_experience(tmp_path / "source")
    unrelated = deepcopy(experience)
    unrelated["experience_id"] = "real_unrelated_motion_experience"
    unrelated["winner_hypothesis"]["type"] = "translate"
    unrelated["winner_hypothesis"]["operation"] = "translate"
    unrelated["winner_hypothesis"]["description"] = "directional motion"
    unrelated["semantic_graph"]["concept_nodes"] = [{"concept": "translate"}]
    unrelated["execution_plan"]["nodes"] = [{"operation": "translate"}]
    unrelated["program"] = {"operation": "translate"}
    unrelated["operation"] = "translate"
    unrelated["execution_signature"] = "translate"
    unrelated["program_signature"] = "translate"
    unrelated["task_signature"] = "real_unrelated_motion_task"
    unrelated["semantic_signature"] = "translate"
    unrelated["concept_signature"] = "translate"
    _persist_experience(tmp_path / "null", unrelated)

    report = _real_runtime_engine(tmp_path / "null").evaluate_reuse(_runtime_context())
    operations = [
        step["operation"]
        for step in report["experience_reuse_report"]
        .get("composed_program", {})
        .get("program_steps", [])
    ]

    assert "replace_color" not in operations
    assert report["experience_reuse_report"]["reused_strategies"][0][
        "source_experience_id"
    ] == unrelated["experience_id"]


def test_real_failure_experience_changes_future_behavior_without_authority(tmp_path):
    _, feedback, failure = _failure_source_experience(tmp_path / "source_failure")
    assert feedback["outcome_evaluation"]["outcome_class"] == "FAILURE"
    assert feedback["outcome_evaluation"]["learning_value"] == "LEARNING_INPUT"
    assert feedback["performance_history"]["failure_count"] == 1
    assert failure["execution_authority"] == "NONE"
    assert failure["reusable_execution_authority"] is False
    _persist_experience(tmp_path / "failure_treatment", failure)

    control = _real_runtime_engine(tmp_path / "failure_control").evaluate_reuse(
        _runtime_context()
    )
    treatment = _real_runtime_engine(tmp_path / "failure_treatment").evaluate_reuse(
        _runtime_context()
    )

    assert control["experience_reuse_report"]["retrieval_successes"] == 0
    assert treatment["experience_reuse_report"]["retrieval_successes"] == 1
    assert _behavior_vector(treatment) != _behavior_vector(control)
    assert treatment["experience_reuse_report"]["reused_strategies"][0][
        "source_experience_id"
    ] == failure["experience_id"]


def test_real_prior_experience_does_not_bypass_future_execution_authority(tmp_path):
    _, _, experience = _source_experience(tmp_path / "source")
    _persist_experience(tmp_path / "treatment", experience)
    reuse_report = _real_runtime_engine(tmp_path / "treatment").evaluate_reuse(
        _runtime_context()
    )

    future = ExecutableIntelligenceEngine(memory=ExecutionMemory()).execute_production(
        candidate=_candidate(),
        compiled_program={"steps": [{"operation": "replace_color", "parameters": {}}]},
        validation={"validation_success": True, "validation_id": "future_validation"},
        qualification=_qualification(),
        arena_selection=_arena(_candidate()),
        execution_grant=experience,
        budget_admission=_budget(run_id="future_run"),
        governance_state={},
        execution_context={"run_id": "future_run", "production_execution_requested": True},
        input_grid=[[1]],
        requested_operation="replace_color",
    )

    assert reuse_report["experience_reuse_report"]["retrieval_successes"] == 1
    assert experience["execution_authority"] == "NONE"
    assert future["real_execution_performed"] is False
    assert future["underlying_executor_called"] is False
