CONTRADICTION_THRESHOLD = 0.10
SOFT_REVIEW_ZONE = 0.02
MEDIUM_RISK_REVIEW_LIMIT = 0.15


def classify_contradiction_review(
    contradiction_score,
    threshold=CONTRADICTION_THRESHOLD,
    soft_review_zone=SOFT_REVIEW_ZONE,
    medium_risk_review_limit=MEDIUM_RISK_REVIEW_LIMIT,
):
    if contradiction_score is None:
        return {
            "contradiction_gap": None,
            "contradiction_review_required": False,
            "within_soft_review_zone": False,
            "contradiction_review_severity": None,
        }
    gap = round(max(contradiction_score - threshold, 0.0), 4)
    review_required = gap > 0
    within_soft_review_zone = review_required and gap <= soft_review_zone
    severity = (
        None
        if not review_required
        else "LOW_RISK_REVIEW"
        if within_soft_review_zone
        else "MEDIUM_RISK_REVIEW"
        if contradiction_score <= medium_risk_review_limit
        else "HIGH_RISK_REVIEW"
    )
    return {
        "contradiction_gap": gap,
        "contradiction_review_required": review_required,
        "within_soft_review_zone": within_soft_review_zone,
        "contradiction_review_severity": severity,
    }


__all__ = [
    "CONTRADICTION_THRESHOLD",
    "MEDIUM_RISK_REVIEW_LIMIT",
    "SOFT_REVIEW_ZONE",
    "classify_contradiction_review",
]
