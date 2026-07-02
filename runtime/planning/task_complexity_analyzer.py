# ============================================
# NEXRYN TASK COMPLEXITY ANALYZER
# ============================================

from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass
class TaskProfile:

    task_id: str

    task_family: str

    target_concepts: list

    suspected_concepts: list

    required_capabilities: list

    complexity: str

    object_count: int

    estimated_concepts: int

    transformation_count: int

    spatial_complexity: float

    process_complexity: float

    temporal_complexity: float

    uncertainty: float

    historical_similarity: float

    estimated_cost: float


@dataclass
class TaskComplexityThresholds:

    low_object_count_max: int = 3

    low_transformation_count_max: int = 2

    low_process_complexity_max: float = 0.30

    medium_object_count_max: int = 8

    medium_transformation_count_max: int = 5

    high_process_complexity_min: float = 0.60

    high_temporal_complexity_min: float = 0.0

    high_dependency_depth_min: int = 6


class TaskComplexityAnalyzer:

    def __init__(self, thresholds=None):

        self.thresholds = thresholds or TaskComplexityThresholds()
        self.last_task_signature = None

    def analyze(self, task):

        task_context = task if isinstance(task, dict) else {}
        input_grid = self._extract_grid(
            task_context.get("input_grid")
            or self._nested_get(task_context, "train_example", "input")
            or self._nested_get(task_context, "input")
        )
        output_grid = self._extract_grid(
            task_context.get("output_grid")
            or self._nested_get(task_context, "train_example", "output")
            or self._nested_get(task_context, "output")
        )

        self.last_task_signature = self.task_signature(task_context)

        input_colors = self._colors(input_grid)
        output_colors = self._colors(output_grid)
        all_colors = input_colors | output_colors

        object_count = self._estimate_object_count(input_grid)
        transformation_count = self._estimate_transformations(
            input_grid,
            output_grid,
            input_colors,
            output_colors,
        )
        spatial_complexity = self._estimate_spatial_complexity(
            input_grid,
            output_grid,
        )
        process_complexity = self._estimate_process_complexity(
            task_context,
            transformation_count,
            object_count,
            len(all_colors),
            spatial_complexity,
        )
        temporal_complexity = self._estimate_temporal_complexity(
            task_context
        )
        historical_similarity = self._historical_similarity(task_context)
        uncertainty = self._estimate_uncertainty(
            object_count,
            transformation_count,
            process_complexity,
            historical_similarity,
        )
        dependency_depth = self._estimate_dependency_depth(
            object_count,
            transformation_count,
            process_complexity,
            temporal_complexity,
        )

        estimated_concepts = max(
            len(all_colors) + object_count + transformation_count,
            transformation_count,
        )

        estimated_cost = self._clamp(
            object_count / 12.0 * 0.24
            + transformation_count / 8.0 * 0.24
            + spatial_complexity * 0.18
            + process_complexity * 0.22
            + temporal_complexity * 0.06
            + uncertainty * 0.06
        )

        complexity = self._classify(
            object_count,
            transformation_count,
            process_complexity,
            temporal_complexity,
            dependency_depth,
        )

        task_id = str(
            task_context.get("task_id")
            or task_context.get("task_path")
            or task_context.get("task_file")
            or self.last_task_signature
        )
        task_family = str(
            task_context.get("task_family")
            or task_context.get("concept_family")
            or ""
        )
        target_concepts = self._as_list(
            task_context.get("target_concepts")
            or task_context.get("concepts")
        )
        target_concepts = list(dict.fromkeys([
            *target_concepts,
            *self._concepts_from_task_identity(task_id, task_family),
        ]))
        suspected_concepts = self._as_list(
            task_context.get("suspected_concepts")
            or task_context.get("priority_concepts")
        )
        suspected_concepts = list(dict.fromkeys([
            *suspected_concepts,
            *self._concepts_from_task_identity(task_id, task_family),
        ]))
        required_capabilities = self._as_list(
            task_context.get("required_capabilities")
        )
        if any(
            concept in target_concepts
            for concept in (
                "object_counting",
                "cardinality",
                "numerical_reasoning",
                "set_reasoning",
            )
        ):
            required_capabilities = list(dict.fromkeys([
                *required_capabilities,
                "object_tracking",
                "counting",
                "dependency_reasoning",
            ]))
        if any(
            concept in target_concepts or concept in suspected_concepts
            for concept in (
                "gravity_simulation",
                "gravity",
                "falling",
                "support",
                "physics",
                "collision",
            )
        ):
            required_capabilities = list(dict.fromkeys([
                *required_capabilities,
                "gravity_reasoning",
                "world_model",
                "dependency_reasoning",
                "context_discovery",
            ]))

        return TaskProfile(
            task_id=str(
                task_id
            ),
            task_family=task_family,
            target_concepts=target_concepts,
            suspected_concepts=suspected_concepts,
            required_capabilities=required_capabilities,
            complexity=complexity,
            object_count=int(object_count),
            estimated_concepts=int(estimated_concepts),
            transformation_count=int(transformation_count),
            spatial_complexity=round(spatial_complexity, 4),
            process_complexity=round(process_complexity, 4),
            temporal_complexity=round(temporal_complexity, 4),
            uncertainty=round(uncertainty, 4),
            historical_similarity=round(historical_similarity, 4),
            estimated_cost=round(estimated_cost, 4),
        )

    def build_report(self, task_profile, task_signature=None):

        return {
            "task_signature":
            task_signature or self.last_task_signature,
            "complexity":
            task_profile.complexity,
            "object_count":
            task_profile.object_count,
            "transformation_count":
            task_profile.transformation_count,
            "spatial_complexity":
            task_profile.spatial_complexity,
            "process_complexity":
            task_profile.process_complexity,
            "temporal_complexity":
            task_profile.temporal_complexity,
            "estimated_cost":
            task_profile.estimated_cost,
        }

    def task_signature(self, task):

        stable_task = self._stable_value(task)
        encoded = json.dumps(
            stable_task,
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]

    def _as_list(self, value):

        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, (tuple, set)):
            return list(value)

        return [value]

    def _concepts_from_task_identity(self, task_id, task_family):

        signal_text = f"{task_id} {task_family}".lower()
        concepts = []
        if any(
            marker in signal_text
            for marker in (
                "object_counting",
                "object counting",
                "counting",
                "count_by_color",
                "count by color",
                "cardinality",
                "quantity",
                "numerical",
                "number",
                "set_reasoning",
                "set reasoning",
            )
        ):
            concepts.extend([
                "object_counting",
                "cardinality",
                "quantity_preservation",
                "quantity_transformation",
                "numerical_reasoning",
                "set_reasoning",
            ])
        if any(
            marker in signal_text
            for marker in (
                "gravity_simulation",
                "gravity simulation",
                "gravity",
                "falling",
                "support",
                "unsupported",
                "physics",
                "collision",
            )
        ):
            concepts.extend([
                "gravity_simulation",
                "gravity",
                "falling",
                "support",
                "physics",
                "collision",
                "downward_motion",
                "state_transition",
            ])
        return list(dict.fromkeys(concepts))

    def _classify(
        self,
        object_count,
        transformation_count,
        process_complexity,
        temporal_complexity,
        dependency_depth,
    ):

        thresholds = self.thresholds

        if (
            process_complexity >= thresholds.high_process_complexity_min
            or temporal_complexity > thresholds.high_temporal_complexity_min
            or dependency_depth >= thresholds.high_dependency_depth_min
        ):
            return "high"

        if (
            object_count <= thresholds.low_object_count_max
            and transformation_count
            <= thresholds.low_transformation_count_max
            and process_complexity < thresholds.low_process_complexity_max
        ):
            return "low"

        if (
            object_count <= thresholds.medium_object_count_max
            and transformation_count
            <= thresholds.medium_transformation_count_max
        ):
            return "medium"

        return "high"

    def _estimate_transformations(
        self,
        input_grid,
        output_grid,
        input_colors,
        output_colors,
    ):

        count = 0

        if input_grid and output_grid:
            if self._shape(input_grid) != self._shape(output_grid):
                count += 1
            else:
                changed = 0
                total = 0
                for row_index, row in enumerate(input_grid):
                    for col_index, value in enumerate(row):
                        total += 1
                        if output_grid[row_index][col_index] != value:
                            changed += 1
                if changed:
                    count += 1
                if total and changed / total > 0.25:
                    count += 1

        if input_colors != output_colors:
            count += 1

        return count

    def _estimate_object_count(self, grid):

        if not grid:
            return 0

        background = self._background_color(grid)
        visited = set()
        count = 0

        for row_index, row in enumerate(grid):
            for col_index, value in enumerate(row):
                position = (row_index, col_index)
                if value == background or position in visited:
                    continue
                count += 1
                self._walk_component(
                    grid,
                    row_index,
                    col_index,
                    value,
                    visited,
                )

        return count

    def _walk_component(
        self,
        grid,
        row_index,
        col_index,
        color,
        visited,
    ):

        stack = [(row_index, col_index)]
        max_row = len(grid)

        while stack:
            row, col = stack.pop()
            if (row, col) in visited:
                continue
            if row < 0 or row >= max_row:
                continue
            if col < 0 or col >= len(grid[row]):
                continue
            if grid[row][col] != color:
                continue
            visited.add((row, col))
            stack.extend([
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ])

    def _estimate_spatial_complexity(self, input_grid, output_grid):

        input_shape = self._shape(input_grid)
        output_shape = self._shape(output_grid)
        cells = max(
            (input_shape[0] * input_shape[1]) if input_shape else 0,
            (output_shape[0] * output_shape[1]) if output_shape else 0,
            1,
        )
        shape_delta = 1.0 if input_shape != output_shape else 0.0
        density = self._density(input_grid)
        return self._clamp((cells / 900.0) + shape_delta * 0.35 + density * 0.25)

    def _estimate_process_complexity(
        self,
        task_context,
        transformation_count,
        object_count,
        color_count,
        spatial_complexity,
    ):

        indicator_text = json.dumps(
            self._stable_value(task_context),
            sort_keys=True,
            default=str,
        ).lower()
        indicators = [
            "process",
            "sequence",
            "temporal",
            "dependency",
            "recursive",
            "chain",
            "symmetry",
            "repeat",
        ]
        indicator_score = sum(
            1 for indicator in indicators if indicator in indicator_text
        ) / float(len(indicators))

        return self._clamp(
            transformation_count / 12.0
            + object_count / 30.0
            + color_count / 40.0
            + spatial_complexity * 0.15
            + indicator_score * 0.30
        )

    def _estimate_temporal_complexity(self, task_context):

        indicator_text = json.dumps(
            self._stable_value(task_context),
            sort_keys=True,
            default=str,
        ).lower()
        indicators = ["temporal", "time", "sequence", "step", "trajectory"]
        return self._clamp(
            sum(1 for indicator in indicators if indicator in indicator_text)
            / float(len(indicators))
        )

    def _estimate_dependency_depth(
        self,
        object_count,
        transformation_count,
        process_complexity,
        temporal_complexity,
    ):

        return int(
            round(
                object_count * 0.35
                + transformation_count * 0.75
                + process_complexity * 5.0
                + temporal_complexity * 3.0
            )
        )

    def _estimate_uncertainty(
        self,
        object_count,
        transformation_count,
        process_complexity,
        historical_similarity,
    ):

        return self._clamp(
            object_count / 20.0
            + transformation_count / 10.0
            + process_complexity * 0.35
            + (1.0 - historical_similarity) * 0.20
        )

    def _historical_similarity(self, task_context):

        candidates = task_context.get("arc_replication_candidates", [])
        if not isinstance(candidates, list) or not candidates:
            return 0.0

        scores = []
        for candidate in candidates:
            if isinstance(candidate, dict):
                for key in ("similarity", "score", "confidence"):
                    value = candidate.get(key)
                    if isinstance(value, (int, float)):
                        scores.append(self._clamp(value))

        if not scores:
            return 0.0

        return max(scores)

    def _extract_grid(self, value):

        if value is None:
            return []

        if hasattr(value, "grid"):
            value = value.grid

        if hasattr(value, "tolist"):
            value = value.tolist()

        if not isinstance(value, list):
            return []

        return [
            list(row)
            for row in value
            if isinstance(row, (list, tuple))
        ]

    def _colors(self, grid):

        return {
            value
            for row in grid
            for value in row
        }

    def _background_color(self, grid):

        counts = {}
        for row in grid:
            for value in row:
                counts[value] = counts.get(value, 0) + 1

        if not counts:
            return 0

        if 0 in counts:
            return 0

        return max(counts, key=counts.get)

    def _shape(self, grid):

        if not grid:
            return None

        return (len(grid), max(len(row) for row in grid))

    def _density(self, grid):

        if not grid:
            return 0.0

        background = self._background_color(grid)
        total = sum(len(row) for row in grid)
        if total == 0:
            return 0.0

        active = sum(
            1
            for row in grid
            for value in row
            if value != background
        )
        return active / float(total)

    def _nested_get(self, mapping, *keys):

        current = mapping
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def _stable_value(self, value):

        if isinstance(value, dict):
            return {
                key: self._stable_value(value[key])
                for key in sorted(value.keys(), key=str)
                if key not in {"loader", "pattern_engine", "rule_engine"}
            }

        if isinstance(value, (list, tuple)):
            return [self._stable_value(item) for item in value]

        if hasattr(value, "grid"):
            return self._stable_value(value.grid)

        if hasattr(value, "tolist"):
            return value.tolist()

        if isinstance(value, (str, int, float, bool)) or value is None:
            return value

        return str(value)

    @staticmethod
    def _clamp(value):

        return max(0.0, min(1.0, float(value)))


task_complexity_analyzer = TaskComplexityAnalyzer()
