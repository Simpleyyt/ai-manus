# Planner + Authoritative Plan Progress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire Agent-mode so Plan panel is driven only by **authoritative** structured events (`Planner.create_plan` / `plan_report` / `replan`→`update_plan` / `COMPLETED`), while Manus stays a single tool loop and `todo.md` is never parsed into Plan UI.

**Architecture:** `AgentLoopFlow` owns the canonical `Plan`, runs `PlannerAgent.create_plan` first, injects the plan into `ManusAgent`, then runs one Manus loop. Mid-run progress applies via `plan_report` (status snapshot → `PlanEvent`/`StepEvent`). Significant changes use `replan` → existing `PlannerAgent.update_plan`. File writes to `todo.md` remain normal file tools (attention only).

**Tech Stack:** Python 3.12, existing `PlannerAgent` / `ManusAgent` / `BaseToolkit` / Pydantic v2, pytest unit tests (no live server).

**Spec:** `docs/superpowers/specs/2026-08-09-planner-single-loop-manus-design.md`

## Global Constraints

- Plan UI source of truth = structured plan events only (Planner + `plan_report` + `replan`). **Never** parse `todo.md` checklists into Plan/Step.
- Do **not** restore `todo_write` / `TodoToolkit`.
- Do **not** revert to full `PlanActFlow` (no forced `update_plan` after every executor step; no per-step `ExecutionAgent`).
- Keep Chat/Lite paths unchanged.
- Suppress timeline/Computer rows for `plan_report` / `replan` (Plan panel is enough).
- At most one step `RUNNING` after each `plan_report`.
- Memory keys: Planner `"planner"`, Manus `"manus"`.
- Do **not** commit unless the user explicitly asks.
- Verify: `cd backend && uv run pytest tests/test_plan_progress.py tests/test_single_loop_manus.py -v`

## File structure

| File | Responsibility |
|------|----------------|
| `backend/app/domain/models/agent_output.py` | Add `PlanReportOutput`, `ReplanOutput` |
| `backend/app/domain/services/plan_progress.py` | Pure: apply status snapshot / mark first running / complete plan |
| `backend/app/domain/services/tools/plan.py` | `PlanToolkit`: `plan_report`, `replan` |
| `backend/app/domain/services/flows/agent_loop.py` | Planner → Manus orchestration; intercept progress tools |
| `backend/app/domain/services/agents/manus.py` | Accept injected plan text; suppress progress tool events in fan-out |
| `backend/app/domain/services/prompts/manus.py` | Authoritative plan + optional `todo.md` sync rules |
| `backend/app/domain/services/tools/file.py` | Soften `todo.md` blurb (attention / rebuild after replan) |
| `frontend/src/composables/useAgentEvents.ts` | Ignore `plan_report` / `replan` tool rows (defense in depth) |
| `backend/tests/test_plan_progress.py` | Pure progress helpers |
| `backend/tests/test_single_loop_manus.py` | Flow + Manus integration with ScriptedLLM |

---

### Task 1: `PlanReportOutput` + pure progress helpers

**Files:**
- Modify: `backend/app/domain/models/agent_output.py`
- Create: `backend/app/domain/services/plan_progress.py`
- Create: `backend/tests/test_plan_progress.py`

**Interfaces:**
- Consumes: `Plan`, `Step`, `ExecutionStatus`, `PlanEvent`, `StepEvent`, `PlanStatus`, `StepStatus`
- Produces:
  - `PlanStepStatusUpdate(id: str, status: ExecutionStatus, reflection: str | None = None)`
  - `PlanReportOutput(steps: list[PlanStepStatusUpdate], reflection: str = "")`
  - `ReplanOutput(reason: str)`
  - `mark_first_step_running(plan: Plan) -> Plan`
  - `apply_plan_report(plan: Plan, report: PlanReportOutput) -> list[BaseEvent]`
  - `complete_plan(plan: Plan) -> Plan` (mark unfinished non-failed steps completed success=True)

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_plan_progress.py
from app.domain.models.plan import Plan, Step, ExecutionStatus
from app.domain.models.event import PlanEvent, PlanStatus, StepEvent, StepStatus
from app.domain.models.agent_output import PlanReportOutput, PlanStepStatusUpdate
from app.domain.services.plan_progress import (
    mark_first_step_running,
    apply_plan_report,
    complete_plan,
)


