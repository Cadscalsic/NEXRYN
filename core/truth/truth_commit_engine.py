from core.epistemic_models import clamp
from core.truth.truth_registry import TruthRegistry
from runtime.semantics.concept_schema_validator import (
    concept_schema_validator,
)


class TruthCommitEngine:
    def __init__(self, registry=None, storage_path=None):
        self.registry = registry or TruthRegistry(storage_path=storage_path)

    def _evidence_sources(self, context):
        evidence = context.get("truth_commit_evidence", [])
        if isinstance(evidence, dict):
            evidence = [evidence]
        return sorted({
            (
                item.get("source")
                if isinstance(item, dict)
                else getattr(item, "source", None)
            )
            for item in evidence
            if (
                item.get("source")
                if isinstance(item, dict)
                else getattr(item, "source", None)
            )
        })

    def _source_tasks(self, context):
        generalization = context.get("knowledge_generalization", {})
        source_tasks = {
            str(item.get("task_path", item.get("task_id")))
            for item in generalization.get("records", [])
            if item.get("task_path", item.get("task_id"))
        }
        if context.get("task_path"):
            source_tasks.add(str(context["task_path"]))
        return sorted(source_tasks)

    def evaluate(
        self,
        concept,
        aggregate,
        truth_candidate,
        identity_integration,
        context=None,
    ):
        context = context if isinstance(context, dict) else {}
        normalized, rejected = concept_schema_validator.normalize_item(
            {"concept": concept},
            record_type="truth_commitment",
        )
        gates = {
            "truth_candidate_ready":
            truth_candidate.get(
                "eligible_for_truth_candidate",
                False,
            )
            is True,
            "identity_safe":
            identity_integration.get("integration_safe", False) is True,
            "schema_valid": rejected is None,
        }
        dependency_promotion_diagnostics = {
            "promotion_dependency_score":
            truth_candidate.get("promotion_dependency_score", 0.0),
            "promotion_dependency_bonus":
            truth_candidate.get("promotion_dependency_bonus", 0.0),
            "dependency_promotion_blockers":
            truth_candidate.get("dependency_promotion_blockers", []),
            "dependency_adjusted_candidate_ready":
            truth_candidate.get("eligible_for_truth_candidate", False),
            "dependency_does_not_override_identity_governance": True,
        }
        eligible = all(gates.values())
        record = None
        if eligible:
            generalization = context.get("knowledge_generalization", {})
            lineage = context.get("truth_lineage", {}).get(
                normalized["concept"],
                {},
            )
            record = self.registry.upsert(
                concept=normalized["concept"],
                confidence=clamp(
                    context.get(
                        "calibrated_confidence",
                        context.get("confidence", 0.0),
                    )
                ),
                evidence_strength=clamp(aggregate.evidence_strength),
                causal_alignment=clamp(aggregate.causal_alignment),
                contradiction_score=clamp(
                    aggregate.contradiction_score
                ),
                semantic_consistency=clamp(
                    aggregate.semantic_consistency
                ),
                generalization_score=clamp(
                    generalization.get("generalization_score", 0.0)
                ),
                identity_continuity=clamp(
                    identity_integration.get(
                        "identity_continuity",
                        0.0,
                    )
                ),
                semantic_drift=clamp(
                    identity_integration.get("semantic_drift", 1.0)
                ),
                source_tasks=self._source_tasks(context),
                evidence_sources=self._evidence_sources(context),
                lineage=dict(lineage or {}),
            )
        return {
            "system": "provisional_truth_commit_engine",
            "phase": "7.0",
            "concept": concept,
            "decision": (
                "PROVISIONAL_TRUTH_COMMITMENT"
                if eligible
                else "REMAIN_TRUTH_CANDIDATE"
            ),
            "eligible_for_provisional_commitment": eligible,
            "gates": gates,
            "failed_gates": [
                name
                for name, passed in gates.items()
                if not passed
            ],
            "dependency_promotion_diagnostics":
            dependency_promotion_diagnostics,
            "truth_record": (
                record.as_dict()
                if record is not None
                else None
            ),
            "final_truth_commitment_requires_review": True,
        }

    def report(self):
        return {
            "system": "provisional_truth_commit_engine",
            "phase": "7.0",
            "transition":
            "TRUTH_CANDIDATE + identity_safe + schema_valid -> PROVISIONAL_TRUTH_COMMITMENT",
            "registry": self.registry.report(),
            "final_truth_commitment_requires_review": True,
        }


__all__ = [
    "TruthCommitEngine",
]
