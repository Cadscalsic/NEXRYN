# ============================================
# NEXRYN SELF IMPROVEMENT STAGE
# ============================================

from datetime import datetime

from runtime.learning.confidence_updater import (
    ConfidenceUpdater
)

from runtime.memory.reinforcement_memory import (
    ReinforcementMemory
)

from runtime.memory import (
    cognitive_failure_memory
)

from runtime.learning.strategy_scoring import (
    StrategyScoringEngine
)
from runtime.learning.strategy_lifecycle_manager import (
    StrategyLifecycleManager
)

from runtime.persistence.persistent_memory import (
    PersistentMemory
)

from runtime.episodic.temporal_memory import (
    TemporalEpisodicMemory
)

from runtime.evolution.strategy_evolution_engine import (
    StrategyEvolutionEngine
)

from runtime.evolution.evolution_validator import (
    EvolutionValidator
)

from runtime.evolution.evolution_memory_manager import (
    EvolutionMemoryManager
)


# ============================================
# GLOBAL ENGINES
# ============================================

confidence_updater = (
    ConfidenceUpdater()
)

reinforcement_memory = (
    ReinforcementMemory()
)

strategy_scoring_engine = (
    StrategyScoringEngine()
)

persistent_memory = (
    PersistentMemory()
)

temporal_memory = (
    TemporalEpisodicMemory()
)

strategy_evolution_engine = (
    StrategyEvolutionEngine()
)

evolution_validator = (
    EvolutionValidator()
)

evolution_memory_manager = (
    EvolutionMemoryManager()
)

strategy_lifecycle_manager = (
    StrategyLifecycleManager()
)


# ============================================
# BUILD EVOLUTION METRICS
# ============================================

def build_evolution_metrics(

    updated_hypotheses,

    evolved_hypotheses,

    validated_hypotheses,

    rejected_hypotheses
):

    return {

        "updated_hypotheses":
        len(updated_hypotheses),

        "evolved_hypotheses":
        len(evolved_hypotheses),

        "validated_hypotheses":
        len(validated_hypotheses),

        "rejected_hypotheses":
        len(rejected_hypotheses)
    }


# ============================================
# SELF IMPROVEMENT STAGE
# ============================================

