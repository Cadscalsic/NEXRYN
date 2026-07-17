"""Governed counterfactual reasoning orchestration."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.arena.candidate_simulator import CandidateSimulator
from runtime.counterfactual.alternative_world_builder import AlternativeWorldBuilder
from runtime.counterfactual.assumption_extractor import AssumptionExtractor
from runtime.counterfactual.counterfactual_budget_manager import CounterfactualBudgetManager
from runtime.counterfactual.counterfactual_eligibility_gate import CounterfactualEligibilityGate
from runtime.counterfactual.counterfactual_evidence_comparator import CounterfactualEvidenceComparator
from runtime.counterfactual.counterfactual_generator import CounterfactualGenerator
from runtime.counterfactual.counterfactual_memory import CounterfactualMemory
from runtime.counterfactual.counterfactual_prioritizer import CounterfactualPrioritizer
from runtime.counterfactual.counterfactual_simulator import CounterfactualSimulator
from runtime.counterfactual.falsification_engine import FalsificationEngine
from runtime.counterfactual.minimal_revision_engine import MinimalRevisionEngine
from runtime.counterfactual.winner_stability_assessor import WinnerStabilityAssessor


class CounterfactualReasoningEngine:
    system_name = "counterfactual_reasoning_engine"

    def __init__(
        self,
        eligibility_gate=None,
        assumption_extractor=None,
        generator=None,
        prioritizer=None,
        world_builder=None,
        simulator=None,
        comparator=None,
        falsifier=None,
        stability_assessor=None,
        revision_engine=None,
        memory=None,
        budget_manager=None,
    ):
        self.eligibility_gate = eligibility_gate or CounterfactualEligibilityGate()
        self.assumption_extractor = assumption_extractor or AssumptionExtractor()
        self.generator = generator or CounterfactualGenerator()
        self.prioritizer = prioritizer or CounterfactualPrioritizer()
        self.world_builder = world_builder or AlternativeWorldBuilder()
        self.simulator = simulator or CounterfactualSimulator()
        self.comparator = comparator or CounterfactualEvidenceComparator()
        self.falsifier = falsifier or FalsificationEngine()
        self.stability_assessor = stability_assessor or WinnerStabilityAssessor()
        self.revision_engine = revision_engine or MinimalRevisionEngine()
        self.memory = memory or CounterfactualMemory()
        self.budget_manager = budget_manager or CounterfactualBudgetManager()
        self.original_simulator = CandidateSimulator()

    def reason(
        self,
        arena_report: Mapping[str, Any],
        input_grid: Any,
        target_grid: Any,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        candidate = self._winner_candidate(arena_report)
        eligibility = self.eligibility_gate.evaluate(arena_report, runtime_context)
        assumptions = self.assumption_extractor.extract(candidate, runtime_context)
        original_sim = self.original_simulator.simulate(candidate, input_grid=input_grid, target_grid=target_grid)
        if not eligibility.get("counterfactual_required"):
            report = self._report(
                eligibility,
                assumptions,
                [],
                [],
                [],
                {"original_candidate_id": candidate.get("candidate_id"), "counterfactual_comparisons": [], "best_counterfactual_id": None, "original_candidate_still_best": True},
                self.falsifier.review({"counterfactual_comparisons": []}),
                self.stability_assessor.assess(candidate.get("candidate_id"), {"counterfactual_comparisons": []}, {"falsification_strength": 0.0}),
                self.revision_engine.revise(candidate, [], {"counterfactual_comparisons": []}),
                "WINNER_STABLE" if eligibility.get("eligibility_state") == "SKIPPED" else "NO_VALID_ALTERNATIVES",
                candidate,
                runtime_context,
            )
            self.memory.record_counterfactual_episode(report["COUNTERFACTUAL_REASONING_REPORT"])
            return report

        generated = self.generator.generate(
            candidate,
            assumptions.get("assumptions", []),
            arena_alternatives=arena_report.get("normalized_candidates", []),
            residual_cells=runtime_context.get("residual_cells"),
            budget=eligibility.get("counterfactual_budget", {}),
        )
        prioritized = self.prioritizer.prioritize(
            generated.get("generated_counterfactuals", []),
            eligibility.get("counterfactual_budget", {}),
        )
        worlds = []
        simulations = []
        rejected = []
        for cf in prioritized.get("selected_for_simulation", []):
            gate = self._govern_counterfactual(cf, runtime_context)
            cf["governance_state"] = gate["decision"]
            if gate["decision"] == "BLOCK_COUNTERFACTUAL":
                rejected.append(cf)
                continue
            budget_gate = self.budget_manager.allow(
                cf.get("counterfactual_id"),
                len(simulations),
                eligibility.get("counterfactual_budget", {}),
            )
            if not budget_gate["allowed"]:
                rejected.append({**cf, "rejection_reason": budget_gate["stop_reason"]})
                continue
            world = self.world_builder.build(cf, runtime_context.get("current_world", {}))
            worlds.append(world)
            if not world["world_valid"]:
                rejected.append({**cf, "rejection_reason": "invalid_alternative_world"})
                continue
            simulations.append(self.simulator.simulate(
                cf,
                input_grid=input_grid,
                target_grid=target_grid,
                original_simulation=original_sim,
                budget=eligibility.get("counterfactual_budget", {}),
            ))

        comparison = self.comparator.compare(candidate.get("candidate_id"), original_sim, simulations)
        falsification = self.falsifier.review(comparison, committed_truth=bool(runtime_context.get("committed_truth")))
        stability = self.stability_assessor.assess(candidate.get("candidate_id"), comparison, falsification)
        revision = self.revision_engine.revise(candidate, simulations, comparison)
        stop_reason = "REVISION_GENERATED" if revision.get("revision_required") else self.budget_manager.stop_reason(stability, falsification, len(simulations))
        report = self._report(
            eligibility,
            assumptions,
            generated.get("generated_counterfactuals", []),
            simulations,
            rejected,
            comparison,
            falsification,
            stability,
            revision,
            stop_reason,
            candidate,
            runtime_context,
            worlds=worlds,
            prioritized=prioritized,
            original_simulation=original_sim,
        )
        self.memory.record_counterfactual_episode(report["COUNTERFACTUAL_REASONING_REPORT"])
        return report

    def _winner_candidate(self, arena_report):
        recommendation = arena_report.get("execution_recommendation", {}) if isinstance(arena_report.get("execution_recommendation"), Mapping) else {}
        selected = recommendation.get("selected_candidate")
        if isinstance(selected, Mapping):
            return dict(selected)
        rows = arena_report.get("normalized_candidates") or []
        winner_id = arena_report.get("winner_candidate_id")
        for row in rows:
            if isinstance(row, Mapping) and row.get("candidate_id") == winner_id:
                return dict(row)
        return {
            "candidate_id": winner_id or "preliminary_winner",
            "operation": arena_report.get("winner_operation"),
            "program": arena_report.get("winner_program", {"step_count": 0, "steps": []}),
            "source_confidence": arena_report.get("winner_score", 0.0),
        }

    def _govern_counterfactual(self, cf, runtime_context):
        reasons = []
        if len(cf.get("changed_assumption_ids", [])) > 1:
            reasons.append("multiple_assumption_changes_blocked")
        if cf.get("protected_invariant"):
            reasons.append("protected_invariant")
        for key in ("truth_governance_report", "identity_governance_report", "topology_safety_report", "dependency_governance_report", "context_governance_report", "execution_integrity_report", "constitutional_review_report"):
            value = runtime_context.get(key)
            if isinstance(value, Mapping) and any(item is False for item in value.values()):
                reasons.append(f"{key}_failed")
        decision = "BLOCK_COUNTERFACTUAL" if reasons else "ALLOW_COUNTERFACTUAL"
        return {"decision": decision, "reasons": reasons}

    def _report(self, eligibility, assumptions, generated, simulations, rejected, comparison, falsification, stability, revision, stop_reason, candidate, runtime_context, **extra):
        compact = {
            "counterfactual_required": eligibility.get("counterfactual_required"),
            "eligibility_state": eligibility.get("eligibility_state"),
            "trigger_reasons": eligibility.get("trigger_reasons", []),
            "assumption_count": assumptions.get("assumption_count", 0),
            "challengeable_assumption_count": assumptions.get("challengeable_assumption_count", 0),
            "generated_counterfactual_count": len(generated),
            "simulated_counterfactual_count": len(simulations),
            "rejected_counterfactual_count": len(rejected),
            "best_counterfactual_id": comparison.get("best_counterfactual_id"),
            "original_candidate_still_best": comparison.get("original_candidate_still_best"),
            "falsification_state": falsification.get("falsification_state"),
            "winner_stability_state": stability.get("stability_state"),
            "winner_stability_score": stability.get("stability_score"),
            "minimal_revision_generated": revision.get("revision_required"),
            "execution_recommendation": stability.get("execution_recommendation"),
            "budget_used": len(simulations),
            "stop_reason": stop_reason,
            "counterfactual_search_operational": True,
            "alternative_world_simulation_available": bool(simulations),
            "residual_guided_revision_operational": True,
            "counterfactual_memory_operational": True,
            "budget_enforcement_operational": True,
            "direct_counterfactual_to_executor_access": False,
            "supporting_evidence": falsification.get("supporting_counterfactuals", []),
            "falsifying_evidence": falsification.get("falsifying_counterfactuals", []),
            "counterfactual_summary": [
                {
                    "counterfactual_id": sim.get("counterfactual_id"),
                    "accuracy": sim.get("prediction_accuracy"),
                    "residual": sim.get("difference_count"),
                    "evidence": next((row.get("evidence_class") for row in comparison.get("counterfactual_comparisons", []) if row.get("counterfactual_id") == sim.get("counterfactual_id")), "INCONCLUSIVE"),
                }
                for sim in simulations[:6]
            ],
        }
        return {
            "system": self.system_name,
            "COUNTERFACTUAL_REASONING_REPORT": compact,
            "counterfactual_reasoning_report": compact,
            "eligibility_report": eligibility,
            "assumption_report": assumptions,
            "generated_counterfactuals": generated,
            "simulated_counterfactuals": simulations,
            "rejected_counterfactuals": rejected,
            "comparison_report": comparison,
            "falsification_report": falsification,
            "winner_stability_report": stability,
            "minimal_revision_report": revision,
            "final_execution_governance_payload": {
                "selected_candidate": candidate,
                "counterfactual_state": compact["eligibility_state"],
                "winner_stability": compact["winner_stability_score"],
                "falsification_state": compact["falsification_state"],
                "execution_recommendation": compact["execution_recommendation"],
                "supporting_evidence": compact["supporting_evidence"],
                "falsifying_evidence": compact["falsifying_evidence"],
                "revision_candidate": revision.get("revised_candidate"),
            },
            **extra,
        }


counterfactual_reasoning_engine = CounterfactualReasoningEngine()

__all__ = ["CounterfactualReasoningEngine", "counterfactual_reasoning_engine"]
