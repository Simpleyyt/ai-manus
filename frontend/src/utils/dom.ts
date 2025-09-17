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

/**
 * Copy text to clipboard with fallback support
 * @param text - Text to copy to clipboard
 * @returns Promise<boolean> - Returns true if copy was successful
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  // Check if modern clipboard API is available
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      console.log('Text copied to clipboard using Clipboard API');
      return true;
    } catch (error) {
      console.error('Clipboard API failed:', error);
      // Fall through to fallback method
    }
  }
  
  // Fallback method for older browsers or when clipboard API fails
  try {
    console.log('Copying text to clipboard using fallback method');
    
    // Store current active element to restore focus later
    const activeElement = document.activeElement as HTMLElement;
    
    // Create a temporary textarea element
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '-9999px';
    textArea.style.left = '-9999px';
    textArea.style.opacity = '0';
    textArea.setAttribute('readonly', '');
    
    // Add to DOM, focus, select and copy
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    const successful = document.execCommand('copy');
    
    // Remove the temporary element
    document.body.removeChild(textArea);
    
    // Restore focus to the previous active element to prevent popover from closing
    if (activeElement && activeElement.focus) {
      activeElement.focus();
    }
    
    if (successful) {
      console.log('Text copied using fallback method');
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('All copy methods failed:', error);
    return false;
  }
}

 