# ============================================
# NEXRYN CONSTITUTIONAL REHEARSAL ENGINE
# ============================================


class ConstitutionalRehearsalEngine:

    def rehearsal(self, context):

        requested_action = context.get(
            "requested_action",
            "governed_runtime_cycle",
        )

        return {
            "requested_action":
            requested_action,

            "rehearsal_required":
            requested_action in [
                "direct_core_merge",
                "core_merge",
                "mutation",
                "fusion",
            ],

            "rehearsal_state":
            "rehearsed",
        }

    def simulation(self, context):

        memory_pressure = context.get(
            "memory_pressure_score",
            0.0,
        )

        return {
            "simulation_pressure":
            round(
                memory_pressure,
                4,
            ),

            "simulation_state":
            (
                "unsafe_simulation"
                if memory_pressure > 0.95
                else "safe_simulation"
            ),
        }

    def causal_replay(self, context):

        legitimacy = context.get(
            "semantic_legitimacy_report",
            {},
        )

        causal_score = legitimacy.get(
            "evidence_exports",
            {},
        ).get(
            "causal_attestation_score",
            0.0,
        )

        return {
            "causal_replay_score":
            round(
                float(
                    causal_score,
                ),
                4,
            ),

            "causal_replay_state":
            (
                "causal_replay_supported"
                if causal_score >= 0.34
                else "causal_replay_weak"
            ),
        }

    def constitutional_verification(
        self,
        rehearsal_report,
        simulation_report,
        causal_report,
    ):

        verified = (
            simulation_report.get(
                "simulation_state",
            )
            == "safe_simulation"
            and causal_report.get(
                "causal_replay_state",
            )
            == "causal_replay_supported"
        )

        return {
            "verified":
            verified,

            "verification_state":
            (
                "constitutionally_verified"
                if verified
                else "constitutional_rehearsal_failed"
            ),

            "direct_core_merge_allowed":
            (
                verified
                and rehearsal_report.get(
                    "requested_action",
                )
                != "direct_core_merge"
            ),
        }

    def run_cycle(self, context):

        rehearsal = self.rehearsal(
            context,
        )
        simulation = self.simulation(
            context,
        )
        causal = self.causal_replay(
            context,
        )
        verification = self.constitutional_verification(
            rehearsal,
            simulation,
            causal,
        )

        return {
            "system":
            "constitutional_rehearsal_engine",

            "rehearsal":
            rehearsal,

            "simulation":
            simulation,

            "causal_replay":
            causal,

            "constitutional_verification":
            verification,

            "rehearsal_state":
            verification.get(
                "verification_state",
            ),
        }


constitutional_rehearsal_engine = ConstitutionalRehearsalEngine()
