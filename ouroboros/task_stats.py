"""
ouroboros/task_stats.py — Task outcome intelligence.

Reads events.jsonl, computes success/failure rates, cost averages,
and common error patterns per task type. Writes a short summary
that consciousness reads every cycle.

No LLM calls. Pure arithmetic on existing log data.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ouroboros.utils import utc_now_iso, read_text

log = logging.getLogger(__name__)

_CACHE_TTL_SEC = 120


def _read_tail_lines(path: Path, max_lines: int, max_bytes: int = 512_000) -> List[str]:
    """
    Read the last N lines from a file efficiently.
    Reads from the end of the file, not the beginning.
    Falls back to full read for small files.
    """
    if not path.exists():
        return []
    try:
        file_size = path.stat().st_size
        if file_size == 0:
            return []
        # Small file: just read it all
        if file_size <= max_bytes:
            return path.read_text(encoding="utf-8").strip().split("\n")[-max_lines:]
        # Large file: seek from end
        with open(path, "rb") as f:
            f.seek(-min(max_bytes, file_size), 2)  # seek from end
            chunk = f.read().decode("utf-8", errors="replace")
        lines = chunk.split("\n")
        # First line may be partial (we seeked into the middle of it)
        if len(lines) > 1:
            lines = lines[1:]  # drop partial first line
        return lines[-max_lines:]
    except Exception as e:
        log.debug("_read_tail_lines failed for %s: %s", path, e)
        return []


def compute_task_stats(drive_root: Path, max_events: int = 200) -> Dict[str, Any]:
    """
    Read last N events from events.jsonl, compute stats per task type.
    Returns dict with per-type stats and overall summary.
    """
    events_path = drive_root / "logs" / "events.jsonl"
    if not events_path.exists():
        return {"summary": "(no events yet)", "by_type": {}}

    lines = _read_tail_lines(events_path, max_events)

    # Parse events
    task_done = []
    task_errors = []
    tool_errors = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except Exception:
            continue

        etype = evt.get("type", "")
        if etype == "task_done":
            task_done.append(evt)
        elif etype == "task_error":
            task_errors.append(evt)
        elif etype in ("tool_error", "tool_rounds_exceeded"):
            tool_errors.append(evt)

    if not task_done and not task_errors:
        return {"summary": "(no completed tasks yet)", "by_type": {}}

    # Aggregate by task type
    by_type: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "count": 0, "total_cost": 0.0, "total_rounds": 0,
        "errors": 0, "costs": [], "rounds": [],
    })

    for evt in task_done:
        ttype = evt.get("task_type", "unknown") or "unknown"
        stats = by_type[ttype]
        stats["count"] += 1
        cost = float(evt.get("cost_usd", 0))
        rounds = int(evt.get("total_rounds", 0))
        stats["total_cost"] += cost
        stats["total_rounds"] += rounds
        stats["costs"].append(cost)
        stats["rounds"].append(rounds)

    # Count errors by type
    error_types: Dict[str, int] = defaultdict(int)
    for evt in task_errors:
        ttype = evt.get("task_type", "unknown") or "unknown"
        by_type[ttype]["errors"] += 1
        err_msg = str(evt.get("error", ""))[:60]
        error_types[err_msg] += 1

    for evt in tool_errors:
        tool = evt.get("tool", "?")
        err_msg = str(evt.get("error", ""))[:40]
        error_types[f"{tool}: {err_msg}"] += 1

    # Build summary
    total_tasks = sum(s["count"] for s in by_type.values())
    total_errors = sum(s["errors"] for s in by_type.values())
    total_cost = sum(s["total_cost"] for s in by_type.values())

    lines_out = [
        f"Tasks completed: {total_tasks} | Errors: {total_errors} | "
        f"Total cost: ${total_cost:.4f}",
    ]

    # Per-type breakdown
    for ttype, stats in sorted(by_type.items(), key=lambda x: x[1]["count"], reverse=True):
        if not stats["count"]:
            continue
        avg_cost = stats["total_cost"] / stats["count"]
        avg_rounds = stats["total_rounds"] / stats["count"]
        success_rate = ((stats["count"] - stats["errors"]) / stats["count"]) * 100
        lines_out.append(
            f"  {ttype}: {stats['count']} tasks, "
            f"avg ${avg_cost:.4f}/task, "
            f"avg {avg_rounds:.0f} rounds, "
            f"{success_rate:.0f}% success"
        )

    # Top errors
    if error_types:
        lines_out.append("Common errors:")
        for err, count in sorted(error_types.items(), key=lambda x: -x[1])[:5]:
            lines_out.append(f"  ({count}x) {err}")

    result = {
        "summary": "\n".join(lines_out),
        "by_type": {
            k: {
                "count": v["count"],
                "errors": v["errors"],
                "avg_cost": v["total_cost"] / max(1, v["count"]),
                "avg_rounds": v["total_rounds"] / max(1, v["count"]),
                "max_rounds": max(v["rounds"]) if v["rounds"] else 0,
            }
            for k, v in by_type.items()
        },
    }
    return result


def get_stats_text(drive_root: Path) -> str:
    """Pure function: compute stats and return formatted text. No file I/O side effects."""
    stats = compute_task_stats(drive_root)
    return stats["summary"]


def write_stats_summary(drive_root: Path) -> str:
    """
    Compute stats, write to memory/task_stats.md, return the content.
    Skips recomputation if cache file is fresh (< TTL seconds old).
    """
    output_path = drive_root / "memory" / "task_stats.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Cache check — don't recompute too often
    if output_path.exists():
        try:
            age = time.time() - output_path.stat().st_mtime
            if age < _CACHE_TTL_SEC:
                return read_text(output_path)
        except Exception:
            pass

    summary = get_stats_text(drive_root)
    content = f"# Task Performance (auto-updated)\n\n{summary}\n"
    try:
        tmp = output_path.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(str(tmp), str(output_path))  # atomic
    except Exception as e:
        log.warning("Failed to write task stats: %s", e)

    return content


def get_rounds_stats_for_type(drive_root: Path, task_type: str) -> Optional[Dict[str, int]]:
    """
    Get historical round stats for a task type.
    Returns {avg, max, count} or None if insufficient data (< 3 tasks).
    """
    stats = compute_task_stats(drive_root)
    type_stats = stats.get("by_type", {}).get(task_type)
    if type_stats and type_stats["count"] >= 3:
        return {
            "avg": int(type_stats["avg_rounds"]),
            "max": int(type_stats["max_rounds"]),
            "count": int(type_stats["count"]),
        }
    return None


# Backward compat
def get_avg_rounds_for_type(drive_root: Path, task_type: str) -> Optional[int]:
    """Get historical average rounds for a task type. Returns None if < 3 tasks."""
    s = get_rounds_stats_for_type(drive_root, task_type)
    return s["avg"] if s else None


# Cache for tool stats (module-level, TTL-based)
_tool_stats_cache: Optional[Dict[str, Dict[str, Any]]] = None
_tool_stats_ts: float = 0.0
_tool_stats_lock = __import__("threading").Lock()


def compute_tool_stats(drive_root: Path) -> Dict[str, Dict[str, Any]]:
    """
    Compute per-tool success/failure rates from tools.jsonl.
    Returns dict of {tool_name: {calls, errors, success_rate_pct}}.
    Thread-safe, TTL-cached.
    """
    global _tool_stats_cache, _tool_stats_ts
    now = time.time()

    with _tool_stats_lock:
        if _tool_stats_cache is not None and (now - _tool_stats_ts) < _CACHE_TTL_SEC:
            return _tool_stats_cache

    tools_path = drive_root / "logs" / "tools.jsonl"
    lines = _read_tail_lines(tools_path, 500)
    if not lines:
        return {}

    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"calls": 0, "errors": 0})

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except Exception:
            continue

        tool = evt.get("tool", "")
        if not tool:
            continue

        counts[tool]["calls"] += 1
        result = str(evt.get("result_preview", ""))
        if result.startswith("⚠️") or result.startswith("Error") or "error" in result.lower()[:30]:
            counts[tool]["errors"] += 1

    result: Dict[str, Dict[str, Any]] = {}
    for tool, data in counts.items():
        calls = data["calls"]
        errors = data["errors"]
        success_pct = int(((calls - errors) / calls) * 100) if calls > 0 else 100
        result[tool] = {
            "calls": calls,
            "errors": errors,
            "success_rate_pct": success_pct,
        }

    with _tool_stats_lock:
        _tool_stats_cache = result
        _tool_stats_ts = time.time()

    return result
