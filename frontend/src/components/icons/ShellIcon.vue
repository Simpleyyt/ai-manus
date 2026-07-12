<template>
    <svg :width="size" :height="size" viewBox="0 0 19 18" fill="none" xmlns="http://www.w3.org/2000/svg"
        :style="{ minWidth: `${size}px`, minHeight: `${size}px` }">
        <g id="chat/type-icon">
            <g id="Rectangle 40263">
                <g filter="url(#filter0_ii_1527_83555)">
                    <path
                        d="M2 4.7C2 3.20883 3.20883 2 4.7 2H13.3C14.7912 2 16 3.20883 16 4.7V13.3C16 14.7912 14.7912 16 13.3 16H4.7C3.20883 16 2 14.7912 2 13.3V4.7Z"
                        fill="url(#paint0_linear_1527_83555)"></path>
                </g>
                <path
                    d="M2.42857 4.7C2.42857 3.44552 3.44552 2.42857 4.7 2.42857H13.3C14.5545 2.42857 15.5714 3.44552 15.5714 4.7V13.3C15.5714 14.5545 14.5545 15.5714 13.3 15.5714H4.7C3.44552 15.5714 2.42857 14.5545 2.42857 13.3V4.7Z"
                    stroke="#B9B9B7" stroke-width="0.857143"></path>
            </g>
            <path id="Vector 7323" d="M5.25 7L7 9L5.25 11" stroke="#535350" stroke-width="1.2" stroke-linecap="round"
                stroke-linejoin="round"></path>
            <path id="Vector 7324" d="M8.625 11H12" stroke="#535350" stroke-width="1.2" stroke-linecap="round"
                stroke-linejoin="round"></path>
        </g>
        <defs>
            <filter id="filter0_ii_1527_83555" x="1.5" y="1.5" width="15" height="15" filterUnits="userSpaceOnUse"
                color-interpolation-filters="sRGB">
                <feFlood flood-opacity="0" result="BackgroundImageFix"></feFlood>
                <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape"></feBlend>
                <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
                    result="hardAlpha"></feColorMatrix>
                <feOffset dx="1" dy="1"></feOffset>
                <feGaussianBlur stdDeviation="0.25"></feGaussianBlur>
                <feComposite in2="hardAlpha" operator="arithmetic" k2="-1" k3="1"></feComposite>
                <feColorMatrix type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.6 0"></feColorMatrix>
                <feBlend mode="normal" in2="shape" result="effect1_innerShadow_1527_83555"></feBlend>
                <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
                    result="hardAlpha"></feColorMatrix>
                <feOffset dx="-1" dy="-1"></feOffset>
                <feGaussianBlur stdDeviation="0.25"></feGaussianBlur>
                <feComposite in2="hardAlpha" operator="arithmetic" k2="-1" k3="1"></feComposite>
                <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.08 0"></feColorMatrix>
                <feBlend mode="normal" in2="effect1_innerShadow_1527_83555" result="effect2_innerShadow_1527_83555">
                </feBlend>
            </filter>
            <linearGradient id="paint0_linear_1527_83555" x1="9" y1="2" x2="9" y2="16" gradientUnits="userSpaceOnUse">
                <stop stop-color="white" stop-opacity="0"></stop>
                <stop offset="1" stop-opacity="0.16"></stop>
            </linearGradient>
        </defs>
    </svg>
</template>

<script setup lang="ts">
defineProps({
    size: {
        type: Number,
        default: 21
    }
});
</script>