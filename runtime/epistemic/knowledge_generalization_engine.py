from core.epistemic_models import clamp
from runtime.knowledge_replication_ledger import unwrap_context_value


class KnowledgeGeneralizationEngine:
    def __init__(self, ledger, target_independent_tasks=5):
        self.ledger = ledger
        self.target_independent_tasks = max(int(target_independent_tasks), 1)
        self._observations = []

    def extract_concepts(self, context):
        context = unwrap_context_value(context)
        context = context if isinstance(context, dict) else {}
        concepts = []
        epistemic = unwrap_context_value(
            context.get("epistemic_cognition_report", {})
        )
        epistemic = epistemic if isinstance(epistemic, dict) else {}
        for evaluation in epistemic.get("evaluations", []):
            evaluation = unwrap_context_value(evaluation)
            if isinstance(evaluation, dict) and evaluation.get("concept"):
                concepts.append(str(evaluation["concept"]))

        abstractions = unwrap_context_value(
            context.get("semantic_abstractions", [])
        )
        abstractions = (
            abstractions if isinstance(abstractions, list) else []
        )
        for abstraction in abstractions:
            abstraction = unwrap_context_value(abstraction)
            if not isinstance(abstraction, dict):
                continue
            concept = abstraction.get(
                "semantic_concept",
                abstraction.get("concept"),
            )
            if concept:
                concepts.append(str(concept))
        return list(dict.fromkeys(concepts))

    def compare_with_existing_concepts(self, concepts):
        return [
            self.update_generalization_score(concept)
            for concept in dict.fromkeys(concepts)
        ]

    def increase_cross_task_support(self, concept):
        return self.ledger.concept_report(concept)

    def update_evidence_strength(
        self,
        concept,
        evidence_strength,
        replication_bonus_already_applied=False,
    ):
        bonus = self.ledger.get_replication_bonus(concept)
        projected = clamp(
            evidence_strength
            if replication_bonus_already_applied
            else evidence_strength + bonus
        )
        return {
            "current_evidence_strength": clamp(evidence_strength),
            "replication_coverage_bonus": bonus,
            "projected_evidence_strength": projected,
            "replication_bonus_applied_once": True,
        }

    def update_generalization_score(self, concept):
        report = self.ledger.concept_report(concept)
        records = report["records"]
        causal_alignment = (
            sum(item["causal_alignment"] for item in records) / len(records)
            if records
            else 0.0
        )
        contradiction_score = (
            sum(item["contradiction_score"] for item in records) / len(records)
            if records
            else 1.0
        )
        task_coverage = clamp(
            report["independent_replications"]
            / self.target_independent_tasks
        )
        score = clamp(
            task_coverage * 0.45
            + report["cross_task_support"] * 0.25
            + report["independent_success_rate"] * 0.20
            + causal_alignment * 0.10
        )
        return {
            **report,
            "generalization_score": score,
            "task_coverage_ratio": task_coverage,
            "target_independent_tasks": self.target_independent_tasks,
            "remaining_independent_tasks": max(
                self.target_independent_tasks
                - report["independent_replications"],
                0,
            ),
            "average_causal_alignment": clamp(causal_alignment),
            "average_contradiction_score": clamp(contradiction_score),
            "generalization_state": (
                "CROSS_TASK_GENERALIZED"
                if task_coverage >= 1.0
                else "CROSS_TASK_SUPPORT_GROWING"
                if records
                else "AWAITING_CROSS_TASK_OBSERVATIONS"
            ),
        }

    def evaluate(
        self,
        concept,
        evidence_strength=0.0,
        replication_bonus_already_applied=False,
    ):
        return {
            "system": "knowledge_generalization_engine",
            "phase": "6.5",
            "concept": concept,
            **self.update_generalization_score(concept),
            **self.update_evidence_strength(
                concept,
                evidence_strength,
                replication_bonus_already_applied,
            ),
            "cross_task_replication_is_evidence_not_truth": True,
            "duplicate_task_replication_forbidden": True,
            "automatic_truth_promotion_forbidden": True,
        }

    def observe_task(self, context, accepted_records=None):
        concepts = self.extract_concepts(context)
        observation = {
            "system": "knowledge_generalization_engine",
            "phase": "6.5",
            "observed_concepts": concepts,
            "accepted_cross_task_records": list(accepted_records or []),
            "concept_comparisons":
            self.compare_with_existing_concepts(concepts),
            "duplicate_task_replication_forbidden": True,
            "automatic_truth_promotion_forbidden": True,
        }
        self._observations.append(observation)
        self._observations = self._observations[-64:]
        return observation

    def report(self):
        concepts = sorted({
            concept
            for observation in self._observations
            for concept in observation["observed_concepts"]
        })
        return {
            "system": "knowledge_generalization_engine",
            "phase": "6.5",
            "concepts": self.compare_with_existing_concepts(concepts),
            "observation_count": len(self._observations),
            "task_learning_to_concept_learning": True,
            "cross_task_replication_is_evidence_not_truth": True,
            "duplicate_task_replication_forbidden": True,
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "KnowledgeGeneralizationEngine",
]
