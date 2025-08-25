<template>
  <div class="w-full max-w-[384px] py-[24px] pt-0 px-[12px] relative" style="z-index:1">
    <div class="flex flex-col justify-center gap-[40px] text-[var(--text-primary)] max-sm:gap-[12px]">
      <form @submit.prevent="handleSubmit" class="flex flex-col items-stretch gap-[20px]">
        <div class="relative">
          <div class="transition-all duration-500 ease-out opacity-100 scale-100">
            <div class="flex flex-col gap-[12px]">
              <!-- Full name field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="fullname"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Full Name') }}</span>
                  </label>
                </div>
                <input v-model="formData.fullname"
                  class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pr-1.5 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] w-full"
                  :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.fullname }" id="fullname"
                  :placeholder="t('Enter your full name')" :disabled="isLoading" @input="validateField('fullname')"
                  @blur="validateField('fullname')">
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.fullname ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.fullname }}
                </div>
              </div>

              <!-- Email field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="email"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Email') }}</span>
                  </label>
                </div>
                <input v-model="formData.email"
                  class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pr-1.5 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] w-full"
                  :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.email }" id="email"
                  placeholder="mail@domain.com" type="email" :disabled="isLoading" @input="validateField('email')"
                  @blur="validateField('email')">
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.email ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.email }}
                </div>
              </div>

              <!-- Password field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="password"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Password') }}</span>
                  </label>
                </div>
                <div class="relative w-full">
                  <input v-model="formData.password"
                    class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] pr-[40px]"
                    :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.password }"
                    :placeholder="t('Enter password')" :type="showPassword ? 'text' : 'password'"
                    :disabled="isLoading" @input="validateField('password')" @blur="validateField('password')">
                  <div
                    class="text-[var(--icon-tertiary)] absolute z-30 right-[6px] top-[50%] p-[6px] rounded-md transform -translate-y-1/2 cursor-pointer hover:text-[--icon-primary] active:opacity-90 transition-all"
                    @click="showPassword = !showPassword">
                    <Eye v-if="showPassword" :size="16" />
                    <EyeOff v-else :size="16" />
                  </div>
                </div>
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.password ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.password }}
                </div>
              </div>

              <!-- Confirm password field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="confirmPassword"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Confirm Password') }}</span>
                  </label>
                </div>
                <div class="relative w-full">
                  <input v-model="formData.confirmPassword"
                    class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] pr-[40px]"
                    :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.confirmPassword }"
                    :placeholder="t('Enter password again')" :type="showConfirmPassword ? 'text' : 'password'"
                    :disabled="isLoading" @input="validateField('confirmPassword')"
                    @blur="validateField('confirmPassword')">
                  <div
                    class="text-[var(--icon-tertiary)] absolute z-30 right-[6px] top-[50%] p-[6px] rounded-md transform -translate-y-1/2 cursor-pointer hover:text-[--icon-primary] active:opacity-90 transition-all"
                    @click="showConfirmPassword = !showConfirmPassword">
                    <Eye v-if="showConfirmPassword" :size="16" />
                    <EyeOff v-else :size="16" />
                  </div>
                </div>
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.confirmPassword ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.confirmPassword }}
                </div>
              </div>

              <!-- Submit button -->
              <button type="submit"
                class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors h-[40px] px-[16px] rounded-[10px] gap-[6px] text-sm min-w-16 w-full"
                :class="isFormValid && !isLoading
                  ? 'bg-[var(--Button-primary-black)] text-[var(--text-onblack)] hover:opacity-90 active:opacity-80'
                  : 'bg-[#898988] dark:bg-[#939393] text-[var(--text-onblack)] opacity-50 cursor-not-allowed'"
                :disabled="!isFormValid || isLoading">
                <LoaderCircle v-if="isLoading" :size="16" class="animate-spin" />
                <span>{{ isLoading ? t('Processing...') : t('Register') }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Toggle to login -->
        <div class="text-center text-[13px] leading-[18px] text-[var(--text-tertiary)] mt-[8px]">
          <span>{{ t('Already have an account?') }}</span>
          <span
            class="ms-[8px] text-[var(--text-secondary)] cursor-pointer select-none hover:opacity-80 active:opacity-70 transition-all underline"
            @click="emits('switchToLogin')">
            {{ t('Login') }}
          </span>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Eye, EyeOff, LoaderCircle } from 'lucide-vue-next'
import { useAuth } from '@/api'
import { validateUserInput } from '@/utils/auth'
import { showErrorToast, showSuccessToast } from '@/utils/toast'

const { t } = useI18n()

// Emits
const emits = defineEmits<{
  success: []
  switchToLogin: []
}>()

const { register, isLoading, authError } = useAuth()

// Form state
const showPassword = ref(false)
const showConfirmPassword = ref(false)

// Form data
const formData = ref({
  fullname: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// Validation errors
const validationErrors = ref<Record<string, string>>({})

// Clear form
const clearForm = () => {
  formData.value = {
    fullname: '',
    email: '',
    password: '',
    confirmPassword: ''
  }
  validationErrors.value = {}
}

// Validate single field
const validateField = (field: string) => {
  const errors: Record<string, string> = {}

  if (field === 'fullname') {
    const result = validateUserInput({ fullname: formData.value.fullname })
    if (result.errors.fullname) {
      errors.fullname = result.errors.fullname
    }
  }

  if (field === 'email') {
    const result = validateUserInput({ email: formData.value.email })
    if (result.errors.email) {
      errors.email = result.errors.email
    }
  }

  if (field === 'password') {
    const result = validateUserInput({ password: formData.value.password })
    if (result.errors.password) {
      errors.password = result.errors.password
    }
  }

  if (field === 'confirmPassword') {
    if (formData.value.password !== formData.value.confirmPassword) {
      errors.confirmPassword = t('Passwords do not match')
    }
  }

  // Update error state
  Object.keys(errors).forEach(key => {
    validationErrors.value[key] = errors[key]
  })

  // Clear fixed errors
  if (!errors[field]) {
    delete validationErrors.value[field]
  }
}

// Validate entire form
const validateForm = () => {
  const data = {
    fullname: formData.value.fullname,
    email: formData.value.email,
    password: formData.value.password
  }

  const result = validateUserInput(data)
  validationErrors.value = { ...result.errors }

  // Validate confirm password
  if (formData.value.password !== formData.value.confirmPassword) {
    validationErrors.value.confirmPassword = t('Passwords do not match')
  }

  return Object.keys(validationErrors.value).length === 0
}

// Check if form is valid
const isFormValid = computed(() => {
  const hasRequiredFields = formData.value.fullname.trim() && 
                           formData.value.email.trim() && 
                           formData.value.password.trim() && 
                           formData.value.confirmPassword.trim()

  const hasNoErrors = Object.keys(validationErrors.value).length === 0

  return hasRequiredFields && hasNoErrors
})

// Submit form
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  try {
    await register({
      fullname: formData.value.fullname,
      email: formData.value.email,
      password: formData.value.password
    })
    
    // Registration success message
    showSuccessToast(t('Registration successful! Welcome to Manus'))
    
    // Emit success event
    emits('success')
  } catch (error: any) {
    console.error('Registration failed:', error)
    // Display error message using toast
    showErrorToast(authError.value || t('Registration failed, please try again'))
  }
}

// Re-validate confirm password when original password changes
watch(() => formData.value.password, () => {
  if (formData.value.confirmPassword) {
    validateField('confirmPassword')
  }
})

// Expose clearForm method for parent component
defineExpose({
  clearForm
})
</script>
