#!/usr/bin/env python3
"""Generate assets/agent-loop.svg: the agent loop as a btop-style process list plus a mirrored token graph."""
import math
import random
from pathlib import Path

from fps import quantize

T = 8.0  # seconds per full loop, 2s per step
FG, DIM, GREEN, AMBER, BLUE = "#c9d1d9", "#6e7681", "#3fb950", "#d29922", "#58a6ff"
FONT = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'
STEPS = [("plan", "split the task", 4101), ("tool", "grep / edit / run", 4102),
         ("observe", "read the output", 4103), ("reflect", "did it work?", 4104)]


def discrete(segments):
    """segments: [(start_fraction, value)] sorted; returns calcMode=discrete values/keyTimes attrs."""
    kt = ";".join(f"{s:.4f}" for s, _ in segments)
    vals = ";".join(str(v) for _, v in segments)
    return f'calcMode="discrete" values="{vals}" keyTimes="{kt}"'



def meter_bar(cid, x0, ytop, w, h, paint, slide_anim):
    """One meter: the empty track, and the fill drawn full width as a dashed line. A clip whose right edge slides to
    the fill's end reveals the fill. It slides by a translate
    because Chrome repaints an animated SVG image on every frame while any width/x/x2 animation runs, but on a
    transform only when it moves. slide_anim is the translate's timing, values "<fill width> 0"."""
    return (f'<clipPath id="{cid}"><rect x="{x0 - w}" y="{ytop}" width="{w}" height="{h}">'
            f'<animateTransform attributeName="transform" type="translate" {slide_anim} repeatCount="indefinite"/></rect></clipPath>'
            f'<rect x="{x0}" y="{ytop}" width="{w}" height="{h}" fill="url(#track)"/>'
            f'<line x1="{x0}" y1="{ytop + h / 2:g}" x2="{x0 + w}" y2="{ytop + h / 2:g}" stroke="{paint}" stroke-width="{h}" '
            f'stroke-dasharray="{CELL - 1} 1" clip-path="url(#{cid})"/>')


def active_flag(i, on, off):
    s, e = i / 4, (i + 1) / 4
    segs = [(0, off)] if i else []
    segs += [(s, on), (e, off)] if i < 3 else [(s, on)]
    if i == 0:
        segs = [(0, on), (e, off)]
    return discrete(segs)


def flicker(seed, n=16, lo=0.3, hi=1.0):
    """Irregular TV-style brightness: random levels at random times, looping seamlessly."""
    r = random.Random(seed)
    ts = sorted(r.uniform(0.02, 0.98) for _ in range(n - 2))
    kt = [0.0] + ts + [1.0]
    vals = [r.uniform(lo, hi) for _ in range(n - 1)]
    vals.append(vals[0])
    return f'values="{";".join(f"{v:.2f}" for v in vals)}" keyTimes="{";".join(f"{k:.3f}" for k in kt)}"'


def meter_slide(i, lo=12, hi=(72, 78, 66, 78)):
    """Fill width over the loop, as meter_bar's translate values."""
    lo, hi = f"{lo} 0", tuple(f"{h} 0" for h in hi)
    s = i / 4
    sub = 1 / 16
    segs = [(0, lo)] if i else []
    segs += [(s + j * sub, hi[j]) for j in range(4)]
    segs.append(((i + 1) / 4, lo)) if i < 3 else None
    if i == 0:
        segs = [(j * sub, hi[j]) for j in range(4)] + [(0.25, lo)]
    return discrete(segs)


