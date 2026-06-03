# ============================================
# NEXRYN ENTROPY REGULATION SYSTEM
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


class EntropyRegulator:

    def __init__(self, storm_threshold=0.78):

        self.storm_threshold = storm_threshold
        self.entropy_history = []
        self.cooling_history = []

    def measure_entropy_delta(self, context):

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

        previous_entropy = (
            self.entropy_history[-1]
            if self.entropy_history
            else entropy
        )

        entropy_delta = round(
            entropy
            -
            previous_entropy,
            4,
        )

        self.entropy_history.append(
            entropy,
        )

        self.entropy_history = (
            self.entropy_history[-64:]
        )

        return {
            "runtime_entropy":
            entropy,

            "previous_entropy":
            previous_entropy,

            "entropy_delta":
            entropy_delta,

            "delta_state":
            (
                "rising_fast"
                if entropy_delta >= 0.12
                else "rising"
                if entropy_delta >= 0.04
                else "cooling"
                if entropy_delta <= -0.04
                else "stable"
            ),
        }

    def cognitive_cooling(self, entropy_report, context):

        entropy = entropy_report.get(
            "runtime_entropy",
            0.0,
        )

        entropy_delta = max(
            entropy_report.get(
                "entropy_delta",
                0.0,
            ),
            0.0,
        )

        identity = _clamp(
            context.get(
                "identity_continuity",
                context.get(
                    "cognitive_homeostasis_report",
                    {},
                ).get(
                    "identity_stabilization",
                    {},
                ).get(
                    "identity_stability",
                    0.0,
                ),
            )
        )

        cooling_factor = _clamp(
            1.0
            -
            max(
                entropy - 0.48,
                0.0,
            )
            * 1.20
            -
            entropy_delta
            * 0.56
            +
            identity
            * 0.06
        )

        cooling_intensity = _clamp(
            1.0
            -
            cooling_factor
        )

        return {
            "cooling_factor":
            cooling_factor,

            "cooling_intensity":
            cooling_intensity,

            "cooling_state":
            (
                "hard_cooling"
                if cooling_intensity >= 0.42
                else "soft_cooling"
                if cooling_intensity >= 0.18
                else "passive_cooling"
            ),
        }

    def _traits(self, context):

        return (
            context.get(
                "evolutionary_memory_report",
                {},
            )
            .get(
                "adaptive_trait_memory",
                {},
            )
            .get(
                "traits",
                [],
            )
        )

    def slow_mutation_rate(self, traits, cooling_report):

        regulated_traits = []

        cooling_factor = cooling_report.get(
            "cooling_factor",
            1.0,
        )

        for trait in traits:

            trait_id = trait.get(
                "id",
                trait.get(
                    "trait",
                    "unknown",
                ),
            )

            base_rate = _clamp(
                trait.get(
                    "mutation_rate",
                    0.1,
                )
            )

            cooled_rate = _clamp(
                base_rate
                *
                max(
                    cooling_factor,
                    0.08,
                )
            )

            regulated_traits.append({
                "trait_id":
                trait_id,

                "base_mutation_rate":
                base_rate,

                "cooled_mutation_rate":
                cooled_rate,

                "cooling_applied":
                _clamp(
                    base_rate
                    -
                    cooled_rate,
                ),
            })

        average_base_rate = _clamp(
            sum(
                item.get(
                    "base_mutation_rate",
                    0.0,
                )
                for item in regulated_traits
            )
            /
            max(
                len(
                    regulated_traits,
                ),
                1,
            )
        )

        average_cooled_rate = _clamp(
            sum(
                item.get(
                    "cooled_mutation_rate",
                    0.0,
                )
                for item in regulated_traits
            )
            /
            max(
                len(
                    regulated_traits,
                ),
                1,
            )
        )

        return {
            "regulated_traits":
            regulated_traits,

            "average_base_mutation_rate":
            average_base_rate,

            "average_cooled_mutation_rate":
            average_cooled_rate,
        }

    def prevent_mutation_storms(self, entropy_report, mutation_report):

        entropy = entropy_report.get(
            "runtime_entropy",
            0.0,
        )

        entropy_delta = entropy_report.get(
            "entropy_delta",
            0.0,
        )

        average_rate = mutation_report.get(
            "average_base_mutation_rate",
            0.0,
        )

        storm_pressure = _clamp(
            entropy * 0.62
            +
            max(
                entropy_delta,
                0.0,
            )
            * 1.15
            +
            average_rate
            * 0.45
        )

        return {
            "storm_pressure":
            storm_pressure,

            "storm_threshold":
            self.storm_threshold,

            "mutation_storm_state":
            (
                "storm_suppressed"
                if storm_pressure >= self.storm_threshold
                else "storm_watch"
                if storm_pressure >= 0.50
                else "storm_absent"
            ),
        }

    def stabilization_windows(self, entropy_report, storm_report):

        entropy = entropy_report.get(
            "runtime_entropy",
            0.0,
        )

        storm_pressure = storm_report.get(
            "storm_pressure",
            0.0,
        )

        window_strength = _clamp(
            entropy * 0.55
            +
            storm_pressure * 0.45
        )

        return {
            "window_strength":
            window_strength,

            "stabilization_window":
            (
                "freeze_new_mutations"
                if window_strength >= 0.78
                else "probationary_mutation_window"
                if window_strength >= 0.55
                else "normal_mutation_window"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        entropy_report = self.measure_entropy_delta(
            context,
        )

        cooling_report = self.cognitive_cooling(
            entropy_report,
            context,
        )

        mutation_report = self.slow_mutation_rate(
            self._traits(
                context,
            ),
            cooling_report,
        )

        storm_report = self.prevent_mutation_storms(
            entropy_report,
            mutation_report,
        )

        window_report = self.stabilization_windows(
            entropy_report,
            storm_report,
        )

        report = {
            "system":
            "entropy_regulator",

            "regulation_mode":
            "entropy_delta_cognitive_cooling",

            "entropy_delta_report":
            entropy_report,

            "cognitive_cooling":
            cooling_report,

            "mutation_rate_slowdown":
            mutation_report,

            "mutation_storm_control":
            storm_report,

            "stabilization_windows":
            window_report,

            "entropy_regulation_state":
            (
                "cooling_lock"
                if window_report.get(
                    "stabilization_window",
                ) == "freeze_new_mutations"
                else "cooling_active"
                if cooling_report.get(
                    "cooling_intensity",
                    0.0,
                ) >= 0.18
                else "entropy_stable"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.cooling_history.append(
            report,
        )

        self.cooling_history = (
            self.cooling_history[-128:]
        )

        return report


entropy_regulator = EntropyRegulator()
