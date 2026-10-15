#!/usr/bin/env python3
"""Generate assets/footer.svg: a btop-style 'sleep' dashboard with zek-debian asleep."""
import math
import random
from pathlib import Path

T = 8.0  # seconds per loop
FG, DIM, GREEN, AMBER, BLUE = "#c9d1d9", "#6e7681", "#3fb950", "#d29922", "#58a6ff"
FONT = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'


def discrete(segments):
    kt = ";".join(f"{s:.4f}" for s, _ in segments)
    vals = ";".join(str(v) for _, v in segments)
    return f'calcMode="discrete" values="{vals}" keyTimes="{kt}"'


BY, BH = 52, 110  # box top / height

# ---- zek-debian box ----
bit_box = (f'<rect x="24" y="{BY}" width="150" height="{BH}" rx="6" fill="none" stroke="#30363d"/>'
           f'<rect x="38" y="{BY - 8}" width="88" height="16" fill="#0d1117"/>'
           f'<text x="44" y="{BY + 4}" font-size="12" fill="{GREEN}">zek-debian</text>')
zs = "".join(
    f'<text x="136" y="92" font-size="15" font-weight="700" fill="{DIM}" opacity="0">{ch}'
    f'<animate attributeName="opacity" values="0;1;0" dur="3s" begin="{b}s" repeatCount="indefinite"/>'
    f'<animateTransform attributeName="transform" type="translate" values="0 0;10 -14" dur="3s" begin="{b}s" repeatCount="indefinite"/></text>'
    for ch, b in [("z", 0), ("Z", 1), ("z", 2)]
)
bit = f"""<g transform="translate(66 70)" fill="none" stroke="{FG}" stroke-width="2" stroke-linecap="round">
    <rect x="0" y="14" width="64" height="44" rx="7"/>
    <rect x="8" y="22" width="48" height="22" rx="4" fill="#0d1117"/>
    <line x1="16" y1="33" x2="28" y2="33" stroke="{GREEN}"/><line x1="36" y1="33" x2="48" y2="33" stroke="{GREEN}"/>
    <line x1="32" y1="14" x2="32" y2="4"/>
    <circle cx="32" cy="0" r="3" fill="{DIM}" stroke="none"><animate attributeName="opacity" values="1;0.2;1" dur="4s" repeatCount="indefinite"/></circle>
    <rect x="-6" y="62" width="76" height="12" rx="5"/>
  </g>"""

# ---- status box: draining / filling meters ----
SX, SW = 190, 330
MX, MW, CELL = 276, 150, 6   # 25 cells


def steps(vals):
    """Five equal time slots (fractions) -> discrete segments."""
    return [(i / len(vals), v) for i, v in enumerate(vals)]


def meter(y, name, w_vals, pct_vals, color_text=FG):
    n = len(w_vals)
    pts = [i / (n - 1) * 0.9 for i in range(n)]
    w_anim = (f'<animate attributeName="width" values="{";".join(str(v) for v in w_vals + [w_vals[0], w_vals[0]])}" '
              f'keyTimes="{";".join(f"{t:.4f}" for t in pts + [0.9001, 1])}" dur="{T:g}s" repeatCount="indefinite"/>')
    starts = [0] + [(j - 0.5) / (n - 1) * 0.9 for j in range(1, n)]
    pcts = "".join(
        f'<text x="{SX + SW - 16}" y="{y}" font-size="13" fill="{AMBER if int(p[:-1]) > 60 else DIM}" text-anchor="end" opacity="0">{p}'
        f'<animate attributeName="opacity" {discrete([(starts[j], 1 if j == i else 0) for j in range(n)] + [(0.9001, 1 if i == 0 else 0)])} dur="{T:g}s" repeatCount="indefinite"/></text>'
        for i, p in enumerate(pct_vals)
    )
    return f"""<text x="{SX + 16}" y="{y}" font-size="13" fill="{color_text}">{name}</text>
    <g filter="url(#mglow)"><g mask="url(#cellmask)">
      <rect x="{MX}" y="{y - 11}" width="{MW}" height="12" fill="#21262d"/>
      <rect x="{MX}" y="{y - 11}" width="{w_vals[0]}" height="12" fill="url(#meter)">{w_anim}</rect>
    </g></g>
    {pcts}"""


