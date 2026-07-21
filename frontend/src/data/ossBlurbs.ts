/**
 * D3-FEAT-01: owner-curated one-line what/why per merged upstream PR,
 * keyed `owner/repo#number`. Lives in the frontend (not the DB) so a
 * blurb edit is a normal reviewed code change; the strip renders the
 * PR title alone when a blurb is missing, so an unsynced new PR
 * degrades gracefully.
 *
 * Register note: blurbs describe the upstream change on its own terms —
 * they never tie a contribution to employer work or internal tooling.
 */
export const OSS_BLURBS: Record<string, string> = {
  'DefectDojo/django-DefectDojo#15081':
    'Brings Promptfoo LLM eval and red-teaming findings into DefectDojo, so LLM security results live in the same vulnerability workflow as everything else.',
  'DefectDojo/django-DefectDojo#15013':
    "Parser for NVIDIA's Garak LLM vulnerability scanner — normalizes probe results into DefectDojo findings with deduplication.",
  'fo-dicom/fo-dicom#2149':
    'DICOM server reliability: per-connection service task exceptions were silently unobserved, hiding the real cause of dropped associations.',
  'fo-dicom/fo-dicom#2147':
    'Fixed RawPDU protocol logging crashing with a FormatException under .NET 8 enum formatting.',
  'fo-dicom/fo-dicom#2114':
    'Added a recursion depth guard to the DICOM parser — malformed nested sequences could previously drive unbounded recursion, a denial-of-service class.',
  'anchore/syft#4963':
    'SBOM completeness: opkg/ipkg package entries were missing their License field in generated SBOMs.',
  'anchore/grype#3396':
    'Made silently-insecure registry transport visible: Grype now warns when TLS verification is disabled for a registry.',
  'anchore/stereoscope#587':
    'The same guard one layer down: the container-image library logs when registry transport is configured insecurely.',
  'anchore/syft#4791':
    'Spec-correct CycloneDX output: distro qualifiers were leaking into package names, breaking downstream component matching.'
}
