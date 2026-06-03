# ============================================
# NEXRYN STRATEGY EVOLUTION ENGINE
# ============================================


# ============================================
# STRATEGY EVOLUTION ENGINE
# ============================================

class StrategyEvolutionEngine:

    def __init__(self):

        self.strategy_memory = {}

        self.evolution_history = []

        self.lineage_graph = {}

    # ============================================
    # NORMALIZE STRATEGY NAME
    # ============================================

    def normalize_strategy_name(

        self,

        strategy_name
    ):

        while (

            "adaptive_adaptive_"

            in

            strategy_name
        ):

            strategy_name = (

                strategy_name.replace(

                    "adaptive_adaptive_",

                    "adaptive_"
                )
            )

        while (

            "evolved_evolved_"

            in

            strategy_name
        ):

            strategy_name = (

                strategy_name.replace(

                    "evolved_evolved_",

                    "evolved_"
                )
            )

        return strategy_name

    # ============================================
    # REGISTER STRATEGY
    # ============================================

    def register_strategy(

        self,

        hypothesis
    ):

        strategy_name = hypothesis.get(

            "type",

            "unknown_strategy"
        )

        strategy_name = (

            self.normalize_strategy_name(

                strategy_name
            )
        )

        if strategy_name not in self.strategy_memory:

            self.strategy_memory[
                strategy_name
            ] = {

                "success_count":
                0,

                "failure_count":
                0,

                "total_confidence":
                0.0,

                "average_confidence":
                0.0,

                "mutations":
                0,

                "evolution_score":
                0.0,

                "categories":
                set(),

                "lineage_depth":
                0
            }

        strategy_data = (

            self.strategy_memory[
                strategy_name
            ]
        )

        strategy_data[
            "categories"
        ].add(

            hypothesis.get(

                "category",

                "unknown"
            )
        )

    # ============================================
    # UPDATE STRATEGY PERFORMANCE
    # ============================================

    def update_strategy(

        self,

        hypothesis,

        evaluation_result
    ):

        strategy_name = hypothesis.get(

            "type",

            "unknown_strategy"
        )

        strategy_name = (

            self.normalize_strategy_name(

                strategy_name
            )
        )

        self.register_strategy(
            hypothesis
        )

        strategy_data = (

            self.strategy_memory[
                strategy_name
            ]
        )

        confidence = hypothesis.get(

            "confidence",

            0.0
        )

        success = evaluation_result.get(

            "success",

            False
        )

        # ====================================
        # UPDATE COUNTERS
        # ====================================

        if success:

            strategy_data[
                "success_count"
            ] += 1

        else:

            strategy_data[
                "failure_count"
            ] += 1

        strategy_data[
            "total_confidence"
        ] += confidence

        total_attempts = (

            strategy_data[
                "success_count"
            ]

            +

            strategy_data[
                "failure_count"
            ]
        )

        # ====================================
        # UPDATE AVERAGE CONFIDENCE
        # ====================================

        strategy_data[
            "average_confidence"
        ] = round(

            strategy_data[
                "total_confidence"
            ]

            /

            max(
                total_attempts,
                1
            ),

            4
        )

        # ====================================
        # SUCCESS RATE
        # ====================================

        success_rate = (

            strategy_data[
                "success_count"
            ]

            /

            max(
                total_attempts,
                1
            )
        )

        # ====================================
        # EVOLUTION SCORE
        # ====================================

        evolution_score = (

            success_rate * 0.7

            +

            strategy_data[
                "average_confidence"
            ] * 0.3
        )

        strategy_data[
            "evolution_score"
        ] = round(

            evolution_score,

            4
        )

    # ============================================
    # EVOLVE STRATEGY
    # ============================================

    def evolve_strategy(

        self,

        hypothesis
    ):

        evolved_hypothesis = dict(
            hypothesis
        )

        original_type = hypothesis.get(

            "type",

            "unknown"
        )

        # ====================================
        # EVOLUTION RULES
        # ====================================

        if "color" in original_type:

            evolved_type = (

                "adaptive_"

                +

                original_type
            )

        elif "symmetry" in original_type:

            evolved_type = (

                "contextual_"

                +

                original_type
            )

        elif "object" in original_type:

            evolved_type = (

                "structural_"

                +

                original_type
            )

        else:

            evolved_type = (

                "evolved_"

                +

                original_type
            )

        # ====================================
        # NORMALIZE TYPE
        # ====================================

        evolved_type = (

            self.normalize_strategy_name(

                evolved_type
            )
        )

        # ====================================
        # UPDATE TYPE
        # ====================================

        evolved_hypothesis[
            "type"
        ] = evolved_type

        # ====================================
        # BOOST CONFIDENCE
        # ====================================

        evolved_hypothesis[
            "confidence"
        ] = min(

            hypothesis.get(

                "confidence",

                0.0
            )

            +

            0.05,

            1.0
        )

        # ====================================
        # EVOLUTION METADATA
        # ====================================

        evolved_hypothesis[
            "parent_strategy"
        ] = original_type

        evolved_hypothesis[
            "evolution_source"
        ] = (
            "strategy_evolution_engine"
        )

        evolved_hypothesis[
            "mutation_applied"
        ] = True

        evolved_hypothesis[
            "evolved"
        ] = True

        # ====================================
        # REGISTER EVOLVED STRATEGY
        # ====================================

        self.register_strategy(

            evolved_hypothesis
        )

        strategy_data = (

            self.strategy_memory[
                evolved_type
            ]
        )

        strategy_data[
            "mutations"
        ] += 1

        # ====================================
        # LINEAGE TRACKING
        # ====================================

        if original_type not in self.lineage_graph:

            self.lineage_graph[
                original_type
            ] = []

        self.lineage_graph[
            original_type
        ].append(

            evolved_type
        )

        strategy_data[
            "lineage_depth"
        ] = len(

            self.lineage_graph[
                original_type
            ]
        )

        return evolved_hypothesis

    # ============================================
    # STORE EVOLUTION EVENT
    # ============================================

    def store_evolution_event(

        self,

        event
    ):

        self.evolution_history.append(
            event
        )

    # ============================================
    # RANK STRATEGIES
    # ============================================

    def rank_strategies(self):

        ranked = []

        for strategy_name, data in (

            self.strategy_memory.items()
        ):

            ranked.append({

                "strategy_name":
                strategy_name,

                "evolution_score":
                data.get(
                    "evolution_score",
                    0.0
                ),

                "success_count":
                data.get(
                    "success_count",
                    0
                ),

                "failure_count":
                data.get(
                    "failure_count",
                    0
                ),

                "mutations":
                data.get(
                    "mutations",
                    0
                ),

                "lineage_depth":
                data.get(
                    "lineage_depth",
                    0
                )
            })

        ranked.sort(

            key=lambda item:

            item.get(
                "evolution_score",
                0.0
            ),

            reverse=True
        )

        return ranked

    # ============================================
    # GET BEST STRATEGY
    # ============================================

    def get_best_strategy(self):

        ranked = self.rank_strategies()

        if ranked:

            return ranked[0]

        return {}

    # ============================================
    # BUILD EVOLUTION REPORT
    # ============================================

    def build_evolution_report(self):

        return {

            "strategy_count":
            len(
                self.strategy_memory
            ),

            "ranked_strategies":
            self.rank_strategies(),

            "best_strategy":
            self.get_best_strategy(),

            "lineage_graph":
            self.lineage_graph
        }

    # ============================================
    # BUILD EVOLUTION SUMMARY
    # ============================================

    def build_evolution_summary(self):

        return {

            "evolution_events":
            len(
                self.evolution_history
            ),

            "tracked_strategies":
            len(
                self.strategy_memory
            ),

            "best_strategy":
            self.get_best_strategy(),

            "lineage_count":
            len(
                self.lineage_graph
            )
        }