# ============================================
# NEXRYN CONTEXT COMPRESSION ENGINE
# ============================================

from datetime import datetime
import uuid

from runtime.context.context_layer_manager import (
    context_layer_manager
)


# ============================================
# CONTEXT COMPRESSION ENGINE
# ============================================

class ContextCompressionEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # COMPRESSION HISTORY
        # ====================================

        self.compression_history = []

        # ====================================
        # COMPRESSED CONTEXT STORAGE
        # ====================================

        self.compressed_contexts = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "compression_mode":
            "adaptive_context_compression",

            "semantic_compression":
            True,

            "duplicate_removal":
            True,

            "context_pruning":
            True,

            "execution_trace_compression":
            True,

            "compression_stability":
            "stable",

            "compression_cycles":
            0
        }

        # ====================================
        # LIMITS
        # ====================================

        self.max_string_length = 250

        self.max_list_size = 10

        self.max_dict_entries = 15

        self.max_trace_length = 20

    # ========================================
    # NORMALIZE LAYER DATA
    # ========================================

    def normalize_layer_data(

        self,

        layer_data
    ):

        if layer_data is None:

            layer_data = {}

        if not isinstance(
            layer_data,
            dict
        ):

            layer_data = {}

        return layer_data

    # ========================================
    # COMPUTE IMPORTANCE SCORE
    # ========================================

    def compute_importance_score(

        self,

        key,

        value
    ):

        score = 0.5

        critical_keywords = [

            "winner",

            "hypothesis",

            "evaluation",

            "inference",

            "execution",

            "strategy",

            "semantic",

            "prediction",

            "transformation",

            "reasoning"
        ]

        for keyword in critical_keywords:

            if keyword in key:

                score += 0.1

        if isinstance(value, dict):

            score += 0.1

        if isinstance(value, list):

            score += 0.05

        return min(
            round(score, 4),
            1.0
        )

    # ========================================
    # COMPRESS VALUE
    # ========================================

    def compress_value(

        self,

        value
    ):

        # ====================================
        # STRING COMPRESSION
        # ====================================

        if isinstance(
            value,
            str
        ):

            if len(value) > (

                self.max_string_length
            ):

                return value[
                    :self.max_string_length
                ]

            return value

        # ====================================
        # LIST COMPRESSION
        # ====================================

        if isinstance(
            value,
            list
        ):

            return value[
                :self.max_list_size
            ]

        # ====================================
        # DICTIONARY COMPRESSION
        # ====================================

        if isinstance(
            value,
            dict
        ):

            compressed = {}

            for index, (
                key,
                item
            ) in enumerate(
                value.items()
            ):

                if index >= (

                    self.max_dict_entries
                ):

                    break

                compressed[key] = item

            return compressed

        return value

    # ========================================
    # REMOVE DUPLICATES
    # ========================================

    def remove_duplicates(

        self,

        layer_data
    ):

        layer_data = (

            self.normalize_layer_data(
                layer_data
            )
        )

        unique_entries = {}

        observed_values = set()

        for key, value in (

            layer_data.items()
        ):

            # ====================================
            # SAFE VALUE SIGNATURE
            # ====================================

            try:

                # ================================
                # NUMPY ARRAYS
                # ================================

                if hasattr(

                    value,

                    "shape"
                ):

                    value_signature = (

                        f"ndarray_"

                        f"{value.shape}_"

                        f"{value.dtype}"
                    )

                # ================================
                # DICTIONARIES
                # ================================

                elif isinstance(
                    value,
                    dict
                ):

                    value_signature = (

                        f"dict_"

                        f"{len(value)}"
                    )

                # ================================
                # LISTS
                # ================================

                elif isinstance(
                    value,
                    list
                ):

                    value_signature = (

                        f"list_"

                        f"{len(value)}"
                    )

                # ================================
                # TUPLES
                # ================================

                elif isinstance(
                    value,
                    tuple
                ):

                    value_signature = (

                        f"tuple_"

                        f"{len(value)}"
                    )

                # ================================
                # PRIMITIVE TYPES
                # ================================

                elif isinstance(

                    value,

                    (
                        int,
                        float,
                        str,
                        bool
                    )
                ):

                    value_signature = str(
                        value
                    )

                # ================================
                # FALLBACK TYPE SIGNATURE
                # ================================

                else:

                    value_signature = (

                        type(value)
                        .__name__
                    )

            except Exception:

                value_signature = (
                    "unknown"
                )

            # ====================================
            # DUPLICATE CHECK
            # ====================================

            if value_signature in (
                observed_values
            ):

                continue

            observed_values.add(
                value_signature
            )

            unique_entries[key] = value

        return unique_entries

    # ========================================
    # COMPRESS EXECUTION TRACE
    # ========================================

    def compress_execution_trace(

        self,

        runtime_context
    ):

        trace = runtime_context.get(
            "execution_trace",
            []
        )

        if len(trace) > (

            self.max_trace_length
        ):

            runtime_context[
                "execution_trace"
            ] = trace[

                -self.max_trace_length:
            ]

        return runtime_context

    # ========================================
    # BUILD SEMANTIC SUMMARY
    # ========================================

    def build_semantic_summary(

        self,

        runtime_context
    ):

        return {

            "winner_hypothesis":

            runtime_context.get(
                "winner_hypothesis"
            ),

            "evaluation_result":

            runtime_context.get(
                "evaluation_result"
            ),

            "best_evolved_strategy":

            runtime_context.get(
                "best_evolved_strategy"
            ),

            "cognitive_pressure":

            runtime_context.get(
                "cognitive_pressure"
            ),

            "execution_state":

            runtime_context.get(
                "execution_state"
            ),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # COMPRESS CONTEXT
    # ========================================

    def compress_context(

        self,

        runtime_context
    ):

        if runtime_context is None:

            runtime_context = {}

        # ====================================
        # REMOVE DUPLICATES
        # ====================================

        runtime_context = (

            self.remove_duplicates(
                runtime_context
            )
        )

        # ====================================
        # TRACE COMPRESSION
        # ====================================

        runtime_context = (

            self.compress_execution_trace(
                runtime_context
            )
        )

        compressed_context = {}

        # ====================================
        # IMPORTANCE FILTERING
        # ====================================

        for key, value in (

            runtime_context.items()
        ):

            importance_score = (

                self.compute_importance_score(

                    key,

                    value
                )
            )

            if importance_score >= 0.5:

                compressed_context[
                    key
                ] = (

                    self.compress_value(
                        value
                    )
                )

        # ====================================
        # SEMANTIC SUMMARY
        # ====================================

        compressed_context[
            "semantic_summary"
        ] = (

            self.build_semantic_summary(

                compressed_context
            )
        )

        return compressed_context

    # ========================================
    # COMPRESS LAYER
    # ========================================

    def compress_layer(

        self,

        layer_name
    ):

        layer_data = (

            context_layer_manager.get_context(
                layer_name
            )
        )

        layer_data = (

            self.normalize_layer_data(
                layer_data
            )
        )

        # ====================================
        # REMOVE DUPLICATES
        # ====================================

        cleaned_layer = (

            self.remove_duplicates(
                layer_data
            )
        )

        compressed_layer = {}

        # ====================================
        # COMPRESS ENTRIES
        # ====================================

        for key, value in (

            cleaned_layer.items()
        ):

            compressed_layer[key] = (

                self.compress_value(
                    value
                )
            )

        # ====================================
        # UPDATE LAYER
        # ====================================

        context_layer_manager.clear_layer(
            layer_name
        )

        for key, value in (

            compressed_layer.items()
        ):

            context_layer_manager.set_context(

                layer_name,

                key,

                value
            )

        # ====================================
        # BUILD REPORT
        # ====================================

        compression_report = {

            "compression_id":
            str(uuid.uuid4()),

            "layer_name":
            layer_name,

            "original_entries":
            len(layer_data),

            "compressed_entries":
            len(compressed_layer),

            "compression_ratio":
            round(

                len(compressed_layer)

                /

                max(
                    len(layer_data),
                    1
                ),

                4
            ),

            "compression_state":
            "completed",

            "timestamp":
            str(datetime.utcnow())
        }

        self.compression_history.append(
            compression_report
        )

        self.engine_state[
            "compression_cycles"
        ] += 1

        return compression_report

    # ========================================
    # RUN COMPRESSION CYCLE
    # ========================================

    def run_compression_cycle(

        self,

        runtime_context
    ):

        if runtime_context is None:

            runtime_context = {}

        original_size = len(
            runtime_context
        )

        # ====================================
        # COMPRESS CONTEXT
        # ====================================

        compressed = (

            self.compress_context(
                runtime_context
            )
        )

        compressed_size = len(
            compressed
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "compression_applied":
            True,

            "original_entries":
            original_size,

            "compressed_entries":
            compressed_size,

            "compression_ratio":
            round(

                compressed_size

                /

                max(
                    original_size,
                    1
                ),

                4
            ),

            "compression_mode":
            "adaptive_cognitive_compression",

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # STORE HISTORY
        # ====================================

        self.compression_history.append(
            report
        )

        self.compressed_contexts.append(
            compressed
        )

        return report

    # ========================================
    # COMPRESS ALL LAYERS
    # ========================================

    def compress_all_layers(self):

        compression_results = []

        layer_summary = (

            context_layer_manager
            .build_layer_summary()
        )

        for layer_name in (

            layer_summary.keys()
        ):

            compression_result = (

                self.compress_layer(
                    layer_name
                )
            )

            compression_results.append(
                compression_result
            )

        return compression_results

    # ========================================
    # BUILD COMPRESSION SUMMARY
    # ========================================

    def build_compression_summary(self):

        total_compressions = len(
            self.compression_history
        )

        compressed_layers = []

        for compression in (

            self.compression_history
        ):

            compressed_layers.append(

                compression.get(
                    "layer_name"
                )
            )

        return {

            "total_compressions":
            total_compressions,

            "compressed_layers":
            list(
                set(compressed_layers)
            ),

            "compression_state":
            self.engine_state.get(
                "compression_stability",
                "stable"
            )
        }

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "engine_state":
            self.engine_state,

            "compression_summary":

            self.build_compression_summary(),

            "compression_history":

            len(
                self.compression_history
            ),

            "compressed_contexts":

            len(
                self.compressed_contexts
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL CONTEXT COMPRESSION ENGINE
# ============================================

context_compression_engine = (
    ContextCompressionEngine()
)