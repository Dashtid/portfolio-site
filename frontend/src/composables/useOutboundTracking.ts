import analytics from '@/services/analytics'

/**
 * Outbound-click tracking (Campaign 2026-08 Sprint 3).
 *
 * Wires the site's conversion links — LinkedIn, GitHub, merged OSS PRs — into
 * the existing analytics pipeline so the owner can see click-through, not just
 * page views. `analytics.trackEvent` records a synthetic page view at
 * `/event/outbound/<destination>/<label>`, so these show up in the admin
 * analytics without any new backend endpoint.
 *
 * Fire-and-forget: the call never awaits, never throws into the handler, and
 * never blocks or prevents the navigation (all wired links are
 * target="_blank", so the current tab stays alive for the request to finish).
 * It also respects the analytics opt-out flag inside trackEvent.
 */
export function useOutboundTracking() {
  const trackOutbound = (destination: string, label: string | null = null): void => {
    void analytics.trackEvent('outbound', destination, label)
  }

  return { trackOutbound }
}
