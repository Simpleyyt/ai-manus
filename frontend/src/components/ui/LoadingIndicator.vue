<template>
  <div class="flex items-center gap-1 text-[var(--text-tertiary)] text-sm">
    <span v-if="text">{{ text }}</span>
    <span class="flex gap-1 relative top-[4px]">
      <span
        v-for="(_, index) in 3"
        :key="index"
        class="w-[3px] h-[3px] rounded animate-bounce-dot bg-[var(--icon-tertiary)]"
        :style="{ 'animation-delay': `${index * 200}ms` }"
      ></span>
    </span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  text?: string
}

withDefaults(defineProps<Props>(), {
  text: undefined
})
</script>

<style scoped>
.animate-bounce-dot {
  display: inline-block;
  animation: dot-animation 1.5s infinite;
}

@keyframes dot-animation {
  0% {
    transform: translateY(0);
  }

  20% {
    transform: translateY(-4px);
  }

  40% {
    transform: translateY(0);
  }

  100% {
    transform: translateY(0);
  }
}
</style>
