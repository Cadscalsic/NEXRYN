class SandboxExperimentExecutor:
    def __init__(self):
        self.pending_requests = {}
        self.executed_experiments = set()

    def register(self, requests):
        for request in requests or []:
            if not request:
                continue
            experiment_id = request["experiment_id"]
            if experiment_id not in self.executed_experiments:
                self.pending_requests.setdefault(experiment_id, request)

    def _worlds(self, worlds):
        if isinstance(worlds, dict):
            return worlds
        return {
            item["experiment_id"]: item
            for item in worlds or []
            if item.get("experiment_id")
        }

    def run(self, worlds=None):
        worlds = self._worlds(worlds or {})
        completed = []
        blocked = []

        for experiment_id, request in list(self.pending_requests.items()):
            world = worlds.get(experiment_id)
            if not world:
                continue

            reason = None
            contract = request.get("execution_contract", {})
            if request.get("execution_permission") != "sandbox_only":
                reason = "sandbox_only_execution_required"
            elif contract.get("isolated_world_required") is not True:
                reason = "isolated_world_contract_required"
            elif world.get("isolated_world") is not True:
                reason = "isolated_world_validation_required"
            elif world.get("reversible") is not True:
                reason = "reversible_intervention_required"
            elif "baseline_execution_result" not in world:
                reason = "baseline_execution_result_required"
            elif "intervention_execution_result" not in world:
                reason = "intervention_execution_result_required"

            if reason:
                blocked.append({
                    "experiment_id": experiment_id,
                    "concept": request.get("concept"),
                    "execution_state": "SANDBOX_EXECUTION_BLOCKED",
                    "reason": reason,
                })
                continue

            completed.append({
                "experiment_id": experiment_id,
                "concept": request["concept"],
                "strategy": request["experiment_proposal"]["strategy"],
                "baseline_execution_result":
                world["baseline_execution_result"],
                "intervention_execution_result":
                world["intervention_execution_result"],
                "baseline_contradiction_score":
                world.get("baseline_contradiction_score", 0.0),
                "intervention_contradiction_score":
                world.get("intervention_contradiction_score", 0.0),
                "semantic_consistency":
                world.get("semantic_consistency", 0.80),
                "measurement_reliability":
                world.get("measurement_reliability", 0.90),
                "automated_case_id": world.get("automated_case_id"),
                "synthetic_sandbox_probe":
                world.get("synthetic_sandbox_probe", False),
                "generated_task_id": world.get("generated_task_id"),
                "sandbox_validated": True,
                "isolated_world": True,
                "reversible": True,
                "execution_state": "SANDBOX_EXECUTION_COMPLETED",
            })
            self.executed_experiments.add(experiment_id)
            self.pending_requests.pop(experiment_id, None)

        return {
            "system": "sandbox_experiment_executor",
            "phase": "5.5",
            "execution_mode": "isolated_epistemic_sandbox_only",
            "completed_experiments": completed,
            "blocked_experiments": blocked,
            "pending_experiment_ids": sorted(self.pending_requests),
            "arbitrary_code_execution_forbidden": True,
            "persistent_commit_forbidden": True,
        }


__all__ = [
    "SandboxExperimentExecutor",
]
