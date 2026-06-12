from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set


LIFECYCLE_TRACE = [
    "DISCOVERED",
    "CANDIDATE",
    "STABLE_TRUTH",
    "LOCKED_TRUTH",
    "WEAKENED",
    "EXTINCT",
    "REHABILITATED",
]

ACTIVE_TRUTH_STATES = {
    "STABLE_TRUTH",
    "LOCKED_TRUTH",
    "TRUTH_COMMITTED",
    "ACTIVE_TRUTH",
}

GRAVEYARD_CONFLICT_STATES = {
    "EXTINCT",
    "WEAKENED",
    "REHABILITATION_CANDIDATE",
}


def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _concept_id(item):
    if not isinstance(item, dict):
        return None

    for key in [
        "concept",
        "trait_id",
        "id",
        "name",
        "trait",
        "trait_name",
    ]:
        value = item.get(key)
        if value:
            return str(value)

    trait = item.get("trait_snapshot") or item.get("trait")
    if isinstance(trait, dict):
        return _concept_id(trait)

    return None


def _last_update_cycle(*items):
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in [
            "last_update_cycle",
            "cycle",
            "reviewed_at",
            "updated_at",
            "timestamp",
            "lastSeen",
            "last_seen",
        ]:
            value = item.get(key)
            if value is not None:
                return value
    return None


def _normalize_graveyard_state(item):
    if not isinstance(item, dict):
        return None

    values = []
    for key in [
        "trait_state",
        "state",
        "type",
        "status",
        "reason",
        "rehearsal_state",
        "recovery_status",
    ]:
        value = item.get(key)
        if value is not None:
            values.append(str(value).lower())

    text = " ".join(values)

    if "rehabilitation candidate" in text or "resurrection_candidate" in text:
        return "REHABILITATION_CANDIDATE"
    if "rehabilitated" in text or "probationary_resurrection" in text:
        return "REHABILITATED"
    if "extinct" in text or "dormant archive" in text:
        return "EXTINCT"
    if "weakened" in text or "decaying" in text or "suppressed" in text:
        return "WEAKENED"
    if "rejected" in text or "blocked" in text or "unsafe" in text:
        return "EXTINCT"

    return None


@dataclass
class ConceptState:
    concept: str
    truth_state: str = "UNKNOWN"
    graveyard_state: str = "NONE"
    source_of_truth: str = "none"
    last_update_cycle: Optional[Any] = None
    truth_record: Optional[Dict[str, Any]] = None
    graveyard_record: Optional[Dict[str, Any]] = None
    recovery_record: Optional[Dict[str, Any]] = None


