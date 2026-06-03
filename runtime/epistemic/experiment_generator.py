from runtime.epistemic.autonomous_experiment_generator import (
    AutonomousExperimentGenerator,
)


class ExperimentGenerator(AutonomousExperimentGenerator):
    def generate(
        self,
        concept,
        bottleneck,
        strategy,
        sequence,
        evidence_gap_analysis=None,
    ):
        proposal = super().generate(
            concept,
            bottleneck,
            strategy,
            sequence,
        )
        evidence_gap_analysis = evidence_gap_analysis or {}
        return {
            **proposal,
            "knowledge_acquisition_phase": "6.94",
            "target_concept": concept,
            "goal": (
                "acquire_missing_epistemic_evidence"
                if evidence_gap_analysis.get("acquisition_required")
                else f"improve_{bottleneck}"
            ),
            "priority": evidence_gap_analysis.get("priority", "medium"),
            "missing_regions": list(
                evidence_gap_analysis.get("missing_regions", [])
            ),
            "required_success_examples":
            evidence_gap_analysis.get("required_success_examples"),
            "required_counterexamples":
            evidence_gap_analysis.get("required_counterexamples"),
            "knowledge_acquisition_is_evidence_not_truth": True,
        }


__all__ = [
    "ExperimentGenerator",
]
