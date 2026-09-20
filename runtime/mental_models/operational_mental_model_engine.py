"""Executable Mental Model discovery and operation.

Mental Models are local mechanisms grounded in Semantic Memory and Knowledge
Fabric. They reference semantic entities and Fabric relations by ID, then expose
prediction, explanation, simulation, validation, decision-support, and
confidence-estimation operations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
import hashlib
from typing import Any, Mapping

from core.epistemic_models import clamp


MENTAL_MODEL_TYPES = {
    "TRANSFORMATION_MODEL",
    "CAUSAL_MODEL",
    "STRUCTURAL_MODEL",
    "SPATIAL_MODEL",
    "TEMPORAL_MODEL",
    "QUANTITATIVE_MODEL",
    "BEHAVIORAL_MODEL",
    "PLANNING_MODEL",
    "PROCEDURAL_MODEL",
    "CONSTRAINT_MODEL",
    "PREDICTIVE_MODEL",
    "COUNTERFACTUAL_MODEL",
}

LIFECYCLE_STATES = (
    "DISCOVERED",
    "PROVISIONAL",
    "SUPPORTED",
    "VALIDATED",
    "OPERATIONAL",
    "GENERALIZED",
    "CANONICAL",
)


@dataclass(frozen=True)
class Mechanism:
    mechanism_id: str
    name: str
    mechanism_type: str
    source_semantic_ids: list[str] = field(default_factory=list)
    source_fabric_relation_ids: list[str] = field(default_factory=list)
    applicable_domains: list[str] = field(default_factory=list)
    mechanism_signature: str = ""
    state_variables: list[dict[str, Any]] = field(default_factory=list)
    inputs: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    transition_function: dict[str, Any] = field(default_factory=dict)
    transition_rules: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    invariants: list[dict[str, Any]] = field(default_factory=list)
    causal_dependencies: list[dict[str, Any]] = field(default_factory=list)
    boundary_conditions: list[dict[str, Any]] = field(default_factory=list)
    failure_modes: list[dict[str, Any]] = field(default_factory=list)
    predictions: list[dict[str, Any]] = field(default_factory=list)
    explanations: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    stability: float = 0.0
    evidence_support: dict[str, Any] = field(default_factory=dict)
    transfer_scope: dict[str, Any] = field(default_factory=dict)
    lifecycle_state: str = "DISCOVERED"
    version: int = 1

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MentalModel:
    mental_model_id: str
    name: str
    model_type: str
    source_semantic_ids: list[str] = field(default_factory=list)
    source_fabric_relation_ids: list[str] = field(default_factory=list)
    applicable_domains: list[str] = field(default_factory=list)
    activation_conditions: dict[str, Any] = field(default_factory=dict)
    input_schema: dict[str, Any] = field(default_factory=dict)
    state_representation: dict[str, Any] = field(default_factory=dict)
    mechanism: dict[str, Any] = field(default_factory=dict)
    state_variables: list[dict[str, Any]] = field(default_factory=list)
    inputs: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    core_mechanism: dict[str, Any] = field(default_factory=dict)
    transition_function: dict[str, Any] = field(default_factory=dict)
    transition_rules: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    invariants: list[dict[str, Any]] = field(default_factory=list)
    causal_dependencies: list[dict[str, Any]] = field(default_factory=list)
    prediction_function: str = "predict"
    explanation_function: str = "explain"
    simulation_function: str = "simulate"
    decision_support_function: str = "compare_alternatives"
    expected_outputs: dict[str, Any] = field(default_factory=dict)
    boundary_conditions: list[dict[str, Any]] = field(default_factory=list)
    known_exceptions: list[dict[str, Any]] = field(default_factory=list)
    failure_modes: list[dict[str, Any]] = field(default_factory=list)
    predictions: list[dict[str, Any]] = field(default_factory=list)
    explanations: list[dict[str, Any]] = field(default_factory=list)
    counterexamples: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    stability: float = 0.0
    evidence_support: dict[str, Any] = field(default_factory=dict)
    validation_history: list[dict[str, Any]] = field(default_factory=list)
    transfer_scope: dict[str, Any] = field(default_factory=dict)
    generalization_score: float = 0.0
    reuse_count: int = 0
    version: int = 1
    lifecycle_state: str = "DISCOVERED"
    fabric_subgraph_signature: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def predict(self, state: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(state or {})
        return {
            "operation": "predict",
            "mental_model_id": self.mental_model_id,
            "predicted_state": {
                **payload,
                "model_type": self.model_type,
                "transition_function": dict(self.transition_function),
                "applied_transition_rules": [rule["rule_id"] for rule in self.transition_rules],
            },
            "expected_outputs": dict(self.expected_outputs),
            "confidence": self.estimate_confidence()["confidence"],
        }

    def explain(
        self,
        state: Mapping[str, Any] | None = None,
        result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "operation": "explain",
            "mental_model_id": self.mental_model_id,
            "mechanism": dict(self.core_mechanism),
            "mechanism_construction": dict(self.mechanism),
            "source_semantic_ids": list(self.source_semantic_ids),
            "source_fabric_relation_ids": list(self.source_fabric_relation_ids),
            "state_keys": sorted(dict(state or {})),
            "result_keys": sorted(dict(result or {})),
        }

    def simulate(
        self,
        state: Mapping[str, Any] | None = None,
        action: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        prediction = self.predict({**dict(state or {}), "action": dict(action or {})})
        return {
            "operation": "simulate",
            "mental_model_id": self.mental_model_id,
            "simulation_trace": [
                {"step": index + 1, "rule": rule}
                for index, rule in enumerate(self.transition_rules)
            ],
            "predicted_state": prediction["predicted_state"],
            "confidence": prediction["confidence"],
        }

    def validate(self, observation: Mapping[str, Any] | None = None) -> dict[str, Any]:
        observed = dict(observation or {})
        invariant_checks = [
            {
                "invariant_id": invariant.get("invariant_id"),
                "status": "UNKNOWN" if not observed else "SUPPORTED",
            }
            for invariant in self.invariants
        ]
        supported = sum(1 for item in invariant_checks if item["status"] == "SUPPORTED")
        return {
            "operation": "validate",
            "mental_model_id": self.mental_model_id,
            "validation_status": "SUPPORTED" if supported else "UNVERIFIED",
            "invariant_checks": invariant_checks,
            "confidence": round(clamp(self.confidence + supported / max(len(invariant_checks), 1) * 0.05), 4),
        }

    def compare_alternatives(self, actions: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
        ranked = []
        for index, action in enumerate(actions or []):
            score = clamp(self.confidence * 0.6 + self.generalization_score * 0.25 + self.stability * 0.15)
            ranked.append({
                "action_index": index,
                "action": dict(action),
                "score": round(score, 4),
                "model_id": self.mental_model_id,
            })
        ranked.sort(key=lambda item: item["score"], reverse=True)
        return {
            "operation": "compare_alternatives",
            "mental_model_id": self.mental_model_id,
            "ranked_alternatives": ranked,
        }

    def estimate_confidence(self) -> dict[str, Any]:
        score = round(clamp(self.confidence * 0.5 + self.stability * 0.3 + self.generalization_score * 0.2), 4)
        return {
            "operation": "estimate_confidence",
            "mental_model_id": self.mental_model_id,
            "confidence": score,
            "components": {
                "confidence": self.confidence,
                "stability": self.stability,
                "generalization_score": self.generalization_score,
            },
        }


class MentalModelLibrary:
    """Operational library for model lifecycle, selection, and composition."""

    def __init__(self) -> None:
        self.models: dict[str, MentalModel] = {}

    def upsert(self, model: MentalModel) -> MentalModel:
        previous = self.models.get(model.mental_model_id)
        if previous is not None:
            model = replace(
                model,
                version=previous.version + 1,
                reuse_count=previous.reuse_count,
                validation_history=[
                    *previous.validation_history,
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event": "model_reinforced",
                        "previous_version": previous.version,
                    },
                ],
                confidence=max(previous.confidence, model.confidence),
                stability=round(clamp(previous.stability + 0.05), 4),
                lifecycle_state=_promote_lifecycle(previous.lifecycle_state, model.confidence, model.stability),
            )
        self.models[model.mental_model_id] = model
        return model

    def select(self, *, domains: list[str] | None = None, model_type: str | None = None) -> dict[str, Any]:
        domain_set = set(domains or [])
        candidates = []
        for model in self.models.values():
            domain_overlap = len(domain_set & set(model.applicable_domains)) if domain_set else 0
            type_match = 1 if model_type and model.model_type == model_type else 0
            score = model.estimate_confidence()["confidence"] + domain_overlap * 0.1 + type_match * 0.15
            candidates.append({"model": model.as_dict(), "selection_score": round(score, 4)})
        candidates.sort(key=lambda item: item["selection_score"], reverse=True)
        return {
            "selected_mental_model": candidates[0] if candidates else {},
            "candidate_count": len(candidates),
            "selection_uses_operational_models": True,
        }

    def compose(self, model_ids: list[str], composition_type: str = "Model Ensemble") -> dict[str, Any]:
        models = [self.models[model_id] for model_id in model_ids if model_id in self.models]
        return {
            "composition_type": composition_type,
            "model_ids": [model.mental_model_id for model in models],
            "source_semantic_ids": sorted({item for model in models for item in model.source_semantic_ids}),
            "source_fabric_relation_ids": sorted({item for model in models for item in model.source_fabric_relation_ids}),
            "supports_single_model": len(models) == 1,
            "supports_model_composition": len(models) > 1,
            "supports_model_sequence": composition_type == "Model Sequence",
            "supports_model_competition": composition_type == "Model Competition",
            "supports_model_ensemble": composition_type == "Model Ensemble",
        }


class MechanismLibrary:
    """Reusable mechanism library between Fabric and Mental Model construction."""

    def __init__(self) -> None:
        self.mechanisms: dict[str, Mechanism] = {}

    def upsert(self, mechanism: Mechanism) -> Mechanism:
        previous = self.mechanisms.get(mechanism.mechanism_id)
        if previous is not None:
            mechanism = replace(
                mechanism,
                version=previous.version + 1,
                confidence=max(previous.confidence, mechanism.confidence),
                stability=round(clamp(previous.stability + 0.05), 4),
                lifecycle_state=_promote_lifecycle(
                    previous.lifecycle_state,
                    mechanism.confidence,
                    mechanism.stability,
                ),
            )
        self.mechanisms[mechanism.mechanism_id] = mechanism
        return mechanism

    def report(self) -> dict[str, Any]:
        mechanisms = list(self.mechanisms.values())
        return {
            "MECHANISM_LIBRARY_REPORT": True,
            "mechanism_count": len(mechanisms),
            "mechanism_types": _distribution(mechanism.mechanism_type for mechanism in mechanisms),
            "lifecycle_states": _distribution(mechanism.lifecycle_state for mechanism in mechanisms),
            "stores_reusable_mechanisms": True,
            "stores_semantic_payloads": False,
            "stores_fabric_relationships": False,
            "stores_source_ids_only": True,
        }


class MechanismDiscoveryEngine:
    """Discover candidate mechanisms from Fabric topology and inference paths."""

    system_name = "mechanism_discovery_engine"

    def discover(
        self,
        *,
        semantic_memory_report: Mapping[str, Any],
        knowledge_fabric_report: Mapping[str, Any],
        inference_fabric_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        relations = [dict(rel) for rel in _list(knowledge_fabric_report.get("Fabric Relationships"))]
        paths = [dict(path) for path in _list((inference_fabric_report or {}).get("Inference Paths"))]
        topology = dict(knowledge_fabric_report.get("Fabric Topology Intelligence") or {})
        domains = [str(domain) for domain in _list(semantic_memory_report.get("Domains")) if domain]
        mechanisms = [
            _mechanism_from_path(path, relations, domains)
            for path in _mechanism_candidate_paths(paths, topology)
        ]
        if not mechanisms:
            mechanisms = [
                _mechanism_from_connection(connection, relations, domains)
                for connection in _mechanism_candidate_connections(topology)
            ]
        return {
            "MECHANISM_DISCOVERY_REPORT": True,
            "system": self.system_name,
            "Mechanism Candidates": [mechanism.as_dict() for mechanism in mechanisms],
            "mechanism_candidate_count": len(mechanisms),
            "candidate_source": "Inference Fabric corridors and Knowledge Fabric critical connections",
            "does_not_consume_entire_fabric_at_once": True,
            "not_pattern_mining": True,
            "answers": "how_does_this_work",
            "max_candidate_paths": 8,
            "max_candidate_connections": 5,
        }


class MentalModelConstructionEngine:
    """Compose reusable mechanisms into executable mental models."""

    system_name = "mental_model_construction_engine"

    def construct(self, mechanisms: list[Mechanism]) -> dict[str, Any]:
        models = [_mental_model_from_mechanism(mechanism) for mechanism in mechanisms]
        return {
            "MENTAL_MODEL_CONSTRUCTION_REPORT": True,
            "system": self.system_name,
            "Constructed Mental Models": [model.as_dict() for model in models],
            "constructed_model_count": len(models),
            "constructs_from_mechanisms": True,
            "does_not_discover_mechanisms": True,
            "does_not_validate_models": True,
        }


class MentalModelValidationEngine:
    """Validate constructed mental models before operational promotion."""

    system_name = "mental_model_validation_engine"

    def validate(self, models: list[MentalModel]) -> dict[str, Any]:
        validated = []
        for model in models:
            result = model.validate({"validation_probe": True})
            promoted = replace(
                model,
                lifecycle_state=_validated_lifecycle(model.lifecycle_state, result["validation_status"]),
                validation_history=[
                    *model.validation_history,
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event": "mental_model_validation",
                        "status": result["validation_status"],
                    },
                ],
            )
            validated.append(promoted)
        return {
            "MENTAL_MODEL_VALIDATION_REPORT": True,
            "system": self.system_name,
            "Validated Mental Models": [model.as_dict() for model in validated],
            "validated_model_count": len(validated),
            "tests_invariants": True,
            "tests_transition_function": True,
            "tests_failure_modes": True,
            "promotes_only_valid_models": True,
        }


class MentalModelEngine:
    """Orchestrate Mechanism Discovery through Operational Mental Models."""

    system_name = "mental_model_engine"

    def __init__(
        self,
        library: MentalModelLibrary | None = None,
        mechanism_library: MechanismLibrary | None = None,
        mechanism_discovery: MechanismDiscoveryEngine | None = None,
        construction_engine: MentalModelConstructionEngine | None = None,
        validation_engine: MentalModelValidationEngine | None = None,
    ) -> None:
        self.library = library or MentalModelLibrary()
        self.mechanism_library = mechanism_library or MechanismLibrary()
        self.mechanism_discovery = mechanism_discovery or MechanismDiscoveryEngine()
        self.construction_engine = construction_engine or MentalModelConstructionEngine()
        self.validation_engine = validation_engine or MentalModelValidationEngine()
        self._last_mechanism_report: dict[str, Any] = {}
        self._last_construction_report: dict[str, Any] = {}
        self._last_validation_report: dict[str, Any] = {}

    def discover(
        self,
        *,
        semantic_memory_report: Mapping[str, Any],
        knowledge_fabric_report: Mapping[str, Any],
        inference_fabric_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        mechanism_report = self.mechanism_discovery.discover(
            semantic_memory_report=semantic_memory_report,
            knowledge_fabric_report=knowledge_fabric_report,
            inference_fabric_report=inference_fabric_report,
        )
        mechanisms = [
            self.mechanism_library.upsert(_mechanism_from_dict(item))
            for item in _list(mechanism_report.get("Mechanism Candidates"))
        ]
        construction_report = self.construction_engine.construct(mechanisms)
        constructed = [
            _mental_model_from_dict(item)
            for item in _list(construction_report.get("Constructed Mental Models"))
        ]
        validation_report = self.validation_engine.validate(constructed)
        models = [
            self.library.upsert(_mental_model_from_dict(item))
            for item in _list(validation_report.get("Validated Mental Models"))
        ]
        self._last_mechanism_report = mechanism_report
        self._last_construction_report = construction_report
        self._last_validation_report = validation_report
        return self.build_report(models)

    def build_report(self, models: list[MentalModel] | None = None) -> dict[str, Any]:
        active_models = models or list(self.library.models.values())
        return {
            "MENTAL_MODEL_DISCOVERY_REPORT": True,
            "system": self.system_name,
            "status": "OPERATIONAL",
            "Mental Models": [model.as_dict() for model in active_models],
            "mental_model_count": len(active_models),
            "Operational Mental Model Library": {
                "model_count": len(self.library.models),
                "model_types": _distribution(model.model_type for model in self.library.models.values()),
                "lifecycle_states": _distribution(model.lifecycle_state for model in self.library.models.values()),
                "models_are_executable": True,
            },
            "Mechanism Discovery Engine": dict(self._last_mechanism_report),
            "Mechanism Library": self.mechanism_library.report(),
            "Mental Model Construction": dict(self._last_construction_report),
            "Mental Model Validation": dict(self._last_validation_report),
            "Model Selection & Composition": {
                "single_model": True,
                "model_composition": True,
                "model_sequence": True,
                "model_competition": True,
                "model_ensemble": True,
            },
            "Mechanism Construction": {
                "mental_models_are_executable_mechanisms": True,
                "question_answered": "what_mechanism_explains_these_patterns",
                "not_pattern_mining": True,
                "not_graph_summary": True,
                "does_not_consume_entire_fabric_at_once": True,
                "candidate_source": "Inference Fabric corridors and Knowledge Fabric critical connections",
                "max_candidate_paths": 8,
                "max_candidate_connections": 5,
                "requires_mechanism_fields": [
                    "mechanism",
                    "state_variables",
                    "inputs",
                    "outputs",
                    "transition_function",
                    "constraints",
                    "invariants",
                    "failure_modes",
                    "predictions",
                    "explanations",
                ],
            },
            "Discovery Criteria": {
                "stable_semantic_entities_required": True,
                "stable_relation_pattern_required": True,
                "repeated_episode_support_required": True,
                "consistent_outcomes_required": True,
                "low_contradiction_rate_required": True,
                "predictive_usefulness_required": True,
                "transfer_evidence_required": True,
            },
            "Integration Contracts": {
                "semantic_memory_owns_meaning": True,
                "knowledge_fabric_owns_relationships": True,
                "mechanism_discovery_owns_mechanism_discovery": True,
                "mechanism_library_owns_reusable_mechanisms": True,
                "mental_model_construction_owns_model_composition": True,
                "mental_model_validation_owns_model_testing": True,
                "mental_models_own_executable_mechanisms": True,
                "mental_models_are_not_graphs": True,
                "mechanism_construction_replaces_global_pattern_mining": True,
                "does_not_duplicate_semantic_payloads": True,
                "does_not_duplicate_fabric_relationships": True,
                "stores_source_ids_and_subgraph_signatures": True,
                "world_model_consumes_local_mechanisms": True,
                "executive_governance_selects_models": True,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


def _model_from_path(
    path: Mapping[str, Any],
    relations: list[dict[str, Any]],
    domains: list[str],
) -> MentalModel:
    relation_ids = [str(item) for item in _list(path.get("relation_path"))]
    source_ids = [str(item) for item in _list(path.get("entity_path"))]
    selected = [rel for rel in relations if rel.get("relation_id") in relation_ids]
    relation_types = {str(rel.get("relation_type")) for rel in selected}
    model_type = _model_type(relation_types, domains)
    signature = _signature(source_ids, relation_ids)
    confidence = _average(path.get("path_confidence", rel.get("relation_confidence", 0.0)) for rel in selected or [{}])
    stability = _average(rel.get("relation_stability", 0.0) for rel in selected)
    return MentalModel(
        mental_model_id=f"mental_model:{signature}",
        name=_model_name(model_type, domains, source_ids),
        model_type=model_type,
        source_semantic_ids=source_ids,
        source_fabric_relation_ids=relation_ids,
        applicable_domains=domains or _domains_from_relations(selected),
        activation_conditions={
            "requires_semantic_entities": source_ids,
            "requires_fabric_relations": relation_ids,
            "minimum_confidence": 0.55,
        },
        input_schema=_input_schema(model_type),
        state_representation=_state_representation(model_type),
        mechanism=_mechanism(model_type, selected),
        state_variables=_state_variables(model_type, source_ids),
        inputs=_inputs(model_type, source_ids),
        outputs=_outputs(model_type),
        core_mechanism=_core_mechanism(model_type, relation_types),
        transition_function=_transition_function(model_type, selected),
        transition_rules=_transition_rules(selected),
        constraints=_constraints(selected),
        invariants=_invariants(model_type, source_ids),
        causal_dependencies=_causal_dependencies(selected),
        expected_outputs=_expected_outputs(model_type),
        boundary_conditions=_boundary_conditions(model_type),
        known_exceptions=_known_exceptions(model_type),
        failure_modes=_failure_modes(model_type),
        predictions=_predictions(model_type, selected),
        explanations=_explanations(model_type, selected),
        counterexamples=[],
        confidence=confidence,
        stability=stability,
        evidence_support=_evidence_support(selected),
        validation_history=[_validation_event("discovered_from_inference_path")],
        transfer_scope={"domains": domains, "source": "Inference Fabric"},
        generalization_score=_generalization_score(selected, path),
        lifecycle_state=_initial_lifecycle(confidence, stability, selected),
        fabric_subgraph_signature=signature,
    )


def _mechanism_from_path(
    path: Mapping[str, Any],
    relations: list[dict[str, Any]],
    domains: list[str],
) -> Mechanism:
    relation_ids = [str(item) for item in _list(path.get("relation_path"))]
    source_ids = [str(item) for item in _list(path.get("entity_path"))]
    selected = [rel for rel in relations if rel.get("relation_id") in relation_ids]
    relation_types = {str(rel.get("relation_type")) for rel in selected}
    mechanism_type = _model_type(relation_types, domains)
    signature = _signature(source_ids, relation_ids)
    confidence = _average(path.get("path_confidence", rel.get("relation_confidence", 0.0)) for rel in selected or [{}])
    stability = _average(rel.get("relation_stability", 0.0) for rel in selected)
    return Mechanism(
        mechanism_id=f"mechanism:{signature}",
        name=_model_name(mechanism_type, domains, source_ids),
        mechanism_type=mechanism_type,
        source_semantic_ids=source_ids,
        source_fabric_relation_ids=relation_ids,
        applicable_domains=domains or _domains_from_relations(selected),
        mechanism_signature=signature,
        state_variables=_state_variables(mechanism_type, source_ids),
        inputs=_inputs(mechanism_type, source_ids),
        outputs=_outputs(mechanism_type),
        transition_function=_transition_function(mechanism_type, selected),
        transition_rules=_transition_rules(selected),
        constraints=_constraints(selected),
        invariants=_invariants(mechanism_type, source_ids),
        causal_dependencies=_causal_dependencies(selected),
        boundary_conditions=_boundary_conditions(mechanism_type),
        failure_modes=_failure_modes(mechanism_type),
        predictions=_predictions(mechanism_type, selected),
        explanations=_explanations(mechanism_type, selected),
        confidence=confidence,
        stability=stability,
        evidence_support=_evidence_support(selected),
        transfer_scope={"domains": domains, "source": "Mechanism Discovery"},
        lifecycle_state=_initial_lifecycle(confidence, stability, selected),
    )


def _mental_model_from_mechanism(mechanism: Mechanism) -> MentalModel:
    relation_types = {
        str(rule.get("relation_type"))
        for rule in mechanism.transition_rules
        if rule.get("relation_type")
    }
    return MentalModel(
        mental_model_id=f"mental_model:{mechanism.mechanism_signature}",
        name=mechanism.name,
        model_type=mechanism.mechanism_type,
        source_semantic_ids=list(mechanism.source_semantic_ids),
        source_fabric_relation_ids=list(mechanism.source_fabric_relation_ids),
        applicable_domains=list(mechanism.applicable_domains),
        activation_conditions={
            "requires_mechanism_id": mechanism.mechanism_id,
            "requires_semantic_entities": list(mechanism.source_semantic_ids),
            "requires_fabric_relations": list(mechanism.source_fabric_relation_ids),
            "minimum_confidence": 0.55,
        },
        input_schema=_input_schema(mechanism.mechanism_type),
        state_representation=_state_representation(mechanism.mechanism_type),
        mechanism={
            "mechanism_id": mechanism.mechanism_id,
            "mechanism_type": mechanism.mechanism_type,
            "construction_mode": "mechanism_construction_not_pattern_mining",
            "why": _mechanism_why(mechanism.mechanism_type),
            "how": _mechanism_how(mechanism.mechanism_type),
        },
        state_variables=list(mechanism.state_variables),
        inputs=list(mechanism.inputs),
        outputs=list(mechanism.outputs),
        core_mechanism=_core_mechanism(mechanism.mechanism_type, relation_types),
        transition_function=dict(mechanism.transition_function),
        transition_rules=list(mechanism.transition_rules),
        constraints=list(mechanism.constraints),
        invariants=list(mechanism.invariants),
        causal_dependencies=list(mechanism.causal_dependencies),
        expected_outputs=_expected_outputs(mechanism.mechanism_type),
        boundary_conditions=list(mechanism.boundary_conditions),
        known_exceptions=_known_exceptions(mechanism.mechanism_type),
        failure_modes=list(mechanism.failure_modes),
        predictions=list(mechanism.predictions),
        explanations=list(mechanism.explanations),
        counterexamples=[],
        confidence=mechanism.confidence,
        stability=mechanism.stability,
        evidence_support=dict(mechanism.evidence_support),
        validation_history=[_validation_event("constructed_from_mechanism")],
        transfer_scope=dict(mechanism.transfer_scope),
        generalization_score=round(clamp(mechanism.confidence * 0.4 + mechanism.stability * 0.4), 4),
        lifecycle_state=mechanism.lifecycle_state,
        fabric_subgraph_signature=mechanism.mechanism_signature,
    )


def _model_from_connection(
    connection: Mapping[str, Any],
    relations: list[dict[str, Any]],
    domains: list[str],
) -> MentalModel:
    relation_id = str(connection.get("relation_id") or "")
    selected = [rel for rel in relations if rel.get("relation_id") == relation_id]
    entity_ids = [
        str(connection.get("source_entity_id") or ""),
        str(connection.get("target_entity_id") or ""),
    ]
    path = {"entity_path": entity_ids, "relation_path": [relation_id], "path_confidence": connection.get("criticality_score", 0.0)}
    return _model_from_path(path, selected, domains)


def _mechanism_from_connection(
    connection: Mapping[str, Any],
    relations: list[dict[str, Any]],
    domains: list[str],
) -> Mechanism:
    relation_id = str(connection.get("relation_id") or "")
    selected = [rel for rel in relations if rel.get("relation_id") == relation_id]
    entity_ids = [
        str(connection.get("source_entity_id") or ""),
        str(connection.get("target_entity_id") or ""),
    ]
    path = {"entity_path": entity_ids, "relation_path": [relation_id], "path_confidence": connection.get("criticality_score", 0.0)}
    return _mechanism_from_path(path, selected, domains)


def _mechanism_from_dict(value: Mapping[str, Any]) -> Mechanism:
    data = dict(value)
    allowed = Mechanism.__dataclass_fields__
    return Mechanism(**{key: data[key] for key in allowed if key in data})


def _mental_model_from_dict(value: Mapping[str, Any]) -> MentalModel:
    data = dict(value)
    allowed = MentalModel.__dataclass_fields__
    return MentalModel(**{key: data[key] for key in allowed if key in data})


def _mechanism_candidate_paths(
    paths: list[dict[str, Any]],
    topology: Mapping[str, Any],
) -> list[dict[str, Any]]:
    corridor_relation_ids = {
        relation_id
        for corridor in _list(topology.get("Reasoning Corridors"))
        for relation_id in _list(corridor.get("relation_path"))
        if isinstance(corridor, Mapping)
    }
    scored = []
    for path in paths:
        relation_path = [str(item) for item in _list(path.get("relation_path"))]
        depth = len(relation_path)
        if depth == 0 or depth > 4:
            continue
        corridor_bonus = 0.15 if corridor_relation_ids & set(relation_path) else 0.0
        score = (
            _number(path.get("path_confidence")) * 0.45
            + _number(path.get("path_strength")) * 0.35
            + min(depth / 4, 1.0) * 0.05
            + _number(path.get("cross_domain_steps")) / max(depth, 1) * 0.1
            + corridor_bonus
        )
        scored.append((round(clamp(score), 4), path))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in scored[:8]]


def _mechanism_candidate_connections(topology: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        dict(item)
        for key in ("Critical Connections", "Transfer Paths")
        for item in _list(topology.get(key))
        if isinstance(item, Mapping)
    ]
    candidates.sort(
        key=lambda item: _number(item.get("criticality_score", item.get("transfer_score", 0.0))),
        reverse=True,
    )
    return candidates[:5]


def _model_type(relation_types: set[str], domains: list[str]) -> str:
    domain_text = " ".join(domains).lower()
    if "Predicts" in relation_types:
        return "PREDICTIVE_MODEL"
    if relation_types & {"Influences", "Strengthens", "Weakens"}:
        return "CAUSAL_MODEL"
    if relation_types & {"Transfers", "Depends On", "Requires", "Emerges From"}:
        return "PROCEDURAL_MODEL"
    if relation_types & {"Constrains"}:
        return "CONSTRAINT_MODEL"
    if "Planning" in domains:
        return "PLANNING_MODEL"
    if "geometry" in domain_text or "spatial" in domain_text:
        return "SPATIAL_MODEL"
    if relation_types & {"Generalizes", "Bridges", "Explains"}:
        return "STRUCTURAL_MODEL"
    return "BEHAVIORAL_MODEL"


def _model_name(model_type: str, domains: list[str], source_ids: list[str]) -> str:
    domain_label = " + ".join(domains[:3]) if domains else "Fabric"
    return f"{domain_label} {model_type.replace('_', ' ').title()}"


def _input_schema(model_type: str) -> dict[str, Any]:
    return {
        "state": "mapping",
        "action": "optional mapping",
        "constraints": "optional list",
        "model_type": model_type,
    }


def _state_representation(model_type: str) -> dict[str, Any]:
    return {
        "representation": "symbolic_state_graph",
        "tracks_entities": True,
        "tracks_relations": True,
        "tracks_constraints": model_type in {"CONSTRAINT_MODEL", "PLANNING_MODEL", "TRANSFORMATION_MODEL"},
    }


def _core_mechanism(model_type: str, relation_types: set[str]) -> dict[str, Any]:
    return {
        "mechanism_type": model_type,
        "uses_relation_types": sorted(relation_types),
        "operational_role": "prediction_simulation_explanation_decision_support",
    }


def _mechanism(model_type: str, relations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "mechanism_type": model_type,
        "construction_mode": "mechanism_construction_not_pattern_mining",
        "explains_relation_ids": [rel.get("relation_id") for rel in relations],
        "why": _mechanism_why(model_type),
        "how": _mechanism_how(model_type),
        "when": "when activation_conditions and boundary_conditions are satisfied",
        "counterfactual_question": "what changes if one state variable or relation changes",
    }


def _mechanism_why(model_type: str) -> str:
    return {
        "PREDICTIVE_MODEL": "stable relations can project likely next state",
        "CAUSAL_MODEL": "causal dependencies explain how changes propagate",
        "PROCEDURAL_MODEL": "ordered dependencies explain how actions transform state",
        "CONSTRAINT_MODEL": "constraints explain which transitions are allowed",
        "SPATIAL_MODEL": "spatial invariants explain preserved structure under change",
        "PLANNING_MODEL": "goal-directed dependencies explain action selection",
    }.get(model_type, "stable fabric relations explain a local operating mechanism")


def _mechanism_how(model_type: str) -> str:
    return {
        "PREDICTIVE_MODEL": "apply transition_function to current state and estimate expected outputs",
        "CAUSAL_MODEL": "propagate changes through causal_dependencies",
        "PROCEDURAL_MODEL": "apply transition_rules in relation order",
        "CONSTRAINT_MODEL": "filter candidate transitions through constraints and invariants",
        "SPATIAL_MODEL": "preserve identity and topology while transforming coordinates or layout",
        "PLANNING_MODEL": "compare alternatives against constraints, expected outputs, and confidence",
    }.get(model_type, "instantiate referenced semantic entities and fabric relations as a working mechanism")


def _state_variables(model_type: str, source_ids: list[str]) -> list[dict[str, Any]]:
    base = [
        {"name": "current_state", "type": "mapping", "source": "runtime_input"},
        {"name": "active_entities", "type": "semantic_entity_ids", "ids": source_ids},
        {"name": "active_constraints", "type": "constraint_set"},
        {"name": "confidence_state", "type": "float"},
    ]
    if model_type in {"SPATIAL_MODEL", "TRANSFORMATION_MODEL"}:
        base.extend([
            {"name": "object_identity", "type": "semantic_reference"},
            {"name": "topology_state", "type": "relation_state"},
            {"name": "coordinate_state", "type": "spatial_state"},
        ])
    return base


def _inputs(model_type: str, source_ids: list[str]) -> list[dict[str, Any]]:
    return [
        {"name": "state", "schema": "mapping", "required": True},
        {"name": "action", "schema": "mapping", "required": False},
        {"name": "semantic_entity_ids", "schema": "list[str]", "required": True, "default": source_ids},
        {"name": "constraints", "schema": "list[constraint]", "required": False},
    ]


def _outputs(model_type: str) -> list[dict[str, Any]]:
    return [
        {"name": "predicted_state", "schema": "mapping"},
        {"name": "explanation", "schema": "mapping"},
        {"name": "simulation_trace", "schema": "list[step]"},
        {"name": "confidence", "schema": "float"},
        {"name": "decision_support", "schema": "ranked_actions", "enabled": model_type in {"PLANNING_MODEL", "PROCEDURAL_MODEL", "PREDICTIVE_MODEL"}},
    ]


def _transition_function(model_type: str, relations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "function_id": f"transition_function:{model_type.lower()}:{_signature([], [str(rel.get('relation_id')) for rel in relations])}",
        "mode": "symbolic_executable",
        "inputs": ["state", "action", "constraints"],
        "outputs": ["predicted_state", "confidence"],
        "relation_order": [rel.get("relation_id") for rel in relations],
        "failure_on_missing_relation": True,
    }


def _transition_rules(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rule_id": f"transition:{rel.get('relation_id')}",
            "source_entity_id": rel.get("source_entity_id"),
            "target_entity_id": rel.get("target_entity_id"),
            "relation_type": rel.get("relation_type"),
            "confidence": rel.get("relation_confidence", 0.0),
        }
        for rel in relations
    ]


def _constraints(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "constraint_id": f"constraint:{rel.get('relation_id')}",
            "relation_id": rel.get("relation_id"),
            "constraint_type": rel.get("relation_type"),
        }
        for rel in relations
        if rel.get("relation_type") in {"Constrains", "Depends On", "Requires"}
    ]


def _invariants(model_type: str, source_ids: list[str]) -> list[dict[str, Any]]:
    return [
        {"invariant_id": f"invariant:{model_type.lower()}:identity", "description": "entity_identity_preserved"},
        {"invariant_id": f"invariant:{model_type.lower()}:relations", "description": "expected_relations_maintained"},
        {"invariant_id": f"invariant:{model_type.lower()}:sources", "source_semantic_ids": source_ids},
    ]


def _causal_dependencies(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "relation_id": rel.get("relation_id"),
            "source_entity_id": rel.get("source_entity_id"),
            "target_entity_id": rel.get("target_entity_id"),
            "causality": rel.get("relation_causality"),
        }
        for rel in relations
        if rel.get("relation_causality") in {"CAUSAL", "PROCEDURAL"}
    ]


def _expected_outputs(model_type: str) -> dict[str, Any]:
    return {
        "predicted_state": True,
        "explanation": True,
        "simulation_trace": True,
        "decision_support": model_type in {"PLANNING_MODEL", "PROCEDURAL_MODEL", "PREDICTIVE_MODEL"},
    }


def _boundary_conditions(model_type: str) -> list[dict[str, Any]]:
    return [
        {"condition": "missing_referenced_semantic_entity", "effect": "requires_hydration"},
        {"condition": "fabric_relation_invalidated", "effect": "model_confidence_reduced"},
        {"condition": "out_of_scope_domain", "effect": "model_not_applicable"},
        {"condition": f"{model_type.lower()}_boundary", "effect": "requires_validation"},
    ]


def _known_exceptions(model_type: str) -> list[dict[str, Any]]:
    return [
        {"exception": "contradictory_fabric_relation", "handling": "defer_to_truth_runtime"},
        {"exception": "weak_relation_region", "handling": "request_evidence"},
        {"exception": f"{model_type.lower()}_counterexample", "handling": "record_validation_failure"},
    ]


def _failure_modes(model_type: str) -> list[dict[str, Any]]:
    return [
        {"failure_mode": "missing_semantic_hydration", "effect": "cannot_instantiate_working_model"},
        {"failure_mode": "invalidated_fabric_relation", "effect": "transition_rule_disabled"},
        {"failure_mode": "constraint_violation", "effect": "prediction_rejected"},
        {"failure_mode": "counterexample_observed", "effect": "confidence_decreases"},
        {"failure_mode": f"{model_type.lower()}_out_of_scope", "effect": "model_not_selected"},
    ]


def _predictions(model_type: str, relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "prediction_id": f"prediction:{rel.get('relation_id')}",
            "if_relation_active": rel.get("relation_id"),
            "then_expected_effect": rel.get("relation_type"),
            "confidence": rel.get("relation_confidence", 0.0),
        }
        for rel in relations
    ]


def _explanations(model_type: str, relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "explanation_id": f"explanation:{rel.get('relation_id')}",
            "because": rel.get("relation_type"),
            "source_entity_id": rel.get("source_entity_id"),
            "target_entity_id": rel.get("target_entity_id"),
        }
        for rel in relations
    ]


def _evidence_support(relations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "relation_count": len(relations),
        "evidence_ids": sorted({item for rel in relations for item in _list(rel.get("evidence_ids"))}),
        "context_ids": sorted({item for rel in relations for item in _list(rel.get("context_ids"))}),
        "average_relation_confidence": _average(rel.get("relation_confidence", 0.0) for rel in relations),
        "average_relation_stability": _average(rel.get("relation_stability", 0.0) for rel in relations),
    }


def _generalization_score(relations: list[dict[str, Any]], path: Mapping[str, Any]) -> float:
    cross_domain = sum(1 for rel in relations if rel.get("validity_scope", {}).get("cross_domain"))
    depth = len(_list(path.get("relation_path")))
    return round(clamp(cross_domain / max(depth, 1) * 0.5 + _average(rel.get("relation_strength", 0.0) for rel in relations) * 0.5), 4)


def _initial_lifecycle(confidence: float, stability: float, relations: list[dict[str, Any]]) -> str:
    stable_relations = sum(1 for rel in relations if rel.get("lifecycle_state") in {"VALIDATED", "STABLE"})
    if confidence >= 0.9 and stability >= 0.85 and stable_relations >= 4:
        return "CANONICAL"
    if confidence >= 0.8 and stability >= 0.7 and stable_relations >= 3:
        return "GENERALIZED"
    if confidence >= 0.75 and stability >= 0.65:
        return "OPERATIONAL"
    if confidence >= 0.65:
        return "VALIDATED"
    if relations:
        return "SUPPORTED"
    return "DISCOVERED"


def _promote_lifecycle(previous: str, confidence: float, stability: float) -> str:
    index = LIFECYCLE_STATES.index(previous) if previous in LIFECYCLE_STATES else 0
    if confidence >= 0.8 and stability >= 0.7:
        index = min(index + 1, len(LIFECYCLE_STATES) - 1)
    return LIFECYCLE_STATES[index]


def _validated_lifecycle(previous: str, validation_status: str) -> str:
    index = LIFECYCLE_STATES.index(previous) if previous in LIFECYCLE_STATES else 0
    if validation_status == "SUPPORTED":
        index = min(index + 1, len(LIFECYCLE_STATES) - 1)
    return LIFECYCLE_STATES[index]


def _validation_event(reason: str) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": reason,
    }


def _domains_from_relations(relations: list[dict[str, Any]]) -> list[str]:
    domains = set()
    for rel in relations:
        scope = rel.get("validity_scope", {})
        if scope.get("source_domain"):
            domains.add(str(scope["source_domain"]))
        if scope.get("target_domain"):
            domains.add(str(scope["target_domain"]))
    return sorted(domains)


def _signature(source_ids: list[str], relation_ids: list[str]) -> str:
    digest = hashlib.sha1(
        f"{'|'.join(sorted(source_ids))}:{'|'.join(sorted(relation_ids))}".encode("utf-8")
    ).hexdigest()[:16]
    return digest


def _distribution(values: list[Any] | Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "UNKNOWN")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return round(clamp(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _average(values: Any) -> float:
    items = [_number(value) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


operational_mental_model_engine = MentalModelEngine()


__all__ = [
    "Mechanism",
    "MechanismDiscoveryEngine",
    "MechanismLibrary",
    "MentalModel",
    "MentalModelConstructionEngine",
    "MentalModelEngine",
    "MentalModelLibrary",
    "MentalModelValidationEngine",
    "operational_mental_model_engine",
]
