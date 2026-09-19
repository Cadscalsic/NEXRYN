"""Observation-only natural production authority handoff tracing."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


PASSED_VALIDATION_STATES = {
    "PASSED",
    "SANDBOX_VALIDATION_PASSED",
    "ACCEPTED",
}
PASSED_QUALIFICATION_STATES = {"QUALIFIED", "EXECUTION_ELIGIBLE"}
SAFE_WINNER_STATES = {"WINNER_SELECTED", "EXECUTION_ELIGIBLE", "SAFE_WINNER"}
ADMITTED_BUDGET_STATES = {
    "RUNTIME_BUDGET_FINALIZED",
    "ROUTE_BUDGET_ADMITTED",
    "BUDGET_ADMITTED",
}


class NaturalProductionHandoffObserver:
    """Classify the natural candidate -> grant -> executor lifecycle."""

    system_name = "natural_production_handoff_observer"

    def build_trace(
        self,
        *,
        run_id: str | None = None,
        task_id: str | None = None,
        execution_plan_id: str | None = None,
        execution_plan_fingerprint: str | None = None,
        candidate: Mapping[str, Any] | None = None,
        materialization: Mapping[str, Any] | None = None,
        sandbox_validation: Mapping[str, Any] | None = None,
        qualification: Mapping[str, Any] | None = None,
        arena_selection: Mapping[str, Any] | None = None,
        execution_grant: Mapping[str, Any] | None = None,
        budget_admission: Mapping[str, Any] | None = None,
        production_execution: Mapping[str, Any] | None = None,
        production_outcome: Mapping[str, Any] | None = None,
        run_budget_state: str | None = None,
        synthetic_assistance_used: bool = False,
        test_fixture_used: bool = False,
        manual_grant_issuance: bool = False,
        manual_executor_invocation: bool = False,
    ) -> dict[str, Any]:
        candidate_map = dict(candidate or {})
        materialization_map = dict(materialization or {})
        validation_map = dict(sandbox_validation or {})
        qualification_map = dict(qualification or {})
        arena_map = dict(arena_selection or {})
        grant_map = dict(execution_grant or {})
        budget_map = dict(budget_admission or {})
        production_map = dict(production_execution or {})
        outcome_map = dict(production_outcome or {})

        selected_candidate = arena_map.get("selected_candidate")
        selected_candidate = selected_candidate if isinstance(selected_candidate, Mapping) else {}
        candidate_identity = self._candidate_identity(candidate_map or selected_candidate)
        selected_candidate_id = (
            arena_map.get("selected_candidate_id")
            or selected_candidate.get("candidate_id")
        )
        arena_decision = str(
            arena_map.get("selection_state")
            or arena_map.get("arena_decision")
            or "NOT_REACHED"
        )
        candidate_generated = bool(candidate_identity.get("candidate_id"))
        materialized = self._materialized(candidate_map, materialization_map)
        validation_passed = self._validation_passed(validation_map)
        qualified = self._qualified(qualification_map)
        arena_reached = bool(arena_map)
        safe_winner = (
            arena_decision in SAFE_WINNER_STATES
            and bool(selected_candidate_id)
        )
        safe_winner_predicate = self._safe_winner_predicate_evaluation(
            arena_map,
            run_id=run_id,
            task_id=task_id,
            execution_plan_id=execution_plan_id,
            execution_plan_fingerprint=execution_plan_fingerprint,
            arena_decision=arena_decision,
            selected_candidate_id=selected_candidate_id,
            safe_winner=safe_winner,
        )
        grant_expected = safe_winner
        grant_state = str(grant_map.get("grant_state") or "NOT_REACHED")
        grant_issued = grant_state in {"ISSUED", "CONSUMED"}
        budget_expected = grant_issued
        budget_state = self._budget_state(budget_map)
        budget_admitted = budget_state in ADMITTED_BUDGET_STATES
        executor_expected = grant_issued and budget_admitted
        executor_called = bool(
            production_map.get("underlying_executor_called") is True
            or production_map.get("real_execution_performed") is True
        )
        executor_reached = executor_called
        real_execution = production_map.get("real_execution_performed") is True
        outcome_state = str(
            production_map.get("outcome_provenance_state")
            or outcome_map.get("outcome_provenance_state")
            or "OUTCOME_PROVENANCE_NOT_REACHED"
        )
        outcome_complete = outcome_state == "OUTCOME_PROVENANCE_COMPLETE"
        lineage = self._lineage_state(
            run_id=run_id,
            candidate_identity=candidate_identity,
            selected_candidate_id=selected_candidate_id,
            grant=grant_map,
            production=production_map,
        )
        contamination = any(
            [
                synthetic_assistance_used,
                test_fixture_used,
                manual_grant_issuance,
                manual_executor_invocation,
            ]
        )
        unauthorized = self._unauthorized_activity(
            arena_decision=arena_decision,
            grant_expected=grant_expected,
            grant_issued=grant_issued,
            budget_expected=budget_expected,
            budget_admitted=budget_admitted,
            executor_expected=executor_expected,
            executor_called=executor_called,
            real_execution=real_execution,
        )
        expectations = self._expectations(
            candidate_generated=candidate_generated,
            materialized=materialized,
            validation_passed=validation_passed,
            qualified=qualified,
            arena_reached=arena_reached,
            safe_winner=safe_winner,
            grant_issued=grant_issued,
            budget_admitted=budget_admitted,
            executor_called=executor_called,
            real_execution=real_execution,
            outcome_complete=outcome_complete,
        )
        reachability_gaps = [
            row["boundary"]
            for row in expectations
            if row["expected"] is True
            and row["observed"] is not True
            and row["reachability_gap"] is True
        ]
        first_block = self._first_block(
            candidate_generated=candidate_generated,
            materialized=materialized,
            validation_passed=validation_passed,
            qualified=qualified,
            qualification=qualification_map,
            arena_reached=arena_reached,
            arena_decision=arena_decision,
            safe_winner=safe_winner,
            grant_expected=grant_expected,
            grant_issued=grant_issued,
            budget_expected=budget_expected,
            budget_admitted=budget_admitted,
            executor_expected=executor_expected,
            executor_called=executor_called,
            real_execution=real_execution,
            outcome_complete=outcome_complete,
            contamination=contamination,
        )
        phase_state = self._phase_state(
            unauthorized=bool(unauthorized),
            contamination=contamination,
            natural_e7=real_execution and outcome_complete,
            reachability_gaps=reachability_gaps,
            candidate_generated=candidate_generated,
            first_block=first_block,
        )
        boundaries = {
            "candidate_generated": "PASSED" if candidate_generated else "BLOCKED",
            "materialization": self._boundary_state(candidate_generated, materialized),
            "sandbox_validation": self._boundary_state(materialized, validation_passed),
            "qualification": self._boundary_state(validation_passed, qualified),
            "arena": self._arena_boundary_state(qualified, arena_reached, arena_decision, safe_winner),
            "execution_grant": self._expected_boundary_state(grant_expected, grant_issued),
            "candidate_budget_admission": self._expected_boundary_state(budget_expected, budget_admitted),
            "production_executor": self._expected_boundary_state(executor_expected, executor_called),
            "outcome_provenance": self._expected_boundary_state(real_execution, outcome_complete),
        }
        highest_natural_level = self._highest_level(
            candidate_generated=candidate_generated,
            materialized=materialized,
            validation_passed=validation_passed,
            qualified=qualified,
            arena_reached=arena_reached,
            safe_winner=safe_winner,
            grant_issued=grant_issued,
            budget_admitted=budget_admitted,
            executor_called=executor_called,
            real_execution=real_execution,
            outcome_complete=outcome_complete,
        )
        trace = {
            "system": self.system_name,
            "trace_state": "FINAL",
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "phase_3_state": phase_state,
            "run_id": str(run_id or production_map.get("run_id") or grant_map.get("run_id") or "UNKNOWN"),
            "task_id": str(task_id or candidate_map.get("task_id") or "UNKNOWN"),
            "execution_plan_id": execution_plan_id,
            "execution_plan_fingerprint": execution_plan_fingerprint,
            "candidate_generated": "PASSED" if candidate_generated else "BLOCKED",
            "candidate_id": candidate_identity.get("candidate_id"),
            "candidate_source": candidate_identity.get("candidate_source"),
            "candidate_type": candidate_identity.get("candidate_type"),
            "candidate_fingerprint": candidate_identity.get("candidate_fingerprint"),
            "learned_object_id": candidate_identity.get("learned_object_id"),
            "source_program_id": candidate_identity.get("source_program_id"),
            "producer_operation_id": candidate_identity.get("producer_operation_id"),
            "materialized": "PASSED" if materialized else "NOT_REACHED",
            "materialization_id": materialization_map.get("materialization_id"),
            "sandbox_validation_reached": bool(validation_map),
            "sandbox_validation_state": self._validation_state(validation_map),
            "qualification_reached": bool(qualification_map),
            "qualification_state": self._qualification_state(qualification_map),
            "qualification_id": qualification_map.get("qualification_id"),
            "arena_reached": arena_reached,
            "arena_decision": arena_decision,
            "arena_selected_candidate_id": selected_candidate_id,
            "safe_winner_selected": safe_winner,
            "safe_winner_predicate_evaluation": safe_winner_predicate,
            "grant_boundary_reached": bool(grant_map),
            "grant_expected": grant_expected,
            "grant_state": grant_state,
            "grant_id": grant_map.get("grant_id"),
            "budget_boundary_reached": bool(budget_map),
            "candidate_budget_admission_expected": budget_expected,
            "budget_admission_state": budget_state,
            "run_budget_state": run_budget_state,
            "production_candidate_budget_admission_state": budget_state,
            "production_executor_expected": executor_expected,
            "production_executor_reached": executor_reached,
            "production_executor_called": executor_called,
            "underlying_executor_called": executor_called,
            "real_execution_performed": real_execution,
            "execution_result_id": production_map.get("execution_result_id"),
            "outcome_provenance_state": outcome_state,
            "highest_contract_proven_level": "E7",
            "highest_natural_execution_level": highest_natural_level,
            "highest_natural_runtime_level": highest_natural_level,
            "first_unreached_boundary": self._first_unreached(boundaries),
            "first_blocked_boundary": first_block,
            "blocking_state": first_block,
            "blocking_reason": self._blocking_reason(first_block, arena_decision),
            "candidate_lineage_state": lineage,
            "boundary_states": boundaries,
            "expected_vs_observed_reachability": expectations,
            "synthetic_assistance_used": bool(synthetic_assistance_used),
            "test_fixture_used": bool(test_fixture_used),
            "manual_grant_issuance": bool(manual_grant_issuance),
            "manual_executor_invocation": bool(manual_executor_invocation),
            "authority_bypass_detected": bool(unauthorized),
            "unauthorized_downstream_activity": unauthorized or "NONE",
            "reachability_gap": bool(reachability_gaps),
            "reachability_gap_boundaries": reachability_gaps,
        }
        trace["trace_id"] = self._stable_id("natural_production_handoff", trace)
        return trace

    def _safe_winner_predicate_evaluation(
        self,
        arena: Mapping[str, Any],
        *,
        run_id: str | None,
        task_id: str | None,
        execution_plan_id: str | None,
        execution_plan_fingerprint: str | None,
        arena_decision: str,
        selected_candidate_id: Any,
        safe_winner: bool,
    ) -> dict[str, Any]:
        diagnostics = (
            arena.get("candidate_arena_diagnostics")
            if isinstance(arena.get("candidate_arena_diagnostics"), Mapping)
            else {}
        )
        selection = (
            diagnostics.get("selection_report")
            if isinstance(diagnostics.get("selection_report"), Mapping)
            else {}
        )
        winner = (
            selection.get("winner_candidate")
            if isinstance(selection.get("winner_candidate"), Mapping)
            else {}
        )
        second = (
            selection.get("second_best_candidate")
            if isinstance(selection.get("second_best_candidate"), Mapping)
            else {}
        )
        thresholds = (
            selection.get("thresholds")
            if isinstance(selection.get("thresholds"), Mapping)
            else {}
        )
        winner_id = winner.get("candidate_id") or selected_candidate_id
        simulations = (
            diagnostics.get("simulations")
            if isinstance(diagnostics.get("simulations"), Mapping)
            else {}
        )
        simulation = (
            simulations.get(winner_id)
            if winner_id and isinstance(simulations.get(winner_id), Mapping)
            else {}
        )
        top_score = self._number(
            winner.get("final_score"),
            arena.get("winner_score"),
        )
        second_score = self._number(
            second.get("final_score"),
            arena.get("second_best_score"),
        )
        margin = self._number(
            selection.get("selection_margin"),
            arena.get("selection_margin"),
        )
        accuracy = self._number(simulation.get("prediction_accuracy"))
        analysis_only = arena.get("analysis_only")
        if analysis_only is None:
            summary = arena.get("candidate_arena_summary")
            if isinstance(summary, Mapping):
                analysis_only = summary.get("analysis_only")
        inputs_complete = all(
            value is not None
            for value in (top_score, margin, accuracy, analysis_only)
        ) and bool(thresholds)
        strong_score_required = float(thresholds.get("strong_score", 0.90))
        strong_margin_required = float(thresholds.get("strong_margin", 0.05))
        conditional_score_required = float(
            thresholds.get("conditional_score", 0.80)
        )
        conditional_margin_required = float(
            thresholds.get("conditional_margin", 0.02)
        )
        minimum_accuracy = float(thresholds.get("minimum_accuracy", 0.60))
        minimum_score = float(thresholds.get("minimum_score", 0.55))
        tie_margin = float(thresholds.get("tie_margin", 0.02))
        accuracy_passed = accuracy is not None and accuracy >= minimum_accuracy
        tie_observed = bool(second) and margin is not None and abs(margin) < tie_margin
        strong_score_passed = (
            top_score is not None and top_score >= strong_score_required
        )
        strong_margin_passed = (
            margin is not None and margin >= strong_margin_required
        )
        strong_passed = strong_score_passed and strong_margin_passed
        conditional_score_passed = (
            top_score is not None and top_score >= conditional_score_required
        )
        conditional_margin_passed = (
            margin is not None and margin >= conditional_margin_required
        )
        conditional_passed = (
            conditional_score_passed and conditional_margin_passed
        )
        sandbox_passed = bool(
            analysis_only
            and top_score is not None
            and top_score >= minimum_score
            and accuracy_passed
            and not tie_observed
            and not strong_passed
            and not conditional_passed
        )
        candidate_rows = arena.get("candidate_summary") or arena.get(
            "candidate_rows"
        ) or []
        candidate_ids = [
            row.get("candidate_id")
            for row in candidate_rows
            if isinstance(row, Mapping) and row.get("candidate_id")
        ]
        if not candidate_ids:
            candidate_ids = [
                row.get("candidate_id")
                for row in diagnostics.get("scores", []) or []
                if isinstance(row, Mapping) and row.get("candidate_id")
            ]
        if winner_id and winner_id not in candidate_ids:
            candidate_ids.append(winner_id)
        candidate_ids = sorted(set(candidate_ids))
        score_rows = [
            dict(row)
            for row in diagnostics.get("scores", []) or []
            if isinstance(row, Mapping) and row.get("candidate_id")
        ]
        if not score_rows:
            score_rows = [dict(row) for row in (winner, second) if row]
        score_rows.sort(
            key=lambda row: (
                -float(row.get("final_score", 0.0) or 0.0),
                str(row.get("candidate_id") or ""),
            )
        )
        ranked_candidate_scores = [
            {
                "rank_position": index + 1,
                "candidate_id": row.get("candidate_id"),
                "final_score": self._number(row.get("final_score")),
                "eligible_for_selection": row.get("eligible_for_selection"),
                "selection_blockers": list(row.get("selection_blockers") or []),
                "score_components": dict(row.get("score_components") or {}),
                "penalties": dict(row.get("penalties") or {}),
                "score_composition": dict(row.get("score_composition") or {}),
            }
            for index, row in enumerate(score_rows)
        ]
        normalized_candidates = [
            dict(row)
            for row in arena.get("normalized_candidates", []) or []
            if isinstance(row, Mapping) and row.get("candidate_id")
        ]
        selected_candidate = arena.get("selected_candidate")
        if not isinstance(selected_candidate, Mapping):
            selected_candidate = {}
        if selected_candidate and not normalized_candidates:
            normalized_candidates = [dict(selected_candidate)]
        candidate_records = []
        for candidate in normalized_candidates:
            candidate_payload = dict(candidate)
            candidate_fingerprint = hashlib.sha256(
                json.dumps(
                    candidate_payload,
                    sort_keys=True,
                    ensure_ascii=True,
                    default=str,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            candidate_records.append({
                "candidate_id": candidate.get("candidate_id"),
                "immutable_fingerprint": candidate_fingerprint,
                "candidate_type": candidate.get("candidate_type"),
                "source": candidate.get("source"),
                "source_run_id": candidate.get("source_run_id") or candidate.get("run_id"),
                "source_task_id": candidate.get("source_task_id") or candidate.get("task_id"),
                "qualification_reference": candidate.get("qualification_id"),
                "program": candidate.get("program"),
                "transformation": candidate.get("transformation"),
                "source_artifact": candidate.get("source_artifact"),
                "canonical_candidate": candidate_payload,
            })
        candidate_set_id = arena.get("candidate_set_id")
        if not candidate_set_id:
            candidate_set_id = self._stable_id(
                "candidate_set", {"candidate_ids": candidate_ids}
            )
        binding = {
            "run_id": str(run_id or "UNKNOWN"),
            "task_id": str(task_id or "UNKNOWN"),
            "execution_plan_id": execution_plan_id,
            "execution_plan_fingerprint": execution_plan_fingerprint,
            "candidate_set_id": candidate_set_id,
            "candidate_ids": candidate_ids,
            "selected_candidate_id": selected_candidate_id,
        }
        evaluation_timestamp = datetime.now(timezone.utc).isoformat()
        arena_decision_id = self._stable_id(
            "arena_decision",
            {
                **binding,
                "selection_state": arena_decision,
                "selection_margin": margin,
            },
        )
        score_by_id = {
            row.get("candidate_id"): row
            for row in ranked_candidate_scores
            if row.get("candidate_id")
        }
        candidate_by_id = {
            row.get("candidate_id"): row
            for row in candidate_records
            if row.get("candidate_id")
        }
        governance = (
            diagnostics.get("governance_decisions")
            if isinstance(diagnostics.get("governance_decisions"), Mapping)
            else {}
        )
        ordered_candidate_records = []
        for score_row in ranked_candidate_scores:
            candidate_id = score_row.get("candidate_id")
            candidate_record = candidate_by_id.get(candidate_id, {})
            canonical_candidate = candidate_record.get("canonical_candidate")
            canonical_candidate = (
                canonical_candidate
                if isinstance(canonical_candidate, Mapping)
                else {}
            )
            semantics = {
                "operation": canonical_candidate.get("operation"),
                "program": canonical_candidate.get("program"),
                "transformation": canonical_candidate.get("transformation"),
                "program_signature": canonical_candidate.get("program_signature"),
            }
            semantics_available = bool(
                semantics.get("program")
                or semantics.get("transformation")
                or semantics.get("operation")
            )
            semantics_fingerprint = hashlib.sha256(
                json.dumps(
                    semantics,
                    sort_keys=True,
                    ensure_ascii=True,
                    default=str,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            governance_record = governance.get(candidate_id, {})
            if not isinstance(governance_record, Mapping):
                governance_record = {}
            qualification_payload = {
                "candidate_id": candidate_id,
                "decision": governance_record.get("decision"),
                "reasons": list(governance_record.get("reasons") or []),
                "run_id": binding["run_id"],
                "task_id": binding["task_id"],
            }
            qualification_id = (
                canonical_candidate.get("qualification_id")
                or self._stable_id("arena_qualification", qualification_payload)
            )
            ordered_candidate_records.append({
                "candidate_id": candidate_id,
                "candidate_fingerprint": candidate_record.get("immutable_fingerprint"),
                "candidate_type": (
                    candidate_record.get("candidate_type")
                    or canonical_candidate.get("learned_object_type")
                    or "EXECUTABLE_CANDIDATE"
                ),
                "source_component": candidate_record.get("source"),
                "source_artifact": candidate_record.get("source_artifact"),
                "executable_semantics_reference": (
                    canonical_candidate.get("program_signature")
                    or f"candidate_semantics:{semantics_fingerprint[:16]}"
                ),
                "executable_semantics_fingerprint": semantics_fingerprint,
                "executable_semantics_available": semantics_available,
                "executable_semantics": semantics,
                "score": score_row.get("final_score"),
                "deterministic_rank": score_row.get("rank_position"),
                "qualification_id": qualification_id,
                "qualification_decision": governance_record.get("decision"),
                "candidate_set_id": candidate_set_id,
                "run_id": binding["run_id"],
                "task_id": binding["task_id"],
                "execution_plan_id": execution_plan_id,
                "arena_decision_id": arena_decision_id,
                "evaluation_timestamp": evaluation_timestamp,
                "authority": "OBSERVATION_ONLY",
                "behavioral_authority": "NONE",
            })
        candidate_set_fingerprint = hashlib.sha256(
            json.dumps(
                [
                    {
                        "candidate_id": row["candidate_id"],
                        "candidate_fingerprint": row["candidate_fingerprint"],
                    }
                    for row in ordered_candidate_records
                ],
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        top_tie_candidate_ids = []
        if ordered_candidate_records and top_score is not None:
            top_tie_candidate_ids = sorted(
                row["candidate_id"]
                for row in ordered_candidate_records
                if row.get("score") is not None
                and abs(float(top_score) - float(row["score"])) < tie_margin
            )
        tie_group_payload = {
            "candidate_set_id": candidate_set_id,
            "candidate_ids": top_tie_candidate_ids,
            "top_score": top_score,
            "tie_margin": tie_margin,
        }
        top_tie_group_fingerprint = hashlib.sha256(
            json.dumps(
                tie_group_payload,
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        top_tie_group_id = f"arena_top_tie_group_{top_tie_group_fingerprint[:16]}"
        for record in ordered_candidate_records:
            record["tie_group_id"] = (
                top_tie_group_id
                if record["candidate_id"] in top_tie_candidate_ids
                else None
            )
        canonical_contract_complete = bool(
            ordered_candidate_records
            and len(ordered_candidate_records) == len(score_by_id)
            and len(ordered_candidate_records) == len(candidate_by_id)
            and all(
                row.get("candidate_id")
                and row.get("candidate_fingerprint")
                and row.get("score") is not None
                and row.get("deterministic_rank") is not None
                and row.get("qualification_id")
                and row.get("executable_semantics_reference")
                and row.get("executable_semantics_fingerprint")
                and row.get("executable_semantics_available") is True
                for row in ordered_candidate_records
            )
        )

        def predicate(name: str, branch: str, observed: Any, required: Any, result: bool) -> dict[str, Any]:
            return {
                "predicate_name": name,
                "branch": branch,
                "observed_value": observed,
                "required_value": required,
                "result": bool(result),
                "input_source": "cognitive_candidate_arena.winner_selection_policy",
                "lineage_identity": dict(binding),
                "temporal_run_binding": "CURRENT_RUN_BOUND",
                "can_grant_behavioral_authority": False,
                "telemetry_authority": "OBSERVATION_ONLY",
                "behavioral_authority": "NONE",
            }

        evaluations = [
            predicate("PREDICTION_ACCURACY_THRESHOLD", "pre_selection", accuracy, f">={minimum_accuracy}", accuracy_passed),
            predicate("UNRESOLVED_TIE", "tie", {"second_candidate_present": bool(second), "margin": margin}, f"margin_not_below_{tie_margin}", not tie_observed),
            predicate("STRONG_WINNER_SCORE_THRESHOLD", "strong_winner", top_score, f">={strong_score_required}", strong_score_passed),
            predicate("STRONG_WINNER_MARGIN_THRESHOLD", "strong_winner", margin, f">={strong_margin_required}", strong_margin_passed),
            predicate("STRONG_WINNER", "strong_winner", {"score": strong_score_passed, "margin": strong_margin_passed}, "all_true", strong_passed),
            predicate("CONDITIONAL_WINNER_SCORE_THRESHOLD", "conditional_winner", top_score, f">={conditional_score_required}", conditional_score_passed),
            predicate("CONDITIONAL_WINNER_MARGIN_THRESHOLD", "conditional_winner", margin, f">={conditional_margin_required}", conditional_margin_passed),
            predicate("CONDITIONAL_WINNER", "conditional_winner", {"score": conditional_score_passed, "margin": conditional_margin_passed}, "all_true", conditional_passed),
            predicate("SANDBOX_WINNER", "sandbox_winner", {"analysis_only": analysis_only, "top_score": top_score}, {"analysis_only": True, "top_score": f">={minimum_score}"}, sandbox_passed),
            predicate("SAFE_WINNER", "production_handoff", arena_decision, sorted(SAFE_WINNER_STATES), safe_winner),
            predicate("EXECUTION_ELIGIBILITY", "production_handoff", {"safe_winner": safe_winner, "selected_candidate_id": selected_candidate_id}, {"safe_winner": True, "selected_candidate_present": True}, safe_winner and bool(selected_candidate_id)),
        ]
        earliest_failed = next(
            (
                row["predicate_name"]
                for row in evaluations
                if row["predicate_name"] in {
                    "PREDICTION_ACCURACY_THRESHOLD",
                    "UNRESOLVED_TIE",
                    "STRONG_WINNER_SCORE_THRESHOLD",
                    "STRONG_WINNER_MARGIN_THRESHOLD",
                }
                and row["result"] is False
            ),
            "NONE",
        )
        payload = {
            "schema_version": "1.0",
            "source_component": "natural_production_handoff_observer",
            "predicate": (
                "selection_state_in_safe_winner_states_and_selected_candidate_present"
            ),
            **binding,
            "arena_decision_id": arena_decision_id,
            "observed_selection_state": arena_decision,
            "required_selection_states": sorted(SAFE_WINNER_STATES),
            "selected_candidate_id": selected_candidate_id,
            "safe_winner_selected": safe_winner,
            "analysis_only": analysis_only,
            "top_score": top_score,
            "second_best_score": second_score,
            "selection_margin": margin,
            "prediction_accuracy": accuracy,
            "thresholds": dict(thresholds),
            "strong_winner_predicate_passed": strong_passed,
            "conditional_winner_predicate_passed": conditional_passed,
            "sandbox_winner_predicate_passed": sandbox_passed,
            "safe_winner_predicate_passed": safe_winner,
            "execution_eligibility_predicate_passed": (
                safe_winner and bool(selected_candidate_id)
            ),
            "evidence_state": "NOT_CONSUMED_BY_WINNER_SELECTION_POLICY",
            "evidence_requirement": "NONE",
            "ranked_candidate_scores": ranked_candidate_scores,
            "candidate_records": candidate_records,
            "complete_evaluated_candidate_count": len(ordered_candidate_records),
            "ordered_candidate_records": ordered_candidate_records,
            "deterministic_ranking_policy": "FINAL_SCORE_DESC_THEN_CANDIDATE_ID_ASC",
            "candidate_set_fingerprint": candidate_set_fingerprint,
            "tie_threshold": tie_margin,
            "top_tie_group_id": top_tie_group_id,
            "top_tie_group_fingerprint": top_tie_group_fingerprint,
            "top_tie_candidate_ids": top_tie_candidate_ids,
            "top_tie_member_count": len(top_tie_candidate_ids),
            "canonical_persistence_contract_state": (
                "COMPLETE" if canonical_contract_complete else "INCOMPLETE"
            ),
            "predicate_evaluations": evaluations,
            "earliest_failed_substantive_predicate": earliest_failed,
            "predicate_inputs_complete": inputs_complete,
            "predicate_evaluation_state": (
                "EVALUATED" if inputs_complete else "INSUFFICIENT_OBSERVABILITY"
            ),
            "telemetry_authority": "OBSERVATION_ONLY",
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                ensure_ascii=True,
                default=str,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return {
            **payload,
            "predicate_record_id": f"safe_winner_predicate_{fingerprint[:16]}",
            "immutable_fingerprint": fingerprint,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def verify_predicate_record(self, record: Mapping[str, Any]) -> bool:
        payload = {
            key: value
            for key, value in record.items()
            if key not in {
                "predicate_record_id",
                "immutable_fingerprint",
                "created_at",
                "production_handoff_id",
                "artifact_fingerprint",
            }
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                ensure_ascii=True,
                default=str,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return fingerprint == record.get("immutable_fingerprint")

    def verify_canonical_arena_persistence(self, record: Mapping[str, Any]) -> bool:
        rows = record.get("ordered_candidate_records")
        candidates = record.get("candidate_records")
        if not isinstance(rows, list) or not rows or not isinstance(candidates, list):
            return False
        ids = [row.get("candidate_id") for row in rows if isinstance(row, Mapping)]
        if len(ids) != len(rows) or len(set(ids)) != len(ids):
            return False
        if record.get("complete_evaluated_candidate_count") != len(rows):
            return False
        if [row.get("deterministic_rank") for row in rows] != list(range(1, len(rows) + 1)):
            return False
        if ids != sorted(ids, key=lambda candidate_id: (
            -float(next(row.get("score") for row in rows if row.get("candidate_id") == candidate_id)),
            str(candidate_id),
        )):
            return False
        canonical_by_id = {
            row.get("candidate_id"): row
            for row in candidates
            if isinstance(row, Mapping) and row.get("candidate_id")
        }
        if set(canonical_by_id) != set(ids):
            return False
        for row in rows:
            candidate = canonical_by_id[row["candidate_id"]]
            canonical_payload = candidate.get("canonical_candidate")
            semantics = row.get("executable_semantics")
            if not isinstance(canonical_payload, Mapping) or not isinstance(semantics, Mapping):
                return False
            candidate_fingerprint = hashlib.sha256(json.dumps(
                dict(canonical_payload), sort_keys=True, ensure_ascii=True,
                default=str, separators=(",", ":"),
            ).encode("utf-8")).hexdigest()
            semantics_fingerprint = hashlib.sha256(json.dumps(
                dict(semantics), sort_keys=True, ensure_ascii=True,
                default=str, separators=(",", ":"),
            ).encode("utf-8")).hexdigest()
            if candidate_fingerprint != row.get("candidate_fingerprint"):
                return False
            if candidate_fingerprint != candidate.get("immutable_fingerprint"):
                return False
            if semantics_fingerprint != row.get("executable_semantics_fingerprint"):
                return False
            if row.get("candidate_set_id") != record.get("candidate_set_id"):
                return False
            if row.get("run_id") != record.get("run_id"):
                return False
            if row.get("task_id") != record.get("task_id"):
                return False
            if row.get("execution_plan_id") != record.get("execution_plan_id"):
                return False
            if row.get("arena_decision_id") != record.get("arena_decision_id"):
                return False
            if row.get("qualification_id") in (None, ""):
                return False
            if row.get("executable_semantics_available") is not True:
                return False
            if row.get("authority") != "OBSERVATION_ONLY" or row.get("behavioral_authority") != "NONE":
                return False
        candidate_set_fingerprint = hashlib.sha256(json.dumps(
            [{"candidate_id": row["candidate_id"], "candidate_fingerprint": row["candidate_fingerprint"]} for row in rows],
            sort_keys=True, ensure_ascii=True, separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        if candidate_set_fingerprint != record.get("candidate_set_fingerprint"):
            return False
        top_score = max(float(row["score"]) for row in rows)
        ordered_scores = [float(row["score"]) for row in rows]
        runner_up = ordered_scores[1] if len(ordered_scores) > 1 else None
        expected_margin = round(top_score - runner_up, 4) if runner_up is not None else top_score
        if top_score != record.get("top_score") or runner_up != record.get("second_best_score"):
            return False
        if expected_margin != record.get("selection_margin"):
            return False
        tie_threshold = float(record.get("tie_threshold"))
        top_ids = sorted(row["candidate_id"] for row in rows if abs(top_score - float(row["score"])) < tie_threshold)
        if top_ids != record.get("top_tie_candidate_ids"):
            return False
        if len(top_ids) != record.get("top_tie_member_count"):
            return False
        tie_payload = {
            "candidate_set_id": record.get("candidate_set_id"),
            "candidate_ids": top_ids,
            "top_score": record.get("top_score"),
            "tie_margin": tie_threshold,
        }
        tie_fingerprint = hashlib.sha256(json.dumps(
            tie_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        if tie_fingerprint != record.get("top_tie_group_fingerprint"):
            return False
        if record.get("top_tie_group_id") != f"arena_top_tie_group_{tie_fingerprint[:16]}":
            return False
        if any(
            row.get("tie_group_id") != (record["top_tie_group_id"] if row["candidate_id"] in top_ids else None)
            for row in rows
        ):
            return False
        return record.get("canonical_persistence_contract_state") == "COMPLETE"

    def persist_predicate_record(
        self,
        trace: Mapping[str, Any],
        artifact_root: str | os.PathLike[str] = (
            "runtime/artifacts/safe_winner_predicates"
        ),
    ) -> dict[str, Any]:
        record = trace.get("safe_winner_predicate_evaluation")
        if (
            not isinstance(record, Mapping)
            or not self.verify_predicate_record(record)
            or not self.verify_canonical_arena_persistence(record)
        ):
            raise ValueError("safe_winner_predicate_record_integrity_failed")
        run_id = str(record.get("run_id") or "UNKNOWN")
        root = Path(artifact_root)
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{run_id}.json"
        temporary = path.with_suffix(".json.tmp")
        persisted_record = {
            **dict(record),
            "production_handoff_id": trace.get("trace_id"),
        }
        persisted_record["artifact_fingerprint"] = hashlib.sha256(
            json.dumps(
                persisted_record,
                sort_keys=True,
                ensure_ascii=True,
                default=str,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        temporary.write_text(
            json.dumps(
                persisted_record,
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
                default=str,
            ) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
        persisted = json.loads(path.read_text(encoding="utf-8"))
        if (
            not self.verify_predicate_record(persisted)
            or not self.verify_canonical_arena_persistence(persisted)
        ):
            raise ValueError("persisted_safe_winner_predicate_record_invalid")
        return {
            "persistence_state": "PERSISTED_AND_VERIFIED",
            "artifact_path": str(path),
            "predicate_record_id": record.get("predicate_record_id"),
            "immutable_fingerprint": record.get("immutable_fingerprint"),
            "artifact_fingerprint": persisted.get("artifact_fingerprint"),
            "production_handoff_id": trace.get("trace_id"),
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
        }

    def _number(self, *values: Any) -> float | None:
        for value in values:
            if value is None or isinstance(value, bool):
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    def _candidate_identity(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
        learned_object_id = (
            candidate.get("learned_object_id")
            or candidate.get("source_learned_object_id")
            or metadata.get("learned_object_id")
            or metadata.get("source_learned_object_id")
        )
        fingerprint = (
            candidate.get("candidate_fingerprint")
            or metadata.get("candidate_fingerprint")
            or self._stable_id("candidate_fingerprint", candidate)
            if candidate.get("candidate_id")
            else None
        )
        return {
            "candidate_id": candidate.get("candidate_id"),
            "candidate_source": candidate.get("source") or metadata.get("source"),
            "candidate_type": candidate.get("candidate_type")
            or candidate.get("learned_object_type")
            or metadata.get("candidate_type")
            or metadata.get("learned_object_type"),
            "candidate_fingerprint": fingerprint,
            "learned_object_id": learned_object_id,
            "source_program_id": candidate.get("source_program_id")
            or candidate.get("program_id")
            or learned_object_id,
            "producer_operation_id": candidate.get("producer_operation_id")
            or metadata.get("producer_operation_id"),
            "run_id": candidate.get("run_id") or candidate.get("target_run_id"),
        }

    def _materialized(
        self,
        candidate: Mapping[str, Any],
        materialization: Mapping[str, Any],
    ) -> bool:
        state = str(materialization.get("materialization_state") or "")
        return bool(
            candidate.get("candidate_id")
            and (
                not materialization
                or materialization.get("materialized") is True
                or state in {"MATERIALIZED", "PASSED", "CANDIDATE_MATERIALIZED"}
            )
        )

    def _validation_passed(self, validation: Mapping[str, Any]) -> bool:
        return bool(
            validation.get("validation_success") is True
            or validation.get("validation_state") in PASSED_VALIDATION_STATES
        )

    def _qualified(self, qualification: Mapping[str, Any]) -> bool:
        return qualification.get("qualification_state") in PASSED_QUALIFICATION_STATES

    def _budget_state(self, budget: Mapping[str, Any]) -> str:
        return str(
            budget.get("budget_admission_state")
            or budget.get("runtime_budget_state")
            or budget.get("route_budget_enforcement_state")
            or "NOT_REACHED"
        )

    def _validation_state(self, validation: Mapping[str, Any]) -> str:
        if not validation:
            return "NOT_REACHED"
        if self._validation_passed(validation):
            return "PASSED"
        return str(validation.get("validation_state") or "BLOCKED")

    def _qualification_state(self, qualification: Mapping[str, Any]) -> str:
        if not qualification:
            return "NOT_REACHED"
        if self._qualified(qualification):
            return "PASSED"
        return str(qualification.get("qualification_state") or "BLOCKED")

    def _boundary_state(self, expected: bool, passed: bool) -> str:
        if passed:
            return "PASSED"
        return "BLOCKED" if expected else "NOT_REACHED"

    def _arena_boundary_state(
        self,
        expected: bool,
        reached: bool,
        decision: str,
        safe_winner: bool,
    ) -> str:
        if not expected:
            return "NOT_REACHED"
        if safe_winner:
            return "PASSED"
        if reached and decision in {"TIE_REQUIRES_REVIEW", "NO_SAFE_WINNER"}:
            return "BLOCKED"
        return "REACHED" if reached else "NOT_REACHED"

    def _expected_boundary_state(self, expected: bool, observed: bool) -> str:
        if observed:
            return "PASSED"
        return "NOT_REACHED" if not expected else "BLOCKED"

    def _expectations(self, **state: bool) -> list[dict[str, Any]]:
        rows = [
            ("candidate_generated", True, state["candidate_generated"]),
            ("materialization", state["candidate_generated"], state["materialized"]),
            ("sandbox_validation", state["materialized"], state["validation_passed"]),
            ("qualification", state["validation_passed"], state["qualified"]),
            ("arena_selection", state["qualified"], state["arena_reached"]),
            ("execution_grant", state["safe_winner"], state["grant_issued"]),
            ("candidate_budget_admission", state["grant_issued"], state["budget_admitted"]),
            ("production_executor", state["grant_issued"] and state["budget_admitted"], state["executor_called"]),
            ("outcome_provenance", state["real_execution"], state["outcome_complete"]),
        ]
        return [
            {
                "boundary": boundary,
                "expected": bool(expected),
                "observed": bool(observed),
                "state": (
                    "OBSERVED"
                    if observed
                    else "EXPECTED_NOT_OBSERVED"
                    if expected
                    else "NOT_EXPECTED"
                ),
                "reachability_gap": bool(expected and not observed),
            }
            for boundary, expected, observed in rows
        ]

    def _unauthorized_activity(
        self,
        *,
        arena_decision: str,
        grant_expected: bool,
        grant_issued: bool,
        budget_expected: bool,
        budget_admitted: bool,
        executor_expected: bool,
        executor_called: bool,
        real_execution: bool,
    ) -> str | None:
        blocked_arena = arena_decision in {"TIE_REQUIRES_REVIEW", "NO_SAFE_WINNER"}
        if blocked_arena and grant_issued:
            return "UNEXPECTED_GRANT_AFTER_BLOCK"
        if blocked_arena and executor_called:
            return "UNAUTHORIZED_EXECUTOR_REACHABILITY"
        if blocked_arena and real_execution:
            return "UNAUTHORIZED_PRODUCTION_EXECUTION"
        if not grant_expected and grant_issued:
            return "UNEXPECTED_GRANT_AFTER_BLOCK"
        if not budget_expected and budget_admitted:
            return "UNEXPECTED_BUDGET_ADMISSION_AFTER_BLOCK"
        if not executor_expected and executor_called:
            return "UNAUTHORIZED_EXECUTOR_REACHABILITY"
        return None

    def _first_block(self, **state: Any) -> str:
        if state["contamination"]:
            return "NATURAL_E7_PROOF_INVALID"
        if not state["candidate_generated"]:
            return "CANDIDATE_NOT_GENERATED"
        if not state["materialized"]:
            return "MATERIALIZATION_BLOCKED"
        if not state["validation_passed"]:
            return "SANDBOX_VALIDATION_FAILED"
        if not state["qualified"]:
            return (
                "QUALIFICATION_BLOCKED"
                if state["qualification"]
                else "EVIDENCE_INSUFFICIENT"
            )
        if not state["arena_reached"]:
            return "ARENA_ADMISSION_BLOCKED"
        if state["arena_decision"] == "TIE_REQUIRES_REVIEW":
            return "ARENA_TIE_REQUIRES_REVIEW"
        if state["arena_decision"] == "NO_SAFE_WINNER" or not state["safe_winner"]:
            return "ARENA_NO_SAFE_WINNER"
        if state["grant_expected"] and not state["grant_issued"]:
            return "EXECUTION_GRANT_BLOCKED"
        if state["budget_expected"] and not state["budget_admitted"]:
            return "RUNTIME_BUDGET_BLOCKED"
        if state["executor_expected"] and not state["executor_called"]:
            return "PRODUCTION_EXECUTOR_NOT_REACHED"
        if not state["real_execution"]:
            return "EXECUTION_INTEGRITY_BLOCKED"
        if not state["outcome_complete"]:
            return "OUTCOME_PROVENANCE_INCOMPLETE"
        return "NATURAL_E7_REACHED"

    def _phase_state(
        self,
        *,
        unauthorized: bool,
        contamination: bool,
        natural_e7: bool,
        reachability_gaps: list[str],
        candidate_generated: bool,
        first_block: str,
    ) -> str:
        if unauthorized:
            return "UNAUTHORIZED_DOWNSTREAM_REACHABILITY"
        if contamination:
            return "INSUFFICIENT_OBSERVABILITY"
        if natural_e7:
            return "NATURAL_END_TO_END_REACHABILITY_PROVEN"
        if reachability_gaps and first_block not in {
            "ARENA_TIE_REQUIRES_REVIEW",
            "ARENA_NO_SAFE_WINNER",
            "QUALIFICATION_BLOCKED",
            "EVIDENCE_INSUFFICIENT",
            "SANDBOX_VALIDATION_FAILED",
        }:
            return "NATURAL_HANDOFF_GAP_PROVEN"
        if candidate_generated:
            return "NATURAL_RUNTIME_LAWFULLY_BLOCKED_UPSTREAM"
        return "INSUFFICIENT_OBSERVABILITY"

    def _lineage_state(
        self,
        *,
        run_id: str | None,
        candidate_identity: Mapping[str, Any],
        selected_candidate_id: Any,
        grant: Mapping[str, Any],
        production: Mapping[str, Any],
    ) -> str:
        candidate_id = str(candidate_identity.get("candidate_id") or "")
        if not candidate_id:
            return "CANDIDATE_LINEAGE_UNDETERMINED"
        if selected_candidate_id and str(selected_candidate_id) != candidate_id:
            return "CANDIDATE_LINEAGE_BREAK"
        if grant.get("candidate_id") and str(grant.get("candidate_id")) != candidate_id:
            return "CANDIDATE_LINEAGE_BREAK"
        if production.get("candidate_id") and str(production.get("candidate_id")) != candidate_id:
            return "CANDIDATE_LINEAGE_BREAK"
        learned = str(candidate_identity.get("learned_object_id") or "")
        if grant.get("learned_object_id") and str(grant.get("learned_object_id")) != learned:
            return "CANDIDATE_LINEAGE_BREAK"
        if production.get("learned_object_id") and str(production.get("learned_object_id")) != learned:
            return "CANDIDATE_LINEAGE_BREAK"
        expected_run = str(run_id or "")
        if expected_run:
            for source in (grant, production):
                if source.get("run_id") and str(source.get("run_id")) != expected_run:
                    return "CANDIDATE_LINEAGE_BREAK"
        if grant.get("candidate_fingerprint") and (
            grant.get("candidate_fingerprint")
            != candidate_identity.get("candidate_fingerprint")
        ):
            return "CANDIDATE_FINGERPRINT_DRIFT"
        return "CANDIDATE_LINEAGE_CONTINUITY_VERIFIED"

    def _highest_level(self, **state: bool) -> str:
        levels = [
            ("E0", state["candidate_generated"]),
            ("E1", state["materialized"]),
            ("E2", state["validation_passed"]),
            ("E3", state["qualified"]),
            ("E4", state["arena_reached"]),
            ("E5", state["safe_winner"]),
            ("E6", state["grant_issued"] and state["budget_admitted"]),
            ("E7", state["executor_called"] and state["real_execution"] and state["outcome_complete"]),
        ]
        highest = "E0_NOT_REACHED"
        for level, reached in levels:
            if reached:
                highest = level
        return highest

    def _first_unreached(self, boundaries: Mapping[str, str]) -> str:
        for boundary, state in boundaries.items():
            if state in {"BLOCKED", "NOT_REACHED", "UNDETERMINED"}:
                return boundary
        return "NONE"

    def _blocking_reason(self, first_block: str, arena_decision: str) -> str:
        if first_block == "ARENA_TIE_REQUIRES_REVIEW":
            return "Arena decision TIE_REQUIRES_REVIEW lawfully prevents grant expectation."
        if first_block == "ARENA_NO_SAFE_WINNER":
            return f"Arena decision {arena_decision} produced no safe winner."
        if first_block == "NATURAL_E7_REACHED":
            return "NONE"
        return first_block

    def _stable_id(self, prefix: str, payload: Any) -> str:
        text = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=True,
            default=str,
            separators=(",", ":"),
        )
        return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


natural_production_handoff_observer = NaturalProductionHandoffObserver()


__all__ = [
    "NaturalProductionHandoffObserver",
    "natural_production_handoff_observer",
]
