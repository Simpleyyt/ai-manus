<template>
  <img
    v-if="connector.icon_url"
    :alt="connector.name"
    :src="connector.icon_url"
    :style="{ width: `${size}px`, height: `${size}px` }"
  >
  <Server
    v-else
    :size="size"
    color="var(--icon-secondary)"
  />
</template>

<script setup lang="ts">
import { Server } from 'lucide-vue-next'
import type { Connector } from '@/types/connector'

withDefaults(defineProps<{
  connector: Connector
  size?: number
}>(), {
  size: 16,
})
</script>
