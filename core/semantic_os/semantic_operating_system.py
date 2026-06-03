# ============================================
# NEXRYN SEMANTIC OPERATING SYSTEM
# ============================================

from datetime import datetime

from core.semantic_os.concept_router import (
    ConceptRouter,
)

from core.semantic_os.semantic_process_manager import (
    SemanticProcessManager,
)

from core.semantic_os.semantic_scheduler import (
    SemanticScheduler,
)

from core.semantic_os.virtual_semantic_memory import (
    VirtualSemanticMemory,
)


class SemanticOperatingSystem:

    def __init__(self):

        self.virtual_semantic_memory = VirtualSemanticMemory()
        self.concept_router = ConceptRouter()
        self.semantic_process_manager = SemanticProcessManager()
        self.semantic_scheduler = SemanticScheduler()
        self.os_history = []

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        memory_report = self.virtual_semantic_memory.build_memory_map(
            context,
        )

        routing_report = self.concept_router.route_concepts(
            context,
            memory_report,
        )

        process_report = self.semantic_process_manager.build_processes(
            context,
            routing_report,
        )

        schedule_report = self.semantic_scheduler.schedule(
            context,
            process_report,
        )

        report = {
            "system":
            "semantic_operating_system",

            "virtual_semantic_memory":
            memory_report,

            "concept_router":
            routing_report,

            "semantic_process_manager":
            process_report,

            "semantic_scheduler":
            schedule_report,

            "semantic_memory_mode":
            "executable_semantic_infrastructure",

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.os_history.append(
            report,
        )

        self.os_history = (
            self.os_history[-64:]
        )

        return report


semantic_operating_system = (
    SemanticOperatingSystem()
)
