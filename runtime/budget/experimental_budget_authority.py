"""Run-scoped experimental budget authority for isolated ablations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


EXPERIMENTAL_BUDGET_SOURCE = "EXPERIMENTAL_BUDGET_GRANT"
NORMAL_BUDGET_SOURCE = "COGNITIVE_BUDGET_REPORT"
CURRENT_RUN_ONLY = "CURRENT_RUN_ONLY"


class ExperimentalBudgetAuthorityError(ValueError):
    """Raised when an experimental budget contract is malformed."""


@dataclass(frozen=True)
class ExperimentalBudgetRequest:
    experiment_id: str
    requested_max_active_routes: int
    requested_max_reasoning_depth: int
    requested_max_dependency_depth: int
    requested_max_hypotheses: int
    persistent: bool = False
    production_policy_mutation: bool = False
    authority: str = "NONE"

    def __post_init__(self) -> None:
        _require_identity(self.experiment_id, "experiment_id")
        _require_positive_int(self.requested_max_active_routes, "requested_max_active_routes")
        _require_positive_int(self.requested_max_reasoning_depth, "requested_max_reasoning_depth")
        _require_positive_int(self.requested_max_dependency_depth, "requested_max_dependency_depth")
        _require_positive_int(self.requested_max_hypotheses, "requested_max_hypotheses")
        if self.persistent is not False:
            raise ExperimentalBudgetAuthorityError("experimental request must be nonpersistent")
        if self.production_policy_mutation is not False:
            raise ExperimentalBudgetAuthorityError("experimental request cannot mutate production policy")
        if self.authority != "NONE":
            raise ExperimentalBudgetAuthorityError("experimental request has zero runtime authority")

    def as_report(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentalBudgetGrant:
    experiment_id: str
    run_id: str
    granted_max_active_routes: int
    granted_max_reasoning_depth: int
    granted_max_dependency_depth: int
    granted_max_hypotheses: int
    scope: str = CURRENT_RUN_ONLY
    persistent: bool = False
    promotable: bool = False
    stale: bool = False

    def __post_init__(self) -> None:
        _require_identity(self.experiment_id, "experiment_id")
        _require_identity(self.run_id, "run_id")
        _require_positive_int(self.granted_max_active_routes, "granted_max_active_routes")
        _require_positive_int(self.granted_max_reasoning_depth, "granted_max_reasoning_depth")
        _require_positive_int(self.granted_max_dependency_depth, "granted_max_dependency_depth")
        _require_positive_int(self.granted_max_hypotheses, "granted_max_hypotheses")
        if self.scope != CURRENT_RUN_ONLY:
            raise ExperimentalBudgetAuthorityError("experimental grant must be current-run scoped")
        if self.persistent is not False:
            raise ExperimentalBudgetAuthorityError("experimental grant must be nonpersistent")
        if self.promotable is not False:
            raise ExperimentalBudgetAuthorityError("experimental grant must be nonpromotable")

    def as_report(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeBudgetBinding:
    experiment_id: str | None
    run_id: str
    budget_source: str
    effective_max_active_routes: int
    effective_max_reasoning_depth: int
    effective_max_dependency_depth: int
    effective_max_hypotheses: int
    binding_state: str
    persistent: bool = False
    production_policy_mutation: bool = False
    non_budget_authority_changed: bool = False
    rejection_reason: str | None = None

    def as_report(self) -> dict[str, Any]:
        return asdict(self)


def issue_experimental_budget_grant(
    request: ExperimentalBudgetRequest | Mapping[str, Any],
    *,
    run_id: str,
) -> ExperimentalBudgetGrant:
    """Issue the explicit current-run grant from a non-authoritative request."""

    request = _request_from(request)
    return ExperimentalBudgetGrant(
        experiment_id=request.experiment_id,
        run_id=str(run_id),
        granted_max_active_routes=request.requested_max_active_routes,
        granted_max_reasoning_depth=request.requested_max_reasoning_depth,
        granted_max_dependency_depth=request.requested_max_dependency_depth,
        granted_max_hypotheses=request.requested_max_hypotheses,
    )


def resolve_runtime_budget_authority(
    *,
    normal_budget: Any,
    runtime_context: Mapping[str, Any] | None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Resolve the effective runtime budget without granting request authority."""

    context = runtime_context if isinstance(runtime_context, Mapping) else {}
    bound_run_id = str(
        run_id
        or _plan_value(context, "run_id")
        or context.get("run_id")
        or context.get("execution_id")
        or "current_run"
    )
    request_raw = context.get("experimental_budget_request")
    grant_raw = context.get("experimental_budget_grant")

    if grant_raw is None:
        binding = RuntimeBudgetBinding(
            experiment_id=_mapping_value(request_raw, "experiment_id"),
            run_id=bound_run_id,
            budget_source=NORMAL_BUDGET_SOURCE,
            effective_max_active_routes=_budget_int(normal_budget, "max_active_routes", 0),
            effective_max_reasoning_depth=_budget_int(normal_budget, "max_reasoning_depth", 0),
            effective_max_dependency_depth=_budget_int(normal_budget, "max_dependency_depth", 0),
            effective_max_hypotheses=_budget_int(normal_budget, "max_hypotheses", 0),
            binding_state=(
                "EXPERIMENT_REQUEST_NON_AUTHORITATIVE"
                if request_raw is not None
                else "NORMAL_PRODUCTION_BUDGET"
            ),
        )
        return {
            "budget": normal_budget,
            "binding": binding.as_report(),
            "grant_applied": False,
        }

    try:
        request = _request_from(request_raw)
        grant = _grant_from(grant_raw)
        _validate_grant_matches_request(request, grant, bound_run_id)
    except ExperimentalBudgetAuthorityError as exc:
        binding = RuntimeBudgetBinding(
            experiment_id=_mapping_value(grant_raw, "experiment_id"),
            run_id=bound_run_id,
            budget_source=NORMAL_BUDGET_SOURCE,
            effective_max_active_routes=_budget_int(normal_budget, "max_active_routes", 0),
            effective_max_reasoning_depth=_budget_int(normal_budget, "max_reasoning_depth", 0),
            effective_max_dependency_depth=_budget_int(normal_budget, "max_dependency_depth", 0),
            effective_max_hypotheses=_budget_int(normal_budget, "max_hypotheses", 0),
            binding_state="EXPERIMENTAL_BUDGET_GRANT_REJECTED",
            rejection_reason=str(exc),
        )
        return {
            "budget": normal_budget,
            "binding": binding.as_report(),
            "grant_applied": False,
        }

    _set_budget_value(normal_budget, "max_active_routes", grant.granted_max_active_routes)
    _set_budget_value(normal_budget, "max_reasoning_depth", grant.granted_max_reasoning_depth)
    _set_budget_value(normal_budget, "max_dependency_depth", grant.granted_max_dependency_depth)
    _set_budget_value(normal_budget, "max_hypotheses", grant.granted_max_hypotheses)

    notes = getattr(normal_budget, "notes", None)
    if isinstance(notes, list) and "experimental_budget_grant_applied" not in notes:
        notes.append("experimental_budget_grant_applied")

    binding = RuntimeBudgetBinding(
        experiment_id=grant.experiment_id,
        run_id=bound_run_id,
        budget_source=EXPERIMENTAL_BUDGET_SOURCE,
        effective_max_active_routes=grant.granted_max_active_routes,
        effective_max_reasoning_depth=grant.granted_max_reasoning_depth,
        effective_max_dependency_depth=grant.granted_max_dependency_depth,
        effective_max_hypotheses=grant.granted_max_hypotheses,
        binding_state="EXPERIMENTAL_BUDGET_GRANT_ACCEPTED",
    )
    return {
        "budget": normal_budget,
        "binding": binding.as_report(),
        "grant": grant.as_report(),
        "grant_applied": True,
    }


