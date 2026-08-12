# Single-Loop Manus (M1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Agent-mode `PlanActFlow` (Planner + Executor + forced `update_plan`) with a single LLM↔tools loop whose soft plan is `todo_write`, projected to existing `PlanEvent` / `StepEvent` for the UI.

**Architecture:** One `ManusAgent` (one memory key), `TodoToolkit` + existing work tools + `deliver_result` OutputTool; `AgentLoopFlow` owns session status / wait resume; `AgentTaskRunner` wires the new flow for `TaskMode.AGENT`. Chat/Lite unchanged.

**Tech Stack:** Python 3.12, FastAPI domain layer, Pydantic v2, existing `BaseAgent` / `OutputTool` / Beanie agent memories, pytest (unit, no live server required for M1 domain tests).

**Spec:** `docs/superpowers/specs/2026-08-05-single-loop-manus-design.md`

## Global Constraints

- Scope = **M1 only** (behavior switch). Do not delete `PlannerAgent` / `PlanActFlow` files in M1 — leave unused until M2.
- Chat / Lite path in `agent_task_runner.py` must stay behavior-identical.
- Frontend contract: keep emitting `PlanEvent` with `plan.steps[{id,description,status}]` so `PlanPanel` works without FE changes.
- Control outputs use native FC (`OutputTool` / toolkit tools) — no JSON-in-prompt protocol.
- `todo_write` always submits the **full** item list (replace semantics).
- Memory key for the new agent: `"manus"` (do not write `"planner"` / `"execution"` from the new path).
- Verify M1: `cd backend && uv run pytest tests/test_todo_projection.py tests/test_single_loop_manus.py -v`
- Do **not** commit unless the user explicitly asks.

## File structure

| File | Responsibility |
|------|----------------|
| `backend/app/domain/models/todo.py` | `TodoStatus`, `TodoItem`, `TodoWriteArgs` |
| `backend/app/domain/services/todo_projection.py` | Map todo snapshot → `Plan` + plan/step events |
| `backend/app/domain/services/tools/todo.py` | `TodoToolkit.todo_write` |
| `backend/app/domain/services/prompts/manus.py` | Single-loop role prompt |
| `backend/app/domain/services/agents/manus.py` | `ManusAgent` run / resume / event fan-out |
| `backend/app/domain/services/flows/agent_loop.py` | `AgentLoopFlow` session orchestration |
| `backend/app/domain/services/agents/base.py` | Add `continue_execute` (resume without new user turn) |
| `backend/app/domain/models/agent_output.py` | Keep `FinalResult`; unused planner/step schemas stay until M2 |
| `backend/app/domain/services/agent_task_runner.py` | Construct `AgentLoopFlow` instead of `PlanActFlow` |
| `backend/app/domain/services/tools/message.py` | Align `instructions` with todo + deliver |
| `backend/tests/test_todo_projection.py` | Pure projection tests |
| `backend/tests/test_single_loop_manus.py` | Agent + flow tests with mock LLM |

---

### Task 1: Todo models + projection helper

**Files:**
- Create: `backend/app/domain/models/todo.py`
- Create: `backend/app/domain/services/todo_projection.py`
- Create: `backend/tests/test_todo_projection.py`

**Interfaces:**
- Consumes: `Plan`, `Step`, `ExecutionStatus` from `app.domain.models.plan`; `PlanEvent`, `PlanStatus`, `StepEvent`, `StepStatus` from `app.domain.models.event`
- Produces:

```python
class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TodoItem(BaseModel):
    id: str
    content: str
    status: TodoStatus = TodoStatus.PENDING

class TodoWriteArgs(BaseModel):
    items: List[TodoItem]

def todos_to_plan(items: List[TodoItem], *, title: str = "", goal: str = "") -> Plan: ...

def project_todo_write(
    items: List[TodoItem],
    *,
    previous_items: Optional[List[TodoItem]],
    title: str = "",
) -> List[BaseEvent]:
    """Return PlanEvent (+ optional StepEvents) for this todo_write."""
```

