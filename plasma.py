"""
phase/plasma.py — PLASMA: the boss orchestrator.

PLASMA is the central intelligence of the PHASE system.
It coordinates all FLUX nodes, manages the task queue,
monitors results, and self-evolves via GitHub.

Responsibilities:
  1. Goal decomposition — break a user goal into atomic tasks
  2. Task routing      — assign each task to the right FLUX node
  3. Result synthesis  — combine FLUX outputs into a final answer
  4. Node management   — spawn/kill nodes based on queue pressure
  5. Self-evolution    — propose and commit improvements to its own code
  6. Telegram relay    — the only component that talks to the user

Self-evolution flow:
  PLASMA notices an improvement opportunity
       ↓
  Writes proposed change to a temp file
       ↓
  SOLID votes (unanimous required for self-evolution)
       ↓
  If approved → git commit to 'plasma' branch → restart
  If rejected → log feedback, try again next cycle
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Callable, Awaitable, Optional

from config     import cfg, reload_config
import llm as _llm_mod
from llm import register_usage_callback
from state      import state, NodeInfo
from task       import Task, TaskStatus, TaskPriority, task_queue
from solid_engine import solid
from plugin_base import plugin_registry

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("PHASE_DATA_DIR", "data"))
REPO_DIR = Path(os.environ.get("PHASE_REPO_DIR", "."))

# ── Prompts ───────────────────────────────────────────────────────────────────

_DECOMPOSE_PROMPT = """\
You are PLASMA — the orchestrating boss of the PHASE multi-agent system.
You coordinate FLUX nodes: coder, researcher, reviewer, architect.

User goal: {goal}

Available FLUX nodes:
  coder      — writes, edits, debugs code
  researcher — researches, summarises, finds information
  reviewer   — quality-checks and improves outputs
  architect  — designs systems and makes technical decisions (expensive, use sparingly)

Decompose the goal into 1-4 atomic tasks. For each task specify:
  - node_type: which FLUX node handles it
  - task_goal: the specific instruction for that node
  - priority: 1 (urgent) to 4 (low)
  - depends_on: index of task that must complete first (or null)

Output valid JSON only:
{{
  "tasks": [
    {{
      "node_type": "researcher",
      "task_goal": "Research Python asyncio best practices for task queues",
      "priority": 3,
      "depends_on": null
    }},
    {{
      "node_type": "coder",
      "task_goal": "Write an asyncio task queue using the research findings",
      "priority": 2,
      "depends_on": 0
    }}
  ],
  "synthesis_instruction": "Combine the research and code into a complete answer"
}}
"""

_SYNTHESISE_PROMPT = """\
You are PLASMA. All assigned tasks are complete.
Synthesise the results into a single coherent response for the user.

Original user goal: {goal}

Completed task results:
{results}

Synthesis instruction: {instruction}

Write a clear, complete response. Be direct. If there is code, include it.
"""

_EVOLUTION_PROPOSE_PROMPT = """\
You are PLASMA. You are reviewing your own codebase for improvement opportunities.

Current version: {version}

Recent events (last 20):
{events}

Current performance:
  Tasks done: {tasks_done} | Failed: {tasks_failed}
  SOLID approval rate: {approval_rate}%
  Budget remaining: ${budget_remaining:.2f}

Identify ONE specific, valuable improvement to make this cycle.
It must be:
  - Small enough to complete in one cycle (< 50 lines changed)
  - Testable (we can verify it works)
  - Safe (does not break existing functionality)
  - Aligned with principles: LLM-First, Minimalism, Continuity

