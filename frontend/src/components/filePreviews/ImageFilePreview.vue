<template>
  <!-- Official image previewer default export (module 204772) -->
  <div class="w-full h-full flex flex-col overflow-hidden" @click="emit('close')">
    <!-- Official ImageCloseButton: desktop only -->
    <div class="absolute top-4 end-5 z-20 hidden md:block" @click.stop>
      <button
        type="button"
        class="clickable size-7 flex items-center justify-center cursor-pointer hover:bg-[rgba(255,255,255,0.1)] rounded transition-colors"
        :title="t('Close')"
        @click="emit('close')">
        <X :size="20" color="var(--icon-white)" />
      </button>
    </div>

    <!-- Official ImagePreviewContent -->
    <div
      class="flex items-center justify-center relative touch-none flex-1 min-h-0 pb-[68px] pt-[24px] ps-[24px] pe-[80px] w-full max-md:px-[20px] max-md:pt-[68px] max-md:pb-[88px]"
      @wheel.prevent="onWheel">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="file.filename || 'image'"
        draggable="false"
        class="max-h-full max-w-full rounded-[8px] overflow-hidden select-none"
        :style="imgStyle"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
        @click.stop
      />
    </div>

    <!-- Official floating toolbar (desktop: bottom) — skip Edit in canvas -->
    <div
      class="absolute start-0 end-0 bottom-0 z-20 flex items-center justify-center ps-3 pe-5 py-3 w-full max-md:top-0 max-md:bottom-auto"
      @click.stop>
      <div
        class="backdrop-blur-2xl bg-[rgba(0,0,0,0.65)] rounded-[12px] flex items-center gap-3 ps-1 pe-3 py-1">
        <!-- Official: ToolViewModeMenu on dark image toolbar -->
        <ToolViewModeMenu
          class-name="text-[var(--icon-white)]"
          button-class-name="rounded hover:bg-[rgba(255,255,255,0.1)] data-[popover-trigger]:bg-[rgba(255,255,255,0.1)] data-[state=open]:bg-[rgba(255,255,255,0.1)]"
        />
        <button
          type="button"
          class="clickable size-7 flex items-center justify-center cursor-pointer hover:bg-[rgba(255,255,255,0.1)] rounded transition-colors"
          :title="t('Download')"
          @click="download">
          <Download :size="20" color="var(--icon-white)" />
        </button>
        <div class="h-4 w-px bg-[var(--border-white)]" />
        <div class="flex items-center gap-1.5">
          <button
            type="button"
            class="clickable size-7 flex items-center justify-center hover:bg-[rgba(255,255,255,0.1)] rounded transition-colors"
            :class="scale <= 0.1 ? 'opacity-50 cursor-not-allowed' : ''"
            :title="t('Zoom out')"
            :disabled="scale <= 0.1"
            @click="zoomOut">
            <ZoomOut :size="20" color="var(--icon-white)" />
          </button>
          <span
            class="text-sm text-[var(--text-white)] font-normal leading-5 tracking-[-0.154px] min-w-[40px] text-center">
            {{ scaleLabel }}
          </span>
          <button
            type="button"
            class="clickable size-7 flex items-center justify-center hover:bg-[rgba(255,255,255,0.1)] rounded transition-colors"
            :class="scale >= 10 ? 'opacity-50 cursor-not-allowed' : ''"
            :title="t('Zoom in')"
            :disabled="scale >= 10"
            @click="zoomIn">
            <ZoomIn :size="20" color="var(--icon-white)" />
          </button>
        </div>
        <div class="h-4 w-px bg-[var(--border-white)] md:hidden" />
        <button
          type="button"
          class="clickable size-7 flex items-center justify-center cursor-pointer hover:bg-[rgba(255,255,255,0.1)] rounded transition-colors md:hidden"
          :title="t('Close')"
          @click="emit('close')">
          <X :size="20" color="var(--icon-white)" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Download, X, ZoomIn, ZoomOut } from 'lucide-vue-next'
import { getFileDownloadUrl, type FileInfo } from '../../api/file'
import ToolViewModeMenu from '../ToolViewModeMenu.vue'

const props = defineProps<{
  file: FileInfo
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const { t } = useI18n()

const imageUrl = ref('')
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })

const scaleLabel = computed(() => `${Math.round(scale.value * 100)}%`)

const imgStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`,
  transformOrigin: 'center center',
  cursor: isDragging.value ? 'grabbing' : scale.value !== 1 ? 'grab' : 'default',
  willChange: 'transform',
}))

const clampScale = (v: number) => Math.max(0.1, Math.min(10, v))

const zoomIn = () => {
  scale.value = clampScale(scale.value + 0.25)
}

const zoomOut = () => {
  scale.value = clampScale(scale.value - 0.25)
}

const onWheel = (e: WheelEvent) => {
  if (e.deltaY === 0 || Math.abs(e.deltaX) > Math.abs(e.deltaY)) return
  const next = clampScale(scale.value * (e.deltaY > 0 ? 1 / 1.1 : 1.1))
  scale.value = next
}

const onPointerDown = (e: PointerEvent) => {
  if (e.button !== 0) return
  e.preventDefault()
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  isDragging.value = true
  dragStart.value = {
    x: e.clientX - translateX.value,
    y: e.clientY - translateY.value,
  }
}

const onPointerMove = (e: PointerEvent) => {
  if (!isDragging.value) return
  e.preventDefault()
  translateX.value = e.clientX - dragStart.value.x
  translateY.value = e.clientY - dragStart.value.y
}

const onPointerUp = (e: PointerEvent) => {
  try {
    ;(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId)
  } catch {
    /* already released */
  }
  isDragging.value = false
}

const download = async () => {
  const url = await getFileDownloadUrl(props.file)
  window.open(url, '_blank')
}

watch(
  () => props.file,
  async (file) => {
    if (!file) return
    scale.value = 1
    translateX.value = 0
    translateY.value = 0
    imageUrl.value = await getFileDownloadUrl(file)
  },
  { immediate: true },
)
</script>