def test_mark_first_step_running():
    plan = Plan(steps=[
        Step(id="1", description="A"),
        Step(id="2", description="B"),
    ])
    out = mark_first_step_running(plan)
    assert out.steps[0].status == ExecutionStatus.RUNNING
    assert out.steps[1].status == ExecutionStatus.PENDING


def test_apply_plan_report_updates_and_emits_step_events():
    plan = Plan(
        title="T",
        goal="G",
        steps=[
            Step(id="1", description="A", status=ExecutionStatus.RUNNING),
            Step(id="2", description="B", status=ExecutionStatus.PENDING),
        ],
    )
    report = PlanReportOutput(
        steps=[
            PlanStepStatusUpdate(id="1", status=ExecutionStatus.COMPLETED),
            PlanStepStatusUpdate(id="2", status=ExecutionStatus.RUNNING),
        ],
        reflection="Finished research",
    )
    events = apply_plan_report(plan, report)
    assert plan.steps[0].status == ExecutionStatus.COMPLETED
    assert plan.steps[0].success is True
    assert plan.steps[1].status == ExecutionStatus.RUNNING
    assert any(isinstance(e, PlanEvent) and e.status == PlanStatus.UPDATED for e in events)
    assert any(isinstance(e, StepEvent) and e.status == StepStatus.COMPLETED for e in events)
    assert any(isinstance(e, StepEvent) and e.status == StepStatus.STARTED for e in events)


def test_apply_plan_report_enforces_single_running():
    plan = Plan(steps=[
        Step(id="1", description="A", status=ExecutionStatus.PENDING),
        Step(id="2", description="B", status=ExecutionStatus.PENDING),
    ])
    report = PlanReportOutput(steps=[
        PlanStepStatusUpdate(id="1", status=ExecutionStatus.RUNNING),
        PlanStepStatusUpdate(id="2", status=ExecutionStatus.RUNNING),
    ])
    apply_plan_report(plan, report)
    running = [s for s in plan.steps if s.status == ExecutionStatus.RUNNING]
    assert len(running) == 1
    assert running[0].id == "2"  # last RUNNING in report wins


def test_complete_plan_marks_open_steps_done():
    plan = Plan(steps=[
        Step(id="1", description="A", status=ExecutionStatus.COMPLETED, success=True),
        Step(id="2", description="B", status=ExecutionStatus.RUNNING),
    ])
    out = complete_plan(plan)
    assert out.steps[1].status == ExecutionStatus.COMPLETED
    assert out.steps[1].success is True
    assert out.status == ExecutionStatus.COMPLETED
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd backend && uv run pytest tests/test_plan_progress.py -v
```

Expected: import / missing symbol failures.

- [ ] **Step 3: Implement models + helpers**

Add to `agent_output.py`:

```python
class PlanStepStatusUpdate(BaseModel):
    id: str = Field(description="Existing plan step id")
    status: ExecutionStatus = Field(
        description="pending | running | completed | failed"
    )
    reflection: str | None = Field(
        default=None,
        description="Optional short note for this step transition",
    )


class PlanReportOutput(BaseModel):
    """Arguments of the ``plan_report`` tool (authoritative Plan UI progress)."""

    steps: List[PlanStepStatusUpdate] = Field(
        description="Full status snapshot for known step ids (include every step)"
    )
    reflection: str = Field(
        default="",
        description="Optional short overall reflection for this progress update",
    )


class ReplanOutput(BaseModel):
    """Arguments of the ``replan`` tool."""

    reason: str = Field(
        min_length=1,
        description="Why the remaining plan must change",
    )
```

Note: import `ExecutionStatus` from `app.domain.models.plan` into `agent_output.py`, or use a string enum mirrored in the report model and map inside `apply_plan_report`. Prefer importing `ExecutionStatus` if it does not create a cycle; if it does, use `Literal["pending","running","completed","failed"]` on the report model and map in `plan_progress.py`.

`plan_progress.py` behavior:

- `mark_first_step_running`: copy-on-write or mutate first pending/running step to RUNNING; return plan.
- `apply_plan_report`: for each update id present in plan, set status; if COMPLETED set `success=True` unless status FAILED (`success=False`); if multiple RUNNING, keep only the last reported RUNNING and set earlier reported RUNNING back to PENDING; store top-level `reflection` on the last touched step’s `result` if empty optional; emit UPDATED PlanEvent + STARTED/COMPLETED StepEvents by comparing previous statuses (same spirit as old `project_todo_write`).
- Unknown step ids in the report: ignore (do not crash).
- `complete_plan`: set plan.status COMPLETED; any step not already COMPLETED/FAILED → COMPLETED success=True.

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd backend && uv run pytest tests/test_plan_progress.py -v
```

