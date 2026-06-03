import json
from pathlib import Path


class CurriculumManager:
    """Ranks training tasks by concept scarcity and lifecycle state."""

    RARE_CONCEPT_PRIORITY = 10
    FAMILY_RELATED_PRIORITY = 8
    UNOBSERVED_TASK_PRIORITY = 100
    DISCOVERING_PRIORITY = 20
    BOUNDARY_REFINEMENT_PRIORITY = 5
    PRESERVATION_CONCEPT_PENALTY = 20
    PRESERVATION_FAMILY_DIVERSION_PENALTY = 10
    TARGET_CONCEPT_COUNTS = {
        "topological_change": 20,
        "topological_reasoning": 20,
        "density_modulation": 20,
        "symbolic_remapping": 20,
        "color_transform": 20,
        "shape_transform": 20,
        "shape_change": 20,
        "color_change": 20,
        "topological_growth": 20,
        "grow_topology": 20,
    }

    CONCEPT_FAMILY_MEMBERS = {
        "shape": {
            "shape_preservation",
            "shape_transform",
            "shape_change",
            "expand_object",
            "duplicate_object",
        },
        "color": {
            "color_preservation",
            "color_transform",
            "color_change",
            "recolor_object",
            "replace_color",
        },
        "symmetry": {
            "symmetry_preservation",
            "symmetry_transform",
            "symmetry_break",
            "asymmetry",
            "mirror_object",
        },
        "topology": {
            "topology_preservation",
            "topological_change",
            "topological_reasoning",
            "topological_growth",
            "grow_topology",
            "fill_region",
        },
        "identity": {
            "object_identity_preservation",
            "object_identity_transform",
            "object_split",
            "object_merge",
        },
        "density": {
            "density_preservation",
            "density_modulation",
            "expand_pattern",
        },
    }

    CONCEPT_TO_FAMILY = {
        concept: family
        for family, concepts in CONCEPT_FAMILY_MEMBERS.items()
        for concept in concepts
    }

    def __init__(self, minimum_concept_count=5, target_concept_counts=None):
        self.minimum_concept_count = max(int(minimum_concept_count), 1)
        self.target_concept_counts = {
            **self.TARGET_CONCEPT_COUNTS,
            **{
                str(concept): max(int(count), 1)
                for concept, count in (target_concept_counts or {}).items()
            },
        }

    def _task_metadata(self, task_file, task_directory=None):
        if task_directory is None:
            return {}
        path = Path(task_directory) / task_file
        try:
            with path.open("r", encoding="utf-8") as file:
                task = json.load(file)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return {}
        
        # Try nexryn_metadata first (generated tasks)
        metadata = task.get("nexryn_metadata", {})
        if metadata and isinstance(metadata, dict):
            return metadata
        
        # Fallback: look for target_concepts in top level (for manually configured tasks)
        if "target_concepts" in task:
            return {"target_concepts": task.get("target_concepts", [])}
        
        return {}

    def _concept_states(self, concept_states=None):
        if isinstance(concept_states, dict):
            return {
                str(concept): str(state)
                for concept, state in concept_states.items()
            }
        return {
            str(item["concept"]): str(item.get("state", "DISCOVERING"))
            for item in concept_states or []
            if isinstance(item, dict) and item.get("concept")
        }

    def _concept_family(self, concept):
        return self.CONCEPT_TO_FAMILY.get(concept)

    def _family_target_concepts(self, family):
        return [
            concept
            for concept, count in self.target_concept_counts.items()
            if self._concept_family(concept) == family
        ]

    def _family_priority_for(self, concept, concept_counts):
        if concept in self.target_concept_counts:
            return {
                "priority": 0,
                "reasons": [],
            }
        family = self._concept_family(concept)
        if not family:
            return {
                "priority": 0,
                "reasons": [],
            }
        target_concepts = self._family_target_concepts(family)
        coverage_gap = sum(
            max(
                self.target_concept_counts.get(target, 0)
                - concept_counts.get(target, 0),
                0,
            )
            for target in target_concepts
        )
        if not coverage_gap:
            return {
                "priority": 0,
                "reasons": [],
            }
        if concept.endswith("_preservation"):
            has_transform_gap = any(
                self.target_concept_counts.get(target, 0)
                > concept_counts.get(target, 0)
                for target in target_concepts
                if not target.endswith("_preservation")
            )
            if has_transform_gap:
                return {
                    "priority": 0,
                    "reasons": [],
                }
        return {
            "priority": coverage_gap * self.FAMILY_RELATED_PRIORITY,
            "reasons": ["family_concept_coverage_gap"],
        }

    def _preservation_bias_for(
        self,
        concept,
        concept_counts,
        available_concepts,
    ):
        if not isinstance(concept, str):
            return {
                "priority": 0,
                "reasons": [],
            }
        if not concept.endswith("_preservation"):
            return {
                "priority": 0,
                "reasons": [],
            }
        family = self._concept_family(concept)
        if not family:
            return {
                "priority": 0,
                "reasons": [],
            }
        family_transform_targets = [
            target
            for target in self._family_target_concepts(family)
            if not target.endswith("_preservation")
        ]
        available_family_transforms = [
            target
            for target in family_transform_targets
            if target in available_concepts
        ]
        if not available_family_transforms:
            return {
                "priority": 0,
                "reasons": [],
            }
        has_transform_gap = any(
            self.target_concept_counts.get(target, self.minimum_concept_count)
            > concept_counts.get(target, 0)
            for target in available_family_transforms
        )
        if has_transform_gap:
            return {
                "priority": self.PRESERVATION_FAMILY_DIVERSION_PENALTY,
                "reasons": [
                    "preservation_concept_diverts_from_family_transform",
                ],
            }
        return {
            "priority": 0,
            "reasons": [],
        }

    def _priority_for(
        self,
        concept,
        concept_counts,
        concept_states,
        available_concepts,
    ):
        count = concept_counts.get(concept, 0)
        state = concept_states.get(concept, "UNKNOWN")
        target_count = self.target_concept_counts.get(
            concept,
            self.minimum_concept_count,
        )
        coverage_gap = max(target_count - count, 0)
        priority = 0
        reasons = []
        if coverage_gap:
            priority += coverage_gap * self.RARE_CONCEPT_PRIORITY
            reasons.append("concept_coverage_below_target")
        if state == "DISCOVERING":
            priority += self.DISCOVERING_PRIORITY
            reasons.append("concept_discovering")
        if state == "BOUNDARY_REFINEMENT":
            priority += self.BOUNDARY_REFINEMENT_PRIORITY
            reasons.append("boundary_refinement")
        family_priority = self._family_priority_for(concept, concept_counts)
        if family_priority["priority"]:
            priority += family_priority["priority"]
            reasons.extend(family_priority["reasons"])
        preservation_bias = self._preservation_bias_for(
            concept,
            concept_counts,
            available_concepts,
        )
        if preservation_bias["priority"]:
            priority -= preservation_bias["priority"]
            reasons.extend(preservation_bias["reasons"])
        return {
            "concept": concept,
            "concept_count": count,
            "target_count": target_count,
            "coverage_gap": coverage_gap,
            "coverage_ratio": round(
                min(count / target_count, 1.0),
                4,
            ),
            "concept_state": state,
            "concept_family": self._concept_family(concept),
            "priority": priority,
            "priority_reasons": reasons,
        }

    def rank_tasks(
        self,
        task_files,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        observed_task_ids=None,
    ):
        concept_counts = {
            str(concept): int(count)
            for concept, count in (concept_counts or {}).items()
        }
        concept_states = self._concept_states(concept_states)
        observed_task_files = {
            Path(str(task_id).replace("\\", "/")).name
            for task_id in observed_task_ids or []
        }
        available_concepts = set()
        task_metadata = {}
        for task_file in task_files:
            metadata = self._task_metadata(task_file, task_directory)
            concepts = [
                str(concept)
                for concept in metadata.get("target_concepts", [])
                if concept
            ]
            available_concepts.update(concepts)
            task_metadata[task_file] = concepts
        task_reports = []
        for order, task_file in enumerate(task_files):
            concepts = task_metadata.get(task_file, [])
            concept_priorities = [
                self._priority_for(
                    concept,
                    concept_counts,
                    concept_states,
                    available_concepts,
                )
                for concept in concepts
            ]
            priority = sum(
                item["priority"]
                for item in concept_priorities
            )
            target_coverage_gap = sum(
                item["coverage_gap"]
                for item in concept_priorities
            )
            unobserved_task = task_file not in observed_task_files
            if unobserved_task and target_coverage_gap:
                priority += self.UNOBSERVED_TASK_PRIORITY
            task_reports.append({
                "task_file": task_file,
                "original_order": order,
                "target_concepts": concepts,
                "priority": priority,
                "unobserved_task": unobserved_task,
                "target_coverage_gap": target_coverage_gap,
                "concept_priorities": concept_priorities,
            })
        task_reports.sort(
            key=lambda item: (
                -item["priority"],
                item["original_order"],
            )
        )
        prioritized_concepts = sorted({
            item["concept"]
            for report in task_reports
            for item in report["concept_priorities"]
            if item["priority"] > 0
        })
        return {
            "system": "training_curriculum_manager",
            "training_mode": (
                "concept_imbalance_prioritized_batch"
                if any(report["priority"] > 0 for report in task_reports)
                else "bounded_round_robin_batch"
            ),
            "minimum_concept_count": self.minimum_concept_count,
            "target_concept_counts": dict(self.target_concept_counts),
            "observed_task_count": len(observed_task_files),
            "unobserved_task_priority": self.UNOBSERVED_TASK_PRIORITY,
            "prioritized_concepts": prioritized_concepts,
            "ranked_task_files": [
                report["task_file"]
                for report in task_reports
            ],
            "task_priorities": task_reports,
        }

    def select_batch_tasks(self, curriculum_report, batch_size):
        task_reports = list(curriculum_report.get("task_priorities", []))
        selected = []
        selected_files = set()
        deficient_targets = sorted(
            (
                (concept, count)
                for concept, count in self.target_concept_counts.items()
                if any(
                    item["concept"] == concept
                    and item["coverage_gap"] > 0
                    for report in task_reports
                    for item in report["concept_priorities"]
                )
            ),
            key=lambda item: (
                -max(
                    concept_priority["coverage_gap"]
                    for report in task_reports
                    for concept_priority in report["concept_priorities"]
                    if concept_priority["concept"] == item[0]
                ),
                item[0],
            ),
        )
        covered_targets = set()
        for concept, _ in deficient_targets:
            if concept in covered_targets or len(selected) >= batch_size:
                continue
            candidates = [
                report
                for report in task_reports
                if report["task_file"] not in selected_files
                and concept in report["target_concepts"]
            ]
            if candidates:
                candidate = next(
                    (
                        report
                        for report in candidates
                        if report["unobserved_task"]
                    ),
                    candidates[0] if candidates else None,
                )
                if candidate is not None:
                    selected.append(candidate["task_file"])
                    selected_files.add(candidate["task_file"])
                    covered_targets.update(
                        set(candidate["target_concepts"])
                        &
                        set(self.target_concept_counts)
                    )

        remaining_reports = [
            report
            for report in task_reports
            if report["task_file"] not in selected_files
        ]
        remaining_reports.sort(
            key=lambda item: (
                -item["target_coverage_gap"],
                -item["priority"],
                item["original_order"],
            )
        )

        for report in remaining_reports:
            if len(selected) >= batch_size:
                break
            selected.append(report["task_file"])
            selected_files.add(report["task_file"])

        return selected


__all__ = [
    "CurriculumManager",
]
