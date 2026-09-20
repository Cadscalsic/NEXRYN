import json
from copy import deepcopy

from runtime.adaptive_reuse import AdaptiveReuseLayer
from runtime.adaptive_reuse.episode_memory import EpisodeMemory
from runtime.adaptive_reuse.experience_index import ExperienceIndex
from runtime.adaptive_reuse.program_reuse_engine import ProgramReuseEngine
from runtime.adaptive_reuse.strategy_retriever import StrategyRetriever
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
        "task_signature": "e5_controlled_color_task",
    }


def _adaptive_layer(storage_root):
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


def _behavior_vector(report):
    strategies = report.get("reused_strategies", [])
    programs = report.get("reused_programs", [])
    ranked = report.get("retrieved_experiences", [])
    composed = report.get("composed_program", {})
    return {
        "selected_strategy": (
            strategies[0].get("type")
            or strategies[0].get("operation")
            if strategies
            else "UNAVAILABLE"
        ),
        "selected_candidate": composed.get("composition_state", "UNAVAILABLE"),
        "candidate_order": [
            item.get("source_experience_id")
            for item in strategies
            if item.get("source_experience_id")
        ],
        "candidate_count": len(strategies) + len(programs),
        "reused_object_ids": [
            item.get("learned_object_id")
            for item in ranked
            if item.get("learned_object_id")
        ],
        "reused_experience_ids": [
            item.get("experience_id")
            for item in ranked
            if item.get("experience_id")
        ],
        "repair_actions": "UNAVAILABLE",
        "synthesis_actions": composed.get("program_steps", []),
        "arena_proposals": "UNAVAILABLE",
        "arena_winner": "UNAVAILABLE",
        "execution_plan": composed,
        "reasoning_routes": "UNAVAILABLE",
        "reasoning_depth": "UNAVAILABLE",
        "budget_requested": "UNAVAILABLE",
        "budget_admitted": "UNAVAILABLE",
        "execution_operation": (
            composed.get("program_steps", [{}])[0].get("operation")
            if composed.get("program_steps")
            else "UNAVAILABLE"
        ),
        "terminal_state": report.get("reuse_output_mode"),
    }


def _governed_experience_record():
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = _candidate()
    grant = _grant(
        engine=engine,
        candidate=candidate,
        run_id="run_e5_experience",
        budget=_budget(run_id="run_e5_experience"),
    )
    result = engine.run(
        semantic_intent="replace_color",
        operation="replace_color",
        input_grid=[[1]],
        predicted_output=[[2]],
        target_grid=[[2]],
        validated_candidate=candidate,
        arena_execution_recommendation=_arena(candidate),
        candidate_qualification=_qualification(),
        execution_grant=grant,
        budget_admission=_budget(run_id="run_e5_experience"),
        governance_context={},
        execution_context={"run_id": "run_e5_experience"},
    )
    feedback = ExecutionFeedbackEngine().process_production_outcome(
        result["PRODUCTION_EXECUTION_RESULT"],
        current_run_id="run_e5_experience",
    )
    return feedback["experience_record"]


def _persist_experience(storage_root, experience):
    path = storage_root / "experiences" / f"{experience['experience_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(experience, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return path


def test_prior_governed_experience_causes_reproducible_behavior_change(tmp_path):
    experience = _governed_experience_record()
    deltas = []

    for repeat in range(3):
        control_root = tmp_path / f"control_{repeat}"
        treatment_root = tmp_path / f"treatment_{repeat}"
        removal_root = tmp_path / f"removal_{repeat}"
        _persist_experience(treatment_root, experience)

        control = _adaptive_layer(control_root).evaluate(_runtime_context())
        treatment = _adaptive_layer(treatment_root).evaluate(_runtime_context())
        removal = _adaptive_layer(removal_root).evaluate(_runtime_context())

        behavior_a = _behavior_vector(control)
        behavior_b = _behavior_vector(treatment)
        behavior_removed = _behavior_vector(removal)
        delta = {
            "strategy_hits": treatment["strategy_hits"] - control["strategy_hits"],
            "program_hits": treatment["program_hits"] - control["program_hits"],
            "candidate_count": behavior_b["candidate_count"]
            - behavior_a["candidate_count"],
            "terminal_state_changed": behavior_b["terminal_state"]
            != behavior_a["terminal_state"],
            "removed_returns_to_control": behavior_removed == behavior_a,
            "consumed_experience_id": behavior_b["reused_experience_ids"][0],
        }
        deltas.append(delta)

        assert control["retrieval_successes"] == 0
        assert treatment["retrieval_successes"] == 1
        assert treatment["strategy_hits"] == 1
        assert treatment["program_hits"] == 1
        assert treatment["reused_strategies"][0]["source_experience_id"] == (
            experience["experience_id"]
        )
        assert behavior_b != behavior_a
        assert behavior_removed == behavior_a
        assert delta["consumed_experience_id"] == experience["experience_id"]

    assert all(delta["strategy_hits"] == 1 for delta in deltas)
    assert all(delta["program_hits"] == 1 for delta in deltas)
    assert all(delta["removed_returns_to_control"] is True for delta in deltas)


