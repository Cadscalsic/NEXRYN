# ============================================
# NEXRYN META-COGNITIVE EXECUTIVE
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


class MetaCognitiveExecutive:

    def __init__(self):

        self.executive_history = []

    def read_entropy_risk(self, context):

        thermodynamics = context.get(
            "cognitive_thermodynamics_report",
            {},
        )

        dissipation = thermodynamics.get(
            "semantic_heat_dissipation",
            {},
        )

        entropy = context.get(
            "runtime_entropy",
            context.get(
                "cognitive_entropy_report",
                {},
            ).get(
                "runtime_entropy",
                0.0,
            ),
        )

        return _clamp(
            max(
                entropy,
                dissipation.get(
                    "semantic_heat_after",
                    0.0,
                ),
            )
        )

    def read_identity_drift(self, context):

        identity_anchor = context.get(
            "identity_anchor_core_report",
            {},
        )

        identity_core = context.get(
            "identity_core_report",
            {},
        )

        return _clamp(
            max(
                identity_anchor.get(
                    "identity_drift_before",
                    0.0,
                ),
                identity_core.get(
                    "identity_drift",
                    0.0,
                ),
            )
        )

    def read_recursion_risk(self, context):

        pressure = context.get(
            "recursive_pressure_governor_report",
            {},
        )

        raw_depth = pressure.get(
            "raw_reasoning_depth",
            context.get(
                "raw_reasoning_depth",
                0,
            ),
        )

        return _clamp(
            raw_depth / 16,
        )

    def read_loop_risk(self, context):

        recursive_paths = context.get(
            "recursive_paths",
            [],
        )

        if not isinstance(
            recursive_paths,
            list,
        ):

            return 0.0

        unique_paths = len(
            {
                str(path)
                for path in recursive_paths
            }
        )

        repeated = max(
            len(recursive_paths) - unique_paths,
            0,
        )

        return _clamp(
            repeated / max(
                len(recursive_paths),
                1,
            )
        )

    def estimate_reasoning_usefulness(self, context):

        reasoning = context.get(
            "reasoning_report",
            {},
        )

        orchestration = reasoning.get(
            "orchestration_summary",
            {},
        )

        active_routes = orchestration.get(
            "active_routes",
            0,
        )

        pressure = reasoning.get(
            "pressure_report",
            {},
        ).get(
            "pressure_score",
            0.0,
        )

        return _clamp(
            active_routes / 8
            -
            pressure * 0.25
            +
            0.35,
        )

    def should_explore(self, context):

        novelty = context.get(
            "controlled_safe_novelty_report",
            {},
        )

        promotion = novelty.get(
            "novelty_promotion_gate",
            {},
        )

        promoted = promotion.get(
            "decision_counts",
            {},
        ).get(
            "promote",
            0,
        )

        latent = promotion.get(
            "decision_counts",
            {},
        ).get(
            "latent",
            0,
        )

        entropy_risk = self.read_entropy_risk(
            context,
        )

        return _clamp(
            (promoted * 0.35 + latent * 0.12)
            -
            entropy_risk * 0.30
            +
            0.20,
        )

    def build_budget(self, context):

        entropy_risk = self.read_entropy_risk(
            context,
        )

        identity_drift = self.read_identity_drift(
            context,
        )

        recursion_risk = self.read_recursion_risk(
            context,
        )

        exploration_value = self.should_explore(
            context,
        )

        return {
            "attention":
            _clamp(
                0.42 - entropy_risk * 0.10,
            ),

            "recursion":
            _clamp(
                0.30 - recursion_risk * 0.16,
            ),

            "energy":
            _clamp(
                0.55 - entropy_risk * 0.20,
            ),

            "memory":
            _clamp(
                0.36 - entropy_risk * 0.08,
            ),

            "exploration":
            _clamp(
                exploration_value
                -
                identity_drift * 0.12,
            ),
        }

    def reflect(self, context):

        entropy_risk = self.read_entropy_risk(
            context,
        )

        identity_drift = self.read_identity_drift(
            context,
        )

        recursion_risk = self.read_recursion_risk(
            context,
        )

        loop_risk = self.read_loop_risk(
            context,
        )

        usefulness = self.estimate_reasoning_usefulness(
            context,
        )

        actions = []

        if entropy_risk >= 0.70:

            actions.append(
                "reduce_exploration",
            )

            actions.append(
                "prefer_compiled_semantic_macros",
            )

        if identity_drift >= 0.45:

            actions.append(
                "stabilize_identity",
            )

        if usefulness < 0.35:

            actions.append(
                "collapse_reasoning_branch",
            )

        if recursion_risk >= 0.65 or loop_risk >= 0.35:

            actions.append(
                "compress_recursion",
            )

        if not actions:

            actions.append(
                "maintain_balanced_cognition",
            )

        return {
            "why_think":
            (
                "execute_task_with_controlled_reasoning"
                if usefulness >= 0.35
                else "reasoning_utility_under_review"
            ),

            "thinking_usefulness":
            usefulness,

            "loop_risk":
            loop_risk,

            "exploration_value":
            self.should_explore(
                context,
            ),

            "recursion_risk":
            recursion_risk,

            "identity_drift":
            identity_drift,

            "entropy_risk":
            entropy_risk,

            "strategic_actions":
            actions,
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        budget = self.build_budget(
            context,
        )

        reflection = self.reflect(
            context,
        )

        report = {
            "system":
            "meta_cognitive_executive",

            "cognitive_budgeting":
            budget,

            "strategic_reflection":
            reflection,

            "executive_state":
            (
                "thermal_guarded"
                if reflection.get(
                    "entropy_risk",
                    0.0,
                )
                >= 0.70
                else "balanced"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.executive_history.append(
            report,
        )

        self.executive_history = (
            self.executive_history[-64:]
        )

        return report


meta_cognitive_executive = (
    MetaCognitiveExecutive()
)