Status mapping for `Step` / plan steps:

| `TodoStatus` | `ExecutionStatus` on `Step` |
|--------------|-----------------------------|
| `pending` | `PENDING` |
| `in_progress` | `RUNNING` |
| `completed` | `COMPLETED` (+ `success=True`) |
| `cancelled` | `COMPLETED` (+ `success=False`) |

- [ ] **Step 1: Write failing projection tests**

```python
# backend/tests/test_todo_projection.py
from app.domain.models.todo import TodoItem, TodoStatus
from app.domain.models.event import PlanEvent, PlanStatus, StepEvent, StepStatus
from app.domain.models.plan import ExecutionStatus
from app.domain.services.todo_projection import todos_to_plan, project_todo_write

def test_todos_to_plan_maps_statuses():
    plan = todos_to_plan([
        TodoItem(id="1", content="A", status=TodoStatus.COMPLETED),
        TodoItem(id="2", content="B", status=TodoStatus.IN_PROGRESS),
        TodoItem(id="3", content="C", status=TodoStatus.PENDING),
    ], title="T", goal="G")
    assert plan.title == "T"
    assert plan.goal == "G"
    assert plan.steps[0].status == ExecutionStatus.COMPLETED
    assert plan.steps[0].success is True
    assert plan.steps[1].status == ExecutionStatus.RUNNING
    assert plan.steps[2].status == ExecutionStatus.PENDING

def test_first_todo_write_emits_created_plan():
    items = [TodoItem(id="1", content="Research", status=TodoStatus.IN_PROGRESS)]
    events = project_todo_write(items, previous_items=None, title="Research task")
    assert len(events) >= 1
    assert isinstance(events[0], PlanEvent)
    assert events[0].status == PlanStatus.CREATED
    assert events[0].plan.steps[0].description == "Research"

def test_subsequent_todo_write_emits_updated_and_step_transitions():
    prev = [TodoItem(id="1", content="Research", status=TodoStatus.IN_PROGRESS)]
    curr = [TodoItem(id="1", content="Research", status=TodoStatus.COMPLETED)]
    events = project_todo_write(curr, previous_items=prev, title="Research task")
    types = [(type(e), getattr(e, "status", None)) for e in events]
    assert any(isinstance(e, PlanEvent) and e.status == PlanStatus.UPDATED for e in events)
    assert any(isinstance(e, StepEvent) and e.status == StepStatus.COMPLETED for e in events)
```

- [ ] **Step 2: Run tests — expect fail (modules missing)**

Run: `cd backend && uv run pytest tests/test_todo_projection.py -v`  
Expected: FAIL import / not found

- [ ] **Step 3: Implement models + projection**

`todo.py`: enums + Pydantic models as in Interfaces.

`todo_projection.py` logic:

1. `todos_to_plan` — build `Step(id=item.id, description=item.content, status=..., success=...)` for each item; set `Plan.title` / `Plan.goal` (goal default `""` or first pending content).
2. `project_todo_write`:
   - If `previous_items is None` (or empty) and `items` non-empty → `PlanEvent(CREATED, plan=...)`.
   - Else → `PlanEvent(UPDATED, plan=...)`.
   - Diff by `id`: new/`pending→in_progress` → `StepEvent(STARTED)`; transition to `completed`/`cancelled` → `StepEvent(COMPLETED)` (use matching `Step` from plan).
   - Empty `items` after non-empty: still emit `PlanEvent(UPDATED)` with empty steps (allowed).

- [ ] **Step 4: Run tests — expect pass**

Run: `cd backend && uv run pytest tests/test_todo_projection.py -v`  
Expected: PASS

---

### Task 2: `TodoToolkit`

**Files:**
- Create: `backend/app/domain/services/tools/todo.py`
- Modify: `backend/tests/test_todo_projection.py` (optional toolkit smoke) **or** add cases to `backend/tests/test_domain_tools.py`

