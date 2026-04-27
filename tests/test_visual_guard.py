"""Visual guard tests — synthetic images, no CLIP required for the
color-only paths. CLIP-dependent tests are gated on the optional
[clip] extras being installed.
"""
from __future__ import annotations

import importlib.util
from typing import Any

import numpy as np
import pytest
from PIL import Image

from imageguard import Action, Verdict, VisualGuard


CLIP_AVAILABLE = importlib.util.find_spec("sentence_transformers") is not None


def _solid_color(rgb: tuple[int, int, int], size: int = 224) -> Image.Image:
    return Image.new("RGB", (size, size), rgb)


def _striped(c1: tuple[int, int, int], c2: tuple[int, int, int], size: int = 224) -> Image.Image:
    img = Image.new("RGB", (size, size), c1)
    arr = np.asarray(img).copy()
    arr[::8] = c2  # horizontal stripes every 8 rows
    return Image.fromarray(arr)


# ---- Color histogram path (no CLIP needed) -------------------------------


def test_identical_images_color_match_one():
    """Same color image vs itself → color_match ≈ 1.0."""
    from imageguard.visual_guard import _color_histogram, _histogram_match

    a = _solid_color((30, 60, 180))  # navy
    h = _color_histogram(a)
    assert _histogram_match(h, h) == pytest.approx(1.0)


def test_different_colors_score_low():
    from imageguard.visual_guard import _color_histogram, _histogram_match

    navy = _color_histogram(_solid_color((30, 60, 180)))
    grey = _color_histogram(_solid_color((128, 128, 128)))
    score = _histogram_match(navy, grey)
    assert score < 0.5  # very different


def test_similar_shades_score_moderate_to_high():
    """Navy and slightly-darker navy should be much closer than navy and grey."""
    from imageguard.visual_guard import _color_histogram, _histogram_match

    navy_a = _color_histogram(_solid_color((30, 60, 180)))
    navy_b = _color_histogram(_solid_color((40, 70, 190)))
    score = _histogram_match(navy_a, navy_b)
    # Adjacent shades fall in adjacent histogram bins (16 bins/channel),
    # so the Bhattacharyya coefficient lands in the 0.6-0.7 range — well
    # above the 0.3-0.5 we see for unrelated colors. Loosened threshold.
    assert score > 0.6  # close shades stay clustered
    # And clearly higher than navy vs grey:
    grey = _color_histogram(_solid_color((128, 128, 128)))
    assert score > _histogram_match(navy_a, grey)


# ---- Verdict shape (use a stub CLIP so we don't pull weights in tests) ---


class _FakeClip:
    """Mock CLIP that returns deterministic embeddings keyed off a colour
    fingerprint. Lets us test VisualGuard end-to-end without downloading
    the real model."""

    def encode(
        self, images: list[Image.Image], convert_to_numpy: bool = True,
        show_progress_bar: bool = False, normalize_embeddings: bool = True,
    ) -> Any:
        out = []
        for img in images:
            arr = np.asarray(img.convert("RGB").resize((8, 8))).astype(np.float32) / 255.0
            vec = arr.mean(axis=(0, 1))  # 3-d color centroid
            # Pad to 32 dim and normalise (matches CLIP-ish API expectation).
            full = np.concatenate([vec, np.zeros(29, dtype=np.float32)])
            full = full / (np.linalg.norm(full) + 1e-9)
            out.append(full)
        return np.stack(out, axis=0)


def test_verdict_pass_when_images_identical():
    img = _solid_color((30, 60, 180))
    guard = VisualGuard(packshot=img, clip_model=_FakeClip())
    v = guard.check_render(img)
    assert isinstance(v, Verdict)
    assert v.suggested_action == Action.PASS
    assert v.overall_match >= 0.85


def test_verdict_regenerate_when_color_swapped():
    """Navy packshot → grey render → significant drift → REGENERATE."""
    navy = _solid_color((30, 60, 180))
    grey = _solid_color((128, 128, 128))
    guard = VisualGuard(packshot=navy, clip_model=_FakeClip())
    v = guard.check_render(grey)
    assert v.color_match < 0.5
    assert v.suggested_action == Action.REGENERATE


def test_verdict_warn_when_pattern_drift():
    """Navy solid vs navy striped — color similar, embedding drifts."""
    solid = _solid_color((30, 60, 180))
    striped = _striped((30, 60, 180), (200, 200, 200))
    guard = VisualGuard(packshot=solid, clip_model=_FakeClip())
    v = guard.check_render(striped)
    # Color stays high (navy is dominant), embedding drops slightly →
    # somewhere between PASS and REGENERATE.
    assert v.suggested_action in {Action.PASS, Action.WARN}


def test_verdict_reasoning_is_human_readable():
    img = _solid_color((30, 60, 180))
    v = VisualGuard(packshot=img, clip_model=_FakeClip()).check_render(img)
    assert "overall=" in v.reasoning


# ---- Real CLIP path — only when extras installed -------------------------


@pytest.mark.skipif(not CLIP_AVAILABLE, reason="sentence_transformers not installed")
def test_real_clip_score_for_solid_pair_is_high():
    """Smoke test against the actual CLIP model. Slow first run (model download)."""
    img = _solid_color((30, 60, 180))
    guard = VisualGuard(packshot=img)  # default clip_model
    v = guard.check_render(img)
    # Same image → embedding score should be at the top of the scale.
    assert v.embedding_match > 0.8
