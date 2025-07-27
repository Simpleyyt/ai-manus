import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getParentElement } from '../utils/dom'

export function useResizeObserver(
  targetRef: any,
  options: {
    target?: 'self' | 'parent'
    callback?: (size: number) => void
    property?: 'width' | 'height'
  } = {}
) {
  const {
    target = 'parent',
    callback,
    property = 'width'
  } = options

  const size = ref(0)
  let resizeObserver: ResizeObserver | null = null

  const updateSize = (element: HTMLElement) => {
    const newSize = property === 'width' ? element.offsetWidth : element.offsetHeight
    size.value = newSize
    callback?.(newSize)
  }

  onMounted(async () => {
    // Wait for DOM to be ready
    await nextTick()
    
    // Get the current component's DOM element using ref
    const currentElement = targetRef.value
    if (!currentElement) {
      console.warn('Could not find target element')
      return
    }
    
    // Determine which element to observe
    let observeElement: HTMLElement
    if (target === 'parent') {
      const parentElement = getParentElement(currentElement)
      if (!parentElement) {
        console.warn('Could not find parent element')
        return
      }
      observeElement = parentElement
    } else {
      observeElement = currentElement
    }
    
    // Set initial size immediately for instant response
    updateSize(observeElement)
    
    // Create ResizeObserver to watch size changes with immediate updates
    resizeObserver = new ResizeObserver(() => {
      updateSize(observeElement)
    })
    
    try {
      // Start observing
      resizeObserver.observe(observeElement)
    } catch (error) {
      console.error('Failed to observe element:', error)
    }
  })

  onUnmounted(() => {
    if (resizeObserver) {
      resizeObserver.disconnect()
    }
  })

  return {
    size
  }
} 