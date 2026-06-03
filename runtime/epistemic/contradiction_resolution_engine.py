from core.epistemic_models import clamp
from runtime.epistemic.contradiction_attribution_engine import (
    ContradictionAttributionEngine,
)


class ContradictionResolutionEngine:
    DIRECT_EXECUTION_SOURCES = {
        "causal_attestation",
        "execution_validation",
    }

    def __init__(self, attribution_engine=None):
        self.attribution_engine = (
            attribution_engine or ContradictionAttributionEngine()
        )

    def _gap(self, current, required):
        return round(max(current - required, 0.0), 4)

    def evaluate(
        self,
        concept,
        aggregate,
        evidence_items=None,
        evidence_weight=None,
        epistemic_partition=None,
    ):
        attribution = self.attribution_engine.evaluate(
            concept,
            aggregate,
            evidence_items,
            evidence_weight,
        )
        source_diagnostics = attribution["source_attributions"]
        ranked_sources = attribution[
            "ranked_effective_contradiction_sources"
        ]
        current = attribution["effective_contradiction_score"]
        trial_gap = self._gap(current, 0.18)
        candidate_gap = self._gap(current, 0.10)
        resolution_state = (
            "CONTRADICTION_CLEAR_FOR_TRIAL"
            if not trial_gap
            else "NEAR_TRIAL_RESOLUTION"
            if trial_gap <= 0.02
            else "CONTRADICTION_RESOLUTION_REQUIRED"
        )
        dominant_source = ranked_sources[0] if ranked_sources else None

        return {
            "system": "contradiction_resolution_engine",
            "concept": concept,
            "resolution_state": resolution_state,
            "current_contradiction_score": current,
            "raw_contradiction_score":
            attribution["raw_contradiction_score"],
            "effective_contradiction_score": current,
            "trial_resolution_threshold": 0.18,
            "trial_resolution_gap": trial_gap,
            "truth_candidate_threshold": 0.10,
            "truth_candidate_gap": candidate_gap,
            "source_diagnostics": source_diagnostics,
            "ranked_contradiction_sources": ranked_sources,
            "dominant_contradiction_source": dominant_source,
            "raw_ranked_contradiction_sources":
            attribution["ranked_raw_contradiction_sources"],
            "raw_dominant_contradiction_source":
            attribution["dominant_raw_contradiction_source"],
            "contradiction_attribution": attribution,
            "epistemic_partition": epistemic_partition or {},
            "required_actions": (
                [
                    "inspect_dominant_contradiction_source",
                    "collect_disambiguating_execution_evidence",
                ]
                if trial_gap
                else []
            ),
            "automatic_contradiction_attenuation_forbidden": True,
        }


__all__ = [
    "ContradictionResolutionEngine",
]
