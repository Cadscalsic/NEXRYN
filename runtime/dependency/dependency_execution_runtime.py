"""Plan-authorized dependency execution receipt runtime.

This module does not implement dependency reasoning. It consumes the finalized
canonical execution plan, validates the dependency activation request, prepares
one minimal chain from existing dependency links, invokes the existing
DependencyExecutionBridge once, and captures a serializable receipt.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Mapping

from runtime.dependency.dependency_chain_builder import (
    EXECUTABLE_DEPENDENCY_TYPES,
    DependencyChainBuilder,
)
from runtime.dependency.dependency_execution_bridge import DependencyExecutionBridge


class DependencyExecutionRuntime:
    """Execute exactly one admitted dependency request from a canonical plan."""

    system_name = "dependency_execution_runtime"
    schema_version = "1.0"

    def __init__(
        self,
        execution_bridge: DependencyExecutionBridge | None = None,
        chain_builder: DependencyChainBuilder | None = None,
        component_registry: Mapping[str, Any] | None = None,
    ) -> None:
        self.execution_bridge = execution_bridge or DependencyExecutionBridge()
        self.chain_builder = chain_builder or DependencyChainBuilder()
        self.component_registry = dict(component_registry or {})
        self.component_registry.setdefault("dependency_execution", self.execution_bridge)
        self.component_registry.setdefault(
            "dependency_reasoning_runtime",
            self.execution_bridge,
        )
        self._receipts: dict[str, dict[str, Any]] = {}

    def execute(
        self,
        *,
        canonical_plan: Mapping[str, Any] | None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        plan = canonical_plan if isinstance(canonical_plan, Mapping) else {}
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        run_id = self._identity(plan.get("run_id") or context.get("run_id") or "current_run")
        task_id = self._identity(plan.get("task_id") or context.get("task_id") or "current_task")
        request = self._dependency_activation_request(plan)
        node = self._dependency_node(plan, request)
        invocation_id = self._invocation_id(plan, node, request)
        execution_id = self._stable_id(
            "dependency_execution",
            {
                "run_id": run_id,
                "task_id": task_id,
                "execution_plan_id": plan.get("execution_plan_id"),
                "execution_node_id": node.get("execution_node_id") if node else None,
                "activation_request_id": request.get("activation_request_id") if request else None,
                "invocation_id": invocation_id,
            },
        )
        if invocation_id in self._receipts:
            return deepcopy(self._receipts[invocation_id])

        base = self._base_receipt(
            dependency_execution_id=execution_id,
            run_id=run_id,
            task_id=task_id,
            plan=plan,
            node=node,
            request=request,
            invocation_id=invocation_id,
        )
        validation_failure = self._request_failure(plan, node, request, context)
        if validation_failure:
            return self._finalize({
                **base,
                "execution_state": validation_failure["execution_state"],
                "request_consumption_state": validation_failure["request_consumption_state"],
                "non_execution_reason": validation_failure["reason"],
                "failure_records": [validation_failure],
            })

        target_component_id = str(node.get("target_runtime_component") or "")
        executor = self.component_registry.get(target_component_id)
        if executor is None:
            return self._finalize({
                **base,
                "execution_state": "BLOCKED",
                "request_consumption_state": "REQUEST_TARGET_UNRESOLVED",
                "target_component_id": target_component_id,
                "non_execution_reason": "DEPENDENCY_RUNTIME_COMPONENT_UNRESOLVED",
                "failure_records": [{
                    "failure_code": "DEPENDENCY_RUNTIME_COMPONENT_UNRESOLVED",
                    "target_component_id": target_component_id,
                }],
            })

        link_source = self._link_source(context)
        links = link_source["links"]
        eligibility_records = self._eligibility_records(
            links,
            run_id=run_id,
            task_id=task_id,
        )
        eligible = [
            record for record in eligibility_records
            if record["eligibility_state"] == "ELIGIBLE"
        ]
        base.update({
            "target_component_id": target_component_id,
            "input_link_count": len(links),
            "eligible_link_count": len(eligible),
            "link_eligibility": eligibility_records,
            "link_source": link_source["source"],
        })
        if not links:
            reason = (
                "NO_DEPENDENCY_LINK_RECORDS"
                if link_source["present"]
                else "DEPENDENCY_INPUT_UNAVAILABLE"
            )
            return self._finalize({
                **base,
                "execution_state": "NOT_APPLICABLE" if link_source["present"] else "BLOCKED",
                "request_consumption_state": (
                    "REQUEST_VALIDATED"
                    if link_source["present"]
                    else "REQUEST_INPUT_UNAVAILABLE"
                ),
                "non_execution_reason": reason,
            })
        if not eligible:
            return self._finalize({
                **base,
                "execution_state": "NOT_APPLICABLE",
                "request_consumption_state": "REQUEST_VALIDATED",
                "non_execution_reason": "NO_ELIGIBLE_DEPENDENCY_LINKS",
            })

        chain = self._minimal_chain(
            eligible[0],
            dependency_execution_id=execution_id,
            activation_request_id=request["activation_request_id"],
            invocation_id=invocation_id,
            executor_component_id=target_component_id,
        )
        bridge_graph_report = self._executor_graph_report(chain, eligible[0])
        attempted = 0
        try:
            attempted = 1
            raw = executor.execute(
                activation_request={
                    **request,
                    "request_state": "REQUESTED",
                    "canonical_invocation_id": invocation_id,
                },
                activation_decision={"activation_state": "DEPENDENCY_REQUIRED"},
                concepts=[chain["source_identity"]],
                activated_tools=["dependency_reasoning"],
                graph_report=bridge_graph_report,
                runtime_context=dict(context),
            )
        except Exception as exc:  # pragma: no cover - defensive runtime barrier.
            chain["chain_state"] = "FAILED"
            chain["failure_reason"] = str(exc)
            return self._finalize({
                **base,
                "execution_state": "FAILED",
                "request_consumption_state": "REQUEST_ADMITTED",
                "planned_chain_count": 1,
                "attempted_chain_count": attempted,
                "chain_records": [chain],
                "non_execution_reason": "DEPENDENCY_EXECUTION_EXCEPTION",
                "failure_records": [{
                    "failure_code": "DEPENDENCY_EXECUTION_EXCEPTION",
                    "failure_reason": str(exc),
                }],
            })

        outputs = [
            dict(item)
            for item in raw.get("dependency_outputs", []) or []
            if isinstance(item, Mapping)
        ]
        result_records = self._result_records(
            outputs,
            run_id=run_id,
            task_id=task_id,
            dependency_execution_id=execution_id,
            invocation_id=invocation_id,
            chain_id=chain["dependency_chain_id"],
        )
        executed = int(bool(raw.get("execution_success") and result_records))
        if executed:
            chain["chain_state"] = "CHAIN_EXECUTED"
            chain["executed_depth"] = max(
                int(item.get("dependency_chain_depth", 0) or 0)
                for item in result_records
            )
            chain["used_link_ids"] = list(chain["ordered_link_ids"])
            chain["raw_result_ids"] = [
                item["dependency_result_id"] for item in result_records
            ]
        else:
            chain["chain_state"] = "FAILED"
            chain["failure_reason"] = raw.get("failure_reason") or "DEPENDENCY_RESULT_NOT_CAPTURED"
        receipt = {
            **base,
            "request_consumption_state": "REQUEST_ADMITTED",
            "execution_state": "RESULT_CAPTURED" if executed else "FAILED",
            "input_link_count": len(links),
            "eligible_link_count": len(eligible),
            "planned_chain_count": 1,
            "attempted_chain_count": attempted,
            "executed_chain_count": executed,
            "used_link_count": len(chain["used_link_ids"]),
            "maximum_executed_depth": chain["executed_depth"],
            "result_count": len(result_records),
            "chain_records": [chain],
            "result_records": result_records,
            "raw_execution_report": raw,
            "non_execution_reason": None if executed else chain["failure_reason"],
            "failure_records": [] if executed else [{
                "failure_code": chain["failure_reason"],
                "executor_component_id": target_component_id,
            }],
            "link_eligibility": eligibility_records,
            "link_source": link_source["source"],
        }
        finalized = self._finalize(receipt)
        self._receipts[invocation_id] = deepcopy(finalized)
        return finalized

    def _base_receipt(
        self,
        *,
        dependency_execution_id: str,
        run_id: str,
        task_id: str,
        plan: Mapping[str, Any],
        node: Mapping[str, Any] | None,
        request: Mapping[str, Any] | None,
        invocation_id: str,
    ) -> dict[str, Any]:
        node = node if isinstance(node, Mapping) else {}
        request = request if isinstance(request, Mapping) else {}
        return {
            "dependency_execution_schema_version": self.schema_version,
            "dependency_execution_id": dependency_execution_id,
            "run_id": run_id,
            "task_id": task_id,
            "execution_plan_id": plan.get("execution_plan_id"),
            "execution_node_id": node.get("execution_node_id"),
            "runtime_stage_id": node.get("runtime_stage_id"),
            "activation_request_id": request.get("activation_request_id"),
            "admission_record_id": self._stable_id(
                "admission_record",
                {
                    "plan": plan.get("execution_plan_id"),
                    "node": node.get("execution_node_id"),
                },
            ) if node else None,
            "invocation_id": invocation_id,
            "target_component_id": node.get("target_runtime_component"),
            "execution_state": "REQUEST_RECEIVED",
            "request_consumption_state": "REQUEST_RECEIVED",
            "input_link_count": 0,
            "eligible_link_count": 0,
            "planned_chain_count": 0,
            "attempted_chain_count": 0,
            "executed_chain_count": 0,
            "used_link_count": 0,
            "maximum_executed_depth": 0,
            "result_count": 0,
            "chain_records": [],
            "result_records": [],
            "link_eligibility": [],
            "non_execution_reason": None,
            "failure_records": [],
            "process_context_count": 0,
            "causal_context_count": 0,
            "evidence_acceptance_state": "NOT_EVALUATED",
            "dependency_coverage": "NOT_DEFINED",
            "started_at_or_sequence": "REQUEST_VALIDATION",
            "completed_at_or_sequence": None,
            "immutability_state": "MUTABLE_UNTIL_FINALIZED",
        }

    def _request_failure(
        self,
        plan: Mapping[str, Any],
        node: Mapping[str, Any] | None,
        request: Mapping[str, Any] | None,
        context: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        if plan.get("execution_plan_validation_state") != "VALID":
            return self._failure("REQUEST_REJECTED", "BLOCKED", "PLAN_NOT_VALID")
        if not plan.get("execution_plan_finalized") or not plan.get("execution_plan_immutable"):
            return self._failure("REQUEST_STALE", "BLOCKED", "PLAN_NOT_FINALIZED")
        if not self._plan_fingerprint_valid(plan):
            return self._failure("REQUEST_STALE", "BLOCKED", "PLAN_STALE")
        if self._context_identity(context, "run_id") and self._context_identity(context, "run_id") != self._identity(plan.get("run_id")):
            return self._failure("REQUEST_STALE", "BLOCKED", "DEPENDENCY_RESULT_CROSS_RUN_CONTAMINATION")
        if self._context_identity(context, "task_id") and self._context_identity(context, "task_id") != self._identity(plan.get("task_id")):
            return self._failure("REQUEST_STALE", "BLOCKED", "DEPENDENCY_RESULT_CROSS_TASK_CONTAMINATION")
        if not request:
            return self._failure("REQUEST_REJECTED", "BLOCKED", "DEPENDENCY_ACTIVATION_REQUEST_NOT_CONSUMED")
        if not node:
            return self._failure("REQUEST_REJECTED", "BLOCKED", "DEPENDENCY_PLAN_NODE_NOT_RESOLVED")
        if request.get("execution_node_id") != node.get("execution_node_id"):
            return self._failure("REQUEST_REJECTED", "BLOCKED", "DEPENDENCY_PLAN_NODE_NOT_RESOLVED")
        if node.get("materialization_state") != "MATERIALIZED":
            return self._failure("REQUEST_BLOCKED", "BLOCKED", "DEPENDENCY_CHAIN_NOT_MATERIALIZED")
        if node.get("admission_state") not in {"ADMITTED", "ADMISSION_REQUESTED"}:
            return self._failure("REQUEST_BLOCKED", "BLOCKED", "INVOCATION_WITHOUT_ADMISSION")
        if node.get("activation_state") != "REQUESTED":
            return self._failure("REQUEST_BLOCKED", "BLOCKED", "DEPENDENCY_ACTIVATION_NOT_REQUESTED")
        if request.get("request_state") not in {"REQUESTED", None}:
            return self._failure("REQUEST_REJECTED", "BLOCKED", "DEPENDENCY_ACTIVATION_REQUEST_REJECTED")
        return None

    def _dependency_activation_request(
        self,
        plan: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        for request in plan.get("dependency_activation_requests", []) or []:
            if isinstance(request, Mapping):
                return request
        return None

    def _dependency_node(
        self,
        plan: Mapping[str, Any],
        request: Mapping[str, Any] | None,
    ) -> Mapping[str, Any] | None:
        request_node_id = request.get("execution_node_id") if request else None
        for node in plan.get("nodes", []) or []:
            if not isinstance(node, Mapping):
                continue
            if request_node_id and node.get("execution_node_id") == request_node_id:
                return node
            if node.get("originating_tool") == "dependency_reasoning":
                return node
        return None

    def _link_source(self, context: Mapping[str, Any]) -> dict[str, Any]:
        for key in (
            "dependency_graph_report",
            "dependency_graph_builder_report",
            "dependency_graph_discovery_report",
            "DEPENDENCY_GRAPH_REPORT",
        ):
            value = context.get(key)
            if isinstance(value, Mapping) and "dependency_links" in value:
                return {
                    "source": key,
                    "present": True,
                    "links": [
                        dict(item)
                        for item in value.get("dependency_links", []) or []
                        if isinstance(item, Mapping)
                    ],
                }
        if "dependency_links" in context:
            return {
                "source": "dependency_links",
                "present": True,
                "links": [
                    dict(item)
                    for item in context.get("dependency_links", []) or []
                    if isinstance(item, Mapping)
                ],
            }
        return {"source": None, "present": False, "links": []}

    def _eligibility_records(
        self,
        links: list[Mapping[str, Any]],
        *,
        run_id: str,
        task_id: str,
    ) -> list[dict[str, Any]]:
        records = []
        seen = set()
        for index, link in enumerate(links):
            normalized = self._normalize_link(link, index)
            state = "ELIGIBLE"
            reason = None
            key = (
                normalized["source_identity"],
                normalized["target_identity"],
                normalized["dependency_type"],
            )
            if key in seen:
                state = "DUPLICATE"
                reason = "duplicate_dependency_link"
            elif not normalized["source_identity"]:
                state = "SOURCE_UNRESOLVED"
                reason = "source_identity_missing"
            elif not normalized["target_identity"]:
                state = "TARGET_UNRESOLVED"
                reason = "target_identity_missing"
            elif normalized["dependency_type"] not in EXECUTABLE_DEPENDENCY_TYPES:
                state = "TYPE_UNSUPPORTED"
                reason = "dependency_type_not_executable"
            elif normalized["direction"] not in {"source_to_target", "SOURCE_TO_TARGET"}:
                state = "DIRECTION_INVALID"
                reason = "direction_not_source_to_target"
            elif normalized["run_scope"] not in {run_id, "current_run"}:
                state = "OUT_OF_RUN_SCOPE" if normalized["run_scope"] else "ELIGIBILITY_NOT_VERIFIED"
                reason = "run_scope_not_current" if normalized["run_scope"] else "legacy_run_scope_unverifiable"
            elif normalized["task_scope"] not in {task_id, "current_task"}:
                state = "OUT_OF_TASK_SCOPE" if normalized["task_scope"] else "ELIGIBILITY_NOT_VERIFIED"
                reason = "task_scope_not_current" if normalized["task_scope"] else "legacy_task_scope_unverifiable"
            seen.add(key)
            records.append({
                **normalized,
                "eligibility_state": state,
                "eligibility_authority": self.system_name,
                "rejection_reason": reason,
                "consuming_chain_id": None,
            })
        return sorted(records, key=lambda item: item["dependency_link_id"])

    def _normalize_link(
        self,
        link: Mapping[str, Any],
        index: int,
    ) -> dict[str, Any]:
        source = self._identity(link.get("source") or link.get("source_id") or "")
        target = self._identity(link.get("target") or link.get("target_id") or "")
        dependency_type = str(
            link.get("dependency_type")
            or link.get("relationship")
            or link.get("edge_type")
            or ""
        )
        link_id = str(
            link.get("dependency_link_id")
            or link.get("edge_id")
            or link.get("id")
            or self._stable_id(
                "dependency_link",
                {
                    "source": source,
                    "target": target,
                    "type": dependency_type,
                    "index": index,
                },
            )
        )
        return {
            "dependency_link_id": link_id,
            "source_identity": source,
            "target_identity": target,
            "dependency_type": dependency_type,
            "direction": str(link.get("direction") or "source_to_target"),
            "origin": link.get("origin") or link.get("generated_by") or "dependency_link_record",
            "run_scope": str(link.get("run_id") or link.get("run_scope") or ""),
            "task_scope": str(link.get("task_id") or link.get("task_scope") or ""),
            "confidence": link.get("confidence"),
            "support": link.get("support"),
        }

    def _minimal_chain(
        self,
        link_record: Mapping[str, Any],
        *,
        dependency_execution_id: str,
        activation_request_id: str,
        invocation_id: str,
        executor_component_id: str,
    ) -> dict[str, Any]:
        chain_id = self._stable_id(
            "dependency_chain",
            {
                "dependency_execution_id": dependency_execution_id,
                "link": link_record["dependency_link_id"],
                "activation_request_id": activation_request_id,
            },
        )
        link_record["consuming_chain_id"] = chain_id
        return {
            "dependency_chain_id": chain_id,
            "dependency_execution_id": dependency_execution_id,
            "source_activation_request_id": activation_request_id,
            "ordered_link_ids": [link_record["dependency_link_id"]],
            "source_identity": link_record["source_identity"],
            "terminal_identity": link_record["target_identity"],
            "planned_depth": 1,
            "executed_depth": 0,
            "chain_state": "CHAIN_PLANNED",
            "execution_order": 0,
            "executor_component_id": executor_component_id,
            "invocation_id": invocation_id,
            "used_link_ids": [],
            "raw_result_ids": [],
            "block_reason": None,
            "failure_reason": None,
            "chain_builder_component_id": self.chain_builder.system_name,
            "chain_builder_report": self._chain_builder_report(link_record),
        }

    def _chain_builder_report(
        self,
        link_record: Mapping[str, Any],
    ) -> dict[str, Any]:
        report = self.chain_builder.build(
            link_record["source_identity"],
            [{
                "source": link_record["source_identity"],
                "target": link_record["target_identity"],
                "dependency_type": link_record["dependency_type"],
                "confidence": link_record.get("confidence") or 0.0,
            }],
            max_depth=1,
        )
        return {
            "system": report.get("system"),
            "dependency_chain_depth": report.get("dependency_chain_depth", 0),
            "process_dependency_links_used": report.get(
                "process_dependency_links_used",
                0,
            ),
            "dependency_chain_coverage": report.get(
                "dependency_chain_coverage",
                0.0,
            ),
        }

    def _executor_graph_report(
        self,
        chain: Mapping[str, Any],
        link_record: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "dependency_chains": [{
                "concept": chain["source_identity"],
                "chain": [chain["terminal_identity"]],
                "dependency_depth": 1,
                "dependency_confidence": link_record.get("confidence") or 0.0,
            }],
            "dependency_links": [{
                "source": chain["source_identity"],
                "target": chain["terminal_identity"],
                "dependency_type": link_record["dependency_type"],
                "confidence": link_record.get("confidence"),
            }],
        }

    def _result_records(
        self,
        outputs: list[Mapping[str, Any]],
        *,
        run_id: str,
        task_id: str,
        dependency_execution_id: str,
        invocation_id: str,
        chain_id: str,
    ) -> list[dict[str, Any]]:
        records = []
        for index, output in enumerate(outputs):
            result_id = self._stable_id(
                "dependency_result",
                {
                    "dependency_execution_id": dependency_execution_id,
                    "invocation_id": invocation_id,
                    "chain_id": chain_id,
                    "index": index,
                    "chain": output.get("resolved_dependency_chain") or output.get("chain"),
                },
            )
            records.append({
                "dependency_result_id": result_id,
                "dependency_execution_id": dependency_execution_id,
                "invocation_id": invocation_id,
                "dependency_chain_id": chain_id,
                "run_id": run_id,
                "task_id": task_id,
                "result_state": "RESULT_VALIDATED_STRUCTURALLY",
                "dependency_chain_depth": int(output.get("dependency_chain_depth", 0) or 0),
                "used_link_count": 1 if output.get("dependency_output_produced") else 0,
                "raw_result": dict(output),
                "structural_validation_state": (
                    "VALID"
                    if isinstance(output.get("resolved_dependency_chain"), list)
                    else "INVALID"
                ),
            })
        return [
            record for record in records
            if record["structural_validation_state"] == "VALID"
        ]

    def _finalize(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        finalized = dict(receipt)
        finalized["completed_at_or_sequence"] = "DEPENDENCY_EXECUTION_RECEIPT_FINALIZED"
        finalized["immutability_state"] = "IMMUTABLE"
        finalized["dependency_execution_fingerprint"] = self._fingerprint(finalized)
        return finalized

    def _failure(
        self,
        request_state: str,
        execution_state: str,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "request_consumption_state": request_state,
            "execution_state": execution_state,
            "reason": reason,
            "failure_code": reason,
        }

    def _invocation_id(
        self,
        plan: Mapping[str, Any],
        node: Mapping[str, Any] | None,
        request: Mapping[str, Any] | None,
    ) -> str:
        return self._stable_id(
            "invocation",
            {
                "execution_plan_id": plan.get("execution_plan_id"),
                "execution_node_id": node.get("execution_node_id") if node else None,
                "activation_request_id": request.get("activation_request_id") if request else None,
            },
        )

    def _context_identity(self, context: Mapping[str, Any], key: str) -> str | None:
        if key not in context:
            return None
        return self._identity(context.get(key))

    def _identity(self, value: Any) -> str:
        return str(value or "").strip()

    def _fingerprint(self, payload: Mapping[str, Any]) -> str:
        data = dict(payload)
        data.pop("dependency_execution_fingerprint", None)
        return self._stable_id("dependency_execution_fingerprint", data)

    def _plan_fingerprint_valid(self, plan: Mapping[str, Any]) -> bool:
        fingerprint = plan.get("execution_plan_fingerprint")
        if not fingerprint:
            return False
        data = dict(plan)
        data.pop("execution_plan_fingerprint", None)
        return fingerprint == self._stable_id("execution_plan_fingerprint", data)

    def _stable_id(self, prefix: str, payload: Any) -> str:
        text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


dependency_execution_runtime = DependencyExecutionRuntime()


__all__ = ["DependencyExecutionRuntime", "dependency_execution_runtime"]
