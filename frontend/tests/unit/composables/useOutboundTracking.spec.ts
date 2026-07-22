import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useOutboundTracking } from '@/composables/useOutboundTracking'
import analytics from '@/services/analytics'

vi.mock('@/services/analytics', () => ({
  default: { trackEvent: vi.fn().mockResolvedValue(undefined) }
}))

describe('useOutboundTracking', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('records an outbound event with destination + label', () => {
    const { trackOutbound } = useOutboundTracking()
    trackOutbound('linkedin', 'hero')
    expect(analytics.trackEvent).toHaveBeenCalledWith('outbound', 'linkedin', 'hero')
  })

  it('defaults the label to null when omitted', () => {
    const { trackOutbound } = useOutboundTracking()
    trackOutbound('github')
    expect(analytics.trackEvent).toHaveBeenCalledWith('outbound', 'github', null)
  })

  it('does not throw when the underlying tracker rejects', () => {
    vi.mocked(analytics.trackEvent).mockRejectedValueOnce(new Error('network'))
    const { trackOutbound } = useOutboundTracking()
    expect(() => trackOutbound('oss', 'anchore/syft')).not.toThrow()
  })
})
