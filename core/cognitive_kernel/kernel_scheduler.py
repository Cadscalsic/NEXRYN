# ============================================
# NEXRYN COGNITIVE KERNEL SCHEDULER
# ============================================

from datetime import datetime

from core.cognitive_kernel.kernel_budget import (
    KernelBudget,
)

from core.cognitive_kernel.kernel_collapse_prevention import (
    KernelCollapsePrevention,
)

from core.cognitive_kernel.kernel_modes import (
    KernelModes,
)

from core.cognitive_kernel.kernel_state import (
    KernelState,
)


class CognitiveKernelScheduler:

    def __init__(self):

        self.kernel_modes = KernelModes()
        self.kernel_budget = KernelBudget()
        self.kernel_collapse_prevention = KernelCollapsePrevention()
        self.kernel_state = KernelState()
        self.schedule_history = []

    def choose_mode(self, pressure_report, prevention_report, context):

        if prevention_report.get(
            "architectural_saturation",
            False,
        ):

            return (
                self.kernel_modes.STABILIZATION,
                "architectural_saturation",
            )

        entropy = pressure_report.get(
            "runtime_entropy",
            0.0,
        )

        overload = pressure_report.get(
            "projected_overload",
            0.0,
        )

        memory = pressure_report.get(
            "working_memory_pressure",
            0.0,
        )

        novelty = context.get(
            "controlled_safe_novelty_report",
            {},
        ).get(
            "novelty_state",
            "",
        )

        if (
            entropy >= 0.62
            or overload >= 0.70
            or memory >= 0.90
        ):

            return (
                self.kernel_modes.STABILIZATION,
                "thermal_or_memory_pressure",
            )

        if novelty == "reopened_under_sandbox":

            return (
                self.kernel_modes.EXPLORATION,
                "sandboxed_novelty_available",
            )

        return (
            self.kernel_modes.REASONING,
            "default_reasoning",
        )

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        pressure_report = self.kernel_budget.compute_pressure(
            context,
        )

        prevention_report = (
            self.kernel_collapse_prevention
            .detect_architectural_saturation(
                pressure_report,
                context,
            )
        )

        mode, reason = self.choose_mode(
            pressure_report,
            prevention_report,
            context,
        )

        transition = self.kernel_state.update(
            mode,
            reason,
        )

        budget = self.kernel_budget.allocate(
            mode,
            pressure_report,
        )

        report = {
            "system":
            "cognitive_kernel_scheduler",

            "active_mode":
            mode,

            "mode_reason":
            reason,

            "enabled_subsystems":
            self.kernel_modes.enabled_for(
                mode,
            ),

            "disabled_subsystems":
            self.kernel_modes.disabled_for(
                mode,
            ),

            "kernel_budget":
            budget,

            "pressure_report":
            pressure_report,

            "collapse_prevention":
            prevention_report,

            "kernel_state":
            self.kernel_state.snapshot(),

            "transition":
            transition,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.schedule_history.append(
            report,
        )

        self.schedule_history = (
            self.schedule_history[-64:]
        )

        return report


cognitive_kernel_scheduler = (
    CognitiveKernelScheduler()
)
