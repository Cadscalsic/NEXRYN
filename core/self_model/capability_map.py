# ============================================
# NEXRYN CAPABILITY MAP
# ============================================


class CapabilityMap:

    def map_capabilities(self, context):

        reports = {
            "thermodynamic_regulation":
            "cognitive_thermodynamics_report",

            "distributed_execution":
            "distributed_cognitive_execution_report",

            "semantic_fabric":
            "distributed_semantic_execution_fabric_report",

            "safe_novelty":
            "controlled_safe_novelty_report",

            "semantic_control":
            "adaptive_semantic_control_report",

            "reasoning_orchestration":
            "reasoning_report",
        }

        capabilities = []

        for capability, key in reports.items():

            capabilities.append({
                "capability":
                capability,

                "available":
                key in context,

                "evidence_key":
                key,
            })

        return {
            "capabilities":
            capabilities,

            "available_count":
            len([
                item
                for item in capabilities
                if item.get(
                    "available",
                )
            ]),
        }
