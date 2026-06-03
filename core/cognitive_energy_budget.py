"""
Cognitive Energy Budget: Tracks and enforces energy consumption limits for concepts.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class EnergyAllocation:
    """Energy budget for a single concept."""
    concept_id: str
    total_energy: float  # Total energy allocated
    consumed_energy: float = 0.0  # Energy used so far
    storage_used: float = 0.0  # Memory/storage consumed
    allocated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def remaining_energy(self) -> float:
        """Compute remaining energy."""
        return max(0.0, self.total_energy - self.consumed_energy)

    @property
    def energy_utilization_rate(self) -> float:
        """Return utilization as percentage (0-1)."""
        if self.total_energy == 0:
            return 0.0
        return self.consumed_energy / self.total_energy


class CognitiveEnergyBudget:
    """
    Manages energy and storage budgets for all concepts.
    Concepts that exceed budget or prove low-utility face extinction.
    """

    def __init__(self, total_system_energy: float = 1000.0, total_storage: float = 500.0):
        self._total_system_energy = total_system_energy
        self._total_storage = total_storage
        self._allocations: Dict[str, EnergyAllocation] = {}
        self._extinct_concepts: list[str] = []

    def allocate_budget(
        self, concept_id: str, initial_energy: float = 10.0, storage: float = 1.0
    ) -> EnergyAllocation:
        """Allocate energy budget for a new concept."""
        if concept_id in self._allocations:
            return self._allocations[concept_id]

        allocation = EnergyAllocation(
            concept_id=concept_id,
            total_energy=initial_energy,
            storage_used=storage,
        )
        self._allocations[concept_id] = allocation
        return allocation

    def consume_energy(self, concept_id: str, amount: float) -> bool:
        """
        Attempt to consume energy.
        Returns True if successful, False if budget exceeded.
        """
        if concept_id not in self._allocations:
            return False

        allocation = self._allocations[concept_id]
        if allocation.remaining_energy < amount:
            return False

        allocation.consumed_energy += amount
        return True

    def get_allocation(self, concept_id: str) -> Optional[EnergyAllocation]:
        """Get budget allocation for a concept."""
        return self._allocations.get(concept_id)

    def evaluate_extinction(self, concept_id: str, reputation: float) -> bool:
        """
        Determine if a concept should face extinction.
        Returns True if extinction should occur.
        """
        if concept_id not in self._allocations:
            return False

        allocation = self._allocations[concept_id]

        # Extinct if energy depleted
        if allocation.remaining_energy <= 0:
            return True

        # Extinct if low reputation AND high energy consumption
        if reputation < 0.3 and allocation.energy_utilization_rate > 0.8:
            return True

        return False

    def mark_extinct(self, concept_id: str) -> None:
        """Mark a concept as extinct (freed from budget tracking)."""
        if concept_id in self._allocations:
            self._extinct_concepts.append(concept_id)

    def reclaim_energy(self, concept_id: str) -> float:
        """Reclaim unused energy from an extinct concept."""
        allocation = self._allocations.get(concept_id)
        if not allocation:
            return 0.0

        reclaimed = allocation.remaining_energy
        allocation.consumed_energy = allocation.total_energy  # Mark as fully used
        return reclaimed

    def boost_allocation(self, concept_id: str, energy_boost: float) -> bool:
        """Reward a high-performing concept with more energy."""
        if concept_id not in self._allocations:
            return False

        self._allocations[concept_id].total_energy += energy_boost
        return True

    def get_system_utilization(self) -> Dict[str, Any]:
        """Return overall system energy/storage utilization."""
        total_consumed = sum(
            a.consumed_energy for a in self._allocations.values()
        )
        total_storage_used = sum(
            a.storage_used for a in self._allocations.values()
        )
        return {
            "total_system_energy": self._total_system_energy,
            "total_consumed_energy": total_consumed,
            "energy_utilization_rate": total_consumed / self._total_system_energy
            if self._total_system_energy > 0
            else 0.0,
            "total_storage": self._total_storage,
            "storage_used": total_storage_used,
            "storage_utilization_rate": total_storage_used / self._total_storage
            if self._total_storage > 0
            else 0.0,
            "active_concepts": len(self._allocations),
            "extinct_concepts": len(self._extinct_concepts),
        }

    def export_report(self) -> Dict[str, Any]:
        """Export budget engine state."""
        utilization = self.get_system_utilization()
        return {
            "system_energy": utilization,
            "top_energy_consumers": sorted(
                [
                    {"id": cid, "consumed": a.consumed_energy, "utilization": a.energy_utilization_rate}
                    for cid, a in self._allocations.items()
                ],
                key=lambda x: x["consumed"],
                reverse=True,
            )[:10],
        }


__all__ = ["EnergyAllocation", "CognitiveEnergyBudget"]
