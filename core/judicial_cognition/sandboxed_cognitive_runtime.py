class SandboxedCognitiveRuntime:

    def assign(self, context, ambiguity, court):

        sandbox_required = (
            bool(ambiguity.get("ambiguity_actions", []))
            or court.get("court_score", 1.0) < 0.58
            or context.get("sandbox_only_mode", False)
        )

        return {
            "system": "sandboxed_cognitive_runtime",
            "sandbox_required": sandbox_required,
            "sandbox_actions": [
                "execute_reasoning_in_sandbox",
                "block_persistent_commit_until_review",
            ]
            if sandbox_required
            else [],
            "sandbox_state": (
                "sandboxed_cognitive_runtime_active"
                if sandbox_required
                else "sandboxed_cognitive_runtime_standby"
            ),
        }
