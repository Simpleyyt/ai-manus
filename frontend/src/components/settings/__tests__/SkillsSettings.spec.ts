import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SkillsSettings from '../SkillsSettings.vue'
import { i18n } from '../../../composables/useI18n'
import { resetSkillsStoreForTests, setSkillsStoreForTests } from '../../../composables/skillsStore'

describe('SkillsSettings', () => {
  beforeEach(() => {
    resetSkillsStoreForTests()
    setSkillsStoreForTests({
      added: [
        {
          id: 'skill_market_research',
          name: 'market-research',
          description: 'Research markets',
          owner_type: 'official',
          enabled: true,
        },
      ],
      catalog: [
        {
          id: 'skill_market_research',
          name: 'market-research',
          description: 'Research markets',
          owner_type: 'official',
        },
      ],
    })
  })

  it('renders skill cards and create button', async () => {
    const wrapper = mount(SkillsSettings, { global: { plugins: [i18n] } })
    await flushPromises()
    expect(wrapper.text()).toContain('market-research')
    expect(wrapper.find('[data-testid="skills-create-button"]').exists()).toBe(true)
  })

  it('filters list by search query', async () => {
    const wrapper = mount(SkillsSettings, { global: { plugins: [i18n] } })
    await flushPromises()
    const input = wrapper.find('[data-testid="skills-search-input"]')
    await input.setValue('___no_such_skill___')
    expect(wrapper.text()).toContain('No skills yet')
    expect(wrapper.text()).not.toContain('market-research')
  })

  it('opens create menu with four official actions', async () => {
    const wrapper = mount(SkillsSettings, {
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await wrapper.find('[data-testid="skills-create-button"]').trigger('click')
    await flushPromises()
    const menu = document.body.querySelector('[data-testid="skills-create-menu"]')
    expect(menu).toBeTruthy()
    expect(menu!.textContent).toContain('Create Skill with Manus')
    wrapper.unmount()
  })

  it('opens browse dialog when clicking Browse Skills', async () => {
    const wrapper = mount(SkillsSettings, {
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await wrapper.find('[data-testid="skills-browse-button"]').trigger('click')
    await flushPromises()
    expect(document.body.querySelector('[data-testid="skills-browse-dialog"]')).toBeTruthy()
    wrapper.unmount()
  })
})
