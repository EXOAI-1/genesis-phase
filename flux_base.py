"""
flux/flux_base.py — Base class for all FLUX nodes.

Every FLUX node subclasses FluxNode and implements execute().
The base handles: task polling, status tracking, budget tracking,
SOLID validation, retry logic, and graceful shutdown.

To create a new node type, subclass FluxNode and implement:
  - node_type:     class-level string e.g. "coder"
  - system_prompt: class-level string describing the node's role
  - async execute(task) -> str: the actual work

See flux_coder.py for a complete example.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)

POLL_INTERVAL = float(os.environ.get("PHASE_FLUX_POLL_SECONDS", "2.0"))


class FluxNode(ABC):

    node_type:     str = "base"
    system_prompt: str = "You are a FLUX node in the PHASE system."

    def __init__(self):
        self.node_id   = f"FLUX:{self.node_type}:{uuid.uuid4().hex[:6]}"
        self._running  = False
        self._task:    Optional[asyncio.Task] = None

    @property
    def model(self) -> str:
        from config import cfg
        return cfg.flux_model(self.node_type)

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        import state as _s
        from state import NodeInfo
        await _s.state.register_node(NodeInfo(
            node_id   = self.node_id,
            node_type = self.node_type,
            model     = self.model,
            status    = "idle",
        ))
        self._task = asyncio.create_task(self._loop())
        logger.info("flux: %s started", self.node_id)
        await _s.state.log_event(
            source     = self.node_id,
            event_type = "node_started",
            message    = f"{self.node_type} node online",
            metadata   = {"model": self.model},
        )

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await asyncio.shield(self._task)
            except (asyncio.CancelledError, Exception):
                pass
        import state as _s
        try:
            await _s.state.update_node_status(self.node_id, "stopped")
        except Exception:
            pass
        logger.info("flux: %s stopped", self.node_id)

    @property
    def is_running(self) -> bool:
        return self._running and bool(self._task) and not self._task.done()

    # ── Main loop ──────────────────────────────────────────────────────────────

    async def _loop(self) -> None:
        import task as _t
        import state as _s
        while self._running:
            try:
                task = await _t.task_queue.get_for_node(
                    self.node_type, timeout=POLL_INTERVAL
                )
                if task is None:
                    continue
                await _s.state.update_node_status(self.node_id, "busy")
                await _s.state.task_assigned()
                await self._process(task)
                await _s.state.update_node_status(self.node_id, "idle")
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("flux: %s loop error: %s", self.node_id, exc)
                await asyncio.sleep(2)

    async def _process(self, task) -> None:
        import task as _t
        import state as _s
        import solid_engine as _sol

        task.attempts += 1
        await _t.task_queue.update(task.task_id, status=_t.TaskStatus.IN_PROGRESS)
        await _s.state.log_event(
            source=self.node_id, event_type="task_started",
            message=f"Working on: {task.goal[:80]}",
            metadata={"task_id": task.task_id, "attempt": task.attempts},
        )

        try:
            output = await self.execute(task)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("flux: %s execute error: %s", self.node_id, exc)
            output = ""

        if not output:
            await self._mark_failed(task, "Node returned empty output")
            return

        await _t.task_queue.update(task.task_id, status=_t.TaskStatus.AWAITING_VALIDATION)
        validation = await _sol.solid.validate_task_result(task, output)

        if validation.approved:
            import time
            await _t.task_queue.update(
                task.task_id, status=_t.TaskStatus.DONE,
                result=output, completed_at=time.time(),
            )
            await _s.state.task_completed(self.node_id, success=True)
            await _s.state.log_event(
                source=self.node_id, event_type="task_done",
                message=f"Approved ({validation.consensus})",
                metadata={"task_id": task.task_id, "consensus": validation.consensus},
            )
            logger.info("flux: %s DONE [%s]", self.node_id, task.task_id)
        else:
            if task.can_retry():
                logger.info("flux: %s retrying [%s]", self.node_id, task.task_id)
                task.context["solid_feedback"] = validation.feedback
                await _t.task_queue.put(task)
            else:
                await self._mark_failed(task, validation.feedback)

    async def _mark_failed(self, task, reason: str) -> None:
        import task as _t
        import state as _s
        import time
        await _t.task_queue.update(
            task.task_id, status=_t.TaskStatus.FAILED,
            error=reason, completed_at=time.time(),
        )
        await _s.state.task_completed(self.node_id, success=False)
        logger.warning("flux: %s FAILED [%s]", self.node_id, task.task_id)

    # ── LLM helper ────────────────────────────────────────────────────────────

    async def llm(self, user_message: str, max_tokens: int = 1000,
                  temperature: float = 0.7, extra_context: str = "") -> str:
        from llm import call_llm
        from config import cfg
        system = self.system_prompt
        if extra_context:
            system += f"\n\n{extra_context}"
        return await call_llm(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_message},
            ],
            max_tokens=max_tokens, temperature=temperature,
            tag=self.node_type, fallback_models=cfg.fallback,
        )

    @abstractmethod
    async def execute(self, task) -> str: ...

    def describe(self) -> str:
        status = "running" if self.is_running else "stopped"
        return f"{self.node_type} node [{self.node_id}] model={self.model} status={status}"
