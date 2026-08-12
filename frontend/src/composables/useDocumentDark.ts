import { ref, onMounted, onBeforeUnmount, type Ref } from 'vue'
import { isDocumentDark } from './useTheme'

/**
 * Reactive document dark flag — updates when `html`/`body` class toggles.
 * Used by Monaco / xterm surfaces that need theme sync.
 */
export function useDocumentDark(): Ref<boolean> {
  const isDark = ref(isDocumentDark())
  let observer: MutationObserver | null = null

  onMounted(() => {
    isDark.value = isDocumentDark()
    observer = new MutationObserver(() => {
      isDark.value = isDocumentDark()
    })
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    })
    if (document.body) {
      observer.observe(document.body, {
        attributes: true,
        attributeFilter: ['class'],
      })
    }
  })

  onBeforeUnmount(() => {
    observer?.disconnect()
    observer = null
  })

  return isDark
}
