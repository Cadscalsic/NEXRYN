"""Report-driven cognitive capability composition for ARC-style reasoning."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate


class CognitiveCapabilityOrchestrator:
    """Inventory, compose, and explain cognitive capabilities already in flight."""

    system_name = "cognitive_capability_orchestrator"

    def __init__(
        self,
        truth_admission_gate: CurrentTruthAdmissionGate | None = None,
    ) -> None:
        self.truth_admission_gate = (
            truth_admission_gate or CurrentTruthAdmissionGate()
        )

    CAPABILITIES = {
        "object_reasoning": {
            "priority": 6,
            "typical_arc_tasks": [
                "object_abstraction",
                "object_identity",
                "object_grouping",
                "object_persistence",
            ],
            "patterns": [
                "object_identity",
                "object_persistence",
                "object_grouping",
                "decomposition",
                "merging",
                "hierarchy",
            ],
            "cooperates_with": [
                "spatial_reasoning",
                "color_mapping",
                "transformation_reasoning",
            ],
        },
        "spatial_reasoning": {
            "priority": 5,
            "typical_arc_tasks": [
                "relative_position",
                "containment",
                "adjacency",
                "connectivity",
                "alignment",
            ],
            "patterns": [
                "relative_position",
                "containment",
                "adjacency",
                "connectivity",
                "direction",
                "distance",
                "alignment",
                "topology",
            ],
            "cooperates_with": [
                "object_reasoning",
                "dependency_reasoning",
                "program_synthesis",
            ],
        },
        "color_mapping": {
            "priority": 1,
            "typical_arc_tasks": [
                "global_color_remap",
                "local_color_remap",
                "object_specific_color",
                "palette_inference",
            ],
            "patterns": [
                "global_color_remapping",
                "local_color_remapping",
                "context_sensitive_mapping",
                "conditional_mapping",
                "object_specific_mapping",
                "color_invariants",
                "palette_inference",
            ],
            "cooperates_with": [
                "object_reasoning",
                "spatial_reasoning",
                "program_synthesis",
            ],
        },
        "rotation_reflection": {
            "priority": 2,
            "typical_arc_tasks": [
                "grid_rotation",
                "mirror_symmetry",
                "object_relative_rotation",
            ],
            "patterns": [
                "90_rotation",
                "180_rotation",
                "270_rotation",
                "diagonal_reflection",
                "mirror_combinations",
                "partial_rotation",
                "nested_transformations",
            ],
            "cooperates_with": [
                "pattern_completion",
                "transformation_reasoning",
                "program_synthesis",
            ],
        },
        "pattern_completion": {
            "priority": 3,
            "typical_arc_tasks": [
                "missing_region_completion",
                "repeated_structure",
                "symmetry_completion",
            ],
            "patterns": [
                "missing_regions",
                "repeated_structures",
                "symmetry_completion",
                "rule_completion",
                "hierarchical_completion",
            ],
            "cooperates_with": [
                "spatial_reasoning",
                "rotation_reflection",
                "transformation_reasoning",
            ],
        },
        "occlusion_reasoning": {
            "priority": 4,
            "typical_arc_tasks": [
                "hidden_object_reconstruction",
                "partial_visibility",
                "mask_reasoning",
            ],
            "patterns": [
                "hidden_objects",
                "partial_visibility",
                "occlusion_masks",
                "object_reconstruction",
                "shape_completion",
            ],
            "cooperates_with": [
                "object_reasoning",
                "pattern_completion",
                "causal_reasoning",
            ],
        },
        "dependency_reasoning": {
            "priority": 5,
            "typical_arc_tasks": [
                "rule_prerequisites",
                "dependency_chains",
                "constraint_selection",
            ],
            "patterns": [
                "dependency_graphs",
                "chain_depth",
                "constraint_refinement",
            ],
            "cooperates_with": [
                "process_reasoning",
                "causal_reasoning",
                "transformation_reasoning",
            ],
        },
        "process_reasoning": {
            "priority": 7,
            "typical_arc_tasks": [
                "state_transition",
                "multi_step_process",
                "intermediate_state",
            ],
            "patterns": [
                "intermediate_states",
                "state_transitions",
                "process_validation",
            ],
            "cooperates_with": [
                "dependency_reasoning",
                "causal_reasoning",
                "program_synthesis",
            ],
        },
        "causal_reasoning": {
            "priority": 7,
            "typical_arc_tasks": [
                "cause_effect_explanation",
                "propagation_chain",
                "impossible_hypothesis_rejection",
            ],
            "patterns": [
                "root_cause",
                "consequence_tracking",
                "causal_validation",
            ],
            "cooperates_with": [
                "dependency_reasoning",
                "process_reasoning",
                "program_synthesis",
            ],
        },
        "transformation_reasoning": {
            "priority": 7,
            "typical_arc_tasks": [
                "sequential_transformations",
                "parallel_transformations",
                "composite_transformations",
            ],
            "patterns": [
                "sequential_transformations",
                "parallel_transformations",
                "conditional_transformations",
                "composite_transformations",
                "transformation_graphs",
                "transformation_equivalence",
            ],
            "cooperates_with": [
                "color_mapping",
                "rotation_reflection",
                "program_synthesis",
            ],
        },
        "program_synthesis": {
            "priority": 8,
            "typical_arc_tasks": [
                "program_induction",
                "program_composition",
                "operator_selection",
            ],
            "patterns": [
                "reusable_program_fragments",
                "program_composition",
                "program_ranking",
                "program_simplification",
                "program_validation",
                "program_adaptation",
            ],
            "cooperates_with": [
                "transformation_reasoning",
                "causal_reasoning",
                "adaptive_reuse",
            ],
        },
        "adaptive_reuse": {
            "priority": 8,
            "typical_arc_tasks": [
                "strategy_reuse",
                "program_reuse",
                "truth_reuse",
            ],
            "patterns": [
                "successful_strategies",
                "successful_programs",
                "successful_transformations",
                "successful_causal_explanations",
                "validation_patterns",
            ],
            "cooperates_with": [
                "program_synthesis",
                "truth_validation",
                "dependency_reasoning",
            ],
        },
    }

    def build_report(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        reports: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        reports = reports if isinstance(reports, Mapping) else {}
        executed = self._executed_capabilities(runtime_context, reports)
        inventory = self._inventory(executed, reports)
        hypotheses = self._hypotheses(inventory, reports)
        validated = [
            item for item in hypotheses if item.get("validation_status") == "validated"
        ]
        rejected = [
            item for item in hypotheses if item.get("validation_status") == "rejected"
        ]
        cooperation_events = self._cooperation_events(executed, reports)
        shared_contexts = self._shared_contexts(reports)
        shared_truths = self._shared_truths(runtime_context, reports)
        shared_dependencies = self._shared_dependencies(reports)
        shared_programs = self._shared_programs(reports)
        capability_confidence = {
            item["capability_id"]: item["confidence"]
            for item in inventory
        }
        failures = [
            {
                "capability_id": item["capability_id"],
                "failure_cases": item["failure_cases"],
                "uncertainty": item["uncertainty"],
            }
            for item in inventory
            if item["failure_cases"]
        ]
        reusable_assets = self._reusable_assets(
            validated,
            shared_programs,
            shared_dependencies,
            shared_contexts,
            shared_truths,
        )
        success_rate = round(
            len(validated) / max(len(hypotheses), 1),
            4,
        )
        average_confidence = round(
            sum(capability_confidence.values()) / max(len(capability_confidence), 1),
            4,
        )
        report = {
            "system": self.system_name,
            "COGNITIVE_CAPABILITY_REPORT": True,
            "capability_inventory": inventory,
            "capabilities_executed": executed,
            "capability_confidence": capability_confidence,
            "capability_success_rate": success_rate,
            "capability_failures": failures,
            "cooperation_events": cooperation_events,
            "shared_contexts": shared_contexts,
            "shared_truths": shared_truths,
            "shared_dependencies": shared_dependencies,
            "shared_programs": shared_programs,
            "generated_hypotheses": hypotheses,
            "validated_hypotheses": validated,
            "rejected_hypotheses": rejected,
            "alternative_hypotheses": [
                item for item in hypotheses if item.get("validation_status") == "candidate"
            ],
            "reusable_assets": reusable_assets,
            "successful_strategies": reusable_assets.get("successful_strategies", []),
            "successful_programs": reusable_assets.get("successful_programs", []),
            "successful_transformations": reusable_assets.get(
                "successful_transformations",
                [],
            ),
            "successful_causal_explanations": reusable_assets.get(
                "successful_causal_explanations",
                [],
            ),
            "successful_validation_patterns": reusable_assets.get(
                "successful_validation_patterns",
                [],
            ),
            "reasoning_summary": self._reasoning_summary(
                executed,
                validated,
                rejected,
                cooperation_events,
                average_confidence,
            ),
            "timestamp": str(datetime.utcnow()),
        }
        return report

    def _executed_capabilities(self, runtime_context, reports):
        executed = []
        evidence = self._evidence_text(runtime_context, reports)
        for capability_id in self.CAPABILITIES:
            if self._capability_executed(capability_id, reports, evidence):
                executed.append(capability_id)
        return executed

    def _capability_executed(self, capability_id, reports, evidence):
        if capability_id == "color_mapping":
            return bool(reports.get("color_mapping_report"))
        if capability_id == "transformation_reasoning":
            return bool(reports.get("transformation_synthesis_report"))
        if capability_id == "program_synthesis":
            transformation = reports.get("transformation_synthesis_report", {})
            return bool(transformation.get("selected_program"))
        if capability_id == "dependency_reasoning":
            return bool(reports.get("dependency_activation_report"))
        if capability_id == "process_reasoning":
            return bool(reports.get("process_context_runtime_report"))
        if capability_id == "causal_reasoning":
            return bool(reports.get("causal_context_runtime_report"))
        if capability_id == "adaptive_reuse":
            return bool(reports.get("adaptive_reuse_report"))
        if capability_id == "rotation_reflection":
            return any(token in evidence for token in ("rotation", "reflection", "mirror", "rotate"))
        if capability_id == "pattern_completion":
            return any(token in evidence for token in ("pattern", "symmetry", "completion", "repeat"))
        if capability_id == "occlusion_reasoning":
            return any(token in evidence for token in ("occlusion", "hidden", "mask", "visible"))
        if capability_id == "spatial_reasoning":
            return bool(reports.get("spatial_reasoning_report")) or any(
                token in evidence for token in ("spatial", "position", "adjacency", "alignment", "path")
            )
        if capability_id == "object_reasoning":
            return any(token in evidence for token in ("object", "component", "shape", "identity"))
        return False

    def _inventory(self, executed, reports):
        inventory = []
        for capability_id, spec in self.CAPABILITIES.items():
            confidence, evidence = self._confidence_for(capability_id, reports)
            maturity = self._maturity(confidence, capability_id in executed)
            missing = self._missing_patterns(capability_id, reports)
            inventory.append({
                "capability_id": capability_id,
                "priority": spec["priority"],
                "current_maturity": maturity,
                "executed": capability_id in executed,
                "confidence": confidence,
                "uncertainty": round(1.0 - confidence, 4),
                "evidence": evidence,
                "conflicting_evidence": self._conflicts_for(capability_id, reports),
                "failure_cases": missing,
                "typical_arc_tasks": list(spec["typical_arc_tasks"]),
                "missing_reasoning_patterns": missing,
                "potential_cooperation": list(spec["cooperates_with"]),
                "confidence_quality": (
                    "calibrated"
                    if confidence >= 0.75
                    else "emerging"
                    if confidence >= 0.45
                    else "insufficient"
                ),
            })
        return inventory

    def _confidence_for(self, capability_id, reports):
        if capability_id == "color_mapping":
            report = reports.get("color_mapping_report", {})
            return self._confidence(
                report.get("mapping_confidence"),
                report.get("program_accuracy"),
            ), self._evidence("color_mapping_report", report)
        if capability_id == "transformation_reasoning":
            report = reports.get("transformation_synthesis_report", {})
            return self._confidence(
                report.get("transformation_confidence"),
                report.get("transformation_accuracy"),
            ), self._evidence("transformation_synthesis_report", report)
        if capability_id == "program_synthesis":
            report = reports.get("transformation_synthesis_report", {})
            program = report.get("selected_program", {})
            return self._confidence(
                report.get("transformation_accuracy"),
                0.72 if program.get("steps") else 0.0,
            ), self._evidence("selected_program", program)
        if capability_id == "dependency_reasoning":
            report = reports.get("dependency_activation_report", {})
            return self._confidence(
                report.get("dependency_graph_validation_score"),
                report.get("dependency_chain_coverage"),
                report.get("dependency_execution_success_rate"),
                0.70 if report.get("dependency_chains_executed") else 0.0,
            ), self._evidence("dependency_activation_report", report)
        if capability_id == "process_reasoning":
            report = reports.get("process_context_runtime_report", {})
            return self._confidence(
                report.get("process_validation_score"),
                report.get("process_context_confidence"),
                report.get("process_success_rate"),
            ), self._evidence("process_context_runtime_report", report)
        if capability_id == "causal_reasoning":
            report = reports.get("causal_context_runtime_report", {})
            return self._confidence(
                report.get("causal_confidence"),
                report.get("causal_validation_score"),
                report.get("causal_success_rate"),
            ), self._evidence("causal_context_runtime_report", report)
        if capability_id == "adaptive_reuse":
            report = reports.get("adaptive_reuse_report", {})
            return self._confidence(
                report.get("reuse_rate"),
                0.70 if report.get("reused_assets") else 0.0,
            ), self._evidence("adaptive_reuse_report", report)
        return self._inferred_confidence(capability_id, reports)

    def _inferred_confidence(self, capability_id, reports):
        text = self._evidence_text({}, reports)
        patterns = self.CAPABILITIES[capability_id]["patterns"]
        matches = [
            pattern for pattern in patterns if pattern.replace("_", " ") in text
            or pattern in text
        ]
        confidence = round(min(0.78, 0.28 + len(matches) * 0.10), 4)
        return confidence, {
            "source": "capability_inventory_inference",
            "matched_patterns": matches,
        }

    def _hypotheses(self, inventory, reports):
        hypotheses = []
        for item in inventory:
            if not item["executed"] and item["confidence"] < 0.45:
                continue
            status = (
                "validated"
                if item["confidence"] >= 0.70 and not item["conflicting_evidence"]
                else "rejected"
                if item["conflicting_evidence"] and item["confidence"] < 0.50
                else "candidate"
            )
            hypotheses.append({
                "hypothesis_id": f"capability:{item['capability_id']}",
                "capability_id": item["capability_id"],
                "claim": self._claim_for(item["capability_id"], reports),
                "confidence": item["confidence"],
                "uncertainty": item["uncertainty"],
                "evidence": item["evidence"],
                "conflicting_evidence": item["conflicting_evidence"],
                "alternative_hypotheses": item["missing_reasoning_patterns"][:3],
                "validation_status": status,
            })
        return hypotheses

    def _claim_for(self, capability_id, reports):
        if capability_id == "color_mapping":
            matrix = reports.get("color_mapping_report", {}).get("mapping_matrix", {})
            return f"color mapping can explain palette changes via {matrix.get('mapping_type', 'unknown')} mapping"
        if capability_id == "transformation_reasoning":
            program = reports.get("transformation_synthesis_report", {}).get("selected_program", {})
            steps = [
                step.get("operation")
                for step in program.get("steps", []) or []
                if isinstance(step, Mapping)
            ]
            return f"transformation program candidate uses steps {steps}"
        if capability_id == "causal_reasoning":
            roots = reports.get("causal_context_runtime_report", {}).get("root_cause_candidates", [])
            return f"causal runtime identified root causes {roots}"
        return f"{capability_id} contributed reusable reasoning evidence"

    def _cooperation_events(self, executed, reports):
        events = []
        order = [
            "object_reasoning",
            "spatial_reasoning",
            "color_mapping",
            "dependency_reasoning",
            "process_reasoning",
            "transformation_reasoning",
            "causal_reasoning",
            "program_synthesis",
            "adaptive_reuse",
        ]
        active_order = [item for item in order if item in executed]
        for index, (source, target) in enumerate(zip(active_order, active_order[1:])):
            events.append({
                "event_id": f"capability_cooperation:{index}:{source}->{target}",
                "source_capability": source,
                "target_capability": target,
                "shared_signal": self._shared_signal(source, target, reports),
                "cooperation_type": "context_handoff",
                "confidence": round(
                    min(
                        self._confidence_for(source, reports)[0],
                        self._confidence_for(target, reports)[0],
                    ),
                    4,
                ),
            })
        return events

    def _shared_signal(self, source, target, reports):
        if "color_mapping" in {source, target}:
            return "mapping_matrix"
        if "dependency_reasoning" in {source, target}:
            return "dependency_graph"
        if "process_reasoning" in {source, target}:
            return "state_transition_sequence"
        if "causal_reasoning" in {source, target}:
            return "cause_effect_relation"
        if "program_synthesis" in {source, target}:
            return "selected_program"
        return "capability_context"

    def _shared_contexts(self, reports):
        contexts = []
        process = reports.get("process_context_runtime_report", {})
        contexts.extend(process.get("process_contexts", []) or [])
        causal = reports.get("causal_context_runtime_report", {})
        contexts.extend(causal.get("causal_contexts", []) or [])
        return [dict(item) for item in contexts[:10] if isinstance(item, Mapping)]

    def _shared_truths(self, runtime_context, reports):
        truths = []
        for key in ("truth_commitments", "reusable_truth_commitments", "truth_candidates"):
            value = runtime_context.get(key, [])
            if isinstance(value, Mapping):
                value = value.values()
            for item in value or []:
                if not isinstance(item, Mapping):
                    continue
                admission = self.truth_admission_gate.admit_current_truth(
                    item,
                    consumer_scope="capability_shared_truths",
                )
                if admission.admitted:
                    truths.append({
                        **dict(item),
                        "current_truth_admission": admission.to_dict(),
                    })
        return truths[:10]

    def _shared_dependencies(self, reports):
        dependency = reports.get("dependency_activation_report", {})
        items = []
        for key in ("dependency_reports", "dependency_chains", "causal_contexts"):
            items.extend(dependency.get(key, []) or [])
        return [dict(item) for item in items[:10] if isinstance(item, Mapping)]

    def _shared_programs(self, reports):
        programs = []
        transform = reports.get("transformation_synthesis_report", {})
        selected = transform.get("selected_program", {})
        if selected:
            programs.append(dict(selected))
        color = reports.get("color_mapping_report", {})
        selected = color.get("selected_program", {})
        if selected:
            programs.append(dict(selected))
        return programs

    def _reusable_assets(self, validated, programs, dependencies, contexts, truths):
        return {
            "successful_strategies": [
                {
                    "strategy_id": item["hypothesis_id"],
                    "capability_id": item["capability_id"],
                    "confidence": item["confidence"],
                    "reuse_type": "capability_strategy",
                }
                for item in validated
            ],
            "successful_programs": programs,
            "successful_transformations": [
                item for item in validated
                if item["capability_id"] in {
                    "transformation_reasoning",
                    "rotation_reflection",
                    "color_mapping",
                    "pattern_completion",
                }
            ],
            "successful_causal_explanations": [
                item for item in validated if item["capability_id"] == "causal_reasoning"
            ],
            "successful_validation_patterns": [
                {
                    "capability_id": item["capability_id"],
                    "validation_status": item["validation_status"],
                    "confidence": item["confidence"],
                }
                for item in validated
            ],
            "shared_dependencies": dependencies,
            "shared_contexts": contexts,
            "shared_truths": truths,
        }

    def _missing_patterns(self, capability_id, reports):
        evidence_text = self._evidence_text({}, reports)
        missing = []
        for pattern in self.CAPABILITIES[capability_id]["patterns"]:
            readable = pattern.replace("_", " ")
            if pattern not in evidence_text and readable not in evidence_text:
                missing.append(pattern)
        return missing[:6]

    def _conflicts_for(self, capability_id, reports):
        conflicts = []
        if capability_id == "color_mapping":
            report = reports.get("color_mapping_report", {})
            candidates = report.get("candidate_mappings", []) or []
            if len(candidates) > len(report.get("validated_mappings", []) or []) + 2:
                conflicts.append("multiple_unvalidated_color_mappings")
        if capability_id == "transformation_reasoning":
            report = reports.get("transformation_synthesis_report", {})
            if report.get("candidate_count", 0) and report.get("transformation_accuracy", 0.0) <= 0.0:
                conflicts.append("candidate_transformations_failed_prediction")
        if capability_id == "causal_reasoning":
            report = reports.get("causal_context_runtime_report", {})
            if report.get("causal_failures"):
                conflicts.append("causal_validation_failures")
        return conflicts

    def _maturity(self, confidence, executed):
        if confidence >= 0.82 and executed:
            return "operational"
        if confidence >= 0.60:
            return "developing"
        if executed:
            return "partial"
        return "latent"

    def _confidence(self, *values):
        numbers = []
        for value in values:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number > 0.0:
                numbers.append(max(0.0, min(number, 1.0)))
        if not numbers:
            return 0.0
        return round(sum(numbers) / len(numbers), 4)

    def _evidence(self, source, report):
        if not isinstance(report, Mapping) or not report:
            return {"source": source, "available": False}
        return {
            "source": source,
            "available": True,
            "keys": sorted(str(key) for key in report.keys())[:12],
        }

    def _evidence_text(self, runtime_context, reports):
        return f"{runtime_context} {reports}".lower()

    def _reasoning_summary(
        self,
        executed,
        validated,
        rejected,
        cooperation_events,
        average_confidence,
    ):
        return (
            f"Executed {len(executed)} cognitive capabilities with "
            f"{len(cooperation_events)} cooperation handoffs; "
            f"validated {len(validated)} hypotheses, rejected {len(rejected)}, "
            f"average capability confidence {average_confidence:.4f}."
        )


cognitive_capability_orchestrator = CognitiveCapabilityOrchestrator()


__all__ = [
    "CognitiveCapabilityOrchestrator",
    "cognitive_capability_orchestrator",
]