**Interfaces:**
- Consumes: `@tool`, `BaseToolkit`, `ToolResult`, `TodoWriteArgs` / `TodoItem` / `TodoStatus`
- Produces: `TodoToolkit` with `name = "todo"` and method `todo_write(items: list[dict] | list[TodoItem]) -> ToolResult`

- [ ] **Step 1: Write failing toolkit test**

```python
# add to backend/tests/test_todo_projection.py or test_domain_tools.py
import pytest
from app.domain.services.tools.todo import TodoToolkit

@pytest.mark.asyncio
async def test_todo_write_returns_items():
    tk = TodoToolkit()
    tool = tk.get_tool("todo_write")
    assert tool is not None
    result = await tool.invoke({
        "items": [
            {"id": "1", "content": "Do thing", "status": "pending"},
        ]
    })
    assert result.success is True
    assert result.data is not None
    # data should be list of dicts or TodoItem-shaped payloads
    assert len(result.data) == 1
```

- [ ] **Step 2: Run test — expect fail**

Run: `cd backend && uv run pytest tests/test_todo_projection.py::test_todo_write_returns_items -v`  
Expected: FAIL

- [ ] **Step 3: Implement toolkit**

```python
# backend/app/domain/services/tools/todo.py
class TodoToolkit(BaseToolkit):
    name = "todo"
    instructions = """
- Maintain a short todo list for non-trivial tasks via todo_write
- Each call replaces the entire list; include every item every time
- Mark at most one item in_progress; update statuses as you finish work
- Prefer finishing todos before deliver_result
"""

    @tool(parse_docstring=True)
    async def todo_write(self, items: List[dict]) -> ToolResult:
        """Replace the current todo list with the provided full list.

        Args:
            items: Full list of todos. Each item needs id, content, and status
                (pending | in_progress | completed | cancelled).
        """
        parsed = [TodoItem.model_validate(i) for i in items]
        return ToolResult(
            success=True,
            message=f"Updated {len(parsed)} todos",
            data=[i.model_dump(mode="json") for i in parsed],
        )
```

If `@tool` typing for `List[dict]` is awkward in schema generation, accept `items: list` and validate inside (match patterns used elsewhere in toolkits).

- [ ] **Step 4: Run test — expect pass**

Run: `cd backend && uv run pytest tests/test_todo_projection.py -v`  
Expected: PASS

---

### Task 3: `BaseAgent.continue_execute`

**Files:**
- Modify: `backend/app/domain/services/agents/base.py`
- Create/extend: `backend/tests/test_single_loop_manus.py`

**Interfaces:**
- Consumes: existing `execute`, `ask`, `ask_with_messages`, `_handle_output_call`, `invoke_tool`
- Produces:

```python
async def continue_execute(
    self,
    output_tool: Optional[OutputTool] = None,
) -> AsyncGenerator[BaseEvent, None]:
    """Resume the tool loop from current memory without appending a user turn.
    Used after message_ask_user wait + roll_back injected the user reply as a tool result.
    """
```

Refactor note: extract the post-`ask` tool-processing body of `execute` into a private async generator `_tool_loop(self, message: LLMMessage)` so both `execute` and `continue_execute` share it.

```python
async def execute(self, request: str, output_tool: Optional[OutputTool] = None):
    self._output_tool = output_tool
    try:
        message = await self.ask(request)
        async for event in self._tool_loop(message):
            yield event
    finally:
        self._output_tool = None

async def continue_execute(self, output_tool: Optional[OutputTool] = None):
    self._output_tool = output_tool
    try:
        await self._ensure_memory()
        if self.memory.estimate_tokens() > self.max_context_tokens:
            self.memory.compact(max_tokens=self.max_context_tokens)
            await self._repository.save_memory(...)
        message = await self._llm.ask(
            messages=list(self.memory.get_messages()),
            tools=self.get_tool_schemas(),
            tool_choice=self.tool_choice,
        )
        await self._add_to_memory([message])
        async for event in self._tool_loop(message):
            yield event
    finally:
        self._output_tool = None
```

