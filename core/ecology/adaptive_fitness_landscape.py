# ============================================
# NEXRYN ADAPTIVE FITNESS LANDSCAPE
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


class AdaptiveFitnessLandscape:

    def map(self, selection_report, resource_report):

        pressure = _clamp(
            resource_report.get(
                "resource_pressure",
                0.0,
            ),
        )

        peaks = []

        for trait in selection_report.get(
            "selected_traits",
            [],
        ):

            peaks.append({
                "trait":
                trait.get(
                    "trait",
                    "unknown",
                ),

                "niche":
                trait.get(
                    "niche",
                    "general_adaptation",
                ),

                "fitness_peak":
                _clamp(
                    trait.get(
                        "competitive_score",
                        0.0,
                    )
                    *
                    (
                        1.0 - pressure * 0.22
                    )
                ),
            })

        average_peak = _clamp(
            sum(
                item.get(
                    "fitness_peak",
                    0.0,
                )
                for item in peaks
            )
            /
            max(
                len(
                    peaks,
                ),
                1,
            )
        )

        return {
            "system":
            "adaptive_fitness_landscape",

            "fitness_peaks":
            peaks,

            "average_fitness_peak":
            average_peak,

            "landscape_state":
            (
                "adaptive_peaks_available"
                if average_peak >= 0.42
                else "low_fitness_landscape"
                if peaks
                else "empty_landscape"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
