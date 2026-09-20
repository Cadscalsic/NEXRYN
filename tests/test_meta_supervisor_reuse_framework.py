from runtime.meta.supervisor import meta_supervisor
from runtime.meta.supervisor.execution_memory import ExecutionRecord
from runtime.meta.supervisor.program_memory import ProgramRecord
from runtime.meta.supervisor.strategy_memory import StrategyRecord
from runtime.meta.supervisor.task_signature_engine import TaskSignature


def _signature():
    return TaskSignature(
        concepts=("duplicate_object",),
        contexts=("object_replication_context",),
        transformations=("horizontal_translation",),
        constraints=("preserve_topology",),
    )


def _context():
    return {
        "concept": "duplicate_object",
        "context_name": "object_replication_context",
        "transformation": "horizontal_translation",
        "preserve_topology": True,
    }


def _clear_memories():
    meta_supervisor.reset_episode()
    meta_supervisor.reuse_engine.program_memory.records = []
    meta_supervisor.reuse_engine.strategy_memory.records = []
    meta_supervisor.reuse_engine.execution_memory.records = []


def test_program_reuse_blocks_reasoning_and_synthesis():
    _clear_memories()
    signature_id = _signature().stable_id()
    meta_supervisor.reuse_engine.program_memory.records = [
        ProgramRecord(
            program_id="program-1",
            task_signature_id=signature_id,
            program={"program_steps": [{"operator": "duplicate_object"}]},
            match_confidence=0.97,
            validation_state="validated",
            integrity_verified=True,
        )
    ]

    directive = meta_supervisor.supervise(_context())
    report = meta_supervisor.build_meta_supervisor_report()

    assert directive.action == "REUSE_EXECUTABLE_PROGRAM"
    assert meta_supervisor.is_action_allowed("reasoning") is False
    assert meta_supervisor.is_action_allowed("program_synthesis") is False
    assert meta_supervisor.is_action_allowed("strategy_search") is False
    assert report["program_reused"] is True


def test_strategy_reuse_disables_strategy_search():
    _clear_memories()
    signature_id = _signature().stable_id()
    meta_supervisor.reuse_engine.strategy_memory.records = [
        StrategyRecord(
            strategy_id="strategy-1",
            strategy_name="duplicate_object_right",
            task_signature_id=signature_id,
            success_rate=0.93,
            confidence=0.94,
            context_match=0.92,
            validated=True,
            integrity_verified=True,
        )
    ]

    directive = meta_supervisor.supervise(_context())

    assert directive.action == "REUSE_KNOWN_STRATEGY"
    assert meta_supervisor.is_action_allowed("strategy_search") is False
    assert meta_supervisor.is_action_allowed("hypothesis_expansion") is False


def test_locked_truth_reuse_skips_governance_revalidation():
    _clear_memories()
    directive = meta_supervisor.supervise({
        **_context(),
        "truth_commit_result": {
            "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        },
    })

    assert directive.action == "REUSE_LOCKED_TRUTH"
    assert meta_supervisor.is_action_allowed("governance_revalidation") is False
    assert meta_supervisor.is_action_allowed("truth_revalidation") is False


def test_completed_episode_stops_cognition_fast():
    _clear_memories()
    signature_id = _signature().stable_id()
    meta_supervisor.reuse_engine.execution_memory.records = [
        ExecutionRecord(
            execution_id="execution-1",
            task_signature_id=signature_id,
            episode_completed=True,
            integrity_verified=True,
        )
    ]

    directive = meta_supervisor.supervise(_context())

    assert directive.action == "STOP_COGNITION"
    assert directive.shutdown_mode == "fast"
    assert meta_supervisor.is_action_allowed("self_improvement") is False
    assert meta_supervisor.is_action_allowed("governance_revalidation") is False
