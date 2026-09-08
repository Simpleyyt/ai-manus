<template>
  <div
    v-if="open"
    :class="panelClass"
    :style="positionStyle"
    :data-testid="testId"
  >
    <div :class="bodyClass">
      <template v-for="entry in renderedEntries" :key="entry.key">
        <div
          v-if="entry.type === 'section'"
          class="px-2 pt-1 pb-0.5 text-[13px] text-[var(--text-tertiary)]"
        >
          {{ t(entry.labelKey) }}
        </div>
        <button
          v-else
          type="button"
          :class="[rowClass, entry.activeIndex === activeIndex ? 'bg-[var(--fill-tsp-white-main)]' : '']"
          :data-testid="entry.item.kind === 'skill' ? `slash-skill-${entry.item.id}` : `slash-${entry.item.id}`"
          @mousedown.prevent
          @click="emit('select', entry.item)"
        >
          <div class="size-5 flex items-center justify-center shrink-0">
            <Puzzle
              v-if="entry.item.kind === 'skill'"
              :size="16"
              class="text-[var(--icon-tertiary)]"
            />
            <Paperclip
              v-else
              :size="16"
              class="text-[var(--icon-tertiary)]"
            />
          </div>
          <div class="flex min-w-0 flex-1 flex-col items-start gap-0.5">
            <span class="w-full truncate text-start">{{ displayTitle(entry.item) }}</span>
            <span
              v-if="entry.item.kind === 'skill'"
              class="w-full truncate text-start text-[12px] leading-4 text-[var(--text-tertiary)]"
            >
              {{ entry.item.description }}
            </span>
          </div>
        </button>
        <div
          v-if="entry.type === 'item' && entry.showDividerAfter"
          class="mx-2 my-1 h-px bg-[var(--border-main)]"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Paperclip, Puzzle } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import type { SlashItem } from './slashSuggestion'

export type SlashMenuItem = SlashItem

const props = withDefaults(
  defineProps<{
    open: boolean
    items: SlashMenuItem[]
    positionStyle?: Record<string, string> | string
    activeIndex?: number
    testId?: string
    /** Official + popover vs / suggestion panel (different mined shells). */
    variant?: 'plus' | 'slash'
  }>(),
  {
    positionStyle: undefined,
    activeIndex: -1,
    testId: 'chatbox-slash-menu',
    variant: 'slash',
  },
)

const emit = defineEmits<{
  (e: 'select', item: SlashMenuItem): void
}>()

const { t } = useI18n()

const panelClass = computed(() =>
  props.variant === 'plus'
    ? 'bg-[var(--background-menu-white)] shadow-menu rounded-[12px] min-w-[110px] p-1 w-max flex flex-col z-[9]'
    : 'pointer-events-auto overflow-hidden rounded-[12px] p-[12px] border border-[var(--border-dark)] bg-[var(--background-menu-white)] shadow-[0_8px_32px_0_var(--shadow-XS,rgba(0,0,0,0.06))] w-[240px] flex flex-col backdrop-blur-[40px] z-[9]',
)

const bodyClass = computed(() =>
  props.variant === 'plus'
    ? 'flex flex-col'
    : 'hide-scroll-bar flex-1 min-h-0 max-h-[280px] overflow-y-auto',
)

const rowClass = computed(() =>
  props.variant === 'plus'
    ? 'flex items-center gap-2 w-full p-2 rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer text-[var(--text-primary)] text-sm'
    : 'clickable mx-0 flex min-h-9 w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]',
)

type RenderEntry =
  | { type: 'section'; key: string; labelKey: string }
  | {
      type: 'item'
      key: string
      item: SlashMenuItem
      activeIndex: number
      showDividerAfter?: boolean
    }

const renderedEntries = computed((): RenderEntry[] => {
  if (props.variant === 'plus') {
    return props.items.map((item, index) => ({
      type: 'item' as const,
      key: item.id,
      item,
      activeIndex: index,
    }))
  }

  const entries: RenderEntry[] = []
  let flatIndex = 0
  const skillItems = props.items.filter((item) => item.kind === 'skill')
  const localItems = props.items.filter((item) => item.kind === 'local')

  if (skillItems.length > 0) {
    entries.push({ type: 'section', key: 'section-skills', labelKey: 'Skills' })
    skillItems.forEach((item) => {
      entries.push({
        type: 'item',
        key: item.id,
        item,
        activeIndex: flatIndex,
      })
      flatIndex += 1
    })
  }

  if (localItems.length > 0) {
    if (skillItems.length > 0) {
      const lastSkill = entries[entries.length - 1]
      if (lastSkill?.type === 'item') {
        lastSkill.showDividerAfter = true
      }
    }
    localItems.forEach((item) => {
      entries.push({
        type: 'item',
        key: item.id,
        item,
        activeIndex: flatIndex,
      })
      flatIndex += 1
    })
  }

  return entries
})

const displayTitle = (item: SlashMenuItem) => {
  if (item.kind === 'skill') return `/${item.name}`
  return t(item.titleKey)
}
</script>
