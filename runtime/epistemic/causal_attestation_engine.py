from core.epistemic_models import clamp


class CausalAttestationEngine:
    DIRECT_CAUSAL_SOURCES = {
        "causal_attestation",
        "execution_validation",
        "sandbox_causal_intervention",
    }

    def _gap(self, required, current):
        return round(max(required - current, 0.0), 4)

    def evaluate(
        self,
        concept,
        aggregate,
        evidence_items=None,
        epistemic_partition=None,
        arbitration=None,
    ):
        evidence_items = list(evidence_items or [])
        source_groups = {}
        for item in evidence_items:
            source_groups.setdefault(item.source, []).append(item)
        source_diagnostics = []
        for source, items in sorted(source_groups.items()):
            source_diagnostics.append({
                "source": source,
                "evidence_count": len(items),
                "average_causal_alignment": clamp(
                    sum(item.causal_alignment for item in items)
                    / max(len(items), 1)
                ),
                "direct_causal_attestation":
                source in self.DIRECT_CAUSAL_SOURCES,
            })

        current = aggregate.causal_alignment
        trial_gap = self._gap(0.60, current)
        candidate_gap = self._gap(0.80, current)
        direct_sources = [
            item
            for item in source_diagnostics
            if item["direct_causal_attestation"]
        ]
        architecture_state = (
            "CAUSAL_ATTESTATION_INSUFFICIENT_FOR_TRIAL"
            if trial_gap
            else "CAUSAL_ATTESTATION_FORMING"
            if candidate_gap
            else "CAUSAL_ALIGNMENT_READY"
        )

        return {
            "system": "causal_attestation_engine",
            "concept": concept,
            "architecture_state": architecture_state,
            "current_causal_alignment": current,
            "trial_resolution_threshold": 0.60,
            "trial_resolution_gap": trial_gap,
            "truth_candidate_threshold": 0.80,
            "truth_candidate_gap": candidate_gap,
            "direct_causal_source_count": len(direct_sources),
            "direct_causal_evidence_count": sum(
                item["evidence_count"]
                for item in direct_sources
            ),
            "source_diagnostics": source_diagnostics,
            "epistemic_partition": epistemic_partition or {},
            "causal_evidence_arbitration": arbitration or {},
            "required_action": (
                "collect_causal_attestation_evidence"
                if candidate_gap
                else None
            ),
            "semantic_observation_is_not_causal_proof": True,
        }


__all__ = [
    "CausalAttestationEngine",
]
