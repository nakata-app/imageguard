# Security policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security-sensitive
findings. Instead, email the maintainer at
**hey@nakata.app** with:

- A description of the issue.
- Steps to reproduce (a minimal repro is enough).
- The version / commit you tested against.
- Optionally, your proposed fix.

We aim to acknowledge a report within 72 hours and to ship a fix in
the next minor release where applicable.

## Scope

The Python package itself is the in-scope surface: `VisualGuard`, the
`Verdict` shape, and the embedding / color-histogram comparators in
`imageguard.visual_guard`.

Out of scope:
- Bugs in `Pillow`, `numpy`, `sentence-transformers`, or `torch`.
  Report those upstream.
- Bugs in the CLIP model weights themselves (`clip-ViT-B-32`).
  Report those to the model authors.
- Performance issues without a security impact (file regular issues
  instead).

## Threat model

imageguard reads two image files from the caller, computes embeddings
and color histograms locally, and returns a verdict. It does not bind
network sockets and does not execute remote payloads. The CLIP model
download (first run) is the only outbound call; it goes to Hugging
Face Hub and is gated by `sentence-transformers`.

**Untrusted input:** image bytes loaded from disk via `Pillow`. We do
not call `eval`, `exec`, or shell out on any field derived from image
metadata. Callers should still treat `Verdict.reasoning` as untrusted
markdown / HTML when rendering it in a UI.

**Trusted input:** the local model cache directory and the file paths
the caller passes in. imageguard does not sniff for adjacent files or
walk the directory.

## Image handling

- We rely on `Pillow` for decoding. Pass image paths or PIL images
  only; do not pass raw bytes from a network endpoint without first
  validating size and format upstream.
- Decoded images stay in memory; we do not write them to disk or to
  logs, and we do not embed them in the verdict.
- If you add a new comparator, follow the same convention: never
  persist user images, never log them, never include them in the
  `Verdict` payload.
