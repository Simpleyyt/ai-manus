<template>
  <!-- Official Manus AgentIsTyping: text + 3 bounce dots -->
  <div class="flex items-center gap-1 text-[var(--text-tertiary)] text-sm">
    <span v-if="text">{{ text }}</span>
    <span class="flex gap-1 relative top-[4px]">
      <span
        v-for="delay in delays"
        :key="delay"
        class="w-[3px] h-[3px] rounded animate-bounce-dot bg-[var(--icon-tertiary)]"
        :style="{ animationDelay: delay }"
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

const delays = ['0ms', '200ms', '400ms'] as const
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
