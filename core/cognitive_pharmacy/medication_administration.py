# ============================================
# NEXRYN COGNITIVE PHARMACY MEDICATION ADMINISTRATION
# ============================================


class MedicationAdministration:

    def administer(self, registry, dosage, governance_review):

        approved = governance_review.get(
            "approved_for_controlled_execution",
            False,
        )

        administrations = []

        for medication_id, medication in registry.list_medications().items():

            dose = dosage.get(
                medication_id,
                0.0,
            )

            administrations.append({
                "medication_id": medication_id,
                "category": medication.get(
                    "category",
                ),
                "requested_dose": dose,
                "administered_dose": (
                    dose
                    if approved
                    else 0.0
                ),
                "administration_state": (
                    "controlled_administration"
                    if approved and dose > 0
                    else "held_for_governance"
                    if not approved
                    else "not_indicated"
                ),
                "effects": medication.get(
                    "effects",
                    [],
                ),
            })

        return {
            "system": "medication_administration",
            "governance_approved": approved,
            "administrations": administrations,
            "direct_runtime_mutation": False,
            "authority": "controlled_administration_only",
        }
