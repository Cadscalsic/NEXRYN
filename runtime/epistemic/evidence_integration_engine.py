class EvidenceIntegrationEngine:
    def __init__(self, acquisition_engine, evidence_registry):
        self.acquisition_engine = acquisition_engine
        self.evidence_registry = evidence_registry

    def integrate(self, results):
        ingestion = self.acquisition_engine.ingest_results(results)
        integrated = []
        for item in ingestion["epistemic_evidence_exports"]:
            evidence = self.evidence_registry.collect(item)
            integrated.append(evidence.as_dict())
        return {
            "system": "evidence_integration_engine",
            "phase": "6.95",
            "ingestion": ingestion,
            "integrated_evidence": integrated,
            "integrated_evidence_count": len(integrated),
            "sandbox_validation_required": True,
            "evidence_integration_is_not_truth_commitment": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "EvidenceIntegrationEngine",
]
