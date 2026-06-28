# ============================================
# NEXRYN RUNTIME ENERGY BUDGET
# OPTIMIZED / ACTIONABLE VERSION
# ============================================

from datetime import datetime
import hashlib
import json


def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class RuntimeEnergyBudget:

    BASE_COSTS = {
        "governance_kernel": (0.08, 0.05, 0.06),
        "epistemic_constitution": (0.10, 0.09, 0.07),
        "epistemic_cognition_layer": (0.16, 0.14, 0.12),
        "cognitive_physician": (0.10, 0.08, 0.05),
        "semantic_compression": (0.10, 0.08, 0.04),
        "cognitive_kernel": (0.12, 0.08, 0.08),
        "semantic_os": (0.16, 0.12, 0.06),
        "concept_lifecycle": (0.10, 0.10, 0.04),
        "cognitive_physics": (0.18, 0.14, 0.06),
        "reasoning": (0.24, 0.18, 0.04),
        "legacy_governance_aliases": (0.02, 0.02, 0.02),
    }

    OPTIONAL_MODULES = {
        "semantic_os",
        "concept_lifecycle",
        "cognitive_physics",
        "legacy_governance_aliases",
    }

    EXPENSIVE_MODULES = {
        "epistemic_cognition_layer",
        "cognitive_physics",
        "semantic_os",
        "reasoning",
    }

    def __init__(self):
        self.last_signature = None
        self.last_report = None
        self.cache_hits = 0
        self.cache_misses = 0

    def _stable_hash(self, payload):
        try:
            encoded = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            encoded = str(payload)

        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _signature(self, context, active_modules):
        return self._stable_hash({
            "active_modules": sorted(active_modules or []),
            "runtime_entropy": context.get("runtime_entropy"),
            "memory_pressure_score": context.get("memory_pressure_score"),
            "working_memory_pressure": context.get("working_memory_pressure"),
            "kernel_pressure": (
                context.get("cognitive_kernel_report", {})
                .get("pressure_report", {})
                .get("total_kernel_pressure")
            ),
            "episode_completed": context.get("episode_completed"),
            "shutdown_mode": context.get("shutdown_mode"),
            "post_success_mode": context.get("post_success_mode"),
        })

    def _fast_mode(self, context):
        return (
            context.get("episode_completed") is True
            or context.get("shutdown_mode") == "fast"
            or context.get("post_success_mode") == "fast"
            or context.get("post_success_shutdown", {}).get("enabled") is True
        )

    def compute_pressure(self, context=None):
        context = context or {}

        kernel = context.get("cognitive_kernel_report", {})

        pressure = (
            kernel.get("pressure_report", {})
            .get(
                "total_kernel_pressure",
                context.get("runtime_entropy", 0.0),
            )
        )

        return _clamp(pressure)

    def _cache_report(self):
        total = self.cache_hits + self.cache_misses
        return {
            "system": "runtime_energy_budget_cache",
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hits / total, 4) if total else 0.0,
        }

    def allocate(self, context=None, active_modules=None):
        context = context or {}
        active_modules = active_modules or []

        if not isinstance(active_modules, list):
            active_modules = list(active_modules)

        signature = self._signature(context, active_modules)

        if self.last_signature == signature and self.last_report is not None:
            self.cache_hits += 1
            report = dict(self.last_report)
            report["energy_budget_cache_hit"] = True
            report["energy_budget_cache_report"] = self._cache_report()
            report["timestamp"] = str(datetime.utcnow())
            return report

        self.cache_misses += 1

        pressure = self.compute_pressure(context)
        fast_mode = self._fast_mode(context)

        budgets = {}

        for subsystem in active_modules:
            energy_cost, attention_cost, governance_cost = self.BASE_COSTS.get(
                subsystem,
                (0.12, 0.08, 0.04),
            )

            memory_cost = _clamp(
                energy_cost * 0.70
                + pressure * 0.10
            )

            budgets[subsystem] = {
                "energy_budget": _clamp(
                    max(
                        0.02,
                        0.22 - energy_cost - pressure * 0.04,
                    )
                ),
                "attention_cost": _clamp(
                    attention_cost + pressure * 0.04
                ),
                "memory_cost": memory_cost,
                "governance_cost": _clamp(
                    governance_cost + pressure * 0.03
                ),
                "optional": subsystem in self.OPTIONAL_MODULES,
                "expensive": subsystem in self.EXPENSIVE_MODULES,
            }

        total_governance_cost = _clamp(
            sum(
                item.get("governance_cost", 0.0)
                for item in budgets.values()
            )
        )

        over_budget = total_governance_cost >= 0.70

        should_collapse_optional = (
            over_budget
            or fast_mode
            or pressure >= 0.62
        )

        collapsed_modules = sorted([
            module
            for module in active_modules
            if module in self.OPTIONAL_MODULES
        ]) if should_collapse_optional else []

        throttled_modules = sorted([
            module
            for module in active_modules
            if module in self.EXPENSIVE_MODULES
        ]) if pressure >= 0.62 or over_budget else []

        execution_directives = {
            "collapse_optional_governance_modules": should_collapse_optional,
            "collapsed_modules": collapsed_modules,
            "throttle_expensive_modules": bool(throttled_modules),
            "throttled_modules": throttled_modules,
            "prefer_cache_reuse": fast_mode or over_budget,
            "skip_deep_reports": fast_mode or over_budget,
            "allow_full_governance": not fast_mode and not over_budget,
        }

        report = {
            "system": "runtime_energy_budget",
            "pressure": pressure,
            "subsystems": budgets,
            "total_governance_cost": total_governance_cost,
            "budget_state": (
                "governance_over_budget"
                if over_budget
                else "within_budget"
            ),
            "fast_mode": fast_mode,
            "execution_directives": execution_directives,
            "energy_budget_cache_hit": False,
            "energy_budget_cache_report": self._cache_report(),
            "timestamp": str(datetime.utcnow()),
        }

        self.last_signature = signature
        self.last_report = dict(report)

        return report