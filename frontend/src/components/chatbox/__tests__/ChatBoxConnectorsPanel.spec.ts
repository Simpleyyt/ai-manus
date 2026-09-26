import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import ChatBoxConnectorsPanel from '../ChatBoxConnectorsPanel.vue'
import { i18n } from '../../../composables/useI18n'
import {
  resetConnectorsStoreForTests,
  setConnectorsStoreForTests,
} from '../../../composables/connectorsStore'
import type { ConnectorCatalogItem } from '@/data/connectorCatalog'
import { resetCatalogStoreForTests } from '@/composables/catalogStore'
import * as api from '@/api/connectors'
import type { Connector } from '@/types/connector'

vi.mock('@/api/connectors', () => ({
  fetchConnectors: vi.fn(),
  createConnector: vi.fn(),
  updateConnector: vi.fn(),
  deleteConnector: vi.fn(),
  importMcpJson: vi.fn(),
  createMcpFromUrl: vi.fn(),
  createFromCatalog: vi.fn(),
  fetchConnectorCatalog: vi.fn(),
  setConnectorEnabled: vi.fn(),
}))

vi.mock('@/utils/toast', () => ({
  showErrorToast: vi.fn(),
  showSuccessToast: vi.fn(),
  showInfoToast: vi.fn(),
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

const previewCatalog: ConnectorCatalogItem[] = [
  {
    uid: 'crypto',
    name: 'Crypto.com',
    brief: '',
    iconUrl: 'https://cdn.example/crypto.png',
    iconUrlDark: 'https://cdn.example/crypto.png',
    order: 23,
    serverUrl: 'https://mcp.crypto.com/market-data/mcp',
    transport: 'streamable-http',
    requiredHeaders: [],
  },
  {
    uid: 'gecko',
    name: 'CoinGecko',
    brief: '',
    iconUrl: 'https://cdn.example/gecko.png',
    iconUrlDark: 'https://cdn.example/gecko.png',
    order: 27,
    serverUrl: 'https://mcp.api.coingecko.com/mcp',
    transport: 'streamable-http',
    requiredHeaders: [],
  },
  {
    uid: 'pop',
    name: 'PopHIVE',
    brief: '',
    iconUrl: 'https://cdn.example/pop.png',
    iconUrlDark: 'https://cdn.example/pop.png',
    order: 50,
    serverUrl: 'https://mcp.pophive.org/mcp',
    transport: 'streamable-http',
    requiredHeaders: [],
  },
]

describe('ChatBoxConnectorsPanel', () => {
  beforeEach(() => {
    resetConnectorsStoreForTests()
    resetCatalogStoreForTests()
    setConnectorsStoreForTests(sample)
    vi.clearAllMocks()
    vi.mocked(api.fetchConnectorCatalog).mockResolvedValue(previewCatalog)
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
    expect(row.classes().join(' ')).toContain('cursor-pointer')
    expect(row.classes().join(' ')).toContain('select-none')

    const initials = row.find('[data-testid="connector-initials-icon"]')
    expect(initials.exists()).toBe(true)
    expect(initials.text()).toBe('D')

    const add = wrapper.find('[data-testid="chatbox-connectors-add"]')
    expect(add.classes().join(' ')).toContain('h-[36px]')
    expect(add.attributes('data-close-when-click')).toBe('true')
  })

  it('renders ConnectorPreview from installable marketplace logos', async () => {
    const wrapper = mount(ChatBoxConnectorsPanel, {
      props: { open: true },
      global: { plugins: [i18n] },
    })
    await flushPromises()
    await nextTick()

    expect(wrapper.text()).not.toContain('GitHub')
    expect(wrapper.text()).not.toContain('Gmail')

    const preview = wrapper.find('[data-testid="connector-preview"]')
    expect(preview.exists()).toBe(true)
    expect(preview.text()).toContain('+1')
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
})
