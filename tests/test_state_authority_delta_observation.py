import json
from pathlib import Path

from runtime.observability.state_authority_delta import (
    AUTHORITY,
    BEHAVIORAL_AUTHORITY,
    REPORT_TYPE,
    build_current_run_state_authority_delta_report,
    capture_state_authority_snapshot,
    derive_state_authority_delta,
    finalize_current_run_state_authority_delta,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _defs(tmp_path: Path) -> list[dict]:
    return [
        {
            "store_id": "shared_cognitive_state",
            "domain": "SHARED_COGNITIVE_STATE",
            "path": "shared/latest.json",
            "path_type": "file",
            "mutation_class": "CACHE_UPDATE",
            "semantic_authority_owner": "PRODUCER_RUNTIME",
            "persistence_executor": "SharedCognitiveState.save",
            "writer_component": "runtime.state.shared_cognitive_state.SharedCognitiveState",
            "owner_file": "runtime/state/shared_cognitive_state.py",
            "owner_symbol": "SharedCognitiveState.save",
        },
        {
            "store_id": "evidence_plan_state",
            "domain": "EVIDENCE_PLAN_STATE",
            "path": "evidence/pending",
            "path_type": "directory",
            "mutation_class": "EVIDENCE_PLAN_WRITE",
            "semantic_authority_owner": "EvidenceAcquisitionPlanStore",
            "persistence_executor": "EvidenceAcquisitionPlanStore.persist_plan",
            "writer_component": "runtime.evidence.evidence_plan_store.EvidenceAcquisitionPlanStore",
            "owner_file": "runtime/evidence/evidence_plan_store.py",
            "owner_symbol": "EvidenceAcquisitionPlanStore.persist_plan",
        },
        {
            "store_id": "truth_registry",
            "domain": "TRUTH_REGISTRY",
            "path": "truth_registry.json",
            "path_type": "file",
            "mutation_class": "TRUTH_CANDIDATE_WRITE",
            "semantic_authority_owner": "TruthRegistry",
            "persistence_executor": "TruthRegistry._persist",
            "writer_component": "runtime.truth_registry.truth_registry.TruthRegistry",
            "owner_file": "runtime/truth_registry/truth_registry.py",
            "owner_symbol": "TruthRegistry._persist",
        },
        {
            "store_id": "program_memory",
            "domain": "PROGRAM_MEMORY",
            "path": "program_memory.json",
            "path_type": "file",
            "mutation_class": "PROGRAM_MEMORY_WRITE",
            "semantic_authority_owner": "ProgramMemory",
            "persistence_executor": "ProgramMemory.save",
            "writer_component": "runtime.meta.supervisor.program_memory.ProgramMemory",
            "owner_file": "runtime/meta/supervisor/program_memory.py",
            "owner_symbol": "ProgramMemory.save",
        },
        {
            "store_id": "task_selection_memory",
            "domain": "TASK_SELECTION_MEMORY",
            "path": "task_selection_memory.json",
            "path_type": "file",
            "mutation_class": "TASK_SELECTION_WRITE",
            "semantic_authority_owner": "TrainingAssistant",
            "persistence_executor": "TrainingAssistant._persist_selection_memory",
            "writer_component": "runtime.learning.training_assistant.TrainingAssistant",
            "owner_file": "runtime/learning/training_assistant.py",
            "owner_symbol": "TrainingAssistant._persist_selection_memory",
        },
        {
            "store_id": "knowledge_state",
            "domain": "KNOWLEDGE_STATE",
            "path": "knowledge.json",
            "path_type": "file",
            "mutation_class": "KNOWLEDGE_WRITE",
            "semantic_authority_owner": "KnowledgeReplicationLedger",
            "persistence_executor": "KnowledgeReplicationLedger._persist",
            "writer_component": "runtime.epistemic.knowledge_replication_ledger.KnowledgeReplicationLedger",
            "owner_file": "runtime/epistemic/knowledge_replication_ledger.py",
            "owner_symbol": "KnowledgeReplicationLedger._persist",
        },
    ]


def _snapshot(tmp_path: Path, run_id: str = "run-1") -> dict:
    return capture_state_authority_snapshot(
        run_id=run_id,
        execution_plan_id="plan-1",
        task_id="task-1",
        repository_root=tmp_path,
        store_definitions=_defs(tmp_path),
    )


def _report(tmp_path: Path, pre: dict, run_id: str = "run-1") -> dict:
    return build_current_run_state_authority_delta_report(
        run_id=run_id,
        execution_plan_id="plan-1",
        task_id="task-1",
        pre_run_snapshot=pre,
        repository_root=tmp_path,
        store_definitions=_defs(tmp_path),
    )


def test_historical_pre_existing_state_remains_historical_present(tmp_path):
    _write_json(tmp_path / "program_memory.json", {"programs": [{"program_id": "p1"}]})
    pre = _snapshot(tmp_path)
    report = _report(tmp_path, pre)
    entry = report["derived_state_delta"]["stores"]["program_memory"]["entries"]["p1"]
    assert entry["state_delta"] == "UNCHANGED"
    assert entry["current_run_state"] == "HISTORICAL_PRESENT"


def test_current_run_persistent_write_is_mutated_with_binding(tmp_path):
    pre = _snapshot(tmp_path)
    _write_json(tmp_path / "program_memory.json", {"programs": [{"program_id": "p2", "run_id": "run-1"}]})
    report = _report(tmp_path, pre)
    mutation = report["mutation_observations"][0]
    assert mutation["current_run_state"] == "CURRENT_RUN_MUTATED"
    assert mutation["current_run_binding"] == "VALID"


def test_semantic_authority_owner_differs_from_persistence_executor(tmp_path):
    pre = _snapshot(tmp_path)
    _write_json(tmp_path / "program_memory.json", {"programs": [{"program_id": "p3", "run_id": "run-1"}]})
    mutation = _report(tmp_path, pre)["mutation_observations"][0]
    assert mutation["semantic_authority_owner"] == "ProgramMemory"
    assert mutation["persistence_executor"] == "ProgramMemory.save"


def test_truth_candidate_creation_is_not_truth_commitment(tmp_path):
    pre = _snapshot(tmp_path)
    _write_json(tmp_path / "truth_registry.json", {"truths": [{"concept": "c1", "status": "CANDIDATE", "run_id": "run-1"}]})
    mutation = _report(tmp_path, pre)["mutation_observations"][0]
    assert mutation["mutation_class"] == "TRUTH_CANDIDATE_WRITE"
    assert mutation["operation"] == "truth_candidate_creation_or_update"
    assert mutation["truth_commitment_claimed"] is False


def test_evidence_plan_creation_is_not_evidence_acceptance(tmp_path):
    pre = _snapshot(tmp_path)
    _write_json(tmp_path / "evidence/pending/plan.json", {"plan_id": "ep1", "source_run_id": "run-1"})
    mutation = _report(tmp_path, pre)["mutation_observations"][0]
    assert mutation["mutation_class"] == "EVIDENCE_PLAN_WRITE"
    assert mutation["evidence_acceptance_claimed"] is False


def test_program_persistence_is_not_learning_benefit(tmp_path):
    pre = _snapshot(tmp_path)
    _write_json(tmp_path / "program_memory.json", {"programs": [{"program_id": "p4", "run_id": "run-1"}]})
    mutation = _report(tmp_path, pre)["mutation_observations"][0]
    assert mutation["learning_effect_claimed"] is False


def test_shared_state_publication_does_not_own_semantic_authority(tmp_path):
    pre = _snapshot(tmp_path)
    _write_json(tmp_path / "shared/latest.json", {"knowledge_objects": {"k1": {"run_id": "run-1"}}})
    mutation = _report(tmp_path, pre)["mutation_observations"][0]
    assert mutation["persistence_executor"] == "SharedCognitiveState.save"
    assert mutation["semantic_authority_owner"] == "PRODUCER_RUNTIME"


def test_wrong_run_mutation_is_rejected_from_current_run_attribution(tmp_path):
    pre = _snapshot(tmp_path)
    _write_json(tmp_path / "evidence/pending/plan.json", {"plan_id": "ep2", "source_run_id": "run-2"})
    mutation = _report(tmp_path, pre)["mutation_observations"][0]
    assert mutation["current_run_binding"] == "REJECTED_RUN_MISMATCH"
    assert mutation["included_in_current_run_attribution"] is False


def test_pre_post_detects_added_removed_and_modified_stable_ids(tmp_path):
    _write_json(tmp_path / "program_memory.json", {"programs": [{"program_id": "keep"}, {"program_id": "gone"}]})
    pre = _snapshot(tmp_path)
    _write_json(tmp_path / "program_memory.json", {"programs": [{"program_id": "keep", "changed": True}, {"program_id": "new"}]})
    delta = derive_state_authority_delta(pre, _snapshot(tmp_path))
    entries = delta["stores"]["program_memory"]["entries"]
    assert entries["new"]["state_delta"] == "ADDED"
    assert entries["gone"]["state_delta"] == "REMOVED"
    assert entries["keep"]["state_delta"] == "MODIFIED"


def test_observation_artifact_does_not_contaminate_cognitive_delta(tmp_path):
    pre = _snapshot(tmp_path)
    _write_json(tmp_path / "runtime/artifacts/runtime_data/state_authority_delta/report.json", {"report_type": REPORT_TYPE})
    report = _report(tmp_path, pre)
    assert report["observation_artifact_excluded_from_cognitive_delta"] is True
    assert report["mutation_observations"] == []


def test_report_authority_is_observation_only(tmp_path):
    report = _report(tmp_path, _snapshot(tmp_path))
    assert report["authority"] == AUTHORITY == "OBSERVATION_ONLY"


def test_report_behavioral_authority_is_none(tmp_path):
    report = _report(tmp_path, _snapshot(tmp_path))
    assert report["behavioral_authority"] == BEHAVIORAL_AUTHORITY == "NONE"


def test_observation_failure_does_not_convert_task_success_to_failure(tmp_path):
    artifact_file = tmp_path / "artifact-file"
    artifact_file.write_text("not a directory", encoding="utf-8")
    report = finalize_current_run_state_authority_delta(
        run_id="run-1",
        execution_plan_id="plan-1",
        task_id="task-1",
        pre_run_snapshot={"invalid": object()},
        repository_root=tmp_path,
        store_definitions=_defs(tmp_path),
        artifact_dir=artifact_file,
    )
    assert report["observation_complete"] is False
    assert report["observation_failure_preserves_task_execution"] is True


def test_fast_minimal_completion_emits_bounded_state_authority_delta(tmp_path):
    pre = _snapshot(tmp_path)
    report = finalize_current_run_state_authority_delta(
        run_id="run-1",
        execution_plan_id="plan-1",
        task_id="task-1",
        pre_run_snapshot=pre,
        repository_root=tmp_path,
        store_definitions=_defs(tmp_path),
        artifact_dir=tmp_path / "observer",
    )
    assert report["report_type"] == REPORT_TYPE
    assert report["artifact_size_bytes"] < 500_000
    assert Path(report["artifact_path"]).exists()


def test_existing_behavior_inputs_are_not_mutated(tmp_path):
    pre = _snapshot(tmp_path)
    before = json.loads(json.dumps(pre, sort_keys=True))
    _report(tmp_path, pre)
    assert pre == before
