# ============================================
# NEXRYN WORLD ISOLATION
# ============================================

from datetime import datetime


class WorldIsolation:

    def isolate_worlds(self, context, budget_report):

        worlds_report = context.get(
            "recursive_simulation_worlds_report",
            {},
        )

        worlds = worlds_report.get(
            "worlds",
            [],
        )

        isolated = []

        for index, world in enumerate(
            worlds[:budget_report.get("max_active_worlds", 2)]
        ):

            isolated.append({
                "sandbox_id":
                f"sandbox_world:{index + 1}",

                "source_world_id":
                world.get(
                    "world_id",
                    f"world:{index + 1}",
                ),

                "sandbox_memory":
                "isolated_copy",

                "core_memory_access":
                "read_only_snapshot",

                "write_barrier":
                "enabled",

                "commit_to_core":
                False,

                "identity_continuity":
                world.get(
                    "identity_continuity",
                    0.0,
                ),

                "predicted_entropy_delta":
                world.get(
                    "predicted_entropy_delta",
                    0.0,
                ),

                "timestamp":
                str(
                    datetime.utcnow()
                ),
            })

        return {
            "system":
            "world_isolation",

            "write_barrier_architecture":
            True,

            "isolated_worlds":
            isolated,

            "isolated_world_count":
            len(
                isolated,
            ),

            "blocked_direct_core_writes":
            len(
                worlds,
            ),
        }
