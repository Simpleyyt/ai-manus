<template>
  <Dialog v-model:open="open">
    <DialogContent
      class="flex h-[680px] w-[800px] max-w-[98%] flex-col overflow-hidden border border-[var(--border-main)] bg-[var(--background-gray-main)] p-0 shadow-menu"
    >
      <div class="flex min-h-0 flex-1 flex-col" data-testid="skills-browse-dialog">
      <DialogHeader>
        <DialogTitle>{{ t('Skills') }}</DialogTitle>
      </DialogHeader>

      <div class="flex min-h-0 flex-1 flex-col gap-3 px-6 pb-3">
        <div
          class="flex h-8 items-center gap-[6px] rounded-[8px] bg-[var(--fill-tsp-white-light)] px-2 focus-within:ring-1 focus-within:ring-[var(--border-input-active)]"
        >
          <div class="flex size-5 shrink-0 items-center justify-center">
            <Search :size="16" color="var(--icon-tertiary)" />
          </div>
          <input
            v-model="query"
            type="text"
            data-testid="skills-browse-search"
            :placeholder="t('Search Skills')"
            class="min-w-0 flex-1 border-none bg-transparent px-1 text-[14px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-disable)]"
          >
        </div>

        <div class="flex w-full items-center justify-between gap-3">
          <div class="flex flex-wrap items-center gap-2">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              :data-testid="`skills-browse-tab-${tab.id}`"
              class="h-8 px-3 py-1 text-[14px] font-medium clickable hover:opacity-80"
              :class="activeTab === tab.id
                ? 'rounded-[999px] bg-[var(--fill-tsp-white-light)] text-[var(--text-primary)]'
                : 'rounded-[8px] text-[var(--text-tertiary)]'"
              @click="activeTab = tab.id"
            >
              {{ t(tab.labelKey) }}
            </button>
          </div>
          <SkillsCreateMenu />
        </div>

        <div
          v-if="showTeamEmpty"
          class="flex min-h-0 flex-1 flex-col items-center justify-center gap-3 px-6 pb-6"
        >
          <Puzzle :size="32" color="var(--icon-tertiary)" />
          <p class="text-center text-[14px] font-medium text-[var(--text-primary)]">
            {{ t('No Team skills yet') }}
          </p>
        </div>

        <div
          v-else-if="showPersonalEmpty"
          class="flex min-h-0 flex-1 flex-col items-center justify-center gap-3 px-6 pb-6"
        >
          <Puzzle :size="32" color="var(--icon-tertiary)" />
          <p class="text-center text-[14px] font-medium text-[var(--text-primary)]">
            {{ t('No skills yet') }}
          </p>
          <SkillsCreateMenu />
        </div>

        <div
          v-else-if="showNoResults"
          class="min-h-0 flex-1 px-6 pb-6"
        >
          <div class="flex h-full flex-col items-center justify-center gap-3">
            <Search :size="32" color="var(--icon-tertiary)" />
            <p class="text-sm text-[var(--text-tertiary)]">
              {{ t('No results found') }}
            </p>
          </div>
        </div>

        <div
          v-else
          class="min-h-0 flex-1 overflow-y-auto"
        >
          <div class="flex flex-col gap-3 px-0 pb-6">
            <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
              <SkillCard
                v-for="skill in filteredSkills"
                :key="skill.id"
                :skill="skill"
                :search-query="query"
                mode="browse"
                :added="isAdded(skill.id)"
              />
            </div>
          </div>
        </div>
      </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Puzzle, Search } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useSkills } from '@/composables/useSkills'
import SkillCard from '@/components/skills/SkillCard.vue'
import SkillsCreateMenu from '@/components/skills/SkillsCreateMenu.vue'

type BrowseTab = 'official' | 'personal' | 'team'

const open = defineModel<boolean>('open', { required: true })

const { t } = useI18n()
const { catalog, filterByQuery, isAdded } = useSkills()

const query = ref('')
const activeTab = ref<BrowseTab>('official')

const tabs: { id: BrowseTab; labelKey: string }[] = [
  { id: 'official', labelKey: 'Official' },
  { id: 'personal', labelKey: 'Personal' },
  { id: 'team', labelKey: 'Team' },
]

watch(open, (isOpen) => {
  if (!isOpen) {
    query.value = ''
    activeTab.value = 'official'
  }
})

const tabSkills = computed(() => {
  if (activeTab.value === 'team') return []
  return catalog.value.filter((skill) => skill.owner_type === activeTab.value)
})

const filteredSkills = computed(() => filterByQuery(query.value, tabSkills.value))

const showTeamEmpty = computed(
  () => activeTab.value === 'team' && query.value.trim() === '',
)
const showPersonalEmpty = computed(
  () =>
    activeTab.value === 'personal' &&
    query.value.trim() === '' &&
    tabSkills.value.length === 0,
)
const showNoResults = computed(
  () => query.value.trim() !== '' && filteredSkills.value.length === 0,
)
</script>
