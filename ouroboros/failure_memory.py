"""
ouroboros/failure_memory.py — Past failure injection.

Reads recent task errors from events.jsonl and builds a short
warning for the LLM context. The LLM reads this before starting
a new task and avoids repeating the same mistakes.

No LLM calls. Pure log parsing.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)


def get_recent_failures(
    drive_root: Path,
    task_type: str = "",
    max_events: int = 100,
    max_failures: int = 3,
) -> str:
    """
    Read recent failures from events.jsonl and return a short warning.
    Returns empty string if no relevant failures found.
    """
    events_path = drive_root / "logs" / "events.jsonl"
    if not events_path.exists():
        return ""

    try:
        from ouroboros.task_stats import _read_tail_lines
        lines = _read_tail_lines(events_path, max_events)
    except Exception:
        return ""

    # Normalize task type for matching
    _TYPE_ALIASES = {
        "": "direct_chat", "user": "direct_chat", "chat": "direct_chat",
        "direct": "direct_chat",
    }
    norm_type = _TYPE_ALIASES.get(task_type, task_type)

    # Collect failures
    failures: List[dict] = []
    tool_errors: List[dict] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except Exception:
            continue

        etype = evt.get("type", "")

        if etype == "task_error":
            evt_type = _TYPE_ALIASES.get(evt.get("task_type", ""), evt.get("task_type", ""))
            # Show if: no filter requested, types match, or event has no type
            if not norm_type or evt_type == norm_type or not evt_type:
                failures.append(evt)

        elif etype in ("tool_error", "tool_rounds_exceeded"):
            tool_errors.append(evt)

    if not failures and not tool_errors:
        return ""

    # Build warning text
    parts = []

    # Task failures (most relevant)
    recent_failures = failures[-max_failures:]
    if recent_failures:
        parts.append("⚠️ RECENT FAILURES (avoid repeating these mistakes):")
        for f in recent_failures:
            error = str(f.get("error", "unknown"))[:150]
            ttype = f.get("task_type", "?")
            ts = str(f.get("ts", ""))[:16]
            parts.append(f"  [{ts}] {ttype}: {error}")

    # Tool errors (pattern detection)
    if tool_errors:
        # Count by tool name
        tool_counts: dict = {}
        for te in tool_errors[-20:]:
            tool = te.get("tool", "?")
            err = str(te.get("error", ""))[:60]
            key = f"{tool}: {err}"
            tool_counts[key] = tool_counts.get(key, 0) + 1

        # Only mention tools that failed 2+ times (pattern, not one-off)
        repeated = {k: v for k, v in tool_counts.items() if v >= 2}
        if repeated:
            parts.append("⚠️ REPEATED TOOL ERRORS (consider alternative approaches):")
            for desc, count in sorted(repeated.items(), key=lambda x: -x[1])[:3]:
                parts.append(f"  ({count}x) {desc}")

    if not parts:
        return ""

    return "\n".join(parts)
