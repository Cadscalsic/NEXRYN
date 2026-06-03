from core.learning.boundary_probe_generator import BoundaryProbeGenerator
from core.learning.experiment_scheduler import ExperimentScheduler


class LearningCurriculumManager:
    def __init__(self, scheduler=None, boundary_probe_generator=None):
        self.scheduler = scheduler or ExperimentScheduler()
        self.boundary_probe_generator = (
            boundary_probe_generator or BoundaryProbeGenerator()
        )

    def plan(self, requests, boundary_refinements=None):
        schedule = self.scheduler.schedule(requests)
        refinements = {
            item["concept"]: item
            for item in boundary_refinements or []
        }
        probes = []
        for request in schedule["scheduled_requests"]:
            refinement = refinements.get(request.get("concept"), {})
            boundary_probes = refinement.get("matched_boundary_probes", [])
            if boundary_probes:
                probes.extend(
                    self.boundary_probe_generator.generate(
                        request["concept"],
                        boundary_probes,
                        request.get("experiment_proposal", {}).get(
                            "missing_regions",
                            [],
                        ),
                    )
                )
        return {
            "system": "learning_curriculum_manager",
            "learning_phase": "7-prelude",
            "experiment_schedule": schedule,
            "boundary_probe_tasks": probes,
            "boundary_probe_task_count": len(probes),
            "synthetic_probes_are_not_independent_experiences": True,
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "LearningCurriculumManager",
]
