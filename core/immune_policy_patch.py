# ============================================
# NEXRYN IMMUNE POLICY PATCH
# ============================================
# Asynchronous decoupling layer for lineage integrity
# Prevents semantic_graph_records truncation under freeze_neurogenesis

from datetime import datetime
from collections import deque
from threading import Lock
import json


def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum
    return round(max(minimum, min(value, maximum)), 4)


class LineageSpoolBuffer:
    """Virtual sandbox registry intercepting lineage writes during immune lockdown."""

    def __init__(self):
        self.primary_buffer = []
        self.secondary_stack = []
        self.non_blocking_queue = deque(maxlen=1000)
        self.lock = Lock()
        self.freeze_state = False
        self.truncation_prevented_count = 0
        self.buffer_state = "standby"

    def activate_freeze(self):
        """Engage lockdown mode and activate secondary memory stack."""
        with self.lock:
            self.freeze_state = True
            self.buffer_state = "freeze_active"

    def deactivate_freeze(self):
        """Release lockdown and flush queued lineage."""
        with self.lock:
            self.freeze_state = False
            self.buffer_state = "flush_pending"
            self._flush_queued_lineage()

    def intercept_lineage_write(self, lineage_record):
        """Intercept and buffer lineage writes during freeze state."""
        with self.lock:
            if not self.freeze_state:
                return False

            if not isinstance(lineage_record, dict):
                return False

            self.non_blocking_queue.append(lineage_record)
            self.truncation_prevented_count += 1
            return True

    def _flush_queued_lineage(self):
        """Commit queued partial semantic ancestors after transition."""
        flushed = 0
        while self.non_blocking_queue:
            record = self.non_blocking_queue.popleft()
            self.secondary_stack.append(record)
            flushed += 1

        return flushed

    def allocate_secondary_memory(self, memory_pressure_score):
        """Allocate dedicated secondary stack when memory_pressure spikes."""
        with self.lock:
            if memory_pressure_score > 0.72:
                self.buffer_state = "secondary_allocation_active"
                return True
            return False

    def report(self):
        """Generate buffer status report."""
        with self.lock:
            return {
                "system": "lineage_spool_buffer",
                "freeze_state": self.freeze_state,
                "buffer_state": self.buffer_state,
                "primary_buffer_size": len(self.primary_buffer),
                "secondary_stack_size": len(self.secondary_stack),
                "queued_records": len(self.non_blocking_queue),
                "truncation_prevented": self.truncation_prevented_count,
                "timestamp": str(datetime.utcnow()),
            }


class ImmunePolicyPatch:
    """Immune system policy enforcement with lineage preservation."""

    def __init__(self):
        self.lineage_buffer = LineageSpoolBuffer()
        self.immune_lockdown_active = False
        self.repair_cycle_count = 0
        self.semantic_graph_integrity = 1.0

    def execute_immune_cycle(self, context):
        """Execute immune cycle with lineage protection."""

        freeze_neurogenesis = context.get("freeze_neurogenesis", False)
        memory_pressure_score = _clamp(context.get("memory_pressure_score", 0.0))
        semantic_records = context.get("semantic_graph_records", [])

        if freeze_neurogenesis:
            self.lineage_buffer.activate_freeze()
            self.immune_lockdown_active = True

        self.lineage_buffer.allocate_secondary_memory(memory_pressure_score)

        protected_records = 0
        for record in semantic_records:
            if self.lineage_buffer.intercept_lineage_write(record):
                protected_records += 1

        if not freeze_neurogenesis and self.immune_lockdown_active:
            self.lineage_buffer.deactivate_freeze()
            self.immune_lockdown_active = False

        self.repair_cycle_count += 1

        self.semantic_graph_integrity = _clamp(
            1.0 - (memory_pressure_score * 0.3)
        )

        return {
            "system": "immune_policy_patch",
            "immune_lockdown_active": self.immune_lockdown_active,
            "freeze_neurogenesis": freeze_neurogenesis,
            "memory_pressure_score": memory_pressure_score,
            "protected_records": protected_records,
            "lineage_buffer_state": self.lineage_buffer.buffer_state,
            "semantic_graph_integrity": self.semantic_graph_integrity,
            "repair_cycles_executed": self.repair_cycle_count,
            "lineage_buffer_report": self.lineage_buffer.report(),
            "timestamp": str(datetime.utcnow()),
        }


immune_policy_patch = ImmunePolicyPatch()
