# ============================================
# NEXRYN CONSTITUTIONAL TRAIT PROTECTION
# ============================================

# Block extinction of core stability traits
# Prevents asymmetric cognitive evolution

def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum
    return round(
        max(minimum, min(value, maximum)), 4
    )


# Constitutional traits that CANNOT go extinct
UNEXTINGUISHABLE_TRAITS = [
    "TRUTH_PRIORITY",
    "IDENTITY_CONTINUITY_INSTINCT",
    "CONSTITUTIONAL_STABILITY",
    "TOPOLOGY_LOYALTY",
    "INVARIANT_RESPECT",
    "ADAPTIVE_RESTRAINT",
    "SEMANTIC_PATIENCE",
    "PRESERVATION_INSTINCT",
    "CONTINUITY_AFFINITY",
    "ANTI_EXTREMISM_BIAS",
]


class ConstitutionalTraitProtection:
    """
    Ensures core constitutional traits cannot be
    driven to extinction by natural selection pressure.
    
    Prevents asymmetric evolution where NEXRYN
    chooses novelty over structural stability.
    """

    def __init__(self):
        self.protected_trait_minimum_fitness = 0.35
        self.protection_history = []

    def is_constitutional(self, trait_name):
        """Check if trait is constitutionally protected."""
        return trait_name in UNEXTINGUISHABLE_TRAITS

    def protect_trait_from_extinction(self, trait):
        """
        Prevent extinction of constitutional traits.
        
        If a constitutional trait would be marked extinct,
        restore it to decaying state instead with 
        minimum fitness preservation.
        """

        trait_name = trait.get("trait_name", "")

        if not self.is_constitutional(trait_name):
            return trait

        current_state = trait.get("trait_state", "")

        # If about to go extinct, stop it
        if current_state == "extinct":
            
            trait["trait_state"] = "decaying"
            
            trait["fitness"] = max(
                trait.get("fitness", 0.0),
                self.protected_trait_minimum_fitness,
            )

            trait["stability_score"] = min(
                1.0,
                trait.get("stability_score", 0.5) + 0.15,
            )

            trait["mutation_resistance"] = min(
                1.0,
                trait.get("mutation_resistance", 0.0) + 0.25,
            )

            self.protection_history.append(
                {
                    "trait": trait_name,
                    "action": "prevented_extinction",
                    "restored_to": "decaying",
                    "fitness_floor": self.protected_trait_minimum_fitness,
                }
            )

        return trait

    def enforce_asymmetry_constraints(self, selected_traits, extinct_traits):
        """
        Prevent asymmetric evolution where the system
        over-optimizes for novelty at the expense of stability.
        
        Returns:
        - protected_selected: traits that must stay selected
        - reprotected_extinct: traits restored from extinction
        """

        protected_selected = []
        reprotected_extinct = []

        # Ensure critical traits stay in selection
        for trait_name in UNEXTINGUISHABLE_TRAITS:
            
            found_in_selected = any(
                t.get("trait_name") == trait_name
                for t in selected_traits
            )

            if not found_in_selected:
                
                # Check if it's been driven to extinction
                extinct = next(
                    (
                        t
                        for t in extinct_traits
                        if t.get("trait_name") == trait_name
                    ),
                    None,
                )

                if extinct:
                    
                    # Resurrect it
                    rescued = extinct.copy()
                    rescued["trait_state"] = "adaptive"
                    rescued["fitness"] = max(
                        0.50, rescued.get("fitness", 0.35)
                    )
                    rescued["mutation_resistance"] = min(
                        1.0,
                        rescued.get("mutation_resistance", 0.0) + 0.30,
                    )

                    protected_selected.append(rescued)
                    reprotected_extinct.append(trait_name)

                    self.protection_history.append(
                        {
                            "trait": trait_name,
                            "action": "resurrected_from_extinction",
                            "restored_state": "adaptive",
                            "min_fitness": 0.50,
                        }
                    )

        return {
            "protected_traits_injected": protected_selected,
            "reprotected_from_extinction": reprotected_extinct,
            "asymmetry_constraint_enforced": len(
                reprotected_extinct
            )
            > 0,
        }

    def monitor_selection_imbalance(self, context):
        """
        Monitor if natural selection is becoming asymmetrically
        biased toward novelty, abstraction, and mutation_potential
        at the expense of preservation traits.
        
        Returns threat assessment.
        """

        natural_selection = context.get(
            "cognitive_natural_selection_report", {}
        )

        selected = natural_selection.get("selected_traits", [])

        # Extract trait names and their fitness
        trait_fitness_map = {
            t.get("trait_name"): t.get("fitness", 0.0)
            for t in selected
        }

        # Measure preservation traits
        preservation_traits = [
            "TOPOLOGY_LOYALTY",
            "INVARIANT_RESPECT",
            "ADAPTIVE_RESTRAINT",
            "SEMANTIC_PATIENCE",
            "PRESERVATION_INSTINCT",
            "IDENTITY_CONTINUITY_INSTINCT",
        ]

        # Measure novelty traits
        novelty_traits = [
            "abstraction",
            "mutation_potential",
            "adaptive_discovery",
            "novel_synthesis",
        ]

        preservation_fitness = sum(
            trait_fitness_map.get(t, 0.0)
            for t in preservation_traits
        ) / max(len(preservation_traits), 1)

        novelty_fitness = sum(
            t_fit
            for t_name, t_fit in trait_fitness_map.items()
            if any(nov in str(t_name).lower() for nov in novelty_traits)
        ) / max(
            len(
                [
                    t
                    for t in trait_fitness_map.keys()
                    if any(
                        nov in str(t).lower() for nov in novelty_traits
                    )
                ]
            ),
            1,
        )

        imbalance = _clamp(
            (novelty_fitness - preservation_fitness) / 2.0
        )

        return {
            "system": "asymmetry_monitor",
            "preservation_fitness_avg": round(preservation_fitness, 4),
            "novelty_fitness_avg": round(novelty_fitness, 4),
            "evolution_imbalance": round(imbalance, 4),
            "asymmetry_threat": imbalance > 0.20,
            "threat_level": (
                "critical"
                if imbalance > 0.30
                else "high"
                if imbalance > 0.20
                else "normal"
            ),
        }

    def enforce_temperament_homeostasis(self, traits, context):
        """
        Ensure constitutional traits maintain homeostatic balance.
        
        Prevents the system from becoming too novelty-driven
        and neglecting structural stability.
        """

        # Identify weakened stability traits
        stability_traits = {
            "TOPOLOGY_LOYALTY": 0.95,
            "INVARIANT_RESPECT": 0.96,
            "ADAPTIVE_RESTRAINT": 0.91,
            "SEMANTIC_PATIENCE": 0.90,
            "PRESERVATION_INSTINCT": 0.86,
            "CONTINUITY_AFFINITY": 0.94,
            "ANTI_EXTREMISM_BIAS": 0.93,
        }

        reinforcements = []

        for trait in traits:
            
            trait_name = trait.get("trait_name", "")
            
            if trait_name not in stability_traits:
                continue

            target_priority = stability_traits[trait_name]
            current_adaptive_weight = trait.get(
                "adaptive_weight", 0.0
            )

            # If priority has drifted down, reinforce
            if current_adaptive_weight < target_priority * 0.90:
                
                trait["adaptive_weight"] = min(
                    1.0,
                    target_priority,
                )

                trait["stability_score"] = min(
                    1.0,
                    trait.get("stability_score", 0.0) + 0.08,
                )

                trait["mutation_resistance"] = min(
                    1.0,
                    trait.get("mutation_resistance", 0.0) + 0.15,
                )

                reinforcements.append(
                    {
                        "trait": trait_name,
                        "restored_priority": target_priority,
                        "stability_boost": 0.08,
                    }
                )

        return {
            "system": "temperament_homeostasis",
            "homeostatic_reinforcements": reinforcements,
            "stabilization_active": len(reinforcements) > 0,
        }

    def report(self):
        """Generate protection activity report."""
        
        recent_protections = self.protection_history[-20:]

        protection_count = len(
            [
                p
                for p in recent_protections
                if p.get("action") == "prevented_extinction"
            ]
        )

        resurrection_count = len(
            [
                p
                for p in recent_protections
                if p.get("action") == "resurrected_from_extinction"
            ]
        )

        return {
            "system": "constitutional_trait_protection",
            "unextinguishable_traits": len(UNEXTINGUISHABLE_TRAITS),
            "recent_protections": len(recent_protections),
            "extinctions_prevented": protection_count,
            "traits_resurrected": resurrection_count,
            "protection_active": len(recent_protections) > 0,
            "protected_trait_list": UNEXTINGUISHABLE_TRAITS,
            "minimum_fitness_floor": self.protected_trait_minimum_fitness,
            "recent_history": recent_protections[-5:],
        }


constitutional_trait_protection = ConstitutionalTraitProtection()

__all__ = [
    "ConstitutionalTraitProtection",
    "constitutional_trait_protection",
    "UNEXTINGUISHABLE_TRAITS",
]
