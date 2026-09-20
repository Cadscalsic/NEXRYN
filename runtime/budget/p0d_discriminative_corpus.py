"""P0d design helpers for budget-discriminative corpus selection.

The helpers in this module describe experimental metadata only. They do not
route production work, promote truth, or allocate runtime budget.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from runtime.budget.budget_ablation_experiment import (
    PRODUCTION_DEFAULT_DEPTH,
    PRODUCTION_DEFAULT_ROUTES,
    UNAVAILABLE,
)
from runtime.budget.experimental_budget_authority import EXPERIMENTAL_BUDGET_SOURCE
from runtime.budget.experimental_resource_collector import (
    canonical_task_set_fingerprint,
    state_surface_fingerprint,
    validate_realized_usage_within_effective_ceiling,
)


DEMAND_VALUES = frozenset({"LOW", "MEDIUM", "HIGH", "UNKNOWN"})
P0D_INITIAL_SCREENING_CONFIGS: tuple[str, ...] = ("1/1", "2/2", "3/3", "4/4")
P0D_STATE_SURFACES: tuple[str, ...] = (
    "runtime/artifacts/runtime_data",
    "runtime/state/evidence_acquisition_plans",
    "runtime/memory",
    "memory",
    "runtime/cache",
)


class P0dCorpusContractError(ValueError):
    """Raised when P0d design metadata violates the experimental contract."""


@dataclass(frozen=True)
class FrozenP0dCorpus:
    task_set_fingerprint: str
    selected_tasks: tuple[Mapping[str, Any], ...]


def inventory_task_file(task_path: str | Path, *, task_source: str) -> dict[str, Any]:
    path = Path(task_path)
    payload = _read_task_payload(path)
    train = payload.get("train") if isinstance(payload.get("train"), list) else []
    test = payload.get("test") if isinstance(payload.get("test"), list) else []
    metadata = payload.get("nexryn_metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    grid_summary = _grid_summary(train, test)
    characteristics = _characteristics(metadata, grid_summary)
    profile = cognitive_demand_profile(
        task_id=str(metadata.get("task_id") or path.name),
        metadata=metadata,
        grid_summary=grid_summary,
        characteristics=characteristics,
    )
    return {
        "task_id": str(metadata.get("task_id") or path.name),
        "task_file": path.as_posix(),
        "task_source": str(task_source),
        "task_family": _task_family(metadata, characteristics),
        "input_dimensions": grid_summary["input_dimensions"],
        "output_dimensions": grid_summary["output_dimensions"],
        "number_of_training_examples": len(train),
        "number_of_test_examples": len(test),
        "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "characteristics": characteristics,
        "cognitive_demand_profile": profile,
        "experimental_metadata_only": True,
        "provenance": {
            "identity_source": (
                "nexryn_metadata.task_id" if metadata.get("task_id") else "task_file_name"
            ),
            "classification_source": "task_content_and_nexryn_metadata",
        },
    }


def inventory_task_corpus(
    task_paths: Iterable[str | Path],
    *,
    task_source: str,
) -> list[dict[str, Any]]:
    return [
        inventory_task_file(path, task_source=task_source)
        for path in sorted((Path(item) for item in task_paths), key=lambda item: item.name)
    ]


def cognitive_demand_profile(
    *,
    task_id: str,
    metadata: Mapping[str, Any] | None = None,
    grid_summary: Mapping[str, Any] | None = None,
    characteristics: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Mapping[str, Any]]:
    metadata = metadata if isinstance(metadata, Mapping) else {}
    grid_summary = grid_summary if isinstance(grid_summary, Mapping) else {}
    characteristics = characteristics if isinstance(characteristics, Mapping) else {}
    domain_count = _int(metadata.get("domain_count"))
    changed_ratio = _float(grid_summary.get("changed_cell_ratio"))
    max_area = _int(grid_summary.get("max_grid_area"))
    multiple_strategies = metadata.get("multiple_valid_solution_strategies") is True
    multi_step = metadata.get("multi_step_reasoning") is True or _char_is_yes(
        characteristics,
        "multi_step_reasoning",
    )
    program_required = (
        metadata.get("program_composition_required") is True
        or "program_generation" in _strings(metadata.get("required_operational_capabilities"))
        or _char_is_yes(characteristics, "program_synthesis_dependency")
    )

    profile = {
        "route_demand": _dimension(
            "HIGH" if multiple_strategies else ("MEDIUM" if domain_count >= 3 else "LOW"),
            evidence="multiple solution strategies or domain breadth"
            if multiple_strategies or domain_count
            else "single-source structured task with no route pressure evidence",
            source=f"{task_id}:nexryn_metadata",
            confidence="MEDIUM" if multiple_strategies or domain_count else "LOW",
        ),
        "depth_demand": _dimension(
            "HIGH" if multi_step and domain_count >= 4 else ("MEDIUM" if multi_step else "LOW"),
            evidence="multi-step metadata and domain count"
            if multi_step
            else "no explicit multi-step evidence in content or metadata",
            source=f"{task_id}:task_content_and_metadata",
            confidence="HIGH" if multi_step else "LOW",
        ),
        "transformation_composition": _dimension(
            "HIGH"
            if metadata.get("operational_capability_composition_required") is True
            else ("MEDIUM" if changed_ratio >= 0.15 else "LOW"),
            evidence="capability composition metadata or observed train input-output change",
            source=f"{task_id}:task_content_and_metadata",
            confidence="HIGH"
            if metadata.get("operational_capability_composition_required") is True
            else "LOW",
        ),
        "candidate_ambiguity": _dimension(
            "HIGH" if multiple_strategies else "UNKNOWN",
            evidence="multiple_valid_solution_strategies metadata"
            if multiple_strategies
            else "no canonical candidate-count evidence before measurement",
            source=f"{task_id}:nexryn_metadata",
            confidence="HIGH" if multiple_strategies else "LOW",
        ),
        "repair_pressure": _dimension(
            "MEDIUM"
            if _contains_any(metadata.get("deficiency_targets"), ("validation", "gap", "yield"))
            else "UNKNOWN",
            evidence="deficiency target metadata references validation/yield gaps"
            if _contains_any(metadata.get("deficiency_targets"), ("validation", "gap", "yield"))
            else "no repair telemetry available before measurement",
            source=f"{task_id}:nexryn_metadata",
            confidence="MEDIUM"
            if _contains_any(metadata.get("deficiency_targets"), ("validation", "gap", "yield"))
            else "LOW",
        ),
        "program_dependency": _dimension(
            "HIGH" if program_required else "UNKNOWN",
            evidence="program/composition capability metadata"
            if program_required
            else "no explicit program dependency evidence",
            source=f"{task_id}:nexryn_metadata",
            confidence="HIGH" if program_required else "LOW",
        ),
        "semantic_novelty": _dimension(
            "HIGH"
            if metadata.get("novel_abstraction_required") is True
            else ("MEDIUM" if max_area >= 100 else "LOW"),
            evidence="novel abstraction metadata or large grid search surface",
            source=f"{task_id}:task_content_and_metadata",
            confidence="HIGH"
            if metadata.get("novel_abstraction_required") is True
            else "LOW",
        ),
        "cross_concept_interaction": _dimension(
            "HIGH" if domain_count >= 4 else ("MEDIUM" if domain_count >= 2 else "UNKNOWN"),
            evidence="metadata domain_count"
            if domain_count
            else "no domain-interaction metadata",
            source=f"{task_id}:nexryn_metadata",
            confidence="HIGH" if domain_count >= 4 else ("MEDIUM" if domain_count else "LOW"),
        ),
    }
    validate_demand_profile(profile)
    return profile


def validate_demand_profile(profile: Mapping[str, Any]) -> None:
    required = {
        "route_demand",
        "depth_demand",
        "transformation_composition",
        "candidate_ambiguity",
        "repair_pressure",
        "program_dependency",
        "semantic_novelty",
        "cross_concept_interaction",
    }
    missing = required - set(profile)
    if missing:
        raise P0dCorpusContractError(f"missing demand dimensions: {sorted(missing)}")
    for name in required:
        item = profile.get(name)
        if not isinstance(item, Mapping):
            raise P0dCorpusContractError(f"{name} must be a mapping")
        if item.get("value") not in DEMAND_VALUES:
            raise P0dCorpusContractError(f"{name} has invalid demand value")
        if not str(item.get("evidence") or "").strip():
            raise P0dCorpusContractError(f"{name} requires evidence")
        if not str(item.get("source") or "").strip():
            raise P0dCorpusContractError(f"{name} requires source")
        if not str(item.get("confidence") or "").strip():
            raise P0dCorpusContractError(f"{name} requires confidence")


def freeze_discriminative_corpus(
    inventory: Iterable[Mapping[str, Any]],
    selected_task_ids: Sequence[str],
) -> FrozenP0dCorpus:
    by_id = {str(item.get("task_id")): item for item in inventory if item.get("task_id")}
    frozen = []
    seen: set[str] = set()
    for task_id in selected_task_ids:
        if task_id in seen:
            raise P0dCorpusContractError(f"duplicate selected task: {task_id}")
        if task_id not in by_id:
            raise P0dCorpusContractError(f"selected task not present in inventory: {task_id}")
        seen.add(task_id)
        task = dict(by_id[task_id])
        task_file = str(task.get("task_file") or "")
        if not task_file:
            raise P0dCorpusContractError(f"selected task has no task_file: {task_id}")
        frozen.append(_freeze_mapping(task))
    fingerprint = canonical_task_set_fingerprint(
        [str(item["task_file"]) for item in frozen]
    )["task_set_fingerprint"]
    return FrozenP0dCorpus(
        task_set_fingerprint=fingerprint,
        selected_tasks=tuple(frozen),
    )


def create_state_snapshot(
    *,
    repository_root: str | Path,
    snapshot_root: str | Path,
    state_surfaces: Iterable[str | Path] = P0D_STATE_SURFACES,
) -> dict[str, Any]:
    repository_root = Path(repository_root)
    snapshot_root = Path(snapshot_root)
    if snapshot_root.exists():
        raise P0dCorpusContractError("snapshot_root already exists")
    for surface in state_surfaces:
        source = repository_root / surface
        target = snapshot_root / surface
        if source.is_dir():
            shutil.copytree(source, target)
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return state_surface_fingerprint(root=snapshot_root, surfaces=state_surfaces)


def validate_state_fingerprint(
    *,
    repository_root: str | Path,
    state_surfaces: Iterable[str | Path],
    expected_state_fingerprint: str,
) -> dict[str, Any]:
    observed = state_surface_fingerprint(root=repository_root, surfaces=state_surfaces)
    return {
        "expected_state_fingerprint": expected_state_fingerprint,
        "observed_state_fingerprint": observed["state_fingerprint"],
        "valid": observed["state_fingerprint"] == expected_state_fingerprint,
        "state_identity_entries": observed["state_identity_entries"],
    }


def validate_budget_authority_measurement(measurement: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if measurement.get("authority_source") != EXPERIMENTAL_BUDGET_SOURCE:
        failures.append("AUTHORITY_SOURCE_NOT_EXPERIMENTAL_BUDGET_GRANT")
    pairs = (
        ("requested_max_active_routes", "granted_max_active_routes", "effective_max_active_routes"),
        (
            "requested_max_reasoning_depth",
            "granted_max_reasoning_depth",
            "effective_max_reasoning_depth",
        ),
    )
    for requested_key, granted_key, effective_key in pairs:
        if not (
            measurement.get(requested_key)
            == measurement.get(granted_key)
            == measurement.get(effective_key)
        ):
            failures.append(f"{requested_key.upper()}_GRANT_EFFECTIVE_MISMATCH")
    failures.extend(
        validate_realized_usage_within_effective_ceiling(
            realized=measurement.get("realized_usage", {}),
            effective_max_active_routes=_int(measurement.get("effective_max_active_routes")),
            effective_max_reasoning_depth=_int(measurement.get("effective_max_reasoning_depth")),
        )
    )
    return failures


def classify_capacity_exposure(
    *,
    effective_budget_delta: int | float,
    realized_resource_delta: int | float,
    quality_delta: int | float,
) -> dict[str, Any]:
    if effective_budget_delta <= 0:
        return {"capacity_exposure": "INCONCLUSIVE", "mcv_quality": UNAVAILABLE}
    if realized_resource_delta == 0:
        return {"capacity_exposure": "EXTRA_CAPACITY_UNUSED", "mcv_quality": "NOT_EXPOSED"}
    exposure = "EXTRA_CAPACITY_PARTIALLY_USED"
    if realized_resource_delta >= effective_budget_delta:
        exposure = "EXTRA_CAPACITY_USED"
    if quality_delta == 0:
        mcv = "ZERO_WITHIN_RESOLUTION"
    else:
        mcv = round(float(quality_delta) / float(realized_resource_delta), 6)
    return {"capacity_exposure": exposure, "mcv_quality": mcv}


def classify_search_dilution(
    *,
    realized_resource_delta: int | float,
    final_quality_delta: int | float,
    search_efficiency_delta: int | float | str = UNAVAILABLE,
    reproducible: bool = False,
) -> str:
    if realized_resource_delta <= 0:
        return "NOT_EXPOSED"
    negative_search = _negative(final_quality_delta) or _negative(search_efficiency_delta)
    if not negative_search:
        return "NO_DILUTION_EVIDENCE"
    return "REPRODUCED_DILUTION_SIGNAL" if reproducible else "POSSIBLE_DILUTION_SIGNAL"


def production_budget_snapshot() -> dict[str, int]:
    return {
        "max_active_routes": PRODUCTION_DEFAULT_ROUTES,
        "max_reasoning_depth": PRODUCTION_DEFAULT_DEPTH,
    }


def _read_task_payload(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise P0dCorpusContractError(f"task JSON is invalid: {path}") from exc
    if not isinstance(payload, Mapping):
        raise P0dCorpusContractError(f"task payload must be a mapping: {path}")
    return payload


def _grid_summary(train: Iterable[Mapping[str, Any]], test: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    input_dimensions: list[list[int]] = []
    output_dimensions: list[list[int]] = []
    colors: set[int] = set()
    changed = 0
    comparable = 0
    nonzero_input = 0
    nonzero_output = 0
    size_change = False
    for example in train:
        source = _grid(example.get("input"))
        target = _grid(example.get("output"))
        if source:
            input_dimensions.append([len(source), len(source[0])])
            colors.update(value for row in source for value in row)
            nonzero_input += sum(1 for row in source for value in row if value != 0)
        if target:
            output_dimensions.append([len(target), len(target[0])])
            colors.update(value for row in target for value in row)
            nonzero_output += sum(1 for row in target for value in row if value != 0)
        if source and target:
            size_change = size_change or len(source) != len(target) or len(source[0]) != len(target[0])
            height = min(len(source), len(target))
            width = min(len(source[0]), len(target[0]))
            for row in range(height):
                for column in range(width):
                    comparable += 1
                    changed += int(source[row][column] != target[row][column])
    for example in test:
        source = _grid(example.get("input"))
        if source:
            input_dimensions.append([len(source), len(source[0])])
            colors.update(value for row in source for value in row)
    max_grid_area = max(
        [height * width for height, width in input_dimensions + output_dimensions] or [0]
    )
    return {
        "input_dimensions": input_dimensions,
        "output_dimensions": output_dimensions,
        "color_count": len(colors),
        "changed_cell_ratio": round(changed / comparable, 6) if comparable else 0.0,
        "size_change": size_change,
        "nonzero_input_count": nonzero_input,
        "nonzero_output_count": nonzero_output,
        "max_grid_area": max_grid_area,
    }


def _characteristics(
    metadata: Mapping[str, Any],
    grid_summary: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    concepts = (
        _strings(metadata.get("target_concepts"))
        + _strings(metadata.get("concept_labels"))
        + _strings(metadata.get("concept_family"))
    )
    domains = _strings(metadata.get("target_domains"))
    expected = _strings(metadata.get("expected_transformations"))
    composite = _strings(metadata.get("composite_capabilities"))
    return {
        "color_mapping": _characteristic(_contains_any(concepts + composite, ("color",)), "metadata concepts mention color"),
        "color_transformation": _characteristic(
            grid_summary.get("changed_cell_ratio", 0) > 0 and grid_summary.get("color_count", 0) > 2,
            "train input-output cells change across multiple colors",
        ),
        "spatial_reasoning": _characteristic(_contains_any(concepts + domains, ("spatial",)), "metadata mentions spatial reasoning"),
        "object_counting": _characteristic(_contains_any(concepts + composite, ("count", "object")), "metadata mentions object/count capability"),
        "object_creation": _characteristic(
            _int(grid_summary.get("nonzero_output_count")) > _int(grid_summary.get("nonzero_input_count")),
            "train outputs contain more nonzero cells than inputs",
        ),
        "object_removal": _characteristic(
            _int(grid_summary.get("nonzero_output_count")) < _int(grid_summary.get("nonzero_input_count")),
            "train outputs contain fewer nonzero cells than inputs",
        ),
        "topology_change": _characteristic(_contains_any(concepts + domains, ("topolog",)), "metadata mentions topology"),
        "transformation_sequence": _characteristic(
            metadata.get("transformation_sequence_required") is True
            or _contains_any(expected, ("multi_step", "compose")),
            "metadata requires transformation sequence",
        ),
        "multi_step_reasoning": _characteristic(
            metadata.get("multi_step_reasoning") is True
            or _contains_any(expected, ("multi_step",)),
            "metadata marks multi-step reasoning",
        ),
        "program_synthesis_dependency": _characteristic(
            metadata.get("program_composition_required") is True
            or _contains_any(metadata.get("required_operational_capabilities"), ("program", "compiler")),
            "metadata requires program/compiler capability",
        ),
        "candidate_ambiguity": _characteristic(
            metadata.get("multiple_valid_solution_strategies") is True,
            "metadata marks multiple valid solution strategies",
        ),
        "cross_concept_composition": _characteristic(
            _int(metadata.get("domain_count")) >= 3
            or metadata.get("operational_capability_composition_required") is True,
            "metadata domain count or composition flag",
        ),
        "rotation": _characteristic(
            _contains_any(concepts + expected, ("rotation", "rotate")),
            "metadata concept labels or expected transformations mention rotation",
        ),
        "reflection": _characteristic(
            _contains_any(concepts + expected, ("reflection", "reflect")),
            "metadata concept labels or expected transformations mention reflection",
        ),
        "scaling": _characteristic(
            _contains_any(concepts + expected, ("scaling", "scale")),
            "metadata concept labels or expected transformations mention scaling",
        ),
        "translation": _characteristic(
            _contains_any(concepts + composite + expected, ("translation", "translate")),
            "metadata mentions translation",
        ),
        "component_splitting": _unknown("component split not inferred without component trace"),
        "component_merging": _unknown("component merge not inferred without component trace"),
        "connectivity_change": _unknown("connectivity not inferred without component trace"),
        "relative_position": _unknown("relative position not inferred without semantic trace"),
        "pattern_completion": _characteristic(_contains_any(concepts + composite, ("pattern",)), "metadata mentions pattern"),
        "symbolic_remapping": _unknown("symbolic remapping not inferred without semantic trace"),
        "repair_dependency": _characteristic(
            _contains_any(metadata.get("deficiency_targets"), ("validation", "gap", "yield")),
            "metadata deficiency targets indicate likely repair pressure",
        ),
    }


def _task_family(
    metadata: Mapping[str, Any],
    characteristics: Mapping[str, Mapping[str, Any]],
) -> str:
    if metadata.get("elite_cognitive_task") is True:
        return str(metadata.get("elite_category") or "elite_cognitive")
    concept_family = str(metadata.get("concept_family") or "")
    if concept_family:
        return concept_family
    group = str(metadata.get("group") or "")
    if group:
        return group
    for name in (
        "color_mapping",
        "spatial_reasoning",
        "topology_change",
        "object_counting",
        "pattern_completion",
    ):
        if characteristics.get(name, {}).get("value") is True:
            return name
    return "UNKNOWN"


def _dimension(value: str, *, evidence: str, source: str, confidence: str) -> dict[str, str]:
    return {
        "value": value if value in DEMAND_VALUES else "UNKNOWN",
        "evidence": evidence,
        "source": source,
        "confidence": confidence,
    }


def _characteristic(value: bool, evidence: str) -> dict[str, Any]:
    if not value:
        return _unknown("observable evidence not present")
    return {
        "value": True,
        "evidence": evidence,
        "source": "task_content_or_nexryn_metadata",
        "confidence": "MEDIUM",
    }


def _unknown(evidence: str) -> dict[str, str]:
    return {
        "value": "UNKNOWN",
        "evidence": evidence,
        "source": "task_content_or_nexryn_metadata",
        "confidence": "LOW",
    }


def _grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list) or not value or not isinstance(value[0], list):
        return []
    return value


def _char_is_yes(characteristics: Mapping[str, Mapping[str, Any]], name: str) -> bool:
    return characteristics.get(name, {}).get("value") is True


def _contains_any(values: Any, needles: Iterable[str]) -> bool:
    text = " ".join(_strings(values)).lower()
    return any(needle.lower() in text for needle in needles)


def _strings(values: Any) -> list[str]:
    if isinstance(values, str):
        return [values]
    if isinstance(values, Iterable) and not isinstance(values, (Mapping, bytes)):
        return [str(item) for item in values if item is not None]
    return []


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({str(key): _freeze(value[key]) for key in sorted(value, key=str)})


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _negative(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value < 0


def _int(value: Any) -> int:
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def _float(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


__all__ = [
    "DEMAND_VALUES",
    "FrozenP0dCorpus",
    "P0D_INITIAL_SCREENING_CONFIGS",
    "P0D_STATE_SURFACES",
    "P0dCorpusContractError",
    "classify_capacity_exposure",
    "classify_search_dilution",
    "cognitive_demand_profile",
    "create_state_snapshot",
    "freeze_discriminative_corpus",
    "inventory_task_corpus",
    "inventory_task_file",
    "production_budget_snapshot",
    "validate_budget_authority_measurement",
    "validate_demand_profile",
    "validate_state_fingerprint",
]
