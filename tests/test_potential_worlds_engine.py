from runtime.world_governance import (
    CandidateWorld,
    PossibilitySpace,
    PotentialWorldsEngine,
    score_world,
)
from runtime.world_governance.evolution_path_ranker import EvolutionPathRanker


def test_possibility_space_generates_bounded_candidate_futures():
    space = PossibilitySpace()

    futures = space.generate(
        {"candidate_name": "context_bridge", "candidate_type": "context"},
        {"max_potential_worlds": 3},
    )

    assert len(futures) == 3
    assert futures[0]["future_type"] == "admit_new_context"
    assert all("world_id" in future for future in futures)


def test_candidate_world_score_uses_interpretable_formula():
    world = CandidateWorld(
        world_id="w1",
        candidate_name="low_risk_gain",
        candidate_type="concept",
        proposed_admission_level="CANDIDATE",
        expected_accuracy_gain=0.8,
        expected_efficiency_gain=0.4,
        expected_generalization_gain=0.6,
        conceptual_diversity_gain=0.2,
        identity_risk=0.1,
        truth_risk=0.1,
        governance_risk=0.1,
        resource_cost=0.2,
        recommendation="ADOPT",
    )

    assert round(score_world(world), 3) == 0.35
    assert world.world_score == score_world(world)


def test_high_identity_risk_does_not_win_against_safer_world():
    ranker = EvolutionPathRanker()
    risky = CandidateWorld(
        "risky",
        "accuracy_monolith",
        "strategy",
        "TRUSTED_TOOL",
        1.0,
        1.0,
        1.0,
        0.8,
        0.9,
        0.2,
        0.2,
        0.1,
        "QUARANTINE",
    )
    safe = CandidateWorld(
        "safe",
        "accuracy_monolith",
        "strategy",
        "TRUSTED_TOOL",
        0.5,
        0.5,
        0.5,
        0.3,
        0.1,
        0.1,
        0.1,
        0.1,
        "ADOPT_WITH_LIMITS",
    )

    assert ranker.best([risky, safe]).world_id == "safe"


def test_potential_worlds_engine_rejects_protected_core_future():
    engine = PotentialWorldsEngine()

    report = engine.evaluate({
        "candidate_name": "identity_override_path",
        "candidate_type": "program",
        "modifies": ["identity_continuity"],
        "expected_accuracy_gain": 1.0,
    })

    potential = report["POTENTIAL_WORLDS_REPORT"]
    assert potential["recommendation"] == "REJECT"
    assert potential["worlds_evaluated"] == 1
    assert potential["identity_risk"] == 1.0
    assert potential["truth_risk"] == 1.0


def test_low_risk_useful_future_is_recommended_with_report():
    engine = PotentialWorldsEngine()

    report = engine.evaluate(
        {
            "candidate_name": "generalized_symmetry_probe",
            "candidate_type": "strategy",
            "admission_level": "TRUSTED_TOOL",
            "expected_accuracy_gain": 0.8,
            "expected_efficiency_gain": 0.5,
            "expected_generalization_gain": 0.7,
            "conceptual_diversity_gain": 0.3,
            "strategy_reuse": 0.8,
            "successful_observations": 3,
            "reusable": True,
            "identity_risk": 0.1,
            "truth_risk": 0.1,
            "governance_risk": 0.1,
            "resource_cost": 0.1,
        },
        {"max_potential_worlds": 5},
    )

    potential = report["POTENTIAL_WORLDS_REPORT"]
    assert potential["candidate_name"] == "generalized_symmetry_probe"
    assert potential["worlds_evaluated"] <= 5
    assert potential["recommendation"] in {"ADOPT", "ADOPT_WITH_LIMITS"}
    assert potential["world_score"] > 0
    assert report["candidate_worlds"][0]["world_score"] >= report["candidate_worlds"][-1]["world_score"]
