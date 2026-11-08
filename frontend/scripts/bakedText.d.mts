/** Types for bakedText.mjs. */
export declare const STATE_BLOCK: RegExp
export declare function jsonStrings(node: unknown): string[]
export declare function bakedTexts(html: string): {
  texts: string[]
  state: boolean
  ldJson: number
}
