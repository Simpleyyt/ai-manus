import { computed, ref, watch, type Ref } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import type { FileInfo } from '../api/file'
import { eventBus } from '../utils/eventBus'
import { EVENT_SHOW_FILE_PREVIEWER } from '../constants/event'
import { router } from '../router'

/** Official filePreviewerSlice viewMode — default is center */
export type FilePreviewViewMode = 'side' | 'center' | 'fullscreen'

const isShow = ref(false)
const fileInfo = ref<FileInfo>()
const viewMode = ref<FilePreviewViewMode>('center')
const fullscreenReturnViewMode = ref<Exclude<FilePreviewViewMode, 'fullscreen'>>('center')
/** Official persistDefaultViewMode — session memory only (no localStorage) */
const defaultViewMode = ref<FilePreviewViewMode>('center')

/** Official MOBILE_BREAKPOINT matchMedia `(max-width: ${BP-1}px)` — use 768-1 */
let isMobileRef: Ref<boolean> | null = null
let sideGuardStarted = false

/**
 * Official rootSelectors.canUseSideFilePreview:
 * !!currentSessionId && !isMobile && tasksTabKey ∈ {task, newTask, agents}
 * Local: chat session route (not library / share / claw) && !mobile.
 */
function getCanUseSideFilePreview(isMobile: boolean): boolean {
  if (isMobile) return false
  const route = router.currentRoute.value
  const sessionId = route.params.sessionId
  if (typeof sessionId !== 'string' || !sessionId || sessionId === 'claw') return false
  return route.path.startsWith('/chat/')
}

function resolveViewMode(mode: FilePreviewViewMode, canUseSide: boolean): FilePreviewViewMode {
  if (mode === 'side' && !canUseSide) return 'center'
  return mode
}

function resolveFullscreenReturn(
  mode: Exclude<FilePreviewViewMode, 'fullscreen'>,
  canUseSide: boolean,
): Exclude<FilePreviewViewMode, 'fullscreen'> {
  if (mode === 'side' && !canUseSide) return 'center'
  return mode
}

export function useFilePreviewer() {
  if (!isMobileRef) {
    isMobileRef = useMediaQuery('(max-width: 767px)')
  }
  const isMobile = isMobileRef

  const canUseSideFilePreview = computed(() => getCanUseSideFilePreview(isMobile.value))

  if (!sideGuardStarted) {
    sideGuardStarted = true
    watch(
      canUseSideFilePreview,
      (canUseSide) => {
        if (!canUseSide && viewMode.value === 'side') {
          viewMode.value = 'center'
        }
        if (!canUseSide && fullscreenReturnViewMode.value === 'side') {
          fullscreenReturnViewMode.value = 'center'
        }
      },
      { immediate: true },
    )
  }

  const showFilePreviewer = (file: FileInfo, mode?: FilePreviewViewMode) => {
    eventBus.emit(EVENT_SHOW_FILE_PREVIEWER)
    fileInfo.value = file
    const canUseSide = canUseSideFilePreview.value
    if (mode) {
      viewMode.value = resolveViewMode(mode, canUseSide)
    } else if (viewMode.value === 'fullscreen') {
      // keep fullscreen if already there
    } else {
      const next = defaultViewMode.value === 'fullscreen'
        ? 'fullscreen'
        : defaultViewMode.value
      viewMode.value = resolveViewMode(next, canUseSide)
    }
    isShow.value = true
  }

  const hideFilePreviewer = () => {
    isShow.value = false
  }

  const setViewMode = (mode: FilePreviewViewMode) => {
    // Official: if ("side" !== e || canUseSide) { setViewMode }
    if (mode === 'side' && !canUseSideFilePreview.value) return
    if (mode === 'fullscreen' && viewMode.value !== 'fullscreen') {
      if (viewMode.value === 'side' || viewMode.value === 'center') {
        fullscreenReturnViewMode.value = viewMode.value
      }
    }
    viewMode.value = mode
  }

  const exitFullscreen = () => {
    viewMode.value = resolveFullscreenReturn(
      fullscreenReturnViewMode.value,
      canUseSideFilePreview.value,
    )
  }

  const setDefaultViewMode = (mode: FilePreviewViewMode) => {
    defaultViewMode.value = mode
  }

  return {
    isShow,
    fileInfo,
    viewMode,
    fullscreenReturnViewMode,
    defaultViewMode,
    canUseSideFilePreview,
    showFilePreviewer,
    hideFilePreviewer,
    setViewMode,
    exitFullscreen,
    setDefaultViewMode,
  }
}