Output format:
IMPROVEMENT: (one sentence describing what to change)
FILE: (which file to modify)
RATIONALE: (why this improvement matters)
CURRENT_CODE: (the exact current code block to replace, max 20 lines)
PROPOSED_CODE: (the replacement code, max 25 lines)
"""

SendFn = Callable[[str], Awaitable[None]]


class Plasma:
    """
    PLASMA: the boss orchestrator.

    Usage:
        plasma = Plasma(send_telegram=bot.send_message)
        await plasma.start(nodes=[coder_node, researcher_node, reviewer_node])
        await plasma.handle_goal("Build me a Python web scraper")
    """

    def __init__(
        self,
        send_telegram: Optional[SendFn]   = None,
        version:       str                = "1.0.0",
    ):
        self._send     = send_telegram
        self._version  = version
        self._running  = False
        self._nodes:   dict[str, object] = {}   # node_id -> FluxNode
        self._bg_task: Optional[asyncio.Task] = None
        self._evolution_lock = asyncio.Lock()

        # Wire up budget tracking
        register_usage_callback(self._on_spend)

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def start(self, nodes: list) -> None:
        """Start PLASMA and all provided FLUX nodes."""
        await state.load()
        await state.set_plasma_status("online")
        await state.set_plasma_version(self._version)

        # Start all nodes
        for node in nodes:
            await node.start()
            self._nodes[node.node_id] = node
            logger.info("plasma: node started — %s", node.describe())

        # Load plugins
        loaded = plugin_registry.load_all()
        if loaded:
            logger.info("plasma: %d plugin(s) auto-loaded", loaded)

        # Background monitor loop
        self._running  = True
        self._bg_task  = asyncio.create_task(self._background_loop())

        await state.log_event(
            source     = "PLASMA",
            event_type = "system_start",
            message    = f"PHASE online — PLASMA v{self._version} + {len(nodes)} nodes",
        )

        if self._send:
            summary = state.summary()
            node_list = ", ".join(
                n.node_type for n in nodes
            )
            await self._send(
                f"⚡ *PHASE online*\n\n"
                f"PLASMA v{self._version}\n"
                f"FLUX nodes: {node_list}\n"
                f"SOLID validators: 3 active\n"
                f"Budget: ${summary['budget']['total']:.0f}\n\n"
                f"Send me a goal."
            )

        logger.info("plasma: PHASE online — %d nodes active", len(nodes))

    async def stop(self) -> None:
        """Graceful shutdown."""
        self._running = False
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()

        for node in self._nodes.values():
            try:
                await node.stop()
            except Exception:
                pass

        await state.set_plasma_status("offline")
        logger.info("plasma: PHASE offline")

    # ── Goal handling ──────────────────────────────────────────────────────────

    async def handle_goal(self, goal: str) -> str:
        """
        Main entry point. User sends a goal, PLASMA orchestrates.
        Returns the final synthesised answer.
        """
        await state.log_event(
            source="PLASMA", event_type="goal_received",
            message=f"Goal: {goal[:100]}"
        )

        if self._send:
            await self._send(f"⚡ Decomposing goal into tasks…")

        # 1. Decompose goal into tasks
        try:
            tasks, synth_instruction = await self._decompose(goal)
        except Exception as exc:
            error_msg = f"Goal decomposition failed: {exc}"
            logger.error("plasma: %s", error_msg)
            if self._send:
                await self._send(f"⚠️ {error_msg}")
            return error_msg

        if not tasks:
            # Simple goal — route directly to best node
            tasks = [Task(
                goal=goal, node_type="coder", priority=TaskPriority.NORMAL
            )]
            synth_instruction = "Return the result directly."

        if self._send:
            await self._send(
                f"📋 {len(tasks)} task(s) assigned:\n" +
                "\n".join(f"  · [{t.node_type}] {t.goal[:60]}…" for t in tasks)
            )

        # 2. Enqueue tasks and wait for results
        results = await self._run_tasks(tasks, goal)

        # 3. Synthesise
        final = await self._synthesise(goal, results, synth_instruction)

        await state.log_event(
            source="PLASMA", event_type="goal_completed",
            message=f"Goal completed: {goal[:60]}"
        )

        return final

    async def _decompose(self, goal: str) -> tuple[list[Task], str]:
        """Ask PLASMA (coordination model) to break goal into tasks."""
        import json

        prompt = _DECOMPOSE_PROMPT.format(goal=goal[:600])
        raw    = await _llm_mod.call_llm(
            model      = cfg.plasma.coordination,
            messages   = [{"role": "user", "content": prompt}],
            max_tokens = 600,
            tag        = "plasma_decompose",
        )

        # Strip markdown fences
        raw = (raw or "").strip()
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    raw = part[4:].strip()
                    break
                elif part.startswith("{"):
                    raw = part
                    break
        # Find JSON object
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]

        try:
            data   = json.loads(raw)
            tasks  = []
            synth  = data.get("synthesis_instruction", "Combine results into a clear answer.")

            for item in data.get("tasks", []):
                tasks.append(Task(
                    goal      = item.get("task_goal", goal),
                    node_type = item.get("node_type", "coder"),
                    priority  = int(item.get("priority", TaskPriority.NORMAL)),
                ))
            return tasks, synth

        except Exception:
            return [], "Return the result directly."

    async def _run_tasks(self, tasks: list[Task], goal: str) -> list[dict]:
        """Enqueue all tasks and wait for completion."""
        for task in tasks:
            await task_queue.put(task)

        results   = []
        deadline  = time.time() + cfg.timeouts.node_task_seconds * len(tasks)
        task_ids  = {t.task_id for t in tasks}
        completed = set()

        while len(completed) < len(task_ids) and time.time() < deadline:
            await asyncio.sleep(1.0)
            for tid in task_ids - completed:
                t = task_queue.get_task(tid)
                if t and t.is_terminal():
                    completed.add(tid)
                    if t.result:
                        results.append({
                            "node_type": t.node_type,
                            "goal":      t.goal,
                            "result":    t.result,
                            "status":    t.status.value,
                        })
                    elif t.error:
                        results.append({
                            "node_type": t.node_type,
                            "goal":      t.goal,
                            "result":    f"[FAILED: {t.error}]",
                            "status":    t.status.value,
                        })

            if self._send and len(completed) > 0 and len(completed) < len(task_ids):
                pass  # Could add progress updates here

        return results

    async def _synthesise(
        self, goal: str, results: list[dict], instruction: str
    ) -> str:
        """Combine all FLUX results into a final answer."""
        if not results:
            return "No results were produced. All tasks may have failed."

        results_text = "\n\n".join(
            f"[{r['node_type'].upper()}] {r['goal']}\n{r['result']}"
            for r in results
        )

        prompt = _SYNTHESISE_PROMPT.format(
            goal        = goal[:400],
            results     = results_text[:3000],
            instruction = instruction,
        )

        return await _llm_mod.call_llm(
            model      = cfg.plasma.coordination,
            messages   = [{"role": "user", "content": prompt}],
            max_tokens = 1500,
            tag        = "plasma_synthesise",
        ) or "Synthesis failed — raw results:\n" + results_text[:500]

    # ── Self-evolution ─────────────────────────────────────────────────────────

    async def propose_evolution(self) -> Optional[str]:
        """
        PLASMA examines itself and proposes one improvement.
        Returns commit SHA if successful, None otherwise.
        """
        async with self._evolution_lock:
            await state.set_plasma_status("evolving")
            await state.log_event(
                source="PLASMA", event_type="evolution_start",
                message="Starting self-evolution cycle"
            )

            try:
                result = await self._do_evolution()
            finally:
                await state.set_plasma_status("online")

            return result

    async def _do_evolution(self) -> Optional[str]:
        import json

        summary = state.summary()
        events  = state.recent_events(20)
        events_text = "\n".join(
            f"[{e['source']}] {e['event_type']}: {e['message']}"
            for e in events
        )

        # Ask PLASMA (strategic model) what to improve
        prompt = _EVOLUTION_PROPOSE_PROMPT.format(
            version         = self._version,
            events          = events_text[:1500],
            tasks_done      = summary["tasks"]["done"],
            tasks_failed    = summary["tasks"]["failed"],
            approval_rate   = summary["solid"]["approval_rate"],
            budget_remaining= summary["budget"]["remaining"],
        )

        raw = await _llm_mod.call_llm(
            model      = cfg.plasma.strategic,
            messages   = [{"role": "user", "content": prompt}],
            max_tokens = 800,
            tag        = "plasma_evolve",
        )
        if not raw:
            return None

        # Parse proposal
        lines         = raw.strip().split("\n")
        proposal      = {}
        current_key   = None
        current_lines = []

        for line in lines:
            for key in ["IMPROVEMENT", "FILE", "RATIONALE",
                        "CURRENT_CODE", "PROPOSED_CODE"]:
                if line.startswith(f"{key}:"):
                    if current_key:
                        proposal[current_key] = "\n".join(current_lines).strip()
                    current_key   = key
                    current_lines = [line[len(key)+1:].strip()]
                    break
            else:
                if current_key:
                    current_lines.append(line)

        if current_key:
            proposal[current_key] = "\n".join(current_lines).strip()

        improvement   = proposal.get("IMPROVEMENT", "")
        target_file   = proposal.get("FILE", "")
        current_code  = proposal.get("CURRENT_CODE", "")
        proposed_code = proposal.get("PROPOSED_CODE", "")

        if not improvement or not proposed_code:
            logger.warning("plasma: evolution proposal incomplete")
            return None

        # SOLID votes — unanimous required for self-evolution
        validation = await solid.validate_evolution(
            description   = improvement,
            current_code  = current_code,
            proposed_code = proposed_code,
        )

        if not validation.approved:
            msg = f"Evolution rejected by SOLID: {validation.feedback[:120]}"
            logger.info("plasma: %s", msg)
            await state.log_event(
                source="PLASMA", event_type="evolution_rejected",
                message=msg
            )
            if self._send:
                await self._send(f"🔴 Evolution proposal rejected:\n{validation.feedback[:200]}")
            return None

        # Apply the change
        sha = await self._apply_evolution(
            target_file   = target_file,
            current_code  = current_code,
            proposed_code = proposed_code,
            improvement   = improvement,
        )

        if sha and self._send:
            await self._send(
                f"🧬 *PLASMA evolved*\n\n"
                f"{improvement}\n\n"
                f"Commit: `{sha[:8]}`\n"
                f"SOLID consensus: {validation.consensus}"
            )

        return sha

    async def _apply_evolution(
        self,
        target_file:   str,
        current_code:  str,
        proposed_code: str,
        improvement:   str,
    ) -> Optional[str]:
        """Apply approved evolution to the codebase and commit."""
        try:
            file_path = REPO_DIR / target_file
            if not file_path.exists() or not current_code:
                return None

            content = file_path.read_text()
            if current_code not in content:
                logger.warning("plasma: current_code not found in %s", target_file)
                return None

            new_content = content.replace(current_code, proposed_code, 1)
            file_path.write_text(new_content)

            # Commit to plasma branch
            branch  = "plasma"
            version = self._bump_version()

            cmds = [
                ["git", "checkout", "-B", branch],
                ["git", "add", target_file],
                ["git", "commit", "-m",
                 f"PLASMA evolve v{version}: {improvement[:60]}"],
                ["git", "push", "origin", branch, "--force"],
            ]
            for cmd in cmds:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=REPO_DIR
                )
                if result.returncode != 0:
                    logger.warning("plasma: git cmd failed: %s", result.stderr[:100])
                    break

            # Get SHA
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=REPO_DIR
            )
            sha = sha_result.stdout.strip()[:8]

            await state.set_plasma_version(version)
            self._version = version
            await state.log_event(
                source="PLASMA", event_type="evolution_committed",
                message=f"v{version}: {improvement[:80]}",
                metadata={"sha": sha, "file": target_file},
            )

            return sha

        except Exception as exc:
            logger.error("plasma: evolution apply failed: %s", exc)
            return None

    def _bump_version(self) -> str:
        parts = self._version.split(".")
        try:
            parts[-1] = str(int(parts[-1]) + 1)
        except (ValueError, IndexError):
            parts = ["1", "0", "1"]
        return ".".join(parts)

    # ── Background monitor loop ────────────────────────────────────────────────

    async def _background_loop(self) -> None:
        """
        Lightweight background monitor:
        - Watches for stuck tasks (timeout)
        - Considers evolution every hour
        """
        last_evolution = time.time()
        EVOLUTION_INTERVAL = 3600   # 1 hour

        while self._running:
            try:
                await asyncio.sleep(30)

                # Consider evolution
                if time.time() - last_evolution > EVOLUTION_INTERVAL:
                    logger.info("plasma: starting scheduled evolution")
                    await self.propose_evolution()
                    last_evolution = time.time()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("plasma: bg loop error: %s", exc)

    # ── Telegram command helpers ───────────────────────────────────────────────

    async def handle_phase_status(self) -> str:
        summary = state.summary()
        nodes   = summary["nodes"]["list"]
        node_lines = "\n".join(
            f"  · {n.get('node_type','?')} [{n.get('status','?')}] "
            f"tasks={n.get('tasks_done',0)}"
            for n in nodes
        ) or "  (none)"

        return (
            f"⚡ *PHASE Status*\n\n"
            f"PLASMA v{summary['plasma_version']} — {summary['plasma_status']}\n\n"
            f"*Budget*\n"
            f"  Spent: ${summary['budget']['spent']:.4f} / "
            f"${summary['budget']['total']:.0f} "
            f"({summary['budget']['pct_used']:.1f}%)\n\n"
            f"*Tasks*\n"
            f"  Done: {summary['tasks']['done']} | "
            f"Failed: {summary['tasks']['failed']} | "
            f"Pending: {task_queue.pending_count()}\n\n"
            f"*SOLID*\n"
            f"  Approval rate: {summary['solid']['approval_rate']}% "
            f"({summary['solid']['approved']}/{summary['solid']['total']})\n\n"
            f"*FLUX nodes*\n{node_lines}"
        )

    async def handle_evolve_command(self) -> str:
        if self._evolution_lock.locked():
            return "Evolution already in progress."
        asyncio.create_task(self.propose_evolution())
        return "🧬 Evolution cycle started. SOLID will vote on the proposal."

    # ── Internal ───────────────────────────────────────────────────────────────

    def _on_spend(self, tag: str, cost: float, _pt: int, _ct: int) -> None:
        asyncio.create_task(state.record_spend(tag, cost))
