<template>
    <div class="inline-flex relative">
        <svg
            class="transform -rotate-90 absolute top-[50%] mt-[2px] left-[50%] translate-x-[-50%] translate-y-[-50%]"
            viewBox="0 0 16 15" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="8" cy="7.5" r="6" class="stroke-current text-[var(--icon-white-tsp)]"
                stroke-opacity="0.48" stroke-width="1.2" fill="none"></circle>
            <circle cx="8" cy="7.5" r="6" class="stroke-current text-[var(--icon-white)]"
                stroke-width="1.2" fill="none"
                stroke-dasharray="37.69911184307752 37.69911184307752"
                stroke-dashoffset="37.69911184307752" stroke-linecap="round"></circle>
        </svg>
        <slot />
    </div>
</template>

<script setup lang="ts">
// Empty script block for consistency with other icon components
</script> 