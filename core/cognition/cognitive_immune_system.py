# ============================================
# NEXRYN COGNITIVE IMMUNE SYSTEM
# ============================================

from datetime import datetime


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


MAX_MERGE_ATTEMPTS_PER_FAMILY = 4
MAX_LATENT_CONFLICT_MEMORY = 128


class CognitiveImmuneSystem:

    def __init__(self):

        self.latent_conflict_memory = []
        self.merge_attempts = {}
        self.immune_history = []

    def _tokens(self, value):

        if value is None:

            return set()

        if isinstance(
            value,
            (list, tuple, set),
        ):

            tokens = set()

            for item in value:

                tokens.update(
                    self._tokens(
                        item,
                    )
                )

            return tokens

        return set(
            str(
                value,
            )
            .lower()
            .replace(
                "-",
                "_",
            )
            .split(
                "_",
            )
        )

    def _concept_id(self, concept):

        if isinstance(
            concept,
            dict,
        ):

            return concept.get(
                "concept",
                concept.get(
                    "concept_id",
                    concept.get(
                        "meta_concept_id",
                        concept.get(
                            "id",
                            "unknown_concept",
                        ),
                    ),
                ),
            )

        return str(
            concept,
        )

    def _family_for(self, concept_id):

        tokens = self._tokens(
            concept_id,
        )

        if "preservation" in tokens or "preserve" in tokens:

            subtype = sorted(
                tokens
                -
                {
                    "preservation",
                    "preserve",
                }
            )

            return (
                "preservation_family",
                "_".join(
                    subtype,
                )
                or "general",
            )

        if "translation" in tokens or "motion" in tokens:

            return (
                "motion_family",
                "_".join(
                    sorted(
                        tokens
                        -
                        {
                            "translation",
                            "motion",
                        }
                    )
                )
                or "general",
            )

        if "object" in tokens:

            return (
                "object_family",
                "_".join(
                    sorted(
                        tokens
                        -
                        {
                            "object",
                        }
                    )
                )
                or "general",
            )

        return (
            "general_family",
            "_".join(
                sorted(
                    tokens,
                )
            )
            or "unknown",
        )

    def _concepts_from_context(self, context):

        concepts = []

        concepts.extend(
            context.get(
                "candidate_concepts",
                [],
            )
        )

        concepts.extend(
            context.get(
                "semantic_graph",
                {},
            ).get(
                "concept_nodes",
                [],
            )
        )

        for fusion in context.get(
            "concept_fusion_report",
            {},
        ).get(
            "fused_concepts",
            [],
        ):

            concepts.append(
                fusion.get(
                    "meta_concept",
                    fusion,
                )
            )

        return [
            concept
            if isinstance(
                concept,
                dict,
            )
            else {
                "concept":
                concept,
            }
            for concept in concepts
        ]

    def identity_canonicalization(self, context):

        families = {}

        for concept in self._concepts_from_context(
            context,
        ):

            concept_id = self._concept_id(
                concept,
            )

            family, subtype = self._family_for(
                concept_id,
            )

            families.setdefault(
                family,
                [],
            ).append({
                "concept":
                concept_id,

                "canonical_identity":
                f"{family}/{subtype}",

                "subtype":
                subtype,

                "inheritance":
                family,

                "semantic_ancestry":
                [
                    family,
                    subtype,
                ],
            })

        return {
            "canonical_families":
            families,

            "family_count":
            len(
                families,
            ),

            "canonicalization_state":
            (
                "identity_families_canonicalized"
                if families
                else "no_identity_variants_observed"
            ),
        }

    def hidden_conflict_detection_stabilization(self, context):

        reasoner = context.get(
            "identity_reasoner_report",
            {},
        )

        new_conflicts = []

        for analysis in reasoner.get(
            "identity_analyses",
            [],
        ):

            hidden = (
                analysis.get(
                    "failure_explanation",
                    {},
                ).get(
                    "hidden_conflicts",
                    {},
                )
            )

            if not hidden.get(
                "hidden_conflict_detected",
                False,
            ):

                continue

            overlap = analysis.get(
                "overlap",
                {},
            )

            conflict = {
                "source":
                overlap.get(
                    "source",
                    "unknown",
                ),

                "target":
                overlap.get(
                    "target",
                    "unknown",
                ),

                "conflict_layers":
                hidden.get(
                    "conflict_layers",
                    [],
                ),

                "merge_state":
                analysis.get(
                    "merge_stability",
                    {},
                ).get(
                    "merge_state",
                    "unknown",
                ),
            }

            key = (
                conflict.get(
                    "source",
                ),
                conflict.get(
                    "target",
                ),
                tuple(
                    conflict.get(
                        "conflict_layers",
                        [],
                    )
                ),
            )

            existing = {
                (
                    item.get(
                        "source",
                    ),
                    item.get(
                        "target",
                    ),
                    tuple(
                        item.get(
                            "conflict_layers",
                            [],
                        )
                    ),
                )
                for item in self.latent_conflict_memory
            }

            if key not in existing:

                conflict[
                    "timestamp"
                ] = str(
                    datetime.utcnow()
                )

                self.latent_conflict_memory.append(
                    conflict,
                )

                new_conflicts.append(
                    conflict,
                )

        self.latent_conflict_memory = (
            self.latent_conflict_memory[-MAX_LATENT_CONFLICT_MEMORY:]
        )

        return {
            "new_latent_conflicts":
            new_conflicts,

            "latent_conflict_memory":
            self.latent_conflict_memory[-20:],

            "latent_conflict_count":
            len(
                self.latent_conflict_memory,
            ),

            "hidden_conflict_state":
            (
                "latent_conflicts_stabilized"
                if self.latent_conflict_memory
                else "no_latent_conflicts_observed"
            ),
        }

    def merge_exhaustion_prevention(self, canonical_report, context):

        fusion = context.get(
            "concept_fusion_report",
            {},
        )

        exhausted = []

        for item in (
            fusion.get(
                "fused_concepts",
                [],
            )
            +
            fusion.get(
                "rejected_fusions",
                [],
            )
        ):

            meta = item.get(
                "meta_concept",
                {},
            )

            concept_id = meta.get(
                "meta_concept_id",
                item.get(
                    "overlap",
                    {},
                ).get(
                    "source",
                    "unknown",
                ),
            )

            family, _ = self._family_for(
                concept_id,
            )

            self.merge_attempts[
                family
            ] = (
                self.merge_attempts.get(
                    family,
                    0,
                )
                + 1
            )

        for family, attempts in self.merge_attempts.items():

            if attempts > MAX_MERGE_ATTEMPTS_PER_FAMILY:

                exhausted.append({
                    "family":
                    family,

                    "attempts":
                    attempts,

                    "policy":
                    "freeze_family_merges",
                })

        return {
            "merge_attempts":
            dict(
                self.merge_attempts,
            ),

            "exhausted_families":
            exhausted,

            "merge_budget":
            MAX_MERGE_ATTEMPTS_PER_FAMILY,

            "merge_exhaustion_state":
            (
                "merge_exhaustion_detected"
                if exhausted
                else "merge_budget_available"
            ),
        }

    def semantic_fever_detection(self, context):

        reasoner = context.get(
            "identity_reasoner_report",
            {},
        )

        repair_required = reasoner.get(
            "repair_required_count",
            0,
        )

        memory_pressure = _clamp(
            context.get(
                "memory_pressure_score",
                1.0
                -
                context.get(
                    "memory_compression_report",
                    {},
                ).get(
                    "compression_ratio",
                    1.0,
                ),
            )
        )

        identity_drift = _clamp(
            context.get(
                "identity_continuity_guardian_report",
                {},
            ).get(
                "drift_monitoring",
                {},
            ).get(
                "drift_pressure",
                0.0,
            )
        )

        repair_pressure = _clamp(
            repair_required
            / 64
        )

        fever_score = _clamp(
            repair_pressure * 0.36
            +
            memory_pressure * 0.40
            +
            identity_drift * 0.24
        )

        return {
            "repair_required_count":
            repair_required,

            "memory_pressure_score":
            memory_pressure,

            "identity_drift":
            identity_drift,

            "cognitive_fever_score":
            fever_score,

            "cognitive_fever_state":
            (
                "cognitive_fever_state"
                if fever_score >= 0.66
                else "fever_watch"
                if fever_score >= 0.42
                else "immune_stable"
            ),
        }

    def immune_policy(self, fever_report, merge_report):

        fever = (
            fever_report.get(
                "cognitive_fever_state",
            )
            == "cognitive_fever_state"
        )

        exhausted = bool(
            merge_report.get(
                "exhausted_families",
                [],
            )
        )

        return {
            "freeze_new_fusions":
            fever or exhausted,

            "freeze_neurogenesis":
            fever,

            "aggressive_compression":
            fever,

            "sandbox_only_mode":
            fever or exhausted,

            "immune_policy_state":
            (
                "immune_lockdown"
                if fever
                else "family_merge_freeze"
                if exhausted
                else "immune_monitoring"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        canonical = self.identity_canonicalization(
            context,
        )

        hidden = self.hidden_conflict_detection_stabilization(
            context,
        )

        merge = self.merge_exhaustion_prevention(
            canonical,
            context,
        )

        fever = self.semantic_fever_detection(
            context,
        )

        policy = self.immune_policy(
            fever,
            merge,
        )

        report = {
            "system":
            "cognitive_immune_system",

            "immune_mode":
            "identity_canonicalization_latent_conflict_fever_control",

            "identity_canonicalization":
            canonical,

            "hidden_conflict_stabilization":
            hidden,

            "merge_exhaustion_prevention":
            merge,

            "semantic_fever_detection":
            fever,

            "immune_policy":
            policy,

            "cognitive_immune_state":
            policy.get(
                "immune_policy_state",
                "immune_monitoring",
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.immune_history.append(
            report,
        )

        self.immune_history = (
            self.immune_history[-128:]
        )

        return report


cognitive_immune_system = CognitiveImmuneSystem()
