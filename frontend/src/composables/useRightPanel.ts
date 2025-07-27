import { ref } from 'vue'
import type { ToolContent } from '../types/message'
import type { FileInfo } from '../api/file'

const isShow = ref(false)
const live = ref(false)
const toolContent = ref<ToolContent>()
const fileInfo = ref<FileInfo>()
const panelType = ref<'tool' | 'file'>('tool')

export function useRightPanel() {
  const showTool = (content: ToolContent, isLive: boolean = false) => {
    panelType.value = 'tool'
    toolContent.value = content
    isShow.value = true
    live.value = isLive
  }

  const showFile = (file: FileInfo) => {
    panelType.value = 'file'
    fileInfo.value = file
    isShow.value = true
  }

  const hide = () => {
    isShow.value = false
  }

  return {
    isShow,
    live,
    toolContent,
    fileInfo,
    panelType,
    showTool,
    showFile,
    hide
  }
} 