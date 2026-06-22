from runtime.self_repair.anomaly_detector import AnomalyDetector
from runtime.self_repair.repair_executor import RepairExecutor
from runtime.self_repair.repair_memory import RepairMemory
from runtime.self_repair.repair_planner import RepairPlanner
from runtime.self_repair.rollback_manager import RollbackManager
from runtime.self_repair.self_repair_engine import SelfRepairEngine


def test_completed_episode_forces_fast_shutdown_and_stops_loops(tmp_path):
    engine = SelfRepairEngine()
    engine.repair_memory = RepairMemory(tmp_path / "repair_memory.json")
    engine.rollback_manager = RollbackManager()
    engine.repair_executor = RepairExecutor(
        rollback_manager=engine.rollback_manager,
        repair_memory=engine.repair_memory,
    )

    report = engine.run_operational_repair_cycle({
        "evaluation_result": {
            "episode_completed": True,
            "failure_detected": False,
            "retry_allowed": False,
        },
        "shutdown_mode": "normal",
        "background_loops_active": True,
    })
    context = report["runtime_context"]

    assert report["anomalies_detected"][0]["anomaly_type"] == "TERMINATION_DESYNC"
    assert context["shutdown_mode"] == "fast"
    assert context["post_success_shutdown"]["enabled"] is True
    assert context["background_loops_active"] is False


def test_saturated_locked_truth_syncs_recommended_next_step(tmp_path):
    engine = SelfRepairEngine()
    engine.repair_memory = RepairMemory(tmp_path / "repair_memory.json")
    engine.rollback_manager = RollbackManager()
    engine.repair_executor = RepairExecutor(
        rollback_manager=engine.rollback_manager,
        repair_memory=engine.repair_memory,
    )

    report = engine.run_operational_repair_cycle({
        "truth_commit_result": {
            "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        },
        "learning_saturation_report": {
            "evidence_saturated": True,
            "recommended_next_step": "continue_adaptive_training",
        },
    })
    context = report["runtime_context"]

    anomaly_types = [
        anomaly["anomaly_type"]
        for anomaly in report["anomalies_detected"]
    ]
    assert "LEARNING_SATURATION_CONFLICT" in anomaly_types
    saturation_plan = next(
        plan
        for plan in report["repair_plans_created"]
        if plan["anomaly_type"] == "LEARNING_SATURATION_CONFLICT"
    )
    assert saturation_plan["actions"] == [
        "SYNC_RECOMMENDED_NEXT_STEP",
        "WRITE_REPAIR_MEMORY",
    ]
    assert context["recommended_next_step"] == "freeze_concept"
    assert context["learning_saturation_report"]["enable_adaptive_training"] is False


def test_authorized_zero_steps_flags_critical_without_auto_execute(tmp_path):
    detector = AnomalyDetector()
    planner = RepairPlanner()
    memory = RepairMemory(tmp_path / "repair_memory.json")
    rollback = RollbackManager()
    executor = RepairExecutor(rollback, memory)

    anomalies = detector.detect({
        "execution_report": {
            "execution_authorized": True,
            "executed_steps": 0,
        }
    })
    plans = planner.plan(anomalies)
    context, result = executor.execute({}, plans[0])

    assert anomalies[0].anomaly_type == "EXECUTION_INTEGRITY_CONFLICT"
    assert anomalies[0].severity == "CRITICAL"
    assert plans[0].safe_to_execute is False
    assert result.success is False
    assert context["governance_review_requested"] is True


def test_planned_ops_mismatch_is_execution_integrity_conflict():
    anomalies = AnomalyDetector().detect({
        "execution_report": {
            "planned_ops": ["replace_color"],
            "executed_ops": [],
        }
    })

    assert anomalies[0].anomaly_type == "EXECUTION_INTEGRITY_CONFLICT"
    assert anomalies[0].severity == "CRITICAL"
