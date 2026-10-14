#!/usr/bin/env python3
"""Generate assets/agent-loop.svg: the agent loop as a btop-style process list plus a mirrored token graph."""
import math
import random
from pathlib import Path

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


def active_flag(i, on, off):
    s, e = i / 4, (i + 1) / 4
    segs = [(0, off)] if i else []
    segs += [(s, on), (e, off)] if i < 3 else [(s, on)]
    if i == 0:
        segs = [(0, on), (e, off)]
    return discrete(segs)


def meter_width(i, lo=12, hi=(84, 90, 80, 88)):
    s = i / 4
    sub = 1 / 16
    segs = [(0, lo)] if i else []
    segs += [(s + j * sub, hi[j]) for j in range(4)]
    segs.append(((i + 1) / 4, lo)) if i < 3 else None
    if i == 0:
        segs = [(j * sub, hi[j]) for j in range(4)] + [(0.25, lo)]
    return discrete(segs)


# ---- left: proc box ----
LX, LY, LW, LH = 24, 56, 330, 190
MX, MW, CELL = 174, 96, 6           # meter x, width (16 cells), cell width
rows = []
for i, (name, desc, pid) in enumerate(STEPS):
    y = 112 + i * 26
    rows.append(f"""<g>
    <rect x="{LX + 8}" y="{y - 17}" width="{LW - 16}" height="24" rx="3" fill="#12261a" stroke="{GREEN}" opacity="0">
      <animate attributeName="opacity" {active_flag(i, 1, 0)} dur="{T:g}s" repeatCount="indefinite"/>
    </rect>
    <text x="{LX + 16}" y="{y}" font-size="13" fill="{DIM}">{pid}</text>
    <text x="{LX + 60}" y="{y}" font-size="13" fill="{FG}" xml:space="preserve">{name}</text>
    <text x="{MX - 20}" y="{y}" font-size="13" fill="{DIM}">S<animate attributeName="opacity" {active_flag(i, 0, 1)} dur="{T:g}s" repeatCount="indefinite"/></text>
    <text x="{MX - 20}" y="{y}" font-size="13" fill="{GREEN}" opacity="0">R<animate attributeName="opacity" {active_flag(i, 1, 0)} dur="{T:g}s" repeatCount="indefinite"/></text>
    <g mask="url(#cellmask)">
      <rect x="{MX}" y="{y - 11}" width="{MW}" height="12" fill="#21262d"/>
      <rect x="{MX}" y="{y - 11}" width="12" height="12" fill="url(#meter)">
        <animate attributeName="width" {meter_width(i)} dur="{T:g}s" repeatCount="indefinite"/>
      </rect>
    </g>
    <text x="{LX + LW - 14}" y="{y}" font-size="13" fill="{DIM}" text-anchor="end">03%<animate attributeName="opacity" {active_flag(i, 0, 1)} dur="{T:g}s" repeatCount="indefinite"/></text>
    <text x="{LX + LW - 14}" y="{y}" font-size="13" fill="{AMBER}" text-anchor="end" opacity="0">95%<animate attributeName="opacity" {active_flag(i, 1, 0)} dur="{T:g}s" repeatCount="indefinite"/></text>
  </g>""")
rows_svg = "\n  ".join(rows)

spinner = "".join(
    f'<text x="{LX + 18}" y="{LY + LH - 14}" font-size="12" fill="{GREEN}" opacity="0">{ch}'
    f'<animate attributeName="opacity" {discrete([(j / 4, 1 if j == k else 0) for j in range(4)])} dur="0.6s" repeatCount="indefinite"/></text>'
    for k, ch in enumerate(["|", "/", "-", "\\"])
)

# ---- right: mirrored token graph ----
RX, RY, RW, RH = 362, 56, 230, 190
CW, CH, UP, DN, VIS, P = 6, 6, 11, 11, 30, 64
GX, MID = RX + 14, RY + 30 + UP * CH


def sig(k, a, b, c):
    w = 2 * math.pi * k / P
    v = 0.45 + 0.25 * math.sin(a * w + 0.5) + 0.14 * math.sin(b * w + 2.0) + 0.08 * math.sin(c * w)
    return min(max(v, 0.06), 1.0)


up, dn = [], []
for k in range(P + VIS):
    hu = max(1, round(sig(k % P, 2, 7, 13) * UP)) * CH
    hd = max(1, round(sig((k + 17) % P, 3, 5, 11) * DN)) * CH
    up.append(f'<rect x="{k * CW}" y="{MID - hu}" width="{CW - 1}" height="{hu}"/>')
    dn.append(f'<rect x="{k * CW}" y="{MID}" width="{CW - 1}" height="{hd}"/>')
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
up_svg, dn_svg = "".join(up), "".join(dn)

