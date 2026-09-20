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


def _coverage():
    return {
        "claim_id": "claim_sha256_example",
        "proven_independent_supporting_sources": 1,
        "required_independent_source_count": 8,
        "additional_independent_sources_required": 7,
        "source_identities": ["represented_lineage"],
        "source_relation_components": [{
            "component_id": "independent_source_component_1",
            "members": [{
                "accepted_evidence_id": "accepted_existing",
                "canonical_source_id": "source_identity_existing",
                "lineage_roots": ["represented_lineage"],
            }],
        }],
    }


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


def test_multi_axis_shadow_exposes_operational_compatibility_and_source_potential(tmp_path):
    task_dir = _task_dir(tmp_path)
    selected = _assistant(tmp_path).select_batch(
        [path.name for path in task_dir.glob("*.json")],
        task_directory=task_dir,
        active_epistemic_requirements=_requirement(),
        claim_source_coverage=_coverage(),
    )

    report = selected["epistemic_shadow_rank_report"]
    row = report["rows"][0]

    assert report["multi_axis_shadow_active"] is True
    assert report["production_selector_changed"] is False
    assert "policy_matrix" in report
    assert "distributions" in report
    assert "operational_score" in row
    assert "evidence_compatibility" in row
    assert "independent_source_potential" in row
    assert "expected_source_descriptor" in row
    assert row["expected_source_descriptor"]["grants_independence"] is False
    assert row["source_descriptor_owner"]["producer_component"] == (
        "VALIDATION_LANE_OWNED"
    )
    assert row["source_potential_projection"][
        "potential_is_proven_independence"
    ] is False
    assert row["selection_authority"] == "NONE"


def test_exact_match_with_unknown_lineage_does_not_receive_novelty_credit(tmp_path):
    task_dir = _task_dir(tmp_path)
    selected = _assistant(tmp_path).select_batch(
        [path.name for path in task_dir.glob("*.json")],
        task_directory=task_dir,
        active_epistemic_requirements=_requirement(),
        claim_source_coverage=_coverage(),
    )
    rows = {
        row["task_id"]: row
        for row in selected["epistemic_shadow_rank_report"]["rows"]
    }

    assert rows["task_exact"]["evidence_match_class"] == "EXACT_MATCH"
    assert rows["task_exact"]["independent_source_potential"] == "UNKNOWN"
    assert rows["task_exact"]["expected_marginal_contribution"] == "UNKNOWN"


def test_declared_represented_source_lineage_gets_no_novelty_credit(tmp_path):
    task_dir = tmp_path / "training"
    task_dir.mkdir()
    _write_task(
        task_dir / "task_represented.json",
        {
            "task_id": "task_represented",
            "target_domains": ["Color"],
            "independent_validation_opportunities": [
                "cross_domain_validation",
            ],
            "source_lineage_targets": ["represented_lineage"],
        },
    )

    selected = _assistant(tmp_path).select_batch(
        ["task_represented.json"],
        task_directory=task_dir,
        active_epistemic_requirements=_requirement(),
        claim_source_coverage=_coverage(),
    )
    row = selected["epistemic_shadow_rank_report"]["rows"][0]

    assert row["evidence_match_class"] == "EXACT_MATCH"
    assert row["independent_source_potential"] == "ALREADY_REPRESENTED_SOURCE"
    assert row["expected_marginal_contribution"] == "NO_EXPECTED_NEW_SOURCE"


def test_declared_unrepresented_lineage_can_be_high_potential_but_shadow_only(tmp_path):
    task_dir = tmp_path / "training"
    task_dir.mkdir()
    _write_task(
        task_dir / "task_new_source.json",
        {
            "task_id": "task_new_source",
            "target_domains": ["Color"],
            "independent_validation_opportunities": [
                "cross_domain_validation",
            ],
            "source_lineage_targets": ["unrepresented_lineage"],
        },
    )

    selected = _assistant(tmp_path).select_batch(
        ["task_new_source.json"],
        task_directory=task_dir,
        active_epistemic_requirements=_requirement(),
        claim_source_coverage=_coverage(),
    )
    row = selected["epistemic_shadow_rank_report"]["rows"][0]

    assert row["independent_source_potential"] == "HIGH_POTENTIAL"
    assert row["expected_source_descriptor"]["source_lineage_family"] == (
        "unrepresented_lineage"
    )
    assert row["source_descriptor_owner"]["source_lineage_family"] == (
        "TASK_OWNED"
    )
    assert row["expected_marginal_contribution"] == (
        "POSSIBLE_NEW_INDEPENDENT_SOURCE"
    )
    assert selected["selected_task_files"] == ["task_new_source.json"]
    assert selected["epistemic_shadow_rank_report"][
        "behavioral_integration_applied"
    ] is False


def test_high_operational_no_match_cannot_gain_unbounded_sovereignty(tmp_path):
    task_dir = _task_dir(tmp_path)
    selected = _assistant(tmp_path).select_batch(
        [path.name for path in task_dir.glob("*.json")],
        task_directory=task_dir,
        concept_counts={"noise_removal": 0, "color_mapping": 99},
        active_epistemic_requirements=_requirement(),
        claim_source_coverage=_coverage(),
    )
    rows = {
        row["task_id"]: row
        for row in selected["epistemic_shadow_rank_report"]["rows"]
    }

    assert rows["task_no_match"]["evidence_match_class"] == "NO_MATCH"
    assert rows["task_no_match"]["independent_source_potential"] == "LOW_POTENTIAL"
    assert rows["task_no_match"]["source_potential_projection"][
        "truth_authority"
    ] == "NONE"
    assert selected["selected_task_files"] == (
        selected["epistemic_shadow_rank_report"]["base_selected_tasks"]
    )
