"""Best-effort resource cleanup with warning-only failures."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Callable


TRACKED_RESOURCE_TYPES = (
    "memory_buffers",
    "file_handles",
    "executors",
    "queues",
    "timers",
    "telemetry_streams",
    "cache_writers",
    "report_generators",
)


class ResourceCleanupManager:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.resources = defaultdict(list)
        self.cleanup_failures: list[dict] = []
        self.cleanup_reports: list[dict] = []

    def register(self, resource_type: str, resource: Any, cleanup: Callable | None = None) -> Any:
        if resource_type not in TRACKED_RESOURCE_TYPES:
            raise ValueError(f"Unknown cleanup resource type: {resource_type}")
        self.resources[resource_type].append((resource, cleanup))
        return resource

    def cleanup_all(self) -> dict:
        started = time.perf_counter()
        for resource_type in TRACKED_RESOURCE_TYPES:
            for resource, cleanup in list(self.resources.get(resource_type, [])):
                self._cleanup_resource(resource_type, resource, cleanup)
            self.resources[resource_type].clear()
        duration = time.perf_counter() - started
        return {
            "duration": round(duration, 4),
            "cleanup_failures": list(self.cleanup_failures),
            "cleanup_reports": list(self.cleanup_reports),
        }

    def _cleanup_resource(self, resource_type: str, resource: Any, cleanup: Callable | None) -> None:
        started = time.perf_counter()
        report = {
            "resource_type": resource_type,
            "resource": repr(resource),
            "start": started,
            "duration": 0.0,
            "success": False,
            "failure_reason": None,
        }
        self.logger.info("[SHUTDOWN] cleanup start %s", resource_type)
        try:
            if cleanup is not None:
                cleanup(resource)
            else:
                self._default_cleanup(resource)
            report["success"] = True
        except Exception as error:
            report["failure_reason"] = str(error)
            self.cleanup_failures.append(report.copy())
            self.logger.warning(
                "[SHUTDOWN] cleanup warning %s: %s",
                resource_type,
                error,
            )
        finally:
            report["duration"] = round(time.perf_counter() - started, 4)
            self.cleanup_reports.append(report)
            self.logger.info(
                "[SHUTDOWN] cleanup done %s duration=%s success=%s failure_reason=%s",
                resource_type,
                report["duration"],
                report["success"],
                report["failure_reason"],
            )

    def _default_cleanup(self, resource: Any) -> None:
        if hasattr(resource, "shutdown"):
            try:
                resource.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                resource.shutdown(wait=False)
            return
        if hasattr(resource, "cancel"):
            resource.cancel()
            return
        if hasattr(resource, "close"):
            resource.close()
            return
        if hasattr(resource, "flush"):
            resource.flush()
            return
        if isinstance(resource, (list, dict, set, bytearray)):
            resource.clear()
