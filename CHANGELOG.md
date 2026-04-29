# Changelog

All notable changes to **imageguard** are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versions follow
[SemVer](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-29

First working PoC. Image-domain sibling to `halluguard`: given a
packshot and an AI-generated render of the same product, return a
`Verdict` with a numerical match score and a stylist-actionable
suggestion (`PASS` / `WARN` / `REGENERATE`).

### Added
- `imageguard.VisualGuard`, the high-level entry point. Constructed
  with a packshot path; `check_render(render_path)` returns a
  `Verdict`. Never raises on a missing CLIP backbone or a corrupt
  image; populates `Verdict.error` instead.
- `imageguard.types.Verdict` with `overall_match`, `embedding_match`,
  `color_match`, `suggested_action`, and `reasoning`.
- CLIP-based global similarity via `sentence-transformers/clip-ViT-B-32`
  (gated behind the `[clip]` extra). Falls back to color-histogram-only
  scoring when the backbone is not installed.
- HSV color-histogram comparator with KL-divergence over the dominant
  five colors per image. Deterministic, no model required.
- Threshold-based action mapping. Defaults are conservative
  placeholders pending the calibration pass described in
  `docs/calibration.md`.

### Internals
- Pure-numpy + Pillow core, no `torch` dependency unless `[clip]` is
  installed.
- Unit tests cover the verdict shape, the color comparator, and the
  fallback path. The CLIP path is exercised via a mocked encoder.
- PyPI distribution name: `imageguard` (PoC release; the v0.4 PyPI
  release is gated on calibration data, see roadmap in README).

### Known limitations
- Whole-frame comparison; pose / background drift counts against the
  match score. v0.2 will add segmentation (SAM / CLIPSeg).
- No attribute parser; we cannot say "v-yaka oldu crew-yaka" yet, only
  that something globally drifted. v0.3 ships the parser.
- Caller must pre-pair the packshot with the render. v0.2 will add
  `from_catalog()` for auto-identification.

[0.1.0]: https://github.com/nakata-app/imageguard/releases/tag/v0.1.0
