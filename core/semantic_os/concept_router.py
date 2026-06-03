# ============================================
# NEXRYN CONCEPT ROUTER
# ============================================

from datetime import datetime


def _name(item):

    if isinstance(
        item,
        dict,
    ):

        return str(
            item.get(
                "concept",
                item.get(
                    "semantic_path",
                    item.get(
                        "macro_id",
                        "unknown",
                    ),
                ),
            )
        )

    return str(
        item,
    )


class ConceptRouter:

    def __init__(self):

        self.routing_history = []

    def route_concepts(self, context, memory_report):

        memory_map = memory_report.get(
            "memory_map",
            {},
        )

        routes = []

        for concept in memory_map.get(
            "working_semantic_memory",
            [],
        ):

            routes.append({
                "concept":
                _name(
                    concept,
                ),

                "source":
                "working_semantic_memory",

                "target":
                "semantic_process_manager",

                "route_mode":
                "execute_now",
            })

        for macro in memory_map.get(
            "executable_semantic_memory",
            [],
        ):

            routes.append({
                "concept":
                _name(
                    macro,
                ),

                "source":
                "executable_semantic_memory",

                "target":
                "semantic_scheduler",

                "route_mode":
                "macro_dispatch",
            })

        report = {
            "system":
            "concept_router",

            "routes":
            routes,

            "route_count":
            len(
                routes,
            ),

            "routing_policy":
            "executable_semantic_infrastructure",

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.routing_history.append(
            report,
        )

        self.routing_history = (
            self.routing_history[-64:]
        )

        return report
