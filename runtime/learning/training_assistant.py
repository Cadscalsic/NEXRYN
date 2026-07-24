import json
import random
import uuid
from datetime import datetime
from pathlib import Path

from runtime.training.curriculum_manager import CurriculumManager
from runtime.training.elite_curriculum_validator import (
    ELITE_CURRICULUM_NAME,
    ELITE_VALIDATION_ACADEMY_PATH,
    validate_elite_curriculum,
)


class TrainingAssistant:
    SCHEMA_VERSION = 1
    DOMAIN_OPERATIONALIZATION_ORDER = {
        "Spatial": 0,
        "Identity": 1,
        "Transformation": 2,
        "Color": 3,
        "Geometry": 4,
        "Topology": 5,
        "Growth": 6,
    }
    TASK_COOLDOWN_RUNS = 20
    UNSEEN_TASK_BOOST = 3.0
    RECENT_TASK_PENALTY = 0.1
    TARGET_EXPERIENCE_PER_CAPABILITY = 3
    SELECTION_MODES = {"random", "weighted_random", "curriculum"}

    def __init__(
        self,
        state_path="runtime/artifacts/runtime_data/training_assistant_state.json",
        batch_size=3,
        curriculum_manager=None,
        selection_memory_path="runtime/cache/task_selection_memory.json",
        selection_mode="weighted_random",
        random_seed=None,
        task_cooldown_runs=TASK_COOLDOWN_RUNS,
        survival_store_path="runtime/artifacts/runtime_data/operational_capability_survival.json",
        operational_economy_path="runtime/artifacts/runtime_data/operational_economy_report.json",
        validation_academy_path=ELITE_VALIDATION_ACADEMY_PATH,
    ):
        self.state_path = Path(state_path)
        self.batch_size = max(int(batch_size), 1)
        self.curriculum_manager = curriculum_manager or CurriculumManager()
        self.selection_memory_path = Path(selection_memory_path)
        self.selection_mode = self._selection_mode(selection_mode)
        self.random_seed = random_seed
        self.task_cooldown_runs = max(int(task_cooldown_runs), 0)
        self.survival_store_path = Path(survival_store_path)
        self.operational_economy_path = Path(operational_economy_path)
        self.validation_academy_path = Path(validation_academy_path)
        self.state = self._load()
        self.selection_memory = self._load_selection_memory()

    def _default_state(self):
        return {
            "schema_version": self.SCHEMA_VERSION,
            "next_task_index": 0,
            "next_elite_task_index": 0,
            "completed_cycles": 0,
            "active_batch": [],
            "pending_next_task_index": None,
            "pending_next_elite_task_index": None,
            "prioritized_concepts": [],
            "selected_concepts": [],
            "curriculum_report": {},
            "selection_diversity_report": {},
            "elite_selection_report": {},
            "training_economy_alignment_report": {},
            "history": [],
        }

    def _load(self):
        if not self.state_path.exists():
            return self._default_state()
        try:
            with self.state_path.open("r", encoding="utf-8") as file:
                state = json.load(file)
            if not isinstance(state, dict):
                return self._default_state()
            return {
                **self._default_state(),
                **state,
            }
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return self._default_state()

    def _persist(self):
        temporary_path = self.state_path.with_suffix(
            f"{self.state_path.suffix}.tmp"
        )
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                self.state,
                file,
                indent=2,
                ensure_ascii=True,
            )
        temporary_path.replace(self.state_path)

    def _default_selection_memory(self):
        return {
            "schema_version": 1,
            "run_counter": 0,
            "previous_batch": [],
            "recent_runs": [],
            "tasks": {},
        }

    def _load_selection_memory(self):
        if not self.selection_memory_path.exists():
            return self._default_selection_memory()
        try:
            with self.selection_memory_path.open("r", encoding="utf-8") as file:
                memory = json.load(file)
            if not isinstance(memory, dict):
                return self._default_selection_memory()
            return {
                **self._default_selection_memory(),
                **memory,
                "previous_batch": list(memory.get("previous_batch", [])),
                "recent_runs": list(memory.get("recent_runs", [])),
                "tasks": dict(memory.get("tasks", {})),
            }
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return self._default_selection_memory()

    def _persist_selection_memory(self):
        temporary_path = self.selection_memory_path.with_suffix(
            f"{self.selection_memory_path.suffix}.tmp"
        )
        self.selection_memory_path.parent.mkdir(parents=True, exist_ok=True)
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                self.selection_memory,
                file,
                indent=2,
                ensure_ascii=True,
            )
        temporary_path.replace(self.selection_memory_path)

    def reset(self):
        self.state = self._default_state()
        self.selection_memory = self._default_selection_memory()
        self._persist()
        self._persist_selection_memory()
        return self.report()

    def reset_selection_memory(self):
        self.selection_memory = self._default_selection_memory()
        self._persist_selection_memory()
        return self.report()

    def _normalized_tasks(self, task_files):
        return sorted({
            str(task_file)
            for task_file in task_files
            if str(task_file).endswith(".json")
        })

    def _selection_mode(self, selection_mode):
        selection_mode = str(selection_mode or "weighted_random")
        if selection_mode not in self.SELECTION_MODES:
            raise ValueError(
                "selection_mode must be one of: "
                f"{', '.join(sorted(self.SELECTION_MODES))}"
            )
        return selection_mode

    def _active_batch_is_valid(self, task_files):
        active_batch = self.state.get("active_batch", [])
        return (
            bool(active_batch)
            and len(active_batch) == min(self.batch_size, len(task_files))
            and all(
            task_file in task_files
            for task_file in active_batch
            )
        )

    def _task_metadata(self, task_file, task_directory=None):
        return self.curriculum_manager._task_metadata(
            task_file,
            task_directory,
        )

    def _load_operational_economy_report(self):
        if not self.operational_economy_path.exists():
            return {}
        try:
            with self.operational_economy_path.open("r", encoding="utf-8") as file:
                report = json.load(file)
            return report if isinstance(report, dict) else {}
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return {}

    def _load_validation_academy_tasks(self):
        if not self.validation_academy_path.exists():
            return []
        try:
            with self.validation_academy_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return []
        tasks = payload.get("tasks") or []
        return [task for task in tasks if isinstance(task, dict)]

    def _term(self, value):
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def _metadata_terms(self, metadata):
        terms = set()

        def visit(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    visit(key)
                    visit(item)
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)
            elif value is not None:
                term = self._term(value)
                if term:
                    terms.add(term)
                    terms.update(part for part in term.split("_") if part)

        for key in (
            "target_concepts",
            "target_domains",
            "deficiency_targets",
            "required_operational_capabilities",
            "composite_capabilities",
            "capability_graduation_targets",
            "domain_expansion_targets",
            "adaptive_reuse_opportunities",
            "curriculum_diagnostics_tags",
            "independent_validation_opportunities",
            "required_evidence",
            "evidence_targets",
            "validation_evidence",
            "task_properties",
            "transformation_contract",
            "operation_contract",
            "primary_operation",
            "ground_truth_type",
            "required_task_property",
            "required_ground_truth",
            "target_capability",
            "target_cluster",
            "target_domain",
            "validation_objective",
            "trust_objective",
            "graduation_objective",
            "operationalization_objective",
        ):
            visit(metadata.get(key))
        return terms

    def _operational_economy_context(self, report):
        report = report if isinstance(report, dict) else {}
        investment_rows = [
            row for row in report.get("capability_investment_priorities", []) or []
            if isinstance(row, dict)
        ]
        clusters = [
            row for row in report.get("operational_capability_clusters", []) or []
            if isinstance(row, dict)
        ]
        roadmap = [
            row for row in report.get("operational_economy_roadmap", []) or []
            if isinstance(row, dict)
        ]
        grounding_rows = [
            row for row in report.get("grounding_requirement_rows", []) or []
            if isinstance(row, dict)
        ]
        for cluster in clusters:
            grounding_rows.extend([
                row for row in cluster.get("required_grounding", []) or []
                if isinstance(row, dict)
            ])
        capability_targets = []
        for row in investment_rows[:8]:
            operation = row.get("operation")
            if operation:
                capability_targets.append(self._term(operation))
        cluster_targets = []
        for row in clusters[:8]:
            cluster_targets.append(self._term(row.get("cluster_name")))
            for capability in row.get("member_capabilities") or []:
                cluster_targets.append(self._term(capability))
            for capability in row.get("missing_capabilities") or []:
                cluster_targets.append(self._term(capability))
        roadmap_targets = []
        for row in roadmap[:7]:
            roadmap_targets.extend([
                self._term(row.get("priority")),
                self._term(row.get("target")),
                self._term(row.get("action")),
            ])
        grounding_targets = []
        grounding_properties = []
        for row in grounding_rows[:12]:
            grounding_targets.append(self._term(row.get("operation")))
            grounding_properties.extend([
                self._term(row.get("required_task_property")),
                self._term(row.get("required_evidence")),
            ])
        return {
            "source_available": bool(report),
            "operational_economy_health": report.get("operational_economy_health"),
            "capability_economy_crisis_state": report.get(
                "capability_economy_crisis_state"
            ),
            "operational_economy_bottleneck": report.get(
                "operational_economy_bottleneck"
            ),
            "governed_validation_bottleneck_state": report.get(
                "governed_validation_bottleneck_state"
            ),
            "governed_validation_action": report.get(
                "governed_validation_action"
            ),
            "governed_validation_required_evidence": report.get(
                "governed_validation_required_evidence"
            ),
            "investment_targets": sorted(set(filter(None, capability_targets))),
            "cluster_targets": sorted(set(filter(None, cluster_targets))),
            "roadmap_targets": sorted(set(filter(None, roadmap_targets))),
            "grounding_targets": sorted(set(filter(None, grounding_targets))),
            "grounding_properties": sorted(set(filter(None, grounding_properties))),
            "investment_rows": investment_rows[:8],
            "cluster_rows": clusters[:8],
            "roadmap_rows": roadmap[:7],
            "grounding_requirement_rows": grounding_rows[:12],
        }

    def _training_economy_priority(self, metadata, economy_context):
        if not economy_context or not economy_context.get("source_available"):
            return 0.0, [], []
        terms = self._metadata_terms(metadata)
        matches = []
        priority = 0.0
        reasons = []

        def matched_targets(targets):
            found = []
            for target in targets:
                if not target:
                    continue
                target_parts = set(target.split("_"))
                if target in terms or target_parts.intersection(terms):
                    found.append(target)
            return sorted(set(found))

        def matched_grounding_targets(targets):
            found = []
            for target in targets:
                if not target:
                    continue
                if target in terms:
                    found.append(target)
            return sorted(set(found))

        investment_matches = matched_targets(
            economy_context.get("investment_targets", [])
        )
        if investment_matches:
            priority += 45 + min(len(investment_matches), 4) * 8
            reasons.append("capability_economy_investment_alignment")
            matches.extend(
                {
                    "match_type": "investment_priority",
                    "target": target,
                }
                for target in investment_matches[:6]
            )

        cluster_matches = matched_targets(economy_context.get("cluster_targets", []))
        if cluster_matches:
            priority += 35 + min(len(cluster_matches), 5) * 6
            reasons.append("operational_cluster_training_alignment")
            matches.extend(
                {
                    "match_type": "operational_cluster",
                    "target": target,
                }
                for target in cluster_matches[:6]
            )

        roadmap_matches = matched_targets(economy_context.get("roadmap_targets", []))
        if roadmap_matches:
            priority += 30 + min(len(roadmap_matches), 4) * 5
            reasons.append("operational_economy_roadmap_alignment")
            matches.extend(
                {
                    "match_type": "economy_roadmap",
                    "target": target,
                }
                for target in roadmap_matches[:6]
            )

        grounding_matches = matched_grounding_targets(
            economy_context.get("grounding_targets", [])
        )
        grounding_property_matches = matched_grounding_targets(
            economy_context.get("grounding_properties", [])
        )
        if grounding_matches or grounding_property_matches:
            priority += (
                40
                + min(len(grounding_matches), 4) * 6
                + min(len(grounding_property_matches), 3) * 10
            )
            reasons.append("grounding_economy_alignment")
            matches.extend(
                {
                    "match_type": "grounding_requirement",
                    "target": target,
                }
                for target in grounding_matches[:6]
            )
            matches.extend(
                {
                    "match_type": "grounding_required_task_property",
                    "target": target,
                }
                for target in grounding_property_matches[:6]
            )

        governed_evidence = self._term(
            economy_context.get("governed_validation_required_evidence")
        )
        governed_action = self._term(economy_context.get("governed_validation_action"))
        governed_evidence_match = bool(governed_evidence and governed_evidence in terms)
        governed_action_match = bool(
            governed_action
            and any(part in terms for part in governed_action.split("_"))
        )
        if governed_evidence_match or governed_action_match:
            priority += 35
            reasons.append("governed_validation_evidence_alignment")
            matches.append({
                "match_type": "governed_validation_required_evidence",
                "target": governed_evidence or governed_action,
            })

        bottleneck = self._term(economy_context.get("operational_economy_bottleneck"))
        if bottleneck and any(part in terms for part in bottleneck.split("_")):
            priority += 25
            reasons.append("operational_economy_bottleneck_probe")
            matches.append({
                "match_type": "economy_bottleneck",
                "target": bottleneck,
            })

        return round(priority, 4), reasons, matches[:12]

    def _validation_academy_priority(
        self,
        metadata,
        *,
        validation_academy_tasks,
        survival_targets,
        operational_economy_context,
    ):
        if not validation_academy_tasks:
            return 0.0, [], []
        terms = self._metadata_terms(metadata) | self._task_evidence_terms(metadata)
        survival_targets = [
            target for target in (survival_targets or [])
            if isinstance(target, dict)
        ]
        target_operations = {
            self._term(target.get("operation"))
            for target in survival_targets
            if target.get("operation")
        }
        target_operations.update(
            self._term(target)
            for target in (
                operational_economy_context or {}
            ).get("grounding_targets", [])
            if target
        )
        required_properties = {
            self._term(target.get("required_task_property"))
            for target in survival_targets
            if target.get("required_task_property")
        }
        required_properties.update(
            self._term(prop)
            for prop in (
                operational_economy_context or {}
            ).get("grounding_properties", [])
            if prop
        )
        governed_evidence = self._term(
            (operational_economy_context or {}).get(
                "governed_validation_required_evidence"
            )
        )
        if governed_evidence:
            required_properties.add(governed_evidence)
        priority = 0.0
        matches = []
        for academy_task in validation_academy_tasks:
            capability = self._term(academy_task.get("target_capability"))
            required_property = self._term(
                academy_task.get("required_task_property")
            )
            required_evidence = self._term(
                academy_task.get("required_validation_evidence")
            )
            cluster = self._term(academy_task.get("target_cluster"))
            domain = self._term(academy_task.get("target_domain"))
            overlap = sorted(
                item for item in {
                    capability,
                    required_property,
                    required_evidence,
                    cluster,
                    domain,
                }
                if item and item in terms
            )
            if not overlap:
                continue
            contribution = 0.0
            if capability and capability in target_operations:
                contribution += 65
            if required_property and required_property in required_properties:
                contribution += 80
            if required_evidence and required_evidence in required_properties:
                contribution += 40
            if cluster and cluster in terms:
                contribution += 25
            if domain and domain in terms:
                contribution += 10
            if required_property and required_property in terms:
                contribution += 35
            if contribution <= 0:
                continue
            contribution *= float(academy_task.get("promotion_weight") or 1.0)
            priority += contribution
            matches.append({
                "match_type": "elite_validation_opportunity",
                "academy_task_id": academy_task.get("task_id"),
                "elite_group": academy_task.get("elite_group"),
                "target_capability": academy_task.get("target_capability"),
                "target_cluster": academy_task.get("target_cluster"),
                "required_task_property": academy_task.get(
                    "required_task_property"
                ),
                "required_validation_evidence": academy_task.get(
                    "required_validation_evidence"
                ),
                "matched_terms": overlap,
                "priority": round(contribution, 4),
            })
        matches.sort(key=lambda item: -float(item.get("priority") or 0.0))
        reasons = ["elite_validation_task_selection_intelligence"] if matches else []
        if any(
            self._term(match.get("required_task_property")) in required_properties
            for match in matches
        ):
            reasons.append("validation_task_property_match")
        if any(
            self._term(match.get("target_capability")) in target_operations
            for match in matches
        ):
            reasons.append("capability_directed_validation")
        return round(priority, 4), reasons, matches[:5]

    def _training_economy_alignment_report(
        self,
        selected,
        elite_selection_report,
        economy_context,
    ):
        priorities = elite_selection_report.get("elite_task_priorities", [])
        priorities = priorities if isinstance(priorities, list) else []
        selected_set = set(selected or [])
        selected_rows = [
            row for row in priorities
            if isinstance(row, dict) and row.get("task_file") in selected_set
        ]
        match_rows = [
            match
            for row in selected_rows
            for match in row.get("training_economy_matches", []) or []
            if isinstance(match, dict)
        ]
        academy_match_rows = [
            match
            for row in selected_rows
            for match in row.get("validation_academy_matches", []) or []
            if isinstance(match, dict)
        ]
        matched_targets = sorted({
            str(match.get("target"))
            for match in match_rows
            if match.get("target")
        })
        grounding_match_rows = [
            match for match in match_rows
            if str(match.get("match_type", "")).startswith("grounding")
        ]
        selected_grounding_aligned_tasks = [
            row.get("task_file")
            for row in selected_rows
            if any(
                isinstance(match, dict)
                and str(match.get("match_type", "")).startswith("grounding")
                for match in row.get("training_economy_matches", []) or []
            )
        ]
        selected_with_matches = [
            row.get("task_file")
            for row in selected_rows
            if row.get("training_economy_matches")
        ]
        return {
            "system": "training_economy_alignment",
            "operational_economy_source_available": bool(
                economy_context.get("source_available")
            ),
            "alignment_state": (
                "ECONOMY_ALIGNED_TRAINING"
                if selected_with_matches
                else "ECONOMY_SIGNAL_AVAILABLE_WITHOUT_SELECTED_MATCH"
                if economy_context.get("source_available")
                else "NO_OPERATIONAL_ECONOMY_SIGNAL"
            ),
            "operational_economy_health": economy_context.get(
                "operational_economy_health"
            ),
            "capability_economy_crisis_state": economy_context.get(
                "capability_economy_crisis_state"
            ),
            "operational_economy_bottleneck": economy_context.get(
                "operational_economy_bottleneck"
            ),
            "governed_validation_bottleneck_state": economy_context.get(
                "governed_validation_bottleneck_state"
            ),
            "governed_validation_action": economy_context.get(
                "governed_validation_action"
            ),
            "governed_validation_required_evidence": economy_context.get(
                "governed_validation_required_evidence"
            ),
            "investment_targets": economy_context.get("investment_targets", []),
            "cluster_targets": economy_context.get("cluster_targets", []),
            "roadmap_targets": economy_context.get("roadmap_targets", []),
            "grounding_targets": economy_context.get("grounding_targets", []),
            "grounding_properties": economy_context.get("grounding_properties", []),
            "selected_economy_aligned_tasks": selected_with_matches,
            "selected_grounding_aligned_tasks": selected_grounding_aligned_tasks,
            "matched_economy_targets": matched_targets[:12],
            "matched_grounding_targets": [
                match.get("target")
                for match in grounding_match_rows[:12]
                if match.get("target")
            ],
            "grounding_economy_alignment": (
                "GROUNDING_ECONOMY_ALIGNED"
                if selected_grounding_aligned_tasks
                else "GROUNDING_SIGNAL_AVAILABLE_WITHOUT_SELECTED_MATCH"
                if economy_context.get("grounding_requirement_rows")
                else "NO_GROUNDING_ECONOMY_SIGNAL"
            ),
            "grounding_alignment_trace": [
                {
                    "selected_task": row.get("task_file"),
                    "matched_operation_or_property": match.get("target"),
                    "match_type": match.get("match_type"),
                    "evidence_collection_attempted": (
                        str(match.get("match_type", "")).startswith("grounding")
                    ),
                }
                for row in selected_rows
                for match in row.get("training_economy_matches", []) or []
                if isinstance(match, dict)
                and str(match.get("match_type", "")).startswith("grounding")
            ][:12],
            "validation_academy_alignment": (
                "VALIDATION_ACADEMY_ALIGNED"
                if academy_match_rows
                else "VALIDATION_ACADEMY_AVAILABLE_WITHOUT_SELECTED_MATCH"
                if elite_selection_report.get("elite_task_priorities")
                else "NO_VALIDATION_ACADEMY_SIGNAL"
            ),
            "validation_academy_alignment_trace": [
                {
                    "selected_task": row.get("task_file"),
                    "academy_task_id": match.get("academy_task_id"),
                    "target_capability": match.get("target_capability"),
                    "target_cluster": match.get("target_cluster"),
                    "required_task_property": match.get(
                        "required_task_property"
                    ),
                    "required_validation_evidence": match.get(
                        "required_validation_evidence"
                    ),
                    "evidence_collection_attempted": True,
                }
                for row in selected_rows
                for match in row.get("validation_academy_matches", []) or []
                if isinstance(match, dict)
            ][:12],
            "validation_academy_match_count": len(academy_match_rows),
            "alignment_match_count": len(match_rows),
            "training_economy_alignment_score": round(
                len(selected_with_matches) / max(len(selected or []), 1),
                4,
            ),
        }

    def _is_elite_task(self, task_file, task_directory=None):
        if str(task_file).startswith("elite_cognitive_task_"):
            return True
        metadata = self._task_metadata(task_file, task_directory)
        return bool(
            metadata.get("elite_cognitive_task")
            or str(metadata.get("curriculum", "")).startswith(
                "nexryn_elite_cognitive_training"
            )
        )

    def _partition_elite_tasks(self, task_files, task_directory=None):
        elite = []
        normal = []
        for task_file in task_files:
            if self._is_elite_task(task_file, task_directory):
                elite.append(task_file)
            else:
                normal.append(task_file)
        return elite, normal

    def _elite_operationalization_policy_active(
        self,
        elite_task_files,
        task_directory=None,
    ):
        if len(elite_task_files) < self.batch_size:
            return False
        for task_file in elite_task_files[: min(len(elite_task_files), 20)]:
            metadata = self._task_metadata(task_file, task_directory)
            if (
                metadata.get("curriculum") == ELITE_CURRICULUM_NAME
                and metadata.get("operationalization_phase_curriculum")
            ):
                return True
        return False

    def _active_batch_matches_elite_policy(
        self,
        task_files,
        elite_task_files,
        task_directory=None,
    ):
        if not elite_task_files:
            return True
        active_batch = list(self.state.get("active_batch", []))
        elite_set = set(elite_task_files)
        if self._elite_operationalization_policy_active(
            elite_task_files,
            task_directory,
        ):
            return active_batch and all(
                task_file in elite_set for task_file in active_batch
            )
        return sum(1 for task_file in active_batch if task_file in elite_set) == 1

    def _core_knowledge_concepts(self, core_knowledge=None):
        concepts = set()
        for item in core_knowledge or []:
            if not isinstance(item, dict):
                continue
            concept = item.get("concept")
            if concept:
                concepts.add(str(concept))
        return concepts

    def _load_survival_store(self):
        if not self.survival_store_path.exists():
            return {}
        try:
            with self.survival_store_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return {}

    def _survival_reappearance_targets(self):
        rows = [
            row for row in self._load_survival_store().values()
            if isinstance(row, dict)
        ]
        population_policy = self._capability_population_evolution_policy(rows)
        targets = []
        for row in rows:
            lifecycle_state = str(row.get("lifecycle_state") or "")
            next_evidence = str(row.get("next_required_evidence") or "")
            if lifecycle_state not in {
                "ARENA_SIMULATED",
                "INCUBATING_VALIDATION_GAP",
                "SURVIVING_CAPABILITY",
            }:
                continue
            if next_evidence not in {
                "independent_task_reappearance",
                "repeatable_validation_across_independent_task",
                "prediction_quality_improvement",
                "validator_acceptance",
                "stability_recovery_evidence",
                "exact_or_governed_validation_success",
            }:
                continue
            improvement_trend = str(row.get("improvement_trend") or "")
            try:
                best_accuracy = float(row.get("best_accuracy"))
            except (TypeError, ValueError):
                best_accuracy = 0.0
            try:
                average_accuracy = float(row.get("average_accuracy"))
            except (TypeError, ValueError):
                average_accuracy = 0.0
            arena_quality_count = int(row.get("arena_quality_count", 0) or 0)
            distinct_task_count = int(row.get("distinct_task_count", 0) or 0)
            crystallization_candidate = (
                lifecycle_state in {
                    "INCUBATING_VALIDATION_GAP",
                    "SURVIVING_CAPABILITY",
                }
                and arena_quality_count >= 3
                and distinct_task_count >= 3
                and best_accuracy >= 0.90
                and average_accuracy >= 0.75
                and improvement_trend not in {"DECLINING", "DECLINING_CRITICAL"}
            )
            if (
                distinct_task_count >= 3
                and improvement_trend not in {"DECLINING", "DECLINING_CRITICAL"}
                and not crystallization_candidate
            ):
                continue
            priority = (
                100
                + int(row.get("validation_attempts", 0) or 0) * 8
                + int(row.get("arena_simulated_count", 0) or 0) * 5
                + best_accuracy * 40
            )
            if lifecycle_state == "INCUBATING_VALIDATION_GAP":
                priority += 35
            elif lifecycle_state == "SURVIVING_CAPABILITY":
                priority += 20
            if improvement_trend in {"DECLINING", "DECLINING_CRITICAL"}:
                priority += 90
            if crystallization_candidate:
                priority += 120
            if population_policy.get("policy_state") in {
                "POPULATION_EVOLUTION_SPRINT",
                "SEVERE_POPULATION_EVOLUTION_SPRINT",
            }:
                if lifecycle_state == "SURVIVING_CAPABILITY":
                    priority += 160
                elif crystallization_candidate:
                    priority += 110
                elif lifecycle_state == "INCUBATING_VALIDATION_GAP":
                    priority += 50
            targets.append({
                "capability_id": row.get("capability_id"),
                "operation": str(row.get("operation") or ""),
                "domain": str(row.get("domain") or ""),
                "semantic_intent": str(row.get("semantic_intent") or ""),
                "lifecycle_state": lifecycle_state,
                "next_required_evidence": next_evidence,
                "improvement_trend": improvement_trend,
                "best_accuracy": best_accuracy,
                "average_accuracy": average_accuracy,
                "arena_quality_count": arena_quality_count,
                "distinct_task_count": distinct_task_count,
                "crystallization_candidate": crystallization_candidate,
                "maturation_no_progress": (
                    lifecycle_state == "SURVIVING_CAPABILITY"
                    and next_evidence == "exact_or_governed_validation_success"
                    and distinct_task_count >= 8
                    and int(row.get("validation_attempts", 0) or 0) >= 6
                    and average_accuracy < 0.80
                ),
                "required_task_property": self._required_task_property_for_evidence(
                    row,
                    next_evidence,
                ),
                "population_evolution_target": bool(
                    row.get("capability_id") in set(
                        population_policy.get("target_capability_ids", [])
                    )
                ),
                "priority": round(priority, 4),
            })
        targets.sort(
            key=lambda item: (
                -float(item.get("priority") or 0.0),
                str(item.get("capability_id") or ""),
            )
        )
        return targets[:10]

    def _capability_population_evolution_policy(self, rows=None):
        rows = [
            row for row in (rows if rows is not None else self._load_survival_store().values())
            if isinstance(row, dict)
        ]
        citizen_rows = [
            row for row in rows
            if row.get("lifecycle_state") == "OPERATIONAL_CITIZEN"
        ]
        maturation_rows = []
        graduation_rows = []
        operational_experience_count = 0
        for row in rows:
            experience_count = self._row_int(
                row,
                "operational_experience_count",
                "experience_count",
                "reuse_count",
            )
            if experience_count <= 0:
                experience_count = max(
                    self._row_int(row, "arena_simulated_count"),
                    self._row_int(row, "distinct_task_count"),
                )
            operational_experience_count += experience_count
            lifecycle_state = str(row.get("lifecycle_state") or "")
            if lifecycle_state not in {
                "INCUBATING_VALIDATION_GAP",
                "SURVIVING_CAPABILITY",
            }:
                continue
            best_accuracy = self._row_float(row, "best_accuracy")
            average_accuracy = self._row_float(row, "average_accuracy")
            distinct_task_count = self._row_int(row, "distinct_task_count")
            arena_quality_count = self._row_int(row, "arena_quality_count")
            arena_simulated_count = self._row_int(row, "arena_simulated_count")
            trend = str(row.get("improvement_trend") or "")
            if (
                distinct_task_count >= 3
                and max(arena_quality_count, arena_simulated_count) >= 3
                and best_accuracy >= 0.85
                and average_accuracy >= 0.70
                and trend not in {"DECLINING_CRITICAL"}
            ):
                maturation_rows.append(row)
            if (
                lifecycle_state == "SURVIVING_CAPABILITY"
                and distinct_task_count >= 15
                and max(arena_quality_count, arena_simulated_count) >= 15
                and best_accuracy >= 0.90
                and average_accuracy >= 0.70
                and trend in {
                    "IMPROVING",
                    "STABLE",
                    "STABLE_HIGH_PERFORMANCE",
                    "DECLINING_MINOR",
                }
            ):
                graduation_rows.append(row)
        citizen_count = len(citizen_rows)
        expected_population = max(
            citizen_count + len(maturation_rows),
            int(
                (operational_experience_count + self.TARGET_EXPERIENCE_PER_CAPABILITY - 1)
                / self.TARGET_EXPERIENCE_PER_CAPABILITY
            )
            if operational_experience_count > 0
            else 0,
        )
        evolution_gap = max(expected_population - citizen_count, 0)
        evolution_lag = (
            round(evolution_gap / expected_population, 4)
            if expected_population > 0
            else None
        )
        experience_per_citizen = (
            round(operational_experience_count / citizen_count, 4)
            if citizen_count > 0
            else None
        )
        policy_state = (
            "NOT_MEASURABLE"
            if expected_population <= 0
            else "SEVERE_POPULATION_EVOLUTION_SPRINT"
            if evolution_lag is not None and evolution_lag >= 0.60
            else "POPULATION_EVOLUTION_SPRINT"
            if evolution_lag is not None and evolution_lag >= 0.30
            else "POPULATION_EVOLVING"
        )
        maturation_rows.sort(
            key=lambda row: (
                str(row.get("lifecycle_state") or "") != "SURVIVING_CAPABILITY",
                -self._row_float(row, "best_accuracy"),
                -self._row_float(row, "average_accuracy"),
                str(row.get("capability_id") or ""),
            )
        )
        return {
            "system": "capability_population_evolution_policy",
            "policy_state": policy_state,
            "target_experience_per_capability": self.TARGET_EXPERIENCE_PER_CAPABILITY,
            "operational_experience_count": operational_experience_count,
            "operational_citizen_count": citizen_count,
            "maturation_backlog_count": len(maturation_rows),
            "graduation_queue_count": len(graduation_rows),
            "expected_operational_population": expected_population,
            "capability_population_evolution_gap": evolution_gap,
            "capability_population_evolution_lag": evolution_lag,
            "operational_experience_per_citizen": experience_per_citizen,
            "target_capability_ids": [
                str(row.get("capability_id"))
                for row in maturation_rows[:10]
                if row.get("capability_id")
            ],
            "target_operations": list(dict.fromkeys(
                str(row.get("operation"))
                for row in maturation_rows[:10]
                if row.get("operation")
            )),
            "graduation_target_operations": list(dict.fromkeys(
                str(row.get("operation"))
                for row in graduation_rows[:10]
                if row.get("operation")
            )),
            "governance_action": (
                "graduation_sprint_required"
                if graduation_rows
                else
                "prioritize_maturation_reappearance"
                if policy_state in {
                    "POPULATION_EVOLUTION_SPRINT",
                    "SEVERE_POPULATION_EVOLUTION_SPRINT",
                }
                else "monitor_population_evolution"
            ),
        }

    def _row_int(self, row, *keys):
        for key in keys:
            try:
                value = row.get(key)
                if value is not None:
                    return int(value or 0)
            except (TypeError, ValueError):
                continue
        return 0

    def _row_float(self, row, key):
        try:
            return float(row.get(key) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _survival_terms_for(self, target):
        operation = str(target.get("operation") or "").lower()
        domain = str(target.get("domain") or "").lower()
        semantic_intent = str(target.get("semantic_intent") or "").lower()
        terms = {
            operation,
            domain,
            semantic_intent,
            operation.replace("preserve_", ""),
            semantic_intent.replace("_preservation", ""),
        }
        if "topolog" in operation or "topolog" in domain or "topolog" in semantic_intent:
            terms.update({"topology", "topological_reasoning", "topological_growth"})
        if "color" in operation or "color" in domain or "color" in semantic_intent:
            terms.update({"color", "color_transformation", "color_mapping"})
        if "growth" in operation or "growth" in domain or operation == "duplicate_object":
            terms.update({"growth", "topological_growth", "object_evolution"})
        if "spatial" in domain or "grid" in operation or "translate" in operation:
            terms.update({"spatial", "spatial_reasoning", "translation"})
        if "identity" in operation or "identity" in domain or "identity" in semantic_intent:
            terms.update({"identity", "identity_preservation"})
        return {term for term in terms if term}

    def _required_task_property_for_evidence(self, row, next_evidence):
        operation = str(row.get("operation") or "").lower()
        if next_evidence == "exact_or_governed_validation_success":
            if operation == "translate":
                return "unambiguous_directional_translation_ground_truth"
            return "exact_or_governed_validation_ground_truth"
        if next_evidence == "stability_recovery_evidence":
            return "stability_recovery_probe"
        if next_evidence in {
            "independent_task_reappearance",
            "repeatable_validation_across_independent_task",
        }:
            return "independent_task_signature"
        if next_evidence == "prediction_quality_improvement":
            return "quality_improvement_probe"
        if next_evidence == "validator_acceptance":
            return "validator_acceptance_probe"
        return "independent_task_signature"

    def _task_evidence_terms(self, metadata):
        values = []
        for key in (
            "required_evidence",
            "evidence_targets",
            "validation_evidence",
            "task_properties",
            "transformation_contract",
            "operation_contract",
            "primary_operation",
            "ground_truth_type",
            "required_task_property",
            "required_ground_truth",
            "target_capability",
            "target_cluster",
            "target_domain",
            "validation_objective",
            "trust_objective",
            "graduation_objective",
            "operationalization_objective",
        ):
            values.extend(self._flatten_metadata_values(metadata.get(key)))
        normalized = {
            str(value).strip().lower()
            for value in values
            if str(value).strip()
        }
        if "translate" in normalized or "translation" in normalized:
            normalized.add("directional_translation")
        if "directional_translation" in normalized:
            normalized.add("unambiguous_directional_translation_ground_truth")
        if "exact_validation" in normalized or "exact_match" in normalized:
            normalized.add("exact_or_governed_validation_success")
        if "governed_validation" in normalized:
            normalized.add("exact_or_governed_validation_success")
        return normalized

    def _flatten_metadata_values(self, value):
        if value is None:
            return []
        if isinstance(value, dict):
            flattened = []
            for item in value.values():
                flattened.extend(self._flatten_metadata_values(item))
            return flattened
        if isinstance(value, (list, tuple, set)):
            flattened = []
            for item in value:
                flattened.extend(self._flatten_metadata_values(item))
            return flattened
        return [value]

    def _domain_label(self, domain):
        label = str(domain or "").strip()
        for suffix in (" Cognitive Domain", " Domain"):
            if label.endswith(suffix):
                label = label[: -len(suffix)]
        return label.strip().title()

    def _domain_citizenship_gaps(self):
        expected_domains = {
            "Color",
            "Geometry",
            "Growth",
            "Identity",
            "Spatial",
            "Topology",
            "Transformation",
        }
        rows = [
            row for row in self._load_survival_store().values()
            if isinstance(row, dict)
        ]
        citizen_domains = {
            self._domain_label(row.get("domain"))
            for row in rows
            if row.get("lifecycle_state") == "OPERATIONAL_CITIZEN"
            and row.get("domain")
        }
        candidate_domains = {
            self._domain_label(row.get("domain"))
            for row in rows
            if row.get("domain")
            and row.get("lifecycle_state") in {
                "ARENA_SIMULATED",
                "INCUBATING_VALIDATION_GAP",
                "SURVIVING_CAPABILITY",
            }
        }
        regression_domains = {
            self._domain_label(row.get("domain"))
            for row in rows
            if row.get("domain")
            and row.get("improvement_trend") in {"DECLINING", "DECLINING_CRITICAL"}
        }
        missing = sorted(expected_domains - citizen_domains)
        active_missing = sorted(candidate_domains - citizen_domains)
        return {
            "expected_domains": sorted(expected_domains),
            "citizen_domains": sorted(citizen_domains),
            "missing_citizen_domains": missing,
            "active_missing_citizen_domains": active_missing,
            "regression_domains": sorted(regression_domains),
        }

    def _domain_terms_for(self, domain):
        domain = self._domain_label(domain).lower()
        terms = {domain}
        if domain == "spatial":
            terms.update({"spatial_reasoning", "translation", "path_finding"})
        elif domain == "identity":
            terms.update({"identity_preservation", "preserve_grid", "preserve_shape"})
        elif domain == "transformation":
            terms.update({"transformation", "program_composition", "unknown_transformation"})
        elif domain == "topology":
            terms.update({"topological_reasoning", "topological_change", "bridge_creation"})
        elif domain == "geometry":
            terms.update({"geometry", "symmetry", "reflection", "rotation"})
        elif domain == "growth":
            terms.update({"growth", "object_evolution", "duplicate_object"})
        elif domain == "color":
            terms.update({"color", "color_transformation", "preserve_colors"})
        return terms

    def _domain_citizenship_priority(self, task_terms, domain_gaps):
        task_terms = {str(term).lower() for term in task_terms if term}
        active_missing = domain_gaps.get("active_missing_citizen_domains") or []
        missing = domain_gaps.get("missing_citizen_domains") or []
        priority = 0.0
        matches = []
        for domain in missing:
            domain_terms = self._domain_terms_for(domain)
            overlap = task_terms & domain_terms
            if not overlap:
                continue
            rank_bonus = max(
                0,
                6 - self.DOMAIN_OPERATIONALIZATION_ORDER.get(domain, 6),
            ) * 12.0
            contribution = (110.0 if domain in active_missing else 55.0) + rank_bonus
            priority += contribution
            matches.append({
                "domain": domain,
                "matched_terms": sorted(overlap),
                "priority": contribution,
                "gap_type": (
                    "active_capability_without_citizen"
                    if domain in active_missing
                    else "missing_domain_citizen"
                ),
            })
        matches.sort(key=lambda item: -float(item.get("priority") or 0.0))
        return round(priority, 4), matches[:3]

    def _survival_reappearance_priority(
        self,
        task_terms,
        evidence_terms,
        targets,
        population_policy=None,
    ):
        task_terms = {str(term).lower() for term in task_terms if term}
        evidence_terms = {str(term).lower() for term in evidence_terms if term}
        population_policy = population_policy or {}
        sprint_active = population_policy.get("policy_state") in {
            "POPULATION_EVOLUTION_SPRINT",
            "SEVERE_POPULATION_EVOLUTION_SPRINT",
        }
        matches = []
        priority = 0.0
        for target in targets:
            survival_terms = self._survival_terms_for(target)
            overlap = task_terms & survival_terms
            if not overlap:
                continue
            contribution = float(target.get("priority") or 0.0) * (
                len(overlap) / max(len(survival_terms), 1)
            )
            evidence_aligned = self._evidence_gap_aligned(
                target,
                evidence_terms,
            )
            if evidence_aligned:
                contribution += 220.0
            if sprint_active and target.get("population_evolution_target"):
                contribution += 90.0 if evidence_aligned else 15.0
            priority += contribution
            matches.append({
                "capability_id": target.get("capability_id"),
                "operation": target.get("operation"),
                "lifecycle_state": target.get("lifecycle_state"),
                "next_required_evidence": target.get("next_required_evidence"),
                "crystallization_candidate": bool(
                    target.get("crystallization_candidate")
                ),
                "population_evolution_target": bool(
                    target.get("population_evolution_target")
                ),
                "maturation_no_progress": bool(
                    target.get("maturation_no_progress")
                ),
                "required_task_property": target.get("required_task_property"),
                "evidence_gap_aligned": bool(evidence_aligned),
                "matched_terms": sorted(overlap),
                "priority": round(contribution, 4),
            })
        matches.sort(key=lambda item: -float(item.get("priority") or 0.0))
        return round(priority, 4), matches[:3]

    def _evidence_gap_aligned(self, target, evidence_terms):
        next_evidence = str(target.get("next_required_evidence") or "")
        required = str(target.get("required_task_property") or "").lower()
        operation = str(target.get("operation") or "").lower()
        if next_evidence == "exact_or_governed_validation_success":
            if required and required in evidence_terms:
                return True
            if operation == "translate":
                return (
                    "directional_translation" in evidence_terms
                    and (
                        "exact_or_governed_validation_success" in evidence_terms
                        or "exact_validation" in evidence_terms
                        or "governed_validation" in evidence_terms
                        or "unambiguous_ground_truth" in evidence_terms
                    )
                )
            return (
                "exact_or_governed_validation_success" in evidence_terms
                or "exact_validation" in evidence_terms
                or "governed_validation" in evidence_terms
            )
        if next_evidence == "stability_recovery_evidence":
            return "stability_recovery_probe" in evidence_terms
        return False

    def _elite_priority_for(
        self,
        task_file,
        order,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        core_knowledge=None,
        survival_targets=None,
        domain_gaps=None,
        population_policy=None,
        operational_economy_context=None,
        validation_academy_tasks=None,
    ):
        metadata = self._task_metadata(task_file, task_directory)
        concepts = [
            str(concept)
            for concept in metadata.get("target_concepts", [])
            if concept
        ]
        deficiencies = [
            str(item)
            for item in metadata.get("deficiency_targets", [])
            if item
        ]
        capabilities = [
            str(item)
            for item in metadata.get("required_operational_capabilities", [])
            if item
        ]
        task_terms = set(concepts) | set(deficiencies) | set(capabilities)
        evidence_terms = self._task_evidence_terms(metadata)
        concept_counts = concept_counts or {}
        concept_states = self.curriculum_manager._concept_states(
            concept_states
        )
        priority = 0
        reasons = []
        for concept in concepts:
            count = int(concept_counts.get(concept, 0))
            if count <= 0:
                priority += 60
                reasons.append(f"unobserved_target:{concept}")
            elif count < 5:
                priority += (5 - count) * 10
                reasons.append(f"low_target_coverage:{concept}")
            state = concept_states.get(concept)
            if state in {"DISCOVERING", "BOUNDARY_REFINEMENT", "UNKNOWN"}:
                priority += 15
                reasons.append(f"active_lifecycle_gap:{concept}")
        core_concepts = self._core_knowledge_concepts(core_knowledge)
        if "replace_color" in core_concepts and not any(
            "color" in concept for concept in concepts
        ):
            priority += 80
            reasons.append("capability_monopoly_pressure:replace_color")
        if "topological_reasoning" in concepts or "topological_change" in concepts:
            priority += 25
            reasons.append("topology_domain_operationalization_pressure")
        if any("composition" in concept for concept in concepts + capabilities):
            priority += 20
            reasons.append("low_operational_yield_composition_probe")
        if any("unknown" in concept for concept in concepts + capabilities):
            priority += 20
            reasons.append("novel_capability_discovery_probe")
        survival_priority, survival_matches = (
            self._survival_reappearance_priority(
                task_terms,
                evidence_terms,
                survival_targets or [],
                population_policy=population_policy,
            )
        )
        if survival_priority:
            priority += survival_priority
            reasons.append("survival_store_independent_reappearance_probe")
            if any(
                match.get("crystallization_candidate")
                for match in survival_matches
            ):
                reasons.append("capability_crystallization_probe")
            if (
                population_policy
                and population_policy.get("policy_state") in {
                    "POPULATION_EVOLUTION_SPRINT",
                    "SEVERE_POPULATION_EVOLUTION_SPRINT",
                }
                and any(
                    match.get("population_evolution_target")
                    for match in survival_matches
                )
            ):
                reasons.append("capability_population_evolution_sprint")
            if population_policy and any(
                match.get("operation")
                in set(population_policy.get("graduation_target_operations", []))
                for match in survival_matches
            ):
                reasons.append("capability_graduation_sprint_required")
            if any(
                match.get("evidence_gap_aligned")
                for match in survival_matches
            ):
                reasons.append("evidence_gap_aligned_maturation_probe")
            if any(
                match.get("maturation_no_progress")
                for match in survival_matches
            ):
                reasons.append("maturation_no_progress_repair_probe")
        domain_priority, domain_matches = self._domain_citizenship_priority(
            task_terms,
            domain_gaps or {},
        )
        if domain_priority:
            priority += domain_priority
            reasons.append("domain_citizenship_gap_probe")
        economy_priority, economy_reasons, economy_matches = (
            self._training_economy_priority(
                metadata,
                operational_economy_context or {},
            )
        )
        if economy_priority:
            priority += economy_priority
            reasons.extend(economy_reasons)
        academy_priority, academy_reasons, academy_matches = (
            self._validation_academy_priority(
                metadata,
                validation_academy_tasks=validation_academy_tasks or [],
                survival_targets=survival_targets or [],
                operational_economy_context=operational_economy_context or {},
            )
        )
        if academy_priority:
            priority += academy_priority
            reasons.extend(academy_reasons)
        priority += max(0, 20 - order) * 0.01
        return {
            "task_file": task_file,
            "original_order": order,
            "target_concepts": concepts,
            "deficiency_targets": deficiencies,
            "required_operational_capabilities": capabilities,
            "evidence_terms": sorted(evidence_terms),
            "priority": round(priority, 4),
            "priority_reasons": reasons,
            "survival_reappearance_matches": survival_matches,
            "domain_citizenship_matches": domain_matches,
            "training_economy_matches": economy_matches,
            "validation_academy_matches": academy_matches,
        }

    def _elite_priorities(
        self,
        elite_task_files,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        core_knowledge=None,
        operational_economy_context=None,
    ):
        if not elite_task_files:
            return [], [], {}, {}, {}
        start = int(self.state.get("next_elite_task_index", 0))
        start %= len(elite_task_files)
        rotated = [
            elite_task_files[(start + offset) % len(elite_task_files)]
            for offset in range(len(elite_task_files))
        ]
        survival_targets = self._survival_reappearance_targets()
        domain_gaps = self._domain_citizenship_gaps()
        population_policy = self._capability_population_evolution_policy()
        validation_academy_tasks = self._load_validation_academy_tasks()
        priorities = [
            self._elite_priority_for(
                task_file,
                order,
                concept_counts=concept_counts,
                concept_states=concept_states,
                task_directory=task_directory,
                core_knowledge=core_knowledge,
                survival_targets=survival_targets,
                domain_gaps=domain_gaps,
                population_policy=population_policy,
                operational_economy_context=operational_economy_context,
                validation_academy_tasks=validation_academy_tasks,
            )
            for order, task_file in enumerate(rotated)
        ]
        priorities.sort(
            key=lambda item: (
                -item["priority"],
                item["original_order"],
            )
        )
        return rotated, priorities, survival_targets, domain_gaps, population_policy

    def _select_elite_task(
        self,
        elite_task_files,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        core_knowledge=None,
        operational_economy_context=None,
    ):
        if not elite_task_files:
            return None, {
                "system": "elite_task_selection",
                "elite_task_available": False,
            }
        rotated, priorities, survival_targets, domain_gaps, population_policy = (
            self._elite_priorities(
                elite_task_files,
                concept_counts=concept_counts,
                concept_states=concept_states,
                task_directory=task_directory,
                core_knowledge=core_knowledge,
                operational_economy_context=operational_economy_context,
            )
        )
        selected = priorities[0]["task_file"]
        selected_rotated_index = rotated.index(selected)
        start = int(self.state.get("next_elite_task_index", 0))
        return selected, {
            "system": "elite_task_selection",
            "elite_task_available": True,
            "policy": "exactly_one_elite_task_per_cycle",
            "selected_elite_task_file": selected,
            "elite_task_count": len(elite_task_files),
            "normal_task_slots": max(self.batch_size - 1, 0),
            "prioritized_deficiencies": priorities[0].get(
                "deficiency_targets",
                [],
            ),
            "priority_reasons": priorities[0].get("priority_reasons", []),
            "survival_reappearance_targets": survival_targets,
            "survival_reappearance_matches": priorities[0].get(
                "survival_reappearance_matches",
                [],
            ),
            "domain_citizenship_gaps": domain_gaps,
            "domain_citizenship_matches": priorities[0].get(
                "domain_citizenship_matches",
                [],
            ),
            "training_economy_matches": priorities[0].get(
                "training_economy_matches",
                [],
            ),
            "validation_academy_matches": priorities[0].get(
                "validation_academy_matches",
                [],
            ),
            "capability_population_evolution_policy": population_policy,
            "elite_task_priorities": priorities,
            "next_elite_task_index_after_completion": (
                start + selected_rotated_index + 1
            ) % len(elite_task_files),
        }

    def _select_elite_task_batch(
        self,
        elite_task_files,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        core_knowledge=None,
        operational_economy_context=None,
    ):
        if not elite_task_files:
            return [], {
                "system": "elite_task_selection",
                "elite_task_available": False,
            }
        rotated, priorities, survival_targets, domain_gaps, population_policy = (
            self._elite_priorities(
                elite_task_files,
                concept_counts=concept_counts,
                concept_states=concept_states,
                task_directory=task_directory,
                core_knowledge=core_knowledge,
                operational_economy_context=operational_economy_context,
            )
        )
        selected = [row["task_file"] for row in priorities[: self.batch_size]]
        last_selected = selected[-1]
        selected_rotated_index = rotated.index(last_selected)
        return selected, {
            "system": "elite_task_selection",
            "elite_task_available": True,
            "policy": "elite_tasks_only_operationalization_phase",
            "selected_elite_task_file": selected[0],
            "selected_elite_task_files": selected,
            "elite_task_count": len(elite_task_files),
            "normal_task_slots": 0,
            "prioritized_deficiencies": priorities[0].get(
                "deficiency_targets",
                [],
            ),
            "priority_reasons": priorities[0].get("priority_reasons", []),
            "survival_reappearance_targets": survival_targets,
            "survival_reappearance_matches": priorities[0].get(
                "survival_reappearance_matches",
                [],
            ),
            "domain_citizenship_gaps": domain_gaps,
            "domain_citizenship_matches": priorities[0].get(
                "domain_citizenship_matches",
                [],
            ),
            "training_economy_matches": priorities[0].get(
                "training_economy_matches",
                [],
            ),
            "validation_academy_matches": priorities[0].get(
                "validation_academy_matches",
                [],
            ),
            "capability_population_evolution_policy": population_policy,
            "elite_task_priorities": priorities,
            "next_elite_task_index_after_completion": (
                int(self.state.get("next_elite_task_index", 0))
                + selected_rotated_index
                + 1
            ) % len(elite_task_files),
        }

    def _prioritized_tasks(
        self,
        task_files,
        start,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        observed_task_ids=None,
        history=None,
        core_knowledge=None,
    ):
        rotated = [
            task_files[(start + offset) % len(task_files)]
            for offset in range(len(task_files))
        ]
        curriculum_report = self.curriculum_manager.rank_tasks(
            rotated,
            concept_counts=concept_counts,
            concept_states=concept_states,
            task_directory=task_directory,
            observed_task_ids=observed_task_ids,
            history=history,
            core_knowledge=core_knowledge,
        )
        return (
            curriculum_report["ranked_task_files"],
            curriculum_report,
        )

    def _rng_for_run(self):
        if self.random_seed is not None:
            seed = int(self.random_seed)
        else:
            seed = random.SystemRandom().randrange(1, 2 ** 63)
        return random.Random(seed), seed

    def _recent_task_ids(self):
        if self.task_cooldown_runs <= 0:
            return set()
        recent_runs = list(self.selection_memory.get("recent_runs", []))
        recent = recent_runs[-self.task_cooldown_runs:]
        return {
            str(task_file)
            for run in recent
            if isinstance(run, dict)
            for task_file in run.get("task_ids", [])
        }

    def _task_record(self, task_file):
        record = self.selection_memory.setdefault("tasks", {}).get(
            task_file,
            {},
        )
        return {
            "task_id": task_file,
            "times_selected": int(record.get("times_selected", 0)),
            "last_selected_at": record.get("last_selected_at"),
            "last_run_id": record.get("last_run_id"),
            "recent_selection_count": int(
                record.get("recent_selection_count", 0)
            ),
        }

    def _selection_weight(self, task_file, recent_task_ids, rng):
        record = self._task_record(task_file)
        unseen_boost = (
            self.UNSEEN_TASK_BOOST
            if record["times_selected"] <= 0
            else 1.0
        )
        cooldown_factor = (
            self.RECENT_TASK_PENALTY
            if task_file in recent_task_ids
            else 1.0
        )
        inverse_frequency_factor = 1.0 / (
            1.0 + record["times_selected"]
        )
        random_jitter = rng.uniform(0.85, 1.15)
        return (
            1.0
            * unseen_boost
            * cooldown_factor
            * inverse_frequency_factor
            * random_jitter
        )

    def _weighted_choice_without_replacement(
        self,
        candidates,
        weights,
        rng,
        count,
    ):
        remaining = list(zip(candidates, weights))
        selected = []
        while remaining and len(selected) < count:
            total_weight = sum(max(weight, 0.0) for _, weight in remaining)
            if total_weight <= 0.0:
                rng.shuffle(remaining)
                selected.extend(
                    task_file
                    for task_file, _ in remaining[:count - len(selected)]
                )
                break
            threshold = rng.random() * total_weight
            cumulative = 0.0
            selected_index = 0
            for index, (_, weight) in enumerate(remaining):
                cumulative += max(weight, 0.0)
                if cumulative >= threshold:
                    selected_index = index
                    break
            task_file, _ = remaining.pop(selected_index)
            selected.append(task_file)
        return selected

    def _selection_diversity_score(
        self,
        selected,
        previous_overlap,
        unseen_selected,
        average_frequency,
    ):
        if not selected:
            return 0.0
        unique_score = len(set(selected)) / len(selected)
        no_overlap_score = 1.0 - previous_overlap / len(selected)
        unseen_score = unseen_selected / len(selected)
        frequency_score = 1.0 / (1.0 + average_frequency)
        return round(
            max(
                0.0,
                min(
                    1.0,
                    unique_score * 0.35
                    + no_overlap_score * 0.30
                    + unseen_score * 0.20
                    + frequency_score * 0.15,
                ),
            ),
            4,
        )

    def _randomized_select(self, task_files, batch_size, selection_mode, rng):
        previous_batch = set(self.selection_memory.get("previous_batch", []))
        recent_task_ids = self._recent_task_ids()
        dataset_large = len(task_files) > batch_size * 5
        shuffled_tasks = list(task_files)
        rng.shuffle(shuffled_tasks)

        excluded = set(recent_task_ids)
        if dataset_large:
            excluded.update(previous_batch)
        available = [
            task_file
            for task_file in shuffled_tasks
            if task_file not in excluded
        ]
        cooldown_relaxed = False
        if len(available) < batch_size:
            cooldown_relaxed = True
            available = [
                task_file
                for task_file in shuffled_tasks
                if not (dataset_large and task_file in previous_batch)
            ]
        if len(available) < batch_size:
            available = list(shuffled_tasks)

        if selection_mode == "random":
            selected = available[:batch_size]
        else:
            weights = [
                self._selection_weight(task_file, recent_task_ids, rng)
                for task_file in available
            ]
            selected = self._weighted_choice_without_replacement(
                available,
                weights,
                rng,
                batch_size,
            )

        selected = list(dict.fromkeys(selected))[:batch_size]
        selected_set = set(selected)
        selected_records = [self._task_record(task_file) for task_file in selected]
        unseen_selected = sum(
            1 for record in selected_records if record["times_selected"] <= 0
        )
        average_frequency = (
            sum(record["times_selected"] for record in selected_records)
            / len(selected_records)
            if selected_records
            else 0.0
        )
        previous_overlap = len(selected_set & previous_batch)
        cooldown_filtered = sorted(
            task_file
            for task_file in shuffled_tasks
            if task_file in recent_task_ids and task_file not in selected_set
        )
        repeated_penalty = any(
            self._task_record(task_file)["times_selected"] > 0
            or task_file in recent_task_ids
            for task_file in selected
        )
        return selected, {
            "system": "training_selection_diversity",
            "total_available_tasks": len(task_files),
            "selected_tasks": list(selected),
            "selection_mode": selection_mode,
            "previous_batch_overlap_count": previous_overlap,
            "unseen_tasks_selected": unseen_selected,
            "cooldown_filtered_tasks": len(cooldown_filtered),
            "cooldown_filtered_task_ids": cooldown_filtered[:10],
            "average_task_selection_frequency": round(average_frequency, 4),
            "repeated_task_penalty_applied": repeated_penalty,
            "diversity_score": self._selection_diversity_score(
                selected,
                previous_overlap,
                unseen_selected,
                average_frequency,
            ),
            "cooldown_window_runs": self.task_cooldown_runs,
            "cooldown_relaxed": cooldown_relaxed,
            "dataset_large": dataset_large,
        }

    def _record_selection(self, selected, run_id):
        now = datetime.utcnow().isoformat()
        recent_runs = list(self.selection_memory.get("recent_runs", []))
        recent_task_ids = self._recent_task_ids()
        tasks = self.selection_memory.setdefault("tasks", {})
        for task_file in selected:
            record = self._task_record(task_file)
            record["times_selected"] += 1
            record["last_selected_at"] = now
            record["last_run_id"] = run_id
            record["recent_selection_count"] = (
                record["recent_selection_count"] + 1
                if task_file in recent_task_ids
                else 1
            )
            tasks[task_file] = record
        self.selection_memory["run_counter"] = int(
            self.selection_memory.get("run_counter", 0)
        ) + 1
        self.selection_memory["previous_batch"] = list(selected)
        self.selection_memory["recent_runs"] = [
            *recent_runs[-max(self.task_cooldown_runs * 2, 1):],
            {
                "run_id": run_id,
                "task_ids": list(selected),
                "selected_at": now,
            },
        ]
        self._persist_selection_memory()

    def select_batch(
        self,
        task_files,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        observed_task_ids=None,
        core_knowledge=None,
        selection_mode=None,
        random_seed=None,
        operational_economy_report=None,
    ):
        task_files = self._normalized_tasks(task_files)
        if not task_files:
            raise ValueError("at least one JSON training task is required")
        elite_task_files, normal_task_files = self._partition_elite_tasks(
            task_files,
            task_directory,
        )
        elite_only_policy_active = self._elite_operationalization_policy_active(
            elite_task_files,
            task_directory,
        )
        if operational_economy_report is None:
            operational_economy_report = self._load_operational_economy_report()
        operational_economy_context = self._operational_economy_context(
            operational_economy_report,
        )
        normal_selection_files = (
            []
            if elite_only_policy_active
            else normal_task_files
            if elite_task_files
            else task_files
        )
        selection_mode = self._selection_mode(
            selection_mode or self.selection_mode
        )
        original_random_seed = self.random_seed
        if random_seed is not None:
            self.random_seed = random_seed

        resumed = (
            selection_mode == "curriculum"
            and
            self._active_batch_is_valid(task_files)
            and
            self._active_batch_matches_elite_policy(
                task_files,
                elite_task_files,
                task_directory,
            )
            and (
                task_directory is None
                or
                self.state.get("curriculum_report", {})
                .get("training_diversity_report", {})
                .get("knowledge_expansion_score", 0.0)
                > 0.0
            )
        )
        run_id = f"selection-{uuid.uuid4()}"
        rng, effective_seed = self._rng_for_run()
        selection_report = dict(
            self.state.get("selection_diversity_report", {})
        )
        elite_selection_report = dict(
            self.state.get("elite_selection_report", {})
        )
        if resumed:
            selected = list(self.state["active_batch"])
            prioritized_concepts = list(
                self.state.get("prioritized_concepts", [])
            )
            selected_concepts = list(
                self.state.get("selected_concepts", [])
            )
            curriculum_report = dict(
                self.state.get("curriculum_report", {})
            )
            elite_selection_report = dict(
                self.state.get("elite_selection_report", {})
            )
        else:
            start = int(self.state.get("next_task_index", 0))
            if normal_selection_files:
                start %= len(normal_selection_files)
            else:
                start = 0
            if elite_only_policy_active:
                elite_batch, elite_selection_report = self._select_elite_task_batch(
                    elite_task_files,
                    concept_counts=concept_counts,
                    concept_states=concept_states,
                    task_directory=task_directory,
                    core_knowledge=core_knowledge,
                    operational_economy_context=operational_economy_context,
                )
                elite_task = elite_batch[0] if elite_batch else None
            else:
                elite_task, elite_selection_report = self._select_elite_task(
                    elite_task_files,
                    concept_counts=concept_counts,
                    concept_states=concept_states,
                    task_directory=task_directory,
                    core_knowledge=core_knowledge,
                    operational_economy_context=operational_economy_context,
                )
                elite_batch = [elite_task] if elite_task else []
            normal_batch_size = min(
                0
                if elite_only_policy_active
                else self.batch_size - (1 if elite_task else 0),
                len(normal_selection_files),
            )
            if normal_selection_files:
                ranked_tasks, curriculum_report = self._prioritized_tasks(
                    normal_selection_files,
                    start,
                    concept_counts=concept_counts,
                    concept_states=concept_states,
                    task_directory=task_directory,
                    observed_task_ids=observed_task_ids,
                    history=self.state.get("history", []),
                    core_knowledge=core_knowledge,
                )
            else:
                ranked_tasks = []
                curriculum_report = {
                    "system": "training_curriculum_manager",
                    "training_mode": "elite_only_batch",
                    "prioritized_concepts": [],
                    "ranked_task_files": [],
                    "task_priorities": [],
                    "training_diversity_report": {},
                }
            prioritized_concepts = curriculum_report[
                "prioritized_concepts"
            ]
            if normal_batch_size <= 0:
                selected = []
                selection_report = {
                    "system": "training_selection_diversity",
                    "total_available_tasks": len(normal_selection_files),
                    "selected_tasks": [],
                    "selection_mode": selection_mode,
                    "random_seed": effective_seed,
                    "run_id": run_id,
                    "previous_batch_overlap_count": 0,
                    "unseen_tasks_selected": 0,
                    "cooldown_filtered_tasks": 0,
                    "cooldown_filtered_task_ids": [],
                    "average_task_selection_frequency": 0.0,
                    "repeated_task_penalty_applied": False,
                    "diversity_score": 0.0,
                    "cooldown_window_runs": self.task_cooldown_runs,
                    "cooldown_relaxed": False,
                    "dataset_large": False,
                }
            elif selection_mode == "curriculum":
                selected = self.curriculum_manager.select_batch_tasks(
                    curriculum_report,
                    normal_batch_size,
                )
                previous_batch = set(
                    self.selection_memory.get("previous_batch", [])
                )
                selected_records = [
                    self._task_record(task_file)
                    for task_file in selected
                ]
                unseen_selected = sum(
                    1
                    for record in selected_records
                    if record["times_selected"] <= 0
                )
                average_frequency = (
                    sum(
                        record["times_selected"]
                        for record in selected_records
                    )
                    / len(selected_records)
                    if selected_records
                    else 0.0
                )
                previous_overlap = len(set(selected) & previous_batch)
                selection_report = {
                    "system": "training_selection_diversity",
                    "total_available_tasks": len(task_files),
                    "selected_tasks": list(selected),
                    "selection_mode": selection_mode,
                    "random_seed": effective_seed,
                    "run_id": run_id,
                    "previous_batch_overlap_count": previous_overlap,
                    "unseen_tasks_selected": unseen_selected,
                    "cooldown_filtered_tasks": 0,
                    "cooldown_filtered_task_ids": [],
                    "average_task_selection_frequency": round(
                        average_frequency,
                        4,
                    ),
                    "repeated_task_penalty_applied": False,
                    "diversity_score": self._selection_diversity_score(
                        selected,
                        previous_overlap,
                        unseen_selected,
                        average_frequency,
                    ),
                    "cooldown_window_runs": self.task_cooldown_runs,
                    "cooldown_relaxed": False,
                    "dataset_large": len(task_files)
                    > normal_batch_size * 5,
                }
            else:
                selected, selection_report = self._randomized_select(
                    list(ranked_tasks or task_files),
                    normal_batch_size,
                    selection_mode,
                    rng,
                )
                selection_report["random_seed"] = effective_seed
                selection_report["run_id"] = run_id
            if elite_only_policy_active:
                selected = list(elite_batch)
            elif elite_task:
                selected = [elite_task, *[
                    task_file
                    for task_file in selected
                    if task_file != elite_task
                ]]
            if elite_only_policy_active:
                previous_batch = set(
                    self.selection_memory.get("previous_batch", [])
                )
                selected_records = [
                    self._task_record(task_file)
                    for task_file in selected
                ]
                unseen_selected = sum(
                    1
                    for record in selected_records
                    if record["times_selected"] <= 0
                )
                average_frequency = (
                    sum(
                        record["times_selected"]
                        for record in selected_records
                    )
                    / len(selected_records)
                    if selected_records
                    else 0.0
                )
                previous_overlap = len(set(selected) & previous_batch)
                selection_report = {
                    "system": "training_selection_diversity",
                    "total_available_tasks": len(elite_task_files),
                    "selected_tasks": list(selected),
                    "selection_mode": "elite_only_operationalization",
                    "random_seed": effective_seed,
                    "run_id": run_id,
                    "previous_batch_overlap_count": previous_overlap,
                    "unseen_tasks_selected": unseen_selected,
                    "cooldown_filtered_tasks": 0,
                    "cooldown_filtered_task_ids": [],
                    "average_task_selection_frequency": round(
                        average_frequency,
                        4,
                    ),
                    "repeated_task_penalty_applied": previous_overlap > 0,
                    "diversity_score": self._selection_diversity_score(
                        selected,
                        previous_overlap,
                        unseen_selected,
                        average_frequency,
                    ),
                    "cooldown_window_runs": self.task_cooldown_runs,
                    "cooldown_relaxed": False,
                    "dataset_large": len(elite_task_files) > self.batch_size * 5,
                    "elite_only_policy_active": True,
                }
            selected_concepts = sorted({
                concept
                for report in curriculum_report.get("task_priorities", [])
                if report.get("task_file") in selected
                for concept in report.get("target_concepts", [])
            })
            if elite_task:
                elite_metadata = self._task_metadata(
                    elite_task,
                    task_directory,
                )
                selected_concepts = sorted(set(selected_concepts) | {
                    str(concept)
                    for concept in elite_metadata.get("target_concepts", [])
                    if concept
                })
            self.state["active_batch"] = selected
            self.state["prioritized_concepts"] = prioritized_concepts
            self.state["selected_concepts"] = selected_concepts
            self.state["curriculum_report"] = curriculum_report
            self.state["selection_diversity_report"] = selection_report
            self.state["elite_selection_report"] = elite_selection_report
            self.state["training_economy_alignment_report"] = (
                self._training_economy_alignment_report(
                    selected,
                    elite_selection_report,
                    operational_economy_context,
                )
            )
            self.state["pending_next_task_index"] = (
                (start + len([
                    task_file
                    for task_file in selected
                    if task_file not in set(elite_task_files)
                ])) % len(normal_selection_files)
                if normal_selection_files
                else 0
            )
            self.state["pending_next_elite_task_index"] = (
                elite_selection_report.get(
                    "next_elite_task_index_after_completion"
                )
            )
            self._persist()
            self._record_selection(selected, run_id)

        if random_seed is not None:
            self.random_seed = original_random_seed

        training_diversity_report = dict(
            curriculum_report.get("training_diversity_report")
            or self.state.get("curriculum_report", {}).get(
                "training_diversity_report",
                {},
            )
            or {}
        )
        if selection_report:
            training_diversity_report["selection_diversity_score"] = (
                selection_report.get("diversity_score", 0.0)
            )
        training_economy_alignment_report = dict(
            self.state.get("training_economy_alignment_report", {})
        )
        if not training_economy_alignment_report:
            training_economy_alignment_report = (
                self._training_economy_alignment_report(
                    self.state.get("active_batch", []),
                    elite_selection_report,
                    operational_economy_context,
                )
            )
        if training_economy_alignment_report:
            training_diversity_report.update({
                "training_economy_alignment_state": (
                    training_economy_alignment_report.get("alignment_state")
                ),
                "training_economy_alignment_score": (
                    training_economy_alignment_report.get(
                        "training_economy_alignment_score"
                    )
                ),
                "training_economy_match_count": (
                    training_economy_alignment_report.get("alignment_match_count")
                ),
                "training_economy_bottleneck": (
                    training_economy_alignment_report.get(
                        "operational_economy_bottleneck"
                    )
                ),
                "grounding_economy_alignment": (
                    training_economy_alignment_report.get(
                        "grounding_economy_alignment"
                    )
                ),
            })
        elite_curriculum_report = {}
        if elite_task_files:
            try:
                elite_curriculum_report = validate_elite_curriculum(
                    task_directory or "data/training",
                )
            except (OSError, TypeError, ValueError):
                elite_curriculum_report = {}
        if elite_curriculum_report:
            training_diversity_report.update({
                "elite_curriculum_health": elite_curriculum_report.get(
                    "elite_curriculum_health",
                ),
                "elite_task_difficulty": elite_curriculum_report.get(
                    "elite_task_difficulty",
                ),
                "capability_graduation_coverage": elite_curriculum_report.get(
                    "capability_graduation_coverage",
                ),
                "domain_expansion_coverage": elite_curriculum_report.get(
                    "domain_expansion_coverage",
                ),
                "composite_capability_coverage": elite_curriculum_report.get(
                    "composite_capability_coverage",
                ),
                "adaptive_reuse_coverage": elite_curriculum_report.get(
                    "adaptive_reuse_coverage",
                ),
                "operationalization_coverage": elite_curriculum_report.get(
                    "operationalization_coverage",
                ),
                "curriculum_diversity_score": elite_curriculum_report.get(
                    "curriculum_diversity_score",
                ),
                "elite_task_utilization": elite_curriculum_report.get(
                    "elite_task_utilization",
                ),
                "training_value_score": elite_curriculum_report.get(
                    "training_value_score",
                ),
            })

        return {
            "system": "training_assistant",
            "training_mode":
            (
                selection_mode
                if selection_mode != "curriculum"
                else curriculum_report.get(
                    "training_mode",
                    "bounded_round_robin_batch",
                )
            ),
            "prioritized_concepts": prioritized_concepts,
            "selected_concepts": selected_concepts,
            "curriculum_report": curriculum_report,
            "elite_curriculum_report": elite_curriculum_report,
            "training_economy_alignment_report": training_economy_alignment_report,
            "training_diversity_report": training_diversity_report,
            "selection_diversity_report": selection_report,
            "elite_selection_report": elite_selection_report,
            "batch_size": self.batch_size,
            "available_task_count": len(task_files),
            "available_elite_task_count": len(elite_task_files),
            "available_normal_task_count": len(normal_task_files),
            "elite_only_policy_active": elite_only_policy_active,
            "selected_task_count": len(selected),
            "selected_task_files": selected,
            "selected_elite_task_files": [
                task_file
                for task_file in selected
                if task_file in set(elite_task_files)
            ],
            "resumed_active_batch": resumed,
            "completed_cycles": self.state.get("completed_cycles", 0),
            "next_task_index_after_completion":
            self.state.get("pending_next_task_index"),
        }

    def complete_cycle(
        self,
        successful_tasks=0,
        failed_tasks=0,
        incomplete_tasks=0,
    ):
        active_batch = list(self.state.get("active_batch", []))
        if not active_batch:
            return {
                **self.report(),
                "cycle_completion_state": "NO_ACTIVE_BATCH",
            }

        completed_cycles = int(self.state.get("completed_cycles", 0)) + 1
        self.state["next_task_index"] = int(
            self.state.get("pending_next_task_index", 0)
        )
        pending_elite_index = self.state.get("pending_next_elite_task_index")
        if pending_elite_index is not None:
            self.state["next_elite_task_index"] = int(pending_elite_index)
        self.state["completed_cycles"] = completed_cycles
        self.state["active_batch"] = []
        self.state["pending_next_task_index"] = None
        self.state["pending_next_elite_task_index"] = None
        self.state["prioritized_concepts"] = []
        selected_concepts = list(self.state.get("selected_concepts", []))
        self.state["selected_concepts"] = []
        self.state["curriculum_report"] = {}
        self.state["selection_diversity_report"] = {}
        self.state["elite_selection_report"] = {}
        self.state["training_economy_alignment_report"] = {}
        self.state["history"] = [
            *list(self.state.get("history", []))[-31:],
            {
                "cycle": completed_cycles,
                "task_files": active_batch,
                "concepts": selected_concepts,
                "successful_tasks": int(successful_tasks),
                "failed_tasks": int(failed_tasks),
                "incomplete_tasks": int(incomplete_tasks),
                "timestamp": datetime.utcnow().isoformat(),
            },
        ]
        self._persist()
        return {
            **self.report(),
            "cycle_completion_state": "TRAINING_BATCH_COMPLETED",
            "completed_task_files": active_batch,
        }

    def report(self):
        return {
            "system": "training_assistant",
            "training_mode": "bounded_round_robin_batch",
            "batch_size": self.batch_size,
            "next_task_index": self.state.get("next_task_index", 0),
            "next_elite_task_index": self.state.get(
                "next_elite_task_index",
                0,
            ),
            "completed_cycles": self.state.get("completed_cycles", 0),
            "active_batch": list(self.state.get("active_batch", [])),
            "prioritized_concepts":
            list(self.state.get("prioritized_concepts", [])),
            "selected_concepts":
            list(self.state.get("selected_concepts", [])),
            "selection_diversity_report": dict(
                self.state.get("selection_diversity_report", {})
            ),
            "elite_selection_report": dict(
                self.state.get("elite_selection_report", {})
            ),
            "selection_memory_path": str(self.selection_memory_path),
            "selection_mode": self.selection_mode,
            "survival_store_path": str(self.survival_store_path),
            "history_size": len(self.state.get("history", [])),
            "state_path": str(self.state_path),
        }


__all__ = [
    "TrainingAssistant",
]
