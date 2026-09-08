from app.domain.models.skill import Skill, SkillOwnerType, SkillSource

OFFICIAL_SKILLS: list[Skill] = [
    Skill(
        id="skill_creator",
        name="skill-creator",
        description="Build a reusable skill together with Manus",
        owner_type=SkillOwnerType.OFFICIAL,
        source=SkillSource.CATALOG,
    ),
    Skill(
        id="skill_market_research",
        name="market-research",
        description="Research markets and competitors into a structured brief",
        owner_type=SkillOwnerType.OFFICIAL,
        source=SkillSource.CATALOG,
    ),
    Skill(
        id="skill_slides",
        name="slides",
        description="Turn an outline into presentation slides",
        owner_type=SkillOwnerType.OFFICIAL,
        source=SkillSource.CATALOG,
    ),
    Skill(
        id="skill_web_research",
        name="web-research",
        description="Search the web and synthesize findings with citations",
        owner_type=SkillOwnerType.OFFICIAL,
        source=SkillSource.CATALOG,
    ),
    Skill(
        id="skill_summarize",
        name="summarize",
        description="Summarize long documents into concise takeaways",
        owner_type=SkillOwnerType.OFFICIAL,
        source=SkillSource.CATALOG,
    ),
]

OFFICIAL_SKILL_IDS = {skill.id for skill in OFFICIAL_SKILLS}
OFFICIAL_SKILL_BY_ID = {skill.id: skill for skill in OFFICIAL_SKILLS}

DEFAULT_ADDED_OFFICIAL_SKILL_IDS = [
    "skill_creator",
    "skill_web_research",
    "skill_summarize",
    "skill_slides",
]

DEFAULT_PERSONAL_SKILL = {
    "name": "data-viz",
    "description": "Plot CSV data with clear charts",
    "body": (
        "# Data Visualization\n\n"
        "Load the user's CSV, pick appropriate chart types, and save plots to files "
        "with clear labels and legends."
    ),
}
