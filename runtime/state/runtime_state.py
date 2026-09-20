# ============================================
# NEXRYN RUNTIME STATE
# ============================================

from datetime import datetime
from dataclasses import asdict, is_dataclass

from runtime.context import (
    context_bus
)

from runtime.context import (
    context_delta_engine
)

from runtime.profiling import telemetry
from runtime.security import memory_access_guard, security_reporter
from runtime.execution.execution_planner import execution_planner
from runtime.world_governance import WorldState


# ============================================
# RUNTIME STATE
# ============================================

class RuntimeState:

    def __init__(self):

        # ====================================
        # EXECUTION STAGES
        # ====================================

        self.current_stage = None

        self.completed_stages = []

        self.failed_stages = []

        # ====================================
        # RUNTIME CONTEXT
        # ====================================

        self.context = {}

        # ====================================
        # OBSERVATIONAL TASK PROFILE
        # ====================================

        self._current_task_profile = None

        self._current_cognitive_cost = None

        self._current_reasoning_budget = None

        self.enabled_tools = []

        self.disabled_tools = []

        self.runtime_tool_requests = {}

        self.cache_metrics = None

        self.concept_version_hashes = {}

        self.reused_concepts = []

        self.invalidated_concepts = []

        self.early_exit_triggered = False

        self.current_meta_decision = None

        self.meta_action_history = []

        self.meta_decision_reason = None

        self.meta_reason = None

        self.world_governance_state = WorldState()

        self.world_governance_report = None

        self.execution_time = 0.0

        self.slowest_modules = []

        # ====================================
        # ACTIVE ENGINE
        # ====================================

        self.active_engine = None

        # ====================================
        # EXECUTION STATUS
        # ====================================

        self.is_running = False

        self.has_failed = False

        # ====================================
        # TRACE LOGS
        # ====================================

        self.logs = []

        # ====================================
        # RUNTIME EVENTS
        # ====================================

        self.runtime_events = []

        # ====================================
        # DELTA ENGINE
        # ====================================

        self.delta_engine = (
            context_delta_engine
        )

        # ====================================
        # EXECUTION METRICS
        # ====================================

        self.metrics = {

            "runtime_cycles":
            0,

            "context_updates":
            0,

            "stage_transitions":
            0,

            "runtime_errors":
            0,

            "runtime_health":
            "stable"
        }

        # ====================================
        # RUNTIME TIMING
        # ====================================

        self.start_timestamp = None

        self.stop_timestamp = None

    @property
    def current_task_profile(self):

        return self._current_task_profile

    @property
    def current_cognitive_cost(self):

        return self._current_cognitive_cost

    @property
    def current_reasoning_budget(self):

        return self._current_reasoning_budget

    def set_observational_profile(

        self,

        task_profile=None,

        cognitive_cost=None
    ):

        self._current_task_profile = task_profile

        self._current_cognitive_cost = cognitive_cost

    def apply_reasoning_budget(

        self,

        budget
    ):

        self._current_reasoning_budget = budget

        self.context[
            "current_reasoning_budget"
        ] = budget

        max_contexts = getattr(
            budget,
            "max_contexts",
            None
        )

        if max_contexts is not None:

            context_bus.compress_contexts(
                max_active=max(
                    1,
                    int(max_contexts)
                )
            )

        return budget

    def apply_meta_decision(

        self,

        decision
    ):

        if decision is None:
            return None

        if hasattr(decision, "as_report"):
            decision_report = decision.as_report()
        elif is_dataclass(decision):
            decision_report = asdict(decision)
        elif isinstance(decision, dict):
            decision_report = dict(decision)
        else:
            decision_report = {
                "action": str(decision),
                "reason": "unstructured_meta_decision",
            }

        self.current_meta_decision = decision_report
        self.meta_decision_reason = decision_report.get("reason")
        self.meta_reason = self.meta_decision_reason
        self.meta_action_history.append({
            "action": decision_report.get("action"),
            "reason": decision_report.get("reason"),
            "timestamp": str(datetime.utcnow()),
        })
        self.meta_action_history = self.meta_action_history[-50:]

        self.context[
            "current_meta_decision"
        ] = decision_report
        self.context[
            "meta_decision_reason"
        ] = self.meta_decision_reason
        self.context[
            "meta_reason"
        ] = self.meta_reason
        self.context[
            "meta_action_history"
        ] = list(self.meta_action_history)
        self.context[
            "meta_executive_report"
        ] = {
            "action": decision_report.get("action"),
            "reason": decision_report.get("reason"),
            "confidence": decision_report.get("confidence"),
            "max_reasoning_depth":
            decision_report.get("max_reasoning_depth"),
            "max_active_routes":
            decision_report.get("max_active_routes"),
            "enable_memory_reuse":
            decision_report.get("enable_memory_reuse"),
            "enable_localization":
            decision_report.get("enable_localization"),
            "enable_governance":
            decision_report.get("enable_governance"),
            "enable_self_improvement":
            decision_report.get("enable_self_improvement"),
            "enable_strategy_evolution":
            decision_report.get("enable_strategy_evolution"),
            "shutdown_mode": decision_report.get("shutdown_mode"),
        }

        return decision_report

    def is_meta_action_enabled(

        self,

        action
    ):

        decision = self.current_meta_decision
        if not isinstance(decision, dict):
            decision = self.context.get(
                "current_meta_decision",
                {},
            )
        if not isinstance(decision, dict):
            return False

        action = str(action)
        if decision.get("action") == action:
            return True

        flag_by_action = {
            "RUN_LOCALIZATION": "enable_localization",
            "ESCALATE_TO_GOVERNANCE": "enable_governance",
            "RUN_SELF_IMPROVEMENT": "enable_self_improvement",
            "RUN_STRATEGY_EVOLUTION": "enable_strategy_evolution",
        }
        flag = flag_by_action.get(action)
        return bool(flag and decision.get(flag) is True)

    def is_action_enabled(

        self,

        action
    ):

        return self.is_meta_action_enabled(action)

    def apply_tool_selection(

        self,

        selection
    ):

        self.enabled_tools = list(
            getattr(selection, "enabled_tools", [])
        )

        self.disabled_tools = list(
            getattr(selection, "disabled_tools", [])
        )

        self.context[
            "enabled_tools"
        ] = self.enabled_tools

        self.context[
            "disabled_tools"
        ] = self.disabled_tools

        self.runtime_tool_requests = {
            tool_name: {
                "tool_name": tool_name,
                "request_state": "REQUESTED",
                "requested_by": "tool_selection",
            }
            for tool_name in self.enabled_tools
        }
        plan_result = execution_planner.plan(
            enabled_tools=self.enabled_tools,
            runtime_context={
                **self.context,
                "enabled_tools": self.enabled_tools,
                "disabled_tools": self.disabled_tools,
                "tool_selection_report": {
                    "enabled_tools": self.enabled_tools,
                    "disabled_tools": self.disabled_tools,
                    "selected_tools": self.enabled_tools,
                },
            },
        )
        canonical_plan = plan_result.get("canonical_execution_plan", {})
        plan_requests = {
            **plan_result.get("dependency_requests", {}),
            **plan_result.get("process_requests", {}),
            **plan_result.get("causal_requests", {}),
        }
        if plan_requests:
            self.runtime_tool_requests = {
                **self.runtime_tool_requests,
                **plan_requests,
            }
        self.context["canonical_execution_plan"] = canonical_plan
        self.context["EXECUTION_PLAN_REPORT"] = plan_result.get(
            "EXECUTION_PLAN_REPORT",
            {},
        )
        self.context["CANONICAL_EXECUTION_PLAN_REPORT"] = canonical_plan
        self.context["EXECUTION_PLAN_RUNTIME_HANDOFF"] = (
            execution_planner.consume_finalized_plan(
                canonical_plan,
                runtime_context=self.context,
            )
        )

        self.context[
            "runtime_tool_requests"
        ] = self.runtime_tool_requests

        if "dependency_reasoning" in self.runtime_tool_requests:

            self.context[
                "dependency_lifecycle_report"
            ] = {
                **self.context.get("dependency_lifecycle_report", {}),
                "system": "dependency_runtime",
                "report_state": "pending",
                "dependency_activation_state": "REQUESTED",
                "dependency_requested_by": "tool_selection",
                "dependency_chains_executed": 0,
                "dependency_outputs_generated": 0,
            }

        return selection

    def is_tool_enabled(

        self,

        tool_name
    ):

        tool_name = str(tool_name)

        if tool_name in set(self.disabled_tools):

            return False

        if self.enabled_tools:

            return tool_name in set(self.enabled_tools)

        return True

    def get_budget_value(

        self,

        name,

        default=None
    ):

        if self._current_reasoning_budget is None:

            return default

        if hasattr(
            self._current_reasoning_budget,
            name
        ):

            return getattr(
                self._current_reasoning_budget,
                name
            )

        return default

    def update_cache_metrics(

        self,

        cache_metrics
    ):

        self.cache_metrics = cache_metrics

        self.context[
            "cache_metrics"
        ] = cache_metrics

        return cache_metrics

    def record_cache_hit(

        self,

        concept_name=None
    ):

        if concept_name and concept_name not in self.reused_concepts:

            self.reused_concepts.append(concept_name)

        self.context[
            "reused_concepts"
        ] = self.reused_concepts

    def record_cache_miss(

        self,

        concept_name=None
    ):

        if concept_name:

            self.context.setdefault(
                "cache_missed_concepts",
                []
            )

            if concept_name not in self.context[
                "cache_missed_concepts"
            ]:

                self.context[
                    "cache_missed_concepts"
                ].append(concept_name)

    def record_invalidation(

        self,

        concept_name=None
    ):

        if concept_name and concept_name not in self.invalidated_concepts:

            self.invalidated_concepts.append(concept_name)

        self.context[
            "invalidated_concepts"
        ] = self.invalidated_concepts

    def is_concept_stable(

        self,

        concept_name,

        concept_version_hash=None
    ):

        previous_hash = self.concept_version_hashes.get(
            concept_name
        )

        if concept_version_hash is None:

            return previous_hash is not None

        stable = previous_hash == concept_version_hash

        self.concept_version_hashes[
            concept_name
        ] = concept_version_hash

        self.context[
            "concept_version_hashes"
        ] = self.concept_version_hashes

        return stable

    def apply_early_exit(

        self,

        decision
    ):

        self.early_exit_triggered = bool(
            getattr(decision, "should_stop", False)
        )

        self.context[
            "early_exit_triggered"
        ] = self.early_exit_triggered

        self.context[
            "early_exit_decision"
        ] = decision

        return decision

    def apply_world_governance_report(

        self,

        report
    ):

        if not isinstance(report, dict):

            return None

        self.world_governance_report = report

        self.context[
            "WORLD_GOVERNANCE_REPORT"
        ] = report.get(
            "WORLD_GOVERNANCE_REPORT",
            report,
        )

        self.context[
            "world_governance_report"
        ] = report

        state_report = report.get(
            "world_state"
        )

        if state_report is not None:

            self.context[
                "world_governance_state"
            ] = state_report

        return report

    def update_performance_state(

        self,

        execution_time=0.0,

        slowest_modules=None
    ):

        self.execution_time = execution_time

        self.slowest_modules = list(
            slowest_modules or []
        )

        self.context[
            "execution_time"
        ] = self.execution_time

        self.context[
            "slowest_modules"
        ] = self.slowest_modules

        telemetry.record(
            "runtime",
            "execution_time",
            execution_time,
        )

    # ========================================
    # BULK UPDATE CONTEXT
    # ========================================

    def bulk_update_context(

        self,

        updates
    ):

        # ====================================
        # SAFE NORMALIZATION
        # ====================================

        if updates is None:

            return {

                "bulk_update_state":
                "skipped",

                "reason":
                "updates_none"
            }

        if not isinstance(
            updates,
            dict
        ):

            return {

                "bulk_update_state":
                "invalid",

                "reason":
                "updates_not_dict"
            }

        # ====================================
        # CONTEXT STORAGE
        # ====================================

        if not hasattr(
            self,
            "context"
        ):

            self.context = {}

        if self.context is None:

            self.context = {}

        if not isinstance(
            self.context,
            dict
        ):

            self.context = {}

        # ====================================
        # BULK UPDATE
        # ====================================

        for key, value in updates.items():

            self.context[key] = value

        # ====================================
        # UPDATE METADATA
        # ====================================

        if not hasattr(
            self,
            "update_history"
        ):

            self.update_history = []

        self.update_history.append({

            "updated_keys":
            list(updates.keys()),

            "update_count":
            len(updates),

            "timestamp":
            str(datetime.utcnow())
        })

        telemetry.record(
            "context",
            "bulk_update_count",
            len(updates),
        )

        # ====================================
        # FINAL REPORT
        # ====================================

        return {

            "bulk_update_state":
            "completed",

            "updated_keys":
            len(updates),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # REGISTER EVENT
    # ========================================

    def register_event(

        self,

        event_type,

        metadata=None
    ):

        self.runtime_events.append({

            "event":
            event_type,

            "metadata":
            metadata or {},

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

    # ========================================
    # START RUNTIME
    # ========================================

    def start(self):

        self.is_running = True

        self.start_timestamp = (
            datetime.utcnow()
        )

        self.metrics[
            "runtime_cycles"
        ] += 1

        self.logs.append(
            "RUNTIME STARTED"
        )

        self.register_event(
            "runtime_started"
        )

        telemetry.record(
            "runtime",
            "started",
            1,
        )

    # ========================================
    # STOP RUNTIME
    # ========================================

    def stop(self):

        self.is_running = False

        self.stop_timestamp = (
            datetime.utcnow()
        )

        self.logs.append(
            "RUNTIME STOPPED"
        )

        self.register_event(
            "runtime_stopped"
        )

        telemetry.record(
            "runtime",
            "stopped",
            1,
        )

    # ========================================
    # SET ACTIVE ENGINE
    # ========================================

    def set_active_engine(

        self,

        engine_name
    ):

        self.active_engine = engine_name

        self.logs.append(
            f"ACTIVE ENGINE :: {engine_name}"
        )

        self.register_event(

            "engine_activation",

            {
                "engine":
                engine_name
            }
        )

    # ========================================
    # ENTER STAGE
    # ========================================

    def set_stage(

        self,

        stage_name
    ):

        self.current_stage = stage_name

        self.metrics[
            "stage_transitions"
        ] += 1

        self.logs.append(
            f"ENTER STAGE :: {stage_name}"
        )

        self.register_event(

            "stage_entered",

            {
                "stage":
                stage_name
            }
        )

        telemetry.record(
            "stage",
            "entered",
            stage_name,
        )

    # ========================================
    # COMPLETE STAGE
    # ========================================

    def complete_stage(

        self,

        stage_name
    ):

        self.completed_stages.append(
            stage_name
        )

        self.logs.append(
            f"COMPLETE STAGE :: {stage_name}"
        )

        self.register_event(

            "stage_completed",

            {
                "stage":
                stage_name
            }
        )

        telemetry.record(
            "stage",
            "completed",
            stage_name,
        )

    # ========================================
    # FAIL STAGE
    # ========================================

    def fail_stage(

        self,

        stage_name
    ):

        self.failed_stages.append(
            stage_name
        )

        self.has_failed = True

        self.metrics[
            "runtime_errors"
        ] += 1

        self.metrics[
            "runtime_health"
        ] = "degraded"

        self.logs.append(
            f"FAILED STAGE :: {stage_name}"
        )

        self.register_event(

            "stage_failed",

            {
                "stage":
                stage_name
            }
        )

        telemetry.record(
            "stage",
            "failed",
            stage_name,
        )

    # ========================================
    # UPDATE CONTEXT
    # ========================================

    def update_context(

        self,

        key,

        value,

        priority="medium"
    ):

        if key in {
            "locked_truth",
            "locked_truths",
            "locked_truth_memory",
        }:
            decision = memory_access_guard.check_access(
                "locked_truth_memory",
                "write",
                {
                    "key": key,
                    "operation": "write",
                },
            )
            self.context[
                "SECURITY_REPORT"
            ] = security_reporter.build_report()
            if decision.permission == "DENY":
                self.context[
                    "last_security_decision"
                ] = decision.as_dict()
                return {
                    "context_update_state": "denied_by_security",
                    "security_decision": decision.as_dict(),
                }

        # ====================================
        # STRUCTURED CONTEXT STORAGE
        # ====================================

        self.context[key] = {

            "value":
            value,

            "priority":
            priority,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        # ====================================
        # DELTA TRACKING
        # ====================================

        self.delta_engine.detect_changes(
            self.context
        )

        # ====================================
        # METRICS
        # ====================================

        self.metrics[
            "context_updates"
        ] += 1

        telemetry.record(
            "context",
            "update",
            key,
        )

        # ====================================
        # CONTEXT BUS
        # ====================================

        context_bus.publish(

            key,

            value,

            priority
        )

        # ====================================
        # AUTO COMPRESSION
        # ====================================

        context_bus.compress_contexts(
            max_active=64
        )

        # ====================================
        # LOGS
        # ====================================

        self.logs.append(

            f"CONTEXT UPDATE :: {key}"
        )


    # ============================================
    # SET FULL CONTEXT
    # ============================================

    def set_context(

        self,

        context
    ):

        self.context = {}

        for key, value in context.items():

            self.context[key] = {

                "value":
                value,

                "priority":
                "medium"
            }

   
    # ========================================
    # GET CONTEXT VALUE
    # ========================================

    def get_context_value(

        self,

        key,

        default=None
    ):

        if key not in self.context:

            return default

        stored_value = self.context.get(

            key,

            {}
        )

        if isinstance(

            stored_value,

            dict
        ) and "value" in stored_value:

            return stored_value["value"]

        return stored_value

    # ========================================
    # RUNTIME HEALTH CHECK
    # ========================================

    def health_check(self):

        healthy = True

        if len(self.failed_stages) > 3:

            healthy = False

        if self.metrics[
            "runtime_errors"
        ] > 5:

            healthy = False

        return {

            "healthy":
            healthy,

            "runtime_health":
            self.metrics[
                "runtime_health"
            ],

            "failed_stages":
            len(
                self.failed_stages
            ),

            "runtime_errors":
            self.metrics[
                "runtime_errors"
            ]
        }

    # ========================================
    # BUILD RUNTIME REPORT
    # ========================================

    def build_runtime_report(self):

        return {

            "runtime_metrics":
            self.metrics,

            "health":
            self.health_check(),

            "context_count":
            len(
                self.context
            ),

            "events":
            len(
                self.runtime_events
            ),

            "active_engine":
            self.active_engine,

            "current_stage":
            self.current_stage
        }
        
    def get_context(self):

        return self.context

    # ========================================
    # GET DELTA SNAPSHOT
    # ========================================

    def get_delta_snapshot(self):

        return (

            self.delta_engine
            .build_summary()
        )

    def summary(self):

        return {

            "current_stage":
            self.current_stage,

            "active_engine":
            self.active_engine,

            "completed_stages":
            len(
                self.completed_stages
            ),

            "failed_stages":
            len(
                self.failed_stages
            ),

            "is_running":
            self.is_running,

            "has_failed":
            self.has_failed,

            "active_contexts":
            len(
                context_bus.active_contexts
            ),

            "dormant_contexts":
            len(
                context_bus.dormant_contexts
            ),

            "archived_contexts":
            len(
                context_bus.archived_contexts
            ),

            "runtime_health":
            self.metrics[
                "runtime_health"
            ],

            "runtime_cycles":
            self.metrics[
                "runtime_cycles"
            ]
        }
