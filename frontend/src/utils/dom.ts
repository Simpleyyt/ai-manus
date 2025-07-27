/**
 * Get parent element by selector or element
 * @param selector - CSS selector or HTMLElement or Element
 * @param parentSelector - Optional parent selector to find specific parent
 * @returns Parent element or null if not found
 */
export function getParentElement(
  selector: string | HTMLElement | Element,
  parentSelector?: string
): HTMLElement | null {
  let element: Element | null = null

  // Handle both string selector and HTMLElement/Element
  if (typeof selector === 'string') {
    element = document.querySelector(selector)
  } else {
    element = selector
  }

  if (!element) {
    console.warn(`Could not find element: ${typeof selector === 'string' ? selector : 'provided element'}`)
    return null
  }

  // If parentSelector is provided, find specific parent
  if (parentSelector) {
    const parent = element.closest(parentSelector)
    if (!parent) {
      console.warn(`Could not find parent element with selector: ${parentSelector}`)
      return null
    }
    return parent as HTMLElement
  }

  // Get immediate parent
  const parent = element.parentElement
  if (!parent) {
    console.warn('Could not find parent element')
    return null
  }

  return parent
}

 