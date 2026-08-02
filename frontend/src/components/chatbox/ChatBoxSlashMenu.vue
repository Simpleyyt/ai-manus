<template>
  <div
    v-if="open"
    :class="panelClass"
    :style="positionStyle"
    :data-testid="testId"
  >
    <div :class="bodyClass">
      <button
        v-for="(item, index) in items"
        :key="item.id"
        type="button"
        :class="[rowClass, index === activeIndex ? 'bg-[var(--fill-tsp-white-main)]' : '']"
        @mousedown.prevent
        @click="emit('select', item)"
      >
        <div class="size-5 flex items-center justify-center shrink-0">
          <Paperclip :size="16" class="text-[var(--icon-tertiary)]" />
        </div>
        <span class="flex-1 min-w-0 truncate text-start">{{ t(item.titleKey) }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Paperclip } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

export type SlashMenuItem = {
  id: string
  titleKey: string
}

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

/** Official + menu: rounded-[12px] p-1 w-max (not slash rounded-xl w-[240px]). */
const panelClass = computed(() =>
  props.variant === 'plus'
    ? 'bg-[var(--background-menu-white)] shadow-menu rounded-[12px] min-w-[110px] p-1 w-max flex flex-col z-[9]'
    : 'bg-[var(--background-menu-white)] shadow-menu rounded-xl w-[240px] flex flex-col p-0 backdrop-blur-[40px] overflow-hidden z-[9]',
)

const bodyClass = computed(() =>
  props.variant === 'plus'
    ? 'flex flex-col'
    : 'hide-scroll-bar flex-1 min-h-0 max-h-[280px] overflow-y-auto py-1',
)

/** Official + row: p-2 rounded-[8px] + size-5 icon wrap. */
const rowClass = computed(() =>
  props.variant === 'plus'
    ? 'flex items-center gap-2 w-full p-2 rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer text-[var(--text-primary)] text-sm'
    : 'clickable mx-1 flex min-h-9 w-[calc(100%-8px)] items-center gap-2 rounded-lg px-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]',
)
</script>
