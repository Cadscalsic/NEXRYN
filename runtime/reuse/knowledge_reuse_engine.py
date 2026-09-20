"""Reuse existing contexts, truths, strategies, and programs before regeneration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from runtime.knowledge.current_knowledge_admission import CurrentKnowledgeAdmissionGate


class KnowledgeReuseEngine:
    system_name = "knowledge_reuse_engine"

    def __init__(
        self,
        knowledge_admission_gate: CurrentKnowledgeAdmissionGate | None = None,
    ) -> None:
        self.context_hits = 0
        self.truth_hits = 0
        self.strategy_hits = 0
        self.program_hits = 0
        self.context_misses = 0
        self.truth_misses = 0
        self.strategy_misses = 0
        self.program_misses = 0
        self.reuse_events: list[dict[str, Any]] = []
        self._context_cache: list[dict[str, Any]] | None = None
        self._strategy_cache: list[dict[str, Any]] | None = None
        self._program_cache: list[dict[str, Any]] | None = None
        self.knowledge_admission_gate = (
            knowledge_admission_gate or CurrentKnowledgeAdmissionGate()
        )
        self.current_knowledge_inputs: list[dict[str, Any]] = []
        self.excluded_noncurrent_knowledge: list[dict[str, Any]] = []

    def reuse_before_regenerate(
        self,
        query: Mapping[str, Any] | str | None,
        contexts: list[Mapping[str, Any]] | None = None,
        truths: list[Mapping[str, Any]] | None = None,
        strategies: list[Mapping[str, Any]] | None = None,
        programs: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        context = self._best(
            query,
            contexts or self._stored_contexts(),
            "context",
        )
        truth = self._best(query, truths or [], "truth")
        strategy = self._best(
            query,
            strategies or self._stored_strategies(),
            "strategy",
        )
        program = self._best(
            query,
            programs or self._stored_programs(),
            "program",
        )
        self._count("context", context)
        self._count("truth", truth)
        self._count("strategy", strategy)
        self._count("program", program)
        reused = [item for item in (context, truth, strategy, program) if item]
        self.reuse_events.extend(reused)
        return {
            "system": self.system_name,
            "knowledge_reused": bool(reused),
            "reused_context": context,
            "reused_truth": truth,
            "reused_strategy": strategy,
            "reused_program": program,
            **self.metrics(),
            "reason": "reuse_before_regenerate" if reused else "no_reusable_knowledge_found",
        }

    def metrics(self) -> dict[str, Any]:
        hits = self.context_hits + self.truth_hits + self.strategy_hits + self.program_hits
        misses = self.context_misses + self.truth_misses + self.strategy_misses + self.program_misses
        return {
            "context_hits": self.context_hits,
            "truth_hits": self.truth_hits,
            "strategy_hits": self.strategy_hits,
            "program_hits": self.program_hits,
            "context_misses": self.context_misses,
            "truth_misses": self.truth_misses,
            "strategy_misses": self.strategy_misses,
            "program_misses": self.program_misses,
            "current_knowledge_input_count": len(self.current_knowledge_inputs),
            "excluded_noncurrent_knowledge_count": len(
                self.excluded_noncurrent_knowledge
            ),
            "CURRENT_KNOWLEDGE_INPUTS": self.current_knowledge_inputs[-10:],
            "EXCLUDED_NONCURRENT_KNOWLEDGE": (
                self.excluded_noncurrent_knowledge[-10:]
            ),
            "knowledge_reuse_rate": round(hits / max(hits + misses, 1), 4),
            "knowledge_reuse_events": hits,
        }

    def report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "KNOWLEDGE REUSE REPORT": True,
            "reuse_events": list(self.reuse_events),
            **self.metrics(),
        }

    def _best(
        self,
        query: Mapping[str, Any] | str | None,
        candidates: list[Mapping[str, Any]],
        kind: str,
    ) -> dict[str, Any]:
        ranked = []
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            admitted = self._admit_current_knowledge_if_required(
                candidate,
                consumer_scope=f"knowledge_reuse_engine_{kind}",
            )
            if admitted is False:
                continue
            candidate = admitted or candidate
            score = _similarity(query, candidate)
            if score >= 0.5:
                ranked.append({**dict(candidate), "reuse_kind": kind, "reuse_score": score})
        ranked.sort(key=lambda item: item["reuse_score"], reverse=True)
        return ranked[0] if ranked else {}

    def _admit_current_knowledge_if_required(
        self,
        candidate: Mapping[str, Any],
        *,
        consumer_scope: str,
    ) -> dict[str, Any] | bool | None:
        item = dict(candidate)
        if not (item.get("knowledge_id") or item.get("source_knowledge_id")):
            return None
        admission_candidate = item
        if item.get("source_knowledge_id") and not item.get("knowledge_id"):
            admission_candidate = {
                "knowledge_id": item.get("source_knowledge_id"),
                "subject_id": item.get("source_knowledge_subject_id"),
                "current_knowledge_decision_id": item.get(
                    "source_knowledge_decision_id"
                ),
                "current_state_fingerprint": item.get(
                    "source_knowledge_fingerprint"
                ),
                "support_fingerprint": item.get(
                    "source_knowledge_support_fingerprint"
                ),
            }
        admission = self.knowledge_admission_gate.admit_current_knowledge(
            admission_candidate,
            consumer_scope=consumer_scope,
        )
        record = {**item, "current_knowledge_admission": admission.to_dict()}
        if admission.admitted:
            enriched = {
                **item,
                "current_knowledge_admission": admission.to_dict(),
                "source_knowledge_id": admission.knowledge_id,
                "source_knowledge_subject_id": admission.subject_id,
                "source_knowledge_decision_id": admission.current_knowledge_decision_id,
                "source_knowledge_status": admission.current_status,
                "source_knowledge_fingerprint": admission.current_state_fingerprint,
            }
            self.current_knowledge_inputs.append(enriched)
            return enriched
        self.excluded_noncurrent_knowledge.append(record)
        return False

    def _count(self, kind: str, item: Mapping[str, Any]) -> None:
        attr = f"{kind}_hits" if item else f"{kind}_misses"
        setattr(self, attr, getattr(self, attr) + 1)

    def _stored_strategies(self) -> list[dict[str, Any]]:
        if self._strategy_cache is not None:
            return list(self._strategy_cache)
        root = Path("runtime/memory/storage/strategies")
        strategies = []
        if root.exists():
            for path in list(root.glob("*.json"))[:200]:
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if isinstance(payload, Mapping):
                    strategy = payload.get("strategy", payload)
                    record = dict(strategy) if isinstance(strategy, Mapping) else {}
                    record["strategy_id"] = payload.get("strategy_id") or path.stem
                    record["name"] = record.get("type") or path.stem
                    record["concept"] = record.get("concept") or record.get("type")
                    strategies.append(record)
        self._strategy_cache = strategies
        return list(strategies)

    def _stored_contexts(self) -> list[dict[str, Any]]:
        if self._context_cache is not None:
            return list(self._context_cache)
        root = Path("runtime/memory/context_memory.json")
        contexts = []
        if root.exists():
            try:
                payload = json.loads(root.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                payload = {}
            stored_contexts = payload.get("contexts", {})
            if isinstance(stored_contexts, Mapping):
                iterable = stored_contexts.values()
            elif isinstance(stored_contexts, list):
                iterable = stored_contexts
            else:
                iterable = []
            for item in iterable:
                if not isinstance(item, Mapping):
                    continue
                source_context = item.get("source_context", {})
                source_context = (
                    source_context
                    if isinstance(source_context, Mapping)
                    else {}
                )
                record = {
                    **dict(source_context),
                    **dict(item),
                }
                context_id = (
                    record.get("context_id")
                    or record.get("context_name")
                    or record.get("context")
                )
                record["context_id"] = context_id
                record["name"] = context_id
                record["concept"] = (
                    record.get("concept")
                    or record.get("source_concept")
                    or record.get("context")
                    or context_id
                )
                contexts.append(record)
        self._context_cache = contexts
        return list(contexts)

    def _stored_programs(self) -> list[dict[str, Any]]:
        if self._program_cache is not None:
            return list(self._program_cache)
        programs = []
        try:
            from runtime.meta.supervisor.program_memory import ProgramMemory

            memory = ProgramMemory()
            records = memory.records
        except Exception:
            records = []
        for record in records:
            if getattr(record, "stale", False):
                continue
            if getattr(record, "validation_state", "") not in {
                "validated",
                "stable",
            }:
                continue
            if not getattr(record, "integrity_verified", False):
                continue
            metadata = getattr(record, "metadata", {}) or {}
            metadata = metadata if isinstance(metadata, Mapping) else {}
            program = getattr(record, "program", {}) or {}
            program = program if isinstance(program, Mapping) else {}
            operation_sequence = getattr(record, "operation_sequence", []) or []
            operations = [
                str(step.get("operator") or step.get("operation"))
                for step in operation_sequence
                if isinstance(step, Mapping)
                and (step.get("operator") or step.get("operation"))
            ]
            for step in program.get("program_steps", []) or program.get("steps", []):
                if not isinstance(step, Mapping):
                    continue
                operation = step.get("operator") or step.get("operation")
                if operation:
                    operations.append(str(operation))
            concept = (
                metadata.get("concept")
                or program.get("concept")
                or " ".join(operations)
                or getattr(record, "task_signature_id", "")
            )
            programs.append({
                "program_id": getattr(record, "program_id", ""),
                "task_signature_id": getattr(record, "task_signature_id", ""),
                "concept": concept,
                "name": concept,
                "confidence": getattr(record, "match_confidence", 0.0),
                "program": dict(program),
                "operation_sequence": operation_sequence,
                "validation_state": getattr(record, "validation_state", ""),
                "integrity_verified": getattr(record, "integrity_verified", False),
            })
        self._program_cache = programs
        return list(programs)


def _similarity(query: Mapping[str, Any] | str | None, candidate: Mapping[str, Any]) -> float:
    if isinstance(query, Mapping):
        concept = str(query.get("concept") or query.get("truth_name") or "")
        query_text = json.dumps(query, sort_keys=True, default=str)
    else:
        concept = str(query or "")
        query_text = concept
    candidate_concept = str(candidate.get("concept") or candidate.get("truth_name") or candidate.get("name") or "")
    score = 0.0
    if concept and candidate_concept and concept == candidate_concept:
        score += 0.65
    score += _overlap(query_text, json.dumps(candidate, sort_keys=True, default=str)) * 0.25
    score += _confidence(candidate) * 0.10
    return round(min(1.0, score), 4)


def _overlap(left: str, right: str) -> float:
    left_tokens = {token for token in left.lower().replace("_", " ").split() if len(token) > 2}
    right_tokens = {token for token in right.lower().replace("_", " ").split() if len(token) > 2}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _confidence(candidate: Mapping[str, Any]) -> float:
    for key in ("confidence", "truth_confidence", "support_score", "promotion_score"):
        try:
            return max(0.0, min(1.0, float(candidate.get(key, 0.0) or 0.0)))
        except (TypeError, ValueError):
            continue
    return 0.0


knowledge_reuse_engine = KnowledgeReuseEngine()


__all__ = ["KnowledgeReuseEngine", "knowledge_reuse_engine"]
