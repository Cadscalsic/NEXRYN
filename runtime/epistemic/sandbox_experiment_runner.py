class SandboxExperimentRunner:
    def __init__(self, executor, result_evaluator):
        self.executor = executor
        self.result_evaluator = result_evaluator
        self.executed_case_ids = set()

    def register(self, requests):
        self.executor.register(requests)

    def _worlds(self, worlds):
        if isinstance(worlds, dict):
            return dict(worlds)
        return {
            item["experiment_id"]: item
            for item in worlds or []
            if item.get("experiment_id")
        }

    def _catalog(self, cases):
        if isinstance(cases, dict):
            cases = [
                {
                    "case_id": case_id,
                    **case,
                }
                for case_id, case in cases.items()
            ]
        return list(cases or [])

    def _matches(self, request, case):
        proposal = request.get("experiment_proposal", {})
        return (
            case.get("concept") == request.get("concept")
            and (
                not case.get("strategy")
                or case["strategy"] == proposal.get("strategy")
            )
        )

    def _bind_catalog_worlds(self, worlds, cases):
        bindings = []
        for experiment_id, request in self.executor.pending_requests.items():
            if experiment_id in worlds:
                continue
            for index, case in enumerate(cases):
                case_id = str(
                    case.get(
                        "case_id",
                        f"{case.get('concept', 'unknown')}:{index}",
                    )
                )
                if (
                    case_id in self.executed_case_ids
                    or not self._matches(request, case)
                ):
                    continue
                worlds[experiment_id] = {
                    **case,
                    "automated_case_id": case_id,
                }
                bindings.append({
                    "experiment_id": experiment_id,
                    "concept": request.get("concept"),
                    "strategy":
                    request.get("experiment_proposal", {}).get("strategy"),
                    "case_id": case_id,
                })
                break
        return bindings

    def run(self, requests=None, worlds=None, cases=None):
        self.register(requests)
        worlds = self._worlds(worlds or {})
        bindings = self._bind_catalog_worlds(
            worlds,
            self._catalog(cases),
        )
        execution = self.executor.run(worlds)
        self.executed_case_ids.update(
            item["automated_case_id"]
            for item in execution["completed_experiments"]
            if item.get("automated_case_id")
        )
        evaluation = self.result_evaluator.evaluate(
            execution["completed_experiments"]
        )
        return {
            "system": "sandbox_experiment_runner",
            "phase": "6.95",
            "runner_state": (
                "SANDBOX_EXPERIMENTS_COMPLETED"
                if execution["completed_experiments"]
                else "AWAITING_DECLARED_SANDBOX_CASES"
                if self.executor.pending_requests
                else "NO_PENDING_SANDBOX_EXPERIMENTS"
            ),
            "automatic_case_bindings": bindings,
            "sandbox_execution": execution,
            "result_evaluation": evaluation,
            "completed_experiment_count":
            len(execution["completed_experiments"]),
            "pending_experiment_ids":
            sorted(self.executor.pending_requests),
            "declared_sandbox_cases_only": True,
            "fabricated_experiment_results_forbidden": True,
            "persistent_external_execution_forbidden": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "SandboxExperimentRunner",
]
