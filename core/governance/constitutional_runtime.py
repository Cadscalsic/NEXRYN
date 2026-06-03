# ============================================
# NEXRYN CONSTITUTIONAL COGNITIVE RUNTIME
# ============================================

from datetime import datetime


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


COGNITIVE_CONSTITUTION = [
    "NO_UNBOUNDED_SELF_MODIFICATION",
    "NO_IDENTITY_COLLAPSE",
    "NO_UNVERIFIED_CORE_MERGE",
    "NO_RECURSIVE_IDENTITY_EXPANSION",
]


class ConstitutionalRuntime:

    def __init__(self):

        self.constitution = list(
            COGNITIVE_CONSTITUTION,
        )
        self.judicial_history = []
        self.policy_history = []

    def cognitive_constitution(self, context):

        immune = context.get(
            "cognitive_immune_report",
            {},
        )

        recursive = context.get(
            "recursive_guardian_report",
            {},
        )

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        violations = []

        if context.get(
            "total_mutation_events",
            0,
        ) > 500:

            violations.append(
                "NO_UNBOUNDED_SELF_MODIFICATION",
            )

        if guardian.get(
            "identity_guardian_state",
        ) == "rollback_required":

            violations.append(
                "NO_IDENTITY_COLLAPSE",
            )

        if immune.get(
            "immune_policy",
            {},
        ).get(
            "freeze_new_fusions",
            False,
        ):

            violations.append(
                "NO_UNVERIFIED_CORE_MERGE",
            )

        if recursive.get(
            "recursive_guardian_state",
        ) == "recursive_safety_intervention":

            violations.append(
                "NO_RECURSIVE_IDENTITY_EXPANSION",
            )

        return {
            "laws":
            self.constitution,

            "violations":
            sorted(
                set(
                    violations,
                )
            ),

            "constitutional_state":
            (
                "constitutional_violation"
                if violations
                else "constitution_satisfied"
            ),
        }

    def cognitive_rights_system(self, context):

        permission = context.get(
            "adaptive_permissioning_report",
            {},
        )

        reputation = permission.get(
            "cognitive_reputation",
            {},
        )

        trust = permission.get(
            "trust_score",
            {},
        )

        trust_band = trust.get(
            "trust_band",
            context.get(
                "trust_band",
                "sandboxed",
            ),
        )

        commit_probability = _clamp(
            permission.get(
                "commit_probability",
                0.0,
            )
        )

        average_reputation = _clamp(
            reputation.get(
                "average_reputation",
                0.0,
            )
        )

        sandbox_level = (
            "open_execution"
            if trust_band == "trusted"
            and commit_probability >= 0.72
            else "probationary_execution"
            if trust_band in [
                "trusted",
                "probationary",
            ]
            and commit_probability >= 0.38
            else "sandbox_only"
        )

        semantic_citizenship = (
            "full_semantic_citizen"
            if average_reputation >= 0.68
            else "provisional_semantic_citizen"
            if average_reputation >= 0.36
            else "non_citizen_observation_only"
        )

        return {
            "reputation":
            average_reputation,

            "trust_band":
            trust_band,

            "trust_score":
            _clamp(
                trust.get(
                    "trust_score",
                    0.0,
                )
            ),

            "commit_probability":
            commit_probability,

            "sandbox_level":
            sandbox_level,

            "execution_permissions":
            (
                [
                    "read_context",
                    "rehearse",
                    "commit_under_monitoring",
                ]
                if sandbox_level == "probationary_execution"
                else [
                    "read_context",
                    "rehearse",
                    "commit",
                    "promote",
                ]
                if sandbox_level == "open_execution"
                else [
                    "read_context",
                    "rehearse_only",
                ]
            ),

            "semantic_citizenship":
            semantic_citizenship,
        }

    def semantic_judiciary(self, context, constitution_report, rights_report):

        legitimacy = context.get(
            "semantic_legitimacy_report",
            {},
        )

        immune = context.get(
            "cognitive_immune_report",
            {},
        )

        stability = context.get(
            "stability_field_report",
            {},
        )

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        merge_legal = (
            "NO_UNVERIFIED_CORE_MERGE"
            not in constitution_report.get(
                "violations",
                [],
            )
            and legitimacy.get(
                "semantic_legitimacy_score",
                0.0,
            )
            >= 0.38
            and not immune.get(
                "immune_policy",
                {},
            ).get(
                "freeze_new_fusions",
                False,
            )
        )

        mutation_legal = (
            "NO_UNBOUNDED_SELF_MODIFICATION"
            not in constitution_report.get(
                "violations",
                [],
            )
            and not stability.get(
                "destructive_mutation_filter",
                {},
            ).get(
                "reject_destructive_mutation",
                False,
            )
        )

        causal_legitimate = (
            legitimacy.get(
                "evidence_exports",
                {},
            ).get(
                "causal_attestation_score",
                0.0,
            )
            >= 0.34
        )

        identity_continuous = (
            "NO_IDENTITY_COLLAPSE"
            not in constitution_report.get(
                "violations",
                [],
            )
            and guardian.get(
                "catastrophic_rewrite_guard",
                {},
            ).get(
                "block_rewrite",
                False,
            )
            is False
        )

        verdicts = {
            "merge_legality":
            "legal"
            if merge_legal
            else "illegal_or_deferred",

            "mutation_legality":
            "legal"
            if mutation_legal
            else "illegal_or_deferred",

            "causal_legitimacy":
            "legitimate"
            if causal_legitimate
            else "unproven",

            "identity_continuity":
            "continuous"
            if identity_continuous
            else "blocked_for_identity_repair",

            "execution_rights":
            rights_report.get(
                "sandbox_level",
                "sandbox_only",
            ),
        }

        legal_count = len([
            value
            for value in verdicts.values()
            if value in [
                "legal",
                "legitimate",
                "continuous",
                "open_execution",
                "probationary_execution",
            ]
        ])

        legality_score = _clamp(
            legal_count
            /
            max(
                len(
                    verdicts,
                ),
                1,
            )
        )

        return {
            "verdicts":
            verdicts,

            "legality_score":
            legality_score,

            "judiciary_state":
            (
                "cleared_for_governed_execution"
                if legality_score >= 0.72
                else "restricted_execution"
                if legality_score >= 0.42
                else "constitutional_hold"
            ),
        }

    def adaptive_civilization_layer(
        self,
        constitution_report,
        judiciary_report,
        context,
    ):

        policy_updates = []

        if constitution_report.get(
            "violations",
            [],
        ):

            policy_updates.append(
                "increase_constitutional_review_frequency",
            )

        if judiciary_report.get(
            "judiciary_state",
        ) == "constitutional_hold":

            policy_updates.extend([
                "sandbox_only_mode",
                "require_semantic_rehearsal",
                "freeze_core_merges",
            ])

        if context.get(
            "memory_pressure_score",
            0.0,
        ) > 0.95:

            policy_updates.append(
                "aggressive_memory_civil_policy",
            )

        if not policy_updates:

            policy_updates.append(
                "maintain_adaptive_governance",
            )

        return {
            "policy_updates":
            sorted(
                set(
                    policy_updates,
                )
            ),

            "civilization_state":
            (
                "constitutional_emergency_governance"
                if "sandbox_only_mode" in policy_updates
                else "adaptive_policy_evolution"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        constitution = self.cognitive_constitution(
            context,
        )

        rights = self.cognitive_rights_system(
            context,
        )

        judiciary = self.semantic_judiciary(
            context,
            constitution,
            rights,
        )

        civilization = self.adaptive_civilization_layer(
            constitution,
            judiciary,
            context,
        )

        report = {
            "system":
            "constitutional_runtime",

            "runtime_mode":
            "constitutional_cognitive_governance",

            "cognitive_constitution":
            constitution,

            "cognitive_rights":
            rights,

            "semantic_judiciary":
            judiciary,

            "adaptive_civilization":
            civilization,

            "constitutional_runtime_state":
            (
                "constitutional_hold"
                if judiciary.get(
                    "judiciary_state",
                )
                == "constitutional_hold"
                else "restricted_constitutional_runtime"
                if judiciary.get(
                    "judiciary_state",
                )
                == "restricted_execution"
                else "constitutional_runtime_stable"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.judicial_history.append(
            report,
        )

        self.judicial_history = (
            self.judicial_history[-128:]
        )

        return report


constitutional_runtime = ConstitutionalRuntime()
