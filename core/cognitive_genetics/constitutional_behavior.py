class ConstitutionalBehavior:

    def synthesize(self, instincts, ethics):

        return {
            "system": "constitutional_behavior",
            "behavioral_architecture": "trait_regulated_cognition",
            "instinct_count": sum(
                len(value.get("instincts", value.get("behaviors", [])))
                for value in instincts
                if isinstance(value, dict)
            ),
            "ethics_state": ethics.get("ethics_state"),
            "scripted_personality": False,
        }
