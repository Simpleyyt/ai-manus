from app.domain.models.plan import Plan, Step
from app.domain.services.skills.plan_steps import (
    ensure_skill_read_first_step,
    plan_already_starts_with_skill_read,
    skill_read_step_description,
)


def test_skill_read_step_description_zh():
    assert skill_read_step_description("pdf", language="zh") == "加载 pdf 技能"


def test_skill_read_step_description_en_default():
    assert skill_read_step_description("pdf") == "Load pdf skill"
    assert skill_read_step_description("pdf", language="en") == "Load pdf skill"


def test_skill_read_step_description_zh_cn_alias():
    assert skill_read_step_description("summarize", language="zh-CN") == "加载 summarize 技能"


def test_ensure_skill_read_first_step_uses_plan_language():
    plan = Plan(
        title="t",
        language="zh",
        steps=[Step(description="写文件")],
    )
    ensure_skill_read_first_step(plan, "openclaw-workspace")
    assert plan.steps[0].description == "加载 openclaw-workspace 技能"
    assert plan.steps[1].description == "写文件"


def test_ensure_skill_read_first_step_english_when_plan_en():
    plan = Plan(language="en", steps=[Step(description="Write SOUL.md")])
    ensure_skill_read_first_step(plan, "pdf")
    assert plan.steps[0].description == "Load pdf skill"


def test_ensure_skill_read_first_step_idempotent_when_already_first():
    desc = skill_read_step_description("pdf", language="zh")
    plan = Plan(language="zh", steps=[Step(description=desc), Step(description="Make the PDF")])
    ensure_skill_read_first_step(plan, "pdf")
    assert len(plan.steps) == 2
    assert plan.steps[0].description == desc


def test_ensure_skill_read_first_step_detects_loose_skill_md_wording():
    plan = Plan(
        steps=[
            Step(
                description="Read the SKILL.md file at /home/ubuntu/skills/pdf/SKILL.md first."
            ),
            Step(description="Create PDF"),
        ]
    )
    assert plan_already_starts_with_skill_read(plan, "pdf")
    ensure_skill_read_first_step(plan, "pdf")
    assert len(plan.steps) == 2


def test_ensure_skill_read_first_step_noop_without_name():
    plan = Plan(steps=[Step(description="Do stuff")])
    ensure_skill_read_first_step(plan, "")
    assert len(plan.steps) == 1