def self_improvement_stage(context):

    print(
        "\n=================================================="
    )

    print(
        "NEXRYN :: SELF IMPROVEMENT STAGE"
    )

    print(
        "==================================================\n"
    )

    # ========================================
    # STAGE REPORT
    # ========================================

    stage_report = {

        "stage":
        "self_improvement",

        "status":
        "running",

        "runtime_health":
        "stable",

        "timestamp":
        str(
            datetime.utcnow()
        )
    }

    # ========================================
    # LOAD CONTEXT
    # ========================================

    hypotheses = context.get(
        "hypotheses",
        []
    )

    evaluation_result = context.get(
        "evaluation_result",
        {}
    )

    cognitive_cycle = context.get(
        "cognitive_cycle",
        {}
    )

    semantic_abstractions = context.get(
        "semantic_abstractions",
        []
    )

    success = evaluation_result.get(
        "success",
        False
    )

    # ========================================
    # UPDATE CONFIDENCE
    # ========================================

    updated_hypotheses = (

        confidence_updater.update_hypotheses(

            hypotheses,

            success
        )
    )

    # ========================================
    # EVOLUTION CONTAINERS
    # ========================================

    evolved_hypotheses = []

    validated_hypotheses = []

    rejected_hypotheses = []

    persistent_buffer = []

    cycle_validation_events = []

    # ========================================
    # EVOLUTION BUDGET
    # ========================================

    max_evolution_cycles = 32

    # ========================================
    # PROCESS HYPOTHESES
    # ========================================

    for index, hypothesis in enumerate(

        updated_hypotheses
    ):

        # ====================================
        # EVOLUTION LIMIT
        # ====================================

        if index >= max_evolution_cycles:

            print(
                "EVOLUTION BUDGET LIMIT REACHED"
            )

            break

        # ====================================
        # STORE EXPERIENCE
        # ====================================

        reinforcement_memory.store_experience(

            hypothesis,

            evaluation_result
        )

        persistent_buffer.append({

            "hypothesis":
            hypothesis,

            "evaluation_result":
            evaluation_result,

            "cognitive_cycle":
            cognitive_cycle
        })

        # ====================================
        # STRATEGY SCORING
        # ====================================

        strategy_scoring_engine.update_strategy(

            strategy_name=
            hypothesis.get(
                "type",
                "unknown"
            ),

            success=success,

            accuracy=
            evaluation_result.get(
                "accuracy",
                0.0
            )
        )

        # ====================================
        # REGISTER ORIGINAL STRATEGY
        # ====================================

        evolution_memory_manager.register_strategy(

            hypothesis
        )

        # ====================================
        # EVOLVE STRATEGY
        # ====================================

        evolved_hypothesis = (

            strategy_evolution_engine.evolve_strategy(

                hypothesis
            )
        )

        evolved_hypotheses.append(

            evolved_hypothesis
        )

        # ====================================
        # REGISTER EVOLVED STRATEGY
        # ====================================

        evolution_memory_manager.register_strategy(

            evolved_hypothesis
        )

        evolution_memory_manager.update_strategy(

            strategy_name=
            evolved_hypothesis.get(
                "type",
                "unknown"
            ),

            success=success,

            confidence=
            evolved_hypothesis.get(
                "confidence",
                0.0
            ),

            accuracy=
            evaluation_result.get(
                "accuracy",
                0.0
            )
        )

        # ====================================
        # LINEAGE TRACKING
        # ====================================

        evolution_memory_manager.add_lineage(

            parent_strategy=
            hypothesis.get(
                "type",
                "unknown"
            ),

            child_strategy=
            evolved_hypothesis.get(
                "type",
                "unknown"
            )
        )

        # ====================================
        # VALIDATION
        # ====================================

        validation = (

            evolution_validator.validate_strategy(

                hypothesis,

                evolved_hypothesis,

                evaluation_result
            )
        )

        evolution_validator.store_validation_event(

            validation
        )

        cycle_validation_events.append(

            validation
        )

        # ====================================
        # PROMOTION GOVERNANCE
        # ====================================

        promotion_score = validation.get(

            "promotion_score",

            0.0
        )

        if (

            validation.get(

                "promotion_candidate",

                False
            )

            and

            promotion_score >= 0.75
        ):

            promoted = (

                evolution_validator.promote_strategy(

                    evolved_hypothesis
                )
            )

            if promoted.get(
                "newly_promoted",
                False
            ):

                evolution_memory_manager.mark_strategy_promoted(

                    evolved_hypothesis.get(
                        "type",
                        "unknown"
                    )
                )

                validated_hypotheses.append({

                    "hypothesis":
                    evolved_hypothesis,

                    "promotion":
                    promoted
                })

            else:

                validation[
                    "duplicate_promotion_suppressed"
                ] = True

        # ====================================
        # REJECTION
        # ====================================

        elif validation.get(
            "validation_status"
        ) == "rejected":

            rejected = (

                evolution_validator.reject_strategy(

                    evolved_hypothesis,

                    validation.get(
                        "rejection_reason",
                        "unknown"
                    )
                )
            )

            rejected_hypotheses.append({

                "hypothesis":
                evolved_hypothesis,

                "rejection":
                rejected
            })

        # ====================================
        # STORE EVOLUTION EVENT
        # ====================================

        strategy_evolution_engine.store_evolution_event({

            "original_strategy":
            hypothesis.get(
                "type",
                "unknown"
            ),

            "evolved_strategy":
            evolved_hypothesis.get(
                "type",
                "unknown"
            ),

            "success":
            success,

            "accuracy":
            evaluation_result.get(
                "accuracy",
                0.0
            )
        })

    # ========================================
    # PERSISTENT STORAGE BATCH
    # ========================================

    for memory_item in persistent_buffer:

        persistent_memory.store_experience(
            memory_item
        )

    # ========================================
    # POPULATION MANAGEMENT
    # ========================================

    strategy_lifecycle = (

        strategy_lifecycle_manager
        .protection_report(

            cycle_validation_events
        )
    )

    protected_strategies = (

        strategy_lifecycle.get(

            "protected_strategies",

            []
        )
    )

    pruned_strategies = (

        evolution_memory_manager.prune_strategies(

            protected_strategies=
            protected_strategies
        )
    )

    entropy_pruned_strategies = (

        evolution_memory_manager
        .prune_high_entropy_strategies(
            abstraction_count=
            len(semantic_abstractions),

            semantic_abstractions=
            semantic_abstractions,

            protected_strategies=
            protected_strategies
        )
    )

    merged_strategies = (

        evolution_memory_manager.merge_similar_strategies()
    )

    post_merge_entropy_pruned = (

        evolution_memory_manager
        .prune_high_entropy_strategies(
            abstraction_count=
            len(semantic_abstractions),

            semantic_abstractions=
            semantic_abstractions,

            protected_strategies=
            protected_strategies
        )
    )

    entropy_pruned_strategies.extend(
        post_merge_entropy_pruned
    )

    failure_memory_events = []

    failure_memory_events.extend(
        cognitive_failure_memory
        .record_merge_rejections(
            evolution_memory_manager
            .rejected_merges[-10:]
        )
    )

    failure_memory_events.extend(
        cognitive_failure_memory
        .record_semantic_contradictions(
            semantic_abstractions
        )
    )

    # ========================================
    # EVOLUTION PRESSURE
    # ========================================

    evolution_pressure = round(

        min(

            len(evolved_hypotheses) / 20,

            1.0
        ),

        4
    )

    # ========================================
    # TEMPORAL MEMORY STORAGE
    # ========================================

    temporal_memory.store_episode(

        cognitive_cycle=
        cognitive_cycle,

        evaluation_result={

            "evolution_success":
            success,

            "evolution_pressure":
            evolution_pressure
        }
    )

    # ========================================
    # REPORTS
    # ========================================

    evolution_report = (

        strategy_evolution_engine.build_evolution_report()
    )

    evolution_summary = (

        strategy_evolution_engine.build_evolution_summary()
    )

    best_evolved_strategy = (

        strategy_evolution_engine.get_best_strategy()
    )

    validation_report = (

        evolution_validator.build_validation_report()
    )

    promotion_summary = (

        evolution_validator.build_promotion_summary()
    )

    memory_report = (

        evolution_memory_manager.build_memory_report()
    )

    archive_summary = (

        evolution_memory_manager.build_archive_summary()
    )

    evolution_metrics = (

        build_evolution_metrics(

            updated_hypotheses,

            evolved_hypotheses,

            validated_hypotheses,

            rejected_hypotheses
        )
    )

    # ========================================
    # DISPLAY RESULTS
    # ========================================

    print(
        "\nEVOLVED HYPOTHESES:\n"
    )

    for evolved in evolved_hypotheses:

        print(evolved)

    print(
        "\nVALIDATION REPORT:\n"
    )

    print(validation_report)

    print(
        "\nPROMOTION SUMMARY:\n"
    )

    print(promotion_summary)

    print(
        "\nMEMORY REPORT:\n"
    )

    print(memory_report)

    print(
        "\nPRUNED STRATEGIES:\n"
    )

    print(pruned_strategies)

    print(
        "\nENTROPY PRUNED STRATEGIES:\n"
    )

    cognitive_failure_memory_report = (
        cognitive_failure_memory
        .build_report()
    )

    print(entropy_pruned_strategies)

    print(
        "\nMERGED STRATEGIES:\n"
    )

    print(merged_strategies)

    print(
        "\nEVOLUTION METRICS:\n"
    )

    print(evolution_metrics)

    print(
        "\nCOGNITIVE FAILURE MEMORY:\n"
    )

    print(cognitive_failure_memory_report)

    # ========================================
    # UPDATE STAGE REPORT
    # ========================================

    stage_report.update({

        "status":
        "completed",

        "updated_hypotheses":
        len(updated_hypotheses),

        "evolved_hypotheses":
        len(evolved_hypotheses),

        "validated_hypotheses":
        len(validated_hypotheses),

        "rejected_hypotheses":
        len(rejected_hypotheses),

        "success":
        success,

        "evolution_pressure":
        evolution_pressure
    })

    # ========================================
    # SAVE CONTEXT
    # ========================================

    context[
        "updated_hypotheses"
    ] = updated_hypotheses

    context[
        "evolved_hypotheses"
    ] = evolved_hypotheses

    context[
        "validated_hypotheses"
    ] = validated_hypotheses

    context[
        "rejected_hypotheses"
    ] = rejected_hypotheses

    context[
        "evolution_report"
    ] = evolution_report

    context[
        "evolution_summary"
    ] = evolution_summary

    context[
        "best_evolved_strategy"
    ] = best_evolved_strategy

    context[
        "validation_report"
    ] = validation_report

    context[
        "promotion_summary"
    ] = promotion_summary

    context[
        "memory_report"
    ] = memory_report

    context[
        "archive_summary"
    ] = archive_summary

    context[
        "pruned_strategies"
    ] = pruned_strategies

    context[
        "strategy_lifecycle"
    ] = strategy_lifecycle

    context[
        "entropy_pruned_strategies"
    ] = entropy_pruned_strategies

    context[
        "merged_strategies"
    ] = merged_strategies

    context[
        "rejected_merges"
    ] = (
        evolution_memory_manager
        .rejected_merges[-100:]
    )

    context[
        "evolution_metrics"
    ] = evolution_metrics

    context[
        "cognitive_failure_memory_events"
    ] = failure_memory_events

    context[
        "cognitive_failure_memory_report"
    ] = cognitive_failure_memory_report

    context[
        "evolution_pressure"
    ] = evolution_pressure

    context[
        "self_improvement_stage_report"
    ] = stage_report

    context[
        "self_improvement_complete"
    ] = True

    # ========================================
    # RETURN CONTEXT
    # ========================================

    return context
