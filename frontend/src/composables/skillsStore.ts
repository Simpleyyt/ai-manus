import { computed, ref } from 'vue'
import {
  addSkills as addSkillsApi,
  fetchSkillsState,
  importSkillFromGitHub as importSkillFromGitHubApi,
  importSkillFromUpload as importSkillFromUploadApi,
  setSkillEnabled as setSkillEnabledApi,
  type AddedSkill,
} from '@/api/skills'
import type { Skill } from '@/types/skill'

const catalog = ref<Skill[]>([])
const added = ref<AddedSkill[]>([])
const loading = ref(false)
const loaded = ref(false)
const loadError = ref<string | null>(null)

let loadPromise: Promise<void> | null = null

function applyState(state: { catalog: Skill[]; added: AddedSkill[] }) {
  catalog.value = state.catalog
  added.value = state.added
  loaded.value = true
}

export async function reloadSkills(): Promise<void> {
  loading.value = true
  loadError.value = null
  try {
    applyState(await fetchSkillsState())
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : 'Failed to load skills'
    throw error
  } finally {
    loading.value = false
  }
}

export async function ensureSkillsLoaded(): Promise<void> {
  if (loaded.value) return
  if (!loadPromise) {
    loadPromise = reloadSkills().finally(() => {
      loadPromise = null
    })
  }
  await loadPromise
}

export const skills = computed(() => added.value)
export const slashSkills = computed(() => added.value.filter((skill) => skill.enabled))
export const officialCatalog = computed(() =>
  catalog.value.filter((skill) => skill.owner_type === 'official'),
)

const addedIds = computed(() => new Set(added.value.map((skill) => skill.id)))

export function filterSkillsByQuery(query: string, source: Skill[] = added.value): Skill[] {
  const q = query.trim().toLowerCase()
  if (!q) return source
  return source.filter(
    (skill) =>
      skill.name.toLowerCase().includes(q) ||
      skill.description.toLowerCase().includes(q),
  )
}

export function isSkillAdded(skillId: string): boolean {
  return addedIds.value.has(skillId)
}

export function isSkillEnabled(skillId: string): boolean {
  return added.value.some((skill) => skill.id === skillId && skill.enabled)
}

export function getSkillById(skillId: string): Skill | undefined {
  return catalog.value.find((skill) => skill.id === skillId)
    ?? added.value.find((skill) => skill.id === skillId)
}

export async function addSkills(skillIds: string[]): Promise<Skill[]> {
  const state = await addSkillsApi(skillIds)
  applyState(state)
  return state.added.filter((skill) => skillIds.includes(skill.id))
}

export async function setSkillEnabled(skillId: string, enabled: boolean): Promise<void> {
  await setSkillEnabledApi(skillId, enabled)
  const item = added.value.find((skill) => skill.id === skillId)
  if (item) item.enabled = enabled
}

export async function importSkillFromGitHub(url: string): Promise<AddedSkill> {
  const skill = await importSkillFromGitHubApi(url)
  await reloadSkills()
  return skill
}

export async function importSkillFromUpload(file: File): Promise<AddedSkill> {
  const skill = await importSkillFromUploadApi(file)
  await reloadSkills()
  return skill
}

/** Ensure official skill-creator is added+enabled; returns catalog skill for chip attrs. */
export async function launchSkillCreatorFlow(): Promise<Skill> {
  await addSkills(['skill_creator'])
  const skill =
    getSkillById('skill_creator') ||
    added.value.find((item) => item.id === 'skill_creator' || item.name === 'skill-creator')
  if (!skill) {
    throw new Error('skill-creator not found after add')
  }
  return skill
}

/** Vitest helper — reset in-memory store between tests. */
export function resetSkillsStoreForTests(): void {
  catalog.value = []
  added.value = []
  loading.value = false
  loaded.value = false
  loadError.value = null
  loadPromise = null
}

export function setSkillsStoreForTests(state: {
  catalog?: Skill[]
  added?: AddedSkill[]
}): void {
  catalog.value = state.catalog ?? []
  added.value = state.added ?? []
  loaded.value = true
}

export { catalog, added, loading, loaded, loadError }
