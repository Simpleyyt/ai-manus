import { ref } from 'vue'
import type { FileInfo } from '../api/file'
import { eventBus } from '../utils/eventBus'
import { EVENT_SHOW_FILE_PREVIEWER } from '../constants/event'

const isShow = ref(false)
const visible = ref(true)
const fileInfo = ref<FileInfo>()

export function useFilePreviewer() {
  const showFilePreviewer = (file: FileInfo) => {
    eventBus.emit(EVENT_SHOW_FILE_PREVIEWER)
    visible.value = true
    fileInfo.value = file
    isShow.value = true
  }

  const hideFilePreviewer = () => {
    isShow.value = false
  }

  return {
    isShow,
    fileInfo,
    visible,
    showFilePreviewer,
    hideFilePreviewer,
  }
}
