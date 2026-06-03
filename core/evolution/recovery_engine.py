# ============================================
# NEXRYN TRAIT RECOVERY ENGINE
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


class TraitRecoveryEngine:

    def __init__(self, recovery_threshold=0.58):

        self.recovery_threshold = recovery_threshold
        self.recovery_history = []
        self.recovered_traits = {}

    def _trait_id(self, trait):

        return trait.get(
            "id",
            trait.get(
                "trait_id",
                trait.get(
                    "trait",
                    "unknown",
                ),
            ),
        )

    def monitor_extinct_traits(self, context):

        extinction = context.get(
            "extinction_engine_report",
            {},
        )

        extinct = []

        for trait in extinction.get(
            "extinct_traits",
            [],
        ):

            extinct.append({
                "trait_id":
                self._trait_id(
                    trait,
                ),

                "reason":
                "active_extinction_report",

                "trait_snapshot":
                trait,
            })

        extinct.extend(
            extinction.get(
                "extinction_archive",
                [],
            )
        )

        by_id = {}

        for item in extinct:

            trait = item.get(
                "trait_snapshot",
                item,
            )

            trait_id = self._trait_id(
                trait,
            )

            by_id[
                trait_id
            ] = {
                "trait_id":
                trait_id,

                "reason":
                item.get(
                    "reason",
                    "unknown_extinction_reason",
                ),

                "trait_snapshot":
                trait,

                "timestamp":
                item.get(
                    "timestamp",
                    "",
                ),
            }

        return list(
            by_id.values()
        )

    def analyze_extinction_reason(self, extinct_trait, context):

        trait = extinct_trait.get(
            "trait_snapshot",
            {},
        )

        reason = extinct_trait.get(
            "reason",
            "",
        )

        entropy = _clamp(
            context.get(
                "runtime_entropy",
                context.get(
                    "cognitive_entropy_report",
                    {},
                ).get(
                    "runtime_entropy",
                    0.0,
                ),
            ),
        )

        ecology = context.get(
            "cognitive_ecology_report",
            {},
        )

        environmental_pressure = _clamp(
            ecology.get(
                "ecological_pressure_score",
                ecology.get(
                    "resource_pressure",
                    {},
                ).get(
                    "resource_pressure",
                    0.0,
                ),
            ),
        )

        legitimacy_score = _clamp(
            context.get(
                "semantic_legitimacy_report",
                {},
            ).get(
                "semantic_legitimacy_score",
                0.0,
            )
        )

        identity_stability = _clamp(
            context.get(
                "cognitive_homeostasis_report",
                {},
            ).get(
                "identity_stabilization",
                {},
            ).get(
                "identity_stability",
                context.get(
                    "identity_continuity",
                    0.0,
                ),
            )
        )

        past_fitness = _clamp(
            trait.get(
                "fitness",
                trait.get(
                    "net_fitness",
                    0.0,
                ),
            )
        )

        semantic_alignment = _clamp(
            trait.get(
                "semantic_alignment",
                0.0,
            )
        )

        environment_shift_score = _clamp(
            (
                1.0
                -
                entropy
            )
            * 0.32
            +
            environmental_pressure
            * 0.22
            +
            legitimacy_score
            * 0.24
            +
            identity_stability
            * 0.22
        )

        extinction_confidence = _clamp(
            (
                1.0
                -
                past_fitness
            )
            * 0.38
            +
            (
                1.0
                -
                semantic_alignment
            )
            * 0.24
            +
            entropy
            * 0.22
            +
            (
                1.0
                -
                identity_stability
            )
            * 0.16
        )

        wrongful_extinction_risk = _clamp(
            environment_shift_score
            -
            extinction_confidence * 0.42
            +
            semantic_alignment * 0.20
        )

        return {
            "trait_id":
            extinct_trait.get(
                "trait_id",
                self._trait_id(
                    trait,
                ),
            ),

            "extinction_reason":
            reason,

            "environment_shift_score":
            environment_shift_score,

            "extinction_confidence":
            extinction_confidence,

            "wrongful_extinction_risk":
            wrongful_extinction_risk,

            "analysis_state":
            (
                "review_extinction"
                if wrongful_extinction_risk >= 0.54
                else "extinction_likely_valid"
            ),
        }

    def resurrection_rehearsal(self, extinct_trait, analysis):

        trait = extinct_trait.get(
            "trait_snapshot",
            {},
        )

        base_fitness = _clamp(
            trait.get(
                "fitness",
                trait.get(
                    "net_fitness",
                    0.0,
                ),
            )
        )

        semantic_alignment = _clamp(
            trait.get(
                "semantic_alignment",
                0.0,
            )
        )

        stability = _clamp(
            trait.get(
                "stability_score",
                0.0,
            )
        )

        resurrection_score = _clamp(
            analysis.get(
                "environment_shift_score",
                0.0,
            )
            * 0.34
            +
            analysis.get(
                "wrongful_extinction_risk",
                0.0,
            )
            * 0.28
            +
            semantic_alignment
            * 0.18
            +
            stability
            * 0.12
            +
            base_fitness
            * 0.08
        )

        return {
            "trait_id":
            extinct_trait.get(
                "trait_id",
                self._trait_id(
                    trait,
                ),
            ),

            "resurrection_score":
            resurrection_score,

            "rehearsal_state":
            (
                "resurrection_candidate"
                if resurrection_score >= self.recovery_threshold
                else "remain_extinct"
            ),
        }

    def recover_trait(self, extinct_trait, rehearsal):

        trait = dict(
            extinct_trait.get(
                "trait_snapshot",
                {},
            )
        )

        trait_id = self._trait_id(
            trait,
        )

        trait[
            "trait_state"
        ] = "emerging"

        trait[
            "recovery_status"
        ] = "probationary_resurrection"

        trait[
            "resurrection_score"
        ] = rehearsal.get(
            "resurrection_score",
            0.0,
        )

        trait[
            "mutation_rate"
        ] = _clamp(
            trait.get(
                "mutation_rate",
                0.1,
            )
            * 0.52
        )

        self.recovered_traits[
            trait_id
        ] = trait

        return trait

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        monitored = self.monitor_extinct_traits(
            context,
        )

        analyses = []
        rehearsals = []
        resurrection_candidates = []
        recovered_traits = []
        wrongful_extinction_alerts = []

        for extinct_trait in monitored:

            analysis = self.analyze_extinction_reason(
                extinct_trait,
                context,
            )

            rehearsal = self.resurrection_rehearsal(
                extinct_trait,
                analysis,
            )

            analyses.append(
                analysis,
            )

            rehearsals.append(
                rehearsal,
            )

            if rehearsal.get(
                "rehearsal_state",
            ) == "resurrection_candidate":

                resurrection_candidates.append(
                    extinct_trait,
                )

                recovered_traits.append(
                    self.recover_trait(
                        extinct_trait,
                        rehearsal,
                    )
                )

            if analysis.get(
                "wrongful_extinction_risk",
                0.0,
            ) >= 0.64:

                wrongful_extinction_alerts.append(
                    analysis,
                )

        report = {
            "system":
            "trait_recovery_engine",

            "recovery_mode":
            "extinction_review_resurrection_rehearsal",

            "monitored_extinct_traits":
            monitored,

            "extinction_analyses":
            analyses,

            "resurrection_rehearsals":
            rehearsals,

            "resurrection_candidates":
            resurrection_candidates,

            "recovered_traits":
            recovered_traits,

            "wrongful_extinction_alerts":
            wrongful_extinction_alerts,

            "monitored_count":
            len(
                monitored,
            ),

            "recovered_count":
            len(
                recovered_traits,
            ),

            "wrongful_extinction_risk_count":
            len(
                wrongful_extinction_alerts,
            ),

            "recovery_state":
            (
                "resurrection_active"
                if recovered_traits
                else "extinction_review_active"
                if monitored
                else "no_extinct_traits_to_review"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.recovery_history.append(
            report,
        )

        self.recovery_history = (
            self.recovery_history[-128:]
        )

        return report


trait_recovery_engine = TraitRecoveryEngine()
