from core.knowledge.truth_state_authority import TruthStateAuthority
from core.truth.truth_candidate_engine import (
    TruthCandidatePromotionEngine,
)


class ConceptMaturityTracker:
    TRUTH_CANDIDATE_MINIMUM_TASKS = 8
    TRUTH_CANDIDATE_MINIMUM_SUPPORT = 0.80
    TRUTH_CANDIDATE_MINIMUM_CAUSAL_ALIGNMENT = 0.80
    TRUTH_CANDIDATE_MAXIMUM_CONTRADICTION = 0.10

    STATES = [
        "DISCOVERING",
        "SUPPORTED",
        "GENERALIZING",
        "BOUNDARY_REFINEMENT",
        "TRUTH_CANDIDATE",
        "STABLE_TRUTH",
    ]

    def __init__(
        self,
        supported_task_count=3,
        generalizing_task_count=5,
    ):
        self.supported_task_count = max(int(supported_task_count), 1)
        self.generalizing_task_count = max(
            int(generalizing_task_count),
            self.supported_task_count,
        )
        self._concepts = {}
        self.truth_state_authority = TruthStateAuthority()
        self.truth_candidate_promotion_engine = (
            TruthCandidatePromotionEngine()
        )

    def _concept_names(self, report, key, accepted_key=None):
        concepts = set()
        for item in report.get(key, []):
            if not isinstance(item, dict):
                continue
            if accepted_key and item.get(accepted_key) is not True:
                continue
            concept = item.get("concept")
            if concept:
                concepts.add(str(concept))
        return concepts

    def _stable_truths(self, truth_registry):
        return self.truth_state_authority.stable_truth_concepts(
            truth_registry,
        )

    def _lock_candidate_ready(self, promotion, reason):
        readiness_gates = {
            gate: True
            for gate in promotion.get("readiness_gates", {})
        }
        return {
            **promotion,
            "decision": reason,
            "candidate_ready": True,
            "readiness_gates": readiness_gates,
            "failed_gates": [],
            "candidate_ready_lock_reason": reason,
            "raw_readiness_gates_before_lifecycle_lock":
            promotion.get("readiness_gates", {}),
            "raw_failed_gates_before_lifecycle_lock":
            promotion.get("failed_gates", []),
        }

    def evaluate(
        self,
        ledger_report=None,
        truth_candidate_report=None,
        truth_registry=None,
    ):
        ledger_report = ledger_report or {}
        truth_candidate_report = truth_candidate_report or {}
        truth_registry = truth_registry or {}
        candidate_concepts = self._concept_names(
            truth_candidate_report,
            "evaluations",
            "eligible_for_truth_candidate",
        )
        stable_truths = self._stable_truths(truth_registry)

        concepts = []
        for item in ledger_report.get("concepts", []):
            concept = str(item.get("concept", ""))
            if not concept:
                continue
            records = list(item.get("records", []))
            successful_tasks = sum(
                record.get("success") is True
                for record in records
            )
            counterexample_tasks = sum(
                record.get("success") is False
                for record in records
            )
            used_task_count = int(item.get("used_task_count", 0))
            mixed_outcomes = bool(successful_tasks and counterexample_tasks)
            average_causal_alignment = (
                sum(
                    record.get("causal_alignment", 0.0)
                    for record in records
                )
                / len(records)
                if records
                else 0.0
            )
            average_contradiction_score = (
                sum(
                    record.get("contradiction_score", 0.0)
                    for record in records
                )
                / len(records)
                if records
                else 1.0
            )
            cross_task_support = item.get("cross_task_support", 0.0)
            promotion = self.truth_candidate_promotion_engine.evaluate(
                item,
                truth_candidate_report,
            )
            if concept in stable_truths:
                state = "STABLE_TRUTH"
                promotion = self._lock_candidate_ready(
                    promotion,
                    "STABLE_TRUTH_CANDIDATE_LOCKED",
                )
            elif (
                concept in candidate_concepts
                or promotion["candidate_ready"]
            ):
                state = "TRUTH_CANDIDATE"
                if concept in candidate_concepts:
                    promotion = self._lock_candidate_ready(
                        promotion,
                        "RUNTIME_TRUTH_CANDIDATE_READY",
                    )
            elif mixed_outcomes:
                state = "BOUNDARY_REFINEMENT"
            elif used_task_count >= self.generalizing_task_count:
                state = "GENERALIZING"
            elif used_task_count >= self.supported_task_count:
                state = "SUPPORTED"
            else:
                state = "DISCOVERING"
            readiness_gates = {
                "independent_task_coverage": promotion[
                    "readiness_gates"
                ]["observed_task_count"],
                "cross_task_support": promotion["readiness_gates"][
                    "cross_task_support"
                ],
                "causal_alignment": promotion["readiness_gates"][
                    "causal_stability"
                ],
                "contradiction_score": promotion["readiness_gates"][
                    "contradiction_governance"
                ],
                "context_strength": promotion["readiness_gates"][
                    "context_strength"
                ],
                "identity_strength": promotion["readiness_gates"][
                    "identity_strength"
                ],
            }

            maturity = {
                "concept": concept,
                "state": state,
                "used_task_count": used_task_count,
                "task_ids": list(item.get("used_task_ids", [])),
                "successful_task_count": successful_tasks,
                "counterexample_task_count": counterexample_tasks,
                "mixed_outcomes_detected": mixed_outcomes,
                "independent_success_rate":
                item.get("independent_success_rate", 0.0),
                "cross_task_support": item.get("cross_task_support", 0.0),
                "average_causal_alignment":
                round(average_causal_alignment, 4),
                "average_contradiction_score":
                round(average_contradiction_score, 4),
                "truth_candidate_readiness_gates": readiness_gates,
                "preliminary_truth_candidate_ready":
                promotion["candidate_ready"],
                "truth_candidate_promotion": promotion,
                "truth_candidate_requires_epistemic_gates": True,
                "stable_truth_requires_truth_registry_commitment": True,
            }
            self._concepts[concept] = maturity
            concepts.append(maturity)

        return {
            "system": "concept_maturity_tracker",
            "states": list(self.STATES),
            "concepts": concepts,
            "candidate_ready_definition":
            "TRUTH_CANDIDATE_OR_STABLE_TRUTH_IMPLIES_CANDIDATE_READY",
            "candidate_ready_lifecycle_invariant_preserved": all(
                concept["preliminary_truth_candidate_ready"]
                for concept in concepts
                if concept["state"] in {
                    "TRUTH_CANDIDATE",
                    "STABLE_TRUTH",
                }
            ),
            "state_counts": {
                state: sum(
                    concept["state"] == state
                    for concept in concepts
                )
                for state in self.STATES
            },
            "closest_truth_candidate_concepts": [
                concept["concept"]
                for concept in concepts
                if concept["state"] in {
                    "GENERALIZING",
                    "BOUNDARY_REFINEMENT",
                    "TRUTH_CANDIDATE",
                }
            ],
            "count_alone_cannot_promote_truth": True,
        }


__all__ = [
    "ConceptMaturityTracker",
]
