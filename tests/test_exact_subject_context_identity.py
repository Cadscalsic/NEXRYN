from runtime.capability_intelligence.context_identity import (
    AUTHORITY,
    canonical_capability_id_v2,
    capability_operation_id_v2,
    classify_context_diversity,
    legacy_identity_mapping,
    validation_context_id,
)
from runtime.capability_intelligence.integrated_capability_qualification import (
    capability_id_for_subject,
)


def _subject(context="alpha", *, operation="fill_center", name="fill_center_capability"):
    return {
        "schema_version": "1.0",
        "capability_name": name,
        "operation": operation,
        "domain": "arc_grid_transformation",
        "qualifiers": {"validation_context": context},
    }


def _context(signature="enclosure_a", *, intervention="fill_center", control="disabled"):
    return {
        "context_type": "VALIDATION_SCENARIO",
        "context_parameters": {"fixture": signature},
        "structural_signature": signature,
        "causal_intervention_signature": intervention,
        "counterfactual_contract": control,
    }


def test_legacy_capability_identity_changes_when_validation_context_changes():
    assert capability_id_for_subject(_subject("alpha")) != capability_id_for_subject(
        _subject("beta")
    )


def test_v2_canonical_capability_preserves_same_capability_across_contexts():
    assert canonical_capability_id_v2(_subject("alpha")) == canonical_capability_id_v2(
        _subject("beta")
    )


def test_v2_operation_identity_changes_for_different_operation():
    assert capability_operation_id_v2(
        _subject("alpha", operation="fill_center")
    ) != capability_operation_id_v2(_subject("alpha", operation="outline_border"))


def test_different_capability_has_different_v2_capability_id():
    assert canonical_capability_id_v2(
        _subject("alpha", name="fill_center_capability")
    ) != canonical_capability_id_v2(
        _subject("alpha", name="outline_border_capability")
    )


def test_validation_context_identity_separates_context_from_capability():
    subject_a = _subject("alpha")
    subject_b = _subject("beta")

    assert canonical_capability_id_v2(subject_a) == canonical_capability_id_v2(subject_b)
    assert validation_context_id(
        subject=subject_a,
        qualification_claim_id="claim_fill_center",
        context=_context("enclosure_a"),
    ) != validation_context_id(
        subject=subject_b,
        qualification_claim_id="claim_fill_center",
        context=_context("enclosure_b"),
    )


def test_same_context_replay_has_same_context_identity():
    subject = _subject("alpha")
    context = _context("enclosure_a")

    assert validation_context_id(
        subject=subject,
        qualification_claim_id="claim_fill_center",
        context=context,
    ) == validation_context_id(
        subject=subject,
        qualification_claim_id="claim_fill_center",
        context=dict(context),
    )


def test_context_diversity_rejects_replay_and_accepts_distinct_causal_context():
    replay = classify_context_diversity(
        baseline_context=_context("enclosure_a"),
        candidate_context=_context("enclosure_a"),
    )
    distinct = classify_context_diversity(
        baseline_context=_context("enclosure_a"),
        candidate_context=_context("enclosure_b", intervention="fill_center_variant"),
    )

    assert replay["context_diversity_state"] == "SAME_CONTEXT_REPLAY"
    assert replay["counts_for_c5_context_diversity"] is False
    assert distinct["context_diversity_state"] == "DISTINCT_CAUSAL_CONTEXT"
    assert distinct["counts_for_c5_context_diversity"] is True


def test_legacy_mapping_preserves_historical_identity_without_mutation():
    subject = _subject("alpha")

    mapping = legacy_identity_mapping(
        subject,
        qualification_claim_id="claim_fill_center",
        validation_context=_context("enclosure_a"),
    )

    assert mapping["legacy_capability_id"] == capability_id_for_subject(subject)
    assert mapping["historical_artifact_mutation_required"] is False
    assert mapping["canonical_capability_id_v2"] == canonical_capability_id_v2(subject)


def test_identity_layer_has_no_runtime_or_qualification_authority():
    assert AUTHORITY["identity_authority"] == "IDENTITY_ONLY"
    assert AUTHORITY["qualification_authority"] == "NONE"
    assert AUTHORITY["evidence_acceptance_authority"] == "NONE"
    assert AUTHORITY["source_independence_authority"] == "NONE"
    assert AUTHORITY["truth_authority"] == "NONE"
    assert AUTHORITY["budget_authority"] == "NONE"
