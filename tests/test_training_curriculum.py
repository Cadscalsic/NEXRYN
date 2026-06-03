from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path

from core.loader import ARCJSONLoader
from tools.audit_training_curriculum import curriculum_coverage


TRAINING_DIRECTORY = Path("data/training")
GENERATED_TASKS = [
    TRAINING_DIRECTORY / f"task_{sequence:03d}.json"
    for sequence in range(7, 37)
]
TARGETED_TASKS = [
    TRAINING_DIRECTORY / f"task_{sequence:03d}.json"
    for sequence in range(37, 87)
]
SCARCITY_TASKS = [
    TRAINING_DIRECTORY / f"task_{sequence:03d}.json"
    for sequence in range(87, 102)
]


def test_phase_7_prelude_curriculum_contains_30_valid_arc_tasks():
    assert all(path.exists() for path in GENERATED_TASKS)
    payloads = set()

    for path in GENERATED_TASKS:
        task = json.loads(path.read_text(encoding="utf-8"))
        metadata = task["nexryn_metadata"]
        assert metadata["curriculum"] == "phase_7_prelude_batch_01"
        assert metadata["target_concepts"]
        assert metadata["probe_kind"] in {
            "direct",
            "matched_boundary",
            "composite",
        }
        assert len(task["train"]) == 2
        assert len(task["test"]) == 1
        assert all(
            example["input"] != example["output"]
            for example in task["train"]
        )
        payloads.add(json.dumps({
            "train": task["train"],
            "test": task["test"],
        }, sort_keys=True))
        with redirect_stdout(StringIO()):
            assert ARCJSONLoader(str(path)).load() is True

    assert len(payloads) == 30


def test_training_directory_exposes_original_and_generated_tasks():
    task_paths = sorted(TRAINING_DIRECTORY.glob("*.json"))

    assert len(task_paths) == 101


def test_phase_7_targeted_curriculum_covers_rare_concepts():
    assert all(path.exists() for path in TARGETED_TASKS)
    payloads = set()
    concept_counts = {}

    for path in TARGETED_TASKS:
        task = json.loads(path.read_text(encoding="utf-8"))
        metadata = task["nexryn_metadata"]
        assert metadata["curriculum"] == "phase_7_targeted_batch_02"
        assert metadata["target_concepts"]
        assert metadata["probe_kind"] in {
            "targeted_direct",
            "targeted_topology",
            "targeted_density",
            "targeted_composite",
            "causal_sequence",
        }
        assert len(task["train"]) == 2
        assert len(task["test"]) == 1
        assert all(
            example["input"] != example["output"]
            for example in task["train"]
        )
        payloads.add(json.dumps({
            "train": task["train"],
            "test": task["test"],
        }, sort_keys=True))
        for concept in metadata["target_concepts"]:
            concept_counts[concept] = concept_counts.get(concept, 0) + 1
        with redirect_stdout(StringIO()):
            assert ARCJSONLoader(str(path)).load() is True

    assert len(payloads) == 50
    assert concept_counts["replication"] >= 10
    assert concept_counts["topological_reasoning"] >= 10
    assert concept_counts["topological_change"] >= 10
    assert concept_counts["density_modulation"] >= 10
    assert concept_counts["propagation"] >= 10
    assert concept_counts["symbolic_remapping"] >= 10


def test_training_curriculum_audit_reports_no_targeting_gaps():
    report = curriculum_coverage()

    assert report["curriculum_counts"]["phase_7_targeted_batch_02"] == 50
    assert report["curriculum_counts"]["phase_7_scarcity_batch_03"] == 15
    assert set(report["coverage_gaps"].values()) == {0}
    assert report["metadata_is_targeting_not_runtime_observation"] is True


def test_phase_7_scarcity_curriculum_closes_runtime_target_gaps():
    assert all(path.exists() for path in SCARCITY_TASKS)
    report = curriculum_coverage()

    assert report["targeted_concept_coverage"]["topological_change"] >= 20
    assert report["targeted_concept_coverage"]["topological_reasoning"] >= 20
    assert report["targeted_concept_coverage"]["density_modulation"] >= 20
