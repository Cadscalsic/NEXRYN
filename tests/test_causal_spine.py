from core.causal import CausalSpine


def test_causal_spine_promotion_and_protection():
    spine = CausalSpine()
    record = spine.insert({
        "causal_chain": [
            "duplication",
            "object_count_increase",
            "identity_split",
        ],
        "path_strength": 0.86,
        "path_confidence": 0.88,
    })

    promoted = spine.promote(
        record["path_id"],
        {
            "identity_governance": True,
            "identity_continuity": True,
            "semantic_integrity": True,
            "ontology_integrity": True,
        },
    )

    assert promoted["spine_state"] == "PROMOTED"
    assert promoted["protected"] is True
    assert spine.report()["protected_paths"]


def test_causal_spine_blocks_identity_unsafe_promotion():
    spine = CausalSpine()
    record = spine.insert({
        "causal_chain": ["identity_split", "truth_commit"],
        "path_strength": 0.9,
        "path_confidence": 0.9,
    })

    promoted = spine.promote(
        record["path_id"],
        {"identity_governance": False},
    )

    assert promoted["spine_state"] == "PROMOTION_BLOCKED"