def _request_from(value: ExperimentalBudgetRequest | Mapping[str, Any] | None) -> ExperimentalBudgetRequest:
    if isinstance(value, ExperimentalBudgetRequest):
        return value
    if not isinstance(value, Mapping):
        raise ExperimentalBudgetAuthorityError("matching experimental request is required")
    return ExperimentalBudgetRequest(
        experiment_id=str(value.get("experiment_id") or ""),
        requested_max_active_routes=value.get("requested_max_active_routes"),
        requested_max_reasoning_depth=value.get("requested_max_reasoning_depth"),
        requested_max_dependency_depth=value.get("requested_max_dependency_depth"),
        requested_max_hypotheses=value.get("requested_max_hypotheses"),
        persistent=value.get("persistent", False),
        production_policy_mutation=value.get("production_policy_mutation", False),
        authority=str(value.get("authority", "NONE")),
    )


def _grant_from(value: ExperimentalBudgetGrant | Mapping[str, Any]) -> ExperimentalBudgetGrant:
    if isinstance(value, ExperimentalBudgetGrant):
        return value
    if not isinstance(value, Mapping):
        raise ExperimentalBudgetAuthorityError("experimental grant must be a mapping")
    return ExperimentalBudgetGrant(
        experiment_id=str(value.get("experiment_id") or ""),
        run_id=str(value.get("run_id") or ""),
        granted_max_active_routes=value.get("granted_max_active_routes"),
        granted_max_reasoning_depth=value.get("granted_max_reasoning_depth"),
        granted_max_dependency_depth=value.get("granted_max_dependency_depth"),
        granted_max_hypotheses=value.get("granted_max_hypotheses"),
        scope=str(value.get("scope", CURRENT_RUN_ONLY)),
        persistent=value.get("persistent", False),
        promotable=value.get("promotable", False),
        stale=value.get("stale", False),
    )


