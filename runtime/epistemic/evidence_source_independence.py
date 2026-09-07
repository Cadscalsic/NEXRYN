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

class RealizedEpistemicContributionEngine:
    """Account for accepted-evidence contribution after provenance is realized."""

    schema_version = "1.0"
    system_name = "realized_epistemic_contribution_engine"
    contribution_classes = [
        "NEW_INDEPENDENT_SUPPORT",
        "DEPENDENT_SUPPORT",
        "CONTRADICTORY_INDEPENDENT_EVIDENCE",
        "DUPLICATE_EVIDENCE",
        "UNKNOWN_PROVENANCE",
        "REJECTED_EVIDENCE",
        "NO_EPISTEMIC_EFFECT",
    ]

    def __init__(self, source_engine: EvidenceSourceIndependenceEngine | None = None):
        self.source_engine = source_engine or EvidenceSourceIndependenceEngine()

    def contract(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_owner": self.system_name,
            "required_fields": [
                "claim_id",
                "task_id",
                "source_run_id",
                "accepted_evidence_id",
                "canonical_source_identity",
                "support_direction",
                "source_relation_to_existing_coverage",
                "independent_count_before",
                "independent_count_after",
                "marginal_independent_delta",
                "contradiction_delta",
                "evidence_acceptance_state",
                "provenance_completeness",
                "contribution_class",
            ],
            "contribution_classes": list(self.contribution_classes),
            "accepted_evidence_is_not_independent_contribution": True,
            "task_success_is_not_epistemic_contribution": True,
            "weak_identifier_independence_forbidden": True,
            "predicted_source_potential_is_not_realized_independence": True,
            "realized_provenance_required_for_independent_credit": True,
            "grants_selection": False,
            "grants_execution": False,
            "grants_evidence": False,
            "grants_truth": False,
            "grants_independence": False,
            **AUTHORITY,
            "authority": "NONE",
        }

    def assess_event(
        self,
        existing_accepted_evidence: Iterable[Mapping[str, Any]],
        evidence_event: Mapping[str, Any],
        *,
        claim_id: str | None = None,
        selection_context: Mapping[str, Any] | None = None,
        required_independent_sources: int = 8,
    ) -> dict[str, Any]:
        before_items = [
            dict(item)
            for item in existing_accepted_evidence
            if isinstance(item, Mapping)
        ]
        event = dict(evidence_event) if isinstance(evidence_event, Mapping) else {}
        effective_claim_id = str(
            claim_id
            or event.get("claim_id")
            or next(
                (
                    item.get("claim_id")
                    for item in before_items
                    if item.get("claim_id")
                ),
                "NOT_AVAILABLE",
            )
        )
        before_coverage = self.source_engine.source_coverage(
            before_items,
            claim_id=effective_claim_id,
            required_independent_sources=required_independent_sources,
        )
        accepted = self._is_accepted(event)
        after_items = before_items + [event] if accepted else before_items
        after_coverage = self.source_engine.source_coverage(
            after_items,
            claim_id=effective_claim_id,
            required_independent_sources=required_independent_sources,
        )
        identity = self.source_engine.source_identity(event)
        relation = self._relation_to_existing(
            before_items,
            event,
            effective_claim_id,
            accepted=accepted,
            identity=identity,
        )
        before_count = int(
            before_coverage.get("proven_independent_supporting_sources") or 0
        )
        after_count = int(
            after_coverage.get("proven_independent_supporting_sources") or 0
        )
        contradiction_before = int(
            before_coverage.get("proven_independent_contradicting_sources") or 0
        )
        contradiction_after = int(
            after_coverage.get("proven_independent_contradicting_sources") or 0
        )
        marginal_delta = max(after_count - before_count, 0)
        contradiction_delta = max(contradiction_after - contradiction_before, 0)
        contribution_class = self._contribution_class(
            accepted=accepted,
            evidence_event=event,
            identity=identity,
            relation=relation,
            marginal_delta=marginal_delta,
            contradiction_delta=contradiction_delta,
        )
        result = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "claim_id": effective_claim_id,
            "task_id": self._first(
                event,
                "source_task_id",
                "selected_validation_task_id",
                "task_id",
            ),
            "source_run_id": self._first(event, "source_run_id", "run_id"),
            "accepted_evidence_id": event.get("accepted_evidence_id"),
            "canonical_source_identity": (
                identity["canonical_source_id"]
                if identity.get("source_identity_state") == "PROVEN"
                else "UNKNOWN"
            ),
            "support_direction": event.get("evidence_direction", "SUPPORTING"),
            "source_relation_to_existing_coverage": relation,
            "independent_count_before": before_count,
            "independent_count_after": after_count,
            "marginal_independent_delta": marginal_delta,
            "contradiction_delta": contradiction_delta,
            "evidence_acceptance_state": event.get(
                "evidence_acceptance_state",
                "UNKNOWN",
            ),
            "provenance_completeness": identity.get("source_identity_state"),
            "contribution_class": contribution_class,
            "before_source_coverage": before_coverage,
            "after_source_coverage": after_coverage,
            "grants_selection": False,
            "grants_execution": False,
            "grants_evidence": False,
            "grants_truth": False,
            "grants_independence": False,
            **AUTHORITY,
            "authority": "NONE",
        }
        if selection_context:
            result["selection_context_binding"] = (
                self._selection_context_binding(selection_context, result)
            )
        return result

    def before_after_trace(
        self,
        existing_accepted_evidence: Iterable[Mapping[str, Any]],
        evidence_event: Mapping[str, Any],
        *,
        claim_id: str | None = None,
        selection_context: Mapping[str, Any] | None = None,
        required_independent_sources: int = 8,
    ) -> dict[str, Any]:
        contribution = self.assess_event(
            existing_accepted_evidence,
            evidence_event,
            claim_id=claim_id,
            selection_context=selection_context,
            required_independent_sources=required_independent_sources,
        )
        return {
            "schema_version": self.schema_version,
            "system": "realized_epistemic_contribution_before_after_trace",
            "claim_id": contribution["claim_id"],
            "accepted_evidence_event": {
                "accepted_evidence_id": contribution["accepted_evidence_id"],
                "evidence_acceptance_state": contribution[
                    "evidence_acceptance_state"
                ],
                "canonical_source_identity": contribution[
                    "canonical_source_identity"
                ],
                "support_direction": contribution["support_direction"],
            },
            "source_coverage_before": contribution["before_source_coverage"],
            "source_coverage_after": contribution["after_source_coverage"],
            "delta_verified": (
                contribution["independent_count_after"]
                - contribution["independent_count_before"]
                == contribution["marginal_independent_delta"]
            ),
            "realized_epistemic_contribution": contribution,
            **AUTHORITY,
            "authority": "NONE",
        }

    def batch_report(
        self,
        events: Iterable[Mapping[str, Any]],
        *,
        claim_id: str | None = None,
        selection_context_by_evidence_id: Mapping[str, Mapping[str, Any]] | None = None,
        initial_accepted_evidence: Iterable[Mapping[str, Any]] | None = None,
        required_independent_sources: int = 8,
    ) -> dict[str, Any]:
        accepted_so_far = [
            dict(item)
            for item in (initial_accepted_evidence or [])
            if isinstance(item, Mapping)
        ]
        selection_context_by_evidence_id = selection_context_by_evidence_id or {}
        contributions = []
        for event in events:
            if not isinstance(event, Mapping):
                continue
            evidence_id = str(event.get("accepted_evidence_id") or "")
            contribution = self.assess_event(
                accepted_so_far,
                event,
                claim_id=claim_id,
                selection_context=selection_context_by_evidence_id.get(evidence_id),
                required_independent_sources=required_independent_sources,
            )
            contributions.append(contribution)
            if self._is_accepted(event):
                accepted_so_far.append(dict(event))
        metrics = self.quality_metrics(contributions)
        return {
            "schema_version": self.schema_version,
            "system": "realized_epistemic_contribution_batch_report",
            "claim_id": claim_id or (
                contributions[0]["claim_id"] if contributions else "NOT_AVAILABLE"
            ),
            "realized_contributions": contributions,
            "prediction_vs_realization": self.prediction_vs_realization_table(
                contributions
            ),
            "quality_metrics": metrics,
            "decision_gate": self._decision_gate(contributions),
            **AUTHORITY,
            "authority": "NONE",
        }

    def quality_metrics(
        self,
        contributions: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        rows = [
            dict(item)
            for item in contributions
            if isinstance(item, Mapping)
        ]
        accepted = [
            row for row in rows if self._is_accepted(row)
        ]
        independent = [
            row for row in accepted
            if row.get("contribution_class") == "NEW_INDEPENDENT_SUPPORT"
        ]
        dependent = [
            row for row in accepted
            if row.get("contribution_class") == "DEPENDENT_SUPPORT"
        ]
        contradictions = [
            row for row in accepted
            if row.get("contribution_class")
            == "CONTRADICTORY_INDEPENDENT_EVIDENCE"
        ]
        unknown = [
            row for row in accepted
            if row.get("contribution_class") == "UNKNOWN_PROVENANCE"
        ]
        return {
            "accepted_evidence_count": len(accepted),
            "independent_contribution_count": len(independent),
            "dependent_support_count": len(dependent),
            "contradiction_count": len(contradictions),
            "unknown_provenance_count": len(unknown),
            "independent_yield": (
                len(independent) / len(accepted) if accepted else "UNAVAILABLE"
            ),
            **AUTHORITY,
            "authority": "NONE",
        }

    def prediction_vs_realization_table(
        self,
        contributions: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        rows = []
        for contribution in contributions:
            if not isinstance(contribution, Mapping):
                continue
            binding = contribution.get("selection_context_binding") or {}
            predicted = binding.get("predicted_source_potential", "UNKNOWN")
            realized = contribution.get("contribution_class")
            rows.append({
                "accepted_evidence_id": contribution.get("accepted_evidence_id"),
                "task_id": contribution.get("task_id"),
                "predicted_source_potential": predicted,
                "realized_contribution_class": realized,
                "classification": self._prediction_class(predicted, realized),
                "authority": "NONE",
                "grants_selection": False,
                "grants_truth": False,
                "grants_independence": False,
            })
        return rows

    def _selection_context_binding(
        self,
        selection_context: Mapping[str, Any],
        contribution: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "operational_rank_at_selection": selection_context.get(
                "operational_rank_at_selection",
                selection_context.get("operational_rank"),
            ),
            "evidence_compatibility_at_selection": selection_context.get(
                "evidence_compatibility_at_selection",
                selection_context.get("evidence_compatibility"),
            ),
            "expected_source_descriptor": selection_context.get(
                "expected_source_descriptor",
                {},
            ),
            "predicted_source_potential": selection_context.get(
                "predicted_source_potential",
                selection_context.get("source_potential", "UNKNOWN"),
            ),
            "realized_source_relation": contribution.get(
                "source_relation_to_existing_coverage"
            ),
            "realized_epistemic_delta": contribution.get(
                "marginal_independent_delta"
            ),
            "authority": "NONE",
            "grants_selection": False,
            "grants_truth": False,
            "grants_independence": False,
        }

    def _relation_to_existing(
        self,
        existing: list[dict[str, Any]],
        event: Mapping[str, Any],
        claim_id: str,
        *,
        accepted: bool,
        identity: Mapping[str, Any],
    ) -> str:
        if not accepted:
            return "NOT_APPLICABLE_REJECTED_EVIDENCE"
        if identity.get("source_identity_state") != "PROVEN":
            return "UNKNOWN_PROVENANCE"
        same_claim = [item for item in existing if item.get("claim_id") == claim_id]
        if any(
            item.get("accepted_evidence_id") == event.get("accepted_evidence_id")
            for item in same_claim
        ):
            return "DUPLICATE_EVIDENCE_ARTIFACT"
        if not same_claim:
            return "NO_EXISTING_COVERAGE"
        states = [
            self.source_engine.pairwise_independence(item, event)[
                "independence_state"
            ]
            for item in same_claim
        ]
        if "DEPENDENT" in states:
            return "DEPENDENT_ON_EXISTING_COVERAGE"
        if states and all(state == "INDEPENDENT" for state in states):
            return "INDEPENDENT_OF_EXISTING_COVERAGE"
        return "UNKNOWN_PROVENANCE"

    def _contribution_class(
        self,
        *,
        accepted: bool,
        evidence_event: Mapping[str, Any],
        identity: Mapping[str, Any],
        relation: str,
        marginal_delta: int,
        contradiction_delta: int,
    ) -> str:
        if not accepted:
            return "REJECTED_EVIDENCE"
        if identity.get("source_identity_state") != "PROVEN":
            return "UNKNOWN_PROVENANCE"
        if relation == "DUPLICATE_EVIDENCE_ARTIFACT":
            return "DUPLICATE_EVIDENCE"
        direction = str(evidence_event.get("evidence_direction", "SUPPORTING"))
        if direction == "CONTRADICTING" and contradiction_delta > 0:
            return "CONTRADICTORY_INDEPENDENT_EVIDENCE"
        if direction == "SUPPORTING" and marginal_delta > 0:
            return "NEW_INDEPENDENT_SUPPORT"
        if direction == "SUPPORTING" and relation == "DEPENDENT_ON_EXISTING_COVERAGE":
            return "DEPENDENT_SUPPORT"
        return "NO_EPISTEMIC_EFFECT"

    def _prediction_class(self, predicted: Any, realized: Any) -> str:
        predicted_text = str(predicted or "UNKNOWN").upper()
        realized_text = str(realized or "UNKNOWN")
        if predicted_text in {"UNKNOWN", "UNKNOWN_POTENTIAL"}:
            if realized_text == "DEPENDENT_SUPPORT":
                return "PREDICTED_UNKNOWN_REALIZED_DEPENDENT"
            if realized_text == "NEW_INDEPENDENT_SUPPORT":
                return "PREDICTED_UNKNOWN_REALIZED_NOVEL"
            return "INSUFFICIENT_PREEXECUTION_DATA"
        if predicted_text in {
            "HIGH_POTENTIAL",
            "MODERATE_POTENTIAL",
            "POSSIBLY_NEW_SOURCE",
            "NEW_INDEPENDENT_SUPPORT",
        }:
            if realized_text == "NEW_INDEPENDENT_SUPPORT":
                return "PREDICTED_NOVEL_REALIZED_NOVEL"
            if realized_text == "DEPENDENT_SUPPORT":
                return "PREDICTED_NOVEL_REALIZED_DEPENDENT"
        if predicted_text in {"LOW_POTENTIAL", "DEPENDENT_SOURCE", "DEPENDENT"}:
            if realized_text == "DEPENDENT_SUPPORT":
                return "PREDICTED_DEPENDENT_REALIZED_DEPENDENT"
        return "INSUFFICIENT_PREEXECUTION_DATA"

    def _decision_gate(self, contributions: list[dict[str, Any]]) -> str:
        if not contributions:
            return "R4-A_REALIZED_CONTRIBUTION_NOT_OBSERVABLE"
        if all(
            row.get("selection_context_binding")
            for row in contributions
            if row.get("contribution_class") != "REJECTED_EVIDENCE"
        ):
            return "R4-D_REALIZED_CONTRIBUTION_OBSERVABLE_AND_SELECTION_CONTEXT_BOUND"
        if any(
            row.get("provenance_completeness") == "PROVEN"
            for row in contributions
        ):
            return "R4-C_REALIZED_CONTRIBUTION_OBSERVABLE"
        return "R4-B_REALIZED_CONTRIBUTION_PARTIALLY_OBSERVABLE"

    def _is_accepted(self, item: Mapping[str, Any]) -> bool:
        return str(item.get("evidence_acceptance_state", "")).upper() in {
            "ACCEPTED",
            "EVIDENCE_ACCEPTED",
        }

    def _first(self, item: Mapping[str, Any], *keys: str) -> Any:
        for key in keys:
            value = item.get(key)
            if value not in UNKNOWN:
                return value
        return None


class EpistemicSelectionCalibrationDatasetBuilder:
    """Build non-authoritative calibration observations from realized outcomes."""

    schema_version = "1.0"
    system_name = "epistemic_selection_calibration_dataset_builder"

    contribution_classes = list(
        RealizedEpistemicContributionEngine.contribution_classes
    )
    prediction_buckets = [
        "UNKNOWN",
        "LOW",
        "MODERATE",
        "HIGH",
    ]

    def contract(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_owner": self.system_name,
            "required_fields": [
                "observation_id",
                "claim_id",
                "task_id",
                "source_run_id",
                "pre_execution",
                "post_execution",
                "quality",
            ],
            "pre_execution_fields": [
                "operational_rank",
                "operational_score",
                "evidence_compatibility",
                "expected_source_descriptor",
                "predicted_source_potential",
                "selection_reason",
                "repetition_count",
                "prior_task_history",
            ],
            "post_execution_fields": [
                "evidence_decision",
                "accepted_evidence_id",
                "canonical_source_identity",
                "realized_source_relation",
                "realized_contribution_class",
                "independent_count_before",
                "independent_count_after",
                "marginal_independent_delta",
                "contradiction_delta",
            ],
            "historical_classes": [
                "FULLY_PROVENANCE_NATIVE",
                "PARTIAL_HISTORICAL",
                "PRE_E1_UNBOUND",
                "UNUSABLE_FOR_CALIBRATION",
            ],
            "quality_gates": [
                "selection_context_available",
                "execution_identity_available",
                "evidence_decision_available",
                "source_provenance_available",
                "realized_source_relation_available",
                "realized_contribution_calculable",
            ],
            "dataset_quality_classes": [
                "CALIBRATION_READY",
                "PARTIAL",
                "REJECTED",
            ],
            "authority": "NONE",
            "selection_authority": "NONE",
            "execution_authority": "NONE",
            "evidence_authority": "NONE",
            "truth_authority": "NONE",
            "budget_authority": "NONE",
            "grants_selection": False,
            "grants_execution": False,
            "grants_evidence": False,
            "grants_truth": False,
            "grants_independence": False,
            **AUTHORITY,
            "authority": "NONE",
        }

    def observation(
        self,
        realized_contribution: Mapping[str, Any],
        *,
        selection_context: Mapping[str, Any] | None = None,
        prior_task_history: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contribution = (
            dict(realized_contribution)
            if isinstance(realized_contribution, Mapping)
            else {}
        )
        binding = contribution.get("selection_context_binding") or {}
        selection = dict(selection_context or binding)
        prior = dict(prior_task_history or {})
        pre_execution = {
            "operational_rank": self._first(
                selection,
                "operational_rank",
                "operational_rank_at_selection",
            ),
            "operational_score": self._first(
                selection,
                "operational_score",
                "operational_score_at_selection",
            ),
            "evidence_compatibility": self._first(
                selection,
                "evidence_compatibility",
                "evidence_compatibility_at_selection",
            ),
            "expected_source_descriptor": selection.get(
                "expected_source_descriptor",
                {},
            ),
            "predicted_source_potential": self._first(
                selection,
                "predicted_source_potential",
                "source_potential",
            ) or "UNKNOWN",
            "selection_reason": selection.get("selection_reason", []),
            "repetition_count": int(
                self._first(selection, "repetition_count", "prior_selection_count")
                or prior.get("repetition_count")
                or 0
            ),
            "prior_task_history": prior,
        }
        post_execution = {
            "evidence_decision": contribution.get("evidence_acceptance_state"),
            "accepted_evidence_id": contribution.get("accepted_evidence_id"),
            "canonical_source_identity": contribution.get(
                "canonical_source_identity"
            ),
            "realized_source_relation": contribution.get(
                "source_relation_to_existing_coverage"
            ),
            "realized_contribution_class": contribution.get(
                "contribution_class"
            ),
            "independent_count_before": contribution.get(
                "independent_count_before"
            ),
            "independent_count_after": contribution.get("independent_count_after"),
            "marginal_independent_delta": contribution.get(
                "marginal_independent_delta"
            ),
            "contradiction_delta": contribution.get("contradiction_delta"),
        }
        gates = self._quality_gates(contribution, pre_execution, post_execution)
        quality_class = self._quality_class(gates)
        observation = {
            "schema_version": self.schema_version,
            "system": "epistemic_selection_calibration_observation",
            "observation_id": self._observation_id(contribution),
            "claim_id": contribution.get("claim_id"),
            "task_id": contribution.get("task_id"),
            "source_run_id": contribution.get("source_run_id"),
            "pre_execution": pre_execution,
            "post_execution": post_execution,
            "quality": {
                **gates,
                "provenance_completeness": contribution.get(
                    "provenance_completeness",
                    "UNKNOWN",
                ),
                "observation_completeness": quality_class,
                "historical_policy_class": self._historical_class(
                    contribution,
                    gates,
                ),
                "authority": "NONE",
            },
            "authority": "NONE",
            "selection_authority": "NONE",
            "execution_authority": "NONE",
            "evidence_authority": "NONE",
            "truth_authority": "NONE",
            "budget_authority": "NONE",
            "grants_selection": False,
            "grants_execution": False,
            "grants_evidence": False,
            "grants_truth": False,
            "grants_independence": False,
        }
        return observation

    def dataset(
        self,
        observations: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        deduped: dict[str, dict[str, Any]] = {}
        duplicates = []
        for item in observations:
            if not isinstance(item, Mapping):
                continue
            observation = dict(item)
            observation_id = str(observation.get("observation_id") or "")
            if not observation_id:
                continue
            if observation_id in deduped:
                duplicates.append(observation_id)
                continue
            deduped[observation_id] = observation
        rows = [
            deduped[key]
            for key in sorted(deduped)
        ]
        ready = [
            row for row in rows
            if row.get("quality", {}).get("observation_completeness")
            == "CALIBRATION_READY"
        ]
        partial = [
            row for row in rows
            if row.get("quality", {}).get("observation_completeness") == "PARTIAL"
        ]
        rejected = [
            row for row in rows
            if row.get("quality", {}).get("observation_completeness") == "REJECTED"
        ]
        historical = self._historical_counts(rows)
        contribution_distribution = self._contribution_distribution(rows)
        matrix = self._prediction_realization_matrix(rows)
        evidence = self._evidence_compatibility_calibration(rows)
        repetition = self._repetition_value(rows)
        metrics = self._calibration_metrics(rows)
        sufficiency = self._data_sufficiency(rows, ready)
        return {
            "schema_version": self.schema_version,
            "system": "epistemic_selection_calibration_dataset",
            "dataset_size": len(rows),
            "deduplicated_observation_count": len(rows),
            "duplicate_observation_count": len(duplicates),
            "duplicate_observation_ids": sorted(set(duplicates)),
            "calibration_ready_count": len(ready),
            "partial_count": len(partial),
            "rejected_count": len(rejected),
            "historical_partial_count": (
                historical.get("PARTIAL_HISTORICAL", 0)
                + historical.get("PRE_E1_UNBOUND", 0)
            ),
            "historical_policy_counts": historical,
            "contribution_class_distribution": contribution_distribution,
            "prediction_vs_realization_matrix": matrix,
            "evidence_compatibility_calibration": evidence,
            "repetition_value": repetition,
            "data_sufficiency_level": sufficiency,
            "calibration_metrics": metrics,
            "predictive_signal_status": self._predictive_signal_status(
                sufficiency
            ),
            "decision_gate": self._decision_gate(rows, ready),
            "observations": rows,
            "contract_compatibility": (
                "SelectionContext -> Execution -> AcceptedEvidence -> "
                "RealizedEpistemicContribution -> CalibrationObservation -> "
                "CalibrationDataset"
            ),
            "authority": "NONE",
            "selection_authority": "NONE",
            "execution_authority": "NONE",
            "evidence_authority": "NONE",
            "truth_authority": "NONE",
            "budget_authority": "NONE",
            **AUTHORITY,
            "authority": "NONE",
        }

    def _quality_gates(
        self,
        contribution: Mapping[str, Any],
        pre_execution: Mapping[str, Any],
        post_execution: Mapping[str, Any],
    ) -> dict[str, bool]:
        return {
            "selection_context_available": bool(
                pre_execution.get("operational_rank") is not None
                or pre_execution.get("evidence_compatibility") is not None
                or pre_execution.get("expected_source_descriptor")
                or pre_execution.get("predicted_source_potential") != "UNKNOWN"
            ),
            "execution_identity_available": bool(
                contribution.get("task_id") and contribution.get("source_run_id")
            ),
            "evidence_decision_available": bool(
                post_execution.get("evidence_decision") not in UNKNOWN
            ),
            "source_provenance_available": bool(
                contribution.get("provenance_completeness") == "PROVEN"
                and post_execution.get("canonical_source_identity") != "UNKNOWN"
            ),
            "realized_source_relation_available": bool(
                post_execution.get("realized_source_relation") not in UNKNOWN
            ),
            "realized_contribution_calculable": bool(
                post_execution.get("realized_contribution_class")
                in self.contribution_classes
                and post_execution.get("marginal_independent_delta") is not None
                and post_execution.get("contradiction_delta") is not None
            ),
        }

    def _quality_class(self, gates: Mapping[str, bool]) -> str:
        if all(gates.values()):
            return "CALIBRATION_READY"
        if (
            gates.get("execution_identity_available")
            and gates.get("evidence_decision_available")
            and gates.get("realized_contribution_calculable")
        ):
            return "PARTIAL"
        return "REJECTED"

    def _historical_class(
        self,
        contribution: Mapping[str, Any],
        gates: Mapping[str, bool],
    ) -> str:
        if contribution.get("claim_evidence_binding_state") == "PRE_E1_UNBOUND":
            return "PRE_E1_UNBOUND"
        if all(gates.values()):
            return "FULLY_PROVENANCE_NATIVE"
        if (
            gates.get("execution_identity_available")
            or gates.get("evidence_decision_available")
            or gates.get("realized_contribution_calculable")
        ):
            return "PARTIAL_HISTORICAL"
        return "UNUSABLE_FOR_CALIBRATION"

    def _observation_id(self, contribution: Mapping[str, Any]) -> str:
        payload = {
            "claim_id": contribution.get("claim_id"),
            "task_id": contribution.get("task_id"),
            "source_run_id": contribution.get("source_run_id"),
            "accepted_evidence_id": contribution.get("accepted_evidence_id"),
            "canonical_source_identity": contribution.get(
                "canonical_source_identity"
            ),
            "contribution_class": contribution.get("contribution_class"),
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return (
            "calibration_observation_"
            f"{hashlib.sha1(encoded.encode('utf-8')).hexdigest()[:16]}"
        )

    def _historical_counts(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> dict[str, int]:
        counts = {
            "FULLY_PROVENANCE_NATIVE": 0,
            "PARTIAL_HISTORICAL": 0,
            "PRE_E1_UNBOUND": 0,
            "UNUSABLE_FOR_CALIBRATION": 0,
        }
        for row in rows:
            state = row.get("quality", {}).get(
                "historical_policy_class",
                "UNUSABLE_FOR_CALIBRATION",
            )
            counts[state] = counts.get(state, 0) + 1
        return counts

    def _contribution_distribution(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> dict[str, int]:
        counts = {key: 0 for key in self.contribution_classes}
        for row in rows:
            state = row.get("post_execution", {}).get(
                "realized_contribution_class",
                "NO_EPISTEMIC_EFFECT",
            )
            counts[state] = counts.get(state, 0) + 1
        return counts

    def _prediction_realization_matrix(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> dict[str, dict[str, int]]:
        matrix = {
            bucket: {state: 0 for state in self.contribution_classes}
            for bucket in self.prediction_buckets
        }
        for row in rows:
            predicted = self._prediction_bucket(
                row.get("pre_execution", {}).get("predicted_source_potential")
            )
            realized = row.get("post_execution", {}).get(
                "realized_contribution_class",
                "NO_EPISTEMIC_EFFECT",
            )
            matrix[predicted][realized] = matrix[predicted].get(realized, 0) + 1
        return matrix

    def _evidence_compatibility_calibration(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        buckets = {
            "EXACT_MATCH": [],
            "STRONG_MATCH": [],
            "PARTIAL_MATCH": [],
            "NO_MATCH": [],
            "UNKNOWN": [],
        }
        for row in rows:
            bucket = str(
                row.get("pre_execution", {}).get(
                    "evidence_compatibility",
                    "UNKNOWN",
                )
            )
            if bucket.replace(".", "", 1).isdigit():
                number = float(bucket)
                bucket = (
                    "EXACT_MATCH"
                    if number >= 1.0
                    else "STRONG_MATCH"
                    if number >= 0.75
                    else "PARTIAL_MATCH"
                    if number > 0
                    else "NO_MATCH"
                )
            if bucket not in buckets:
                bucket = "UNKNOWN"
            buckets[bucket].append(row)
        return {
            bucket: self._outcome_summary(items)
            for bucket, items in buckets.items()
        }

    def _repetition_value(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        buckets = {
            "FIRST_SELECTION": [],
            "REPEATED_SELECTION": [],
            "UNKNOWN": [],
        }
        for row in rows:
            repetition = row.get("pre_execution", {}).get("repetition_count")
            if repetition is None:
                buckets["UNKNOWN"].append(row)
            elif int(repetition) > 0:
                buckets["REPEATED_SELECTION"].append(row)
            else:
                buckets["FIRST_SELECTION"].append(row)
        return {
            bucket: self._outcome_summary(items)
            for bucket, items in buckets.items()
        }

    def _calibration_metrics(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        items = list(rows)
        total = len(items)
        accepted = [
            row for row in items
            if str(row.get("post_execution", {}).get("evidence_decision", "")).upper()
            in {"ACCEPTED", "EVIDENCE_ACCEPTED"}
        ]
        independent = [
            row for row in accepted
            if row.get("post_execution", {}).get("realized_contribution_class")
            == "NEW_INDEPENDENT_SUPPORT"
        ]
        dependent = [
            row for row in accepted
            if row.get("post_execution", {}).get("realized_contribution_class")
            == "DEPENDENT_SUPPORT"
        ]
        contradictions = [
            row for row in accepted
            if row.get("post_execution", {}).get("realized_contribution_class")
            == "CONTRADICTORY_INDEPENDENT_EVIDENCE"
        ]
        unknown = [
            row for row in accepted
            if row.get("post_execution", {}).get("realized_contribution_class")
            == "UNKNOWN_PROVENANCE"
        ]
        return {
            "accepted_evidence_rate": (
                len(accepted) / total if total else "UNAVAILABLE"
            ),
            "independent_yield": (
                len(independent) / len(accepted)
                if accepted else "UNAVAILABLE"
            ),
            "dependent_replication_rate": (
                len(dependent) / len(accepted) if accepted else "UNAVAILABLE"
            ),
            "contradiction_rate": (
                len(contradictions) / len(accepted)
                if accepted else "UNAVAILABLE"
            ),
            "unknown_provenance_rate": (
                len(unknown) / len(accepted) if accepted else "UNAVAILABLE"
            ),
            "conditional_probabilities": {
                "P_independent_given_evidence_compatibility": "UNAVAILABLE",
                "P_independent_given_predicted_source_potential": "UNAVAILABLE",
                "P_independent_given_repetition_bucket": "UNAVAILABLE",
            },
            "authority": "NONE",
        }

    def _outcome_summary(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        items = list(rows)
        counts = self._contribution_distribution(items)
        accepted = [
            row for row in items
            if str(row.get("post_execution", {}).get("evidence_decision", "")).upper()
            in {"ACCEPTED", "EVIDENCE_ACCEPTED"}
        ]
        return {
            "sample_count": len(items),
            "accepted_evidence_count": len(accepted),
            "independent_contribution_count": counts["NEW_INDEPENDENT_SUPPORT"],
            "dependent_support_count": counts["DEPENDENT_SUPPORT"],
            "contradiction_count": counts[
                "CONTRADICTORY_INDEPENDENT_EVIDENCE"
            ],
            "no_effect_count": counts["NO_EPISTEMIC_EFFECT"],
            "distribution": counts,
            "authority": "NONE",
        }

    def _data_sufficiency(
        self,
        rows: list[Mapping[str, Any]],
        ready: list[Mapping[str, Any]],
    ) -> str:
        ready_classes = {
            row.get("post_execution", {}).get("realized_contribution_class")
            for row in ready
        }
        lineages = {
            row.get("post_execution", {}).get("canonical_source_identity")
            for row in ready
            if row.get("post_execution", {}).get("canonical_source_identity")
            not in UNKNOWN
        }
        if len(ready) >= 50 and len(ready_classes) >= 3 and len(lineages) > 1:
            return "P3"
        if len(ready) >= 20 and len(ready_classes) >= 2:
            return "P2"
        if len(ready) >= 5:
            return "P1"
        if rows:
            return "P0"
        return "P0"

    def _decision_gate(
        self,
        rows: list[Mapping[str, Any]],
        ready: list[Mapping[str, Any]],
    ) -> str:
        ready_classes = {
            row.get("post_execution", {}).get("realized_contribution_class")
            for row in ready
        }
        if len(ready) >= 20 and len(ready_classes) >= 2:
            return "R5-C_CALIBRATION_DATASET_HAS_USEFUL_DIVERSITY"
        if rows:
            return "R5-B_CALIBRATION_DATASET_EXISTS_BUT_LOW_DIVERSITY"
        return "R5-A_MEASUREMENT_ONLY_INSUFFICIENT_DATA"

    def _predictive_signal_status(self, sufficiency: str) -> str:
        if sufficiency in {"P4", "P5"}:
            return "REPRODUCIBLE_PREDICTIVE_SIGNAL_OBSERVED"
        return "INSUFFICIENT_FOR_PREDICTIVE_CLAIM"

    def _prediction_bucket(self, value: Any) -> str:
        text = str(value or "UNKNOWN").upper()
        if "HIGH" in text:
            return "HIGH"
        if "MODERATE" in text:
            return "MODERATE"
        if "LOW" in text or "DEPENDENT" in text:
            return "LOW"
        return "UNKNOWN"

    def _first(self, item: Mapping[str, Any], *keys: str) -> Any:
        for key in keys:
            value = item.get(key)
            if value not in UNKNOWN:
                return value
        return None


__all__ = [
    "AUTHORITY",
    "EpistemicSelectionCalibrationDatasetBuilder",
    "EvidenceSourceIndependenceEngine",
    "RealizedEpistemicContributionEngine",
]
