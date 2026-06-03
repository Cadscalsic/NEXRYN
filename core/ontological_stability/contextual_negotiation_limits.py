class ContextualNegotiationLimits:

    RULES = {
        "symbolic_forms": "negotiable",
        "contextual_heuristics": "negotiable",
        "topology_structure": "limited",
        "causal_laws": "strictly_limited",
        "semantic_anchors": "near_forbidden",
        "constitutional_truth": "forbidden",
    }

    def run_cycle(self, context):

        proposed = context.get(
            "proposed_contextual_negotiations",
            [],
        )

        blocked = []
        limited = []
        allowed = []

        for negotiation in proposed:

            target = negotiation.get(
                "target",
                negotiation,
            )

            policy = self.RULES.get(
                target,
                "strictly_limited",
            )

            if policy in [
                "forbidden",
                "near_forbidden",
            ]:

                blocked.append(
                    {
                        "target": target,
                        "policy": policy,
                    }
                )

            elif policy == "strictly_limited":

                limited.append(
                    {
                        "target": target,
                        "policy": policy,
                    }
                )

            else:

                allowed.append(
                    {
                        "target": target,
                        "policy": policy,
                    }
                )

        return {
            "system":
            "contextual_negotiation_limits",

            "negotiation_rules":
            self.RULES,

            "allowed_negotiations":
            allowed,

            "limited_negotiations":
            limited,

            "blocked_negotiations":
            blocked,

            "negotiation_state":
            (
                "contextual_relativism_contained"
                if blocked
                else "contextual_negotiation_bounded"
            ),
        }
