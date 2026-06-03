# ============================================
# NEXRYN SEMANTIC POINTER SYSTEM
# ============================================

from datetime import datetime


class SemanticPointerSystem:

    def __init__(self):

        self.pointer_history = []

    def build_pointer_id(
        self,
        concept
    ):

        normalized = (
            str(
                concept
            )
            .strip()
            .lower()
            .replace(
                " ",
                "_"
            )
        )

        return "ptr:" + normalized

    def extract_concept(
        self,
        item
    ):

        if not isinstance(
            item,
            dict
        ):

            return None

        return (
            item.get(
                "semantic_concept"
            )
            or
            item.get(
                "concept"
            )
            or
            item.get(
                "primitive"
            )
            or
            item.get(
                "type"
            )
        )

    def build_pointers(
        self,
        context
    ):

        abstractions = context.get(
            "semantic_abstractions",
            []
        )

        if not isinstance(
            abstractions,
            list
        ):

            abstractions = []

        pointers = {}
        alias_links = []

        for item in abstractions:

            concept = self.extract_concept(
                item
            )

            if concept is None:

                continue

            pointer_id = self.build_pointer_id(
                concept
            )

            pointers.setdefault(
                pointer_id,
                {
                    "pointer_id":
                    pointer_id,

                    "canonical_concept":
                    concept,

                    "aliases":
                    [],

                    "reference_count":
                    0
                }
            )

            pointers[pointer_id][
                "reference_count"
            ] += 1

            source = (
                item.get(
                    "original_type"
                )
                or
                item.get(
                    "primitive"
                )
                or
                item.get(
                    "type"
                )
            )

            if source and source not in pointers[pointer_id]["aliases"]:

                pointers[pointer_id][
                    "aliases"
                ].append(
                    source
                )

                alias_links.append({
                    "alias":
                    source,

                    "pointer_id":
                    pointer_id,

                    "canonical_concept":
                    concept
                })

        report = {
            "system":
            "semantic_pointer",

            "pointer_count":
            len(
                pointers
            ),

            "alias_count":
            len(
                alias_links
            ),

            "pointers":
            list(
                pointers.values()
            ),

            "alias_links":
            alias_links,

            "policy":
            "alias_without_merging",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.pointer_history.append(
            report
        )

        self.pointer_history = (
            self.pointer_history[-32:]
        )

        return report


semantic_pointer_system = (
    SemanticPointerSystem()
)
