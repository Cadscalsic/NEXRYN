class BoundedCuriosity:

    def regulate(self, context):

        entropy = context.get("runtime_entropy", 0.0)

        return {
            "system": "bounded_curiosity",
            "curiosity_state": (
                "curiosity_tempered_by_entropy"
                if entropy >= 0.68
                else "adaptive_discovery_enabled"
            ),
            "recursive_overload_limit": True,
            "topology_preservation": True,
        }
