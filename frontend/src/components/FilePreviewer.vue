<template>
  <!-- Official FilePreviewer side shell: function eb (3waye1i3878mv.js) -->
  <div
    ref="rootRef"
    v-if="visible"
    :class="{
      'h-full w-full top-0 ltr:right-0 rtl:left-0 z-50 fixed sm:sticky sm:top-0 sm:h-[100vh]': isShow,
      'h-full overflow-hidden': !isShow,
    }"
    :style="{
      width: isShow ? `${parentSize / 2}px` : '0px',
      opacity: isShow ? '1' : '0',
      transition: '0.2s ease-in-out',
    }">
    <div class="h-full" :style="{ width: isShow ? '100%' : '0px' }">
      <div
        v-if="isShow && fileInfo && fileType"
        class="overflow-hidden shadow-[0px_0px_8px_0px_rgba(0,0,0,0.02)] ltr:border-l rtl:border-r border-black/8 dark:border-[var(--border-light)] flex flex-col h-full w-full relative"
        :class="isImagePreview
          ? 'bg-[var(--background-mask-black)] dark:bg-[var(--background-preview-mask)]'
          : 'bg-[var(--background-gray-main)]'">

        <!-- Official FilePreviewerHeader: null for image/svg -->
        <div
          v-if="!isImagePreview"
          class="flex h-[56px] shrink-0 items-center justify-between gap-[16px] px-[16px] py-[12px] border-b border-[var(--border-main)]">
          <!-- Official FilePreviewerBrief -->
          <div class="flex min-w-0 flex-1 items-center justify-between">
            <div
              class="flex min-w-0 flex-row items-center gap-[8px] truncate text-[var(--text-secondary)] [&_svg]:flex-shrink-0">
              <a
                href=""
                class="flex size-[36px] flex-shrink-0 items-center justify-center cursor-default"
                target="_blank"
                rel="noreferrer"
                @click.prevent>
                <div class="relative flex items-center justify-center [&_svg]:w-8 [&_svg]:h-8">
                  <component :is="fileType.icon" />
                </div>
              </a>
              <div class="flex min-w-0 flex-col truncate text-[var(--text-primary)]">
                <span
                  class="truncate text-[14px] font-medium leading-[20px] tracking-[-0.15px]"
                  :title="fileInfo.filename">
                  {{ fileInfo.filename }}
                </span>
              </div>
            </div>
          </div>

          <div class="flex shrink-0 items-center justify-end gap-[4px] select-none">
            <div class="flex items-center gap-[4px]">
              <button
                type="button"
                class="flex size-[32px] items-center justify-center rounded-[8px] hover:bg-[var(--fill-tsp-white-main)]"
                :title="t('Download')"
                @click="download">
                <Download class="size-[18px] text-[var(--icon-secondary)]" />
              </button>
            </div>
            <div class="flex items-center gap-[4px]">
              <!-- Official divider before Close (when not fullscreen) -->
              <div class="flex h-[32px] items-center px-[4px]">
                <div class="h-[16px] w-px bg-[var(--border-dark)]" />
              </div>
              <button
                type="button"
                class="flex size-[32px] items-center justify-center rounded-[8px] hover:bg-[var(--fill-tsp-white-main)]"
                :title="t('Close')"
                @click="hideFilePreviewer">
                <X class="size-[18px] text-[var(--icon-secondary)]" />
              </button>
            </div>
          </div>
        </div>

        <!-- Official body -->
        <div class="flex flex-1 min-h-0 w-full relative">
          <component :is="fileType.preview" :file="fileInfo" @close="hideFilePreviewer" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Download, X } from 'lucide-vue-next'
import { useFilePreviewer } from '../composables/useFilePreviewer'
import { getFileDownloadUrl } from '../api/file'
import { getFileType } from '../utils/fileType'
import { useResizeObserver } from '../composables/useResizeObserver'
import { eventBus } from '../utils/eventBus'
import { EVENT_SHOW_COMPUTER_PANEL } from '../constants/event'

const { t } = useI18n()

const {
  isShow,
  fileInfo,
  visible,
  showFilePreviewer,
  hideFilePreviewer,
} = useFilePreviewer()

const rootRef = ref<HTMLElement>()
const { size: parentSize } = useResizeObserver(rootRef, {
  target: 'parent',
  property: 'width',
})

const fileType = computed(() => {
  if (!fileInfo.value) return null
  return getFileType(fileInfo.value.filename)
})

const isImagePreview = computed(() => {
  const f = fileInfo.value
  if (!f) return false
  const ct = f.content_type || ''
  if (ct.startsWith('image/') || ct === 'image/svg+xml') return true
  const name = f.filename || ''
  const i = name.lastIndexOf('.')
  if (i <= 0) return false
  const ext = name.slice(i + 1).toLowerCase()
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif', 'heic', 'heif'].includes(ext)
})

const download = async () => {
  if (!fileInfo.value) return
  const url = await getFileDownloadUrl(fileInfo.value)
  window.open(url, '_blank')
}

onMounted(() => {
  eventBus.on(EVENT_SHOW_COMPUTER_PANEL, () => {
    visible.value = false
  })
})

onUnmounted(() => {
  eventBus.off(EVENT_SHOW_COMPUTER_PANEL)
})

defineExpose({
  showFilePreviewer,
  hideFilePreviewer,
  isShow,
})
</script>
