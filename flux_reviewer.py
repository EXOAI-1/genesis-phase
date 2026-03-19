"""
flux/flux_reviewer.py — Reviewer FLUX node.

Handles quality review of other nodes' outputs.
Checks correctness, clarity, completeness, and safety.

Model: NANO (Gemini Flash by default)
Max rounds: 15
Always spawned: yes

Note: The Reviewer is a FLUX node — it does the work.
SOLID is the validation layer. These are distinct roles:
  - Reviewer: deep quality analysis, suggestions, rewrite
  - SOLID: binary approve/reject gate with feedback

PLASMA may assign a task to Reviewer AFTER Coder has produced output,
creating a Coder → Reviewer pipeline for high-stakes tasks.
"""

from __future__ import annotations

from task import Task
from flux_base import FluxNode


class ReviewerNode(FluxNode):

    node_type = "reviewer"

    system_prompt = """\
You are the Reviewer FLUX node in the PHASE multi-agent system.
You review, critique, and improve outputs from other nodes.

Core responsibilities:
- Check outputs for correctness, completeness, and clarity
- Identify bugs, logical errors, or missing edge cases
- Suggest specific, actionable improvements
- Rewrite or correct the output if needed

Output format:
ASSESSMENT: (one line — pass / needs improvement / fail)
ISSUES: (list any problems found)
IMPROVED OUTPUT: (the corrected/improved version, or "No changes needed")
NOTES: (any important caveats)

Be honest and specific. Vague feedback is useless.
"""

    async def execute(self, task: Task) -> str:
        feedback = task.context.get("solid_feedback", "")
        feedback_block = (
            f"\n\nPREVIOUS REVIEW WAS REJECTED. Validator feedback:\n{feedback}\n"
            if feedback else ""
        )

        # task.context may include the original output to review
        original_output = task.context.get("original_output", "")
        context_block   = (
            f"\n\nORIGINAL OUTPUT TO REVIEW:\n{original_output}\n"
            if original_output else ""
        )

        prompt = f"Review the following:\n\n{task.goal}{context_block}{feedback_block}"

        return await self.llm(
            user_message = prompt,
            max_tokens   = 1000,
            temperature  = 0.2,   # very low — review needs consistency
        )
