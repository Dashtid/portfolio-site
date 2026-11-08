/**
 * The text of one baked page as the content checks in
 * verify-dist-invariants.mjs read it: the page itself, then every key and
 * string value of its JSON blocks, decoded.
 *
 * vite-ssg's serializeState writes the bake's store as a JSON string literal
 * whose content is JSON again, with <, > and / written as \u escapes, and the
 * onFinished hook in vite.config.ts keeps that literal verbatim as the
 * content of the state block. Each application/ld+json block is JSON once.
 * In the raw page a word inside either kind of block can sit against an
 * escape (`u002f` in front of a path segment, `n` after an escaped newline),
 * where a word match does not see it; in the decoded strings it stands alone.
 */

/** The state block as the onFinished hook in vite.config.ts writes it. */
export const STATE_BLOCK =
  /<script type="application\/json" id="__INITIAL_STATE__">(".*?")<\/script>/s

const LD_JSON_BLOCK = /<script type="application\/ld\+json">(.*?)<\/script>/gs

/** Every key and string value in a parsed JSON tree, depth first. */
export const jsonStrings = node => {
  if (typeof node === 'string') return [node]
  if (Array.isArray(node)) return node.flatMap(jsonStrings)
  if (node && typeof node === 'object') {
    return Object.entries(node).flatMap(([key, value]) => [key, ...jsonStrings(value)])
  }
  return []
}

/**
 * The texts to check for one baked page: the raw page first, then the
 * decoded strings of its state block and of each JSON-LD block. `state` says
 * whether a state block was decoded and `ldJson` how many JSON-LD blocks
 * were. Throws when the page carries the state block's id in another form,
 * or when a block does not parse.
 */
export const bakedTexts = html => {
  const texts = [html]
  const state = STATE_BLOCK.exec(html)
  if (!state && html.includes('id="__INITIAL_STATE__"')) {
    throw new Error('the __INITIAL_STATE__ block is not in the form vite.config.ts writes')
  }
  if (state) texts.push(...jsonStrings(JSON.parse(JSON.parse(state[1]))))
  let ldJson = 0
  for (const [, body] of html.matchAll(LD_JSON_BLOCK)) {
    texts.push(...jsonStrings(JSON.parse(body)))
    ldJson++
  }
  return { texts, state: state !== null, ldJson }
}
