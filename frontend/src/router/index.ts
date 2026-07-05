import { createRouter, createWebHistory } from 'vue-router'
import { getStoredToken } from '../api/auth'
import { getCachedClientConfig } from '../api/config'

// Pages are lazy-loaded so heavy dependencies (Monaco, NoVNC, Claw assets)
// stay out of the initial bundle.
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/chat',
      component: () => import('../pages/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          component: () => import('../pages/HomePage.vue'),
          alias: ['/', '/home'],
          meta: { requiresAuth: true }
        },
        {
          path: 'claw',
          component: () => import('../pages/ClawPage.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: ':sessionId',
          component: () => import('../pages/ChatPage.vue'),
          meta: { requiresAuth: true }
        }
      ]
    },
    {
      path: '/share',
      component: () => import('../pages/ShareLayout.vue'),
      children: [
        {
          path: ':sessionId',
          component: () => import('../pages/SharePage.vue'),
        }
      ]
    },
    {
      path: '/login',
      component: () => import('../pages/LoginPage.vue')
    }
  ]
})

// Global route guard
router.beforeEach(async (to, _, next) => {
  const requiresAuth = to.matched.some((record) => record.meta?.requiresAuth)
  const hasToken = !!getStoredToken()
  const clientConfig = await getCachedClientConfig()
  const authProvider = clientConfig?.auth_provider ?? null

  if (requiresAuth) {
    if (authProvider === 'none' || authProvider === null) {
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
