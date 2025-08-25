<template>
  <div class="w-full min-h-[100vh] relative bg-[var(--background-gray-main)] dark:bg-[#050505]">
    <div class="sticky top-0 left-0 w-full z-[10] px-[48px] max-sm:px-[12px] max-sm:bg-[var(--background-gray-login)]">
      <div class="w-full h-[60px] mx-auto flex items-center justify-between text-[var(--text-primary)]">
        <a href="/">
          <div class="flex">
            <Bot :size="30" />
            <ManusLogoTextIcon />
          </div>
        </a>
      </div>
    </div>
    <div
      class="relative z-[1] flex flex-col justify-center items-center min-h-[100vh] pt-[20px] pb-[60px] -mt-[60px] max-sm:pt-[80px] max-sm:pb-[80px] max-sm:mt-0 max-sm:min-h-[calc(100vh-60px)] max-sm:justify-start">
      <div class="w-full max-w-[720px] pt-[24px] mb-[40px] max-sm:pt-[0px]">
        <div class="flex flex-col items-center gap-[20px] relative" style="z-index:1">
          <div class="w-[80px] h-[80px] text-[var(--icon-primary)] max-sm:w-[64px] max-sm:h-[64px]">
            <Bot :size="80" />
          </div>
          <h1 class="text-[20px] font-bold text-center text-[var(--text-primary)] max-sm:text-[18px]">
            {{ 
              isResettingPassword ? t('Reset Password') 
              : isRegistering ? t('Register to Manus') 
              : t('Login to Manus') 
            }}
          </h1>
        </div>
      </div>
      <LoginForm v-if="!isRegistering && !isResettingPassword" 
        @success="handleLoginSuccess" 
        @switch-to-register="switchToRegister" 
        @switch-to-reset="switchToReset" />
      <RegisterForm v-else-if="isRegistering && !isResettingPassword" 
        @success="handleLoginSuccess" 
        @switch-to-login="switchToLogin" />
      <ResetPasswordForm v-else-if="isResettingPassword" 
        @back-to-login="switchToLogin" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Bot } from 'lucide-vue-next'
import ManusLogoTextIcon from '@/components/icons/ManusLogoTextIcon.vue'
import LoginForm from '@/components/login/LoginForm.vue'
import RegisterForm from '@/components/login/RegisterForm.vue'
import ResetPasswordForm from '@/components/login/ResetPasswordForm.vue'
import { useAuth } from '@/api'

const { t } = useI18n()

const router = useRouter()
const { isAuthenticated } = useAuth()

// Form state for header display
const isRegistering = ref(false)
const isResettingPassword = ref(false)

// Switch to register mode
const switchToRegister = () => {
  isRegistering.value = true
  isResettingPassword.value = false
}

// Switch to login mode
const switchToLogin = () => {
  isRegistering.value = false
  isResettingPassword.value = false
}

// Switch to reset password mode
const switchToReset = () => {
  isRegistering.value = false
  isResettingPassword.value = true
}

// Handle successful login/registration
const handleLoginSuccess = () => {
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/')
}

// Listen for authentication state changes
watch(isAuthenticated, (authenticated) => {
  if (authenticated) {
    handleLoginSuccess()
  }
})

// Check if already logged in when page loads
onMounted(() => {
  if (isAuthenticated.value) {
    router.push('/')
  }
})
</script>