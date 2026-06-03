class ExecutionGatekeeper:

    def gate(self, court, sandbox, topology, legality, causal):

        blockers = []

        if court.get("court_score", 1.0) < 0.42:
            blockers.append("epistemic_court_block")

        if topology.get("recursive_topology_risk", 0.0) >= 0.58:
            blockers.append("recursive_topology_block")

        if legality.get("semantic_legality", 1.0) < 0.42:
            blockers.append("semantic_legality_block")

        if causal.get("causal_permission_score", 1.0) < 0.42:
            blockers.append("causal_permission_block")

        sandboxed = sandbox.get("sandbox_required", False)

        return {
            "system": "execution_gatekeeper",
            "execution_blockers": blockers,
            "execution_permission": (
                "blocked"
                if blockers
                else "sandbox_only"
                if sandboxed
                else "granted"
            ),
            "gatekeeper_actions": (
                ["block_execution"] if blockers else
                ["allow_sandboxed_execution"] if sandboxed else
                ["allow_guarded_execution"]
            ),
        }
