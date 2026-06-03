# ============================================
# NEXRYN EXTINCTION ENGINE
# ============================================

from datetime import datetime

from core.cognitive_genetics.constitutional_trait_protection import (
    constitutional_trait_protection,
)


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


class ExtinctionEngine:

    def __init__(self, decay_threshold=2, suppressed_threshold=1):

        self.decay_threshold = decay_threshold
        self.suppressed_threshold = suppressed_threshold
        self.decay_counters = {}
        self.suppressed_counters = {}
        self.extinction_archive = []
        self.extinction_history = []

    def _trait_id(self, trait):

        return trait.get(
            "id",
            trait.get(
                "trait_id",
                trait.get(
                    "trait",
                    "unknown",
                ),
            ),
        )

    def _natural_selection(self, context):

        return context.get(
            "cognitive_natural_selection_report",
            {},
        )

    def _promotion_grace_traits(self, context):

        return set(
            context.get(
                "epistemic_promotion_grace_report",
                {},
            ).get(
                "traits",
                [],
            )
        )

    def _active_traits(self, context):

        natural_selection = self._natural_selection(
            context,
        )

        traits = []

        for key in [
            "selected_traits",
            "decaying_traits",
            "suppressed_traits",
            "extinct_traits",
        ]:

            traits.extend(
                natural_selection.get(
                    key,
                    [],
                )
            )

        if traits:

            return traits

        return (
            context.get(
                "evolutionary_memory_report",
                {},
            )
            .get(
                "adaptive_trait_memory",
                {},
            )
            .get(
                "traits",
                [],
            )
        )

    def track_decay(self, traits):

        active_trait_ids = set()

        for trait in traits:

            trait_id = self._trait_id(
                trait,
            )

            active_trait_ids.add(
                trait_id,
            )

            state = trait.get(
                "trait_state",
                "candidate",
            )

            if state == "decaying":

                self.decay_counters[
                    trait_id
                ] = (
                    self.decay_counters.get(
                        trait_id,
                        0,
                    )
                    + 1
                )

            elif state in [
                "adaptive",
                "dominant",
            ]:

                self.decay_counters[
                    trait_id
                ] = max(
                    self.decay_counters.get(
                        trait_id,
                        0,
                    )
                    - 1,
                    0,
                )

            if state == "suppressed":

                self.suppressed_counters[
                    trait_id
                ] = (
                    self.suppressed_counters.get(
                        trait_id,
                        0,
                    )
                    + 1
                )

            elif state in [
                "adaptive",
                "dominant",
                "candidate",
            ]:

                self.suppressed_counters[
                    trait_id
                ] = 0

        for known_id in list(
            self.decay_counters.keys()
        ):

            if known_id not in active_trait_ids:

                self.decay_counters.pop(
                    known_id,
                    None,
                )

        for known_id in list(
            self.suppressed_counters.keys()
        ):

            if known_id not in active_trait_ids:

                self.suppressed_counters.pop(
                    known_id,
                    None,
                )

        return {
            "decay_counters":
            dict(
                self.decay_counters,
            ),

            "suppressed_counters":
            dict(
                self.suppressed_counters,
            ),
        }

    def archive_trait(self, trait, reason):

        archived = {
            "trait_id":
            self._trait_id(
                trait,
            ),

            "reason":
            reason,

            "trait_snapshot":
            dict(
                trait,
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.extinction_archive.append(
            archived,
        )

        self.extinction_archive = (
            self.extinction_archive[-512:]
        )

        return archived

    def suppress_trait(self, trait, reason):

        updated = dict(
            trait,
        )

        updated[
            "trait_state"
        ] = "suppressed"

        return {
            "trait_id":
            self._trait_id(
                trait,
            ),

            "action":
            "suppress_trait",

            "reason":
            reason,

            "trait":
            updated,
        }

    def delete_trait(self, trait, reason):

        updated = dict(
            trait,
        )

        updated[
            "trait_state"
        ] = "extinct"

        return {
            "trait_id":
            self._trait_id(
                trait,
            ),

            "action":
            "delete_trait",

            "reason":
            reason,

            "trait":
            updated,
        }

    def reclaim_resources(self, trait):

        resource_costs = trait.get(
            "resource_costs",
            {},
        )

        if not resource_costs:

            resource_costs = {
                "memory_cost":
                _clamp(
                    0.08
                    +
                    len(
                        trait.get(
                            "survival_history",
                            [],
                        )
                    )
                    * 0.03
                ),

                "attention_cost":
                _clamp(
                    0.10
                    +
                    (
                        1.0
                        -
                        trait.get(
                            "fitness",
                            0.0,
                        )
                    )
                    * 0.16
                ),

                "mutation_cost":
                _clamp(
                    trait.get(
                        "mutation_rate",
                        0.1,
                    )
                    * 0.72
                ),

                "evaluation_cost":
                _clamp(
                    0.07
                    +
                    (
                        1.0
                        -
                        trait.get(
                            "stability_score",
                            0.0,
                        )
                    )
                    * 0.12
                ),
            }

        return {
            "memory":
            _clamp(
                resource_costs.get(
                    "memory_cost",
                    0.0,
                )
            ),

            "attention":
            _clamp(
                resource_costs.get(
                    "attention_cost",
                    0.0,
                )
            ),

            "mutation_cycles":
            _clamp(
                resource_costs.get(
                    "mutation_cost",
                    resource_costs.get(
                        "execution_cost",
                        0.0,
                    ),
                )
            ),

            "evaluation_bandwidth":
            _clamp(
                resource_costs.get(
                    "evaluation_cost",
                    resource_costs.get(
                        "maintenance_cost",
                        0.0,
                    ),
                )
            ),
        }

    def _resource_totals(self, reclaimed):

        totals = {
            "memory":
            0.0,

            "attention":
            0.0,

            "mutation_cycles":
            0.0,

            "evaluation_bandwidth":
            0.0,
        }

        for item in reclaimed:

            resources = item.get(
                "resources",
                {},
            )

            for key in totals:

                totals[
                    key
                ] += resources.get(
                    key,
                    0.0,
                )

        return {
            key:
            _clamp(value)
            for key, value in totals.items()
        }

    def compute_graveyard_pressure(
        self,
        context,
        decaying_traits,
        suppressed_traits,
        extinct_traits,
        actions,
    ):

        failure_memory = context.get(
            "cognitive_failure_memory",
            {},
        ).get(
            "latest_failure",
            {},
        )

        concept_fusion_report = context.get(
            "concept_fusion_report",
            {},
        )

        lineage_report = context.get(
            "concept_lineage_report",
            {},
        )

        entropy_report = context.get(
            "entropy_regulator_report",
            {},
        )

        rejected_merges = len(
            concept_fusion_report.get(
                "rejected_fusions",
                [],
            )
        )

        unsafe_failures = (
            1
            if failure_memory.get(
                "contradiction_type",
            )
            in [
                "unsafe_merge",
                "unsafe_evolution",
                "destructive_mutation",
            ]
            else 0
        )

        ontology_damage = _clamp(
            failure_memory.get(
                "ontology_damage",
                0.0,
            )
        )

        unstable_lineages = 0
        unsafe_mutations = 0

        for record in lineage_report.get(
            "lineage_records",
            [],
        ):

            for mutation in record.get(
                "mutations",
                [],
            ):

                mutation_type = mutation.get(
                    "type",
                    "",
                )

                survival_state = mutation.get(
                    "survival_state",
                    "",
                )

                if (
                    "unsafe" in mutation_type
                    or "destructive" in mutation_type
                ):

                    unsafe_mutations += 1

                if survival_state in [
                    "extinct",
                    "rejected",
                    "collapsed",
                ]:

                    unstable_lineages += 1

        entropy_pruning_pressure = 0.0

        if entropy_report.get(
            "stabilization_windows",
            {},
        ).get(
            "window_state",
        ) == "freeze_new_mutations":

            entropy_pruning_pressure = 1.0

        pressure = _clamp(
            len(
                extinct_traits,
            )
            * 0.16
            +
            len(
                suppressed_traits,
            )
            * 0.08
            +
            len(
                decaying_traits,
            )
            * 0.05
            +
            len([
                action
                for action in actions
                if action.get(
                    "action",
                )
                == "delete_trait"
            ])
            * 0.18
            +
            rejected_merges
            * 0.12
            +
            unstable_lineages
            * 0.10
            +
            unsafe_mutations
            * 0.14
            +
            unsafe_failures
            * 0.18
            +
            ontology_damage
            * 0.22
            +
            entropy_pruning_pressure
            * 0.10
        )

        return {
            "pressure_score":
            pressure,

            "pressure_state":
            (
                "graveyard_pressure_critical"
                if pressure >= 0.72
                else "graveyard_pressure_high"
                if pressure >= 0.48
                else "graveyard_pressure_elevated"
                if pressure >= 0.24
                else "graveyard_pressure_low"
            ),

            "pressure_factors":
            {
                "failed_merges":
                rejected_merges,

                "unstable_lineages":
                unstable_lineages,

                "ontology_damage":
                ontology_damage,

                "entropy_pruning_pressure":
                entropy_pruning_pressure,

                "extinct_concepts":
                len(
                    extinct_traits,
                ),

                "unsafe_evolution":
                unsafe_failures
                +
                unsafe_mutations,

                "suppressed_concepts":
                len(
                    suppressed_traits,
                ),
            },

            "psychological_load":
            (
                "lineage_trauma_active"
                if pressure >= 0.48
                else "evolutionary_stress_detected"
                if pressure >= 0.24
                else "graveyard_load_tolerable"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        traits = self._active_traits(
            context,
        )

        tracking_report = self.track_decay(
            traits,
        )
        promotion_grace_traits = self._promotion_grace_traits(
            context,
        )

        surviving_traits = []
        decaying_traits = []
        suppressed_traits = []
        extinct_traits = []
        actions = []
        archived_traits = []
        reclaimed_resources = []

        for trait in traits:

            trait_id = self._trait_id(
                trait,
            )

            state = trait.get(
                "trait_state",
                "candidate",
            )

            decay_count = self.decay_counters.get(
                trait_id,
                0,
            )

            suppressed_count = self.suppressed_counters.get(
                trait_id,
                0,
            )

            if (
                trait_id in promotion_grace_traits
                and state in [
                    "decaying",
                    "suppressed",
                    "extinct",
                ]
            ):

                protected = dict(
                    trait,
                )

                protected[
                    "epistemic_trial_grace"
                ] = True

                protected[
                    "extinction_delay_reason"
                ] = "active_epistemic_promotion_trial"

                surviving_traits.append(
                    protected,
                )

                actions.append({
                    "trait_id":
                    trait_id,

                    "action":
                    "delay_extinction_for_epistemic_trial",

                    "reason":
                    "active_epistemic_promotion_trial",
                })

                continue

            if (
                state == "decaying"
                and decay_count > self.decay_threshold
            ):

                action = self.delete_trait(
                    trait,
                    "decay_counter_exceeded_threshold",
                )

                archive = self.archive_trait(
                    action.get(
                        "trait",
                        trait,
                    ),
                    "extinct_after_persistent_decay",
                )

                resources = self.reclaim_resources(
                    trait,
                )

                extinct_traits.append(
                    action.get(
                        "trait",
                    )
                )

                actions.append(
                    action,
                )

                archived_traits.append(
                    archive,
                )

                reclaimed_resources.append({
                    "trait_id":
                    trait_id,

                    "resources":
                    resources,
                })

            elif (
                state == "suppressed"
                and suppressed_count > self.suppressed_threshold
            ):

                action = self.delete_trait(
                    trait,
                    "suppressed_trait_failed_recovery_window",
                )

                archive = self.archive_trait(
                    action.get(
                        "trait",
                        trait,
                    ),
                    "extinct_after_suppression_window",
                )

                resources = self.reclaim_resources(
                    trait,
                )

                extinct_traits.append(
                    action.get(
                        "trait",
                    )
                )

                actions.append(
                    action,
                )

                archived_traits.append(
                    archive,
                )

                reclaimed_resources.append({
                    "trait_id":
                    trait_id,

                    "resources":
                    resources,
                })

            elif (
                state == "decaying"
                and decay_count >= self.decay_threshold
            ):

                action = self.suppress_trait(
                    trait,
                    "decay_counter_reached_threshold",
                )

                suppressed_traits.append(
                    action.get(
                        "trait",
                    )
                )

                actions.append(
                    action,
                )

            elif state == "decaying":

                decaying_traits.append(
                    trait,
                )

            elif state == "suppressed":

                suppressed_traits.append(
                    trait,
                )

            elif state == "extinct":

                action = self.delete_trait(
                    trait,
                    "extinct_after_epistemic_trial_window",
                )

                archive = self.archive_trait(
                    action.get(
                        "trait",
                        trait,
                    ),
                    "extinct_after_epistemic_trial_window",
                )

                extinct_traits.append(
                    action.get(
                        "trait",
                    )
                )

                actions.append(
                    action,
                )

                archived_traits.append(
                    archive,
                )

            else:

                surviving_traits.append(
                    trait,
                )

        # ====================================
        # CONSTITUTIONAL TRAIT PROTECTION
        # ====================================
        # Prevent extinction of core stability traits
        
        protected_extinct = []
        for trait in extinct_traits:
            protected = (
                constitutional_trait_protection
                .protect_trait_from_extinction(
                    trait,
                )
            )
            if protected.get("trait_state") != "extinct":
                protected_extinct.append(protected)
                surviving_traits.append(protected)
        
        # Remove protected traits from extinct list
        extinct_traits = [
            t
            for t in extinct_traits
            if t.get("trait_name", "")
            not in [
                p.get("trait_name", "")
                for p in protected_extinct
            ]
        ]

        # Enforce asymmetry constraints
        asymmetry_report = (
            constitutional_trait_protection
            .enforce_asymmetry_constraints(
                surviving_traits,
                extinct_traits,
            )
        )

        # Inject any protected traits that were lost
        for trait in asymmetry_report.get(
            "protected_traits_injected", []
        ):
            surviving_traits.append(trait)

        # Monitor selection imbalance
        imbalance_monitor = (
            constitutional_trait_protection
            .monitor_selection_imbalance(
                context,
            )
        )

        graveyard_pressure = self.compute_graveyard_pressure(
            context,
            decaying_traits,
            suppressed_traits,
            extinct_traits,
            actions,
        )

        # ====================================
        # BUILD REPORT WITH PROTECTION
        # ====================================

        report = {
            "system":
            "extinction_engine",

            "extinction_mode":
            "decay_counter_resource_reclamation",

            "decay_threshold":
            self.decay_threshold,

            "suppressed_threshold":
            self.suppressed_threshold,

            "decay_counters":
            tracking_report.get(
                "decay_counters",
                {},
            ),

            "suppressed_counters":
            tracking_report.get(
                "suppressed_counters",
                {},
            ),

            "surviving_traits":
            surviving_traits,

            "decaying_traits":
            decaying_traits,

            "suppressed_traits":
            suppressed_traits,

            "extinct_traits":
            extinct_traits,

            "selection_actions":
            actions,

            "archived_traits":
            archived_traits,

            "extinction_archive":
            self.extinction_archive[-32:],

            "epistemic_promotion_grace":
            {
                "protected_trait_ids":
                sorted(
                    promotion_grace_traits,
                ),

                "protection_count":
                len(
                    promotion_grace_traits,
                ),

                "survival_is_not_truth":
                True,
            },

            "reclaimed_resources":
            reclaimed_resources,

            "resource_reclamation_totals":
            self._resource_totals(
                reclaimed_resources,
            ),

            "surviving_count":
            len(
                surviving_traits,
            ),

            "decaying_count":
            len(
                decaying_traits,
            ),

            "suppressed_count":
            len(
                suppressed_traits,
            ),

            "extinct_count":
            len(
                extinct_traits,
            ),

            "graveyard_pressure":
            graveyard_pressure,

            "extinction_state":
            (
                "extinction_wave"
                if extinct_traits
                else "suppression_active"
                if suppressed_traits
                else "decay_monitoring"
                if decaying_traits
                else "trait_pool_clean"
            ),

            "constitutional_protection":
            {
                "extinctions_prevented": len(protected_extinct),
                "traits_protected": protected_extinct,
                "asymmetry_constraints_enforced": (
                    asymmetry_report.get(
                        "asymmetry_constraint_enforced",
                        False,
                    )
                ),
                "traits_resurrected": asymmetry_report.get(
                    "reprotected_from_extinction",
                    [],
                ),
                "selection_imbalance_threat": (
                    imbalance_monitor.get(
                        "asymmetry_threat",
                        False,
                    )
                ),
                "imbalance_level": (
                    imbalance_monitor.get(
                        "threat_level",
                        "normal",
                    )
                ),
            },

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.extinction_history.append(
            report,
        )

        self.extinction_history = (
            self.extinction_history[-128:]
        )

        return report


extinction_engine = ExtinctionEngine()
