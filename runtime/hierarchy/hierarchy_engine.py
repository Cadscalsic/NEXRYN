# ============================================
# NEXRYN RECURSIVE HIERARCHY ENGINE
# ============================================

from datetime import datetime
import uuid


# ============================================
# HIERARCHY ENGINE
# ============================================

class HierarchyEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # HIERARCHY LEVELS
        # ====================================

        self.levels = {

            "low_level": [],

            "mid_level": [],

            "high_level": [],

            "meta_level": []
        }

        # ====================================
        # LEVEL PRIORITIES
        # ====================================

        self.level_priorities = {

            "low_level":
            1,

            "mid_level":
            2,

            "high_level":
            3,

            "meta_level":
            4
        }

        # ====================================
        # HIERARCHY EVENTS
        # ====================================

        self.hierarchy_events = []

        # ====================================
        # RECURSIVE LINKS
        # ====================================

        self.recursive_links = []

        # ====================================
        # ACTIVATION SCORES
        # ====================================

        self.activation_scores = {}

        # ====================================
        # HIERARCHY STATE
        # ====================================

        self.hierarchy_state = {

            "hierarchy_mode":
            "recursive_hierarchical_cognition",

            "abstraction":
            "enabled",

            "cross_level_reasoning":
            "enabled",

            "meta_reasoning":
            "active",

            "recursive_coordination":
            "enabled",

            "hierarchy_cycles":
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

        self.hierarchy_events.append(
            event
        )

        return event

    # ========================================
    # BUILD HIERARCHY
    # ========================================

    def build_hierarchy(

        self,

        hypotheses
    ):

        hierarchy = {

            "low_level": [],

            "mid_level": [],

            "high_level": [],

            "meta_level": []
        }

        for hypothesis in hypotheses:

            hypothesis_type = hypothesis.get(
                "type",
                ""
            )

            # ====================================
            # LOW LEVEL
            # ====================================

            if (

                "color" in hypothesis_type

                or

                "density" in hypothesis_type

                or

                "pixel" in hypothesis_type
            ):

                hierarchy[
                    "low_level"
                ].append(
                    hypothesis
                )

                self.activation_scores[
                    str(hypothesis)
                ] = 0.55

            # ====================================
            # MID LEVEL
            # ====================================

            elif (

                "object" in hypothesis_type

                or

                "symmetry" in hypothesis_type

                or

                "group" in hypothesis_type
            ):

                hierarchy[
                    "mid_level"
                ].append(
                    hypothesis
                )

                self.activation_scores[
                    str(hypothesis)
                ] = 0.70

            # ====================================
            # HIGH LEVEL
            # ====================================

            elif (

                "adaptive" in hypothesis_type

                or

                "hybrid" in hypothesis_type

                or

                "strategic" in hypothesis_type
            ):

                hierarchy[
                    "high_level"
                ].append(
                    hypothesis
                )

                self.activation_scores[
                    str(hypothesis)
                ] = 0.85

            # ====================================
            # META LEVEL
            # ====================================

            else:

                hierarchy[
                    "meta_level"
                ].append(
                    hypothesis
                )

                self.activation_scores[
                    str(hypothesis)
                ] = 0.95

        self.levels = hierarchy

        self.register_event(

            "hierarchy_built",

            {

                "hypothesis_count":
                len(hypotheses)
            }
        )

        return hierarchy

    # ========================================
    # BUILD RECURSIVE LINKS
    # ========================================

    def build_recursive_links(self):

        self.recursive_links = []

        level_names = list(
            self.levels.keys()
        )

        for index in range(

            len(level_names) - 1
        ):

            source = level_names[index]

            target = level_names[index + 1]

            link = {

                "source":
                source,

                "target":
                target,

                "relation":
                "hierarchical_abstraction"
            }

            self.recursive_links.append(
                link
            )

        return self.recursive_links

    # ========================================
    # CROSS LEVEL REASONING
    # ========================================

    def cross_level_reasoning(self):

        reasoning_paths = []

        for source_level in self.levels:

            for target_level in self.levels:

                if source_level == target_level:

                    continue

                if (

                    self.levels[source_level]

                    and

                    self.levels[target_level]
                ):

                    reasoning_paths.append({

                        "source":
                        source_level,

                        "target":
                        target_level,

                        "reasoning":
                        "cross_level_inference"
                    })

        return reasoning_paths

    # ========================================
    # COMPUTE ABSTRACTION SCORE
    # ========================================

    def compute_abstraction_score(self):

        total = sum(

            len(level)

            for level in self.levels.values()
        )

        if total == 0:

            return 0.0

        weighted_score = (

            len(
                self.levels["low_level"]
            ) * 0.25

            +

            len(
                self.levels["mid_level"]
            ) * 0.50

            +

            len(
                self.levels["high_level"]
            ) * 0.75

            +

            len(
                self.levels["meta_level"]
            ) * 1.0
        )

        return round(

            weighted_score / total,

            4
        )

    # ========================================
    # COMPETITIVE ACTIVATION
    # ========================================

    def competitive_activation(self):

        if not self.activation_scores:

            return None

        dominant = max(

            self.activation_scores,

            key=self.activation_scores.get
        )

        return {

            "dominant_hypothesis":
            dominant,

            "activation_score":

            self.activation_scores[
                dominant
            ]
        }

    # ========================================
    # BUILD META HIERARCHY
    # ========================================

    def build_meta_hierarchy(self):

        meta_hierarchy = {

            "hierarchical_depth":
            len(self.levels),

            "recursive_links":
            len(self.recursive_links),

            "cross_level_reasoning":
            "enabled",

            "abstraction_mode":
            "recursive_hierarchical_abstraction",

            "timestamp":
            str(datetime.utcnow())
        }

        return meta_hierarchy

    # ========================================
    # RUN HIERARCHY CYCLE
    # ========================================

    def run_hierarchy_cycle(

        self,

        hypotheses
    ):

        hierarchy = (

            self.build_hierarchy(
                hypotheses
            )
        )

        recursive_links = (

            self.build_recursive_links()
        )

        cross_reasoning = (

            self.cross_level_reasoning()
        )

        abstraction_score = (

            self.compute_abstraction_score()
        )

        activation = (

            self.competitive_activation()
        )

        meta_hierarchy = (

            self.build_meta_hierarchy()
        )

        self.hierarchy_state[
            "hierarchy_cycles"
        ] += 1

        report = {

            "hierarchy":
            hierarchy,

            "recursive_links":
            recursive_links,

            "cross_reasoning":
            cross_reasoning,

            "abstraction_score":
            abstraction_score,

            "activation":
            activation,

            "meta_hierarchy":
            meta_hierarchy,

            "hierarchy_state":
            self.hierarchy_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "hierarchy_cycle",

            report
        )

        return report

    # ========================================
    # GET LEVEL
    # ========================================

    def get_level(

        self,

        level_name
    ):

        return self.levels.get(
            level_name,
            []
        )

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "levels":
            {

                key:
                len(value)

                for key, value in

                self.levels.items()
            },

            "recursive_links":
            len(self.recursive_links),

            "activation_scores":
            len(self.activation_scores),

            "hierarchy_events":
            len(self.hierarchy_events),

            "hierarchy_state":
            self.hierarchy_state
        }

    # ========================================
    # PRINT HIERARCHY
    # ========================================

    def print_hierarchy(self):

        print("\n==================================================")
        print("NEXRYN :: HIERARCHICAL COGNITION")
        print("==================================================\n")

        for level, hypotheses in (

            self.levels.items()
        ):

            print(f"{level}:\n")

            for hypothesis in hypotheses:

                print(hypothesis)

            print()