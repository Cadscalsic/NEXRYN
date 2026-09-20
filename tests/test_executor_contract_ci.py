import json
from copy import deepcopy
from pathlib import Path

from runtime.arena.candidate_normalizer import CandidateNormalizer
from runtime.arena.executor_contract import (
    EXACT_VERSION_REPLAY,
    MIGRATION_REQUIRED,
    UNDETERMINED,
    classify_replay,
)
from tools.executor_contract_ci import (
    MANIFEST_PATH,
    SURFACES,
    VECTOR_PATH,
    compute_surface_fingerprint,
    object_fingerprint,
    verify,
)


def sources():
    return {path: Path(path).read_text(encoding="utf-8") for path in SURFACES}


def test_committed_contract_and_vectors_are_current():
    assert verify()["status"] == "PASSED"


def test_non_semantic_comment_edit_without_bump_passes():
    changed = sources()
    changed["runtime/arena/candidate_simulator.py"] += "\n# non-semantic comment\n"
    assert verify(source_overrides=changed)["status"] == "PASSED"


def test_execution_semantic_edit_without_bump_fails_closed():
    changed = sources()
    path = "runtime/arena/candidate_simulator.py"
    changed[path] = changed[path].replace("return output, False", "return output, True")
    assert "UNCLASSIFIED_POTENTIAL_SEMANTIC_CHANGE" in verify(source_overrides=changed)["failures"]


def test_active_field_default_coordinate_and_failure_changes_fail_closed():
    base = sources()
    path = "runtime/arena/candidate_simulator.py"
    mutations = [
        ("parameters.get(\"cells_to_write\", [])", "parameters.get(\"active_cells\", [])"),
        ("parameters.get(\"degrees\", 90)", "parameters.get(\"degrees\", 180)"),
        ("target_row = row + delta_row", "target_row = row - delta_row"),
        ("return output, False", "raise ValueError(operation)"),
    ]
    for old, new in mutations:
        changed = dict(base)
        changed[path] = changed[path].replace(old, new)
        assert verify(source_overrides=changed)["status"] == "FAILED"


def test_normalization_and_serialization_changes_require_review():
    base = sources()
    path = "runtime/arena/candidate_normalizer.py"
    for old, new in [
        ("parameters.pop(\"duplication_count\", None)", "pass"),
        ("sort_keys=True", "sort_keys=False"),
    ]:
        changed = dict(base)
        changed[path] = changed[path].replace(old, new)
        assert verify(source_overrides=changed)["status"] == "FAILED"


def test_stale_manifest_and_stale_vectors_are_rejected():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["semantic_version"] = "1.1"
    assert "STALE_MANIFEST_FINGERPRINT" in verify(manifest=manifest)["failures"]
    vectors = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    vectors["vectors"][0]["expected"]["simulation_success"] = False
    assert "STALE_VECTOR_SET_FINGERPRINT" in verify(vectors=vectors)["failures"]


def test_version_change_requires_manifest_and_vectors():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["semantic_version"] = "2.0"
    manifest["immutable_fingerprint"] = object_fingerprint(manifest)
    failures = verify(manifest=manifest)["failures"]
    assert "AUTHORITATIVE_VERSION_MANIFEST_MISMATCH" in failures


def test_every_supported_operation_has_a_canonical_vector():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    vectors = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    covered = {op for row in vectors["vectors"] for op in row["covers_operations"]}
    assert set(manifest["supported_operation_set"]) <= covered


def test_cross_version_replay_is_fail_closed():
    assert classify_replay("nexryn.arena.candidate_simulator", "1.0") == EXACT_VERSION_REPLAY
    assert classify_replay("nexryn.arena.candidate_simulator", "2.0") == MIGRATION_REQUIRED
    assert classify_replay(None, None) == UNDETERMINED


def test_count_semantics_are_unambiguous_and_invariant_holds():
    step = {"operation": "duplicate_object", "parameters": {"cells_to_write": []}}
    proposals = [
        {"candidate_id": "a", "source": "one", "program": {"steps": [step]}},
        {"candidate_id": "b", "source": "two", "program": {"steps": [step]}},
        {"candidate_id": "c", "source": "three", "program": {"steps": [{"operation": "rotate", "parameters": {}}]}},
    ]
    report = CandidateNormalizer().normalize(proposals)
    assert report["raw_candidate_count"] == report["retained_representative_count"] + report["collapsed_record_count"]
    assert report["semantic_equivalence_class_count"] == report["retained_representative_count"] == report["arena_candidate_count"] == 2
    assert report["alias_class_count"] == 1
    assert report["total_alias_member_count"] == 2


def test_old_artifact_identity_is_preserved_on_normalization():
    candidate = {"candidate_id": "old", "source": "archive", "executor_contract_version": "0.9", "program": {"steps": []}}
    snapshot = deepcopy(candidate)
    normalized = CandidateNormalizer().normalize([candidate])["normalized_candidates"][0]
    assert candidate == snapshot
    assert normalized["executor_contract_version"] == "0.9"
    assert normalized["executor_contract_binding_state"] == "NONCURRENT_CONTRACT_PRESERVED_FAIL_CLOSED"


def test_pending_plan_is_run_bound_and_behaviorally_powerless():
    path = Path("runtime/state/evidence_acquisition_plans/pending/evidence_plan_run_20260919_231626_f83c998ae9.json")
    plan = json.loads(path.read_text(encoding="utf-8"))
    assert plan["source_run_id"] == "run_20260919_231626"
    assert plan["lifecycle_state"] == "PENDING_NEXT_RUN"
    assert plan["claim_evidence_binding_authority"] == "OBSERVATION_ONLY"
    assert plan["claim_evidence_binding_behavioral_authority"] == "NONE"
    assert plan["execution_authority"] == plan["truth_authority"] == "NONE"
    forbidden = {"safe_winner", "execution_grant", "accepted_evidence"}
    assert forbidden.isdisjoint(plan)


def test_governance_has_no_authority_escalation():
    result = verify()
    assert result["authority"] == "CI_VALIDATION_ONLY"
    assert result["behavioral_authority"] == "NONE"
    assert "winner" not in result and "execution_grant" not in result
