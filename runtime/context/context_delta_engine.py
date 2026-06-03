
import gc
import json
import hashlib
import logging

from datetime import datetime

from typing import Dict
from typing import Any
from typing import Optional

import numpy as np


# ============================================
# LOGGER
# ============================================

logger = logging.getLogger(
    "NEXRYN.CONTEXT_DELTA_ENGINE"
)


# ============================================
# CONTEXT DELTA ENGINE
# ============================================

class ContextDeltaEngine:

    """
    Memory-safe cognitive context tracking engine
    for the NEXRYN Runtime Architecture.
    """

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        config: Optional[
            Dict[str, Any]
        ] = None
    ):

        self.config = config or {}

        # ====================================
        # HISTORY LIMITS
        # ====================================

        self.history_size_limit = (

            self.config.get(

                "history_size_limit",

                5
            )
        )

        self.max_fingerprint_cache = (

            self.config.get(

                "max_fingerprint_cache",

                50
            )
        )

        # ====================================
        # STATE STORAGE
        # ====================================

        self._processed_fingerprints = set()

        self._snapshot_vault = {}

        self.previous_snapshot = {}

        self.delta_history = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "delta_tracking":
            True,

            "memory_safe_mode":
            True,

            "lightweight_fingerprinting":
            True,

            "recursive_protection":
            True,

            "spatial_delta_tracking":
            True
        }

        logger.info(

            "ContextDeltaEngine initialized successfully."
        )

    # ========================================
    # BUILD LIGHTWEIGHT SERIALIZATION
    # ========================================

    def build_lightweight_representation(

        self,

        data
    ):

        # ====================================
        # DICTIONARY
        # ====================================

        if isinstance(
            data,
            dict
        ):

            lightweight_data = {

                key:

                type(value).__name__

                for key, value in data.items()
            }

            return json.dumps(

                lightweight_data,

                sort_keys=True
            )

        # ====================================
        # LIST
        # ====================================

        if isinstance(
            data,
            list
        ):

            return json.dumps({

                "type":
                "list",

                "length":
                len(data)
            })

        # ====================================
        # NUMPY ARRAY
        # ====================================

        if isinstance(
            data,
            np.ndarray
        ):

            return json.dumps({

                "type":
                "ndarray",

                "shape":
                data.shape,

                "dtype":
                str(data.dtype)
            })

        # ====================================
        # NONE
        # ====================================

        if data is None:

            return "None"

        # ====================================
        # DEFAULT
        # ====================================

        return str(
            type(data).__name__
        )

    # ========================================
    # GENERATE FINGERPRINT
    # ========================================

    def generate_fingerprint(

        self,

        data
    ):

        try:

            serialized = (

                self.build_lightweight_representation(
                    data
                )
            )

            return hashlib.md5(

                serialized.encode(
                    "utf-8"
                )

            ).hexdigest()

        except Exception as error:

            logger.warning(

                f"Fingerprint generation failed: {error}"
            )

            return str(id(data))

    # ========================================
    # NORMALIZE CONTEXT
    # ========================================

    def normalize_context(

        self,

        runtime_context
    ):

        if runtime_context is None:

            return {}

        if not isinstance(
            runtime_context,
            dict
        ):

            return {}

        normalized_context = {}

        # ====================================
        # EXCLUDED HEAVY KEYS
        # ====================================

        excluded_keys = [

            "execution_trace",

            "recursive_report",

            "symbolic_report",

            "causal_report",

            "merged_strategies",

            "governance_reports",

            "reasoning_history",

            "synthesis_history"
        ]

        for key, value in (

            runtime_context.items()
        ):

            if key in excluded_keys:

                continue

            normalized_context[key] = value

        return normalized_context

    # ========================================
    # CREATE SNAPSHOT
    # ========================================

    def create_snapshot(

        self,

        task_id=None,

        context_data=None,

        **kwargs
    ):

        # ====================================
        # LEGACY PIPELINE COMPATIBILITY
        # ====================================

        if context_data is None:

            context_data = task_id

            task_id = "runtime_snapshot"

        # ====================================
        # NORMALIZE CONTEXT
        # ====================================

        context_data = (

            self.normalize_context(
                context_data
            )
        )

        gc.collect()

        try:

            snapshot_hash = (

                self.generate_fingerprint(
                    context_data
                )
            )

            snapshot = {}

            # ================================
            # BUILD SAFE SNAPSHOT
            # ================================

            for key, value in (

                context_data.items()
            ):

                snapshot[key] = {

                    "fingerprint":

                    self.generate_fingerprint(
                        value
                    ),

                    "type":
                    type(value).__name__
                }

            # ================================
            # HISTORY LIMIT
            # ================================

            if len(
                self._snapshot_vault
            ) >= self.history_size_limit:

                oldest_key = next(

                    iter(
                        self._snapshot_vault
                    )
                )

                self._snapshot_vault.pop(

                    oldest_key,

                    None
                )

            # ================================
            # STORE SNAPSHOT
            # ================================

            self._snapshot_vault[
                task_id
            ] = {

                "snapshot_hash":
                snapshot_hash,

                "snapshot":
                snapshot,

                "timestamp":
                str(datetime.utcnow())
            }

            self.previous_snapshot = (
                snapshot
            )

            logger.debug(

                f"Snapshot created for {task_id}"
            )

            return snapshot

        except Exception as error:

            logger.error(

                f"Snapshot creation failed: {error}"
            )

            return {}

    # ========================================
    # DETECT CHANGES
    # ========================================

    def detect_changes(

        self,

        input_context,

        output_context=None,

        **kwargs
    ):

        gc.collect()

        # ====================================
        # NORMALIZATION
        # ====================================

        input_context = (

            self.normalize_context(
                input_context
            )
        )

        if output_context is None:

            output_context = input_context

            input_context = self.previous_snapshot

        output_context = (

            self.normalize_context(
                output_context
            )
        )

        # ====================================
        # DELTA REPORT
        # ====================================

        delta_report = {

            "failure_detected":
            False,

            "accuracy":
            1.0,

            "spatial_shift_detected":
            False,

            "color_changes": {

                "added_colors":
                [],

                "removed_colors":
                []
            },

            "structural_modifications":
            {},

            "delta_changes":
            {},

            "failure_causes":
            [],

            "timestamp":
            str(datetime.utcnow()),

            "engine_state":
            self.engine_state
        }

        try:

            # ================================
            # FINGERPRINT COMPARISON
            # ================================

            input_fp = (

                self.generate_fingerprint(
                    input_context
                )
            )

            output_fp = (

                self.generate_fingerprint(
                    output_context
                )
            )

            if input_fp == output_fp:

                return delta_report

            # ================================
            # SPATIAL DETECTION
            # ================================

            input_objects = input_context.get(

                "input_objects",

                []
            )

            output_objects = output_context.get(

                "output_objects",

                []
            )

            if (

                len(input_objects) == 1

                and

                len(output_objects) == 1
            ):

                input_object = (
                    input_objects[0]
                )

                output_object = (
                    output_objects[0]
                )

                input_centroid = (

                    input_object.get(
                        "centroid",
                        {}
                    )
                )

                output_centroid = (

                    output_object.get(
                        "centroid",
                        {}
                    )
                )

                if input_centroid != (
                    output_centroid
                ):

                    delta_report[
                        "spatial_shift_detected"
                    ] = True

                    delta_report[
                        "structural_modifications"
                    ][
                        "translation"
                    ] = {

                        "row_shift":

                        output_centroid.get(
                            "row",
                            0
                        )

                        -

                        input_centroid.get(
                            "row",
                            0
                        ),

                        "col_shift":

                        output_centroid.get(
                            "col",
                            0
                        )

                        -

                        input_centroid.get(
                            "col",
                            0
                        )
                    }

            # ================================
            # COLOR TRANSFORMATION
            # ================================

            input_grid_summary = (

                input_context.get(

                    "input_grid_summary",

                    {}
                )
            )

            output_grid_summary = (

                output_context.get(

                    "output_grid_summary",

                    {}
                )
            )

            input_colors = set(

                input_grid_summary.get(

                    "colors",

                    []
                )
            )

            output_colors = set(

                output_grid_summary.get(

                    "colors",

                    []
                )
            )

            delta_report[
                "color_changes"
            ][
                "added_colors"
            ] = list(

                output_colors
                -
                input_colors
            )

            delta_report[
                "color_changes"
            ][
                "removed_colors"
            ] = list(

                input_colors
                -
                output_colors
            )

            # ================================
            # ACTIVE STRATEGIES
            # ================================

            active_strategies = kwargs.get(

                "active_strategies",

                []
            )

            stable_strategies = []

            for strategy in (
                active_strategies
            ):

                strategy_fp = (

                    self.generate_fingerprint(
                        strategy
                    )
                )

                if strategy_fp in (

                    self._processed_fingerprints
                ):

                    continue

                self._processed_fingerprints.add(
                    strategy_fp
                )

                stable_strategies.append(
                    strategy
                )

            # ================================
            # CACHE LIMIT
            # ================================

            if len(

                self._processed_fingerprints

            ) > self.max_fingerprint_cache:

                self._processed_fingerprints.clear()

            # ================================
            # STRUCTURAL DIFFERENCES
            # ================================

            input_keys = set(
                input_context.keys()
            )

            output_keys = set(
                output_context.keys()
            )

            added_keys = (
                output_keys
                -
                input_keys
            )

            removed_keys = (
                input_keys
                -
                output_keys
            )

            shared_keys = (
                input_keys
                &
                output_keys
            )

            # ================================
            # ADDED
            # ================================

            for key in added_keys:

                delta_report[
                    "delta_changes"
                ][key] = {

                    "change_type":
                    "added"
                }

            # ================================
            # REMOVED
            # ================================

            for key in removed_keys:

                delta_report[
                    "delta_changes"
                ][key] = {

                    "change_type":
                    "removed"
                }

            # ================================
            # MODIFIED
            # ================================

            for key in shared_keys:

                input_value = (
                    input_context.get(key)
                )

                output_value = (
                    output_context.get(key)
                )

                input_value_fp = (

                    self.generate_fingerprint(
                        input_value
                    )
                )

                output_value_fp = (

                    self.generate_fingerprint(
                        output_value
                    )
                )

                if input_value_fp != (
                    output_value_fp
                ):

                    delta_report[
                        "delta_changes"
                    ][key] = {

                        "change_type":
                        "modified"
                    }

            # ================================
            # DELTA HISTORY
            # ================================

            self.delta_history.append(
                delta_report
            )

            self.previous_snapshot = (
                output_context.copy()
            )

        except MemoryError:

            logger.critical(

                "Memory overflow mitigated."
            )

            delta_report[
                "failure_detected"
            ] = True

            delta_report[
                "accuracy"
            ] = 0.0

            delta_report[
                "failure_causes"
            ].append(

                "memory_overflow_mitigated"
            )

        except Exception as error:

            logger.error(

                f"Context delta failure: {error}"
            )

            delta_report[
                "failure_detected"
            ] = True

            delta_report[
                "accuracy"
            ] = 0.0

            delta_report[
                "failure_causes"
            ].append(

                "context_delta_failure"
            )

        finally:

            # ================================
            # CLEANUP
            # ================================

            input_objects = None

            output_objects = None

            gc.collect()

        return delta_report

    # ========================================
    # CLEAR ENGINE CACHE
    # ========================================

    def clear_engine_cache(self):

        self._processed_fingerprints.clear()

        self._snapshot_vault.clear()

        gc.collect()

        logger.info(
            "ContextDeltaEngine cache cleared."
        )

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_delta = {}

        if self.delta_history:

            latest_delta = (

                self.delta_history[-1]
            )

        return {

            "tracked_snapshots":

            len(
                self._snapshot_vault
            ),

            "delta_cycles":

            len(
                self.delta_history
            ),

            "fingerprint_cache":

            len(
                self._processed_fingerprints
            ),

            "engine_state":
            self.engine_state,

            "latest_delta":
            latest_delta
        }


# ============================================
# GLOBAL ENGINE
# ============================================

context_delta_engine = (
    ContextDeltaEngine()
)
