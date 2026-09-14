<template>
  <Popover v-model:open="menuOpen">
    <PopoverTrigger as-child>
      <button
        type="button"
        data-testid="skills-create-button"
        class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 h-8 min-w-[56px] px-3 rounded-[8px] gap-1 text-[13px] leading-[18px] outline outline-1 -outline-offset-1 hover:bg-[var(--fill-tsp-white-light)] text-[var(--text-primary)] outline-[var(--Button-border-secondary)] bg-transparent clickable"
        :aria-expanded="menuOpen"
        aria-haspopup="dialog"
      >
        {{ t('Create') }}
        <ChevronDown :size="16" color="var(--icon-primary)" />
      </button>
    </PopoverTrigger>
    <PopoverContent
      align="end"
      side="bottom"
      :side-offset="4"
      class="z-[1100] w-[252px] rounded-[12px] border-0 bg-[var(--background-menu-white)] p-1 shadow-menu"
      data-testid="skills-create-menu"
    >
      <button
        v-for="item in menuItems"
        :key="item.id"
        type="button"
        :data-testid="item.testId"
        class="flex w-full cursor-pointer items-center gap-2 rounded-[8px] p-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
        @click="selectItem(item.variant)"
      >
        <div class="flex size-5 items-center justify-center shrink-0">
          <component :is="item.icon" :size="16" color="var(--icon-primary)" />
        </div>
        <span class="truncate text-start">{{ t(item.labelKey) }}</span>
      </button>
    </PopoverContent>
  </Popover>

  <SkillsPlaceholderDialog
    v-for="variant in placeholderVariants"
    :key="variant"
    v-model:open="dialogOpen[variant]"
    :variant="variant"
  />
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronDown, Github, MessageCircleMore, ShieldCheck, Upload } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import SkillsPlaceholderDialog, {
  type SkillsPlaceholderVariant,
} from './SkillsPlaceholderDialog.vue'
import { launchSkillCreatorFlow } from '@/composables/skillsStore'
import { setPendingHomeDraft } from '@/composables/usePendingHomeMessage'
import { useSettingsDialog } from '@/composables/useSettingsDialog'

const { t } = useI18n()
const router = useRouter()
const { closeSettingsDialog } = useSettingsDialog()
const menuOpen = ref(false)

const placeholderVariants: SkillsPlaceholderVariant[] = [
  'build',
  'upload',
  'github',
  'official',
]

const dialogOpen = reactive<Record<SkillsPlaceholderVariant, boolean>>({
  build: false,
  upload: false,
  github: false,
  official: false,
})

const menuItems = [
  {
    id: 'build',
    variant: 'build' as const,
    labelKey: 'Create Skill with Manus',
    testId: 'skills-create-build',
    icon: MessageCircleMore,
  },
  {
    id: 'upload',
    variant: 'upload' as const,
    labelKey: 'Upload a Skill',
    testId: 'skills-create-upload',
    icon: Upload,
  },
  {
    id: 'github',
    variant: 'github' as const,
    labelKey: 'Import Skill from GitHub',
    testId: 'skills-create-github',
    icon: Github,
  },
  {
    id: 'official',
    variant: 'official' as const,
    labelKey: 'Add from official',
    testId: 'skills-create-official',
    icon: ShieldCheck,
  },
]

const selectItem = async (variant: SkillsPlaceholderVariant) => {
  menuOpen.value = false
  if (variant === 'build') {
    await startCreateSkillWithManus()
    return
  }
  dialogOpen[variant] = true
}

async function startCreateSkillWithManus() {
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
    await router.push('/')
  } catch {
    // keep settings open on failure
  }
}
</script>
