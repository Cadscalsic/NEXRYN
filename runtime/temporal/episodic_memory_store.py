# ============================================
# NEXRYN EPISODIC MEMORY STORE
# ============================================

from datetime import datetime
import uuid
import json
import os


# ============================================
# EPISODIC MEMORY STORE
# ============================================

class EpisodicMemoryStore:

    # ========================================
    # INITIALIZE MEMORY STORE
    # ========================================

    def __init__(self):

        # ====================================
        # EPISODIC MEMORY
        # ====================================

        self.episodes = []

        # ====================================
        # TEMPORAL INDEX
        # ====================================

        self.temporal_index = {}

        # ====================================
        # STRATEGY INDEX
        # ====================================

        self.strategy_index = {}

        # ====================================
        # FAILURE INDEX
        # ====================================

        self.failure_index = {}

        # ====================================
        # SUCCESS INDEX
        # ====================================

        self.success_index = {}

        # ====================================
        # RECURSIVE EVENTS
        # ====================================

        self.recursive_events = []

        # ====================================
        # ABSTRACTION MEMORY
        # ====================================

        self.abstraction_memory = []

        # ====================================
        # EXPERIENCE SNAPSHOTS
        # ====================================

        self.experience_snapshots = []

        # ====================================
        # EPISODIC EVENTS
        # ====================================

        self.episodic_events = []

        # ====================================
        # STORAGE CONFIGURATION
        # ====================================

        self.storage_config = {

            "storage_mode":
            "adaptive_temporal_memory",

            "persistent_storage":
            True,

            "experience_replay":
            True,

            "semantic_indexing":
            True,

            "recursive_tracking":
            True,

            "strategy_tracking":
            True,

            "failure_learning":
            True,

            "abstraction_tracking":
            True
        }

        # ====================================
        # STORAGE PATH
        # ====================================

        self.storage_path = (
            "memory/episodic_memory.json"
        )

    # ========================================
    # REGISTER EVENT
    # ========================================

    def register_event(

        self,

        event_type,

        payload
    ):

        event = {

            "event_id":
            str(uuid.uuid4()),

            "event_type":
            event_type,

            "payload":
            payload,

            "timestamp":
            str(datetime.utcnow())
        }

        self.episodic_events.append(
            event
        )

        return event

    # ========================================
    # BUILD EPISODE
    # ========================================

    def build_episode(

        self,

        runtime_context
    ):

        episode = {

            "episode_id":
            str(uuid.uuid4()),

            "timestamp":
            str(datetime.utcnow()),

            "task":
            runtime_context.get(
                "task_path",
                "unknown"
            ),

            "runtime_summary":
            runtime_context.get(
                "final_report",
                {}
            ),

            "evaluation":
            runtime_context.get(
                "evaluation_stage_report",
                {}
            ),

            "reasoning_trace":
            runtime_context.get(
                "reasoning_trace",
                []
            ),

            "semantic_graph":
            runtime_context.get(
                "semantic_graph",
                {}
            ),

            "governance":
            runtime_context.get(
                "governance_report",
                {}
            ),

            "transformation":
            runtime_context.get(
                "transformation_stage_report",
                {}
            ),

            "self_improvement":
            runtime_context.get(
                "self_improvement_stage_report",
                {}
            ),

            "abstractions":
            runtime_context.get(
                "semantic_abstractions",
                []
            ),

            "strategies":
            runtime_context.get(
                "evolved_hypotheses",
                []
            ),

            "runtime_health":
            runtime_context.get(
                "context_health",
                {}
            )
        }

        return episode

    # ========================================
    # STORE EPISODE
    # ========================================

    def store_episode(

        self,

        runtime_context
    ):

        episode = self.build_episode(
            runtime_context
        )

        self.episodes.append(
            episode
        )

        # ====================================
        # INDEX TEMPORALLY
        # ====================================

        timestamp = episode[
            "timestamp"
        ]

        self.temporal_index[
            timestamp
        ] = episode[
            "episode_id"
        ]

        # ====================================
        # INDEX STRATEGIES
        # ====================================

        for strategy in episode[
            "strategies"
        ]:

            strategy_name = strategy.get(
                "strategy",
                "unknown"
            )

            if strategy_name not in (
                self.strategy_index
            ):

                self.strategy_index[
                    strategy_name
                ] = []

            self.strategy_index[
                strategy_name
            ].append(
                episode["episode_id"]
            )

        # ====================================
        # INDEX FAILURES
        # ====================================

        evaluation = episode[
            "evaluation"
        ]

        success = evaluation.get(
            "success",
            False
        )

        if not success:

            failure_key = (
                episode["task"]
            )

            if failure_key not in (
                self.failure_index
            ):

                self.failure_index[
                    failure_key
                ] = []

            self.failure_index[
                failure_key
            ].append(
                episode["episode_id"]
            )

        # ====================================
        # INDEX SUCCESSES
        # ====================================

        else:

            success_key = (
                episode["task"]
            )

            if success_key not in (
                self.success_index
            ):

                self.success_index[
                    success_key
                ] = []

            self.success_index[
                success_key
            ].append(
                episode["episode_id"]
            )

        # ====================================
        # TRACK RECURSIVE EVENTS
        # ====================================

        recursive_depth = len(

            episode[
                "reasoning_trace"
            ]
        )

        recursive_event = {

            "episode_id":
            episode["episode_id"],

            "recursive_depth":
            recursive_depth,

            "timestamp":
            str(datetime.utcnow())
        }

        self.recursive_events.append(
            recursive_event
        )

        # ====================================
        # STORE ABSTRACTIONS
        # ====================================

        for abstraction in episode[
            "abstractions"
        ]:

            self.abstraction_memory.append({

                "episode_id":
                episode["episode_id"],

                "abstraction":
                abstraction,

                "timestamp":
                str(datetime.utcnow())
            })

        # ====================================
        # SNAPSHOT
        # ====================================

        snapshot = {

            "episode_id":
            episode["episode_id"],

            "task":
            episode["task"],

            "strategy_count":
            len(
                episode["strategies"]
            ),

            "abstraction_count":
            len(
                episode["abstractions"]
            ),

            "recursive_depth":
            recursive_depth,

            "timestamp":
            str(datetime.utcnow())
        }

        self.experience_snapshots.append(
            snapshot
        )

        # ====================================
        # REGISTER EVENT
        # ====================================

        self.register_event(

            "episode_stored",

            snapshot
        )

        return episode

    # ========================================
    # EXPERIENCE REPLAY
    # ========================================

    def replay_experiences(

        self,

        limit=5
    ):

        if len(self.episodes) == 0:

            return []

        replay = self.episodes[-limit:]

        self.register_event(

            "experience_replay",

            {

                "replay_count":
                len(replay)
            }
        )

        return replay

    # ========================================
    # SEARCH BY STRATEGY
    # ========================================

    def search_by_strategy(

        self,

        strategy_name
    ):

        matching_ids = (

            self.strategy_index.get(

                strategy_name,

                []
            )
        )

        matches = []

        for episode in self.episodes:

            if episode[
                "episode_id"
            ] in matching_ids:

                matches.append(
                    episode
                )

        return matches

    # ========================================
    # SEARCH FAILURES
    # ========================================

    def search_failures(

        self,

        task_name=None
    ):

        failures = []

        for episode in self.episodes:

            evaluation = episode.get(
                "evaluation",
                {}
            )

            if not evaluation.get(
                "success",
                False
            ):

                if task_name is None:

                    failures.append(
                        episode
                    )

                elif task_name in (
                    episode["task"]
                ):

                    failures.append(
                        episode
                    )

        return failures

    # ========================================
    # SAVE MEMORY
    # ========================================

    def save_memory(self):

        os.makedirs(

            os.path.dirname(
                self.storage_path
            ),

            exist_ok=True
        )

        payload = {

            "episodes":
            self.episodes,

            "temporal_index":
            self.temporal_index,

            "strategy_index":
            self.strategy_index,

            "failure_index":
            self.failure_index,

            "success_index":
            self.success_index,

            "recursive_events":
            self.recursive_events,

            "abstraction_memory":
            self.abstraction_memory,

            "experience_snapshots":
            self.experience_snapshots
        }

        with open(

            self.storage_path,

            "w",

            encoding="utf-8"
        ) as file:

            json.dump(

                payload,

                file,

                indent=4
            )

        self.register_event(

            "memory_saved",

            {

                "storage_path":
                self.storage_path
            }
        )

    # ========================================
    # LOAD MEMORY
    # ========================================

    def load_memory(self):

        if not os.path.exists(
            self.storage_path
        ):

            return

        with open(

            self.storage_path,

            "r",

            encoding="utf-8"
        ) as file:

            payload = json.load(
                file
            )

        self.episodes = payload.get(
            "episodes",
            []
        )

        self.temporal_index = payload.get(
            "temporal_index",
            {}
        )

        self.strategy_index = payload.get(
            "strategy_index",
            {}
        )

        self.failure_index = payload.get(
            "failure_index",
            {}
        )

        self.success_index = payload.get(
            "success_index",
            {}
        )

        self.recursive_events = payload.get(
            "recursive_events",
            []
        )

        self.abstraction_memory = payload.get(
            "abstraction_memory",
            []
        )

        self.experience_snapshots = payload.get(
            "experience_snapshots",
            []
        )

        self.register_event(

            "memory_loaded",

            {

                "episode_count":
                len(self.episodes)
            }
        )

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "storage_config":
            self.storage_config,

            "episode_count":
            len(self.episodes),

            "temporal_index":
            len(self.temporal_index),

            "strategy_index":
            len(self.strategy_index),

            "failure_index":
            len(self.failure_index),

            "success_index":
            len(self.success_index),

            "recursive_events":
            len(self.recursive_events),

            "abstraction_memory":
            len(self.abstraction_memory),

            "experience_snapshots":
            len(self.experience_snapshots),

            "episodic_events":
            len(self.episodic_events),

            "latest_episode":

            self.episodes[-1]

            if self.episodes

            else {}
        }


# ============================================
# GLOBAL EPISODIC MEMORY STORE
# ============================================

episodic_memory_store = (
    EpisodicMemoryStore()
)