# ============================================
# NEXRYN CONTROLLED SAFE NOVELTY
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
                maximum
            )
        ),
        4
    )


def _as_list(value):

    if isinstance(
        value,
        list
    ):

        return value

    if value is None:

        return []

    return [
        value
    ]


def _entropy(context):

    report = context.get(
        "cognitive_entropy_report",
        {}
    )

    return _clamp(
        report.get(
            "runtime_entropy",
            context.get(
                "runtime_entropy",
                0.0
            )
        )
    )


def _identity_protection_pressure(context):

    identity = context.get(
        "cognitive_identity_report",
        {}
    )

    identity_core = context.get(
        "identity_core_report",
        {}
    )

    identity_anchor = context.get(
        "identity_anchor_core_report",
        {}
    )

    executive_state = str(
        context.get(
            "executive_state",
            identity.get(
                "identity_state",
                ""
            )
        )
    )

    base = (
        identity.get(
            "identity_risk",
            0.0
        )
        * 0.40
        +
        identity_core.get(
            "identity_drift",
            0.0
        )
        * 0.30
        +
        identity_anchor.get(
            "identity_drift_before",
            0.0
        )
        * 0.30
    )

    if "identity_protection" in executive_state:

        base += 0.22

    if identity.get(
        "identity_state"
    ) == "identity_guarded":

        base += 0.12

    return _clamp(
        base
    )


