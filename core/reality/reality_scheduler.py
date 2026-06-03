# ============================================
# NEXRYN REALITY SCHEDULER
# ============================================


class RealityScheduler:

    def schedule(self, budget_report, isolation_report, lifetime_report):

        expired = {
            item.get(
                "sandbox_id",
            )
            for item in lifetime_report.get(
                "lifetimes",
                [],
            )
            if item.get(
                "ttl_cycles",
                0,
            )
            == 0
        }

        scheduled = []
        deferred = []

        for sandbox in isolation_report.get(
            "isolated_worlds",
            [],
        ):

            if sandbox.get(
                "sandbox_id",
            ) in expired:

                deferred.append(
                    sandbox,
                )

                continue

            scheduled.append(
                sandbox,
            )

        return {
            "system":
            "reality_scheduler",

            "scheduled_worlds":
            scheduled[:budget_report.get(
                "max_active_worlds",
                2,
            )],

            "deferred_worlds":
            deferred + scheduled[budget_report.get(
                "max_active_worlds",
                2,
            ):],

            "scheduled_count":
            min(
                len(
                    scheduled,
                ),
                budget_report.get(
                    "max_active_worlds",
                    2,
                ),
            ),

            "scheduler_policy":
            budget_report.get(
                "budget_policy",
                "bounded_reality_budget",
            ),
        }
