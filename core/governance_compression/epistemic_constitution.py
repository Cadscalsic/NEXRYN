# ============================================
# NEXRYN EPISTEMIC CONSTITUTION
# ============================================


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class EpistemicConstitution:

    def reputation(self, context):

        anchor = context.get(
            "reputation_anchor_report",
            {},
        )

        if anchor:

            return {
                "strength":
                _clamp(
                    anchor.get(
                        "strength",
                        0.0,
                    )
                ),

                "state":
                anchor.get(
                    "reputation_state",
                    "unknown",
                ),

                "source":
                anchor.get(
                    "anchor_source",
                    "unknown",
                ),
            }

        concept_reputation = context.get(
            "concept_reputation_engine_report",
            {},
        )

        return {
            "strength":
            _clamp(
                concept_reputation.get(
                    "average_concept_reputation",
                    0.0,
                )
            ),

            "state":
            concept_reputation.get(
                "reputation_state",
                "unknown",
            ),

            "source":
            "concept_reputation_engine",
        }

    def epistemic_judiciary(self, context):

        reputation = self.reputation(
            context,
        )

        admission = context.get(
            "concept_admission_pipeline_report",
            {},
        )

        legitimacy_scores = [
            item.get(
                "legitimacy_testing",
                {},
            ).get(
                "legitimacy_score",
                0.0,
            )
            for item in admission.get(
                "evaluations",
                [],
            )
        ]

        average_legitimacy = _clamp(
            sum(
                legitimacy_scores,
            )
            /
            max(
                len(
                    legitimacy_scores,
                ),
                1,
            )
        )

        contradiction_load = _clamp(
            context.get(
                "reputation_anchor_report",
                {},
            ).get(
                "contradiction_load",
                0.0,
            )
        )

        failure_propagation = _clamp(
            context.get(
                "reputation_anchor_report",
                {},
            ).get(
                "failure_propagation_score",
                0.0,
            )
        )

        truth_score = _clamp(
            average_legitimacy * 0.42
            +
            reputation[
                "strength"
            ]
            * 0.40
            +
            (1.0 - contradiction_load) * 0.10
            +
            (1.0 - failure_propagation) * 0.08
        )

        stability_score = _clamp(
            1.0
            -
            context.get(
                "runtime_entropy",
                0.0,
            )
            * 0.45
            -
            context.get(
                "semantic_drift",
                0.0,
            )
            * 0.35
        )

        spread_score = _clamp(
            context.get(
                "conceptive_neurogenesis_report",
                {},
            ).get(
                "generated_count",
                0,
            )
            / 24
        )

        parasitic_risk = _clamp(
            spread_score * 0.35
            +
            failure_propagation * 0.35
            +
            contradiction_load * 0.30
        )

        decision = (
            "epistemically_legitimate"
            if truth_score >= 0.68
            and parasitic_risk < 0.35
            else "requires_epistemic_trial"
            if truth_score >= 0.42
            else "epistemically_untrusted"
        )

        return {
            "system":
            "epistemic_legitimacy_engine",

            "judiciary_scope":
            [
                "truth",
                "stability",
                "spread",
                "power",
                "imitation",
                "parasitism",
            ],

            "truth_score":
            truth_score,

            "stability_score":
            stability_score,

            "spread_score":
            spread_score,

            "parasitic_risk":
            parasitic_risk,

            "reputation_strength":
            reputation[
                "strength"
            ],

            "reputation_state":
            reputation[
                "state"
            ],

            "decision":
            decision,

            "survival_is_not_truth":
            True,
        }

    def ontological_growth_constitution(self, context, judiciary):

        admission = context.get(
            "concept_admission_pipeline_report",
            {},
        )

        decision_counts = admission.get(
            "decision_counts",
            {},
        )

        staged = decision_counts.get(
            "staged_rehearsal",
            0,
        )

        reputation_required = decision_counts.get(
            "historical_reputation_required",
            0,
        )

        entropy = _clamp(
            context.get(
                "runtime_entropy",
                0.0,
            )
        )

        drift = _clamp(
            context.get(
                "semantic_drift",
                0.0,
            )
        )

        growth_pressure = _clamp(
            staged * 0.05
            +
            reputation_required * 0.06
            +
            entropy * 0.35
            +
            drift * 0.35
        )

        causal_value = _clamp(
            judiciary.get(
                "truth_score",
                0.0,
            )
        )

        policy = (
            "freeze_ontology_growth"
            if growth_pressure >= 0.76
            else "quarantine_new_concepts"
            if growth_pressure >= 0.52
            else "allow_costed_birth"
        )

        return {
            "system":
            "ontological_growth_constitution",

            "laws":
            [
                "concept_birth_requires_epistemic_value",
                "growth_pays_entropy_cost",
                "causal_value_must_exceed_fragmentation_risk",
                "bridge_hypotheses_are_not_concepts",
                "reputation_precedes_core_integration",
            ],

            "growth_pressure":
            growth_pressure,

            "causal_value":
            causal_value,

            "concept_birth_policy":
            policy,

            "freeze_new_fusions":
            policy == "freeze_ontology_growth",
        }

    def value_hierarchy(self, context, judiciary, ontology):

        truth = 0.30
        coherence = 0.20
        stability = 0.16
        survival = 0.14
        adaptability = 0.10
        exploration = 0.06
        autonomy = 0.04

        if judiciary.get(
            "decision",
        ) != "epistemically_legitimate":

            truth += 0.08
            exploration -= 0.03
            autonomy -= 0.02
            stability += 0.02

        if ontology.get(
            "concept_birth_policy",
        ) == "freeze_ontology_growth":

            stability += 0.06
            exploration -= 0.04
            adaptability -= 0.02

        values = {
            "truth":
            _clamp(truth),

            "coherence":
            _clamp(coherence),

            "stability":
            _clamp(stability),

            "survival":
            _clamp(survival),

            "adaptability":
            _clamp(adaptability),

            "exploration":
            _clamp(exploration),

            "autonomy":
            _clamp(autonomy),
        }

        return {
            "system":
            "value_hierarchy_system",

            "values":
            values,

            "ordering":
            [
                key
                for key, value in sorted(
                    values.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ],

            "anti_collapse_rule":
            "truth_over_survival_when_survival_lacks_legitimacy",
        }

    def resource_allocation(self, context, values, ontology):

        entropy = _clamp(
            context.get(
                "runtime_entropy",
                0.0,
            )
        )

        pressure = _clamp(
            context.get(
                "memory_pressure_score",
                context.get(
                    "working_memory_pressure",
                    0.0,
                ),
            )
        )

        allocations = {
            "attention_to_truth_validation":
            _clamp(
                values[
                    "truth"
                ]
                +
                entropy * 0.12
            ),

            "reasoning_to_causal_tests":
            _clamp(
                values[
                    "coherence"
                ]
                +
                values[
                    "truth"
                ]
                * 0.35
            ),

            "energy_to_stabilization":
            _clamp(
                values[
                    "stability"
                ]
                +
                pressure * 0.18
            ),

            "budget_to_exploration":
            _clamp(
                values[
                    "exploration"
                ]
                *
                (
                    0.35
                    if ontology.get(
                        "freeze_new_fusions",
                        False,
                    )
                    else 1.0
                )
            ),
        }

        return {
            "system":
            "resource_allocation_intelligence",

            "attention_economy":
            allocations,

            "resource_policy":
            (
                "truth_and_stability_first"
                if entropy >= 0.62 or pressure >= 0.62
                else "balanced_epistemic_growth"
            ),
        }

    def civilizational_ethics(self, judiciary, ontology, values):

        return {
            "system":
            "civilizational_ethics_layer",

            "rights_and_limits":
            {
                "delete_concepts":
                "allowed_only_after_reputation_failure_and_gc_review",

                "suppress_traits":
                "allowed_when_failure_propagation_exceeds_causal_value",

                "permit_extinction":
                "only_for_parasitic_or_contradictory_lineages",

                "identity_sacrifice":
                "forbidden_without_supervised_rewrite_and_rollback",

                "innovation_vs_stability":
                (
                    "stability_precedes_innovation"
                    if ontology.get(
                        "freeze_new_fusions",
                        False,
                    )
                    else "innovation_allowed_under_epistemic_trial"
                ),
            },

            "ethical_priority":
            (
                "prevent_false_survival"
                if judiciary.get(
                    "decision",
                )
                != "epistemically_legitimate"
                else "permit_responsible_growth"
            ),

            "highest_value":
            max(
                values,
                key=values.get,
            ),
        }

    def distributed_constitution(self, context, judiciary):

        agent_count = int(
            context.get(
                "agent_count",
                context.get(
                    "parallel_thread_count",
                    1,
                ),
            )
            or 1
        )

        return {
            "system":
            "distributed_constitutional_cognition",

            "federation_policy":
            (
                "single_agent_constitutional_mode"
                if agent_count <= 1
                else "federated_agents_require_shared_epistemic_court"
            ),

            "agent_count":
            agent_count,

            "shared_requirements":
            [
                "shared_value_hierarchy",
                "local_sandbox_write_barriers",
                "cross_agent_reputation_ledger",
                "no_agent_can_commit_false_survival",
            ],

            "commit_policy":
            (
                "federated_commit_blocked_until_legitimate"
                if judiciary.get(
                    "decision",
                )
                != "epistemically_legitimate"
                else "federated_commit_allowed_with_audit"
            ),
        }

    def executive_governance(
        self,
        judiciary,
        ontology,
        values,
        resources,
        ethics,
        distributed,
    ):

        if judiciary.get(
            "decision",
        ) == "epistemically_untrusted":

            mode = "epistemic_quarantine"
            action = "block_core_commit_and_start_truth_trial"

        elif ontology.get(
            "freeze_new_fusions",
            False,
        ):

            mode = "ontological_stabilization"
            action = "freeze_growth_and_reallocate_to_reputation"

        else:

            mode = "constitutional_growth"
            action = "allow_costed_growth_under_judiciary"

        return {
            "system":
            "executive_cognitive_governance",

            "executive_mode":
            mode,

            "selected_action":
            action,

            "conflict_resolution":
            {
                "truth_vs_survival":
                "truth_precedes_survival_claims",

                "stability_vs_exploration":
                (
                    "stability_wins_temporarily"
                    if resources.get(
                        "resource_policy",
                    )
                    == "truth_and_stability_first"
                    else "exploration_allowed_with_budget"
                ),

                "autonomy_vs_constitution":
                "constitution_precedes_unverified_autonomy",
            },

            "sacrifice_policy":
            ethics.get(
                "rights_and_limits",
                {},
            ),

            "distributed_commit_policy":
            distributed.get(
                "commit_policy",
            ),
        }

    def run_cycle(self, context):

        judiciary = self.epistemic_judiciary(
            context,
        )

        ontology = self.ontological_growth_constitution(
            context,
            judiciary,
        )

        values = self.value_hierarchy(
            context,
            judiciary,
            ontology,
        )

        resources = self.resource_allocation(
            context,
            values.get(
                "values",
                {},
            ),
            ontology,
        )

        ethics = self.civilizational_ethics(
            judiciary,
            ontology,
            values.get(
                "values",
                {},
            ),
        )

        distributed = self.distributed_constitution(
            context,
            judiciary,
        )

        executive = self.executive_governance(
            judiciary,
            ontology,
            values.get(
                "values",
                {},
            ),
            resources,
            ethics,
            distributed,
        )

        return {
            "system":
            "epistemic_constitution",

            "epistemic_legitimacy_engine":
            judiciary,

            "ontological_growth_constitution":
            ontology,

            "value_hierarchy_system":
            values,

            "resource_allocation_intelligence":
            resources,

            "civilizational_ethics_layer":
            ethics,

            "distributed_constitutional_cognition":
            distributed,

            "executive_cognitive_governance":
            executive,

            "constitutional_state":
            (
                "epistemic_trial_required"
                if judiciary.get(
                    "decision",
                )
                != "epistemically_legitimate"
                else "constitutional_cognition_stable"
            ),
        }
