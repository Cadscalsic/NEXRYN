from core.epistemic_models import clamp
from runtime.knowledge_replication_ledger import (
    ReplicationRecord,
    normalize_task_id,
    unwrap_context_value,
    utc_timestamp,
)


class CrossTaskReplicationCollector:
    def __init__(
        self,
        ledger,
        evidence_registry,
        knowledge_generalization_engine=None,
    ):
        self.ledger = ledger
        self.evidence_registry = evidence_registry
        self.knowledge_generalization_engine = (
            knowledge_generalization_engine
        )

    def _concepts(self, context):
        concepts = []
        epistemic = unwrap_context_value(
            context.get("epistemic_cognition_report", {})
        )
        epistemic = epistemic if isinstance(epistemic, dict) else {}
        for evaluation in epistemic.get("evaluations", []):
            concept = evaluation.get("concept")
            if concept:
                concepts.append(str(concept))

        abstractions = unwrap_context_value(
            context.get("semantic_abstractions", [])
        )
        abstractions = (
            abstractions if isinstance(abstractions, list) else []
        )
        for abstraction in abstractions:
            concept = abstraction.get(
                "semantic_concept",
                abstraction.get("concept"),
            )
            if concept:
                concepts.append(str(concept))

        return list(dict.fromkeys(concepts))

    def _metrics(self, evaluation):
        accuracy = clamp(evaluation.get("accuracy", 0.0))
        structural_score = clamp(
            evaluation.get("structural_score", accuracy)
        )
        final_score = clamp(evaluation.get("final_score", accuracy))
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
        causal_alignment = clamp(
            accuracy * 0.58
            + structural_score * 0.28
            + final_score * 0.14
        )
        return {
            "accuracy": accuracy,
            "structural_score": structural_score,
            "final_score": final_score,
            "support": support,
            "contradiction": contradiction,
            "causal_alignment": causal_alignment,
        }

    def collect(self, context):
        context = context if isinstance(context, dict) else {}
        task_path = str(unwrap_context_value(context.get("task_path", "")))
        evaluation = unwrap_context_value(
            context.get("evaluation_result", {})
        )
        concepts = self._concepts(context)
        accepted = []
        rejected = []
        exports = []

        if not task_path:
            return self._report(
                accepted,
                rejected,
                exports,
                "TASK_PATH_REQUIRED",
            )
        if not evaluation:
            return self._report(
                accepted,
                rejected,
                exports,
                "EVALUATION_RESULT_REQUIRED",
            )
        if not concepts:
            return self._report(
                accepted,
                rejected,
                exports,
                "NO_TASK_CONCEPTS_DISCOVERED",
            )

        metrics = self._metrics(evaluation)
        reliability = clamp(
            0.68
            + metrics["structural_score"] * 0.18
            + metrics["accuracy"] * 0.10
        )
        task_id = normalize_task_id(task_path)
        for concept in concepts:
            record = ReplicationRecord(
                concept=concept,
                task_id=task_id,
                task_path=task_path,
                success=metrics["final_score"] >= 0.80,
                causal_alignment=metrics["causal_alignment"],
                contradiction_score=metrics["contradiction"],
                confidence=metrics["support"],
                timestamp=utc_timestamp(),
                conditions=dict(
                    evaluation.get(
                        "conditions",
                        evaluation.get("features", {}),
                    ) or {}
                ),
                failure_reason=str(
                    evaluation.get(
                        "failure_reason",
                        ""
                        if metrics["final_score"] >= 0.80
                        else "task_score_below_success_threshold",
                    )
                ),
                reliability=reliability,
                semantic_consistency=metrics["structural_score"],
            )
            if not self.ledger.add_record(record):
                rejected.append({
                    "concept": concept,
                    "task_id": task_id,
                    "task_path": task_path,
                    "reason": "duplicate_task_replication_forbidden",
                })
                continue

            evidence = {
                "concept": concept,
                "source": "independent_execution_replication",
                "support_score": metrics["support"],
                "contradiction_score": metrics["contradiction"],
                "reliability": reliability,
                "causal_alignment": metrics["causal_alignment"],
                "semantic_consistency": metrics["structural_score"],
                "metadata": {
                    "evidence_id":
                    f"cross_task_replication:{concept}:{task_id}",
                    "task_id": task_id,
                    "task_path": task_path,
                    "collector": "cross_task_replication_collector",
                    "independent_task": True,
                    "replication_is_evidence_not_truth": True,
                    "conditions": dict(record.conditions),
                    "failure_reason": record.failure_reason,
                },
            }
            self.evidence_registry.collect(evidence)
            accepted.append(record.as_dict())
            exports.append(evidence)

        report = self._report(
            accepted,
            rejected,
            exports,
            "CROSS_TASK_REPLICATION_COLLECTED",
        )
        if self.knowledge_generalization_engine is not None:
            report["knowledge_generalization"] = (
                self.knowledge_generalization_engine.observe_task(
                    context,
                    accepted,
                )
            )
        return report

    def _report(self, accepted, rejected, exports, state):
        return {
            "system": "cross_task_replication_collector",
            "state": state,
            "accepted_records": accepted,
            "rejected_records": rejected,
            "epistemic_evidence_exports": exports,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "knowledge_replication_ledger": self.ledger.report(),
            "duplicate_task_replication_forbidden": True,
            "replication_is_evidence_not_truth": True,
        }


__all__ = [
    "CrossTaskReplicationCollector",
]
