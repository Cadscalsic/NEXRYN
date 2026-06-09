from core.truth_commit_engine import TruthCommitEngine
from runtime.truth_registry import TruthRecord
from runtime.truth_registry import TruthRegistry
from runtime.truth_registry import TruthRetrievalEngine
from runtime.truth_registry import TruthReinforcementEngine
from core.truth import TruthCommitEngine as ProvisionalTruthCommitEngine


class TruthCommitmentEngine(TruthCommitEngine):
    def __init__(
        self,
        *args,
        truth_registry_path=None,
        provisional_truth_registry_path=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.registry = TruthRegistry(storage_path=truth_registry_path)
        self.provisional_truth_commit_engine = (
            ProvisionalTruthCommitEngine(
                storage_path=provisional_truth_registry_path
            )
        )
        self.retrieval_engine = TruthRetrievalEngine(self.registry)
        self.reinforcement_engine = TruthReinforcementEngine(self.registry)
        self.truth_registry = {
            record["concept"]: self.registry.retrieve_record(
                record["concept"]
            )
            for record in self.registry.all_truths()
            if record["status"] == "ACTIVE"
        }
        self.review_history = []

    @property
    def truth_object_registry(self):
        return {
            record["concept"]: self.registry.retrieve_record(
                record["concept"]
            )
            for record in self.registry.all_truths()
        }

    def _lineage(self, belief, context):
        context = context if isinstance(context, dict) else {}
        evidence = context.get("truth_commit_evidence", [])
        if isinstance(evidence, dict):
            evidence = [evidence]
        metadata = context.get("truth_lineage", {}).get(
            belief.concept,
            {},
        )
        parent_truths = metadata.get(
            "parent_truths",
            context.get("parent_truths", []),
        )
        observed_sources = [
            item.get("source")
            if isinstance(item, dict)
            else getattr(item, "source", None)
            for item in evidence
        ]
        evidence_sources = metadata.get(
            "evidence_sources",
            [
                source
                for source in observed_sources
                if source
            ],
        )
        return {
            "parent_truths": list(parent_truths or []),
            "evidence_sources": list(evidence_sources or []),
        }

    def _evidence_snapshot(self, context):
        evidence = context.get("truth_commit_evidence", [])
        if isinstance(evidence, dict):
            evidence = [evidence]
        return [
            (
                item.as_dict()
                if hasattr(item, "as_dict")
                else dict(item)
            )
            for item in evidence
            if isinstance(item, dict) or hasattr(item, "as_dict")
        ]

    def _causal_history(self, aggregate, evidence, context):
        history = context.get("truth_causal_history", [])
        if isinstance(history, dict):
            history = [history]
        causal_history = list(history)
        causal_history.extend([
            {
                "source": item.get("source"),
                "causal_alignment": item.get("causal_alignment", 0.0),
                "support_score": item.get("support_score", 0.0),
                "observed_at": item.get("observed_at"),
            }
            for item in evidence
            if item.get("source")
        ])
        causal_history.append({
            "source": "truth_commit_aggregate",
            "causal_alignment": aggregate.causal_alignment,
            "evidence_strength": aggregate.evidence_strength,
        })
        return causal_history

    def _identity_impact(self, context):
        integration = context.get(
            "identity_safe_truth_integration",
            {},
        )
        adaptive_policy = context.get(
            "adaptive_identity_integration_policy",
            {},
        )
        return {
            "integration_state": integration.get("integration_state"),
            "integration_safe": integration.get("integration_safe", False),
            "strengthens_identity":
            integration.get("strengthens_identity", False),
            "identity_stability_state":
            integration.get("identity_stability_state"),
            "identity_continuity": integration.get("identity_continuity"),
            "identity_delta": integration.get("identity_delta", 0.0),
            "semantic_drift": integration.get("semantic_drift"),
            "adaptive_identity_integration": dict(adaptive_policy),
        }

    def _review_event(self, truth_object, decision, reasons):
        event = {
            "truth_id": truth_object.truth_id,
            "concept": truth_object.concept,
            "decision": decision,
            "status": truth_object.status,
            "revision": truth_object.revision,
            "reasons": list(reasons),
            "timestamp": truth_object.reviewed_at,
        }
        self.review_history.append(event)
        self.review_history = self.review_history[-512:]
        return event

    def _upsert_truth_object(self, belief, aggregate, trials, commit, context):
        lineage = self._lineage(belief, context)
        evidence = self._evidence_snapshot(context)
        generalization = context.get("knowledge_generalization", {})
        truth_object = self.registry.commit_truth(
            concept=belief.concept,
            claim=belief.claim,
            evidence_strength=aggregate.evidence_strength,
            confidence=belief.confidence,
            contradiction_score=aggregate.contradiction_score,
            causal_alignment=aggregate.causal_alignment,
            trial_count=len(trials),
            parent_truths=lineage["parent_truths"],
            evidence_sources=lineage["evidence_sources"],
            evidence=evidence,
            causal_history=self._causal_history(
                aggregate,
                evidence,
                context,
            ),
            generalization_score=generalization.get(
                "generalization_score",
                0.0,
            ),
            identity_impact=self._identity_impact(context),
            metadata={
                "constitutional_invariants":
                dict(commit.constitutional_invariants),
                "truth_requires_reviewable_evidence": True,
                "counterevidence_can_revoke_truth": True,
                "knowledge_generalization_state":
                generalization.get("generalization_state"),
                "causal_graph_alignment":
                context.get("causal_graph_alignment", {}),
                "causal_graph_validation":
                context.get("causal_graph_validation", {}),
                "causal_explanation":
                context.get("causal_explanation", {}),
                "causal_validation":
                context.get("causal_validation", {}),
                "contextual_truth":
                context.get("contextual_truth", {}),
                "context_hierarchy":
                context.get("context_hierarchy", {}),
                "semantic_context":
                context.get("semantic_context", {}),
                "stable_truth_semantic_context":
                context.get("semantic_context", {}).get(
                    "semantic_profile",
                    {},
                ),
                "stable_truth_why_chain":
                context.get("causal_explanation", {}).get("why", []),
                "stable_truth_how_we_know":
                context.get("causal_validation", {}).get(
                    "how_we_know",
                    [],
                ),
                "stable_truth_when_valid":
                context.get("contextual_truth", {}).get("when_valid", []),
                "stable_truth_when_invalid":
                context.get("contextual_truth", {}).get(
                    "when_invalid",
                    [],
                ),
                "stable_truth_context_inheritance":
                context.get("context_hierarchy", {}).get(
                    "inheritance",
                    [],
                ),
            },
            decision=commit.decision,
            reasons=commit.reasons,
        )
        self._review_event(truth_object, commit.decision, commit.reasons)
        return truth_object

    def _revoke_truth_object(self, belief, commit):
        truth_object = self.registry.revoke_truth(
            belief.concept,
            commit.decision,
            commit.reasons,
        )
        if truth_object is not None:
            self._review_event(
                truth_object,
                commit.decision,
                commit.reasons,
            )
        return truth_object

    def evaluate(self, belief, aggregate, trials, context=None):
        context = context if isinstance(context, dict) else {}
        provisional_commit = (
            self.provisional_truth_commit_engine.evaluate(
                belief.concept,
                aggregate,
                context.get("truth_candidate", {}),
                context.get("identity_safe_truth_integration", {}),
                {
                    **context,
                    "confidence": belief.confidence,
                },
            )
        )
        commit = super().evaluate(
            belief,
            aggregate,
            trials,
            context,
        )
        final_commit_state = commit.metadata.get(
            "final_commit_decision",
            {},
        ).get(
            "final_commit_state",
        )
        if (
            commit.committed
            and final_commit_state != "LOCKED_TRUTH_PRESERVED"
        ):
            truth_object = self._upsert_truth_object(
                belief,
                aggregate,
                trials,
                commit,
                context,
            )
        elif final_commit_state == "LOCKED_TRUTH_PRESERVED":
            truth_object = self.registry.retrieve_record(belief.concept)
        elif commit.decision == "TRUTH_REVOKED":
            truth_object = self._revoke_truth_object(belief, commit)
        else:
            truth_object = self.registry.retrieve_record(belief.concept)

        commit.metadata["truth_object"] = (
            truth_object.as_dict()
            if truth_object is not None
            else None
        )
        commit.metadata["reusable_truth_available"] = bool(
            truth_object is not None
            and truth_object.status == "ACTIVE"
            and truth_object.reusable
        )
        commit.metadata["provisional_truth_commitment"] = (
            provisional_commit
        )
        return commit

    def retrieve_truth(self, concept):
        return self.retrieval_engine.retrieve_truth(concept)

    def find_related_truths(self, concept):
        return self.retrieval_engine.find_related_truths(concept)

    def rank_truths_by_confidence(self):
        return self.retrieval_engine.rank_truths_by_confidence()

    def retrieve_truth_lineage(self, concept):
        return self.retrieval_engine.retrieve_truth_lineage(concept)

    def reinforce_truth(self, concept, **kwargs):
        return self.reinforcement_engine.reinforce_truth(
            concept,
            **kwargs,
        )

    def reusable_truths(self):
        return self.registry.active_truths()

    def report(self):
        registry_report = self.registry.report()
        return {
            "system": "truth_commitment_engine",
            "phase": "7.1",
            "active_truth_objects": self.reusable_truths(),
            "truth_objects": self.registry.all_truths(),
            "review_history": list(self.review_history),
            "active_truth_count": len(self.reusable_truths()),
            "truth_object_count": registry_report["truth_count"],
            "truth_registry": registry_report,
            "truth_retrieval_engine": self.retrieval_engine.report(),
            "truth_reinforcement_engine":
            self.reinforcement_engine.report(),
            "provisional_truth_commit_engine":
            self.provisional_truth_commit_engine.report(),
            "reusable_across_future_tasks": True,
            "counterevidence_review_enabled": True,
        }


TruthObject = TruthRecord


__all__ = [
    "TruthCommitmentEngine",
    "TruthObject",
]
