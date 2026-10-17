#!/usr/bin/env python3
"""Put every SMIL animation in an SVG on one shared frame clock (24 fps by default).

Chrome and Firefox repaint an animated SVG <img> only on frames where some animated value changed. A smooth animation
changes on every display frame (60+ fps), and many discrete ones with unrelated keyTimes add up to nearly the same.
Here every animation becomes discrete, with its duration, begin and change times on multiples of 1/fps, so all the
changes land on the same frames and the image repaints at most fps times a second: a movie frame rate.

Generators call quantize() on their output; the hand-written SVGs are rewritten in place with
    python3 scripts/fps.py assets/title-*.svg
Running it again on its own output changes nothing.
"""
import re
import sys
from pathlib import Path

FPS = 24
ANIM = re.compile(r"<(animate|animateTransform)\b([^>]*?)\s*(/?)>")
ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
NUM = re.compile(r"-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?")
NUMLIST = re.compile(r"^[\s\d.,eE+-]+$")


def _secs(v):
    return float(v[:-2]) / 1000 if v.endswith("ms") else float(v.rstrip("s"))


def _lerp(a, b, f):
    """Interpolate two number lists ("12", "584 0"); anything else holds `a`, as SMIL does for non-numeric values."""
    if not (NUMLIST.match(a) and NUMLIST.match(b)):
        return a
    na, nb = NUM.findall(a), NUM.findall(b)
    if len(na) != len(nb):
        return a
    vals = iter(f"{round(float(x) + (float(y) - float(x)) * f, 2):g}" for x, y in zip(na, nb))
    return NUM.sub(lambda m: next(vals), a)


def _sample(values, key_times, discrete, t, half):
    """Value at time t (0..1). Discrete changes snap to the nearest frame (`half` = half a frame), which also makes a
    second pass over already-quantized keyTimes (rounded to 6 decimals) land on the same frames."""
    if discrete:
        i = max(j for j, k in enumerate(key_times) if k <= t + half)
        return values[i]
    for j in range(len(values) - 1):
        k0, k1 = key_times[j], key_times[j + 1]
        if t <= k1 + 1e-9:
            return values[j + 1] if k1 - k0 < 1e-9 else _lerp(values[j], values[j + 1], max(0.0, (t - k0) / (k1 - k0)))
    return values[-1]


def _quantize_one(m, fps):
    tag, attrs, close = m.group(1), dict(ATTR.findall(m.group(2))), m.group(3)
    values = attrs["values"].split(";") if "values" in attrs else [attrs["from"], attrs["to"]]
    values = [v.strip() for v in values]
    discrete = attrs.get("calcMode") == "discrete"
    if "keyTimes" in attrs:
        key_times = [float(k) for k in attrs["keyTimes"].split(";")]
    else:
        n = len(values)
        key_times = [i / n for i in range(n)] if discrete else [i / max(1, n - 1) for i in range(n)]
    frames = max(1, round(_secs(attrs["dur"]) * fps))
    vals, kts = [], []
    for f in range(frames):
        v = _sample(values, key_times, discrete, f / frames, 0.5 / frames)
        if not vals or v != vals[-1]:
            vals.append(v)
            kts.append(f / frames)
    out = {k: v for k, v in attrs.items() if k not in ("values", "keyTimes", "calcMode", "from", "to", "dur", "begin")}
    out["calcMode"] = "discrete"
    out["values"] = ";".join(vals)
    out["keyTimes"] = ";".join(f"{k:.6f}".rstrip("0").rstrip(".") if k else "0" for k in kts)
    out["dur"] = f"{frames / fps:.9g}s"
    if "begin" in attrs:
        out["begin"] = f"{round(_secs(attrs['begin']) * fps) / fps:.9g}s"
    order = ["attributeName", "type", "calcMode", "values", "keyTimes", "dur", "begin", "repeatCount"]
    keys = [k for k in order if k in out] + [k for k in out if k not in order]
    return f"<{tag} " + " ".join(f'{k}="{out[k]}"' for k in keys) + (f"{close}>" if close else ">")


def quantize(svg, fps=FPS):
    """Every <animate>/<animateTransform> in `svg` as a discrete animation on the shared 1/fps clock."""
    return ANIM.sub(lambda m: _quantize_one(m, fps), svg)


if __name__ == "__main__":
    for path in sys.argv[1:]:
        p = Path(path)
        p.write_text(quantize(p.read_text()))
        print(f"quantized {p}")
