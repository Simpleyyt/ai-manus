declare module '*.vue' {
  import Vue from 'vue'
  export default Vue
}

declare module 'vue-toastification' {
  import { PluginFunction } from 'vue'
  const plugin: PluginFunction<any>
  export default plugin
}

declare module 'lucide-vue' {
  import Vue from 'vue'
  export const Bot: typeof Vue
  export const Play: typeof Vue
  export const Pause: typeof Vue
  export const StepBack: typeof Vue
  export const StepForward: typeof Vue
  export const Share2: typeof Vue
  export const FileSearch: typeof Vue
  export const ArrowDown: typeof Vue
}

declare module '@vue/composition-api' {
  import { PluginFunction } from 'vue'
  const plugin: PluginFunction<any>
  export default plugin
  export const ref: any
  export const onMounted: any
  export const onUnmounted: any
  export const watch: any
  export const reactive: any
  export const toRefs: any
  export const nextTick: any
}

declare module 'vue-router' {
  import { PluginFunction } from 'vue'
  const plugin: PluginFunction<any>
  export default plugin
  export const useRouter: any
  export const onBeforeRouteUpdate: any
}

declare module 'vue-i18n' {
  import { PluginFunction } from 'vue'
  const plugin: PluginFunction<any>
  export default plugin
  export const useI18n: any
} 