<template>
  <div class="think-container my-3 border border-[var(--border-light)] rounded-lg overflow-hidden">
    <div 
      class="think-header w-full px-4 py-2 bg-[var(--fill-tsp-gray-main)] hover:bg-[var(--fill-tsp-gray-dark)] text-left text-sm font-medium text-[var(--text-secondary)] flex items-center justify-between transition-colors cursor-pointer"
      @click="toggleContent"
    >
      <span class="flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
        </svg>
        思考过程
      </span>
      <svg 
        class="w-4 h-4 transform transition-transform" 
        :class="{ 'rotate-180': isExpanded }"
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </div>
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="max-h-96 opacity-0"
      enter-to-class="max-h-96 opacity-100"
      leave-active-class="transition-all duration-300 ease-in"
      leave-from-class="max-h-96 opacity-100"
      leave-to-class="max-h-0 opacity-0"
    >
      <div 
        v-show="isExpanded"
        class="think-content px-4 py-3 bg-[var(--background-gray-main)] text-sm text-[var(--text-secondary)] whitespace-pre-wrap overflow-hidden"
      >
        {{ content }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  content: string;
}>();

const isExpanded = ref(true);

const toggleContent = () => {
  isExpanded.value = !isExpanded.value;
};
</script>

<style scoped>
.think-container {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.think-header {
  user-select: none;
}

/* 思考图标动画 */
.think-header svg:first-child {
  animation: think-pulse 2s infinite;
}

@keyframes think-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style> 