import numpy as np

from runtime.cognitive_pipeline import (
    CognitiveContext,
    CognitivePipelineOrchestrator,
)


class ARCSolver:

    def __init__(self, input_grid, rules):

        self.input_grid = input_grid
        self.rules = rules

    # =========================================
    # APPLY RULES
    # =========================================

    def solve(self):

        context = CognitiveContext(
            input_grid=self.input_grid,
            rules=list(self.rules),
        )
        context = CognitivePipelineOrchestrator().execute(context)
        self.cognitive_context = context
        self.cognitive_pipeline_report = {
            "COGNITIVE_PIPELINE_REPORT": True,
            "stage_timeline": list(context.stage_events),
            "stage_snapshots": list(context.stage_snapshots),
            "execution_trace": list(context.trace),
        }
        if context.final_output is None:
            return np.copy(self.input_grid.grid)
        return context.final_output
