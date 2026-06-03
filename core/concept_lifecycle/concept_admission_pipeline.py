# ============================================
# NEXRYN MULTI-PHASE CONCEPT ADMISSION PIPELINE
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


class ConceptAdmissionPipeline:

    CLASSIFICATION_TOKENS = {
        "causal": [
            "cause",
            "causal",
            "effect",
            "temporal",
        ],
        "structural": [
            "shape",
            "topology",
            "topological",
            "object",
            "structure",
        ],
        "symbolic": [
            "symbol",
            "mapping",
            "color",
            "rule",
        ],
        "metaphorical": [
            "bridge",
            "analogy",
            "metaphor",
        ],
        "invariant": [
            "identity",
            "consistency",
            "causality",
            "continuity",
        ],
        "adaptive": [
            "adaptive",
            "mutation",
            "variant",
            "growth",
            "propagation",
        ],
    }

    def semantic_drift(self, context):

        candidates = [
            context.get(
                "semantic_drift",
                None,
            ),
            context.get(
                "semantic_drift_detection",
                {},
            ).get(
                "semantic_drift",
                None,
            ),
            context.get(
                "identity_continuity_engine_report",
                {},
            ).get(
                "semantic_drift",
                None,
            ),
            context.get(
                "cognitive_spine_stabilizer_report",
                {},
            ).get(
                "semantic_drift",
                {},
            ).get(
                "semantic_drift",
                None,
            ),
        ]

        for candidate in candidates:

            if candidate is not None:

                return _clamp(
                    candidate,
                )

        return 0.0

    def compression_report(self, context):

        report = context.get(
            "memory_compression_report",
            {},
        )

        ratio = _clamp(
            report.get(
                "compression_ratio",
                1.0,
            )
        )

        original_count = int(
            report.get(
                "original_item_count",
                0,
            )
            or 0
        )

        retained_count = int(
            report.get(
                "retained_item_count",
                0,
            )
            or 0
        )

        overcompressed = (
            original_count >= 32
            and ratio <= 0.20
        )

        return {
            "original_item_count":
            original_count,

            "retained_item_count":
            retained_count,

            "compression_ratio":
            ratio,

            "overcompression_state":
            (
                "semantic_bone_loss_risk"
                if overcompressed
                else "compression_tolerable"
            ),
        }

    def classify(self, concept_name):

        tokens = [
            token
            for token in str(
                concept_name,
            ).split(
                "_"
            )
            if token
        ]

        scores = {}

        for concept_type, markers in self.CLASSIFICATION_TOKENS.items():

            scores[
                concept_type
            ] = len([
                token
                for token in tokens
                if token in markers
            ])

        concept_type = max(
            scores,
            key=scores.get,
        )

        if scores.get(
            concept_type,
            0,
        ) == 0:

            concept_type = "adaptive"

        return {
            "concept_type":
            concept_type,

            "tokens":
            tokens,

            "classification_scores":
            scores,
        }

    def legitimacy(self, birth, context):

        viability = _clamp(
            birth.get(
                "viability",
                0.0,
            )
        )

        entropy = _clamp(
            context.get(
                "runtime_entropy",
                0.0,
            )
        )

        drift = self.semantic_drift(
            context,
        )

        executable = (
            0.2
            +
            viability * 0.55
            +
            (1.0 - entropy) * 0.15
            +
            (1.0 - drift) * 0.10
        )

        contradiction_risk = _clamp(
            entropy * 0.35
            +
            drift * 0.45
            +
            (
                0.20
                if context.get(
                    "identity_state",
                    context.get(
                        "identity_continuity_engine_report",
                        {},
                    ).get(
                        "identity_state",
                        "",
                    ),
                )
                == "identity_fragile"
                else 0.0
            )
        )

        legitimacy_score = _clamp(
            executable
            -
            contradiction_risk * 0.35
        )

        return {
            "is_real_enough":
            viability >= 0.35,

            "is_executable":
            executable >= 0.42,

            "is_stable":
            drift < 0.78,

            "is_non_contradictory":
            contradiction_risk < 0.70,

            "legitimacy_score":
            legitimacy_score,

            "contradiction_risk":
            contradiction_risk,
        }

    def sandboxed_evolution(self, birth, context):

        sandbox_policy = context.get(
            "sandbox_policy",
            context.get(
                "concept_sandboxing_report",
                {},
            ).get(
                "sandbox_policy",
                "",
            ),
        )

        rehearsal_state = context.get(
            "mutation_rehearsal_report",
            {},
        ).get(
            "simulation_state",
            context.get(
                "simulation_state",
                "",
            ),
        )

        survived = (
            birth.get(
                "rehearsal_state",
            )
            == "survived_rehearsal"
            or context.get(
                "mutation_lineage_report",
                {},
            ).get(
                "lineage_state",
            )
            == "survived_rehearsal"
        )

        return {
            "sandbox_policy":
            sandbox_policy,

            "simulation_state":
            rehearsal_state,

            "survived_rehearsal":
            survived,

            "requires_rehearsal_before_commit":
            (
                sandbox_policy == "deny_commit"
                or rehearsal_state == "ambiguous"
            ),
        }

    def historical_reputation(self, birth, concept_registry, context):

        concept_id = birth.get(
            "concept_id",
        )

        concept_reputations = {
            item.get(
                "concept_id",
            ):
            item
            for item in context.get(
                "concept_reputation_report",
                {},
            ).get(
                "concept_reputations",
                [],
            )
        }

        concept_reputation = concept_reputations.get(
            concept_id,
            {},
        )

        existing = concept_registry.get(
            concept_id,
            {},
        )

        reputation = concept_reputation.get(
            "reputation",
            existing.get(
                "reputation",
                birth.get(
                    "reputation",
                    None,
                ),
            ),
        )

        if reputation is None:

            reputation = context.get(
                "cognitive_reputation",
                context.get(
                    "constitutional_runtime_report",
                    {},
                ).get(
                    "cognitive_reputation",
                    {},
                ),
            ).get(
                "average_reputation",
                0.0,
            )

        reputation = _clamp(
            reputation,
        )

        return {
            "reputation":
            reputation,

            "historical_consistency":
            concept_reputation.get(
                "historical_consistency",
                reputation,
            ),

            "causal_reliability":
            concept_reputation.get(
                "causal_reliability",
                reputation,
            ),

            "long_term_usefulness":
            concept_reputation.get(
                "long_term_usefulness",
                reputation,
            ),

            "contradiction_history":
            concept_reputation.get(
                "contradiction_history",
                0.0,
            ),

            "recovery_success":
            concept_reputation.get(
                "recovery_success",
                0.0,
            ),

            "failure_propagation_score":
            concept_reputation.get(
                "failure_propagation_score",
                0.0,
            ),

            "reputation_state":
            (
                "trusted"
                if reputation >= 0.68
                else "provisional"
                if reputation >= 0.36
                else "missing_or_weak"
            ),

            "survival_is_not_truth":
            True,
        }

    def constitutional_validation(self, birth, classification, context):

        invariant_tokens = [
            token
            for token in classification.get(
                "tokens",
                [],
            )
            if token in [
                "causality",
                "identity",
                "consistency",
                "continuity",
            ]
        ]

        lock = context.get(
            "identity_core_lock_report",
            {},
        )

        blocked = (
            lock.get(
                "decision",
            )
            == "blocked"
            and bool(
                invariant_tokens,
            )
        )

        return {
            "constitutional_state":
            (
                "invariant_rewrite_blocked"
                if blocked
                else "constitutionally_clear"
            ),

            "invariant_tokens":
            invariant_tokens,
        }

    def integration_decision(
        self,
        legitimacy,
        sandbox,
        reputation,
        constitutional,
        compression,
        drift,
    ):

        if constitutional.get(
            "constitutional_state",
        ) == "invariant_rewrite_blocked":

            return "reject"

        if (
            compression.get(
                "overcompression_state",
            )
            == "semantic_bone_loss_risk"
            or drift >= 0.86
        ):

            return "staged_rehearsal"

        if sandbox.get(
            "requires_rehearsal_before_commit",
            False,
        ):

            return "staged_rehearsal"

        if not all([
            legitimacy.get(
                "is_real_enough",
                False,
            ),
            legitimacy.get(
                "is_executable",
                False,
            ),
            legitimacy.get(
                "is_non_contradictory",
                False,
            ),
        ]):

            return "reject"

        if (
            reputation.get(
                "reputation_state",
            )
            == "missing_or_weak"
            and (
                drift >= 0.60
                or sandbox.get(
                    "requires_rehearsal_before_commit",
                    False,
                )
                or compression.get(
                    "overcompression_state",
                )
                == "semantic_bone_loss_risk"
                or reputation.get(
                    "contradiction_history",
                    0.0,
                )
                >= 0.12
                or reputation.get(
                    "failure_propagation_score",
                    0.0,
                )
                >= 0.50
            )
        ):

            return "historical_reputation_required"

        return "controlled_integration"

    def evaluate(self, births, concept_registry, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        compression = self.compression_report(
            context,
        )

        drift = self.semantic_drift(
            context,
        )

        evaluations = []

        for birth in births.get(
            "births",
            [],
        ):

            classification = self.classify(
                birth.get(
                    "concept",
                    "",
                )
            )

            legitimacy = self.legitimacy(
                birth,
                context,
            )

            sandbox = self.sandboxed_evolution(
                birth,
                context,
            )

            reputation = self.historical_reputation(
                birth,
                concept_registry,
                context,
            )

            constitutional = self.constitutional_validation(
                birth,
                classification,
                context,
            )

            decision = self.integration_decision(
                legitimacy,
                sandbox,
                reputation,
                constitutional,
                compression,
                drift,
            )

            evaluations.append({
                "concept_id":
                birth.get(
                    "concept_id",
                ),

                "concept":
                birth.get(
                    "concept",
                ),

                "observation":
                {
                    "source":
                    birth.get(
                        "origin",
                        "unknown",
                    ),

                    "viability":
                    birth.get(
                        "viability",
                        0.0,
                    ),
                },

                "semantic_classification":
                classification,

                "legitimacy_testing":
                legitimacy,

                "sandboxed_evolution":
                sandbox,

                "historical_reputation":
                reputation,

                "constitutional_validation":
                constitutional,

                "controlled_integration":
                {
                    "decision":
                    decision,

                    "integration_mode":
                    (
                        "gradual_commit"
                        if decision == "controlled_integration"
                        else "hold_outside_core"
                    ),
                },
            })

        return {
            "system":
            "multi_phase_concept_admission_pipeline",

            "phases":
            [
                "observation",
                "semantic_classification",
                "legitimacy_testing",
                "sandboxed_evolution",
                "historical_reputation",
                "constitutional_validation",
                "controlled_integration",
            ],

            "semantic_drift":
            drift,

            "compression":
            compression,

            "evaluations":
            evaluations,

            "decision_counts":
            {
                decision:
                len([
                    item
                    for item in evaluations
                    if item.get(
                        "controlled_integration",
                        {},
                    ).get(
                        "decision",
                    )
                    == decision
                ])
                for decision in [
                    "controlled_integration",
                    "staged_rehearsal",
                    "historical_reputation_required",
                    "reject",
                ]
            },
        }
