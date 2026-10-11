/**
 * Sentry `beforeSend` hook: drop errors raised only by code this site never
 * shipped (browser automation, extensions, userscripts).
 *
 * [!] loadSentry() in ./sentry.ts loads this file as a small lazy chunk of
 * its own, requested together with the SDK chunk. Never import it
 * statically: that would put it in the eager app chunk every page downloads
 * before first paint, for code that only runs once Sentry itself has loaded.
 *
 * The trap. script-src is hash-locked ('self' plus two sha256 hashes, no
 * 'unsafe-eval'), so every eval or `new Function` that automation, an
 * extension or a userscript runs in the page's main world throws an
 * EvalError in THAT code. When it lands as an unhandled rejection, Sentry's
 * globalHandlers integration reports it as this site's error (level error,
 * handled: no) and the default alert rule mails it out as a new
 * high-priority issue. The 2026-10-06 event was exactly this: Chromium's CSP
 * eval message, frames `eval` <- `predicate` <- `next`, and not one frame
 * from this origin. V8 prints a function created by an eval inside a script
 * that has no URL (one compiled over the DevTools protocol, for instance) as
 * an eval-origin frame: `predicate (eval at evaluate (:311:30),
 * <anonymous>:4:60)`. Sentry's parser keeps only the eval call site (311:30)
 * as the position, with an EMPTY filename, then back-fills the filename from
 * the newest frame, here the blocked `eval (<anonymous>)` builtin. That is
 * where the alert's `<anonymous>:311:30` came from. The stack matches the
 * shape of Playwright's waitForFunction poll.
 *
 * The rule, per frame, across every exception value (chained causes too):
 *
 * - OWN: the filename starts with this origin plus '/'. Chunks are
 *   /assets/js/<name>-<hash>.js; the inline hashed theme script, and the
 *   frame the SDK adds to a stackless window.onerror event, carry the page
 *   URL.
 * - FOREIGN: an empty or `<anonymous>` filename WITH a line or column. That
 *   is code with no script URL (eval-origin frames, DevTools and automation
 *   input), which nothing the site ships can produce under this CSP. Also
 *   FOREIGN: any other origin or scheme (chrome-extension://,
 *   moz-extension://, safari-web-extension://, https://other.host/...),
 *   which this CSP only lets run when something injected it. And FOREIGN: a
 *   scheme-less name WITH a line or column, i.e. a script named only by its
 *   own `//# sourceURL=` comment. Playwright's addInitScript({ path }) (and
 *   playwright-python's add_init_script(path=...)) names injected files that
 *   way, `stealth.min.js` or `/home/bot/autoaccept.js`, and Lighthouse names
 *   its page code `_lighthouse-eval.js`. Nothing this site serves carries a
 *   sourceURL.
 * - NO EVIDENCE: `[native code]`; an empty or `<anonymous>` filename with no
 *   position (V8 builtins such as `at Array.forEach (<anonymous>)`, which sit
 *   inside perfectly genuine stacks); blob:; `<data:...>`; scheme-less names
 *   with no position (V8's `at async Promise.all (index 0)`).
 *
 * An event is dropped only when it has at least one FOREIGN frame and no OWN
 * frame. Everything else is kept: events with no frames at all (non-Error
 * rejections, network TypeErrors with an empty stack; since SDK 11 a
 * captureMessage carries its call site's stack instead), native-only
 * stacks, and mixed stacks. Mixed stacks get the tag
 * foreign_code=mixed, so an extension wrapping site code stays visible and
 * searchable. In short, the hook keeps every error whose SDK-parsed stack
 * contains a frame from this origin.
 *
 * [!] That guarantee is only as good as the filenames. rewriteFramesIntegration,
 * or any integration that rewrites frame filenames before beforeSend, would
 * make this rule drop EVERY stack-bearing error unless ownOriginPrefix() is
 * changed to match. The reverse holds too: anything that puts a frame from
 * this origin under foreign code makes a bot's error look like ours. The
 * SDK's callback wrapping (timers, animation frames, XHR callbacks, event
 * listeners) did exactly that, which is why loadSentry() turns it off. The
 * SDK's fetch, XMLHttpRequest and History instrumentation does it too, and
 * stays on because breadcrumbs and tracing need it: see the residuals.
 *
 * Known residuals. Kept although foreign (noise that still reaches Sentry):
 * - JavaScriptCore stacks, where URL-less code prints as a bare `fn@` line
 *   that does not parse into a frame, so only `eval@[native code]` survives;
 *   Gecko `debugger eval code` lines, which do not parse either.
 * - Foreign calls to fetch(), XMLHttpRequest open() or send() (or an
 *   onreadystatechange set before open()) and history.pushState() or
 *   replaceState(). They run through the SDK's wrappers in the Sentry chunk,
 *   on this origin, so an error raised there carries a frame of ours and is
 *   kept, tagged mixed. When that frame is the newest one, the parser also
 *   back-fills its URL into the foreign frames' empty filenames, and the
 *   event looks wholly ours.
 * - Non-Error values thrown or rejected by foreign code. Once Sentry is up, a
 *   thrown one gets a single frame the SDK builds from the error event's URL,
 *   which for code with no script URL is the page's own, and a rejected one
 *   has no frames at all. During the idle window, sentry.ts's buffer wraps
 *   either kind in an Error created in the app chunk, which looks like ours.
 * - The SDK's other wrappers on this origin: its FunctionToString patch of
 *   Function.prototype.toString and its breadcrumb hooks on
 *   addEventListener/removeEventListener. Foreign code that errors inside one
 *   of them carries a Sentry-chunk frame, so it is kept, mixed or untagged.
 * - A multi-line foreign message containing a line that parses as a frame
 *   from this origin (an own URL with a line number): it counts as ours.
 * - A V8 frame whose function name has an unbalanced '(' (a string-keyed or
 *   defineProperty name): the parser splits it into a scheme-less filename,
 *   which counts as foreign, so the event is tagged mixed, or dropped if that
 *   was its only own frame. Nothing this site ships produces such a name.
 *
 * Dropped although the site was involved:
 * - a foreign wrapper that catches a site error and rethrows a NEW error
 *   without `cause` (the site frames never reach the event);
 * - a multi-line message with enough lines that parse as frames from
 *   elsewhere (a URL, or a path with a line number) to use up the SDK's
 *   50-frame parse budget before the real frames. V8 prints the message
 *   above the frames; a few such lines only add a false foreign_code=mixed
 *   tag;
 * - an event raised while this module's chunk is still pending, if the page
 *   is closed, reloaded or left before the chunk settles or the 5 s wait
 *   ends, or if it is one of a burst that overflows the SDK's buffers
 *   meanwhile (sentry.ts, deferredForeignCodeFilter). Lost, not filtered.
 *
 * Fail-open: no http(s) origin to compare against (prerender, opaque origin)
 * and any exception inside the hook both return the event unchanged. A hook
 * that throws would cost the event instead: SDK 11 drops it and records only
 * a `callback_error` client discard.
 * A chunk that fails to load is fail-open too, and so is one that is slow:
 * loadSentry() never waits for it, and an event raised before it arrives is
 * held at most 5 s, then sent unfiltered (unless the page exits first; see
 * above). beforeSend sees only error and message events;
 * traces never pass here. Drops are counted client-side and show on Sentry's
 * Stats page as "Client Discard: Before Send".
 *
 * Why not Sentry's thirdPartyErrorFilterIntegration: it does this job with
 * bundler-injected module metadata, which needs @sentry/vite-plugin in every
 * production build (vite.config.ts only adds it when SENTRY_AUTH_TOKEN is
 * set), and a chunk without that metadata makes every error with a stack
 * "third party". The origin check needs no build step.
 */

