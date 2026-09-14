<template>
  <div
    v-if="open"
    data-testid="chatbox-plus-menu"
    class="bg-[var(--background-menu-white)] shadow-menu rounded-[12px] min-w-[110px] p-1 w-max flex flex-col z-[9]"
    :style="positionStyle"
  >
    <div
      class="relative group/skills"
      data-testid="chatbox-plus-use-skills"
      @mouseenter="skillsOpen = true"
      @mouseleave="skillsOpen = false"
    >
      <div
        class="flex items-center gap-2 w-full p-2 rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer text-[var(--text-primary)] text-sm"
        :class="skillsOpen ? 'bg-[var(--fill-tsp-white-main)]' : ''"
        @click.stop.prevent
      >
        <div class="size-5 flex items-center justify-center shrink-0">
          <Puzzle :size="16" class="text-[var(--icon-tertiary)]" />
        </div>
        <span class="flex-1 min-w-0 truncate text-start">{{ t('Use skills') }}</span>
        <ChevronRight :size="16" class="ms-2 shrink-0 text-[var(--icon-tertiary)]" />
      </div>
      <div
        v-if="skillsOpen"
        class="absolute start-full bottom-0 ms-1 z-10"
      >
        <ChatBoxPlusSkillsPanel
          :open="skillsOpen"
          @select-skill="onSelectSkill"
          @add-skill="onAddSkill"
          @manage-skills="onManageSkills"
          @close="onSkillsClose"
        />
      </div>
    </div>

    <button
      type="button"
      data-testid="slash-add_local_files"
      class="flex items-center gap-2 w-full p-2 rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer text-[var(--text-primary)] text-sm"
      @mousedown.prevent
      @click="onAddLocalFiles"
    >
      <div class="size-5 flex items-center justify-center shrink-0">
        <Paperclip :size="16" class="text-[var(--icon-tertiary)]" />
      </div>
      <span class="w-full truncate text-start">{{ t('Add local files') }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronRight, Paperclip, Puzzle } from 'lucide-vue-next'
import ChatBoxPlusSkillsPanel from './ChatBoxPlusSkillsPanel.vue'
import type { Skill } from '@/types/skill'
import type { SkillsPlaceholderVariant } from '@/components/skills/SkillsPlaceholderDialog.vue'

const props = defineProps<{
  open: boolean
  positionStyle?: Record<string, string> | string
}>()

const emit = defineEmits<{
  (e: 'add-local-files'): void
  (e: 'select-skill', skill: Skill): void
  (e: 'add-skill', variant: SkillsPlaceholderVariant): void
  (e: 'manage-skills'): void
  (e: 'close'): void
}>()

const { t } = useI18n()
const skillsOpen = ref(false)

watch(
  () => props.open,
  (open) => {
    if (!open) skillsOpen.value = false
  },
)

const onAddLocalFiles = () => {
  emit('add-local-files')
  emit('close')
}

const onSelectSkill = (skill: Skill) => {
  emit('select-skill', skill)
  emit('close')
}

const onAddSkill = (variant: SkillsPlaceholderVariant) => {
  emit('add-skill', variant)
  emit('close')
}

const onManageSkills = () => {
  emit('manage-skills')
  emit('close')
}

const onSkillsClose = () => {
  skillsOpen.value = false
  emit('close')
}
</script>
