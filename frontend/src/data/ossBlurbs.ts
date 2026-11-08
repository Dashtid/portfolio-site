/**
 * D3-FEAT-01: owner-curated one-line what/why per merged upstream PR,
 * keyed `owner/repo#number`. Lives in the frontend (not the DB) so a
 * blurb edit is a normal reviewed code change; the strip renders the
 * PR title alone when a blurb is missing, so an unsynced new PR
 * degrades gracefully.
 *
 * Each blurb describes the upstream change itself.
 */
export const OSS_BLURBS: Record<string, string> = {
  'Efferent-Health/fo-dicom.Codecs#190':
    'JPEG 2000 decoder hardening: a codestream claiming more samples than the declared pixel geometry could write past the destination buffer — now rejected before decoding.',
  'Efferent-Health/fo-dicom.Codecs#181':
    "Fixed a process crash in the JPEG decoder's error path: on malformed input it freed a caller-owned pixel buffer, corrupting the heap.",
  'DefectDojo/django-DefectDojo#15081':
    'Brings Promptfoo eval and red-teaming findings into DefectDojo, so they are triaged in the same vulnerability workflow as other scanner results.',
  'DefectDojo/django-DefectDojo#15013':
    "Parser for NVIDIA's Garak scanner: normalizes its probe results into DefectDojo findings with deduplication.",
  'fo-dicom/fo-dicom#2149':
    'DICOM server reliability: per-connection service task exceptions were silently unobserved, hiding the real cause of dropped associations.',
  'fo-dicom/fo-dicom#2147':
    'Fixed RawPDU protocol logging crashing with a FormatException under .NET 8 enum formatting.',
  'fo-dicom/fo-dicom#2114':
    'Added a recursion depth guard to the DICOM parser — malformed nested sequences could previously drive unbounded recursion, a denial-of-service class.',
  'anchore/syft#4963':
    'SBOM completeness: opkg/ipkg package entries were missing their License field in generated SBOMs.',
  'anchore/grype#3611':
    "Configuration fix: Grype's Rust matcher now honors the match.rust.using-cpes setting instead of silently ignoring it.",
  'anchore/grype#3396':
    'Made silently-insecure registry transport visible: Grype now warns when TLS verification is disabled for a registry.',
  'anchore/stereoscope#587':
    'The same guard one layer down: the container-image library logs when registry transport is configured insecurely.',
  'anchore/syft#4791':
    'Spec-correct CycloneDX output: distro qualifiers were leaking into package names, breaking downstream component matching.',
  'cartography-cncf/cartography#3088':
    "Trust conditions in the graph: a role trusted from one branch and a role open to a whole GitHub org no longer look the same in Cartography's AWS graph."
}
