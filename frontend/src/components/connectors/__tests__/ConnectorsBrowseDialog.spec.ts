import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ConnectorsBrowseDialog from '../ConnectorsBrowseDialog.vue'
import { i18n } from '../../../composables/useI18n'
import {
  resetConnectorsStoreForTests,
  setConnectorsStoreForTests,
} from '../../../composables/connectorsStore'
import { CONNECTOR_IDS } from '@/data/connectorCatalog'
import * as api from '@/api/connectors'
import { showInfoToast } from '@/utils/toast'
import type { Connector } from '@/types/connector'

vi.mock('@/api/connectors', () => ({
  fetchConnectors: vi.fn(),
  createConnector: vi.fn(),
  updateConnector: vi.fn(),
  deleteConnector: vi.fn(),
  importMcpJson: vi.fn(),
  createMcpFromUrl: vi.fn(),
  createFromCatalog: vi.fn(),
  setConnectorEnabled: vi.fn(),
}))

vi.mock('@/utils/toast', () => ({
  showErrorToast: vi.fn(),
  showSuccessToast: vi.fn(),
  showInfoToast: vi.fn(),
}))

const learnConnector: Connector = {
  id: 'learn-1',
  name: 'Microsoft Learn',
  server_key: 'microsoft_learn',
  catalog_uid: CONNECTOR_IDS.microsoftLearn,
  transport: 'streamable-http',
  enabled: true,
  source: 'catalog',
  readonly: false,
  url: 'https://learn.microsoft.com/api/mcp',
}

async function searchBrowse(text: string) {
  const input = document.body.querySelector('[data-testid="connectors-browse-search"]') as HTMLInputElement
  input.value = text
  input.dispatchEvent(new Event('input', { bubbles: true }))
  await flushPromises()
}

function catalogCard(name: string): HTMLElement {
  const cards = [...document.body.querySelectorAll('[data-testid="connector-catalog-card"]')]
  const match = cards.find((node) => node.textContent?.includes(name))
  if (!match) throw new Error(`catalog card not found: ${name}`)
  return match as HTMLElement
}

describe('ConnectorsBrowseDialog', () => {
  beforeEach(() => {
    resetConnectorsStoreForTests()
    setConnectorsStoreForTests([])
    vi.clearAllMocks()
  })

  it('defaults to Apps tab with only installable MCP cards', async () => {
    const wrapper = mount(ConnectorsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()

    const dialog = document.body.querySelector('[data-testid="connectors-browse-dialog"]')
    expect(dialog).toBeTruthy()
    expect(dialog!.textContent).toContain('Apps')
    expect(dialog!.textContent).toContain('Custom MCP')
    expect(dialog!.textContent).not.toContain('Custom API')
    expect(dialog!.textContent).not.toContain('Projects')
    expect(dialog!.textContent).not.toContain('Gmail')
    expect(dialog!.textContent).not.toContain('GitHub')
    expect(dialog!.textContent).toContain('Crypto.com')
    expect(dialog!.textContent).toContain('CoinGecko')

    const appsTab = document.body.querySelector('[data-testid="connectors-browse-tab-apps"]')
    expect(appsTab?.className).toContain('rounded-[8px]')
    expect(appsTab?.className).toContain('bg-[var(--fill-tsp-white-dark)]')
    expect(appsTab?.className).not.toContain('rounded-[999px]')

    const cards = [...document.body.querySelectorAll('[data-testid="connector-catalog-card"]')]
    expect(cards.length).toBeGreaterThan(11)
    expect(cards[0]!.className).toContain('h-[76px]')
    expect(cards[0]!.textContent).toContain('Crypto.com')
    expect(cards[1]!.textContent).toContain('CoinGecko')
    expect(cards[0]!.querySelector('[data-testid="connector-catalog-connect"]')).toBeTruthy()
    expect(cards[0]!.querySelector('[data-testid="connector-catalog-connect"]')?.className).toContain('size-8')
    expect(cards[0]!.querySelector('[data-testid="connector-icon-img"]')).toBeTruthy()

    wrapper.unmount()
  })

  it('shows Custom MCP empty cable copy', async () => {
    const wrapper = mount(ConnectorsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()

    ;(document.body.querySelector('[data-testid="connectors-browse-tab-custom-mcp"]') as HTMLElement).click()
    await flushPromises()
    expect(document.body.textContent).toContain('No custom MCP added yet.')

    wrapper.unmount()
  })

  it('does not list OAuth apps such as Gmail', async () => {
    const wrapper = mount(ConnectorsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await searchBrowse('Gmail')
    expect(document.body.querySelector('[data-testid="connector-catalog-card"]')).toBeNull()
    expect(api.createFromCatalog).not.toHaveBeenCalled()
    expect(showInfoToast).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('installs Microsoft Learn from Plus into a real catalog connector', async () => {
    vi.mocked(api.createFromCatalog).mockResolvedValue(learnConnector)
    vi.mocked(api.fetchConnectors).mockResolvedValue([learnConnector])
    const wrapper = mount(ConnectorsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await searchBrowse('Microsoft Learn')
    const plus = catalogCard('Microsoft Learn').querySelector('[data-testid="connector-catalog-connect"]') as HTMLElement
    plus.click()
    await flushPromises()
    expect(api.createFromCatalog).toHaveBeenCalledWith(expect.objectContaining({
      catalog_uid: CONNECTOR_IDS.microsoftLearn,
      url: 'https://learn.microsoft.com/api/mcp',
      transport: 'streamable-http',
    }))
    expect(catalogCard('Microsoft Learn').querySelector('svg.lucide-check')).toBeTruthy()
    expect(catalogCard('Microsoft Learn').querySelector('svg.lucide-plus')).toBeFalsy()
    wrapper.unmount()
  })

  it('shows Check when the same catalog_uid is already installed', async () => {
    setConnectorsStoreForTests([learnConnector])
    const wrapper = mount(ConnectorsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await searchBrowse('Microsoft Learn')
    expect(catalogCard('Microsoft Learn').querySelector('svg.lucide-check')).toBeTruthy()
    catalogCard('Microsoft Learn').click()
    await flushPromises()
    expect(api.createFromCatalog).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('asks for the TomTom API key before installing', async () => {
    const wrapper = mount(ConnectorsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await searchBrowse('TomTom')
    ;(catalogCard('TomTom Maps').querySelector('[data-testid="connector-catalog-connect"]') as HTMLElement).click()
    await flushPromises()
    expect(api.createFromCatalog).not.toHaveBeenCalled()
    expect(document.body.querySelector('[data-testid="catalog-mcp-secrets-dialog"]')).toBeTruthy()
    expect(document.body.querySelector('[data-testid="catalog-secret-tomtom-api-key"]')).toBeTruthy()
    wrapper.unmount()
  })
})
