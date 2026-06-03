# ============================================
# NEXRYN META-COGNITIVE DIVERSITY ENGINE
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


class MetaCognitiveDiversityEngine:

    DIVERSITY_THRESHOLDS = {
        "diverse": 0.60,
        "fragile": 0.36,
        "lock_in": 0.10,
    }

    RECOMMENDED_ACTIONS = [
        "introduce_abstraction_variants",
        "balance_topology_exploration",
        "activate_contrastive_simulation",
        "counteract_pattern_repetition",
    ]

    def _distribution_score(self, items):

        if not items or not isinstance(items, list):
            return 0.0

        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1

        total = float(sum(counts.values()))
        if total <= 0.0:
            return 0.0

        max_ratio = max(counts.values()) / total
        return _clamp(1.0 - max_ratio)

    def _dominant(self, items):

        if not items or not isinstance(items, list):
            return None

        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1

        dominant = max(counts.items(), key=lambda pair: pair[1])[0]
        ratio = counts[dominant] / float(sum(counts.values()))

        return {
            "label": dominant,
            "dominance_ratio": _clamp(ratio),
        }

    def assess(self, runtime_context):

        abstraction_profiles = runtime_context.get(
            "abstraction_profiles",
            [],
        )

        topology_profiles = runtime_context.get(
            "topology_profiles",
            [],
        )

        perception_patterns = runtime_context.get(
            "perception_pattern_history",
            [],
        )

        strategy_history = runtime_context.get(
            "strategy_usage_history",
            [],
        )

        abstraction_diversity = self._distribution_score(
            abstraction_profiles,
        )

        topology_diversity = self._distribution_score(
            topology_profiles,
        )

        perception_diversity = self._distribution_score(
            perception_patterns,
        )

        strategy_diversity = self._distribution_score(
            strategy_history,
        )

        average_diversity = _clamp(
            (
                abstraction_diversity
                + topology_diversity
                + perception_diversity
                + strategy_diversity
            )
            / 4.0
        )

        lock_in_risk = _clamp(1.0 - average_diversity)

        dominant_abstraction = self._dominant(
            abstraction_profiles,
        )

        dominant_topology = self._dominant(
            topology_profiles,
        )

        diversity_state = (
            "diverse"
            if average_diversity >= self.DIVERSITY_THRESHOLDS["diverse"]
            else "fragile"
            if average_diversity >= self.DIVERSITY_THRESHOLDS["fragile"]
            else "locked_in"
        )

        recommended_actions = []
        if lock_in_risk >= 0.42:
            recommended_actions.append(
                "introduce_abstraction_variants",
            )
        if lock_in_risk >= 0.55:
            recommended_actions.append(
                "balance_topology_exploration",
            )
        if dominant_abstraction and dominant_abstraction["dominance_ratio"] >= 0.72:
            recommended_actions.append(
                "counteract_pattern_repetition",
            )
        if dominant_topology and dominant_topology["dominance_ratio"] >= 0.72:
            recommended_actions.append(
                "activate_contrastive_simulation",
            )

        return {
            "system":
            "meta_cognitive_diversity_engine",

            "abstraction_diversity":
            abstraction_diversity,

            "topology_diversity":
            topology_diversity,

            "perception_diversity":
            perception_diversity,

            "strategy_diversity":
            strategy_diversity,

            "average_diversity":
            average_diversity,

            "lock_in_risk":
            lock_in_risk,

            "diversity_state":
            diversity_state,

            "dominant_abstraction":
            dominant_abstraction,

            "dominant_topology":
            dominant_topology,

            "recommended_actions":
            recommended_actions,

            "timestamp":
            str(datetime.utcnow()),
        }
