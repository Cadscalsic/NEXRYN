import json
from collections import Counter
from pathlib import Path


TRAINING_DIRECTORY = Path("data/training")
TARGET_MINIMUMS = {
    "replication": 10,
    "topological_reasoning": 20,
    "topological_change": 20,
    "density_modulation": 20,
    "propagation": 10,
    "symbolic_remapping": 10,
    "object_counting": 15,
    "spatial_reasoning": 15,
    "pattern_completion": 15,
    "color_mapping": 15,
    "color_transformation": 15,
    "rotation": 15,
    "reflection": 15,
    "scaling": 15,
    "inside_outside": 15,
    "occlusion": 15,
    "masking": 15,
    "path_finding": 15,
    "gravity_simulation": 15,
    "noise_removal": 15,
}


def curriculum_coverage(training_directory=TRAINING_DIRECTORY):
    coverage = Counter()
    curriculum_counts = Counter()
    task_count = 0
    for path in sorted(Path(training_directory).glob("*.json")):
        task = json.loads(path.read_text(encoding="utf-8"))
        metadata = task.get("nexryn_metadata")
        if not isinstance(metadata, dict):
            continue
        task_count += 1
        curriculum_counts[metadata.get("curriculum", "unknown")] += 1
        coverage.update(metadata.get("target_concepts", []))
    return {
        "task_count": task_count,
        "curriculum_counts": dict(sorted(curriculum_counts.items())),
        "targeted_concept_coverage": dict(sorted(coverage.items())),
        "coverage_gaps": {
            concept: max(minimum - coverage.get(concept, 0), 0)
            for concept, minimum in TARGET_MINIMUMS.items()
        },
        "metadata_is_targeting_not_runtime_observation": True,
    }


def main():
    print(json.dumps(curriculum_coverage(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
