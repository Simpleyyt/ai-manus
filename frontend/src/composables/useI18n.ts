import { createI18n } from 'vue-i18n'
import { ref, watch } from 'vue'
import messages from '../locales'
import type { Locale } from '../locales'

const STORAGE_KEY = 'manus-locale'

// Get browser language and map to supported locale
const getBrowserLocale = (): Locale => {
  const browserLang = navigator.language || navigator.languages?.[0]
  // Check if browser language starts with any supported locale
  if (browserLang?.startsWith('zh')) {
    return 'zh'
  }
  if (browserLang?.startsWith('en')) {
    return 'en'
  }
  // Default to Chinese if no match
  return 'en'
}

// Get current language from localStorage, default to browser language
const getStoredLocale = (): Locale => {
  const storedLocale = localStorage.getItem(STORAGE_KEY)
  return (storedLocale as Locale) || getBrowserLocale()
}

// Create i18n instance
export const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: getStoredLocale(),
  fallbackLocale: 'en',
  messages,
  silentTranslationWarn: true,    // Disable translation warnings
  silentFallbackWarn: true,       // Disable fallback warnings
  missingWarn: false,             // Disable missing key warnings
  fallbackWarn: false,            // Disable fallback warnings
  warnHtmlMessage: false          // Disable HTML in message warnings
})

// Create a composable to use in components
export function useLocale() {
  const currentLocale = ref(getStoredLocale())

  // Switch language
  const setLocale = (locale: Locale) => {
    i18n.global.locale.value = locale
    currentLocale.value = locale
    localStorage.setItem(STORAGE_KEY, locale)
    document.querySelector('html')?.setAttribute('lang', locale)
  }

  // Watch language change
  watch(currentLocale, (val) => {
    setLocale(val)
  })

  return {
    currentLocale,
    setLocale
  }
}

export default i18n 