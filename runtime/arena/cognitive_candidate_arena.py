"""Governed cognitive candidate arena and evidence-based selection."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import numpy as np

from runtime.arena.arena_memory import ArenaMemory
from runtime.arena.candidate_diversity_analyzer import CandidateDiversityAnalyzer
from runtime.arena.candidate_normalizer import CandidateNormalizer
from runtime.arena.candidate_proposal_gateway import CandidateProposalGateway
from runtime.arena.candidate_scorer import CandidateScorer
from runtime.arena.candidate_simulator import CandidateSimulator
from runtime.arena.source_dominance_guard import SourceDominanceGuard
from runtime.arena.winner_selection_policy import WinnerSelectionPolicy


class CognitiveCandidateArena:
    """Compare validated executable candidates and recommend execution mode."""

    system_name = "cognitive_candidate_arena"

    def __init__(
        self,
        gateway: CandidateProposalGateway | None = None,
        normalizer: CandidateNormalizer | None = None,
        simulator: CandidateSimulator | None = None,
        scorer: CandidateScorer | None = None,
        diversity_analyzer: CandidateDiversityAnalyzer | None = None,
        dominance_guard: SourceDominanceGuard | None = None,
        winner_policy: WinnerSelectionPolicy | None = None,
        memory: ArenaMemory | None = None,
    ):
        self.gateway = gateway or CandidateProposalGateway()
        self.normalizer = normalizer or CandidateNormalizer()
        self.simulator = simulator or CandidateSimulator()
        self.scorer = scorer or CandidateScorer()
        self.diversity_analyzer = diversity_analyzer or CandidateDiversityAnalyzer()
        self.dominance_guard = dominance_guard or SourceDominanceGuard()
        self.winner_policy = winner_policy or WinnerSelectionPolicy()
        self.memory = memory or ArenaMemory()

    def run(
        self,
        proposals: list[Mapping[str, Any]] | None,
        input_grid: Any = None,
        target_grid: Any = None,
        runtime_context: Mapping[str, Any] | None = None,
        analysis_only: bool = False,
        task_signature: str | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        gateway_report = self.gateway.submit(proposals)
        normalization = self.normalizer.normalize(gateway_report["proposals"])
        candidates = normalization["normalized_candidates"]
        target_size = int(np.array(target_grid).size) if target_grid is not None else 1
        for candidate in candidates:
            candidate["target_size"] = max(target_size, 1)

        governance = {candidate["candidate_id"]: self._governance(candidate, runtime_context) for candidate in candidates}
        blocked = [
            candidate for candidate in candidates
            if governance[candidate["candidate_id"]]["decision"] == "BLOCK_CANDIDATE"
        ]
        eligible = [
            candidate for candidate in candidates
            if governance[candidate["candidate_id"]]["decision"] in {"ALLOW_COMPETITION", "ALLOW_SANDBOX_ONLY"}
        ]
        diversity = self.diversity_analyzer.analyze(eligible)
        simulations = {}
        scores = []
        for candidate in eligible:
            simulation = self.simulator.simulate(candidate, input_grid=input_grid, target_grid=target_grid)
            simulations[candidate["candidate_id"]] = simulation
            score = self.scorer.score(candidate, simulation, governance[candidate["candidate_id"]])
            score["source"] = candidate.get("source")
            scores.append(score)

        selection = self.winner_policy.select(scores, simulations, analysis_only=analysis_only)
        winner_score = selection.get("winner_candidate") or {}
        selected_states = {"WINNER_SELECTED", "CONDITIONAL_WINNER", "SANDBOX_ONLY_WINNER"}
        winner = (
            self._candidate_by_id(eligible, winner_score.get("candidate_id"))
            if selection.get("selection_state") in selected_states
            else {}
        )
        second_score = selection.get("second_best_candidate") or {}
        validation_probe = self._validation_probe_candidate(
            eligible,
            scores,
            simulations,
            selection,
        )
        dominance = self.dominance_guard.review(
            eligible,
            scores=scores,
            winner=winner,
            expected_sources=runtime_context.get("expected_candidate_sources", []),
        )
        source_policy = self._source_diversity_policy(
            diversity,
            dominance,
            eligible,
            runtime_context,
        )
        arena_state = self._arena_state(
            candidates,
            eligible,
            blocked,
            diversity,
            selection,
            dominance,
        )
        rows = self._candidate_rows(
            candidates,
            blocked,
            simulations,
            scores,
            selection,
            governance,
            validation_probe.get("candidate_id") if validation_probe else None,
        )
        sources_entered = sorted({
            source
            for candidate in eligible
            for source in candidate.get("sources", [candidate.get("source")])
            if source
        })
        sources_rejected = sorted({
            candidate.get("source")
            for candidate in blocked + gateway_report["rejected_proposals"]
            if candidate.get("source")
        })
        proposal_report = (
            runtime_context.get("candidate_proposal_report")
            if isinstance(runtime_context.get("candidate_proposal_report"), Mapping)
            else {}
        )
        source_flow_trace = self._source_flow_trace(
            proposal_report=proposal_report,
            arena_proposals=proposals,
            sources_entered=sources_entered,
            gateway_report=gateway_report,
            expected_sources=runtime_context.get("expected_candidate_sources", []),
        )
        compact = {
            "arena_state": arena_state,
            "candidate_count": len(eligible),
            "unique_candidate_count": len(candidates),
            "cross_source_consensus_count": normalization.get(
                "cross_source_consensus_count",
                0,
            ),
            "cross_source_consensus_groups": normalization.get(
                "cross_source_consensus_groups",
                [],
            ),
            "cross_source_consensus_state": (
                "CROSS_SOURCE_CONSENSUS"
                if normalization.get("cross_source_consensus_count")
                else "NO_CROSS_SOURCE_CONSENSUS"
            ),
            "source_count": len(sources_entered),
            "sources_entered": sources_entered,
            "sources_rejected": sources_rejected,
            "proposal_sources_with_proposals": (
                proposal_report.get("sources_with_proposals") or []
            ),
            "candidate_source_flow_trace": source_flow_trace,
            "competition_diversity": diversity.get("competition_diversity", 0.0),
            "operational_diversity": diversity.get("operational_diversity", 0.0),
            "source_diversity": diversity.get("source_diversity", 0.0),
            "simulation_count": len(simulations),
            "simulation_success_count": sum(1 for item in simulations.values() if item.get("simulation_success")),
            "governance_blocked_count": len(blocked),
            "winner_candidate_id": winner.get("candidate_id") if winner else None,
            "winner_source": winner.get("source") if winner else None,
            "winner_operation": winner.get("operation") if winner else None,
            "winner_score": winner_score.get("final_score"),
            "second_best_score": second_score.get("final_score"),
            "selection_margin": selection.get("selection_margin"),
            "selection_state": selection.get("selection_state"),
            "source_dominance_detected": dominance.get("dominance_detected"),
            "arena_source_diversity_state": source_policy["state"],
            "arena_source_diversity_action": source_policy["action"],
            "target_candidate_sources": source_policy["target_sources"],
            "missing_candidate_sources": source_policy["missing_sources"],
            "no_competition_reason": self._no_competition_reason(eligible, diversity, gateway_report, blocked),
            "selection_explanation": selection.get("selection_explanation"),
            "validation_probe_candidate_id": validation_probe.get("candidate_id") if validation_probe else None,
            "validation_probe_operation": validation_probe.get("operation") if validation_probe else None,
            "validation_probe_source": validation_probe.get("source") if validation_probe else None,
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY" if validation_probe else "NONE",
            "validation_probe_shared_input_trace": self._shared_input_trace(
                runtime_context
            ),
            "arena_to_compiled_bridge_state": (
                "VALIDATION_PROBE_AVAILABLE"
                if validation_probe
                else "NO_VALIDATION_PROBE"
            ),
            "arena_to_compiled_bridge_action": (
                "route_validation_probe_to_compiler_without_prediction_authority"
                if validation_probe
                else "wait_for_safe_winner_or_better_grounding"
            ),
            "candidate_scores_fully_explained": True,
            "source_dominance_guard_active": True,
            "winner_selected_from_evidence": bool(winner),
            "direct_source_to_executor_access": False,
            "arena_memory_operational": True,
            "candidate_summary": rows,
            "winner_takes_all_detected": bool(
                dominance.get("dominance_detected")
                and selection.get("selection_state") in {
                    "WINNER_SELECTED",
                    "CONDITIONAL_WINNER",
                    "SANDBOX_ONLY_WINNER",
                }
                and float(selection.get("selection_margin") or 0.0) > 0.0
            ),
            "dominance_source": dominance.get("dominant_source"),
            "selection_mode": "EVIDENCE_BASED_ARENA",
            "validation_coverage": round(len(scores) / max(len(eligible), 1), 4) if eligible else 0.0,
        }
        recommendation = {
            "selected_candidate": deepcopy(winner) if winner else None,
            "validation_probe_candidate": deepcopy(validation_probe) if validation_probe else None,
            "validation_probe_mode": "sandbox_validation_only" if validation_probe else "none",
            "validation_probe_grounding_context": (
                {
                    "input_grid": self._context_grid_payload(
                        input_grid,
                        runtime_context,
                        ("input_grid", "input", "source_grid", "source"),
                    ),
                    "target_grid": self._context_grid_payload(
                        target_grid,
                        runtime_context,
                        ("target_grid", "output_grid", "target", "output"),
                    ),
                    "predicted_output": self._context_grid_payload(
                        simulations.get(validation_probe.get("candidate_id"), {}).get(
                            "predicted_output"
                        ),
                        runtime_context,
                        ("predicted_output", "predicted_grid", "prediction"),
                    ),
                }
                if validation_probe
                else {}
            ),
            "selection_state": selection.get("selection_state"),
            "execution_mode": self._execution_mode(selection, winner),
            "selection_evidence": {
                "winner_score": compact["winner_score"],
                "second_best_score": compact["second_best_score"],
                "selection_margin": compact["selection_margin"],
                "simulation": simulations.get(winner.get("candidate_id")) if winner else None,
                "score": winner_score,
            },
        }
        report = {
            "system": self.system_name,
            "COGNITIVE_CANDIDATE_ARENA_REPORT": compact,
            "candidate_arena_summary": compact,
            "candidate_arena_diagnostics": {
                "gateway_report": gateway_report,
                "normalization_report": normalization,
                "diversity_report": diversity,
                "dominance_report": dominance,
                "selection_report": selection,
                "simulations": simulations,
                "scores": scores,
                "governance_decisions": governance,
            },
            "normalized_candidates": candidates,
            "rejected_candidates": blocked + gateway_report["rejected_proposals"],
            "execution_recommendation": recommendation,
            **compact,
        }
        report["task_signature"] = task_signature
        report["winner_program_signature"] = winner.get("program_signature") if winner else None
        self.memory.record_competition(report)
        return report

    def _source_flow_trace(
        self,
        *,
        proposal_report: Mapping[str, Any],
        arena_proposals: list[Mapping[str, Any]] | Mapping[str, Any] | None,
        sources_entered: list[str],
        gateway_report: Mapping[str, Any],
        expected_sources: list[str] | tuple[str, ...],
    ) -> list[dict[str, Any]]:
        proposal_sources = [
            str(source)
            for source in proposal_report.get("sources_with_proposals", []) or []
            if source
        ]
        rejected_sources = [
            str(source)
            for source in proposal_report.get("sources_rejected", []) or []
            if source
        ]
        proposal_rows = [
            item
            for item in proposal_report.get("candidate_proposals", []) or []
            if isinstance(item, Mapping)
        ]
        source_diagnostics = (
            proposal_report.get("source_diagnostics")
            if isinstance(proposal_report.get("source_diagnostics"), Mapping)
            else {}
        )
        raw_arena = (
            list(arena_proposals)
            if isinstance(arena_proposals, (list, tuple))
            else [arena_proposals]
            if isinstance(arena_proposals, Mapping)
            else []
        )
        arena_builder_sources = {
            self._source_alias(item.get("source"))
            for item in raw_arena
            if isinstance(item, Mapping) and item.get("source")
        }
        gateway_sources = {
            self._source_alias(item.get("source"))
            for item in gateway_report.get("proposals", []) or []
            if isinstance(item, Mapping) and item.get("source")
        }
        gateway_rejections = {
            self._source_alias(item.get("source")): item
            for item in gateway_report.get("rejected_proposals", []) or []
            if isinstance(item, Mapping) and item.get("source")
        }
        entered = {self._source_alias(source) for source in sources_entered}
        target_sources_by_alias = {}
        for source in (
            list(proposal_sources)
            + list(rejected_sources)
            + [str(source) for source in expected_sources if source]
            + list(arena_builder_sources)
            + list(gateway_sources)
            + list(entered)
        ):
            alias = self._source_alias(source)
            if alias and alias not in target_sources_by_alias:
                target_sources_by_alias[alias] = source
        rows = []
        for alias in sorted(target_sources_by_alias):
            source = target_sources_by_alias[alias]
            proposed = source in proposal_sources or alias in {
                self._source_alias(item) for item in proposal_sources
            }
            rejected = source in rejected_sources or alias in {
                self._source_alias(item) for item in rejected_sources
            }
            built = alias in arena_builder_sources
            gateway_accepted = alias in gateway_sources
            arena_entered = alias in entered
            source_proposal_rows = [
                row for row in proposal_rows
                if self._source_alias(row.get("source")) == alias
            ]
            rejected_rows = [
                row for row in source_proposal_rows
                if row.get("proposal_status") == "REJECTED"
            ]
            diagnostic = self._source_diagnostic_for_alias(source_diagnostics, alias)
            build_failure = self._arena_build_failure_reason(
                proposed=proposed,
                rejected=rejected,
                built=built,
                proposal_rows=source_proposal_rows,
                rejected_rows=rejected_rows,
                gateway_rejection=gateway_rejections.get(alias, {}),
            )
            if arena_entered:
                state = "ENTERED_ARENA"
                blocked_stage = "none"
                action = "monitor_source_competitiveness"
            elif gateway_accepted:
                state = "GATEWAY_ACCEPTED_NOT_ELIGIBLE"
                blocked_stage = "arena_governance_or_normalization"
                action = "inspect_gateway_to_arena_eligibility"
            elif built:
                state = "BUILT_NOT_ACCEPTED_BY_GATEWAY"
                blocked_stage = "candidate_proposal_gateway"
                action = "inspect_source_alias_and_program_shape"
            elif proposed:
                state = "PROPOSAL_NOT_BUILT_FOR_ARENA"
                blocked_stage = "arena_proposal_builder"
                action = "preserve_proposal_runtime_source_in_arena_builder"
            elif rejected:
                state = "REJECTED_BY_PROPOSAL_RUNTIME"
                blocked_stage = "candidate_proposal_runtime"
                action = "inspect_source_materialization_payload"
            else:
                state = "NO_PROPOSAL_SIGNAL"
                blocked_stage = "source_materialization"
                action = "activate_candidate_source_materialization"
            rows.append({
                "source": source,
                "normalized_source": alias,
                "proposal_runtime_proposed": proposed,
                "proposal_runtime_rejected": rejected,
                "proposal_runtime_rejection_reason": build_failure[
                    "proposal_rejection_reason"
                ],
                "arena_proposal_built": built,
                "gateway_accepted": gateway_accepted,
                "entered_arena": arena_entered,
                "flow_state": state,
                "blocked_stage": blocked_stage,
                "build_failure_reason": build_failure["reason"],
                "build_failure_detail": build_failure["detail"],
                "expected_candidate_fields": build_failure["expected_fields"],
                "received_candidate_fields": build_failure["received_fields"],
                "source_diagnostic": diagnostic,
                "action": action,
            })
        return rows

    def _arena_build_failure_reason(
        self,
        *,
        proposed: bool,
        rejected: bool,
        built: bool,
        proposal_rows: list[Mapping[str, Any]],
        rejected_rows: list[Mapping[str, Any]],
        gateway_rejection: Mapping[str, Any],
    ) -> dict[str, Any]:
        expected_fields = ["source", "operation", "program.steps"]
        rejection_reason = (
            str(rejected_rows[0].get("rejection_reason"))
            if rejected_rows and rejected_rows[0].get("rejection_reason")
            else None
        )
        if built:
            return {
                "reason": "none",
                "detail": "arena_proposal_built",
                "expected_fields": expected_fields,
                "received_fields": [],
                "proposal_rejection_reason": rejection_reason,
            }
        if rejected:
            row = dict(rejected_rows[0]) if rejected_rows else {}
            return {
                "reason": "proposal_runtime_rejected",
                "detail": rejection_reason or "source_rejected_before_arena_builder",
                "expected_fields": expected_fields,
                "received_fields": sorted(str(key) for key in row),
                "proposal_rejection_reason": rejection_reason,
            }
        if not proposed:
            return {
                "reason": "source_not_proposed",
                "detail": "candidate_source_did_not_emit_proposal",
                "expected_fields": expected_fields,
                "received_fields": [],
                "proposal_rejection_reason": rejection_reason,
            }
        if not proposal_rows:
            return {
                "reason": "proposal_row_missing",
                "detail": "source_listed_in_sources_with_proposals_but_no_row_found",
                "expected_fields": expected_fields,
                "received_fields": [],
                "proposal_rejection_reason": rejection_reason,
            }
        row = dict(proposal_rows[0])
        program = row.get("program") if isinstance(row.get("program"), Mapping) else {}
        steps = program.get("steps") if isinstance(program.get("steps"), list) else []
        received_fields = sorted(str(key) for key in row)
        if gateway_rejection:
            reasons = gateway_rejection.get("rejection_reasons") or []
            return {
                "reason": "candidate_schema_validation_failed",
                "detail": ",".join(str(item) for item in reasons) or "gateway_rejected",
                "expected_fields": expected_fields,
                "received_fields": received_fields,
                "proposal_rejection_reason": rejection_reason,
            }
        if not isinstance(program, Mapping) or not program:
            reason = "missing_program_representation"
            detail = "program_field_missing_or_not_mapping"
        elif not steps:
            reason = "missing_program_steps"
            detail = "program.steps_empty_or_not_list"
        elif not row.get("operation"):
            reason = "missing_operation"
            detail = "operation_missing_after_proposal_runtime"
        else:
            reason = "arena_builder_dropped_valid_proposal"
            detail = "proposal_has_required_candidate_shape_but_was_not_built"
        return {
            "reason": reason,
            "detail": detail,
            "expected_fields": expected_fields,
            "received_fields": received_fields,
            "proposal_rejection_reason": rejection_reason,
        }

    def _source_diagnostic_for_alias(
        self,
        source_diagnostics: Mapping[str, Any],
        alias: str,
    ) -> dict[str, Any]:
        for source, diagnostic in source_diagnostics.items():
            if self._source_alias(source) == alias and isinstance(diagnostic, Mapping):
                return dict(diagnostic)
        return {}

    def _source_alias(self, source: Any) -> str:
        token = str(source or "").strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "program_generation": "normalized_program_candidates",
            "semantic_to_transformation_compiler": "semantic_compiler",
            "compiler": "semantic_compiler",
            "adaptive_reuse_layer": "adaptive_reuse",
            "repair": "repair_engine",
        }
        return aliases.get(token, token)

    def _grid_payload(self, grid: Any) -> Any:
        if grid is None:
            return None
        if isinstance(grid, list):
            return deepcopy(grid)
        if hasattr(grid, "grid"):
            return self._grid_payload(getattr(grid, "grid"))
        if hasattr(grid, "tolist"):
            try:
                return grid.tolist()
            except Exception:
                return deepcopy(grid)
        return deepcopy(grid)

    def _context_grid_payload(
        self,
        primary: Any,
        runtime_context: Mapping[str, Any],
        keys: tuple[str, ...],
    ) -> Any:
        payload = self._grid_payload(primary)
        if self._grid_payload_available(payload):
            return payload
        for container in (
            runtime_context.get("shared_state_inputs"),
            runtime_context,
        ):
            if not isinstance(container, Mapping):
                continue
            for key in keys:
                payload = self._grid_payload(container.get(key))
                if self._grid_payload_available(payload):
                    return payload
        return payload

    def _shared_input_trace(self, runtime_context: Mapping[str, Any]) -> dict[str, Any]:
        shared = runtime_context.get("shared_state_inputs")
        shared = shared if isinstance(shared, Mapping) else {}
        expected = ["input_grid", "target_grid", "predicted_output"]
        present = [key for key in expected if key in shared]
        non_empty = [
            key
            for key in expected
            if self._grid_payload_available(self._grid_payload(shared.get(key)))
        ]
        empty = [key for key in present if key not in non_empty]
        return {
            "expected_keys": expected,
            "present_keys": present,
            "empty_keys": empty,
            "non_empty_keys": non_empty,
            "task_io_source_status": shared.get("task_io_source_status"),
            "input_population_state": (
                "SHARED_TASK_IO_AVAILABLE"
                if {"input_grid", "target_grid"}.issubset(set(non_empty))
                else "SHARED_TASK_IO_EMPTY"
            ),
        }

    def _grid_payload_available(self, payload: Any) -> bool:
        if payload is None:
            return False
        if isinstance(payload, list):
            if not payload:
                return False
            if all(isinstance(row, list) for row in payload):
                return any(row for row in payload)
            return True
        if hasattr(payload, "size"):
            try:
                return int(payload.size) > 0
            except Exception:
                return True
        return True

    def _governance(self, candidate: Mapping[str, Any], runtime_context: Mapping[str, Any]) -> dict[str, Any]:
        reasons = []
        for key in (
            "truth_governance_report",
            "identity_governance_report",
            "dependency_governance_report",
            "context_governance_report",
            "execution_integrity_report",
            "safety_validation_report",
        ):
            value = runtime_context.get(key)
            if isinstance(value, Mapping) and self._explicit_failure(value):
                reasons.append(f"{key}_failed")
        metadata = candidate.get("metadata", {}) if isinstance(candidate.get("metadata"), Mapping) else {}
        if metadata.get("identity_violation"):
            reasons.append("identity_violation")
        if metadata.get("safety_violation"):
            reasons.append("safety_violation")
        if reasons:
            decision = "BLOCK_CANDIDATE"
        elif metadata.get("sandbox_only"):
            decision = "ALLOW_SANDBOX_ONLY"
        elif metadata.get("requires_review"):
            decision = "REQUIRE_REVIEW"
        else:
            decision = "ALLOW_COMPETITION"
        return {
            "candidate_id": candidate.get("candidate_id"),
            "decision": decision,
            "reasons": reasons,
        }

    def _explicit_failure(self, value: Mapping[str, Any]) -> bool:
        for key, item in value.items():
            normalized_key = _normalize(key)
            normalized_value = _normalize(item)
            if normalized_key.endswith(("passed", "success", "ready", "validated")) and item is False:
                return True
            if normalized_key in {"status", "state", "validation_state", "governance_state"}:
                if normalized_value in {"failed", "rejected", "blocked", "invalid", "unsafe"}:
                    return True
        return False

    def _source_diversity_policy(
        self,
        diversity: Mapping[str, Any],
        dominance: Mapping[str, Any],
        eligible: list[Mapping[str, Any]],
        runtime_context: Mapping[str, Any],
    ) -> dict[str, Any]:
        source_diversity = float(diversity.get("source_diversity") or 0.0)
        source_count = int(diversity.get("source_count") or 0)
        target_sources = [
            str(source)
            for source in runtime_context.get("expected_candidate_sources", []) or []
            if source
        ]
        missing_sources = dominance.get("missing_candidate_sources") or []
        missing_sources = [
            str(source) for source in missing_sources if source
        ]
        if not eligible:
            state = "NO_CANDIDATE_SOURCES"
            action = "REQUEST_CANDIDATE_SOURCE_ACTIVATION"
        elif source_count <= 1:
            state = "LOW_SOURCE_DIVERSITY"
            action = "SOURCE_DIVERSITY_SPRINT_REQUIRED"
        elif source_diversity < 0.25:
            state = "SOURCE_DIVERSITY_PRESSURE"
            action = "EXPAND_ARENA_SOURCE_MIX"
        else:
            state = "MULTI_SOURCE_ARENA"
            action = "MONITOR_SOURCE_DIVERSITY"
        return {
            "state": state,
            "action": action,
            "target_sources": target_sources,
            "missing_sources": missing_sources,
        }

    def _arena_state(self, candidates, eligible, blocked, diversity, selection, dominance):
        if blocked and not eligible:
            return "GOVERNANCE_BLOCKED"
        if not candidates:
            return "ARENA_EMPTY"
        if len(eligible) == 1:
            return "SINGLE_SOURCE_ONLY"
        if not diversity.get("diversity_sufficient"):
            return "SINGLE_SOURCE_ONLY"
        state = selection.get("selection_state")
        if state in {"WINNER_SELECTED", "CONDITIONAL_WINNER", "SANDBOX_ONLY_WINNER"}:
            return "WINNER_SELECTED"
        if state == "TIE_REQUIRES_REVIEW":
            return "TIE_REQUIRES_REVIEW"
        if state in {"NO_SAFE_WINNER", "ALL_CANDIDATES_REJECTED"}:
            return "NO_SAFE_WINNER"
        return "COMPETITION_ACTIVE"

    def _validation_probe_candidate(self, eligible, scores, simulations, selection):
        state = selection.get("selection_state")
        if state in {"WINNER_SELECTED", "CONDITIONAL_WINNER", "SANDBOX_ONLY_WINNER"}:
            return {}
        top = selection.get("winner_candidate") or {}
        top_id = top.get("candidate_id")
        if top_id and simulations.get(top_id, {}).get("simulation_success"):
            return self._candidate_by_id(eligible, top_id)
        ranked_scores = sorted(
            [
                item for item in scores
                if item.get("candidate_id")
                and item.get("eligible_for_selection")
                and simulations.get(item.get("candidate_id"), {}).get("simulation_success")
            ],
            key=lambda item: item.get("final_score", 0.0),
            reverse=True,
        )
        if not ranked_scores:
            return {}
        return self._candidate_by_id(eligible, ranked_scores[0].get("candidate_id"))

    def _candidate_rows(self, candidates, blocked, simulations, scores, selection, governance, validation_probe_id=None):
        score_by_id = {item.get("candidate_id"): item for item in scores}
        winner_id = (selection.get("winner_candidate") or {}).get("candidate_id")
        second_id = (selection.get("second_best_candidate") or {}).get("candidate_id")
        rows = []
        for candidate in candidates:
            candidate_id = candidate.get("candidate_id")
            score = score_by_id.get(candidate_id, {})
            simulation = simulations.get(candidate_id, {})
            metadata = (
                candidate.get("metadata")
                if isinstance(candidate.get("metadata"), dict)
                else {}
            )
            if governance[candidate_id]["decision"] == "BLOCK_CANDIDATE":
                status = "BLOCKED_BY_GOVERNANCE"
            elif candidate_id == winner_id and selection.get("selection_state") in {"WINNER_SELECTED", "CONDITIONAL_WINNER", "SANDBOX_ONLY_WINNER"}:
                status = "WINNER"
            elif candidate_id == second_id:
                status = "RUNNER_UP"
            elif simulation.get("simulation_errors") or simulation.get("unsupported_steps"):
                status = "REJECTED_BY_SIMULATION"
            elif not score.get("eligible_for_selection", False):
                status = "REJECTED_BY_SCORE"
            else:
                status = "EVALUATED"
            rows.append({
                "candidate_id": candidate_id,
                "source": candidate.get("source"),
                "sources": candidate.get("sources", []),
                "origin_source": candidate.get("origin_source"),
                "origin_sources": candidate.get("origin_sources", []),
                "normalized_source": candidate.get("normalized_source"),
                "normalized_sources": candidate.get("normalized_sources", []),
                "provenance_history": candidate.get("provenance_history", []),
                "operation": candidate.get("operation"),
                "score": score.get("final_score"),
                "accuracy": simulation.get("prediction_accuracy"),
                "simulation_success": simulation.get("simulation_success"),
                "status": status,
                "entered_arena": status != "BLOCKED_BY_GOVERNANCE",
                "selected": status == "WINNER",
                "validation_probe": candidate_id == validation_probe_id,
                "validation_probe_authority": (
                    "SANDBOX_VALIDATION_ONLY"
                    if candidate_id == validation_probe_id
                    else None
                ),
                "validation_status": governance[candidate_id]["decision"],
                "blocked_reason": ";".join(governance[candidate_id].get("reasons", [])) or None,
                "semantic_intent": candidate.get("intent"),
                "program_signature": candidate.get("program_signature"),
                "program_representation": metadata.get("program_representation"),
                "reuse_evidence": metadata.get("reuse_evidence"),
                "cross_source_consensus": candidate.get("cross_source_consensus"),
                "cross_source_consensus_id": candidate.get(
                    "cross_source_consensus_id"
                ),
                "consensus_sources": candidate.get("consensus_sources", []),
            })
        return rows

    def _candidate_by_id(self, candidates, candidate_id):
        return next((dict(item) for item in candidates if item.get("candidate_id") == candidate_id), {})

    def _no_competition_reason(self, eligible, diversity, gateway_report, blocked):
        if not eligible and blocked:
            return "All candidates were blocked by governance."
        if not eligible:
            return "No executable candidates were admitted."
        if len(eligible) == 1:
            return "Only one legitimate candidate entered the arena."
        if not diversity.get("diversity_sufficient"):
            return "Candidates lacked meaningful source or program diversity."
        return None

    def _execution_mode(self, selection, winner):
        state = selection.get("selection_state")
        if state == "WINNER_SELECTED":
            return "real"
        if state in {"CONDITIONAL_WINNER", "SANDBOX_ONLY_WINNER"}:
            return "sandbox"
        return "blocked"


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


cognitive_candidate_arena = CognitiveCandidateArena()

__all__ = ["CognitiveCandidateArena", "cognitive_candidate_arena"]
