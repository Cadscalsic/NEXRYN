class MultiModalSemanticRouter:

    DEFAULT_MODES = ["symbolic", "spatial", "causal"]
    CONFLICT_THRESHOLD = 0.34
    MAX_FAST_ROUTES = 1
    MAX_NORMAL_ROUTES = 3

    def route(self, context=None, conflict=None):
        context = context or {}
        conflict = conflict or {}

        conflict_score = float(
            conflict.get("paradigm_conflict_score", 0.0) or 0.0
        )

        modes = conflict.get("candidate_paradigms", [])

        if not isinstance(modes, list):
            modes = []

        if not modes:
            modes = list(self.DEFAULT_MODES)

        modes = sorted(set(str(mode) for mode in modes if mode))

        fast_mode = (
            context.get("episode_completed") is True
            or context.get("shutdown_mode") == "fast"
            or context.get("post_success_mode") == "fast"
        )

        conflict_active = conflict_score >= self.CONFLICT_THRESHOLD

        if fast_mode and not conflict_active:
            modes = modes[:self.MAX_FAST_ROUTES]
            routing_state = "minimal_fast_semantic_route"
        else:
            modes = modes[:self.MAX_NORMAL_ROUTES]
            routing_state = (
                "multi_modal_routes_attested"
                if conflict_active
                else "multi_modal_routes_open"
            )

        routes = []

        for mode in modes:
            routes.append({
                "mode": mode,
                "route_policy": (
                    "attested_hybrid_route"
                    if conflict_active
                    else "direct_semantic_route"
                ),
            })

        return {
            "system": "multi_modal_semantic_router",
            "semantic_routes": routes,
            "routing_state": routing_state,
            "route_count": len(routes),
            "conflict_active": conflict_active,
            "conflict_score": round(conflict_score, 4),
            "fast_mode": fast_mode,
        }