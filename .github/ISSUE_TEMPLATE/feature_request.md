---
name: Feature request
about: Propose new behaviour or an API addition
title: ''
labels: enhancement
---

**What's the use case**
<!-- describe the problem first, not the solution. Concrete example:
     "we ship womenswear renders and our v-yaka becomes crew-yaka in
     ~8% of batches; we need a per-attribute score." -->

**Proposed approach** (optional)
<!-- if you already have a sketch, function signature, a fixture, a
     pseudo-code outline -->

**Why this belongs in imageguard (not halluguard / claimcheck / a domain pipeline)**
<!-- imageguard is image-domain hallucination detection: render vs
     packshot, deterministic comparators, no LLM in the decision path.
     halluguard is text-domain; claimcheck is orchestration. If your
     idea wants an LLM to grade a render, it probably belongs upstream
     (a pipeline using imageguard as one signal), not inside imageguard. -->

**Alternatives considered**
<!-- existing workarounds, third-party libraries (CLIP-only, DINOv2,
     SAM, attribute parsers), the upstream model authors themselves,
     etc. -->

**Calibration data**
<!-- if you have packshot+render pairs with stylist labels, that is
     gold for tuning; let us know roughly how many and whether they
     can be shared (anonymised or under NDA). See docs/calibration.md
     for the score format. -->
