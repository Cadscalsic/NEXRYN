import threading

from runtime.shutdown import SHUTDOWN_REPORT, ShutdownController
from runtime.shutdown.post_success_isolation import PostSuccessIsolation
from runtime.shutdown.resource_cleanup_manager import ResourceCleanupManager
from runtime.shutdown.shutdown_state_machine import (
    ShutdownState,
    ShutdownStateMachine,
)


def test_shutdown_state_machine_is_monotonic():
    machine = ShutdownStateMachine()

    machine.transition_to(ShutdownState.TASK_COMPLETED)
    machine.transition_to(ShutdownState.LEARNING_COMMITTED)

    try:
        machine.transition_to(ShutdownState.TASK_RUNNING)
    except ValueError:
        pass
    else:
        raise AssertionError("shutdown state returned to TASK_RUNNING")


def test_post_success_isolation_blocks_nonessential_cognition():
    isolation = PostSuccessIsolation()
    context = {
        "evaluation_result": {"success": True},
        "evaluation_metrics": {"accuracy": 1.0},
    }

    isolation.activate(context)

    assert isolation.operation_allowed("shutdown") is True
    assert isolation.operation_allowed("memory_commit") is True
    assert isolation.operation_allowed("deep_reasoning") is False
    assert context["post_success_isolation"]["success_lock"]["evaluation_metrics"] == {
        "accuracy": 1.0,
    }


def test_resource_cleanup_failures_are_warning_only():
    manager = ResourceCleanupManager()
    manager.register(
        "file_handles",
        object(),
        cleanup=lambda _resource: (_ for _ in ()).throw(RuntimeError("close failed")),
    )

    report = manager.cleanup_all()

    assert report["cleanup_failures"]
    assert report["cleanup_failures"][0]["failure_reason"] == "close failed"


def test_shutdown_controller_generates_report_without_exiting():
    controller = ShutdownController()
    context = {
        "episode_completed": True,
        "evaluation_result": {"success": True},
        "evaluation_metrics": {"accuracy": 1.0},
    }

    context = controller.execute_shutdown(context, exit_process=False)

    assert SHUTDOWN_REPORT in context
    assert context[SHUTDOWN_REPORT]["state_machine"]["terminal"] is True
    assert context[SHUTDOWN_REPORT]["post_success_isolation"]["enabled"] is True
    assert context["evaluation_result"]["success"] is True


def test_thread_monitor_reports_hanging_thread_before_exit():
    controller = ShutdownController()
    stop = threading.Event()
    thread = threading.Thread(
        target=lambda: stop.wait(0.1),
        name="shutdown-test-thread",
    )
    thread.start()
    try:
        report = controller.monitor.hanging_resources()
        names = {item["name"] for item in report["active_threads"]}
        assert "shutdown-test-thread" in names
    finally:
        stop.set()
        thread.join(timeout=1)
