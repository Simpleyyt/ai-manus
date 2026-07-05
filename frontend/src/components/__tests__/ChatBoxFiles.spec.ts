import { describe, it, expect, vi, beforeEach } from 'vitest'
import { defineComponent, ref, type Ref } from 'vue'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import ChatBoxFiles, { type ExtendedFileInfo } from '../ChatBoxFiles.vue'
import { i18n } from '../../composables/useI18n'
import type { FileInfo } from '../../api/file'

vi.mock('../../api/file', () => ({
  uploadFile: vi.fn()
}))

import { uploadFile as apiUploadFile } from '../../api/file'

const uploadedFile: FileInfo = {
  file_id: 'server-id-1',
  filename: 'hello.txt',
  content_type: 'text/plain',
  size: 5,
  upload_date: '2026-01-01T00:00:00Z'
}

/** Mounts ChatBoxFiles inside a parent that provides the v-model binding. */
const mountWithParent = (initial: ExtendedFileInfo[] = []) => {
  const attachments = ref<ExtendedFileInfo[]>(initial) as Ref<ExtendedFileInfo[]>
  const Parent = defineComponent({
    components: { ChatBoxFiles },
    setup: () => ({ attachments }),
    template: '<ChatBoxFiles v-model:attachments="attachments" />'
  })
  const wrapper = mount(Parent, { global: { plugins: [i18n] } })
  return { wrapper, attachments }
}

const selectFile = async (wrapper: VueWrapper) => {
  const file = new File(['hello'], 'hello.txt', { type: 'text/plain' })
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, 'files', { value: [file] })
  await input.trigger('change')
  await flushPromises()
}

describe('ChatBoxFiles', () => {
  beforeEach(() => {
    vi.mocked(apiUploadFile).mockReset()
  })

  it('propagates uploaded files to the parent via v-model:attachments', async () => {
    vi.mocked(apiUploadFile).mockResolvedValue(uploadedFile)
    const { wrapper, attachments } = mountWithParent()

    await selectFile(wrapper)

    expect(attachments.value).toHaveLength(1)
    expect(attachments.value[0].status).toBe('success')
    expect(attachments.value[0].file_id).toBe('server-id-1')
    expect(attachments.value[0].filename).toBe('hello.txt')
  })

  it('marks the file as failed when the upload throws', async () => {
    vi.mocked(apiUploadFile).mockRejectedValue(new Error('network down'))
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { wrapper, attachments } = mountWithParent()

    await selectFile(wrapper)

    expect(attachments.value).toHaveLength(1)
    expect(attachments.value[0].status).toBe('failed')
    consoleError.mockRestore()
  })

  it('removes the file from the parent list when the remove button is clicked', async () => {
    const existing: ExtendedFileInfo = { ...uploadedFile, status: 'success' }
    const { wrapper, attachments } = mountWithParent([existing])

    await wrapper.find('button').trigger('click')

    expect(attachments.value).toEqual([])
  })

  it('does not mutate the attachments prop array directly', async () => {
    vi.mocked(apiUploadFile).mockResolvedValue(uploadedFile)
    const initial: ExtendedFileInfo[] = []
    const wrapper = mount(ChatBoxFiles, {
      props: { attachments: initial },
      global: { plugins: [i18n] }
    })

    await selectFile(wrapper)

    // The parent array must stay untouched; updates flow through emits only
    expect(initial).toHaveLength(0)
    expect(wrapper.emitted('update:attachments')).toBeTruthy()
  })

  it('treats server-provided files without status as uploaded', () => {
    const wrapper = mount(ChatBoxFiles, {
      props: { attachments: [{ ...uploadedFile }] },
      global: { plugins: [i18n] }
    })
    expect((wrapper.vm as unknown as { isAllUploaded: boolean }).isAllUploaded).toBe(true)
  })

  it('reports not-all-uploaded while a file is uploading', () => {
    const wrapper = mount(ChatBoxFiles, {
      props: { attachments: [{ ...uploadedFile, status: 'uploading' }] },
      global: { plugins: [i18n] }
    })
    expect((wrapper.vm as unknown as { isAllUploaded: boolean }).isAllUploaded).toBe(false)
  })
})
