# imageguard

**Visual hallucination detection — does this AI render show the same product as the original packshot?**

> Status: **v0.1 working PoC.** CLIP embedding + color histogram diff
> on a single packshot ↔ render pair. Segmentation-aware (v0.2) and
> fashion-attribute parsing (v0.3) are on the roadmap.

Sibling to [`halluguard`](https://github.com/nakata-app/halluguard)
(text hallucination) — the **image-domain** equivalent. Cluster shape:

```
text claim    → halluguard.Guard.check(answer)        → trust_score
image claim   → imageguard.VisualGuard.check_render() → match_score
```

---

## The problem this solves

AI image generators rotate the product subtly: lacivert keten gömlek
becomes koyu gri pamuk gömlek; v-yaka becomes crew-yaka; striped
becomes plain. The render *looks* fine, the brand sees it ship, the
customer gets the wrong product description.

`imageguard` re-checks every render against the packshot it was
supposed to depict.

## v0.1 — what works today

Two layers, both deterministic, no LLM in the loop:

1. **CLIP embedding similarity** — global "are we showing the same
   thing" signal via `sentence-transformers/clip-ViT-B-32`.
2. **Color histogram comparison** — HSV space, dominant 5 colors per
   image, KL divergence between distributions.

Returns a `Verdict` with:
- `overall_match: 0.0–1.0`
- `embedding_match`, `color_match` (sub-scores)
- `suggested_action: "PASS" | "WARN" | "REGENERATE"`
- `reasoning: str` (human-readable summary)

## Quickstart

```python
from imageguard import VisualGuard

guard = VisualGuard(packshot="path/to/SKU-1002.jpg")
verdict = guard.check_render("path/to/render-attempt-3.jpg")

if verdict.suggested_action == "REGENERATE":
    print(f"Render off: {verdict.reasoning}")
    # trigger another render
elif verdict.suggested_action == "WARN":
    # surface to stylist for manual review
    pass
else:
    # ship it
    pass
```

## Install

```bash
pip install "imageguard[clip]"   # the only path that ships today
```

## What v0.1 does NOT yet do

- **No segmentation.** A render with a different model / pose / background
  scores lower than it should — we compare the whole frame instead of
  just the garment region. v0.2 brings SAM/CLIPSeg masking.
- **No attribute parsing.** Can't tell you "v-yaka oldu crew-yaka" — only
  that something globally drifted. v0.3 adds a fashion-attribute parser
  (collar / sleeve / cut / length).
- **No multi-packshot identification.** Caller must know which packshot
  to compare against. v0.2 will add `from_catalog()` so you pass the
  render and the library finds the closest match itself.

## Roadmap

| Version | Adds | Status |
|---|---|---|
| v0.0 | API surface stubs | shipped |
| **v0.1** | **CLIP + color histogram, single-packshot mode** | **shipped** |
| v0.2 | Segmentation-aware (SAM/CLIPSeg) + `from_catalog()` for auto-identification | planned |
| v0.3 | Fashion-attribute parser (yaka / kol / kesim / boy) | planned |
| v0.4 | PyPI release | gated on `[fashion]` extras stabilising |

## How it composes with the cluster

```
                                    ┌─────────────────┐
text claim ─→ halluguard.Guard ─────→  trust_score    │
                                    └─────────────────┘
                                    ┌─────────────────┐
image render ─→ imageguard.Guard ───→  match_score    │
                                    └─────────────────┘

                        Sienna pipeline (example):
   stylist + product → AI render → imageguard.check
                                       │
                                       ▼
                          ┌────────────┴────────────┐
                          PASS                  REGENERATE
                          (ship)                 (try again, max 3 attempts,
                                                  then flag for stylist)
```

## License

MIT (planned).

## Status

v0.1 is a **proof of concept**. Tutarlılık (consistency) needs measurement
on real packshot+render pairs before claiming production fitness — see
`docs/calibration.md` for how to score it on your own dataset.
