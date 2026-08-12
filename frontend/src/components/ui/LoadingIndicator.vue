<template>
  <!-- Official Manus thinking row (user-pasted DOM) -->
  <div class="flex items-center h-[28px] gap-2" style="opacity: 1">
    <LiveStatusCanvas :size="16" />
    <div
      class="animate-live-status-shimmer bg-[linear-gradient(110deg,var(--text-primary),35%,var(--text-shining),50%,var(--text-primary),75%,var(--text-primary))] bg-[length:200%_100%] bg-clip-text text-[14px] text-transparent [contain:paint] motion-reduce:animate-none motion-reduce:bg-none motion-reduce:text-[var(--text-primary)]">
      {{ text }}
    </div>
  </div>
</template>

<script setup lang="ts">
import LiveStatusCanvas from '@/components/LiveStatusCanvas.vue'

interface Props {
  text?: string
}

withDefaults(defineProps<Props>(), {
  text: undefined,
})
</script>
