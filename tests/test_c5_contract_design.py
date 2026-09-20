from runtime.experiments.c5_contract_design import (
    C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT,
    C5_MIN_TARGET_SUBJECTS,
    c5_gate,
    c5_subject_unit,
)


def _subject(index: int, *, c4=True, level="REPRODUCIBLY_SUPPORTED"):
    return {
        "capability_id": f"capability_{index}",
        "operation": f"operation_{index}",
        "qualification_claim_id": f"claim_{index}",
        "current_qualification_level": level,
        "C4_state": "C4_PASSED" if c4 else "C4_NOT_PASSED",
        "independent_causal_source_count": (
            C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT
        ),
        "canonical_source_ids": [f"source_{index}_a", f"source_{index}_b"],
        "context_count": 2,
    }


def test_c5_unit_is_c4_qualified_exact_subject_not_artifact():
    subject = _subject(1)

    unit = c5_subject_unit(subject)

    assert unit["c5_unit_type"] == "C4_QUALIFIED_EXACT_SUBJECT"
    assert unit["counts_toward_c5"] is True


def test_c5_rejects_subject_without_c4_even_if_it_has_causal_sources():
    subject = _subject(1, c4=False)

    unit = c5_subject_unit(subject)

    assert unit["independent_source_count_sufficient"] is True
    assert unit["counts_toward_c5"] is False


def test_c5_gate_requires_frozen_target_set_and_all_subjects_replicated():
    subjects = [_subject(1), _subject(2), _subject(3, c4=False)]

    result = c5_gate(
        target_set_frozen=True,
        contract_mutation_count=0,
        subjects=subjects,
        source_independence_inflation_count=0,
        synthetic_downstream_object_count=0,
        authority_violation_count=0,
    )

    assert result["c5_pass"] is False
    assert "target_set_not_fully_replicated" in result["failure_reasons"]


def test_c5_gate_rejects_post_hoc_subject_removal():
    subjects = [_subject(1), _subject(2), _subject(3)]

    result = c5_gate(
        target_set_frozen=True,
        contract_mutation_count=0,
        subjects=subjects,
        source_independence_inflation_count=0,
        synthetic_downstream_object_count=0,
        authority_violation_count=0,
        dropped_failed_subject_count=1,
    )

    assert result["c5_pass"] is False
    assert "failed_subject_removed_after_freeze" in result["failure_reasons"]


def test_c5_gate_passes_minimal_formal_contract():
    subjects = [_subject(1), _subject(2), _subject(3)]

    result = c5_gate(
        target_set_frozen=True,
        contract_mutation_count=0,
        subjects=subjects,
        source_independence_inflation_count=0,
        synthetic_downstream_object_count=0,
        authority_violation_count=0,
    )

    assert len(subjects) == C5_MIN_TARGET_SUBJECTS
    assert result["c5_pass"] is True
    assert result["replicated_subject_count"] == C5_MIN_TARGET_SUBJECTS


def test_c5_gate_rejects_runtime_authority_or_synthetic_objects():
    subjects = [_subject(1), _subject(2), _subject(3)]

    result = c5_gate(
        target_set_frozen=True,
        contract_mutation_count=0,
        subjects=subjects,
        source_independence_inflation_count=0,
        synthetic_downstream_object_count=1,
        authority_violation_count=1,
    )

    assert result["c5_pass"] is False
    assert "synthetic_downstream_objects_present" in result["failure_reasons"]
    assert "authority_violation" in result["failure_reasons"]


def test_c5_gate_rejects_subject_without_context_diversity():
    subjects = [_subject(1), _subject(2), _subject(3)]
    subjects[0]["context_count"] = 1

    result = c5_gate(
        target_set_frozen=True,
        contract_mutation_count=0,
        subjects=subjects,
        source_independence_inflation_count=0,
        synthetic_downstream_object_count=0,
        authority_violation_count=0,
    )

    assert result["c5_pass"] is False
    assert "subject_context_count_below_minimum" in result["failure_reasons"]
