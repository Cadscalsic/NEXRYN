# ============================================
# NEXRYN UNIFIED COGNITIVE KERNEL
# ============================================

from datetime import datetime

from core.state.cognitive_state import (
    CognitiveState
)

from runtime.kernel.blackboard import (
    CognitiveBlackboard
)

from runtime.state.runtime_state import (
    RuntimeState
)

from runtime.scheduler import (
    RuntimeScheduler
)

from runtime.orchestration import (
    EngineRegistry,
    EngineLifecycleManager
)


# ============================================
# COGNITIVE KERNEL
# ============================================

class CognitiveKernel:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # CORE COGNITIVE STATE
        # ====================================

        self.cognitive_state = (
            CognitiveState()
        )

        # ====================================
        # SHARED BLACKBOARD
        # ====================================

        self.blackboard = (
            CognitiveBlackboard()
        )

        # ====================================
        # RUNTIME STATE
        # ====================================

        self.runtime_state = (
            RuntimeState()
        )

        # ====================================
        # RUNTIME SCHEDULER
        # ====================================

        self.scheduler = (
            RuntimeScheduler()
        )

        # ====================================
        # ENGINE REGISTRY
        # ====================================

        self.engine_registry = (
            EngineRegistry()
        )

        # ====================================
        # ENGINE LIFECYCLE
        # ====================================

        self.lifecycle_manager = (
            EngineLifecycleManager()
        )

        # ====================================
        # SHARED MEMORY
        # ====================================

        self.shared_memory = {}

        # ====================================
        # KERNEL EVENTS
        # ====================================

        self.kernel_events = []

        # ====================================
        # KERNEL STATE
        # ====================================

        self.kernel_state = {

            "kernel_mode":
            "recursive_cognitive_kernel",

            "runtime_state":
            "initialized",

            "workspace_sync":
            "enabled",

            "cross_domain_reasoning":
            "enabled",

            "cognitive_cycles":
            0
        }

    # ========================================
    # LOAD TASK
    # ========================================

    def load_task(

        self,

        input_grid,

        output_grid=None
    ):

        self.cognitive_state.load_task(

            input_grid,

            output_grid
        )

        self.register_event(

            "task_loaded",

            {

                "input_loaded":
                True,

                "output_loaded":
                output_grid is not None
            }
        )

    # ========================================
    # START RUNTIME
    # ========================================

    def start(self):

        self.runtime_state.start()

        self.scheduler.start()

        self.kernel_state[
            "runtime_state"
        ] = "active"

        self.register_event(

            "runtime_started",

            {

                "state":
                "active"
            }
        )

    # ========================================
    # STOP RUNTIME
    # ========================================

    def stop(self):

        self.runtime_state.stop()

        self.scheduler.stop()

        self.kernel_state[
            "runtime_state"
        ] = "stopped"

        self.register_event(

            "runtime_stopped",

            {

                "state":
                "stopped"
            }
        )

    # ========================================
    # REGISTER EVENT
    # ========================================

    def register_event(

        self,

        event_type,

        payload
    ):

        event = {

            "event_type":
            event_type,

            "payload":
            payload,

            "timestamp":
            str(datetime.utcnow())
        }

        self.kernel_events.append(
            event
        )

        return event

    # ========================================
    # UPDATE SHARED MEMORY
    # ========================================

    def update_shared_memory(

        self,

        key,

        value
    ):

        self.shared_memory[
            key
        ] = {

            "value":
            value,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # GET SHARED MEMORY
    # ========================================

    def get_shared_memory(

        self,

        key,

        default=None
    ):

        if key not in self.shared_memory:

            return default

        return self.shared_memory[
            key
        ].get(
            "value"
        )

    # ========================================
    # REGISTER ENGINE
    # ========================================

    def register_engine(

        self,

        engine_name,

        engine_instance,

        metadata=None
    ):

        self.engine_registry.register(

            engine_name,

            engine_instance,

            metadata
        )

        self.register_event(

            "engine_registered",

            {

                "engine":
                engine_name
            }
        )

    # ========================================
    # REGISTER ENGINE TASK
    # ========================================

    def register_engine_task(

        self,

        engine_name,

        priority=1
    ):

        self.scheduler.register_task(

            engine_name,

            priority
        )

    # ========================================
    # NEXT SCHEDULED TASK
    # ========================================

    def next_scheduled_task(self):

        return self.scheduler.next_task()

    # ========================================
    # COMPLETE TASK
    # ========================================

    def complete_task(

        self,

        task
    ):

        self.scheduler.complete_task(
            task
        )

    # ========================================
    # FAIL TASK
    # ========================================

    def fail_task(

        self,

        task
    ):

        self.scheduler.fail_task(
            task
        )

    # ========================================
    # COORDINATE COGNITIVE SYSTEMS
    # ========================================

    def coordinate_cognitive_systems(

        self,

        runtime_context
    ):

        cognitive_domains = {

            "reasoning":
            "reasoning_orchestration_report",

            "governance":
            "governance_report",

            "memory":
            "memory_report",

            "execution":
            "execution_report",

            "repair":
            "self_repair_report",

            "evolution":
            "evolution_report",

            "identity":
            "identity_report",

            "meta":
            "meta_cognitive_report"
        }

        coordinated_domains = {}

        for domain, key in cognitive_domains.items():

            coordinated_domains[
                domain
            ] = key in runtime_context

        coordination_score = round(

            sum(
                coordinated_domains.values()
            ) / len(cognitive_domains),

            4
        )

        coordination_state = "stable"

        if coordination_score < 0.7:

            coordination_state = (
                "degraded"
            )

        report = {

            "coordinated_domains":
            coordinated_domains,

            "coordination_score":
            coordination_score,

            "coordination_state":
            coordination_state,

            "coordination_mode":
            "cross_domain_cognitive_coordination",

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # UPDATE WORKING MEMORY
        # ====================================

        self.blackboard.update_working_memory(

            "cognitive_coordination",

            report
        )

        # ====================================
        # REGISTER EVENT
        # ====================================

        self.blackboard.register_event(

            "coordination_cycle",

            report
        )

        return report

    # ========================================
    # EXECUTE KERNEL CYCLE
    # ========================================

    def execute_kernel_cycle(

        self,

        runtime_context
    ):

        coordination = (

            self.coordinate_cognitive_systems(

                runtime_context
            )
        )

        workspace_report = (

            self.blackboard.run_workspace_cycle()
        )

        self.kernel_state[
            "cognitive_cycles"
        ] += 1

        cycle_report = {

            "coordination":
            coordination,

            "workspace":
            workspace_report,

            "kernel_state":
            self.kernel_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "kernel_cycle",

            cycle_report
        )

        return cycle_report

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "runtime":
            self.runtime_state.summary(),

            "cognitive_state":
            self.cognitive_state.summary(),

            "blackboard":
            self.blackboard.summary(),

            "lifecycle":
            self.lifecycle_manager.summary(),

            "shared_memory":
            len(self.shared_memory),

            "kernel_events":
            len(self.kernel_events),

            "kernel_state":
            self.kernel_state
        }