from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any


AUTHORITY = {
    "authority": "OBSERVATION_ONLY",
    "behavioral_authority": "NONE",
    "evidence_acceptance_authority": "NONE",
    "selection_authority": "NONE",
    "truth_authority": "NONE",
    "trust_authority": "NONE",
    "graduation_authority": "NONE",
    "execution_authority": "NONE",
}


UNKNOWN = {None, "", "UNKNOWN", "Not Available", "NOT_AVAILABLE"}


class EvidenceSourceIndependenceEngine:
    """Assess evidence source identity without granting truth authority."""

    schema_version = "1.0"
    system_name = "evidence_source_independence_engine"

    def source_identity(self, evidence: Mapping[str, Any]) -> dict[str, Any]:
        item = evidence if isinstance(evidence, Mapping) else {}
        explicit = self._first(
            item,
            "canonical_source_identity",
            "canonical_source_id",
            "source_identity_id",
        )
        if explicit:
            identity_payload = {
                "claim_id": self._value(item, "claim_id"),
                "canonical_source_identity": explicit,
            }
            return self._identity_report(
                item,
                identity_payload,
                state="PROVEN",
                reason="explicit_canonical_source_identity_present",
            )

        producer_operation_id = self._first(
            item,
            "producer_operation_id",
            "source_producer_operation_id",
        )
        producer_component_id = self._first(
            item,
            "producer_component_id",
            "source_producer_id",
        )
        producer_source_type = self._first(
            item,
            "producer_source_type",
            "source_type",
        )
        lineage = self._lineage(item)
        source_family = self._first(
            item,
            "source_family",
            "required_evidence",
            "evidence_type",
        )
        if producer_operation_id and producer_component_id and producer_source_type:
            identity_payload = {
                "claim_id": self._value(item, "claim_id"),
                "producer_component_id": producer_component_id,
                "producer_source_type": producer_source_type,
                "producer_operation_id": producer_operation_id,
                "source_family": source_family,
                "lineage_roots": lineage or ["NO_DECLARED_UPSTREAM_LINEAGE"],
            }
            return self._identity_report(
                item,
                identity_payload,
                state="PROVEN",
                reason="producer_operation_lineage_present",
            )

        partial_fields = {
            "source_run_id": self._first(item, "source_run_id", "run_id"),
            "source_task_id": self._first(
                item,
                "source_task_id",
                "selected_validation_task_id",
                "task_id",
            ),
            "raw_result_id": self._value(item, "raw_result_id"),
            "execution_id": self._value(item, "execution_id"),
        }
        observed = {key: value for key, value in partial_fields.items() if value}
        if observed:
            return self._identity_report(
                item,
                {
                    "claim_id": self._value(item, "claim_id"),
                    "partial_source_fields": observed,
                },
                state="PARTIAL",
                reason="only_weak_or_partial_source_fields_present",
            )
        return self._identity_report(
            item,
            {"claim_id": self._value(item, "claim_id")},
            state="UNKNOWN",
            reason="missing_source_provenance",
        )

    def pairwise_independence(
        self,
        evidence_a: Mapping[str, Any],
        evidence_b: Mapping[str, Any],
    ) -> dict[str, Any]:
        source_a = self.source_identity(evidence_a)
        source_b = self.source_identity(evidence_b)
        reasons = []
        state = "UNKNOWN"
        if self._value(evidence_a, "accepted_evidence_id") and (
            self._value(evidence_a, "accepted_evidence_id")
            == self._value(evidence_b, "accepted_evidence_id")
        ):
            state = "DEPENDENT"
            reasons.append("SAME_EVIDENCE_ARTIFACT")
        elif source_a["source_identity_state"] != "PROVEN" or (
            source_b["source_identity_state"] != "PROVEN"
        ):
            state = "UNKNOWN"
            reasons.append("UNKNOWN_DEPENDENCE")
        elif source_a["canonical_source_id"] == source_b["canonical_source_id"]:
            state = "DEPENDENT"
            reasons.append("SAME_CANONICAL_SOURCE")
        elif set(source_a["lineage_roots"]) & set(source_b["lineage_roots"]):
            state = "DEPENDENT"
            reasons.append("SHARED_CAUSAL_ORIGIN")
        elif self._same(evidence_a, evidence_b, "producer_operation_id"):
            state = "DEPENDENT"
            reasons.append("SAME_PRODUCER_EVENT")
        else:
            state = "INDEPENDENT"
            reasons.append("DISTINCT_PROVEN_SOURCE_LINEAGE")
        return {
            "schema_version": self.schema_version,
            "evidence_A": self._value(evidence_a, "accepted_evidence_id"),
            "evidence_B": self._value(evidence_b, "accepted_evidence_id"),
            "source_A": source_a["canonical_source_id"],
            "source_B": source_b["canonical_source_id"],
            "same_source": source_a["canonical_source_id"] == source_b["canonical_source_id"],
            "shared_lineage": bool(set(source_a["lineage_roots"]) & set(source_b["lineage_roots"])),
            "shared_task": self._same_task(evidence_a, evidence_b),
            "shared_run": self._same(evidence_a, evidence_b, "source_run_id")
            or self._same(evidence_a, evidence_b, "run_id"),
            "shared_producer": self._same(evidence_a, evidence_b, "producer_operation_id"),
            "independence_state": state,
            "reason": reasons,
            "confidence": "HIGH" if state in {"DEPENDENT", "INDEPENDENT"} else "LOW",
            **AUTHORITY,
        }

    def source_coverage(
        self,
        accepted_evidence: Iterable[Mapping[str, Any]],
        *,
        claim_id: str | None = None,
        required_independent_sources: int = 8,
    ) -> dict[str, Any]:
        items = [
            dict(item)
            for item in accepted_evidence
            if isinstance(item, Mapping)
            and (not claim_id or item.get("claim_id") == claim_id)
        ]
        supporting = self._direction_items(items, "SUPPORTING")
        contradicting = self._direction_items(items, "CONTRADICTING")
        supporting_accounting = self._direction_accounting(supporting)
        contradicting_accounting = self._direction_accounting(contradicting)
        unknown = supporting_accounting["unknown_dependence_artifacts"]
        pairwise = self.pairwise_matrix(supporting)
        independent_count = supporting_accounting["independent_source_count"]
        return {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "claim_id": claim_id or next(
                (item.get("claim_id") for item in supporting if item.get("claim_id")),
                "NOT_AVAILABLE",
            ),
            "accepted_evidence_count": len(items),
            "supporting_evidence_count": len(supporting),
            "contradicting_evidence_count": len(contradicting),
            "distinct_evidence_ids": sorted({
                str(item.get("accepted_evidence_id"))
                for item in supporting
                if item.get("accepted_evidence_id")
            }),
            "distinct_task_ids": sorted({
                str(self._first(item, "source_task_id", "selected_validation_task_id", "task_id"))
                for item in supporting
                if self._first(item, "source_task_id", "selected_validation_task_id", "task_id")
            }),
            "distinct_run_ids": sorted({
                str(self._first(item, "source_run_id", "run_id"))
                for item in supporting
                if self._first(item, "source_run_id", "run_id")
            }),
            "distinct_producer_ids": sorted({
                str(self._first(item, "producer_operation_id", "source_producer_operation_id"))
                for item in supporting
                if self._first(item, "producer_operation_id", "source_producer_operation_id")
            }),
            "source_identities": supporting_accounting["source_identities"],
            "contradicting_source_identities": contradicting_accounting[
                "source_identities"
            ],
            "current_proven_independent_source_count": independent_count,
            "proven_independent_supporting_sources": independent_count,
            "proven_independent_contradicting_sources": contradicting_accounting[
                "independent_source_count"
            ],
            "required_independent_source_count": required_independent_sources,
            "additional_independent_sources_required": max(
                required_independent_sources - independent_count,
                0,
            ),
            "unknown_dependence_artifacts": unknown,
            "unknown_source_relation_count": len(unknown),
            "dependent_supporting_sources": supporting_accounting[
                "dependent_source_count"
            ],
            "duplicate_supporting_evidence_count": supporting_accounting[
                "duplicate_evidence_count"
            ],
            "source_relation_components": supporting_accounting[
                "source_relation_components"
            ],
            "pairwise_independence": pairwise,
            "independence_counting_definition": (
                "count independent components of proven supporting source "
                "identities after pairwise dependence collapse; unknown or "
                "partial provenance does not increase count"
            ),
            "realized_independence_assessment": (
                "PROVEN" if supporting and not unknown else "PARTIAL" if supporting else "NOT_PROVEN"
            ),
            **AUTHORITY,
        }

    def marginal_independent_contribution(
        self,
        before_coverage: Mapping[str, Any],
        after_coverage: Mapping[str, Any],
        accepted_evidence_id: str,
    ) -> dict[str, Any]:
        before = before_coverage if isinstance(before_coverage, Mapping) else {}
        after = after_coverage if isinstance(after_coverage, Mapping) else {}
        delta = int(after.get("proven_independent_supporting_sources") or 0) - int(
            before.get("proven_independent_supporting_sources") or 0
        )
        if delta > 0:
            state = "+1_PROVEN_NEW_INDEPENDENT_SOURCE"
            reason = "source_coverage_independent_supporting_count_increased"
        else:
            unknown_ids = {
                str(item.get("accepted_evidence_id"))
                for item in after.get("unknown_dependence_artifacts", [])
                if isinstance(item, Mapping)
            }
            if accepted_evidence_id in unknown_ids:
                state = "0_UNKNOWN_INDEPENDENCE"
                reason = "source_relation_unknown_or_partial"
            else:
                state = "0_ALREADY_REPRESENTED_SOURCE"
                reason = "source_count_unchanged_after_dependence_collapse"
        return {
            "schema_version": self.schema_version,
            "claim_id": after.get("claim_id", before.get("claim_id")),
            "accepted_evidence_id": accepted_evidence_id,
            "contribution_state": state,
            "independent_supporting_source_delta": max(delta, 0),
            "direction": "SUPPORTING",
            "reason": reason,
            **AUTHORITY,
        }

    def pairwise_matrix(
        self,
        accepted_evidence: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]] | dict[str, Any]:
        items = [dict(item) for item in accepted_evidence if isinstance(item, Mapping)]
        if len(items) < 2:
            return {
                "state": "NOT_APPLICABLE_SINGLE_ARTIFACT",
                "evidence_count": len(items),
                **AUTHORITY,
            }
        rows = []
        for left_index, left in enumerate(items):
            for right in items[left_index + 1:]:
                rows.append(self.pairwise_independence(left, right))
        return rows

    def _direction_items(
        self,
        items: Iterable[Mapping[str, Any]],
        direction: str,
    ) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in items
            if str(item.get("evidence_direction", "SUPPORTING")) == direction
        ]

    def _direction_accounting(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        identities = [self.source_identity(item) for item in items]
        proven_indices = [
            index
            for index, identity in enumerate(identities)
            if identity["source_identity_state"] == "PROVEN"
        ]
        unknown = [
            {
                "accepted_evidence_id": item.get("accepted_evidence_id"),
                "source_identity_state": identity["source_identity_state"],
                "reason": identity["source_identity_reason"],
            }
            for item, identity in zip(items, identities)
            if identity["source_identity_state"] != "PROVEN"
        ]
        parent = {index: index for index in proven_indices}

        def find(index: int) -> int:
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        def union(left: int, right: int) -> None:
            root_left = find(left)
            root_right = find(right)
            if root_left != root_right:
                parent[root_right] = root_left

        for left_position, left_index in enumerate(proven_indices):
            for right_index in proven_indices[left_position + 1:]:
                relation = self.pairwise_independence(
                    items[left_index],
                    items[right_index],
                )
                if relation["independence_state"] == "DEPENDENT":
                    union(left_index, right_index)
        components: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for index in proven_indices:
            identity = identities[index]
            components[find(index)].append({
                "accepted_evidence_id": items[index].get("accepted_evidence_id"),
                "canonical_source_id": identity["canonical_source_id"],
                "lineage_roots": identity["lineage_roots"],
            })
        duplicate_count = sum(max(len(rows) - 1, 0) for rows in components.values())
        return {
            "source_identities": sorted({
                identities[index]["canonical_source_id"]
                for index in proven_indices
            }),
            "independent_source_count": len(components),
            "dependent_source_count": duplicate_count,
            "duplicate_evidence_count": max(
                len(items) - len(components) - len(unknown),
                0,
            ),
            "unknown_dependence_artifacts": unknown,
            "source_relation_components": [
                {
                    "component_id": f"independent_source_component_{number}",
                    "members": rows,
                }
                for number, rows in enumerate(
                    sorted(
                        components.values(),
                        key=lambda group: [
                            str(item["accepted_evidence_id"]) for item in group
                        ],
                    ),
                    start=1,
                )
            ],
        }

    def independent_source_potential(
        self,
        task_profile: Mapping[str, Any],
        source_coverage: Mapping[str, Any],
        requirement: Mapping[str, Any],
    ) -> dict[str, Any]:
        profile = task_profile if isinstance(task_profile, Mapping) else {}
        coverage = source_coverage if isinstance(source_coverage, Mapping) else {}
        evidence_type = requirement.get("evidence_type") or requirement.get("required_evidence")
        potential_types = {
            str(item)
            for item in profile.get("evidence_types_potentially_supported", [])
            if item != "UNKNOWN"
        }
        task_family = (
            profile.get("corpus_family")
            or profile.get("classification")
            or "UNKNOWN"
        )
        represented_families = set(coverage.get("represented_source_families") or [])
        if evidence_type not in potential_types:
            state = "UNKNOWN" if not potential_types else "DEPENDENT_SOURCE"
            reason = "task_profile_does_not_support_required_evidence"
        elif task_family in represented_families:
            state = "POSSIBLY_NEW_SOURCE"
            reason = "compatible_task_family_already_represented"
        else:
            state = "POSSIBLY_NEW_SOURCE"
            reason = "compatible_task_may_expose_unrepresented_source_family"
        return {
            "schema_version": self.schema_version,
            "task_id": profile.get("task_id"),
            "required_evidence": evidence_type,
            "source_novelty_state": state,
            "source_family_overlap": task_family in represented_families,
            "known_dependency": "UNKNOWN",
            "potential_independence_is_realized_independence": False,
            "reason": reason,
            **AUTHORITY,
        }

    def source_ontology_map(self) -> list[dict[str, Any]]:
        return [
            self._ontology("source_run_id", "evidence_plan_store / validation", "run provenance for source task", "run scoped", "pre/post evidence", "OBSERVATION_ONLY", False, "weak only"),
            self._ontology("source_task_id", "evidence_plan_store / validation", "origin task identifier", "task scoped", "pre/post evidence", "OBSERVATION_ONLY", False, "weak only"),
            self._ontology("raw_result_id", "validation_task_execution_pipeline", "raw validation result artifact identity", "artifact scoped", "post execution", "OBSERVATION_ONLY", False, "duplicate detection"),
            self._ontology("producer_operation_id", "validation_task_execution_pipeline", "producer event identity", "producer-event scoped", "post execution", "OBSERVATION_ONLY", True, "canonical input"),
            self._ontology("producer_component_id", "validation_task_execution_pipeline", "producer subsystem identity", "component scoped", "post execution", "OBSERVATION_ONLY", True, "canonical input"),
            self._ontology("producer_source_type", "validation_task_execution_pipeline", "producer class", "method scoped", "post execution", "OBSERVATION_ONLY", True, "canonical input"),
            self._ontology("claim_evidence_binding_id", "claim_identity", "claim-to-evidence binding identity", "claim/evidence scoped", "post acceptance", "OBSERVATION_ONLY", False, "binding not source"),
            self._ontology("originating_arena_id", "arena evidence admission", "arena deliberation origin", "arena scoped", "post acceptance", "OBSERVATION_ONLY", False, "lineage context"),
            self._ontology("source", "knowledge replication ledger", "evidence export category", "collector/category scoped", "post execution", "EVIDENCE_ONLY", False, "label not identity"),
            self._ontology("source_identity_id", "evidence_source_independence_engine", "canonical source identity", "claim-relative source scoped", "post evidence", "OBSERVATION_ONLY", True, "counting identity"),
        ]

    def _identity_report(
        self,
        evidence: Mapping[str, Any],
        payload: Mapping[str, Any],
        *,
        state: str,
        reason: str,
    ) -> dict[str, Any]:
        canonical = (
            str(payload.get("canonical_source_identity"))
            if payload.get("canonical_source_identity")
            else "source_identity_"
            + hashlib.sha1(
                json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
            ).hexdigest()[:16]
        )
        return {
            "schema_version": self.schema_version,
            "accepted_evidence_id": evidence.get("accepted_evidence_id"),
            "claim_id": evidence.get("claim_id"),
            "canonical_source_id": canonical,
            "source_identity_state": state,
            "source_identity_reason": reason,
            "source_identity_payload": dict(payload),
            "lineage_roots": self._lineage(evidence),
            **AUTHORITY,
        }

    def _ontology(
        self,
        field: str,
        owner: str,
        meaning: str,
        identity_scope: str,
        lifecycle_scope: str,
        authority: str,
        canonical: bool,
        relevance: str,
    ) -> dict[str, Any]:
        return {
            "source_field": field,
            "owning_subsystem": owner,
            "semantic_meaning": meaning,
            "identity_scope": identity_scope,
            "lifecycle_scope": lifecycle_scope,
            "authority": authority,
            "canonical": canonical,
            "independence_relevance": relevance,
        }

    def _lineage(self, item: Mapping[str, Any]) -> list[str]:
        raw = (
            item.get("source_lineage")
            or item.get("lineage")
            or item.get("upstream_source_ids")
            or item.get("upstream_evidence_ids")
            or []
        )
        if isinstance(raw, str):
            raw = [raw]
        if isinstance(raw, list):
            return sorted(str(value) for value in raw if value not in UNKNOWN)
        return []

    def _same_task(self, left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
        return bool(
            self._first(left, "source_task_id", "selected_validation_task_id", "task_id")
            and self._first(left, "source_task_id", "selected_validation_task_id", "task_id")
            == self._first(right, "source_task_id", "selected_validation_task_id", "task_id")
        )

    def _same(self, left: Mapping[str, Any], right: Mapping[str, Any], key: str) -> bool:
        return bool(self._value(left, key) and self._value(left, key) == self._value(right, key))

    def _first(self, item: Mapping[str, Any], *keys: str) -> Any:
        for key in keys:
            value = self._value(item, key)
            if value:
                return value
        return None

    def _value(self, item: Mapping[str, Any], key: str) -> Any:
        value = item.get(key)
        if value in UNKNOWN:
            return None
        return value


__all__ = ["AUTHORITY", "EvidenceSourceIndependenceEngine"]
