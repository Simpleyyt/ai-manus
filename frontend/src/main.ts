import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import App from './App.vue'
import './assets/global.css'
import './assets/theme.css'
import './utils/toast'
import i18n from './composables/useI18n'

// Import page components
import HomePage from './pages/HomePage.vue'
import ChatPage from './pages/ChatPage.vue'
import PlaybackPage from './pages/PlaybackPage.vue'

// Create router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/chat', component: ChatPage },
    { path: '/chat/:sessionId', component: ChatPage },
    { path: '/shared/:shareId/:token', component: PlaybackPage }
  ]
})

const app = createApp(App)
app.use(router)
app.use(i18n)
app.use(Toast)
app.mount('#app') 