"""Governed realized task-yield analytics.

This module is observational only. It reads provenance-bearing evidence and
support records and emits recomputable analytics; it does not grant evidence,
qualification, truth, knowledge, execution, or selector authority.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any


UNKNOWN = {None, "", "UNKNOWN", "NOT_AVAILABLE", "Not Available"}


AUTHORITY_NONE = {
    "analytics": "NONE",
    "evidence": "NONE",
    "qualification": "NONE",
    "truth": "NONE",
    "knowledge": "NONE",
    "planning": "NONE",
    "goal": "NONE",
    "intent": "NONE",
    "budget": "NONE",
    "execution": "NONE",
    "e4": "NONE",
    "selector": "NONE",
}


class RealizedTaskYieldAnalyticsEngine:
    """Compute per-task realized-yield vectors without feedback authority."""

    schema_version = "1.0"
    contract_version = "1.0"
    system_name = "realized_task_yield_analytics_engine"
    authority = "NONE"

    def analyze_task_execution(
        self,
        *,
        task_execution_id: str | None,
        run_id: str | None,
        task_id: str | None,
        raw_evidence: Iterable[Mapping[str, Any]] | None = None,
        accepted_evidence: Iterable[Mapping[str, Any]] | None = None,
        capability_assessments: Iterable[Mapping[str, Any]] | None = None,
        qualification_decisions: Iterable[Mapping[str, Any]] | None = None,
        task_outcome: Mapping[str, Any] | None = None,
        diagnostics: Iterable[Mapping[str, Any]] | None = None,
        predicted_selection: Mapping[str, Any] | None = None,
        measured_at: str | None = None,
    ) -> dict[str, Any]:
        task_execution_id = self._term(task_execution_id)
        run_id = self._term(run_id)
        task_id = self._term(task_id)
        raw_input_rows = self._dedupe(
            [dict(item) for item in raw_evidence or [] if isinstance(item, Mapping)],
            ("raw_result_id", "raw_validation_result_id", "canonical_raw_result_id"),
        )
        accepted_input_rows = self._dedupe(
            [
                dict(item)
                for item in accepted_evidence or []
                if isinstance(item, Mapping)
            ],
            ("accepted_evidence_id",),
        )
        raw_rows = self._dedupe(
            self._task_raw_evidence(raw_input_rows, task_execution_id),
            ("raw_result_id", "raw_validation_result_id", "canonical_raw_result_id"),
        )
        accepted_rows = self._dedupe(
            self._task_accepted_evidence(accepted_input_rows, task_execution_id),
            ("accepted_evidence_id",),
        )
        unattributable_input_evidence_count = (
            len(raw_input_rows)
            + len(accepted_input_rows)
            - len(raw_rows)
            - len(accepted_rows)
        )
        active_rows = [
            item for item in accepted_rows if self._is_current_active(item)
        ]
        noncurrent_rows = [
            item for item in accepted_rows if not self._is_current_active(item)
        ]
        source_ids = self._source_identities(active_rows)
        capability_support = self._capability_support(
            capability_assessments or [],
            task_execution_id,
        )
        qualification_support = self._qualification_support(
            qualification_decisions or [],
            task_execution_id,
        )
        diagnostic = self._diagnostic_value(
            task_outcome or {},
            diagnostics or [],
        )
        redundancy = self._redundancy(
            raw_rows=raw_rows,
            accepted_rows=accepted_rows,
            capability_support=capability_support,
            qualification_support=qualification_support,
            diagnostic=diagnostic,
        )
        causal_count = sum(
            1 for item in active_rows
            if self._upper_first(
                item,
                "capability_causal_support_state",
                "causal_support_state",
                "causal_attribution_state",
            )
            in {
                "CAUSALLY_SUPPORTED",
                "CAUSALLY_DEMONSTRATED",
                "MATERIAL_CONTRIBUTION_DEMONSTRATED",
            }
        )
        reproducibility_count = sum(
            1 for decision in qualification_support["decisions"]
            if self._term(decision.get("reproducibility_state"))
            == "REPRODUCIBLY_SUPPORTED"
        )
        deficit_reduction = self._deficit_reduction(task_outcome or {})
        shared_support_count = sum(
            1 for decision in qualification_support["decisions"]
            if len(self._origin_ids(decision.get("capability_evidence_support_lineage"))) > 1
        )
        current_useful = len(active_rows)
        historical_only = max(len(accepted_rows) - current_useful, 0)
        attribution_confidence = self._attribution_confidence(
            task_execution_id=task_execution_id,
            raw_count=len(raw_rows),
            accepted_rows=accepted_rows,
            capability_support=capability_support,
            qualification_support=qualification_support,
            diagnostic=diagnostic,
            unattributable_input_evidence_count=unattributable_input_evidence_count,
        )
        success_class = self._success_or_failure_class(
            task_outcome or {},
            current_useful=current_useful,
            diagnostic=diagnostic,
            redundancy=redundancy,
        )
        value_vector = {
            "task_execution_id": task_execution_id,
            "run_id": run_id,
            "task_id": task_id,
            "raw_evidence_count": len(raw_rows),
            "accepted_evidence_count": len(accepted_rows),
            "current_active_evidence_count": current_useful,
            "historical_only_evidence_count": historical_only,
            "independent_source_count": len(source_ids),
            "capability_support_count": capability_support["support_count"],
            "qualification_support_count": qualification_support["support_count"],
            "qualification_advanced_count": qualification_support[
                "advanced_count"
            ],
            "qualification_maintained_with_new_support_count": (
                qualification_support["maintained_count"]
            ),
            "qualification_review_count": qualification_support["review_count"],
            "qualification_invalidated_count": qualification_support[
                "invalidated_count"
            ],
            "causal_support_count": causal_count,
            "reproducibility_support_count": reproducibility_count,
            "deficit_reduction_count": deficit_reduction[
                "deficit_reduction_count"
            ],
            "diagnostic_value": diagnostic["diagnostic_value"],
            "diagnostic_value_count": diagnostic["diagnostic_value_count"],
            "redundancy_count": redundancy["redundancy_count"],
            "invalidated_yield_count": self._invalidated_count(accepted_rows),
            "shared_support_count": shared_support_count,
            "unattributable_input_evidence_count": (
                unattributable_input_evidence_count
            ),
            "attribution_confidence": attribution_confidence,
            "measurement_status": (
                "MEASURED"
                if attribution_confidence
                not in {"ATTRIBUTION_UNKNOWN", "TEMPORAL_ASSOCIATION_ONLY"}
                else "PARTIAL_OR_UNKNOWN"
            ),
        }
        yield_class = self._yield_class(value_vector)
        report = {
            "analytics_schema_version": self.schema_version,
            "analytics_contract_version": self.contract_version,
            "system": self.system_name,
            "realized_task_yield_report_id": self._stable_id(
                "realized_task_yield_report",
                {
                    "task_execution_id": task_execution_id,
                    "run_id": run_id,
                    "task_id": task_id,
                    "value_vector": value_vector,
                },
            ),
            "identity": {
                "task_execution_id": task_execution_id,
                "run_id": run_id,
                "task_id": task_id,
            },
            "lineage_refs": {
                "raw_evidence_ids": self._ids(
                    raw_rows,
                    "raw_result_id",
                    "raw_validation_result_id",
                    "canonical_raw_result_id",
                ),
                "accepted_evidence_ids": self._ids(
                    accepted_rows,
                    "accepted_evidence_id",
                ),
                "current_active_accepted_evidence_ids": self._ids(
                    active_rows,
                    "accepted_evidence_id",
                ),
                "capability_assessment_ids": capability_support[
                    "capability_assessment_ids"
                ],
                "qualification_decision_ids": qualification_support[
                    "qualification_decision_ids"
                ],
                "independent_source_ids": source_ids,
            },
            "value_vector": value_vector,
            "yield_class": yield_class,
            "success_failure_value_class": success_class,
            "qualification_advancement_support_class": qualification_support[
                "advancement_support_class"
            ],
            "deficit_reduction_state": deficit_reduction[
                "deficit_reduction_state"
            ],
            "predicted_vs_realized": self.predicted_vs_realized(
                predicted_selection or {},
                value_vector,
            ),
            "limitations": self._limitations(
                raw_rows=raw_rows,
                accepted_rows=accepted_rows,
                deficit_reduction=deficit_reduction,
            ),
            "currentness_reference": {
                "current_active_evidence_count": current_useful,
                "noncurrent_evidence_count": len(noncurrent_rows),
                "measured_at": measured_at
                or datetime.now(timezone.utc).isoformat(),
            },
            "analytics_authority": self.authority,
            "authority": dict(AUTHORITY_NONE),
            "selector_feedback_consumed": False,
            "selector_changed": False,
            "task_data_changed": False,
        }
        report["report_fingerprint"] = self._fingerprint(report)
        return report

    def aggregate_by_task(
        self,
        reports: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for report in reports:
            if not isinstance(report, Mapping):
                continue
            identity = report.get("identity") or {}
            grouped[self._term(identity.get("task_id"))].append(dict(report))
        rows = []
        for task_id, items in sorted(grouped.items()):
            classes = Counter(str(item.get("yield_class")) for item in items)
            rows.append({
                "task_id": task_id,
                "execution_count": len(items),
                "high_yield_count": classes.get("HIGH_REALIZED_YIELD", 0),
                "medium_yield_count": classes.get("MEDIUM_REALIZED_YIELD", 0),
                "low_yield_count": classes.get("LOW_REALIZED_YIELD", 0),
                "zero_yield_count": classes.get("ZERO_REALIZED_YIELD", 0),
                "corrective_yield_count": classes.get("CORRECTIVE_REALIZED_YIELD", 0),
                "unknown_yield_count": classes.get("UNKNOWN_REALIZED_YIELD", 0),
                "current_support_produced": sum(
                    int((item.get("value_vector") or {}).get(
                        "current_active_evidence_count", 0
                    ) or 0)
                    for item in items
                ),
                "diagnostic_value_count": sum(
                    int((item.get("value_vector") or {}).get(
                        "diagnostic_value_count", 0
                    ) or 0)
                    for item in items
                ),
                "redundancy_count": sum(
                    int((item.get("value_vector") or {}).get(
                        "redundancy_count", 0
                    ) or 0)
                    for item in items
                ),
                "authority": "NONE",
            })
        return {
            "analytics_schema_version": self.schema_version,
            "system": "task_longitudinal_realized_yield",
            "task_count": len(rows),
            "tasks": rows,
            "authority": dict(AUTHORITY_NONE),
        }

    def aggregate_by_capability(
        self,
        reports: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        capability_rows: dict[str, dict[str, Any]] = {}
        for report in reports:
            for assessment_id in (
                report.get("lineage_refs", {}).get("capability_assessment_ids")
                or []
            ):
                row = capability_rows.setdefault(str(assessment_id), {
                    "capability_assessment_id": str(assessment_id),
                    "task_execution_ids": set(),
                    "current_support": 0,
                    "qualification_support": 0,
                })
                identity = report.get("identity") or {}
                row["task_execution_ids"].add(identity.get("task_execution_id"))
                vector = report.get("value_vector") or {}
                row["current_support"] += int(
                    vector.get("current_active_evidence_count", 0) or 0
                )
                row["qualification_support"] += int(
                    vector.get("qualification_support_count", 0) or 0
                )
        rows = []
        for row in capability_rows.values():
            rows.append({
                **row,
                "task_execution_ids": sorted(
                    str(item) for item in row["task_execution_ids"] if item
                ),
                "authority": "NONE",
            })
        return {
            "analytics_schema_version": self.schema_version,
            "system": "capability_longitudinal_realized_yield",
            "capability_scope_count": len(rows),
            "capability_scopes": rows,
            "authority": dict(AUTHORITY_NONE),
        }

    def predicted_vs_realized(
        self,
        predicted_selection: Mapping[str, Any],
        value_vector: Mapping[str, Any],
    ) -> dict[str, Any]:
        predicted = dict(predicted_selection or {})
        info_gain = self._number(
            predicted.get("expected_information_gain_bonus")
            or predicted.get("information_gain_bonus")
        )
        novelty = self._number(predicted.get("novelty_bonus"))
        exposure = self._number(
            predicted.get("exposure_penalty")
            or predicted.get("exposure_damping")
        )
        recency = self._number(
            predicted.get("recency_penalty")
            or predicted.get("recency_damping")
        )
        realized_signal = (
            int(value_vector.get("current_active_evidence_count", 0) or 0)
            + int(value_vector.get("qualification_support_count", 0) or 0)
            + int(value_vector.get("diagnostic_value_count", 0) or 0)
        )
        return {
            "predicted_vs_realized_result": (
                "INSUFFICIENT_DATA"
                if info_gain is None
                else "DIRECTIONALLY_ALIGNED"
                if info_gain > 0 and realized_signal > 0
                else "UNALIGNED"
                if info_gain > 0 and realized_signal == 0
                else "PARTIALLY_ALIGNED"
            ),
            "novelty_vs_realized_result": (
                "INSUFFICIENT_DATA"
                if novelty is None
                else "DIRECTIONALLY_ALIGNED"
                if novelty > 0 and realized_signal > 0
                else "UNALIGNED"
                if novelty > 0 and realized_signal == 0
                else "PARTIALLY_ALIGNED"
            ),
            "exposure_vs_realized_result": (
                "INSUFFICIENT_DATA"
                if exposure is None
                else "PARTIALLY_ALIGNED"
                if exposure > 0
                else "INSUFFICIENT_DATA"
            ),
            "recency_vs_realized_result": (
                "INSUFFICIENT_DATA"
                if recency is None
                else "PARTIALLY_ALIGNED"
                if recency > 0
                else "INSUFFICIENT_DATA"
            ),
            "realized_signal_count": realized_signal,
            "selector_feedback_consumed": False,
            "authority": "NONE",
        }

    def feedback_readiness(
        self,
        reports: Iterable[Mapping[str, Any]],
        *,
        natural_observation_count: int = 0,
    ) -> dict[str, Any]:
        items = [dict(item) for item in reports if isinstance(item, Mapping)]
        blockers = []
        if not items:
            blockers.append("NO_REALIZED_YIELD_REPORTS")
        if natural_observation_count <= 0:
            blockers.append("INSUFFICIENT_NATURAL_OBSERVATIONS")
        if any(
            (item.get("value_vector") or {}).get("attribution_confidence")
            in {"ATTRIBUTION_UNKNOWN", "TEMPORAL_ASSOCIATION_ONLY"}
            for item in items
        ):
            blockers.append("ATTRIBUTION_NOT_UNIFORMLY_STRONG")
        state = (
            "READY"
            if not blockers and natural_observation_count >= 20
            else "PARTIALLY_READY"
            if items and not any("ATTRIBUTION" in item for item in blockers)
            else "NOT_READY"
        )
        return {
            "feedback_readiness": state,
            "blockers": blockers,
            "selector_feedback_consumed": False,
            "rich_get_richer_risk": "HIGH",
            "exploration_starvation_risk": "HIGH_WITHOUT_UNKNOWN_YIELD_PROTECTION",
            "negative_evidence_gaming_risk": "MEDIUM",
            "qualification_gaming_risk": "MEDIUM",
            "currentness_gaming_risk": "CONTROLLED_BY_LIFECYCLE_AWARE_CURRENT_YIELD",
            "authority": dict(AUTHORITY_NONE),
        }

    def _task_raw_evidence(
        self,
        evidence: Iterable[Mapping[str, Any]],
        task_execution_id: str,
    ) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in evidence
            if isinstance(item, Mapping)
            and self._term(item.get("origin_task_execution_id"))
            == task_execution_id
        ]

    def _task_accepted_evidence(
        self,
        evidence: Iterable[Mapping[str, Any]],
        task_execution_id: str,
    ) -> list[dict[str, Any]]:
        rows = []
        for item in evidence:
            if not isinstance(item, Mapping):
                continue
            origin = item.get("accepted_evidence_origin")
            origin = dict(origin) if isinstance(origin, Mapping) else {}
            observed = (
                origin.get("origin_task_execution_id")
                or item.get("origin_task_execution_id")
            )
            if self._term(observed) == task_execution_id:
                rows.append(dict(item))
        return rows

    def _capability_support(
        self,
        assessments: Iterable[Mapping[str, Any]],
        task_execution_id: str,
    ) -> dict[str, Any]:
        matched = []
        assessment_ids = []
        for assessment in assessments:
            if not isinstance(assessment, Mapping):
                continue
            refs = assessment.get("supporting_accepted_evidence_refs") or []
            task_refs = [
                dict(ref) for ref in refs
                if isinstance(ref, Mapping)
                and self._term(ref.get("origin_task_execution_id"))
                == task_execution_id
            ]
            if task_refs:
                matched.extend(task_refs)
                assessment_ids.append(
                    self._term(assessment.get("capability_evidence_assessment_id"))
                )
        return {
            "support_count": len(self._dedupe(matched, ("accepted_evidence_id",))),
            "support_refs": matched,
            "capability_assessment_ids": sorted(set(assessment_ids)),
        }

    def _qualification_support(
        self,
        decisions: Iterable[Mapping[str, Any]],
        task_execution_id: str,
    ) -> dict[str, Any]:
        matched = []
        decision_ids = []
        advanced = maintained = review = invalidated = 0
        advancement_class = "ADVANCEMENT_WITHOUT_TASK_SUPPORT"
        for decision in decisions:
            if not isinstance(decision, Mapping):
                continue
            refs = decision.get("capability_evidence_support_lineage") or []
            task_refs = [
                dict(ref) for ref in refs
                if isinstance(ref, Mapping)
                and self._term(ref.get("origin_task_execution_id"))
                == task_execution_id
            ]
            if task_refs:
                matched.extend(task_refs)
                decision_ids.append(self._decision_id(decision))
                state = self._term(decision.get("decision_state"))
                current = self._term(decision.get("current_level"))
                granted = self._term(decision.get("granted_level"))
                if state == "PROMOTION_GRANTED" and current != granted:
                    advanced += 1
                    advancement_class = (
                        "SHARED_TASK_SUPPORT_IN_ADVANCEMENT"
                        if len(self._origin_ids(refs)) > 1
                        else "TASK_SUPPORT_PRESENT_IN_ADVANCEMENT"
                    )
                elif state == "PROMOTION_GRANTED":
                    maintained += 1
                if "REVIEW" in state:
                    review += 1
                if "INVALIDATED" in state:
                    invalidated += 1
        return {
            "support_count": len(self._dedupe(matched, ("accepted_evidence_id",))),
            "support_refs": matched,
            "qualification_decision_ids": sorted(set(decision_ids)),
            "decisions": [dict(item) for item in decisions if isinstance(item, Mapping)],
            "advanced_count": advanced,
            "maintained_count": maintained,
            "review_count": review,
            "invalidated_count": invalidated,
            "advancement_support_class": advancement_class
            if matched else "ATTRIBUTION_UNRESOLVED",
        }

    def _diagnostic_value(
        self,
        task_outcome: Mapping[str, Any],
        diagnostics: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        markers = []
        for row in diagnostics:
            if not isinstance(row, Mapping):
                continue
            marker = self._upper_first(
                row,
                "diagnostic_class",
                "failure_value_class",
                "diagnostic_value",
            )
            if marker in {
                "NEW_FAILURE_CLASS",
                "NEW_RESIDUAL_PATTERN",
                "NEW_UNSUPPORTED_CAPABILITY_SIGNAL",
                "NEW_REPAIR_TARGET",
                "NEW_NEGATIVE_EVIDENCE",
                "NEW_CONTRADICTION",
                "CORRECTIVE_EPISTEMIC_VALUE",
            }:
                markers.append(marker)
        outcome_marker = self._upper_first(
            task_outcome,
            "diagnostic_class",
            "failure_value_class",
        )
        if outcome_marker:
            markers.append(outcome_marker)
        markers = sorted(set(markers))
        return {
            "diagnostic_value": (
                "CORRECTIVE_EPISTEMIC_VALUE"
                if "CORRECTIVE_EPISTEMIC_VALUE" in markers
                else "NEW_DIAGNOSTIC_VALUE"
                if markers
                else "NO_NEW_DIAGNOSTIC_INFORMATION"
            ),
            "diagnostic_value_count": len(markers),
            "diagnostic_markers": markers,
        }

    def _redundancy(
        self,
        *,
        raw_rows: list[dict[str, Any]],
        accepted_rows: list[dict[str, Any]],
        capability_support: Mapping[str, Any],
        qualification_support: Mapping[str, Any],
        diagnostic: Mapping[str, Any],
    ) -> dict[str, Any]:
        duplicate_sources = len(accepted_rows) - len(self._source_identities(accepted_rows))
        redundant = 0
        if raw_rows and not accepted_rows and not diagnostic.get("diagnostic_value_count"):
            redundant += 1
        if accepted_rows and not capability_support.get("support_count") and (
            not qualification_support.get("support_count")
        ):
            redundant += 1
        if duplicate_sources > 0:
            redundant += duplicate_sources
        return {
            "redundancy_count": max(redundant, 0),
            "duplicate_source_count": max(duplicate_sources, 0),
            "redundancy_model": (
                "NO_CURRENT_SUPPORT_OR_DUPLICATE_SOURCE_INDICATES_REDUNDANCY"
            ),
        }

    def _success_or_failure_class(
        self,
        outcome: Mapping[str, Any],
        *,
        current_useful: int,
        diagnostic: Mapping[str, Any],
        redundancy: Mapping[str, Any],
    ) -> str:
        success = bool(
            outcome.get("success")
            or self._term(outcome.get("execution_status")) in {"SUCCESS", "PASSED"}
        )
        if success and current_useful:
            return "SUCCESS_WITH_NEW_CURRENT_SUPPORT"
        if success and diagnostic.get("diagnostic_value_count"):
            return "SUCCESS_WITH_DIAGNOSTIC_VALUE"
        if success and redundancy.get("redundancy_count"):
            return "SUCCESS_REDUNDANT"
        if success:
            return "SUCCESS_YIELD_UNKNOWN"
        if diagnostic.get("diagnostic_value") == "CORRECTIVE_EPISTEMIC_VALUE":
            return "FAILURE_WITH_CORRECTIVE_VALUE"
        if diagnostic.get("diagnostic_value_count"):
            return "FAILURE_WITH_NEW_DIAGNOSTIC_VALUE"
        if current_useful:
            return "FAILURE_WITH_NEW_EVIDENCE"
        if redundancy.get("redundancy_count"):
            return "FAILURE_REDUNDANT"
        return "FAILURE_YIELD_UNKNOWN"

    def _yield_class(self, vector: Mapping[str, Any]) -> str:
        if (
            vector.get("unattributable_input_evidence_count")
            and vector.get("attribution_confidence") in {
            "ATTRIBUTION_UNKNOWN",
            "TEMPORAL_ASSOCIATION_ONLY",
            }
        ):
            return "UNKNOWN_REALIZED_YIELD"
        if vector.get("qualification_invalidated_count") or (
            vector.get("diagnostic_value") == "CORRECTIVE_EPISTEMIC_VALUE"
        ):
            return "CORRECTIVE_REALIZED_YIELD"
        if vector.get("qualification_support_count") and vector.get(
            "current_active_evidence_count"
        ):
            return "HIGH_REALIZED_YIELD"
        if vector.get("current_active_evidence_count") or vector.get(
            "capability_support_count"
        ):
            return "MEDIUM_REALIZED_YIELD"
        if vector.get("accepted_evidence_count") or vector.get(
            "diagnostic_value_count"
        ):
            return "LOW_REALIZED_YIELD"
        if vector.get("raw_evidence_count"):
            return "LOW_REALIZED_YIELD"
        return "ZERO_REALIZED_YIELD"

    def _attribution_confidence(
        self,
        *,
        task_execution_id: str,
        raw_count: int,
        accepted_rows: list[dict[str, Any]],
        capability_support: Mapping[str, Any],
        qualification_support: Mapping[str, Any],
        diagnostic: Mapping[str, Any],
        unattributable_input_evidence_count: int,
    ) -> str:
        if unattributable_input_evidence_count and not (
            raw_count or accepted_rows or capability_support.get("support_count")
        ):
            return "ATTRIBUTION_UNKNOWN"
        if task_execution_id in UNKNOWN:
            return "ATTRIBUTION_UNKNOWN"
        if qualification_support.get("support_count") and accepted_rows:
            return (
                "SHARED_SUPPORT_LINEAGE"
                if any(
                    self._term(item.get("accepted_evidence_origin_state"))
                    == "SHARED_MULTI_TASK_SUPPORT"
                    for item in accepted_rows
                )
                else "STRONG_SUPPORT_LINEAGE"
            )
        if capability_support.get("support_count") and accepted_rows:
            return "STRONG_SUPPORT_LINEAGE"
        if accepted_rows or raw_count:
            return "DIRECT_PROVENANCE"
        if diagnostic.get("diagnostic_value_count"):
            return "DIRECT_PROVENANCE"
        return "ATTRIBUTION_UNKNOWN"

    def _deficit_reduction(self, outcome: Mapping[str, Any]) -> dict[str, Any]:
        pre = self._number(outcome.get("pre_deficit_count"))
        post = self._number(outcome.get("post_deficit_count"))
        if pre is None or post is None:
            return {
                "deficit_reduction_state": "DEFICIT_REDUCTION_NOT_MEASURABLE",
                "deficit_reduction_count": 0,
            }
        return {
            "deficit_reduction_state": (
                "DEFICIT_REDUCED" if post < pre else "DEFICIT_NOT_REDUCED"
            ),
            "deficit_reduction_count": int(max(pre - post, 0)),
        }

    def _limitations(
        self,
        *,
        raw_rows: list[dict[str, Any]],
        accepted_rows: list[dict[str, Any]],
        deficit_reduction: Mapping[str, Any],
    ) -> list[str]:
        limitations = ["ANALYTICS_NOT_AUTHORITY", "NO_SELECTOR_FEEDBACK"]
        if not raw_rows and not accepted_rows:
            limitations.append("NO_DIRECT_TASK_EVIDENCE_OBSERVED")
        if deficit_reduction.get("deficit_reduction_state") == (
            "DEFICIT_REDUCTION_NOT_MEASURABLE"
        ):
            limitations.append("DEFICIT_REDUCTION_NOT_MEASURABLE")
        return limitations

    def _is_current_active(self, evidence: Mapping[str, Any]) -> bool:
        state = evidence.get("accepted_evidence_current_state")
        if isinstance(state, Mapping):
            return (
                state.get("current_status") == "ACTIVE"
                and state.get("is_currently_accepted") is True
                and not state.get("superseded_by")
            )
        status = (
            evidence.get("current_status")
            or evidence.get("accepted_evidence_current_status")
        )
        if status not in UNKNOWN:
            return status == "ACTIVE"
        return evidence.get("evidence_acceptance_state") == "ACCEPTED"

    def _invalidated_count(self, evidence: Iterable[Mapping[str, Any]]) -> int:
        states = {"REVOKED", "INVALIDATED", "SUPERSEDED", "REVALIDATION_REQUIRED"}
        count = 0
        for item in evidence:
            state = item.get("accepted_evidence_current_state")
            status = (
                state.get("current_status") if isinstance(state, Mapping)
                else item.get("current_status")
            )
            if status in states:
                count += 1
        return count

    def _source_identities(self, rows: Iterable[Mapping[str, Any]]) -> list[str]:
        ids = set()
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            source = (
                row.get("canonical_source_identity")
                or row.get("canonical_source_id")
                or row.get("source_identity_id")
                or row.get("producer_operation_id")
            )
            if source not in UNKNOWN:
                ids.add(str(source))
        return sorted(ids)

    def _origin_ids(self, refs: Any) -> set[str]:
        return {
            str(row.get("origin_task_execution_id"))
            for row in refs or []
            if isinstance(row, Mapping)
            and row.get("origin_task_execution_id") not in UNKNOWN
        }

    def _decision_id(self, decision: Mapping[str, Any]) -> str:
        for key in (
            "qualification_decision_id",
            "review_decision_id",
            "invalidation_decision_id",
            "revalidation_decision_id",
        ):
            value = decision.get(key)
            if value not in UNKNOWN:
                return str(value)
        return "UNKNOWN"

    def _ids(self, rows: Iterable[Mapping[str, Any]], *keys: str) -> list[str]:
        ids = set()
        for row in rows:
            for key in keys:
                value = row.get(key)
                if value not in UNKNOWN:
                    ids.add(str(value))
                    break
        return sorted(ids)

    def _dedupe(
        self,
        rows: Iterable[Mapping[str, Any]],
        keys: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        observed = set()
        deduped = []
        for row in rows:
            item = dict(row)
            identity = next(
                (str(item.get(key)) for key in keys if item.get(key) not in UNKNOWN),
                self._fingerprint(item),
            )
            if identity in observed:
                continue
            observed.add(identity)
            deduped.append(item)
        return deduped

    def _upper_first(self, item: Mapping[str, Any], *keys: str) -> str:
        for key in keys:
            value = item.get(key)
            if value not in UNKNOWN:
                return str(value).strip().upper()
        return ""

    def _term(self, value: Any) -> str:
        text = str(value or "").strip()
        return text if text else "Not Available"

    def _number(self, value: Any) -> float | None:
        try:
            if value in UNKNOWN:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _stable_id(self, prefix: str, payload: Any) -> str:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        return f"{prefix}_{hashlib.sha1(encoded.encode('utf-8')).hexdigest()[:12]}"

    def _fingerprint(self, payload: Any) -> str:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


realized_task_yield_analytics_engine = RealizedTaskYieldAnalyticsEngine()


__all__ = [
    "AUTHORITY_NONE",
    "RealizedTaskYieldAnalyticsEngine",
    "realized_task_yield_analytics_engine",
]
