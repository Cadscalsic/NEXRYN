# ============================================
# NEXRYN ARC GENERALIZATION ENGINE
# ============================================

from datetime import datetime

import copy


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class ARCGeneralizationEngine:

    def __init__(self):

        self.generalization_history = []
        self.abstract_rule_memory = []
        self.transfer_memory = []

    def extract_abstract_rules(self, symbolic_report, spatial_report):

        rules = []

        for rule in symbolic_report.get(
            "generalized_rules",
            [],
        ):

            confidence = _clamp(
                rule.get(
                    "confidence",
                    0.0,
                ),
            )

            rules.append({
                "rule_id":
                f"abstract_rule:{len(rules) + 1}",

                "abstract_rule":
                rule.get(
                    "abstract_rule",
                    "unknown",
                ),

                "semantic_meaning":
                rule.get(
                    "semantic_meaning",
                    "unknown",
                ),

                "confidence":
                confidence,

                "abstraction_level":
                (
                    "task_general"
                    if confidence >= 0.72
                    else "candidate_general"
                ),
            })

        for hypothesis in spatial_report.get(
            "hypotheses",
            [],
        ):

            hypothesis_type = hypothesis.get(
                "type",
                "unknown",
            )

            if hypothesis_type == "unknown":

                continue

            rules.append({
                "rule_id":
                f"spatial_abstract_rule:{len(rules) + 1}",

                "abstract_rule":
                hypothesis_type,

                "semantic_meaning":
                hypothesis.get(
                    "description",
                    hypothesis_type,
                ),

                "confidence":
                _clamp(
                    hypothesis.get(
                        "confidence",
                        0.0,
                    ),
                ),

                "abstraction_level":
                "arc_spatial_invariant",
            })

        return rules[:64]

    def transfer_traits_across_tasks(self, runtime_context):

        evolutionary = runtime_context.get(
            "evolutionary_memory_report",
            {},
        )

        traits = evolutionary.get(
            "adaptive_trait_memory",
            {},
        ).get(
            "traits",
            [],
        )

        task_signature = runtime_context.get(
            "task_signature",
            {},
        )

        task_shape = task_signature.get(
            "shape",
            "unknown",
        )

        transferred = []

        for trait in traits:

            fitness = _clamp(
                trait.get(
                    "fitness",
                    0.0,
                ),
            )

            inheritance = _clamp(
                trait.get(
                    "inheritance_strength",
                    0.0,
                ),
            )

            stability = _clamp(
                trait.get(
                    "stability_score",
                    0.0,
                ),
            )

            transfer_score = _clamp(
                fitness * 0.40
                +
                inheritance * 0.34
                +
                stability * 0.26
            )

            if transfer_score <= 0.24:

                continue

            transferred.append({
                "trait_id":
                trait.get(
                    "id",
                    trait.get(
                        "trait",
                        "unknown",
                    ),
                ),

                "source_niche":
                trait.get(
                    "niche",
                    "general_adaptation",
                ),

                "target_task_shape":
                task_shape,

                "transfer_score":
                transfer_score,

                "transfer_policy":
                (
                    "direct_transfer"
                    if transfer_score >= 0.68
                    else "rehearsed_transfer"
                    if transfer_score >= 0.42
                    else "shadow_transfer"
                ),
            })

        self.transfer_memory.extend(
            copy.deepcopy(
                transferred,
            )
        )

        self.transfer_memory = (
            self.transfer_memory[-256:]
        )

        return transferred[:64]

    def build_causal_abstractions(self, causal_report):

        abstractions = []

        for dependency in causal_report.get(
            "dependencies",
            [],
        ):

            source = dependency.get(
                "source",
                "unknown",
            )

            target = dependency.get(
                "target",
                "unknown",
            )

            abstractions.append({
                "causal_abstraction_id":
                f"causal_abstraction:{len(abstractions) + 1}",

                "source_cause":
                source,

                "target_effect":
                target,

                "abstract_causal_rule":
                f"{source}_implies_{target}",

                "causal_strength":
                _clamp(
                    causal_report.get(
                        "causal_strength",
                        0.0,
                    ),
                ),
            })

        return abstractions[:64]

    def build_symbolic_analogies(self, analogical_report, transfer_insight):

        analogies = []

        for match in analogical_report.get(
            "matches",
            [],
        )[:32]:

            experience = match.get(
                "experience",
                {},
            )

            analogies.append({
                "analogy_id":
                f"symbolic_analogy:{len(analogies) + 1}",

                "similarity":
                _clamp(
                    match.get(
                        "similarity",
                        0.0,
                    ),
                ),

                "source_task_signature":
                experience.get(
                    "task_signature",
                    {},
                ),

                "mapped_reasoning":
                experience.get(
                    "reasoning_result",
                    {},
                ),

                "analogy_policy":
                (
                    "reuse_with_adaptation"
                    if match.get(
                        "similarity",
                        0.0,
                    )
                    >= 0.72
                    else "compare_only"
                ),
            })

        if transfer_insight.get(
            "transfer_detected",
            False,
        ):

            analogies.append({
                "analogy_id":
                "symbolic_analogy:transfer_insight",

                "similarity":
                _clamp(
                    transfer_insight.get(
                        "transfer_confidence",
                        0.0,
                    ),
                ),

                "mapped_reasoning":
                transfer_insight.get(
                    "recommended_reasoning",
                    {},
                ),

                "analogy_policy":
                "transfer_insight",
            })

        return analogies[:64]

    def run_cycle(
        self,
        runtime_context,
        symbolic_report,
        causal_report,
        analogical_report,
        transfer_insight,
        spatial_report,
    ):

        if not isinstance(
            runtime_context,
            dict,
        ):

            runtime_context = {}

        abstract_rules = self.extract_abstract_rules(
            symbolic_report,
            spatial_report,
        )

        transferable_traits = self.transfer_traits_across_tasks(
            runtime_context,
        )

        causal_abstractions = self.build_causal_abstractions(
            causal_report,
        )

        symbolic_analogies = self.build_symbolic_analogies(
            analogical_report,
            transfer_insight,
        )

        generalization_strength = _clamp(
            len(
                abstract_rules,
            )
            / 16
            * 0.25
            +
            len(
                transferable_traits,
            )
            / 8
            * 0.25
            +
            len(
                causal_abstractions,
            )
            / 12
            * 0.25
            +
            len(
                symbolic_analogies,
            )
            / 8
            * 0.25
        )

        report = {
            "system":
            "arc_generalization_engine",

            "generalization_mode":
            "arc_to_general_adaptive_cognition",

            "abstract_rules":
            abstract_rules,

            "abstract_rule_count":
            len(
                abstract_rules,
            ),

            "transferable_traits":
            transferable_traits,

            "transferable_trait_count":
            len(
                transferable_traits,
            ),

            "causal_abstractions":
            causal_abstractions,

            "causal_abstraction_count":
            len(
                causal_abstractions,
            ),

            "symbolic_analogies":
            symbolic_analogies,

            "symbolic_analogy_count":
            len(
                symbolic_analogies,
            ),

            "generalization_strength":
            generalization_strength,

            "generalization_state":
            (
                "general_adaptive_cognition"
                if generalization_strength >= 0.58
                else "arc_generalization_forming"
                if generalization_strength > 0.0
                else "awaiting_transferable_structure"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.abstract_rule_memory.extend(
            copy.deepcopy(
                abstract_rules,
            )
        )

        self.abstract_rule_memory = (
            self.abstract_rule_memory[-512:]
        )

        self.generalization_history.append(
            copy.deepcopy(
                report,
            )
        )

        self.generalization_history = (
            self.generalization_history[-128:]
        )

        return report


generalization_engine = (
    ARCGeneralizationEngine()
)
