"""End-to-end PlanAct tests over the real dev stack (marker: e2e).

Drives the real backend chat WebSocket with the mockserver replaying a
scripted LLM scenario (switched via POST /mock/scenario), and the real
sandbox executing tools. Requires the dev stack:

    ./dev.sh up -d   # backend + mongodb + redis + mockserver + sandbox

Run with: uv run pytest -m e2e
"""

import asyncio
import json
import time
import uuid

import httpx
import pytest
import websockets

BACKEND_BASE = "http://localhost:8000/api/v1"
CHAT_WS_URL = "ws://localhost:8000/api/v1/ws/chat"
MOCKSERVER_BASE = "http://localhost:8090"
STREAM_TIMEOUT = 120

pytestmark = pytest.mark.e2e


def _stack_available() -> bool:
    try:
        httpx.get(f"{MOCKSERVER_BASE}/mock/scenario", timeout=3).raise_for_status()
        return httpx.put(f"{BACKEND_BASE}/sessions", timeout=5).status_code == 200
    except Exception:
        return False


requires_stack = pytest.mark.skipif(
    not _stack_available(),
    reason="dev stack not running (./dev.sh up -d)",
)


def _set_scenario(file: str) -> None:
    response = httpx.post(
        f"{MOCKSERVER_BASE}/mock/scenario", json={"file": file}, timeout=5
    )
    response.raise_for_status()
    assert response.json()["index"] == 0


def _create_session() -> str:
    response = httpx.put(f"{BACKEND_BASE}/sessions", timeout=10)
    response.raise_for_status()
    return response.json()["data"]["session_id"]


def _frame(type_: str, session_id: str, **extra) -> str:
    return json.dumps({
        "id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "version": 2,
        "type": type_,
        "session_id": session_id,
        **extra,
    })


async def _collect_until_stream_end(ws) -> list[dict]:
    """Read frames until stream_end, skipping pings."""
    frames: list[dict] = []
    deadline = asyncio.get_event_loop().time() + STREAM_TIMEOUT
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        assert remaining > 0, f"stream_end not seen within {STREAM_TIMEOUT}s: {frames}"
        frame = json.loads(await asyncio.wait_for(ws.recv(), timeout=remaining))
        if frame.get("type") == "ping":
            continue
        frames.append(frame)
        assert frame.get("type") != "error", f"server error frame: {frame}"
        if frame.get("type") == "stream_end":
            return frames


def _events(frames: list[dict], name: str) -> list[dict]:
    return [f["data"] for f in frames if f.get("type") == "event" and f.get("event") == name]


def _statuses(frames: list[dict]) -> list[str]:
    return [d["agent_status"] for d in _events(frames, "status_update")]


async def _join(ws, session_id: str) -> None:
    await ws.send(_frame("join_session", session_id))
    while True:
        frame = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
        if frame.get("type") == "joined":
            assert frame["session_id"] == session_id
            return


@requires_stack
async def test_e2e_plan_act_smoke():
    """Full loop: plan -> real shell_exec in sandbox -> complete -> deliver."""
    _set_scenario("plan_act_e2e.yaml")
    session_id = _create_session()

    async with websockets.connect(CHAT_WS_URL) as ws:
        await _join(ws, session_id)
        await ws.send(_frame("chat", session_id, message="Run the e2e smoke"))
        frames = await _collect_until_stream_end(ws)

    plans = _events(frames, "plan")
    assert plans, "no plan events"
    assert [s["id"] for s in plans[0]["steps"]] == ["1"]
    assert all(s["status"] == "completed" for s in plans[-1]["steps"])

    steps = _events(frames, "step")
    assert any(s["id"] == "1" and s["status"] == "completed" for s in steps)

    tools = _events(frames, "tool")
    shell_calls = [t for t in tools if t["function"] == "shell_exec"]
    assert shell_calls, "shell_exec tool event missing"
    assert shell_calls[0]["name"] == "shell"

    titles = _events(frames, "title")
    assert titles and titles[0]["title"] == "E2E Smoke Task"

    messages = [d["content"] for d in _events(frames, "message")]
    assert "E2E smoke finished" in messages

    assert _statuses(frames)[-1] == "completed"
    assert _events(frames, "done"), "no done event"


@requires_stack
async def test_e2e_plan_act_wait_and_resume():
    """ask_user parks the session WAITING; a follow-up chat resumes to done."""
    _set_scenario("plan_act_wait_e2e.yaml")
    session_id = _create_session()

    async with websockets.connect(CHAT_WS_URL) as ws:
        await _join(ws, session_id)

        await ws.send(_frame("chat", session_id, message="Pick for me"))
        first = await _collect_until_stream_end(ws)

        assert _events(first, "wait"), "no wait event"
        assert _statuses(first)[-1] == "waiting"
        questions = [d["content"] for d in _events(first, "message")]
        assert "Which option do you want, A or B?" in questions
        assert not _events(first, "done"), "done must not fire while waiting"

        await ws.send(_frame("chat", session_id, message="Option B"))
        second = await _collect_until_stream_end(ws)

    messages = [d["content"] for d in _events(second, "message")]
    assert "Done with the chosen option" in messages
    plans = _events(second, "plan")
    assert plans and all(s["status"] == "completed" for s in plans[-1]["steps"])
    assert _statuses(second)[-1] == "completed"
    assert _events(second, "done"), "no done event after resume"
