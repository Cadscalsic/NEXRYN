# ============================================
# NEXRYN TRAJECTORY ENGINE
# ============================================

from datetime import datetime


# ============================================
# TRAJECTORY ENGINE
# ============================================

class TrajectoryEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        self.trajectory_history = []

        self.recursive_chains = []

        self.temporal_predictions = []

        self.trajectory_state = {

            "trajectory_mode":
            "recursive_temporal",

            "prediction_depth":
            1,

            "temporal_horizon":
            "short_term",

            "active_trajectories":
            0,

            "completed_trajectories":
            0,

            "trajectory_stability":
            "stable"
        }

    # ============================================
    # BUILD TRAJECTORY
    # ============================================

    def build_trajectory(

        self,

        mission,

        branch_data,

        depth=3
    ):

        trajectory_steps = []

        current_confidence = 1.0

        for step in range(depth):

            current_confidence *= 0.95

            trajectory_steps.append({

                "step_id":
                step + 1,

                "mission":
                mission,

                "predicted_state":

                "stable"

                if current_confidence >= 0.75

                else "unstable",

                "confidence":
                round(
                    current_confidence,
                    4
                ),

                "source_branch":

                branch_data.get(
                    "branch_id"
                ),

                "timestamp":
                str(
                    datetime.utcnow()
                )
            })

        trajectory = {

            "trajectory_id":

            len(
                self.trajectory_history
            ) + 1,

            "mission":
            mission,

            "steps":
            trajectory_steps,

            "depth":
            depth,

            "created_at":
            str(
                datetime.utcnow()
            )
        }

        self.trajectory_history.append(
            trajectory
        )

        self.trajectory_state[
            "active_trajectories"
        ] = len(
            self.trajectory_history
        )

        return trajectory

    # ============================================
    # SIMULATE TEMPORAL EVOLUTION
    # ============================================

    def simulate_temporal_evolution(

        self,

        trajectory
    ):

        evolution_chain = []

        for step in trajectory.get(

            "steps",

            []
        ):

            evolution_chain.append({

                "step_id":

                step.get(
                    "step_id"
                ),

                "temporal_state":

                step.get(
                    "predicted_state"
                ),

                "confidence":

                step.get(
                    "confidence"
                ),

                "evolution_status":

                "stable_transition"

                if step.get(
                    "confidence",
                    0.0
                ) >= 0.75

                else "degradation_detected"
            })

        simulation = {

            "trajectory_id":

            trajectory.get(
                "trajectory_id"
            ),

            "evolution_chain":
            evolution_chain,

            "chain_depth":

            len(
                evolution_chain
            ),

            "simulation_timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.recursive_chains.append(
            simulation
        )

        self.trajectory_state[
            "completed_trajectories"
        ] += 1

        return simulation

    # ============================================
    # SCORE TRAJECTORY
    # ============================================

    def score_trajectory(

        self,

        trajectory
    ):

        confidence_sum = 0.0

        steps = trajectory.get(
            "steps",
            []
        )

        for step in steps:

            confidence_sum += step.get(
                "confidence",
                0.0
            )

        average_score = (

            confidence_sum /

            max(
                len(steps),
                1
            )
        )

        return {

            "trajectory_id":

            trajectory.get(
                "trajectory_id"
            ),

            "trajectory_score":
            round(
                average_score,
                4
            ),

            "trajectory_quality":

            "high"

            if average_score >= 0.85

            else "moderate"
        }

    # ============================================
    # BUILD TEMPORAL FORECAST
    # ============================================

    def build_temporal_forecast(self):

        latest_trajectory = {}

        if len(
            self.trajectory_history
        ) > 0:

            latest_trajectory = (

                self.trajectory_history[-1]
            )

        return {

            "temporal_horizon":

            self.trajectory_state.get(
                "temporal_horizon"
            ),

            "prediction_depth":

            self.trajectory_state.get(
                "prediction_depth"
            ),

            "latest_trajectory":
            latest_trajectory,

            "trajectory_count":

            len(
                self.trajectory_history
            )
        }

    # ============================================
    # ADAPT TEMPORAL HORIZON
    # ============================================

    def adapt_temporal_horizon(

        self,

        evaluation_result
    ):

        accuracy = evaluation_result.get(
            "accuracy",
            0.0
        )

        if accuracy >= 0.98:

            self.trajectory_state[
                "temporal_horizon"
            ] = "long_term"

            self.trajectory_state[
                "prediction_depth"
            ] = 5

        elif accuracy >= 0.90:

            self.trajectory_state[
                "temporal_horizon"
            ] = "mid_term"

            self.trajectory_state[
                "prediction_depth"
            ] = 3

    # ============================================
    # BUILD TRAJECTORY REPORT
    # ============================================

    def build_trajectory_report(self):

        return {

            "trajectory_state":
            self.trajectory_state,

            "trajectory_count":

            len(
                self.trajectory_history
            ),

            "recursive_chain_count":

            len(
                self.recursive_chains
            ),

            "latest_chain":

            self.recursive_chains[-1]

            if len(
                self.recursive_chains
            ) > 0

            else {}
        }

    # ============================================
    # BUILD EXECUTIVE TRAJECTORY PROFILE
    # ============================================

    def build_executive_trajectory_profile(self):

        return {

            "trajectory_mode":

            self.trajectory_state.get(
                "trajectory_mode"
            ),

            "temporal_horizon":

            self.trajectory_state.get(
                "temporal_horizon"
            ),

            "prediction_depth":

            self.trajectory_state.get(
                "prediction_depth"
            ),

            "active_trajectories":

            self.trajectory_state.get(
                "active_trajectories"
            ),

            "completed_trajectories":

            self.trajectory_state.get(
                "completed_trajectories"
            ),

            "trajectory_stability":

            self.trajectory_state.get(
                "trajectory_stability"
            )
        }