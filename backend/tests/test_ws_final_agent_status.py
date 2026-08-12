"""Final chat WS agent_status must not regress waiting → running.

Race: WaitEvent is streamed before Mongo flips to WAITING; a naive final
status_update from session.status=RUNNING would wipe the waiting footer.
"""

from app.interfaces.api.ws_routes import _final_agent_status


def test_saw_wait_wins_over_stale_running_session():
    assert _final_agent_status("running", saw_wait=True, saw_error=False) == "waiting"


def test_saw_wait_wins_over_saw_error():
    assert _final_agent_status("running", saw_wait=True, saw_error=True) == "waiting"


def test_mongo_waiting_without_saw_wait():
    assert _final_agent_status("waiting", saw_wait=False, saw_error=False) == "waiting"


def test_saw_error_when_not_waiting():
    assert _final_agent_status("completed", saw_wait=False, saw_error=True) == "error"


def test_completed_when_clean():
    assert _final_agent_status("completed", saw_wait=False, saw_error=False) == "completed"