- [ ] **Step 1: Write failing test with mock LLM + in-memory fake repo**

```python
# backend/tests/test_single_loop_manus.py
import pytest
from app.domain.models.message import LLMMessage, Role, ToolCall
from app.domain.models.memory import Memory
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
# ... FakeRepo, ScriptedLLM helpers ...

@pytest.mark.asyncio
async def test_continue_execute_does_not_append_user_message():
    """Memory before continue ends with a tool result; after one LLM round-trip
    with deliver_result, no new Role.USER was inserted by continue_execute."""
    # Arrange memory: system, user, assistant(ask_user), tool(user reply)
    # ScriptedLLM returns assistant with deliver_result tool call
    # Act: continue_execute(DELIVER_RESULT)
    # Assert: count of Role.USER messages unchanged; StructuredOutputEvent yielded
```

Implement minimal `FakeAgentRepository` storing `dict[str, Memory]` and `ScriptedLLM` returning queued `LLMMessage`s.

- [ ] **Step 2: Run test — expect fail**

Run: `cd backend && uv run pytest tests/test_single_loop_manus.py::test_continue_execute_does_not_append_user_message -v`  
Expected: FAIL (`continue_execute` missing)

- [ ] **Step 3: Refactor `execute` + add `continue_execute`**

Keep public behavior of `execute` identical for existing planner/executor callers.

- [ ] **Step 4: Run test — expect pass**

Run: `cd backend && uv run pytest tests/test_single_loop_manus.py::test_continue_execute_does_not_append_user_message -v`  
Expected: PASS

---

### Task 4: `ManusAgent` + role prompt

**Files:**
- Create: `backend/app/domain/services/prompts/manus.py`
- Create: `backend/app/domain/services/agents/manus.py`
- Modify: `backend/tests/test_single_loop_manus.py`
- Modify: `backend/app/domain/services/tools/message.py` (`instructions` only)

**Interfaces:**
- Consumes: `BaseAgent`, `DELIVER_RESULT`-equivalent `OutputTool(FinalResult)`, `TodoToolkit`, work toolkits, `project_todo_write`, `FinalResult`
- Produces:

```python
class ManusAgent(BaseAgent):
    name: str = "manus"

    def build_system_prompt(self) -> str: ...

    async def run(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        """Fresh user turn: ask(user text) then tool loop until deliver / wait."""

    async def resume(self) -> AsyncGenerator[BaseEvent, None]:
        """After WAITING + roll_back: continue_execute until deliver / wait."""
```

Event fan-out inside `run` / `resume` while iterating `execute` / `continue_execute`:

| Incoming | Action |
|----------|--------|
| `ToolEvent` `todo_write` + `CALLED` | Parse items from `function_args["items"]` (validate `TodoItem`); call `project_todo_write`; yield those events; keep agent-side `self._todo_items`; on first created plan also yield `TitleEvent` if title non-empty |
| `ToolEvent` `message_ask_user` + `CALLING` | Yield `MessageEvent(text)` |
| `ToolEvent` `message_ask_user` + `CALLED` | Yield `WaitEvent`; **return** (stop generator) |
| `ToolEvent` other | Yield as-is |
| `StructuredOutputEvent` (`FinalResult`) | Yield `MessageEvent(message, attachments=FileInfo paths)`; return |
| `ErrorEvent` | Yield |
| Plain `MessageEvent` from base when no tools | If Agent should force deliver: ignore / do not end; base already nudges when `output_tool` set — rely on that |

Title helper:

```python
def suggest_title(user_message: str, items: list[TodoItem]) -> str:
    if items:
        return items[0].content.strip()[:80] or "New task"
    text = (user_message or "").strip().replace("\n", " ")
    return (text[:80] if text else "New task")
```

