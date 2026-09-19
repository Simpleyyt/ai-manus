<template>
  <ConnectorInitialsIcon
    v-if="showInitials"
    :name="connectorName"
    :size="size"
    :class-name="className"
  />
  <Cable
    v-else-if="showCable"
    :size="size"
    color="var(--icon-primary)"
  />
  <img
    v-else
    data-testid="connector-icon-img"
    :src="src || ''"
    :alt="connectorName || 'Connector'"
    :class="className"
    :style="{ width: `${size}px`, height: `${size}px` }"
    @error="failed = true"
  >
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Cable } from 'lucide-vue-next'
import { connectors } from '@/composables/connectorsStore'
import { useDocumentDark } from '@/composables/useDocumentDark'
import ConnectorInitialsIcon from './ConnectorInitialsIcon.vue'

const props = withDefaults(defineProps<{
  uid?: string
  size?: number
  className?: string
  defaultIconUrl?: string | null
  defaultIconUrlDark?: string | null
}>(), {
  uid: '',
  size: 16,
})

const isDark = useDocumentDark()
const failed = ref(false)

const connector = computed(() => (
  props.uid ? connectors.value.find((item) => item.id === props.uid) : undefined
))

const connectorName = computed(() => connector.value?.name || '')

const src = computed(() => {
  if (props.defaultIconUrl || props.defaultIconUrlDark) {
    return (isDark.value && props.defaultIconUrlDark) || props.defaultIconUrl || null
  }
  return connector.value?.icon_url || null
})

watch(src, () => {
  failed.value = false
})

const showInitials = computed(() => (
  (failed.value || !src.value) && Boolean(connectorName.value)
))

const showCable = computed(() => (
  (failed.value || !src.value) && !connectorName.value
))
</script>
