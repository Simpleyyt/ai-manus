<template>
  <Dialog v-model:open="open">
    <DialogContent
      :class="contentClass"
    >
      <div data-testid="skills-placeholder-dialog">
        <!-- Official uploadSkillDialog -->
        <template v-if="variant === 'upload'">
          <DialogHeader class="pt-5 px-5 pb-[10px] pe-8">
            <DialogTitle>{{ t('Upload skill') }}</DialogTitle>
          </DialogHeader>
          <div class="px-5 pb-5 space-y-4">
            <button
              type="button"
              class="w-full border-2 border-dashed border-[var(--border-dark)] rounded-xl bg-[var(--fill-tsp-white-light)] flex flex-col items-center justify-center pt-5 pb-3 px-2 hover:bg-[var(--fill-tsp-white-dark)] transition-colors cursor-pointer"
              @click="openUploadPicker"
            >
              <div class="h-[115px] flex flex-col items-center justify-center gap-3">
                <div class="relative w-[100px] h-[48px]">
                  <div class="absolute left-[10px] top-[1px] w-[38px] h-[41px] flex items-center justify-center">
                    <div
                      class="w-[33px] h-[36px] bg-[var(--background-gray-main)] border border-[var(--border-dark)] rounded-md shadow-sm opacity-60 flex items-center justify-center"
                      style="transform: rotate(-9deg)"
                    >
                      <div class="space-y-1">
                        <div class="w-[11px] h-[2.5px] bg-[#d9d9d9] rounded-full" />
                        <div class="w-[22px] h-[2.5px] bg-[#d9d9d9] rounded-full opacity-30" />
                      </div>
                    </div>
                  </div>
                  <div class="absolute left-[54px] top-[1px] w-[40px] h-[43px] flex items-center justify-center">
                    <div
                      class="w-[32px] h-[36px] bg-[var(--background-gray-main)] border border-[var(--border-dark)] rounded-md shadow-sm opacity-60 p-1"
                      style="transform: rotate(14deg)"
                    >
                      <div class="w-[20px] h-[13px] bg-[#d9d9d9] rounded-sm opacity-30 mt-2.5" />
                    </div>
                  </div>
                  <div class="absolute left-[35px] top-[10.5px] w-[31px] h-[36px] bg-[var(--background-gray-main)] border border-[var(--border-dark)] rounded-md shadow-sm flex flex-col items-center justify-center p-1">
                    <div class="space-y-1">
                      <div class="w-[18px] h-[2.5px] bg-[#d9d9d9] rounded-full" />
                      <div class="w-[14px] h-[2.5px] bg-[#d9d9d9] rounded-full opacity-50" />
                      <div class="w-[18px] h-[2.5px] bg-[#d9d9d9] rounded-full opacity-30" />
                    </div>
                  </div>
                </div>
                <p class="text-[14px] text-[var(--text-secondary)]">
                  {{ t('Drag and drop or click to upload') }}
                </p>
              </div>
            </button>

            <div class="space-y-1">
              <p class="text-[14px] text-[var(--text-primary)]">
                {{ t('File requirements') }}
              </p>
              <div class="flex items-start">
                <span class="w-4 h-5 flex items-center justify-center text-[var(--text-secondary)]">•</span>
                <p class="flex-1 text-[13px] text-[var(--text-secondary)]">
                  {{ t('.zip or .skill file that includes a SKILL.md file at the root level') }}
                </p>
              </div>
              <div class="flex items-start">
                <span class="w-4 h-5 flex items-center justify-center text-[var(--text-secondary)]">•</span>
                <p class="flex-1 text-[13px] text-[var(--text-secondary)]">
                  {{ t('SKILL.md contains a skill name and description formatted in YAML') }}
                </p>
              </div>
            </div>

            <div class="flex items-center gap-1">
              <CircleAlert :size="16" color="var(--icon-tertiary)" class="shrink-0" />
              <p class="text-[13px] text-[var(--text-tertiary)]">
                <a
                  href="https://agentskills.io/what-are-skills"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="underline clickable"
                >{{ t('Read more about creating skills') }}</a>
                {{ ' ' }}{{ t('or') }}{{ ' ' }}
                <a
                  href="https://d1oupeiobkpcny.cloudfront.net/manus-space-dispatcher/skill-creator.skill"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="underline clickable"
                >{{ t('see an example') }}</a>
              </p>
            </div>
            <input
              ref="uploadInputRef"
              type="file"
              accept=".zip,.skill"
              class="hidden"
              data-testid="skills-upload-input"
              @change="onUploadSelected"
            >
          </div>
        </template>

        <!-- Official importSkillDialog -->
        <template v-else-if="variant === 'github'">
          <DialogTitle class="sr-only">{{ t('Import from GitHub') }}</DialogTitle>
          <div class="flex min-w-0 flex-col gap-6 items-center px-6 pt-2">
            <div class="flex flex-col gap-3 items-center w-full">
              <div class="flex gap-3 items-center justify-center">
                <div class="flex items-center justify-center size-10 rounded-lg bg-[var(--background-menu-white)] border border-[var(--border-main)] shadow-[0px_6.667px_26.667px_0px_var(--shadow-XS)]">
                  <Github :size="24" color="var(--text-primary)" />
                </div>
                <ArrowLeftRight :size="16" color="var(--icon-tertiary)" />
                <div class="flex items-center justify-center size-10 rounded-lg bg-[var(--background-menu-white)] border border-[var(--border-main)] shadow-[0px_6.667px_26.667px_0px_var(--shadow-XS)]">
                  <ManusLogoMark :size="24" />
                </div>
              </div>
              <div class="flex flex-col gap-1 items-center text-center w-full">
                <h2 class="text-[20px] font-semibold text-[var(--text-primary)]">
                  {{ t('Import from GitHub') }}
                </h2>
                <p class="text-[14px] text-[var(--text-tertiary)]">
                  {{ t('Import a skill directly from a public GitHub repository.') }}
                </p>
              </div>
            </div>
            <div class="flex flex-col gap-2 w-full">
              <label for="skills-github-url" class="text-[14px] font-medium text-[var(--text-primary)]">
                {{ t('URL') }}
              </label>
              <input
                id="skills-github-url"
                v-model="githubUrl"
                data-testid="skills-github-url-input"
                type="url"
                autofocus
                placeholder="https://github.com/username/repo"
                class="w-full h-10 px-3 rounded-[10px] border border-[var(--border-main)] bg-[var(--fill-tsp-white-main)] text-[var(--text-primary)] text-sm outline-none focus:border-[var(--border-dark)] placeholder:text-[var(--text-disable)]"
                @keydown.enter.prevent="onImport"
              >
            </div>
          </div>
          <div class="p-6">
            <button
              type="button"
              data-testid="skills-github-import-button"
              class="w-full inline-flex h-11 items-center justify-center rounded-[10px] bg-[var(--Button-primary-black)] px-4 text-sm font-medium text-[var(--text-onblack)] hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!githubUrl.trim()"
              @click="onImport"
            >
              {{ t('Import') }}
            </button>
          </div>
        </template>

        <!-- Build — navigates to chat in official; shell shows info only -->
        <template v-else-if="variant === 'build'">
          <DialogTitle class="sr-only">{{ t('Create Skill with Manus') }}</DialogTitle>
          <div class="flex min-w-0 flex-col items-center gap-6 px-6 pt-2">
            <div class="flex flex-col items-center gap-3 text-center">
              <div class="flex size-10 items-center justify-center rounded-lg border border-[var(--border-main)] bg-[var(--background-menu-white)] shadow-[0px_6.667px_26.667px_0px_var(--shadow-XS)]">
                <MessageCircleMore :size="24" color="var(--icon-primary)" />
              </div>
              <div class="flex flex-col gap-1">
                <h2 class="text-[20px] font-semibold text-[var(--text-primary)]">
                  {{ t('Create Skill with Manus') }}
                </h2>
                <p class="text-[14px] text-[var(--text-tertiary)]">
                  {{ t('Opens a new chat with the skill creator to build a reusable skill together.') }}
                </p>
              </div>
            </div>
          </div>
          <div class="p-6">
            <button
              type="button"
              class="w-full inline-flex h-11 items-center justify-center rounded-[10px] bg-[var(--Button-primary-black)] px-4 text-sm font-medium text-[var(--text-onblack)] hover:opacity-90"
              @click="onBuildStart"
            >
              {{ t('Get started') }}
            </button>
          </div>
        </template>

        <!-- Official library — addFromOfficialSkillsDialog shell -->
        <template v-else-if="variant === 'official'">
          <DialogHeader class="pb-0 pt-5 px-5 pe-8">
            <DialogTitle>{{ t('Official library') }}</DialogTitle>
          </DialogHeader>
          <div class="flex flex-col p-0">
            <div class="px-5 pb-2 pt-4">
              <div
                class="flex h-8 max-w-52 items-center gap-1.5 rounded-lg bg-transparent px-3 py-1 text-[13px] ring-1 ring-[var(--border-dark)] focus-within:bg-[var(--fill-tsp-white-light)] focus-within:ring-[var(--border-input-active)]"
              >
                <Search :size="16" color="var(--icon-secondary)" class="shrink-0" />
                <input
                  v-model="officialQuery"
                  type="text"
                  data-testid="skills-official-search"
                  :placeholder="t('Search Skill')"
                  class="min-w-0 flex-1 border-none bg-transparent outline-none placeholder:text-[var(--text-disable)]"
                >
              </div>
            </div>
            <div class="h-[400px] overflow-y-auto px-5">
              <div
                v-if="filteredOfficial.length === 0"
                class="flex h-full flex-col items-center justify-center gap-3 text-sm text-[var(--text-tertiary)]"
              >
                <Search :size="32" color="var(--icon-tertiary)" />
                <span>{{ t('No results found') }}</span>
              </div>
              <div v-else class="space-y-0">
                <button
                  v-for="skill in filteredOfficial"
                  :key="skill.id"
                  type="button"
                  data-testid="skills-official-row"
                  class="flex w-full items-start gap-4 border-b border-[var(--border-main)] py-4 text-start last:border-b-0 clickable"
                  :class="isOfficialAlreadyAdded(skill.id) ? 'cursor-not-allowed opacity-50' : ''"
                  :disabled="isOfficialAlreadyAdded(skill.id)"
                  @click="toggleOfficialSelection(skill.id)"
                >
                  <div class="min-w-0 flex-1 space-y-1">
                    <div class="flex items-center space-x-1">
                      <span class="text-[14px] font-medium text-[var(--text-primary)]">
                        {{ skill.name }}
                      </span>
                    </div>
                    <p class="line-clamp-2 text-[13px] text-[var(--text-tertiary)]">
                      {{ skill.description }}
                    </p>
                  </div>
                  <span
                    class="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-[4px] border"
                    :class="isOfficialSelected(skill.id)
                      ? 'border-[var(--icon-blue)] bg-[var(--icon-blue)]'
                      : 'border-[var(--border-dark)] bg-transparent'"
                  >
                    <Check
                      v-if="isOfficialSelected(skill.id) || isOfficialAlreadyAdded(skill.id)"
                      :size="14"
                      color="var(--icon-white)"
                    />
                  </span>
                </button>
              </div>
            </div>
            <DialogFooter class="px-5 pb-5 pt-4">
              <button
                type="button"
                class="inline-flex h-9 min-w-[72px] items-center justify-center rounded-lg border border-[var(--Button-border-secondary)] px-4 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-light)]"
                @click="open = false"
              >
                {{ t('Cancel') }}
              </button>
              <button
                type="button"
                data-testid="skills-official-add-button"
                class="inline-flex h-9 min-w-[72px] items-center justify-center rounded-lg bg-[var(--Button-primary-black)] px-4 text-sm font-medium text-[var(--text-onblack)] hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                :disabled="selectedOfficialIds.size === 0"
                @click="onOfficialAdd"
              >
                {{ t('Add') }}
              </button>
            </DialogFooter>
          </div>
        </template>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeftRight, Check, CircleAlert, Github, MessageCircleMore, Search } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useSkills } from '@/composables/useSkills'
