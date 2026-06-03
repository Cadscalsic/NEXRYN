# ============================================
# NEXRYN COGNITIVE BUDGET MANAGER
# ============================================

from datetime import datetime
import uuid


# ============================================
# COGNITIVE BUDGET MANAGER
# ============================================

class CognitiveBudgetManager:

    # ========================================
    # INITIALIZE MANAGER
    # ========================================

    def __init__(self):

        # ====================================
        # ACTIVE BUDGETS
        # ====================================

        self.active_budgets = {}

        # ====================================
        # BUDGET HISTORY
        # ====================================

        self.budget_history = []

        # ====================================
        # EXECUTION HISTORY
        # ====================================

        self.execution_history = []

        # ====================================
        # MANAGER STATE
        # ====================================

        self.manager_state = {

            "budget_mode":
            "adaptive_cognitive_budgeting",

            "resource_regulation":
            True,

            "adaptive_allocation":
            True,

            "pressure_monitoring":
            True,

            "runtime_stability":
            "stable",

            "budget_cycles":
            0
        }

        # ====================================
        # DEFAULT BUDGET
        # ====================================

        self.default_budget = 100

        # ====================================
        # OPERATION COSTS
        # ====================================

        self.operation_costs = {

            "reasoning":
            5,

            "planning":
            7,

            "execution":
            4,

            "reflection":
            6,

            "meta":
            10,

            "projection":
            8,

            "memory":
            3,

            "compression":
            4,

            "stabilization":
            5
        }

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
    # INITIALIZE BUDGET
    # ========================================

    def initialize_budget(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        if domain not in (

            self.active_budgets
        ):

            self.active_budgets[
                domain
            ] = {

                "allocated_budget":
                self.default_budget,

                "consumed_budget":
                0,

                "remaining_budget":
                self.default_budget,

                "budget_state":
                "stable"
            }

        return self.active_budgets[
            domain
        ]

    # ========================================
    # GET OPERATION COST
    # ========================================

    def get_operation_cost(

        self,

        operation
    ):

        operation = self.normalize_domain(
            operation
        )

        return self.operation_costs.get(
            operation,
            5
        )

    # ========================================
    # CAN EXECUTE
    # ========================================

    def can_execute(

        self,

        domain,

        operation
    ):

        domain = self.normalize_domain(
            domain
        )

        budget = self.initialize_budget(
            domain
        )

        operation_cost = (

            self.get_operation_cost(
                operation
            )
        )

        remaining_budget = (

            budget.get(
                "remaining_budget",
                0
            )
        )

        return remaining_budget >= operation_cost

    # ========================================
    # CONSUME BUDGET
    # ========================================

    def consume_budget(

        self,

        domain,

        operation
    ):

        domain = self.normalize_domain(
            domain
        )

        budget = self.initialize_budget(
            domain
        )

        operation_cost = (

            self.get_operation_cost(
                operation
            )
        )

        # ====================================
        # EXECUTION VALIDATION
        # ====================================

        allowed = self.can_execute(

            domain,

            operation
        )

        if not allowed:

            event = {

                "event_id":
                str(uuid.uuid4()),

                "domain":
                domain,

                "operation":
                operation,

                "event_type":
                "budget_exceeded",

                "remaining_budget":

                budget.get(
                    "remaining_budget",
                    0
                ),

                "required_budget":
                operation_cost,

                "timestamp":
                str(datetime.utcnow())
            }

            self.execution_history.append(
                event
            )

            return {

                "allowed":
                False,

                "event":
                event
            }

        # ====================================
        # UPDATE BUDGET
        # ====================================

        budget[
            "consumed_budget"
        ] += operation_cost

        budget[
            "remaining_budget"
        ] -= operation_cost

        # ====================================
        # BUDGET STATE
        # ====================================

        remaining = budget[
            "remaining_budget"
        ]

        if remaining <= 15:

            budget[
                "budget_state"
            ] = "critical"

        elif remaining <= 40:

            budget[
                "budget_state"
            ] = "elevated"

        else:

            budget[
                "budget_state"
            ] = "stable"

        # ====================================
        # EXECUTION EVENT
        # ====================================

        event = {

            "event_id":
            str(uuid.uuid4()),

            "domain":
            domain,

            "operation":
            operation,

            "operation_cost":
            operation_cost,

            "remaining_budget":
            remaining,

            "event_type":
            "budget_consumed",

            "timestamp":
            str(datetime.utcnow())
        }

        self.execution_history.append(
            event
        )

        self.manager_state[
            "budget_cycles"
        ] += 1

        return {

            "allowed":
            True,

            "event":
            event
        }

    # ========================================
    # RESTORE BUDGET
    # ========================================

    def restore_budget(

        self,

        domain,

        amount=20
    ):

        domain = self.normalize_domain(
            domain
        )

        budget = self.initialize_budget(
            domain
        )

        budget[
            "remaining_budget"
        ] += amount

        budget[
            "remaining_budget"
        ] = min(

            budget[
                "remaining_budget"
            ],

            budget[
                "allocated_budget"
            ]
        )

        return budget

    # ========================================
    # RESET BUDGET
    # ========================================

    def reset_budget(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        self.active_budgets[
            domain
        ] = {

            "allocated_budget":
            self.default_budget,

            "consumed_budget":
            0,

            "remaining_budget":
            self.default_budget,

            "budget_state":
            "stable"
        }

        return self.active_budgets[
            domain
        ]

    # ========================================
    # COMPUTE GLOBAL PRESSURE
    # ========================================

    def compute_global_pressure(self):

        total_remaining = 0

        total_consumed = 0

        for budget in (

            self.active_budgets.values()
        ):

            total_remaining += budget.get(
                "remaining_budget",
                0
            )

            total_consumed += budget.get(
                "consumed_budget",
                0
            )

        if total_consumed <= 100:

            pressure = "low"

        elif total_consumed <= 300:

            pressure = "moderate"

        else:

            pressure = "high"

        return {

            "total_remaining":
            total_remaining,

            "total_consumed":
            total_consumed,

            "pressure":
            pressure
        }

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        return {

            "active_domains":

            len(
                self.active_budgets
            ),

            "global_pressure":

            self.compute_global_pressure(),

            "runtime_state":

            self.manager_state.get(
                "runtime_stability",
                "stable"
            )
        }

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "manager_state":
            self.manager_state,

            "active_budgets":
            self.active_budgets,

            "execution_history":

            len(
                self.execution_history
            ),

            "summary":
            self.build_summary(),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL COGNITIVE BUDGET MANAGER
# ============================================

cognitive_budget_manager = (
    CognitiveBudgetManager()
)