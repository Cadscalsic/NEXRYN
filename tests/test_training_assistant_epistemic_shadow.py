import json

from runtime.learning.training_assistant import TrainingAssistant


def _write_task(path, metadata):
    path.write_text(
        json.dumps({
            "train": [{"input": [[0]], "output": [[1]]}],
            "test": [{"input": [[0]]}],
            "nexryn_metadata": metadata,
        }),
        encoding="utf-8",
    )


def _requirement(evidence_type="cross_source_consensus_evidence"):
    return {
        "requirement_id": "e2_more_independent_sources",
        "evidence_type": evidence_type,
        "target_claim_id": "claim_sha256_example",
        "claim_domains": ["Color"],
        "missing_requirement": "more_independent_sources",
        "authority": "OBSERVATION_ONLY",
    }


def _task_dir(tmp_path):
    task_dir = tmp_path / "training"
    task_dir.mkdir()
    _write_task(
        task_dir / "task_exact.json",
        {
            "task_id": "task_exact",
            "target_concepts": ["color_mapping"],
            "target_domains": ["Color"],
            "independent_validation_opportunities": [
                "cross_domain_validation",
                "independent_task_validation",
            ],
        },
    )
    _write_task(
        task_dir / "task_strong.json",
        {
            "task_id": "task_strong",
            "target_concepts": ["identity_preservation"],
            "target_domains": ["Identity"],
            "independent_validation_opportunities": [
                "cross_domain_validation",
            ],
        },
    )
    _write_task(
        task_dir / "task_no_match.json",
        {
            "task_id": "task_no_match",
            "target_concepts": ["noise_removal"],
            "target_domains": ["Noise"],
            "required_operational_capabilities": ["world_model_validation"],
            "independent_validation_opportunities": ["exact_validation"],
        },
    )
    _write_task(
        task_dir / "task_unknown.json",
        {"task_id": "task_unknown"},
    )
    return task_dir


def _assistant(tmp_path):
    return TrainingAssistant(
        state_path=tmp_path / "state.json",
        selection_memory_path=tmp_path / "memory.json",
        batch_size=2,
        selection_mode="curriculum",
    )


def test_active_requirement_reaches_selector_shadow_report(tmp_path):
    task_dir = _task_dir(tmp_path)
    selected = _assistant(tmp_path).select_batch(
        [path.name for path in task_dir.glob("*.json")],
        task_directory=task_dir,
        active_epistemic_requirements=_requirement(),
    )

    report = selected["epistemic_shadow_rank_report"]
    assert report["shadow_mode_active"] is True
    assert report["requirement_state"] == "ACTIVE_REQUIREMENT_AVAILABLE"
    assert report["active_requirement_id"] == "e2_more_independent_sources"
    assert report["selector_decision_owner"] == "TrainingAssistant"
    assert report["behavioral_integration_applied"] is False


def test_matching_projection_preserves_task_and_requirement_ids(tmp_path):
    task_dir = _task_dir(tmp_path)
    selected = _assistant(tmp_path).select_batch(
        [path.name for path in task_dir.glob("*.json")],
        task_directory=task_dir,
        active_epistemic_requirements=_requirement(),
    )
    rows = {
        row["task_id"]: row
        for row in selected["epistemic_shadow_rank_report"]["rows"]
    }

    exact = rows["task_exact"]
    assert exact["match_projection"]["task_id"] == "task_exact"
    assert exact["match_projection"]["requirement_id"] == (
        "e2_more_independent_sources"
    )
    assert exact["evidence_match_class"] == "EXACT_MATCH"
    assert exact["authority"] == "OBSERVATION_ONLY"
    assert exact["selection_authority"] == "NONE"
    assert exact["truth_authority"] == "NONE"


def test_no_active_requirement_preserves_base_selection(tmp_path):
    task_dir = _task_dir(tmp_path)
    files = [path.name for path in task_dir.glob("*.json")]
    baseline = _assistant(tmp_path / "baseline").select_batch(
        files,
        task_directory=task_dir,
    )
    shadowless = _assistant(tmp_path / "shadowless").select_batch(
        files,
        task_directory=task_dir,
        active_epistemic_requirements=None,
    )

    assert shadowless["selected_task_files"] == baseline["selected_task_files"]
    assert shadowless["epistemic_shadow_rank_report"]["shadow_mode_active"] is False
    assert shadowless["epistemic_shadow_rank_report"]["rows"] == []


