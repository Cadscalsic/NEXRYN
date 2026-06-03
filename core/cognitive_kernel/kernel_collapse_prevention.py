# ============================================
# NEXRYN KERNEL COLLAPSE PREVENTION
# ============================================


class KernelCollapsePrevention:

    def detect_architectural_saturation(self, pressure_report, context):

        selected_actions = context.get(
            "selected_actions",
            context.get(
                "executive_arbitration_report",
                {},
            ).get(
                "selected_actions",
                [],
            ),
        )

        action_count = (
            len(
                selected_actions,
            )
            if isinstance(
                selected_actions,
                list,
            )
            else 0
        )

        executive_mode = context.get(
            "executive_mode",
            context.get(
                "executive_arbitration_report",
                {},
            ).get(
                "executive_mode",
                "",
            ),
        )

        pressure = pressure_report.get(
            "total_kernel_pressure",
            0.0,
        )

        saturated = (
            pressure >= 0.70
            or action_count >= 20
            or executive_mode == "protective_arbitration"
        )

        return {
            "architectural_saturation":
            saturated,

            "selected_action_count":
            action_count,

            "executive_mode":
            executive_mode,

            "collapse_prevention_actions":
            (
                [
                    "enter_single_active_kernel_mode",
                    "suspend_recursive_meta_control",
                    "disable_nonessential_subsystems",
                    "collapse_governance_stack",
                ]
                if saturated
                else [
                    "maintain_kernel_monitoring",
                ]
            ),
        }
