from core.epistemic_models import clamp


class CausalCounterexampleStore:
    def __init__(self, ledger):
        self.ledger = ledger

    def _record_profile(self, record):
        conditions = dict(record.conditions or {})
        conditions.setdefault(
            "causal_alignment_region",
            self._region(record.causal_alignment),
        )
        conditions.setdefault(
            "contradiction_region",
            self._region(record.contradiction_score),
        )
        conditions.setdefault(
            "confidence_region",
            self._region(record.confidence),
        )
        return {
            **record.as_dict(),
            "conditions": conditions,
            "outcome": "HOLDS" if record.success else "FAILS",
            "failure_reason": (
                record.failure_reason
                if not record.success
                else ""
            ),
        }

    def _region(self, value):
        value = clamp(value)
        if value >= 0.80:
            return "high"
        if value >= 0.60:
            return "medium"
        return "low"

    def report_for(self, concept):
        profiles = [
            self._record_profile(record)
            for record in self.ledger.get_concept_records(concept)
        ]
        holds = [
            item
            for item in profiles
            if item["outcome"] == "HOLDS"
        ]
        failures = [
            item
            for item in profiles
            if item["outcome"] == "FAILS"
        ]
        return {
            "system": "causal_counterexample_store",
            "phase": "6.93",
            "concept": concept,
            "observation_count": len(profiles),
            "supported_observations": holds,
            "counterexamples": failures,
            "supported_observation_count": len(holds),
            "counterexample_count": len(failures),
            "counterexamples_are_boundary_evidence_not_truth_negation": True,
        }


__all__ = [
    "CausalCounterexampleStore",
]
