import { ref, onMounted, watch } from 'vue'

export function useTheme() {
  const isDark = ref(false)

  const checkTheme = () => {
    // 检查HTML根元素是否有dark类
    isDark.value = document.documentElement.classList.contains('dark')
  }

  const toggleTheme = () => {
    isDark.value = !isDark.value
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  onMounted(() => {
    checkTheme()
    
    // 监听主题变化
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          checkTheme()
        }
      })
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    })
  })

  return {
    isDark,
    toggleTheme
  }
} 