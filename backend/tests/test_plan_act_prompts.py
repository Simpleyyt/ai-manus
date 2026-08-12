"""Prompt copy for PlanAct: no stale single-loop tools; clear exits; lean plans."""

from app.domain.services.prompts.execution import EXECUTION_ROLE_PROMPT
from app.domain.services.prompts.planner import PLANNER_ROLE_PROMPT
from app.domain.services.tools.file import FileToolkit
from app.domain.services.tools.message import MessageToolkit


def test_file_instructions_do_not_mention_plan_report_or_replan():
    text = FileToolkit.instructions
    assert "plan_report" not in text
    assert "replan" not in text


def test_message_instructions_align_step_and_final_exits():
    text = MessageToolkit.instructions
    assert "complete_step" in text
    assert "deliver_result" in text
    assert "todo list" in text.lower()


def test_planner_role_balances_lean_plans_with_multi_phase_splits():
    text = PLANNER_ROLE_PROMPT
    from app.domain.services.prompts.planner import CREATE_PLAN_PROMPT

    assert "verify" in text.lower() or "3–5" in text or "3-5" in text
    assert "assumptions" in text.lower() or "defaults" in text.lower()
    assert "Default to ONE step" not in text
    assert "Prefer ONE step when possible" not in CREATE_PLAN_PROMPT
    assert "verification" in CREATE_PLAN_PROMPT.lower() or "verify" in CREATE_PLAN_PROMPT.lower()


def test_execution_role_requires_verification_before_complete():
    text = EXECUTION_ROLE_PROMPT
    assert "complete_step" in text
    assert "deliver_result" not in text
    assert "verify" in text.lower() or "run" in text.lower()
