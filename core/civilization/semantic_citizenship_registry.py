# ============================================
# NEXRYN SEMANTIC CITIZENSHIP REGISTRY
# ============================================


class SemanticCitizenshipRegistry:

    def __init__(self):

        self.registry = {}
        self.banned_concepts = set()

    def register_concept(
        self,
        concept_id,
        reputation=0.0,
        trust_level="sandboxed",
        permissions=None,
    ):

        if not concept_id:

            return None

        permissions = (
            permissions
            if permissions is not None
            else [
                "read_context",
                "rehearse_only",
            ]
        )

        entry = {
            "concept_id":
            concept_id,

            "reputation":
            round(
                float(
                    reputation,
                ),
                4,
            ),

            "trust_level":
            trust_level,

            "execution_right":
            "execute" in permissions
            or "commit" in permissions
            or "promote" in permissions,

            "merge_right":
            "merge" in permissions
            or "promote" in permissions,

            "permissions":
            permissions,

            "registry_state":
            "banned"
            if concept_id in self.banned_concepts
            else "registered",
        }

        self.registry[
            concept_id
        ] = entry

        return entry

    def ban_concept(self, concept_id, reason):

        self.banned_concepts.add(
            concept_id,
        )

        if concept_id in self.registry:

            self.registry[
                concept_id
            ][
                "registry_state"
            ] = "banned"

            self.registry[
                concept_id
            ][
                "ban_reason"
            ] = reason

        return {
            "concept_id":
            concept_id,

            "ban_reason":
            reason,

            "registry_state":
            "banned",
        }

    def run_cycle(self, context):

        rights = context.get(
            "constitutional_runtime_report",
            {},
        ).get(
            "cognitive_rights",
            {},
        )

        concept_id = context.get(
            "active_concept_id",
            "runtime_cognition",
        )

        entry = self.register_concept(
            concept_id,
            reputation=rights.get(
                "reputation",
                0.0,
            ),
            trust_level=rights.get(
                "trust_band",
                "sandboxed",
            ),
            permissions=rights.get(
                "execution_permissions",
                [],
            ),
        )

        court = context.get(
            "semantic_court_report",
            {},
        )

        if court.get(
            "court_state",
        ) == "semantic_injunction":

            self.ban_concept(
                concept_id,
                "semantic_injunction",
            )

            entry = self.registry.get(
                concept_id,
                entry,
            )

        return {
            "system":
            "semantic_citizenship_registry",

            "active_citizen":
            entry,

            "registered_count":
            len(
                self.registry,
            ),

            "banned_count":
            len(
                self.banned_concepts,
            ),

            "registry_state":
            (
                "citizenship_restricted"
                if self.banned_concepts
                else "citizenship_registry_active"
            ),
        }


semantic_citizenship_registry = SemanticCitizenshipRegistry()
