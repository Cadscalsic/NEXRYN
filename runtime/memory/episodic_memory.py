# ============================================
# NEXRYN EPISODIC MEMORY
# ============================================

from datetime import datetime


# ============================================
# EPISODIC MEMORY
# ============================================

class EpisodicMemory:

    def __init__(self):

        self.episodes = []

        self.memory_state = {

            "memory_type":
            "episodic_memory",

            "experience_tracking":
            "enabled",

            "failure_analysis":
            "enabled",

            "strategy_learning":
            "enabled"
        }

    # ============================================
    # STORE EPISODE
    # ============================================

    def store_episode(

        self,

        task_id,

        strategy,

        result,

        score=0.0
    ):

        episode = {

            "task_id":
            task_id,

            "strategy":
            strategy,

            "result":
            result,

            "score":
            score,

            "success":
            bool(
                score >= 0.95
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.episodes.append(
            episode
        )

        return episode

    # ============================================
    # SUCCESSFUL EPISODES
    # ============================================

    def successful_episodes(self):

        return [

            episode

            for episode in self.episodes

            if episode["success"]
        ]

    # ============================================
    # FAILED EPISODES
    # ============================================

    def failed_episodes(self):

        return [

            episode

            for episode in self.episodes

            if not episode["success"]
        ]

    # ============================================
    # BEST STRATEGIES
    # ============================================

    def best_strategies(

        self,

        limit=5
    ):

        sorted_episodes = sorted(

            self.episodes,

            key=lambda x: x["score"],

            reverse=True
        )

        return sorted_episodes[:limit]

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        successful = len(

            self.successful_episodes()
        )

        failed = len(

            self.failed_episodes()
        )

        total = len(
            self.episodes
        )

        success_rate = 0.0

        if total > 0:

            success_rate = round(

                successful / total,

                4
            )

        return {

            "memory_type":
            "episodic_memory",

            "total_episodes":
            total,

            "successful_episodes":
            successful,

            "failed_episodes":
            failed,

            "success_rate":
            success_rate,

            "state":
            "stable"
        }