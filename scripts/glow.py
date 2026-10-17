"""Pre-blurred glow bitmaps for the generators.

An SVG feGaussianBlur over animated content reruns every frame (GitHub shows the SVG as an <img>, and Chrome re-rasters
the whole image while anything animates). The bars themselves never change, they only scroll, so their glow can be
blurred once here and embedded as a small PNG that scrolls with them: the same gaussian look, but drawing it each
frame is just a bitmap blit.
"""
import base64
import math
import struct
import zlib


def hex_rgb(c):
    return tuple(int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))


def gradient(stops):
    """stops: [(offset, "#rrggbb")] -> f(t) giving (r, g, b) in 0..1, clamped like an SVG gradient."""
    pts = [(o, hex_rgb(c)) for o, c in stops]

    def at(t):
        if t <= pts[0][0]:
            return pts[0][1]
        for (o0, c0), (o1, c1) in zip(pts, pts[1:]):
            if t <= o1:
                f = (t - o0) / (o1 - o0)
                return tuple(a + (b - a) * f for a, b in zip(c0, c1))
        return pts[-1][1]
    return at


def cell_rects(tops_heights, cw, ch, color_at):
    """Block-graph cells as glow_image rects: column k at x = k * cw, (top, height) in user units, row gaps left open;
    color_at(y) colours each cell by its centre (cells are small enough that a gradient across one doesn't show)."""
    return [(k * cw, top + r * ch, cw - 1, ch - 1, color_at(top + r * ch + (ch - 1) / 2))
            for k, (top, h) in enumerate(tops_heights) for r in range(h // ch)]


def _png(w, h, rgba):
    rows = []
    prev = bytes(w * 4)
    for y in range(h):
        row = rgba[y * w * 4:(y + 1) * w * 4]
        rows.append(b"\x02" + bytes((a - b) & 255 for a, b in zip(row, prev)))   # "Up" filter: smooth glows compress well
        prev = row

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


def _blur1d(src, w, h, k, horizontal):
    r = len(k) // 2
    out = [0.0] * (w * h)
    for y in range(h):
        for x in range(w):
            s = 0.0
            for i, kv in enumerate(k):
                if horizontal:
                    xx = x + i - r
                    if 0 <= xx < w:
                        s += src[y * w + xx] * kv
                else:
                    yy = y + i - r
                    if 0 <= yy < h:
                        s += src[yy * w + x] * kv
            out[y * w + x] = s
    return out


def glow_image(rects, sigma, alpha, dim=1.0, scale=0.5, extra=""):
    """rects: [(x, y, w, h, (r, g, b))] in user units on an integer grid. Returns an <image> covering their bounds plus
    room for the blur: the rects drawn, blurred with `sigma` (user units), times `alpha`, colours times `dim` --
    what <feGaussianBlur stdDeviation=sigma> then <feFuncA slope=alpha> made of them."""
    pad = math.ceil(3 * sigma) + 1
    x0 = min(r[0] for r in rects) - pad
    y0 = min(r[1] for r in rects) - pad
    W = max(r[0] + r[2] for r in rects) + pad - x0
    H = max(r[1] + r[3] for r in rects) + pad - y0
    # draw at 1px per unit (premultiplied; the rects never overlap), then box-downsample to `scale`
    full = [[0.0] * (W * H) for _ in range(4)]
    for rx, ry, rw, rh, (cr, cg, cb) in rects:
        for yy in range(ry - y0, ry - y0 + rh):
            base = yy * W
            for xx in range(rx - x0, rx - x0 + rw):
                full[0][base + xx], full[1][base + xx], full[2][base + xx], full[3][base + xx] = cr, cg, cb, 1.0
    step = round(1 / scale)
    w, h = math.ceil(W / step), math.ceil(H / step)
    small = []
    for ch in full:
        out = [0.0] * (w * h)
        for y in range(H):
            for x in range(W):
                out[(y // step) * w + x // step] += ch[y * W + x]
        small.append([v / (step * step) for v in out])
    s = sigma / step
    r = math.ceil(3 * s)
    k = [math.exp(-(i * i) / (2 * s * s)) for i in range(-r, r + 1)]
    k = [v / sum(k) for v in k]
    blurred = [_blur1d(_blur1d(ch, w, h, k, True), w, h, k, False) for ch in small]
    rgba = bytearray()
    for i in range(w * h):
        a = blurred[3][i]
        if a <= 1e-6:
            rgba += b"\0\0\0\0"
            continue
        rgba += bytes(min(255, round(blurred[c][i] / a * dim * 255)) for c in range(3)) + bytes([min(255, round(a * alpha * 255))])
    uri = "data:image/png;base64," + base64.b64encode(_png(w, h, bytes(rgba))).decode()
    return f'<image x="{x0}" y="{y0}" width="{w * step}" height="{h * step}" preserveAspectRatio="none" href="{uri}"{extra}/>'
