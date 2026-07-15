import { createApp } from 'vue'
import App from './App.vue'
import '@fontsource/libre-baskerville/400.css'
import '@fontsource/libre-baskerville/400-italic.css'
import '@fontsource/libre-baskerville/700.css'
import './assets/global.css'
import './assets/theme.css'
import './utils/toast'
import i18n from './composables/useI18n'
import { router } from './router'
import { getCachedClientConfig } from './api/config'
import { configure } from "vue-gtag"

// Preload client runtime config and initialize Google Analytics.
void getCachedClientConfig().then((config) => {
  if (config?.google_analytics_id) {
    configure({ tagId: config.google_analytics_id })
  }
})

const app = createApp(App)

app.use(router)
app.use(i18n)
app.mount('#app')
