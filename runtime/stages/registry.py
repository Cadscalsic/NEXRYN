# ============================================
# NEXRYN STAGE REGISTRY
# ============================================

from datetime import datetime


# ============================================
# STAGE REGISTRY
# ============================================

class StageRegistry:

    def __init__(self):

        # ====================================
        # REGISTERED STAGES
        # ====================================

        self.stages = {}

        # ====================================
        # ACTIVE STAGES
        # ====================================

        self.active_stages = []

        # ====================================
        # REGISTRY HISTORY
        # ====================================

        self.registry_history = []

        # ====================================
        # REGISTRY METRICS
        # ====================================

        self.metrics = {

            "registered_stages":
            0,

            "removed_stages":
            0,

            "retrieved_stages":
            0,

            "failed_retrievals":
            0,

            "registry_health":
            "stable"
        }

    # ============================================
    # REGISTER STAGE
    # ============================================

    def register(

        self,

        stage_function,

        priority="medium",

        stage_type="runtime_stage"
    ):

        stage_name = (
            stage_function.__name__
        )

        # ====================================
        # REGISTER METADATA
        # ====================================

        self.stages[
            stage_name
        ] = {

            "name":
            stage_name,

            "function":
            stage_function,

            "priority":
            priority,

            "stage_type":
            stage_type,

            "registered_at":
            str(
                datetime.utcnow()
            ),

            "execution_count":
            0,

            "active":
            True
        }

        # ====================================
        # ACTIVE STAGES
        # ====================================

        if stage_name not in (

            self.active_stages
        ):

            self.active_stages.append(
                stage_name
            )

        # ====================================
        # METRICS
        # ====================================

        self.metrics[
            "registered_stages"
        ] += 1

        # ====================================
        # HISTORY
        # ====================================

        self.registry_history.append({

            "event":
            "stage_registered",

            "stage":
            stage_name,

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

    # ============================================
    # GET STAGE
    # ============================================

    def get(

        self,

        stage_name
    ):

        stage = self.stages.get(
            stage_name
        )

        # ====================================
        # FAILED RETRIEVAL
        # ====================================

        if stage is None:

            self.metrics[
                "failed_retrievals"
            ] += 1

            return None

        # ====================================
        # UPDATE METRICS
        # ====================================

        self.metrics[
            "retrieved_stages"
        ] += 1

        stage[
            "execution_count"
        ] += 1

        return stage[
            "function"
        ]

    # ============================================
    # GET STAGE METADATA
    # ============================================

    def get_stage_metadata(

        self,

        stage_name
    ):

        return self.stages.get(
            stage_name
        )

    # ============================================
    # HAS STAGE
    # ============================================

    def has_stage(

        self,

        stage_name
    ):

        return (
            stage_name in self.stages
        )

    # ============================================
    # ACTIVATE STAGE
    # ============================================

    def activate_stage(

        self,

        stage_name
    ):

        if self.has_stage(
            stage_name
        ):

            self.stages[
                stage_name
            ]["active"] = True

            if stage_name not in (

                self.active_stages
            ):

                self.active_stages.append(
                    stage_name
                )

    # ============================================
    # DEACTIVATE STAGE
    # ============================================

    def deactivate_stage(

        self,

        stage_name
    ):

        if self.has_stage(
            stage_name
        ):

            self.stages[
                stage_name
            ]["active"] = False

            self.active_stages = [

                stage

                for stage in self.active_stages

                if stage != stage_name
            ]

    # ============================================
    # REMOVE STAGE
    # ============================================

    def remove(

        self,

        stage_name
    ):

        if self.has_stage(
            stage_name
        ):

            del self.stages[
                stage_name
            ]

            self.active_stages = [

                stage

                for stage in self.active_stages

                if stage != stage_name
            ]

            self.metrics[
                "removed_stages"
            ] += 1

            self.registry_history.append({

                "event":
                "stage_removed",

                "stage":
                stage_name,

                "timestamp":
                str(
                    datetime.utcnow()
                )
            })

    # ============================================
    # LIST STAGES
    # ============================================

    def list_stages(self):

        return list(
            self.stages.keys()
        )

    # ============================================
    # GET ACTIVE STAGES
    # ============================================

    def get_active_stages(self):

        return self.active_stages

    # ============================================
    # GET ALL STAGES
    # ============================================

    def get_all(self):

        return self.stages

    # ============================================
    # HEALTH CHECK
    # ============================================

    def health_check(self):

        healthy = True

        if self.metrics[
            "failed_retrievals"
        ] > 10:

            healthy = False

            self.metrics[
                "registry_health"
            ] = "degraded"

        return {

            "healthy":
            healthy,

            "registry_health":
            self.metrics[
                "registry_health"
            ],

            "registered_stages":
            self.metrics[
                "registered_stages"
            ],

            "active_stages":
            len(
                self.active_stages
            )
        }

    # ============================================
    # BUILD REGISTRY REPORT
    # ============================================

    def build_registry_report(self):

        return {

            "metrics":
            self.metrics,

            "health":
            self.health_check(),

            "registered_stages":
            len(
                self.stages
            ),

            "active_stages":
            len(
                self.active_stages
            ),

            "history_events":
            len(
                self.registry_history
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

    # ============================================
    # PRINT REGISTRY
    # ============================================

    def print_registry(self):

        print(
            "\n=================================================="
        )

        print(
            "NEXRYN :: STAGE REGISTRY"
        )

        print(
            "==================================================\n"
        )

        for stage_name, metadata in (

            self.stages.items()
        ):

            print(

                f"{stage_name} "

                f"[{metadata['priority']}] "

                f"({metadata['stage_type']})"
            )

        print()