---

### Task 2: `PlanToolkit` (`plan_report`, `replan`)

**Files:**
- Create: `backend/app/domain/services/tools/plan.py`
- Modify: `backend/tests/test_plan_progress.py` (add toolkit smoke test) or keep toolkit covered by flow tests only

**Interfaces:**
- Consumes: `BaseToolkit`, `tool`, `ToolResult`, `PlanReportOutput`, `ReplanOutput`
- Produces: `PlanToolkit` with `name = "plan"`, tools `plan_report`, `replan`

- [ ] **Step 1: Implement toolkit**

```python
# backend/app/domain/services/tools/plan.py
from app.domain.models.agent_output import PlanReportOutput, ReplanOutput
from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, tool


class PlanToolkit(BaseToolkit):
    name = "plan"
    instructions = """
- The product Plan panel is authoritative and separate from todo.md.
- After finishing or starting a planned step, call plan_report with a FULL
  status snapshot for every known step id (pending|running|completed|failed).
  Keep at most one step running.
- Call replan with a clear reason when remaining steps no longer fit reality;
  then rebuild /home/ubuntu/todo.md to match the new plan (attention only).
- Do not invent Plan UI updates by only editing todo.md.
"""

    @tool(parse_docstring=True)
    async def plan_report(self, steps: list[dict], reflection: str = "") -> ToolResult:
        """Update authoritative plan step statuses for the Plan panel.

        Args:
            steps: Full list of {id, status} (optional reflection per step).
            reflection: Optional short overall reflection.
        """
        parsed = PlanReportOutput.model_validate(
            {"steps": steps, "reflection": reflection or ""}
        )
        return ToolResult(
            success=True,
            message="Plan progress recorded",
            data=parsed.model_dump(mode="json"),
        )

    @tool(parse_docstring=True)
    async def replan(self, reason: str) -> ToolResult:
        """Request Planner to rewrite remaining steps.

        Args:
            reason: Why the current remaining plan is wrong or incomplete.
        """
        parsed = ReplanOutput.model_validate({"reason": reason})
        return ToolResult(
            success=True,
            message="Replan requested",
            data=parsed.model_dump(mode="json"),
        )
```

Validate status strings carefully: if LLM sends `in_progress`, map to `running` inside `plan_report` before validate, or accept aliases in a thin preprocess.

- [ ] **Step 2: Quick import check**

```bash
cd backend && uv run python -c "from app.domain.services.tools.plan import PlanToolkit; print(PlanToolkit().get_tools())"
```

Expected: two tools named `plan_report` and `replan`.

---

### Task 3: `AgentLoopFlow` — Planner first + intercept authoritative tools

**Files:**
- Modify: `backend/app/domain/services/flows/agent_loop.py`
- Modify: `backend/tests/test_single_loop_manus.py`

**Interfaces:**
- Consumes: `PlannerAgent`, `PlanToolkit`, `mark_first_step_running`, `apply_plan_report`, `complete_plan`, `PlanReportOutput`, `ReplanOutput`
- Produces: Flow that yields CREATED → (progress UPDATED*) → COMPLETED + Done; wait skips Done

- [ ] **Step 1: Write / rewrite failing flow tests**

Add/replace tests in `test_single_loop_manus.py`:

1. `test_agent_loop_flow_create_plan_then_manus_deliver`  
   ScriptedLLM for **planner** memory and **manus** memory separately — easiest approach: patch/fake by using ScriptedLLM that returns create_plan then Manus notify+deliver. Because Planner and Manus share one LLM instance today, sequence responses in order:
   - Response 1: planner `create_plan` tool call with title/goal/steps/message  
   - Response 2: manus `message_notify_user`  
   - Response 3: manus `plan_report`  
   - Response 4: manus `deliver_result`  
   Assert: PlanEvent CREATED, then UPDATED (from report), MessageEvent deliver, PlanEvent COMPLETED, DoneEvent. Title from plan title.

