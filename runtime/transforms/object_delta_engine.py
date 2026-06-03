# ============================================
# NEXRYN OBJECT DELTA ENGINE
# EXECUTABLE OBJECT CAUSALITY ANALYZER
# ============================================

from datetime import datetime

import numpy as np


# ============================================
# OBJECT DELTA ENGINE
# ============================================

class ObjectDeltaEngine:

    # ========================================
    # INITIALIZATION
    # ========================================

    def __init__(self):

        self.delta_history = []

        self.operator_statistics = {}

        self.delta_memory = []

        self.object_lineage = []

    # ========================================
    # SAFE OBJECTS
    # ========================================

    def safe_objects(
        self,
        objects
    ):

        if objects is None:
            return []

        if not isinstance(
            objects,
            list
        ):

            return []

        return objects

    # ========================================
    # SAFE OBJECT SIZE
    # ========================================

    def extract_object_size(
        self,
        obj
    ):

        if not isinstance(
            obj,
            dict
        ):

            return 1

        size = obj.get(
            "size",
            1
        )

        if not isinstance(
            size,
            (
                int,
                float
            )
        ):

            return 1

        return int(size)

    # ========================================
    # SAFE POSITION
    # ========================================

    def extract_position(
        self,
        obj
    ):

        if not isinstance(
            obj,
            dict
        ):

            return (0, 0)

        centroid = obj.get(
            "centroid"
        )

        if isinstance(
            centroid,
            dict
        ):

            row = centroid.get(
                "row"
            )

            col = centroid.get(
                "col"
            )

            if (

                row is not None

                and

                col is not None
            ):

                return (
                    float(row),
                    float(col)
                )

        bounding_box = obj.get(
            "bounding_box"
        )

        if isinstance(
            bounding_box,
            dict
        ):

            row = bounding_box.get(
                "min_row"
            )

            col = bounding_box.get(
                "min_col"
            )

            if (

                row is not None

                and

                col is not None
            ):

                return (
                    float(row),
                    float(col)
                )

        position = obj.get(
            "position",
            (
                0,
                0
            )
        )

        if not isinstance(
            position,
            (
                list,
                tuple
            )
        ):

            return (0, 0)

        if len(position) != 2:

            return (0, 0)

        return (
            float(position[0]),
            float(position[1])
        )

    # ========================================
    # SAFE COLOR
    # ========================================

    def extract_color(
        self,
        obj
    ):

        if not isinstance(
            obj,
            dict
        ):

            return None

        return obj.get(
            "color"
        )

    # ========================================
    # OBJECT COUNT DELTA
    # ========================================

    def analyze_object_count_delta(

        self,

        input_objects,

        output_objects
    ):

        input_count = len(
            input_objects
        )

        output_count = len(
            output_objects
        )

        delta = (
            output_count
            -
            input_count
        )

        operator = (
            "preserve_objects"
        )

        confidence = 0.85

        if delta > 0:

            operator = (
                "duplicate_object"
            )

            confidence = 0.96

        elif delta < 0:

            operator = (
                "remove_object"
            )

            confidence = 0.92

        return {

            "delta_type":
            "object_count",

            "input_count":
            input_count,

            "output_count":
            output_count,

            "delta":
            delta,

            "operator":
            operator,

            "confidence":
            confidence
        }

    # ========================================
    # OBJECT SIZE DELTA
    # ========================================

    def analyze_object_size_delta(

        self,

        input_objects,

        output_objects
    ):

        input_sizes = [

            self.extract_object_size(obj)

            for obj in input_objects
        ]

        output_sizes = [

            self.extract_object_size(obj)

            for obj in output_objects
        ]

        input_total = sum(
            input_sizes
        )

        output_total = sum(
            output_sizes
        )

        delta = (
            output_total
            -
            input_total
        )

        operator = (
            "preserve_size"
        )

        confidence = 0.84

        if delta > 0:

            operator = (
                "expand_object"
            )

            confidence = 0.94

        elif delta < 0:

            operator = (
                "shrink_object"
            )

            confidence = 0.90

        return {

            "delta_type":
            "object_size",

            "input_total_size":
            input_total,

            "output_total_size":
            output_total,

            "delta":
            delta,

            "operator":
            operator,

            "confidence":
            confidence
        }

    # ========================================
    # POSITION DELTA
    # ========================================

    def analyze_position_delta(

        self,

        input_objects,

        output_objects
    ):

        translations = []

        for index, input_obj in enumerate(
            input_objects
        ):

            if index >= len(
                output_objects
            ):

                continue

            output_obj = (
                output_objects[index]
            )

            input_position = (
                self.extract_position(
                    input_obj
                )
            )

            output_position = (
                self.extract_position(
                    output_obj
                )
            )

            dy = (
                output_position[0]
                -
                input_position[0]
            )

            dx = (
                output_position[1]
                -
                input_position[1]
            )

            translations.append(
                (
                    int(round(dy)),
                    int(round(dx))
                )
            )

        dominant_translation = (
            (0, 0)
        )

        if translations:

            dominant_translation = max(

                set(translations),

                key=translations.count
            )

        operator = (
            "preserve_position"
        )

        confidence = 0.80

        if dominant_translation != (0, 0):

            dy, dx = (
                dominant_translation
            )

            if abs(dx) > abs(dy):

                if dx > 0:

                    operator = (
                        "translate_right"
                    )

                else:

                    operator = (
                        "translate_left"
                    )

            else:

                if dy > 0:

                    operator = (
                        "translate_down"
                    )

                else:

                    operator = (
                        "translate_up"
                    )

            confidence = 0.91

        return {

            "delta_type":
            "object_translation",

            "translations":
            translations,

            "dominant_translation":
            dominant_translation,

            "operator":
            operator,

            "confidence":
            confidence
        }

    # ========================================
    # COLOR DELTA
    # ========================================

    def analyze_color_delta(

        self,

        input_objects,

        output_objects
    ):

        input_colors = set()

        output_colors = set()

        for obj in input_objects:

            color = (
                self.extract_color(
                    obj
                )
            )

            if color is not None:

                input_colors.add(
                    color
                )

        for obj in output_objects:

            color = (
                self.extract_color(
                    obj
                )
            )

            if color is not None:

                output_colors.add(
                    color
                )

        added_colors = (
            output_colors
            -
            input_colors
        )

        removed_colors = (
            input_colors
            -
            output_colors
        )

        operator = (
            "preserve_colors"
        )

        confidence = 0.83

        if added_colors or removed_colors:

            operator = (
                "replace_color"
            )

            confidence = 0.92

        return {

            "delta_type":
            "color_change",

            "input_colors":
            list(input_colors),

            "output_colors":
            list(output_colors),

            "added_colors":
            list(added_colors),

            "removed_colors":
            list(removed_colors),

            "operator":
            operator,

            "confidence":
            confidence
        }

    # ========================================
    # TOPOLOGY DELTA
    # ========================================

    def analyze_topology_delta(

        self,

        input_objects,

        output_objects
    ):

        input_complexity = len(
            input_objects
        )

        output_complexity = len(
            output_objects
        )

        complexity_delta = (
            output_complexity
            -
            input_complexity
        )

        operator = (
            "preserve_topology"
        )

        confidence = 0.82

        if complexity_delta > 0:

            operator = (
                "grow_topology"
            )

            confidence = 0.90

        elif complexity_delta < 0:

            operator = (
                "compress_topology"
            )

            confidence = 0.88

        return {

            "delta_type":
            "topology_change",

            "input_complexity":
            input_complexity,

            "output_complexity":
            output_complexity,

            "complexity_delta":
            complexity_delta,

            "operator":
            operator,

            "confidence":
            confidence
        }

    # ========================================
    # RANK DELTAS
    # ========================================

    def rank_deltas(
        self,
        reports
    ):

        ranked = sorted(

            reports,

            key=lambda x: x.get(
                "confidence",
                0.0
            ),

            reverse=True
        )

        return ranked

    # ========================================
    # BUILD EXECUTABLE HYPOTHESES
    # ========================================

    def build_hypotheses(
        self,
        ranked_reports
    ):

        hypotheses = []

        for report in ranked_reports:

            hypothesis = {

                "type":
                report.get(
                    "delta_type"
                ),

                "primitive":
                report.get(
                    "operator"
                ),

                "confidence":
                round(

                    report.get(
                        "confidence",
                        0.0
                    ),

                    4
                ),

                "execution_score":
                round(

                    report.get(
                        "confidence",
                        0.0
                    ) * 0.95,

                    4
                ),

                "geometric_grounding":
                report
            }

            hypotheses.append(
                hypothesis
            )

        return hypotheses

    # ========================================
    # UPDATE STATISTICS
    # ========================================

    def update_statistics(
        self,
        reports
    ):

        for report in reports:

            operator = report.get(
                "operator"
            )

            if operator not in (
                self.operator_statistics
            ):

                self.operator_statistics[
                    operator
                ] = 0

            self.operator_statistics[
                operator
            ] += 1

    # ========================================
    # BUILD DELTA REPORT
    # ========================================

    def build_delta_report(

        self,

        ranked_reports,

        hypotheses
    ):

        top_operator = None

        if ranked_reports:

            top_operator = (

                ranked_reports[0]
                .get(
                    "operator"
                )
            )

        return {

            "delta_events":
            len(ranked_reports),

            "generated_hypotheses":
            len(hypotheses),

            "top_operator":
            top_operator,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN ANALYSIS
    # ========================================

    def analyze_deltas(

        self,

        input_objects,

        output_objects
    ):

        input_objects = (
            self.safe_objects(
                input_objects
            )
        )

        output_objects = (
            self.safe_objects(
                output_objects
            )
        )

        reports = []

        # ====================================
        # OBJECT COUNT
        # ====================================

        reports.append(

            self.analyze_object_count_delta(

                input_objects,

                output_objects
            )
        )

        # ====================================
        # OBJECT SIZE
        # ====================================

        reports.append(

            self.analyze_object_size_delta(

                input_objects,

                output_objects
            )
        )

        # ====================================
        # POSITION
        # ====================================

        reports.append(

            self.analyze_position_delta(

                input_objects,

                output_objects
            )
        )

        # ====================================
        # COLORS
        # ====================================

        reports.append(

            self.analyze_color_delta(

                input_objects,

                output_objects
            )
        )

        # ====================================
        # TOPOLOGY
        # ====================================

        reports.append(

            self.analyze_topology_delta(

                input_objects,

                output_objects
            )
        )

        # ====================================
        # RANKING
        # ====================================

        ranked_reports = (
            self.rank_deltas(
                reports
            )
        )

        # ====================================
        # BUILD HYPOTHESES
        # ====================================

        executable_hypotheses = (

            self.build_hypotheses(
                ranked_reports
            )
        )

        # ====================================
        # UPDATE MEMORY
        # ====================================

        self.delta_history.append(
            ranked_reports
        )

        self.delta_memory.append(
            executable_hypotheses
        )

        self.object_lineage.append({

            "input_count":
            len(input_objects),

            "output_count":
            len(output_objects),

            "timestamp":
            str(datetime.utcnow())
        })

        self.update_statistics(
            ranked_reports
        )

        # ====================================
        # FINAL REPORT
        # ====================================

        delta_report = (

            self.build_delta_report(

                ranked_reports,

                executable_hypotheses
            )
        )

        return {

            "ranked_reports":
            ranked_reports,

            "executable_hypotheses":
            executable_hypotheses,

            "delta_report":
            delta_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

object_delta_engine = (
    ObjectDeltaEngine()
)
