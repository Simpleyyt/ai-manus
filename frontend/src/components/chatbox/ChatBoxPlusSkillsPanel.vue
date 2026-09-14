<template>
  <div
    data-testid="chatbox-plus-skills-panel"
    class="w-[320px] flex flex-col p-0 max-h-[min(440px,70vh)] rounded-[12px] bg-[var(--background-menu-white)] shadow-menu overflow-hidden"
  >
    <div class="p-1 shrink-0">
      <div class="flex items-center gap-2 p-2">
        <Search :size="16" class="text-[var(--icon-tertiary)] shrink-0" />
        <input
          ref="searchInputRef"
          v-model="query"
          type="text"
          data-testid="chatbox-plus-skills-search"
          :placeholder="t('Search skills')"
          class="flex-1 bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] outline-none"
        >
      </div>
    </div>
    <div class="h-px shrink-0 bg-[var(--border-main)]" />
    <div class="flex-1 min-h-0 overflow-y-auto p-1">
      <div
        v-if="filtered.length === 0"
        class="px-1 py-4 text-center text-sm text-[var(--text-tertiary)] flex flex-col items-center gap-3"
      >
        <Puzzle :size="32" class="text-[var(--icon-tertiary)]" />
        <span>{{ hasAnySkills ? t('No results found') : t('No skills yet') }}</span>
      </div>
      <button
        v-for="skill in filtered"
        :key="skill.id"
        type="button"
        :data-testid="`chatbox-plus-skill-${skill.id}`"
        class="flex w-full items-center gap-2 rounded-[8px] p-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer"
        @mousedown.prevent
        @click="onSelect(skill)"
      >
        <div class="size-5 flex items-center justify-center shrink-0">
          <Puzzle :size="16" class="text-[var(--icon-tertiary)]" />
        </div>
        <div class="flex min-w-0 flex-1 flex-col items-start gap-0.5">
          <span class="w-full truncate text-start">{{ skill.name }}</span>
          <span class="w-full truncate text-start text-[12px] leading-4 text-[var(--text-tertiary)]">
            {{ skill.description }}
          </span>
        </div>
      </button>
    </div>
    <div class="h-px shrink-0 bg-[var(--border-main)]" />
    <div class="p-1 shrink-0">
      <div
        class="relative group/add"
        data-testid="chatbox-plus-add-skills"
        @mouseenter="addMenuOpen = true"
        @mouseleave="addMenuOpen = false"
      >
        <div
          class="flex items-center gap-[8px] p-[8px] rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer"
          :class="addMenuOpen ? 'bg-[var(--fill-tsp-white-main)]' : ''"
          @click.stop.prevent
        >
          <div class="flex items-center justify-center">
            <Plus :size="16" class="text-[var(--icon-primary)]" />
          </div>
          <span class="text-[14px] text-[var(--text-primary)]">{{ t('Add skills') }}</span>
          <ChevronRight :size="16" class="ms-auto text-[var(--icon-primary)]" />
        </div>
        <div
          v-if="addMenuOpen"
          data-testid="chatbox-plus-add-skills-menu"
          class="absolute start-full top-0 ms-1 z-10 w-[252px] rounded-[12px] bg-[var(--background-menu-white)] p-1 shadow-menu"
        >
          <button
            v-for="item in addMenuItems"
            :key="item.id"
            type="button"
            :data-testid="item.testId"
            class="flex w-full cursor-pointer items-center gap-2 rounded-[8px] p-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
            @mousedown.prevent
            @click="onAddAction(item.variant)"
          >
            <div class="flex size-5 items-center justify-center shrink-0">
              <component :is="item.icon" :size="16" class="text-[var(--icon-primary)]" />
            </div>
            <span class="truncate text-start">{{ t(item.labelKey) }}</span>
          </button>
        </div>
      </div>
      <button
        type="button"
        data-testid="chatbox-plus-manage-skills"
        class="flex w-full items-center gap-[8px] p-[8px] rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer"
        @mousedown.prevent
        @click="onManage"
      >
        <div class="flex items-center justify-center">
          <Settings2 :size="16" class="text-[var(--icon-primary)]" />
        </div>
        <span class="text-[14px] text-[var(--text-primary)]">{{ t('Manage skills') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ChevronRight,
  Github,
  MessageCircleMore,
  Plus,
  Puzzle,
  Search,
  Settings2,
  ShieldCheck,
  Upload,
} from 'lucide-vue-next'
import { useSkills } from '@/composables/useSkills'
import type { Skill } from '@/types/skill'
import type { SkillsPlaceholderVariant } from '@/components/skills/SkillsPlaceholderDialog.vue'

const emit = defineEmits<{
  (e: 'select-skill', skill: Skill): void
  (e: 'add-skill', variant: SkillsPlaceholderVariant): void
  (e: 'manage-skills'): void
  (e: 'close'): void
}>()

const props = defineProps<{
  open?: boolean
}>()

const { t } = useI18n()
const { slashSkills, filterByQuery, ensureSkillsLoaded } = useSkills()
const query = ref('')
const addMenuOpen = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)

const filtered = computed(() => filterByQuery(query.value, slashSkills.value))
const hasAnySkills = computed(() => slashSkills.value.length > 0)

const addMenuItems = [
  {
    id: 'build',
    variant: 'build' as const,
    labelKey: 'Create Skill with Manus',
    testId: 'chatbox-plus-add-build',
    icon: MessageCircleMore,
  },
  {
    id: 'upload',
    variant: 'upload' as const,
    labelKey: 'Upload a Skill',
    testId: 'chatbox-plus-add-upload',
    icon: Upload,
  },
  {
    id: 'github',
    variant: 'github' as const,
    labelKey: 'Import Skill from GitHub',
    testId: 'chatbox-plus-add-github',
    icon: Github,
  },
  {
    id: 'official',
    variant: 'official' as const,
    labelKey: 'Add from official',
    testId: 'chatbox-plus-add-official',
    icon: ShieldCheck,
  },
]

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      query.value = ''
      addMenuOpen.value = false
      return
    }
    await ensureSkillsLoaded()
    await nextTick()
    searchInputRef.value?.focus()
  },
)

onMounted(() => {
  void ensureSkillsLoaded()
})

const onSelect = (skill: Skill) => {
  emit('select-skill', skill)
  emit('close')
}

const onAddAction = (variant: SkillsPlaceholderVariant) => {
  addMenuOpen.value = false
  emit('add-skill', variant)
  emit('close')
}

const onManage = () => {
  emit('manage-skills')
  emit('close')
}
</script>
