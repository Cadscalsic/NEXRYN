# ============================================
# NEXRYN COGNITIVE PHARMACY DOSAGE ENGINE
# ============================================


def clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class PharmacyDosageEngine:

    def compute(self, physician_report, dependency_report):

        metrics = physician_report.get(
            "health_metrics",
            {},
        )

        physician_dosage = physician_report.get(
            "dosage_controller",
            {},
        )

        recovery = physician_report.get(
            "recovery_monitor",
            {},
        ).get(
            "recovery_rate",
            0.0,
        )

        dependency = dependency_report.get(
            "dependency_risk",
            0.0,
        )

        taper = clamp(
            1.0
            -
            dependency * 0.40
            +
            recovery * 0.20
        )

        fever = metrics.get(
            "cognitive_fever_score",
            0.0,
        )
        entropy = metrics.get(
            "semantic_entropy",
            0.0,
        )
        drift = metrics.get(
            "identity_drift",
            0.0,
        )
        recursion = metrics.get(
            "recursion_pressure",
            0.0,
        )
        memory = metrics.get(
            "memory_pressure",
            0.0,
        )
        topology_stress = 1.0 - metrics.get(
            "topology_integrity",
            1.0,
        )

        return {
            "system": "pharmacy_dosage_engine",
            "dosage_is_static": False,
            "taper_factor": taper,
            "SEMANTIC_SEDATIVE": clamp(
                max(
                    physician_dosage.get("semantic_sedation", 0.0),
                    fever * 0.45 + entropy * 0.25 + recursion * 0.20,
                )
                * taper
            ),
            "IDENTITY_STABILIZER": clamp(
                max(
                    physician_dosage.get("identity_stabilization", 0.0),
                    drift * 0.55,
                )
                * taper
            ),
            "COGNITIVE_ANTI_INFLAMMATORY": clamp(
                max(
                    physician_dosage.get("cognitive_immunology", 0.0),
                    metrics.get("latent_conflict_density", 0.0) * 0.45
                    + metrics.get("semantic_instability", 0.0) * 0.25,
                )
                * taper
            ),
            "TRAUMA_RECOVERY_AGENT": clamp(
                physician_dosage.get("trauma_recovery", 0.0)
                * taper
            ),
            "RECURSIVE_REGULATOR": clamp(
                recursion * 0.65
                * taper
            ),
            "ONTOLOGY_DETOX_AGENT": clamp(
                physician_dosage.get("ontological_detox", 0.0)
                * taper
            ),
            "MEMORY_REPAIR_AGENT": clamp(
                memory * 0.42
                * taper
            ),
            "TOPOLOGY_STABILIZER": clamp(
                topology_stress * 0.56
                * taper
            ),
            "COGNITIVE_SLEEP_AGENT": clamp(
                physician_dosage.get("sleep_cycle", 0.0)
                * taper
            ),
            "EXPLORATION_BALANCER": clamp(
                dependency * 0.50
                +
                physician_report.get(
                    "dependency_alerts",
                    {},
                ).get(
                    "dependency_risk",
                    0.0,
                )
                * 0.30
            ),
        }
