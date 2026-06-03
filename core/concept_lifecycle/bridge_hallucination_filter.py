# ============================================
# NEXRYN BRIDGE HALLUCINATION FILTER
# ============================================


class BridgeHallucinationFilter:

    HALLUCINATION_TOKENS = [
        "bridge",
        "object",
        "identity",
        "preservation",
        "topological",
        "replication",
        "propagation",
        "growth",
    ]

    def pressure(self, context):

        reports = [
            context.get(
                "cognitive_immune_system_report",
                {},
            ),
            context.get(
                "cognitive_immune_system_v2_report",
                {},
            ),
            context.get(
                "semantic_legitimacy_report",
                {},
            ),
        ]

        latent_conflicts = max([
            report.get(
                "latent_conflict_count",
                0,
            )
            for report in reports
        ] or [0])

        repairs = max([
            report.get(
                "repair_required_count",
                0,
            )
            for report in reports
        ] or [0])

        return {
            "latent_conflict_count":
            latent_conflicts,

            "repair_required_count":
            repairs,

            "pressure_state":
            (
                "critical"
                if latent_conflicts >= 40 or repairs >= 80
                else "elevated"
                if latent_conflicts >= 12 or repairs >= 24
                else "normal"
            ),
        }

    def bridge_risk(self, concept_name):

        tokens = [
            token
            for token in str(
                concept_name,
            ).split(
                "_"
            )
            if token
        ]

        token_hits = len([
            token
            for token in tokens
            if token in self.HALLUCINATION_TOKENS
        ])

        return {
            "tokens":
            tokens,

            "token_hits":
            token_hits,

            "is_hybrid_bridge":
            (
                bool(
                    tokens,
                )
                and tokens[0] == "bridge"
                and len(
                    tokens,
                )
                >= 4
                and token_hits >= 3
            ),
        }

    def evidence_score(self, concept, promotion_decisions):

        name = concept.get(
            "concept",
        )

        promotion = promotion_decisions.get(
            name,
            {},
        )

        task_count = max(
            int(
                concept.get(
                    "task_count",
                    0,
                )
                or 0
            ),
            int(
                promotion.get(
                    "task_count",
                    0,
                )
                or 0
            ),
        )

        usefulness = max(
            float(
                concept.get(
                    "execution_usefulness",
                    0.0,
                )
                or 0.0
            ),
            float(
                promotion.get(
                    "average_execution_usefulness",
                    0.0,
                )
                or 0.0
            ),
        )

        identity_continuity = max(
            float(
                concept.get(
                    "identity_continuity",
                    0.0,
                )
                or 0.0
            ),
            float(
                promotion.get(
                    "average_identity_continuity",
                    0.0,
                )
                or 0.0
            ),
        )

        decision = promotion.get(
            "decision",
            concept.get(
                "decision",
                "latent",
            ),
        )

        score = 0.0

        if task_count >= 3:

            score += 0.35

        if usefulness >= 0.45:

            score += 0.25

        if identity_continuity >= 0.55:

            score += 0.25

        if decision == "promote":

            score += 0.15

        return round(
            min(
                1.0,
                score,
            ),
            4,
        )

    def filter(self, concepts, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        promotion_decisions = {
            item.get(
                "concept",
            ):
            item
            for item in context.get(
                "novelty_promotion_gate_report",
                {},
            ).get(
                "evaluations",
                [],
            )
        }

        pressure_report = self.pressure(
            context,
        )

        accepted = []
        quarantined = []

        for concept in concepts:

            name = concept.get(
                "concept",
                "unknown_concept",
            )

            risk = self.bridge_risk(
                name,
            )

            evidence = self.evidence_score(
                concept,
                promotion_decisions,
            )

            must_quarantine = (
                risk[
                    "is_hybrid_bridge"
                ]
                and (
                    evidence < 0.70
                    or pressure_report[
                        "pressure_state"
                    ]
                    == "critical"
                )
            )

            if must_quarantine:

                quarantined.append({
                    "concept":
                    name,

                    "status":
                    "quarantined_relation_hypothesis",

                    "reason":
                    "bridge_hallucination_risk",

                    "evidence_score":
                    evidence,

                    "tokens":
                    risk[
                        "tokens"
                    ],
                })

                continue

            accepted.append(
                concept,
            )

        return {
            "system":
            "bridge_hallucination_filter",

            "accepted_concepts":
            accepted,

            "quarantined_concepts":
            quarantined,

            "accepted_count":
            len(
                accepted,
            ),

            "quarantined_count":
            len(
                quarantined,
            ),

            "pressure":
            pressure_report,
        }
