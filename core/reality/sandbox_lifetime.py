# ============================================
# NEXRYN SANDBOX LIFETIME
# ============================================


class SandboxLifetime:

    def assign_lifetime(self, isolation_report, collapse_report):

        collapsed = {
            item.get(
                "sandbox_id",
            )
            for item in collapse_report.get(
                "collapsed_branches",
                [],
            )
        }

        lifetimes = []

        for sandbox in isolation_report.get(
            "isolated_worlds",
            [],
        ):

            sandbox_id = sandbox.get(
                "sandbox_id",
            )

            lifetimes.append({
                "sandbox_id":
                sandbox_id,

                "ttl_cycles":
                (
                    0
                    if sandbox_id in collapsed
                    else 2
                    if sandbox.get(
                        "identity_continuity",
                        0.0,
                    )
                    < 0.65
                    else 4
                ),

                "lifetime_policy":
                (
                    "terminate_now"
                    if sandbox_id in collapsed
                    else "short_lived_sandbox"
                    if sandbox.get(
                        "identity_continuity",
                        0.0,
                    )
                    < 0.65
                    else "bounded_sandbox"
                ),
            })

        return {
            "system":
            "sandbox_lifetime",

            "lifetimes":
            lifetimes,

            "expired_count":
            len([
                item
                for item in lifetimes
                if item.get(
                    "ttl_cycles",
                )
                == 0
            ]),
        }
