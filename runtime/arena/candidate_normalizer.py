"""Canonical candidate normalization and equivalence collapsing."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from runtime.arena.candidate_simulator import CandidateSimulator
from runtime.arena.executor_contract import EXECUTOR_NORMALIZATION_VERSION
from runtime.telemetry.route_contribution import ROUTE_LINEAGE_FIELDS


class CandidateNormalizer:
    """Convert proposals into canonical candidates and merge equivalents."""

    system_name = "candidate_normalizer"

    def normalize(self, proposals: list[Mapping[str, Any]] | None) -> dict[str, Any]:
        canonical = [self._candidate(item) for item in proposals or [] if isinstance(item, Mapping)]
        groups: dict[str, list[dict[str, Any]]] = {}
        for candidate in canonical:
            groups.setdefault(self._collapse_key(candidate), []).append(candidate)
        normalized = []
        equivalent_groups = []
        collapsed = 0
        for signature, group in groups.items():
            if len(group) == 1:
                normalized.append(group[0])
                continue
            merged = self._merge_group(group)
            normalized.append(merged)
            collapsed += len(group) - 1
            equivalent_groups.append({
                "program_signature": merged["program_signature"],
                "candidate_ids": sorted(item["candidate_id"] for item in group),
                "sources": sorted({source for item in group for source in item.get("sources", [item.get("source")])}),
                "merged_candidate_id": merged["candidate_id"],
            })
        equivalent_groups.sort(key=lambda item: item["program_signature"])
        consensus_groups = self._cross_source_consensus_groups(normalized)
        self._annotate_consensus(normalized, consensus_groups)
        normalized.sort(key=lambda item: item["candidate_id"])
        raw_candidate_count = len(canonical)
        equivalence_class_count = len(normalized)
        alias_class_count = len(equivalent_groups)
        total_alias_member_count = sum(
            len(group["candidate_ids"]) for group in equivalent_groups
        )
        return {
            "system": self.system_name,
            "normalized_candidates": normalized,
            "duplicate_candidates_collapsed": collapsed,
            "count_semantics_schema": "candidate_normalization_counts.v1",
            "raw_candidate_count": raw_candidate_count,
            "semantic_equivalence_class_count": equivalence_class_count,
            "equivalence_class_count": equivalence_class_count,
            "singleton_class_count": equivalence_class_count - alias_class_count,
            "alias_class_count": alias_class_count,
            "total_alias_member_count": total_alias_member_count,
            "collapsed_record_count": collapsed,
            "retained_representative_count": equivalence_class_count,
            "arena_candidate_count": equivalence_class_count,
            "equivalent_candidate_groups": equivalent_groups,
            "cross_source_consensus_groups": consensus_groups,
            "cross_source_consensus_count": len(consensus_groups),
            "normalization_success": True,
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "score_authority": "NONE",
            "ranking_authority": "NONE",
            "safe_winner_authority": "NONE",
            "execution_authority": "NONE",
        }

    def _candidate(self, proposal: Mapping[str, Any]) -> dict[str, Any]:
        source_record = deepcopy(dict(proposal))
        program = proposal.get("program") if isinstance(proposal.get("program"), Mapping) else {}
        steps = program.get("steps") if isinstance(program.get("steps"), list) else []
        normalized_steps = [self._step(step) for step in steps if isinstance(step, Mapping)]
        operation = _normalize_operation(proposal.get("operation") or (normalized_steps[0].get("operation") if normalized_steps else None))
        program = {
            "step_count": int(program.get("step_count", len(normalized_steps)) or 0),
            "steps": normalized_steps,
        }
        source = _normalize(proposal.get("source"))
        origin_source = _normalize(
            proposal.get("origin_source")
            or (proposal.get("provenance") or {}).get("origin_source")
            or (proposal.get("provenance") or {}).get("original_source")
            or source
        )
        candidate = deepcopy(dict(proposal))
        semantic_program = self._semantic_program(program)
        executor_contract_id = str(
            proposal.get("executor_contract_id")
            or CandidateSimulator.EXECUTOR_CONTRACT_ID
        )
        executor_contract_version = str(
            proposal.get("executor_contract_version")
            or CandidateSimulator.EXECUTOR_CONTRACT_VERSION
        )
        semantic_fingerprint = self._semantic_fingerprint(
            semantic_program,
            executor_contract_id,
            executor_contract_version,
        )
        source_candidate_fingerprint = self._source_record_fingerprint(source_record)
        candidate.update({
            "candidate_id": str(proposal.get("candidate_id") or f"candidate:{source}:unknown"),
            "source": source,
            "sources": [source] if source else [],
            "origin_source": origin_source,
            "origin_sources": [origin_source] if origin_source else [],
            "normalized_source": source,
            "normalized_sources": [source] if source else [],
            "operation": operation,
            "program": program,
            "source_confidence": _score(proposal.get("source_confidence", 0.0)),
            "semantic_support": _score(proposal.get("semantic_support", 0.0)),
            "truth_support": _score(proposal.get("truth_support", 0.0)),
            "context_support": _score(proposal.get("context_support", 0.0)),
            "dependency_support": _score(proposal.get("dependency_support", 0.0)),
            "identity_support": _score(proposal.get("identity_support", 0.0)),
            "localization_support": _score(proposal.get("localization_support", 0.0)),
            "program_signature": semantic_fingerprint,
            "semantic_fingerprint": semantic_fingerprint,
            "semantic_equivalence_class_id": (
                "semantic_equivalence_class:" + semantic_fingerprint
            ),
            "normalized_semantics": semantic_program,
            "semantic_equivalence_scope": "CURRENT_ARENA_EXECUTOR_CONTRACT",
            "semantic_equivalence_is_correctness_evidence": False,
            "executor_contract_id": executor_contract_id,
            "executor_contract_version": executor_contract_version,
            "normalization_version": EXECUTOR_NORMALIZATION_VERSION,
            "executor_contract_binding_state": (
                "CURRENT_CONTRACT_VERIFIED"
                if executor_contract_id == CandidateSimulator.EXECUTOR_CONTRACT_ID
                and executor_contract_version
                == CandidateSimulator.EXECUTOR_CONTRACT_VERSION
                else "NONCURRENT_CONTRACT_PRESERVED_FAIL_CLOSED"
            ),
            "source_candidate_fingerprint": source_candidate_fingerprint,
            "source_candidate_record": source_record,
            "provenance_history": [deepcopy(proposal.get("provenance", {}))],
            "supporting_hypotheses": [
                proposal.get("hypothesis_id")
            ] if proposal.get("hypothesis_id") else [],
            "confidence_contributions": {
                source: _score(proposal.get("source_confidence", 0.0))
            } if source else {},
        })
        metadata = candidate.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        for field in ROUTE_LINEAGE_FIELDS:
            value = proposal.get(field)
            if value is None:
                value = metadata.get(field)
            if value is not None:
                candidate[field] = deepcopy(value)
                metadata[field] = deepcopy(value)
        candidate["metadata"] = metadata
        candidate["semantic_alias_records"] = [
            self._alias_record(candidate)
        ]
        return candidate

    def _collapse_key(self, candidate: Mapping[str, Any]) -> str:
        return str(candidate.get("semantic_fingerprint") or candidate.get("program_signature"))

    def _step(self, step: Mapping[str, Any]) -> dict[str, Any]:
        operation = _normalize_operation(step.get("operation") or step.get("primitive"))
        parameters = step.get("parameters") if isinstance(step.get("parameters"), Mapping) else {}
        return {
            "operation": operation,
            "parameters": deepcopy(dict(parameters)),
        }

    def _merge_group(self, group: list[dict[str, Any]]) -> dict[str, Any]:
        ordered_group = sorted(group, key=lambda item: str(item.get("candidate_id")))
        base = deepcopy(ordered_group[0])
        sources = sorted({source for item in ordered_group for source in item.get("sources", [])})
        origin_sources = sorted({
            source for item in ordered_group
            for source in item.get("origin_sources", [item.get("origin_source")])
            if source
        })
        normalized_sources = sorted({
            source for item in ordered_group
            for source in item.get("normalized_sources", [item.get("normalized_source")])
            if source
        })
        hypotheses = sorted({
            hypothesis for item in ordered_group
            for hypothesis in item.get("supporting_hypotheses", [])
            if hypothesis
        })
        base["candidate_id"] = "merged:" + base["semantic_fingerprint"][:16]
        base["representative_source_candidate_id"] = ordered_group[0]["candidate_id"]
        base["equivalence_reason"] = "EXECUTOR_SEMANTIC_FINGERPRINT_MATCH"
        base["equivalent_executable_representations"] = [
            {
                "candidate_id": item["candidate_id"],
                "program": deepcopy(item["program"]),
                "program_fingerprint": self._raw_program_fingerprint(item["program"]),
            }
            for item in ordered_group
        ]
        base["semantic_alias_records"] = [
            self._alias_record(item) for item in ordered_group
        ]
        base["sources"] = sources
        base["source"] = sources[0] if sources else base.get("source")
        base["origin_sources"] = origin_sources
        base["origin_source"] = origin_sources[0] if origin_sources else base.get("origin_source")
        base["normalized_sources"] = normalized_sources
        base["normalized_source"] = normalized_sources[0] if normalized_sources else base.get("normalized_source")
        base["supporting_hypotheses"] = hypotheses
        base["source_confidence"] = max(
            _score(item.get("source_confidence")) for item in ordered_group
        )
        for field in (
            "semantic_support",
            "truth_support",
            "context_support",
            "dependency_support",
            "identity_support",
            "localization_support",
        ):
            base[field] = round(
                sum(_score(item.get(field)) for item in ordered_group)
                / len(ordered_group),
                4,
            )
        base["provenance_history"] = [
            history for item in ordered_group
            for history in item.get("provenance_history", [])
        ]
        base["confidence_contributions"] = {
            item.get("source"): _score(item.get("source_confidence"))
            for item in ordered_group
            if item.get("source")
        }
        route_execution_ids = sorted({
            route_id
            for item in ordered_group
            for route_id in item.get("origin_route_execution_ids", [])
            if route_id
        })
        route_ids = sorted({
            route_id
            for item in ordered_group
            for route_id in item.get("origin_route_ids", [])
            if route_id
        })
        if route_execution_ids:
            base["origin_route_execution_ids"] = route_execution_ids
            base["origin_route_execution_id"] = route_execution_ids[0]
            base["origin_route_ids"] = route_ids
            base["origin_route_id"] = route_ids[0] if route_ids else None
            base["route_lineage_origin_type"] = (
                "MULTI_ORIGIN_DIRECT_LINEAGE"
                if len(route_execution_ids) > 1
                else base.get("route_lineage_origin_type")
            )
            base["route_lineage_scope_state"] = (
                "ROUTE_ORIGIN_CURRENT"
                if all(
                    item.get("route_lineage_scope_state") == "ROUTE_ORIGIN_CURRENT"
                    for item in ordered_group
                    if item.get("origin_route_execution_ids")
                )
                else "ROUTE_ORIGIN_PARTIAL"
            )
            base["route_origin_lineage"] = {
                "schema_version": "route_origin_lineage.v1",
                "run_id": base.get("route_origin_lineage", {}).get("run_id")
                if isinstance(base.get("route_origin_lineage"), dict)
                else None,
                "task_id": base.get("route_origin_lineage", {}).get("task_id")
                if isinstance(base.get("route_origin_lineage"), dict)
                else None,
                "route_execution_id": route_execution_ids[0],
                "route_execution_ids": route_execution_ids,
                "route_id": route_ids[0] if route_ids else None,
                "route_ids": route_ids,
                "route_lineage_origin_type": base["route_lineage_origin_type"],
                "route_lineage_scope_state": base["route_lineage_scope_state"],
                "authority": "OBSERVATION_ONLY",
                "behavioral_authority": "NONE",
            }
            metadata = base.get("metadata") if isinstance(base.get("metadata"), dict) else {}
            for field in ROUTE_LINEAGE_FIELDS:
                if base.get(field) is not None:
                    metadata[field] = deepcopy(base.get(field))
            base["metadata"] = metadata
        base["equivalent_candidate_ids"] = [
            item["candidate_id"] for item in ordered_group
        ]
        return base

    def _cross_source_consensus_groups(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        by_signature: dict[str, list[dict[str, Any]]] = {}
        for candidate in candidates:
            by_signature.setdefault(candidate["program_signature"], []).append(candidate)
        groups = []
        for signature, group in sorted(by_signature.items()):
            sources = sorted({
                source
                for item in group
                for source in item.get("sources", [item.get("source")])
                if source
            })
            if len(sources) < 2:
                continue
            groups.append({
                "consensus_id": f"cross_source:{signature[:16]}",
                "program_signature": signature,
                "candidate_ids": [item["candidate_id"] for item in group],
                "sources": sources,
                "operation": group[0].get("operation"),
                "consensus_state": "CROSS_SOURCE_CONSENSUS",
            })
        return groups

    def _annotate_consensus(
        self,
        candidates: list[dict[str, Any]],
        consensus_groups: list[dict[str, Any]],
    ) -> None:
        group_by_candidate = {
            candidate_id: group
            for group in consensus_groups
            for candidate_id in group.get("candidate_ids", [])
        }
        for candidate in candidates:
            group = group_by_candidate.get(candidate.get("candidate_id"))
            if not group:
                candidate["cross_source_consensus"] = False
                continue
            candidate["cross_source_consensus"] = True
            candidate["cross_source_consensus_id"] = group["consensus_id"]
            candidate["consensus_sources"] = group["sources"]

    def _program_signature(self, program: Mapping[str, Any]) -> str:
        payload = json.dumps(
            program,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _raw_program_fingerprint(self, program: Mapping[str, Any]) -> str:
        return self._program_signature(program)

    def _semantic_fingerprint(
        self,
        program: Mapping[str, Any],
        executor_contract_id: str,
        executor_contract_version: str,
    ) -> str:
        return self._program_signature({
            "executor_contract_id": executor_contract_id,
            "executor_contract_version": executor_contract_version,
            "normalized_semantics": program,
        })

    def _source_record_fingerprint(self, source_record: Mapping[str, Any]) -> str:
        return self._program_signature(source_record)

    def _alias_record(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "candidate_id": candidate.get("candidate_id"),
            "candidate_fingerprint": candidate.get("source_candidate_fingerprint"),
            "generator_source": candidate.get("source"),
            "origin_source": candidate.get("origin_source"),
            "parent_candidate_ids": deepcopy(
                candidate.get("equivalent_candidate_ids", [])
            ),
            "executable_representation": deepcopy(candidate.get("program", {})),
            "executable_fingerprint": self._raw_program_fingerprint(
                candidate.get("program", {})
            ),
            "source_record": deepcopy(candidate.get("source_candidate_record", {})),
            "source_record_fingerprint": candidate.get(
                "source_candidate_fingerprint"
            ),
        }

    def _semantic_program(self, program: Mapping[str, Any]) -> dict[str, Any]:
        semantic_steps = []
        for step in program.get("steps", []) or []:
            if not isinstance(step, Mapping):
                continue
            operation = _normalize_operation(step.get("operation") or step.get("primitive"))
            if operation in {
                "noop",
                "preserve_grid",
                "preserve_colors",
                "preserve_topology",
                "preserve_shape",
                "preserve_size",
                "preserve_density",
                "preserve_symmetry",
            }:
                continue
            parameters = deepcopy(dict(step.get("parameters") or {}))
            if operation == "duplicate_object":
                parameters.pop("duplication_count", None)
                parameters.pop("duplication_policy", None)
            semantic_steps.append({
                "operation": operation,
                "parameters": parameters,
            })
        return {
            "step_count": len(semantic_steps),
            "steps": semantic_steps,
        }


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_operation(value: Any) -> str | None:
    token = _normalize(value)
    aliases = {
        "remap_colors": "replace_color",
        "global_recolor": "replace_color",
        "preserve_input": "preserve_grid",
        "identity": "preserve_grid",
        "preserve_color": "preserve_colors",
        "preserve_color_mapping": "preserve_colors",
        "duplicate": "duplicate_object",
        "replicate": "duplicate_object",
        "translate_object": "translate",
    }
    return aliases.get(token, token) if token else None


candidate_normalizer = CandidateNormalizer()

__all__ = ["CandidateNormalizer", "candidate_normalizer"]
