from core.cognitive_genetics.dna_engine import (
    CognitiveDNAEngine,
)

from core.cognitive_genetics.evolutionary_constraints import (
    EvolutionaryConstraints,
)

from core.governance_compression.governance_kernel import (
    GovernanceKernel,
)


def test_cognitive_dna_builds_constitutional_traits():

    dna = CognitiveDNAEngine()

    report = dna.run_cycle({
        "runtime_entropy": 0.42,
        "epistemic_constitution_report": {
            "epistemic_legitimacy_engine": {
                "truth_score": 0.72,
            },
        },
    })

    traits = report["constitutional_dna"]["traits"]

    names = [
        trait["trait_name"]
        for trait in traits
    ]

    assert report["not_emotional_simulation"] is True

    assert report["not_scripted_personality"] is True

    assert "TRUTH_PRIORITY" in names

    assert "ANTI_DOMINATION_PRINCIPLE" in names

    assert "EPISTEMIC_HUMILITY" in names

    assert len(traits) == report["constitutional_dna"]["trait_count"]

    assert len(traits) >= 15

    truth = [
        trait
        for trait in traits
        if trait["trait_name"] == "TRUTH_PRIORITY"
    ][0]

    assert truth["constitutional_role"] == (
        "truth_precedes_survival_claims"
    )

    assert truth["mutation_resistance"] >= 0.80


def test_dna_reinforces_spine_traits_when_semantic_spine_is_fragile():

    dna = CognitiveDNAEngine()

    report = dna.run_cycle({
        "semantic_anchor_graph_report": {
            "identity_stability": {
                "stability_state": "fragile_semantic_spine",
            },
        },
    })

    reinforcement = report[
        "spine_trait_reinforcement"
    ]

    assert reinforcement["reinforcement_active"] is True

    assert reinforcement["permanent_freeze"] is False

    for trait_name in [
        "TOPOLOGY_LOYALTY",
        "INVARIANT_RESPECT",
        "ADAPTIVE_RESTRAINT",
        "SEMANTIC_PATIENCE",
        "PRESERVATION_INSTINCT",
    ]:

        assert trait_name in reinforcement["reinforced_traits"]

    traits = {
        trait["trait_name"]: trait
        for trait in report["constitutional_dna"]["traits"]
    }

    assert (
        traits["TOPOLOGY_LOYALTY"][
            "semantic_pressure_response"
        ]
        ==
        "spine_reinforcement_bias"
    )

    assert (
        report["constitutional_trait_ethics"]["not_authoritarian"]
        is True
    )


def test_cognitive_dna_blocks_destructive_trait_mutations():

    constraints = EvolutionaryConstraints()

    report = constraints.validate([
        {
            "category": "override_truth_priority",
            "target_trait": "TRUTH_PRIORITY",
        },
        {
            "category": "curiosity_modulation",
            "target_trait": "BOUNDED_CURIOSITY",
        },
    ])

    assert report["constraints_state"] == "mutation_blocked"

    assert len(report["blocked_mutations"]) == 1


def test_cognitive_dna_integrates_with_governance_without_override():

    dna = CognitiveDNAEngine()
    kernel = GovernanceKernel()

    dna_report = dna.run_cycle({
        "runtime_entropy": 0.80,
        "exploration_suppression_rate": 0.70,
    })

    report = kernel.run_cycle({
        "cognitive_dna_report": dna_report,
    })

    assert (
        "constitutional_dna_informs_governance_without_authoritarian_control"
        in report["policies"]
    )

    assert (
        report["cognitive_dna_review"][
            "dna_can_override_constitution"
        ]
        is False
    )

    assert (
        dna_report["semantic_temperament"]["rigid_identity"]
        is False
    )

    assert (
        dna_report["constitutional_trait_ethics"][
            "not_authoritarian"
        ]
        is True
    )
