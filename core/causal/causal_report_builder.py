class CausalReportBuilder:
    """Builds runtime-friendly causal cognition reports."""

    def build(
        self,
        concept,
        alignment_report=None,
        root_cause_report=None,
        counterfactual_report=None,
        dependency_report=None,
        contextual_truth_report=None,
        identity_report=None,
        spine_report=None,
    ):
        alignment_report = alignment_report or {}
        root_cause_report = root_cause_report or {}
        counterfactual_report = counterfactual_report or {}
        dependency_report = dependency_report or {}
        contextual_truth_report = contextual_truth_report or {}
        identity_report = identity_report or {}
        best_chain = root_cause_report.get(
            "best_causal_chain",
            alignment_report.get("explanation_path", []),
        )
        return {
            "system": "causal_report_builder",
            "concept": concept,
            "root_cause": (
                root_cause_report.get("root_causes", [None])[0]
                if root_cause_report.get("root_causes")
                else None
            ),
            "causal_chain": best_chain,
            "dependency_coherence":
            alignment_report.get("dependency_coherence", 0.0),
            "causal_graph_alignment":
            alignment_report.get("causal_graph_alignment", 0.0),
            "causal_validation_score":
            alignment_report.get("causal_validation_score", 0.0),
            "counterfactual_status":
            counterfactual_report.get("counterfactual_status"),
            "status": alignment_report.get("status", "PROVISIONAL"),
            "recommended_action":
            alignment_report.get("recommended_action"),
            "spine": spine_report or {},
            "reports": {
                "CAUSAL VALIDATION REPORT": alignment_report,
                "ROOT CAUSE REPORT": root_cause_report,
                "DEPENDENCY REPORT": dependency_report,
                "CONTEXTUAL TRUTH REPORT": contextual_truth_report,
                "COUNTERFACTUAL REPORT": counterfactual_report,
                "IDENTITY CONTINUITY REPORT": identity_report,
                "CAUSAL SPINE REPORT": spine_report or {},
            },
        }


__all__ = [
    "CausalReportBuilder",
]
