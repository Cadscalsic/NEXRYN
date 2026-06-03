# ============================================
# NEXRYN VIRTUAL SEMANTIC MEMORY
# ============================================

from datetime import datetime


class VirtualSemanticMemory:

    def __init__(self):

        self.memory_history = []

    def build_memory_map(self, context):

        swapping = context.get(
            "dynamic_cognitive_swapping_report",
            {},
        )

        phase_5 = context.get(
            "semantic_virtual_memory_report",
            {},
        )

        loaded = swapping.get(
            "loaded_concepts",
            phase_5.get(
                "active_cognition",
                [],
            ),
        )

        latent = swapping.get(
            "latent_concepts",
            phase_5.get(
                "latent_cognition",
                [],
            ),
        )

        archive = swapping.get(
            "paged_out_concepts",
            phase_5.get(
                "archived_cognition",
                [],
            ),
        )

        memory_map = {
            "working_semantic_memory":
            loaded,

            "latent_semantic_memory":
            latent,

            "archive_semantic_memory":
            archive,

            "executable_semantic_memory":
            context.get(
                "semantic_cache_compiler_report",
                {},
            ).get(
                "executable_semantic_macros",
                [],
            ),
        }

        report = {
            "system":
            "virtual_semantic_memory",

            "memory_map":
            memory_map,

            "working_count":
            len(
                loaded,
            ),

            "latent_count":
            len(
                latent,
            ),

            "archive_count":
            len(
                archive,
            ),

            "executable_count":
            len(
                memory_map[
                    "executable_semantic_memory"
                ],
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.memory_history.append(
            report,
        )

        self.memory_history = (
            self.memory_history[-64:]
        )

        return report
