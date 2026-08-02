import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ChatAttachmentList from '../ChatAttachmentList.vue'
import { i18n } from '../../composables/useI18n'
import type { FileInfo } from '../../api/file'

vi.mock('../../api/file', () => ({
  getFileDownloadUrl: vi.fn(async () => 'https://example.com/shot.png'),
}))

vi.mock('../../composables/useFilePreviewer', () => ({
  useFilePreviewer: () => ({ showFilePreviewer: vi.fn() }),
}))

describe('ChatAttachmentList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders images in official 88px grid and files as wide chips', async () => {
    const attachments: FileInfo[] = [
      {
        file_id: 'img-1',
        filename: 'a.png',
        content_type: 'image/png',
        size: 10,
        upload_date: '2026-01-01T00:00:00Z',
      },
      {
        file_id: 'doc-1',
        filename: 'notes.txt',
        content_type: 'text/plain',
        size: 5,
        upload_date: '2026-01-01T00:00:00Z',
      },
    ]

    const wrapper = mount(ChatAttachmentList, {
      props: { attachments, alignEnd: true },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    const grid = wrapper.find('[data-testid="chat-detail-image-grid"]')
    expect(grid.exists()).toBe(true)
    expect(grid.classes().join(' ')).toContain('grid-cols-[repeat(6,minmax(0,88px))]')
    expect(grid.findAll('img').length).toBe(1)
    expect(grid.find('.aspect-square').attributes('style')).toContain('grid-column-start: 6')

    expect(wrapper.find('[data-testid="chat-detail-file-chip"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="chat-detail-file-chip"]').text()).toContain('notes.txt')
  })
})
