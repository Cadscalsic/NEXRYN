# ============================================
# NEXRYN AGENT RUNTIME
# ============================================

from datetime import datetime

from runtime.tools import (
    tool_execution_engine
)

from runtime.executive import (
    executive_brain
)


# ============================================
# AGENT RUNTIME
# ============================================

class AgentRuntime:

    def __init__(self):

        # ========================================
        # AGENT STATE
        # ========================================

        self.agent_state = {

            "agent_mode":
            "autonomous_recursive_agent",

            "task_execution":
            "enabled",

            "goal_persistence":
            "enabled",

            "tool_coordination":
            "enabled",

            "executive_alignment":
            "enabled",

            "adaptive_reasoning":
            "enabled",

            "runtime_state":
            "stable",

            "execution_cycles":
            0
        }

        # ========================================
        # ACTIVE AGENTS
        # ========================================

        self.active_agents = []

        # ========================================
        # TASK HISTORY
        # ========================================

        self.task_history = []

        # ========================================
        # GOAL MEMORY
        # ========================================

        self.goal_memory = []

        # ========================================
        # EXECUTION HISTORY
        # ========================================

        self.execution_history = []

    # ============================================
    # CREATE AGENT
    # ============================================

    def create_agent(

        self,

        agent_name,

        specialization
    ):

        agent = {

            "agent_id":

            len(
                self.active_agents
            ) + 1,

            "agent_name":
            agent_name,

            "specialization":
            specialization,

            "agent_state":
            "active",

            "created_at":
            str(
                datetime.utcnow()
            )
        }

        self.active_agents.append(
            agent
        )

        return agent

    # ============================================
    # REGISTER GOAL
    # ============================================

    def register_goal(

        self,

        goal
    ):

        goal_state = {

            "goal":
            goal,

            "goal_state":
            "active",

            "priority":
            "high",

            "registered_at":
            str(
                datetime.utcnow()
            )
        }

        self.goal_memory.append(
            goal_state
        )

        return goal_state

    # ============================================
    # BUILD TASK PLAN
    # ============================================

    def build_task_plan(

        self,

        task_description
    ):

        plan = {

            "task":
            task_description,

            "execution_steps": [

                "analyze_task",

                "build_strategy",

                "allocate_tools",

                "execute_task",

                "validate_results"
            ],

            "execution_mode":
            "adaptive_recursive_execution",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.task_history.append(
            plan
        )

        return plan

    # ============================================
    # EXECUTE PYTHON TASK
    # ============================================

    def execute_python_task(

        self,

        python_code
    ):

        execution = (

            tool_execution_engine.execute_python(

                python_code
            )
        )

        self.execution_history.append(
            execution
        )

        return execution

    # ============================================
    # EXECUTE COMMAND TASK
    # ============================================

    def execute_command_task(

        self,

        command
    ):

        execution = (

            tool_execution_engine.execute_command(

                command
            )
        )

        self.execution_history.append(
            execution
        )

        return execution

    # ============================================
    # EXECUTE FILE WRITE
    # ============================================

    def execute_file_write(

        self,

        file_path,

        content
    ):

        execution = (

            tool_execution_engine.write_file(

                file_path,

                content
            )
        )

        self.execution_history.append(
            execution
        )

        return execution

    # ============================================
    # RUN AGENT CYCLE
    # ============================================

    def run_agent_cycle(

        self,

        runtime_context
    ):

        # ========================================
        # BUILD EXECUTIVE STATE
        # ========================================

        executive_state = (

            executive_brain.build_report()
        )

        # ========================================
        # BUILD ACTIVE GOALS
        # ========================================

        active_goals = []

        for goal in self.goal_memory:

            if goal.get(
                "goal_state"
            ) == "active":

                active_goals.append(
                    goal
                )

        # ========================================
        # BUILD ACTIVE TASKS
        # ========================================

        active_tasks = []

        for task in self.task_history:

            active_tasks.append(

                task.get(
                    "task"
                )
            )

        # ========================================
        # BUILD AGENT REPORT
        # ========================================

        report = {

            "agent_state":
            self.agent_state,

            "active_agents":

            len(
                self.active_agents
            ),

            "active_goals":

            len(
                active_goals
            ),

            "active_tasks":

            len(
                active_tasks
            ),

            "executive_alignment":

            executive_state.get(
                "executive_state",
                {}
            ),

            "execution_history":

            len(
                self.execution_history
            ),

            "runtime_state":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.agent_state[
            "execution_cycles"
        ] += 1

        return report

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "agent_state":
            self.agent_state,

            "active_agents":

            len(
                self.active_agents
            ),

            "goal_memory":

            len(
                self.goal_memory
            ),

            "task_history":

            len(
                self.task_history
            ),

            "execution_history":

            len(
                self.execution_history
            ),

            "latest_goal":

            self.goal_memory[-1]

            if self.goal_memory

            else {},

            "latest_task":

            self.task_history[-1]

            if self.task_history

            else {}
        }


# ============================================
# GLOBAL AGENT RUNTIME
# ============================================

agent_runtime = (
    AgentRuntime()
)