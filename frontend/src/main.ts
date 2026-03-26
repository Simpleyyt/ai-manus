import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/global.css'
import './assets/theme.css'
import './utils/toast'
import i18n from './composables/useI18n'
import { getStoredToken } from './api/auth'
import { getCachedClientConfig } from './api/config'
import { configure } from "vue-gtag"

// Import page components
import HomePage from './pages/HomePage.vue'
import ChatPage from './pages/ChatPage.vue'
import LoginPage from './pages/LoginPage.vue'
import MainLayout from './pages/MainLayout.vue'
import SharePage from './pages/SharePage.vue'
import ShareLayout from './pages/ShareLayout.vue'

// Create router
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { 
      path: '/chat', 
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        { 
          path: '', 
          component: HomePage, 
          alias: ['/', '/home'],
          meta: { requiresAuth: true }
        },
        { 
          path: ':sessionId', 
          component: ChatPage,
          meta: { requiresAuth: true }
        }
      ]
    },
    {
      path: '/share',
      component: ShareLayout,
      children: [
        {
          path: ':sessionId',
          component: SharePage,
        }
      ]
    },
    { 
      path: '/login', 
      component: LoginPage
    }
  ]
})

// Global route guard
router.beforeEach(async (to, _, next) => {
  const requiresAuth = to.matched.some((record: any) => record.meta?.requiresAuth)
  const hasToken = !!getStoredToken()
  const clientConfig = await getCachedClientConfig()
  const authProvider = clientConfig?.auth_provider ?? null

  if (requiresAuth) {
    if (authProvider === 'none') {
      next()
      return
    }
    
    if (!hasToken) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
  }
  
  if (to.path === '/login') {
    if (authProvider === 'none') {
      next('/')
      return
    }
    if (hasToken) {
      next('/')
      return
    }
  }

  next()
})

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