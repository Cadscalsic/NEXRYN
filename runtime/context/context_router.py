# ============================================
# NEXRYN CONTEXT ROUTER
# ============================================

from datetime import datetime
import uuid

from runtime.context.context_layer_manager import (
    context_layer_manager
)


# ============================================
# CONTEXT ROUTER
# ============================================

class ContextRouter:

    # ========================================
    # INITIALIZE ROUTER
    # ========================================

    def __init__(self):

        # ====================================
        # ROUTING RULES
        # ====================================

        self.routing_rules = {

            "reasoning":
            "reasoning_context",

            "execution":
            "execution_context",

            "memory":
            "memory_context",

            "temporal":
            "temporal_context",

            "meta":
            "meta_context",

            "security":
            "security_context",

            "core":
            "core_context"
        }

        # ====================================
        # ROUTING HISTORY
        # ====================================

        self.routing_history = []

        # ====================================
        # ROUTER STATE
        # ====================================

        self.router_state = {

            "router_mode":
            "adaptive_context_routing",

            "automatic_routing":
            True,

            "context_segmentation":
            True,

            "routing_stability":
            "stable",

            "routing_cycles":
            0
        }

    # ========================================
    # NORMALIZE DOMAIN
    # ========================================

    def normalize_domain(

        self,

        domain
    ):

        if domain is None:

            domain = "core"

        if not isinstance(
            domain,
            str
        ):

            domain = str(domain)

        domain = domain.lower()

        return domain

    # ========================================
    # RESOLVE LAYER
    # ========================================

    def resolve_layer(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        return self.routing_rules.get(

            domain,

            "core_context"
        )

    # ========================================
    # ROUTE CONTEXT
    # ========================================

    def route_context(

        self,

        domain,

        key,

        value
    ):

        # ====================================
        # RESOLVE TARGET LAYER
        # ====================================

        target_layer = (

            self.resolve_layer(
                domain
            )
        )

        # ====================================
        # STORE CONTEXT
        # ====================================

        result = (

            context_layer_manager.set_context(

                target_layer,

                key,

                value
            )
        )

        # ====================================
        # ROUTING EVENT
        # ====================================

        routing_event = {

            "event_id":
            str(uuid.uuid4()),

            "domain":
            domain,

            "target_layer":
            target_layer,

            "context_key":
            key,

            "routing_result":
            result,

            "timestamp":
            str(datetime.utcnow())
        }

        self.routing_history.append(
            routing_event
        )

        self.router_state[
            "routing_cycles"
        ] += 1

        return {

            "routing_success":
            result,

            "target_layer":
            target_layer,

            "routing_event":
            routing_event
        }

    # ========================================
    # GET ROUTED CONTEXT
    # ========================================

    def get_routed_context(

        self,

        domain,

        key=None,

        default=None
    ):

        target_layer = (

            self.resolve_layer(
                domain
            )
        )

        return (

            context_layer_manager.get_context(

                target_layer,

                key,

                default
            )
        )

    # ========================================
    # REGISTER ROUTING RULE
    # ========================================

    def register_routing_rule(

        self,

        domain,

        target_layer
    ):

        domain = self.normalize_domain(
            domain
        )

        self.routing_rules[
            domain
        ] = target_layer

        return True

    # ========================================
    # BUILD ROUTING SUMMARY
    # ========================================

    def build_routing_summary(self):

        return {

            "registered_domains":

            len(
                self.routing_rules
            ),

            "routing_cycles":

            self.router_state.get(
                "routing_cycles",
                0
            ),

            "routing_state":

            self.router_state.get(
                "routing_stability",
                "stable"
            )
        }

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "router_state":
            self.router_state,

            "routing_rules":
            self.routing_rules,

            "routing_summary":

            self.build_routing_summary(),

            "routing_history":

            len(
                self.routing_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL CONTEXT ROUTER
# ============================================

context_router = (
    ContextRouter()
)