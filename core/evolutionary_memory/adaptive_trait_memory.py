# ============================================
# NEXRYN ADAPTIVE TRAIT MEMORY
# ============================================

from dataclasses import dataclass, field
from datetime import datetime

from core.cognition.mutation_firewall import (
    mutation_firewall,
)


def _clamp(value, minimum=0.0, maximum=1.0):

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


TRAIT_STATES = [
    "emerging",
    "candidate",
    "adaptive",
    "dominant",
    "decaying",
    "suppressed",
    "extinct",
]

MAX_SURVIVAL_HISTORY = 12


@dataclass
class CognitiveTrait:

    id: str
    niche: str = "general_adaptation"
    fitness: float = 0.20
    mutation_rate: float = 0.10
    inheritance_strength: float = 0.20
    stability_score: float = 0.50
    semantic_alignment: float = 0.50
    trait_state: str = "emerging"
    survival_history: list = field(default_factory=list)
    mutation_firewall: object = mutation_firewall

    def observe(self, pattern):

        constructive_score = _clamp(
            pattern.get(
                "constructive_score",
                0.0,
            ),
        )

        identity_continuity = _clamp(
            pattern.get(
                "identity_continuity",
                0.0,
            ),
        )

        if not self.mutation_firewall.allow_rehearsal(
            self.id,
            constructive_score,
            identity_continuity,
        ):

            return

        mutation = pattern.get(
            "mutation",
            {},
        )

        source = mutation.get(
            "source",
            {},
        )

        semantic_alignment = _clamp(
            source.get(
                "causal_alignment",
                mutation.get(
                    "causal_alignment",
                    constructive_score,
                ),
            ),
        )

        self.semantic_alignment = _clamp(
            self.semantic_alignment * 0.68
            +
            semantic_alignment * 0.32
        )

        self.stability_score = _clamp(
            self.stability_score * 0.62
            +
            identity_continuity * 0.28
            +
            (
                1.0
                -
                mutation.get(
                    "predicted_entropy_delta",
                    0.0,
                )
            )
            * 0.10
        )

        self.fitness = _clamp(
            self.fitness * 0.58
            +
            constructive_score * 0.24
            +
            self.stability_score * 0.10
            +
            self.semantic_alignment * 0.08
        )

        self.mutation_rate = _clamp(
            0.04
            +
            (
                1.0 - self.stability_score
            )
            * 0.18
            +
            (
                1.0 - self.semantic_alignment
            )
            * 0.10
        )

        self.inheritance_strength = _clamp(
            self.fitness * 0.46
            +
            self.stability_score * 0.34
            +
            self.semantic_alignment * 0.20
        )

        self.survival_history.append({
            "survival_state":
            pattern.get(
                "survival_state",
                "unknown",
            ),

            "constructive_score":
            constructive_score,

            "identity_continuity":
            identity_continuity,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        })

        self.survival_history = (
            self.survival_history[-MAX_SURVIVAL_HISTORY:]
        )

        self.trait_state = self._classify_state()

    def _classify_state(self):

        observations = len(
            self.survival_history,
        )

        if self.fitness <= 0.08:

            return "extinct"

        if self.fitness < 0.20 and observations >= 2:

            return "suppressed"

        if self.fitness < 0.30 and observations >= 3:

            return "decaying"

        if (
            self.fitness >= 0.74
            and self.inheritance_strength >= 0.68
            and self.stability_score >= 0.66
        ):

            return "dominant"

        if (
            self.fitness >= 0.52
            and self.inheritance_strength >= 0.50
        ):

            return "adaptive"

        if observations:

            return "candidate"

        return "emerging"

    def to_dict(self):

        return {
            "id":
            self.id,

            "trait":
            self.id,

            "niche":
            self.niche,

            "fitness":
            _clamp(
                self.fitness,
            ),

            "mutation_rate":
            _clamp(
                self.mutation_rate,
            ),

            "inheritance_strength":
            _clamp(
                self.inheritance_strength,
            ),

            "stability_score":
            _clamp(
                self.stability_score,
            ),

            "semantic_alignment":
            _clamp(
                self.semantic_alignment,
            ),

            "survival_history":
            self.survival_history[-MAX_SURVIVAL_HISTORY:],

            "observations":
            len(
                self.survival_history,
            ),

            "trait_state":
            self.trait_state,
        }


class AdaptiveTraitMemory:

    def __init__(self):

        self.traits = {}

    def _trait_name(self, mutation):

        source = mutation.get(
            "source",
            {},
        )

        return str(
            source.get(
                "second",
                source.get(
                    "mutation_type",
                    mutation.get(
                        "candidate_type",
                        "unknown_trait",
                    ),
                ),
            )
        )

    def _trait_niche(self, trait):

        if "identity" in trait or "preserve" in trait:

            return "identity_stability"

        if "direction" in trait or "position" in trait:

            return "spatial_causal_reasoning"

        if "symbolic" in trait or "remap" in trait:

            return "semantic_remapping"

        return "general_adaptation"

    def update(self, archive_report):

        updates = []

        for pattern in archive_report.get(
            "archived_patterns",
            [],
        ):

            mutation = pattern.get(
                "mutation",
                {},
            )

            trait = self._trait_name(
                mutation,
            )

            current = self.traits.get(
                trait,
                CognitiveTrait(
                    id=trait,
                    niche=self._trait_niche(
                        trait,
                    ),
                ),
            )

            current.observe(
                pattern,
            )

            self.traits[
                trait
            ] = current

            updates.append(
                current.to_dict(),
            )

        return {
            "system":
            "adaptive_trait_memory",

            "updated_traits":
            updates,

            "trait_count":
            len(
                self.traits,
            ),

            "adaptive_trait_count":
            len([
                item
                for item in self.traits.values()
                if item.to_dict().get(
                    "trait_state",
                )
                in [
                    "adaptive",
                    "dominant",
                ]
            ]),

            "traits":
            [
                trait.to_dict()
                for trait in list(
                    self.traits.values()
                )[-64:]
            ],

            "genome_mode":
            "cognitive_trait_objects",

            "trait_states":
            TRAIT_STATES,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