# ---- third box: system + GPU meters ----
SX, SY, SW, SH = 600, 56, 276, 190
RMX, RMW = SX + 66, 84                 # meter x, width (14 cells)
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
    widths = ";".join(str(max(CELL, round(f * RMW / CELL) * CELL)) for f in fs)
    texts = "".join(
        f'<text x="{SX + SW - 10}" y="{y}" font-size="11" fill="{AMBER if f > 0.9 else FG}" text-anchor="end" opacity="0">{fmt(f)}'
        f'<animate attributeName="opacity" calcMode="discrete" values="{";".join("1" if j == k else "0" for j in range(n))}" keyTimes="{kt}" dur="{total:.2f}s" repeatCount="indefinite"/></text>'
        for k, f in enumerate(fs))
    gauge_rows.append(f"""<text x="{SX + 12}" y="{y}" font-size="11" fill="{DIM}">{label}</text>
  <g mask="url(#rcellmask)">
    <rect x="{RMX}" y="{y - 9}" width="{RMW}" height="10" fill="#21262d"/>
    <rect x="{RMX}" y="{y - 9}" width="{CELL}" height="10" fill="url(#rmeter)">
      <animate attributeName="width" calcMode="discrete" values="{widths}" keyTimes="{kt}" dur="{total:.2f}s" repeatCount="indefinite"/>
    </rect>
  </g>
  {texts}""")
gauges_svg = "\n  ".join(gauge_rows)


svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 262" width="900" height="262" role="img" aria-labelledby="t d">
  <title id="t">Agent loop</title>
  <desc id="d">A btop-style process list where plan, tool, observe and reflect take turns running, next to a scrolling tokens in and out graph and a sys box with GPU, VRAM, context, memory and disk meters.</desc>
  <defs>
    <style>text {{ font-family: {FONT}; }}</style>
    <linearGradient id="meter" gradientUnits="userSpaceOnUse" x1="{MX}" y1="0" x2="{MX + MW}" y2="0">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.6" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <pattern id="vgap" width="{CELL}" height="10" patternUnits="userSpaceOnUse" x="{MX}">
      <rect width="{CELL}" height="10" fill="#fff"/><rect x="{CELL - 1}" width="1" height="10" fill="#000"/>
    </pattern>
    <mask id="cellmask" maskUnits="userSpaceOnUse" x="{MX}" y="0" width="{MW}" height="262">
      <rect x="{MX}" y="0" width="{MW}" height="262" fill="url(#vgap)"/>
    </mask>
    <linearGradient id="rmeter" gradientUnits="userSpaceOnUse" x1="{RMX}" y1="0" x2="{RMX + RMW}" y2="0">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.6" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <pattern id="rvgap" width="{CELL}" height="10" patternUnits="userSpaceOnUse" x="{RMX}">
      <rect width="{CELL}" height="10" fill="#fff"/><rect x="{CELL - 1}" width="1" height="10" fill="#000"/>
    </pattern>
    <mask id="rcellmask" maskUnits="userSpaceOnUse" x="{RMX}" y="0" width="{RMW}" height="262">
      <rect x="{RMX}" y="0" width="{RMW}" height="262" fill="url(#rvgap)"/>
    </mask>
    <linearGradient id="gup" gradientUnits="userSpaceOnUse" x1="0" y1="{MID}" x2="0" y2="{MID - UP * CH}">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.6" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <linearGradient id="gdn" gradientUnits="userSpaceOnUse" x1="0" y1="{MID}" x2="0" y2="{MID + DN * CH}">
      <stop offset="0" stop-color="#58a6ff"/><stop offset="1" stop-color="#bc8cff"/>
    </linearGradient>
    <pattern id="hgap" width="{CW}" height="{CH}" patternUnits="userSpaceOnUse" y="{MID}">
      <rect width="{CW}" height="{CH}" fill="#fff"/><rect y="{CH - 1}" width="{CW}" height="1" fill="#000"/>
    </pattern>
    <mask id="gcells" maskUnits="userSpaceOnUse" x="{GX}" y="{MID - UP * CH}" width="{VIS * CW}" height="{(UP + DN) * CH}">
      <rect x="{GX}" y="{MID - UP * CH}" width="{VIS * CW}" height="{(UP + DN) * CH}" fill="url(#hgap)"/>
    </mask>
    <clipPath id="gclip"><rect x="{GX}" y="{MID - UP * CH}" width="{VIS * CW}" height="{(UP + DN) * CH}"/></clipPath>
  </defs>

  <rect width="900" height="262" rx="10" fill="#0d1117"/>
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
  <text x="{LX + 36}" y="{LY + LH - 14}" font-size="12" fill="{DIM}">looping until done</text>

  <!-- tokens graph -->
  <rect x="{RX}" y="{RY}" width="{RW}" height="{RH}" rx="6" fill="none" stroke="#30363d"/>
  <rect x="{RX + 14}" y="{RY - 8}" width="100" height="16" fill="#0d1117"/>
  <text x="{RX + 20}" y="{RY + 4}" font-size="12" fill="{GREEN}" xml:space="preserve">tokens <tspan fill="{DIM}">/ s</tspan></text>
  <g mask="url(#gcells)">
    <g clip-path="url(#gclip)">
      <g transform="translate({GX} 0)">
        <animateTransform attributeName="transform" type="translate" {scroll} repeatCount="indefinite"/>
        <g fill="url(#gup)">{up_svg}</g>
        <g fill="url(#gdn)">{dn_svg}</g>
      </g>
    </g>
  </g>
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
out.write_text(svg)
print(f"wrote {out} ({len(svg)} bytes)")
