# Contributing to imageguard

Thanks for considering a contribution. The repo is small enough that the
review pipeline is short, keep changes focused, the bar is "honest
visual verdicts + clear tradeoffs."

## Quickstart for a local dev loop

```bash
git clone https://github.com/nakata-app/imageguard.git
cd imageguard
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,clip]"
```

The first `VisualGuard(packshot=...)` instantiation downloads the
CLIP weights (`sentence-transformers/clip-ViT-B-32`) into the local
HF cache. Subsequent runs are offline.

## What we run before every commit

```bash
ruff check imageguard tests             # lint
mypy --strict imageguard                # type check
pytest -q                               # unit tests
```

CI runs the same three on Python 3.10 / 3.11 / 3.12. A PR that doesn't
pass them locally won't pass CI either.

## What lands easily

- Bug fixes with a regression test that fails before / passes after.
- New comparators behind the existing
  `imageguard.visual_guard.Comparator`-style functions (color, embedding,
  later: segmentation, attribute parsing). Keep them deterministic and
  explainable.
- Calibration data: real packshot+render pairs with stylist labels.
  See `docs/calibration.md` for the score format.
- Threshold tuning that ships with a calibration run (numbers, not
  vibes) on a representative dataset.
- Documentation, especially worked examples for non-fashion domains
  (product photography, e-commerce QA, dataset audit).

## What needs a discussion first

- Anything that changes the public API surface (`VisualGuard.check_render`,
  the `Verdict` shape, the `Action` enum).
- Adding an LLM into the inference path. imageguard is intentionally
  LLM-free at decision time. An LLM can help a future
  attribute-parser stage, but must never silently grade renders.
- New required dependencies. We try hard to keep the core install
  small (`numpy` + `Pillow`); heavy deps (`sentence-transformers`,
  `torch`, segmentation backbones) ship as opt-in extras.
- Segmentation backbones. v0.2 plans SAM / CLIPSeg, but the choice of
  default model affects install size dramatically. Open an issue
  before wiring one in.

## Style

- Match the existing code. Type hints on public surfaces; no
  speculative abstractions; comments only for non-obvious WHY.
- One commit per logical change. Squash if you accumulate "fix
  comments" commits.
- Commit messages: imperative mood, short subject ("add segmentation
  comparator"), longer body if the change is non-trivial.

## Reporting bugs

GitHub Issues. Include:
- Python version + OS.
- The minimum reproduction (one packshot path + one render path is
  enough; if you can share the images, even better).
- What `suggested_action` you expected vs what you got.
- Whether you ran with the CLIP backbone (`[clip]` extra) or only
  the color-histogram fallback.

## Reporting security issues

See [`SECURITY.md`](SECURITY.md). Don't open a public issue for an
unpatched vulnerability.
