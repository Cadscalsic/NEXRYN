class OntologyDetoxificationAgents:

    medication_id = "ONTOLOGY_DETOX_AGENT"

    def protocol(self):

        return {
            "medication_id": self.medication_id,
            "purpose": "remove_toxic_semantic_structures",
        }
