import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/global.css'
import './assets/theme.css'
import './utils/toast'
import i18n from './composables/useI18n'
import { getStoredToken } from './api/auth'
import { getCachedClientConfig, getAuthProvider } from './api/config'

// Import page components
import HomePage from './pages/HomePage.vue'
import ChatPage from './pages/ChatPage.vue'
import LoginPage from './pages/LoginPage.vue'
import MainLayout from './pages/MainLayout.vue'
import { configure } from "vue-gtag";
import SharePage from './pages/SharePage.vue';
import ShareLayout from './pages/ShareLayout.vue';

configure({
  tagId: 'G-XCRZ3HH31S'
})

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

// Global route guard — uses synchronously cached auth provider (loaded once at startup).
router.beforeEach((to, _, next) => {
  const requiresAuth = to.matched.some((record: any) => record.meta?.requiresAuth)
  const authProvider = getAuthProvider()
  const hasToken = !!getStoredToken()

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

  // Redirect away from /login when auth is not needed or user already has a token
  if (to.path === '/login') {
    if (authProvider === 'none' || hasToken) {
      next('/')
      return
    }
  }

  next()
})

async function bootstrap() {
  // Load client config once before the app mounts so the route guard
  // and all components can read it synchronously.
  await getCachedClientConfig()

  const app = createApp(App)
  app.use(router)
  app.use(i18n)
  app.mount('#app')
}

bootstrap() 