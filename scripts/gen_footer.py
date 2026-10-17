#!/usr/bin/env python3
"""Generate assets/footer.svg: a btop-style 'sleep' dashboard with zek-debian asleep."""
import math
import random
from pathlib import Path

from fps import quantize
from glow import cell_rects, glow_image, gradient, hex_rgb

T = 8.0  # seconds per loop
FG, DIM, GREEN, AMBER, BLUE = "#c9d1d9", "#6e7681", "#3fb950", "#d29922", "#58a6ff"
FONT = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'


def discrete(segments):
    kt = ";".join(f"{s:.4f}" for s, _ in segments)
    vals = ";".join(str(v) for _, v in segments)
    return f'calcMode="discrete" values="{vals}" keyTimes="{kt}"'



def meter_bar(cid, img, x0, ytop, w, h, paint, slide_anim):
    """One meter: its pre-blurred glow (`img`, see glow.py), the empty track, and the fill drawn full width as a dashed
    line. A clip whose right edge slides to the fill's end reveals the glow and the fill. It slides by a translate
    because Chrome repaints an animated SVG image on every frame while any width/x/x2 animation runs, but on a
    transform only when it moves. slide_anim is the translate's timing, values "<fill width> 0". Glow spills 5px left
    and 6 above/below but not past the fill's end, where the full meter's glow would light up the empty track."""
    return (f'<clipPath id="{cid}"><rect x="{x0 - w - 5}" y="{ytop - 6}" width="{w + 5}" height="{h + 12}">'
            f'<animateTransform attributeName="transform" type="translate" {slide_anim} repeatCount="indefinite"/></rect></clipPath>'
            f'<g clip-path="url(#{cid})"><use href="#{img}" y="{ytop}"/></g>'
            f'<rect x="{x0}" y="{ytop}" width="{w}" height="{h}" fill="url(#track)"/>'
            f'<line x1="{x0}" y1="{ytop + h / 2:g}" x2="{x0 + w}" y2="{ytop + h / 2:g}" stroke="{paint}" stroke-width="{h}" '
            f'stroke-dasharray="{CELL - 1} 1" clip-path="url(#{cid})"/>')


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
    slide = (f'values="{";".join(f"{v} 0" for v in w_vals + [w_vals[0], w_vals[0]])}" '
                            f'keyTimes="{";".join(f"{t:.4f}" for t in pts + [0.9001, 1])}" dur="{T:g}s"')
    starts = [0] + [(j - 0.5) / (n - 1) * 0.9 for j in range(1, n)]
    pcts = "".join(
        f'<text x="{SX + SW - 16}" y="{y}" font-size="13" fill="{AMBER if int(p[:-1]) > 60 else DIM}" text-anchor="end" visibility="hidden">{p}'
        f'<animate attributeName="visibility" {discrete([(starts[j], "visible" if j == i else "hidden") for j in range(n)] + [(0.9001, "visible" if i == 0 else "hidden")])} dur="{T:g}s" repeatCount="indefinite"/></text>'
        for i, p in enumerate(pct_vals)
    )
    return f"""<text x="{SX + 16}" y="{y}" font-size="13" fill="{color_text}">{name}</text>
    {meter_bar(f"g{name}", "mglowimg", MX, y - 11, MW, 12, "url(#meter)", slide)}
    <rect x="{MX}" y="{y - 11}" width="{MW}" height="12" fill="url(#mcrt)"/>
    {pcts}"""