def test_shadow_rank_does_not_affect_production_selection(tmp_path):
    task_dir = _task_dir(tmp_path)
    files = [path.name for path in task_dir.glob("*.json")]
    selected = _assistant(tmp_path).select_batch(
        files,
        task_directory=task_dir,
        concept_counts={"noise_removal": 0, "color_mapping": 99},
        active_epistemic_requirements=_requirement(),
    )

    report = selected["epistemic_shadow_rank_report"]
    assert selected["selected_task_files"] == report["base_selected_tasks"]
    assert report["selection_changed_by_epistemic_signal"] is False
    assert any(row["epistemic_adjustment"] > 0 for row in report["rows"])
    assert all("base_score" in row for row in report["rows"])


def test_exact_strong_no_match_and_unknown_policies_are_distinct(tmp_path):
    task_dir = _task_dir(tmp_path)
    selected = _assistant(tmp_path).select_batch(
        [path.name for path in task_dir.glob("*.json")],
        task_directory=task_dir,
        active_epistemic_requirements=_requirement(),
    )
    rows = {
        row["task_id"]: row
        for row in selected["epistemic_shadow_rank_report"]["rows"]
    }

    assert rows["task_exact"]["evidence_match_class"] == "EXACT_MATCH"
    assert rows["task_exact"]["epistemic_adjustment"] == 1.0
    assert rows["task_strong"]["evidence_match_class"] == "STRONG_MATCH"
    assert rows["task_strong"]["epistemic_adjustment"] == 0.5
    assert rows["task_no_match"]["evidence_match_class"] == "NO_MATCH"
    assert rows["task_no_match"]["epistemic_adjustment"] == 0.0
    assert rows["task_unknown"]["evidence_match_class"] == "UNKNOWN"
    assert rows["task_unknown"]["epistemic_adjustment"] == 0.0


def test_invalid_foreign_and_unknown_requirements_fail_closed(tmp_path):
    task_dir = _task_dir(tmp_path)
    files = [path.name for path in task_dir.glob("*.json")]

    malformed = _assistant(tmp_path / "malformed").select_batch(
        files,
        task_directory=task_dir,
        active_epistemic_requirements={},
    )
    foreign = _assistant(tmp_path / "foreign").select_batch(
        files,
        task_directory=task_dir,
        active_epistemic_requirements={
            **_requirement(),
            "foreign_requirement": True,
        },
    )
    unknown = _assistant(tmp_path / "unknown").select_batch(
        files,
        task_directory=task_dir,
        active_epistemic_requirements=_requirement("unknown_evidence_type"),
    )

    assert malformed["epistemic_shadow_rank_report"]["shadow_mode_active"] is False
    assert foreign["epistemic_shadow_rank_report"]["requirement_state"] == (
        "FOREIGN_REQUIREMENT_REJECTED"
    )
    assert unknown["epistemic_shadow_rank_report"]["requirement_state"] == (
        "UNKNOWN_EVIDENCE_TYPE"
    )


def test_existing_cooldown_history_policy_still_operates(tmp_path):
    task_dir = _task_dir(tmp_path)
    assistant = TrainingAssistant(
        state_path=tmp_path / "state.json",
        selection_memory_path=tmp_path / "memory.json",
        batch_size=2,
        selection_mode="weighted_random",
        random_seed=17,
    )
    assistant.selection_memory["recent_runs"] = [{
        "run_id": "prior",
        "task_ids": ["task_exact.json"],
    }]

    selected = assistant.select_batch(
        [path.name for path in task_dir.glob("*.json")],
        task_directory=task_dir,
        selection_mode="weighted_random",
        random_seed=17,
        active_epistemic_requirements=_requirement(),
    )

    assert "task_exact.json" not in selected["selected_task_files"]
    assert any(
        row["task_file"] == "task_exact.json"
        and row["evidence_match_class"] == "EXACT_MATCH"
        for row in selected["epistemic_shadow_rank_report"]["rows"]
    )
