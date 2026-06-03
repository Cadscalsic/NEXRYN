# ============================================
# NEXRYN LATENT COGNITION RESERVOIR
# ============================================

from datetime import datetime


class LatentReservoir:

    def __init__(self):

        self.latent_paths = []

    def store_deferred_reasoning(self, context):

        reasoning = context.get(
            "reasoning_trace",
            []
        )

        if not isinstance(
            reasoning,
            list
        ):

            reasoning = []

        event = {
            "reasoning_depth":
            len(
                reasoning
            ),

            "hidden_paths":
            reasoning[4:],

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        if event.get(
            "hidden_paths"
        ):

            self.latent_paths.append(
                event
            )

        self.latent_paths = (
            self.latent_paths[-64:]
        )

        return event

    def reactivate_on_uncertainty(self, context):

        uncertainty = (
            context.get(
                "world_model_report",
                {}
            )
            .get(
                "simulation_uncertainty",
                0.0
            )
        )

        if uncertainty < 0.20:

            return []

        return self.retrieve_hidden_paths(
            limit=3
        )

    def retrieve_hidden_paths(self, limit=5):

        paths = []

        for event in reversed(
            self.latent_paths
        ):

            paths.extend(
                event.get(
                    "hidden_paths",
                    []
                )
            )

            if len(
                paths
            ) >= limit:

                break

        return paths[:limit]

    def compress_latent_clusters(self):

        cluster_count = min(
            len(
                self.latent_paths
            ),
            8
        )

        return {
            "cluster_count":
            cluster_count,

            "policy":
            (
                "compress_latent_clusters"
                if cluster_count >= 6
                else "retain_latents"
            )
        }

    def decay_irrelevant_latents(self):

        self.latent_paths = (
            self.latent_paths[-32:]
        )

    def run_cycle(self, context):

        stored = self.store_deferred_reasoning(
            context
        )

        reactivated = self.reactivate_on_uncertainty(
            context
        )

        cluster_report = self.compress_latent_clusters()

        self.decay_irrelevant_latents()

        return {
            "reservoir":
            "latent_cognition",

            "stored_event":
            stored,

            "reactivated_paths":
            reactivated,

            "latent_population":
            len(
                self.latent_paths
            ),

            "cluster_report":
            cluster_report,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }


latent_reservoir = (
    LatentReservoir()
)
