---
name: Bug report
about: Something broke or behaves unexpectedly
title: ''
labels: bug
---

**What happened**
<!-- one-line summary -->

**Reproduce**
```python
# minimal snippet, two image paths + the VisualGuard call that
# misbehaves
from imageguard import VisualGuard
guard = VisualGuard(packshot="...")
verdict = guard.check_render("...")
```

**Expected**
<!-- what suggested_action / match score you thought you'd see -->

**Got**
<!-- what you actually saw, including any traceback and the full Verdict -->

**Environment**
- imageguard version (commit SHA if you're on master):
- Python version:
- OS:
- Did you install the `[clip]` extra (full CLIP backbone) or only the
  color-histogram fallback?
- `sentence-transformers` / `torch` versions if applicable:
- Image format and rough dimensions (jpg/png, 1024x1024, etc.):

**Images**
<!-- if you can share them, attach packshot + render. If they are
     internal / customer-confidential, describe them instead (color,
     subject, framing) and we will work from your description. -->
