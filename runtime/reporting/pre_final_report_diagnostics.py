from __future__ import annotations

import cProfile
import faulthandler
import json
import os
import pstats
import sys
import threading
import time
import tracemalloc
from collections import Counter
from pathlib import Path
from typing import Any


class PreFinalReportDiagnostics:
    """Environment-gated diagnostics for the silent final-report interval."""

    def __init__(self) -> None:
        self.enabled = os.environ.get("NEXRYN_FINAL_REPORT_DIAG") == "1"
        self.execution_id = os.environ.get("NEXRYN_EXECUTION_ID", "local")
        self.started = 0.0
        self.previous = 0.0
        self.phase = "not_started"
        self.profile = cProfile.Profile()
        self.profile_enabled = False
        self.markers: list[dict[str, Any]] = []
        self.counters: Counter[str] = Counter()
        self.snapshots: dict[str, Any] = {}
        self.artifact_path = Path("runtime/artifacts/pre_final_report_diagnostics.json")

    def start(self, execution_id: str | None = None) -> None:
        if not self.enabled:
            return
        if execution_id:
            self.execution_id = str(execution_id)
        self.started = time.perf_counter()
        self.previous = self.started
        if not tracemalloc.is_tracing():
            tracemalloc.start(25)
        try:
            faulthandler.enable()
            faulthandler.dump_traceback_later(10, repeat=True)
        except Exception:
            pass
        self.profile.enable()
        self.profile_enabled = True
        self.mark("PRE_FINALIZATION_ENTER")

    def stop(self) -> None:
        if not self.enabled:
            return
        if self.profile_enabled:
            self.profile.disable()
            self.profile_enabled = False
        try:
            faulthandler.cancel_dump_traceback_later()
        except Exception:
            pass
        self.write_artifact()

    def mark(self, name: str, **sizes: Any) -> None:
        if not self.enabled:
            return
        now = time.perf_counter()
        elapsed = now - (self.previous or now)
        total = now - (self.started or now)
        self.previous = now
        current, peak = tracemalloc.get_traced_memory() if tracemalloc.is_tracing() else (0, 0)
        record = {
            "marker": name,
            "monotonic": round(now, 6),
            "elapsed_from_previous": round(elapsed, 6),
            "elapsed_total": round(total, 6),
            "memory_tracemalloc_current_bytes": current,
            "memory_tracemalloc_peak_bytes": peak,
            "thread": threading.current_thread().name,
            "execution_id": self.execution_id,
            **sizes,
        }
        self.markers.append(record)
        print(f"[PRE_FINAL_REPORT_DIAG] {json.dumps(record, sort_keys=True, default=str)}", flush=True)

    def phase_enter(self, phase: str, **sizes: Any) -> None:
        self.phase = phase
        self.mark(f"{phase}_ENTER", **sizes)

    def phase_exit(self, phase: str, **sizes: Any) -> None:
        self.mark(f"{phase}_EXIT", **sizes)

    def count(self, name: str, amount: int = 1) -> None:
        if not self.enabled:
            return
        self.counters[name] += amount
        value = self.counters[name]
        if value <= 10 or value % 100 == 0:
            self.mark(f"PROGRESS_{name}", count=value, phase=self.phase)

    def collection_snapshot(self, label: str, payload: Any, *, max_depth: int = 6) -> None:
        if not self.enabled:
            return
        summary = self._shape(payload, max_depth=max_depth)
        self.snapshots[label] = summary
        self.mark(f"{label}_SNAPSHOT", **summary)

    def write_artifact(self) -> None:
        if not self.enabled:
            return
        stats = {}
        top_allocations = []
        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            for stat in snapshot.statistics("lineno")[:30]:
                top_allocations.append({
                    "trace": str(stat.traceback),
                    "size_bytes": stat.size,
                    "count": stat.count,
                })
        if self.profile_enabled:
            self.profile.disable()
            self.profile_enabled = False
        stats_path = self.artifact_path.with_suffix(".pstats")
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        self.profile.dump_stats(str(stats_path))
        ps = pstats.Stats(self.profile)
        cumulative = []
        self_time = []
        for func, stat in ps.stats.items():
            cc, nc, tt, ct, callers = stat
            entry = {
                "file": func[0],
                "line": func[1],
                "function": func[2],
                "call_count": nc,
                "primitive_call_count": cc,
                "self_time": round(tt, 6),
                "cumulative_time": round(ct, 6),
            }
            cumulative.append(entry)
            self_time.append(entry)
        stats["top_cumulative"] = sorted(cumulative, key=lambda item: item["cumulative_time"], reverse=True)[:30]
        stats["top_self"] = sorted(self_time, key=lambda item: item["self_time"], reverse=True)[:30]
        payload = {
            "execution_id": self.execution_id,
            "markers": self.markers,
            "counters": dict(self.counters),
            "collection_snapshots": self.snapshots,
            "top_allocations": top_allocations,
            "profile": stats,
            "pstats_path": str(stats_path),
        }
        self.artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
        print(f"[PRE_FINAL_REPORT_DIAG] artifact={self.artifact_path}", flush=True)

    def _shape(self, payload: Any, *, max_depth: int) -> dict[str, Any]:
        seen: set[int] = set()
        totals = {
            "total_nodes": 0,
            "total_lists": 0,
            "total_dicts": 0,
            "max_depth": 0,
            "largest_list": 0,
            "largest_dict": 0,
            "estimated_scalar_chars": 0,
        }

        def visit(value: Any, depth: int) -> None:
            totals["total_nodes"] += 1
            totals["max_depth"] = max(totals["max_depth"], depth)
            if depth >= max_depth:
                return
            if isinstance(value, dict):
                oid = id(value)
                if oid in seen:
                    return
                seen.add(oid)
                totals["total_dicts"] += 1
                totals["largest_dict"] = max(totals["largest_dict"], len(value))
                for key, item in list(value.items())[:500]:
                    totals["estimated_scalar_chars"] += len(str(key))
                    visit(item, depth + 1)
            elif isinstance(value, (list, tuple)):
                oid = id(value)
                if oid in seen:
                    return
                seen.add(oid)
                totals["total_lists"] += 1
                totals["largest_list"] = max(totals["largest_list"], len(value))
                for item in list(value)[:500]:
                    visit(item, depth + 1)
            elif isinstance(value, (str, int, float, bool, type(None))):
                totals["estimated_scalar_chars"] += len(str(value))

        visit(payload, 0)
        return totals


pre_final_report_diagnostics = PreFinalReportDiagnostics()

