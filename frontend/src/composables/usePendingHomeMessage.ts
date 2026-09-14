import { ref } from 'vue'

export type PendingSkillChip = {
  skillId: string
  name: string
  description?: string
  ownerType?: string
}

/** Prefill home ChatBox with text + skillTag (official Create Skill with Manus). */
export type PendingHomeDraft = {
  before: string
  skill: PendingSkillChip
  after: string
}

const pendingHomeDraft = ref<PendingHomeDraft | null>(null)

export function setPendingHomeDraft(draft: PendingHomeDraft): void {
  pendingHomeDraft.value = draft
}

export function consumePendingHomeDraft(): PendingHomeDraft | null {
  const draft = pendingHomeDraft.value
  pendingHomeDraft.value = null
  return draft
}

/** @deprecated Prefer setPendingHomeDraft — plain text cannot carry skill chips. */
export function setPendingHomeMessage(message: string): void {
  pendingHomeDraft.value = {
    before: message,
    skill: { skillId: '', name: '' },
    after: '',
  }
}

/** @deprecated Prefer consumePendingHomeDraft */
export function consumePendingHomeMessage(): string | null {
  const draft = consumePendingHomeDraft()
  if (!draft) return null
  if (!draft.skill.name) return `${draft.before}${draft.after}` || null
  return `${draft.before}/${draft.skill.name}${draft.after}`
}

export { pendingHomeDraft }
