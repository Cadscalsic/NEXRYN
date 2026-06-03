from core.constitutional_core import ConstitutionalCore
from core.epistemic_certainty_engine import EpistemicCertaintyEngine
from core.contradiction_engine import ContradictionEngine
from core.semantic_lock_manager import SemanticLockManager


def test_constitutional_core_blocks_forbidden_mutation():

    context = {
        "mutation_proposals": [
            "core_kernel",
            "identity_spine",
        ],
        "identity_pressure": 0.52,
    }

    report = ConstitutionalCore().evaluate(
        context,
    )

    assert report["constitutional_state"] == "core_locked"
    assert "core_kernel" in report["attempted_forbidden_mutations"]
    assert "identity_spine" in report["attempted_invariant_mutations"]
    assert "engage_identity_preservation_axioms" in report["constitutional_actions"]


def test_epistemic_certainty_engine_identifies_low_certainty():

    context = {
        "truth_confidence": 0.18,
        "abstraction_validity": 0.28,
        "causal_coherence": 0.14,
        "contradiction_likelihood": 0.85,
    }

    report = EpistemicCertaintyEngine().assess(
        context,
    )

    assert report["epistemic_state"] == "epistemic_understanding_gap"
    assert "require_epistemic_review" in report["recommended_actions"]
    assert report["certainty_score"] < 0.40


def test_contradiction_engine_detects_recursive_inconsistency():

    context = {
        "semantic_contradictions": [
            {"source": "A", "target": "B", "type": "semantic"},
        ],
        "causal_relation_map": {
            "A": ["B"],
            "B": ["A"],
        },
    }

    report = ContradictionEngine().analyze(
        context,
    )

    assert report["contradiction_trace"]
    assert report["recursive_inconsistencies"]
    assert report["contradiction_severity"] > 0.0


def test_semantic_lock_manager_engages_for_core_violation():

    context = {
        "mutation_proposals": [
            "identity_matrix",
        ],
    }

    report = SemanticLockManager().manage(
        context,
    )

    assert report["semantic_lock_state"] == "semantic_lock_engaged"
    assert "constitutional_core_violation" in report["lock_reasons"]


def test_semantic_lock_manager_blocks_policy_changes_on_high_lock_in():

    context = {
        "abstraction_profiles": [
            "symbolic",
            "symbolic",
            "symbolic",
            "symbolic",
            "symbolic",
        ],
        "topology_profiles": [
            "grid",
            "grid",
            "grid",
            "grid",
        ],
        "perception_pattern_history": [
            "pattern_A",
            "pattern_A",
        ],
        "strategy_usage_history": [
            "search",
            "search",
            "search",
        ],
    }

    report = SemanticLockManager().manage(context)

    assert report["policy_blocked"] is True
    assert report["system_notifications"]
    assert any("lock-in" in n["message"] or "lock-in" in n["message"].lower() for n in report["system_notifications"]) or any("locking" in n["message"].lower() for n in report["system_notifications"])
