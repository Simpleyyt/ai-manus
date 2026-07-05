<template>
  <FormField :id="id" :label="label" :error="error">
    <template #label-extra>
      <slot name="label-extra" />
    </template>
    <div class="relative w-full">
      <input :value="modelValue"
        class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] pr-[40px]"
        :class="{ 'ring-1 ring-[var(--function-error)]': !!error }" :id="id" :placeholder="placeholder"
        :type="showPassword ? 'text' : 'password'" :disabled="disabled"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)" @blur="$emit('blur')">
      <button type="button"
        class="text-[var(--icon-tertiary)] absolute z-30 right-[6px] top-[50%] p-[6px] rounded-md transform -translate-y-1/2 cursor-pointer hover:text-[--icon-primary] active:opacity-90 transition-all"
        @click="showPassword = !showPassword">
        <Eye v-if="showPassword" :size="16" />
        <EyeOff v-else :size="16" />
      </button>
    </div>
  </FormField>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'
import FormField from './FormField.vue'

defineProps<{
  id: string
  label?: string
  modelValue?: string
  error?: string
  placeholder?: string
  disabled?: boolean
}>()

defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()

const showPassword = ref(false)
</script>