meter_cells = gradient([(0, "#3fb950"), (0.6, "#d29922"), (1, "#f85149")])
mglow_img = glow_image([(MX + c * CELL, 0, CELL - 1, 12, meter_cells((c + 0.5) * CELL / MW)) for c in range(MW // CELL)], 1.6, 0.5,
                       extra=' id="mglowimg"')   # was mglow; meter_bar reveals it up to each fill
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




def bars_path(tops_heights, paint, opacity=1):
    """All columns as one filled path of cell squares, row gaps left open. Cheaper per frame than masking whole bars
    (a mask is an extra offscreen layer every frame) or dashing a stroke (the dashes are rebuilt every frame)."""
    cell = f"h{CW - 1}v{CH - 1}h{1 - CW}z"
    d = "".join(f"M{k * CW} {top}" + f"m0 {CH}".join([cell] * (h // CH)) for k, (top, h) in enumerate(tops_heights))
    return f'<path d="{d}" fill="{paint}"' + (f' fill-opacity="{opacity}"' if opacity < 1 else "") + "/>"




cpu_cols = [(GBOT - max(1, round(idle(k % P) * ROWS)) * CH, max(1, round(idle(k % P) * ROWS)) * CH) for k in range(P + VIS)]
cols = bars_path(cpu_cols, "url(#heat)", 0.9)   # 0.9: the old phosphor dimmed bars by 10%
heat = gradient([(0, "#3fb950"), (0.55, "#d29922"), (1, "#f85149")])
cols_glow = glow_image(cell_rects(cpu_cols, CW, CH, lambda y: heat((GBOT - y) / (ROWS * CH))), 2.2, 0.8, dim=0.9)   # was phosphor
cpu_box = (f'<rect x="{GXB}" y="{BY}" width="{GW}" height="{BH}" rx="6" fill="none" stroke="#30363d"/>'
           f'<rect x="{GXB + 14}" y="{BY - 8}" width="92" height="16" fill="#0d1117"/>'
           f'<text x="{GXB + 20}" y="{BY + 4}" font-size="12" fill="{GREEN}" xml:space="preserve">cpu <tspan fill="{DIM}">idle</tspan></text>'
           f'<rect x="{GXB + GW - 84}" y="{BY - 8}" width="72" height="16" fill="#0d1117"/>'
           f'<text x="{GXB + GW - 16}" y="{BY + 4}" font-size="11" fill="{DIM}" text-anchor="end">99% idle</text>')


def strip(sid, top, heights, color, label, anim, vis=VIS, box_right=GXB + GW):
    """Small second panel under a graph (like an extra indicator pane): short block graph, same x-axis and scroll.
    Its glow is a pre-blurred image (glow.py) clipped a few px taller than the pane (not wider: off-screen scroll
    columns would glow in from the sides)."""
    rows = max(heights)
    h = rows * CH
    w = vis * CW
    cols = [(top + h - heights[k % P] * CH, heights[k % P] * CH) for k in range(P + vis)]
    bars, glow = bars_path(cols, color), glow_image(cell_rects(cols, CW, CH, lambda y: hex_rgb(color)), 1.6, 0.5)   # was mglow
    return f"""<clipPath id="{sid}c"><rect x="{GX}" y="{top}" width="{w}" height="{h}"/></clipPath>
  <clipPath id="{sid}h"><rect x="{GX}" y="{top - 5}" width="{w}" height="{h + 10}"/></clipPath>
  <rect x="{GX}" y="{top}" width="{w}" height="{h}" fill="url(#empty)"/>
  <g clip-path="url(#{sid}h)"><g transform="translate({GX} 0)">
    {anim}
    {glow}
  </g></g>
  <g clip-path="url(#{sid}c)"><g transform="translate({GX} 0)">
    {anim}
    {bars}
  </g></g>
  <rect x="{GX}" y="{top}" width="{w}" height="{h}" fill="url(#crt)"/>
  <text x="{box_right - 6}" y="{top + h - 1}" font-size="8" fill="{DIM}" text-anchor="end">{label}</text>"""

temp_h = [2 + (1 if math.sin(2 * math.pi * 2 * k / P) > 0.3 else 0) for k in range(P)]
strips_svg = strip("temp", GBOT + 6, temp_h, AMBER, "temp", f'<animateTransform attributeName="transform" type="translate" from="{GX} 0" to="{GX - P * CW} 0" dur="12s" repeatCount="indefinite"/>')

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 214" width="900" height="214" role="img" aria-labelledby="t d">
  <title id="t">Signing off</title>
  <desc id="d">A btop-style dashboard while zek-debian the robot sleeps: energy drains, dreams fill, the cpu is idle. The prompt says back on the next shift.</desc>
  <defs>
    {mglow_img}
    <style>text {{ font-family: {FONT}; }}</style>
    <linearGradient id="meter" gradientUnits="userSpaceOnUse" x1="{MX}" y1="0" x2="{MX + MW}" y2="0">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.6" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <!-- meter cells: the empty track is a pattern and the fill a dashed line, so neither needs a cell mask -->
    <pattern id="track" width="{CELL}" height="{CELL}" patternUnits="userSpaceOnUse" x="{MX}">
      <rect width="{CELL - 1}" height="{CELL}" fill="#21262d"/>
    </pattern>
    <pattern id="mcrt" width="{CELL}" height="3" patternUnits="userSpaceOnUse" x="{MX}">
      <rect y="1" width="{CELL - 1}" height="1" fill="#000" opacity="0.32"/>
    </pattern>
    <linearGradient id="heat" gradientUnits="userSpaceOnUse" x1="0" y1="{GBOT}" x2="0" y2="{GBOT - ROWS * CH}">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.55" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <pattern id="empty" width="{CW}" height="{CH}" patternUnits="userSpaceOnUse" x="{GX}" y="{GBOT}">
      <rect width="{CW - 1}" height="{CH - 1}" fill="#161b22"/>
    </pattern>
    <!-- CRT scanlines: two dark lines per cell row, on the row grid so gap rows stay clear; static, no filter -->
    <pattern id="crt" width="{CW}" height="{CH}" patternUnits="userSpaceOnUse" y="{GBOT}">
      <rect y="1" width="{CW}" height="1" fill="#000" opacity="0.32"/><rect y="3" width="{CW}" height="1" fill="#000" opacity="0.32"/>
    </pattern>
    <linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#7ee787" stop-opacity="0"/><stop offset="0.85" stop-color="#7ee787" stop-opacity="0.08"/><stop offset="1" stop-color="#7ee787" stop-opacity="0.22"/>
    </linearGradient>
    <clipPath id="gclip"><rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}"/></clipPath>
    <!-- glow clip: taller than gclip so glow spills above/below, same width so off-screen columns stay dark -->
    <clipPath id="gglow"><rect x="{GX}" y="{GBOT - ROWS * CH - 8}" width="{VIS * CW}" height="{ROWS * CH + 16}"/></clipPath>
    <!-- typing reveal and cursor move by translate, not width/x: Chrome repaints every frame while a width/x animation runs -->
    <clipPath id="say"><rect x="{176 - 232}" y="170" width="232" height="26">
      <animateTransform attributeName="transform" type="translate" values="0 0;0 0;232 0;232 0;0 0" keyTimes="0;0.08;0.5;0.94;1" dur="10s" repeatCount="indefinite"/>
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

  {cpu_box}
  <rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}" fill="url(#empty)"/>
  <g clip-path="url(#gglow)">
    <g transform="translate({GX} 0)">
      <animateTransform attributeName="transform" type="translate" from="{GX} 0" to="{GX - P * CW} 0" dur="12s" repeatCount="indefinite"/>
      {cols_glow}
    </g>
  </g>
  <g clip-path="url(#gclip)">
    <g transform="translate({GX} 0)">
      <animateTransform attributeName="transform" type="translate" from="{GX} 0" to="{GX - P * CW} 0" dur="12s" repeatCount="indefinite"/>
      {cols}
    </g>
  </g>
  <rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}" fill="url(#crt)"/>
  <clipPath id="sweepclip"><rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}"/><rect x="{GX}" y="{GBOT + 6}" width="{VIS * CW}" height="{max(temp_h) * CH}"/></clipPath>
  {strips_svg}
  <!-- CRT sweep: faint band rolling down the panes; unfiltered, so moving it never re-runs a blur -->
  <g clip-path="url(#sweepclip)"><rect x="{GX}" y="0" width="{VIS * CW}" height="40" fill="url(#sweep)">
    <animateTransform attributeName="transform" type="translate" from="0 {GBOT - ROWS * CH - 40}" to="0 {GBOT + 6 + max(temp_h) * CH}" dur="5s" repeatCount="indefinite"/>
  </rect></g>
  <text x="24" y="190" font-size="14" xml:space="preserve"><tspan fill="{GREEN}">zek@zek-debian</tspan><tspan fill="{DIM}">:</tspan><tspan fill="{BLUE}">~</tspan><tspan fill="{DIM}">$ </tspan><tspan fill="{FG}" clip-path="url(#say)">echo "back on the next shift"</tspan></text>
  <rect x="176" y="177" width="9" height="16" fill="{GREEN}">
    <animateTransform attributeName="transform" type="translate" values="0 0;0 0;224 0;224 0;0 0" keyTimes="0;0.08;0.5;0.94;1" dur="10s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/>
  </rect>
</svg>
"""

out = Path(__file__).resolve().parent.parent / "assets" / "footer.svg"
svg = quantize(svg)   # all animations on one 24 fps clock, so the image repaints at most 24x a second
out.write_text(svg)
print(f"wrote {out} ({len(svg)} bytes)")
