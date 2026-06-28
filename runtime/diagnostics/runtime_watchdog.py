from __future__ import annotations

import time


class RuntimeWatchdog:
    DEFAULT_THRESHOLDS = {
        "boot_total": 5.0,
        "cache_init": 1.0,
        "task_selection": 2.0,
        "governance": 10.0,
        "finalization": 3.0,
    }

    def __init__(self, thresholds: dict | None = None):
        self.thresholds = {
            **self.DEFAULT_THRESHOLDS,
            **(thresholds or {}),
        }
        self._starts = {}
        self.durations = {}
        self.checkpoints = {}
        self.warnings = []

    def start(self, label):
        self._starts[str(label)] = time.perf_counter()
        return self._starts[str(label)]

    def stop(self, label):
        label = str(label)
        started = self._starts.get(label)
        if started is None:
            return 0.0
        duration = time.perf_counter() - started
        self.durations[label] = duration
        return duration

    def checkpoint(self, label):
        self.checkpoints[str(label)] = time.perf_counter()
        return self.checkpoints[str(label)]

    def exceeded(self, label, threshold_seconds):
        duration = self.durations.get(str(label))
        if duration is None and str(label) in self._starts:
            duration = time.perf_counter() - self._starts[str(label)]
        exceeded = bool(duration is not None and duration > threshold_seconds)
        if exceeded:
            self.warn(str(label), duration, threshold_seconds)
        return exceeded

    def warn(self, label, duration, threshold_seconds):
        warning = {
            "stage": str(label),
            "duration": round(float(duration), 4),
            "threshold": float(threshold_seconds),
        }
        if warning not in self.warnings:
            self.warnings.append(warning)
            print(
                "NEXRYN WATCHDOG WARNING :: "
                f"{warning['stage']} took {warning['duration']}s "
                f"(threshold {warning['threshold']}s)"
            )
        return warning

    def stop_and_warn(self, label, threshold_label=None):
        duration = self.stop(label)
        threshold = self.thresholds.get(threshold_label or label)
        if threshold is not None and duration > threshold:
            self.warn(label, duration, threshold)
        return duration

    def report(self):
        return {
            "system": "runtime_watchdog",
            "durations": {
                key: round(value, 4)
                for key, value in self.durations.items()
            },
            "checkpoints": sorted(self.checkpoints),
            "warnings": list(self.warnings),
        }


__all__ = ["RuntimeWatchdog"]
