# ============================================
# NEXRYN CONTEXT PRUNING ENGINE
# ============================================

from datetime import datetime
import uuid

from runtime.context.context_layer_manager import (
    context_layer_manager
)


# ============================================
# CONTEXT PRUNING ENGINE
# ============================================

class ContextPruningEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # PRUNING HISTORY
        # ====================================

        self.pruning_history = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "pruning_mode":
            "adaptive_context_pruning",

            "noise_reduction":
            True,

            "importance_filtering":
            True,

            "stale_context_cleanup":
            True,

            "runtime_stability":
            "stable",

            "pruning_cycles":
            0
        }

        # ====================================
        # RESERVED KEYS
        # ====================================

        self.reserved_keys = [

            "runtime_state",

            "execution_state",

            "governance_state",

            "identity_state"
        ]

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
    # COMPUTE IMPORTANCE
    # ========================================

    def compute_importance(

        self,

        key,

        value
    ):

        score = 0.5

        # ====================================
        # RESERVED PRIORITY
        # ====================================

        if key in self.reserved_keys:

            score += 0.4

        # ====================================
        # DICTIONARY PRIORITY
        # ====================================

        if isinstance(
            value,
            dict
        ):

            score += 0.2

        # ====================================
        # LARGE VALUES
        # ====================================

        if isinstance(
            value,
            (list, str)
        ):

            if len(value) > 50:

                score -= 0.2

        # ====================================
        # REPORT PRIORITY
        # ====================================

        if "report" in key:

            score += 0.2

        return round(
            max(
                0.0,
                min(score, 1.0)
            ),
            4
        )

    # ========================================
    # SHOULD PRUNE
    # ========================================

    def should_prune(

        self,

        key,

        value
    ):

        # ====================================
        # RESERVED KEYS
        # ====================================

        if key in self.reserved_keys:

            return False

        importance_score = (

            self.compute_importance(

                key,

                value
            )
        )

        # ====================================
        # LOW IMPORTANCE
        # ====================================

        if importance_score < 0.35:

            return True

        # ====================================
        # EMPTY VALUES
        # ====================================

        if value in [

            None,
            "",
            [],
            {}
        ]:

            return True

        return False

    # ========================================
    # PRUNE LAYER
    # ========================================

    def prune_layer(

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

        retained_entries = {}

        pruned_entries = []

        # ====================================
        # FILTER ENTRIES
        # ====================================

        for key, value in (

            layer_data.items()
        ):

            should_prune = (

                self.should_prune(

                    key,

                    value
                )
            )

            if should_prune:

                pruned_entries.append(
                    key
                )

                continue

            retained_entries[key] = value

        # ====================================
        # RESET LAYER
        # ====================================

        context_layer_manager.clear_layer(
            layer_name
        )

        for key, value in (

            retained_entries.items()
        ):

            context_layer_manager.set_context(

                layer_name,

                key,

                value
            )



        # ====================================
        # BUILD REPORT
        # ====================================

        pruning_report = {

            "pruning_id":
            str(uuid.uuid4()),

            "layer_name":
            layer_name,

            "original_entries":
            len(layer_data),

            "retained_entries":
            len(retained_entries),

            "pruned_entries":
            len(pruned_entries),

            "removed_keys":
            pruned_entries,

            "pruning_state":
            "completed",

            "timestamp":
            str(datetime.utcnow())
        }

        self.pruning_history.append(
            pruning_report
        )

        self.engine_state[
            "pruning_cycles"
        ] += 1

        return pruning_report
    

        # ========================================
    # RUN PRUNING CYCLE
    # ========================================

    def run_pruning_cycle(

        self,

        runtime_context
    ):

        if runtime_context is None:

            runtime_context = {}

        # ====================================
        # APPLY PRUNING
        # ====================================

        if hasattr(

            self,

            "prune_context"
        ):

            pruned = (

                self.prune_context(
                    runtime_context
                )
            )

        elif hasattr(

            self,

            "prune"
        ):

            pruned = (

                self.prune(
                    runtime_context
                )
            )

        else:

            pruned = runtime_context

        # ====================================
        # BUILD REPORT
        # ====================================

        original_count = len(
            runtime_context
        )

        pruned_count = len(
            pruned
        )

        removed_entries = max(

            original_count
            - pruned_count,

            0
        )

        report = {

            "pruning_applied":
            True,

            "original_entries":
            original_count,

            "remaining_entries":
            pruned_count,

            "removed_entries":
            removed_entries,

            "pruning_ratio":
            round(

                removed_entries

                /

                max(
                    original_count,
                    1
                ),

                4
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # STORE HISTORY
        # ====================================

        if hasattr(

            self,

            "pruning_history"
        ):

            self.pruning_history.append(
                report
            )

        return report

    # ========================================
    # PRUNE ALL LAYERS
    # ========================================

    def prune_all_layers(self):

        pruning_results = []

        layer_summary = (

            context_layer_manager.build_layer_summary()
        )

        for layer_name in (

            layer_summary.keys()
        ):

            pruning_result = (

                self.prune_layer(
                    layer_name
                )
            )

            pruning_results.append(
                pruning_result
            )

        return pruning_results

    # ========================================
    # BUILD PRUNING SUMMARY
    # ========================================

    def build_pruning_summary(self):

        total_pruned = 0

        for report in (

            self.pruning_history
        ):

            total_pruned += report.get(
                "pruned_entries",
                0
            )

        return {

            "pruning_cycles":

            len(
                self.pruning_history
            ),

            "total_pruned_entries":
            total_pruned,

            "runtime_state":
            self.engine_state.get(
                "runtime_stability",
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

            "pruning_summary":

            self.build_pruning_summary(),

            "pruning_history":

            len(
                self.pruning_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL CONTEXT PRUNING ENGINE
# ============================================

context_pruning_engine = (
    ContextPruningEngine()
)