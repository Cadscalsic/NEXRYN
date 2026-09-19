import json
import hashlib
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from runtime.arena.candidate_normalizer import CandidateNormalizer


SOURCE_ARTIFACT = Path(
    "runtime/artifacts/safe_winner_predicates/run_20260919_215701.json"
)


def proposal(candidate_id, source, steps, **extra):
    return {
        "candidate_id": candidate_id,
        "source": source,
        "hypothesis_id": f"hypothesis:{candidate_id}",
        "program": {"step_count": len(steps), "steps": steps},
        **extra,
    }


def duplicate_step(*, metadata=False):
    parameters = {
        "cells_to_write": [
            {"row": 1, "col": 2, "value": 8},
            {"row": 3, "col": 4, "value": 9},
        ]
    }
    if metadata:
        parameters.update(
            duplication_count=2,
            duplication_policy="observed_added_object_cells",
        )
    return {"operation": "duplicate_object", "parameters": parameters}


def normalize(*items):
    return CandidateNormalizer().normalize(list(items))


def test_identical_programs_with_different_ids_and_sources_collapse():
    result = normalize(
        proposal("a", "generator_a", [duplicate_step()]),
        proposal("b", "generator_b", [duplicate_step()]),
    )
    assert result["duplicate_candidates_collapsed"] == 1
    assert len(result["normalized_candidates"]) == 1


def test_equivalent_operation_aliases_collapse():
    left = proposal("a", "one", [{"operation": "duplicate", "parameters": {"cells_to_write": []}}])
    right = proposal("b", "two", [{"operation": "replicate", "parameters": {"cells_to_write": []}}])
    assert normalize(left, right)["duplicate_candidates_collapsed"] == 1


def test_redundant_noop_does_not_create_distinct_semantics():
    left = proposal("a", "one", [{"operation": "noop", "parameters": {}}, duplicate_step()])
    right = proposal("b", "two", [duplicate_step()])
    assert normalize(left, right)["duplicate_candidates_collapsed"] == 1


def test_executor_ignored_metadata_serialization_collapses():
    result = normalize(
        proposal("a", "one", [duplicate_step()]),
        proposal("b", "two", [duplicate_step(metadata=True)]),
    )
    candidate = result["normalized_candidates"][0]
    assert result["duplicate_candidates_collapsed"] == 1
    assert candidate["equivalence_reason"] == "EXECUTOR_SEMANTIC_FINGERPRINT_MATCH"


