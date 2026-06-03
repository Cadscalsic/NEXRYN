# ============================================
# NEXRYN MEMORY COMPRESSION RUNTIME
# ============================================

from datetime import datetime


class MemoryCompressionRuntime:

    def __init__(self):

        self.compression_history = []

    def build_plan(
        self,
        context
    ):

        memory = context.get(
            "hierarchical_memory_architecture_report",
            {}
        )

        layers = memory.get(
            "layers",
            {}
        )

        compression_targets = []
        protected_layers = []

        for layer_name, layer in layers.items():

            pressure = layer.get(
                "pressure",
                0.0
            )

            if pressure >= 0.80:

                compression_targets.append({
                    "layer":
                    layer_name,

                    "pressure":
                    pressure,

                    "policy":
                    (
                        "summarize_and_spill"
                        if layer_name in [
                            "working_memory",
                            "latent_memory"
                        ]
                        else "deduplicate_and_alias"
                    )
                })

            else:

                protected_layers.append(
                    layer_name
                )

        combined_pressure = memory.get(
            "combined_memory_pressure",
            0.0
        )

        compression_mode = (
            "collapse_prevention"
            if combined_pressure >= 0.80
            else "pressure_reduction"
            if combined_pressure >= 0.65
            else "maintenance"
        )

        report = {
            "runtime":
            "memory_compression",

            "compression_mode":
            compression_mode,

            "combined_memory_pressure":
            combined_pressure,

            "compression_targets":
            compression_targets,

            "protected_layers":
            protected_layers,

            "actions":
            [
                target.get(
                    "policy"
                )
                for target in compression_targets
            ],

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.compression_history.append(
            report
        )

        self.compression_history = (
            self.compression_history[-32:]
        )

        return report


memory_compression_runtime = (
    MemoryCompressionRuntime()
)
