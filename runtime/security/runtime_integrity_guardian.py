# ============================================
# NEXRYN RUNTIME INTEGRITY GUARDIAN
# ============================================

from datetime import datetime
import uuid


# ============================================
# RUNTIME INTEGRITY GUARDIAN
# ============================================

class RuntimeIntegrityGuardian:

    # ========================================
    # INITIALIZE GUARDIAN
    # ========================================

    def __init__(self):

        # ====================================
        # GUARDIAN STATE
        # ====================================

        self.guardian_state = {

            "guardian_mode":
            "adaptive_runtime_protection",

            "fault_isolation":
            "enabled",

            "corruption_detection":
            "enabled",

            "rollback_protection":
            "enabled",

            "recursive_validation":
            "enabled",

            "quarantine_management":
            "enabled",

            "secure_boundaries":
            "enabled",

            "architecture_integrity":
            "enabled",

            "guardian_stability":
            "stable",

            "guardian_cycles":
            0
        }

        # ====================================
        # HISTORIES
        # ====================================

        self.validation_history = []

        self.corruption_history = []

        self.quarantine_history = []

        self.rollback_history = []

        self.integrity_history = []

        # ====================================
        # RUNTIME LIMITS
        # ====================================

        self.minimum_context_size = 20

        self.maximum_context_size = 500

        # ====================================
        # CRITICAL SYSTEMS
        # ====================================

        self.critical_systems = [

            "executive_brain_report",

            "reasoning_orchestration_report",

            "execution_governor_report",

            "autonomous_planning_report",

            "context_report",

            "memory_report"
        ]

        # ====================================
        # CORRUPTION PATTERNS
        # ====================================

        self.corruption_patterns = [

            "null",

            "undefined",

            "corrupted",

            "broken",

            "invalid",

            "nan"
        ]

    # ========================================
    # NORMALIZE RUNTIME CONTEXT
    # ========================================

    def normalize_runtime_context(

        self,

        runtime_context
    ):

        if runtime_context is None:

            runtime_context = {}

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        return runtime_context

    # ========================================
    # VALIDATE CONTEXT ENTRY
    # ========================================

    def validate_context_entry(

        self,

        key,

        value
    ):

        validation = {

            "key":
            key,

            "valid":
            True,

            "issues":
            []
        }

        # ====================================
        # NONE VALIDATION
        # ====================================

        if value is None:

            validation[
                "valid"
            ] = False

            validation[
                "issues"
            ].append(
                "null_value"
            )

        # ====================================
        # EMPTY STRUCTURES
        # ====================================

        if isinstance(
            value,
            (list, dict, str)
        ):

            if len(value) == 0:

                validation[
                    "issues"
                ].append(
                    "empty_structure"
                )

        # ====================================
        # INVALID NUMBERS
        # ====================================

        if isinstance(
            value,
            float
        ):

            if str(value).lower() == "nan":

                validation[
                    "valid"
                ] = False

                validation[
                    "issues"
                ].append(
                    "nan_detected"
                )

        return validation

    # ========================================
    # ANALYZE RUNTIME INTEGRITY
    # ========================================

    def analyze_runtime_integrity(

        self,

        runtime_context
    ):

        runtime_context = (

            self.normalize_runtime_context(
                runtime_context
            )
        )

        context_size = len(
            runtime_context
        )

        missing_critical = []

        invalid_entries = []

        # ====================================
        # CRITICAL SYSTEM CHECK
        # ====================================

        for system in self.critical_systems:

            if system not in runtime_context:

                missing_critical.append(
                    system
                )

        # ====================================
        # ENTRY VALIDATION
        # ====================================

        for key, value in (

            runtime_context.items()
        ):

            validation = (

                self.validate_context_entry(

                    key,

                    value
                )
            )

            if not validation.get(
                "valid",
                True
            ):

                invalid_entries.append(
                    validation
                )

        # ====================================
        # INTEGRITY VALIDATION
        # ====================================

        integrity_valid = (

            len(missing_critical) == 0

            and

            len(invalid_entries) == 0
        )

        # ====================================
        # CONTEXT STATE
        # ====================================

        if context_size < (

            self.minimum_context_size
        ):

            integrity_state = (
                "underloaded"
            )

        elif context_size < 150:

            integrity_state = (
                "stable"
            )

        elif context_size < (

            self.maximum_context_size
        ):

            integrity_state = (
                "elevated"
            )

        else:

            integrity_state = (
                "critical"
            )

        analysis = {

            "analysis_id":
            str(uuid.uuid4()),

            "integrity_valid":
            integrity_valid,

            "missing_critical":
            missing_critical,

            "invalid_entries":
            invalid_entries,

            "context_size":
            context_size,

            "integrity_state":
            integrity_state,

            "analysis_mode":
            "adaptive_recursive_validation",

            "timestamp":
            str(datetime.utcnow())
        }

        self.validation_history.append(
            analysis
        )

        return analysis

    # ========================================
    # DETECT CORRUPTION
    # ========================================

    def detect_corruption(

        self,

        runtime_context
    ):

        runtime_context = (

            self.normalize_runtime_context(
                runtime_context
            )
        )

        corruption_candidates = []

        # ====================================
        # CONTEXT SCAN
        # ====================================

        for key, value in (

            runtime_context.items()
        ):

            value_string = str(
                value
            ).lower()

            # ================================
            # PATTERN DETECTION
            # ================================

            for pattern in (

                self.corruption_patterns
            ):

                if pattern in value_string:

                    corruption_candidates.append({

                        "candidate_id":
                        str(uuid.uuid4()),

                        "context":
                        key,

                        "pattern":
                        pattern,

                        "corruption_state":
                        "suspected",

                        "timestamp":
                        str(datetime.utcnow())
                    })

                    break

        # ====================================
        # BUILD REPORT
        # ====================================

        corruption_report = {

            "corruption_candidates":
            corruption_candidates,

            "corruption_count":

            len(
                corruption_candidates
            ),

            "corruption_state":

            "detected"

            if len(
                corruption_candidates
            ) > 0

            else

            "stable",

            "corruption_mode":
            "adaptive_corruption_detection",

            "timestamp":
            str(datetime.utcnow())
        }

        self.corruption_history.append(
            corruption_report
        )

        return corruption_report

    # ========================================
    # BUILD QUARANTINE PLAN
    # ========================================

    def build_quarantine_plan(

        self,

        corruption_report
    ):

        if corruption_report is None:

            corruption_report = {}

        quarantine_targets = []

        corruption_candidates = (

            corruption_report.get(
                "corruption_candidates",
                []
            )
        )

        # ====================================
        # BUILD TARGETS
        # ====================================

        for candidate in corruption_candidates:

            if not isinstance(
                candidate,
                dict
            ):

                continue

            quarantine_targets.append({

                "target":
                candidate.get(
                    "context",
                    "unknown"
                ),

                "quarantine_state":
                "pending",

                "priority":
                "high"
            })

        quarantine_plan = {

            "quarantine_targets":
            quarantine_targets,

            "quarantine_count":

            len(
                quarantine_targets
            ),

            "quarantine_mode":
            "adaptive_fault_isolation",

            "timestamp":
            str(datetime.utcnow())
        }

        self.quarantine_history.append(
            quarantine_plan
        )

        return quarantine_plan

    # ========================================
    # BUILD ROLLBACK STRATEGY
    # ========================================

    def build_rollback_strategy(

        self,

        integrity_analysis
    ):

        if integrity_analysis is None:

            integrity_analysis = {}

        integrity_valid = (

            integrity_analysis.get(
                "integrity_valid",
                True
            )
        )

        integrity_state = (

            integrity_analysis.get(
                "integrity_state",
                "stable"
            )
        )

        # ====================================
        # STABLE STATE
        # ====================================

        if integrity_valid:

            rollback_actions = [

                "maintain_runtime_state",

                "preserve_execution_integrity"
            ]

            rollback_state = (
                "standby"
            )

        # ====================================
        # DEGRADED STATE
        # ====================================

        else:

            rollback_actions = [

                "restore_previous_checkpoint",

                "stabilize_runtime_context",

                "preserve_core_systems",

                "reduce_execution_risk"
            ]

            if integrity_state == "critical":

                rollback_actions.append(
                    "activate_safe_mode"
                )

            rollback_state = (
                "active"
            )

        rollback_strategy = {

            "rollback_actions":
            rollback_actions,

            "rollback_depth":

            len(
                rollback_actions
            ),

            "rollback_state":
            rollback_state,

            "rollback_mode":
            "adaptive_runtime_recovery",

            "timestamp":
            str(datetime.utcnow())
        }

        self.rollback_history.append(
            rollback_strategy
        )

        return rollback_strategy

    # ========================================
    # BUILD INTEGRITY GRAPH
    # ========================================

    def build_integrity_graph(

        self,

        integrity_analysis
    ):

        nodes = []

        edges = []

        # ====================================
        # BUILD NODES
        # ====================================

        for index, system in enumerate(

            self.critical_systems
        ):

            nodes.append({

                "node_id":
                index,

                "system":
                system,

                "state":
                "validated"
            })

        # ====================================
        # BUILD EDGES
        # ====================================

        for index in range(

            len(nodes) - 1
        ):

            edges.append({

                "source":
                index,

                "target":
                index + 1,

                "relation":
                "runtime_dependency"
            })

        integrity_graph = {

            "graph_id":
            str(uuid.uuid4()),

            "node_count":
            len(nodes),

            "edge_count":
            len(edges),

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "runtime_integrity_graph",

            "timestamp":
            str(datetime.utcnow())
        }

        return integrity_graph

    # ========================================
    # BUILD INTEGRITY SUMMARY
    # ========================================

    def build_integrity_summary(

        self,

        integrity_analysis,

        corruption_report
    ):

        if integrity_analysis is None:

            integrity_analysis = {}

        if corruption_report is None:

            corruption_report = {}

        corruption_count = (

            corruption_report.get(
                "corruption_count",
                0
            )
        )

        integrity_valid = (

            integrity_analysis.get(
                "integrity_valid",
                True
            )
        )

        guardian_state = (
            "stable"
        )

        if corruption_count > 0:

            guardian_state = (
                "elevated"
            )

        if not integrity_valid:

            guardian_state = (
                "critical"
            )

        summary = {

            "integrity_valid":
            integrity_valid,

            "integrity_state":

            integrity_analysis.get(
                "integrity_state",
                "stable"
            ),

            "missing_critical":

            len(
                integrity_analysis.get(
                    "missing_critical",
                    []
                )
            ),

            "invalid_entries":

            len(
                integrity_analysis.get(
                    "invalid_entries",
                    []
                )
            ),

            "corruption_count":
            corruption_count,

            "guardian_state":
            guardian_state,

            "timestamp":
            str(datetime.utcnow())
        }

        return summary

    # ========================================
    # RUN INTEGRITY CYCLE
    # ========================================

    def run_integrity_cycle(

        self,

        runtime_context
    ):

        runtime_context = (

            self.normalize_runtime_context(
                runtime_context
            )
        )

        # ====================================
        # ANALYSIS
        # ====================================

        integrity_analysis = (

            self.analyze_runtime_integrity(

                runtime_context
            )
        )

        # ====================================
        # CORRUPTION DETECTION
        # ====================================

        corruption_report = (

            self.detect_corruption(

                runtime_context
            )
        )

        # ====================================
        # QUARANTINE
        # ====================================

        quarantine_plan = (

            self.build_quarantine_plan(

                corruption_report
            )
        )

        # ====================================
        # ROLLBACK
        # ====================================

        rollback_strategy = (

            self.build_rollback_strategy(

                integrity_analysis
            )
        )

        # ====================================
        # GRAPH
        # ====================================

        integrity_graph = (

            self.build_integrity_graph(

                integrity_analysis
            )
        )

        # ====================================
        # SUMMARY
        # ====================================

        integrity_summary = (

            self.build_integrity_summary(

                integrity_analysis,

                corruption_report
            )
        )

        # ====================================
        # UPDATE STATE
        # ====================================

        self.guardian_state[
            "guardian_stability"
        ] = (

            integrity_summary.get(
                "guardian_state",
                "stable"
            )
        )

        self.guardian_state[
            "guardian_cycles"
        ] += 1

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "cycle_id":
            str(uuid.uuid4()),

            "integrity_analysis":
            integrity_analysis,

            "corruption_report":
            corruption_report,

            "quarantine_plan":
            quarantine_plan,

            "rollback_strategy":
            rollback_strategy,

            "integrity_graph":
            integrity_graph,

            "integrity_summary":
            integrity_summary,

            "guardian_state":
            self.guardian_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.integrity_history.append(
            report
        )

        return report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        latest_cycle = {}

        if self.integrity_history:

            latest_cycle = (
                self.integrity_history[-1]
            )

        return {

            "guardian_state":
            self.guardian_state,

            "validation_history":

            len(
                self.validation_history
            ),

            "corruption_history":

            len(
                self.corruption_history
            ),

            "quarantine_history":

            len(
                self.quarantine_history
            ),

            "rollback_history":

            len(
                self.rollback_history
            ),

            "integrity_cycles":

            len(
                self.integrity_history
            ),

            "latest_cycle":
            latest_cycle
        }


# ============================================
# GLOBAL RUNTIME INTEGRITY GUARDIAN
# ============================================

runtime_integrity_guardian = (
    RuntimeIntegrityGuardian()
)