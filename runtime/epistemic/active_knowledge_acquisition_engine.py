from core.epistemic_models import clamp


class ActiveKnowledgeAcquisitionEngine:
    REQUIRED_RESULT_FIELDS = {
        "experiment_id",
        "concept",
        "baseline_execution_result",
        "intervention_execution_result",
        "causal_effect_delta",
        "contradiction_delta",
        "measured_causal_alignment",
        "measured_contradiction_score",
    }

    def prepare_request(self, proposal, hypothesis):
        if not proposal or not hypothesis:
            return None

        return {
            "system": "active_knowledge_acquisition_engine",
            "phase": "5.4",
            "request_id": f"sandbox_request:{proposal['experiment_id']}",
            "experiment_id": proposal["experiment_id"],
            "concept": proposal["concept"],
            "acquisition_state": "SANDBOX_EXECUTION_REQUESTED",
            "execution_permission": "sandbox_only",
            "autonomous_sandbox_execution_permitted": True,
            "persistent_external_execution_forbidden": True,
            "hypothesis": hypothesis,
            "experiment_proposal": proposal,
            "execution_contract": {
                "isolated_world_required": True,
                "reversible_intervention_required": True,
                "persistent_commit_forbidden": True,
                "automatic_truth_commit_forbidden": True,
                "required_result_fields": sorted(
                    self.REQUIRED_RESULT_FIELDS
                ),
            },
        }

    def ingest_results(self, results):
        results = results or []
        if isinstance(results, dict):
            results = [results]

        accepted = []
        rejected = []
        exports = []
        for result in results:
            missing = sorted(
                self.REQUIRED_RESULT_FIELDS - set(result)
            )
            rejection_reason = None
            if missing:
                rejection_reason = "missing_required_result_fields"
            elif result.get("sandbox_validated") is not True:
                rejection_reason = "sandbox_validation_required"
            elif result.get("reversible") is not True:
                rejection_reason = "reversible_intervention_required"

            if rejection_reason:
                rejected.append({
                    "experiment_id": result.get("experiment_id"),
                    "concept": result.get("concept"),
                    "reason": rejection_reason,
                    "missing_fields": missing,
                })
                continue

            experiment_id = result["experiment_id"]
            accepted.append({
                "experiment_id": experiment_id,
                "concept": result["concept"],
                "result_state": "SANDBOX_RESULT_ACCEPTED",
            })
            exports.append({
                "concept": result["concept"],
                "source": "sandbox_causal_intervention",
                "support_score": clamp(
                    result.get("measured_support_score", 0.75)
                ),
                "contradiction_score": clamp(
                    result["measured_contradiction_score"]
                ),
                "reliability": clamp(
                    result.get("measurement_reliability", 0.90)
                ),
                "causal_alignment": clamp(
                    result["measured_causal_alignment"]
                ),
                "semantic_consistency": clamp(
                    result.get("semantic_consistency", 0.80)
                ),
                "metadata": {
                    "evidence_id": f"sandbox_result:{experiment_id}",
                    "experiment_id": experiment_id,
                    "sandbox_validated": True,
                    "reversible": True,
                    "causal_effect_delta": clamp(
                        result["causal_effect_delta"]
                    ),
                    "contradiction_delta": clamp(
                        result["contradiction_delta"],
                        -1.0,
                        1.0,
                    ),
                    "truth_commit_forbidden": True,
                    "synthetic_sandbox_probe":
                    result.get("synthetic_sandbox_probe", False),
                    "generated_task_id": result.get("generated_task_id"),
                    "independent_task_replication": False,
                },
            })

        return {
            "system": "active_knowledge_acquisition_engine",
            "phase": "5.4",
            "accepted_results": accepted,
            "rejected_results": rejected,
            "epistemic_evidence_exports": exports,
            "reevaluate_truth_candidate_after_ingestion": bool(exports),
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "ActiveKnowledgeAcquisitionEngine",
]
