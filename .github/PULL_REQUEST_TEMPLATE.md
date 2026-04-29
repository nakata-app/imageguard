## What this changes

<!-- one-paragraph summary; link to a tracking issue if there is one -->

## How it was tested

<!-- pytest output, a manual packshot+render repro, or a calibration-set smoke -->

## Checklist

- [ ] `ruff check imageguard tests` is clean
- [ ] `mypy --strict imageguard` is clean
- [ ] `pytest -q` passes locally
- [ ] CHANGELOG entry added (under `[Unreleased]`)
- [ ] If this changes the public API (`VisualGuard.check_render`,
      `Verdict`, `Action`): README updated
- [ ] If this adds a comparator: it is deterministic, has a unit test
      with a fixture, and is wired in behind a clear flag/strategy
- [ ] If this adds a dependency: it is an `[optional]` extra unless
      truly core (numpy + Pillow only)
- [ ] If thresholds changed: include the calibration numbers (which
      dataset, sample size, before/after action distribution)
