# =========================================================
# NEXRYN RECURSIVE EXECUTIVE REGULATION
# =========================================================

from datetime import datetime
from dataclasses import asdict, dataclass, field

import uuid
import random

MIN_EXPLORATION_RATE = 0.02

MIN_REASONING_DEPTH_LIMIT = 4

MAX_REASONING_DEPTH_LIMIT = 15


ALLOWED_META_ACTIONS = {
    "REUSE_MEMORY",
    "RUN_FAST_REASONING",
    "RUN_LOCALIZATION",
    "RUN_DEEP_REASONING",
    "ESCALATE_TO_GOVERNANCE",
    "STOP_AFTER_SUCCESS",
}


@dataclass
class MetaDecision:

    action: str

    reason: str

    confidence: float

    max_reasoning_depth: int = 2

    max_active_routes: int = 2

    enable_memory_reuse: bool = True

    enable_localization: bool = True

    enable_governance: bool = True

    enable_self_improvement: bool = False

    enable_strategy_evolution: bool = False

    shutdown_mode: str = "fast"

    notes: list[str] = field(default_factory=list)

    def as_report(self):

        return asdict(self)


# =========================================================
# REGULATION NODE
# =========================================================

@dataclass
class RegulationNode:

    node_id: str

    exploration_rate: float

    mutation_rate: float

    reasoning_depth_limit: int

    uncertainty_level: float

    energy_pressure: float

    regulation_mode: str

    created_at: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# META CONTROLLER ENGINE
# =========================================================