Store `self._todo_items` and `self._title_emitted: bool` on the agent instance for projection diffs within a run. Persist nothing extra beyond memory messages (todo state is in tool history + session PlanEvents).

`MANUS_ROLE_PROMPT` (in `prompts/manus.py`): single-loop role — use tools; maintain todos for non-trivial work; `message_notify_user` for brief progress; `message_ask_user` only when blocked; finish with `deliver_result`; do not hand work back to the user.

User turn text for `run`:

```python
request = message.message
if message.attachments:
    request += "\n\nAttachments:\n" + "\n".join(message.attachments)
```

- [ ] **Step 1: Write failing tests**

```python
@pytest.mark.asyncio
async def test_manus_run_todo_then_deliver_emits_plan_and_message():
    # ScriptedLLM:
    # 1) assistant → todo_write(items=[...])
    # 2) after tool result → assistant → deliver_result({message, attachments:[]})
    # Assert: PlanEvent CREATED, MessageEvent with final text, no planner tools

@pytest.mark.asyncio
async def test_manus_ask_user_yields_wait_and_stops():
    # ScriptedLLM: message_ask_user then stop consuming further scripts
    # Assert: WaitEvent present; deliver not called
```

- [ ] **Step 2: Run — expect fail**

Run: `cd backend && uv run pytest tests/test_single_loop_manus.py -v`  
Expected: FAIL missing `ManusAgent`

- [ ] **Step 3: Implement prompt + `ManusAgent`**

Wire `DELIVER_RESULT_TOOL = OutputTool(name="deliver_result", schema=FinalResult, ...)` (can import/copy from `execution.py` to avoid circular imports — prefer defining once in `agent_output` adjacent module or `manus.py`).

Update `MessageToolkit.instructions` to mention todos live in `todo_write` and finals go through `deliver_result` (remove contradiction “not todo lists” if it conflicts — say “do not dump raw todo lists as the final user answer; use deliver_result for the answer”).

- [ ] **Step 4: Run — expect pass**

Run: `cd backend && uv run pytest tests/test_single_loop_manus.py -v`  
Expected: PASS

---

### Task 5: `AgentLoopFlow`

**Files:**
- Create: `backend/app/domain/services/flows/agent_loop.py`
- Modify: `backend/tests/test_single_loop_manus.py`

**Interfaces:**
- Consumes: same constructor deps as `PlanActFlow` (agent_id, repos, sandbox, browser, mcp, llm, search, project_repo); `ManusAgent`; toolkits list identical to today’s executor tools **plus** `TodoToolkit()`
- Produces:

```python
class AgentLoopFlow(BaseFlow):
    def __init__(...): ...
    async def run(self, message: Message) -> AsyncGenerator[BaseEvent, None]: ...
    def is_done(self) -> bool: ...
```

`run` logic:

```text
session = find session
apply project instruction → agent.sync_system_prompt()
if session.status != PENDING:
    await agent.roll_back(message)
update_status(RUNNING)

if session.status == WAITING:
    async for event in agent.resume():
        yield event
else:
    async for event in agent.run(message):
        yield event

# If resume/run returned without WaitEvent, emit PlanEvent(COMPLETED) if a plan exists
# then DoneEvent
# Track whether WaitEvent was yielded — if so, do not DoneEvent (task runner sets WAITING)
```

Implementation detail for Done vs Wait:

```python
waited = False
async for event in ...:
    if isinstance(event, WaitEvent):
        waited = True
    yield event
if not waited:
    if agent has todos / last plan:
        yield PlanEvent(status=COMPLETED, plan=todos_to_plan(agent._todo_items or last))
    yield DoneEvent()
```

Rehydrate `agent._todo_items` on WAITING resume from `session.get_last_plan()` mapped back to todos (id/description/status) so projection diffs stay correct.

- [ ] **Step 1: Write failing flow test with fake session repo**

