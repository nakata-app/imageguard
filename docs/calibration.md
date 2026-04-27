# Calibration — kendi datasınla test et

v0.1 prototip. Tutarlılığı ölçmek için kendi packshot+render örneklerinle
şu adımları çalıştır.

## Hızlı tek-çift testi

```python
from imageguard import VisualGuard

guard = VisualGuard(packshot="/path/to/SKU-1002.jpg")
verdict = guard.check_render("/path/to/render-attempt-1.jpg")

print(f"overall:    {verdict.overall_match:.3f}")
print(f"embedding:  {verdict.embedding_match:.3f}")
print(f"color:      {verdict.color_match:.3f}")
print(f"action:     {verdict.suggested_action.value}")
print(f"reasoning:  {verdict.reasoning}")
```

İlk çalıştırma CLIP modelini indirir (~600MB). Sonraki çağrılarda cache.

## Toplu kalibrasyon — gerçek tutarlılık ölçümü

Eline 2 etiketli klasör al:
- `good/` — render packshot ile uyumlu, stilist onaylamış olduğu örnekler
- `bad/`  — render'da renk/desen/kesim kaymış, atılmış örnekler

Her klasörün adında packshot+render çiftleri var (örn: `SKU-1002_packshot.jpg`
ve `SKU-1002_render.jpg`).

```python
from pathlib import Path

from imageguard import VisualGuard


def score_pair(packshot_path, render_path):
    return VisualGuard(packshot=packshot_path).check_render(render_path)


good_scores = []
bad_scores = []

for pair in Path("good").glob("*_packshot.jpg"):
    sku = pair.stem.replace("_packshot", "")
    render = pair.parent / f"{sku}_render.jpg"
    if render.exists():
        good_scores.append(score_pair(pair, render).overall_match)

for pair in Path("bad").glob("*_packshot.jpg"):
    sku = pair.stem.replace("_packshot", "")
    render = pair.parent / f"{sku}_render.jpg"
    if render.exists():
        bad_scores.append(score_pair(pair, render).overall_match)

print(f"GOOD median: {sorted(good_scores)[len(good_scores)//2]:.3f}")
print(f"BAD  median: {sorted(bad_scores)[len(bad_scores)//2]:.3f}")
print(f"separation:  {(sum(good_scores)/len(good_scores)) - (sum(bad_scores)/len(bad_scores)):.3f}")
```

## Ne aramalısın

**İyi sinyal (v0.1 işe yarıyor):**
- GOOD median > 0.80
- BAD median < 0.55
- İkisi arasında >= 0.20 separation

**Vasat sinyal (segmentation ile düzelir):**
- GOOD median 0.65–0.80 (model/poz farkı global skoru aşağı çekiyor)
- BAD median 0.55–0.70 (renk korumaya almış, embedding kararsız)
- Separation 0.10–0.20

→ Çözüm: v0.2'de SAM mask ile sadece kıyafet bölgesi karşılaştırılır.

**Kötü sinyal (yaklaşım yetmez):**
- GOOD ve BAD birbirine girmiş
- Separation < 0.05

→ V0.1 modeli ile çözülmez. Fashion-attribute parser (v0.3) gerek.

## Threshold tuning

`pass_over` ve `regenerate_below` parametrelerini kendi dağılımına göre tut:

```python
guard = VisualGuard(
    packshot="...",
    pass_over=0.78,         # GOOD median - 1 stddev
    regenerate_below=0.55,  # BAD median + 1 stddev
)
```

Sonuç dağılımı:
- `>= pass_over` → otomatik geçer (göz atmadan ship)
- `< regenerate_below` → otomatik regenerate
- Aradakiler → stilist gözüne sun

## False-positive analizi

`good/` üzerinde REGENERATE çıkan vakalara bak:
- Aynı ürün ama farklı arka plan → embedding yanlışlıkla düşük → segmentation lazım
- Aynı renk ama farklı ışık → color histogram dürüst tutmuş → bunu HSV V kanalını ağırlıklandırarak düzeltebiliriz

Bu ipuçlarını bana ilet, v0.2 önceliklendirmesi netleşir.

## False-negative analizi

`bad/` üzerinde PASS çıkan vakalara bak — bunlar **kaçırılmış halüsinasyonlar**:
- Renk doğru, desen değişmiş → fashion-attribute parser (v0.3) lazım
- Yaka tipi değişmiş → segmentation + parsing lazım

## Quick win: hızlı eşik bul

50-100 etiketli çift varsa optimal threshold ROC analizi ile bulunur:

```python
from sklearn.metrics import roc_curve

scores = good_scores + bad_scores
labels = [1] * len(good_scores) + [0] * len(bad_scores)
fpr, tpr, thresholds = roc_curve(labels, scores)
optimal_idx = (tpr - fpr).argmax()
print(f"optimal pass_over threshold: {thresholds[optimal_idx]:.3f}")
```
