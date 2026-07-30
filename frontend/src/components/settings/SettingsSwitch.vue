<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<{
  checked?: boolean
  disabled?: boolean
  size?: 'small' | 'medium' | 'large'
}>(), {
  checked: false,
  disabled: false,
  size: 'medium',
})

const emit = defineEmits<{
  'update:checked': [value: boolean]
  'checked-change': [value: boolean]
}>()

const trackClass = computed(() => cn(
  'rounded-[16px] transition-colors',
  {
    small: 'w-[22px] h-[14px] px-[1px]',
    medium: 'w-[26px] h-[16px] px-[1px]',
    large: 'w-[36px] h-[20px] px-[2px]',
  }[props.size],
  props.disabled && 'opacity-50 cursor-not-allowed',
  props.checked ? 'bg-[var(--icon-blue)]' : 'bg-[var(--icon-disable)]',
))

const thumbClass = computed(() => cn(
  'block pointer-events-none rounded-full bg-[var(--icon-white)] transition-transform',
  {
    small: 'size-3 translate-y-[1px]',
    medium: 'size-3.5 translate-y-[1px]',
    large: 'size-4 translate-y-[2px]',
  }[props.size],
  props.checked && ({
    small: 'translate-x-2 rtl:-translate-x-2',
    medium: 'translate-x-2.5 rtl:-translate-x-2.5',
    large: 'translate-x-4 rtl:-translate-x-4',
  }[props.size]),
))

const onClick = () => {
  if (props.disabled) return
  const next = !props.checked
  emit('update:checked', next)
  emit('checked-change', next)
}
</script>

<template>
  <button
    type="button"
    role="switch"
    :data-checked="checked ? '' : undefined"
    :data-disabled="disabled ? '' : undefined"
    :aria-checked="checked"
    :disabled="disabled"
    class="group flex items-center gap-2 cursor-pointer"
    @click="onClick"
  >
    <div :class="trackClass">
      <span :class="thumbClass" />
    </div>
  </button>
</template>
