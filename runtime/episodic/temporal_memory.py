# ============================================
# NEXRYN TEMPORAL EPISODIC MEMORY
# ============================================

from datetime import datetime


# ============================================
# TEMPORAL EPISODIC MEMORY
# ============================================

class TemporalEpisodicMemory:

    def __init__(self):

        self.episodes = []

    # ============================================
    # STORE EPISODE
    # ============================================

    def store_episode(

        self,

        cognitive_cycle,

        evaluation_result
    ):

        episode = {

            "timestamp":
            str(
                datetime.utcnow()
            ),

            "cognitive_cycle":
            cognitive_cycle,

            "evaluation_result":
            evaluation_result
        }

        self.episodes.append(
            episode
        )

    # ============================================
    # GET EPISODES
    # ============================================

    def get_episodes(self):

        return self.episodes

    # ============================================
    # GET RECENT EPISODES
    # ============================================

    def get_recent_episodes(

        self,

        limit=5
    ):

        return self.episodes[-limit:]

    # ============================================
    # BUILD TEMPORAL REPORT
    # ============================================

    def build_temporal_report(self):

        success_count = 0

        failure_count = 0

        for episode in self.episodes:

            success = episode.get(
                "evaluation_result",
                {}
            ).get(
                "success",
                False
            )

            if success:

                success_count += 1

            else:

                failure_count += 1

        total = len(self.episodes)

        success_rate = 0.0

        if total > 0:

            success_rate = round(

                success_count / total,

                4
            )

        return {

            "episode_count":
            total,

            "success_count":
            success_count,

            "failure_count":
            failure_count,

            "success_rate":
            success_rate
        }

    # ============================================
    # REPLAY EPISODES
    # ============================================

    def replay_episodes(

        self,

        limit=3
    ):

        return self.episodes[-limit:]