energy = meter(88, "energy", [150, 112, 74, 36, 6], ["100%", "75%", "49%", "24%", "03%"])
dreams = meter(114, "dreams", [6, 36, 74, 112, 150], ["04%", "24%", "49%", "75%", "99%"])
coffee = meter(140, "coffee", [12, 12, 12, 12, 12], ["08%"] * 5)
status_box = (f'<rect x="{SX}" y="{BY}" width="{SW}" height="{BH}" rx="6" fill="none" stroke="#30363d"/>'
              f'<rect x="{SX + 14}" y="{BY - 8}" width="60" height="16" fill="#0d1117"/>'
              f'<text x="{SX + 20}" y="{BY + 4}" font-size="12" fill="{GREEN}">sleep</text>')

# ---- cpu idle graph ----
GXB, GW = 536, 340
CW, CH, ROWS, VIS, P = 6, 6, 8, 50, 64
GX, GBOT = GXB + 14, BY + 28 + ROWS * CH


def idle(k):
    w = 2 * math.pi * k / P
    v = 0.10 + 0.05 * math.sin(3 * w) + 0.04 * math.sin(8 * w + 1) + 0.28 * max(0, math.sin(w + 4.0)) ** 14
    return min(max(v, 0.05), 1.0)


cols = "".join(
    f'<rect x="{k * CW}" y="{GBOT - max(1, round(idle(k % P) * ROWS)) * CH}" width="{CW - 1}" height="{max(1, round(idle(k % P) * ROWS)) * CH}"/>'
    for k in range(P + VIS)
)
cpu_box = (f'<rect x="{GXB}" y="{BY}" width="{GW}" height="{BH}" rx="6" fill="none" stroke="#30363d"/>'
           f'<rect x="{GXB + 14}" y="{BY - 8}" width="92" height="16" fill="#0d1117"/>'
           f'<text x="{GXB + 20}" y="{BY + 4}" font-size="12" fill="{GREEN}" xml:space="preserve">cpu <tspan fill="{DIM}">idle</tspan></text>'
           f'<rect x="{GXB + GW - 84}" y="{BY - 8}" width="72" height="16" fill="#0d1117"/>'
           f'<text x="{GXB + GW - 16}" y="{BY + 4}" font-size="11" fill="{DIM}" text-anchor="end">99% idle</text>')


def strip(sid, top, heights, color, label, anim, gap, vis=VIS, box_right=GXB + GW):
    """Small second panel under a graph (like an extra indicator pane): short block graph, same x-axis and scroll."""
    rows = max(heights)
    h = rows * CH
    w = vis * CW
    bars = "".join(f'<rect x="{k * CW}" y="{top + h - heights[k % P] * CH}" width="{CW - 1}" height="{heights[k % P] * CH}"/>'
                   for k in range(P + vis))
    return f"""<mask id="{sid}m" maskUnits="userSpaceOnUse" x="{GX}" y="{top}" width="{w}" height="{h}"><rect x="{GX}" y="{top}" width="{w}" height="{h}" fill="url(#{gap})"/></mask>
  <clipPath id="{sid}c"><rect x="{GX}" y="{top}" width="{w}" height="{h}"/></clipPath>
  <rect x="{GX}" y="{top}" width="{w}" height="{h}" fill="url(#empty)"/>
  <g filter="url(#mglow)"><g mask="url(#{sid}m)"><g clip-path="url(#{sid}c)"><g transform="translate({GX} 0)" fill="{color}">
    {anim}
    {bars}
  </g></g></g></g>
  <rect x="{GX}" y="{top}" width="{w}" height="{h}" fill="#fff" filter="url(#gnoisedark)" mask="url(#{sid}m)"/>
  <rect x="{GX}" y="{top}" width="{w}" height="{h}" fill="#fff" filter="url(#gnoise)" mask="url(#{sid}m)"/>
  <text x="{box_right - 6}" y="{top + h - 1}" font-size="8" fill="{DIM}" text-anchor="end">{label}</text>"""

