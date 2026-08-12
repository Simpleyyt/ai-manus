import { computed, onUnmounted, ref, watch, type Ref } from 'vue'

/**
 * Keep the label shimmering for the whole live window:
 * - while status === calling
 * - and briefly after a fast called (we lack official streaming states)
 * Parent can also pass `active` (e.g. current tool of a running step) to force
 * continuous shimmer beyond the raw calling bit.
 */
export const TOOL_SHIMMER_MIN_MS = 2200

export function useToolShimmer(
  status: Ref<'calling' | 'called' | string>,
  active: Ref<boolean> = ref(false),
) {
  const holdShimmer = ref(status.value === 'calling')
  let startedAt = status.value === 'calling' ? Date.now() : 0
  let hideTimer: ReturnType<typeof setTimeout> | null = null

  const clearHideTimer = () => {
    if (hideTimer !== null) {
      clearTimeout(hideTimer)
      hideTimer = null
    }
  }

  watch(
    status,
    (next) => {
      if (next === 'calling') {
        clearHideTimer()
        startedAt = Date.now()
        holdShimmer.value = true
        return
      }

      if (!startedAt) {
        holdShimmer.value = false
        return
      }

      const elapsed = Date.now() - startedAt
      const remain = Math.max(0, TOOL_SHIMMER_MIN_MS - elapsed)
      clearHideTimer()
      if (remain === 0) {
        holdShimmer.value = false
        return
      }
      hideTimer = setTimeout(() => {
        hideTimer = null
        if (status.value !== 'calling') {
          holdShimmer.value = false
        }
      }, remain)
    },
    { immediate: true },
  )

  onUnmounted(clearHideTimer)

  const showShimmer = computed(() => holdShimmer.value || active.value)

  return { showShimmer }
}
