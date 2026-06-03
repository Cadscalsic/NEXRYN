from core.epistemic_models import clamp
from core.identity.core_truth_registry import CoreTruthRegistry


class CausalAlignmentEngine:
    """Checks a new truth against the active semantic spine truths."""

    def __init__(self, minimum_alignment=0.80, core_truth_registry=None):
        self.minimum_alignment = clamp(minimum_alignment)
        self.core_truth_registry = (
            core_truth_registry or CoreTruthRegistry()
        )

    def _active_spine_truths(self, registry, concept):
        if registry is None:
            return []
        return [
            truth
            for truth in registry.active_truths()
            if truth.get("concept") != concept
        ]

    def _explicit_alignment(self, concept, spine_concept, context):
        alignments = context.get(
            "causal_spine_alignments",
            context.get("causal_alignment_with_spine_truths", {}),
        )
        if not isinstance(alignments, dict):
            return None
        concept_alignments = alignments.get(concept, alignments)
        if not isinstance(concept_alignments, dict):
            return None
        value = concept_alignments.get(spine_concept)
        if isinstance(value, dict):
            value = value.get(
                "alignment_score",
                value.get("causal_alignment"),
            )
        return clamp(value) if value is not None else None

    def evaluate(self, concept, candidate_alignment, registry, context=None):
        context = context if isinstance(context, dict) else {}
        candidate_alignment = clamp(candidate_alignment)
        spine_truths = self._active_spine_truths(registry, concept)
        locked_core_truths = self.core_truth_registry.locked_truths(
            registry,
        )
        locked_core_concepts = {
            truth["concept"]
            for truth in locked_core_truths
            if truth["concept"] != concept
        }
        comparisons = []
        for truth in spine_truths:
            spine_concept = truth["concept"]
            explicit_alignment = self._explicit_alignment(
                concept,
                spine_concept,
                context,
            )
            alignment_score = (
                explicit_alignment
                if explicit_alignment is not None
                else candidate_alignment
            )
            passed = alignment_score >= self.minimum_alignment
            required_for_core_compatibility = (
                spine_concept in locked_core_concepts
            )
            pairwise_attestation_observed = explicit_alignment is not None
            comparisons.append({
                "concept": concept,
                "spine_truth": spine_concept,
                "spine_truth_id": truth.get("truth_id"),
                "alignment_score": alignment_score,
                "spine_truth_local_causal_alignment":
                clamp(truth.get("causal_alignment", 0.0)),
                "minimum_alignment": self.minimum_alignment,
                "passed": passed,
                "required_for_core_compatibility":
                required_for_core_compatibility,
                "pairwise_attestation_observed":
                pairwise_attestation_observed,
                "pairwise_attestation_pending":
                not pairwise_attestation_observed,
                "core_compatibility_passed": (
                    passed
                    if pairwise_attestation_observed
                    else True
                ),
                "core_compatibility_state": (
                    "NOT_REQUIRED"
                    if not required_for_core_compatibility
                    else "COMPATIBLE"
                    if pairwise_attestation_observed and passed
                    else "INCOMPATIBILITY_EVIDENCE_OBSERVED"
                    if pairwise_attestation_observed
                    else "PAIRWISE_ATTESTATION_PENDING"
                ),
                "alignment_source": (
                    "explicit_spine_relation"
                    if pairwise_attestation_observed
                    else "candidate_local_alignment_proxy"
                ),
            })

        alignment_score = min(
            (
                item["alignment_score"]
                for item in comparisons
            ),
            default=candidate_alignment,
        )
        alignment_ready = all(
            item["passed"]
            for item in comparisons
        )
        compatible_with_core_truths = (
            self.core_truth_registry.compatible_with_core_truths(
                comparisons,
            )
        )
        return {
            "system": "causal_alignment_engine",
            "concept": concept,
            "candidate_causal_alignment": candidate_alignment,
            "semantic_spine_truth_count": len(spine_truths),
            "semantic_spine_truths": [
                truth["concept"]
                for truth in spine_truths
            ],
            "comparisons": comparisons,
            "locked_core_truths": sorted(locked_core_concepts),
            "compatible_with_core_truths":
            compatible_with_core_truths,
            "alignment_score": alignment_score,
            "minimum_alignment": self.minimum_alignment,
            "alignment_ready": alignment_ready,
            "blocked_by_spine_truths": [
                item["spine_truth"]
                for item in comparisons
                if not item["passed"]
            ],
            "blocked_by_core_truths": [
                item["spine_truth"]
                for item in comparisons
                if (
                    item["required_for_core_compatibility"]
                    and not item["core_compatibility_passed"]
                )
            ],
            "pairwise_attestation_pending": [
                item["spine_truth"]
                for item in comparisons
                if item["pairwise_attestation_pending"]
            ],
            "alignment_state": (
                "CAUSAL_SPINE_BOOTSTRAP"
                if not comparisons
                else "CAUSAL_SPINE_ALIGNED"
                if alignment_ready
                else "CAUSAL_SPINE_ALIGNMENT_REQUIRED"
            ),
            "local_causal_evidence_is_not_spine_alignment": True,
            "core_truth_compatibility_required": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "CausalAlignmentEngine",
]
