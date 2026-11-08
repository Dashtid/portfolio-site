/** Types for hashedTerms.mjs. */
export declare const MAX_WORDS: number
export declare const EXCLUDED_REPO_DIGESTS: ReadonlySet<string>
export declare const OTHER_REPO_DIGESTS: ReadonlySet<string>
export declare function digest(term: string): string
export declare function candidates(text: string): Generator<string, void, undefined>
export declare function findTerms(text: string, digests: ReadonlySet<string>): string[]
