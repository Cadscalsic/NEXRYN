from core.epistemic_models import clamp


class ConceptSchemaValidator:
    CONCEPT_KEYS = (
        "concept",
        "semantic_concept",
        "compressed_concept",
    )

    def _concept(self, item):
        if isinstance(item, str):
            return item.strip()
        if not isinstance(item, dict):
            return ""
        for key in self.CONCEPT_KEYS:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def normalize_item(self, item, record_type="concept"):
        concept = self._concept(item)
        if not concept:
            return None, {
                "item": item,
                "reason": "concept_identifier_required",
            }

        normalized = (
            {"concept": concept}
            if isinstance(item, str)
            else dict(item)
        )
        normalized["concept"] = concept
        normalized.setdefault("semantic_concept", concept)
        confidence = clamp(
            normalized.get(
                "calibrated_confidence",
                normalized.get("confidence", 1.0),
            )
        )
        normalized.setdefault("confidence", confidence)
        if record_type == "truth_commitment":
            normalized.setdefault("claim", concept)
            normalized.setdefault("calibrated_confidence", confidence)
            normalized.setdefault("status", "ACTIVE")
            normalized.setdefault("reusable", True)
        normalized["concept_contract"] = {
            "schema": "nexryn_concept_v1",
            "record_type": record_type,
            "normalized_from_string": isinstance(item, str),
        }
        return normalized, None

    def normalize_items(self, items, record_type="concept"):
        if items is None:
            items = []
        elif isinstance(items, (str, dict)):
            items = [items]
        elif not isinstance(items, list):
            items = list(items) if isinstance(items, tuple) else [items]

        normalized_items = []
        rejected_items = []
        coerced_string_count = 0
        for item in items:
            normalized, rejected = self.normalize_item(
                item,
                record_type,
            )
            if rejected:
                rejected_items.append(rejected)
                continue
            normalized_items.append(normalized)
            coerced_string_count += int(isinstance(item, str))

        return {
            "system": "concept_schema_validator",
            "phase": "7.5",
            "schema": "nexryn_concept_v1",
            "record_type": record_type,
            "normalized_items": normalized_items,
            "input_count": len(items),
            "accepted_count": len(normalized_items),
            "coerced_string_count": coerced_string_count,
            "rejected_count": len(rejected_items),
            "rejected_items": rejected_items,
            "contract_enforced": True,
        }


concept_schema_validator = ConceptSchemaValidator()


__all__ = [
    "ConceptSchemaValidator",
    "concept_schema_validator",
]
