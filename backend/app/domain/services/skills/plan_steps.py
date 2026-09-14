"""Host-side plan shaping for skill invocation — no model prompt required."""

from __future__ import annotations

from app.domain.models.plan import Plan, Step
from app.domain.skills.package import skill_md_path


def _normalize_language(language: str | None) -> str:
    raw = (language or "en").strip().lower().replace("_", "-")
    if raw.startswith("zh"):
        return "zh"
    return "en"


def skill_read_step_description(
    skill_name: str,
    *,
    language: str | None = None,
) -> str:
    """User-facing first-step label in the plan's working language."""
    name = (skill_name or "").strip()
    if _normalize_language(language) == "zh":
        return f"加载 {name} 技能"
    return f"Load {name} skill"


def plan_already_starts_with_skill_read(plan: Plan, skill_name: str) -> bool:
    if not plan.steps:
        return False
    first_raw = plan.steps[0].description or ""
    first = first_raw.lower()
    name = (skill_name or "").lower()
    path = skill_md_path(skill_name).lower()
    # Preferred UI wording (zh / en)
    if name and first_raw in {
        skill_read_step_description(name, language="zh"),
        skill_read_step_description(name, language="en"),
    }:
        return True
    if "加载" in first_raw and "技能" in first_raw and name in first:
        return True
    if first.startswith("load ") and " skill" in first and name in first:
        return True
    if "load_skill" in first and (name in first or f"/{name}" in first):
        return True
    # Legacy plans that still say "read SKILL.md" with the package path
    if path in first:
        return True
    if "skill.md" in first and (name in first or f"/skills/{name}/" in first):
        return True
    return False


def ensure_skill_read_first_step(plan: Plan, skill_name: str) -> Plan:
    """Prepend a deterministic load-skill step when a skill is active.

    Idempotent: if the first step already loads this skill, return the plan
    unchanged. Mutates and returns ``plan``. Uses ``plan.language`` for the
    user-facing step label (zh →「加载 {name} 技能」, else English).
    """
    name = (skill_name or "").strip()
    if not name:
        return plan
    if plan_already_starts_with_skill_read(plan, name):
        return plan
    plan.steps.insert(
        0,
        Step(
            description=skill_read_step_description(
                name,
                language=plan.language,
            )
        ),
    )
    return plan
