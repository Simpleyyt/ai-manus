"""Wide Research — Manus 2.0 parallel research flow.

This flow implements the "Wide Research" capability described in Manus docs:
decomposes a request into independent sub-tasks, runs multiple agents in
parallel with clean context, and synthesizes results into a structured table
+ report. See https://manus.im/features/wide-research and
https://manus.im/docs/features/wide-research

In the open-source replica, Wide Research is limited to 3-5 parallel agents
to stay within free-tier quotas (as per "Como montar um Manus gratuito" §6).

Architecture:
    Task (e.g. "compare 100 products")
      ↓
    Coordinator (splits into N sub-tasks)
      ↓
    Fan-out: N ExecutionAgents in parallel (asyncio.gather)
      ↓
    Aggregator: ManusAgent synthesizes results → final deliverable

This file provides the domain model + flow, wired via PlanActFlow when a plan
step is tagged with `wide_research: true`.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, List, Optional

from app.domain.external.browser import Browser
from app.domain.external.llm import LLM
from app.domain.external.sandbox import Sandbox
from app.domain.external.search import SearchEngine
from app.domain.models.event import BaseEvent, MessageEvent, ToolEvent
from app.domain.models.message import Message
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.session_repository import SessionRepository
from app.domain.services.agents.execution import ExecutionAgent
from app.domain.services.tools.browser import BrowserToolkit
from app.domain.services.tools.file import FileToolkit
from app.domain.services.tools.mcp import MCPToolkit
from app.domain.services.tools.search import SearchToolkit
from app.domain.services.tools.shell import ShellToolkit

logger = logging.getLogger(__name__)


@dataclass
class WideResearchTask:
    """A single independent sub-task for parallel execution."""

    id: str
    query: str
    description: str


@dataclass
class WideResearchResult:
    """Aggregated result from parallel research."""

    task_id: str
    query: str
    summary: str
    files: List[str]


class WideResearchCoordinator:
    """Decomposes a task and runs sub-agents in parallel."""

    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        llm: LLM,
        sandbox: Sandbox,
        browser: Browser,
        mcp_tool: MCPToolkit,
        search_engine: Optional[SearchEngine] = None,
        max_parallel: int = 3,
    ):
        self.agent_id = agent_id
        self.agent_repository = agent_repository
        self.llm = llm
        self.sandbox = sandbox
        self.browser = browser
        self.mcp_tool = mcp_tool
        self.search_engine = search_engine
        self.max_parallel = max_parallel

    def decompose(self, goal: str, items: List[str]) -> List[WideResearchTask]:
        """Split a goal into parallel sub-tasks, one per item or batch."""
        tasks = []
        for idx, item in enumerate(items):
            tasks.append(
                WideResearchTask(
                    id=f"wr-{idx}",
                    query=item,
                    description=f"Research '{item}' for goal: {goal}. Save findings to /workspace/wide_research/{idx}.md",
                )
            )
        return tasks

    async def _run_single(self, task: WideResearchTask) -> WideResearchResult:
        """Run a single sub-task with a clean ExecutionAgent context."""
        tools = [
            ShellToolkit(self.sandbox),
            BrowserToolkit(self.browser),
            FileToolkit(self.sandbox),
        ]
        if self.search_engine:
            tools.append(SearchToolkit(self.search_engine))
        tools.append(self.mcp_tool)

        agent = ExecutionAgent(
            agent_id=f"{self.agent_id}-wr-{task.id}",
            agent_repository=self.agent_repository,
            llm=self.llm,
            tools=tools,
        )

        # Build a minimal plan with one step for this sub-task
        from app.domain.models.plan import Plan, Step, ExecutionStatus

        plan = Plan(
            title=f"Wide Research: {task.query}",
            goal=task.description,
            steps=[Step(description=task.description, status=ExecutionStatus.PENDING)],
        )

        message = Message(message=task.description)
        summary_parts: List[str] = []

        async for event in agent.execute_step(plan, plan.steps[0], message):
            if isinstance(event, MessageEvent):
                summary_parts.append(event.message)
            elif isinstance(event, ToolEvent):
                # Collect tool observations for synthesis
                if event.function_result and hasattr(event.function_result, "message"):
                    summary_parts.append(str(event.function_result.message))

        return WideResearchResult(
            task_id=task.id,
            query=task.query,
            summary="\n".join(summary_parts)[:4000],
            files=[f"/workspace/wide_research/{task.id}.md"],
        )

    async def run_parallel(
        self, tasks: List[WideResearchTask]
    ) -> AsyncGenerator[BaseEvent, None]:
        """Run all sub-tasks in parallel batches, yielding progress events."""
        yield MessageEvent(message=f"🔬 Wide Research: launching {len(tasks)} parallel agents...")

        # Batch to respect max_parallel limit (quota protection)
        for batch_start in range(0, len(tasks), self.max_parallel):
            batch = tasks[batch_start : batch_start + self.max_parallel]
            yield MessageEvent(
                message=f"Batch {batch_start // self.max_parallel + 1}: researching {len(batch)} items in parallel"
            )

            results: List[WideResearchResult] = await asyncio.gather(
                *(self._run_single(t) for t in batch)
            )

            for r in results:
                yield MessageEvent(
                    message=f"✓ Completed: {r.query} → {r.files[0]} ({len(r.summary)} chars)"
                )

        yield MessageEvent(message="Wide Research fan-out complete — synthesizing...")

    async def synthesize(
        self,
        goal: str,
        results: List[WideResearchResult],
    ) -> str:
        """Ask LLM to synthesize parallel results into a structured report."""
        context = "\n\n".join(f"## {r.query}\n{r.summary}" for r in results)
        synthesis_prompt = (
            f"Goal: {goal}\n\n"
            f"You have collected parallel research on {len(results)} items:\n\n"
            f"{context}\n\n"
            "Synthesize into a markdown table with key attributes, notable patterns, "
            "and top recommendations. Save to /workspace/wide_research_report.md "
            "and return the markdown."
        )

        # Use sandbox to save synthesis via shell
        shell = ShellToolkit(self.sandbox)
        # We delegate synthesis to the LLM via a direct call; for now save a summary file
        import json

        save_code = f"""
import pathlib
path = pathlib.Path('/workspace/wide_research_report.md')
path.parent.mkdir(parents=True, exist_ok=True)
content = '''# Wide Research Report

**Goal:** {goal}

## Summary Table

| Item | Key Findings |
|------|--------------|
'''
for r in results:
    save_code += f"| {r.query} | See {r.files[0]} |\\n"

save_code += '''
## Detailed Findings

'''
for r in results:
    save_code += f"### {r.query}\\n{r.summary[:500]}\\n\\n"

save_code += '''
---
*Generated by Landis AI Wide Research — {len(results)} parallel agents*
'''
path.write_text(content, encoding='utf-8')
print(f"Saved {{path}} ({{path.stat().st_size}} bytes)")
"""

        # Execute synthesis save via sandbox shell
        try:
            # Use the sandbox's shell interface directly
            from app.domain.models.sandbox.shell import ShellExecRequest

            await self.sandbox.exec_shell(
                ShellExecRequest(command=f"python3 << 'PYEOF'\n{save_code}\nPYEOF", session_id="wide-research-synth")
            )
        except Exception as e:
            logger.warning(f"Wide research synthesis save failed: {e}")

        return synthesis_prompt
