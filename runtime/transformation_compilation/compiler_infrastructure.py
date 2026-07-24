"""Compiler infrastructure inventory and diagnostics.

This module is not a runtime layer. It is a bounded compiler-side inventory used
to measure executable package and primitive coverage for semantic compilation.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


PRIMITIVE_OPERATION_REGISTRY: dict[str, dict[str, Any]] = {
    "translate": {
        "package": "spatial_execution_package",
        "domain": "Spatial",
        "parameters": ["translation", "delta_row", "delta_col"],
        "multi_step": True,
    },
    "rotate": {
        "package": "geometry_execution_package",
        "domain": "Geometry",
        "parameters": ["degrees", "rotation"],
        "multi_step": True,
    },
    "mirror_horizontal": {
        "package": "geometry_execution_package",
        "domain": "Geometry",
        "parameters": ["reflection_source"],
        "multi_step": True,
    },
    "mirror_vertical": {
        "package": "geometry_execution_package",
        "domain": "Geometry",
        "parameters": ["reflection_source"],
        "multi_step": True,
    },
    "duplicate_object": {
        "package": "growth_execution_package",
        "domain": "Growth",
        "parameters": ["cells_to_write", "relative_offset", "placement_vector"],
        "multi_step": True,
    },
    "replace_color": {
        "package": "color_execution_package",
        "domain": "Color",
        "parameters": ["color_mapping", "mapping", "source_color", "target_color"],
        "multi_step": True,
    },
    "preserve_colors": {
        "package": "color_execution_package",
        "domain": "Color",
        "parameters": ["preservation_policy"],
        "multi_step": True,
    },
    "preserve_grid": {
        "package": "spatial_execution_package",
        "domain": "Spatial",
        "parameters": ["preservation_policy"],
        "multi_step": True,
    },
    "preserve_shape": {
        "package": "spatial_execution_package",
        "domain": "Spatial",
        "parameters": ["preservation_policy"],
        "multi_step": True,
    },
    "preserve_size": {
        "package": "spatial_execution_package",
        "domain": "Spatial",
        "parameters": ["preservation_policy"],
        "multi_step": True,
    },
    "preserve_topology": {
        "package": "topology_execution_package",
        "domain": "Topology",
        "parameters": ["preservation_policy"],
        "multi_step": True,
    },
    "preserve_symmetry": {
        "package": "geometry_execution_package",
        "domain": "Geometry",
        "parameters": ["preservation_policy"],
        "multi_step": True,
    },
    "preserve_density": {
        "package": "density_execution_package",
        "domain": "Growth",
        "parameters": ["preservation_policy"],
        "multi_step": True,
    },
    "construct_path": {
        "package": "topology_execution_package",
        "domain": "Topology",
        "parameters": ["path_cells", "path_color", "start", "end"],
        "multi_step": True,
    },
    "connect_components": {
        "package": "topology_execution_package",
        "domain": "Topology",
        "parameters": ["path_cells", "path_color", "start", "end"],
        "multi_step": True,
    },
    "bridge_creation": {
        "package": "topology_execution_package",
        "domain": "Topology",
        "parameters": ["path_cells", "path_color", "start", "end"],
        "multi_step": True,
        "canonical_operation": "connect_components",
    },
    "pattern_completion": {
        "package": "pattern_execution_package",
        "domain": "Pattern",
        "parameters": ["density_delta", "fill_color"],
        "multi_step": True,
        "canonical_operation": "expand_pattern",
    },
    "density_modulation": {
        "package": "density_execution_package",
        "domain": "Growth",
        "parameters": ["density_delta", "fill_color", "cells_to_write"],
        "multi_step": True,
        "canonical_operation": "expand_pattern",
    },
    "topological_change": {
        "package": "topology_execution_package",
        "domain": "Topology",
        "parameters": ["path_cells", "path_color"],
        "multi_step": True,
        "canonical_operation": "construct_path",
    },
    "topological_reasoning": {
        "package": "topology_execution_package",
        "domain": "Topology",
        "parameters": ["path_cells", "path_color"],
        "multi_step": True,
        "canonical_operation": "construct_path",
    },
    "remove_object": {
        "package": "object_execution_package",
        "domain": "Object",
        "parameters": ["cells_to_clear", "remove_colors", "background_color"],
        "multi_step": True,
    },
    "scale_up": {
        "package": "geometry_execution_package",
        "domain": "Geometry",
        "parameters": ["scale_mode", "row_scale", "col_scale", "scale_factor"],
        "multi_step": True,
    },
    "scale_down": {
        "package": "geometry_execution_package",
        "domain": "Geometry",
        "parameters": ["scale_mode", "row_scale", "col_scale", "scale_factor"],
        "multi_step": True,
    },
    "expand_pattern": {
        "package": "pattern_execution_package",
        "domain": "Pattern",
        "parameters": ["density_delta", "fill_color"],
        "multi_step": True,
    },
}


EXECUTION_PACKAGES: dict[str, dict[str, Any]] = {
    "color_execution_package": {
        "domain": "Color",
        "operations": ["replace_color", "preserve_colors"],
    },
    "spatial_execution_package": {
        "domain": "Spatial",
        "operations": ["translate", "preserve_grid", "preserve_shape", "preserve_size"],
    },
    "geometry_execution_package": {
        "domain": "Geometry",
        "operations": ["rotate", "mirror_horizontal", "mirror_vertical", "scale_up", "scale_down", "preserve_symmetry"],
    },
    "growth_execution_package": {
        "domain": "Growth",
        "operations": ["duplicate_object"],
    },
    "topology_execution_package": {
        "domain": "Topology",
        "operations": ["construct_path", "connect_components", "preserve_topology", "bridge_creation", "topological_change", "topological_reasoning"],
    },
    "density_execution_package": {
        "domain": "Growth",
        "operations": ["preserve_density", "density_modulation"],
    },
    "pattern_execution_package": {
        "domain": "Pattern",
        "operations": ["pattern_completion", "expand_pattern"],
    },
    "object_execution_package": {
        "domain": "Object",
        "operations": ["remove_object"],
    },
}


EXECUTOR_OPERATION_ALIASES = {
    "bridge_creation": "connect_components",
    "pattern_completion": "expand_pattern",
    "density_modulation": "expand_pattern",
    "preserve_size": "preserve_grid",
    "topological_change": "construct_path",
    "topological_reasoning": "construct_path",
}


class CompilerInfrastructureAnalyzer:
    """Measure compiler infrastructure without changing compiler behavior."""

    def __init__(
        self,
        *,
        operation_registry: Mapping[str, Mapping[str, Any]] | None = None,
        execution_packages: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self.operation_registry = {
            str(key): dict(value)
            for key, value in (operation_registry or PRIMITIVE_OPERATION_REGISTRY).items()
        }
        self.execution_packages = {
            str(key): dict(value)
            for key, value in (execution_packages or EXECUTION_PACKAGES).items()
        }

    def build_report(
        self,
        *,
        compiler_report: Mapping[str, Any] | None = None,
        executor: Any = None,
        expected_operations: list[str] | None = None,
        candidate_programs: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        compiler_report = compiler_report if isinstance(compiler_report, Mapping) else {}
        expected = list(expected_operations or [])
        if not expected:
            diagnostics = compiler_report.get("compiler_failure_diagnostics")
            diagnostics = diagnostics if isinstance(diagnostics, Mapping) else {}
            expected = [
                str(item)
                for item in diagnostics.get("expected_operations", []) or []
                if item
            ]
        candidates = list(candidate_programs or compiler_report.get("compiler_candidates") or [])
        used_operations = self._used_operations(compiler_report, candidates, expected)
        executable_operations = self._executor_operations(executor)
        packages = self._package_rows(used_operations, executable_operations)
        primitives = self._primitive_rows(used_operations, executable_operations, candidates)
        missing_packages = sorted({
            row["package"]
            for row in primitives
            if row["required"] and not row["execution_package_present"]
        })
        partial_packages = sorted({
            row["package"]
            for row in packages
            if row["support_state"] == "PARTIAL_SUPPORT"
        })
        unused_packages = sorted([
            row["package"]
            for row in packages
            if row["usage_count"] == 0
        ])
        package_utilization_gap_rows = self._package_utilization_gap_rows(
            packages=packages,
            primitives=primitives,
            reason_counts=self._failure_reason_counts(compiler_report),
        )
        primitive_coverage = self._ratio(
            len([row for row in primitives if row["primitive_present"]]),
            len(primitives),
        )
        executable_coverage = self._ratio(
            len([row for row in primitives if row["executable"]]),
            len(primitives),
        )
        package_coverage = self._ratio(
            len([row for row in packages if row["package_present"]]),
            len(packages),
        )
        package_count = len(packages)
        primitive_count = len(primitives)
        executable_package_count = len([
            row for row in packages if row["package_present"]
        ])
        executable_primitive_count = len([
            row for row in primitives if row["executable"]
        ])
        dependency_coverage = self._ratio(
            len([row for row in packages if row["support_state"] == "FULL_SUPPORT"]),
            len(packages),
        )
        primitive_success_rate = self._primitive_success_rate(candidates)
        multi_step_report = self._multi_step_report(candidates, executable_operations)
        health_score = round(
            (
                package_coverage
                + primitive_coverage
                + executable_coverage
                + dependency_coverage
                + primitive_success_rate
                + multi_step_report["multi_step_program_support"]
            )
            / 6,
            4,
        )
        return {
            "system": "compiler_infrastructure",
            "execution_package_inventory": packages,
            "primitive_operation_inventory": primitives,
            "execution_package_inventory_state": (
                "PACKAGE_INVENTORY_AVAILABLE"
                if package_count
                else "PACKAGE_INVENTORY_NOT_AVAILABLE"
            ),
            "primitive_operation_inventory_state": (
                "PRIMITIVE_INVENTORY_AVAILABLE"
                if primitive_count
                else "PRIMITIVE_INVENTORY_NOT_AVAILABLE"
            ),
            "execution_package_inventory_count": package_count,
            "primitive_operation_inventory_count": primitive_count,
            "executable_package_count": executable_package_count,
            "executable_primitive_count": executable_primitive_count,
            "existing_execution_packages": sorted([
                row["package"] for row in packages if row["package_present"]
            ]),
            "missing_execution_packages": missing_packages,
            "unused_execution_packages": unused_packages,
            "package_utilization_gap_rows": package_utilization_gap_rows,
            "package_utilization_gap_count": len(package_utilization_gap_rows),
            "package_utilization_gap_state": (
                "UNUSED_EXECUTABLE_PACKAGES_PRESENT"
                if package_utilization_gap_rows
                else "NO_UNUSED_EXECUTABLE_PACKAGE_GAP"
            ),
            "partial_execution_packages": partial_packages,
            "execution_package_health_score": health_score,
            "primitive_operation_coverage": primitive_coverage,
            "compiler_infrastructure_health": health_score,
            "multi_step_program_support": multi_step_report["multi_step_program_support"],
            "multi_step_program_report": multi_step_report,
            "execution_package_dependency_coverage": dependency_coverage,
            "primitive_infrastructure_coverage": executable_coverage,
            "compiler_primitive_success_rate": primitive_success_rate,
            "execution_package_utilization": self._ratio(
                len([row for row in packages if row["usage_count"] > 0]),
                len(packages),
            ),
            "compiler_infrastructure_readiness": (
                "READY"
                if health_score >= 0.85 and not missing_packages
                else "PARTIAL"
                if health_score >= 0.50
                else "BLOCKED"
            ),
        }

    def _failure_reason_counts(self, compiler_report: Mapping[str, Any]) -> dict[str, int]:
        diagnostics = compiler_report.get("compiler_failure_diagnostics")
        diagnostics = diagnostics if isinstance(diagnostics, Mapping) else {}
        counts = diagnostics.get("failure_reason_counts") or {}
        return {
            str(reason): int(count or 0)
            for reason, count in counts.items()
            if count
        } if isinstance(counts, Mapping) else {}

    def _package_utilization_gap_rows(
        self,
        *,
        packages: list[Mapping[str, Any]],
        primitives: list[Mapping[str, Any]],
        reason_counts: Mapping[str, int],
    ) -> list[dict[str, Any]]:
        primitive_by_package: dict[str, list[Mapping[str, Any]]] = {}
        for primitive in primitives:
            primitive_by_package.setdefault(
                str(primitive.get("package") or "unknown_execution_package"),
                [],
            ).append(primitive)
        gap_rows = []
        for package in packages:
            if int(package.get("usage_count") or 0) > 0:
                continue
            if not package.get("package_present"):
                continue
            package_name = str(package.get("package"))
            executable_operations = [
                str(row.get("operation"))
                for row in primitive_by_package.get(package_name, [])
                if row.get("executable")
            ]
            if not executable_operations:
                continue
            gap_rows.append({
                "package": package_name,
                "domain": package.get("domain"),
                "supported_operations": sorted(executable_operations),
                "failure_reasons_present": sorted(reason_counts),
                "utilization_gap_type": self._package_utilization_gap_type(
                    reason_counts
                ),
                "diagnostic": (
                    "execution_package_available_but_not_selected_by_compiler"
                ),
                "action": "route_semantic_programs_to_existing_package",
            })
        return gap_rows

    def _package_utilization_gap_type(
        self,
        reason_counts: Mapping[str, int],
    ) -> str:
        reasons = set(reason_counts)
        if "missing_grid_pair" in reasons:
            return "GROUNDING_BLOCKED_PACKAGE_UTILIZATION"
        if "compiler_support_missing" in reasons or "missing_primitive" in reasons:
            return "COMPILER_ROUTING_OR_PRIMITIVE_ALIGNMENT_GAP"
        if "execution_package_missing" in reasons:
            return "PACKAGE_DISCOVERY_OR_BINDING_GAP"
        if "RULE_NOT_CAPTURED" in reasons:
            return "RULE_TRACEABILITY_GAP"
        return "UNUSED_PACKAGE_UTILIZATION_GAP"

    def _package_rows(
        self,
        used_operations: list[str],
        executable_operations: set[str],
    ) -> list[dict[str, Any]]:
        used_counts = Counter(
            self._package_for(operation)
            for operation in used_operations
            if self._package_for(operation)
        )
        rows = []
        for package, metadata in sorted(self.execution_packages.items()):
            operations = [
                str(item)
                for item in metadata.get("operations", []) or []
            ]
            executable = [
                operation for operation in operations
                if self._executor_operation(operation) in executable_operations
            ]
            missing = sorted(set(operations) - set(executable))
            if not executable:
                state = "NO_PRIMITIVE_SUPPORT"
            elif missing:
                state = "PARTIAL_SUPPORT"
            else:
                state = "FULL_SUPPORT"
            rows.append({
                "package": package,
                "domain": metadata.get("domain"),
                "package_present": bool(executable),
                "supported_operations": sorted(executable),
                "unsupported_operations": missing,
                "usage_count": int(used_counts.get(package, 0)),
                "support_state": state,
            })
        return rows

    def _primitive_rows(
        self,
        used_operations: list[str],
        executable_operations: set[str],
        candidates: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        used_counts = Counter(used_operations)
        candidate_ops = Counter()
        for candidate in candidates:
            for operation in self._program_operations(candidate.get("compiled_program") or candidate):
                candidate_ops[operation] += 1
        rows = []
        for operation, metadata in sorted(self.operation_registry.items()):
            executor_operation = self._executor_operation(operation)
            primitive_present = executor_operation in executable_operations
            package = str(metadata.get("package") or "unknown_execution_package")
            rows.append({
                "operation": operation,
                "canonical_operation": executor_operation,
                "package": package,
                "domain": metadata.get("domain"),
                "required": operation in used_operations,
                "primitive_present": primitive_present,
                "execution_package_present": primitive_present,
                "executable": primitive_present,
                "parameter_support": sorted(str(item) for item in metadata.get("parameters", []) or []),
                "parameters_supported": bool(metadata.get("parameters")),
                "multi_step_supported": bool(metadata.get("multi_step")),
                "compiler_can_emit": bool(candidate_ops.get(operation) or candidate_ops.get(executor_operation)),
                "usage_count": int(used_counts.get(operation, 0)),
            })
        return rows

    def _used_operations(
        self,
        compiler_report: Mapping[str, Any],
        candidates: list[Mapping[str, Any]],
        expected: list[str],
    ) -> list[str]:
        operations = [str(item) for item in expected if item]
        compiled = compiler_report.get("compiled_program")
        if isinstance(compiled, Mapping):
            operations.extend(self._program_operations(compiled))
        for candidate in candidates:
            if isinstance(candidate, Mapping):
                operations.extend(
                    self._program_operations(candidate.get("compiled_program") or candidate)
                )
        return sorted(dict.fromkeys(operation for operation in operations if operation))

    def _program_operations(self, program: Any) -> list[str]:
        if not isinstance(program, Mapping):
            return []
        steps = program.get("steps") or program.get("program_steps") or []
        if not isinstance(steps, list):
            return []
        return [
            str(step.get("operation") or step.get("primitive") or step.get("operator"))
            for step in steps
            if isinstance(step, Mapping)
            and (step.get("operation") or step.get("primitive") or step.get("operator"))
        ]

    def _executor_operations(self, executor: Any) -> set[str]:
        if executor is None:
            executable = {
                "duplicate_object",
                "remove_object",
                "expand_object",
                "shrink_object",
                "expand_grid",
                "shrink_grid",
                "translate",
                "replace_color",
                "expand_pattern",
                "grow_topology",
                "mirror_object",
                "mirror_horizontal",
                "mirror_vertical",
                "rotate",
                "rotate_grid",
                "construct_path",
                "connect_components",
                "fill_region",
                "scale_up",
                "scale_down",
                "preserve_grid",
                "preserve_shape",
                "preserve_density",
                "preserve_colors",
                "preserve_topology",
                "preserve_symmetry",
            }
        else:
            executable = {
                name
                for name in dir(executor)
                if not name.startswith("_") and callable(getattr(executor, name, None))
            }
        return executable | set(EXECUTOR_OPERATION_ALIASES)

    def _executor_operation(self, operation: str) -> str:
        metadata = self.operation_registry.get(operation, {})
        return str(
            metadata.get("canonical_operation")
            or EXECUTOR_OPERATION_ALIASES.get(operation)
            or operation
        )

    def _package_for(self, operation: str) -> str | None:
        metadata = self.operation_registry.get(operation, {})
        package = metadata.get("package")
        return str(package) if package else None

    def _primitive_success_rate(self, candidates: list[Mapping[str, Any]]) -> float:
        if not candidates:
            return 0.0
        successful = 0
        attempted = 0
        for candidate in candidates:
            validation = candidate.get("validation") if isinstance(candidate, Mapping) else {}
            validation = validation if isinstance(validation, Mapping) else {}
            program = candidate.get("compiled_program") if isinstance(candidate, Mapping) else {}
            step_count = len(self._program_operations(program))
            attempted += max(step_count, 1)
            if validation.get("exact_match"):
                successful += max(step_count, 1)
            elif float(validation.get("accuracy", 0.0) or 0.0) > 0.0:
                successful += max(step_count, 1) * float(validation.get("accuracy", 0.0) or 0.0)
        return self._ratio(successful, attempted)

    def _multi_step_report(
        self,
        candidates: list[Mapping[str, Any]],
        executable_operations: set[str],
    ) -> dict[str, Any]:
        rows = []
        supported = 0
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            program = candidate.get("compiled_program") or candidate
            operations = self._program_operations(program)
            if len(operations) <= 1:
                continue
            missing = [
                operation for operation in operations
                if self._executor_operation(operation) not in executable_operations
            ]
            validation = candidate.get("validation")
            validation = validation if isinstance(validation, Mapping) else {}
            row = {
                "program": candidate.get("program_id")
                or program.get("program_id")
                or "multi_step_program",
                "step_count": len(operations),
                "required_primitives": operations,
                "required_execution_packages": sorted({
                    self._package_for(operation)
                    for operation in operations
                    if self._package_for(operation)
                }),
                "missing_primitives": missing,
                "step_success_rate": validation.get("accuracy", 0.0),
                "failure_step": missing[0] if missing else None,
                "supported": not missing,
            }
            supported += 1 if row["supported"] else 0
            rows.append(row)
        return {
            "multi_step_program_count": len(rows),
            "supported_multi_step_program_count": supported,
            "multi_step_program_support": self._ratio(supported, len(rows))
            if rows
            else 1.0,
            "multi_step_program_rows": rows[:10],
        }

    def _ratio(self, numerator: float, denominator: float) -> float:
        if not denominator:
            return 0.0
        return round(max(0.0, min(1.0, float(numerator) / float(denominator))), 4)


compiler_infrastructure_analyzer = CompilerInfrastructureAnalyzer()


__all__ = [
    "CompilerInfrastructureAnalyzer",
    "compiler_infrastructure_analyzer",
    "EXECUTION_PACKAGES",
    "PRIMITIVE_OPERATION_REGISTRY",
]
