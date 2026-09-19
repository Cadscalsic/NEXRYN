"""Deterministic, fail-closed governance check for Arena executor semantics."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.arena.candidate_normalizer import CandidateNormalizer
from runtime.arena.candidate_simulator import CandidateSimulator
from runtime.arena.executor_contract import (
    EXECUTOR_CONTRACT_ID,
    EXECUTOR_CONTRACT_VERSION,
)

MANIFEST_PATH = ROOT / "runtime/arena/contracts/candidate_simulator_1.0.json"
VECTOR_PATH = ROOT / "runtime/arena/contracts/candidate_simulator_1.0_vectors.json"

SURFACES = {
    "runtime/arena/candidate_simulator.py": ["simulate", "_predicted_localization", "_execute", "_array"],
    "runtime/arena/candidate_normalizer.py": [
        "_candidate", "_collapse_key", "_step", "_semantic_fingerprint",
        "_semantic_program", "_normalize_operation",
    ],
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def object_fingerprint(value: dict[str, Any]) -> str:
    return fingerprint({key: item for key, item in value.items() if key != "immutable_fingerprint"})


def semantic_surface(source: str, names: list[str]) -> list[dict[str, str]]:
    tree = ast.parse(source)
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            rows.append({"name": node.name, "ast": ast.dump(node, annotate_fields=True, include_attributes=False)})
    found = {row["name"] for row in rows}
    missing = sorted(set(names) - found)
    if missing:
        raise ValueError(f"missing semantic surfaces: {missing}")
    return sorted(rows, key=lambda row: row["name"])


def compute_surface_fingerprint(source_overrides: dict[str, str] | None = None) -> str:
    overrides = source_overrides or {}
    inventory = {}
    for relative, names in SURFACES.items():
        source = overrides.get(relative, (ROOT / relative).read_text(encoding="utf-8"))
        inventory[relative] = semantic_surface(source, names)
    return fingerprint(inventory)


def _grid(spec: dict[str, Any]) -> list[list[int]]:
    if "grid" in spec:
        return spec["grid"]
    rows, cols = spec["shape"]
    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    for row, col, value in spec.get("cells", []):
        grid[row][col] = value
    return grid


def vector_result(vector: dict[str, Any]) -> dict[str, Any]:
    candidate = {
        "candidate_id": vector["vector_id"],
        "source": "canonical_contract_vector",
        "program": vector["program"],
    }
    normalized = CandidateNormalizer().normalize([candidate])["normalized_candidates"][0]
    simulation = CandidateSimulator().simulate(
        normalized, _grid(vector["input"]), vector.get("target", {}).get("grid")
    )
    return {
        "normalized_executable_semantics": normalized["normalized_semantics"],
        "semantic_fingerprint": normalized["semantic_fingerprint"],
        "predicted_output": simulation["predicted_output"],
        "simulation_success": simulation["simulation_success"],
        "unsupported_steps": simulation["unsupported_steps"],
    }


def _baseline_vectors() -> dict[str, Any]:
    steps = {
        "preserve_grid": {}, "preserve_colors": {}, "preserve_topology": {},
        "preserve_shape": {}, "preserve_size": {}, "preserve_density": {},
        "preserve_symmetry": {}, "noop": {},
        "replace_color": {"source_color": 1, "target_color": 2},
        "recolor": {"color_mapping": {"1": 3}, "affected_positions": [[0, 0]]},
        "construct_path": {"path_cells": [[0, 1]], "path_color": 4},
        "connect_components": {"path_cells": [[1, 0]], "fill_color": 5},
        "remove_object": {"remove_colors": [1], "background_color": 0},
        "duplicate_object": {"cells_to_write": [{"row": 1, "col": 1, "value": 7}]},
        "translate": {"translation": [0, 1]}, "rotate": {},
        "mirror_horizontal": {}, "mirror_vertical": {}, "mirror_object": {},
    }
    rows = []
    for operation, parameters in steps.items():
        vector = {
            "vector_id": f"v1_{operation}",
            "contract_id": EXECUTOR_CONTRACT_ID,
            "contract_version": EXECUTOR_CONTRACT_VERSION,
            "applicability": "APPLICABLE",
            "covers_operations": [operation],
            "input": {"grid": [[1, 0], [0, 0]]},
            "program": {"step_count": 1, "steps": [{"operation": operation, "parameters": parameters}]},
        }
        vector["expected"] = vector_result(vector)
        vector["vector_fingerprint"] = fingerprint(vector)
        rows.append(vector)
    special = [
        ("v1_empty_input", {"grid": []}, {"step_count": 0, "steps": []}, []),
        ("v1_minimal_grid_boundary", {"grid": [[1]]}, {"step_count": 1, "steps": [{"operation": "duplicate_object", "parameters": {"cells_to_write": [{"row": -1, "col": 2, "value": 9}]}}]}, ["duplicate_object"]),
        ("v1_maximal_supported_grid", {"shape": [30, 30], "cells": [[0, 0, 1], [29, 29, 2]]}, {"step_count": 1, "steps": [{"operation": "mirror_vertical", "parameters": {}}]}, ["mirror_vertical"]),
        ("v1_unsupported_failure", {"grid": [[1]]}, {"step_count": 1, "steps": [{"operation": "unknown_operation", "parameters": {}}]}, []),
        ("v1_alias_normalization", {"grid": [[1]]}, {"step_count": 1, "steps": [{"operation": "replicate", "parameters": {"cells_to_write": []}}]}, ["duplicate_object"]),
    ]
    for vector_id, input_spec, program, covers in special:
        vector = {"vector_id": vector_id, "contract_id": EXECUTOR_CONTRACT_ID, "contract_version": EXECUTOR_CONTRACT_VERSION, "applicability": "APPLICABLE", "covers_operations": covers, "input": input_spec, "program": program}
        vector["expected"] = vector_result(vector)
        vector["vector_fingerprint"] = fingerprint(vector)
        rows.append(vector)
    payload = {
        "schema_version": "executor_canonical_vectors.v1",
        "source_component": "tools.executor_contract_ci",
        "contract_id": EXECUTOR_CONTRACT_ID,
        "contract_version": EXECUTOR_CONTRACT_VERSION,
        "normalization_version": "candidate_normalizer.v1",
        "authority": "CI_VALIDATION_ONLY",
        "behavioral_authority": "NONE",
        "creation_timestamp": "2026-09-20T00:00:00Z",
        "vectors": rows,
    }
    payload["immutable_fingerprint"] = object_fingerprint(payload)
    return payload


def refresh_derived_contract() -> None:
    vectors = _baseline_vectors()
    manifest = {
        "schema_version": "executor_semantic_contract.v1",
        "source_component": "runtime.arena.executor_contract",
        "contract_id": EXECUTOR_CONTRACT_ID,
        "semantic_version": EXECUTOR_CONTRACT_VERSION,
        "fingerprint_namespace": f"{EXECUTOR_CONTRACT_ID}@{EXECUTOR_CONTRACT_VERSION}",
        "supported_operation_set": sorted({operation for row in vectors["vectors"] for operation in row["covers_operations"]}),
        "execution_relevant_fields": ["program.steps", "step.operation", "step.parameters", "operation order"],
        "explicitly_inert_fields": ["duplicate_object.duplication_count", "duplicate_object.duplication_policy"],
        "normalization_rules": ["operation aliases canonicalized", "preservation and noop steps omitted", "unknown parameters retained fail-closed"],
        "serialization_rules": ["UTF-8 JSON", "sorted keys", "ASCII escapes", "compact separators"],
        "failure_semantics": ["unsupported operation preserves grid and marks simulation unsuccessful", "step exception is recorded and subsequent steps continue"],
        "compatibility_policy": {"exact": "EXACT_VERSION_REPLAY", "declared_compatible": "VERIFIED_COMPATIBLE_REPLAY", "different_version": "MIGRATION_REQUIRED", "unknown_contract": "UNSUPPORTED_LEGACY_CONTRACT", "missing_identity": "UNDETERMINED"},
        "version_policy": {"NON_SEMANTIC_CHANGE": "NO_BUMP", "CONTRACT_METADATA_CHANGE": "NO_BUMP_WITH_MANIFEST_REFRESH", "BACKWARD_COMPATIBLE_SEMANTIC_EXTENSION": "MINOR_BUMP", "SEMANTIC_PATCH_CHANGE": "PATCH_BUMP", "SEMANTIC_BREAKING_CHANGE": "MAJOR_BUMP_AND_NEW_NAMESPACE", "UNCLASSIFIED_POTENTIAL_SEMANTIC_CHANGE": "REJECT"},
        "semantic_surface_inventory": SURFACES,
        "semantic_surface_fingerprint": compute_surface_fingerprint(),
        "canonical_test_vector_references": [str(VECTOR_PATH.relative_to(ROOT)).replace("\\", "/")],
        "canonical_vector_set_fingerprint": object_fingerprint(vectors),
        "creation_or_update_timestamp": "2026-09-20T00:00:00Z",
        "authority": "CI_GOVERNANCE_ONLY",
        "behavioral_authority": "NONE",
    }
    manifest["immutable_fingerprint"] = object_fingerprint(manifest)
    VECTOR_PATH.write_text(json.dumps(vectors, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(
    *, source_overrides: dict[str, str] | None = None,
    manifest: dict[str, Any] | None = None,
    vectors: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    vectors = vectors or json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    failures = []
    if manifest.get("immutable_fingerprint") != object_fingerprint(manifest):
        failures.append("STALE_MANIFEST_FINGERPRINT")
    if vectors.get("immutable_fingerprint") != object_fingerprint(vectors):
        failures.append("STALE_VECTOR_SET_FINGERPRINT")
    if manifest.get("contract_id") != EXECUTOR_CONTRACT_ID or manifest.get("semantic_version") != EXECUTOR_CONTRACT_VERSION:
        failures.append("AUTHORITATIVE_VERSION_MANIFEST_MISMATCH")
    surface_fingerprint = compute_surface_fingerprint(source_overrides)
    if surface_fingerprint != manifest.get("semantic_surface_fingerprint"):
        failures.append("UNCLASSIFIED_POTENTIAL_SEMANTIC_CHANGE")
    if manifest.get("canonical_vector_set_fingerprint") != object_fingerprint(vectors):
        failures.append("MANIFEST_VECTOR_SET_MISMATCH")
    operations = set(manifest.get("supported_operation_set", []))
    covered = {operation for vector in vectors.get("vectors", []) for operation in vector.get("covers_operations", [])}
    if operations - covered:
        failures.append("CANONICAL_OPERATION_COVERAGE_INCOMPLETE")
    for vector in vectors.get("vectors", []):
        if vector.get("contract_version") != EXECUTOR_CONTRACT_VERSION:
            failures.append(f"VECTOR_VERSION_MISMATCH:{vector.get('vector_id')}")
            continue
        actual = vector_result(vector)
        expected = vector.get("expected", {})
        if actual != expected:
            failures.append(f"CANONICAL_VECTOR_DRIFT:{vector.get('vector_id')}")
        vector_payload = {key: value for key, value in vector.items() if key != "vector_fingerprint"}
        if vector.get("vector_fingerprint") != fingerprint(vector_payload):
            failures.append(f"STALE_VECTOR_FINGERPRINT:{vector.get('vector_id')}")
    return {
        "schema_version": "executor_contract_ci_result.v1",
        "contract_id": EXECUTOR_CONTRACT_ID,
        "contract_version": EXECUTOR_CONTRACT_VERSION,
        "semantic_surface_fingerprint": surface_fingerprint,
        "status": "PASSED" if not failures else "FAILED",
        "failures": failures,
        "authority": "CI_VALIDATION_ONLY",
        "behavioral_authority": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-derived", action="store_true")
    args = parser.parse_args()
    if args.write_derived:
        refresh_derived_contract()
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
