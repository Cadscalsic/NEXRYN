# ============================================
# NEXRYN CAUSAL REHEARSAL
# ============================================

from datetime import datetime

from core.rehearsal.future_state_projection import (
    FutureStateProjection,
)

from core.rehearsal.identity_forecaster import (
    IdentityForecaster,
)

from core.rehearsal.mutation_simulator import (
    MutationSimulator,
)


class CausalRehearsal:

    def __init__(self):

        self.mutation_simulator = MutationSimulator()
        self.identity_forecaster = IdentityForecaster()
        self.future_state_projection = FutureStateProjection()
        self.rehearsal_history = []

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        simulation_report = self.mutation_simulator.run_cycle(
            context,
        )

        identity_report = self.identity_forecaster.forecast(
            simulation_report,
            context,
        )

        future_report = self.future_state_projection.project(
            simulation_report,
            identity_report,
            context,
        )

        report = {
            "system":
            "causal_rehearsal",

            "mutation_simulator":
            simulation_report,

            "identity_forecaster":
            identity_report,

            "future_state_projection":
            future_report,

            "rehearsal_state":
            (
                "constructive_evolution_rehearsed"
                if simulation_report.get(
                    "constructive_count",
                    0,
                )
                and future_report.get(
                    "future_state",
                )
                != "unsafe_future"
                else "continue_rehearsal"
                if simulation_report.get(
                    "candidate_count",
                    0,
                )
                else "idle"
            ),

            "evidence_exports":
            {
                "causal_attestation_score":
                future_report.get(
                    "future_stability",
                    0.0,
                ),

                "identity_attestation_score":
                identity_report.get(
                    "identity_continuity",
                    0.0,
                ),
            },

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.rehearsal_history.append(
            report,
        )

        self.rehearsal_history = (
            self.rehearsal_history[-128:]
        )

        return report


causal_rehearsal = (
    CausalRehearsal()
)
