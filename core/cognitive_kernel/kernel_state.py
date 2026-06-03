# ============================================
# NEXRYN KERNEL STATE
# ============================================

from datetime import datetime


class KernelState:

    def __init__(self):

        self.active_mode = "reasoning_mode"
        self.mode_history = []

    def update(self, mode, reason):

        self.active_mode = mode

        entry = {
            "active_mode":
            mode,

            "reason":
            reason,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.mode_history.append(
            entry,
        )

        self.mode_history = (
            self.mode_history[-64:]
        )

        return entry

    def snapshot(self):

        return {
            "active_mode":
            self.active_mode,

            "mode_history_size":
            len(
                self.mode_history,
            ),

            "latest_transition":
            (
                self.mode_history[-1]
                if self.mode_history
                else {}
            ),
        }
