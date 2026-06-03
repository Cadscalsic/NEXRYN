from core.existential_pressure.pressure_accumulation_engine import (
    PressureAccumulationEngine,
)
from core.existential_pressure.ontological_stress_monitor import (
    OntologicalStressMonitor,
)
from core.existential_pressure.semantic_fatigue_cycles import (
    SemanticFatigueCycles,
)
from core.existential_pressure.adaptive_self_damping import (
    AdaptiveSelfDamping,
)
from core.existential_pressure.cognitive_pressure_release import (
    CognitivePressureRelease,
)
from core.existential_pressure.merge_pressure_balancer import (
    MergePressureBalancer,
)
from core.existential_pressure.drift_absorption_engine import (
    DriftAbsorptionEngine,
)
from core.existential_pressure.resonance_stability_control import (
    ResonanceStabilityControl,
)
from core.existential_pressure.identity_strain_regulator import (
    IdentityStrainRegulator,
)
from core.existential_pressure.ontological_tension_homeostasis import (
    OntologicalTensionHomeostasis,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ExistentialPressureManagementLayer:

    def __init__(self):

        self.pressure_accumulation_engine = PressureAccumulationEngine()
        self.ontological_stress_monitor = OntologicalStressMonitor()
        self.semantic_fatigue_cycles = SemanticFatigueCycles()
        self.adaptive_self_damping = AdaptiveSelfDamping()
        self.cognitive_pressure_release = CognitivePressureRelease()
        self.merge_pressure_balancer = MergePressureBalancer()
        self.drift_absorption_engine = DriftAbsorptionEngine()
        self.resonance_stability_control = ResonanceStabilityControl()
        self.identity_strain_regulator = IdentityStrainRegulator()
        self.ontological_tension_homeostasis = OntologicalTensionHomeostasis()
        self.pressure_history = []

    def run_cycle(self, context):

        if not isinstance(context, dict):

            context = {}

        accumulation = self.pressure_accumulation_engine.accumulate(context)
        stress = self.ontological_stress_monitor.monitor(context, accumulation)
        fatigue = self.semantic_fatigue_cycles.compute(context, stress)
        damping = self.adaptive_self_damping.damp(
            accumulation,
            stress,
            fatigue,
        )
        release = self.cognitive_pressure_release.release(damping, fatigue)
        merge = self.merge_pressure_balancer.balance(context)
        absorption = self.drift_absorption_engine.absorb(context, fatigue)
        resonance = self.resonance_stability_control.control(
            accumulation,
            fatigue,
            merge,
        )
        strain = self.identity_strain_regulator.regulate(context, stress)
        tension = self.ontological_tension_homeostasis.balance([
            damping,
            release,
            merge,
            absorption,
            resonance,
            strain,
        ])

        managed_pressure = _clamp(
            accumulation.get("accumulated_pressure", 0.0)
            -
            damping.get("damping_strength", 0.0) * 0.22
            -
            (
                0.10
                if release.get("release_actions", [])
                else 0.0
            )
        )

        policy = {
            "activate_self_damping":
            bool(damping.get("damping_actions", [])),

            "release_cognitive_pressure":
            bool(release.get("release_actions", [])),

            "throttle_identity_sensitive_merges":
            bool(merge.get("merge_actions", [])),

            "absorb_semantic_drift":
            bool(absorption.get("absorption_actions", [])),

            "stabilize_resonance":
            bool(resonance.get("resonance_actions", [])),

            "regulate_identity_strain":
            bool(strain.get("strain_actions", [])),
        }

        report = {
            "system": "existential_pressure_management",
            "layer": "existential_pressure_management_layer",
            "pressure_accumulation": accumulation,
            "ontological_stress": stress,
            "semantic_fatigue_cycles": fatigue,
            "adaptive_self_damping": damping,
            "cognitive_pressure_release": release,
            "merge_pressure_balancer": merge,
            "drift_absorption": absorption,
            "resonance_stability_control": resonance,
            "identity_strain_regulator": strain,
            "ontological_tension_homeostasis": tension,
            "managed_pressure": managed_pressure,
            "pressure_policy": policy,
            "pressure_management_state": (
                "existential_pressure_management_active"
                if any(policy.values())
                else "existential_pressure_managed"
            ),
        }

        self.pressure_history.append(report)
        self.pressure_history = self.pressure_history[-128:]

        return report


existential_pressure_management = ExistentialPressureManagementLayer()


__all__ = [
    "AdaptiveSelfDamping",
    "CognitivePressureRelease",
    "DriftAbsorptionEngine",
    "ExistentialPressureManagementLayer",
    "IdentityStrainRegulator",
    "MergePressureBalancer",
    "OntologicalStressMonitor",
    "OntologicalTensionHomeostasis",
    "PressureAccumulationEngine",
    "ResonanceStabilityControl",
    "SemanticFatigueCycles",
    "existential_pressure_management",
]
