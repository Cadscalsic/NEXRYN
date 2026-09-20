from runtime.diagnostics import RuntimeWatchdog


def test_runtime_watchdog_records_first_task_started():
    watchdog = RuntimeWatchdog()

    watchdog.start("boot_total")
    watchdog.checkpoint("boot_start")
    watchdog.checkpoint("first_task_started")

    report = watchdog.report()

    assert "first_task_started" in report["checkpoints"]
