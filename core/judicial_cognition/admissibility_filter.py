class AdmissibilityFilter:

    def filter(self, court, ambiguity, legality, causal):

        admissible = (
            court.get("court_score", 0.0) >= 0.42
            and ambiguity.get("ambiguity_load", 1.0) < 0.72
            and legality.get("semantic_legality", 0.0) >= 0.42
            and causal.get("causal_permission_score", 0.0) >= 0.42
        )

        return {
            "system": "admissibility_filter",
            "admissible": admissible,
            "admissibility_actions": [
                "admit_claim_for_guarded_reasoning",
            ]
            if admissible
            else [
                "reject_or_sandbox_inadmissible_claim",
            ],
            "admissibility_state": (
                "claim_admissible"
                if admissible
                else "claim_inadmissible_or_sandboxed"
            ),
        }
