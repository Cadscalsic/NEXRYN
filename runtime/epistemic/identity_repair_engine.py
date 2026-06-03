class IdentityRepairEngine:
    def _results(self, context):
        results = context.get(
            "truth_internalization_rehearsal_results",
            [],
        )
        if isinstance(results, dict):
            results = [results]
        return results

    def _result_for(self, concept, context):
        for result in reversed(self._results(context)):
            if result.get("concept") == concept:
                return result
        return None

    def _validated_result(self, concept, context):
        result = self._result_for(concept, context)
        if not result:
            return None
        if not (
            result.get("rehearsal_cycle_id") is not None
            and
            result.get("sandbox_validated") is True
            and result.get("isolated_world") is True
            and result.get("reversible") is True
        ):
            return None
        return {
            "concept": concept,
            "rehearsal_cycle_id":
            str(result["rehearsal_cycle_id"]),
            "identity_continuity":
            result.get("identity_continuity"),
            "semantic_drift":
            result.get("semantic_drift"),
            "identity_repair_inactive":
            result.get("identity_repair_inactive", False) is True,
            "semantic_containment_inactive":
            result.get("semantic_containment_inactive", False) is True,
            "semantic_spine_state":
            result.get(
                "semantic_spine_state",
                "semantic_spine_repairing",
            ),
            "sandbox_validated": True,
            "isolated_world": True,
            "reversible": True,
        }

    def evaluate(self, belief, internalization, context=None):
        context = context if isinstance(context, dict) else {}
        rehearsal = internalization.get(
            "reversible_internalization_rehearsal",
        )
        accepted_result = self._validated_result(
            belief.concept,
            context,
        )
        internalization_required = internalization.get(
            "knowledge_internalization_required",
            False,
        )

        return {
            "system": "identity_repair_engine",
            "concept": belief.concept,
            "repair_state": (
                "REHEARSAL_RESULT_ACCEPTED"
                if accepted_result
                else "REVERSIBLE_REHEARSAL_REQUESTED"
                if internalization_required
                else "REPAIR_NOT_REQUIRED"
            ),
            "repair_actions":
            list(internalization.get("required_actions", [])),
            "reversible_internalization_rehearsal_request":
            rehearsal if internalization_required and not accepted_result else None,
            "accepted_rehearsal_result": accepted_result,
            "rejected_unvalidated_result":
            self._result_for(belief.concept, context) is not None
            and accepted_result is None,
            "semantic_anchor_reconstruction_requested":
            "reanchor_semantic_spine"
            in internalization.get("required_actions", []),
            "persistent_identity_write_forbidden": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "IdentityRepairEngine",
]
