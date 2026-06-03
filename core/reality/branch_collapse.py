# ============================================
# NEXRYN BRANCH COLLAPSE
# ============================================


class BranchCollapse:

    def validate_branch(self, sandbox):

        identity = sandbox.get(
            "identity_continuity",
            0.0,
        )

        entropy_delta = sandbox.get(
            "predicted_entropy_delta",
            1.0,
        )

        identity_valid = identity >= 0.55
        entropy_valid = entropy_delta <= 0.32
        causal_valid = sandbox.get(
            "write_barrier",
        ) == "enabled"

        commit_allowed = (
            identity_valid
            and entropy_valid
            and causal_valid
        )

        return {
            "sandbox_id":
            sandbox.get(
                "sandbox_id",
            ),

            "identity_validation":
            identity_valid,

            "causal_validation":
            causal_valid,

            "entropy_validation":
            entropy_valid,

            "commit_allowed":
            commit_allowed,

            "branch_action":
            (
                "commit_candidate"
                if commit_allowed
                else "collapse_branch"
            ),
        }

    def collapse_unstable(self, isolation_report):

        validations = [
            self.validate_branch(
                sandbox,
            )
            for sandbox in isolation_report.get(
                "isolated_worlds",
                [],
            )
        ]

        return {
            "system":
            "branch_collapse",

            "validations":
            validations,

            "collapsed_branches":
            [
                item
                for item in validations
                if item.get(
                    "branch_action",
                )
                == "collapse_branch"
            ],

            "commit_candidates":
            [
                item
                for item in validations
                if item.get(
                    "commit_allowed",
                    False,
                )
            ],

            "collapsed_count":
            len([
                item
                for item in validations
                if item.get(
                    "branch_action",
                )
                == "collapse_branch"
            ]),
        }
