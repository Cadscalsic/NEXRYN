from core.epistemic_models import clamp


class AmbiguityResolutionEngine:
    def _resolve(self, simulation, rehearsal):
        simulation_state = simulation.get(
            "simulation_state",
            "ambiguous",
        )
        exports = rehearsal.get(
            "evidence_exports",
            {},
        )
        causal_alignment = clamp(
            simulation.get(
                "causal_alignment",
                0.0,
            )
        )
        identity_preservation = clamp(
            1.0
            -
            simulation.get(
                "predicted_identity_delta",
                1.0,
            )
        )
        entropy_bound = clamp(
            1.0
            -
            simulation.get(
                "predicted_entropy_delta",
                1.0,
            )
        )
        causal_attestation = clamp(
            exports.get(
                "causal_attestation_score",
                causal_alignment,
            )
        )
        identity_attestation = clamp(
            exports.get(
                "identity_attestation_score",
                identity_preservation,
            )
        )
        resolution_score = clamp(
            causal_alignment * 0.26
            +
            identity_preservation * 0.22
            +
            entropy_bound * 0.16
            +
            causal_attestation * 0.20
            +
            identity_attestation * 0.16
        )

        if simulation_state == "harmful":
            resolution = "REJECTED_PATH"
        elif simulation_state == "constructive" and resolution_score >= 0.68:
            resolution = "SUPPORTED_PATH"
        elif resolution_score >= 0.52:
            resolution = "PROBATIONARY_PATH"
        else:
            resolution = "DEFERRED_PATH"

        return {
            "simulation_id":
            simulation.get(
                "simulation_id",
                "unknown_simulation",
            ),

            "simulation_state":
            simulation_state,

            "resolution":
            resolution,

            "resolution_score":
            resolution_score,

            "confidence_is_not_resolution":
            True,

            "reason":
            (
                "ambiguous_path_has_bounded_support"
                if simulation_state == "ambiguous"
                and resolution == "PROBATIONARY_PATH"
                else "constructive_path_supported_by_attestation"
                if resolution == "SUPPORTED_PATH"
                else "path_requires_more_evidence"
                if resolution == "DEFERRED_PATH"
                else "path_rejected_by_simulation"
            ),
        }

    def run_cycle(self, context):
        context = context if isinstance(context, dict) else {}
        rehearsal = context.get(
            "causal_rehearsal_report",
            {},
        )
        simulations = rehearsal.get(
            "mutation_simulator",
            {},
        ).get(
            "simulations",
            [],
        )
        resolutions = [
            self._resolve(
                simulation,
                rehearsal,
            )
            for simulation in simulations
        ]
        return {
            "system":
            "ambiguity_resolution_engine",

            "resolutions":
            resolutions,

            "resolution_count":
            len(
                resolutions,
            ),

            "probationary_count":
            sum(
                item["resolution"]
                == "PROBATIONARY_PATH"
                for item in resolutions
            ),

            "supported_count":
            sum(
                item["resolution"]
                == "SUPPORTED_PATH"
                for item in resolutions
            ),

            "deferred_count":
            sum(
                item["resolution"]
                == "DEFERRED_PATH"
                for item in resolutions
            ),
        }


ambiguity_resolution_engine = AmbiguityResolutionEngine()
