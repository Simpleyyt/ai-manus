import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import ChatBoxConnectorsPanel from '../ChatBoxConnectorsPanel.vue'
import { i18n } from '../../../composables/useI18n'
import {
  resetConnectorsStoreForTests,
  setConnectorsStoreForTests,
} from '../../../composables/connectorsStore'
import { CONNECTOR_IDS } from '@/data/connectorCatalog'
import type { Connector } from '@/types/connector'

vi.mock('@/api/connectors', () => ({
  fetchConnectors: vi.fn(),
  createConnector: vi.fn(),
  updateConnector: vi.fn(),
  deleteConnector: vi.fn(),
  importMcpJson: vi.fn(),
  createMcpFromUrl: vi.fn(),
  setConnectorEnabled: vi.fn(),
}))

const sample: Connector[] = [
  {
    id: 'c1',
    name: 'Docs MCP',
    server_key: 'docs_mcp',
    transport: 'streamable-http',
    enabled: true,
    source: 'form',
    readonly: false,
    url: 'https://mcp.example.com/mcp',
  },
]

describe('ChatBoxConnectorsPanel', () => {
  beforeEach(() => {
    resetConnectorsStoreForTests()
    setConnectorsStoreForTests(sample)
  })

  it('renders official row tokens, Add connectors, and Manage connectors', async () => {
    const wrapper = mount(ChatBoxConnectorsPanel, {
      props: { open: true },
      global: { plugins: [i18n] },
    })
    await flushPromises()
    await nextTick()

    const panel = wrapper.find('[data-testid="chatbox-connectors-panel"]')
    expect(panel.exists()).toBe(true)
    expect(wrapper.text()).toContain('Docs MCP')
    expect(wrapper.text()).toContain('Add connectors')
    expect(wrapper.text()).toContain('Manage connectors')

    const row = wrapper.find('[data-testid="chatbox-connector-c1"]')
    expect(row.classes().join(' ')).toContain('group/connector-item')
    expect(row.classes().join(' ')).toContain('h-[36px]')
    expect(row.classes().join(' ')).toContain('ps-[4px]')

    const initials = row.find('[data-testid="connector-initials-icon"]')
    expect(initials.exists()).toBe(true)
    expect(initials.text()).toBe('D')

    const add = wrapper.find('[data-testid="chatbox-connectors-add"]')
    expect(add.classes().join(' ')).toContain('h-[36px]')
    expect(add.attributes('data-close-when-click')).toBe('true')
  })

  it('renders official featured Connect rows, logos, and ConnectorPreview', async () => {
    const wrapper = mount(ChatBoxConnectorsPanel, {
      props: { open: true },
      global: { plugins: [i18n] },
    })
    await flushPromises()
    await nextTick()

    const github = wrapper.find(`[data-testid="chatbox-connector-${CONNECTOR_IDS.github}"]`)
    expect(github.exists()).toBe(true)
    expect(github.text()).toContain('GitHub')
    expect(github.text()).toContain('Connect')
    const img = github.find('[data-testid="connector-icon-img"]')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src') || '').toContain('cloudfront.net')

    const preview = wrapper.find('[data-testid="connector-preview"]')
    expect(preview.exists()).toBe(true)
    expect(preview.text()).toContain('+99')
    expect(preview.classes().join(' ')).toContain('-space-x-1')
  })

  it('emits add and manage', async () => {
    const wrapper = mount(ChatBoxConnectorsPanel, {
      props: { open: true },
      global: { plugins: [i18n] },
    })
    await flushPromises()
    await wrapper.find('[data-testid="chatbox-connectors-add"]').trigger('click')
    await wrapper.find('[data-testid="chatbox-connectors-manage"]').trigger('click')
    expect(wrapper.emitted('add')).toHaveLength(1)
    expect(wrapper.emitted('manage')).toHaveLength(1)
  })

  it('emits add when clicking a featured Connect row', async () => {
    const wrapper = mount(ChatBoxConnectorsPanel, {
      props: { open: true },
      global: { plugins: [i18n] },
    })
    await flushPromises()
    await wrapper.find(`[data-testid="chatbox-connector-${CONNECTOR_IDS.github}"]`).trigger('click')
    expect(wrapper.emitted('add')).toHaveLength(1)
  })
})
