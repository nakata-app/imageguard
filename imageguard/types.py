"""Public data types — stable contract surface."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    """What the caller's pipeline should do with the render."""

    PASS = "PASS"
    """Render matches the packshot well enough to ship."""

    WARN = "WARN"
    """Drift detected — surface to a human reviewer."""

    REGENERATE = "REGENERATE"
    """Significant drift — re-run the render with a different seed / prompt."""


@dataclass
class Verdict:
    """Result of a single packshot ↔ render comparison.

    All sub-scores are 0.0 (totally different) – 1.0 (pixel-identical).
    `overall_match` is the geometric mean of the sub-scores.
    """

    overall_match: float
    embedding_match: float
    color_match: float
    suggested_action: Action
    reasoning: str
