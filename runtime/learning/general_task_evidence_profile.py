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


class ExpectedSourceDescriptorBuilder:
    """Build pre-execution source expectations without claiming independence."""

    schema_version = "1.0"

    def build(
        self,
        metadata: Mapping[str, Any],
        *,
        evidence_types: Iterable[str],
        transformations: Iterable[str],
        validation_roles: Iterable[str],
    ) -> dict[str, Any]:
        evidence_types = [str(item) for item in evidence_types if item != "UNKNOWN"]
        transformations = [
            str(item) for item in transformations if item != "UNKNOWN"
        ]
        validation_roles = [
            str(item) for item in validation_roles if item != "UNKNOWN"
        ]
        lineage = self._expected_source_lineage(metadata)
        descriptor = {
            "schema_version": self.schema_version,
            "system": "expected_source_descriptor_builder",
            "producer_family": "validation",
            "producer_component": "VALIDATION_TASK_EXECUTION_PIPELINE",
            "producer_type": "scheduled_validation_task",
            "operation_family": transformations[0] if transformations else "UNKNOWN",
            "validation_method": evidence_types[0] if evidence_types else "UNKNOWN",
            "validation_lane": "scheduled_validation_task",
            "source_lineage_family": lineage[0] if lineage else "UNKNOWN",
            "expected_source_lineage": lineage or ["UNKNOWN"],
            "derivation_basis": {
                "producer_family": "VALIDATION_LANE_OWNED",
                "producer_component": "VALIDATION_LANE_OWNED",
                "producer_type": "VALIDATION_LANE_OWNED",
                "operation_family": (
                    "TASK_OWNED" if transformations else "UNKNOWN"
                ),
                "validation_method": (
                    "DERIVED" if evidence_types else "UNKNOWN"
                ),
                "validation_lane": "VALIDATION_LANE_OWNED",
                "source_lineage_family": "TASK_OWNED" if lineage else "UNKNOWN",
                "expected_source_lineage": "TASK_OWNED" if lineage else "UNKNOWN",
            },
            "provenance_confidence": (
                "MEDIUM" if lineage and evidence_types else "LOW"
                if evidence_types or validation_roles else "UNKNOWN"
            ),
            "task_identity_is_source_identity": False,
            "expected_source_is_realized_source": False,
            "grants_selection": False,
            "grants_evidence": False,
            "grants_truth": False,
            "grants_independence": False,
            **AUTHORITY,
        }
        descriptor["descriptor_id"] = self._descriptor_id(descriptor)
        return descriptor

    def _expected_source_lineage(self, metadata: Mapping[str, Any]) -> list[str]:
        lineage = []
        for key in (
            "expected_source_lineage",
            "source_lineage_targets",
            "candidate_source_targets",
        ):
            value = metadata.get(key)
            if isinstance(value, list):
                lineage.extend(str(item) for item in value if item not in (None, ""))
            elif value not in (None, ""):
                lineage.append(str(value))
        return sorted(set(lineage))

    def _descriptor_id(self, descriptor: Mapping[str, Any]) -> str:
        payload = {
            key: descriptor.get(key)
            for key in (
                "producer_family",
                "producer_component",
                "producer_type",
                "operation_family",
                "validation_method",
                "validation_lane",
                "expected_source_lineage",
            )
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return (
            "expected_source_descriptor_"
            f"{hashlib.sha1(encoded.encode()).hexdigest()[:12]}"
        )


class PreExecutionSourceDescriptorProviderDiscovery:
    """Forensic audit of possible pre-execution source descriptor providers."""

    schema_version = "1.0"

    PROVIDERS = [
        "CurriculumManager",
        "TrainingAssistant",
        "ValidationCurriculumRegistry",
        "ValidationTaskScheduler",
        "ExecutionPlanner",
        "CandidateProposalRuntime",
        "SemanticCompiler",
        "SynthesisSubsystem",
        "ToolSelection",
        "ValidationLane",
        "ProducerRegistry",
        "ExperimentProtocol",
        "ReusableLearnedObjectProvenance",
    ]

    FIELD_MATRIX = {
        "CurriculumManager": {
            "operation_family": "AUTHORITATIVELY_DECLARED",
            "validation_method": "POSSIBLE_ONLY",
        },
        "TrainingAssistant": {
            "operation_family": "DETERMINISTICALLY_DERIVED",
            "validation_method": "DETERMINISTICALLY_DERIVED",
            "expected_evidence_direction": "POSSIBLE_ONLY",
        },
        "ValidationCurriculumRegistry": {
            "validation_method": "AUTHORITATIVELY_DECLARED",
            "operation_family": "AUTHORITATIVELY_DECLARED",
            "validation_lane": "DETERMINISTICALLY_DERIVED",
        },
        "ValidationTaskScheduler": {
            "producer_family": "DETERMINISTICALLY_DERIVED",
            "producer_component": "DETERMINISTICALLY_DERIVED",
            "producer_type": "DETERMINISTICALLY_DERIVED",
            "validation_lane": "AUTHORITATIVELY_DECLARED",
            "expected_evidence_direction": "POSSIBLE_ONLY",
        },
        "ValidationLane": {
            "producer_family": "AUTHORITATIVELY_DECLARED",
            "producer_component": "AUTHORITATIVELY_DECLARED",
            "producer_type": "AUTHORITATIVELY_DECLARED",
            "validation_lane": "AUTHORITATIVELY_DECLARED",
        },
        "ExperimentProtocol": {
            "validation_method": "AUTHORITATIVELY_DECLARED",
            "expected_evidence_direction": "POSSIBLE_ONLY",
        },
        "ReusableLearnedObjectProvenance": {
            "source_lineage_family": "HISTORICALLY_INFERRED",
            "expected_upstream_lineage": "HISTORICALLY_INFERRED",
        },
    }

    FIELDS = [
        "producer_family",
        "producer_component",
        "producer_type",
        "operation_family",
        "validation_method",
        "validation_lane",
        "source_lineage_family",
        "expected_upstream_lineage",
        "expected_evidence_direction",
    ]

    def discover(self) -> dict[str, Any]:
        rows = []
        for provider in self.PROVIDERS:
            capabilities = {
                field: self.FIELD_MATRIX.get(provider, {}).get(field, "UNKNOWN")
                for field in self.FIELDS
            }
            legitimacy = self._legitimacy(provider, capabilities)
            rows.append({
                "provider_id": provider,
                "provider_type": self._provider_type(provider),
                "descriptor_fields": capabilities,
                "legitimate_descriptor_provider": legitimacy["legitimate"],
                "provider_rejection_reason": legitimacy["reason"],
                "temporal_scope": "PRE_EXECUTION",
                "authority": "NONE",
                "grants_selection": False,
                "grants_execution": False,
                "grants_evidence": False,
                "grants_truth": False,
                "grants_independence": False,
            })
        legitimate = [
            row for row in rows if row["legitimate_descriptor_provider"]
        ]
        lineage_capable = [
            row for row in legitimate
            if row["descriptor_fields"]["expected_upstream_lineage"]
            in {"AUTHORITATIVELY_DECLARED", "DETERMINISTICALLY_DERIVED"}
            or row["descriptor_fields"]["source_lineage_family"]
            in {"AUTHORITATIVELY_DECLARED", "DETERMINISTICALLY_DERIVED"}
        ]
        return {
            "schema_version": self.schema_version,
            "system": "pre_execution_source_descriptor_provider_discovery",
            "providers_inspected": [row["provider_id"] for row in rows],
            "provider_capability_matrix": rows,
            "legitimate_provider_found": bool(legitimate),
            "legitimate_provider_ids": [
                row["provider_id"] for row in legitimate
            ],
            "legitimate_lineage_provider_found": bool(lineage_capable),
            "legitimate_lineage_provider_ids": [
                row["provider_id"] for row in lineage_capable
            ],
            "decision_gate": (
                "R2-D_LEGITIMATE_PROVIDER_EXISTS_WITH_USEFUL_DISCRIMINATION"
                if lineage_capable
                else "R2-C_LEGITIMATE_PROVIDER_EXISTS_WITH_USEFUL_COVERAGE_BUT_LOW_DISCRIMINATION"
                if legitimate
                else "R2-A_NO_LEGITIMATE_PREEXECUTION_PROVIDER"
            ),
            "route_is_source_lineage": False,
            "historical_recurrence_grants_independence": False,
            "prediction_grants_epistemic_authority": False,
            **AUTHORITY,
        }

    def _legitimacy(
        self,
        provider: str,
        capabilities: Mapping[str, str],
    ) -> dict[str, Any]:
        known = {
            value for value in capabilities.values()
            if value not in {"UNKNOWN", "POSSIBLE_ONLY", "HISTORICALLY_INFERRED"}
        }
        if known:
            return {
                "legitimate": True,
                "reason": "pre_execution_descriptor_fields_owned_without_independence_claim",
            }
        if provider == "ReusableLearnedObjectProvenance":
            return {
                "legitimate": False,
                "reason": "historical_recurrence_is_prediction_not_pre_execution_authority",
            }
        return {
            "legitimate": False,
            "reason": "no_authoritative_or_deterministic_pre_execution_descriptor_fields",
        }

    def _provider_type(self, provider: str) -> str:
        if provider in {"ValidationLane", "ValidationTaskScheduler"}:
            return "VALIDATION_LANE_PROVIDER"
        if provider in {"CurriculumManager", "ValidationCurriculumRegistry"}:
            return "CURRICULUM_PROVIDER"
        if provider in {"ExecutionPlanner", "ToolSelection"}:
            return "ROUTE_PROVIDER"
        if provider == "ReusableLearnedObjectProvenance":
            return "HISTORICAL_PREDICTION_PROVIDER"
        return "RUNTIME_PROVIDER"


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
        validation_roles = sorted(set(
            self._list(metadata, "independent_validation_opportunities")
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
            "expected_producer_component": "DERIVED_FROM_VALIDATION_LANE",
            "expected_producer_type": "DERIVED_FROM_VALIDATION_LANE",
            "expected_operation": (
                "DECLARED_BY_TASK" if transformations else "UNKNOWN"
            ),
            "expected_method": (
                "DERIVED_FROM_DECLARED_TASK_METADATA"
                if evidence_types else "UNKNOWN"
            ),
            "expected_source_lineage": (
                "DECLARED_BY_TASK"
                if self._expected_source_lineage(metadata) else "UNKNOWN"
            ),
            "historical_source_lineage": "UNKNOWN",
            "previously_realized_source_identities": "UNKNOWN",
        }
        prior = self._selection_record(path.name, selection_memory)
        expected_lineage = self._expected_source_lineage(metadata)
        expected_source_descriptor = ExpectedSourceDescriptorBuilder().build(
            metadata,
            evidence_types=evidence_types,
            transformations=transformations,
            validation_roles=validation_roles,
        )
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
            "validation_roles": validation_roles or ["UNKNOWN"],
            "expected_source_descriptor": expected_source_descriptor,
            "source_descriptor_owner": expected_source_descriptor[
                "derivation_basis"
            ],
            "source_descriptor_confidence": expected_source_descriptor[
                "provenance_confidence"
            ],
            "expected_validation_lane": "scheduled_validation_task",
            "expected_producer_component": "VALIDATION_TASK_EXECUTION_PIPELINE",
            "expected_producer_type": "scheduled_validation_task",
            "expected_operation": transformations[0] if transformations else "UNKNOWN",
            "expected_method": evidence_types[0] if evidence_types else "UNKNOWN",
            "expected_source_lineage": expected_lineage or ["UNKNOWN"],
            "historical_source_lineage": ["UNKNOWN"],
            "previously_realized_source_identities": ["UNKNOWN"],
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
            "pre_selection_observability": {
                "task_identity": "DECLARED",
                "evidence_requirement_compatibility": (
                    "DERIVED" if evidence_types else "UNKNOWN"
                ),
                "expected_validation_category": (
                    "DERIVED" if evidence_types else "UNKNOWN"
                ),
                "expected_producer_component": "DERIVED",
                "expected_producer_type": "DERIVED",
                "expected_operation": "DECLARED" if transformations else "UNKNOWN",
                "expected_method": "DERIVED" if evidence_types else "UNKNOWN",
                "expected_source_lineage": (
                    "DECLARED" if expected_lineage else "UNKNOWN"
                ),
                "historical_source_lineage": "UNKNOWN",
                "previously_realized_source_identities": "UNKNOWN",
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

    def _expected_source_lineage(self, metadata: Mapping[str, Any]) -> list[str]:
        lineage = []
        for key in (
            "expected_source_lineage",
            "source_lineage_targets",
            "candidate_source_targets",
        ):
            lineage.extend(self._list(metadata, key))
        return sorted(set(lineage))

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


class IndependentSourcePotentialEvaluator:
    """Observation-only estimate of pre-execution independent source potential."""

    schema_version = "1.0"

    SCORE_BY_CLASS = {
        "HIGH_POTENTIAL": 1.0,
        "MODERATE_POTENTIAL": 0.65,
        "LOW_POTENTIAL": 0.2,
        "ALREADY_REPRESENTED_SOURCE": 0.0,
        "UNKNOWN": 0.0,
    }

    def evaluate(
        self,
        requirement: Mapping[str, Any],
        profile: Mapping[str, Any],
        match: Mapping[str, Any],
        source_coverage: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        coverage = source_coverage if isinstance(source_coverage, Mapping) else {}
        descriptor = profile.get("expected_source_descriptor")
        descriptor = descriptor if isinstance(descriptor, Mapping) else {}
        expected_lineage = {
            str(item)
            for item in (
                descriptor.get("expected_source_lineage")
                or profile.get("expected_source_lineage", [])
                or []
            )
            if item and item != "UNKNOWN"
        }
        represented_lineage = {
            str(lineage)
            for component in coverage.get("source_relation_components", []) or []
            if isinstance(component, Mapping)
            for member in component.get("members", []) or []
            if isinstance(member, Mapping)
            for lineage in member.get("lineage_roots", []) or []
            if lineage and lineage != "UNKNOWN"
        }
        represented_sources = {
            str(item)
            for item in coverage.get("source_identities", []) or []
            if item and item != "UNKNOWN"
        }
        match_strength = str(match.get("match_strength") or "UNKNOWN")
        if not match.get("eligible"):
            potential_class = "LOW_POTENTIAL" if match_strength == "NO_MATCH" else "UNKNOWN"
            reason = (
                "task_does_not_match_required_evidence"
                if match_strength == "NO_MATCH"
                else "evidence_or_source_potential_unknown"
            )
        elif not expected_lineage:
            potential_class = "UNKNOWN"
            reason = "expected_source_lineage_not_declared_pre_execution"
        elif expected_lineage & (represented_lineage | represented_sources):
            potential_class = "ALREADY_REPRESENTED_SOURCE"
            reason = "expected_source_lineage_already_represented"
        elif coverage.get("additional_independent_sources_required", 1) <= 0:
            potential_class = "LOW_POTENTIAL"
            reason = "independent_source_deficit_already_closed"
        elif match_strength == "EXACT_MATCH":
            potential_class = "HIGH_POTENTIAL"
            reason = "exact_evidence_match_with_unrepresented_declared_lineage"
        else:
            potential_class = "MODERATE_POTENTIAL"
            reason = "compatible_evidence_with_unrepresented_declared_lineage"
        return {
            "schema_version": self.schema_version,
            "system": "independent_source_potential_evaluator",
            "requirement_id": requirement.get("requirement_id"),
            "task_id": profile.get("task_id"),
            "potential_class": potential_class,
            "potential_score": self.SCORE_BY_CLASS[potential_class],
            "expected_marginal_contribution": (
                "POSSIBLE_NEW_INDEPENDENT_SOURCE"
                if potential_class in {"HIGH_POTENTIAL", "MODERATE_POTENTIAL"}
                else "NO_EXPECTED_NEW_SOURCE"
                if potential_class in {"LOW_POTENTIAL", "ALREADY_REPRESENTED_SOURCE"}
                else "UNKNOWN"
            ),
            "expected_source_lineage": sorted(expected_lineage) or ["UNKNOWN"],
            "expected_source_descriptor": descriptor or "UNKNOWN",
            "descriptor_confidence": descriptor.get(
                "provenance_confidence",
                profile.get("source_descriptor_confidence", "UNKNOWN"),
            ),
            "represented_lineage_overlap": sorted(
                expected_lineage & represented_lineage
            ),
            "represented_source_overlap": sorted(
                expected_lineage & represented_sources
            ),
            "potential_is_proven_independence": False,
            "reason": reason,
            **AUTHORITY,
        }


class MultiAxisEpistemicSelectionShadow:
    """Compare task-selection policies without changing production selection."""

    schema_version = "1.0"
    policy_names = [
        "production_baseline",
        "evidence_compatibility_only",
        "independent_source_potential_only",
        "lexicographic_evidence_source_operational",
        "operational_first_bounded_epistemic_tiebreak",
        "normalized_multi_objective_shadow",
    ]

    def policy_matrix(
        self,
        rows: Iterable[Mapping[str, Any]],
        *,
        selected_count: int,
        base_selected_tasks: Iterable[str],
    ) -> dict[str, Any]:
        base_selected = set(base_selected_tasks or [])
        source_rows = [dict(row) for row in rows]
        policies = {
            "production_baseline": self._rank(
                source_rows,
                [("base_score", True), ("base_rank", False), ("task_file", False)],
            ),
            "evidence_compatibility_only": self._rank(
                source_rows,
                [("evidence_compatibility", True), ("base_rank", False), ("task_file", False)],
            ),
            "independent_source_potential_only": self._rank(
                source_rows,
                [("independent_source_potential_score", True), ("base_rank", False), ("task_file", False)],
            ),
            "lexicographic_evidence_source_operational": self._rank(
                source_rows,
                [("evidence_compatibility", True), ("independent_source_potential_score", True), ("base_score", True), ("base_rank", False)],
            ),
            "operational_first_bounded_epistemic_tiebreak": self._rank(
                [
                    {
                        **row,
                        "_bounded_score": round(
                            float(row.get("base_score") or 0.0)
                            + min(
                                float(row.get("evidence_compatibility") or 0.0)
                                + float(row.get("independent_source_potential_score") or 0.0),
                                0.25,
                            ),
                            4,
                        ),
                    }
                    for row in source_rows
                ],
                [("_bounded_score", True), ("base_rank", False), ("task_file", False)],
            ),
            "normalized_multi_objective_shadow": self._rank(
                [
                    {
                        **row,
                        "_normalized_score": round(
                            self._normalized_base(row, source_rows) * 0.5
                            + float(row.get("evidence_compatibility") or 0.0) * 0.3
                            + float(row.get("independent_source_potential_score") or 0.0) * 0.2,
                            4,
                        ),
                    }
                    for row in source_rows
                ],
                [("_normalized_score", True), ("base_rank", False), ("task_file", False)],
            ),
        }
        matrix = {}
        for name, ranked in policies.items():
            selected = {row["task_file"] for row in ranked[:selected_count]}
            overlap = len(selected & base_selected)
            deltas = [
                abs(int(row.get("base_rank", 0) or 0) - index)
                for index, row in enumerate(ranked, start=1)
            ]
            matrix[name] = {
                "selected_tasks": sorted(selected),
                "top_k_overlap_with_production": overlap,
                "top_k_overlap_ratio": round(overlap / max(selected_count, 1), 4),
                "would_change_production_selection": selected != base_selected,
                "maximum_rank_delta": max(deltas) if deltas else 0,
                "policy_authority": "SHADOW_ONLY",
            }
        return {
            "schema_version": self.schema_version,
            "system": "multi_axis_epistemic_selection_shadow",
            "policies": matrix,
            "policy_count": len(matrix),
            "behavioral_integration_applied": False,
            "production_selector_changed": False,
            **AUTHORITY,
        }

    def distribution_report(self, rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        source_rows = [dict(row) for row in rows]
        return {
            "total_tasks": len(source_rows),
            "evidence_compatibility": dict(
                Counter(row.get("evidence_match_class") for row in source_rows)
            ),
            "source_potential": dict(
                Counter(row.get("independent_source_potential") for row in source_rows)
            ),
            "unknown_source_potential": sum(
                1
                for row in source_rows
                if row.get("independent_source_potential") == "UNKNOWN"
            ),
            "already_represented_sources": sum(
                1
                for row in source_rows
                if row.get("independent_source_potential")
                == "ALREADY_REPRESENTED_SOURCE"
            ),
            "high_potential": sum(
                1
                for row in source_rows
                if row.get("independent_source_potential") == "HIGH_POTENTIAL"
            ),
            "moderate_potential": sum(
                1
                for row in source_rows
                if row.get("independent_source_potential") == "MODERATE_POTENTIAL"
            ),
        }

    def _rank(self, rows: list[dict[str, Any]], keys: list[tuple[str, bool]]) -> list[dict[str, Any]]:
        def key(row):
            values = []
            for field, descending in keys:
                value = row.get(field, 0)
                if isinstance(value, (int, float)):
                    values.append(-float(value) if descending else float(value))
                else:
                    values.append(str(value))
            values.append(str(row.get("task_file")))
            return tuple(values)
        return sorted(rows, key=key)

    def _normalized_base(self, row: Mapping[str, Any], rows: list[dict[str, Any]]) -> float:
        maximum = max(float(item.get("base_score") or 0.0) for item in rows) if rows else 0.0
        if maximum <= 0:
            return 0.0
        return float(row.get("base_score") or 0.0) / maximum


def _split_token(value: str) -> list[str]:
    return [
        part
        for part in str(value).lower().replace("-", "_").split("_")
        if part
    ]


__all__ = [
    "AUTHORITY",
    "ExpectedSourceDescriptorBuilder",
    "GeneralTaskEvidenceProfileError",
    "GeneralTaskEvidenceProfiler",
    "IndependentSourcePotentialEvaluator",
    "MultiAxisEpistemicSelectionShadow",
    "PreExecutionSourceDescriptorProviderDiscovery",
    "TaskEvidenceMatcher",
]
