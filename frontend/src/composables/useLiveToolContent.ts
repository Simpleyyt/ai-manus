import { onMounted, onUnmounted, ref, watch, type Ref } from 'vue'
import type { ToolContent } from '../types/message'

const DEFAULT_REFRESH_INTERVAL_MS = 5000

/**
 * Shared load + auto-refresh behavior for tool views (file, shell, ...).
 *
 * Loads content on mount and whenever the tool content changes; while `live`
 * is true and a target key is present, re-loads on a fixed interval.
 */
export function useLiveToolContent(options: {
  toolContent: Ref<ToolContent>
  live: Ref<boolean>
  /** Identifies what to load (e.g. file path, shell session id). Empty disables refresh. */
  targetKey: Ref<string>
  load: () => void | Promise<void>
  intervalMs?: number
}) {
  const { toolContent, live, targetKey, load } = options
  const intervalMs = options.intervalMs ?? DEFAULT_REFRESH_INTERVAL_MS
  const refreshTimer = ref<number | null>(null)

  const stopAutoRefresh = () => {
    if (refreshTimer.value) {
      clearInterval(refreshTimer.value)
      refreshTimer.value = null
    }
  }

  const startAutoRefresh = () => {
    stopAutoRefresh()
    if (live.value && targetKey.value) {
      refreshTimer.value = window.setInterval(() => {
        load()
      }, intervalMs)
    }
  }

  watch(targetKey, (newVal: string) => {
    if (newVal) {
      load()
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  })

  watch(toolContent, () => {
    load()
  })

  watch(() => toolContent.value.timestamp, () => {
    load()
  })

  watch(live, (isLive: boolean) => {
    if (isLive) {
      load()
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  })

  onMounted(() => {
    load()
    startAutoRefresh()
  })

  onUnmounted(() => {
    stopAutoRefresh()
  })

  return { startAutoRefresh, stopAutoRefresh }
}
