# ============================================
# NEXRYN CONTEXT HEALTH MONITOR
# ============================================

from datetime import datetime
import uuid
import math

from runtime.context import (
    recursive_depth_governor
)


# ============================================
# CONTEXT HEALTH MONITOR
# ============================================

class ContextHealthMonitor:

    # ========================================
    # INITIALIZE MONITOR
    # ========================================

    def __init__(self):

        # ====================================
        # HEALTH HISTORY
        # ====================================

        self.health_history = []

        # ====================================
        # HEALTH EVENTS
        # ====================================

        self.health_events = []

        # ====================================
        # PRESSURE HISTORY
        # ====================================

        self.pressure_history = []

        # ====================================
        # RECURSIVE HISTORY
        # ====================================

        self.recursive_history = []

        # ====================================
        # LATENCY HISTORY
        # ====================================

        self.latency_history = []

        # ====================================
        # STABILITY HISTORY
        # ====================================

        self.stability_history = []

        # ====================================
        # FAILURE EVENTS
        # ====================================

        self.failure_events = []

        # ====================================
        # RECOVERY EVENTS
        # ====================================

        self.recovery_events = []

        # ====================================
        # MONITOR STATE
        # ====================================

        self.monitor_state = {

            "monitor_mode":
            "recursive_context_health_monitor",

            "pressure_monitoring":
            "enabled",

            "recursive_monitoring":
            "enabled",

            "latency_monitoring":
            "enabled",

            "stability_monitoring":
            "enabled",

            "recovery_tracking":
            "enabled",

            "adaptive_health_analysis":
            "enabled",

            "health_cycles":
            0
        }

        # ====================================
        # HEALTH LIMITS
        # ====================================

        self.health_limits = {

            "max_active_contexts":
            64,

            "max_dormant_contexts":
            256,

            "max_archived_contexts":
            1024,

            "max_graph_edges":
            5000,

            "max_pressure_score":
            0.85,

            "max_recursive_depth":
            12
        }

    # ========================================
    # REGISTER EVENT
    # ========================================

    def register_event(

        self,

        event_type,

        payload
    ):

        event = {

            "event_id":
            str(uuid.uuid4()),

            "event_type":
            event_type,

            "payload":
            payload,

            "timestamp":
            str(datetime.utcnow())
        }

        self.health_events.append(
            event
        )

        return event

    # ========================================
    # ANALYZE PRESSURE
    # ========================================

    def analyze_pressure(

        self,

        context_bus
    ):

        if context_bus is None:

            return {

                "active_contexts": 0,
                "dormant_contexts": 0,
                "archived_contexts": 0,
                "total_contexts": 0,
                "pressure_score": 0.0,
                "pressure_state": "stable",
                "timestamp": str(datetime.utcnow())
            }

        active = len(
            context_bus.active_contexts
        )

        dormant = len(
            context_bus.dormant_contexts
        )

        archived = len(
            context_bus.archived_contexts
        )

        total = (

            active +
            dormant +
            archived
        )

        pressure_score = round(

            min(
                total / 500,
                1.0
            ),

            4
        )

        if pressure_score >= 0.90:

            pressure_state = "critical"

        elif pressure_score >= 0.70:

            pressure_state = "high"

        elif pressure_score >= 0.45:

            pressure_state = "medium"

        else:

            pressure_state = "stable"

        report = {

            "active_contexts":
            active,

            "dormant_contexts":
            dormant,

            "archived_contexts":
            archived,

            "total_contexts":
            total,

            "pressure_score":
            pressure_score,

            "pressure_state":
            pressure_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.pressure_history.append(
            report
        )

        return report

    # ========================================
    # ANALYZE GRAPH HEALTH
    # ========================================

    def analyze_graph_health(

        self,

        context_bus
    ):

        if context_bus is None:

            return {

                "node_count": 0,
                "edge_count": 0,
                "graph_density": 0.0,
                "graph_state": "stable",
                "timestamp": str(datetime.utcnow())
            }

        graph = (
            context_bus.build_context_graph()
        )

        node_count = len(
            graph["nodes"]
        )

        edge_count = len(
            graph["edges"]
        )

        graph_density = round(

            edge_count
            /
            max(node_count, 1),

            4
        )

        if edge_count >= 10000:

            graph_state = "critical"

        elif edge_count >= 5000:

            graph_state = "high"

        else:

            graph_state = "stable"

        report = {

            "node_count":
            node_count,

            "edge_count":
            edge_count,

            "graph_density":
            graph_density,

            "graph_state":
            graph_state,

            "timestamp":
            str(datetime.utcnow())
        }

        return report

    # ========================================
    # ANALYZE RECURSIVE HEALTH
    # ========================================

    def analyze_recursive_health(

        self,

        recursive_depth=0
    ):

        recursive_load = round(

            recursive_depth
            /
            max(

                self.health_limits[
                    "max_recursive_depth"
                ],

                1
            ),

            4
        )

        if recursive_load >= 1.0:

            recursive_state = "critical"

        elif recursive_load >= 0.75:

            recursive_state = "high"

        elif recursive_load >= 0.50:

            recursive_state = "medium"

        else:

            recursive_state = "stable"

        report = {

            "recursive_depth":
            recursive_depth,

            "recursive_load":
            recursive_load,

            "recursive_state":
            recursive_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.recursive_history.append(
            report
        )

        return report

    # ========================================
    # ANALYZE LATENCY
    # ========================================

    def analyze_latency(

        self,

        context_bus
    ):

        if context_bus is None:

            return {

                "estimated_latency": 0.0,
                "latency_state": "low",
                "timestamp": str(datetime.utcnow())
            }

        graph = (
            context_bus.build_context_graph()
        )

        edge_count = len(
            graph["edges"]
        )

        active_contexts = len(
            context_bus.active_contexts
        )

        estimated_latency = round(

            (
                edge_count * 0.001
                +
                active_contexts * 0.005
            ),

            4
        )

        if estimated_latency >= 5:

            latency_state = "critical"

        elif estimated_latency >= 2:

            latency_state = "high"

        elif estimated_latency >= 1:

            latency_state = "medium"

        else:

            latency_state = "low"

        report = {

            "estimated_latency":
            estimated_latency,

            "latency_state":
            latency_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.latency_history.append(
            report
        )

        return report

    # ========================================
    # DETECT FAILURES
    # ========================================

    def detect_failures(

        self,

        pressure_report,

        graph_report,

        recursive_report,

        latency_report
    ):

        failures = []

        if pressure_report[
            "pressure_state"
        ] == "critical":

            failures.append(
                "pressure_overload"
            )

        if graph_report[
            "graph_state"
        ] == "critical":

            failures.append(
                "graph_explosion"
            )

        if recursive_report[
            "recursive_state"
        ] == "critical":

            failures.append(
                "recursive_overflow"
            )

        if latency_report[
            "latency_state"
        ] == "critical":

            failures.append(
                "runtime_latency_collapse"
            )

        report = {

            "failure_count":
            len(failures),

            "failures":
            failures,

            "timestamp":
            str(datetime.utcnow())
        }

        if failures:

            self.failure_events.append(
                report
            )

        return report

    # ========================================
    # RECOVERY ANALYSIS
    # ========================================

    def recovery_analysis(

        self,

        failure_report
    ):

        recovery_actions = []

        for failure in failure_report[
            "failures"
        ]:

            if failure == "pressure_overload":

                recovery_actions.append(
                    "semantic_compression"
                )

            elif failure == "graph_explosion":

                recovery_actions.append(
                    "graph_pruning"
                )

            elif failure == "recursive_overflow":

                recovery_actions.append(
                    "recursive_shutdown"
                )

            elif failure == (

                "runtime_latency_collapse"
            ):

                recovery_actions.append(
                    "latency_throttling"
                )

        report = {

            "recovery_actions":
            recovery_actions,

            "recovery_count":
            len(recovery_actions),

            "timestamp":
            str(datetime.utcnow())
        }

        if recovery_actions:

            self.recovery_events.append(
                report
            )

        return report

    # ========================================
    # STABILITY ANALYSIS
    # ========================================

    def stability_analysis(

        self,

        pressure_report,

        graph_report,

        recursive_report,

        latency_report
    ):

        stability_score = 1.0

        stability_score -= (

            pressure_report[
                "pressure_score"
            ] * 0.35
        )

        stability_score -= min(

            graph_report[
                "graph_density"
            ] / 100,

            0.25
        )

        stability_score -= (

            recursive_report[
                "recursive_load"
            ] * 0.25
        )

        latency_penalty = min(

            latency_report[
                "estimated_latency"
            ] / 10,

            0.15
        )

        stability_score -= latency_penalty

        stability_score = round(

            max(
                stability_score,
                0.0
            ),

            4
        )

        if stability_score >= 0.80:

            stability_state = "stable"

        elif stability_score >= 0.55:

            stability_state = "elevated"

        else:

            stability_state = "critical"

        report = {

            "stability_score":
            stability_score,

            "stability_state":
            stability_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.stability_history.append(
            report
        )

        return report

    # ========================================
    # RUN HEALTH CYCLE
    # ========================================

    def run_health_cycle(

        self,

        context_bus=None
    ):

        # ====================================
        # RECURSIVE DEPTH
        # ====================================

        recursive_summary = (

            recursive_depth_governor
            .build_governor_summary()
        )

        recursive_depth = (

            recursive_summary.get(
                "recursive_depth",
                0
            )
        )

        # ====================================
        # PRESSURE
        # ====================================

        pressure_report = (

            self.analyze_pressure(
                context_bus
            )
        )

        # ====================================
        # GRAPH HEALTH
        # ====================================

        graph_report = (

            self.analyze_graph_health(
                context_bus
            )
        )

        # ====================================
        # RECURSIVE HEALTH
        # ====================================

        recursive_report = (

            self.analyze_recursive_health(
                recursive_depth
            )
        )

        # ====================================
        # LATENCY
        # ====================================

        latency_report = (

            self.analyze_latency(
                context_bus
            )
        )

        # ====================================
        # FAILURES
        # ====================================

        failure_report = (

            self.detect_failures(

                pressure_report,

                graph_report,

                recursive_report,

                latency_report
            )
        )

        # ====================================
        # RECOVERY
        # ====================================

        recovery_report = (

            self.recovery_analysis(
                failure_report
            )
        )

        # ====================================
        # STABILITY
        # ====================================

        stability_report = (

            self.stability_analysis(

                pressure_report,

                graph_report,

                recursive_report,

                latency_report
            )
        )

        # ====================================
        # UPDATE STATE
        # ====================================

        self.monitor_state[
            "health_cycles"
        ] += 1

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "pressure_report":
            pressure_report,

            "graph_report":
            graph_report,

            "recursive_report":
            recursive_report,

            "latency_report":
            latency_report,

            "failure_report":
            failure_report,

            "recovery_report":
            recovery_report,

            "stability_report":
            stability_report,

            "monitor_state":
            self.monitor_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.health_history.append(
            report
        )

        self.register_event(

            "health_cycle",

            report
        )

        return report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "monitor_state":
            self.monitor_state,

            "health_history":
            len(self.health_history),

            "health_events":
            len(self.health_events),

            "pressure_history":
            len(self.pressure_history),

            "recursive_history":
            len(self.recursive_history),

            "latency_history":
            len(self.latency_history),

            "stability_history":
            len(self.stability_history),

            "failure_events":
            len(self.failure_events),

            "recovery_events":
            len(self.recovery_events),

            "latest_health_cycle":

            self.health_history[-1]

            if self.health_history

            else {}
        }


# ============================================
# GLOBAL HEALTH MONITOR
# ============================================

context_health_monitor = (
    ContextHealthMonitor()
)