# ============================================
# NEXRYN CIVILIZATIONAL POLICY ENGINE
# ============================================


class CivilizationalPolicyEngine:

    def emergency_governance(self, context, court_report):

        memory_pressure = context.get(
            "memory_pressure_score",
            0.0,
        )

        constitutional_state = context.get(
            "constitutional_runtime_report",
            {},
        ).get(
            "constitutional_runtime_state",
            "unknown",
        )

        emergency = (
            memory_pressure > 0.95
            or constitutional_state == "constitutional_hold"
            or court_report.get(
                "court_state",
            ) == "semantic_injunction"
        )

        return {
            "emergency_active":
            emergency,

            "emergency_state":
            (
                "emergency_governance"
                if emergency
                else "normal_governance"
            ),
        }

    def adaptive_lockdown(self, context, emergency_report):

        lockdown_level = (
            "hard_lockdown"
            if emergency_report.get(
                "emergency_active",
                False,
            )
            and context.get(
                "memory_pressure_score",
                0.0,
            ) > 0.95
            else "soft_lockdown"
            if emergency_report.get(
                "emergency_active",
                False,
            )
            else "no_lockdown"
        )

        return {
            "lockdown_level":
            lockdown_level,

            "freeze_new_fusions":
            lockdown_level in [
                "hard_lockdown",
                "soft_lockdown",
            ],

            "sandbox_only_mode":
            lockdown_level == "hard_lockdown",
        }

    def semantic_sanctions(self, court_report):

        sanctions = []

        if not court_report.get(
            "merge_legality",
            {},
        ).get(
            "merge_allowed",
            False,
        ):

            sanctions.append(
                "merge_sanction",
            )

        if not court_report.get(
            "mutation_legality",
            {},
        ).get(
            "mutation_allowed",
            False,
        ):

            sanctions.append(
                "mutation_sanction",
            )

        if court_report.get(
            "causal_ethics",
            {},
        ).get(
            "causal_ethics_state",
        ) == "causal_ethics_unproven":

            sanctions.append(
                "causal_rehearsal_required",
            )

        return {
            "sanctions":
            sanctions,

            "sanction_state":
            (
                "semantic_sanctions_active"
                if sanctions
                else "no_semantic_sanctions"
            ),
        }

    def permission_diplomacy(self, context, sanctions_report):

        rights = context.get(
            "constitutional_runtime_report",
            {},
        ).get(
            "cognitive_rights",
            {},
        )

        sandbox_level = rights.get(
            "sandbox_level",
            "sandbox_only",
        )

        if sanctions_report.get(
            "sanctions",
            [],
        ):

            negotiated_permission = "rehearsal_only"

        elif sandbox_level == "open_execution":

            negotiated_permission = "governed_execution"

        else:

            negotiated_permission = "probationary_execution"

        return {
            "negotiated_permission":
            negotiated_permission,

            "permission_diplomacy_state":
            (
                "permission_restricted"
                if negotiated_permission == "rehearsal_only"
                else "permission_negotiated"
            ),
        }

    def run_cycle(self, context, court_report):

        emergency = self.emergency_governance(
            context,
            court_report,
        )
        lockdown = self.adaptive_lockdown(
            context,
            emergency,
        )
        sanctions = self.semantic_sanctions(
            court_report,
        )
        diplomacy = self.permission_diplomacy(
            context,
            sanctions,
        )

        return {
            "system":
            "civilizational_policy_engine",

            "emergency_governance":
            emergency,

            "adaptive_lockdown":
            lockdown,

            "semantic_sanctions":
            sanctions,

            "permission_diplomacy":
            diplomacy,

            "policy_state":
            (
                "civilizational_emergency"
                if emergency.get(
                    "emergency_active",
                    False,
                )
                else "civilizational_policy_stable"
            ),
        }


civilizational_policy_engine = CivilizationalPolicyEngine()
