from runtime.concept_probe_generator import ConceptProbeGenerator


class CurriculumManager:
    def __init__(self, concept_probe_generator=None):
        self.concept_probe_generator = (
            concept_probe_generator or ConceptProbeGenerator()
        )
        self.planned_request_ids = set()

    def _cases(self, cases):
        if isinstance(cases, dict):
            return [
                {
                    "case_id": case_id,
                    **case,
                }
                for case_id, case in cases.items()
            ]
        return list(cases or [])

    def merge_cases(self, declared_cases=None, generated_cases=None):
        return [
            *self._cases(declared_cases),
            *self._cases(generated_cases),
        ]

    def _refinement_for(self, request, refinements):
        return next(
            (
                item
                for item in refinements or []
                if item.get("concept") == request.get("concept")
            ),
            {},
        )

    def plan(self, pending_requests, refinements=None):
        generated_tasks = []
        for request in pending_requests or []:
            request_id = request.get(
                "request_id",
                request.get("experiment_id"),
            )
            if not request_id or request_id in self.planned_request_ids:
                continue
            proposal = request.get("experiment_proposal", {})
            refinement = self._refinement_for(request, refinements)
            boundary_probes = (
                refinement.get("matched_boundary_probes", [])
                if proposal.get("strategy")
                == "matched_boundary_replication"
                else []
            )
            if boundary_probes:
                for probe in boundary_probes:
                    generated_tasks.extend(
                        self.concept_probe_generator.generate_for_request(
                            request,
                            boundary_probe=probe,
                        )
                    )
            else:
                generated_tasks.extend(
                    self.concept_probe_generator.generate_for_request(request)
                )
            self.planned_request_ids.add(request_id)

        return {
            "system": "curriculum_manager",
            "phase": "6.95",
            "curriculum_state": (
                "SYNTHETIC_SANDBOX_PROBES_GENERATED"
                if generated_tasks
                else "AWAITING_KNOWLEDGE_ACQUISITION_REQUESTS"
            ),
            "generated_tasks": generated_tasks,
            "sandbox_case_templates": [
                task["sandbox_case_template"]
                for task in generated_tasks
            ],
            "sandbox_cases": [],
            "boundary_targeted_task_count": sum(
                bool(task["boundary_probe"])
                for task in generated_tasks
            ),
            "generated_task_count": len(generated_tasks),
            "curriculum_execution_state": (
                "AWAITING_GENERATED_TASK_EVALUATION"
                if generated_tasks
                else "NO_GENERATED_TASKS_PENDING"
            ),
            "synthetic_probes_are_not_independent_replications": True,
            "generated_probe_results_must_be_measured": True,
            "persistent_task_write_forbidden": True,
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "CurriculumManager",
]
