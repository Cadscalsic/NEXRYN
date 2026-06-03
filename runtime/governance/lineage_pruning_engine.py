# ============================================
# NEXRYN LINEAGE PRUNING ENGINE
# ============================================

from datetime import datetime


# ============================================
# LINEAGE PRUNING ENGINE
# ============================================

class LineagePruningEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # LIMITS
        # ====================================

        self.MAX_LINEAGE_DEPTH = 2

        self.MAX_MUTATION_COUNT = 5

        self.MAX_BRANCH_COUNT = 50

        self.MAX_RECURSIVE_RISK = 3

        # ====================================
        # PRUNING HISTORY
        # ====================================

        self.pruning_history = []

        self.removed_branches = []

        self.detected_cycles = []

        self.active_constraints = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "lineage_pruning":
            True,

            "recursive_protection":
            True,

            "merge_limiting":
            True,

            "branch_stabilization":
            True,

            "adaptive_evolution_control":
            True
        }

    # ========================================
    # ANALYZE LINEAGE DEPTH
    # ========================================

    def analyze_lineage_depth(

        self,

        lineage_history
    ):

        if not isinstance(
            lineage_history,
            list
        ):

            lineage_history = []

        lineage_depth = 0

        mutation_count = 0

        recursive_branches = 0

        branch_count = len(
            lineage_history
        )

        for lineage in lineage_history:

            merge_depth = lineage.get(
                "merge_depth",
                0
            )

            mutations = lineage.get(
                "mutation_count",
                0
            )

            recursive_flag = lineage.get(
                "recursive_branch",
                False
            )

            lineage_depth = max(

                lineage_depth,

                merge_depth
            )

            mutation_count += mutations

            if recursive_flag:

                recursive_branches += 1

        analysis_report = {

            "lineage_depth":
            lineage_depth,

            "mutation_count":
            mutation_count,

            "recursive_branches":
            recursive_branches,

            "branch_count":
            branch_count,

            "timestamp":
            str(datetime.utcnow())
        }

        return analysis_report

    # ========================================
    # DETECT RECURSIVE EXPLOSION
    # ========================================

    def detect_recursive_explosion(

        self,

        lineage_history
    ):

        recursive_risk = 0

        detected_cycles = []

        observed_ids = set()

        for lineage in lineage_history:

            lineage_id = lineage.get(
                "strategy_id"
            )

            merge_depth = lineage.get(
                "merge_depth",
                0
            )

            mutation_count = lineage.get(
                "mutation_count",
                0
            )

            # ====================================
            # CYCLIC DETECTION
            # ====================================

            if lineage_id in observed_ids:

                recursive_risk += 1

                detected_cycles.append({

                    "strategy_id":
                    lineage_id,

                    "risk":
                    "cyclic_reference"
                })

            observed_ids.add(
                lineage_id
            )

            # ====================================
            # EXCESSIVE DEPTH
            # ====================================

            if merge_depth > (

                self.MAX_LINEAGE_DEPTH
            ):

                recursive_risk += 1

            # ====================================
            # EXCESSIVE MUTATION
            # ====================================

            if mutation_count > (

                self.MAX_MUTATION_COUNT
            ):

                recursive_risk += 1

        self.detected_cycles.extend(
            detected_cycles
        )

        explosion_report = {

            "recursive_risk":
            recursive_risk,

            "detected_cycles":
            detected_cycles,

            "explosion_detected":

            recursive_risk >= (
                self.MAX_RECURSIVE_RISK
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        return explosion_report

    # ========================================
    # ENFORCE MERGE LIMITS
    # ========================================

    def enforce_merge_limits(

        self,

        lineage_history
    ):

        stabilized_lineage = []

        for lineage in lineage_history:

            merge_depth = lineage.get(
                "merge_depth",
                0
            )

            mutation_count = lineage.get(
                "mutation_count",
                0
            )

            branch_score = lineage.get(
                "score",
                0.0
            )

            # ====================================
            # DEPTH LIMIT
            # ====================================

            if merge_depth > (

                self.MAX_LINEAGE_DEPTH
            ):

                self.removed_branches.append({

                    "strategy_id":

                    lineage.get(
                        "strategy_id"
                    ),

                    "reason":
                    "merge_depth_limit"
                })

                continue

            # ====================================
            # MUTATION LIMIT
            # ====================================

            if mutation_count > (

                self.MAX_MUTATION_COUNT
            ):

                self.removed_branches.append({

                    "strategy_id":

                    lineage.get(
                        "strategy_id"
                    ),

                    "reason":
                    "mutation_limit"
                })

                continue

            # ====================================
            # LOW SCORE FILTER
            # ====================================

            if branch_score <= 0.10:

                self.removed_branches.append({

                    "strategy_id":

                    lineage.get(
                        "strategy_id"
                    ),

                    "reason":
                    "low_score"
                })

                continue

            stabilized_lineage.append(
                lineage
            )

        # ====================================
        # MAX BRANCH COUNT
        # ====================================

        if len(stabilized_lineage) > (

            self.MAX_BRANCH_COUNT
        ):

            stabilized_lineage = sorted(

                stabilized_lineage,

                key=lambda branch:

                branch.get(
                    "score",
                    0.0
                ),

                reverse=True
            )

            stabilized_lineage = stabilized_lineage[
                :self.MAX_BRANCH_COUNT
            ]

            self.active_constraints.append(
                "branch_count_limited"
            )

        return stabilized_lineage

    # ========================================
    # PRUNE LINEAGE
    # ========================================

    def prune_lineage(

        self,

        lineage_history
    ):

        if not isinstance(
            lineage_history,
            list
        ):

            lineage_history = []

        # ====================================
        # ANALYZE LINEAGE
        # ====================================

        analysis_report = (

            self.analyze_lineage_depth(

                lineage_history
            )
        )

        # ====================================
        # DETECT RECURSIVE RISK
        # ====================================

        explosion_report = (

            self.detect_recursive_explosion(

                lineage_history
            )
        )

        # ====================================
        # ENFORCE LIMITS
        # ====================================

        stabilized_lineage = (

            self.enforce_merge_limits(

                lineage_history
            )
        )

        pruning_report = {

            "analysis_report":
            analysis_report,

            "explosion_report":
            explosion_report,

            "stabilized_lineage_count":

            len(stabilized_lineage),

            "removed_branches":

            len(
                self.removed_branches
            ),

            "active_constraints":
            self.active_constraints,

            "timestamp":
            str(datetime.utcnow())
        }

        self.pruning_history.append(
            pruning_report
        )

        return {

            "stabilized_lineage":
            stabilized_lineage,

            "pruning_report":
            pruning_report
        }

    # ========================================
    # BUILD PRUNING REPORT
    # ========================================

    def build_pruning_report(self):

        latest_report = {}

        if self.pruning_history:

            latest_report = (

                self.pruning_history[-1]
            )

        return {

            "pruning_cycles":

            len(
                self.pruning_history
            ),

            "removed_branches":

            len(
                self.removed_branches
            ),

            "detected_cycles":

            len(
                self.detected_cycles
            ),

            "active_constraints":
            self.active_constraints,

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL PRUNING ENGINE
# ============================================

lineage_pruning_engine = (
    LineagePruningEngine()
)