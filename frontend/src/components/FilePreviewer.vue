<template>
  <!-- Measure parent width for side mode (always mounted when previewer is allowed) -->
  <div
    ref="sideRootRef"
    class="h-full overflow-hidden shrink-0"
    :style="{
      width: viewMode === 'side' && isShow && fileInfo ? `${sideWidth}px` : '0px',
      opacity: viewMode === 'side' && isShow && fileInfo ? '1' : '0',
      transition: '0.2s ease-in-out',
    }">
    <div
      v-if="viewMode === 'side' && isShow && fileInfo && fileType"
      class="h-full w-full sticky top-0 h-[100vh]">
      <div
        class="overflow-hidden shadow-[0px_0px_8px_0px_rgba(0,0,0,0.02)] ltr:border-l rtl:border-r border-black/8 dark:border-[var(--border-light)] flex flex-col h-full w-full relative"
        :class="panelToneClass">
        <FilePreviewerChrome
          :file-info="fileInfo"
          :file-type="fileType"
          :is-image="isImagePreview"
          :view-mode="viewMode"
          @download="download"
          @close="hideFilePreviewer"
        />
        <div class="flex flex-1 min-h-0 w-full relative">
          <component :is="fileType.preview" :file="fileInfo" @close="hideFilePreviewer" />
        </div>
      </div>
    </div>
  </div>

  <!-- Official portal: center mask + panel / fullscreen.
       Keep center/fullscreen above Computer sidebar updates — do not dismiss
       when EVENT_SHOW_COMPUTER_PANEL fires during a running task. -->
  <Teleport to="body">
    <div
      v-if="isShow && fileInfo && fileType && (viewMode === 'center' || viewMode === 'fullscreen')"
      class="fixed inset-0 pointer-events-none z-[1000]">
      <div
        v-if="viewMode === 'center'"
        class="absolute inset-0 bg-[var(--background-dialog-mask)] backdrop-blur-[4px] pointer-events-auto"
        @click="hideFilePreviewer"
      />
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div
          class="overflow-hidden pointer-events-auto origin-center flex flex-col relative"
          :class="[
            panelToneClass,
            viewMode === 'fullscreen'
              ? 'size-full rounded-none'
              : 'md:w-[calc(100vw-80px)] md:h-[calc(100vh-80px)] rounded-2xl w-[calc(100vw-32px)] h-[calc(100vh-32px)] max-w-[1200px] transition-[width,height] duration-220 border border-black/8 dark:border-[var(--border-light)]',
            'shadow-[0px_0px_8px_0px_rgba(0,0,0,0.02)]',
          ]">
          <FilePreviewerChrome
            :file-info="fileInfo"
            :file-type="fileType"
            :is-image="isImagePreview"
            :view-mode="viewMode"
            @download="download"
            @close="hideFilePreviewer"
          />
          <div class="flex flex-1 min-h-0 w-full relative">
            <component :is="fileType.preview" :file="fileInfo" @close="hideFilePreviewer" />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useFilePreviewer } from '../composables/useFilePreviewer'
import { getFileDownloadUrl } from '../api/file'
import { getFileType } from '../utils/fileType'
import { useResizeObserver } from '../composables/useResizeObserver'
import FilePreviewerChrome from './FilePreviewerChrome.vue'

const {
  isShow,
  fileInfo,
  viewMode,
  showFilePreviewer,
  hideFilePreviewer,
} = useFilePreviewer()

const sideRootRef = ref<HTMLElement>()
const { size: parentSize } = useResizeObserver(sideRootRef, {
  target: 'parent',
  property: 'width',
})

const sideWidth = computed(() => Math.max(320, Math.floor(parentSize.value / 2) || 480))

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

const panelToneClass = computed(() =>
  isImagePreview.value
    ? 'bg-[var(--background-mask-black)] dark:bg-[var(--background-preview-mask)]'
    : 'bg-[var(--background-gray-main)]',
)

const download = async () => {
  if (!fileInfo.value) return
  const url = await getFileDownloadUrl(fileInfo.value)
  window.open(url, '_blank')
}

defineExpose({
  showFilePreviewer,
  hideFilePreviewer,
  isShow,
})
</script>