import { useSettingsDialog } from '@/composables/useSettingsDialog'
import { setPendingHomeDraft } from '@/composables/usePendingHomeMessage'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import ManusLogoMark from '@/components/icons/ManusLogoMark.vue'

export type SkillsPlaceholderVariant = 'build' | 'upload' | 'github' | 'official'

const props = defineProps<{
  variant: SkillsPlaceholderVariant
}>()

const open = defineModel<boolean>('open', { required: true })

const { t } = useI18n()
const router = useRouter()
const { closeSettingsDialog } = useSettingsDialog()
const {
  addSkills,
  filterByQuery,
  importSkillFromGitHub,
  importSkillFromUpload,
  launchSkillCreatorFlow,
  officialCatalog,
  isAdded,
} = useSkills()
const githubUrl = ref('')
const officialQuery = ref('')
const selectedOfficialIds = ref<Set<string>>(new Set())
const uploadInputRef = ref<HTMLInputElement | null>(null)

watch(open, (isOpen) => {
  if (!isOpen) {
    githubUrl.value = ''
    officialQuery.value = ''
    selectedOfficialIds.value = new Set()
  }
})

const contentClass = computed(() => {
  if (props.variant === 'official') {
    return 'w-[680px] max-w-[98%] overflow-x-hidden rounded-[20px] border border-[var(--border-main)] bg-[var(--background-gray-main)] p-0 shadow-menu'
  }
  if (props.variant === 'upload' || props.variant === 'github' || props.variant === 'build') {
    return 'w-[400px] max-w-[98%] overflow-x-hidden rounded-[20px] border border-[var(--border-main)] bg-[var(--background-gray-main)] shadow-menu'
  }
  return 'w-[380px] max-w-[98%] rounded-[16px] border-0 shadow-menu'
})

