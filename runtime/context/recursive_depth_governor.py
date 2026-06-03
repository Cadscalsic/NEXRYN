# ============================================
# NEXRYN RECURSIVE DEPTH GOVERNOR
# ============================================

from datetime import datetime
import uuid


# ============================================
# RECURSIVE DEPTH GOVERNOR
# ============================================

class RecursiveDepthGovernor:

    # ========================================
    # INITIALIZE GOVERNOR
    # ========================================

    def __init__(self):

        # ====================================
        # ACTIVE DEPTHS
        # ====================================

        self.active_depths = {}

        # ====================================
        # DEPTH HISTORY
        # ====================================

        self.depth_history = []

        # ====================================
        # DEPTH LIMITS
        # ====================================

        self.depth_limits = {

            "reasoning": 12,

            "planning": 10,

            "reflection": 8,

            "meta": 6,

            "execution": 14,

            "default": 10
        }

        # ====================================
        # GOVERNOR STATE
        # ====================================

        self.governor_state = {

            "governor_mode":
            "adaptive_recursive_regulation",

            "recursive_control":
            True,

            "depth_monitoring":
            True,

            "pressure_detection":
            True,

            "runtime_stability":
            "stable",

            "governor_cycles":
            0
        }

    # ========================================
    # GOVERN RECURSION
    # ========================================

    def govern(

        self,

        recursive_depth,

        domain="reasoning"
    ):

        domain = self.normalize_domain(
            domain
        )

        limit = self.get_depth_limit(
            domain
        )

        recursive_state = "stable"

        if recursive_depth >= limit:

            recursive_state = "critical"

        elif recursive_depth >= (

            limit * 0.7
        ):

            recursive_state = "elevated"

        # ====================================
        # UPDATE ACTIVE DEPTH
        # ====================================

        self.active_depths[
            domain
        ] = recursive_depth

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "domain":
            domain,

            "recursive_depth":
            recursive_depth,

            "depth_limit":
            limit,

            "recursive_state":
            recursive_state,

            "allowed":

            recursive_depth < limit,

            "timestamp":
            str(datetime.utcnow())
        }

        self.depth_history.append(
            report
        )

        self.governor_state[
            "governor_cycles"
        ] += 1

        return report

    # ========================================
    # NORMALIZE DOMAIN
    # ========================================

    def normalize_domain(

        self,

        domain
    ):

        if domain is None:

            domain = "reasoning"

        if not isinstance(
            domain,
            str
        ):

            domain = str(domain)

        return domain.lower()

    # ========================================
    # GET CURRENT DEPTH
    # ========================================

    def get_current_depth(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        return self.active_depths.get(
            domain,
            0
        )

    # ========================================
    # GET DEPTH LIMIT
    # ========================================

    def get_depth_limit(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        return self.depth_limits.get(
            domain,
            3
        )

    # ========================================
    # CAN RECURSE
    # ========================================

    def can_recurse(

        self,

        domain
    ):

        current_depth = (

            self.get_current_depth(
                domain
            )
        )

        depth_limit = (

            self.get_depth_limit(
                domain
            )
        )

        return current_depth < depth_limit

    # ========================================
    # ENTER RECURSION
    # ========================================

    def enter_recursion(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        current_depth = (

            self.get_current_depth(
                domain
            )
        )

        allowed = self.can_recurse(
            domain
        )

        # ====================================
        # BLOCK RECURSION
        # ====================================

        if not allowed:

            event = {

                "event_id":
                str(uuid.uuid4()),

                "domain":
                domain,

                "event_type":
                "recursion_blocked",

                "depth":
                current_depth,

                "limit":
                self.get_depth_limit(
                    domain
                ),

                "timestamp":
                str(datetime.utcnow())
            }

            self.depth_history.append(
                event
            )

            return {

                "allowed":
                False,

                "event":
                event
            }

        # ====================================
        # UPDATE DEPTH
        # ====================================

        self.active_depths[
            domain
        ] = current_depth + 1

        event = {

            "event_id":
            str(uuid.uuid4()),

            "domain":
            domain,

            "event_type":
            "recursion_entered",

            "depth":
            self.active_depths[
                domain
            ],

            "timestamp":
            str(datetime.utcnow())
        }

        self.depth_history.append(
            event
        )

        self.governor_state[
            "governor_cycles"
        ] += 1

        return {

            "allowed":
            True,

            "event":
            event
        }

    # ========================================
    # EXIT RECURSION
    # ========================================

    def exit_recursion(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        current_depth = (

            self.get_current_depth(
                domain
            )
        )

        if current_depth > 0:

            self.active_depths[
                domain
            ] = current_depth - 1

        event = {

            "event_id":
            str(uuid.uuid4()),

            "domain":
            domain,

            "event_type":
            "recursion_exited",

            "depth":
            self.active_depths.get(
                domain,
                0
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.depth_history.append(
            event
        )

        return event

    # ========================================
    # COMPUTE RECURSIVE PRESSURE
    # ========================================

    def compute_recursive_pressure(self):

        total_depth = sum(

            self.active_depths.values()
        )

        if total_depth <= 5:

            pressure = "low"

        elif total_depth <= 12:

            pressure = "moderate"

        else:

            pressure = "high"

        return {

            "total_depth":
            total_depth,

            "pressure":
            pressure
        }

    # ========================================
    # BUILD GOVERNOR SUMMARY
    # ========================================

    def build_governor_summary(self):

        recursive_pressure = (

            self.compute_recursive_pressure()
        )

        return {

            "active_domains":

            len(
                self.active_depths
            ),

            "recursive_pressure":
            recursive_pressure,

            "runtime_state":

            self.governor_state.get(
                "runtime_stability",
                "stable"
            )
        }

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "governor_state":
            self.governor_state,

            "active_depths":
            self.active_depths,

            "depth_history":

            len(
                self.depth_history
            ),

            "governor_summary":

            self.build_governor_summary(),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL RECURSIVE DEPTH GOVERNOR
# ============================================

recursive_depth_governor = (
    RecursiveDepthGovernor()
)
