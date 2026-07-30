<template>
  <div
    v-show="open"
    class="bg-[var(--background-menu-white)] shadow-menu rounded-xl w-[240px] flex flex-col p-0 backdrop-blur-[40px] overflow-hidden z-[9]"
    :style="positionStyle"
    data-testid="chatbox-slash-menu"
  >
    <div class="hide-scroll-bar flex-1 min-h-0 max-h-[280px] overflow-y-auto py-1">
      <button
        v-for="(item, index) in items"
        :key="item.id"
        type="button"
        class="clickable mx-1 flex min-h-9 w-[calc(100%-8px)] items-center gap-2 rounded-lg px-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
        :class="index === activeIndex ? 'bg-[var(--fill-tsp-white-main)]' : ''"
        @click="emit('select', item)"
      >
        <Paperclip :size="16" class="text-[var(--icon-tertiary)]" />
        {{ t(item.titleKey) }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Paperclip } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

export type SlashMenuItem = {
  id: string
  titleKey: string
}

withDefaults(
  defineProps<{
    open: boolean
    items: SlashMenuItem[]
    positionStyle?: Record<string, string> | string
    activeIndex?: number
  }>(),
  {
    positionStyle: undefined,
    activeIndex: -1,
  },
)

const emit = defineEmits<{
  (e: 'select', item: SlashMenuItem): void
}>()

const { t } = useI18n()
</script>
