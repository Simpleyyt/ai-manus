import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ConnectorsSettings from '../ConnectorsSettings.vue'
import { i18n } from '../../../composables/useI18n'
import {
  resetConnectorsStoreForTests,
  setConnectorsStoreForTests,
} from '../../../composables/connectorsStore'
import type { Connector } from '@/types/connector'

const sample: Connector = {
  id: 'c1',
  name: 'Docs MCP',
  server_key: 'docs_mcp',
  note: 'Search docs',
  transport: 'streamable-http',
  enabled: true,
  source: 'form',
  readonly: false,
  url: 'https://mcp.example.com/mcp',
}

describe('ConnectorsSettings', () => {
  beforeEach(() => {
    resetConnectorsStoreForTests()
    setConnectorsStoreForTests([sample])
  })

  it('renders connector cards and create button', async () => {
    const wrapper = mount(ConnectorsSettings, { global: { plugins: [i18n] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Docs MCP')
    expect(wrapper.find('[data-testid="connectors-create-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="connectors-browse-button"]').exists()).toBe(true)
  })

  it('shows official empty copy when there are no connectors', async () => {
    resetConnectorsStoreForTests()
    setConnectorsStoreForTests([])
    const wrapper = mount(ConnectorsSettings, { global: { plugins: [i18n] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Connect Manus with your everyday apps, APIs and MCPs')
    expect(wrapper.find('[data-testid="connectors-add-button"]').exists()).toBe(true)
  })

  it('filters list by search query', async () => {
    const wrapper = mount(ConnectorsSettings, { global: { plugins: [i18n] } })
    await flushPromises()
    const input = wrapper.find('[data-testid="connectors-search-input"]')
    await input.setValue('___no_such_connector___')
    expect(wrapper.text()).toContain('No matching connectors.')
    expect(wrapper.text()).not.toContain('Docs MCP')
  })

  it('opens create menu with official MCP actions', async () => {
    const wrapper = mount(ConnectorsSettings, {
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await wrapper.find('[data-testid="connectors-create-button"]').trigger('click')
    await flushPromises()
    const menu = document.body.querySelector('[data-testid="connectors-create-menu"]')
    expect(menu).toBeTruthy()
    expect(menu!.textContent).toContain('Custom MCP')
    expect(menu!.textContent).toContain('Import MCP by JSON')
    expect(menu!.textContent).toContain('Add MCP by URL')
    wrapper.unmount()
  })

  it('opens browse dialog when clicking Browse Connectors', async () => {
    const wrapper = mount(ConnectorsSettings, {
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await wrapper.find('[data-testid="connectors-browse-button"]').trigger('click')
    await flushPromises()
    expect(document.body.querySelector('[data-testid="connectors-browse-dialog"]')).toBeTruthy()
    wrapper.unmount()
  })
})
