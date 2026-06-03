def calculate_causal_support_score(
    supporting_observation_count,
    observation_count,
    minimum_supporting_observations,
):
    minimum_supporting_observations = max(
        int(minimum_supporting_observations),
        1,
    )
    observation_count = max(int(observation_count), 0)
    supporting_observation_count = max(
        min(int(supporting_observation_count), observation_count),
        0,
    )
    support_maturity = min(
        supporting_observation_count / minimum_supporting_observations,
        1.0,
    )
    support_reliability = (
        supporting_observation_count / observation_count
        if observation_count
        else 0.0
    )
    return {
        "support_maturity": round(support_maturity, 4),
        "support_reliability": round(support_reliability, 4),
        "causal_support_score": round(
            support_maturity * support_reliability,
            4,
        ),
    }


__all__ = [
    "calculate_causal_support_score",
]
