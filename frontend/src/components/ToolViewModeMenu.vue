<template>
  <!-- Official ToolViewModeMenu -->
  <div
    class="flex h-[32px] overflow-hidden rounded-[8px] text-[var(--icon-secondary)]"
    :class="className">
    <button
      type="button"
      class="clickable flex h-full w-[28px] items-center justify-center hover:bg-[var(--fill-tsp-white-main)]"
      :class="buttonClassName"
      :title="toggleTitle"
      @click="toggleFullscreen">
      <component :is="toggleIcon" :size="18" color="currentColor" />
    </button>

    <Popover v-model:open="menuOpen">
      <PopoverTrigger as-child>
        <button
          type="button"
          class="clickable flex h-full w-[18px] items-center justify-center hover:bg-[var(--fill-tsp-white-main)] data-[state=open]:bg-[var(--fill-tsp-white-main)]"
          :class="buttonClassName"
          :title="t('View')"
          :aria-expanded="menuOpen"
          aria-haspopup="dialog">
          <ChevronDown :size="13" color="currentColor" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        side="bottom"
        :side-offset="4"
        class="z-[1100] w-[220px] min-w-[110px] rounded-[12px] border-0 bg-[var(--background-menu-white)] p-1 shadow-menu">
        <!-- Official DropdownMenu.w-[220px] — disabled: side && !canUseSide -->
        <div
          v-for="opt in viewOptions"
          :key="opt.value"
          :class="itemClass(isModeDisabled(opt.value))"
          @click="selectMode(opt.value)">
          <div class="flex size-5 items-center justify-center">
            <component
              :is="opt.icon"
              :size="16"
              :color="isModeDisabled(opt.value) ? 'var(--icon-disable)' : 'var(--icon-primary)'"
            />
          </div>
          <div class="flex min-w-0 flex-1 items-center gap-2">
            {{ opt.label }}
          </div>
          <div
            v-if="viewMode === opt.value"
            class="flex size-5 items-center justify-center self-center">
            <Check :size="16" color="currentColor" />
          </div>
        </div>

        <div class="my-[2px] h-px w-full bg-[var(--border-main)]" />

        <!-- Official Edit default view + hover submenu (side not disabled here) -->
        <Popover v-model:open="defaultMenuOpen">
          <PopoverTrigger as-child>
            <div
              class="flex w-full cursor-pointer items-center gap-2 rounded-[8px] p-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
              @click.prevent.stop>
              <div class="flex size-5 items-center justify-center">
                <SlidersHorizontal :size="16" color="var(--icon-primary)" />
              </div>
              <div class="flex min-w-0 flex-1 items-center gap-2">
                {{ t('Edit default view') }}
              </div>
              <ChevronRight :size="16" color="var(--icon-secondary)" class="ms-auto" />
            </div>
          </PopoverTrigger>
          <PopoverContent
            side="right"
            align="start"
            :side-offset="4"
            class="z-[1100] w-[200px] min-w-[110px] rounded-[12px] border-0 bg-[var(--background-menu-white)] p-1 shadow-menu">
            <div
              v-for="opt in viewOptions"
              :key="`default-${opt.value}`"
              class="flex w-full cursor-pointer items-center gap-2 rounded-[8px] p-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
              @click="selectDefaultMode(opt.value)">
              <div class="flex size-5 items-center justify-center">
                <component :is="opt.icon" :size="16" color="var(--icon-primary)" />
              </div>
              <div class="flex min-w-0 flex-1 items-center gap-2">
                {{ opt.label }}
              </div>
              <div
                v-if="defaultViewMode === opt.value"
                class="flex size-5 items-center justify-center self-center">
                <Check :size="16" color="currentColor" />
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </PopoverContent>
    </Popover>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Check, ChevronDown, ChevronRight, SlidersHorizontal } from 'lucide-vue-next'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import CenterViewIcon from './icons/CenterViewIcon.vue'
import FullViewIcon from './icons/FullViewIcon.vue'
import SideViewIcon from './icons/SideViewIcon.vue'
import type { FilePreviewViewMode } from '../composables/useFilePreviewer'
import { useFilePreviewer } from '../composables/useFilePreviewer'

withDefaults(defineProps<{
  className?: string
  buttonClassName?: string
}>(), {
  className: '',
  buttonClassName: '',
})

const { t } = useI18n()
const {
  viewMode,
  defaultViewMode,
  fullscreenReturnViewMode,
  canUseSideFilePreview,
  setViewMode,
  exitFullscreen,
  setDefaultViewMode,
} = useFilePreviewer()

const menuOpen = ref(false)
const defaultMenuOpen = ref(false)

const viewOptions = computed(() => [
  { value: 'side' as const, label: t('Side'), icon: SideViewIcon },
  { value: 'center' as const, label: t('Center'), icon: CenterViewIcon },
  { value: 'fullscreen' as const, label: t('Full page'), icon: FullViewIcon },
])

const isFullscreen = computed(() => viewMode.value === 'fullscreen')

const returnMode = computed(() => {
  const m = fullscreenReturnViewMode.value
  if (m === 'side' && !canUseSideFilePreview.value) return 'center'
  return m === 'side' || m === 'center' ? m : 'center'
})

const toggleIcon = computed(() => {
  if (isFullscreen.value) {
    return returnMode.value === 'side' ? SideViewIcon : CenterViewIcon
  }
  return FullViewIcon
})

const toggleTitle = computed(() => {
  if (isFullscreen.value) {
    return returnMode.value === 'side' ? t('Side') : t('Center')
  }
  return t('Full page')
})

const isModeDisabled = (mode: FilePreviewViewMode) =>
  mode === 'side' && !canUseSideFilePreview.value

/** Official DropdownMenuItem enabled / disabled classNames (live DOM) */
const itemClass = (disabled: boolean) =>
  disabled
    ? 'flex items-center gap-2 w-full p-2 rounded-[8px] text-sm cursor-not-allowed hover:bg-transparent text-[var(--text-disable)]'
    : 'flex items-center gap-2 w-full p-2 rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] cursor-pointer text-[var(--text-primary)] text-sm'

const toggleFullscreen = () => {
  if (isFullscreen.value) {
    exitFullscreen()
  } else {
    setViewMode('fullscreen')
  }
}

const selectMode = (mode: FilePreviewViewMode) => {
  if (isModeDisabled(mode)) return
  setViewMode(mode)
  menuOpen.value = false
  defaultMenuOpen.value = false
}

const selectDefaultMode = (mode: FilePreviewViewMode) => {
  setDefaultViewMode(mode)
  defaultMenuOpen.value = false
}
</script>
