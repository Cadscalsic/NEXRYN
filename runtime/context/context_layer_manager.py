# ============================================
# NEXRYN CONTEXT LAYER MANAGER
# ============================================

from datetime import datetime
import uuid


# ============================================
# CONTEXT LAYER MANAGER
# ============================================

class ContextLayerManager:

    # ========================================
    # INITIALIZE MANAGER
    # ========================================

    def __init__(self):

        # ====================================
        # CONTEXT LAYERS
        # ====================================

        self.context_layers = {

            "core_context": {},

            "reasoning_context": {},

            "execution_context": {},

            "memory_context": {},

            "temporal_context": {},

            "meta_context": {},

            "security_context": {}
        }

        # ====================================
        # LAYER HISTORY
        # ====================================

        self.layer_history = []

        # ====================================
        # MANAGER STATE
        # ====================================

        self.manager_state = {

            "manager_mode":
            "adaptive_context_segmentation",

            "layered_context":
            True,

            "context_isolation":
            True,

            "adaptive_segmentation":
            True,

            "runtime_stability":
            "stable",

            "segmentation_cycles":
            0
        }

    # ========================================
    # NORMALIZE KEY
    # ========================================

    def normalize_key(

        self,

        key
    ):

        if key is None:

            key = "undefined"

        if not isinstance(
            key,
            str
        ):

            key = str(key)

        return key

    # ========================================
    # NORMALIZE VALUE
    # ========================================

    def normalize_value(

        self,

        value
    ):

        if value is None:

            return {}

        return value

    # ========================================
    # VALIDATE LAYER
    # ========================================

    def validate_layer(

        self,

        layer_name
    ):

        if layer_name not in (

            self.context_layers
        ):

            return False

        return True

    # ========================================
    # SET CONTEXT
    # ========================================

    def set_context(

        self,

        layer_name,

        key,

        value
    ):

        # ====================================
        # VALIDATION
        # ====================================

        if not self.validate_layer(
            layer_name
        ):

            return False

        key = self.normalize_key(
            key
        )

        value = self.normalize_value(
            value
        )

        # ====================================
        # STORE VALUE
        # ====================================

        self.context_layers[
            layer_name
        ][key] = value

        # ====================================
        # REGISTER EVENT
        # ====================================

        event = {

            "event_id":
            str(uuid.uuid4()),

            "layer":
            layer_name,

            "key":
            key,

            "event_type":
            "context_update",

            "timestamp":
            str(datetime.utcnow())
        }

        self.layer_history.append(
            event
        )

        self.manager_state[
            "segmentation_cycles"
        ] += 1

        return True

    # ========================================
    # GET CONTEXT
    # ========================================

    def get_context(

        self,

        layer_name,

        key=None,

        default=None
    ):

        # ====================================
        # VALIDATION
        # ====================================

        if not self.validate_layer(
            layer_name
        ):

            return default

        layer = self.context_layers.get(
            layer_name,
            {}
        )

        # ====================================
        # RETURN FULL LAYER
        # ====================================

        if key is None:

            return layer

        key = self.normalize_key(
            key
        )

        return layer.get(
            key,
            default
        )

    # ========================================
    # REMOVE CONTEXT
    # ========================================

    def remove_context(

        self,

        layer_name,

        key
    ):

        # ====================================
        # VALIDATION
        # ====================================

        if not self.validate_layer(
            layer_name
        ):

            return False

        key = self.normalize_key(
            key
        )

        layer = self.context_layers.get(
            layer_name,
            {}
        )

        if key in layer:

            del layer[key]

            return True

        return False

    # ========================================
    # CLEAR LAYER
    # ========================================

    def clear_layer(

        self,

        layer_name
    ):

        if not self.validate_layer(
            layer_name
        ):

            return False

        self.context_layers[
            layer_name
        ] = {}

        return True

    # ========================================
    # BUILD LAYER SUMMARY
    # ========================================

    def build_layer_summary(self):

        layer_summary = {}

        for layer_name, layer_data in (

            self.context_layers.items()
        ):

            layer_summary[layer_name] = {

                "entry_count":
                len(layer_data),

                "layer_state":
                "stable"
            }

        return layer_summary

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "manager_state":
            self.manager_state,

            "layer_summary":

            self.build_layer_summary(),

            "history_size":

            len(
                self.layer_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL CONTEXT LAYER MANAGER
# ============================================

context_layer_manager = (
    ContextLayerManager()
)