# ---- left: proc box ----
HI_DIM = "#b1bac4"   # PID colour while its row is highlighted (needs contrast on the green tint)
LX, LY, LW, LH = 24, 56, 310, 190
MX, MW, CELL = 174, 84, 6           # meter x, width (14 cells), cell width
rows = []
for i, (name, desc, pid) in enumerate(STEPS):
    y = 112 + i * 26
    rows.append(f"""<g>
    <g visibility="hidden">
      <animate attributeName="visibility" {active_flag(i, "visible", "hidden")} dur="{T:g}s" repeatCount="indefinite"/>
      <rect x="{LX + 8}" y="{y - 17}" width="{LW - 16}" height="24" rx="3" fill="none" stroke="{GREEN}" stroke-width="2" filter="url(#hglow)">
        <animate attributeName="opacity" {flicker(40 + i)} dur="{1.1 + i * 0.37:.2f}s" repeatCount="indefinite"/>
      </rect>
      <rect x="{LX + 8}" y="{y - 17}" width="{LW - 16}" height="24" rx="3" fill="#12261a" stroke="{GREEN}"/>
      <rect x="{LX + 9}" y="{y - 16}" width="{LW - 18}" height="22" rx="2" fill="#fff" filter="url(#tvnoise)">
        <animate attributeName="opacity" values="1;0.8;1;0.9;0.7;1" dur="0.9s" repeatCount="indefinite"/>
      </rect>
      <rect x="{LX + 9}" y="{y - 16}" width="{LW - 18}" height="22" rx="2" fill="url(#scan)"/>
    </g>
    <text x="{LX + 16}" y="{y}" font-size="13" fill="{DIM}">{pid}<animate attributeName="filter" {active_flag(i, "url(#tshadow)", "none")} dur="{T:g}s" repeatCount="indefinite"/><animate attributeName="fill" {active_flag(i, HI_DIM, DIM)} dur="{T:g}s" repeatCount="indefinite"/></text>
    <text x="{LX + 60}" y="{y}" font-size="13" fill="{FG}" xml:space="preserve">{name}<animate attributeName="filter" {active_flag(i, "url(#tshadow)", "none")} dur="{T:g}s" repeatCount="indefinite"/><animate attributeName="fill" {active_flag(i, "#ffffff", FG)} dur="{T:g}s" repeatCount="indefinite"/></text>
    <text x="{MX - 20}" y="{y}" font-size="13" fill="{DIM}">S<animate attributeName="visibility" {active_flag(i, "hidden", "visible")} dur="{T:g}s" repeatCount="indefinite"/></text>
    <text x="{MX - 20}" y="{y}" font-size="13" fill="#7ee787" visibility="hidden" filter="url(#tshadow)">R<animate attributeName="visibility" {active_flag(i, "visible", "hidden")} dur="{T:g}s" repeatCount="indefinite"/></text>
    {meter_bar(f"pg{i}", MX, y - 11, MW, 12, "url(#meter)", f'{meter_slide(i)} dur="{T:g}s"')}
    <rect x="{MX}" y="{y - 11}" width="{MW}" height="12" fill="url(#mcrt)"/>
    <text x="{LX + LW - 14}" y="{y}" font-size="13" fill="{DIM}" text-anchor="end">03%<animate attributeName="visibility" {active_flag(i, "hidden", "visible")} dur="{T:g}s" repeatCount="indefinite"/></text>
    <text x="{LX + LW - 14}" y="{y}" font-size="13" fill="#f2cc60" text-anchor="end" visibility="hidden" filter="url(#tshadow)">95%<animate attributeName="visibility" {active_flag(i, "visible", "hidden")} dur="{T:g}s" repeatCount="indefinite"/></text>
  </g>""")
rows_svg = "\n  ".join(rows)

def comet(x0, y0, pitch=2.8, r=0.8, dur=1.6, tail=(1, .8, .62, .46, .32, .2, .12)):
    """Small braille-style 6x4 dot grid; a green comet chases its tail around the ring."""
    per = [(c, 0) for c in range(6)] + [(5, 1), (5, 2)] + [(c, 3) for c in range(5, -1, -1)] + [(0, 2), (0, 1)]
    n = len(per)
    kt = ";".join(f"{f / n:.4f}" for f in range(n))
    out = []
    for c in range(6):
        for rr in range(4):
            if (c, rr) not in per:
                out.append(f'<circle cx="{x0 + c * pitch:g}" cy="{y0 + rr * pitch:g}" r="{r}" fill="#30363d"/>')
    for k, (c, rr) in enumerate(per):
        cx, cy = f"{x0 + c * pitch:g}", f"{y0 + rr * pitch:g}"
        vals = ";".join(str(tail[(f - k) % n]) if (f - k) % n < len(tail) else "0" for f in range(n))
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#30363d"/><circle cx="{cx}" cy="{cy}" r="{r + 0.1:g}" fill="{GREEN}" opacity="0">'
                   f'<animate attributeName="opacity" calcMode="discrete" values="{vals}" keyTimes="{kt}" dur="{dur}s" repeatCount="indefinite"/></circle>')
    return "".join(out)


