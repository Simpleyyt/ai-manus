---
name: harness
description: >-
  Harness coding guide for the agent framework (Plan-Act loop, BaseAgent tool
  loop, context engineering, events). Use when changing backend/app/domain/
  services (flows, agents, prompts, tools), adding a toolkit or event type,
  debugging the agent loop, or writing offline tests with
  backend/tests/harness.py or mockserver scenarios.
---

# Agent Harness Coding

The "harness" is the framework that drives the LLM: the Plan-Act state
machine, the two role agents, the `BaseAgent` tool loop, and the event
stream. All of it lives in `backend/app/domain/services/` and depends only
on the Protocols in `backend/app/domain/external/` — which is what makes it
fully testable offline.

## File map (reading order)

| File | Role |
|---|---|
| `flows/plan_act.py` | `PlanActFlow.run()` state machine (~250 lines, the main loop) |
| `agents/base.py` | `BaseAgent._tool_loop`: tool calling, retries, memory, structured output |
| `agents/planner.py` | `PlannerAgent`: `create_plan` / `update_plan` output tools |
| `agents/execution.py` | `ExecutionAgent`: one step per run, `complete_step` / `deliver_result` |
| `agent_task_runner.py` | Runs a flow as a cancellable background task (stop/resume) |
| `prompts/` | System prompt assembly (`system.py`) + role/request prompts |
| `tools/` | Toolkits (`shell`, `browser`, `file`, `search`, `message`, `mcp`, `plan`) |
| `../models/event.py` | Typed events streamed to the frontend over Redis + WebSocket |
| `flows/agent_loop.py` + `agents/manus.py` | Experimental single-loop alternative (not wired by default) |

## Invariants (do not break)

State machine (`PlanActFlow`):

- Transitions are `IDLE → PLANNING → EXECUTING ⇄ UPDATING → SUMMARIZING → COMPLETED`. Executor runs **one step at a time**.
- Successful steps are marked **locally** and emit `PlanEvent(UPDATED)` without a Planner round-trip; only `step_needs_replan()` (step FAILED, or COMPLETED with `success=False`) enters `UPDATING`.
- A `WaitEvent` (from `message_ask_user`) aborts `run()` **without** a `DoneEvent`; `is_done()` stays `False`. Resume path: `SessionStatus.WAITING` → `executor.resume_step`, and the user's reply is injected as the **tool response** to the pending `message_ask_user` call (see `BaseAgent.roll_back`).
- On a non-`PENDING` session, both agents `roll_back` before the loop starts.
- An empty plan (no steps) completes directly; a single successful step skips summarize (`can_skip_summarize`).

Tool loop (`BaseAgent`):

- **Every** `tool_call` in an assistant message must receive a tool response — including unknown tools and failed `OutputTool` validations — so the memory's call/response pairing stays valid for the next LLM request.
- Structured output goes through native function calling (`OutputTool`); validation errors are fed back as the tool response so the model self-repairs. A plain text reply while an output tool is active gets nudged to call it.
- Context budgets: tool results are truncated at ingestion (`max_tool_result_chars`, 16k chars); memory is compacted before LLM calls when over `max_context_tokens` (100k). Compaction elides old tool results but **preserves the message skeleton**.
- `invoke_tool` retries `max_retries` (3) times; the loop caps at `max_iterations` (100).
- Planner has `tool_choice="required"` and holds **no** executor toolkits — only a compact capability overview (`describe_toolkits`), keeping full schemas out of its context.
- Executor rejects `complete_step(success=true)` unless real work tools ran (`_WORK_TOOLKITS`).
- `StructuredOutputEvent` is internal — never part of the public event union streamed to clients.
- Planner and Executor keep **separate** memories, keyed `agent_id:name` in `AgentRepository` — this is what makes sessions resumable.

## Extension recipes

**Add a toolkit**: subclass `BaseToolkit` in `tools/`, decorate methods with `@tool` (docstring Args become the schema), optionally set `instructions` (becomes a `<name_rules>` system-prompt section). Wire it into the `tools` list in `flows/plan_act.py`. For rich UI rendering add a tool content type in `../models/event.py` and a renderer in `frontend/src/components/toolViews/`.

**Add an event type**: define it in `../models/event.py`, yield it from the flow/agent, handle it in the frontend WebSocket client (`frontend/src/api/`). Events reach the browser via Redis message queues → `/api/v1/ws/chat`.

**Change prompts**: edit `prompts/`; `test_plan_act_prompts.py` guards against stale tool references. System prompts are assembled by `prompts/system.py:build_system_prompt` (core + toolkit sections + role + project instructions).

**Change external capabilities**: define the Protocol in `domain/external/` first, implement in `infrastructure/external/`, wire in `interfaces/dependencies.py`. The harness must keep depending on the Protocol only.

## Testing pyramid

**1. Offline unit tests (seconds — always run these when touching the harness):**

```bash
cd backend && uv run pytest tests/test_plan_act_flow.py \
  tests/test_context_engineering.py tests/test_single_loop_manus.py -q
```

Shared fakes live in `backend/tests/harness.py`: `ScriptedLLM` (scripted
assistant replies, records every request), `FakeAgentRepository`,
`FakeSandbox`, `FakeSession(Repository)`, `StubAgent`, plus
`build_plan_act_flow` / `build_agent_loop_flow` and the `create_plan_call`
factory. Import from there — do not redefine fakes per test module. A
scripted test is: list the exact `LLMMessage.assistant(tool_calls=[...])`
turns, run the flow, assert on the yielded events and on
`llm.asked_tool_names` / `llm.requests`; end with `assert llm.responses == []`.

Gotchas: run `uv sync` first; `Settings` reads real env vars, so unset
`API_BASE` etc. when testing config defaults (`env -u API_BASE uv run pytest …`).

**2. Mockserver scenarios (end-to-end over real HTTP):** the mockserver
replays a YAML script of chat completions in order. Select with
`MOCK_DATA_FILE=<name>.yaml` (default `default.yaml`), tune `MOCK_DELAY`;
restart mockserver to reset the reply index (`./dev.sh restart mockserver`).

| Scenario | Covers |
|---|---|
| `default.yaml` | Baseline plan → step → deliver flow |
| `shell_tools.yaml` / `shell_stateful.yaml` | Shell toolkit, live terminal updates |
| `file_tools.yaml` | File toolkit views |
| `browser_tools.yaml` | Browser toolkit + VNC view |
| `search_tools.yaml` | Search toolkit |
| `message_tools.yaml` | notify / ask_user (WaitEvent path) |
| `chat_page_parity_e2e.yaml` / `computer_ui_e2e.yaml` | Frontend UI e2e |
| `single-loop-ui-demo.yaml` | Experimental single-loop flow |

**3. Full stack:** `./dev.sh up -d`, open `http://localhost:5173`, watch
`./dev.sh logs -f backend`. Needed for sandbox/browser/VNC behavior that
fakes can't cover.

## Maintenance

When you change flow transitions, event contracts, memory/rollback
semantics, or output tools, update the **Invariants** section above and the
affected scripted tests in the same PR.
