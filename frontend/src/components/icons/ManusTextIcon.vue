<template>
    <div class="flex items-center">
        <img
            :src="logoSrc"
            alt="Manus Text"
            :style="imgStyle"
            @error="handleImageError"
            class="logo-image"
        />
        <span class="text-[var(--text-primary)] font-medium text-base">关基安全智能体</span>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
    size?: number
    class?: string
}

const props = withDefaults(defineProps<Props>(), {
    size: 20,
    class: ''
})

const logoSrc = computed(() => {
    return new URL('../../assets/images/logo.png', import.meta.url).href
})

const imgStyle = computed(() => {
    // 保持宽高比 59:10
    const aspectRatio = 59 / 10
    const height = props.size
    const width = height * aspectRatio

    return {
        width: `${width}px`,
        height: `${height}px`,
        objectFit: 'contain',
        display: 'block'
    }
})

const handleImageError = (event: Event) => {
    console.error('Failed to load Manus text image:', event)
    const img = event.target as HTMLImageElement
    img.style.display = 'none'
}
</script>

<style scoped>
.logo-image {
    display: block;
    vertical-align: top;
    margin: 0;
    padding: 0;
}
</style>