def _validate_grant_matches_request(
    request: ExperimentalBudgetRequest,
    grant: ExperimentalBudgetGrant,
    run_id: str,
) -> None:
    if grant.stale is True:
        raise ExperimentalBudgetAuthorityError("experimental grant is stale")
    if grant.run_id != str(run_id):
        raise ExperimentalBudgetAuthorityError("experimental grant is foreign-run")
    if grant.experiment_id != request.experiment_id:
        raise ExperimentalBudgetAuthorityError("experimental grant/request mismatch")
    expected = {
        "max_active_routes": (
            request.requested_max_active_routes,
            grant.granted_max_active_routes,
        ),
        "max_reasoning_depth": (
            request.requested_max_reasoning_depth,
            grant.granted_max_reasoning_depth,
        ),
        "max_dependency_depth": (
            request.requested_max_dependency_depth,
            grant.granted_max_dependency_depth,
        ),
        "max_hypotheses": (
            request.requested_max_hypotheses,
            grant.granted_max_hypotheses,
        ),
    }
    mismatched = [name for name, (requested, granted) in expected.items() if requested != granted]
    if mismatched:
        raise ExperimentalBudgetAuthorityError(
            "experimental grant/request budget mismatch: " + ",".join(mismatched)
        )


def _require_identity(value: str, name: str) -> None:
    if not str(value or "").strip():
        raise ExperimentalBudgetAuthorityError(f"{name} is required")


def _require_positive_int(value: Any, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ExperimentalBudgetAuthorityError(f"{name} must be a positive integer")


def _mapping_value(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


def _plan_value(context: Mapping[str, Any], key: str) -> Any:
    plan = context.get("authoritative_execution_plan")
    if isinstance(plan, Mapping):
        return plan.get(key)
    reference = context.get("authoritative_execution_plan_reference")
    if isinstance(reference, Mapping):
        return reference.get(key)
    return None


def _budget_int(budget: Any, key: str, default: int) -> int:
    value = budget.get(key, default) if isinstance(budget, Mapping) else getattr(budget, key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _set_budget_value(budget: Any, key: str, value: int) -> None:
    if isinstance(budget, dict):
        budget[key] = value
    else:
        setattr(budget, key, value)


__all__ = [
    "CURRENT_RUN_ONLY",
    "EXPERIMENTAL_BUDGET_SOURCE",
    "NORMAL_BUDGET_SOURCE",
    "ExperimentalBudgetAuthorityError",
    "ExperimentalBudgetGrant",
    "ExperimentalBudgetRequest",
    "RuntimeBudgetBinding",
    "issue_experimental_budget_grant",
    "resolve_runtime_budget_authority",
]
