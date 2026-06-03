class OrganizedRecursiveRuntime:

    def organize(self, supervisor, limits, diffusion):

        runtime_actions = list(supervisor.get("supervisor_actions", []))

        if limits.get("limit_required", False):

            runtime_actions.append("run_recursive_runtime_in_budgeted_mode")

        if diffusion.get("diffusion_state") == "adaptive_diffusion_balancing_active":

            runtime_actions.append("serialize_high_risk_recursive_diffusion")

        return {
            "system": "organized_recursive_runtime",
            "runtime_actions": sorted(set(runtime_actions)),
            "runtime_state": (
                "organized_recursive_runtime_active"
                if runtime_actions
                else "organized_recursive_runtime_standby"
            ),
        }