class SafeExploratorySandbox:

    def __init__(self):

        self.sandbox_history = []

    def collect_experiments(self, context):

        experiments = []

        for key, experiment_type in [
            ("rejected_merges", "merge"),
            ("mutation_candidates", "mutation"),
            ("recursive_paths", "recursive_branch"),
            ("reasoning_hypotheses", "hypothesis"),
        ]:

            for index, item in enumerate(
                _as_list(
                    context.get(
                        key,
                        []
                    )
                )
            ):

                experiments.append({
                    "experiment_id":
                    f"{experiment_type}:{index}",

                    "experiment_type":
                    experiment_type,

                    "source":
                    key,

                    "payload":
                    item,
                })

        if not experiments:

            experiments.append({
                "experiment_id":
                "novelty:seed",

                "experiment_type":
                "mutation",

                "source":
                "controlled_safe_novelty",

                "payload":
                {
                    "proposal":
                    "low_risk_semantic_variant"
                },
            })

        return experiments[:24]

    def run(self, context, immunity_report):

        experiments = self.collect_experiments(
            context
        )

        tolerance = immunity_report.get(
            "adaptive_tolerance",
            0.25
        )

        sandboxed = []

        for experiment in experiments:

            risk = (
                0.32
                if experiment.get(
                    "experiment_type"
                )
                in [
                    "mutation",
                    "hypothesis",
                ]
                else 0.46
                if experiment.get(
                    "experiment_type"
                )
                == "merge"
                else 0.52
            )

            sandboxed.append({
                "experiment_id":
                experiment.get(
                    "experiment_id"
                ),

                "experiment_type":
                experiment.get(
                    "experiment_type"
                ),

                "isolation":
                "core_identity_detached",

                "sandbox_risk":
                _clamp(
                    risk
                ),

                "admission":
                (
                    "simulate"
                    if risk <= tolerance + 0.25
                    else "quarantine"
                ),
            })

        report = {
            "system":
            "safe_exploratory_sandbox",

            "sandbox_mode":
            "isolated_novelty_lab",

            "experiments":
            sandboxed,

            "simulation_count":
            len([
                item
                for item in sandboxed
                if item.get(
                    "admission"
                )
                == "simulate"
            ]),

            "quarantine_count":
            len([
                item
                for item in sandboxed
                if item.get(
                    "admission"
                )
                == "quarantine"
            ]),

            "core_identity_contamination":
            0.0,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.sandbox_history.append(
            report
        )

        self.sandbox_history = (
            self.sandbox_history[-32:]
        )

        return report


class SemanticImmuneConfidenceCalibration:

    def __init__(self):

        self.calibration_history = []

    def calibrate(self, context):

        entropy = _entropy(
            context
        )

        protection_pressure = _identity_protection_pressure(
            context
        )

        rigidity = _clamp(
            entropy * 0.45
            +
            protection_pressure * 0.55
        )

        tolerance = _clamp(
            0.18
            +
            (1.0 - entropy) * 0.20
            +
            min(
                protection_pressure,
                0.55
            )
            * 0.35
        )

        merge_threshold = _clamp(
            0.78
            -
            tolerance * 0.22
        )

        mutation_threshold = _clamp(
            0.70
            -
            tolerance * 0.18
        )

        report = {
            "system":
            "semantic_immune_confidence_calibration",

            "runtime_entropy":
            entropy,

            "identity_protection_pressure":
            protection_pressure,

            "rigidity_risk":
            rigidity,

            "adaptive_tolerance":
            tolerance,

            "dynamic_thresholds":
            {
                "merge_review_threshold":
                merge_threshold,

                "mutation_review_threshold":
                mutation_threshold,

                "novelty_release_threshold":
                _clamp(
                    0.64
                    +
                    entropy * 0.12
                ),
            },

            "immunity_state":
            (
                "de_escalated"
                if protection_pressure >= 0.55
                else "context_aware"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.calibration_history.append(
            report
        )

        self.calibration_history = (
            self.calibration_history[-32:]
        )

        return report


class ConceptiveNeurogenesis:

    def __init__(self):

        self.generated_concepts = []

    def generate(self, context, immunity_report, sandbox_report):

        entropy = immunity_report.get(
            "runtime_entropy",
            0.0
        )

        tolerance = immunity_report.get(
            "adaptive_tolerance",
            0.0
        )

        seeds = []

        for item in context.get(
            "semantic_distance_fields_report",
            {}
        ).get(
            "high_risk_merge_pairs",
            []
        )[:4]:

            seeds.append(
                f"bridge_{item.get('first')}_{item.get('second')}"
            )

        if not seeds:

            seeds = [
                "elastic_identity_variant",
                "sandboxed_merge_hypothesis",
                "low_entropy_novelty_route",
            ]

        generated = []

        for seed in seeds[:6]:

            viability = _clamp(
                tolerance * 0.55
                +
                (1.0 - entropy) * 0.25
                +
                sandbox_report.get(
                    "simulation_count",
                    0
                )
                / 24
                * 0.20
            )

            generated.append({
                "concept":
                seed,

                "origin":
                "conceptive_neurogenesis",

                "viability":
                viability,

                "status":
                (
                    "sandbox_candidate"
                    if viability >= 0.35
                    else "latent_seed"
                ),
            })

        self.generated_concepts.extend(
            generated
        )

        self.generated_concepts = (
            self.generated_concepts[-128:]
        )

        return {
            "system":
            "conceptive_neurogenesis",

            "generated_concepts":
            generated,

            "generated_count":
            len(
                generated
            ),

            "total_generated_concepts":
            len(
                self.generated_concepts
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }


class RecursiveSimulationWorlds:

    def __init__(self):

        self.world_history = []

    def simulate(self, context, sandbox_report):

        worlds = []

        entropy = _entropy(
            context
        )

        for index, experiment in enumerate(
            sandbox_report.get(
                "experiments",
                []
            )[:8]
        ):

            if experiment.get(
                "admission"
            ) != "simulate":

                continue

            stability = _clamp(
                1.0
                -
                entropy * 0.45
                -
                experiment.get(
                    "sandbox_risk",
                    0.0
                )
                * 0.35
            )

            worlds.append({
                "world_id":
                f"sim_world:{index}",

                "source_experiment":
                experiment.get(
                    "experiment_id"
                ),

                "world_model":
                "temporary_recursive_simulation",

                "predicted_entropy_delta":
                _clamp(
                    entropy * 0.20
                    +
                    experiment.get(
                        "sandbox_risk",
                        0.0
                    )
                    * 0.30
                ),

                "identity_continuity":
                stability,

                "release_recommendation":
                (
                    "release_to_latent_memory"
                    if stability >= 0.48
                    else "retain_in_sandbox"
                ),
            })

        report = {
            "system":
            "recursive_simulation_worlds",

            "world_count":
            len(
                worlds
            ),

            "worlds":
            worlds,

            "direct_reasoning_bypass":
            True,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.world_history.append(
            report
        )

        self.world_history = (
            self.world_history[-32:]
        )

        return report


class IdentityElasticityLayer:

    def __init__(self):

        self.elasticity_history = []

    def regulate(self, context, immunity_report, worlds_report):

        protection_pressure = immunity_report.get(
            "identity_protection_pressure",
            0.0
        )

        viable_worlds = [
            world
            for world in worlds_report.get(
                "worlds",
                []
            )
            if world.get(
                "release_recommendation"
            )
            == "release_to_latent_memory"
        ]

        elasticity = _clamp(
            0.20
            +
            immunity_report.get(
                "adaptive_tolerance",
                0.0
            )
            * 0.45
            +
            len(
                viable_worlds
            )
            / 12
            * 0.35
        )

        guardian_mode = (
            "advisor"
            if protection_pressure >= 0.55
            else "guardian"
        )

        report = {
            "system":
            "identity_elasticity_layer",

            "identity_guardian_mode":
            guardian_mode,

            "elasticity":
            elasticity,

            "protected_core":
            [
                "execution_grounding",
                "reward_alignment",
                "temporal_continuity",
            ],

            "elastic_zones":
            [
                "ontology_aliasing",
                "hypothesis_mutation",
                "recursive_branching",
                "novel_concept_generation",
            ],

            "novelty_release_budget":
            _clamp(
                elasticity * 0.65
                +
                (1.0 - _entropy(context)) * 0.20
            ),

            "dictator_prevention":
            {
                "single_guardian_veto":
                False,

                "requires_simulation_evidence":
                True,

                "allows_reversible_experiments":
                True,
            },

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.elasticity_history.append(
            report
        )

        self.elasticity_history = (
            self.elasticity_history[-32:]
        )

        return report


class NoveltyPromotionGate:

    def __init__(self):

        self.promotion_history = []

        self.validation_tasks = [
            "semantic_transfer_probe",
            "identity_continuity_probe",
            "execution_usefulness_probe",
        ]

    def collect_sandbox_concepts(self, neurogenesis_report):

        return [
            concept
            for concept in neurogenesis_report.get(
                "generated_concepts",
                []
            )
            if concept.get(
                "status"
            )
            in [
                "sandbox_candidate",
                "latent_seed",
            ]
        ]

    def evaluate_task(
        self,
        concept,
        task_name,
        context,
        worlds_report,
        elasticity_report
    ):

        viability = concept.get(
            "viability",
            0.0
        )

        entropy = _entropy(
            context
        )

        release_budget = elasticity_report.get(
            "novelty_release_budget",
            0.0
        )

        viable_world_count = len([
            world
            for world in worlds_report.get(
                "worlds",
                []
            )
            if world.get(
                "release_recommendation"
            )
            == "release_to_latent_memory"
        ])

        if task_name == "semantic_transfer_probe":

            execution_usefulness = _clamp(
                viability * 0.55
                +
                release_budget * 0.25
                +
                viable_world_count / 12 * 0.20
            )

            entropy_impact = _clamp(
                entropy * 0.25
                +
                (1.0 - viability) * 0.30
            )

            identity_continuity = _clamp(
                0.50
                +
                release_budget * 0.25
                -
                entropy_impact * 0.20
            )

        elif task_name == "identity_continuity_probe":

            identity_continuity = _clamp(
                0.58
                +
                elasticity_report.get(
                    "elasticity",
                    0.0
                )
                * 0.30
                -
                entropy * 0.22
            )

            entropy_impact = _clamp(
                entropy * 0.18
                +
                max(
                    0.0,
                    0.60 - viability
                )
                * 0.28
            )

            execution_usefulness = _clamp(
                viability * 0.45
                +
                identity_continuity * 0.25
            )

        else:

            execution_usefulness = _clamp(
                viability * 0.50
                +
                viable_world_count / 8 * 0.25
                +
                release_budget * 0.25
            )

            entropy_impact = _clamp(
                entropy * 0.22
                +
                (1.0 - execution_usefulness) * 0.20
            )

            identity_continuity = _clamp(
                0.52
                +
                release_budget * 0.20
                -
                entropy_impact * 0.18
            )

        task_score = _clamp(
            execution_usefulness * 0.40
            +
            identity_continuity * 0.38
            +
            (1.0 - entropy_impact) * 0.22
        )

        return {
            "task":
            task_name,

            "entropy_impact":
            entropy_impact,

            "identity_continuity":
            identity_continuity,

            "execution_usefulness":
            execution_usefulness,

            "task_score":
            task_score,
        }

    def decide(self, aggregate):

        score = aggregate.get(
            "promotion_score",
            0.0
        )

        entropy_impact = aggregate.get(
            "average_entropy_impact",
            1.0
        )

        identity_continuity = aggregate.get(
            "average_identity_continuity",
            0.0
        )

        execution_usefulness = aggregate.get(
            "average_execution_usefulness",
            0.0
        )

        if (
            score >= 0.68
            and
            entropy_impact <= 0.30
            and
            identity_continuity >= 0.62
            and
            execution_usefulness >= 0.55
        ):

            return "promote"

        if (
            score >= 0.42
            and
            identity_continuity >= 0.45
            and
            entropy_impact <= 0.58
        ):

            return "latent"

        return "reject"

    def evaluate(
        self,
        context,
        neurogenesis_report,
        worlds_report,
        elasticity_report
    ):

        concepts = self.collect_sandbox_concepts(
            neurogenesis_report
        )

        evaluations = []

        for concept in concepts:

            task_results = [
                self.evaluate_task(
                    concept,
                    task_name,
                    context,
                    worlds_report,
                    elasticity_report
                )
                for task_name in self.validation_tasks
            ]

            average_entropy_impact = _clamp(
                sum(
                    task.get(
                        "entropy_impact",
                        0.0
                    )
                    for task in task_results
                )
                /
                max(
                    len(
                        task_results
                    ),
                    1
                )
            )

            average_identity_continuity = _clamp(
                sum(
                    task.get(
                        "identity_continuity",
                        0.0
                    )
                    for task in task_results
                )
                /
                max(
                    len(
                        task_results
                    ),
                    1
                )
            )

            average_execution_usefulness = _clamp(
                sum(
                    task.get(
                        "execution_usefulness",
                        0.0
                    )
                    for task in task_results
                )
                /
                max(
                    len(
                        task_results
                    ),
                    1
                )
            )

            promotion_score = _clamp(
                average_execution_usefulness * 0.40
                +
                average_identity_continuity * 0.35
                +
                (1.0 - average_entropy_impact) * 0.25
            )

            aggregate = {
                "concept":
                concept.get(
                    "concept"
                ),

                "source_viability":
                concept.get(
                    "viability",
                    0.0
                ),

                "task_count":
                len(
                    task_results
                ),

                "task_results":
                task_results,

                "average_entropy_impact":
                average_entropy_impact,

                "average_identity_continuity":
                average_identity_continuity,

                "average_execution_usefulness":
                average_execution_usefulness,

                "promotion_score":
                promotion_score,
            }

            aggregate[
                "decision"
            ] = self.decide(
                aggregate
            )

            evaluations.append(
                aggregate
            )

        report = {
            "system":
            "novelty_promotion_gate",

            "validation_tasks":
            self.validation_tasks,

            "minimum_task_count":
            3,

            "evaluations":
            evaluations,

            "decision_counts":
            {
                "reject":
                len([
                    item
                    for item in evaluations
                    if item.get(
                        "decision"
                    )
                    == "reject"
                ]),

                "latent":
                len([
                    item
                    for item in evaluations
                    if item.get(
                        "decision"
                    )
                    == "latent"
                ]),

                "promote":
                len([
                    item
                    for item in evaluations
                    if item.get(
                        "decision"
                    )
                    == "promote"
                ]),
            },

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.promotion_history.append(
            report
        )

        self.promotion_history = (
            self.promotion_history[-32:]
        )

        return report


class ControlledSafeNovelty:

    def __init__(self):

        self.semantic_immune_confidence_calibration = (
            SemanticImmuneConfidenceCalibration()
        )

        self.safe_exploratory_sandbox = (
            SafeExploratorySandbox()
        )

        self.conceptive_neurogenesis = (
            ConceptiveNeurogenesis()
        )

        self.recursive_simulation_worlds = (
            RecursiveSimulationWorlds()
        )

        self.identity_elasticity_layer = (
            IdentityElasticityLayer()
        )

        self.novelty_promotion_gate = (
            NoveltyPromotionGate()
        )

        self.novelty_history = []

    def run_cycle(self, runtime_context):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        immunity_report = (
            self.semantic_immune_confidence_calibration
            .calibrate(runtime_context)
        )

        sandbox_report = (
            self.safe_exploratory_sandbox
            .run(
                runtime_context,
                immunity_report
            )
        )

        neurogenesis_report = (
            self.conceptive_neurogenesis
            .generate(
                runtime_context,
                immunity_report,
                sandbox_report
            )
        )

        worlds_report = (
            self.recursive_simulation_worlds
            .simulate(
                runtime_context,
                sandbox_report
            )
        )

        elasticity_report = (
            self.identity_elasticity_layer
            .regulate(
                runtime_context,
                immunity_report,
                worlds_report
            )
        )

        promotion_report = (
            self.novelty_promotion_gate
            .evaluate(
                runtime_context,
                neurogenesis_report,
                worlds_report,
                elasticity_report
            )
        )

        report = {
            "phase":
            "Controlled Safe Novelty",

            "semantic_immune_confidence_calibration":
            immunity_report,

            "safe_exploratory_sandbox":
            sandbox_report,

            "conceptive_neurogenesis":
            neurogenesis_report,

            "recursive_simulation_worlds":
            worlds_report,

            "identity_elasticity_layer":
            elasticity_report,

            "novelty_promotion_gate":
            promotion_report,

            "novelty_state":
            (
                "reopened_under_sandbox"
                if immunity_report.get(
                    "immunity_state"
                )
                == "de_escalated"
                else "controlled"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        runtime_context[
            "semantic_immune_confidence_calibration_report"
        ] = immunity_report

        runtime_context[
            "safe_exploratory_sandbox_report"
        ] = sandbox_report

        runtime_context[
            "conceptive_neurogenesis_report"
        ] = neurogenesis_report

        runtime_context[
            "recursive_simulation_worlds_report"
        ] = worlds_report

        runtime_context[
            "identity_elasticity_layer_report"
        ] = elasticity_report

        runtime_context[
            "novelty_promotion_gate_report"
        ] = promotion_report

        runtime_context[
            "controlled_safe_novelty_report"
        ] = report

        self.novelty_history.append(
            report
        )

        self.novelty_history = (
            self.novelty_history[-32:]
        )

        return runtime_context


controlled_safe_novelty = (
    ControlledSafeNovelty()
)
