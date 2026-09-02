from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


AUTHORITY = {
    "authority": "OBSERVATION_ONLY",
    "behavioral_authority": "NONE",
    "evidence_acceptance_authority": "NONE",
    "truth_authority": "NONE",
    "trust_authority": "NONE",
    "graduation_authority": "NONE",
    "execution_authority": "NONE",
    "selection_authority": "NONE",
}


class GeneralTaskEvidenceProfileError(ValueError):
    """Raised when a task profile or evidence requirement is malformed."""


class GeneralTaskEvidenceProfiler:
    """Build descriptive evidence-capability profiles for general training tasks."""

    schema_version = "1.0"

    EVIDENCE_TYPE_BY_TERM = {
        "cross_source_consensus_evidence": {
            "cross_source_consensus_evidence",
            "independent_task_validation",
            "cross_domain_validation",
            "governed_validation",
        },
        "independent_replication_evidence": {
            "replication",
            "independent_task_validation",
            "cross_task_replication",
        },
        "causal_alignment_evidence": {
            "causal_alignment",
            "causal_validation",
            "world_model_validation",
        },
        "contradiction_resolution_evidence": {
            "contradiction_resolution",
            "negative_control",
            "counterexample",
        },
    }

    def profile_task(
        self,
        task_file: str | Path,
        *,
        task_directory: str | Path | None = None,
        selection_memory: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = self._resolve_path(task_file, task_directory)
        payload = self._read_task(path)
        metadata = payload.get("nexryn_metadata")
        metadata = metadata if isinstance(metadata, Mapping) else {}
        task_id = str(metadata.get("task_id") or path.stem)
        task_terms = self._terms_from_task(payload, metadata)
        evidence_types = sorted(
            evidence_type
            for evidence_type, terms in self.EVIDENCE_TYPE_BY_TERM.items()
            if task_terms & terms
        )
        semantic_capabilities = self._list(metadata, "required_operational_capabilities")
        transformations = sorted(set(
            self._list(payload, "expected_transformations")
            + self._list(metadata, "composite_capabilities")
            + self._list(metadata, "capability_graduation_targets")
        ))
        concepts = sorted(set(
            self._list(metadata, "target_concepts")
            + self._list(payload, "concept_labels")
        ))
        profile_sources = {
            "semantic_capabilities": (
                "DECLARED_BY_TASK"
                if semantic_capabilities else "UNKNOWN"
            ),
            "transformations_exercised": (
                "DECLARED_BY_TASK"
                if transformations else "UNKNOWN"
            ),
            "claim_domains": (
                "DECLARED_BY_TASK"
                if metadata.get("target_domains") else "DERIVED_FROM_TASK_STRUCTURE"
                if payload.get("concept_family") else "UNKNOWN"
            ),
            "evidence_types_potentially_supported": (
                "DERIVED_FROM_DECLARED_TASK_METADATA"
                if evidence_types else "UNKNOWN"
            ),
        }
        prior = self._selection_record(path.name, selection_memory)
        return {
            "schema_version": self.schema_version,
            "profile_id": self._profile_id(task_id, path),
            "task_id": task_id,
            "task_file": path.name,
            "task_path": str(path),
            "selectable": True,
            "classification": self._classification(path.name, metadata),
            "corpus_family": self._corpus_family(path.name, metadata, payload),
            "task_type": "arc_grid_task" if payload.get("train") else "UNKNOWN",
            "semantic_capabilities": semantic_capabilities or ["UNKNOWN"],
            "transformations_exercised": transformations or ["UNKNOWN"],
            "concepts": concepts or ["UNKNOWN"],
            "claim_domains": sorted(set(self._list(metadata, "target_domains"))) or [
                payload.get("concept_family") or "UNKNOWN"
            ],
            "evidence_types_potentially_supported": evidence_types or ["UNKNOWN"],
            "validation_roles": sorted(set(
                self._list(metadata, "independent_validation_opportunities")
            )) or ["UNKNOWN"],
            "known_baseline_sensitivity": (
                "NEGATIVE_CONTROLS_DECLARED"
                if payload.get("negative_controls") else "UNKNOWN"
            ),
            "known_repair_dependency": "UNKNOWN",
            "profile_source": profile_sources,
            "profile_confidence": self._confidence(metadata, evidence_types),
            "prior_selection_count": prior["prior_selection_count"],
            "prior_execution_count": "UNKNOWN",
            "prior_evidence_contribution": "UNKNOWN",
            "provenance": {
                "profile_builder": "general_task_evidence_profiler",
                "task_file": path.name,
                "metadata_present": bool(metadata),
                "declared_metadata_only": True,
                "historical_execution_does_not_rewrite_static_task": True,
            },
            **AUTHORITY,
        }

    def profile_corpus(
        self,
        task_files: Iterable[str | Path],
        *,
        task_directory: str | Path | None = None,
        selection_memory: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            self.profile_task(
                task_file,
                task_directory=task_directory,
                selection_memory=selection_memory,
            )
            for task_file in sorted(task_files, key=lambda item: str(item))
        ]

    def _resolve_path(self, task_file: str | Path, task_directory: str | Path | None) -> Path:
        path = Path(task_file)
        if task_directory is not None and not path.is_absolute():
            path = Path(task_directory) / path
        return path

    def _read_task(self, path: Path) -> dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise GeneralTaskEvidenceProfileError(
                f"cannot read task profile source {path}: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise GeneralTaskEvidenceProfileError("task payload must be a mapping")
        return payload

    def _list(self, mapping: Mapping[str, Any], key: str) -> list[str]:
        value = mapping.get(key)
        if isinstance(value, list):
            return [str(item) for item in value if item not in (None, "")]
        if value not in (None, ""):
            return [str(value)]
        return []

    def _terms_from_task(
        self,
        payload: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> set[str]:
        terms = set()

        def visit(value: Any) -> None:
            if isinstance(value, Mapping):
                for key, item in value.items():
                    visit(key)
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
            elif value is not None:
                term = str(value).strip().lower().replace(" ", "_").replace("-", "_")
                if term:
                    terms.add(term)

        for key in (
            "target_concepts",
            "target_domains",
            "required_operational_capabilities",
            "composite_capabilities",
            "capability_graduation_targets",
            "independent_validation_opportunities",
            "curriculum_diagnostics_tags",
            "deficiency_targets",
            "required_evidence",
            "evidence_targets",
        ):
            visit(metadata.get(key))
        for key in ("concept_family", "concept_labels", "expected_transformations"):
            visit(payload.get(key))
        if payload.get("negative_controls"):
            terms.add("negative_control")
        return terms

    def _classification(self, filename: str, metadata: Mapping[str, Any]) -> str:
        if metadata.get("validation_only") is True:
            return "VALIDATION_ONLY"
        if filename.startswith("elite_cognitive_task_"):
            return "SELECTABLE"
        if metadata or filename.startswith("arc_concept_"):
            return "SELECTABLE"
        return "SELECTABLE"

    def _corpus_family(
        self,
        filename: str,
        metadata: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> str:
        curriculum = str(metadata.get("curriculum") or "")
        if filename.startswith("elite_cognitive_task_"):
            return "elite"
        if filename.startswith("arc_concept_"):
            return "ARC concept"
        if curriculum:
            return curriculum
        if payload.get("concept_family"):
            return "ARC concept"
        return "generated"

    def _confidence(self, metadata: Mapping[str, Any], evidence_types: list[str]) -> str:
        if metadata and evidence_types:
            return "MEDIUM"
        if metadata:
            return "LOW"
        return "UNKNOWN"

    def _profile_id(self, task_id: str, path: Path) -> str:
        payload = {
            "schema_version": self.schema_version,
            "task_id": task_id,
            "task_file": path.name,
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return f"general_task_evidence_profile_{hashlib.sha1(encoded.encode()).hexdigest()[:12]}"

    def _selection_record(
        self,
        filename: str,
        selection_memory: Mapping[str, Any] | None,
    ) -> dict[str, int]:
        memory = selection_memory if isinstance(selection_memory, Mapping) else {}
        tasks = memory.get("tasks") if isinstance(memory.get("tasks"), Mapping) else {}
        record = tasks.get(filename) if isinstance(tasks.get(filename), Mapping) else {}
        return {"prior_selection_count": int(record.get("times_selected", 0) or 0)}


class TaskEvidenceMatcher:
    """Advisory matcher from required evidence to task profiles."""

    schema_version = "1.0"

    def match(
        self,
        requirement: Mapping[str, Any],
        profile: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(requirement, Mapping):
            raise GeneralTaskEvidenceProfileError("requirement must be a mapping")
        evidence_type = str(
            requirement.get("evidence_type")
            or requirement.get("required_evidence")
            or ""
        ).strip()
        if not evidence_type:
            raise GeneralTaskEvidenceProfileError("requirement evidence_type missing")
        profile_types = [
            str(item)
            for item in profile.get("evidence_types_potentially_supported", [])
            if item != "UNKNOWN"
        ]
        profile_concepts = [
            str(item)
            for item in profile.get("concepts", [])
            if item != "UNKNOWN"
        ]
        required_domains = {
            str(item).lower()
            for item in requirement.get("claim_domains", []) or []
            if item
        }
        profile_domains = {
            str(item).lower()
            for item in profile.get("claim_domains", []) or []
            if item != "UNKNOWN"
        }
        exact = evidence_type in profile_types
        domain_overlap = bool(required_domains & profile_domains)
        concept_overlap = bool(
            set(_split_token(evidence_type)) & set().union(*[
                set(_split_token(concept)) for concept in profile_concepts
            ])
            if profile_concepts else False
        )
        if exact and domain_overlap:
            strength = "EXACT_MATCH"
            score = 1.0
        elif exact:
            strength = "STRONG_MATCH"
            score = 0.82
        elif domain_overlap and concept_overlap:
            strength = "PARTIAL_MATCH"
            score = 0.55
        elif profile_types:
            strength = "NO_MATCH"
            score = 0.0
        else:
            strength = "UNKNOWN"
            score = 0.0
        return {
            "schema_version": self.schema_version,
            "task_id": profile.get("task_id"),
            "requirement_id": requirement.get("requirement_id", evidence_type),
            "required_evidence": evidence_type,
            "eligible": strength in {"EXACT_MATCH", "STRONG_MATCH", "PARTIAL_MATCH"},
            "compatibility_score": score,
            "match_strength": strength,
            "matched_requirements": [evidence_type] if exact else [],
            "unmet_requirements": [] if exact else [evidence_type],
            "mapping_confidence": profile.get("profile_confidence", "UNKNOWN"),
            "match_provenance": {
                "matcher": "task_evidence_matcher",
                "evidence_type_source": "REQUIRED_EVIDENCE",
                "profile_source": profile.get("profile_source", {}),
                "advisory_only": True,
            },
            **AUTHORITY,
        }

    def coverage_report(
        self,
        requirement: Mapping[str, Any],
        profiles: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        selectable = list(profiles)
        rows = [self.match(requirement, profile) for profile in selectable]
        return {
            "schema_version": self.schema_version,
            "requirement_id": requirement.get("requirement_id"),
            "evidence_type": requirement.get("evidence_type")
            or requirement.get("required_evidence"),
            "target_claim_id": requirement.get("target_claim_id")
            or requirement.get("claim_id"),
            "total_selectable_tasks": len(selectable),
            "compatible_tasks": sum(1 for row in rows if row["eligible"]),
            "strong_matches": sum(
                1 for row in rows if row["match_strength"] in {"EXACT_MATCH", "STRONG_MATCH"}
            ),
            "previously_executed_matches": "UNKNOWN",
            "never_executed_matches": "UNKNOWN",
            "evidence_producing_matches": "UNKNOWN",
            "independent_source_potential": sum(1 for row in rows if row["eligible"]),
            "match_strength_counts": dict(Counter(row["match_strength"] for row in rows)),
            "matches": rows,
            **AUTHORITY,
        }


def _split_token(value: str) -> list[str]:
    return [
        part
        for part in str(value).lower().replace("-", "_").split("_")
        if part
    ]


__all__ = [
    "AUTHORITY",
    "GeneralTaskEvidenceProfileError",
    "GeneralTaskEvidenceProfiler",
    "TaskEvidenceMatcher",
]