spinner = comet(LX + 18, LY + LH - 21)

# ---- right: mirrored token graph ----
RX, RY, RW, RH = 342, 56, 210, 190
CW, CH, UP, DN, VIS, P = 6, 6, 9, 9, 27, 64
GX, MID = RX + 14, RY + 30 + UP * CH


def sig(k, a, b, c):
    w = 2 * math.pi * k / P
    v = 0.45 + 0.25 * math.sin(a * w + 0.5) + 0.14 * math.sin(b * w + 2.0) + 0.08 * math.sin(c * w)
    return min(max(v, 0.06), 1.0)




def bars_path(tops_heights, paint, opacity=1):
    """All columns as one filled path of cell squares, row gaps left open. Cheaper per frame than masking whole bars
    (a mask is an extra offscreen layer every frame) or dashing a stroke (the dashes are rebuilt every frame)."""
    cell = f"h{CW - 1}v{CH - 1}h{1 - CW}z"
    d = "".join(f"M{k * CW} {top}" + f"m0 {CH}".join([cell] * (h // CH)) for k, (top, h) in enumerate(tops_heights))
    return f'<path d="{d}" fill="{paint}"' + (f' fill-opacity="{opacity}"' if opacity < 1 else "") + "/>"




up, dn = [], []
for k in range(P + VIS):
    hu = max(1, round(sig(k % P, 2, 7, 13) * UP)) * CH
    hd = max(1, round(sig((k + 17) % P, 3, 5, 11) * DN)) * CH
    up.append((MID - hu, hu))
    dn.append((MID, hd))
def scroll_attrs(seed, gx, cw, cols):
    """Stop-and-go scroll: short moves of a few columns separated by random pauses (seamless over `cols` columns)."""
    r = random.Random(seed)
    t, done = 0.0, 0
    pts = [(0.0, 0)]
    while done < cols:
        c = min(cols - done, r.choice([1, 2, 2, 3, 4, 6]))
        t += 0.12 + 0.07 * c          # move
        done += c
        pts.append((t, done))
        t += r.choice([0.15, 0.3, 0.5, 0.9, 1.4, 2.2]) if done < cols else 0.6   # pause
        pts.append((t, done))
    keys = ";".join(f"{p / t:.4f}" for p, _ in pts)
    vals = ";".join(f"{gx - d * cw} 0" for _, d in pts)
    return f'values="{vals}" keyTimes="{keys}" dur="{t:.2f}s"'

scroll = scroll_attrs(23, GX, CW, P)
up_svg, dn_svg = bars_path(up, "url(#gup)", 0.9), bars_path(dn, "url(#gdn)", 0.9)   # 0.9: the old phosphor dimmed bars by 10%

# ---- third box: system + GPU meters ----
SX, SY, SW, SH = 560, 56, 262, 190
RMX, RMW = SX + 64, 84                 # meter x (on the 6px grid), width (14 cells)
assert MX % CELL == RMX % CELL == 0     # both meters share the x=0 track pattern
GAUGES = [  # label, base, jitter, formatter
    ("gpu0", 0.97, 0.05, lambda f: f"{f * 100:.0f}%"),
    ("gpu1", 0.82, 0.14, lambda f: f"{f * 100:.0f}%"),
    ("vram", 0.89, 0.05, lambda f: f"{f * 24:.1f}/24G"),
    ("ctx", None, 0, lambda f: f"{f * 200:.0f}k/200k"),     # context fills up, then resets
    ("kv$", 0.61, 0.14, lambda f: f"{f * 100:.0f}%"),
    ("mem", 0.28, 0.05, lambda f: f"{f * 64:.1f}/64G"),
    ("disk", 0.23, 0.01, lambda f: f"{f * 1800:.0f}G/1.8T"),
    ("pwr", 0.78, 0.14, lambda f: f"{f * 450:.0f}W/450W"),
]
grng = random.Random(5)
gauge_rows = []
for gi, (label, base, jit, fmt) in enumerate(GAUGES):
    y = SY + 48 + gi * 17
    n = 7
    holds = [grng.choice([2.0, 2.6, 3.2]) if grng.random() < 0.3 else grng.choice([0.5, 0.7, 0.9, 1.2]) for _ in range(n)]
    total = sum(holds)
    fs = [0.15 + 0.78 * k / (n - 1) for k in range(n)] if base is None else \
         [min(0.99, max(0.03, base + grng.uniform(-jit, jit))) for _ in range(n)]
    cum, kts = 0.0, []
    for h in holds:
        kts.append(f"{cum / total:.4f}")
        cum += h
    kt = ";".join(kts)
    slide = f'calcMode="discrete" values="{";".join(f"{max(CELL, round(f * RMW / CELL) * CELL)} 0" for f in fs)}" keyTimes="{kt}" dur="{total:.2f}s"'
    texts = "".join(
        f'<text x="{SX + SW - 10}" y="{y}" font-size="11" fill="{AMBER if f > 0.9 else FG}" text-anchor="end" visibility="hidden">{fmt(f)}'
        f'<animate attributeName="visibility" calcMode="discrete" values="{";".join("visible" if j == k else "hidden" for j in range(n))}" keyTimes="{kt}" dur="{total:.2f}s" repeatCount="indefinite"/></text>'
        for k, f in enumerate(fs))
    gauge_rows.append(f"""<text x="{SX + 12}" y="{y}" font-size="11" fill="{DIM}">{label}</text>
  {meter_bar(f"sg{gi}", RMX, y - 9, RMW, 10, "url(#rmeter)", slide)}
  <rect x="{RMX}" y="{y - 9}" width="{RMW}" height="10" fill="url(#mcrt)"/>
  {texts}""")
gauges_svg = "\n  ".join(gauge_rows)


def strip(sid, top, heights, color, label, anim, vis=VIS, box_right=RX + RW):
    """Small second panel under a graph (like an extra indicator pane): short block graph, same x-axis and scroll."""
    rows = max(heights)
    h = rows * CH
    w = vis * CW
    cols = [(top + h - heights[k % P] * CH, heights[k % P] * CH) for k in range(P + vis)]
    bars = bars_path(cols, color)
    return f"""<clipPath id="{sid}c"><rect x="{GX}" y="{top}" width="{w}" height="{h}"/></clipPath>
  <rect x="{GX}" y="{top}" width="{w}" height="{h}" fill="url(#empty)"/>
  <g clip-path="url(#{sid}c)"><g transform="translate({GX} 0)">
    {anim}
    {bars}
  </g></g>
  <rect x="{GX}" y="{top}" width="{w}" height="{h}" fill="url(#crt)"/>
  <text x="{box_right - 6}" y="{top + h - 1}" font-size="8" fill="{DIM}" text-anchor="end">{label}</text>"""

_r2 = random.Random(31)
lag_h = [min(4, 1 + int(2 * (0.5 + 0.5 * math.sin(2 * math.pi * 3 * k / P + 1))) + (1 if _r2.random() < 0.15 else 0)) for k in range(P)]
strips_svg = strip("lag", MID + 60, lag_h, BLUE, "lag", f'<animateTransform attributeName="transform" type="translate" {scroll} repeatCount="indefinite"/>')

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 846 262" width="846" height="262" role="img" aria-labelledby="t d">
  <title id="t">Agent loop</title>
  <desc id="d">A btop-style process list where plan, tool, observe and reflect take turns running, next to a scrolling tokens in and out graph and a sys box with GPU, VRAM, context, memory and disk meters.</desc>
  <defs>
    <style>text {{ font-family: {FONT}; }}</style>
    <!-- CRT scanlines: two dark lines per cell row, on the row grid so gap rows stay clear; static, no filter -->
    <pattern id="crt" width="{CW}" height="{CH}" patternUnits="userSpaceOnUse" y="{MID}">
      <rect y="1" width="{CW}" height="1" fill="#000" opacity="0.32"/><rect y="3" width="{CW}" height="1" fill="#000" opacity="0.32"/>
    </pattern>
    <linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#7ee787" stop-opacity="0"/><stop offset="0.85" stop-color="#7ee787" stop-opacity="0.03"/><stop offset="1" stop-color="#7ee787" stop-opacity="0.08"/>
    </linearGradient>
    <filter id="tshadow" x="-20%" y="-40%" width="140%" height="180%"><feDropShadow dx="1" dy="1.3" stdDeviation="1" flood-color="#000"/></filter>
    <filter id="hglow" x="-5%" y="-60%" width="110%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>
    <!-- TV static on the active row's highlight; only one row is visible at a time -->
    <filter id="tvnoise" x="0" y="0" width="1" height="1">
      <feTurbulence type="fractalNoise" baseFrequency="0.5 1.1" numOctaves="1" seed="1" result="n">
        <animate attributeName="seed" calcMode="discrete" values="1;2;3;4;5;6;7;8" dur="0.4s" repeatCount="indefinite"/>
      </feTurbulence>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.9  0 0 0 0 0.45  1.1 0 0 0 -0.38" result="g"/>
      <feComposite in="g" in2="SourceGraphic" operator="in"/>
    </filter>
    <pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" y="2" fill="#000" opacity="0.35"/>
    </pattern>
    <linearGradient id="meter" gradientUnits="userSpaceOnUse" x1="{MX}" y1="0" x2="{MX + MW}" y2="0">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.6" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <!-- meter cells: the empty track is a pattern and the fill a dashed line, so neither needs the old cell mask
         (MX and RMX are both on the {CELL}px grid, so one pattern at x=0 lines up with both) -->
    <pattern id="track" width="{CELL}" height="{CELL}" patternUnits="userSpaceOnUse">
      <rect width="{CELL - 1}" height="{CELL}" fill="#21262d"/>
    </pattern>
    <pattern id="mcrt" width="{CELL}" height="3" patternUnits="userSpaceOnUse">
      <rect y="1" width="{CELL - 1}" height="1" fill="#000" opacity="0.32"/>
    </pattern>
    <linearGradient id="rmeter" gradientUnits="userSpaceOnUse" x1="{RMX}" y1="0" x2="{RMX + RMW}" y2="0">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.6" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <linearGradient id="gup" gradientUnits="userSpaceOnUse" x1="0" y1="{MID}" x2="0" y2="{MID - UP * CH}">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.6" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <linearGradient id="gdn" gradientUnits="userSpaceOnUse" x1="0" y1="{MID}" x2="0" y2="{MID + DN * CH}">
      <stop offset="0" stop-color="#58a6ff"/><stop offset="1" stop-color="#bc8cff"/>
    </linearGradient>
    <pattern id="empty" width="{CW}" height="{CH}" patternUnits="userSpaceOnUse" x="{GX}" y="{MID}">
      <rect width="{CW - 1}" height="{CH - 1}" fill="#161b22"/>
    </pattern>
    <clipPath id="gclip"><rect x="{GX}" y="{MID - UP * CH}" width="{VIS * CW}" height="{(UP + DN) * CH}"/></clipPath>
  </defs>

  <rect width="846" height="262" rx="10" fill="#0d1117"/>
  <text x="24" y="36" font-size="14" xml:space="preserve"><tspan fill="{GREEN}">zek@zek-debian</tspan><tspan fill="{DIM}">:</tspan><tspan fill="{BLUE}">~</tspan><tspan fill="{DIM}">$ </tspan><tspan fill="{FG}">btop --agent</tspan></text>

  <!-- proc box -->
  <rect x="{LX}" y="{LY}" width="{LW}" height="{LH}" rx="6" fill="none" stroke="#30363d"/>
  <rect x="{LX + 14}" y="{LY - 8}" width="70" height="16" fill="#0d1117"/>
  <text x="{LX + 20}" y="{LY + 4}" font-size="12" fill="{GREEN}">proc</text>
  <g font-size="11" fill="{DIM}">
    <text x="{LX + 16}" y="{LY + 34}">PID</text><text x="{LX + 60}" y="{LY + 34}">STEP</text>
    <text x="{MX - 20}" y="{LY + 34}">ST</text>
    <text x="{MX}" y="{LY + 34}">LOAD</text><text x="{LX + LW - 14}" y="{LY + 34}" text-anchor="end">CPU%</text>
  </g>
  {rows_svg}
  {spinner}
  <text x="{LX + 42}" y="{LY + LH - 14}" font-size="12" fill="{DIM}">looping until done</text>

  <!-- tokens graph -->
  <rect x="{RX}" y="{RY}" width="{RW}" height="{RH}" rx="6" fill="none" stroke="#30363d"/>
  <rect x="{RX + 14}" y="{RY - 8}" width="100" height="16" fill="#0d1117"/>
  <text x="{RX + 20}" y="{RY + 4}" font-size="12" fill="{GREEN}" xml:space="preserve">tokens <tspan fill="{DIM}">/ s</tspan></text>
  <rect x="{GX}" y="{MID - UP * CH}" width="{VIS * CW}" height="{(UP + DN) * CH}" fill="url(#empty)"/>
  <g clip-path="url(#gclip)">
    <g transform="translate({GX} 0)">
      <animateTransform attributeName="transform" type="translate" {scroll} repeatCount="indefinite"/>
      {up_svg}
      {dn_svg}
    </g>
  </g>
  <rect x="{GX}" y="{MID - UP * CH}" width="{VIS * CW}" height="{(UP + DN) * CH}" fill="url(#crt)"/>
  <clipPath id="sweepclip"><rect x="{GX}" y="{MID - UP * CH}" width="{VIS * CW}" height="{(UP + DN) * CH}"/><rect x="{GX}" y="{MID + 60}" width="{VIS * CW}" height="{max(lag_h) * CH}"/></clipPath>
  {strips_svg}
  <!-- CRT sweep: faint band rolling down the panes; unfiltered, so moving it never re-runs a blur -->
  <g clip-path="url(#sweepclip)"><rect x="{GX}" y="0" width="{VIS * CW}" height="40" fill="url(#sweep)">
    <animateTransform attributeName="transform" type="translate" from="0 {MID - UP * CH - 40}" to="0 {MID + 60 + max(lag_h) * CH}" dur="5s" repeatCount="indefinite"/>
  </rect></g>
  <text x="{RX + RW - 10}" y="{MID - UP * CH + 8}" font-size="10" fill="{GREEN}" text-anchor="end">in</text>
  <text x="{RX + RW - 10}" y="{MID + DN * CH}" font-size="10" fill="{BLUE}" text-anchor="end">out</text>

  <!-- system / gpu box -->
  <rect x="{SX}" y="{SY}" width="{SW}" height="{SH}" rx="6" fill="none" stroke="#30363d"/>
  <rect x="{SX + 14}" y="{SY - 8}" width="64" height="16" fill="#0d1117"/>
  <text x="{SX + 20}" y="{SY + 4}" font-size="12" fill="{GREEN}">sys</text>
  <text x="{SX + 12}" y="{SY + 28}" font-size="10" fill="{DIM}">NVIDIA GeForce RTX 4090 x2</text>
  {gauges_svg}
</svg>
"""

out = Path(__file__).resolve().parent.parent / "assets" / "agent-loop.svg"
svg = quantize(svg)   # all animations on one 24 fps clock, so the image repaints at most 24x a second
out.write_text(svg)
print(f"wrote {out} ({len(svg)} bytes)")
