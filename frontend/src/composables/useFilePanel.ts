import { ref } from 'vue'
import type { FileInfo } from '../api/file'
import { eventBus } from '../utils/eventBus'
import { EVENT_SHOW_FILE_PANEL } from '../constants/event'

const isShow = ref(false)
const visible = ref(true)
const fileInfo = ref<FileInfo>()

export function useFilePanel() {
  const showFilePanel = (file: FileInfo) => {
    eventBus.emit(EVENT_SHOW_FILE_PANEL)
    visible.value = true
    fileInfo.value = file
    isShow.value = true
  }

  const hideFilePanel = () => {
    isShow.value = false
  }

  return {
    isShow,
    fileInfo,
    visible,
    showFilePanel,
    hideFilePanel
  }
} 