2. `test_agent_loop_flow_empty_plan_skips_manus`  
   create_plan with `steps=[]` and non-empty message → MessageEvent from plan.message, COMPLETED, Done; no file/shell tools.

3. `test_agent_loop_waiting_resume_skips_create_plan`  
   WAITING + last_plan → only Manus resume responses; no create_plan in LLM call sequence (ScriptedLLM pops only Manus responses).

4. Keep notify / wait tests working with PlanToolkit registered (Manus may need notify before plan_report).

**LLM tool names:** Planner uses OutputTool `create_plan` / `update_plan`. Manus uses toolkit function names. Ensure ScriptedLLM `ToolCall.name` matches exactly what `BaseAgent` expects (`create_plan`, `plan_report`, etc.).

- [ ] **Step 2: Run tests — expect FAIL** (flow still Manus-only)

- [ ] **Step 3: Implement flow orchestration**

In `AgentLoopFlow.__init__`:

- Build work toolkits as today.
- `self.planner = PlannerAgent(..., capability_toolkits=tools)`
- Append `PlanToolkit()` to Manus tools list.
- `self.plan: Plan | None = None`
- Apply project instruction to **both** planner and manus; sync both system prompts.

In `run`:

```text
if initial_status != WAITING:
  async for event in planner.create_plan(message):
    if PlanEvent CREATED:
      self.plan = mark_first_step_running(event.plan) if steps else event.plan
      event = PlanEvent(CREATED, plan=self.plan)  # replace with normalized
      yield Title if title
      yield MessageEvent if plan.message strip
    yield event
  if not self.plan or not self.plan.steps:
    if self.plan: yield PlanEvent(COMPLETED, complete_plan(self.plan))
    self._done = True; yield DoneEvent; return
  # inject plan into manus
  plan_block = format_plan_for_manus(self.plan)
  # Prefer: agent.run(Message(message=message.message + "\n\n" + plan_block, attachments=...))
  # Or set agent._injected_plan_text used inside run()
else:
  self.plan = last_plan
  rehydrate title/goal/notified as today

waited = False
async for event in (resume or run):
  if ToolEvent plan_report CALLED:
     report = PlanReportOutput.model_validate(event.tool_result.data or function_args)
     for e in apply_plan_report(self.plan, report):
       yield e
     continue  # suppress tool row
  if ToolEvent plan_report CALLING:
     continue
  if ToolEvent replan CALLED:
     reason = ...
     # Build a synthetic finished Step for update_plan context:
     step = self.plan.get_next_step() or self.plan.steps[-1]
     step = step.model_copy(update={"result": reason, "status": ExecutionStatus.COMPLETED, "success": True})
     async for e in self.planner.update_plan(self.plan, step):
       if isinstance(e, PlanEvent) and e.status == UPDATED:
         self.plan = e.plan
       yield e
     continue
  if ToolEvent replan CALLING:
     continue
  if WaitEvent: waited = True
  yield event

if not waited and self.plan:
  yield PlanEvent(COMPLETED, complete_plan(self.plan))
self._done = not waited
if not waited: yield DoneEvent()
```

Remove completion path that rebuilds plan from `_todo_items` / `todos_to_plan` — authoritative completion uses `self.plan` only.

Helper `format_plan_for_manus(plan) -> str`:

```text
<authoritative_plan>
title: ...
goal: ...
steps:
- [running] id=1: ...
- [pending] id=2: ...
</authoritative_plan>
Update the Plan panel only via plan_report / replan. Optionally keep todo.md in sync for your own attention; never rely on todo.md for the UI.
```

Also set `self.agent._plan_title` / `_plan_goal` from created plan.

- [ ] **Step 4: Run flow tests — expect PASS**

```bash
cd backend && uv run pytest tests/test_single_loop_manus.py -v
```

---

### Task 4: Manus prompts + fan-out suppress progress tools

**Files:**
- Modify: `backend/app/domain/services/prompts/manus.py`
- Modify: `backend/app/domain/services/agents/manus.py`
- Modify: `backend/app/domain/services/tools/file.py`
- Modify: `backend/tests/test_single_loop_manus.py` (todo.md still emits no PlanEvent — already true; add assert plan_report path if tested at agent level)

**Interfaces:**
- Consumes: control tool set including `plan_report`, `replan`
- Produces: Manus that does not yield ToolEvents for those names (Flow also suppresses; belt-and-suspenders)

