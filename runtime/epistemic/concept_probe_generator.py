from runtime.task_generator import TaskGenerator


class ConceptProbeGenerator:
    def __init__(self, task_generator=None):
        self.task_generator = task_generator or TaskGenerator()
        self._sequence = 0

    def probe_boundary(
        self,
        concept,
        proposal=None,
        count=1,
        boundary_probe=None,
    ):
        proposal = proposal or {}
        sequence_start = self._sequence + 1
        self._sequence += max(int(count), 0)
        return self.task_generator.generate_tasks(
            concept,
            count,
            proposal.get("strategy", "matched_boundary_replication"),
            sequence_start,
            proposal.get("missing_regions", []),
            boundary_probe,
        )

    def generate_for_request(
        self,
        request,
        count=1,
        boundary_probe=None,
    ):
        proposal = request.get("experiment_proposal", {})
        return self.probe_boundary(
            request["concept"],
            proposal,
            count,
            boundary_probe,
        )


__all__ = [
    "ConceptProbeGenerator",
]
