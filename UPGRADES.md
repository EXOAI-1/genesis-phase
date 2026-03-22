# GENESIS PHASE — Technical Documentation

> Based on [Ouroboros](https://github.com/razzant/ouroboros) by [razzant](https://github.com/razzant).
>
> Ouroboros provides the core: agent, LLM tool loop, supervisor, Telegram, consciousness engine, BIBLE.md constitution, self-evolution pipeline. GENESIS PHASE adds 8 upgrades + 6 bug fixes on top.

---

## What GENESIS PHASE changes

Every upgrade modifies something the LLM actually reads when making decisions. No decorative features. The principle: **if the LLM ignores it, don't build it.**

The LLM pays attention to exactly three things:
1. **System prompt instructions** — follows these closely
2. **Tool descriptions** — reads before every tool call
3. **Recent context directly relevant to the current task**

All 8 upgrades target one of these three.

---

## Upgrade 1: Past Failure Injection

**File:** `ouroboros/failure_memory.py` (new, 109 lines)  
**Wired in:** `ouroboros/context.py` → `build_llm_messages()`  
**LLM reads it in:** System prompt, "Recent Failures" section

Before every task, reads the last 100 events from `events.jsonl`. If the same task type failed recently, injects a warning:

```
⚠️ RECENT FAILURES (avoid repeating these mistakes):
  [2026-03-20T14:32] direct_chat: timeout after 300s
⚠️ REPEATED TOOL ERRORS (consider alternative approaches):
  (3x) run_shell: command not found
```

Task type normalization handles `""`, `"user"`, `"chat"`, `"direct"` → all map to `"direct_chat"`. Uses tail reader for performance.

---

## Upgrade 2: Live Cost in Conversation

**File:** `ouroboros/loop.py` (15 lines added)

Every 10 rounds, injects a system message:

```
[COST CHECK] Round 10/200. This task has spent $0.12. Budget remaining: $41.88.
If nearly done, wrap up. If stuck, try a different approach.
```

The LLM sees the meter running and wraps up faster on simple tasks.

---

## Upgrade 3: Owner Preferences

**Files:** `ouroboros/context.py` (10 lines), `prompts/CONSCIOUSNESS.md` (20 lines)

File `memory/owner_preferences.md` is injected into every task context. Written by consciousness from observed chat patterns — not hardcoded. Follows BIBLE Principle 3 (LLM-First).

---

## Upgrade 4: Tool Success Rates

**Files:** `ouroboros/tools/registry.py` (30 lines), `ouroboros/task_stats.py`

Tool descriptions get annotated: `"Run a shell command. (⚠️ Recent: 67% success, 5 errors in 15 calls)"`. Computed once per task via cached schemas. Thread-safe. Minimum 5 calls before annotating.

---

## Upgrade 5: Task Outcome Intelligence

**File:** `ouroboros/task_stats.py` (new, 280 lines)

Reads `events.jsonl`, computes per-task-type stats. Consciousness reads the summary every cycle. Tail reader: O(1) file reads regardless of log size.

---

## Upgrade 6: Consciousness Thread

**File:** `ouroboros/consciousness.py` (25 lines)

Tool `update_thought_thread` saves a note for next cycle. Read at start of every thinking cycle. Enables multi-cycle research.

---

## Upgrade 7: Dynamic Round Limits

**File:** `ouroboros/loop.py` (20 lines)

`MAX_ROUNDS = max(10, min(env_max, max_observed * 1.5))`. Chat with max-observed 20 rounds → cap 30 (not 200). Needs 3+ tasks to activate.

---

## Upgrade 8: Test Gate Logging

**File:** `ouroboros/tools/git.py` (15 lines)

Timeout 30s→60s (configurable). Pass/fail logged to events.jsonl. Visible in task stats.

---

## Bug Fixes

| Bug | Severity | Fix |
|-----|----------|-----|
| Consciousness deadlock on hung tool | Critical | `shutdown(wait=False)` on timeout |
| Full-file log reads (O(filesize)) | Medium | Tail reader: seek from end, read 512KB |
| Thread-unsafe tool stats cache | Medium | `threading.Lock()` |
| Non-atomic stats file write | Low | `tmp + os.replace()` |
| Task type normalization | Low | Alias table for 5 variants |
| Magic `avg*3` round cap | Low | `max_observed * 1.5` with `{avg, max, count}` |

---

## File Changes

| File | Status | Lines |
|------|--------|-------|
| `ouroboros/task_stats.py` | NEW | 280 |
| `ouroboros/failure_memory.py` | NEW | 109 |
| `ouroboros/consciousness.py` | MOD | +55 |
| `ouroboros/loop.py` | MOD | +35 |
| `ouroboros/context.py` | MOD | +25 |
| `ouroboros/tools/registry.py` | MOD | +40 |
| `ouroboros/tools/git.py` | MOD | +15 |
| `prompts/CONSCIOUSNESS.md` | MOD | +40 |
| `prompts/SYSTEM.md` | MOD | identity |
| `BIBLE.md` | MOD | identity |

**Total: ~600 lines. No new dependencies.**

---

## Credits

**Ouroboros** by [razzant](https://github.com/razzant): Core agent, tools, supervisor, consciousness, memory, constitution, self-evolution, Colab launcher, tests.

**GENESIS PHASE** by EXOAI-1: 8 upgrades, 6 bug fixes, documentation.

**License:** MIT (same as Ouroboros).
