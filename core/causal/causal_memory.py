from core.epistemic_models import clamp


class CausalMemory:
    """In-memory causal memory for validated Phase 5 artifacts."""

    def __init__(self):
        self.validated_paths = {}
        self.stable_dependencies = {}
        self.dependency_structures = {}
        self.root_causes = {}
        self.counterfactual_outcomes = {}
        self.contextual_truths = {}

    def remember_path(self, report):
        chain = list(report.get("causal_chain", []))
        path_id = report.get("path_id") or " -> ".join(chain)
        self.validated_paths[path_id] = {
            "path_id": path_id,
            "causal_chain": chain,
            "path_strength": clamp(report.get("path_strength", 0.0)),
            "path_confidence": clamp(report.get("path_confidence", 0.0)),
        }
        return self.validated_paths[path_id]

    def remember_dependency(self, concept, dependency_report):
        self.stable_dependencies[concept] = dict(dependency_report or {})
        return self.stable_dependencies[concept]

    def remember_dependency_structure(self, concept, hierarchy_report):
        self.dependency_structures[concept] = dict(hierarchy_report or {})
        return self.dependency_structures[concept]

    def remember_root_cause(self, concept, root_cause_report):
        self.root_causes[concept] = dict(root_cause_report or {})
        return self.root_causes[concept]

    def remember_counterfactual(self, concept, counterfactual_report):
        self.counterfactual_outcomes[concept] = dict(counterfactual_report or {})
        return self.counterfactual_outcomes[concept]

    def remember_contextual_truth(self, concept, contextual_truth_report):
        self.contextual_truths[concept] = dict(contextual_truth_report or {})
        return self.contextual_truths[concept]

    def report(self):
        return {
            "system": "causal_memory",
            "validated_paths": self.validated_paths,
            "stable_dependencies": self.stable_dependencies,
            "dependency_structures": self.dependency_structures,
            "root_causes": self.root_causes,
            "counterfactual_outcomes": self.counterfactual_outcomes,
            "contextual_truths": self.contextual_truths,
        }


__all__ = [
    "CausalMemory",
]
