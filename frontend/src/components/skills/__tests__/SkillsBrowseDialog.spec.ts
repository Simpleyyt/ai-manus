import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import SkillsBrowseDialog from '../SkillsBrowseDialog.vue'
import { i18n } from '../../../composables/useI18n'
import { resetSkillsStoreForTests, setSkillsStoreForTests } from '../../../composables/skillsStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: { template: '<div />' } }],
})

describe('SkillsBrowseDialog', () => {
  beforeEach(() => {
    resetSkillsStoreForTests()
    setSkillsStoreForTests({
      catalog: [
        {
          id: 'skill_market_research',
          name: 'market-research',
          description: 'Research markets',
          owner_type: 'official',
        },
        {
          id: 'skill_web_research',
          name: 'web-research',
          description: 'Web research',
          owner_type: 'official',
        },
      ],
      added: [
        {
          id: 'skill_market_research',
          name: 'market-research',
          description: 'Research markets',
          owner_type: 'official',
          enabled: true,
        },
      ],
    })
    document.body.innerHTML = ''
  })

  it('renders official skills in browse grid', async () => {
    const wrapper = mount(SkillsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n, router] },
      attachTo: document.body,
    })
    await flushPromises()
    const dialog = document.body.querySelector('[data-testid="skills-browse-dialog"]')
    expect(dialog).toBeTruthy()
    expect(dialog!.textContent).toContain('market-research')
    expect(dialog!.textContent).toContain('web-research')
    wrapper.unmount()
  })

  it('shows team empty state', async () => {
    const wrapper = mount(SkillsBrowseDialog, {
      props: { open: true },
      global: { plugins: [i18n, router] },
      attachTo: document.body,
    })
    await flushPromises()
    const teamTab = document.body.querySelector('[data-testid="skills-browse-tab-team"]') as HTMLElement
    teamTab.click()
    await flushPromises()
    const dialog = document.body.querySelector('[data-testid="skills-browse-dialog"]')
    expect(dialog!.textContent).toContain('No Team skills yet')
    wrapper.unmount()
  })
})
