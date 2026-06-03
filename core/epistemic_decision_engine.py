import re

from core.belief_engine import EpistemicCognitionLayer
from core.epistemic_drift_regulator import EpistemicDriftRegulator
from core.epistemic_models import BeliefState, clamp
from runtime.epistemic_verdict_engine import EpistemicVerdictEngine
from runtime.epistemic_promotion_engine import EpistemicPromotionEngine
from runtime.ambiguity_resolution_engine import AmbiguityResolutionEngine


class EpistemicDecisionEngine:
    def __init__(self, cognition_layer=None):
        self.cognition_layer = cognition_layer or EpistemicCognitionLayer()
        self.drift_regulator = EpistemicDriftRegulator()
        self.verdict_engine = EpistemicVerdictEngine()
        self.promotion_engine = EpistemicPromotionEngine()
        self.ambiguity_resolution_engine = AmbiguityResolutionEngine()

    def _concept(self, simulation):
        source = simulation.get("source", {})
        for key in [
            "concept",
            "concept_id",
            "candidate_id",
            "trait_id",
            "id",
            "name",
        ]:
            if source.get(key):
                return str(source[key])

        candidate_type = simulation.get("candidate_type", "hypothesis")
        semantic_keys = sorted(
            key
            for key, value in source.items()
            if isinstance(value, str)
        )
        semantic_values = [
            str(source[key])
            for key in semantic_keys[:3]
        ]
        raw = "_".join([str(candidate_type)] + semantic_values)
        return (
            re.sub(r"[^a-zA-Z0-9_:-]+", "_", raw).strip("_")
            or "unclassified_hypothesis"
        )

    def _simulation_evidence(self, simulation):
        concept = self._concept(simulation)
        identity_preservation = clamp(
            1.0 - simulation.get("predicted_identity_delta", 1.0)
        )
        entropy_bound = clamp(
            1.0 - simulation.get("predicted_entropy_delta", 1.0)
        )
        causal_alignment = clamp(simulation.get("causal_alignment", 0.0))
        predicted_utility = clamp(simulation.get("predicted_utility", 0.0))
        support = clamp(
            predicted_utility * 0.38
            + causal_alignment * 0.34
            + identity_preservation * 0.16
            + entropy_bound * 0.12
        )
        contradiction = clamp(
            simulation.get("predicted_identity_delta", 0.0) * 0.48
            + simulation.get("predicted_entropy_delta", 0.0) * 0.32
            + (1.0 - causal_alignment) * 0.20
        )
        simulation_id = simulation.get("simulation_id", concept)
        return concept, {
            "concept": concept,
            "source": "mutation_rehearsal",
            "support_score": support,
            "contradiction_score": contradiction,
            "reliability": 0.62,
            "causal_alignment": causal_alignment,
            "semantic_consistency": clamp(
                identity_preservation * 0.62
                + entropy_bound * 0.38
            ),
            "metadata": {
                "evidence_id": f"mutation_rehearsal:{simulation_id}",
                "simulation_state": simulation.get("simulation_state"),
            },
        }

    def _constructive_evidence(self, assessment):
        simulation = assessment.get("simulation", {})
        concept = self._concept(simulation)
        signal = assessment.get("constructive_signal", {})
        reasoning = signal.get("reasoning", {})
        causal_gain = assessment.get("causal_gain_estimate", {})
        support = clamp(
            assessment.get("constructive_score", 0.0) * 0.62
            + causal_gain.get("causal_gain", 0.0) * 0.38
        )
        contradiction = clamp(
            1.0 - reasoning.get("identity_preservation", 0.0)
        )
        simulation_id = simulation.get("simulation_id", concept)
        return {
            "concept": concept,
            "source": "constructive_reasoning",
            "support_score": support,
            "contradiction_score": contradiction,
            "reliability": 0.72,
            "causal_alignment": clamp(
                simulation.get("causal_alignment", 0.0)
            ),
            "semantic_consistency": clamp(
                reasoning.get("identity_preservation", 0.0) * 0.65
                + reasoning.get("entropy_bound", 0.0) * 0.35
            ),
            "metadata": {
                "evidence_id": f"constructive_reasoning:{simulation_id}",
            },
        }

    def _causal_attestation_evidence(self, concept, simulation, rehearsal):
        exports = rehearsal.get("evidence_exports", {})
        causal_attestation = clamp(
            exports.get(
                "causal_attestation_score",
                simulation.get("causal_alignment", 0.0),
            )
        )
        identity_attestation = clamp(
            exports.get(
                "identity_attestation_score",
                1.0 - simulation.get("predicted_identity_delta", 1.0),
            )
        )
        simulation_id = simulation.get("simulation_id", concept)
        return {
            "concept": concept,
            "source": "causal_attestation",
            "support_score": clamp(
                causal_attestation * 0.58
                + identity_attestation * 0.42
            ),
            "contradiction_score": clamp(
                (1.0 - causal_attestation) * 0.58
                + (1.0 - identity_attestation) * 0.42
            ),
            "reliability": 0.78,
            "causal_alignment": causal_attestation,
            "semantic_consistency": identity_attestation,
            "metadata": {
                "evidence_id": f"causal_attestation:{simulation_id}",
            },
        }

    def _as_list(self, value):
        if isinstance(value, dict):
            return [value]
        return list(value or [])

    def derive_inputs(self, context):
        explicit_hypotheses = self._as_list(
            context.get("epistemic_hypotheses", [])
        )
        explicit_evidence = self._as_list(
            context.get("epistemic_evidence", [])
        )
        rehearsal = context.get("causal_rehearsal_report", {})
        simulations = rehearsal.get("mutation_simulator", {}).get(
            "simulations", []
        )
        assessments = context.get("constructive_reasoning_report", {}).get(
            "all_assessments", []
        )
        promotion_report = self.promotion_engine.run_cycle(
            context,
        )
        ambiguity_report = self.ambiguity_resolution_engine.run_cycle(
            context,
        )

        hypotheses = {}
        evidence = list(explicit_evidence)
        for item in explicit_hypotheses:
            hypotheses[item["concept"]] = item

        for item in promotion_report.get(
            "epistemic_hypotheses",
            [],
        ):

            hypotheses.setdefault(
                item["concept"],
                item,
            )

        evidence.extend(
            promotion_report.get(
                "epistemic_evidence",
                [],
            )
        )

        for simulation in simulations:
            concept, item = self._simulation_evidence(simulation)
            source = simulation.get("source", {})
            hypotheses.setdefault(concept, {
                "concept": concept,
                "claim": source.get("claim", concept),
                "prior_confidence": clamp(
                    source.get(
                        "confidence",
                        simulation.get("predicted_utility", 0.5),
                    )
                ),
                "semantic_consistency": item["semantic_consistency"],
                "causal_alignment": item["causal_alignment"],
                "metadata": {
                    "origin": "causal_rehearsal",
                    "simulation_state": simulation.get("simulation_state"),
                },
            })
            evidence.append(item)
            evidence.append(
                self._causal_attestation_evidence(
                    concept,
                    simulation,
                    rehearsal,
                )
            )

        for assessment in assessments:
            evidence.append(self._constructive_evidence(assessment))

        return {
            "epistemic_hypotheses": list(hypotheses.values()),
            "epistemic_evidence": evidence,
            "epistemic_promotion_report": promotion_report,
            "ambiguity_resolution_report": ambiguity_report,
        }

    def run_cycle(self, context):
        context = context if isinstance(context, dict) else {}
        derived = self.derive_inputs(context)
        promotion_report = derived.pop(
            "epistemic_promotion_report",
        )
        ambiguity_report = derived.pop(
            "ambiguity_resolution_report",
        )
        context = dict(
            context,
            ambiguity_resolution_report=ambiguity_report,
        )
        drift_assessment = self.drift_regulator.assess(
            context,
        )
        verdict_report = self.verdict_engine.run_cycle(
            context,
            derived,
            drift_assessment,
        )
        derived = {
            "epistemic_hypotheses":
            verdict_report["epistemic_hypotheses"],

            "epistemic_evidence":
            verdict_report["epistemic_evidence"],
        }
        derived, regulation = self.drift_regulator.regulate(
            context,
            derived,
            self.cognition_layer.belief_engine.registry,
        )
        epistemic_context = dict(context)
        epistemic_context.update(derived)
        epistemic_context["epistemic_drift_regulation"] = regulation
        report = self.cognition_layer.run_cycle(epistemic_context)
        regulation["archived_weak_beliefs"] = (
            self.drift_regulator.archive_weak_beliefs(
                self.cognition_layer.belief_engine.registry,
                regulation,
            )
        )
        report["beliefs"] = [
            belief.as_dict()
            for belief in self.cognition_layer.belief_engine.registry.beliefs()
        ]
        for evaluation in report["evaluations"]:
            if evaluation["concept"] in regulation["archived_weak_beliefs"]:
                evaluation["runtime_state"] = "ARCHIVED"
                evaluation["belief"]["state"] = "ARCHIVED"
        report["runtime_state"] = (
            report["beliefs"][-1]["state"]
            if report["beliefs"]
            else "CANDIDATE"
        )
        quarantined = regulation.get(
            "quarantined_probation_beliefs",
            [],
        )
        active_quarantined = [
            concept
            for concept in quarantined
            if self.cognition_layer.belief_engine.registry.registry[
                concept
            ].state
            in [
                BeliefState.CANDIDATE,
                BeliefState.PROBATION,
            ]
        ]
        report["epistemic_drift_regulation"] = regulation
        report["epistemic_quarantine"] = {
            "active":
            regulation["regulation_mode"]
            == "semantic_containment",

            "active_quarantined_beliefs":
            active_quarantined,

            "archived_during_containment":
            [
                concept
                for concept in quarantined
                if concept
                in regulation[
                    "archived_weak_beliefs"
                ]
            ],

            "truth_commit_blocked":
            regulation.get(
                "truth_commit_blocked",
                False,
            ),
        }
        report["epistemic_verdict_engine"] = verdict_report
        report["epistemic_promotion_engine"] = promotion_report
        report["ambiguity_resolution_engine"] = ambiguity_report
        report["epistemic_transition_summary"] = {
            "simulation_candidate_count":
            verdict_report["verdict_count"],

            "verdict_registered_count":
            verdict_report["registered_candidate_count"],

            "verdict_suppressed_count":
            verdict_report["suppressed_count"],

            "drift_gate_suppressed_count":
            regulation["suppressed_hypothesis_count"],

            "total_suppressed_count":
            (
                verdict_report["suppressed_count"]
                +
                regulation["suppressed_hypothesis_count"]
            ),

            "registered_belief_count":
            len(
                self.cognition_layer.belief_engine.registry.beliefs()
            ),

            "trait_candidate_count":
            promotion_report["candidate_count"],

            "trait_promotion_count":
            promotion_report["promotion_count"],

            "quarantined_probation_count":
            len(
                active_quarantined,
            ),
        }
        report["epistemic_decision_engine"] = {
            "system": "epistemic_decision_engine",
            "derived_hypothesis_count": len(derived["epistemic_hypotheses"]),
            "derived_evidence_count": len(derived["epistemic_evidence"]),
            "decision_state": (
                "truth_commitment_available"
                if report["truth_commitments"]
                else "beliefs_formed"
                if report["beliefs"]
                else "awaiting_observations"
            ),
        }
        report["belief_registry"] = (
            self.cognition_layer.belief_engine.registry.report()
        )
        report["belief_promotion_engine"] = report.get(
            "belief_promotion_engine",
            {},
        )
        return report


epistemic_decision_engine = EpistemicDecisionEngine(
    cognition_layer=EpistemicCognitionLayer(
        truth_registry_path=(
            "runtime/memory/storage/truth_registry.json"
        ),
        provisional_truth_registry_path=(
            "runtime/memory/storage/provisional_truth_registry.json"
        ),
        knowledge_replication_ledger_path=(
            "runtime_data/knowledge_replication_ledger.json"
        ),
        semantic_spine_recovery_path=(
            "runtime_data/semantic_spine_recovery.json"
        ),
        reversible_rehearsal_state_path=(
            "runtime_data/reversible_rehearsal_state.json"
        ),
        causal_evidence_ledger_path=(
            "runtime_data/causal_evidence_ledger.json"
        ),
    )
)
