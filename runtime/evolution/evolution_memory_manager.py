# ============================================
# NEXRYN EVOLUTION MEMORY MANAGER
# ============================================


# ============================================
# EVOLUTION MEMORY MANAGER
# ============================================

from runtime.semantics.semantic_identity import (
    build_semantic_identity,
    identity_overlap
)
from runtime.evolution.safe_merge_validator import SafeMergeValidator

MAX_MERGE_DEPTH = 1

MIN_SEMANTIC_SIMILARITY = 0.85

MIN_IDENTITY_OVERLAP = 0.50

MAX_IDENTITY_CONFLICT = 0.20

MAX_ENTROPY_SCORE = 0.55

PROMOTED_STRATEGY_FAILURE_GRACE = 3

HIGH_ACCURACY_STRATEGY_FAILURE_GRACE = 5

HIGH_ACCURACY_PROTECTION_THRESHOLD = 0.95

SEMANTIC_PREFIXES = {

    "contextual",
    "dynamic",
    "adaptive",
    "structural",
    "recursive",
    "hybrid",
    "evolved"
}


class EvolutionMemoryManager:

    def __init__(self):

        self.strategy_population = {}

        self.archived_strategies = []

        self.lineage_graph = {}

        self.rejected_merges = []

        self.entropy_events = []

        self.safe_merge_validator = SafeMergeValidator()

    # ============================================
    # MERGE DEPTH
    # ============================================

    def merge_depth(
        self,
        strategy_name
    ):

        return str(
            strategy_name
        ).count(
            "_merged"
        )

    # ============================================
    # SEMANTIC DEPTH
    # ============================================

    def semantic_depth(
        self,
        strategy_name
    ):

        parts = str(
            strategy_name
        ).split(
            "_"
        )

        return sum(

            1

            for part in parts

            if part in SEMANTIC_PREFIXES
        )

    # ============================================
    # NORMALIZED TOKENS
    # ============================================

    def normalized_tokens(
        self,
        strategy_name
    ):

        tokens = []

        for token in str(
            strategy_name
        ).split(
            "_"
        ):

            if token in SEMANTIC_PREFIXES:

                continue

            if token == "merged":

                continue

            tokens.append(
                token
            )

        return set(tokens)

    # ============================================
    # SEMANTIC SIMILARITY
    # ============================================

    def semantic_similarity(
        self,
        first,
        second
    ):

        first_tokens = self.normalized_tokens(
            first
        )

        second_tokens = self.normalized_tokens(
            second
        )

        union = first_tokens.union(
            second_tokens
        )

        if not union:

            return 0.0

        overlap = first_tokens.intersection(
            second_tokens
        )

        return round(
            len(overlap)
            /
            len(union),
            4
        )

    # ============================================
    # ENTROPY SCORE
    # ============================================

    def entropy_score(
        self,
        strategy_name,
        abstraction_count=0,
        semantic_overlap=0.0,
        lineage_branching=0.0,
        mutation_frequency=0.0,
        abstraction_ambiguity=0.0
    ):

        merge_depth = self.merge_depth(
            strategy_name
        )

        semantic_depth = self.semantic_depth(
            strategy_name
        )

        if abstraction_count:

            abstraction_ambiguity = max(
                abstraction_ambiguity,
                min(
                    abstraction_count / 12,
                    1.0
                )
            )

        mutation_frequency = max(
            mutation_frequency,
            min(
                semantic_depth / 3,
                1.0
            )
        )

        if merge_depth > 0:

            mutation_frequency = max(
                mutation_frequency,
                0.75
            )

            lineage_branching = max(
                lineage_branching,
                0.75
            )

        score = (
            min(
                merge_depth,
                1.0
            )
            * 0.30
            +
            min(
                semantic_overlap,
                1.0
            )
            * 0.25
            +
            min(
                lineage_branching,
                1.0
            )
            * 0.20
            +
            min(
                mutation_frequency,
                1.0
            )
            * 0.15
            +
            min(
                abstraction_ambiguity,
                1.0
            )
            * 0.10
        )

        return round(
            score,
            4
        )

    # ============================================
    # SEMANTIC OVERLAP
    # ============================================

    def semantic_overlap_score(
        self,
        semantic_abstractions
    ):

        if not isinstance(
            semantic_abstractions,
            list
        ):

            return 0.0

        concepts = [

            abstraction.get(
                "semantic_concept",
                "generic_transformation"
            )

            for abstraction in semantic_abstractions

            if isinstance(
                abstraction,
                dict
            )
        ]

        if not concepts:

            return 0.0

        counts = {}

        for concept in concepts:

            counts[concept] = (
                counts.get(
                    concept,
                    0
                )
                + 1
            )

        largest_cluster = max(
            counts.values()
        )

        return round(
            largest_cluster
            /
            len(concepts),
            4
        )

    # ============================================
    # ABSTRACTION AMBIGUITY
    # ============================================

    def abstraction_ambiguity_score(
        self,
        semantic_abstractions
    ):

        if not isinstance(
            semantic_abstractions,
            list
        ):

            return 0.0

        if not semantic_abstractions:

            return 0.0

        generic_count = len([

            abstraction

            for abstraction in semantic_abstractions

            if isinstance(
                abstraction,
                dict
            )

            and

            abstraction.get(
                "semantic_concept"
            ) == "generic_transformation"
        ])

        return round(
            generic_count
            /
            len(semantic_abstractions),
            4
        )

    # ============================================
    # LINEAGE BRANCHING
    # ============================================

    def lineage_branching_score(
        self,
        strategy_name
    ):

        child_count = 0

        parent_count = len(
            self.lineage_graph.get(
                strategy_name,
                []
            )
        )

        population_lineage = (
            self.strategy_population
            .get(
                strategy_name,
                {}
            )
            .get(
                "lineage",
                []
            )
        )

        if isinstance(
            population_lineage,
            list
        ):

            parent_count = max(
                parent_count,
                len(population_lineage)
            )

        for parents in self.lineage_graph.values():

            if strategy_name in parents:

                child_count += 1

        return round(
            min(
                (
                    parent_count
                    +
                    child_count
                )
                /
                4,
                1.0
            ),
            4
        )

    # ============================================
    # CAN MERGE
    # ============================================

    def can_merge(
        self,
        first,
        second
    ):

        safe_merge = self.safe_merge_validator.evaluate(
            first,
            second,
            self.strategy_population.get(first, {}),
            self.strategy_population.get(second, {}),
        )

        if not safe_merge["merge_allowed"]:

            return False, safe_merge["reason"]

        if self.merge_depth(first) > MAX_MERGE_DEPTH:

            return False, "first_merge_depth_limit"

        if self.merge_depth(second) > MAX_MERGE_DEPTH:

            return False, "second_merge_depth_limit"

        similarity = self.semantic_similarity(
            first,
            second
        )

        if similarity < MIN_SEMANTIC_SIMILARITY:

            return False, "semantic_similarity_below_threshold"

        first_identity = build_semantic_identity(
            first
        )

        second_identity = build_semantic_identity(
            second
        )

        identity_report = identity_overlap(
            first_identity,
            second_identity
        )

        if (

            identity_report.get(
                "active_layers",
                0
            ) > 0

            and

            identity_report.get(
                "overlap",
                0.0
            ) < MIN_IDENTITY_OVERLAP
        ):

            return False, "identity_overlap_below_threshold"

        if identity_report.get(
            "conflict",
            0.0
        ) > MAX_IDENTITY_CONFLICT:

            return False, "identity_conflict_above_limit"

        return True, "merge_allowed"

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

        if strategy_name not in (

            self.strategy_population
        ):

            self.strategy_population[
                strategy_name
            ] = {

                "hypothesis":
                hypothesis,

                "usage_count":
                0,

                "success_count":
                0,

                "failure_count":
                0,

                "consecutive_failure_count":
                0,

                "best_accuracy":
                0.0,

                "promoted":
                False,

                "average_confidence":
                hypothesis.get(
                    "confidence",
                    0.0
                ),

                "lineage":
                [],

                "active":
                True,

                "causal_support_ready":
                hypothesis.get(
                    "causal_support_ready",
                    False
                ) is True
            }

    # ============================================
    # UPDATE STRATEGY
    # ============================================

    def update_strategy(

        self,

        strategy_name,

        success,

        confidence,

        accuracy=None
    ):

        if strategy_name not in (

            self.strategy_population
        ):

            return

        strategy = (

            self.strategy_population[
                strategy_name
            ]
        )

        strategy[
            "usage_count"
        ] += 1

        if success:

            strategy[
                "success_count"
            ] += 1

            strategy[
                "consecutive_failure_count"
            ] = 0

        else:

            strategy[
                "failure_count"
            ] += 1

            strategy[
                "consecutive_failure_count"
            ] = strategy.get(
                "consecutive_failure_count",
                0
            ) + 1

        current_confidence = strategy.get(
            "average_confidence",
            0.0
        )

        strategy[
            "average_confidence"
        ] = round(

            (
                current_confidence
                +
                confidence
            ) / 2,

            4
        )

        if accuracy is not None:

            strategy[
                "best_accuracy"
            ] = max(

                strategy.get(
                    "best_accuracy",
                    0.0
                ),

                float(
                    accuracy
                )
            )

    # ============================================
    # MARK PROMOTED STRATEGY
    # ============================================

    def mark_strategy_promoted(self, strategy_name):

        strategy = self.strategy_population.get(
            strategy_name
        )

        if strategy is None:

            return False

        strategy[
            "promoted"
        ] = True

        strategy[
            "consecutive_failure_count"
        ] = 0

        return True

    # ============================================
    # PROMOTION FAILURE GRACE
    # ============================================

    def _promotion_failure_grace_active(self, data):

        return (

            data.get(
                "promoted",
                False
            )

            and

            data.get(
                "consecutive_failure_count",
                0
            ) < PROMOTED_STRATEGY_FAILURE_GRACE
        )

    # ============================================
    # HIGH ACCURACY FAILURE GRACE
    # ============================================

    def _high_accuracy_failure_grace_active(self, data):

        return (

            data.get(
                "best_accuracy",
                0.0
            ) >= HIGH_ACCURACY_PROTECTION_THRESHOLD

            and

            data.get(
                "consecutive_failure_count",
                0
            ) < HIGH_ACCURACY_STRATEGY_FAILURE_GRACE
        )

    # ============================================
    # ADD EVOLUTION LINEAGE
    # ============================================

    def add_lineage(

        self,

        parent_strategy,

        child_strategy
    ):

        if child_strategy not in (

            self.lineage_graph
        ):

            self.lineage_graph[
                child_strategy
            ] = []

        self.lineage_graph[
            child_strategy
        ].append(

            parent_strategy
        )

    # ============================================
    # PRUNE WEAK STRATEGIES
    # ============================================

    def prune_strategies(

        self,

        minimum_score=0.4,

        minimum_usage=1,

        protected_strategies=None
    ):

        pruned = []

        protected_strategies = set(
            protected_strategies or []
        )

        for strategy_name, data in list(

            self.strategy_population.items()
        ):

            if strategy_name in protected_strategies:

                continue

            if self._promotion_failure_grace_active(data):

                continue

            if self._high_accuracy_failure_grace_active(data):

                continue

            usage = data.get(
                "usage_count",
                0
            )

            success = data.get(
                "success_count",
                0
            )

            failure = data.get(
                "failure_count",
                0
            )

            confidence = data.get(
                "average_confidence",
                0.0
            )

            total = success + failure

            success_rate = (

                success / max(
                    total,
                    1
                )
            )

            score = (

                success_rate * 0.7
                +
                confidence * 0.3
            )

            if (

                usage >= minimum_usage

                and

                score < minimum_score
            ):

                data[
                    "active"
                ] = False

                self.archived_strategies.append({

                    "strategy":
                    strategy_name,

                    "score":
                    round(
                        score,
                        4
                    ),

                    "reason":
                    "low_evolution_score"
                })

                pruned.append(
                    strategy_name
                )

        return pruned

    # ============================================
    # MERGE SIMILAR STRATEGIES
    # ============================================

    def merge_similar_strategies(self):

        merged = []

        strategy_names = list(

            [

                strategy_name

                for strategy_name, data in (
                    self.strategy_population.items()
                )

                if data.get(
                    "active",
                    True
                )
            ]
        )

        for i in range(

            len(strategy_names)
        ):

            for j in range(

                i + 1,

                len(strategy_names)
            ):

                first = strategy_names[i]

                second = strategy_names[j]

                allowed, reason = self.can_merge(
                    first,
                    second
                )

                if not allowed:

                    self.rejected_merges.append({

                        "sources":
                        [first, second],

                        "reason":
                        reason,

                        "semantic_similarity":
                        self.semantic_similarity(
                            first,
                            second
                        ),

                        "first_identity":
                        build_semantic_identity(
                            first
                        ).as_dict(),

                        "second_identity":
                        build_semantic_identity(
                            second
                        ).as_dict(),

                        "identity_overlap":
                        identity_overlap(
                            build_semantic_identity(
                                first
                            ),
                            build_semantic_identity(
                                second
                            )
                        )
                    })

                    continue

                if (

                    first in second

                    or

                    second in first
                ):

                    merged_name = (

                        first
                        +
                        "_merged"
                    )

                    if self.merge_depth(
                        merged_name
                    ) > MAX_MERGE_DEPTH:

                        self.rejected_merges.append({

                            "sources":
                            [first, second],

                            "candidate":
                            merged_name,

                            "reason":
                            "merged_name_depth_limit"
                        })

                        continue

                    if merged_name in self.strategy_population:

                        continue

                    self.strategy_population[
                        merged_name
                    ] = {

                        "hypothesis":
                        self.strategy_population[
                            first
                        ][
                            "hypothesis"
                        ],

                        "usage_count":

                        self.strategy_population[
                            first
                        ][
                            "usage_count"
                        ]

                        +

                        self.strategy_population[
                            second
                        ][
                            "usage_count"
                        ],

                        "success_count":

                        self.strategy_population[
                            first
                        ][
                            "success_count"
                        ]

                        +

                        self.strategy_population[
                            second
                        ][
                            "success_count"
                        ],

                        "failure_count":

                        self.strategy_population[
                            first
                        ][
                            "failure_count"
                        ]

                        +

                        self.strategy_population[
                            second
                        ][
                            "failure_count"
                        ],

                        "average_confidence":

                        round(

                            (
                                self.strategy_population[
                                    first
                                ][
                                    "average_confidence"
                                ]

                                +

                                self.strategy_population[
                                    second
                                ][
                                    "average_confidence"
                                ]

                            ) / 2,

                            4
                        ),

                        "lineage":
                        [first, second],

                        "causal_support_ready":
                        self.strategy_population[
                            first
                        ].get(
                            "causal_support_ready",
                            False
                        )
                        and
                        self.strategy_population[
                            second
                        ].get(
                            "causal_support_ready",
                            False
                        ),

                        "active":
                        True
                    }

                    merged.append({

                        "merged":
                        merged_name,

                        "sources":
                        [first, second]
                    })

        return merged

    # ============================================
    # PRUNE HIGH ENTROPY STRATEGIES
    # ============================================

    def prune_high_entropy_strategies(
        self,
        abstraction_count=0,
        semantic_abstractions=None,
        protected_strategies=None
    ):

        pruned = []

        protected_strategies = set(
            protected_strategies or []
        )

        semantic_overlap = self.semantic_overlap_score(
            semantic_abstractions
        )

        abstraction_ambiguity = self.abstraction_ambiguity_score(
            semantic_abstractions
        )

        for strategy_name, data in list(
            self.strategy_population.items()
        ):

            if strategy_name in protected_strategies:

                continue

            if self._promotion_failure_grace_active(data):

                continue

            if self._high_accuracy_failure_grace_active(data):

                continue

            lineage_branching = self.lineage_branching_score(
                strategy_name
            )

            hypothesis = data.get(
                "hypothesis",
                {}
            )

            mutation_frequency = 1.0 if (

                isinstance(
                    hypothesis,
                    dict
                )

                and

                hypothesis.get(
                    "mutation_applied",
                    False
                )
            ) else 0.0

            entropy = self.entropy_score(
                strategy_name,
                abstraction_count,
                semantic_overlap=semantic_overlap,
                lineage_branching=lineage_branching,
                mutation_frequency=mutation_frequency,
                abstraction_ambiguity=abstraction_ambiguity
            )

            data[
                "entropy_score"
            ] = entropy

            data[
                "entropy_components"
            ] = {

                "merge_depth":
                self.merge_depth(
                    strategy_name
                ),

                "semantic_overlap":
                semantic_overlap,

                "lineage_branching":
                lineage_branching,

                "mutation_frequency":
                mutation_frequency,

                "abstraction_ambiguity":
                abstraction_ambiguity
            }

            if entropy > MAX_ENTROPY_SCORE:

                data[
                    "active"
                ] = False

                event = {

                    "strategy":
                    strategy_name,

                    "entropy_score":
                    entropy,

                    "reason":
                    "high_cognitive_entropy"
                }

                self.archived_strategies.append(
                    event
                )

                self.entropy_events.append(
                    event
                )

                pruned.append(
                    strategy_name
                )

                del self.strategy_population[
                    strategy_name
                ]

        return pruned

    # ============================================
    # DETECT DOMINANT STRATEGIES
    # ============================================

    def detect_dominant_strategies(

        self,

        threshold=0.8
    ):

        dominant = []

        for strategy_name, data in (

            self.strategy_population.items()
        ):

            success = data.get(
                "success_count",
                0
            )

            failure = data.get(
                "failure_count",
                0
            )

            total = success + failure

            success_rate = (

                success / max(
                    total,
                    1
                )
            )

            if success_rate >= threshold:

                dominant.append({

                    "strategy":
                    strategy_name,

                    "success_rate":
                    round(
                        success_rate,
                        4
                    )
                })

        return dominant

    # ============================================
    # BUILD MEMORY REPORT
    # ============================================

    def build_memory_report(self):

        active_count = 0

        inactive_count = 0

        for data in (

            self.strategy_population.values()
        ):

            if data.get(
                "active",
                False
            ):

                active_count += 1

            else:

                inactive_count += 1

        report = {

            "strategy_population":
            len(
                self.strategy_population
            ),

            "active_strategies":
            active_count,

            "inactive_strategies":
            inactive_count,

            "promoted_strategies":
            sum(
                data.get("promoted", False)
                for data in self.strategy_population.values()
            ),

            "promoted_strategies_in_failure_grace": [
                strategy_name
                for strategy_name, data
                in self.strategy_population.items()
                if self._promotion_failure_grace_active(data)
            ],

            "promoted_strategy_failure_grace":
            PROMOTED_STRATEGY_FAILURE_GRACE,

            "high_accuracy_strategy_failure_grace":
            HIGH_ACCURACY_STRATEGY_FAILURE_GRACE,

            "high_accuracy_protection_threshold":
            HIGH_ACCURACY_PROTECTION_THRESHOLD,

            "high_accuracy_strategies_in_failure_grace": [
                strategy_name
                for strategy_name, data
                in self.strategy_population.items()
                if self._high_accuracy_failure_grace_active(data)
            ],

            "archived_count":
            len(
                self.archived_strategies
            ),

            "lineage_count":
            len(
                self.lineage_graph
            ),

            "dominant_strategies":

            self.detect_dominant_strategies(),

            "rejected_merges":
            len(self.rejected_merges),

            "entropy_events":
            len(self.entropy_events)
        }

        return report

    # ============================================
    # BUILD ARCHIVE SUMMARY
    # ============================================

    def build_archive_summary(self):

        return {

            "archived_strategies":
            self.archived_strategies,

            "archive_size":
            len(
                self.archived_strategies
            )
        }
