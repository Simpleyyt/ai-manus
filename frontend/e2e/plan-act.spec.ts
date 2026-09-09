import { test, expect, type Page } from '@playwright/test'

// Browser-level e2e: a user opens the app, sends a task, and watches the
// PlanAct loop run end to end (real backend + sandbox, mockserver as LLM).
// Requires the dev stack: ./dev.sh up -d

const MOCKSERVER = process.env.MOCKSERVER_URL || 'http://localhost:8090'

async function setScenario (page: Page, file: string) {
  const response = await page.request.post(`${MOCKSERVER}/mock/scenario`, {
    data: { file }
  })
  expect(response.ok()).toBeTruthy()
}

async function sendMessage (page: Page, text: string) {
  const editor = page.locator('.chat-input-editor [contenteditable="true"]').first()
  await editor.click()
  await editor.pressSequentially(text)
  await editor.press('Enter')
}

test('user sends a task and sees the plan run to completion', async ({ page }) => {
  await setScenario(page, 'plan_act_e2e.yaml')
  await page.goto('/')

  await sendMessage(page, 'Run the e2e smoke')

  // Home navigates into the chat page for the new session.
  await page.waitForURL(/\/chat\//, { timeout: 30_000 })

  // The user's message and the plan's opening message render in the chat.
  await expect(page.getByText('Run the e2e smoke').first()).toBeVisible({ timeout: 30_000 })
  await expect(
    page.getByText('I will run a quick smoke command.').first()
  ).toBeVisible({ timeout: 60_000 })

  // The step from the scripted plan shows up in the timeline.
  await expect(page.getByText('Run the smoke command').first()).toBeVisible({ timeout: 60_000 })

  // Final assistant message from deliver_result, then the completed badge.
  await expect(page.getByText('E2E smoke finished').first()).toBeVisible({ timeout: 60_000 })
  await expect(page.getByText('Task completed').first()).toBeVisible({ timeout: 30_000 })

  await page.screenshot({ path: 'test-results/plan-act-smoke.png', fullPage: true })
})

test('ask_user pauses the session and a reply resumes it to done', async ({ page }) => {
  await setScenario(page, 'plan_act_wait_e2e.yaml')
  await page.goto('/')

  await sendMessage(page, 'Pick for me')
  await page.waitForURL(/\/chat\//, { timeout: 30_000 })

  // The agent's question surfaces in the chat and the session waits.
  await expect(
    page.getByText('Which option do you want, A or B?').first()
  ).toBeVisible({ timeout: 60_000 })

  await page.screenshot({ path: 'test-results/plan-act-waiting.png', fullPage: true })

  // Reply from the chat page input; the flow resumes and delivers.
  await sendMessage(page, 'Option B')
  await expect(
    page.getByText('Done with the chosen option').first()
  ).toBeVisible({ timeout: 60_000 })

  await page.screenshot({ path: 'test-results/plan-act-resumed.png', fullPage: true })
})
