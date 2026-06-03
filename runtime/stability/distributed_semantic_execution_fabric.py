# ============================================
# NEXRYN DISTRIBUTED SEMANTIC EXECUTION FABRIC
# ============================================

from datetime import datetime


def _clamp(value, minimum=0.0, maximum=1.0):

    try:

        value = float(value)

    except Exception:

        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum
            )
        ),
        4
    )


def _as_list(value):

    if isinstance(
        value,
        list
    ):

        return value

    if value is None:

        return []

    return [
        value
    ]


def _entropy(context):

    entropy_report = context.get(
        "cognitive_entropy_report",
        {}
    )

    return _clamp(
        entropy_report.get(
            "runtime_entropy",
            context.get(
                "runtime_entropy",
                0.0
            )
        )
    )


def _name(item):

    if isinstance(
        item,
        dict
    ):

        return str(
            item.get(
                "concept",
                item.get(
                    "hypothesis",
                    item.get(
                        "route",
                        item.get(
                            "semantic_path",
                            item.get(
                                "macro_id",
                                "unknown"
                            )
                        )
                    )
                )
            )
        )

    return str(
        item
    )


class SemanticThreadScheduler:

    def __init__(self):

        self.schedule_history = []

    def collect_threads(self, context):

        distributed = context.get(
            "distributed_cognitive_execution_report",
            {}
        )

        threading = distributed.get(
            "cognitive_threading",
            context.get(
                "cognitive_threading_report",
                {}
            )
        )

        threads = _as_list(
            threading.get(
                "threads",
                []
            )
        )

        if threads:

            return threads

        market = context.get(
            "recursive_budget_market_report",
            {}
        )

        return [
            {
                "thread_id":
                f"semantic_thread:{index + 1}",

                "work_id":
                allocation.get(
                    "hypothesis",
                    "semantic_work"
                ),

                "priority":
                allocation.get(
                    "market_bid",
                    0.0
                ),

                "recursion_budget":
                allocation.get(
                    "recursion_budget_granted",
                    1
                ),
            }
            for index, allocation in enumerate(
                market.get(
                    "allocations",
                    []
                )
            )
        ]

    def schedule(self, context):

        entropy = _entropy(
            context
        )

        threads = self.collect_threads(
            context
        )

        max_parallel = (
            2
            if entropy >= 0.75
            else 4
            if entropy >= 0.50
            else 6
        )

        scheduled = []
        deferred = []

        for index, thread in enumerate(
            sorted(
                threads,
                key=lambda item: item.get(
                    "priority",
                    0.0
                ),
                reverse=True
            )
        ):

            item = dict(
                thread
            )

            item[
                "semantic_isolation"
            ] = "isolated_reasoning_thread"

            item[
                "schedule_policy"
            ] = (
                "parallel_cognition"
                if index < max_parallel
                else "defer_until_cool"
            )

            if index < max_parallel:

                scheduled.append(
                    item
                )

            else:

                deferred.append(
                    item
                )

        report = {
            "system":
            "semantic_thread_scheduler",

            "parallel_cognition":
            True,

            "isolated_reasoning_threads":
            True,

            "max_parallel_threads":
            max_parallel,

            "scheduled_threads":
            scheduled,

            "deferred_threads":
            deferred,

            "scheduled_thread_count":
            len(
                scheduled
            ),

            "deferred_thread_count":
            len(
                deferred
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.schedule_history.append(
            report
        )

        self.schedule_history = (
            self.schedule_history[-32:]
        )

        return report


class CognitiveDMA:

    def __init__(self):

        self.transfer_history = []

    def transfer(self, context, schedule_report):

        transfers = []

        swapping = context.get(
            "dynamic_cognitive_swapping_report",
            {}
        )

        loaded = swapping.get(
            "loaded_concepts",
            []
        )

        for thread in schedule_report.get(
            "scheduled_threads",
            []
        ):

            for concept in loaded[:6]:

                transfers.append({
                    "concept":
                    concept.get(
                        "concept"
                    ),

                    "source_layer":
                    "semantic_memory",

                    "target_layer":
                    thread.get(
                        "thread_id"
                    ),

                    "transfer_mode":
                    "cognitive_dma",

                    "executive_overhead":
                    0.0,
                })

        report = {
            "system":
            "cognitive_dma",

            "direct_concept_transfer":
            True,

            "executive_overhead_bypass":
            True,

            "transfers":
            transfers[:64],

            "transfer_count":
            len(
                transfers
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.transfer_history.append(
            report
        )

        self.transfer_history = (
            self.transfer_history[-32:]
        )

        return report


class SemanticCacheCompiler:

    def __init__(self):

        self.cache = {}
        self.compile_history = []

    def build_macro(self, thread, transfers):

        source = thread.get(
            "work_id",
            thread.get(
                "thread_id",
                "semantic_path"
            )
        )

        macro_id = (
            "semantic_macro:"
            +
            str(
                source
            )
            .replace(
                " ",
                "_"
            )
            .replace(
                ":",
                "_"
            )[:96]
        )

        bound_concepts = [
            transfer.get(
                "concept"
            )
            for transfer in transfers
            if transfer.get(
                "target_layer"
            )
            == thread.get(
                "thread_id"
            )
        ]

        reuse_score = _clamp(
            thread.get(
                "priority",
                0.0
            )
            * 0.45
            +
            min(
                len(
                    bound_concepts
                ),
                6
            )
            / 6
            * 0.35
            +
            min(
                thread.get(
                    "recursion_budget",
                    1
                ),
                4
            )
            / 4
            * 0.20
        )

        macro = {
            "macro_id":
            macro_id,

            "semantic_path":
            source,

            "bound_concepts":
            bound_concepts,

            "executable_semantic_macro":
            [
                "dma_load_bound_concepts",
                "execute_cached_semantic_path",
                "emit_isolated_delta",
            ],

            "reuse_score":
            reuse_score,

            "cache_state":
            (
                "cached"
                if reuse_score >= 0.50
                else "compiled_ephemeral"
            ),
        }

        if macro.get(
            "cache_state"
        ) == "cached":

            self.cache[
                macro_id
            ] = macro

        return macro

    def compile(self, schedule_report, dma_report):

        transfers = dma_report.get(
            "transfers",
            []
        )

        macros = [
            self.build_macro(
                thread,
                transfers
            )
            for thread in schedule_report.get(
                "scheduled_threads",
                []
            )
        ]

        report = {
            "system":
            "semantic_cache_compiler",

            "compile_repeated_paths":
            True,

            "executable_semantic_macros":
            macros,

            "macro_count":
            len(
                macros
            ),

            "cache_size":
            len(
                self.cache
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.compile_history.append(
            report
        )

        self.compile_history = (
            self.compile_history[-32:]
        )

        return report


class EntropyFieldRegulator:

    def __init__(self):

        self.regulation_history = []

    def regulate(self, context, schedule_report, compiler_report):

        entropy = _entropy(
            context
        )

        thread_heat = _clamp(
            schedule_report.get(
                "scheduled_thread_count",
                0
            )
            /
            max(
                schedule_report.get(
                    "max_parallel_threads",
                    1
                ),
                1
            )
        )

        macro_cooling = _clamp(
            compiler_report.get(
                "cache_size",
                0
            )
            /
            max(
                compiler_report.get(
                    "macro_count",
                    1
                ),
                1
            )
            * 0.25
        )

        semantic_heat_before = _clamp(
            entropy * 0.70
            +
            thread_heat * 0.30
        )

        semantic_heat_after = _clamp(
            semantic_heat_before
            -
            macro_cooling
            -
            schedule_report.get(
                "deferred_thread_count",
                0
            )
            * 0.06
        )

        equilibrium = _clamp(
            1.0
            -
            semantic_heat_after
        )

        report = {
            "system":
            "entropy_field_regulator",

            "runtime_entropy":
            entropy,

            "semantic_heat_before":
            semantic_heat_before,

            "semantic_heat_after":
            semantic_heat_after,

            "cognitive_equilibrium":
            equilibrium,

            "semantic_overheating":
            semantic_heat_before >= 0.70,

            "regulation_actions":
            (
                [
                    "defer_hot_threads",
                    "prefer_cached_macros",
                    "cool_semantic_field",
                ]
                if semantic_heat_before >= 0.70
                else [
                    "maintain_equilibrium"
                ]
            ),

            "entropy_state_after":
            (
                "regulated"
                if semantic_heat_after < 0.70
                else "critical"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.regulation_history.append(
            report
        )

        self.regulation_history = (
            self.regulation_history[-32:]
        )

        return report


class DistributedSemanticExecutionFabric:

    def __init__(self):

        self.semantic_thread_scheduler = (
            SemanticThreadScheduler()
        )

        self.cognitive_dma = (
            CognitiveDMA()
        )

        self.semantic_cache_compiler = (
            SemanticCacheCompiler()
        )

        self.entropy_field_regulator = (
            EntropyFieldRegulator()
        )

        self.fabric_history = []

    def run_cycle(self, runtime_context):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        schedule_report = (
            self.semantic_thread_scheduler
            .schedule(runtime_context)
        )

        dma_report = (
            self.cognitive_dma
            .transfer(
                runtime_context,
                schedule_report
            )
        )

        compiler_report = (
            self.semantic_cache_compiler
            .compile(
                schedule_report,
                dma_report
            )
        )

        entropy_report = (
            self.entropy_field_regulator
            .regulate(
                runtime_context,
                schedule_report,
                compiler_report
            )
        )

        report = {
            "phase":
            "Distributed Semantic Execution Fabric",

            "semantic_thread_scheduler":
            schedule_report,

            "cognitive_dma":
            dma_report,

            "semantic_cache_compiler":
            compiler_report,

            "entropy_field_regulator":
            entropy_report,

            "fabric_state":
            (
                "semantic_heat_regulated"
                if entropy_report.get(
                    "entropy_state_after"
                )
                == "regulated"
                else "semantic_heat_critical"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        runtime_context[
            "semantic_thread_scheduler_report"
        ] = schedule_report

        runtime_context[
            "cognitive_dma_report"
        ] = dma_report

        runtime_context[
            "semantic_cache_compiler_report"
        ] = compiler_report

        runtime_context[
            "entropy_field_regulator_report"
        ] = entropy_report

        runtime_context[
            "distributed_semantic_execution_fabric_report"
        ] = report

        self.fabric_history.append(
            report
        )

        self.fabric_history = (
            self.fabric_history[-32:]
        )

        return runtime_context


distributed_semantic_execution_fabric = (
    DistributedSemanticExecutionFabric()
)
