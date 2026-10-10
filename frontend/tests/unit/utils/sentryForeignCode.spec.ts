/**
 * The foreign-code beforeSend, pinned against what the SDK really builds.
 *
 * Every stack below is a RAW string as an engine prints it, turned into
 * exception values by the SDK's own exceptionFromError and defaultStackParser
 * (re-exported by @sentry/vue; nothing in this file is mocked). Hand-written,
 * already-parsed frames would only test what the author believed the parser
 * produces, and that belief was wrong once: the 2026-10-06 frames read like
 * code at `<anonymous>:311:30`, but they are V8 eval-origin frames whose
 * position is the eval call site and whose filename the parser back-fills.
 * An SDK bump that changes any of this fails here, not in production.
 *
 * The site's origin is window.location.origin (happy-dom's page here), the
 * same value the hook reads in production.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defaultStackParser, exceptionFromError } from '@sentry/vue'
import type { ErrorEvent as SentryErrorEvent, Exception } from '@sentry/vue'
import { dropForeignCodeErrors } from '@/utils/sentryForeignCode'

const ORIGIN = window.location.origin
const APP_CHUNK = `${ORIGIN}/assets/js/app-BMZj1I51.js`
const DETAIL_CHUNK = `${ORIGIN}/assets/js/ExperienceDetail-CtzzXvFK.js`
const CHROME_EXT = 'chrome-extension://abcdefghijklmnopabcdefghijklmnop/content.js'
const SAFARI_EXT = 'safari-web-extension://A1B2C3D4-E5F6-7890-ABCD-EF1234567890/content.js'
const FIREFOX_EXT = 'moz-extension://2c7e9a1b-4d5f-4e6a-8b7c-9d0e1f2a3b4c/content.js'

const CSP_EVAL_MESSAGE =
  'Evaluating a string as JavaScript violates the following Content Security Policy ' +
  "directive because 'unsafe-eval' is not an allowed source of script: \"script-src 'self'\"."

/** The three lines of the 2026-10-06 event as V8 prints them, newest first. */
const EMAIL_FRAMES = [
  'eval (<anonymous>)',
  'predicate (eval at evaluate (:311:30), <anonymous>:4:60)',
  'next (eval at evaluate (:311:30), <anonymous>:29:33)'
]

/** V8: a `Name: message` header, then one `    at ...` line per frame. */
function v8(name: string, message: string, frames: string[]): string {
  return [`${name}: ${message}`, ...frames.map(frame => `    at ${frame}`)].join('\n')
}

/** An Error carrying exactly the raw stack string an engine gave it. */
function errorWith(name: string, message: string, stack: string): Error {
  const error = new Error(message)
  error.name = name
  Object.defineProperty(error, 'stack', { value: stack, configurable: true })
  return error
}

/**
 * The event the SDK hands beforeSend: one exception value per error, built by
 * the SDK's own builder. linkedErrors lists causes first, so pass them first.
 */
function eventOf(...errors: Error[]): SentryErrorEvent {
  return {
    type: undefined,
    exception: { values: errors.map(error => exceptionFromError(defaultStackParser, error)) }
  }
}

/** [function, filename, lineno, colno] per parsed frame, oldest first as the SDK orders them. */
function framesOf(event: SentryErrorEvent, value = 0): unknown[][] {
  const frames = event.exception?.values?.[value]?.stacktrace?.frames ?? []
  return frames.map(f => [f.function, f.filename, f.lineno, f.colno])
}

