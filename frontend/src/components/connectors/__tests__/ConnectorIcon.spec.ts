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
})