def test_unrelated_experience_does_not_produce_targeted_behavior_effect(tmp_path):
    unrelated = _governed_experience_record()
    unrelated["experience_id"] = "experience_unrelated_motion"
    unrelated["winner_hypothesis"]["type"] = "translate"
    unrelated["winner_hypothesis"]["operation"] = "translate"
    unrelated["winner_hypothesis"]["description"] = "directional motion"
    unrelated["semantic_graph"]["concept_nodes"] = [{"concept": "translate"}]
    unrelated["execution_plan"]["nodes"] = [{"operation": "translate"}]
    unrelated["program"] = {"operation": "translate"}
    unrelated["operation"] = "translate"
    unrelated["execution_signature"] = "translate"
    unrelated["program_signature"] = "translate"
    unrelated["task_signature"] = "unrelated_motion_task"
    unrelated["semantic_signature"] = "translate"
    unrelated["concept_signature"] = "translate"
    _persist_experience(tmp_path, unrelated)

    report = _adaptive_layer(tmp_path).evaluate(_runtime_context())

    operations = [
        step["operation"]
        for step in report["composed_program"].get("program_steps", [])
    ]
    assert "replace_color" not in operations
    assert report["reused_strategies"][0]["source_experience_id"] == (
        unrelated["experience_id"]
    )


def test_failure_experience_can_change_preference_without_execution_authority(tmp_path):
    failure = _governed_experience_record()
    feedback = ExecutionFeedbackEngine().process_production_outcome(
        {
            **failure,
            "execution_state": "NOT_A_PRODUCTION_OUTCOME",
        }
    )
    failure["experience_id"] = "experience_failure_replace_color"
    failure["evaluation_result"] = {
        "success": False,
        "outcome_class": "FAILURE",
        "evaluation_id": "failure_eval",
    }
    failure["performance_score"] = 0.0
    failure["success_rate"] = 0.0
    _persist_experience(tmp_path, failure)

    report = _adaptive_layer(tmp_path).evaluate(_runtime_context())

    assert feedback["feedback_state"] == "PRODUCTION_OUTCOME_FEEDBACK_BLOCKED"
    assert report["retrieval_successes"] == 1
    assert report["strategy_hits"] == 1
    assert report["reused_strategies"][0]["source_experience_id"] == (
        failure["experience_id"]
    )
    assert failure["execution_authority"] == "NONE"
    assert failure["reusable_execution_authority"] is False


def test_copied_altered_and_repeated_experience_do_not_amplify_authority(tmp_path):
    experience = _governed_experience_record()
    copied = deepcopy(experience)
    copied["experience_id"] = "copied_experience"
    altered = deepcopy(experience)
    altered["execution_grant_id"] = "altered_grant"
    altered["experience_id"] = "altered_experience"

    _persist_experience(tmp_path, experience)
    _persist_experience(tmp_path, copied)
    _persist_experience(tmp_path, altered)

    first = _adaptive_layer(tmp_path).evaluate(_runtime_context())
    second = _adaptive_layer(tmp_path).evaluate(_runtime_context())

    assert first["retrieval_successes"] == 1
    assert second["retrieval_successes"] == 1
    assert first["strategy_hits"] <= 5
    assert second["strategy_hits"] == first["strategy_hits"]
    for strategy in second["reused_strategies"]:
        assert strategy.get("execution_authority") in {None, "NONE"}
