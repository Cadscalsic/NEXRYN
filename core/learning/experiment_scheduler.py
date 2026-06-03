class ExperimentScheduler:
    PRIORITY_ORDER = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    def schedule(self, requests):
        scheduled = sorted(
            list(requests or []),
            key=lambda item: (
                self.PRIORITY_ORDER.get(
                    item.get("experiment_proposal", {}).get(
                        "priority",
                        "medium",
                    ),
                    1,
                ),
                item.get("request_id", item.get("experiment_id", "")),
            ),
        )
        return {
            "system": "experiment_scheduler",
            "learning_phase": "7-prelude",
            "scheduled_requests": scheduled,
            "scheduled_request_count": len(scheduled),
            "priority_order": [
                "high",
                "medium",
                "low",
            ],
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "ExperimentScheduler",
]
