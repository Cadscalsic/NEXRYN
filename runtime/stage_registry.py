# ============================================
# NEXRYN STAGE REGISTRY COMPATIBILITY WRAPPER
# ============================================

from runtime.stages.registry import StageRegistry as CanonicalStageRegistry


# ============================================
# STAGE REGISTRY
# ============================================

class StageRegistry(CanonicalStageRegistry):

    """Compatibility layer for the canonical runtime.stages registry."""

    def register(
        self,
        stage_name_or_function,
        stage_function=None,
        priority="medium",
        stage_type="runtime_stage"
    ):

        if stage_function is None:

            return super().register(
                stage_name_or_function,
                priority=priority,
                stage_type=stage_type
            )

        stage_function.__name__ = str(
            stage_name_or_function
        )

        return super().register(
            stage_function,
            priority=priority,
            stage_type=stage_type
        )

    def get_stage(
        self,
        stage_name
    ):

        return self.get(
            stage_name
        )

    def stage_exists(
        self,
        stage_name
    ):

        return self.has_stage(
            stage_name
        )

    def remove_stage(
        self,
        stage_name
    ):

        return self.remove(
            stage_name
        )

    def get_all_stages(self):

        return self.get_all()

    def list_stage_names(self):

        return self.list_stages()


# ============================================
# GLOBAL REGISTRY
# ============================================

stage_registry = StageRegistry()
