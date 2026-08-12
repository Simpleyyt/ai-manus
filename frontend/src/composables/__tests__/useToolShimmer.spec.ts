import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { TOOL_SHIMMER_MIN_MS, useToolShimmer } from '../useToolShimmer'

describe('useToolShimmer', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows shimmer while calling', async () => {
    const status = ref<'calling' | 'called'>('calling')
    const { showShimmer } = useToolShimmer(status)
    expect(showShimmer.value).toBe(true)
  })

  it('holds shimmer after a fast calling→called so it does not flash away', async () => {
    const status = ref<'calling' | 'called'>('calling')
    const { showShimmer } = useToolShimmer(status)
    status.value = 'called'
    await nextTick()
    expect(showShimmer.value).toBe(true)

    vi.advanceTimersByTime(TOOL_SHIMMER_MIN_MS - 50)
    expect(showShimmer.value).toBe(true)

    vi.advanceTimersByTime(100)
    expect(showShimmer.value).toBe(false)
  })

  it('keeps shimmer while active even after called hold ends', async () => {
    const status = ref<'calling' | 'called'>('calling')
    const active = ref(true)
    const { showShimmer } = useToolShimmer(status, active)
    status.value = 'called'
    await nextTick()
    vi.advanceTimersByTime(TOOL_SHIMMER_MIN_MS + 50)
    expect(showShimmer.value).toBe(true)
    active.value = false
    await nextTick()
    expect(showShimmer.value).toBe(false)
  })

  it('does not shimmer for already-called history rows', async () => {
    const status = ref<'calling' | 'called'>('called')
    const { showShimmer } = useToolShimmer(status)
    expect(showShimmer.value).toBe(false)
    vi.advanceTimersByTime(TOOL_SHIMMER_MIN_MS + 50)
    expect(showShimmer.value).toBe(false)
  })
})
