# ============================================
# NEXRYN CONSTITUTIONAL MEMORY
# ============================================

from datetime import datetime


class ConstitutionalMemory:

    def __init__(self):

        self.precedents = []
        self.judicial_decisions = []
        self.collapse_patterns = []

    def record_judgment(self, judgment):

        if not isinstance(
            judgment,
            dict,
        ):

            return None

        entry = {
            "judgment":
            judgment,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.judicial_decisions.append(
            entry,
        )

        self.judicial_decisions = (
            self.judicial_decisions[-128:]
        )

        return entry

    def record_precedent(self, precedent):

        if not isinstance(
            precedent,
            dict,
        ):

            return None

        key = (
            precedent.get(
                "case_type",
                "unknown_case",
            ),
            precedent.get(
                "verdict",
                "unknown_verdict",
            ),
        )

        existing_keys = {
            (
                item.get(
                    "case_type",
                    "unknown_case",
                ),
                item.get(
                    "verdict",
                    "unknown_verdict",
                ),
            )
            for item in self.precedents
        }

        if key not in existing_keys:

            self.precedents.append(
                precedent,
            )

        self.precedents = (
            self.precedents[-96:]
        )

        return precedent

    def record_collapse_pattern(self, pattern):

        if not isinstance(
            pattern,
            dict,
        ):

            return None

        signature = (
            pattern.get(
                "pattern_type",
                "unknown_pattern",
            ),
            pattern.get(
                "trigger",
                "unknown_trigger",
            ),
        )

        existing_signatures = {
            (
                item.get(
                    "pattern_type",
                    "unknown_pattern",
                ),
                item.get(
                    "trigger",
                    "unknown_trigger",
                ),
            )
            for item in self.collapse_patterns
        }

        if signature not in existing_signatures:

            self.collapse_patterns.append(
                pattern,
            )

        self.collapse_patterns = (
            self.collapse_patterns[-64:]
        )

        return pattern

    def summarize_precedents(self):

        return {
            "precedent_count":
            len(
                self.precedents,
            ),

            "judicial_decision_count":
            len(
                self.judicial_decisions,
            ),

            "collapse_pattern_count":
            len(
                self.collapse_patterns,
            ),

            "latest_precedent":
            (
                self.precedents[-1]
                if self.precedents
                else {}
            ),

            "latest_judgment":
            (
                self.judicial_decisions[-1]
                if self.judicial_decisions
                else {}
            ),
        }

    def run_cycle(self, context):

        constitutional = context.get(
            "constitutional_runtime_report",
            {},
        )

        judiciary = constitutional.get(
            "semantic_judiciary",
            {},
        )

        state = constitutional.get(
            "constitutional_runtime_state",
            "unknown",
        )

        precedent = {
            "case_type":
            state,

            "verdict":
            judiciary.get(
                "judiciary_state",
                "unknown",
            ),

            "violations":
            constitutional.get(
                "cognitive_constitution",
                {},
            ).get(
                "violations",
                [],
            ),
        }

        self.record_precedent(
            precedent,
        )

        self.record_judgment(
            judiciary,
        )

        if state in [
            "constitutional_hold",
            "restricted_constitutional_runtime",
        ]:

            self.record_collapse_pattern({
                "pattern_type":
                "constitutional_pressure",

                "trigger":
                state,

                "memory_pressure_score":
                context.get(
                    "memory_pressure_score",
                    0.0,
                ),
            })

        summary = self.summarize_precedents()

        summary.update({
            "system":
            "constitutional_memory",

            "memory_state":
            (
                "precedent_memory_active"
                if summary.get(
                    "precedent_count",
                    0,
                )
                else "precedent_memory_empty"
            ),
        })

        return summary


constitutional_memory = ConstitutionalMemory()
