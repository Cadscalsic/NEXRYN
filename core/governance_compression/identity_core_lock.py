# ============================================
# NEXRYN IDENTITY CORE LOCK
# ============================================


class IdentityCoreLock:

    IMMUTABLE_INVARIANTS = [
        "causality",
        "identity",
        "consistency",
        "temporal_continuity",
    ]

    REQUIRED_REWRITE_GATES = [
        "supervised_rewrite",
        "staged_rehearsal",
        "rollback_safe_mutation",
    ]

    def evaluate(self, context):

        proposals = context.get(
            "identity_rewrite_request",
            context.get(
                "proposed_invariant_rewrites",
                [],
            ),
        )

        if isinstance(
            proposals,
            dict,
        ):

            proposals = proposals.get(
                "targets",
                [],
            )

        if not isinstance(
            proposals,
            list,
        ):

            proposals = []

        attempted = [
            item
            for item in proposals
            if item in self.IMMUTABLE_INVARIANTS
        ]

        gates = context.get(
            "identity_rewrite_gates",
            {},
        )

        gates_satisfied = all(
            gates.get(
                gate,
                False,
            )
            for gate in self.REQUIRED_REWRITE_GATES
        )

        if attempted and not gates_satisfied:

            decision = "blocked"

        elif attempted:

            decision = "allowed_under_supervision"

        else:

            decision = "locked"

        return {
            "system":
            "identity_core_lock",

            "locked_invariants":
            list(
                self.IMMUTABLE_INVARIANTS,
            ),

            "required_rewrite_gates":
            list(
                self.REQUIRED_REWRITE_GATES,
            ),

            "attempted_rewrites":
            attempted,

            "decision":
            decision,

            "rewrite_gates_satisfied":
            gates_satisfied,
        }
