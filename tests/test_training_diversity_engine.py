from runtime.training.task_diversity_engine import TaskDiversityEngine
from runtime.truth.core_knowledge_registry import CoreKnowledgeRegistry
from runtime.truth.truth_graduation_engine import TruthGraduationEngine


def test_truth_graduation_registers_core_knowledge():
    truth = {
        "concept": "shape_preservation",
        "truth_confidence": 0.96,
        "cross_task_stability": 0.96,
        "contradiction_rate": 0.01,
        "truth_commit_count": 4,
    }

    graduation = TruthGraduationEngine().graduate(
        [truth],
        reuse_report={"truth_reuse_rate": 0.9},
    )
    registry = CoreKnowledgeRegistry()
    registration = registry.register_graduated(
        graduation["graduation_records"],
    )

    assert graduation["graduated_concepts"] == ["shape_preservation"]
    assert registration["core_concepts"] == ["shape_preservation"]
    assert registry.all_records()[0]["graduation_level"] == "CORE_KNOWLEDGE"


def test_task_diversity_penalizes_recent_core_concepts_and_rewards_frontier():
    reports = [
        {
            "task_file": "task_known.json",
            "target_concepts": ["shape_preservation"],
            "priority": 120,
            "target_coverage_gap": 12,
            "original_order": 0,
        },
        {
            "task_file": "task_frontier.json",
            "target_concepts": ["occlusion"],
            "priority": 20,
            "target_coverage_gap": 2,
            "original_order": 1,
        },
    ]

    diversity = TaskDiversityEngine().rerank(
        reports,
        history=[
            {
                "task_files": ["task_known.json"],
                "concepts": ["shape_preservation"],
            }
        ],
        core_knowledge=[
            {
                "concept": "shape_preservation",
                "graduation_level": "CORE_KNOWLEDGE",
                "mastery_score": 0.96,
                "training_dominance_penalty": 0.75,
            }
        ],
        concept_counts={"shape_preservation": 40, "occlusion": 0},
        concept_states={"shape_preservation": "CORE_KNOWLEDGE"},
    )

    assert diversity["ranked_task_files"][0] == "task_frontier.json"
    assert diversity["cooldown_filtered_tasks"] == ["task_known.json"]
    assert diversity["cooldown_filtered_concepts"] == [
        "shape_preservation",
    ]
    assert "occlusion" in diversity["frontier_concepts_explored"]


def test_task_diversity_handles_missing_numeric_values():
    diversity = TaskDiversityEngine().rerank(
        [
            {
                "task_file": "task_missing_numbers.json",
                "target_concepts": ["shape_preservation"],
                "priority": None,
                "target_coverage_gap": None,
                "original_order": 0,
            }
        ],
        core_knowledge=[
            {
                "concept": "shape_preservation",
                "mastery_score": None,
                "training_dominance_penalty": None,
            }
        ],
        concept_counts={"shape_preservation": None},
    )

    ranked = diversity["ranked_task_reports"][0]
    assert ranked["task_file"] == "task_missing_numbers.json"
    assert ranked["base_priority"] == 0.0
    assert ranked["concept_cooldown_penalty"] == 0.0
    assert diversity["concept_reports"][0]["mastery_score"] == 0.0
