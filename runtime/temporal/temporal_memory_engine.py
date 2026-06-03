# ============================================
# NEXRYN TEMPORAL MEMORY ENGINE
# ============================================

from datetime import datetime
import uuid
import math


# ============================================
# TEMPORAL MEMORY ENGINE
# ============================================

class TemporalMemoryEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # TEMPORAL LINKS
        # ====================================

        self.temporal_links = []

        # ====================================
        # EXPERIENCE CHAINS
        # ====================================

        self.experience_chains = []

        # ====================================
        # TEMPORAL ABSTRACTIONS
        # ====================================

        self.temporal_abstractions = []

        # ====================================
        # REPLAY MEMORY
        # ====================================

        self.replay_memory = []

        # ====================================
        # DECAY EVENTS
        # ====================================

        self.decay_events = []

        # ====================================
        # FAILURE PATTERNS
        # ====================================

        self.failure_patterns = []

        # ====================================
        # STRATEGY PERSISTENCE
        # ====================================

        self.strategy_persistence = {}

        # ====================================
        # TEMPORAL GRAPH
        # ====================================

        self.temporal_graph = {

            "nodes": [],

            "edges": []
        }

        # ====================================
        # ENGINE EVENTS
        # ====================================

        self.engine_events = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "engine_mode":
            "persistent_temporal_cognition",

            "temporal_linking":
            "enabled",

            "experience_replay":
            "enabled",

            "temporal_abstraction":
            "enabled",

            "adaptive_decay":
            "enabled",

            "failure_analysis":
            "enabled",

            "strategy_persistence":
            "enabled",

            "future_projection_ready":
            True,

            "temporal_cycles":
            0
        }

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

        self.engine_events.append(
            event
        )

        return event

    # ========================================
    # COMPUTE EPISODE SIMILARITY
    # ========================================

    def compute_episode_similarity(

        self,

        source_episode,

        target_episode
    ):

        source_task = source_episode.get(
            "task",
            ""
        )

        target_task = target_episode.get(
            "task",
            ""
        )

        source_strategies = {

            strategy.get(
                "strategy",
                "unknown"
            )

            for strategy in source_episode.get(
                "strategies",
                []
            )
        }

        target_strategies = {

            strategy.get(
                "strategy",
                "unknown"
            )

            for strategy in target_episode.get(
                "strategies",
                []
            )
        }

        strategy_overlap = len(

            source_strategies.intersection(
                target_strategies
            )
        )

        task_similarity = 0.0

        if source_task == target_task:

            task_similarity = 1.0

        total = max(

            len(
                source_strategies.union(
                    target_strategies
                )
            ),

            1
        )

        strategy_similarity = round(

            strategy_overlap / total,

            4
        )

        final_similarity = round(

            task_similarity * 0.4 +

            strategy_similarity * 0.6,

            4
        )

        return final_similarity

    # ========================================
    # BUILD TEMPORAL LINKS
    # ========================================

    def build_temporal_links(

        self,

        episodes
    ):

        self.temporal_links = []

        for source_index in range(

            len(episodes)
        ):

            for target_index in range(

                source_index + 1,

                len(episodes)
            ):

                source_episode = episodes[
                    source_index
                ]

                target_episode = episodes[
                    target_index
                ]

                similarity = (

                    self.compute_episode_similarity(

                        source_episode,

                        target_episode
                    )
                )

                if similarity >= 0.35:

                    link = {

                        "link_id":
                        str(uuid.uuid4()),

                        "source_episode":
                        source_episode[
                            "episode_id"
                        ],

                        "target_episode":
                        target_episode[
                            "episode_id"
                        ],

                        "similarity":
                        similarity,

                        "relation":
                        "temporal_cognitive_similarity",

                        "timestamp":
                        str(datetime.utcnow())
                    }

                    self.temporal_links.append(
                        link
                    )

        return self.temporal_links

    # ========================================
    # BUILD EXPERIENCE CHAINS
    # ========================================

    def build_experience_chains(

        self,

        episodes
    ):

        chains = []

        current_chain = []

        for episode in episodes:

            current_chain.append(

                episode[
                    "episode_id"
                ]
            )

            if len(current_chain) >= 5:

                chains.append({

                    "chain_id":
                    str(uuid.uuid4()),

                    "episodes":
                    current_chain,

                    "chain_length":
                    len(current_chain),

                    "timestamp":
                    str(datetime.utcnow())
                })

                current_chain = []

        self.experience_chains = chains

        return chains

    # ========================================
    # BUILD TEMPORAL ABSTRACTIONS
    # ========================================

    def build_temporal_abstractions(

        self,

        episodes
    ):

        abstractions = []

        strategy_frequency = {}

        for episode in episodes:

            strategies = episode.get(
                "strategies",
                []
            )

            for strategy in strategies:

                strategy_name = strategy.get(
                    "strategy",
                    "unknown"
                )

                if strategy_name not in (
                    strategy_frequency
                ):

                    strategy_frequency[
                        strategy_name
                    ] = 0

                strategy_frequency[
                    strategy_name
                ] += 1

        for strategy_name, frequency in (

            strategy_frequency.items()
        ):

            abstraction = {

                "abstraction_id":
                str(uuid.uuid4()),

                "strategy":
                strategy_name,

                "frequency":
                frequency,

                "abstraction_type":
                "persistent_temporal_pattern",

                "stability":
                round(
                    min(
                        frequency / 10,
                        1.0
                    ),
                    4
                ),

                "timestamp":
                str(datetime.utcnow())
            }

            abstractions.append(
                abstraction
            )

        self.temporal_abstractions = (
            abstractions
        )

        return abstractions

    # ========================================
    # EXPERIENCE REPLAY
    # ========================================

    def replay_experiences(

        self,

        episodes,

        replay_limit=5
    ):

        ranked = sorted(

            episodes,

            key=lambda episode:

            len(
                episode.get(
                    "strategies",
                    []
                )
            ),

            reverse=True
        )

        replay = ranked[:replay_limit]

        replay_report = {

            "replay_count":
            len(replay),

            "replayed_episodes":

            [

                item["episode_id"]

                for item in replay
            ],

            "timestamp":
            str(datetime.utcnow())
        }

        self.replay_memory.append(
            replay_report
        )

        self.register_event(

            "experience_replay",

            replay_report
        )

        return replay

    # ========================================
    # ADAPTIVE DECAY
    # ========================================

    def adaptive_decay(

        self,

        episodes,

        decay_threshold=0.10
    ):

        retained = []

        decayed = []

        for episode in episodes:

            strategy_count = len(

                episode.get(
                    "strategies",
                    []
                )
            )

            abstraction_count = len(

                episode.get(
                    "abstractions",
                    []
                )
            )

            value_score = round(

                (
                    strategy_count * 0.6
                    +
                    abstraction_count * 0.4
                )
                / 10,

                4
            )

            if value_score >= decay_threshold:

                retained.append(
                    episode
                )

            else:

                decayed.append(
                    episode
                )

        decay_report = {

            "retained":
            len(retained),

            "decayed":
            len(decayed),

            "timestamp":
            str(datetime.utcnow())
        }

        self.decay_events.append(
            decay_report
        )

        return retained

    # ========================================
    # FAILURE ANALYSIS
    # ========================================

    def analyze_failures(

        self,

        episodes
    ):

        patterns = []

        for episode in episodes:

            evaluation = episode.get(
                "evaluation",
                {}
            )

            success = evaluation.get(
                "success",
                False
            )

            if not success:

                pattern = {

                    "episode_id":
                    episode[
                        "episode_id"
                    ],

                    "task":
                    episode[
                        "task"
                    ],

                    "reasoning_depth":
                    len(

                        episode.get(
                            "reasoning_trace",
                            []
                        )
                    ),

                    "strategy_count":
                    len(

                        episode.get(
                            "strategies",
                            []
                        )
                    ),

                    "timestamp":
                    str(datetime.utcnow())
                }

                patterns.append(
                    pattern
                )

        self.failure_patterns = (
            patterns
        )

        return patterns

    # ========================================
    # STRATEGY PERSISTENCE
    # ========================================

    def build_strategy_persistence(

        self,

        abstractions
    ):

        persistence = {}

        for abstraction in abstractions:

            strategy = abstraction[
                "strategy"
            ]

            persistence[strategy] = {

                "frequency":
                abstraction[
                    "frequency"
                ],

                "stability":
                abstraction[
                    "stability"
                ],

                "persistent":
                abstraction[
                    "stability"
                ] >= 0.50
            }

        self.strategy_persistence = (
            persistence
        )

        return persistence

    # ========================================
    # BUILD TEMPORAL GRAPH
    # ========================================

    def build_temporal_graph(

        self,

        episodes
    ):

        nodes = []

        edges = []

        node_map = {}

        node_id = 0

        for episode in episodes:

            episode_id = episode[
                "episode_id"
            ]

            nodes.append({

                "node_id":
                node_id,

                "episode_id":
                episode_id,

                "task":
                episode[
                    "task"
                ]
            })

            node_map[
                episode_id
            ] = node_id

            node_id += 1

        for link in self.temporal_links:

            source = link[
                "source_episode"
            ]

            target = link[
                "target_episode"
            ]

            if source in node_map and (

                target in node_map
            ):

                edges.append({

                    "source":
                    node_map[source],

                    "target":
                    node_map[target],

                    "relation":
                    link["relation"],

                    "weight":
                    link["similarity"]
                })

        self.temporal_graph = {

            "nodes":
            nodes,

            "edges":
            edges
        }

        return self.temporal_graph

    # ========================================
    # RUN TEMPORAL CYCLE
    # ========================================

    def run_temporal_cycle(

        self,

        episodic_memory_store
    ):

        episodes = (
            episodic_memory_store.episodes
        )

        # ====================================
        # BUILD LINKS
        # ====================================

        temporal_links = (

            self.build_temporal_links(
                episodes
            )
        )

        # ====================================
        # EXPERIENCE CHAINS
        # ====================================

        experience_chains = (

            self.build_experience_chains(
                episodes
            )
        )

        # ====================================
        # TEMPORAL ABSTRACTIONS
        # ====================================

        temporal_abstractions = (

            self.build_temporal_abstractions(
                episodes
            )
        )

        # ====================================
        # EXPERIENCE REPLAY
        # ====================================

        replay = (

            self.replay_experiences(
                episodes
            )
        )

        # ====================================
        # ADAPTIVE DECAY
        # ====================================

        retained = (

            self.adaptive_decay(
                episodes
            )
        )

        # ====================================
        # FAILURE ANALYSIS
        # ====================================

        failures = (

            self.analyze_failures(
                retained
            )
        )

        # ====================================
        # STRATEGY PERSISTENCE
        # ====================================

        persistence = (

            self.build_strategy_persistence(

                temporal_abstractions
            )
        )

        # ====================================
        # TEMPORAL GRAPH
        # ====================================

        temporal_graph = (

            self.build_temporal_graph(
                retained
            )
        )

        self.engine_state[
            "temporal_cycles"
        ] += 1

        report = {

            "temporal_links":
            len(temporal_links),

            "experience_chains":
            len(experience_chains),

            "temporal_abstractions":
            len(temporal_abstractions),

            "replay_count":
            len(replay),

            "retained_episodes":
            len(retained),

            "failure_patterns":
            len(failures),

            "persistent_strategies":
            len(persistence),

            "temporal_graph_nodes":
            len(
                temporal_graph["nodes"]
            ),

            "temporal_graph_edges":
            len(
                temporal_graph["edges"]
            ),

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "temporal_cycle",

            report
        )

        return report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "engine_state":
            self.engine_state,

            "temporal_links":
            len(self.temporal_links),

            "experience_chains":
            len(self.experience_chains),

            "temporal_abstractions":
            len(self.temporal_abstractions),

            "replay_memory":
            len(self.replay_memory),

            "decay_events":
            len(self.decay_events),

            "failure_patterns":
            len(self.failure_patterns),

            "strategy_persistence":
            len(self.strategy_persistence),

            "temporal_graph_nodes":
            len(
                self.temporal_graph[
                    "nodes"
                ]
            ),

            "temporal_graph_edges":
            len(
                self.temporal_graph[
                    "edges"
                ]
            ),

            "engine_events":
            len(self.engine_events)
        }


# ============================================
# GLOBAL TEMPORAL ENGINE
# ============================================

temporal_memory_engine = (
    TemporalMemoryEngine()
)