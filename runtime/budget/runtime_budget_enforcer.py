"""Authoritative runtime budget enforcement for routes and reasoning depth."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Mapping


class RuntimeBudgetEnforcer:
    """Build immutable budget receipts from canonical runtime lifecycle records."""

    system_name = "runtime_budget_enforcer"
    schema_version = "1.0"

    TERMINAL_ROUTE_STATES = {
        "COMPLETED_ROUTE",
        "RELEASED_ROUTE",
        "FAILED_ROUTE",
        "CANCELLED_ROUTE",
        "TIMED_OUT_ROUTE",
        "REJECTED_BY_BUDGET",
        "DEFERRED_BY_BUDGET",
        "BLOCKED_ROUTE",
    }

    ACTIVE_ROUTE_STATES = {
        "ACTIVE_ROUTE",
        "ROUTE_ACTIVATION_STARTED",
        "EXECUTING",
        "ACTIVE",
    }

    def build_receipt(
        self,
        *,
        budget: Mapping[str, Any] | None,
        context: Mapping[str, Any] | None,
        execution_plan_id: str | None,
        route_records: list[dict[str, Any]] | None = None,
        nodes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        context = context if isinstance(context, Mapping) else {}
        route_records = list(route_records or [])
        nodes = list(nodes or [])
        run_id = self._identity(
            context.get("run_id")
            or context.get("execution_id")
            or context.get("runtime_id")
            or "current_run"
        )
        task_id = self._identity(context.get("task_id") or context.get("task") or "current_task")

        if not isinstance(budget, Mapping) or not budget:
            return self._finalize({
                "runtime_budget_schema_version": self.schema_version,
                "runtime_budget_state": "RUNTIME_BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE",
                "route_budget_enforcement_state": "RUNTIME_BUDGET_SNAPSHOT_MISSING",
                "depth_enforcement_state": "RUNTIME_BUDGET_SNAPSHOT_MISSING",
                "run_id": run_id,
                "task_id": task_id,
                "execution_plan_id": execution_plan_id,
                "violation_reason": "RUNTIME_BUDGET_SNAPSHOT_MISSING",
            })

        snapshot = dict(budget)
        snapshot_id = self._budget_snapshot_id(snapshot)
        budget_run_id = snapshot.get("run_id") or snapshot.get("execution_id")
        budget_task_id = snapshot.get("task_id") or snapshot.get("task")
        if budget_run_id is not None and self._identity(budget_run_id) != run_id:
            return self._identity_failure(
                snapshot,
                snapshot_id,
                run_id,
                task_id,
                execution_plan_id,
                "ROUTE_BUDGET_CROSS_RUN_CONTAMINATION",
            )
        if budget_task_id is not None and self._identity(budget_task_id) != task_id:
            return self._identity_failure(
                snapshot,
                snapshot_id,
                run_id,
                task_id,
                execution_plan_id,
                "ROUTE_BUDGET_CROSS_TASK_CONTAMINATION",
            )
        if snapshot.get("budget_state") in {"STALE", "EXPIRED"} or snapshot.get("stale") is True:
            return self._identity_failure(
                snapshot,
                snapshot_id,
                run_id,
                task_id,
                execution_plan_id,
                "BUDGET_SNAPSHOT_STALE",
            )
        if snapshot.get("authority_conflict") is True:
            return self._identity_failure(
                snapshot,
                snapshot_id,
                run_id,
                task_id,
                execution_plan_id,
                "RUNTIME_BUDGET_AUTHORITY_CONFLICT",
            )

        route_limit = self._int_or_none(snapshot.get("max_active_routes"))
        depth_limit = self._int_or_none(snapshot.get("max_reasoning_depth"))
        route_scope = str(snapshot.get("active_route_limit_scope") or "TASK_CONCURRENT_ACTIVE_ROUTES")
        depth_scope = str(snapshot.get("reasoning_depth_limit_scope") or "TASK_GOVERNED_REASONING_DEPTH")

        lifecycle = self._route_lifecycle_records(context, run_id, task_id)
        if lifecycle.get("state"):
            return self._identity_failure(
                snapshot,
                snapshot_id,
                run_id,
                task_id,
                execution_plan_id,
                lifecycle["state"],
            )

        admitted_routes = self._admitted_route_ids(route_records, nodes, route_limit)
        route_dispositions = self._route_dispositions(route_records, admitted_routes)
        route_counts = self._route_counts(
            context,
            route_records,
            route_dispositions,
            lifecycle["records"],
        )
        depth_counts = self._depth_counts(context, run_id, task_id, depth_limit)
        if depth_counts.get("state"):
            return self._identity_failure(
                snapshot,
                snapshot_id,
                run_id,
                task_id,
                execution_plan_id,
                depth_counts["state"],
            )

        route_state = "ROUTE_BUDGET_NOT_APPLICABLE"
        route_violations = 0
        if route_limit is not None:
            route_state = "ROUTE_BUDGET_ADMITTED"
            if route_counts["peak_concurrent_active_route_count"] > route_limit:
                route_state = "ROUTE_BUDGET_EXCEEDED"
                route_violations = route_counts["peak_concurrent_active_route_count"] - route_limit
            elif route_counts["selected_route_count"] > len(admitted_routes):
                route_state = "ROUTE_BUDGET_LIMIT_REACHED"

        depth_state = "REASONING_DEPTH_NOT_APPLICABLE"
        depth_violations = 0
        if depth_limit is not None:
            depth_state = "REASONING_DEPTH_AUTHORIZED"
            if depth_counts["maximum_entered_reasoning_depth"] > depth_limit:
                depth_state = "REASONING_DEPTH_EXCEEDED"
                depth_violations = depth_counts["maximum_entered_reasoning_depth"] - depth_limit
            elif depth_counts["planned_reasoning_depth"] > depth_limit:
                depth_state = "REASONING_DEPTH_LIMIT_REACHED"

        state = "RUNTIME_BUDGET_FINALIZED"
        if route_state in {"ROUTE_BUDGET_EXCEEDED"} or depth_state == "REASONING_DEPTH_EXCEEDED":
            state = "RUNTIME_BUDGET_INTEGRITY_FAILED"

        return self._finalize({
            "runtime_budget_schema_version": self.schema_version,
            "runtime_budget_snapshot_id": snapshot_id,
            "runtime_budget_source": snapshot.get("budget_source") or "current_reasoning_budget",
            "runtime_budget_scope": route_scope,
            "runtime_budget_state": state,
            "runtime_budget_finalized": True,
            "runtime_budget_immutable": True,
            "run_id": run_id,
            "batch_id": context.get("batch_id"),
            "task_id": task_id,
            "execution_plan_id": execution_plan_id,
            "maximum_active_routes": route_limit,
            "active_route_limit_scope": route_scope,
            "available_route_count": route_counts["available_route_count"],
            "candidate_route_count": route_counts["candidate_route_count"],
            "selected_route_count": route_counts["selected_route_count"],
            "admitted_route_count": len(admitted_routes),
            "deferred_by_budget_route_count": route_counts["deferred_by_budget_route_count"],
            "rejected_by_budget_route_count": route_counts["rejected_by_budget_route_count"],
            "total_route_activation_count": route_counts["total_route_activation_count"],
            "current_active_route_count": route_counts["current_active_route_count"],
            "peak_concurrent_active_route_count": route_counts["peak_concurrent_active_route_count"],
            "completed_route_count": route_counts["completed_route_count"],
            "released_route_count": route_counts["released_route_count"],
            "route_budget_enforcement_state": route_state,
            "route_budget_violation_count": route_violations,
            "route_dispositions": route_dispositions,
            "maximum_reasoning_depth": depth_limit,
            "reasoning_depth_limit_scope": depth_scope,
            "configured_reasoning_depth": depth_counts["configured_reasoning_depth"],
            "planned_reasoning_depth": depth_counts["planned_reasoning_depth"],
            "attempted_reasoning_depth": depth_counts["attempted_reasoning_depth"],
            "current_reasoning_depth": depth_counts["current_reasoning_depth"],
            "maximum_entered_reasoning_depth": depth_counts["maximum_entered_reasoning_depth"],
            "maximum_completed_reasoning_depth": depth_counts["maximum_completed_reasoning_depth"],
            "available_graph_depth": depth_counts["available_graph_depth"],
            "dependency_execution_depth": depth_counts["dependency_execution_depth"],
            "depth_enforcement_state": depth_state,
            "depth_violation_count": depth_violations,
            "violation_reason": (
                "NONE"
                if route_violations == 0 and depth_violations == 0
                else "AUTHORITATIVE_RUNTIME_BUDGET_EXCEEDED"
            ),
        })

    def verify_receipt(self, receipt: Mapping[str, Any] | None) -> bool:
        if not isinstance(receipt, Mapping):
            return False
        fingerprint = receipt.get("runtime_budget_receipt_fingerprint")
        if not fingerprint:
            return False
        payload = dict(receipt)
        payload.pop("runtime_budget_receipt_fingerprint", None)
        return fingerprint == self._stable_id("runtime_budget_receipt", payload)

    def _route_lifecycle_records(
        self,
        context: Mapping[str, Any],
        run_id: str,
        task_id: str,
    ) -> dict[str, Any]:
        records = context.get("route_lifecycle_records") or []
        records = records if isinstance(records, list) else []
        seen = set()
        clean = []
        for index, row in enumerate(records):
            if not isinstance(row, Mapping):
                continue
            if row.get("run_id") is not None and self._identity(row.get("run_id")) != run_id:
                return {"state": "ROUTE_BUDGET_CROSS_RUN_CONTAMINATION", "records": []}
            if row.get("task_id") is not None and self._identity(row.get("task_id")) != task_id:
                return {"state": "ROUTE_BUDGET_CROSS_TASK_CONTAMINATION", "records": []}
            route_id = self._identity(row.get("route_id") or row.get("id") or f"route_lifecycle_{index}")
            event_id = self._identity(row.get("event_id") or row.get("lifecycle_event_id") or f"{route_id}:{row.get('state')}")
            key = (route_id, event_id)
            if key in seen:
                return {"state": "ROUTE_LIFECYCLE_IDENTITY_CONFLICT", "records": []}
            seen.add(key)
            clean.append({**dict(row), "route_id": route_id})
        return {"state": None, "records": clean}

    def _depth_counts(
        self,
        context: Mapping[str, Any],
        run_id: str,
        task_id: str,
        depth_limit: int | None,
    ) -> dict[str, Any]:
        records = context.get("reasoning_depth_lifecycle_records") or []
        records = records if isinstance(records, list) else []
        current = 0
        entered = []
        completed = []
        attempted = []
        for row in records:
            if not isinstance(row, Mapping):
                continue
            if row.get("run_id") is not None and self._identity(row.get("run_id")) != run_id:
                return {"state": "REASONING_DEPTH_IDENTITY_CONFLICT"}
            if row.get("task_id") is not None and self._identity(row.get("task_id")) != task_id:
                return {"state": "REASONING_DEPTH_IDENTITY_CONFLICT"}
            depth = self._int_or_none(row.get("depth"))
            if depth is None:
                continue
            state = str(row.get("state") or row.get("event") or "")
            if state in {"ATTEMPTED_REASONING_DEPTH", "ATTEMPTED"}:
                attempted.append(depth)
            if state in {"REASONING_DEPTH_ENTRY_AUTHORIZED", "ENTERED", "MAXIMUM_ENTERED_REASONING_DEPTH"}:
                entered.append(depth)
                current = max(current, depth)
            if state in {"REASONING_DEPTH_EXITED", "COMPLETED", "MAXIMUM_COMPLETED_REASONING_DEPTH"}:
                completed.append(depth)
                current = max(0, min(current, depth - 1))
        planned = self._int_or_none(context.get("planned_reasoning_depth"))
        if planned is None:
            introspection = context.get("introspection_report")
            if isinstance(introspection, Mapping):
                planned = self._int_or_none(introspection.get("reasoning_depth"))
        return {
            "state": None,
            "configured_reasoning_depth": depth_limit,
            "planned_reasoning_depth": planned or 0,
            "attempted_reasoning_depth": max(attempted or entered or [0]),
            "current_reasoning_depth": current if records else 0,
            "maximum_entered_reasoning_depth": max(entered or [0]),
            "maximum_completed_reasoning_depth": max(completed or [0]),
            "available_graph_depth": self._int_or_none(context.get("available_graph_depth")) or 0,
            "dependency_execution_depth": self._int_or_none(context.get("dependency_execution_depth")) or 0,
        }

    def _admitted_route_ids(
        self,
        route_records: list[dict[str, Any]],
        nodes: list[dict[str, Any]],
        route_limit: int | None,
    ) -> list[str]:
        materialized_slots = sum(
            1 for node in nodes if node.get("materialization_state") == "MATERIALIZED"
        )
        limit = materialized_slots
        if route_limit is not None:
            limit = min(limit, max(route_limit, 0))
        ordered = sorted(
            route_records,
            key=lambda row: (
                self._int_or_none(row.get("route_rank")) or 10**9,
                str(row.get("route_id") or ""),
            ),
        )
        return [str(row.get("route_id")) for row in ordered[:limit]]

    def _route_dispositions(
        self,
        route_records: list[dict[str, Any]],
        admitted_route_ids: list[str],
    ) -> list[dict[str, Any]]:
        admitted = set(admitted_route_ids)
        rows = []
        for row in sorted(
            route_records,
            key=lambda item: (
                self._int_or_none(item.get("route_rank")) or 10**9,
                str(item.get("route_id") or ""),
            ),
        ):
            route_id = str(row.get("route_id"))
            state = "ROUTE_BUDGET_ADMITTED" if route_id in admitted else "DEFERRED_BY_BUDGET"
            rows.append({
                "route_id": route_id,
                "route_rank": row.get("route_rank"),
                "route_score": row.get("route_score"),
                "budget_disposition": state,
            })
        return rows

    def _route_counts(
        self,
        context: Mapping[str, Any],
        route_records: list[dict[str, Any]],
        dispositions: list[dict[str, Any]],
        lifecycle: list[dict[str, Any]],
    ) -> dict[str, Any]:
        route_report = context.get("route_selection_report") or context.get("cognitive_route_report") or {}
        available = self._list_count(route_report, "available_routes")
        candidates = self._list_count(route_report, "candidate_routes")
        selected = len({row.get("route_id") for row in route_records})
        deferred = sum(1 for row in dispositions if row.get("budget_disposition") == "DEFERRED_BY_BUDGET")
        rejected = sum(1 for row in dispositions if row.get("budget_disposition") == "REJECTED_BY_BUDGET")
        active = set()
        peak = 0
        activations = 0
        completed = set()
        released = set()
        for row in lifecycle:
            route_id = row["route_id"]
            state = str(row.get("state") or row.get("lifecycle_state") or "")
            if state in self.ACTIVE_ROUTE_STATES:
                activations += 1
                active.add(route_id)
                peak = max(peak, len(active))
            if state in {"COMPLETED_ROUTE", "COMPLETED"}:
                completed.add(route_id)
                active.discard(route_id)
            if state in self.TERMINAL_ROUTE_STATES or state in {"RELEASED", "FAILED", "CANCELLED", "TIMEOUT"}:
                if state in {"RELEASED_ROUTE", "RELEASED"}:
                    released.add(route_id)
                active.discard(route_id)
        return {
            "available_route_count": available if available is not None else selected,
            "candidate_route_count": candidates if candidates is not None else selected,
            "selected_route_count": selected,
            "deferred_by_budget_route_count": deferred,
            "rejected_by_budget_route_count": rejected,
            "total_route_activation_count": activations,
            "current_active_route_count": len(active),
            "peak_concurrent_active_route_count": peak,
            "completed_route_count": len(completed),
            "released_route_count": len(released),
        }

    def _identity_failure(
        self,
        snapshot: Mapping[str, Any],
        snapshot_id: str,
        run_id: str,
        task_id: str,
        execution_plan_id: str | None,
        state: str,
    ) -> dict[str, Any]:
        return self._finalize({
            "runtime_budget_schema_version": self.schema_version,
            "runtime_budget_snapshot_id": snapshot_id,
            "runtime_budget_source": snapshot.get("budget_source") or "current_reasoning_budget",
            "runtime_budget_scope": snapshot.get("active_route_limit_scope") or "TASK_CONCURRENT_ACTIVE_ROUTES",
            "runtime_budget_state": state,
            "runtime_budget_finalized": True,
            "runtime_budget_immutable": True,
            "run_id": run_id,
            "task_id": task_id,
            "execution_plan_id": execution_plan_id,
            "route_budget_enforcement_state": state,
            "depth_enforcement_state": state,
            "violation_reason": state,
        })

    def _finalize(self, receipt: dict[str, Any]) -> dict[str, Any]:
        finalized = deepcopy(receipt)
        finalized.setdefault("runtime_budget_finalized", True)
        finalized.setdefault("runtime_budget_immutable", True)
        finalized["runtime_budget_receipt_id"] = self._stable_id(
            "runtime_budget_receipt_id",
            {
                "snapshot": finalized.get("runtime_budget_snapshot_id"),
                "run": finalized.get("run_id"),
                "task": finalized.get("task_id"),
                "plan": finalized.get("execution_plan_id"),
            },
        )
        finalized["runtime_budget_receipt_fingerprint"] = self._stable_id(
            "runtime_budget_receipt",
            finalized,
        )
        return finalized

    def _budget_snapshot_id(self, budget: Mapping[str, Any]) -> str:
        return str(
            budget.get("budget_snapshot_id")
            or budget.get("budget_id")
            or self._stable_id("runtime_budget_snapshot", dict(budget))
        )

    def _stable_id(self, prefix: str, payload: Any) -> str:
        text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"

    def _identity(self, value: Any) -> str:
        text = str(value or "").strip()
        return text or "unidentified"

    def _int_or_none(self, value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _list_count(self, report: Any, key: str) -> int | None:
        if isinstance(report, Mapping) and isinstance(report.get(key), list):
            return len(report[key])
        return None


runtime_budget_enforcer = RuntimeBudgetEnforcer()


__all__ = ["RuntimeBudgetEnforcer", "runtime_budget_enforcer"]