temp_h = [2 + (1 if math.sin(2 * math.pi * 2 * k / P) > 0.3 else 0) for k in range(P)]
strips_svg = strip("temp", GBOT + 6, temp_h, AMBER, "temp", f'<animateTransform attributeName="transform" type="translate" from="{GX} 0" to="{GX - P * CW} 0" dur="12s" repeatCount="indefinite"/>', "hgap")

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 214" width="900" height="214" role="img" aria-labelledby="t d">
  <title id="t">Signing off</title>
  <desc id="d">A btop-style dashboard while zek-debian the robot sleeps: energy drains, dreams fill, the cpu is idle. The prompt says back on the next shift.</desc>
  <defs>
    <style>text {{ font-family: {FONT}; }}</style>
    <linearGradient id="meter" gradientUnits="userSpaceOnUse" x1="{MX}" y1="0" x2="{MX + MW}" y2="0">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.6" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <pattern id="vgap" width="{CELL}" height="10" patternUnits="userSpaceOnUse" x="{MX}">
      <rect width="{CELL}" height="10" fill="#fff"/><rect x="{CELL - 1}" width="1" height="10" fill="#000"/>
    </pattern>
    <mask id="cellmask" maskUnits="userSpaceOnUse" x="{MX}" y="0" width="{MW}" height="214">
      <rect x="{MX}" y="0" width="{MW}" height="214" fill="url(#vgap)"/>
    </mask>
    <linearGradient id="heat" gradientUnits="userSpaceOnUse" x1="0" y1="{GBOT}" x2="0" y2="{GBOT - ROWS * CH}">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.55" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <pattern id="hgap" width="{CW}" height="{CH}" patternUnits="userSpaceOnUse" y="{GBOT}">
      <rect width="{CW}" height="{CH}" fill="#fff"/><rect y="{CH - 1}" width="{CW}" height="1" fill="#000"/>
    </pattern>
    <mask id="gcells" maskUnits="userSpaceOnUse" x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}">
      <rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}" fill="url(#hgap)"/>
    </mask>
    <pattern id="empty" width="{CW}" height="{CH}" patternUnits="userSpaceOnUse" x="{GX}" y="{GBOT}">
      <rect width="{CW - 1}" height="{CH - 1}" fill="#161b22"/>
    </pattern>
    <filter id="phosphor" filterUnits="userSpaceOnUse" x="{GX - 12}" y="{GBOT - ROWS * CH - 12}" width="{VIS * CW + 24}" height="{ROWS * CH + 24}">
      <feColorMatrix in="SourceGraphic" type="saturate" values="1.0" result="soft"/>
      <feComponentTransfer in="soft" result="dim"><feFuncR type="linear" slope="0.9"/><feFuncG type="linear" slope="0.9"/><feFuncB type="linear" slope="0.9"/></feComponentTransfer>
      <feGaussianBlur in="dim" stdDeviation="2.2" result="blur"/>
      <feComponentTransfer in="blur" result="glow"><feFuncA type="linear" slope="0.8"/></feComponentTransfer>
      <feMerge><feMergeNode in="glow"/><feMergeNode in="dim"/></feMerge>
    </filter>
    <filter id="gnoisedark" x="0" y="0" width="1" height="1">
      <feTurbulence type="fractalNoise" baseFrequency="0.7 1.1" numOctaves="1" seed="1" result="n">
        <animate attributeName="seed" calcMode="discrete" values="1;2;3;4;5;6;7;8" dur="0.5s" repeatCount="indefinite"/>
      </feTurbulence>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -1.5 0 0 0 0.66" result="d"/>
      <feComposite in="d" in2="SourceGraphic" operator="in"/>
    </filter>
    <filter id="mglow" x="-5%" y="-70%" width="110%" height="240%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="1.6" result="b"/>
      <feComponentTransfer in="b" result="glow"><feFuncA type="linear" slope="0.5"/></feComponentTransfer>
      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="mnoise" x="0" y="0" width="1" height="1">
      <feTurbulence type="fractalNoise" baseFrequency="0.7 1.1" numOctaves="1" seed="1" result="n">
        <animate attributeName="seed" calcMode="discrete" values="1;2;3;4;5;6;7;8" dur="0.5s" repeatCount="indefinite"/>
      </feTurbulence>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -0.75 0 0 0 0.33" result="d"/>
      <feComposite in="d" in2="SourceGraphic" operator="in"/>
    </filter>
    <filter id="gnoise" x="0" y="0" width="1" height="1">
      <feTurbulence type="fractalNoise" baseFrequency="0.7 1.1" numOctaves="1" seed="1" result="n">
        <animate attributeName="seed" calcMode="discrete" values="1;2;3;4;5;6;7;8" dur="0.5s" repeatCount="indefinite"/>
      </feTurbulence>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.55  0 0 0 0 0.95  0 0 0 0 0.6  1.1 0 0 0 -0.6" result="g"/>
      <feComposite in="g" in2="SourceGraphic" operator="in"/>
    </filter>
    <clipPath id="gclip"><rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}"/></clipPath>
    <clipPath id="say"><rect x="176" y="170" width="0" height="26">
      <animate attributeName="width" values="0;0;232;232;0" keyTimes="0;0.08;0.5;0.94;1" dur="10s" repeatCount="indefinite"/>
    </rect></clipPath>
  </defs>

  <rect width="900" height="214" rx="10" fill="#0d1117"/>
  <text x="24" y="32" font-size="14" xml:space="preserve"><tspan fill="{GREEN}">zek@zek-debian</tspan><tspan fill="{DIM}">:</tspan><tspan fill="{BLUE}">~</tspan><tspan fill="{DIM}">$ </tspan><tspan fill="{FG}">btop --sleep</tspan></text>

  {bit_box}
  {bit}
  {zs}

  {status_box}
  {energy}
  {dreams}
  {coffee}
  <rect x="{MX}" y="{88 - 11}" width="{MW}" height="{140 - 88 + 12}" fill="#fff" filter="url(#mnoise)" mask="url(#cellmask)"/>

  {cpu_box}
  <rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}" fill="url(#empty)"/>
  <g filter="url(#phosphor)">
  <g mask="url(#gcells)"><g clip-path="url(#gclip)">
    <g transform="translate({GX} 0)" fill="url(#heat)">
      <animateTransform attributeName="transform" type="translate" from="{GX} 0" to="{GX - P * CW} 0" dur="12s" repeatCount="indefinite"/>
      {cols}
    </g>
  </g></g>
  </g>
  <rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}" fill="#fff" filter="url(#gnoisedark)" mask="url(#gcells)"/>
  <rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}" fill="#fff" filter="url(#gnoise)" mask="url(#gcells)">
    <animate attributeName="opacity" values="1;0.7;1;0.85;0.6;1" dur="1.1s" repeatCount="indefinite"/>
  </rect>

  {strips_svg}
  <text x="24" y="190" font-size="14" xml:space="preserve"><tspan fill="{GREEN}">zek@zek-debian</tspan><tspan fill="{DIM}">:</tspan><tspan fill="{BLUE}">~</tspan><tspan fill="{DIM}">$ </tspan><tspan fill="{FG}" clip-path="url(#say)">echo "back on the next shift"</tspan></text>
  <rect x="176" y="177" width="9" height="16" fill="{GREEN}">
    <animate attributeName="x" values="176;176;400;400;176" keyTimes="0;0.08;0.5;0.94;1" dur="10s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/>
  </rect>
</svg>
"""

out = Path(__file__).resolve().parent.parent / "assets" / "footer.svg"
out.write_text(svg)
print(f"wrote {out} ({len(svg)} bytes)")
