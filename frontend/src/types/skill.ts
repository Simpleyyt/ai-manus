export type SkillOwnerType = 'personal' | 'official'

export type Skill = {
  id: string
  name: string
  description: string
  owner_type: SkillOwnerType
}
