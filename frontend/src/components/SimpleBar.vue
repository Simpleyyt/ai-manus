<template>
    <div data-simplebar="init" class="[&_.simplebar-scrollbar]:opacity-0 [&_.simplebar-scrollbar::before]:w-[var(--simplebar-scrollbar-width)] [&_.simplebar-scrollbar::before]:bg-[var(--text-disable)] [&_.simplebar-track.simplebar-vertical]:w-[calc(var(--simplebar-scrollbar-width)+2px)] [&_.simplebar-track.simplebar-vertical]:mr-1 [&:hover_.simplebar-scrollbar]:opacity-100 [&:hover_.simplebar-scrollbar::before]:bg-[var(--text-tertiary)] [&_.simplebar-track.simplebar-vertical.simplebar-hover_.simplebar-scrollbar::before]:bg-[var(--text-tertiary)] [&_.simplebar-content-wrapper]:flex [&_.simplebar-content-wrapper]:flex-col [&_.simplebar-content-wrapper]:h-full [&_.simplebar-content]:flex [&_.simplebar-content]:flex-1 flex flex-1 min-w-0 h-full [&_.simplebar-content]:flex-row simplebar-scrollable-y"
        style="--simplebar-scrollbar-width: 6px;">
        <div class="simplebar-wrapper" :style="{ margin: 0 }">
            <div class="simplebar-height-auto-observer-wrapper">
                <div class="simplebar-height-auto-observer"></div>
            </div>
            <div class="simplebar-mask">
                <div class="simplebar-offset" :style="{ right: '0px', bottom: '0px' }">
                    <div ref="contentWrapperRef" class="simplebar-content-wrapper" tabIndex="0" role="region"
                        aria-label="scrollable content" :style="{ height: '100%', overflow: 'hidden scroll' }"
                        @scroll="handleScroll">
                        <div class="simplebar-content" :style="{ padding: '0px' }">
                            <slot></slot>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const emit = defineEmits(['scroll']);
const contentWrapperRef = ref<HTMLElement | null>(null);

const handleScroll = (event: Event) => {
    emit('scroll', event);
};

const scrollToBottom = () => {
    if (contentWrapperRef.value) {
        contentWrapperRef.value.scrollTop = contentWrapperRef.value.scrollHeight;
    }
};

const scrollToTop = () => {
    if (contentWrapperRef.value) {
        contentWrapperRef.value.scrollTop = 0;
    }
};

const isScrolledToBottom = (threshold = 10) => {
    if (!contentWrapperRef.value) return false;
    const { scrollTop, scrollHeight, clientHeight } = contentWrapperRef.value;
    return scrollHeight - scrollTop - clientHeight <= threshold;
};

const canScroll = () => {
    if (!contentWrapperRef.value) return false;
    return contentWrapperRef.value.scrollHeight > contentWrapperRef.value.clientHeight;
};

defineExpose({
    scrollToBottom,
    scrollToTop,
    isScrolledToBottom,
    canScroll
});
</script>
<style>
[data-simplebar] {
    position: relative;
    flex-direction: column;
    flex-wrap: wrap;
    justify-content: flex-start;
    align-content: flex-start;
    align-items: flex-start
}

.simplebar-wrapper {
    overflow: hidden;
    width: inherit;
    height: inherit;
    max-width: inherit;
    max-height: inherit
}

.simplebar-mask {
    direction: inherit;
    overflow: hidden;
    width: auto !important;
    height: auto !important;
    z-index: 0
}

.simplebar-mask,
.simplebar-offset {
    position: absolute;
    padding: 0;
    margin: 0;
    left: 0;
    top: 0;
    bottom: 0;
    right: 0
}

.simplebar-offset {
    direction: inherit !important;
    box-sizing: inherit !important;
    resize: none !important;
    -webkit-overflow-scrolling: touch
}

.simplebar-content-wrapper {
    direction: inherit;
    box-sizing: border-box !important;
    position: relative;
    display: block;
    height: 100%;
    width: auto;
    max-width: 100%;
    max-height: 100%;
    overflow: auto;
    scrollbar-width: none;
    -ms-overflow-style: none
}

.simplebar-content-wrapper::-webkit-scrollbar,
.simplebar-hide-scrollbar::-webkit-scrollbar {
    display: none;
    width: 0;
    height: 0
}

.simplebar-content:after,
.simplebar-content:before {
    content: " ";
    display: table
}

.simplebar-placeholder {
    max-height: 100%;
    max-width: 100%;
    width: 100%;
    pointer-events: none
}

.simplebar-height-auto-observer-wrapper {
    box-sizing: inherit !important;
    height: 100%;
    width: 100%;
    max-width: 1px;
    position: relative;
    float: left;
    max-height: 1px;
    overflow: hidden;
    z-index: -1;
    padding: 0;
    margin: 0;
    pointer-events: none;
    flex-grow: inherit;
    flex-shrink: 0;
    flex-basis: 0
}

.simplebar-height-auto-observer {
    box-sizing: inherit;
    display: block;
    opacity: 0;
    top: 0;
    left: 0;
    height: 1000%;
    width: 1000%;
    min-height: 1px;
    min-width: 1px;
    z-index: -1
}

.simplebar-height-auto-observer,
.simplebar-track {
    position: absolute;
    overflow: hidden;
    pointer-events: none
}

.simplebar-track {
    z-index: 1;
    right: 0;
    bottom: 0
}

[data-simplebar].simplebar-dragging,
[data-simplebar].simplebar-dragging .simplebar-content {
    pointer-events: none;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    user-select: none
}

[data-simplebar].simplebar-dragging .simplebar-track {
    pointer-events: all
}

.simplebar-scrollbar {
    position: absolute;
    left: 0;
    right: 0;
    min-height: 10px
}

.simplebar-scrollbar:before {
    position: absolute;
    content: "";
    background: #000;
    border-radius: 7px;
    opacity: 0;
    transition: opacity .2s linear .5s
}

.simplebar-scrollbar.simplebar-visible:before {
    opacity: .5;
    transition-delay: 0s;
    transition-duration: 0s
}

.simplebar-track.simplebar-vertical {
    top: 0;
    width: 11px
}

.simplebar-scrollbar:before {
    top: 2px;
    bottom: 2px;
    left: 2px;
    right: 2px
}

.simplebar-track.simplebar-horizontal {
    left: 0;
    height: 11px
}

.simplebar-track.simplebar-horizontal .simplebar-scrollbar {
    right: auto;
    left: 0;
    top: 0;
    bottom: 0;
    min-height: 0;
    min-width: 10px;
    width: auto
}

[data-simplebar-direction=rtl] .simplebar-track.simplebar-vertical {
    right: auto;
    left: 0
}

.simplebar-dummy-scrollbar-size {
    direction: rtl;
    position: fixed;
    opacity: 0;
    visibility: hidden;
    height: 500px;
    width: 500px;
    overflow-y: hidden;
    overflow-x: scroll;
    -ms-overflow-style: scrollbar !important
}

.simplebar-dummy-scrollbar-size>div {
    width: 200%;
    height: 200%;
    margin: 10px 0
}

.simplebar-hide-scrollbar {
    position: fixed;
    left: 0;
    visibility: hidden;
    overflow-y: scroll;
    scrollbar-width: none;
    -ms-overflow-style: none
}
</style>