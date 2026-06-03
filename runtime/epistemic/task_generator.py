class TaskGenerator:
    def _grid(self, seed):
        color = 1 + seed % 3
        return [
            [0, 0, color, 0, 0],
            [0, color, color, color, 0],
            [color, color, color, color, color],
            [0, color, color, color, 0],
            [0, 0, color, 0, 0],
        ]

    def _output_grid(self, input_grid):
        return [
            [
                4 if value else 0
                for value in row
            ]
            for row in input_grid
        ]

    def generate_tasks(
        self,
        concept,
        count=1,
        strategy="discover_supported_region",
        sequence_start=1,
        missing_regions=None,
        boundary_probe=None,
    ):
        tasks = []
        for offset in range(max(int(count), 0)):
            sequence = sequence_start + offset
            task_id = (
                f"synthetic_arc_probe:{concept}:{strategy}:{sequence}"
            )
            input_grid = self._grid(sequence)
            output_grid = self._output_grid(input_grid)
            tasks.append({
                "system": "task_generator",
                "phase": "6.95",
                "task_id": task_id,
                "concept": concept,
                "strategy": strategy,
                "train": [{
                    "input": input_grid,
                    "output": output_grid,
                }],
                "test": [{
                    "input": input_grid,
                }],
                "target_missing_regions": list(missing_regions or []),
                "boundary_probe": dict(boundary_probe or {}),
                "sandbox_case_template": {
                    "case_id": task_id,
                    "concept": concept,
                    "strategy": strategy,
                    "isolated_world": True,
                    "reversible": True,
                    "synthetic_sandbox_probe": True,
                    "generated_task_id": task_id,
                    "execution_result_required": True,
                    "boundary_probe": dict(boundary_probe or {}),
                },
                "synthetic_sandbox_probe": True,
                "independent_task_replication": False,
                "persistent_task_write_forbidden": True,
                "automatic_truth_promotion_forbidden": True,
            })
        return tasks


__all__ = [
    "TaskGenerator",
]
