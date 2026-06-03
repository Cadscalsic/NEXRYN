# ============================================
# NEXRYN LATENT GARBAGE COLLECTOR
# ============================================
# Active optimization worker targeting latent_conflict_memory
# Flushes dead concept mutations and structural signature conflicts

from datetime import datetime
import threading
import time


def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum
    return round(max(minimum, min(value, maximum)), 4)


class LatentGarbageCollector:
    """Scans and neutralizes latent conflicts via automatic structural separation."""

    SCAN_INTERVAL_MS = 500
    NEUTRALIZATION_THRESHOLD_ALIGNMENT = 1.0
    DEAD_CONCEPT_TYPES = [
        "shape_transformation",
        "color_transformation",
        "unused_archetype",
    ]

    def __init__(self, lineage_spool_buffer=None):
        self.latent_conflict_memory = []
        self.lineage_spool_buffer = lineage_spool_buffer
        self.scan_active = False
        self.collector_cycles = 0
        self.neutralized_count = 0
        self.flushed_to_spool = 0
        self.lock = threading.Lock()

    def _identify_dead_concepts(self, conflict_record):
        """Identify dead mutations (shape, color transformations)."""
        concept_type = conflict_record.get("concept_type", "")
        return concept_type in self.DEAD_CONCEPT_TYPES

    def _check_neutralization_candidate(self, conflict_pair):
        """Check if conflict pair meets neutralization criteria."""
        archetype_alignment = _clamp(
            conflict_pair.get("archetype_alignment", 0.0)
        )
        structural_state = conflict_pair.get("structural_state", "")

        return (
            structural_state == "structural_conflict"
            and archetype_alignment >= self.NEUTRALIZATION_THRESHOLD_ALIGNMENT
        )

    def _perform_separation(self, conflict_pair):
        """Execute automatic split_structural_signature_from_meta_concept."""
        return {
            "action": "split_structural_signature_from_meta_concept",
            "source_concept": conflict_pair.get("concept_a"),
            "target_concept": conflict_pair.get("concept_b"),
            "separation_timestamp": str(datetime.utcnow()),
        }

    def neutralize_conflicts(self, latent_conflict_memory):
        """Scan memory and neutralize structural conflicts."""
        with self.lock:
            self.collector_cycles += 1

            if not latent_conflict_memory:
                return {"neutralized": 0, "flushed": 0}

            neutralization_log = []

            for conflict in latent_conflict_memory:
                if not isinstance(conflict, dict):
                    continue

                if self._identify_dead_concepts(conflict):
                    neutralization = self._perform_separation(conflict)
                    neutralization_log.append(neutralization)
                    self.neutralized_count += 1

                    if self.lineage_spool_buffer:
                        lineage_data = {
                            "neutralization_record": neutralization,
                            "original_conflict": conflict,
                        }
                        if self.lineage_spool_buffer.intercept_lineage_write(
                            lineage_data
                        ):
                            self.flushed_to_spool += 1

            return {
                "neutralized": self.neutralized_count,
                "flushed": self.flushed_to_spool,
                "neutralization_log": neutralization_log,
            }

    def run_gc_cycle(self, context):
        """Execute full garbage collection cycle."""
        latent_conflict_memory = context.get("latent_conflict_memory", [])
        latent_conflict_count = len(latent_conflict_memory)

        neutralization_result = self.neutralize_conflicts(latent_conflict_memory)

        reduced_conflict_count = max(
            0, latent_conflict_count - neutralization_result["neutralized"]
        )

        conflict_reduction_ratio = (
            (latent_conflict_count - reduced_conflict_count)
            / float(max(latent_conflict_count, 1))
            if latent_conflict_count > 0
            else 0.0
        )

        return {
            "system": "latent_garbage_collector",
            "gc_cycle_count": self.collector_cycles,
            "initial_conflict_count": latent_conflict_count,
            "neutralized_count": neutralization_result["neutralized"],
            "flushed_to_spool": neutralization_result["flushed"],
            "reduced_conflict_count": reduced_conflict_count,
            "conflict_reduction_ratio": _clamp(conflict_reduction_ratio),
            "neutralization_log": neutralization_result["neutralization_log"],
            "timestamp": str(datetime.utcnow()),
        }

    def report(self):
        """Generate garbage collector status."""
        with self.lock:
            return {
                "system": "latent_garbage_collector",
                "scan_active": self.scan_active,
                "collector_cycles": self.collector_cycles,
                "total_neutralized": self.neutralized_count,
                "total_flushed_to_spool": self.flushed_to_spool,
            }


latent_garbage_collector = LatentGarbageCollector()