const onImport = async () => {
  if (!githubUrl.value.trim()) return
  try {
    await importSkillFromGitHub(githubUrl.value)
    showSuccessToast(t('Skill added'))
    open.value = false
  } catch {
    showErrorToast(t('Invalid GitHub URL'))
  }
}

const openUploadPicker = () => {
  uploadInputRef.value?.click()
}

const onUploadSelected = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  try {
    await importSkillFromUpload(file)
    showSuccessToast(t('Skill added'))
    open.value = false
  } catch {
    showErrorToast(t('Invalid skill file name'))
  }
}

const filteredOfficial = computed(() =>
  filterByQuery(officialQuery.value, officialCatalog.value),
)

const isOfficialAlreadyAdded = (skillId: string) => isAdded(skillId)

const isOfficialSelected = (skillId: string) => selectedOfficialIds.value.has(skillId)

const toggleOfficialSelection = (skillId: string) => {
  if (isOfficialAlreadyAdded(skillId)) return
  const next = new Set(selectedOfficialIds.value)
  if (next.has(skillId)) next.delete(skillId)
  else next.add(skillId)
  selectedOfficialIds.value = next
}

const onOfficialAdd = async () => {
  if (selectedOfficialIds.value.size === 0) return
  const addedItems = await addSkills([...selectedOfficialIds.value])
  if (addedItems.length > 0) {
    showSuccessToast(
      addedItems.length > 1
        ? t('Added {count} Skills', { count: addedItems.length })
        : t('Skill added'),
    )
  }
  open.value = false
}

const onBuildStart = async () => {
  try {
    const skill = await launchSkillCreatorFlow()
    setPendingHomeDraft({
      before: t('Help me create a skill together using '),
      skill: {
        skillId: skill.id,
        name: skill.name,
        description: skill.description,
        ownerType: skill.owner_type,
      },
      after: t(' to create a skill. First ask me what the skill should do.'),
    })
    closeSettingsDialog()
    open.value = false
    await router.push('/')
  } catch {
    // stay on dialog
  }
}
</script>