class MetaControllerEngine:

    # =====================================================
    # INITIALIZE ENGINE
    # =====================================================

    def __init__(self):

        # =================================================
        # CONTROL STATE
        # =================================================

        self.control_state = {

            "exploration_rate":
            0.30,

            "mutation_rate":
            0.20,

            "reasoning_depth_limit":
            10,

            "cognitive_mode":
            "balanced",

            "executive_regulation":
            "adaptive",

            "uncertainty_governance":
            "enabled",

            "energy_management":
            "active",

            "recovery_protocol":
            "standby"
        }

        self.control_history = []

        self.regulation_graph = []

        self.executive_interventions = []

        self.energy_history = []

        self.policy_memory = []

        self.overload_events = []

        self.recursive_regulation = []

        self.outcome_history = []

        self.current_decision = None

        self.decision_history = []

    def _clamp(
        self,
        value,
        default=0.0,
    ):

        try:
            value = float(value)
        except (TypeError, ValueError):
            value = default
        return max(0.0, min(1.0, value))

    def _mapping(
        self,
        value,
    ):

        return value if isinstance(value, dict) else {}

    def _get(
        self,
        source,
        key,
        default=None,
    ):

        if isinstance(source, dict):
            return source.get(key, default)
        return getattr(source, key, default)

    def _first_mapping(
        self,
        runtime_context,
        keys,
    ):

        for key in keys:
            value = runtime_context.get(key)
            if isinstance(value, dict):
                return value
        return {}

    def _truth_candidate_changed(
        self,
        runtime_context,
    ):

        for key in [
            "truth_candidate_state_changed",
            "truth_registry_changed",
            "truth_commitment_changed",
        ]:
            if runtime_context.get(key) is True:
                return True
        return False

    def _identity_unstable(
        self,
        runtime_context,
    ):

        stable_states = {
            "IDENTITY_GOVERNANCE_STABLE",
            "STABLE",
            "stable",
        }
        unstable_states = {
            "UNSTABLE",
            "unstable",
            "TEMPORARY_RECOVERY_HOLD",
            "IDENTITY_GOVERNANCE_UNSTABLE",
        }
        for source in [
            runtime_context,
            runtime_context.get("identity_governance_report", {}),
            runtime_context.get("identity_stability_report", {}),
            runtime_context.get("cognitive_identity_report", {}),
            runtime_context.get("governance_report", {}),
        ]:
            if not isinstance(source, dict):
                continue
            state = source.get("identity_governance_state")
            if state in unstable_states:
                return True
            if state in stable_states:
                return False
            if source.get("identity_stable") is False:
                return True
        return False

    def _context_invalidated(
        self,
        runtime_context,
    ):

        if runtime_context.get("context_invalidated") is True:
            return True
        change = self._mapping(
            runtime_context.get("change_detection_report")
        )
        return change.get("important_change_detected") is True

    def _operation_transformation_like(
        self,
        runtime_context,
    ):

        task_profile = runtime_context.get("current_task_profile")
        task_report = self._mapping(
            runtime_context.get("task_complexity_report")
        )
        transformation_count = self._get(
            task_profile,
            "transformation_count",
            task_report.get("transformation_count", 0),
        )
        if isinstance(transformation_count, (int, float)) and transformation_count > 0:
            return True
        for key in [
            "transformation_report",
            "transformation_localization",
            "world_model_anticipation",
        ]:
            if isinstance(runtime_context.get(key), dict):
                return True
        return False

    def _build_decision(
        self,
        action,
        reason,
        confidence,
        **kwargs
    ):

        if action not in ALLOWED_META_ACTIONS:
            action = "RUN_FAST_REASONING"
            reason = "unknown_action_defaulted_to_fast_reasoning"
        decision = MetaDecision(
            action=action,
            reason=reason,
            confidence=round(self._clamp(confidence), 4),
            **kwargs
        )
        self.current_decision = decision
        self.decision_history.append(decision.as_report())
        self.decision_history = self.decision_history[-50:]
        return decision

    def decide(
        self,
        runtime_context=None,
        task_profile=None,
        reasoning_budget=None,
        tool_selection=None,
        cache_status=None,
        localization_status=None,
        world_model_report=None,
        evaluation_report=None,
        governance_status=None,
    ):

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else {}
        )
        task_profile = task_profile or runtime_context.get(
            "current_task_profile"
        )
        reasoning_budget = reasoning_budget or runtime_context.get(
            "current_reasoning_budget"
        )
        tool_selection = tool_selection or runtime_context.get(
            "tool_selection"
        )
        cache_status = self._mapping(
            cache_status
            or runtime_context.get("memory_lookup_report")
            or runtime_context.get("cache_status")
            or runtime_context.get("cache_metrics_report")
        )
        localization_status = self._mapping(
            localization_status
            or runtime_context.get("transformation_localization")
        )
        world_model_report = self._mapping(
            world_model_report
            or runtime_context.get("world_model_gate_report")
            or runtime_context.get("world_model_report")
        )
        evaluation_report = self._mapping(
            evaluation_report
            or runtime_context.get("evaluation_result")
            or runtime_context.get("evaluation_report")
        )
        governance_status = self._mapping(
            governance_status
            or runtime_context.get("governance_report")
        )
        motivation_report = self._mapping(
            runtime_context.get("motivation_report")
            or runtime_context.get("MOTIVATION_REPORT")
        )

        budget_mode = self._get(
            reasoning_budget,
            "mode",
            runtime_context.get("mode", "adaptive"),
        )
        task_complexity = self._get(
            task_profile,
            "complexity",
            self._mapping(
                runtime_context.get("task_complexity_report")
            ).get("complexity"),
        )
        process_complexity = self._get(
            task_profile,
            "process_complexity",
            self._mapping(
                runtime_context.get("task_complexity_report")
            ).get("process_complexity", 0.0),
        )
        process_semantics_required = bool(
            process_complexity
            and self._clamp(process_complexity) >= 0.30
        )

        exact_success = evaluation_report.get("exact_success") is True
        success_state = (
            evaluation_report.get("success_state")
            or runtime_context.get("success_state")
        )
        difference_count = evaluation_report.get("difference_count")
        execution_integrity_preserved = (
            runtime_context.get("execution_integrity_preserved") is True
            or self._mapping(
                runtime_context.get("execution_integrity_report")
            ).get("integrity_preserved") is True
            or self._mapping(
                runtime_context.get("transformation_report")
            ).get("execution_integrity", {}).get("integrity_preserved") is True
        )
        execution_integrity_failed = (
            self._mapping(
                runtime_context.get("execution_integrity_report")
            ).get("integrity_preserved") is False
            or self._mapping(
                runtime_context.get("transformation_report")
            ).get("execution_integrity", {}).get("integrity_preserved") is False
        )

        contradiction_detected = (
            runtime_context.get("contradiction_detected") is True
            or bool(runtime_context.get("unresolved_contradictions"))
            or bool(runtime_context.get("semantic_contradictions"))
            or governance_status.get("contradiction_detected") is True
        )
        outcome_class = motivation_report.get("outcome_class")
        penalty_score = self._clamp(
            motivation_report.get("penalty_score", 0.0)
        )

        terminal_success_ready = (
            (
                exact_success
                and difference_count == 0
            )
            or success_state == "SUCCESS_WITH_RESIDUALS"
            or (
                success_state == "LEARNING_PROGRESS"
                and self._get(evaluation_report, "retry_allowed", False) is False
            )
        )

        if (
            terminal_success_ready
            and not execution_integrity_failed
            and not contradiction_detected
            and not self._identity_unstable(runtime_context)
        ):
            return self._build_decision(
                "STOP_AFTER_SUCCESS",
                (
                    "high_confidence_residual_acceptance"
                    if success_state == "SUCCESS_WITH_RESIDUALS"
                    else "new_knowledge_signal_recorded"
                    if success_state == "LEARNING_PROGRESS"
                    else "exact_success_integrity_preserved"
                ),
                1.0,
                max_reasoning_depth=0,
                max_active_routes=0,
                enable_memory_reuse=False,
                enable_localization=False,
                enable_governance=False,
                enable_self_improvement=False,
                enable_strategy_evolution=False,
                shutdown_mode="fast",
                notes=["store_minimal_success_memory_only"],
            )

        if (
            cache_status.get("exact_cache_hit") is True
            or cache_status.get("cache_hit") is True
        ) and (
            cache_status.get("concept_version_hash_unchanged") is True
            or runtime_context.get("concept_version_hash_unchanged") is True
        ) and (
            cache_status.get("stable_truth_exists") is True
            or runtime_context.get("stable_truth") is True
            or runtime_context.get("stable_truth_exists") is True
        ):
            return self._build_decision(
                "REUSE_MEMORY",
                "stable_cache_hit_with_unchanged_concept_version",
                0.98,
                max_reasoning_depth=0,
                max_active_routes=0,
                enable_memory_reuse=True,
                enable_localization=False,
                enable_governance=False,
                enable_self_improvement=False,
                enable_strategy_evolution=False,
                shutdown_mode="fast",
                notes=["memory_first_runtime"],
            )

        if (
            contradiction_detected
            or self._identity_unstable(runtime_context)
            or self._truth_candidate_changed(runtime_context)
            or self._context_invalidated(runtime_context)
            or outcome_class == "critical_failure"
            or penalty_score >= 0.70
        ):
            return self._build_decision(
                "ESCALATE_TO_GOVERNANCE",
                "governance_or_identity_instability_detected",
                0.92,
                enable_governance=True,
                enable_self_improvement=False,
                enable_strategy_evolution=False,
                shutdown_mode="normal",
                notes=["truth_and_identity_safety_first"],
            )

        residual_difference_count = (
            runtime_context.get("residual_difference_count")
            or self._mapping(
                runtime_context.get("world_model_anticipation")
            ).get("residual_difference_count")
            or self._mapping(
                runtime_context.get("prediction_report")
            ).get("residual_difference_count")
        )
        localization_ready = (
            localization_status.get("localization_ready") is True
            or runtime_context.get("localization_ready") is True
        )
        failure_cause = (
            runtime_context.get("failure_cause")
            or self._mapping(
                runtime_context.get("failure_analysis")
            ).get("failure_cause")
        )
        if (
            (
                isinstance(residual_difference_count, int)
                and residual_difference_count > 0
                and not localization_ready
                and self._operation_transformation_like(runtime_context)
            )
            or failure_cause == "localized_prediction_mismatch"
        ):
            return self._build_decision(
                "RUN_LOCALIZATION",
                "localized_prediction_mismatch_requires_localization_first",
                0.90,
                max_reasoning_depth=2,
                max_active_routes=2,
                enable_memory_reuse=True,
                enable_localization=True,
                enable_governance=False,
                enable_self_improvement=False,
                enable_strategy_evolution=False,
                shutdown_mode="fast",
                notes=["defer_strategy_evolution_until_localization_attempted"],
            )

        failure_confirmed = (
            runtime_context.get("failure_confirmed") is True
            or self._mapping(
                runtime_context.get("failure_analysis")
            ).get("failure_detected") is True
        )
        localization_attempted = (
            localization_ready
            or runtime_context.get("localization_attempted") is True
            or self._mapping(
                runtime_context.get("transformation_localization")
            ).get("localization_attempted") is True
        )
        residual_error_explained = (
            runtime_context.get("residual_error_explained") is True
            or self._mapping(
                runtime_context.get("failure_analysis")
            ).get("residual_error_explained") is True
        )
        no_cache_reuse = not (
            cache_status.get("exact_cache_hit") is True
            or cache_status.get("cache_hit") is True
            or runtime_context.get("pipeline_cache_hit") is True
        )
        simple_localization_mismatch = (
            failure_cause == "localized_prediction_mismatch"
            or (
                isinstance(residual_difference_count, int)
                and residual_difference_count <= 2
                and self._operation_transformation_like(runtime_context)
            )
        )
        if (
            failure_confirmed
            and localization_attempted
            and residual_error_explained
            and no_cache_reuse
            and not exact_success
            and not simple_localization_mismatch
        ):
            return self._build_decision(
                "RUN_DEEP_REASONING",
                "confirmed_explained_failure_after_localization",
                0.78,
                max_reasoning_depth=4,
                max_active_routes=4,
                enable_memory_reuse=False,
                enable_localization=True,
                enable_governance=True,
                enable_self_improvement=False,
                enable_strategy_evolution=False,
                shutdown_mode="normal",
                notes=["self_improvement_requires_explicit_external_enable"],
            )

        if (
            task_complexity == "low"
            and str(budget_mode).lower() == "fast"
            and not process_semantics_required
        ):
            return self._build_decision(
                "RUN_FAST_REASONING",
                "low_complexity_fast_budget_without_process_semantics",
                0.88,
                max_reasoning_depth=2,
                max_active_routes=2,
                enable_memory_reuse=True,
                enable_localization=True,
                enable_governance=True,
                enable_self_improvement=False,
                enable_strategy_evolution=False,
                shutdown_mode="fast",
                notes=["bounded_fast_reasoning"],
            )

        if str(budget_mode).lower() == "deep":
            return self._build_decision(
                "RUN_DEEP_REASONING",
                "deep_budget_requested",
                0.75,
                max_reasoning_depth=self._get(
                    reasoning_budget,
                    "max_reasoning_depth",
                    8,
                ),
                max_active_routes=self._get(
                    reasoning_budget,
                    "max_active_routes",
                    8,
                ),
                enable_memory_reuse=False,
                enable_governance=True,
                enable_self_improvement=False,
                enable_strategy_evolution=False,
                shutdown_mode="deep",
                notes=["deep_mode_keeps_validation_available"],
            )

        return self._build_decision(
            "RUN_FAST_REASONING",
            "no_escalation_needed_minimum_cognition",
            0.80,
            max_reasoning_depth=min(
                int(
                    self._get(
                        reasoning_budget,
                        "max_reasoning_depth",
                        4,
                    )
                ),
                2,
            ),
            max_active_routes=min(
                int(
                    self._get(
                        reasoning_budget,
                        "max_active_routes",
                        4,
                    )
                ),
                2,
            ),
            enable_memory_reuse=True,
            enable_localization=True,
            enable_governance=True,
            enable_self_improvement=False,
            enable_strategy_evolution=False,
            shutdown_mode="fast",
            notes=["default_modern_meta_control"],
        )

    # =====================================================
    # RECORD OUTCOME
    # =====================================================

    def record_outcome(
        self,
        evaluation_result
    ):

        if not isinstance(
            evaluation_result,
            dict
        ):

            evaluation_result = {}

        self.outcome_history.append({

            "success":
            bool(
                evaluation_result.get(
                    "success",
                    False
                )
            ),

            "accuracy":
            evaluation_result.get(
                "accuracy",
                0.0
            ),

            "timestamp":
            str(datetime.utcnow())
        })

        self.outcome_history = (
            self.outcome_history[-10:]
        )

        return self.recent_success_rate()

    # =====================================================
    # RECENT SUCCESS RATE
    # =====================================================

    def recent_success_rate(self):

        if not self.outcome_history:

            return 0.0

        successes = len([

            outcome

            for outcome in self.outcome_history

            if outcome.get(
                "success",
                False
            )
        ])

        return round(
            successes
            /
            len(self.outcome_history),
            4
        )

    # =====================================================
    # ESTIMATE UNCERTAINTY
    # =====================================================

    def estimate_uncertainty(

        self,

        recursive_report
    ):

        complexity = recursive_report.get(
            "cognitive_complexity",
            "low"
        )

        if complexity == "high":

            return 0.75

        elif complexity == "medium":

            return 0.45

        return 0.20

    # =====================================================
    # ESTIMATE ENERGY PRESSURE
    # =====================================================

    def estimate_energy_pressure(

        self,

        recursive_report
    ):

        reasoning_depth = recursive_report.get(
            "reasoning_depth",
            0
        )

        pressure = round(

            min(
                reasoning_depth / 20,
                1.0
            ),

            2
        )

        self.energy_history.append({

            "pressure":
            pressure,

            "timestamp":
            str(datetime.utcnow())
        })

        return pressure

    # =====================================================
    # ADAPT CONTROL
    # =====================================================

    def adapt_control(

        self,

        recursive_report
    ):

        task_complexity = recursive_report.get(
            "task_complexity",
            None
        )

        complexity = recursive_report.get(
            "cognitive_complexity",
            "low"
        )

        mutation_detected = recursive_report.get(
            "mutation_detected",
            False
        )

        exploration_detected = recursive_report.get(
            "exploration_detected",
            False
        )

        uncertainty = (
            self.estimate_uncertainty(
                recursive_report
            )
        )

        energy_pressure = (
            self.estimate_energy_pressure(
                recursive_report
            )
        )

        # =================================================
        # HIGH COMPLEXITY
        # =================================================

        if complexity == "high":

            self.control_state[
                "exploration_rate"
            ] = 0.15

            self.control_state[
                "mutation_rate"
            ] = 0.10

            self.control_state[
                "reasoning_depth_limit"
            ] = 15

            self.control_state[
                "cognitive_mode"
            ] = "focused"

        # =================================================
        # MEDIUM COMPLEXITY
        # =================================================

        elif complexity == "medium":

            self.control_state[
                "exploration_rate"
            ] = 0.25

            self.control_state[
                "mutation_rate"
            ] = 0.20

            self.control_state[
                "reasoning_depth_limit"
            ] = 12

            self.control_state[
                "cognitive_mode"
            ] = "balanced"

        # =================================================
        # LOW COMPLEXITY
        # =================================================

        else:

            self.control_state[
                "exploration_rate"
            ] = 0.40

            self.control_state[
                "mutation_rate"
            ] = 0.35

            self.control_state[
                "reasoning_depth_limit"
            ] = 8

            self.control_state[
                "cognitive_mode"
            ] = "exploratory"

        # =================================================
        # ADAPTIVE DEPTH REGULATION
        # =================================================

        if isinstance(
            task_complexity,
            (int, float)
        ):

            if task_complexity < 0.30:

                self.control_state[
                    "reasoning_depth_limit"
                ] = MIN_REASONING_DEPTH_LIMIT

                self.control_state[
                    "cognitive_mode"
                ] = "minimal_reasoning"

            elif task_complexity > 0.80:

                self.control_state[
                    "reasoning_depth_limit"
                ] = MAX_REASONING_DEPTH_LIMIT

            else:

                self.control_state[
                    "reasoning_depth_limit"
                ] = 8

        # =================================================
        # UNCERTAINTY GOVERNANCE
        # =================================================

        if uncertainty >= 0.70:

            if not (

                isinstance(
                    task_complexity,
                    (int, float)
                )

                and

                task_complexity < 0.30
            ):

                self.control_state[
                    "reasoning_depth_limit"
                ] += 3

            self.control_state[
                "cognitive_mode"
            ] = "stabilization"

        # =================================================
        # ENERGY OVERLOAD
        # =================================================

        if energy_pressure >= 0.80:

            overload = {

                "event_id":
                str(uuid.uuid4()),

                "event":
                "cognitive_overload",

                "severity":
                "high",

                "timestamp":
                str(datetime.utcnow())
            }

            self.overload_events.append(
                overload
            )

            self.control_state[
                "exploration_rate"
            ] *= 0.5

            self.control_state[
                "mutation_rate"
            ] *= 0.5

            self.control_state[
                "recovery_protocol"
            ] = "active"

        # =================================================
        # BOOST EXPLORATION
        # =================================================

        if not exploration_detected:

            self.control_state[
                "exploration_rate"
            ] += 0.05

        # =================================================
        # BOOST MUTATION
        # =================================================

        if not mutation_detected:

            self.control_state[
                "mutation_rate"
            ] += 0.05

        # =================================================
        # SUCCESS STABILIZATION
        # =================================================

        recent_success_rate = (
            self.recent_success_rate()
        )

        if recent_success_rate > 0.90:

            self.control_state[
                "exploration_rate"
            ] = max(
                self.control_state.get(
                    "exploration_rate",
                    0.0
                )
                * 0.5,
                MIN_EXPLORATION_RATE
            )

            self.control_state[
                "mutation_rate"
            ] = max(
                self.control_state.get(
                    "mutation_rate",
                    0.0
                )
                * 0.75,
                0.02
            )

            self.control_state[
                "cognitive_mode"
            ] = "stabilization"

        self.control_state[
            "exploration_rate"
        ] = max(
            self.control_state.get(
                "exploration_rate",
                0.0
            ),
            MIN_EXPLORATION_RATE
        )

        self.control_state[
            "reasoning_depth_limit"
        ] = int(
            min(
                max(
                    self.control_state.get(
                        "reasoning_depth_limit",
                        8
                    ),
                    MIN_REASONING_DEPTH_LIMIT
                ),
                MAX_REASONING_DEPTH_LIMIT
            )
        )

        if self.current_decision is not None:

            if self.current_decision.max_reasoning_depth is not None:

                self.control_state[
                    "reasoning_depth_limit"
                ] = min(
                    self.control_state.get(
                        "reasoning_depth_limit",
                        MIN_REASONING_DEPTH_LIMIT,
                    ),
                    max(
                        1,
                        int(
                            self.current_decision.max_reasoning_depth
                        ),
                    ),
                )

            if not self.current_decision.enable_strategy_evolution:

                self.control_state[
                    "mutation_rate"
                ] = 0.0

                self.control_state[
                    "exploration_rate"
                ] = min(
                    self.control_state.get(
                        "exploration_rate",
                        MIN_EXPLORATION_RATE,
                    ),
                    0.10,
                )

            self.control_state[
                "meta_action"
            ] = self.current_decision.action

            self.control_state[
                "shutdown_mode"
            ] = self.current_decision.shutdown_mode

        # =================================================
        # STORE HISTORY
        # =================================================

        self.control_history.append(

            self.control_state.copy()
        )

        return self.control_state

    # =====================================================
    # EXECUTIVE INTERVENTION
    # =====================================================

    def executive_intervention(

        self,

        recursive_report
    ):

        reasoning_depth = recursive_report.get(
            "reasoning_depth",
            0
        )

        intervention = None

        if reasoning_depth >= 18:

            intervention = {

                "intervention_id":
                str(uuid.uuid4()),

                "intervention_type":
                "reduce_recursive_depth",

                "executive_action":
                "stabilize_runtime",

                "timestamp":
                str(datetime.utcnow())
            }

        elif reasoning_depth <= 3:

            intervention = {

                "intervention_id":
                str(uuid.uuid4()),

                "intervention_type":
                "increase_exploration",

                "executive_action":
                "expand_reasoning",

                "timestamp":
                str(datetime.utcnow())
            }

        if intervention:

            self.executive_interventions.append(
                intervention
            )

        return intervention

    # =====================================================
    # RECURSIVE REGULATION
    # =====================================================

    def recursive_regulation_cycle(

        self,

        control_state
    ):

        regulation = {

            "regulation_id":
            str(uuid.uuid4()),

            "control_snapshot":
            control_state.copy(),

            "regulation_depth":

            len(
                self.recursive_regulation
            ) + 1,

            "regulation_state":
            "adaptive_recursive",

            "timestamp":
            str(datetime.utcnow())
        }

        self.recursive_regulation.append(
            regulation
        )

        return regulation

    # =====================================================
    # BUILD REGULATION GRAPH
    # =====================================================

    def build_regulation_graph(

        self,

        control_state,

        uncertainty,

        energy_pressure
    ):

        node = RegulationNode(

            node_id=str(uuid.uuid4()),

            exploration_rate=

            control_state.get(
                "exploration_rate"
            ),

            mutation_rate=

            control_state.get(
                "mutation_rate"
            ),

            reasoning_depth_limit=

            control_state.get(
                "reasoning_depth_limit"
            ),

            uncertainty_level=
            uncertainty,

            energy_pressure=
            energy_pressure,

            regulation_mode=

            control_state.get(
                "cognitive_mode"
            )
        )

        self.regulation_graph.append(
            node
        )

        return node

    # =====================================================
    # CONSOLIDATE CONTROL POLICY
    # =====================================================

    def consolidate_control_policy(

        self,

        control_state
    ):

        policy = {

            "policy_id":
            str(uuid.uuid4()),

            "policy":
            control_state.copy(),

            "policy_type":
            "executive_regulation",

            "timestamp":
            str(datetime.utcnow())
        }

        self.policy_memory.append(
            policy
        )

        return policy

    # =====================================================
    # RUN CONTROL CYCLE
    # =====================================================

    def run_control_cycle(

        self,

        recursive_report
    ):

        uncertainty = (
            self.estimate_uncertainty(
                recursive_report
            )
        )

        energy_pressure = (
            self.estimate_energy_pressure(
                recursive_report
            )
        )

        control_state = (
            self.adapt_control(
                recursive_report
            )
        )

        intervention = (
            self.executive_intervention(
                recursive_report
            )
        )

        recursive_regulation = (

            self.recursive_regulation_cycle(
                control_state
            )
        )

        regulation_graph = (

            self.build_regulation_graph(

                control_state,

                uncertainty,

                energy_pressure
            )
        )

        policy = (

            self.consolidate_control_policy(
                control_state
            )
        )

        return {

            "control_state":
            control_state,

            "uncertainty":
            uncertainty,

            "energy_pressure":
            energy_pressure,

            "intervention":
            intervention,

            "recursive_regulation":
            recursive_regulation,

            "regulation_graph":
            regulation_graph,

            "policy":
            policy,

            "timestamp":
            str(datetime.utcnow())
        }

    # =====================================================
    # GET CONTROL STATE
    # =====================================================

    def get_control_state(self):

        return self.control_state

    # =====================================================
    # BUILD REPORT
    # =====================================================

    def build_report(self):

        return {

            "control_state":
            self.control_state,

            "control_history":
            len(self.control_history),

            "regulation_graph":
            len(self.regulation_graph),

            "executive_interventions":

            len(
                self.executive_interventions
            ),

            "overload_events":
            len(self.overload_events),

            "policy_memory":
            len(self.policy_memory),

            "recursive_regulation":
            len(self.recursive_regulation),

            "current_decision":
            (
                self.current_decision.as_report()
                if self.current_decision is not None
                else None
            ),

            "decision_history":
            len(self.decision_history)
        }

    # =====================================================
    # PRINT CONTROL STATE
    # =====================================================

    def print_control_state(

        self,

        control_state
    ):

        print("\n==================================================")
        print("NEXRYN :: META CONTROLLER")
        print("==================================================\n")

        print(control_state)
