from runtime.security import (
    execution_authority_guard,
    memory_access_guard,
    meta_supervisor_guard,
    program_safety_guard,
    security_reporter,
    self_repair_safety_guard,
    strategy_safety_guard,
)
from runtime.synthesis.program_synthesis_engine import ProgramSynthesisEngine


def setup_function():
    security_reporter.reset()


def test_planned_ops_mismatch_denies_execution_and_reports_violation():
    decision = execution_authority_guard.request_permission(
        "execute_program",
        {
            "execution_report": {
                "execution_authorized": True,
                "planned_ops": ["replace_color"],
                "executed_ops": [],
            }
        },
        {"integrity_verified": True},
    )
    report = security_reporter.build_report()

    assert decision.permission == "DENY"
    assert decision.reason == "EXECUTION_INTEGRITY_VIOLATION"
    assert report["integrity_violations"]


def test_locked_truth_write_is_blocked():
    decision = memory_access_guard.check_access(
        "locked_truth_memory",
        "write",
        {"truth_id": "stable-truth"},
    )
    report = security_reporter.build_report()

    assert decision.permission == "DENY"
    assert decision.reason == "LOCKED_TRUTH_WRITE_BLOCKED"
    assert report["denied_actions"][0]["reason"] == "LOCKED_TRUTH_WRITE_BLOCKED"


def test_weak_strategy_context_match_requires_sandbox_or_review():
    decision = strategy_safety_guard.evaluate({
        "success_rate": 0.95,
        "context_match": 0.50,
        "strategy_version_hash_unchanged": True,
        "critical_failure_history": False,
        "governance_block": False,
    })

    assert decision.permission in {"SANDBOX_ONLY", "REQUIRE_REVIEW"}


def test_self_repair_critical_change_is_denied():
    decision = self_repair_safety_guard.evaluate_plan({
        "anomaly_type": "IDENTITY_STATE_CONFLICT",
        "severity": "CRITICAL",
        "actions": ["DISABLE_IDENTITY_PROTECTION"],
    })

    assert decision.permission == "DENY"
    assert decision.risk_level == "CRITICAL"


def test_meta_supervisor_stop_cognition_blocks_downstream_cognition():
    decision = meta_supervisor_guard.evaluate(
        "deep_reasoning",
        {
            "cognitive_directive": {
                "action": "STOP_COGNITION",
            }
        },
    )

    assert decision.permission == "DENY"


def test_program_execution_denied_returns_security_result():
    engine = ProgramSynthesisEngine()
    result = engine.execute_program(
        [[1]],
        {
            "execution_authorized": True,
            "executed_ops": [],
            "program_steps": [
                {
                    "operator": "replace_color",
                    "parameters": {
                        "source_color": 1,
                        "target_color": 2,
                    },
                }
            ],
            "integrity_verified": True,
        },
    )

    assert result["execution_denied"] is True
    assert result["security_decision"]["permission"] == "DENY"