def test_non_commuting_operation_order_does_not_collapse():
    recolor = {"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}
    remove = {"operation": "remove_object", "parameters": {"remove_colors": [2]}}
    assert normalize(
        proposal("a", "one", [recolor, remove]),
        proposal("b", "two", [remove, recolor]),
    )["duplicate_candidates_collapsed"] == 0


def test_equal_training_outputs_do_not_collapse_distinct_programs():
    assert normalize(
        proposal("a", "one", [{"operation": "preserve_grid", "parameters": {}}]),
        proposal("b", "two", [{"operation": "replace_color", "parameters": {"color_mapping": {7: 8}}}]),
    )["duplicate_candidates_collapsed"] == 0


def test_semantic_fingerprint_claims_executor_scope_not_universal_equivalence():
    candidate = normalize(proposal("a", "one", [duplicate_step()]))["normalized_candidates"][0]
    assert candidate["semantic_equivalence_scope"] == "CURRENT_ARENA_EXECUTOR_CONTRACT"
    assert candidate["semantic_equivalence_is_correctness_evidence"] is False


def test_lineage_is_preserved_after_semantic_alias_collapse():
    result = normalize(
        proposal("z", "generator_z", [duplicate_step()], provenance={"route": "z"}),
        proposal("a", "generator_a", [duplicate_step(metadata=True)], provenance={"route": "a"}),
    )
    candidate = result["normalized_candidates"][0]
    assert candidate["equivalent_candidate_ids"] == ["a", "z"]
    assert candidate["sources"] == ["generator_a", "generator_z"]
    assert {row["route"] for row in candidate["provenance_history"]} == {"a", "z"}


def test_representative_is_deterministic_and_order_invariant():
    a = proposal("a", "generator_a", [duplicate_step(metadata=True)])
    z = proposal("z", "generator_z", [duplicate_step()])
    forward = normalize(z, a)["normalized_candidates"][0]
    reverse = normalize(a, z)["normalized_candidates"][0]
    assert forward == reverse
    assert forward["representative_source_candidate_id"] == "a"


def test_semantic_representative_does_not_use_score_or_rank():
    low = proposal("a", "one", [duplicate_step()], source_confidence=0.1, final_score=0.1, rank=2)
    high = proposal("z", "two", [duplicate_step(metadata=True)], source_confidence=1.0, final_score=1.0, rank=1)
    candidate = normalize(high, low)["normalized_candidates"][0]
    assert candidate["representative_source_candidate_id"] == "a"


def test_candidate_and_semantic_fingerprints_are_distinct_contracts():
    result = normalize(proposal("a", "one", [duplicate_step()]))
    candidate = result["normalized_candidates"][0]
    assert candidate["semantic_fingerprint"]
    assert candidate["program_signature"] == candidate["semantic_fingerprint"]


def test_false_semantic_collapse_is_prevented_for_changed_write_value():
    altered = duplicate_step()
    altered["parameters"]["cells_to_write"][0]["value"] = 3
    assert normalize(
        proposal("a", "one", [duplicate_step()]),
        proposal("b", "two", [altered]),
    )["duplicate_candidates_collapsed"] == 0


def test_hidden_guard_or_preservation_difference_fails_closed():
    guarded = duplicate_step()
    guarded["parameters"]["guard"] = {"color_present": 8}
    result = normalize(
        proposal("a", "one", [duplicate_step()]),
        proposal("b", "two", [guarded]),
    )
    assert result["duplicate_candidates_collapsed"] == 0


def test_historical_candidate_set_remains_byte_identical(tmp_path):
    before = SOURCE_ARTIFACT.read_bytes()
    normalize(
        proposal("a", "one", [duplicate_step()]),
        proposal("b", "two", [duplicate_step(metadata=True)]),
    )
    assert SOURCE_ARTIFACT.read_bytes() == before


def test_normalization_does_not_mutate_scores_ranks_or_select_winner():
    original = proposal("a", "one", [duplicate_step()], final_score=0.9, rank=1)
    snapshot = deepcopy(original)
    result = normalize(original)
    assert original == snapshot
    assert "winner" not in result
    assert "execution_grant" not in result


def test_normalization_has_no_authority_escalation():
    result = normalize(proposal("a", "one", [duplicate_step()]))
    assert result["authority"] == "OBSERVATION_ONLY"
    assert result["behavioral_authority"] == "NONE"
    assert result["score_authority"] == "NONE"
    assert result["ranking_authority"] == "NONE"


def test_semantic_fingerprint_is_stable_across_repeated_normalization():
    item = proposal("a", "one", [duplicate_step(metadata=True)])
    first = normalize(item)["normalized_candidates"][0]["semantic_fingerprint"]
    second = normalize(json.loads(json.dumps(item)))["normalized_candidates"][0]["semantic_fingerprint"]
    assert first == second


def test_historical_alias_pattern_binds_executor_contract_and_class_identity():
    result = normalize(
        proposal("a", "normalized_program_candidates", [duplicate_step()]),
        proposal("b", "semantic_compiler", [duplicate_step(metadata=True)]),
    )
    candidate = result["normalized_candidates"][0]
    assert candidate["executor_contract_id"] == "nexryn.arena.candidate_simulator"
    assert candidate["executor_contract_version"] == "1.0"
    assert candidate["semantic_equivalence_class_id"].endswith(
        candidate["semantic_fingerprint"]
    )


def test_alias_records_preserve_fingerprints_sources_and_executables():
    result = normalize(
        proposal("a", "one", [duplicate_step()]),
        proposal("b", "two", [duplicate_step(metadata=True)]),
    )
    aliases = result["normalized_candidates"][0]["semantic_alias_records"]
    assert [row["candidate_id"] for row in aliases] == ["a", "b"]
    assert all(row["candidate_fingerprint"] for row in aliases)
    assert all(row["generator_source"] for row in aliases)
    assert all(row["executable_representation"] for row in aliases)
    assert all(row["source_record"] for row in aliases)


def test_executor_contract_version_difference_is_not_collapsed():
    current = proposal("a", "one", [duplicate_step()])
    future = proposal(
        "b",
        "two",
        [duplicate_step()],
        executor_contract_version="2.0",
    )
    assert normalize(current, future)["duplicate_candidates_collapsed"] == 0


def test_round_trip_persistence_preserves_semantic_identity():
    result = normalize(
        proposal("a", "one", [duplicate_step()]),
        proposal("b", "two", [duplicate_step(metadata=True)]),
    )
    restored = json.loads(json.dumps(result, sort_keys=True))
    assert restored == result


def test_semantic_identity_is_cross_process_and_hash_seed_stable():
    code = """
import hashlib
import json
import os
from runtime.arena.candidate_normalizer import CandidateNormalizer
p = lambda cid, src, extra: {
    'candidate_id': cid,
    'source': src,
    'program': {'step_count': 1, 'steps': [{
        'operation': 'duplicate_object',
        'parameters': {'cells_to_write': [{'row': 1, 'col': 2, 'value': 8}], **extra},
    }]},
}
base = [
    p('b', 'two', {'duplication_count': 1}),
    p('a', 'one', {}),
    p('m', 'three', {'guard': {'color_present': 8}}),
]
order = json.loads(os.environ['CANDIDATE_ORDER'])
r = CandidateNormalizer().normalize([base[index] for index in order])
print(json.dumps({
    'fingerprints': [c['semantic_fingerprint'] for c in r['normalized_candidates']],
    'class_ids': [c['semantic_equivalence_class_id'] for c in r['normalized_candidates']],
    'representatives': [c.get('representative_source_candidate_id', c['candidate_id']) for c in r['normalized_candidates']],
    'aliases': [c.get('equivalent_candidate_ids', [c['candidate_id']]) for c in r['normalized_candidates']],
    'candidate_set_fingerprint': hashlib.sha256(json.dumps({
        'candidates': r['normalized_candidates'],
        'groups': r['equivalent_candidate_groups'],
    }, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
}, sort_keys=True))
"""
    outputs = []
    for seed in ("0", "1", "42", "random"):
        for order in ([0, 1, 2], [2, 1, 0], [1, 2, 0]):
            environment = dict(
                os.environ,
                PYTHONHASHSEED=seed,
                CANDIDATE_ORDER=json.dumps(order),
            )
            outputs.append(
                subprocess.check_output(
                    [sys.executable, "-c", code],
                    cwd=Path.cwd(),
                    env=environment,
                    text=True,
                ).strip()
            )
    assert len(set(outputs)) == 1
