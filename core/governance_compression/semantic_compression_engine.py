# ============================================
# NEXRYN SEMANTIC COMPRESSION ENGINE
# ============================================

from datetime import datetime


class SemanticCompressionEngine:

    TOKEN_MAP = {
        "identity": "identity",
        "object": "object",
        "preservation": "preservation",
        "preserve": "preservation",
        "topological": "topology",
        "topology": "topology",
        "growth": "growth",
        "grow": "growth",
        "shape": "shape",
        "color": "color",
        "motion": "motion",
        "translation": "motion",
        "symbolic": "symbolic",
        "remapping": "remap",
        "bridge": None,
        "concept": None,
    }

    CANONICAL_ORDER = [
        "preservation",
        "growth",
        "topology",
        "identity",
        "object",
        "shape",
        "color",
        "motion",
        "symbolic",
        "remap",
    ]

    def tokenize(self, concept):

        return [
            token
            for token in str(
                concept,
            )
            .replace(
                "-",
                "_",
            )
            .split(
                "_",
            )
            if token
        ]

    def canonical_encode(self, concept):

        factors = []

        for token in self.tokenize(
            concept,
        ):

            mapped = self.TOKEN_MAP.get(
                token.lower(),
                token.lower(),
            )

            if mapped is None:

                continue

            if mapped not in factors:

                factors.append(
                    mapped,
                )

        ordered = [
            factor
            for factor in self.CANONICAL_ORDER
            if factor in factors
        ]

        ordered.extend([
            factor
            for factor in factors
            if factor not in ordered
        ])

        if {
            "preservation",
            "growth",
            "topology",
        }.issubset(
            set(
                ordered,
            )
        ):

            ordered = [
                "preservation",
                "growth",
                "topology",
            ]

        return ".".join(
            ordered,
        )

    def collect_concepts(self, context):

        concepts = []

        for report_key in [
            "conceptive_neurogenesis_report",
            "concept_lifecycle_report",
            "semantic_virtual_memory_report",
        ]:

            report = context.get(
                report_key,
                {},
            )

            if report_key == "conceptive_neurogenesis_report":

                concepts.extend([
                    item.get(
                        "concept",
                    )
                    for item in report.get(
                        "generated_concepts",
                        [],
                    )
                ])

            if report_key == "concept_lifecycle_report":

                concepts.extend([
                    item.get(
                        "concept",
                    )
                    for item in report.get(
                        "registry",
                        {},
                    ).get(
                        "concepts",
                        [],
                    )
                ])

            if report_key == "semantic_virtual_memory_report":

                for key in [
                    "active_cognition",
                    "latent_cognition",
                    "archived_cognition",
                ]:

                    for item in report.get(
                        key,
                        [],
                    ):

                        if isinstance(
                            item,
                            dict,
                        ):

                            concepts.append(
                                item.get(
                                    "concept",
                                )
                            )

                        else:

                            concepts.append(
                                item,
                            )

        return [
            concept
            for concept in concepts
            if concept
        ][:128]

    def run_cycle(self, context):

        concepts = self.collect_concepts(
            context,
        )

        encodings = []

        for concept in concepts:

            canonical = self.canonical_encode(
                concept,
            )

            encodings.append({
                "concept":
                concept,

                "canonical_encoding":
                canonical,

                "factor_count":
                len(
                    canonical.split(".")
                )
                if canonical
                else 0,
            })

        return {
            "system":
            "semantic_compression_engine",

            "encoding_mode":
            "symbolic_factorization",

            "encodings":
            encodings,

            "encoded_count":
            len(
                encodings,
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
