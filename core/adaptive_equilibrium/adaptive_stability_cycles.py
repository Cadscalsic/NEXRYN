class AdaptiveStabilityCycles:

    def plan(self, equilibrium, pressure_report):

        cycles = []

        if equilibrium.get("dynamic_equilibrium", 0.0) < 0.66:

            cycles.append("short_stability_cycle")

        if pressure_report.get("pressure_policy", {}).get(
            "activate_self_damping",
            False,
        ):

            cycles.append("damping_assisted_equilibrium_cycle")

        if pressure_report.get("pressure_policy", {}).get(
            "release_cognitive_pressure",
            False,
        ):

            cycles.append("pressure_release_equilibrium_cycle")

        return {
            "system": "adaptive_stability_cycles",
            "planned_stability_cycles": sorted(set(cycles)),
            "cycle_state": (
                "adaptive_stability_cycles_active"
                if cycles
                else "adaptive_stability_cycles_standby"
            ),
        }
