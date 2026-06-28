# ============================================
# NEXRYN IDENTITY CORE LOCK
# OPTIMIZED / BOUNDED VERSION
# ============================================

import hashlib
import json


class IdentityCoreLock:

    IMMUTABLE_INVARIANTS = [
        "causality",
        "identity",
        "consistency",
        "temporal_continuity",
    ]

    REQUIRED_REWRITE_GATES = [
        "supervised_rewrite",
        "staged_rehearsal",
        "rollback_safe_mutation",
    ]

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

    def _extract_proposals(self, context):
        proposals = context.get(
            "identity_rewrite_request",
            context.get("proposed_invariant_rewrites", []),
        )

        if isinstance(proposals, dict):
            proposals = proposals.get("targets", [])

        if not isinstance(proposals, list):
            proposals = []

        return [
            str(item)
            for item in proposals
            if item is not None
        ]

    def _signature(self, context):
        return self._stable_hash({
            "proposals": self._extract_proposals(context),
            "gates": context.get("identity_rewrite_gates", {}),
        })

    def _cache_report(self):
        total = self.cache_hits + self.cache_misses
        return {
            "system": "identity_core_lock_cache",
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hits / total, 4) if total else 0.0,
        }

    def evaluate(self, context=None):
        context = context or {}

        signature = self._signature(context)

        if self.last_signature == signature and self.last_report is not None:
            self.cache_hits += 1
            report = dict(self.last_report)
            report["identity_core_lock_cache_hit"] = True
            report["identity_core_lock_cache_report"] = self._cache_report()
            return report

        self.cache_misses += 1

        proposals = self._extract_proposals(context)

        attempted = [
            item
            for item in proposals
            if item in self.IMMUTABLE_INVARIANTS
        ]

        gates = context.get("identity_rewrite_gates", {})
        if not isinstance(gates, dict):
            gates = {}

        gates_satisfied = all(
            gates.get(gate, False)
            for gate in self.REQUIRED_REWRITE_GATES
        )

        if attempted and not gates_satisfied:
            decision = "blocked"
        elif attempted:
            decision = "allowed_under_supervision"
        else:
            decision = "locked"

        report = {
            "system": "identity_core_lock",
            "locked_invariants": list(self.IMMUTABLE_INVARIANTS),
            "required_rewrite_gates": list(self.REQUIRED_REWRITE_GATES),
            "attempted_rewrites": attempted,
            "decision": decision,
            "rewrite_gates_satisfied": gates_satisfied,
            "identity_core_lock_cache_hit": False,
            "identity_core_lock_cache_report": self._cache_report(),
        }

        self.last_signature = signature
        self.last_report = dict(report)

        return report