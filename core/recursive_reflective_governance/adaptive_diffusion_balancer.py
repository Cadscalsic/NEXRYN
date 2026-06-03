def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class AdaptiveDiffusionBalancer:

    def balance(self, context, pruning):

        diffusion = _clamp(
            context.get("semantic_field_dynamics_report", {})
            .get("drift_diffusion_equations", {})
            .get("diffusion_rate", 0.0)
        )
        pruning_need = _clamp(pruning.get("semantic_pruning_need", 0.0))

        diffusion_balance = _clamp(
            (1.0 - diffusion) * 0.48
            +
            (1.0 - pruning_need) * 0.52
        )

        return {
            "system": "adaptive_diffusion_balancer",
            "diffusion_rate": diffusion,
            "diffusion_balance": diffusion_balance,
            "diffusion_actions": [
                "slow_semantic_diffusion",
                "diffuse_only_attested_recursive_updates",
            ]
            if diffusion_balance < 0.58
            else [],
            "diffusion_state": (
                "adaptive_diffusion_balancing_active"
                if diffusion_balance < 0.58
                else "adaptive_diffusion_balanced"
            ),
        }
