# ============================================
# NEXRYN RUNTIME SESSION MANAGER
# ============================================

import json
import os

from datetime import datetime

from runtime.memory.persistent_cognitive_memory import (

    PersistentCognitiveMemory
)


# ============================================
# RUNTIME SESSION MANAGER
# ============================================

class RuntimeSessionManager:

    # ========================================
    # INITIALIZE SESSION MANAGER
    # ========================================

    def __init__(

        self,

        session_directory="runtime_data/sessions"
    ):

        # ====================================
        # SESSION DIRECTORY
        # ====================================

        self.session_directory = (
            session_directory
        )

        # ====================================
        # CREATE SESSION DIRECTORY
        # ====================================

        if not os.path.exists(

            self.session_directory
        ):

            os.makedirs(

                self.session_directory,

                exist_ok=True
            )

        # ====================================
        # PERSISTENT MEMORY
        # ====================================

        self.persistent_memory = (
            PersistentCognitiveMemory()
        )

        # ====================================
        # SESSION STATE
        # ====================================

        self.session_state = {

            "session_mode":
            "persistent_recursive_runtime",

            "checkpointing":
            "enabled",

            "runtime_restoration":
            "enabled",

            "executive_persistence":
            "enabled",

            "context_persistence":
            "enabled",

            "recovery_mode":
            "adaptive_restoration",

            "runtime_state":
            "stable",

            "session_cycles":
            0
        }

        # ====================================
        # ACTIVE SESSION
        # ====================================

        self.active_session = None

        # ====================================
        # SESSION HISTORY
        # ====================================

        self.session_history = []

        # ====================================
        # CHECKPOINT HISTORY
        # ====================================

        self.checkpoint_history = []

    # ========================================
    # CREATE SESSION ID
    # ========================================

    def create_session_id(self):

        timestamp = datetime.utcnow().strftime(

            "%Y%m%d_%H%M%S"
        )

        return (
            f"nexryn_session_{timestamp}"
        )

    # ========================================
    # CREATE SESSION
    # ========================================

    def create_session(

        self,

        runtime_context
    ):

        session_id = (
            self.create_session_id()
        )

        session = {

            "session_id":
            session_id,

            "created_at":
            str(
                datetime.utcnow()
            ),

            "runtime_context":
            runtime_context,

            "session_state":
            "active"
        }

        self.active_session = session

        self.session_history.append(
            session
        )

        return session

    # ========================================
    # BUILD CHECKPOINT
    # ========================================

    def build_checkpoint(

        self,

        runtime_context
    ):

        checkpoint = {

            "checkpoint_id":

            len(
                self.checkpoint_history
            ) + 1,

            "timestamp":
            str(
                datetime.utcnow()
            ),

            "runtime_context":
            runtime_context,

            "context_size":

            len(
                runtime_context
            ),

            "checkpoint_mode":
            "recursive_runtime_snapshot"
        }

        self.checkpoint_history.append(
            checkpoint
        )

        return checkpoint

    # ========================================
    # SAVE CHECKPOINT
    # ========================================

    def save_checkpoint(

        self,

        checkpoint
    ):

        checkpoint_id = checkpoint.get(
            "checkpoint_id"
        )

        file_name = (
            f"checkpoint_{checkpoint_id}.json"
        )

        file_path = os.path.join(

            self.session_directory,

            file_name
        )

        try:

            temporary_path = (
                f"{file_path}.tmp"
            )

            with open(

                temporary_path,

                "w",

                encoding="utf-8"
            ) as file:

                json.dump(

                    checkpoint,

                    file,

                    indent=4,

                    ensure_ascii=False
                )

            os.replace(
                temporary_path,
                file_path
            )

            return {

                "success":
                True,

                "file_path":
                file_path
            }

        except Exception as error:

            return {

                "success":
                False,

                "error":
                str(error)
            }

    # ========================================
    # LOAD CHECKPOINT
    # ========================================

    def load_checkpoint(

        self,

        checkpoint_file
    ):

        file_path = os.path.join(

            self.session_directory,

            checkpoint_file
        )

        if not os.path.exists(
            file_path
        ):

            return {

                "success":
                False,

                "error":
                "checkpoint_not_found"
            }

        try:

            with open(

                file_path,

                "r",

                encoding="utf-8"
            ) as file:

                checkpoint = json.load(
                    file
                )

            return {

                "success":
                True,

                "checkpoint":
                checkpoint
            }

        except Exception as error:

            return {

                "success":
                False,

                "error":
                str(error)
            }

    # ========================================
    # SAVE SESSION EXPERIENCE
    # ========================================

    def save_session_experience(

        self,

        runtime_context
    ):

        experience = {

            "timestamp":
            str(
                datetime.utcnow()
            ),

            "runtime_size":

            len(
                runtime_context
            ),

            "runtime_keys":

            list(
                runtime_context.keys()
            ),

            "experience_type":
            "persistent_runtime_cycle"
        }

        self.persistent_memory.save_experience(
            experience
        )

        return experience

    # ========================================
    # RESTORE SESSION
    # ========================================

    def restore_session(

        self,

        checkpoint_file
    ):

        checkpoint_state = (

            self.load_checkpoint(
                checkpoint_file
            )
        )

        if not checkpoint_state.get(
            "success"
        ):

            return checkpoint_state

        checkpoint = checkpoint_state.get(
            "checkpoint",
            {}
        )

        restored_context = checkpoint.get(
            "runtime_context",
            {}
        )

        restoration_report = {

            "success":
            True,

            "restored_context":
            restored_context,

            "restored_keys":

            len(
                restored_context
            ),

            "restoration_mode":
            "recursive_runtime_recovery",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return restoration_report

    # ========================================
    # VALIDATE CONTINUITY
    # ========================================

    def validate_continuity(

        self,

        runtime_context
    ):

        required_keys = [

            "runtime_metadata",

            "inference_report",

            "evaluation_result"
        ]

        missing_keys = []

        for key in required_keys:

            if key not in runtime_context:

                missing_keys.append(
                    key
                )

        validation = {

            "continuity_valid":

            len(
                missing_keys
            ) == 0,

            "missing_keys":
            missing_keys,

            "validation_mode":
            "recursive_runtime_validation",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return validation

    # ========================================
    # RUN SESSION CYCLE
    # ========================================

    def run_session_cycle(

        self,

        runtime_context
    ):

        # ====================================
        # CREATE SESSION
        # ====================================

        session = (

            self.create_session(

                runtime_context
            )
        )

        # ====================================
        # BUILD CHECKPOINT
        # ====================================

        checkpoint = (

            self.build_checkpoint(

                runtime_context
            )
        )

        # ====================================
        # SAVE CHECKPOINT
        # ====================================

        checkpoint_result = (

            self.save_checkpoint(
                checkpoint
            )
        )

        # ====================================
        # SAVE EXPERIENCE
        # ====================================

        experience = (

            self.save_session_experience(

                runtime_context
            )
        )

        # ====================================
        # VALIDATE CONTINUITY
        # ====================================

        continuity = (

            self.validate_continuity(

                runtime_context
            )
        )

        # ====================================
        # SESSION REPORT
        # ====================================

        session_report = {

            "session":
            session,

            "checkpoint":
            checkpoint,

            "checkpoint_result":
            checkpoint_result,

            "experience":
            experience,

            "continuity":
            continuity,

            "session_state":
            self.session_state,

            "runtime_state":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.session_state[
            "session_cycles"
        ] += 1

        return session_report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        memory_summary = (

            self.persistent_memory
            .build_memory_summary()
        )

        latest_checkpoint = {}

        if self.checkpoint_history:

            latest_checkpoint = (

                self.checkpoint_history[-1]
            )

        return {

            "session_state":
            self.session_state,

            "active_session":
            self.active_session,

            "session_history":

            len(
                self.session_history
            ),

            "checkpoint_history":

            len(
                self.checkpoint_history
            ),

            "persistent_memory_summary":
            memory_summary,

            "latest_checkpoint":
            latest_checkpoint
        }


# ============================================
# GLOBAL SESSION MANAGER
# ============================================

runtime_session_manager = (
    RuntimeSessionManager()
)
