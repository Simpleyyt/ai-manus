import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import SkillsPlaceholderDialog from '../SkillsPlaceholderDialog.vue'
import { i18n } from '../../../composables/useI18n'
import { resetSkillsStoreForTests, setSkillsStoreForTests } from '../../../composables/skillsStore'

vi.mock('@/api/skills', () => ({
  fetchSkillsState: vi.fn(),
  addSkills: vi.fn(),
  setSkillEnabled: vi.fn(),
  importSkillFromGitHub: vi.fn(),
  importSkillFromUpload: vi.fn(),
}))

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: { template: '<div />' } }],
})

const mountDialog = (variant: 'github' | 'official' | 'upload' | 'build') =>
  mount(SkillsPlaceholderDialog, {
    props: { variant, open: true },
    global: { plugins: [i18n, router] },
    attachTo: document.body,
  })

describe('SkillsPlaceholderDialog github', () => {
  beforeEach(() => {
    resetSkillsStoreForTests()
    setSkillsStoreForTests({ catalog: [], added: [] })
    document.body.innerHTML = ''
  })

  it('renders Import from GitHub shell with URL field', async () => {
    const wrapper = mountDialog('github')
    await flushPromises()
    const root = document.body.querySelector('[data-testid="skills-placeholder-dialog"]')
    expect(root!.textContent).toContain('Import from GitHub')
    expect(root!.querySelector('[data-testid="skills-github-url-input"]')).toBeTruthy()
    wrapper.unmount()
  })

  it('imports skill from GitHub URL via API', async () => {
    const api = await import('@/api/skills')
    vi.mocked(api.importSkillFromGitHub).mockResolvedValue({
      id: 'skill_github_demo-skill',
      name: 'demo-skill',
      description: 'Imported',
      owner_type: 'personal',
      enabled: true,
    })
    vi.mocked(api.fetchSkillsState).mockResolvedValue({
      catalog: [],
      added: [{
        id: 'skill_github_demo-skill',
        name: 'demo-skill',
        description: 'Imported',
        owner_type: 'personal',
        enabled: true,
      }],
    })
    const wrapper = mountDialog('github')
    await flushPromises()
    const input = document.body.querySelector('[data-testid="skills-github-url-input"]') as HTMLInputElement
    input.value = 'https://github.com/acme/demo-skill'
    await input.dispatchEvent(new Event('input'))
    const button = document.body.querySelector('[data-testid="skills-github-import-button"]') as HTMLButtonElement
    button.click()
    await flushPromises()
    expect(api.importSkillFromGitHub).toHaveBeenCalledWith('https://github.com/acme/demo-skill')
    wrapper.unmount()
  })
})

describe('SkillsPlaceholderDialog official', () => {
  beforeEach(() => {
    resetSkillsStoreForTests()
    setSkillsStoreForTests({
      catalog: [
        {
          id: 'skill_summarize',
          name: 'summarize',
          description: 'Summarize docs',
          owner_type: 'official',
        },
      ],
      added: [],
    })
    document.body.innerHTML = ''
  })

  it('renders official library shell with selectable rows', async () => {
    const wrapper = mountDialog('official')
    await flushPromises()
    const root = document.body.querySelector('[data-testid="skills-placeholder-dialog"]')
    expect(root!.textContent).toContain('Official library')
    expect(root!.querySelectorAll('[data-testid="skills-official-row"]').length).toBeGreaterThan(0)
    wrapper.unmount()
  })
})
