class LineageGenetics:

    def trace(self, traits):

        return {
            "system": "lineage_genetics",
            "lineage_tree": [
                {
                    "trait_name": trait["trait_name"],
                    "lineage_origin": trait.get("lineage_origin"),
                    "inheritance_strength": trait.get("inheritance_strength"),
                }
                for trait in traits
            ],
        }
