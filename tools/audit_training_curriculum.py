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
