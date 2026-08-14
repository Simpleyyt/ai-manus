"""
Integration tests for the shell API (real persistent tmux-backed shell).

These tests hit a running sandbox server at http://localhost:8080,
consistent with the other sandbox integration tests.
"""
import time
import uuid

import pytest

from tests.conftest import BASE_URL


def _exec(client, session_id, command, exec_dir=None):
    payload = {"id": session_id, "command": command}
    if exec_dir is not None:
        payload["exec_dir"] = exec_dir
    response = client.post(f"{BASE_URL}/api/v1/shell/exec", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _view(client, session_id, console=False):
    response = client.post(
        f"{BASE_URL}/api/v1/shell/view",
        json={"id": session_id, "console": console},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _wait(client, session_id, seconds=None):
    return client.post(
        f"{BASE_URL}/api/v1/shell/wait",
        json={"id": session_id, "seconds": seconds},
    )


@pytest.fixture
def session_id():
    return str(uuid.uuid4())


class TestShellExec:
    def test_simple_command_completes(self, client, session_id):
        data = _exec(client, session_id, "echo hello_sandbox")
        assert data["session_id"] == session_id
        assert data["status"] == "completed"
        assert data["returncode"] == 0
        assert "hello_sandbox" in data["output"]

    def test_auto_session_id(self, client):
        response = client.post(
            f"{BASE_URL}/api/v1/shell/exec",
            json={"command": "true"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["session_id"]

    def test_nonzero_returncode(self, client, session_id):
        data = _exec(client, session_id, "false")
        assert data["status"] == "completed"
        assert data["returncode"] == 1

    def test_exec_dir_is_respected(self, client, session_id):
        data = _exec(client, session_id, "pwd", exec_dir="/tmp")
        assert data["status"] == "completed"
        assert data["output"].strip() == "/tmp"

    def test_invalid_exec_dir(self, client, session_id):
        response = client.post(
            f"{BASE_URL}/api/v1/shell/exec",
            json={
                "id": session_id,
                "command": "true",
                "exec_dir": "/does/not/exist",
            },
        )
        assert response.status_code == 400


class TestShellStatePersistence:
    """The shell must be a real persistent shell: cwd and env survive
    between exec calls in the same session."""

    def test_env_and_cwd_persist(self, client, session_id):
        data = _exec(client, session_id, "export MANUS_TEST_VAR=hello42 && cd /tmp")
        assert data["status"] == "completed"
        assert data["returncode"] == 0

        data = _exec(client, session_id, "echo $MANUS_TEST_VAR && pwd")
        assert data["status"] == "completed"
        lines = [l.strip() for l in data["output"].splitlines() if l.strip()]
        assert "hello42" in lines
        assert "/tmp" in lines

    def test_venv_activation_persists(self, client, session_id):
        data = _exec(
            client, session_id,
            "cd /tmp && python3 -m venv --without-pip .manus_test_venv && source .manus_test_venv/bin/activate",
        )
        if data["status"] != "completed":
            # venv creation can be slow; wait for it
            response = _wait(client, session_id, seconds=60)
            assert response.status_code == 200
            assert response.json()["data"]["returncode"] == 0
        else:
            assert data["returncode"] == 0

        data = _exec(client, session_id, "which python3")
        assert data["status"] == "completed"
        assert ".manus_test_venv" in data["output"]

        _exec(client, session_id, "deactivate && rm -rf /tmp/.manus_test_venv")

    def test_sessions_are_isolated(self, client):
        session_a = str(uuid.uuid4())
        session_b = str(uuid.uuid4())
        _exec(client, session_a, "export ONLY_IN_A=yes")
        data = _exec(client, session_b, "echo [$ONLY_IN_A]")
        assert data["status"] == "completed"
        assert "[yes]" not in data["output"]
        assert "[]" in data["output"]


class TestShellLongRunning:
    def test_long_running_wait_and_view(self, client, session_id):
        data = _exec(client, session_id, "sleep 7 && echo done_after_sleep")
        assert data["status"] == "running"

        response = _wait(client, session_id, seconds=30)
        assert response.status_code == 200
        assert response.json()["data"]["returncode"] == 0

        data = _view(client, session_id)
        assert "done_after_sleep" in data["output"]

    def test_wait_timeout(self, client, session_id):
        data = _exec(client, session_id, "sleep 60")
        assert data["status"] == "running"

        response = _wait(client, session_id, seconds=2)
        assert response.status_code == 400

        # Clean up the long-running command
        client.post(f"{BASE_URL}/api/v1/shell/kill", json={"id": session_id})

    def test_view_while_running(self, client, session_id):
        data = _exec(client, session_id, "echo first_line && sleep 8 && echo second_line")
        assert data["status"] == "running"

        data = _view(client, session_id)
        assert "first_line" in data["output"]
        assert "second_line" not in data["output"]

        response = _wait(client, session_id, seconds=30)
        assert response.status_code == 200
        data = _view(client, session_id)
        assert "second_line" in data["output"]


class TestShellWrite:
    def test_write_to_interactive_command(self, client, session_id):
        data = _exec(client, session_id, "read NAME && echo greeting_$NAME")
        assert data["status"] == "running"

        response = client.post(
            f"{BASE_URL}/api/v1/shell/write",
            json={"id": session_id, "input": "world", "press_enter": True},
        )
        assert response.status_code == 200

        response = _wait(client, session_id, seconds=15)
        assert response.status_code == 200
        assert response.json()["data"]["returncode"] == 0

        data = _view(client, session_id)
        assert "greeting_world" in data["output"]

    def test_write_when_idle_fails(self, client, session_id):
        _exec(client, session_id, "true")
        response = client.post(
            f"{BASE_URL}/api/v1/shell/write",
            json={"id": session_id, "input": "hello", "press_enter": True},
        )
        assert response.status_code == 400


class TestShellKill:
    def test_kill_running_command(self, client, session_id):
        data = _exec(client, session_id, "sleep 300")
        assert data["status"] == "running"

        response = client.post(f"{BASE_URL}/api/v1/shell/kill", json={"id": session_id})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "terminated"

        # Session survives the kill and keeps its state
        data = _exec(client, session_id, "echo still_alive")
        assert data["status"] == "completed"
        assert "still_alive" in data["output"]

    def test_kill_when_idle(self, client, session_id):
        _exec(client, session_id, "true")
        response = client.post(f"{BASE_URL}/api/v1/shell/kill", json={"id": session_id})
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "already_terminated"


class TestShellConsole:
    def test_console_records(self, client, session_id):
        _exec(client, session_id, "echo cmd_one")
        _exec(client, session_id, "echo cmd_two")

        data = _view(client, session_id, console=True)
        console = data["console"]
        assert len(console) == 2
        assert console[0]["command"] == "echo cmd_one"
        assert "cmd_one" in console[0]["output"]
        assert console[1]["command"] == "echo cmd_two"
        assert "cmd_two" in console[1]["output"]
        # PS1 looks like user@host:dir $
        assert "@" in console[0]["ps1"]
        assert console[0]["ps1"].endswith("$")

    def test_view_unknown_session(self, client):
        response = client.post(
            f"{BASE_URL}/api/v1/shell/view",
            json={"id": str(uuid.uuid4())},
        )
        assert response.status_code == 404
