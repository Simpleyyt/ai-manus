<template>
  <div
    class="h-[76px] flex flex-col gap-3 p-3 rounded-[12px] border border-[var(--border-main)] clickable hover:bg-[var(--fill-tsp-white-light)]"
    data-testid="skill-card"
  >
    <div class="flex gap-3 items-center w-full">
      <div
        class="flex items-center justify-center size-10 bg-[var(--background-menu-white)] rounded-[8px] border border-[var(--border-main)] shrink-0"
      >
        <Puzzle :size="20" color="var(--icon-primary)" />
      </div>
      <div class="flex flex-col items-start justify-center min-w-0 flex-1 h-[52px]">
        <div class="w-full flex gap-1 items-center">
          <p class="truncate text-[14px] font-medium leading-[20px] text-[var(--text-primary)]">
            {{ skill.name }}
          </p>
          <span
            v-if="skill.owner_type === 'official'"
            class="flex items-center shrink-0"
            :title="t('Official skill')"
          >
            <ShieldCheck :size="16" color="var(--icon-tertiary)" />
          </span>
        </div>
        <p class="w-full text-[12px] leading-[16px] text-[var(--text-tertiary)] line-clamp-2">
          {{ skill.description }}
        </p>
      </div>
      <div @click.stop>
        <button
          v-if="mode === 'browse' && !added"
          type="button"
          data-testid="skill-card-add"
          class="flex size-7 shrink-0 items-center justify-center rounded-[8px] border border-[var(--border-main)] clickable"
          :title="t('Add')"
          @click="onAdd"
        >
          <Plus :size="14" color="var(--icon-primary)" />
        </button>
        <div
          v-else-if="mode === 'browse' && added"
          class="flex size-8 shrink-0 items-center justify-center"
        >
          <Check :size="16" color="var(--icon-tertiary)" />
        </div>
        <SettingsSwitch
          v-else
          v-model:checked="enabled"
          size="small"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Check, Plus, Puzzle, ShieldCheck } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import type { Skill } from '@/types/skill'
import SettingsSwitch from '@/components/settings/SettingsSwitch.vue'
import { useSkills } from '@/composables/useSkills'
import { showSuccessToast } from '@/utils/toast'

const props = withDefaults(defineProps<{
  skill: Skill
  mode?: 'settings' | 'browse'
  added?: boolean
  searchQuery?: string
}>(), {
  mode: 'settings',
  added: true,
  searchQuery: '',
})

const { t } = useI18n()
const { addSkills, isEnabled, setSkillEnabled } = useSkills()

const enabled = computed({
  get: () => isEnabled(props.skill.id),
  set: (value: boolean) => setSkillEnabled(props.skill.id, value),
})

const onAdd = async () => {
  await addSkills([props.skill.id])
  showSuccessToast(t('Skill added'))
}
</script>
