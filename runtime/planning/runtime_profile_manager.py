# ============================================
# NEXRYN RUNTIME PROFILE MANAGER
# ============================================

from dataclasses import asdict
from datetime import datetime
import hashlib
import json


class RuntimeProfileManager:

    def __init__(self):

        self.observations = []

    def record(
        self,
        task_profile,
        cognitive_cost,
        task_signature=None,
        actual_runtime_seconds=None,
        actual_reasoning_depth=None,
        actual_dependency_depth=None,
    ):

        observation = {
            "task_signature":
            task_signature or self._profile_signature(task_profile),
            "task_complexity":
            task_profile.complexity,
            "estimated_cost":
            cognitive_cost.total_cost,
            "actual_runtime_seconds":
            actual_runtime_seconds,
            "actual_reasoning_depth":
            actual_reasoning_depth,
            "actual_dependency_depth":
            actual_dependency_depth,
            "recorded_at":
            str(datetime.utcnow()),
        }

        self.observations.append(observation)
        return observation

    def build_report(self):

        return {
            "profile_count": len(self.observations),
            "latest_profile":
            self.observations[-1] if self.observations else None,
        }

    def _profile_signature(self, task_profile):

        encoded = json.dumps(
            asdict(task_profile),
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


runtime_profile_manager = RuntimeProfileManager()
