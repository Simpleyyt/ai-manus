import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ConnectorPreview from '../ConnectorPreview.vue'

describe('ConnectorPreview', () => {
  it('renders overlapping logos from installable marketplace apps', () => {
    const wrapper = mount(ConnectorPreview)
    const root = wrapper.find('[data-testid="connector-preview"]')
    expect(root.exists()).toBe(true)
    expect(root.classes().join(' ')).toContain('-space-x-1')
    expect(root.text()).toContain('+65')
    const imgs = wrapper.findAll('[data-testid="connector-icon-img"]')
    expect(imgs).toHaveLength(2)
    expect(imgs[0].attributes('alt')).toBe('Crypto.com')
    expect(imgs[1].attributes('alt')).toBe('CoinGecko')
    expect(imgs[0].attributes('src') || '').toContain('cloudfront.net')
  })
})
