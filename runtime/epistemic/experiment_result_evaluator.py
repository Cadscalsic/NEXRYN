from runtime.causal_effect_analyzer import CausalEffectAnalyzer


class ExperimentResultEvaluator:
    def __init__(self, causal_effect_analyzer=None):
        self.causal_effect_analyzer = (
            causal_effect_analyzer or CausalEffectAnalyzer()
        )

    def evaluate(self, completed_experiments):
        analysis = self.causal_effect_analyzer.analyze(
            completed_experiments
        )
        measurements = analysis["measurements"]
        return {
            "system": "experiment_result_evaluator",
            "phase": "6.95",
            "measurements": measurements,
            "direct_causal_effect_count":
            analysis["direct_causal_effect_count"],
            "causal_effect_analysis": analysis,
            "evaluated_result_count": len(measurements),
            "causal_effect_is_measured_not_assumed": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "ExperimentResultEvaluator",
]
