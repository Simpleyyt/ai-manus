<template>
  <div class="flex flex-col items-start">
    <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
      <label :for="id"
        class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
        <slot name="label"><span>{{ label }}</span></slot>
      </label>
      <slot name="label-extra" />
    </div>
    <slot>
      <input :value="modelValue"
        class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pr-1.5 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] w-full"
        :class="{ 'ring-1 ring-[var(--function-error)]': !!error }" :id="id" :placeholder="placeholder"
        :type="type ?? 'text'" :disabled="disabled"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)" @blur="$emit('blur')">
    </slot>
    <div
      class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
      :class="error ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  id: string
  label?: string
  modelValue?: string
  error?: string
  placeholder?: string
  type?: string
  disabled?: boolean
}>()

defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()
</script>
