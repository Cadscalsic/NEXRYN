# ============================================
# NEXRYN DISTRIBUTED COGNITIVE EXECUTION
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


def _name(item):

    if isinstance(
        item,
        dict
    ):

        return str(
            item.get(
                "hypothesis",
                item.get(
                    "concept",
                    item.get(
                        "route",
                        item.get(
                            "type",
                            item.get(
                                "alternate_route",
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


class CognitiveThreading:

    def __init__(self):

        self.thread_history = []

    def collect_work_items(self, context):

        market = context.get(
            "recursive_budget_market_report",
            {}
        )

        items = []

        for allocation in market.get(
            "allocations",
            []
        ):

            items.append({
                "work_id":
                _name(
                    allocation
                ),

                "source":
                "recursive_budget_market",

                "budget":
                allocation.get(
                    "recursion_budget_granted",
                    1
                ),

                "priority":
                allocation.get(
                    "market_bid",
                    0.0
                ),
            })

        if not items:

            routing = context.get(
                "predictive_attention_routing_v2_report",
                {}
            )

            for route in routing.get(
                "rebuilt_routes",
                []
            ):

                items.append({
                    "work_id":
                    route.get(
                        "alternate_route"
                    ),

                    "source":
                    "predictive_attention_routing_v2",

                    "budget":
                    1,

                    "priority":
                    1.0
                    -
                    route.get(
                        "collapse_risk_after",
                        0.0
                    ),
                })

        if not items:

            items.append({
                "work_id":
                "default_reasoning_stream",

                "source":
                "fallback",

                "budget":
                1,

                "priority":
                0.5,
            })

        return sorted(
            items,
            key=lambda item: item.get(
                "priority",
                0.0
            ),
            reverse=True
        )[:8]

    def build_threads(self, context):

        threads = []

        for index, item in enumerate(
            self.collect_work_items(
                context
            )
        ):

            threads.append({
                "thread_id":
                f"cog_thread:{index + 1}",

                "work_id":
                item.get(
                    "work_id"
                ),

                "source":
                item.get(
                    "source"
                ),

                "branch_isolation":
                "isolated_context_delta",

                "execution_mode":
                "asynchronous_cognition",

                "recursion_budget":
                item.get(
                    "budget",
                    1
                ),

                "priority":
                _clamp(
                    item.get(
                        "priority",
                        0.0
                    )
                ),

                "status":
                "scheduled",
            })

        report = {
            "system":
            "cognitive_threading",

            "multiple_independent_reasoning_streams":
            True,

            "asynchronous_cognition":
            True,

            "branch_isolation":
            True,

            "threads":
            threads,

            "thread_count":
            len(
                threads
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.thread_history.append(
            report
        )

        self.thread_history = (
            self.thread_history[-32:]
        )

        return report


class SemanticDMA:

    def __init__(self):

        self.transfer_history = []

    def build_transfer_plan(self, context, threading_report):

        swapping = context.get(
            "dynamic_cognitive_swapping_report",
            {}
        )

        transfers = []

        for concept in swapping.get(
            "loaded_concepts",
            []
        ):

            transfers.append({
                "concept":
                concept.get(
                    "concept"
                ),

                "source_layer":
                "latent_memory",

                "target_layer":
                "thread_local_working_set",

                "transfer_mode":
                "direct_memory_access",

                "executive_overhead":
                0.0,
            })

        for thread in threading_report.get(
            "threads",
            []
        ):

            transfers.append({
                "concept":
                thread.get(
                    "work_id"
                ),

                "source_layer":
                "recursive_budget_market",

                "target_layer":
                thread.get(
                    "thread_id"
                ),

                "transfer_mode":
                "thread_dma_bind",

                "executive_overhead":
                0.0,
            })

        report = {
            "system":
            "semantic_dma",

            "direct_layer_transfer":
            True,

            "executive_overhead_bypass":
            True,

            "transfers":
            transfers[:48],

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


class PredictiveCognitiveCompilation:

    def __init__(self):

        self.macro_cache = {}
        self.compilation_history = []

    def macro_id(self, source):

        normalized = (
            str(
                source
            )
            .strip()
            .lower()
            .replace(
                " ",
                "_"
            )
            .replace(
                ":",
                "_"
            )
        )

        return "macro:" + normalized[:96]

    def compile_macro(self, thread, dma_report):

        source = thread.get(
            "work_id"
        )

        macro_id = self.macro_id(
            source
        )

        matching_transfers = [
            transfer
            for transfer in dma_report.get(
                "transfers",
                []
            )
            if transfer.get(
                "concept"
            )
            == source
            or transfer.get(
                "target_layer"
            )
            == thread.get(
                "thread_id"
            )
        ]

        stable_score = _clamp(
            thread.get(
                "priority",
                0.0
            )
            * 0.55
            +
            min(
                len(
                    matching_transfers
                ),
                4
            )
            / 4
            * 0.25
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

            "source_thread":
            thread.get(
                "thread_id"
            ),

            "semantic_path":
            source,

            "executable_semantic_macro":
            [
                "load_dma_working_set",
                "apply_compiled_semantic_path",
                "return_thread_delta",
            ],

            "stable_abstraction_score":
            stable_score,

            "cache_policy":
            (
                "cache_stable_abstraction"
                if stable_score >= 0.55
                else "compile_once"
            ),
        }

        if macro.get(
            "cache_policy"
        ) == "cache_stable_abstraction":

            self.macro_cache[
                macro_id
            ] = macro

        return macro

    def compile(self, context, threading_report, dma_report):

        compiled = [
            self.compile_macro(
                thread,
                dma_report
            )
            for thread in threading_report.get(
                "threads",
                []
            )
        ]

        cache_hits = []

        for macro in compiled:

            macro_id = macro.get(
                "macro_id"
            )

            if macro_id in self.macro_cache:

                cache_hits.append(
                    macro_id
                )

        report = {
            "system":
            "predictive_cognitive_compilation",

            "compile_reusable_cognition_paths":
            True,

            "cache_stable_abstractions":
            True,

            "create_executable_semantic_macros":
            True,

            "compiled_macros":
            compiled,

            "compiled_macro_count":
            len(
                compiled
            ),

            "macro_cache_size":
            len(
                self.macro_cache
            ),

            "cache_hits":
            cache_hits,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.compilation_history.append(
            report
        )

        self.compilation_history = (
            self.compilation_history[-32:]
        )

        return report


class DistributedCognitiveExecution:

    def __init__(self):

        self.cognitive_threading = (
            CognitiveThreading()
        )

        self.semantic_dma = (
            SemanticDMA()
        )

        self.predictive_cognitive_compilation = (
            PredictiveCognitiveCompilation()
        )

        self.execution_history = []

    def run_cycle(self, runtime_context):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        threading_report = (
            self.cognitive_threading
            .build_threads(runtime_context)
        )

        dma_report = (
            self.semantic_dma
            .build_transfer_plan(
                runtime_context,
                threading_report
            )
        )

        compilation_report = (
            self.predictive_cognitive_compilation
            .compile(
                runtime_context,
                threading_report,
                dma_report
            )
        )

        report = {
            "phase":
            "Distributed Cognitive Execution",

            "cognitive_threading":
            threading_report,

            "semantic_dma":
            dma_report,

            "predictive_cognitive_compilation":
            compilation_report,

            "distributed_execution_state":
            (
                "compiled_distributed_threads"
                if compilation_report.get(
                    "compiled_macro_count",
                    0
                )
                else "threaded_dma_ready"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        runtime_context[
            "cognitive_threading_report"
        ] = threading_report

        runtime_context[
            "semantic_dma_report"
        ] = dma_report

        runtime_context[
            "predictive_cognitive_compilation_report"
        ] = compilation_report

        runtime_context[
            "distributed_cognitive_execution_report"
        ] = report

        self.execution_history.append(
            report
        )

        self.execution_history = (
            self.execution_history[-32:]
        )

        return runtime_context


distributed_cognitive_execution = (
    DistributedCognitiveExecution()
)
