# ============================================
# NEXRYN ADAPTIVE COGNITIVE SCHEDULER
# ============================================

from datetime import datetime
import uuid
import math


# ============================================
# RUNTIME SCHEDULER
# ============================================

class RuntimeScheduler:

    # ========================================
    # INITIALIZE SCHEDULER
    # ========================================

    def __init__(self):

        # ====================================
        # EXECUTION QUEUES
        # ====================================

        self.execution_queue = []

        self.completed_queue = []

        self.failed_queue = []

        self.deferred_queue = []

        # ====================================
        # ACTIVE ENGINE
        # ====================================

        self.active_engine = None

        # ====================================
        # ENGINE LOADS
        # ====================================

        self.engine_loads = {}

        # ====================================
        # ENGINE LATENCIES
        # ====================================

        self.engine_latencies = {}

        # ====================================
        # ENGINE FAILURES
        # ====================================

        self.engine_failures = {}

        # ====================================
        # ENGINE COOLDOWNS
        # ====================================

        self.engine_cooldowns = {}

        # ====================================
        # EXECUTION HISTORY
        # ====================================

        self.execution_history = []

        # ====================================
        # RECURSIVE EVENTS
        # ====================================

        self.recursive_events = []

        # ====================================
        # THROTTLING EVENTS
        # ====================================

        self.throttling_events = []

        # ====================================
        # STABILIZATION EVENTS
        # ====================================

        self.stabilization_events = []

        # ====================================
        # RESOURCE BUDGET
        # ====================================

        self.runtime_budget = {

            "max_active_tasks":
            8,

            "max_queue_size":
            128,

            "max_recursive_depth":
            12,

            "max_engine_load":
            0.90,

            "max_latency":
            5.0
        }

        # ====================================
        # SCHEDULER STATE
        # ====================================

        self.scheduler_state = {

            "scheduler_mode":
            "adaptive_recursive_cognition",

            "execution_cycles":
            0,

            "queue_pressure":
            "low",

            "scheduler_status":
            "stable",

            "adaptive_throttling":
            "enabled",

            "recursive_protection":
            "enabled",

            "semantic_prioritization":
            "enabled",

            "runtime_budgeting":
            "enabled",

            "stabilization":
            "enabled"
        }

    # ========================================
    # REGISTER TASK
    # ========================================

    def register_task(

        self,

        engine_name,

        priority=1,

        semantic_weight=0.5,

        recursive_depth=0
    ):

        task = {

            "task_id":
            str(uuid.uuid4()),

            "engine":
            engine_name,

            "priority":
            priority,

            "semantic_weight":
            semantic_weight,

            "recursive_depth":
            recursive_depth,

            "status":
            "waiting",

            "registered_at":
            str(datetime.utcnow())
        }

        # ====================================
        # RECURSIVE PROTECTION
        # ====================================

        if recursive_depth > self.runtime_budget[
            "max_recursive_depth"
        ]:

            task["status"] = "rejected"

            self.recursive_events.append({

                "event":
                "recursive_limit_exceeded",

                "engine":
                engine_name,

                "recursive_depth":
                recursive_depth,

                "timestamp":
                str(datetime.utcnow())
            })

            return task

        # ====================================
        # QUEUE LIMIT
        # ====================================

        if len(self.execution_queue) >= (

            self.runtime_budget[
                "max_queue_size"
            ]
        ):

            task["status"] = "deferred"

            self.deferred_queue.append(
                task
            )

            return task

        self.execution_queue.append(
            task
        )

        self.execution_queue = sorted(

            self.execution_queue,

            key=lambda item:

            (
                item["priority"]
                +
                item["semantic_weight"]
            ),

            reverse=True
        )

        return task

    # ========================================
    # EVALUATE PRESSURE
    # ========================================

    def evaluate_pressure(self):

        queue_size = len(
            self.execution_queue
        )

        if queue_size >= 64:

            pressure = "critical"

        elif queue_size >= 32:

            pressure = "high"

        elif queue_size >= 16:

            pressure = "moderate"

        else:

            pressure = "low"

        self.scheduler_state[
            "queue_pressure"
        ] = pressure

        return pressure

    # ========================================
    # COMPUTE ENGINE LOAD
    # ========================================

    def compute_engine_load(

        self,

        engine_name
    ):

        executions = 0

        for event in self.execution_history:

            if event.get(
                "engine"
            ) == engine_name:

                executions += 1

        load = round(

            min(
                executions / 100,
                1.0
            ),

            4
        )

        self.engine_loads[
            engine_name
        ] = load

        return load

    # ========================================
    # COMPUTE LATENCY
    # ========================================

    def compute_latency(

        self,

        engine_name
    ):

        load = self.engine_loads.get(
            engine_name,
            0.0
        )

        latency = round(

            load * 5,

            4
        )

        self.engine_latencies[
            engine_name
        ] = latency

        return latency

    # ========================================
    # THROTTLING
    # ========================================

    def apply_throttling(

        self,

        engine_name
    ):

        load = self.compute_engine_load(
            engine_name
        )

        latency = self.compute_latency(
            engine_name
        )

        throttled = False

        if load >= self.runtime_budget[
            "max_engine_load"
        ]:

            throttled = True

        if latency >= self.runtime_budget[
            "max_latency"
        ]:

            throttled = True

        if throttled:

            self.throttling_events.append({

                "engine":
                engine_name,

                "load":
                load,

                "latency":
                latency,

                "timestamp":
                str(datetime.utcnow())
            })

        return throttled

    # ========================================
    # NEXT TASK
    # ========================================

    def next_task(self):

        self.evaluate_pressure()

        if len(self.execution_queue) == 0:

            return None

        # ====================================
        # SELECT TASK
        # ====================================

        task = self.execution_queue.pop(0)

        engine_name = task[
            "engine"
        ]

        # ====================================
        # THROTTLING
        # ====================================

        throttled = self.apply_throttling(
            engine_name
        )

        if throttled:

            task["status"] = "deferred"

            self.deferred_queue.append(
                task
            )

            return None

        # ====================================
        # ACTIVATE TASK
        # ====================================

        task["status"] = "active"

        task["started_at"] = str(
            datetime.utcnow()
        )

        self.active_engine = engine_name

        self.scheduler_state[
            "execution_cycles"
        ] += 1

        return task

    # ========================================
    # COMPLETE TASK
    # ========================================

    def complete_task(

        self,

        task
    ):

        task["status"] = "completed"

        task["completed_at"] = str(
            datetime.utcnow()
        )

        self.completed_queue.append(
            task
        )

        self.execution_history.append(
            task
        )

        self.active_engine = None

    # ========================================
    # FAIL TASK
    # ========================================

    def fail_task(

        self,

        task,

        reason="unknown"
    ):

        task["status"] = "failed"

        task["failure_reason"] = reason

        task["failed_at"] = str(
            datetime.utcnow()
        )

        self.failed_queue.append(
            task
        )

        self.execution_history.append(
            task
        )

        engine = task["engine"]

        if engine not in self.engine_failures:

            self.engine_failures[
                engine
            ] = 0

        self.engine_failures[
            engine
        ] += 1

        self.active_engine = None

        self.scheduler_state[
            "scheduler_status"
        ] = "degraded"

    # ========================================
    # STABILIZATION
    # ========================================

    def stabilization_cycle(self):

        failed = len(
            self.failed_queue
        )

        deferred = len(
            self.deferred_queue
        )

        if failed >= 10:

            self.scheduler_state[
                "scheduler_status"
            ] = "critical"

        if deferred >= 32:

            self.scheduler_state[
                "queue_pressure"
            ] = "high"

        report = {

            "failed_tasks":
            failed,

            "deferred_tasks":
            deferred,

            "timestamp":
            str(datetime.utcnow())
        }

        self.stabilization_events.append(
            report
        )

        return report

    # ========================================
    # RECOVERY CYCLE
    # ========================================

    def recovery_cycle(self):

        recovered = []

        while (

            len(self.deferred_queue) > 0

            and

            len(self.execution_queue) < 16
        ):

            task = self.deferred_queue.pop(0)

            task["status"] = "waiting"

            self.execution_queue.append(
                task
            )

            recovered.append(
                task["engine"]
            )

        return {

            "recovered_tasks":
            recovered,

            "recovery_count":
            len(recovered),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # BUILD EXECUTION GRAPH
    # ========================================

    def build_execution_graph(self):

        nodes = []

        edges = []

        node_id = 0

        for task in self.execution_history:

            nodes.append({

                "node_id":
                node_id,

                "engine":
                task["engine"],

                "status":
                task["status"]
            })

            if node_id > 0:

                edges.append({

                    "source":
                    node_id - 1,

                    "target":
                    node_id,

                    "relation":
                    "execution_transition"
                })

            node_id += 1

        return {

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "runtime_execution_graph"
        }

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        self.evaluate_pressure()

        execution_graph = (
            self.build_execution_graph()
        )

        return {

            "active_engine":
            self.active_engine,

            "queued_tasks":
            len(self.execution_queue),

            "completed_tasks":
            len(self.completed_queue),

            "failed_tasks":
            len(self.failed_queue),

            "deferred_tasks":
            len(self.deferred_queue),

            "execution_history":
            len(self.execution_history),

            "recursive_events":
            len(self.recursive_events),

            "throttling_events":
            len(self.throttling_events),

            "stabilization_events":
            len(self.stabilization_events),

            "execution_graph_nodes":
            len(
                execution_graph["nodes"]
            ),

            "execution_graph_edges":
            len(
                execution_graph["edges"]
            ),

            "scheduler_state":
            self.scheduler_state
        }


# ============================================
# GLOBAL SCHEDULER
# ============================================

runtime_scheduler = (
    RuntimeScheduler()
)