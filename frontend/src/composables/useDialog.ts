import { ref, reactive, readonly } from 'vue'
import { useI18n } from 'vue-i18n'

// Dialog state
interface DialogState {
  title: string
  content: string
  confirmText: string
  cancelText: string
  confirmType: 'primary' | 'danger'
  inputEnabled: boolean
  inputValue: string
  inputPlaceholder: string
  onConfirm?: (inputValue?: string) => void | Promise<void>
  onCancel?: () => void
}

// Global state
const dialogVisible = ref(false)
const dialogConfig = reactive<DialogState>({
  title: '',
  content: '',
  confirmText: '',
  cancelText: '',
  confirmType: 'primary',
  inputEnabled: false,
  inputValue: '',
  inputPlaceholder: '',
  onConfirm: undefined,
  onCancel: undefined
})

export function useDialog() {
  const { t } = useI18n()

  const handleConfirm = async () => {
    if (dialogConfig.onConfirm) {
      await dialogConfig.onConfirm(dialogConfig.inputEnabled ? dialogConfig.inputValue : undefined)
    }
    dialogVisible.value = false
  }

  const handleCancel = () => {
    if (dialogConfig.onCancel) {
      dialogConfig.onCancel()
    }
    dialogVisible.value = false
  }

  const showConfirmDialog = (options: {
    title: string
    content: string
    confirmText?: string
    cancelText?: string
    confirmType?: 'primary' | 'danger'
    onConfirm?: () => void | Promise<void>
    onCancel?: () => void
  }) => {
    Object.assign(dialogConfig, {
      title: options.title,
      content: options.content,
      confirmText: options.confirmText || t('Confirm'),
      cancelText: options.cancelText || t('Cancel'),
      confirmType: options.confirmType || 'primary',
      inputEnabled: false,
      inputValue: '',
      inputPlaceholder: '',
      onConfirm: options.onConfirm,
      onCancel: options.onCancel
    })
    dialogVisible.value = true
  }

  const showInputDialog = (options: {
    title: string
    content?: string
    initialValue?: string
    placeholder?: string
    confirmText?: string
    cancelText?: string
    onConfirm?: (value: string) => void | Promise<void>
    onCancel?: () => void
  }) => {
    Object.assign(dialogConfig, {
      title: options.title,
      content: options.content || '',
      confirmText: options.confirmText || t('Confirm'),
      cancelText: options.cancelText || t('Cancel'),
      confirmType: 'primary' as const,
      inputEnabled: true,
      inputValue: options.initialValue || '',
      inputPlaceholder: options.placeholder || '',
      onConfirm: async (inputValue?: string) => {
        if (options.onConfirm) {
          await options.onConfirm((inputValue ?? '').trim())
        }
      },
      onCancel: options.onCancel
    })
    dialogVisible.value = true
  }

  const showDeleteSessionDialog = (onConfirm?: () => void | Promise<void>) => {
    showConfirmDialog({
      title: t('Are you sure you want to delete this session?'),
      content: t('The chat history of this session cannot be recovered after deletion.'),
      confirmText: t('Delete'),
      cancelText: t('Cancel'),
      confirmType: 'danger',
      onConfirm
    })
  }

  return {
    dialogVisible: readonly(dialogVisible),
    dialogConfig,
    handleConfirm,
    handleCancel,
    showConfirmDialog,
    showInputDialog,
    showDeleteSessionDialog
  }
}
