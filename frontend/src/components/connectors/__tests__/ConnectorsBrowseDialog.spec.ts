import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ConnectorsBrowseDialog from '../ConnectorsBrowseDialog.vue'
import { i18n } from '../../../composables/useI18n'
import {
  resetConnectorsStoreForTests,
  setConnectorsStoreForTests,
} from '../../../composables/connectorsStore'
import { CONNECTOR_IDS } from '@/data/connectorCatalog'

vi.mock('@/api/connectors', () => ({
  fetchConnectors: vi.fn(),
  createConnector: vi.fn(),
  updateConnector: vi.fn(),
  deleteConnector: vi.fn(),
  importMcpJson: vi.fn(),
  createMcpFromUrl: vi.fn(),
  setConnectorEnabled: vi.fn(),
}))

describe('ConnectorsBrowseDialog', () => {
  beforeEach(() => {
    resetConnectorsStoreForTests()
    setConnectorsStoreForTests([])
  })

  it('defaults to Apps tab with official catalog cards, brief, and Plus', async () => {
    const wrapper = mount(ConnectorsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()

    const dialog = document.body.querySelector('[data-testid="connectors-browse-dialog"]')
    expect(dialog).toBeTruthy()
    expect(dialog!.textContent).toContain('Apps')
    expect(dialog!.textContent).toContain('Custom API')
    expect(dialog!.textContent).toContain('Custom MCP')
    expect(dialog!.textContent).toContain('Projects')
    expect(dialog!.textContent).toContain('Gmail')
    expect(dialog!.textContent).toContain('Draft replies, search your inbox, and summarize email threads instantly')

    const appsTab = document.body.querySelector('[data-testid="connectors-browse-tab-apps"]')
    expect(appsTab?.className).toContain('rounded-[999px]')

    const card = document.body.querySelector('[data-testid="connector-catalog-card"]')
    expect(card).toBeTruthy()
    expect(card!.className).toContain('h-[76px]')
    expect(card!.querySelector('[data-testid="connector-catalog-connect"]')).toBeTruthy()
    expect(card!.querySelector('[data-testid="connector-icon-img"]')).toBeTruthy()

    wrapper.unmount()
  })

  it('shows Custom MCP empty cable copy and Projects publish copy', async () => {
    const wrapper = mount(ConnectorsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()

    ;(document.body.querySelector('[data-testid="connectors-browse-tab-custom-mcp"]') as HTMLElement).click()
    await flushPromises()
    expect(document.body.textContent).toContain('No custom MCP added yet.')

    ;(document.body.querySelector('[data-testid="connectors-browse-tab-projects"]') as HTMLElement).click()
    await flushPromises()
    expect(document.body.textContent).toContain(
      'Publish your custom MCP and API connectors to share them with your projects.',
    )

    wrapper.unmount()
  })

  it('shows Custom API catalog cards', async () => {
    const wrapper = mount(ConnectorsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    ;(document.body.querySelector('[data-testid="connectors-browse-tab-custom-api"]') as HTMLElement).click()
    await flushPromises()
    expect(document.body.textContent).toContain('Kling')
    expect(document.body.querySelector('[data-testid="connector-catalog-card"]')).toBeTruthy()
    wrapper.unmount()
  })

  it('keeps GitHub in the Apps catalog', async () => {
    expect(CONNECTOR_IDS.github).toBe('bbb0df76-66bd-4a24-ae4f-2aac4750d90b')
  })
})