import type { ErrorEvent as SentryErrorEvent, StackFrame } from '@sentry/vue'

type FrameOrigin = 'own' | 'foreign' | 'unknown'

/** V8's filename for code with no script URL, also back-filled into eval-origin frames. */
const ANONYMOUS_SCRIPT = '<anonymous>'
/** JavaScriptCore's filename for builtin frames. Says nothing about who called the builtin. */
const NATIVE_CODE = '[native code]'
/** A URL scheme prefix: chrome-extension://, moz-extension://, safari-web-extension:, https:// ... */
const HAS_SCHEME = /^[a-z][a-z0-9+.-]*:/i

function classifyFrame(frame: StackFrame, ownPrefix: string): FrameOrigin {
  const file = frame.filename || frame.abs_path || ''
  const positioned = frame.lineno != null || frame.colno != null
  if (file === '' || file === ANONYMOUS_SCRIPT) {
    // Positioned: code with no script URL, i.e. injected. Unpositioned: a builtin.
    return positioned ? 'foreign' : 'unknown'
  }
  if (file === NATIVE_CODE) return 'unknown'
  if (file.startsWith(ownPrefix)) return 'own'
  // blob: carries the page origin whoever called createObjectURL, and
  // <data:...> is how the SDK names data-URI scripts. Neither says who wrote the code.
  if (file.startsWith('blob:') || file.startsWith('<')) return 'unknown'
  // Another origin or scheme; or, with a position, a script named only by its
  // own `//# sourceURL=` (stealth.min.js, /home/bot/x.js), which nothing this
  // site serves carries. Unpositioned scheme-less names are V8 labels such as
  // `Promise.all (index 0)`.
  return HAS_SCHEME.test(file) || positioned ? 'foreign' : 'unknown'
}

/** `https://dashti.se/` in production; null wherever there is no http(s) origin to compare with. */
function ownOriginPrefix(): string | null {
  if (typeof window === 'undefined') return null
  const origin = window.location.origin
  return /^https?:\/\//.test(origin) ? `${origin}/` : null
}

export function dropForeignCodeErrors(event: SentryErrorEvent): SentryErrorEvent | null {
  try {
    const ownPrefix = ownOriginPrefix()
    if (!ownPrefix) return event

    let own = 0
    let foreign = 0
    for (const exception of event.exception?.values ?? []) {
      for (const frame of exception.stacktrace?.frames ?? []) {
        const origin = classifyFrame(frame, ownPrefix)
        if (origin === 'own') own++
        else if (origin === 'foreign') foreign++
      }
    }

    if (foreign === 0) return event
    if (own > 0) {
      event.tags = { ...event.tags, foreign_code: 'mixed' }
      return event
    }
    if (import.meta.env.DEV) {
      console.debug('[Sentry] dropped an error raised only by foreign code', event)
    }
    return null
  } catch {
    // Fail open: a bug in this filter must never cost a real error report.
    return event
  }
}
