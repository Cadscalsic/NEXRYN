class CognitivePressureRelease:

    def release(self, damping, fatigue):

        actions = []

        if damping.get("damping_strength", 0.0) >= 0.36:

            actions.extend([
                "release_pressure_to_recovery_cycles",
                "defer_low_value_evolution",
            ])

        if fatigue.get("fatigue_cycles", 0) > 0:

            actions.append("schedule_semantic_rest_cycle")

        return {
            "system": "cognitive_pressure_release",
            "release_actions": sorted(set(actions)),
            "release_state": (
                "pressure_release_active"
                if actions
                else "pressure_release_standby"
            ),
        }
