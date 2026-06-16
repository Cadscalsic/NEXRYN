"""Persistent memory for governance-visible runtime contexts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


CONTEXT_STATES = {
    "DISCOVERED",
    "VALIDATED",
    "GOVERNANCE_VISIBLE",
    "STABLE",
    "REVOKED",
}

VALIDATED_STATUSES = {
    "SEMANTICALLY_VALIDATED",
    "STABLE_TRUTH_SUPPORTED",
    "PROCESS_CONTEXT_VALIDATED",
    "PROCESS_CONTEXT_SUPPORTED",
    "VALIDATED",
    "STABLE",
}

DEFAULT_STORAGE_PATH = (
    Path(__file__).resolve().parents[1]
    / "memory"
    / "context_memory.json"
)


class PersistentContextMemory:
    """Persist validated contexts across runtime cycles."""

    system_name = "persistent_context_memory"

    def __init__(self, storage_path: str | Path | None = None):
        self.storage_path = Path(storage_path or DEFAULT_STORAGE_PATH)
        self.contexts: dict[str, dict[str, Any]] = {}
        self.lifecycle_events: list[dict[str, Any]] = []
        self.loaded_contexts: list[str] = []
        self.new_contexts: list[str] = []
        self.revoked_contexts: list[str] = []
        self.missing_contexts: list[str] = []
        self.load_persistent_contexts()

    def register_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        record = self._record_from_context(context)
        if not record["context_id"]:
            return {}

        existing = self.contexts.get(record["context_id"])
        if existing and existing.get("status") == "REVOKED":
            self._event(record["context_id"], "registration_ignored_revoked")
            return dict(existing)

        now = self._now()
        if existing:
            merged = self._merge_records(existing, record, now)
            self.contexts[record["context_id"]] = merged
            self._event(record["context_id"], "observed")
        else:
            self.contexts[record["context_id"]] = record
            self.new_contexts.append(record["context_id"])
            self._event(record["context_id"], "registered")

        self._save()
        return dict(self.contexts[record["context_id"]])

    def register_contexts(
        self,
        contexts: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        registered = []
        observed_ids = set()
        for context in contexts:
            if not isinstance(context, Mapping):
                continue
            record = self.register_context(context)
            if record:
                observed_ids.add(record["context_id"])
                registered.append(record)
        self._mark_cycle_survival(observed_ids)
        self.missing_contexts = sorted(
            context_id
            for context_id, record in self.contexts.items()
            if self._active(record) and context_id not in observed_ids
        )
        self._save()
        return registered

    def load_persistent_contexts(self) -> list[dict[str, Any]]:
        self.contexts = {}
        self.loaded_contexts = []
        if not self.storage_path.exists():
            return []
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        raw_contexts = data.get("contexts", {})
        if not isinstance(raw_contexts, Mapping):
            return []
        for context_id, context in raw_contexts.items():
            if not isinstance(context, Mapping):
                continue
            record = self._record_from_context({
                **dict(context),
                "context_id": context_id,
            })
            self.contexts[record["context_id"]] = record
            if record["status"] != "REVOKED":
                self.loaded_contexts.append(record["context_id"])
        events = data.get("lifecycle_events", [])
        self.lifecycle_events = [
            dict(item) for item in events if isinstance(item, Mapping)
        ]
        return list(self.contexts.values())

    def update_context_observation(self, context_id: str) -> dict[str, Any]:
        context_id = _normalize(context_id)
        record = self.contexts.get(context_id)
        if not record:
            return {}
        now = self._now()
        record["last_observed_at"] = now
        record["observation_count"] = int(record.get("observation_count", 0)) + 1
        self._event(context_id, "observation_updated")
        self._save()
        return dict(record)

    def revoke_context(self, context_id: str) -> dict[str, Any]:
        context_id = _normalize(context_id)
        record = self.contexts.get(context_id)
        if not record:
            return {}
        record["status"] = "REVOKED"
        record["governance_visible"] = False
        self.revoked_contexts.append(context_id)
        self._event(context_id, "revoked")
        self._save()
        return dict(record)

    def get_governance_visible_contexts(self) -> list[dict[str, Any]]:
        return [
            dict(record)
            for record in self.contexts.values()
            if self._active(record)
        ]

    def get_context_lifecycle(self, context_id: str) -> list[dict[str, Any]]:
        context_id = _normalize(context_id)
        return [
            dict(event)
            for event in self.lifecycle_events
            if event.get("context_id") == context_id
        ]

    def metrics(
        self,
        runtime_context_count: int = 0,
        governance_context_count: int | None = None,
    ) -> dict[str, Any]:
        persistent_context_count = len(self.get_governance_visible_contexts())
        governance_context_count = (
            persistent_context_count
            if governance_context_count is None
            else int(governance_context_count or 0)
        )
        runtime_context_count = int(runtime_context_count or 0)
        retention_rate = (
            persistent_context_count / runtime_context_count
            if runtime_context_count
            else 1.0
        )
        context_loss_events = max(
            persistent_context_count - governance_context_count,
            0,
        )
        return {
            "runtime_context_count": runtime_context_count,
            "persistent_context_count": persistent_context_count,
            "governance_context_count": governance_context_count,
            "context_retention_rate": round(retention_rate, 4),
            "context_loss_events": context_loss_events,
        }

    def report(
        self,
        runtime_context_count: int = 0,
        governance_context_count: int | None = None,
    ) -> dict[str, Any]:
        metrics = self.metrics(
            runtime_context_count=runtime_context_count,
            governance_context_count=governance_context_count,
        )
        loaded = sorted(set(self.loaded_contexts))
        new = sorted(set(self.new_contexts))
        revoked = sorted(set(self.revoked_contexts))
        missing = sorted(set(self.missing_contexts))
        return {
            "system": self.system_name,
            **metrics,
            "loaded_contexts": loaded,
            "new_contexts": new,
            "revoked_contexts": revoked,
            "missing_contexts": missing,
            "persistent_context_report": (
                "PERSISTENT CONTEXT REPORT\n"
                f"runtime_context_count = {metrics['runtime_context_count']}\n"
                f"persistent_context_count = {metrics['persistent_context_count']}\n"
                f"governance_context_count = {metrics['governance_context_count']}\n"
                f"context_retention_rate = {metrics['context_retention_rate']}\n"
                f"loaded_contexts = {loaded}\n"
                f"new_contexts = {new}\n"
                f"revoked_contexts = {revoked}\n"
                f"missing_contexts = {missing}\n"
            ),
        }

    def _record_from_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        source = dict(context)
        context_id = _context_id(source)
        semantic_validation = bool(source.get("semantic_validation", False))
        identity_compatible = bool(source.get("identity_compatible", True))
        governance_visible = bool(source.get("governance_visible", False))
        status = self._state(source, semantic_validation, governance_visible)
        first_discovered = source.get("first_discovered_at") or self._now()
        last_observed = source.get("last_observed_at") or first_discovered
        return {
            "context_id": context_id,
            "context_type": str(
                source.get("context_type")
                or source.get("type")
                or "STATIC_CONTEXT"
            ),
            "source_concept": _normalize(
                source.get("source_concept")
                or source.get("concept")
                or source.get("source_context", {}).get("concept")
                if isinstance(source.get("source_context"), Mapping)
                else source.get("source_concept") or source.get("concept")
            ),
            "status": status,
            "confidence": clamp(
                source.get(
                    "confidence",
                    source.get("context_confidence", 0.0),
                )
            ),
            "semantic_validation": semantic_validation,
            "identity_compatible": identity_compatible,
            "governance_visible": governance_visible,
            "first_discovered_at": str(first_discovered),
            "last_observed_at": str(last_observed),
            "observation_count": int(source.get("observation_count", 1) or 1),
            "runtime_cycles_survived": int(
                source.get("runtime_cycles_survived", 0) or 0
            ),
            "source_context": dict(source.get("source_context", source)),
        }

    def _state(
        self,
        source: Mapping[str, Any],
        semantic_validation: bool,
        governance_visible: bool,
    ) -> str:
        explicit = str(source.get("status", "") or "").upper()
        if explicit in CONTEXT_STATES:
            return explicit
        if explicit == "REVOKED":
            return "REVOKED"
        if explicit in {"STABLE_TRUTH_SUPPORTED", "STABLE_TRUTH"}:
            return "STABLE"
        if governance_visible and semantic_validation:
            return "GOVERNANCE_VISIBLE"
        if semantic_validation or explicit in VALIDATED_STATUSES:
            return "VALIDATED"
        return "DISCOVERED"

    def _merge_records(
        self,
        existing: Mapping[str, Any],
        incoming: Mapping[str, Any],
        now: str,
    ) -> dict[str, Any]:
        existing_status = str(existing.get("status", "DISCOVERED"))
        incoming_status = str(incoming.get("status", "DISCOVERED"))
        status = self._stronger_status(existing_status, incoming_status)
        return {
            **dict(existing),
            **dict(incoming),
            "status": status,
            "confidence": max(
                clamp(existing.get("confidence", 0.0)),
                clamp(incoming.get("confidence", 0.0)),
            ),
            "semantic_validation": bool(
                existing.get("semantic_validation")
                or incoming.get("semantic_validation")
            ),
            "identity_compatible": bool(
                existing.get("identity_compatible", True)
                and incoming.get("identity_compatible", True)
            ),
            "governance_visible": bool(
                existing.get("governance_visible")
                or incoming.get("governance_visible")
            ),
            "first_discovered_at": existing.get(
                "first_discovered_at",
                incoming.get("first_discovered_at", now),
            ),
            "last_observed_at": now,
            "observation_count": (
                int(existing.get("observation_count", 0) or 0) + 1
            ),
        }

    def _stronger_status(self, existing: str, incoming: str) -> str:
        order = {
            "DISCOVERED": 0,
            "VALIDATED": 1,
            "GOVERNANCE_VISIBLE": 2,
            "STABLE": 3,
            "REVOKED": 4,
        }
        if existing == "REVOKED":
            return "REVOKED"
        return max([existing, incoming], key=lambda item: order.get(item, 0))

    def _mark_cycle_survival(self, observed_ids: set[str]) -> None:
        for context_id, record in self.contexts.items():
            if not self._active(record) or context_id in observed_ids:
                continue
            record["runtime_cycles_survived"] = (
                int(record.get("runtime_cycles_survived", 0) or 0) + 1
            )
            self._event(context_id, "survived_runtime_cycle")

    def _active(self, record: Mapping[str, Any]) -> bool:
        return bool(
            record.get("status") != "REVOKED"
            and record.get("semantic_validation") is True
            and record.get("governance_visible") is True
        )

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "system": self.system_name,
            "contexts": self.contexts,
            "lifecycle_events": self.lifecycle_events,
        }
        self.storage_path.write_text(
            json.dumps(data, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _event(self, context_id: str, event_type: str) -> None:
        self.lifecycle_events.append({
            "context_id": context_id,
            "event": event_type,
            "timestamp": self._now(),
        })

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


def _context_id(context: Mapping[str, Any]) -> str:
    return _normalize(
        context.get("context_id")
        or context.get("context_name")
        or context.get("canonical_context_name")
        or context.get("process_context")
        or context.get("generated_context")
        or context.get("semantic_context")
        or context.get("context")
    )


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


persistent_context_memory = PersistentContextMemory()


__all__ = [
    "CONTEXT_STATES",
    "PersistentContextMemory",
    "persistent_context_memory",
]
