import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ConnectorIcon from '../ConnectorIcon.vue'
import {
  resetConnectorsStoreForTests,
  setConnectorsStoreForTests,
} from '../../../composables/connectorsStore'
import type { Connector } from '@/types/connector'

const named: Connector = {
  id: 'c1',
  name: 'Docs MCP',
  server_key: 'docs_mcp',
  transport: 'streamable-http',
  enabled: true,
  source: 'form',
  readonly: false,
}

describe('ConnectorIcon', () => {
  beforeEach(() => {
    resetConnectorsStoreForTests()
  })

  it('renders official initials when the connector has a name but no icon url', () => {
    setConnectorsStoreForTests([named])
    const wrapper = mount(ConnectorIcon, { props: { uid: 'c1', size: 16 } })
    const initials = wrapper.find('[data-testid="connector-initials-icon"]')
    expect(initials.exists()).toBe(true)
    expect(initials.text()).toBe('D')
    expect(initials.classes()).toContain('rounded')
    expect(initials.classes()).toContain('bg-[var(--fill-tsp-white-main)]')
    expect(initials.classes()).toContain('text-[var(--text-secondary)]')
    expect(wrapper.find('svg.lucide-server').exists()).toBe(false)
  })

  it('renders the image when icon_url is set', () => {
    setConnectorsStoreForTests([{
      ...named,
      icon_url: 'https://example.com/docs.webp',
    }])
    const wrapper = mount(ConnectorIcon, { props: { uid: 'c1', size: 16 } })
    const img = wrapper.find('[data-testid="connector-icon-img"]')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('https://example.com/docs.webp')
    expect(img.attributes('alt')).toBe('Docs MCP')
  })

  it('falls back to CableIcon when there is no name and no icon', () => {
    const wrapper = mount(ConnectorIcon, { props: { uid: 'missing', size: 16 } })
    expect(wrapper.find('svg.lucide-cable').exists()).toBe(true)
    expect(wrapper.find('[data-testid="connector-initials-icon"]').exists()).toBe(false)
  })

  it('uses defaultIconUrl before store lookup', () => {
    setConnectorsStoreForTests([named])
    const wrapper = mount(ConnectorIcon, {
      props: {
        uid: 'c1',
        size: 24,
        defaultIconUrl: 'https://cdn.example.com/preview.png',
      },
    })
    expect(wrapper.find('[data-testid="connector-icon-img"]').attributes('src'))
      .toBe('https://cdn.example.com/preview.png')
  })

  it('falls back to the official catalog icon by uid', () => {
    const wrapper = mount(ConnectorIcon, {
      props: { uid: 'bbb0df76-66bd-4a24-ae4f-2aac4750d90b', size: 16 },
    })
    const img = wrapper.find('[data-testid="connector-icon-img"]')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src') || '').toContain('cloudfront.net')
    expect(img.attributes('alt')).toBe('GitHub')
  })

  it('resolves catalog logos from a stored catalog_uid', () => {
    setConnectorsStoreForTests([{
      id: 'learn-1',
      name: 'Microsoft Learn',
      server_key: 'microsoft_learn',
      catalog_uid: 'f4c2516f-40c3-4be2-b1c6-fb18da6a04bf',
      transport: 'streamable-http',
      enabled: true,
      source: 'catalog',
      readonly: false,
    }])
    const wrapper = mount(ConnectorIcon, { props: { uid: 'learn-1', size: 16 } })
    const img = wrapper.find('[data-testid="connector-icon-img"]')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src') || '').toContain('cloudfront.net')
    expect(img.attributes('alt')).toBe('Microsoft Learn')
  })
})