describe('dropForeignCodeErrors', () => {
  beforeEach(() => {
    // The DEV-only drop log; production compiles it away.
    vi.spyOn(console, 'debug').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('runs against a real http(s) origin', () => {
    expect(ORIGIN).toMatch(/^https?:\/\//)
  })

  describe('drops errors raised only by code the site never shipped', () => {
    it('the 2026-10-06 event: the blocked eval builtin over two eval-origin frames', () => {
      const event = eventOf(
        errorWith('EvalError', CSP_EVAL_MESSAGE, v8('EvalError', CSP_EVAL_MESSAGE, EMAIL_FRAMES))
      )

      // Exactly the frames the alert showed: the parser keeps the eval call
      // site (311:30) and back-fills '<anonymous>' from the newest frame.
      expect(framesOf(event)).toEqual([
        ['next', '<anonymous>', 311, 30],
        ['predicate', '<anonymous>', 311, 30],
        ['eval', '<anonymous>', undefined, undefined]
      ])
      expect(dropForeignCodeErrors(event)).toBeNull()
    })

    it('eval-origin code that throws by itself: no builtin on top, so an EMPTY filename', () => {
      const message = "Cannot read properties of null (reading 'textContent')"
      const event = eventOf(
        errorWith(
          'TypeError',
          message,
          v8('TypeError', message, ['check (eval at evaluate (:311:30), <anonymous>:3:41)'])
        )
      )

      expect(framesOf(event)).toEqual([['check', '', 311, 30]])
      expect(dropForeignCodeErrors(event)).toBeNull()
    })

    it('a nested eval origin (a function predicate cached through a second eval)', () => {
      const message = "Cannot read properties of null (reading 'textContent')"
      const event = eventOf(
        errorWith(
          'TypeError',
          message,
          v8('TypeError', message, [
            'eval (eval at predicate (eval at evaluate (:311:30)), <anonymous>:1:44)',
            'predicate (eval at evaluate (:311:30), <anonymous>:8:24)',
            'next (eval at evaluate (:311:30), <anonymous>:24:33)'
          ])
        )
      )

      expect(dropForeignCodeErrors(event)).toBeNull()
    })

    it('eval-origin code failing inside a builtin', () => {
      const message = 'Unexpected token u in JSON at position 0'
      const event = eventOf(
        errorWith(
          'SyntaxError',
          message,
          v8('SyntaxError', message, [
            'JSON.parse (<anonymous>)',
            'read (eval at evaluate (:311:30), <anonymous>:2:17)'
          ])
        )
      )

      expect(dropForeignCodeErrors(event)).toBeNull()
    })

    it('DevTools console input', () => {
      const event = eventOf(
        errorWith(
          'TypeError',
          'x is not a function',
          v8('TypeError', 'x is not a function', ['<anonymous>:1:7'])
        )
      )

      expect(dropForeignCodeErrors(event)).toBeNull()
    })

    it('extension stacks in V8, JavaScriptCore and Gecko form', () => {
      const chrome = eventOf(
        errorWith(
          'TypeError',
          'x is not a function',
          v8('TypeError', 'x is not a function', [
            `inject (${CHROME_EXT}:1:2)`,
            `run (${CHROME_EXT}:5:6)`
          ])
        )
      )
      // Safari and Firefox print no header line, one `fn@url:line:col` per frame.
      const safari = eventOf(
        errorWith(
          'TypeError',
          'x is not a function',
          `inject@${SAFARI_EXT}:1:2\nrun@${SAFARI_EXT}:5:6`
        )
      )
      const firefox = eventOf(
        errorWith(
          'TypeError',
          'x is not a function',
          `inject@${FIREFOX_EXT}:1:2\nrun@${FIREFOX_EXT}:5:6\n`
        )
      )

      for (const event of [chrome, safari, firefox]) {
        expect(framesOf(event)).toHaveLength(2)
        expect(dropForeignCodeErrors(event)).toBeNull()
      }
    })

    it('code from another origin', () => {
      const other = 'https://cdn.other.example/injected.js'
      const event = eventOf(
        errorWith(
          'TypeError',
          'x is not a function',
          v8('TypeError', 'x is not a function', [`inject (${other}:1:2)`])
        )
      )

      expect(dropForeignCodeErrors(event)).toBeNull()
    })

    it('scripts named only by their own sourceURL: init scripts loaded by path, Lighthouse', () => {
      // Playwright's addInitScript({ path }) appends `//# sourceURL=<path as
      // given>`, with no scheme, and V8 prints that name in every frame.
      const message = "Cannot read properties of null (reading 'click')"
      const relative = eventOf(
        errorWith(
          'TypeError',
          message,
          v8('TypeError', message, ['onClick (stealth.min.js:2:100)'])
        )
      )
      const absolute = eventOf(
        errorWith(
          'TypeError',
          message,
          v8('TypeError', message, ['autoAccept (/home/bot/autoaccept.js:2:83)'])
        )
      )
      const lighthouse = eventOf(
        errorWith(
          'TypeError',
          message,
          v8('TypeError', message, ['audit (_lighthouse-eval.js:3:15)'])
        )
      )

      expect(framesOf(relative)).toEqual([['onClick', 'stealth.min.js', 2, 100]])
      expect(framesOf(absolute)).toEqual([['autoAccept', '/home/bot/autoaccept.js', 2, 83]])
      expect(dropForeignCodeErrors(relative)).toBeNull()
      expect(dropForeignCodeErrors(absolute)).toBeNull()
      expect(dropForeignCodeErrors(lighthouse)).toBeNull()
    })
  })

  describe('keeps every error whose parsed stack has a frame from this origin', () => {
    it('a genuine V8 stack from the site chunks, builtins included, untagged', () => {
      const message = "Cannot read properties of undefined (reading 'name')"
      const event = eventOf(
        errorWith(
          'TypeError',
          message,
          v8('TypeError', message, [
            `Proxy.onSelect (${DETAIL_CHUNK}:1:4821)`,
            `Ii (${APP_CHUNK}:1:16540)`,
            'Array.forEach (<anonymous>)',
            `HTMLButtonElement.n (${APP_CHUNK}:1:52977)`
          ])
        )
      )

      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toBeUndefined()
    })

    it('a genuine Gecko stack from the site chunks, untagged', () => {
      const event = eventOf(
        errorWith(
          'TypeError',
          'e.detail is undefined',
          `onSelect@${DETAIL_CHUNK}:1:4821\nIi@${APP_CHUNK}:1:16540\n`
        )
      )

      expect(framesOf(event)).toHaveLength(2)
      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toBeUndefined()
    })

    it('site code calling eval under the CSP: the one CSP bug worth seeing', () => {
      const event = eventOf(
        errorWith(
          'EvalError',
          CSP_EVAL_MESSAGE,
          v8('EvalError', CSP_EVAL_MESSAGE, ['eval (<anonymous>)', `Xy (${APP_CHUNK}:1:2345)`])
        )
      )

      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toBeUndefined()
    })

    it('the inline hashed theme script, whose frame carries the page URL', () => {
      const message = "Cannot read properties of null (reading 'classList')"
      const event = eventOf(
        errorWith('TypeError', message, v8('TypeError', message, [`${ORIGIN}/:93:41`]))
      )

      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toBeUndefined()
    })

    it('the 2026-10-06 stack over a frame from this origin: kept, tagged mixed', () => {
      // The same bot's error when its poll runs through a timer the SDK has
      // wrapped: the minified wrapper `r` sits at the bottom, from the Sentry
      // chunk on this origin. One own frame, so the filter has to keep it,
      // which is why sentry.ts turns the SDK's callback wrapping off.
      const event = eventOf(
        errorWith(
          'EvalError',
          CSP_EVAL_MESSAGE,
          v8('EvalError', CSP_EVAL_MESSAGE, [
            ...EMAIL_FRAMES,
            `r (${ORIGIN}/assets/js/esm-x.js:2:1)`
          ])
        )
      )

      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toEqual({ foreign_code: 'mixed' })
    })

    it('an extension frame above a site frame: kept, tagged mixed', () => {
      const event = eventOf(
        errorWith(
          'TypeError',
          'x is not a function',
          v8('TypeError', 'x is not a function', [
            `patched (${CHROME_EXT}:1:2)`,
            `render (${APP_CHUNK}:1:2)`
          ])
        )
      )

      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toEqual({ foreign_code: 'mixed' })
    })

    it('an init script named by its sourceURL above a site frame: kept, tagged mixed', () => {
      const event = eventOf(
        errorWith(
          'TypeError',
          'x is not a function',
          v8('TypeError', 'x is not a function', [
            'patched (stealth.min.js:2:100)',
            `render (${APP_CHUNK}:1:2)`
          ])
        )
      )

      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toEqual({ foreign_code: 'mixed' })
    })

    it('a genuine async stack through Promise.all: the `(index 0)` frame is no evidence', () => {
      const message = "Cannot read properties of undefined (reading 'id')"
      const event = eventOf(
        errorWith(
          'TypeError',
          message,
          v8('TypeError', message, [
            `Ab (${APP_CHUNK}:1:777)`,
            'async Promise.all (index 0)',
            `async loadAll (${DETAIL_CHUNK}:1:3000)`
          ])
        )
      )

      // V8's label for the combinator parses as a scheme-less name with no
      // position. With one, it would count as foreign and tag this mixed.
      expect(framesOf(event)).toContainEqual(['async Promise.all', 'index 0', undefined, undefined])
      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toBeUndefined()
    })

    it('a foreign wrapper whose chained cause is a site error', () => {
      const cause = errorWith(
        'TypeError',
        'the cause',
        v8('TypeError', 'the cause', [`loadCompany (${DETAIL_CHUNK}:3:210)`])
      )
      const wrapper = errorWith(
        'Error',
        'the wrapper',
        v8('Error', 'the wrapper', ['predicate (eval at evaluate (:311:30), <anonymous>:4:60)'])
      )
      const event = eventOf(cause, wrapper)

      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toEqual({ foreign_code: 'mixed' })
    })

    it('a multi-line message listing API URLs, over frames from this origin', () => {
      const message =
        'Failed to load:\n' +
        'GET https://api.dashti.se/api/v1/companies/1\n' +
        'GET https://api.dashti.se/api/v1/companies/2'
      const event = eventOf(
        errorWith(
          'Error',
          message,
          v8('Error', message, [
            `Ab (${APP_CHUNK}:1:777)`,
            `async loadAll (${DETAIL_CHUNK}:1:3000)`
          ])
        )
      )

      expect(dropForeignCodeErrors(event)).toBe(event)
      // Known artefact: V8 prints the message above the frames and a line that
      // ends in a URL parses as a frame, from another origin. The event is
      // kept; only the tag is wrong. (Enough such lines to use up the SDK's
      // 50-frame budget would hide the real frames: a documented residual.)
      expect(event.tags).toEqual({ foreign_code: 'mixed' })
    })
  })

  describe('keeps what carries no evidence either way', () => {
    it('a JavaScriptCore stack of injected code (documented residual: noise kept)', () => {
      // WebKit prints URL-less code as a bare `fn@`, which does not parse into
      // a frame; only the builtin survives, and a builtin proves nothing.
      const message =
        "Refused to evaluate a string as JavaScript because 'unsafe-eval' is not an allowed source of script"
      const event = eventOf(
        errorWith('EvalError', message, 'eval@[native code]\npredicate@\nnext@')
      )

      expect(framesOf(event)).toEqual([['eval', '[native code]', undefined, undefined]])
      expect(dropForeignCodeErrors(event)).toBe(event)
      expect(event.tags).toBeUndefined()
    })

    it('blob: and data: scripts alone; with a foreign frame the foreign frame decides', () => {
      const blob = `blob:${ORIGIN}/0f3c4a1b-0000-4000-8000-000000000000`
      const blobOnly = eventOf(
        errorWith('Error', 'boom', v8('Error', 'boom', [`work (${blob}:1:2)`]))
      )
      const dataOnly = eventOf(
        errorWith(
          'Error',
          'boom',
          v8('Error', 'boom', ['inline (data:text/javascript,boom():1:2)'])
        )
      )
      const blobAndInjected = eventOf(
        errorWith('Error', 'boom', v8('Error', 'boom', [`work (${blob}:1:2)`, '<anonymous>:1:7']))
      )

      expect(dropForeignCodeErrors(blobOnly)).toBe(blobOnly)
      expect(dropForeignCodeErrors(dataOnly)).toBe(dataOnly)
      expect(dropForeignCodeErrors(blobAndInjected)).toBeNull()
    })

    it('errors with no frames at all', () => {
      // Safari's network failures, and a stale route chunk, carry no frames.
      const loadFailed = eventOf(errorWith('TypeError', 'Load failed', ''))
      const staleChunk = eventOf(
        errorWith(
          'TypeError',
          'Failed to fetch dynamically imported module',
          'TypeError: Failed to fetch dynamically imported module'
        )
      )

      expect(loadFailed.exception?.values?.[0]?.stacktrace).toBeUndefined()
      expect(dropForeignCodeErrors(loadFailed)).toBe(loadFailed)
      expect(dropForeignCodeErrors(staleChunk)).toBe(staleChunk)
    })

    it('a non-Error rejection and a captureMessage event', () => {
      // What globalHandlers builds for `Promise.reject('cancelled')`: no stacktrace.
      const rejection: SentryErrorEvent = {
        type: undefined,
        exception: {
          values: [
            {
              type: 'UnhandledRejection',
              value: 'Non-Error promise rejection captured with value: cancelled'
            } satisfies Exception
          ]
        }
      }
      const message: SentryErrorEvent = { type: undefined, message: 'hello', level: 'info' }

      expect(dropForeignCodeErrors(rejection)).toBe(rejection)
      expect(dropForeignCodeErrors(message)).toBe(message)
    })
  })

  describe('fails open', () => {
    it('returns the same event object when something inside the hook throws', () => {
      const event = {
        type: undefined,
        exception: {
          get values(): Exception[] {
            throw new Error('a getter that throws')
          }
        }
      } as SentryErrorEvent

      expect(dropForeignCodeErrors(event)).toBe(event)
    })

    it('returns the event unchanged when there is no http(s) origin to compare with', () => {
      const opaque = eventOf(
        errorWith('EvalError', CSP_EVAL_MESSAGE, v8('EvalError', CSP_EVAL_MESSAGE, EMAIL_FRAMES))
      )
      const missing = eventOf(
        errorWith('EvalError', CSP_EVAL_MESSAGE, v8('EvalError', CSP_EVAL_MESSAGE, EMAIL_FRAMES))
      )
      const noWindow = eventOf(
        errorWith('EvalError', CSP_EVAL_MESSAGE, v8('EvalError', CSP_EVAL_MESSAGE, EMAIL_FRAMES))
      )

      // A page saved to disk or a sandboxed frame reports the opaque origin 'null'.
      vi.stubGlobal('window', { location: { origin: 'null' } })
      expect(dropForeignCodeErrors(opaque)).toBe(opaque)
      vi.stubGlobal('window', { location: {} })
      expect(dropForeignCodeErrors(missing)).toBe(missing)
      // The prerender pass in Node has no window at all.
      vi.stubGlobal('window', undefined)
      expect(dropForeignCodeErrors(noWindow)).toBe(noWindow)

      for (const event of [opaque, missing, noWindow]) expect(event.tags).toBeUndefined()
    })
  })
})