class TruthGraveyardSynchronizer:
    """Audits and reconciles public reports across truth and graveyard state.

    The synchronizer is deliberately non-governing. It does not promote,
    resurrect, or delete concepts. It only keeps runtime reports from exposing
    stale graveyard state as the effective state of an active truth.
    """

    def _truth_items(self, truth_report):
        if not isinstance(truth_report, dict):
            return []

        active = truth_report.get("active_truths", [])
        if active:
            return _as_list(active)

        return _as_list(
            truth_report.get(
                "truths",
                truth_report.get("records", []),
            )
        )

    def _truth_states(self, context):
        truth_report = context.get("truth_registry_report", {})
        concept_report = context.get("concept_lifecycle_report", {})

        states: Dict[str, ConceptState] = {}

        for record in self._truth_items(truth_report):
            concept = _concept_id(record)
            if not concept:
                continue

            status = str(record.get("status", "ACTIVE")).upper()
            reusable = record.get("reusable", True)
            if status == "ACTIVE" and reusable is not False:
                truth_state = "LOCKED_TRUTH" if record.get("locked") else "STABLE_TRUTH"
                source = "truth_registry"
            else:
                truth_state = status
                source = "truth_registry_inactive"

            states[concept] = ConceptState(
                concept=concept,
                truth_state=truth_state,
                source_of_truth=source,
                last_update_cycle=_last_update_cycle(record),
                truth_record=record,
            )

        for record in _as_list(concept_report.get("concepts", [])):
            concept = _concept_id(record)
            if not concept:
                continue

            state = str(record.get("state", record.get("lifecycle_state", "")))
            if not state:
                continue

            current = states.get(concept)
            if current is None:
                states[concept] = ConceptState(
                    concept=concept,
                    truth_state=state,
                    source_of_truth="concept_lifecycle",
                    last_update_cycle=_last_update_cycle(record),
                    truth_record=record,
                )
            elif current.truth_state not in [
                "LOCKED_TRUTH",
                "STABLE_TRUTH",
            ]:
                current.truth_state = state
                current.source_of_truth = "concept_lifecycle"

        return states

    def _graveyard_items(self, context):
        extinction = context.get("extinction_engine_report", {})
        graveyard = context.get("evolutionary_graveyard_report", {})

        items = []

        for key in [
            "extinct_traits",
            "decaying_traits",
            "suppressed_traits",
            "extinction_archive",
            "archived_traits",
        ]:
            for item in _as_list(extinction.get(key, [])):
                if isinstance(item, dict):
                    tagged = dict(item)
                    tagged.setdefault("graveyard_source", "extinction_engine")
                    tagged.setdefault("graveyard_list", key)
                    items.append(tagged)

        for key in [
            "recent_entries",
            "entries",
            "graveyard_entries",
            "extinction_archive",
        ]:
            for item in _as_list(graveyard.get(key, [])):
                if isinstance(item, dict):
                    tagged = dict(item)
                    tagged.setdefault("graveyard_source", "evolutionary_graveyard")
                    tagged.setdefault("graveyard_list", key)
                    items.append(tagged)

        return items

    def _recovery_items(self, context):
        recovery = context.get("trait_recovery_report", {})
        items = []

        for key in [
            "monitored_extinct_traits",
            "resurrection_candidates",
            "recovered_traits",
        ]:
            for item in _as_list(recovery.get(key, [])):
                if isinstance(item, dict):
                    tagged = dict(item)
                    tagged.setdefault("graveyard_source", "trait_recovery_engine")
                    tagged.setdefault("graveyard_list", key)
                    items.append(tagged)

        return items

    def build_audit(self, context):
        if not isinstance(context, dict):
            context = {}

        states = self._truth_states(context)

        for item in self._graveyard_items(context):
            concept = _concept_id(item)
            if not concept:
                continue

            current = states.setdefault(
                concept,
                ConceptState(concept=concept),
            )
            graveyard_state = _normalize_graveyard_state(item)
            if graveyard_state:
                current.graveyard_state = graveyard_state
                current.graveyard_record = item
                current.last_update_cycle = _last_update_cycle(
                    current.truth_record,
                    item,
                )

        for item in self._recovery_items(context):
            concept = _concept_id(item)
            if not concept:
                continue

            current = states.setdefault(
                concept,
                ConceptState(concept=concept),
            )
            recovery_state = _normalize_graveyard_state(item)
            if recovery_state in [
                "REHABILITATION_CANDIDATE",
                "REHABILITATED",
            ]:
                current.recovery_record = item
                if current.graveyard_state == "NONE":
                    current.graveyard_state = recovery_state
                current.last_update_cycle = _last_update_cycle(
                    current.truth_record,
                    current.graveyard_record,
                    item,
                )

        audit_rows = []
        conflicts = []
        stale = []
        resurrection_conflicts = []

        for concept in sorted(states.keys()):
            state = states[concept]
            active_truth = state.truth_state in ACTIVE_TRUTH_STATES
            graveyard_conflict = state.graveyard_state in GRAVEYARD_CONFLICT_STATES
            recovery_conflict = (
                active_truth
                and state.recovery_record is not None
            )

            row = {
                "concept": concept,
                "truth_state": state.truth_state,
                "graveyard_state": state.graveyard_state,
                "source_of_truth": state.source_of_truth,
                "last_update_cycle": state.last_update_cycle,
                "state_conflict": bool(active_truth and graveyard_conflict),
                "stale_graveyard_entry": bool(active_truth and graveyard_conflict),
                "resurrection_conflict": bool(recovery_conflict),
                "lifecycle_trace": list(LIFECYCLE_TRACE),
            }
            audit_rows.append(row)

            if row["state_conflict"]:
                conflicts.append(row)
                stale.append(row)
            if row["resurrection_conflict"]:
                resurrection_conflicts.append(row)

        audited = max(len(audit_rows), 1)
        penalty = (
            len(conflicts)
            +
            len(resurrection_conflicts)
        ) / audited

        return {
            "system": "truth_graveyard_synchronization",
            "mode": "audit_and_report_reconciliation",
            "lifecycle_trace": list(LIFECYCLE_TRACE),
            "truth_graveyard_conflicts": len(conflicts),
            "stale_graveyard_entries": len(stale),
            "resurrection_conflicts": len(resurrection_conflicts),
            "constitutional_consistency_score": _clamp(1.0 - penalty),
            "audit_report": audit_rows,
            "conflicting_concepts": [
                item["concept"]
                for item in conflicts
            ],
            "stale_graveyard_concepts": [
                item["concept"]
                for item in stale
            ],
            "resurrection_conflict_concepts": [
                item["concept"]
                for item in resurrection_conflicts
            ],
            "source_of_truth_policy": "truth_registry_over_graveyard_reporting",
            "auto_resurrection_performed": False,
            "governance_modified": False,
        }

    def _stale_concepts(self, report):
        return set(report.get("stale_graveyard_concepts", []))

    def _filter_items(self, items, stale_concepts: Set[str]):
        kept = []
        stale = []

        for item in _as_list(items):
            concept = _concept_id(item)
            if concept in stale_concepts:
                stale.append(item)
            else:
                kept.append(item)

        return kept, stale

    def synchronize_context_reports(self, context):
        report = self.build_audit(context)
        stale_concepts = self._stale_concepts(report)

        synchronized = dict(context)

        extinction = dict(
            synchronized.get("extinction_engine_report", {})
        )
        if extinction:
            for key in [
                "extinct_traits",
                "extinction_archive",
                "archived_traits",
            ]:
                kept, stale = self._filter_items(
                    extinction.get(key, []),
                    stale_concepts,
                )
                extinction[f"raw_{key}"] = extinction.get(key, [])
                extinction[key] = kept
                if stale:
                    extinction[f"stale_{key}"] = stale

            extinction["extinct_count"] = len(
                extinction.get("extinct_traits", [])
            )
            extinction["truth_graveyard_synchronization"] = report
            synchronized["extinction_engine_report"] = extinction

        graveyard = dict(
            synchronized.get("evolutionary_graveyard_report", {})
        )
        if graveyard:
            for key in [
                "recent_entries",
                "entries",
                "graveyard_entries",
            ]:
                kept, stale = self._filter_items(
                    graveyard.get(key, []),
                    stale_concepts,
                )
                if key in graveyard:
                    graveyard[f"raw_{key}"] = graveyard.get(key, [])
                    graveyard[key] = kept
                if stale:
                    graveyard[f"stale_{key}"] = stale

            graveyard["effective_total_entries"] = len(
                graveyard.get(
                    "recent_entries",
                    graveyard.get("entries", []),
                )
            )
            graveyard["truth_graveyard_synchronization"] = report
            synchronized["evolutionary_graveyard_report"] = graveyard

        recovery = dict(
            synchronized.get("trait_recovery_report", {})
        )
        if recovery:
            for key in [
                "monitored_extinct_traits",
                "resurrection_candidates",
                "recovered_traits",
            ]:
                kept, stale = self._filter_items(
                    recovery.get(key, []),
                    stale_concepts,
                )
                recovery[f"raw_{key}"] = recovery.get(key, [])
                recovery[key] = kept
                if stale:
                    recovery[f"stale_{key}"] = stale

            recovery["monitored_count"] = len(
                recovery.get("monitored_extinct_traits", [])
            )
            recovery["recovered_count"] = len(
                recovery.get("recovered_traits", [])
            )
            recovery["truth_graveyard_synchronization"] = report
            synchronized["trait_recovery_report"] = recovery

        synchronized["truth_graveyard_consistency_report"] = report

        return synchronized

    def run_cycle(self, context):
        return self.build_audit(context)


truth_graveyard_synchronizer = TruthGraveyardSynchronizer()


__all__ = [
    "ACTIVE_TRUTH_STATES",
    "GRAVEYARD_CONFLICT_STATES",
    "LIFECYCLE_TRACE",
    "TruthGraveyardSynchronizer",
    "truth_graveyard_synchronizer",
]
