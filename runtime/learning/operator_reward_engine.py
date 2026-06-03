# ============================================
# NEXRYN OPERATOR REWARD ENGINE
# EXECUTION GROUNDING RUNTIME
# ============================================

from datetime import datetime

import numpy as np


# ============================================
# OPERATOR REWARD ENGINE
# ============================================

class OperatorRewardEngine:

    # ========================================
    # INITIALIZATION
    # ========================================

    def __init__(self):

        self.operator_weights = {}

        self.reward_history = []

        self.learning_rate = 0.1

        self.success_threshold = 1.0

    # ========================================
    # SAFE ARRAY
    # ========================================

    def safe_array(
        self,
        grid
    ):

        if grid is None:

            return np.array([])

        if hasattr(
            grid,
            "grid"
        ):

            return np.array(
                grid.grid
            )

        return np.array(grid)

    # ========================================
    # NORMALIZE SCORE
    # ========================================

    def normalize_score(
        self,
        score
    ):

        if not isinstance(
            score,
            (
                int,
                float
            )
        ):

            score = 0.0

        score = max(
            0.0,
            float(score)
        )

        score = min(
            1.0,
            score
        )

        return round(
            score,
            4
        )

    # ========================================
    # ENSURE OPERATOR
    # ========================================

    def ensure_operator(
        self,
        operator_name
    ):

        if operator_name is None:

            operator_name = "unknown_operator"

        operator_name = str(
            operator_name
        )

        if operator_name not in self.operator_weights:

            self.operator_weights[
                operator_name
            ] = {

                "weight":
                0.5,

                "reward_count":
                0,

                "punish_count":
                0,

                "usage_count":
                0,

                "average_accuracy":
                0.0,

                "total_accuracy":
                0.0,

                "last_updated":
                None
            }

        return operator_name

    # ========================================
    # COMPUTE ACCURACY
    # ========================================

    def compute_accuracy(
        self,
        predicted,
        target
    ):

        predicted = self.safe_array(
            predicted
        )

        target = self.safe_array(
            target
        )

        if (

            predicted.size == 0

            or

            target.size == 0

            or

            predicted.shape != target.shape
        ):

            return 0.0

        correct_cells = np.sum(
            predicted == target
        )

        accuracy = (
            correct_cells
            /
            predicted.size
        )

        return self.normalize_score(
            accuracy
        )

    # ========================================
    # STRUCTURAL SIMILARITY
    # ========================================

    def compute_structural_similarity(
        self,
        predicted,
        target
    ):

        predicted = self.safe_array(
            predicted
        )

        target = self.safe_array(
            target
        )

        if (

            predicted.size == 0

            or

            target.size == 0
        ):

            return 0.0

        score = 0.0

        if predicted.shape == target.shape:

            score += 0.4

        predicted_density = np.mean(
            predicted != 0
        )

        target_density = np.mean(
            target != 0
        )

        density_score = 1.0 - abs(
            predicted_density
            -
            target_density
        )

        predicted_mask = (
            predicted != 0
        )

        target_mask = (
            target != 0
        )

        if predicted_mask.shape == target_mask.shape:

            mask_score = np.mean(
                predicted_mask == target_mask
            )

        else:

            mask_score = 0.0

        score += 0.3 * density_score

        score += 0.3 * mask_score

        return self.normalize_score(
            score
        )

    # ========================================
    # COLOR SIMILARITY
    # ========================================

    def compute_color_similarity(
        self,
        predicted,
        target
    ):

        predicted = self.safe_array(
            predicted
        )

        target = self.safe_array(
            target
        )

        if (

            predicted.size == 0

            or

            target.size == 0
        ):

            return 0.0

        predicted_colors = set(
            np.unique(
                predicted
            ).tolist()
        )

        target_colors = set(
            np.unique(
                target
            ).tolist()
        )

        union = predicted_colors.union(
            target_colors
        )

        if not union:

            return 0.0

        overlap = predicted_colors.intersection(
            target_colors
        )

        return self.normalize_score(
            len(overlap)
            /
            len(union)
        )

    # ========================================
    # COMPUTE REWARD
    # ========================================

    def compute_reward_score(
        self,
        predicted,
        target
    ):

        accuracy = self.compute_accuracy(
            predicted,
            target
        )

        structural_similarity = (
            self.compute_structural_similarity(
                predicted,
                target
            )
        )

        color_similarity = (
            self.compute_color_similarity(
                predicted,
                target
            )
        )

        reward_score = (
            accuracy * 0.6
            +
            structural_similarity * 0.25
            +
            color_similarity * 0.15
        )

        return {

            "accuracy":
            accuracy,

            "structural_similarity":
            structural_similarity,

            "color_similarity":
            color_similarity,

            "reward_score":
            self.normalize_score(
                reward_score
            ),

            "success":
            bool(
                accuracy >= self.success_threshold
            )
        }

    # ========================================
    # REWARD OPERATOR
    # ========================================

    def reward_operator(
        self,
        operator_name,
        reward_score
    ):

        operator_name = self.ensure_operator(
            operator_name
        )

        data = self.operator_weights[
            operator_name
        ]

        reward_score = self.normalize_score(
            reward_score
        )

        data[
            "weight"
        ] = self.normalize_score(

            data.get(
                "weight",
                0.5
            )

            +

            self.learning_rate * reward_score
        )

        data[
            "reward_count"
        ] += 1

        return data

    # ========================================
    # PUNISH OPERATOR
    # ========================================

    def punish_operator(
        self,
        operator_name,
        reward_score
    ):

        operator_name = self.ensure_operator(
            operator_name
        )

        data = self.operator_weights[
            operator_name
        ]

        reward_score = self.normalize_score(
            reward_score
        )

        penalty = (
            1.0
            -
            reward_score
        )

        data[
            "weight"
        ] = self.normalize_score(

            data.get(
                "weight",
                0.5
            )

            -

            self.learning_rate * penalty
        )

        data[
            "punish_count"
        ] += 1

        return data

    # ========================================
    # UPDATE OPERATOR WEIGHTS
    # ========================================

    def update_operator_weights(
        self,
        primitives,
        predicted_output,
        target_output
    ):

        primitives = primitives or []

        metrics = self.compute_reward_score(
            predicted_output,
            target_output
        )

        reward_events = []

        for primitive in primitives:

            if not isinstance(
                primitive,
                dict
            ):

                continue

            operator_name = primitive.get(
                "primitive"
            )

            operator_name = self.ensure_operator(
                operator_name
            )

            data = self.operator_weights[
                operator_name
            ]

            if metrics.get(
                "success",
                False
            ):

                self.reward_operator(
                    operator_name,
                    metrics.get(
                        "reward_score",
                        0.0
                    )
                )

                event_type = "reward"

            else:

                self.punish_operator(
                    operator_name,
                    metrics.get(
                        "reward_score",
                        0.0
                    )
                )

                event_type = "punish"

            data[
                "usage_count"
            ] += 1

            data[
                "total_accuracy"
            ] += metrics.get(
                "accuracy",
                0.0
            )

            usage_count = max(
                data.get(
                    "usage_count",
                    1
                ),
                1
            )

            data[
                "average_accuracy"
            ] = round(

                data.get(
                    "total_accuracy",
                    0.0
                )

                /

                usage_count,

                4
            )

            data[
                "last_updated"
            ] = str(
                datetime.utcnow()
            )

            reward_events.append({

                "operator":
                operator_name,

                "event_type":
                event_type,

                "weight":
                data.get(
                    "weight",
                    0.0
                ),

                "accuracy":
                metrics.get(
                    "accuracy",
                    0.0
                ),

                "reward_score":
                metrics.get(
                    "reward_score",
                    0.0
                ),

                "timestamp":
                str(datetime.utcnow())
            })

        report = {

            "operator_count":
            len(reward_events),

            "metrics":
            metrics,

            "events":
            reward_events,

            "operator_weights":
            dict(
                self.operator_weights
            )
        }

        self.reward_history.append(
            report
        )

        return report

    # ========================================
    # APPLY WEIGHTS
    # ========================================

    def apply_operator_weights(
        self,
        primitives
    ):

        weighted = []

        for primitive in primitives or []:

            if not isinstance(
                primitive,
                dict
            ):

                continue

            operator_name = self.ensure_operator(
                primitive.get(
                    "primitive"
                )
            )

            data = self.operator_weights.get(
                operator_name,
                {}
            )

            weight = data.get(
                "weight",
                0.5
            )

            updated = dict(
                primitive
            )

            base_score = updated.get(
                "execution_score",
                updated.get(
                    "confidence",
                    0.0
                )
            )

            grounded_score = (
                base_score * 0.7
                +
                weight * 0.3
            )

            updated[
                "operator_weight"
            ] = round(
                weight,
                4
            )

            updated[
                "grounded_execution_score"
            ] = self.normalize_score(
                grounded_score
            )

            weighted.append(
                updated
            )

        return sorted(

            weighted,

            key=lambda primitive: (

                primitive.get(
                    "grounded_execution_score",
                    0.0
                ),

                primitive.get(
                    "confidence",
                    0.0
                )
            ),

            reverse=True
        )

    # ========================================
    # GET OPERATOR WEIGHT
    # ========================================

    def get_operator_weight(
        self,
        operator_name
    ):

        operator_name = self.ensure_operator(
            operator_name
        )

        return self.operator_weights.get(
            operator_name,
            {}
        ).get(
            "weight",
            0.5
        )

    # ========================================
    # GET OPERATOR REWARD SCORE
    # ========================================

    def get_operator_reward_score(
        self,
        operator_name
    ):

        operator_name = self.ensure_operator(
            operator_name
        )

        data = self.operator_weights.get(
            operator_name,
            {}
        )

        usage_count = data.get(
            "usage_count",
            0
        )

        if usage_count > 0:

            return data.get(
                "average_accuracy",
                0.0
            )

        return data.get(
            "weight",
            0.5
        )

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "operator_count":
            len(
                self.operator_weights
            ),

            "reward_events":
            len(
                self.reward_history
            ),

            "operator_weights":
            self.operator_weights
        }


# ============================================
# GLOBAL ENGINE
# ============================================

operator_reward_engine = (
    OperatorRewardEngine()
)
