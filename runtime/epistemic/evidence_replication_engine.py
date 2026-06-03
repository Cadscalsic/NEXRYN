from core.epistemic_models import clamp
from runtime.knowledge_replication_ledger import (
    KnowledgeReplicationLedger,
    ReplicationRecord,
    normalize_task_id,
    unwrap_context_value,
    utc_timestamp,
)


class EvidenceReplicationEngine:
    def __init__(self, maximum_requests_per_cycle=2, ledger=None):
        self.maximum_requests_per_cycle = max(
            int(maximum_requests_per_cycle),
            1,
        )
        self.requested_tasks = set()
        self.ledger = ledger or KnowledgeReplicationLedger()

    def _task_id(self, task_path):
        return normalize_task_id(task_path)

    def _task_key(self, concept, task_path):
        return f"{concept}:{self._task_id(task_path)}"

    def _candidates(self, context):
        candidates = context.get("arc_replication_candidates", [])
        if isinstance(candidates, dict):
            candidates = [candidates]
        return list(candidates)

    def propose(self, concept, belief, truth_candidate, context=None):
        context = context if isinstance(context, dict) else {}
        blocked_metrics = truth_candidate.get("blocked_metrics", [])
        causal_alignment = next(
            (
                item["current_value"]
                for item in truth_candidate.get("metrics", [])
                if item["metric"] == "causal_alignment"
            ),
            0.0,
        )
        contradiction_score = next(
            (
                item["current_value"]
                for item in truth_candidate.get("metrics", [])
                if item["metric"] == "contradiction_score"
            ),
            1.0,
        )
        eligible = (
            truth_candidate.get(
                "stage_eligible_for_truth_candidate",
                False,
            )
            and blocked_metrics == ["evidence_strength"]
            and causal_alignment >= 0.90
            and contradiction_score < 0.10
        )
        requests = []
        if eligible:
            for candidate in self._candidates(context):
                task_path = str(
                    unwrap_context_value(candidate.get("task_path", ""))
                )
                if not task_path:
                    continue
                task_key = self._task_key(concept, task_path)
                task_id = self._task_id(task_path)
                if (
                    task_key in self.requested_tasks
                    or self.ledger.has_task(concept, task_id)
                ):
                    continue
                requests.append({
                    "system": "evidence_replication_engine",
                    "phase": "5.9",
                    "request_id": f"replication_request:{task_key}",
                    "concept": concept,
                    "task_path": task_path,
                    "task_id": task_id,
                    "replication_strategy":
                    "independent_cross_task_execution_validation",
                    "execution_permission": "sandbox_only",
                    "isolated_world_required": True,
                    "independent_task_required": True,
                    "persistent_commit_forbidden": True,
                    "automatic_truth_promotion_forbidden": True,
                })
                self.requested_tasks.add(task_key)
                if len(requests) >= self.maximum_requests_per_cycle:
                    break

        return {
            "system": "evidence_replication_engine",
            "phase": "5.9",
            "concept": concept,
            "replication_state": (
                "INDEPENDENT_REPLICATION_REQUESTED"
                if requests
                else "AWAITING_NEW_ARC_REPLICATION_TASKS"
                if eligible
                else "REPLICATION_NOT_REQUIRED"
            ),
            "eligible_for_replication": eligible,
            "sandbox_replication_requests": requests,
            **self.ledger.concept_report(concept),
            "duplicate_task_replication_forbidden": True,
            "automatic_truth_promotion_forbidden": True,
        }

    def ingest_results(self, results):
        results = results or []
        if isinstance(results, dict):
            results = [results]
        accepted = []
        rejected = []
        exports = []

        for result in results:
            concept = str(result.get("concept", ""))
            task_path = str(
                unwrap_context_value(result.get("task_path", ""))
            )
            task_key = self._task_key(concept, task_path)
            task_id = self._task_id(task_path)
            reason = None
            if not concept or not task_path:
                reason = "concept_and_task_path_required"
            elif result.get("sandbox_validated") is not True:
                reason = "sandbox_validation_required"
            elif result.get("isolated_world") is not True:
                reason = "isolated_world_validation_required"
            elif result.get("independent_task") is not True:
                reason = "independent_task_validation_required"
            elif self.ledger.has_task(concept, task_id):
                reason = "duplicate_task_replication_forbidden"

            if reason:
                rejected.append({
                    "concept": concept,
                    "task_path": task_path,
                    "reason": reason,
                })
                continue

            accuracy = clamp(result.get("accuracy", 0.0))
            structural_score = clamp(
                result.get("structural_score", accuracy)
            )
            final_score = clamp(result.get("final_score", accuracy))
            support = clamp(
                accuracy * 0.42
                + structural_score * 0.34
                + final_score * 0.24
            )
            contradiction = clamp(
                (1.0 - accuracy) * 0.48
                + (1.0 - structural_score) * 0.30
                + (1.0 - final_score) * 0.22
            )
            reliability = clamp(
                0.68 + structural_score * 0.18 + accuracy * 0.10
            )
            self.requested_tasks.discard(task_key)
            record = ReplicationRecord(
                concept=concept,
                task_id=task_id,
                task_path=task_path,
                success=final_score >= 0.80,
                causal_alignment=clamp(
                    accuracy * 0.58
                    + structural_score * 0.28
                    + final_score * 0.14
                ),
                contradiction_score=contradiction,
                confidence=support,
                timestamp=str(
                    result.get("timestamp", utc_timestamp())
                ),
                conditions=dict(
                    result.get(
                        "conditions",
                        result.get("features", {}),
                    ) or {}
                ),
                failure_reason=str(
                    result.get(
                        "failure_reason",
                        ""
                        if final_score >= 0.80
                        else "replication_score_below_success_threshold",
                    )
                ),
                reliability=reliability,
                semantic_consistency=structural_score,
            )
            self.ledger.add_record(record)
            accepted.append({
                "concept": concept,
                "task_path": task_path,
                "task_id": task_id,
                "replication_state": "INDEPENDENT_REPLICATION_ACCEPTED",
                "passed": record.success,
            })
            exports.append({
                "concept": concept,
                "source": "independent_execution_replication",
                "support_score": support,
                "contradiction_score": contradiction,
                "reliability": reliability,
                "causal_alignment": record.causal_alignment,
                "semantic_consistency": structural_score,
                "metadata": {
                    "evidence_id": f"independent_replication:{task_key}",
                    "task_path": task_path,
                    "task_id": task_id,
                    "sandbox_validated": True,
                    "isolated_world": True,
                    "independent_task": True,
                    "replication_is_evidence_not_truth": True,
                    "conditions": dict(record.conditions),
                    "failure_reason": record.failure_reason,
                },
            })

        return {
            "system": "evidence_replication_engine",
            "phase": "5.9",
            "accepted_results": accepted,
            "rejected_results": rejected,
            "epistemic_evidence_exports": exports,
            "knowledge_replication_ledger": self.ledger.report(),
            "reevaluate_truth_candidate_after_ingestion": bool(exports),
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "EvidenceReplicationEngine",
]
