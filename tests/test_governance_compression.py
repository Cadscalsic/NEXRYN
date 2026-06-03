from core.governance_compression.governance_kernel import (
    GovernanceKernel,
)

from core.governance_compression.semantic_compression_engine import (
    SemanticCompressionEngine,
)


def test_semantic_compression_factorizes_bridge_concepts():

    engine = SemanticCompressionEngine()

    assert (
        engine.canonical_encode(
            "bridge_object_identity_preservation_topological_growth"
        )
        ==
        "preservation.growth.topology"
    )


def test_governance_kernel_compresses_legacy_governance_stack():

    kernel = GovernanceKernel()

    context = {
        "runtime_entropy": 0.6757,
        "cognitive_kernel_report": {
            "active_mode": "stabilization_mode",
            "pressure_report": {
                "total_kernel_pressure": 0.82,
            },
        },
        "conceptive_neurogenesis_report": {
            "generated_concepts": [
                {
                    "concept": (
                        "bridge_object_identity_preservation_"
                        "topological_growth"
                    ),
                },
            ],
        },
    }

    report = kernel.run_cycle(
        context
    )

    assert report["system"] == "governance_kernel"

    assert "no_layer_proliferation" in report["policies"]

    assert (
        report["semantic_compression"]["encodings"][0][
            "canonical_encoding"
        ]
        ==
        "preservation.growth.topology"
    )

    assert (
        report["compatibility_reports"][
            "semantic_court_report"
        ][
            "status"
        ]
        ==
        "compressed_into_governance_kernel"
    )

    assert (
        report["runtime_energy_budget"][
            "subsystems"
        ][
            "governance_kernel"
        ][
            "governance_cost"
        ]
        >=
        0
    )


def test_identity_core_lock_blocks_unsupervised_invariant_rewrite():

    kernel = GovernanceKernel()

    report = kernel.run_cycle({
        "proposed_invariant_rewrites": [
            "causality",
            "identity",
        ],
        "identity_rewrite_gates": {
            "supervised_rewrite": True,
            "staged_rehearsal": False,
            "rollback_safe_mutation": True,
        },
    })

    assert (
        report["identity_core_lock"]["decision"]
        ==
        "blocked"
    )

    assert "identity_core_lock_enforced" in report["policies"]

    assert "identity_invariant_rewrite_blocked" in [
        signal.get(
            "signal",
        )
        for signal in report["signals"]
    ]


def test_epistemic_constitution_prioritizes_truth_over_survival():

    kernel = GovernanceKernel()

    context = {
        "runtime_entropy": 0.71,
        "semantic_drift": 0.64,
        "reputation_anchor_report": {
            "strength": 0.4284,
            "reputation_state": "epistemically_forming",
            "anchor_source": "concept_reputation_engine",
            "contradiction_load": 0.30,
            "failure_propagation_score": 0.42,
        },
        "concept_admission_pipeline_report": {
            "decision_counts": {
                "staged_rehearsal": 3,
                "historical_reputation_required": 2,
            },
            "evaluations": [
                {
                    "legitimacy_testing": {
                        "legitimacy_score": 0.38,
                    },
                },
            ],
        },
        "conceptive_neurogenesis_report": {
            "generated_count": 18,
        },
        "memory_pressure_score": 0.74,
    }

    report = kernel.run_cycle(
        context
    )

    constitution = report[
        "epistemic_constitution"
    ]

    judiciary = constitution[
        "epistemic_legitimacy_engine"
    ]

    ontology = constitution[
        "ontological_growth_constitution"
    ]

    values = constitution[
        "value_hierarchy_system"
    ][
        "values"
    ]

    executive = constitution[
        "executive_cognitive_governance"
    ]

    assert judiciary["survival_is_not_truth"] is True

    assert judiciary["decision"] != "epistemically_legitimate"

    assert (
        "require_epistemic_trial_before_truth_commit"
        in report["policies"]
    )

    assert values["truth"] > values["survival"]

    assert ontology["concept_birth_policy"] in [
        "quarantine_new_concepts",
        "freeze_ontology_growth",
    ]

    assert executive["conflict_resolution"]["truth_vs_survival"] == (
        "truth_precedes_survival_claims"
    )
