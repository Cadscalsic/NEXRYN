from core.epistemic_models import clamp


class IdentityContinuityAdapter:
    """Lightweight identity signal adapter for causal reasoning."""

    STATUS_SCORES = {
        "identity_preserved": (1.0, "CONTINUOUS"),
        "preserved": (1.0, "CONTINUOUS"),
        "identity_split": (0.45, "SPLIT"),
        "split": (0.45, "SPLIT"),
        "identity_fragmented": (0.25, "FRAGMENTED"),
        "fragmented": (0.25, "FRAGMENTED"),
        "identity_replaced": (0.0, "REPLACED"),
        "replaced": (0.0, "REPLACED"),
    }

    def evaluate(self, identity_report=None, context_report=None):
        identity_report = identity_report or {}
        context_report = context_report or {}
        raw_status = (
            identity_report.get("identity_status")
            or identity_report.get("identity_behavior")
            or context_report.get("identity_behavior")
            or "identity_preserved"
        )
        score, status = self.STATUS_SCORES.get(
            str(raw_status),
            (clamp(identity_report.get("identity_continuity", 0.75)), "UNKNOWN"),
        )
        continuity = clamp(identity_report.get("identity_continuity", score))
        if continuity >= 0.85:
            status = "CONTINUOUS"
        elif continuity >= 0.50 and status == "UNKNOWN":
            status = "PARTIAL"
        elif continuity < 0.20:
            status = "REPLACED"
        return {
            "system": "identity_continuity_adapter",
            "identity_continuity": continuity,
            "identity_status": status,
            "identity_preserved": continuity >= 0.85,
            "identity_split": status == "SPLIT",
            "identity_fragmented": status == "FRAGMENTED",
            "identity_replaced": status == "REPLACED",
        }


__all__ = [
    "IdentityContinuityAdapter",
]
