# ============================================
# NEXRYN SEMANTIC PROCESS MANAGER
# ============================================

from datetime import datetime


class SemanticProcessManager:

    def __init__(self):

        self.process_history = []

    def build_processes(self, context, routing_report):

        processes = []

        immune = context.get(
            "cognitive_immune_system_v2_report",
            {},
        )

        blocked = set(
            immune.get(
                "identity_firewall",
                {},
            ).get(
                "blocked_payloads",
                [],
            )
        )

        for index, route in enumerate(
            routing_report.get(
                "routes",
                [],
            )
        ):

            concept = route.get(
                "concept",
                "unknown",
            )

            process_state = (
                "blocked_by_identity_firewall"
                if concept in blocked
                else "ready"
            )

            processes.append({
                "process_id":
                f"semproc:{index + 1}",

                "concept":
                concept,

                "route_mode":
                route.get(
                    "route_mode",
                ),

                "isolation":
                "semantic_process_space",

                "process_state":
                process_state,
            })

        report = {
            "system":
            "semantic_process_manager",

            "processes":
            processes,

            "process_count":
            len(
                processes,
            ),

            "ready_count":
            len([
                process
                for process in processes
                if process.get(
                    "process_state",
                )
                == "ready"
            ]),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.process_history.append(
            report,
        )

        self.process_history = (
            self.process_history[-64:]
        )

        return report
