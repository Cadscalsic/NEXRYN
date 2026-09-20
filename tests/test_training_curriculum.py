from contextlib import redirect_stdout
from collections import Counter
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
ARC_CONCEPT_FAMILIES = [
    "object_counting",
    "spatial_reasoning",
    "color_mapping",
    "rotation_reflection",
    "pattern_completion",
    "inside_outside",
    "noise_removal",
    "occlusion_masking",
    "scaling",
    "path_finding",
    "gravity_simulation",
]
ARC_CONCEPT_TASKS = [
    TRAINING_DIRECTORY / f"arc_concept_{family}_{sequence:02d}.json"
    for family in ARC_CONCEPT_FAMILIES
    for sequence in range(1, 16)
]
ELITE_COGNITIVE_TASKS = [
    TRAINING_DIRECTORY / f"elite_cognitive_task_{sequence:02d}.json"
    for sequence in range(1, 21)
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

    assert len(task_paths) >= len(ARC_CONCEPT_TASKS)
    assert all(path.exists() for path in ARC_CONCEPT_TASKS)


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


def test_elite_cognitive_curriculum_contains_20_operational_tasks():
    assert all(path.exists() for path in ELITE_COGNITIVE_TASKS)

    tiers = Counter()
    covered_domains = set()
    for path in ELITE_COGNITIVE_TASKS:
        task = json.loads(path.read_text(encoding="utf-8"))
        metadata = task["nexryn_metadata"]

        assert metadata["curriculum"] == "nexryn_elite_training_curriculum_v1"
        assert metadata["curriculum_version"] == "Elite Training Curriculum V1"
        assert metadata["elite_cognitive_task"] is True
        assert metadata["operationalization_phase_curriculum"] is True
        assert metadata["elite_task_difficulty"] == "very_high"
        assert metadata["multiple_valid_solution_strategies"] is True
        assert metadata["failure_is_training_signal"] is True
        assert len(metadata["target_concepts"]) >= 3
        assert 3 <= len(metadata["target_domains"]) <= 6
        assert metadata["multi_domain_reasoning"] is True
        assert metadata["multi_step_reasoning"] is True
        assert metadata["program_composition_required"] is True
        assert metadata["operational_capability_composition_required"] is True
        assert metadata["composite_capabilities"]
        assert metadata["adaptive_reuse_opportunities"]
        assert metadata["capability_graduation_targets"]
        assert metadata["domain_expansion_targets"]
        assert len(metadata["required_operational_capabilities"]) >= 6
        assert len(metadata["deficiency_targets"]) >= 7
        assert len(task["train"]) == 2
        assert len(task["test"]) == 1
        assert all(
            example["input"] != example["output"]
            for example in task["train"]
        )
        tiers[metadata["curriculum_tier"]] += 1
        covered_domains.update(metadata["target_domains"])
        with redirect_stdout(StringIO()):
            assert ARCJSONLoader(str(path)).load() is True

    assert tiers == {
        "Tier 1": 5,
        "Tier 2": 5,
        "Tier 3": 5,
        "Tier 4": 5,
    }
    assert covered_domains == {
        "Color",
        "Transformation",
        "Topology",
        "Spatial",
        "Identity",
        "Growth",
        "Geometry",
    }


def test_elite_boss_task_requires_multi_domain_operational_collaboration():
    task = json.loads(
        (TRAINING_DIRECTORY / "elite_cognitive_task_20.json").read_text(
            encoding="utf-8",
        )
    )
    metadata = task["nexryn_metadata"]

    assert metadata["task_title"] == "THE ELITE MULTI DOMAIN BOSS TASK"
    assert len([
        cell
        for row in task["train"][0]["input"]
        for cell in row
        if cell
    ]) >= 10
    assert {
        "growth",
        "spatial_reasoning",
        "topological_reasoning",
        "identity_preservation",
        "world_model",
        "capability_composition",
        "knowledge_investment",
        "candidate_arena",
        "compiler_runtime_activation",
        "validation_pipeline",
    }.issubset(set(metadata["target_concepts"]))
    assert set(metadata["target_domains"]) == {
        "Color",
        "Transformation",
        "Topology",
        "Spatial",
        "Identity",
        "Growth",
    }
    assert {
        "translate",
        "preserve_topology",
        "preserve_colors",
        "preserve_grid",
        "duplicate_object",
    }.issubset(set(metadata["capability_graduation_targets"]))
    assert "replace_color" in metadata["forbidden_simple_solution_classes"]
