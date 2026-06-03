from runtime.task_generator import TaskGenerator


class SyntheticTaskGenerator:
    def __init__(self, task_generator=None):
        self.task_generator = task_generator or TaskGenerator()

    def generate_tasks(
        self,
        concept,
        count=1,
        strategy="discover_supported_region",
        sequence_start=1,
        missing_regions=None,
        boundary_probe=None,
    ):
        tasks = self.task_generator.generate_tasks(
            concept,
            count,
            strategy,
            sequence_start,
            missing_regions,
            boundary_probe,
        )
        return [
            {
                **task,
                "system": "synthetic_task_generator",
                "learning_phase": "7-prelude",
                "experience_class": "synthetic_probe",
                "independent_experience": False,
            }
            for task in tasks
        ]


__all__ = [
    "SyntheticTaskGenerator",
]
