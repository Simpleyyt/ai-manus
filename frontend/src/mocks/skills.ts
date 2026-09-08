import type { Skill } from '../types/skill'

/** Used for skill-creator launch prompt only; catalog lives in backend. */
export const SKILL_CREATOR: Skill = {
  id: 'skill_creator',
  name: 'skill-creator',
  description: 'Build a reusable skill together with Manus',
  owner_type: 'official',
}

/** @deprecated Tests only — prefer setSkillsStoreForTests(). */
export const MOCK_SKILLS: Skill[] = [
  {
    id: 'skill_market_research',
    name: 'market-research',
    description: 'Research markets and competitors into a structured brief',
    owner_type: 'official',
  },
]
