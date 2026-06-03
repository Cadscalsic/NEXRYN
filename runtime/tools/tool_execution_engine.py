# ============================================
# NEXRYN GOVERNED TOOL EXECUTION ENGINE
# ============================================

import os
import json
import time
import subprocess

from datetime import datetime


# ============================================
# TOOL EXECUTION ENGINE
# ============================================

class ToolExecutionEngine:

    def __init__(self):

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "execution_mode":
            "governed_autonomous_runtime",

            "python_execution":
            "enabled",

            "file_operations":
            "enabled",

            "system_commands":
            "restricted",

            "json_processing":
            "enabled",

            "runtime_stability":
            "stable",

            "execution_cycles":
            0,

            "runtime_health":
            "healthy"
        }

        # ====================================
        # EXECUTION HISTORY
        # ====================================

        self.execution_history = []

        # ====================================
        # ACTIVE TOOLS
        # ====================================

        self.active_tools = [

            "python_executor",

            "file_manager",

            "json_processor",

            "runtime_governor"
        ]

        # ====================================
        # SECURITY POLICIES
        # ====================================

        self.blocked_commands = [

            "format",

            "shutdown",

            "del",

            "rm -rf",

            "powershell Remove-Item",

            "mkfs",

            "diskpart",

            "reg delete"
        ]

        # ====================================
        # ALLOWED COMMANDS
        # ====================================

        self.allowed_commands = [

            "dir",

            "echo",

            "type",

            "python",

            "pip list"
        ]

        # ====================================
        # EXECUTION METRICS
        # ====================================

        self.metrics = {

            "successful_executions":
            0,

            "failed_executions":
            0,

            "blocked_executions":
            0,

            "runtime_warnings":
            0
        }

        # ====================================
        # EXECUTION BUDGET
        # ====================================

        self.execution_budget = {

            "max_execution_time":
            10,

            "max_file_size":
            5_000_000,

            "max_history":
            1000
        }

    # ============================================
    # REGISTER EXECUTION
    # ============================================

    def register_execution(

        self,

        execution_result
    ):

        self.execution_history.append(
            execution_result
        )

        if len(

            self.execution_history

        ) > self.execution_budget[
            "max_history"
        ]:

            self.execution_history.pop(0)

        self.engine_state[
            "execution_cycles"
        ] += 1

    # ============================================
    # VALIDATE COMMAND
    # ============================================

    def validate_command(

        self,

        command
    ):

        command_lower = command.lower()

        for blocked in self.blocked_commands:

            if blocked in command_lower:

                self.metrics[
                    "blocked_executions"
                ] += 1

                return {

                    "allowed":
                    False,

                    "reason":
                    "blocked_command"
                }

        allowed = False

        for safe in self.allowed_commands:

            if command_lower.startswith(
                safe
            ):

                allowed = True

        if not allowed:

            self.metrics[
                "blocked_executions"
            ] += 1

            return {

                "allowed":
                False,

                "reason":
                "command_not_whitelisted"
            }

        return {

            "allowed":
            True,

            "reason":
            "safe_execution"
        }

    # ============================================
    # EXECUTE PYTHON CODE
    # ============================================

    def execute_python(

        self,

        python_code
    ):

        execution_result = {

            "execution_type":
            "python",

            "success":
            False,

            "output":
            None,

            "error":
            None,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        restricted_globals = {

            "__builtins__": {

                "print":
                print,

                "len":
                len,

                "range":
                range,

                "min":
                min,

                "max":
                max,

                "sum":
                sum
            }
        }

        try:

            local_scope = {}

            start_time = time.time()

            exec(

                python_code,

                restricted_globals,

                local_scope
            )

            execution_time = (

                time.time() - start_time
            )

            if execution_time > self.execution_budget[
                "max_execution_time"
            ]:

                raise TimeoutError(

                    "execution_timeout"
                )

            execution_result[
                "success"
            ] = True

            execution_result[
                "output"
            ] = local_scope

            execution_result[
                "execution_time"
            ] = round(

                execution_time,

                4
            )

            self.metrics[
                "successful_executions"
            ] += 1

        except Exception as error:

            execution_result[
                "error"
            ] = str(error)

            self.metrics[
                "failed_executions"
            ] += 1

        self.register_execution(
            execution_result
        )

        return execution_result

    # ============================================
    # EXECUTE SYSTEM COMMAND
    # ============================================

    def execute_command(

        self,

        command
    ):

        validation = (

            self.validate_command(
                command
            )
        )

        if not validation.get(
            "allowed"
        ):

            return {

                "execution_type":
                "system_command",

                "success":
                False,

                "error":

                validation.get(
                    "reason"
                ),

                "timestamp":
                str(
                    datetime.utcnow()
                )
            }

        execution_result = {

            "execution_type":
            "system_command",

            "success":
            False,

            "output":
            None,

            "error":
            None,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        try:

            result = subprocess.run(

                command.split(),

                capture_output=True,

                text=True,

                timeout=self.execution_budget[
                    "max_execution_time"
                ]
            )

            execution_result[
                "success"
            ] = True

            execution_result[
                "output"
            ] = result.stdout

            execution_result[
                "error"
            ] = result.stderr

            self.metrics[
                "successful_executions"
            ] += 1

        except Exception as error:

            execution_result[
                "error"
            ] = str(error)

            self.metrics[
                "failed_executions"
            ] += 1

        self.register_execution(
            execution_result
        )

        return execution_result

    # ============================================
    # WRITE FILE
    # ============================================

    def write_file(

        self,

        file_path,

        content
    ):

        execution_result = {

            "execution_type":
            "file_write",

            "success":
            False,

            "file_path":
            file_path,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        try:

            if len(content) > self.execution_budget[
                "max_file_size"
            ]:

                raise ValueError(
                    "file_too_large"
                )

            with open(

                file_path,

                "w",

                encoding="utf-8"
            ) as file:

                file.write(content)

            execution_result[
                "success"
            ] = True

            self.metrics[
                "successful_executions"
            ] += 1

        except Exception as error:

            execution_result[
                "error"
            ] = str(error)

            self.metrics[
                "failed_executions"
            ] += 1

        self.register_execution(
            execution_result
        )

        return execution_result

    # ============================================
    # READ FILE
    # ============================================

    def read_file(

        self,

        file_path
    ):

        execution_result = {

            "execution_type":
            "file_read",

            "success":
            False,

            "content":
            None,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        try:

            with open(

                file_path,

                "r",

                encoding="utf-8"
            ) as file:

                content = file.read()

            execution_result[
                "success"
            ] = True

            execution_result[
                "content"
            ] = content

            self.metrics[
                "successful_executions"
            ] += 1

        except Exception as error:

            execution_result[
                "error"
            ] = str(error)

            self.metrics[
                "failed_executions"
            ] += 1

        self.register_execution(
            execution_result
        )

        return execution_result

    # ============================================
    # SAVE JSON
    # ============================================

    def save_json(

        self,

        file_path,

        data
    ):

        return self.write_file(

            file_path,

            json.dumps(

                data,

                indent=4
            )
        )

    # ============================================
    # LOAD JSON
    # ============================================

    def load_json(

        self,

        file_path
    ):

        read_result = self.read_file(
            file_path
        )

        if not read_result.get(
            "success"
        ):

            return read_result

        try:

            data = json.loads(

                read_result.get(
                    "content"
                )
            )

            return {

                "execution_type":
                "json_load",

                "success":
                True,

                "data":
                data,

                "timestamp":
                str(
                    datetime.utcnow()
                )
            }

        except Exception as error:

            return {

                "execution_type":
                "json_load",

                "success":
                False,

                "error":
                str(error),

                "timestamp":
                str(
                    datetime.utcnow()
                )
            }

    # ============================================
    # LIST DIRECTORY
    # ============================================

    def list_directory(

        self,

        directory_path
    ):

        execution_result = {

            "execution_type":
            "directory_listing",

            "success":
            False,

            "files":
            [],

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        try:

            files = os.listdir(
                directory_path
            )

            execution_result[
                "success"
            ] = True

            execution_result[
                "files"
            ] = files

            self.metrics[
                "successful_executions"
            ] += 1

        except Exception as error:

            execution_result[
                "error"
            ] = str(error)

            self.metrics[
                "failed_executions"
            ] += 1

        self.register_execution(
            execution_result
        )

        return execution_result

    # ============================================
    # HEALTH CHECK
    # ============================================

    def health_check(self):

        healthy = True

        if self.metrics[
            "failed_executions"
        ] > 10:

            healthy = False

        return {

            "healthy":
            healthy,

            "runtime_health":
            self.engine_state[
                "runtime_health"
            ],

            "failed_executions":
            self.metrics[
                "failed_executions"
            ]
        }

    # ============================================
    # BUILD EXECUTION REPORT
    # ============================================

    def build_execution_report(self):

        return {

            "engine_state":
            self.engine_state,

            "active_tools":
            self.active_tools,

            "execution_history":
            len(
                self.execution_history
            ),

            "metrics":
            self.metrics,

            "health":
            self.health_check(),

            "runtime_state":
            "stable"

            if self.metrics[
                "failed_executions"
            ] == 0

            else "adaptive",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }


# ============================================
# GLOBAL TOOL ENGINE
# ============================================

tool_execution_engine = (
    ToolExecutionEngine()
)