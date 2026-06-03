class MultiModalSemanticRouter:

    def route(self, context, conflict):

        modes = conflict.get("candidate_paradigms", [])

        if not modes:

            modes = [
                "symbolic",
                "spatial",
                "causal",
            ]

        routes = []

        for mode in sorted(set(modes)):

            routes.append({
                "mode": mode,
                "route_policy": (
                    "attested_hybrid_route"
                    if conflict.get("paradigm_conflict_score", 0.0) >= 0.34
                    else "direct_semantic_route"
                ),
            })

        return {
            "system": "multi_modal_semantic_router",
            "semantic_routes": routes,
            "routing_state": (
                "multi_modal_routes_attested"
                if conflict.get("paradigm_conflict_score", 0.0) >= 0.34
                else "multi_modal_routes_open"
            ),
        }
