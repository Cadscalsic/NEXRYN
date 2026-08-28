import pytest

from runtime.claim_identity import (
    ClaimIdentityError,
    ClaimKind,
    ClaimSubject,
    SemanticScope,
    canonical_claim_subject_bytes,
    canonical_claim_subject_text,
    derive_claim_id,
)


def test_candidate_operation_golden_vector_freezes_canonical_bytes_and_claim_id():
    subject = ClaimSubject(
        kind=ClaimKind.CANDIDATE_OPERATION,
        semantic_scope=SemanticScope.RUN,
        subject_ref=" semantic_program:Replace Color ",
        operation=" Duplicate Object ",
        qualifiers={
            "input_domain": " ARC Grid ",
            "conditions": ["red cell", "blue cell"],
        },
    )

    expected_text = (
        '{"kind":"candidate_operation","operation":"duplicate_object",'
        '"qualifiers":{"conditions":["blue cell","red cell"],'
        '"input_domain":"ARC Grid"},"schema_version":"1.0",'
        '"semantic_scope":"run","subject_ref":"semantic_program:Replace Color"}'
    )

    assert canonical_claim_subject_text(subject) == expected_text
    assert canonical_claim_subject_bytes(subject) == expected_text.encode("utf-8")
    assert derive_claim_id(subject) == (
        "claim_sha256_ee782438de210d8f9c1b7910ea0a771dae7e9b5b84d1abb4ff708f57dc35877c"
    )


def test_concept_truth_golden_vector_freezes_enum_and_whitespace_normalization():
    subject = ClaimSubject(
        kind="concept truth",
        semantic_scope="cross run",
        subject_ref=" concept:spatial mapping ",
        normalized_statement=" concept X predicts transformation Y under condition Z ",
    )

    expected_text = (
        '{"kind":"concept_truth",'
        '"normalized_statement":"concept X predicts transformation Y under condition Z",'
        '"schema_version":"1.0","semantic_scope":"cross_run",'
        '"subject_ref":"concept:spatial mapping"}'
    )

    assert canonical_claim_subject_text(subject) == expected_text
    assert derive_claim_id(subject) == (
        "claim_sha256_9d83582c6b8663ab2969a0cb97829b208bc1903c95a69b25b5c6ec4c54525e92"
    )


def test_contextual_assertion_golden_vector_freezes_unicode_nfc_and_unordered_lists():
    subject = ClaimSubject(
        kind="contextual assertion",
        semantic_scope="task",
        normalized_statement="cafe\u0301 maps to target",
        qualifiers={
            "unordered_tags": ["beta", "alpha"],
            "context_boundary": "task 17",
        },
    )

    expected_text = (
        '{"kind":"contextual_assertion","normalized_statement":"caf\u00e9 maps to target",'
        '"qualifiers":{"context_boundary":"task 17",'
        '"unordered_tags":["alpha","beta"]},"schema_version":"1.0",'
        '"semantic_scope":"task"}'
    )

    assert canonical_claim_subject_text(subject) == expected_text
    assert canonical_claim_subject_bytes(subject) == expected_text.encode("utf-8")
    assert derive_claim_id(subject) == (
        "claim_sha256_d77230eae9ab80ce1f87e27e2f1e787dfb071dde3df9cb22df132bf468cd8370"
    )


def test_null_optional_fields_are_absent_but_null_required_fields_are_rejected():
    subject = ClaimSubject(
        kind=ClaimKind.CANDIDATE_OPERATION,
        semantic_scope=SemanticScope.TASK,
        subject_ref="candidate:17",
        operation="replace color",
        normalized_statement=None,
        qualifiers={"empty_optional": None},
    )

    text = canonical_claim_subject_text(subject)

    assert "normalized_statement" not in text
    assert "empty_optional" not in text

    with pytest.raises(ClaimIdentityError, match="semantic_scope cannot be null"):
        ClaimSubject(
            kind=ClaimKind.CANDIDATE_OPERATION,
            semantic_scope=None,
            subject_ref="candidate:17",
            operation="replace color",
        ).canonical_payload()


def test_ambiguous_claim_subjects_and_floats_are_rejected_fail_closed():
    with pytest.raises(ClaimIdentityError, match="missing required fields: subject_ref"):
        ClaimSubject(
            kind=ClaimKind.CANDIDATE_OPERATION,
            semantic_scope=SemanticScope.RUN,
            operation="duplicate object",
        ).canonical_payload()

    with pytest.raises(ClaimIdentityError, match="floating-point"):
        ClaimSubject(
            kind=ClaimKind.CONTEXTUAL_ASSERTION,
            semantic_scope=SemanticScope.TASK,
            normalized_statement="score threshold applies",
            qualifiers={"threshold": 0.83, "context_boundary": "task 17"},
        ).canonical_payload()


def test_claim_subject_qualifiers_are_immutable_for_identity_stability():
    qualifiers = {"conditions": ["red cell", "blue cell"]}
    subject = ClaimSubject(
        kind=ClaimKind.CANDIDATE_OPERATION,
        semantic_scope=SemanticScope.RUN,
        subject_ref="candidate:17",
        operation="replace color",
        qualifiers=qualifiers,
    )
    first_text = canonical_claim_subject_text(subject)
    first_id = derive_claim_id(subject)

    qualifiers["conditions"].append("green cell")
    qualifiers["new_context"] = "mutated after construction"

    assert canonical_claim_subject_text(subject) == first_text
    assert derive_claim_id(subject) == first_id


def test_cross_run_and_global_scope_reject_run_local_subject_references():
    with pytest.raises(ClaimIdentityError, match="durable semantic subject_ref"):
        ClaimSubject(
            kind=ClaimKind.CANDIDATE_OPERATION,
            semantic_scope=SemanticScope.CROSS_RUN,
            subject_ref="candidate:17",
            operation="replace color",
        ).canonical_payload()

    with pytest.raises(ClaimIdentityError, match="durable semantic subject_ref"):
        ClaimSubject(
            kind=ClaimKind.CONCEPT_TRUTH,
            semantic_scope=SemanticScope.GLOBAL,
            subject_ref="evidence_plan:abc",
            normalized_statement="candidate solves the task",
        ).canonical_payload()

    allowed = ClaimSubject(
        kind=ClaimKind.CONCEPT_TRUTH,
        semantic_scope=SemanticScope.CROSS_RUN,
        subject_ref="concept:spatial mapping",
        normalized_statement="concept predicts transformation under stable conditions",
    )

    assert derive_claim_id(allowed).startswith("claim_sha256_")
