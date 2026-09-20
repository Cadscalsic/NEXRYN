"""Bounded shutdown latency guard."""

from __future__ import annotations

import logging
import time
from typing import Callable


MAX_SHUTDOWN_TIME = 2.0
SHUTDOWN_TIMEOUT_EXCEEDED = "SHUTDOWN_TIMEOUT_EXCEEDED"


class ShutdownTimeoutGuard:
    def __init__(
        self,
        max_shutdown_time: float = MAX_SHUTDOWN_TIME,
        logger: logging.Logger | None = None,
    ) -> None:
        self.max_shutdown_time = max_shutdown_time
        self.logger = logger or logging.getLogger(__name__)
        self.started_at: float | None = None
        self.timeout_exceeded = False

    def start(self) -> None:
        self.started_at = time.perf_counter()
        self.timeout_exceeded = False

    def elapsed(self) -> float:
        if self.started_at is None:
            return 0.0
        return time.perf_counter() - self.started_at

    def check(self, force_shutdown: Callable[[], None] | None = None) -> bool:
        if self.started_at is None:
            self.start()
        if self.elapsed() <= self.max_shutdown_time:
            return False
        self.timeout_exceeded = True
        self.logger.warning("[SHUTDOWN] %s", SHUTDOWN_TIMEOUT_EXCEEDED)
        if force_shutdown is not None:
            force_shutdown()
        return True
