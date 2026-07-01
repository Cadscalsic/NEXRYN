from runtime.training.concept_coverage_audit import audit_training_tasks
from runtime.training.curriculum_validator import validate_curriculum
from runtime.training.task_generation_engine import TaskGenerationEngine


def test_concept_coverage_audit_reports_required_curriculum_surface(tmp_path):
    task = TaskGenerationEngine(tmp_path).task_for_concepts(
        ["containment", "occlusion"],
    )
    TaskGenerationEngine(tmp_path).write_tasks([task])

    report = audit_training_tasks(tmp_path, report_path=None)

    assert report["total_tasks"] == 1
    assert report["tasks"][0]["primary_concepts"] == ["containment"]
    assert report["tasks"][0]["secondary_concepts"][0] == "occlusion"
    assert report["tasks"][0]["spatial_concepts"] == ["containment"]
    assert report["tasks"][0]["curriculum_level"] == 3
    assert report["concepts"]["containment"]["task_count"] == 1


def test_task_generation_engine_creates_evidence_only_gap_tasks(tmp_path):
    engine = TaskGenerationEngine(tmp_path)
    report = {
        "concepts": {
            "containment": {"task_count": 0},
            "occlusion": {"task_count": 3},
        }
    }

    tasks = engine.generate_for_missing(
        audit_report=report,
        minimum_task_count=1,
        include_multi_concept=False,
    )

    assert any(
        "containment" in task["nexryn_metadata"]["target_concepts"]
        for task in tasks
    )
    assert all(
        task["nexryn_metadata"]["governance_constraints"]["evidence_only"]
        for task in tasks
    )


def test_curriculum_validator_exposes_coverage_report(tmp_path):
    engine = TaskGenerationEngine(tmp_path)
    engine.write_tasks([
        engine.task_for_concepts(["causal_reasoning", "topology_change"]),
    ])

    report = validate_curriculum(tmp_path)
    coverage = report["curriculum_coverage_report"]

    assert "concept_coverage_score" in report
    assert "curriculum_balance_score" in report
    assert coverage["generated_tasks"] == 1
    assert coverage["multi_concept_tasks"] == 1
    assert coverage["topology_tasks"] >= 1
