# ============================================
# NEXRYN RECURSIVE COGNITIVE BLACKBOARD
# ============================================

from datetime import datetime
import uuid


# ============================================
# COGNITIVE BLACKBOARD
# ============================================

class CognitiveBlackboard:

    # ========================================
    # INITIALIZE BLACKBOARD
    # ========================================

    def __init__(self):

        # ====================================
        # PATTERNS
        # ====================================

        self.patterns = []

        # ====================================
        # RULES
        # ====================================

        self.rules = []

        # ====================================
        # HYPOTHESES
        # ====================================

        self.hypotheses = []

        # ====================================
        # PLANS
        # ====================================

        self.plans = []

        # ====================================
        # SEARCH RESULTS
        # ====================================

        self.search_results = []

        # ====================================
        # PROGRAMS
        # ====================================

        self.programs = []

        # ====================================
        # MEMORY MATCHES
        # ====================================

        self.memory_matches = []

        # ====================================
        # EXECUTION TRACE
        # ====================================

        self.execution_trace = []

        # ====================================
        # WORKING MEMORY
        # ====================================

        self.working_memory = {}

        # ====================================
        # ATTENTION SYSTEM
        # ====================================

        self.attention_focus = None

        # ====================================
        # ACTIVATION SCORES
        # ====================================

        self.activation_scores = {}

        # ====================================
        # SEMANTIC LINKS
        # ====================================

        self.semantic_links = []

        # ====================================
        # EVENT STREAM
        # ====================================

        self.workspace_events = []

        # ====================================
        # PRIORITY QUEUE
        # ====================================

        self.priority_queue = []

        # ====================================
        # BLACKBOARD STATE
        # ====================================

        self.blackboard_state = {

            "workspace_mode":
            "recursive_cognitive_workspace",

            "attention_state":
            "dynamic",

            "semantic_sync":
            "enabled",

            "competitive_activation":
            "enabled",

            "working_memory":
            "active",

            "workspace_cycles":
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

        self.workspace_events.append(
            event
        )

        return event

    # ========================================
    # UPDATE ATTENTION
    # ========================================

    def update_attention(

        self,

        target,

        score=1.0
    ):

        self.attention_focus = {

            "target":
            target,

            "attention_score":
            score,

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "attention_update",

            self.attention_focus
        )

    # ========================================
    # ADD PATTERN
    # ========================================

    def add_pattern(

        self,

        pattern,

        activation=0.7
    ):

        self.patterns.append(
            pattern
        )

        self.activation_scores[
            str(pattern)
        ] = activation

        self.register_event(

            "pattern_added",

            pattern
        )

    # ========================================
    # ADD RULE
    # ========================================

    def add_rule(

        self,

        rule,

        activation=0.75
    ):

        self.rules.append(
            rule
        )

        self.activation_scores[
            str(rule)
        ] = activation

        self.register_event(

            "rule_added",

            rule
        )

    # ========================================
    # ADD HYPOTHESIS
    # ========================================

    def add_hypothesis(

        self,

        hypothesis,

        confidence=0.5
    ):

        entry = {

            "hypothesis":
            hypothesis,

            "confidence":
            confidence,

            "timestamp":
            str(datetime.utcnow())
        }

        self.hypotheses.append(
            entry
        )

        self.activation_scores[
            str(hypothesis)
        ] = confidence

        self.register_event(

            "hypothesis_added",

            entry
        )

    # ========================================
    # ADD PLAN
    # ========================================

    def add_plan(

        self,

        plan,

        priority=1
    ):

        entry = {

            "plan":
            plan,

            "priority":
            priority,

            "timestamp":
            str(datetime.utcnow())
        }

        self.plans.append(
            entry
        )

        self.priority_queue.append(
            entry
        )

        self.register_event(

            "plan_added",

            entry
        )

    # ========================================
    # ADD SEARCH RESULT
    # ========================================

    def add_search_result(

        self,

        result
    ):

        self.search_results.append(
            result
        )

        self.register_event(

            "search_result_added",

            result
        )

    # ========================================
    # ADD PROGRAM
    # ========================================

    def add_program(

        self,

        program
    ):

        self.programs.append(
            program
        )

        self.register_event(

            "program_added",

            program
        )

    # ========================================
    # ADD MEMORY MATCH
    # ========================================

    def add_memory_match(

        self,

        memory
    ):

        self.memory_matches.append(
            memory
        )

        self.register_event(

            "memory_match_added",

            memory
        )

    # ========================================
    # TRACE EXECUTION
    # ========================================

    def trace_execution(

        self,

        trace
    ):

        trace_entry = {

            "trace":
            trace,

            "timestamp":
            str(datetime.utcnow())
        }

        self.execution_trace.append(
            trace_entry
        )

        self.register_event(

            "execution_trace",

            trace_entry
        )

    # ========================================
    # UPDATE WORKING MEMORY
    # ========================================

    def update_working_memory(

        self,

        key,

        value
    ):

        self.working_memory[
            key
        ] = {

            "value":
            value,

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "working_memory_update",

            {

                "key":
                key
            }
        )

    # ========================================
    # GET WORKING MEMORY
    # ========================================

    def get_working_memory(

        self,

        key,

        default=None
    ):

        if key not in self.working_memory:

            return default

        return self.working_memory[
            key
        ].get(
            "value",
            default
        )

    # ========================================
    # BUILD SEMANTIC LINKS
    # ========================================

    def build_semantic_links(self):

        self.semantic_links = []

        collections = [

            self.patterns,

            self.rules,

            self.programs
        ]

        for collection in collections:

            for item in collection:

                link = {

                    "source":
                    str(item),

                    "target":
                    "workspace",

                    "relation":
                    "semantic_activation"
                }

                self.semantic_links.append(
                    link
                )

        return self.semantic_links

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

        score = self.activation_scores[
            dominant
        ]

        self.update_attention(

            dominant,

            score
        )

        return {

            "dominant":
            dominant,

            "activation_score":
            score
        }

    # ========================================
    # RUN WORKSPACE CYCLE
    # ========================================

    def run_workspace_cycle(self):

        semantic_links = (

            self.build_semantic_links()
        )

        activation = (

            self.competitive_activation()
        )

        self.blackboard_state[
            "workspace_cycles"
        ] += 1

        report = {

            "workspace_state":
            self.blackboard_state,

            "semantic_links":
            len(semantic_links),

            "activation":
            activation,

            "attention_focus":
            self.attention_focus,

            "working_memory":
            len(self.working_memory),

            "events":
            len(self.workspace_events),

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "workspace_cycle",

            report
        )

        return report

    # ========================================
    # CLEAR WORKSPACE
    # ========================================

    def clear_workspace(self):

        self.patterns.clear()

        self.rules.clear()

        self.hypotheses.clear()

        self.plans.clear()

        self.search_results.clear()

        self.programs.clear()

        self.memory_matches.clear()

        self.execution_trace.clear()

        self.semantic_links.clear()

        self.priority_queue.clear()

        self.activation_scores.clear()

        self.working_memory.clear()

        self.attention_focus = None

        self.register_event(

            "workspace_cleared",

            {

                "status":
                "completed"
            }
        )

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "patterns":
            len(self.patterns),

            "rules":
            len(self.rules),

            "hypotheses":
            len(self.hypotheses),

            "plans":
            len(self.plans),

            "search_results":
            len(self.search_results),

            "programs":
            len(self.programs),

            "memory_matches":
            len(self.memory_matches),

            "execution_trace":
            len(self.execution_trace),

            "working_memory":
            len(self.working_memory),

            "semantic_links":
            len(self.semantic_links),

            "workspace_events":
            len(self.workspace_events),

            "attention_focus":
            self.attention_focus,

            "blackboard_state":
            self.blackboard_state
        }