<template>
  <div class="w-full max-w-[384px] py-[24px] pt-0 px-[12px] relative z-[1]">
    <div class="flex flex-col justify-center gap-[40px] text-[var(--text-primary)] max-sm:gap-[12px]">
      <form @submit.prevent="$emit('submit')" class="flex flex-col items-stretch gap-[20px]">
        <div class="relative">
          <div class="transition-all duration-500 ease-out opacity-100 scale-100">
            <div class="flex flex-col gap-[12px]">
              <slot />
            </div>
          </div>
        </div>
        <slot name="footer" />
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  submit: []
}>()
</script>
