import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/global.css'
import './assets/theme.css'
import './utils/toast'
import i18n from './composables/useI18n'
import { getStoredToken } from './api/auth'

// Import page components
import HomePage from './pages/HomePage.vue'
import ChatPage from './pages/ChatPage.vue'
import LoginPage from './pages/LoginPage.vue'
import MainLayout from './pages/MainLayout.vue'

// Create router
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { 
      path: '/chat', 
      component: MainLayout,
      meta: { requiresAuth: true }, // 需要登录才能访问聊天功能
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
      path: '/login', 
      component: LoginPage,
      meta: { requiresAuth: false } // 登录页面不需要认证
    }
  ]
})

// 全局路由守卫 - 仅检查本地token，无网络请求
router.beforeEach((to, _, next) => {
  // 检查路由是否需要认证
  const requiresAuth = to.matched.some((record: any) => record.meta?.requiresAuth)
  
  // 检查本地是否有token（不发起网络请求）
  const hasToken = !!getStoredToken()
  
  if (requiresAuth && !hasToken) {
    // 需要认证但没有本地token，重定向到登录页面
    next({
      path: '/login',
      query: { redirect: to.fullPath } // 保存原始路径，登录后可以重定向回来
    })
  } else if (to.path === '/login' && hasToken) {
    // 已有token的用户访问登录页面，重定向到首页
    next('/')
  } else {
    // 允许访问
    next()
  }
})

const app = createApp(App)

app.use(router)
app.use(i18n)
app.mount('#app') 