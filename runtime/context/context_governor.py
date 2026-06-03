# ============================================
# NEXRYN RECURSIVE CONTEXT GOVERNOR
# ============================================

from datetime import datetime
import uuid
import math


# ============================================
# CONTEXT GOVERNOR
# ============================================

class ContextGovernor:

    # ========================================
    # INITIALIZE GOVERNOR
    # ========================================

    def __init__(self):

        # ====================================
        # GOVERNOR STATE
        # ====================================

        self.governor_state = {

            "governor_mode":
            "recursive_semantic_governance",

            "runtime_stability":
            "stable",

            "overload_protection":
            "enabled",

            "recursive_protection":
            "enabled",

            "semantic_arbitration":
            "enabled",

            "adaptive_stabilization":
            "enabled",

            "emergency_recovery":
            "enabled",

            "pressure_level":
            "normal",

            "governance_cycles":
            0,

            "last_intervention":
            None
        }

        # ====================================
        # GOVERNANCE LIMITS
        # ====================================

        self.max_active_contexts = 64

        self.max_dormant_contexts = 256

        self.max_context_history = 512

        self.max_recursive_depth = 12

        self.max_graph_edges = 4000

        self.max_memory_pressure = 0.85

        # ====================================
        # STABILIZATION POLICIES
        # ====================================

        self.stabilization_policies = {

            "emergency_freeze":
            True,

            "semantic_pruning":
            True,

            "recursive_halt":
            True,

            "adaptive_throttling":
            True,

            "history_compression":
            True,

            "reactivation_control":
            True
        }

        # ====================================
        # GOVERNANCE HISTORY
        # ====================================

        self.governance_history = []

        # ====================================
        # GOVERNANCE EVENTS
        # ====================================

        self.governance_events = []

        # ====================================
        # RECURSIVE EVENTS
        # ====================================

        self.recursive_events = []

        # ====================================
        # PRESSURE HISTORY
        # ====================================

        self.pressure_history = []

        # ====================================
        # STABILITY HISTORY
        # ====================================

        self.stability_history = []

        # ====================================
        # DEADLOCK HISTORY
        # ====================================

        self.deadlock_history = []

        # ====================================
        # GOVERNANCE GRAPH
        # ====================================

        self.governance_graph = {

            "nodes": [],
            "edges": []
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

        self.governance_events.append(
            event
        )

        return event

    # ========================================
    # ANALYZE PRESSURE
    # ========================================

    def analyze_pressure(

        self,

        context_manager
    ):

        active_count = len(
            context_manager.active_contexts
        )

        dormant_count = len(
            context_manager.dormant_contexts
        )

        history_count = len(
            context_manager.context_history
        )

        graph_edges = len(

            context_manager
            .context_graph
            .get("edges", [])
        )

        importance_density = sum(

            context_manager.context_importance.values()
        )

        pressure_score = round(

            (
                active_count * 1.0
                +
                dormant_count * 0.30
                +
                history_count * 0.10
                +
                graph_edges * 0.02
                +
                importance_density * 0.05
            )
            /
            100,

            4
        )

        if pressure_score >= 0.90:

            pressure_level = "critical"

        elif pressure_score >= 0.70:

            pressure_level = "high"

        elif pressure_score >= 0.45:

            pressure_level = "medium"

        else:

            pressure_level = "normal"

        analysis = {

            "active_contexts":
            active_count,

            "dormant_contexts":
            dormant_count,

            "history_size":
            history_count,

            "graph_edges":
            graph_edges,

            "importance_density":
            round(
                importance_density,
                4
            ),

            "pressure_score":
            pressure_score,

            "pressure_level":
            pressure_level,

            "timestamp":
            str(datetime.utcnow())
        }

        self.pressure_history.append(
            analysis
        )

        self.governor_state[
            "pressure_level"
        ] = pressure_level

        return analysis

    # ========================================
    # EMERGENCY COMPRESSION
    # ========================================

    def emergency_compression(

        self,

        context_manager
    ):

        frozen = []

        active_count = len(

            context_manager.active_contexts
        )

        overflow = max(

            0,

            active_count

            -

            self.max_active_contexts
        )

        sorted_contexts = sorted(

            context_manager
            .active_contexts
            .items(),

            key=lambda item:

            context_manager
            .context_importance
            .get(

                item[0],
                0.0
            )
        )

        for key, _ in sorted_contexts[:overflow]:

            context_manager.freeze_context(
                key
            )

            frozen.append(key)

        intervention = {

            "intervention":
            "semantic_emergency_compression",

            "frozen_contexts":
            frozen,

            "frozen_count":
            len(frozen),

            "timestamp":
            str(datetime.utcnow())
        }

        self.governance_history.append(
            intervention
        )

        self.governor_state[
            "last_intervention"
        ] = intervention

        self.register_event(

            "emergency_compression",

            intervention
        )

        return intervention

    # ========================================
    # RECURSIVE PROTECTION
    # ========================================

    def recursive_protection(

        self,

        recursive_depth
    ):

        recursive_load = round(

            recursive_depth
            /
            max(
                self.max_recursive_depth,
                1
            ),

            4
        )

        safe = (

            recursive_depth
            <
            self.max_recursive_depth
        )

        protection = {

            "recursive_depth":
            recursive_depth,

            "recursive_load":
            recursive_load,

            "max_recursive_depth":
            self.max_recursive_depth,

            "safe":
            safe,

            "timestamp":
            str(datetime.utcnow())
        }

        self.recursive_events.append(
            protection
        )

        if not safe:

            intervention = {

                "intervention":
                "recursive_shutdown",

                "recursive_depth":
                recursive_depth,

                "priority":
                "critical",

                "timestamp":
                str(datetime.utcnow())
            }

            self.governance_history.append(
                intervention
            )

            self.governor_state[
                "runtime_stability"
            ] = "critical"

            self.governor_state[
                "last_intervention"
            ] = intervention

            self.register_event(

                "recursive_shutdown",

                intervention
            )

        return protection

    # ========================================
    # DETECT DEADLOCKS
    # ========================================

    def detect_deadlocks(

        self,

        context_manager
    ):

        graph_edges = len(

            context_manager
            .context_graph
            .get("edges", [])
        )

        active_count = len(

            context_manager.active_contexts
        )

        deadlock_detected = (

            graph_edges
            >
            max(
                active_count * 20,
                1
            )
        )

        deadlock_report = {

            "deadlock_detected":
            deadlock_detected,

            "graph_edges":
            graph_edges,

            "active_contexts":
            active_count,

            "timestamp":
            str(datetime.utcnow())
        }

        self.deadlock_history.append(
            deadlock_report
        )

        if deadlock_detected:

            self.governor_state[
                "runtime_stability"
            ] = "degraded"

        return deadlock_report

    # ========================================
    # COMPRESS HISTORY
    # ========================================

    def compress_history(

        self,

        context_manager
    ):

        history_size = len(

            context_manager.context_history
        )

        if history_size <= self.max_context_history:

            return {

                "compressed":
                False,

                "history_size":
                history_size
            }

        retained = context_manager.context_history[
            -self.max_context_history:
        ]

        removed = (

            history_size

            -

            self.max_context_history
        )

        context_manager.context_history = retained

        intervention = {

            "intervention":
            "history_compression",

            "removed_entries":
            removed,

            "remaining_entries":
            len(retained),

            "timestamp":
            str(datetime.utcnow())
        }

        self.governance_history.append(
            intervention
        )

        self.governor_state[
            "last_intervention"
        ] = intervention

        self.register_event(

            "history_compression",

            intervention
        )

        return intervention

    # ========================================
    # STABILIZATION ANALYSIS
    # ========================================

    def stabilization_analysis(

        self,

        pressure_analysis,

        recursive_analysis,

        deadlock_report
    ):

        stability_score = 1.0

        stability_score -= min(

            pressure_analysis[
                "pressure_score"
            ],

            1.0
        ) * 0.50

        stability_score -= (

            recursive_analysis[
                "recursive_load"
            ] * 0.30
        )

        if deadlock_report[
            "deadlock_detected"
        ]:

            stability_score -= 0.40

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

        self.governor_state[
            "runtime_stability"
        ] = stability_state

        return report

    # ========================================
    # BUILD GOVERNANCE GRAPH
    # ========================================

    def build_governance_graph(self):

        nodes = []
        edges = []

        for index, event in enumerate(

            self.governance_events[-25:]
        ):

            nodes.append({

                "node_id":
                index,

                "event":
                event.get(
                    "event_type"
                )
            })

            if index > 0:

                edges.append({

                    "source":
                    index - 1,

                    "target":
                    index,

                    "relation":
                    "governance_transition"
                })

        self.governance_graph = {

            "nodes":
            nodes,

            "edges":
            edges
        }

        return self.governance_graph

    # ========================================
    # GOVERN CONTEXT SYSTEM
    # ========================================

    def govern(

        self,

        context_manager,

        recursive_depth=0
    ):

        # ====================================
        # PRESSURE ANALYSIS
        # ====================================

        pressure_analysis = (

            self.analyze_pressure(
                context_manager
            )
        )

        # ====================================
        # RECURSIVE PROTECTION
        # ====================================

        recursive_analysis = (

            self.recursive_protection(
                recursive_depth
            )
        )

        # ====================================
        # DEADLOCK DETECTION
        # ====================================

        deadlock_report = (

            self.detect_deadlocks(
                context_manager
            )
        )

        # ====================================
        # HISTORY COMPRESSION
        # ====================================

        history_report = (

            self.compress_history(
                context_manager
            )
        )

        # ====================================
        # EMERGENCY ACTIONS
        # ====================================

        emergency_report = None

        if pressure_analysis[

            "pressure_level"

        ] in [

            "high",
            "critical"
        ]:

            emergency_report = (

                self.emergency_compression(
                    context_manager
                )
            )

        # ====================================
        # STABILIZATION
        # ====================================

        stabilization_report = (

            self.stabilization_analysis(

                pressure_analysis,

                recursive_analysis,

                deadlock_report
            )
        )

        # ====================================
        # GOVERNANCE GRAPH
        # ====================================

        governance_graph = (

            self.build_governance_graph()
        )

        # ====================================
        # GOVERNANCE CYCLE
        # ====================================

        self.governor_state[
            "governance_cycles"
        ] += 1

        governance_report = {

            "pressure_analysis":
            pressure_analysis,

            "recursive_analysis":
            recursive_analysis,

            "deadlock_report":
            deadlock_report,

            "history_report":
            history_report,

            "emergency_report":
            emergency_report,

            "stabilization_report":
            stabilization_report,

            "governance_graph":
            governance_graph,

            "governor_state":
            self.governor_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "governance_cycle",

            governance_report
        )

        return governance_report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "governor_state":
            self.governor_state,

            "governance_cycles":
            len(self.governance_history),

            "governance_events":
            len(self.governance_events),

            "recursive_events":
            len(self.recursive_events),

            "pressure_history":
            len(self.pressure_history),

            "stability_history":
            len(self.stability_history),

            "deadlock_history":
            len(self.deadlock_history),

            "governance_graph_nodes":
            len(
                self.governance_graph.get(
                    "nodes",
                    []
                )
            ),

            "governance_graph_edges":
            len(
                self.governance_graph.get(
                    "edges",
                    []
                )
            ),

            "last_intervention":

            self.governor_state.get(
                "last_intervention"
            )
        }


# ============================================
# GLOBAL GOVERNOR
# ============================================

context_governor = (
    ContextGovernor()
)