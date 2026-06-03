class CognitiveState:

    def __init__(self):

        # ====================================
        # RAW TASK DATA
        # ====================================

        self.input_grid = None
        self.output_grid = None

        # ====================================
        # SYMBOLIC WORLD
        # ====================================

        self.entities = []
        self.relations = []
        self.scene_graph = None

        # ====================================
        # PATTERN LAYER
        # ====================================

        self.patterns = []

        # ====================================
        # RULE LAYER
        # ====================================

        self.rules = []

        # ====================================
        # INFERENCE
        # ====================================

        self.hypotheses = []

        # ====================================
        # PLANNING
        # ====================================

        self.plans = []

        # ====================================
        # SEARCH
        # ====================================

        self.search_results = []

        # ====================================
        # SYNTHESIS
        # ====================================

        self.programs = []

        # ====================================
        # MEMORY
        # ====================================

        self.memory_matches = []

        # ====================================
        # EXECUTION
        # ====================================

        self.execution_trace = []

        # ====================================
        # META COGNITION
        # ====================================

        self.confidence = {}

        self.active_engine = None

    # ========================================
    # LOAD TASK
    # ========================================

    def load_task(

        self,

        input_grid,

        output_grid=None

    ):

        self.input_grid = input_grid

        self.output_grid = output_grid

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "entities":
                len(self.entities),

            "relations":
                len(self.relations),

            "patterns":
                len(self.patterns),

            "rules":
                len(self.rules),

            "plans":
                len(self.plans),

            "programs":
                len(self.programs),

            "search_results":
                len(self.search_results),

            "memory_matches":
                len(self.memory_matches)
        }