```python
@pytest.mark.asyncio
async def test_agent_loop_flow_fresh_message_runs_manus():
    # Minimal fakes for session_repository.find_by_id / update_status / project
    # ScriptedLLM deliver immediately
    # Assert DoneEvent and MessageEvent
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement `AgentLoopFlow`**

Copy toolkit assembly from `plan_act.py` (Shell, Browser, File, Message, MCP, optional Search) and insert `TodoToolkit()`.

Do **not** instantiate `PlannerAgent`.

- [ ] **Step 4: Run — expect pass**

---

### Task 6: Wire `AgentTaskRunner`

**Files:**
- Modify: `backend/app/domain/services/agent_task_runner.py`

**Interfaces:**
- Consumes: `AgentLoopFlow`
- Produces: Agent mode uses `AgentLoopFlow`; `_run_flow` iterates it as today

- [ ] **Step 1: Change construction**

Replace:

```python
from app.domain.services.flows.plan_act import PlanActFlow
self._flow = PlanActFlow(...)
```

with:

```python
from app.domain.services.flows.agent_loop import AgentLoopFlow
self._flow = AgentLoopFlow(...)
```

Keep `_run_flow` as:

```python
async def _run_flow(self, message: Message):
    async for event in self._flow.run(message):
        # existing tool enrichment hooks for ToolEvent / MessageEvent attachments
        ...
        yield event
```

Ensure `_handle_tool_event` still runs for shell/browser/file; `todo_write` needs no special enrichment (no `tool_content`).

- [ ] **Step 2: Sanity check imports**

Run: `cd backend && uv run python -c "from app.domain.services.agent_task_runner import AgentTaskRunner; print('ok')"`  
Expected: `ok`

- [ ] **Step 3: Run full M1 unit suite**

Run: `cd backend && uv run pytest tests/test_todo_projection.py tests/test_single_loop_manus.py tests/test_context_engineering.py -v`  
Expected: PASS (context_engineering may still import planner schemas — should not break)

If `test_context_engineering.py` asserts planner-only behavior that conflicts, adjust only tests that break due to shared base changes — do not expand scope.

---

### Task 7: Manual / stack smoke (verification)

**Files:** none required

- [ ] **Step 1: Start stack** (if Docker available)

Run: `./dev.sh up -d mongodb redis backend mockserver`  
(or full `./dev.sh up -d`)

- [ ] **Step 2: Agent session smoke**

1. Open UI or use WS/API with `AUTH_PROVIDER=none`.  
2. Agent mode: ask a multi-step fake task.  
3. Confirm: plan panel updates (todo projection), tools run, final assistant message appears, no requirement for `create_plan` in backend logs.  
4. Optional: trigger `message_ask_user` via mock if feasible; resume and finish.

- [ ] **Step 3: Chat mode smoke**

Send a Chat/Lite message — single reply, no sandbox/todo.

---

## Follow-on (out of this plan — M2 / M3)

Do **not** implement in M1:

- **M2:** Delete or archive `PlannerAgent`, planner prompts, `PlanActFlow` wiring, `create_plan` / `update_plan` / `complete_step`, dual-memory usage.  
- **M3:** Restorable tool offload, schema-aware token budget, hard “all todos completed before deliver” validation.

---

## Spec coverage self-review

| Spec section | Task |
|--------------|------|
| Single master loop | 4–6 |
| `todo_write` + full replace | 1–2 |
| Plan UI projection | 1, 4 |
| `deliver_result` / `ask_user` | 4–5 |
| One memory key `manus` | 4 |
| Chat unchanged | 6 |
| WAITING resume without new user prompt | 3, 5 |
| M2/M3 deferred | Follow-on |
| No FE required | Event shapes preserved in 1 |

Placeholder scan: none intentional. Type names: `TodoItem`, `TodoWriteArgs`, `ManusAgent`, `AgentLoopFlow`, `continue_execute`, `project_todo_write` used consistently.
