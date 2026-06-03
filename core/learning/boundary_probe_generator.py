from core.learning.synthetic_task_generator import SyntheticTaskGenerator


class BoundaryProbeGenerator:
    def __init__(self, synthetic_task_generator=None):
        self.synthetic_task_generator = (
            synthetic_task_generator or SyntheticTaskGenerator()
        )
        self._sequence = 0

    def generate(self, concept, probes, missing_regions=None):
        tasks = []
        for probe in probes or []:
            self._sequence += 1
            tasks.extend(
                self.synthetic_task_generator.generate_tasks(
                    concept,
                    count=1,
                    strategy="matched_boundary_replication",
                    sequence_start=self._sequence,
                    missing_regions=missing_regions,
                    boundary_probe=probe,
                )
            )
        return tasks


__all__ = [
    "BoundaryProbeGenerator",
]
