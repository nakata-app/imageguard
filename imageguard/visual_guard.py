"""VisualGuard — single-packshot ↔ render comparison.

Two layers in v0.1:
  1. CLIP embedding cosine similarity (global "are we showing the same thing")
  2. Color histogram KL-divergence in HSV space (was navy now grey?)

Both are deterministic + no LLM in the loop. Same positioning as
halluguard: opt-in heavier paths (segmentation in v0.2, attribute
parsing in v0.3) are sibling features rather than a forced default.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from imageguard.types import Action, Verdict


# Threshold defaults — tune on your own calibration set. These err on
# the side of "more flags, less silent failure" for the v0.1 release.
DEFAULT_PASS_OVER = 0.85
DEFAULT_REGEN_BELOW = 0.55


class VisualGuard:
    """Compare a single render against a single reference packshot.

    Args:
        packshot: path / PIL Image / numpy array of the reference image.
        clip_model: any CLIP-compatible sentence-transformers model id.
            Pass an instance (already loaded) to skip the lazy load.
        pass_over: overall_match >= this → suggested_action=PASS.
        regenerate_below: overall_match < this → REGENERATE. Between the
            two thresholds → WARN.
    """

    def __init__(
        self,
        packshot: str | Path | Image.Image | np.ndarray[Any, Any],
        clip_model: str | Any = "sentence-transformers/clip-ViT-B-32",
        pass_over: float = DEFAULT_PASS_OVER,
        regenerate_below: float = DEFAULT_REGEN_BELOW,
    ) -> None:
        self._clip_model_arg = clip_model
        self._clip: Any = None  # lazy
        self.pass_over = pass_over
        self.regenerate_below = regenerate_below

        self._packshot_image = _load_image(packshot)
        self._packshot_embedding: np.ndarray[Any, Any] | None = None
        self._packshot_hist = _color_histogram(self._packshot_image)

    # ------------------------------------------------------------------
    def check_render(
        self,
        render: str | Path | Image.Image | np.ndarray[Any, Any],
    ) -> Verdict:
        """Score the render against the packshot supplied at __init__."""
        render_image = _load_image(render)

        # Layer 1: CLIP embedding similarity.
        emb_score = self._embedding_similarity(render_image)

        # Layer 2: color histogram match.
        render_hist = _color_histogram(render_image)
        color_score = _histogram_match(self._packshot_hist, render_hist)

        # Geometric mean — penalises a low score in either layer.
        overall = float(np.sqrt(max(emb_score, 0.0) * max(color_score, 0.0)))

        if overall >= self.pass_over:
            action = Action.PASS
            reasoning = f"render matches packshot (overall={overall:.2f})."
        elif overall < self.regenerate_below:
            action = Action.REGENERATE
            reasoning = (
                f"significant drift (overall={overall:.2f}); "
                f"embedding={emb_score:.2f}, color={color_score:.2f}."
            )
        else:
            action = Action.WARN
            reasoning = (
                f"partial drift (overall={overall:.2f}); "
                f"embedding={emb_score:.2f}, color={color_score:.2f}."
            )

        return Verdict(
            overall_match=overall,
            embedding_match=emb_score,
            color_match=color_score,
            suggested_action=action,
            reasoning=reasoning,
        )

    # ------------------------------------------------------------------
    def _ensure_clip(self) -> None:
        if self._clip is not None:
            return
        if isinstance(self._clip_model_arg, str):
            if importlib.util.find_spec("sentence_transformers") is None:
                raise SystemExit(
                    "VisualGuard's CLIP layer needs sentence-transformers. "
                    'Install with `pip install "imageguard[clip]"`.'
                )
            from sentence_transformers import SentenceTransformer

            self._clip = SentenceTransformer(self._clip_model_arg)
        else:
            self._clip = self._clip_model_arg

    def _embedding_similarity(self, render: Image.Image) -> float:
        self._ensure_clip()
        if self._packshot_embedding is None:
            self._packshot_embedding = self._clip.encode(
                [self._packshot_image],
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True,
            )[0]
        render_emb = self._clip.encode(
            [render],
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )[0]
        # Cosine similarity in [0, 1] (normalised, both vectors unit length).
        cos = float(np.dot(self._packshot_embedding, render_emb))
        # CLIP cosine sims for "same object" usually live in [0.6, 1.0].
        # Stretch [0.5, 1.0] linearly into [0.0, 1.0] for a more
        # interpretable score; below 0.5 is "not even close".
        return max(0.0, min(1.0, (cos - 0.5) * 2))


# ---- Helpers --------------------------------------------------------------

def _load_image(src: str | Path | Image.Image | np.ndarray[Any, Any]) -> Image.Image:
    if isinstance(src, Image.Image):
        return src.convert("RGB")
    if isinstance(src, np.ndarray):
        return Image.fromarray(src.astype(np.uint8)).convert("RGB")
    return Image.open(src).convert("RGB")


def _color_histogram(image: Image.Image, bins: int = 16) -> np.ndarray[Any, Any]:
    """3-channel HSV histogram, normalised to a probability distribution.

    HSV decouples color (hue) from lightness (value), which means a
    "navy linen shirt" and "navy linen shirt under softer light" land in
    similar bins, but a "navy → grey" drift moves the hue mass to a
    different bin → high divergence.
    """
    hsv = image.convert("HSV")
    arr = np.asarray(hsv).reshape(-1, 3).astype(np.float32)
    # Per-channel histograms then concatenated. Captures dominant hue,
    # saturation, and value distributions.
    hist_h, _ = np.histogram(arr[:, 0], bins=bins, range=(0, 256))
    hist_s, _ = np.histogram(arr[:, 1], bins=bins, range=(0, 256))
    hist_v, _ = np.histogram(arr[:, 2], bins=bins, range=(0, 256))
    full: np.ndarray[Any, Any] = np.concatenate([hist_h, hist_s, hist_v]).astype(np.float32)
    s = full.sum()
    if s == 0:
        return full
    out: np.ndarray[Any, Any] = full / s
    return out


def _histogram_match(p: np.ndarray[Any, Any], q: np.ndarray[Any, Any]) -> float:
    """Symmetric similarity score in [0, 1] from two probability distributions.

    Uses Bhattacharyya coefficient (sqrt(p)·sqrt(q) summed) — symmetric,
    bounded, and friendlier than KL when one bin is zero.
    """
    bc = float(np.sum(np.sqrt(p) * np.sqrt(q)))
    return max(0.0, min(1.0, bc))