- [ ] **Step 1: Update `MANUS_ROLE_PROMPT`**

Include:

- Opening: `message_notify_user` then work.
- Authoritative plan is injected; call `plan_report` when step status changes; `replan` when steps must change; then rebuild `todo.md`.
- `todo.md` optional attention; not Plan UI.
- Finish with `deliver_result`.

- [ ] **Step 2: Update Manus `_CONTROL_TOOLS` / notify gate**

Treat `plan_report` and `replan` like message tools for the notify gate? **Decision (authoritative):** they still require prior notify (they are work-adjacent). Keep them **outside** `_CONTROL_TOOLS` so notify-before-work applies; Flow suppresses their ToolEvents after notify.

In `_fan_out`, if `function_name in {"plan_report", "replan"}`: `continue` (do not yield ToolEvent). Flow must read args from the agent stream — **problem**: if Manus swallows events, Flow never sees them.

**Critical ordering:** Flow must intercept **before** Manus swallows, OR Manus yields a dedicated internal event, OR Manus applies progress itself.

**Chosen approach (implement this):** Manus `_fan_out` does **not** swallow `plan_report`/`replan`; **Flow** swallows after applying. Manus only skips Computer-facing enrichment. Frontend also ignores those function names.

Alternatively Manus applies `apply_plan_report` if `self._plan` is set by Flow — then Manus yields PlanEvents directly and suppresses ToolEvents. That duplicates ownership.

**Stick to Flow interception:** Manus yields ToolEvents for plan_* ; Flow consumes and does not forward ToolEvents; frontend ignore as backup.

- [ ] **Step 3: File toolkit instructions** — maintain `todo.md` as attention notes; rebuild after replan; do not claim it drives Plan UI.

- [ ] **Step 4: Run tests**

```bash
cd backend && uv run pytest tests/test_plan_progress.py tests/test_single_loop_manus.py -v
```

---

### Task 5: Frontend ignore authoritative control tools

**Files:**
- Modify: `frontend/src/composables/useAgentEvents.ts`
- Modify: `frontend/src/composables/__tests__/useAgentEvents.spec.ts`

- [ ] **Step 1: Ignore tool rows**

Alongside existing `todo_write` / message ignores:

```typescript
|| toolData.function === 'plan_report'
|| toolData.function === 'replan'
```

- [ ] **Step 2: Spec** — tool event with `function: 'plan_report'` does not append a timeline tool message.

- [ ] **Step 3: Run**

```bash
cd frontend && npm run test -- --run src/composables/__tests__/useAgentEvents.spec.ts
```

---

### Task 6: End-to-end verification checklist

- [ ] **Step 1: Backend suite**

```bash
cd backend && uv run pytest tests/test_plan_progress.py tests/test_single_loop_manus.py -v
```

Expected: all PASS.

- [ ] **Step 2: Manual smoke (optional, stack up)**

1. New agent session, multi-step ask.  
2. Plan panel appears after planner (CREATED).  
3. During run, statuses move when model calls `plan_report` (UPDATED).  
4. Writing `todo.md` alone does not create Plan steps.  
5. Deliver → plan COMPLETED.

- [ ] **Step 3: Stop** — ask user before any git commit.

---

## Spec coverage (self-review)

| Spec requirement | Task |
|---|---|
| Planner `create_plan` → CREATED + Title + optional message | Task 3 |
| First step RUNNING | Task 1 + 3 |
| Manus single loop after plan | Task 3 |
| `plan_report` → UPDATED / StepEvents (authoritative) | Task 1–3 |
| `replan` → Planner `update_plan` | Task 2–3 |
| Empty steps short-circuit | Task 3 |
| WAITING resume no create_plan | Task 3 |
| COMPLETED via `complete_plan` | Task 1 + 3 |
| No checklist parse | All (no todo_md parser) |
| Suppress plan tool rows | Task 3 + 5 |
| `todo.md` attention only | Task 4 |
| No full PlanAct / no todo_write | Global constraints |

## Placeholder scan

None intentional. Names locked: `PlanReportOutput`, `ReplanOutput`, `PlanToolkit`, `plan_report`, `replan`, `apply_plan_report`, `mark_first_step_running`, `complete_plan`, `format_plan_for_manus`.
