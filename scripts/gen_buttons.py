#!/usr/bin/env python3
"""Generate the tiny terminal-style link buttons in assets/btn-*.svg."""
from pathlib import Path

FONT = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'
BUTTONS = [("linkedin", "in", "#58a6ff"), ("stackoverflow", "so", "#d29922")]
CHAR_W, PAD, H = 6.6, 10, 22

for name, tag, color in BUTTONS:
    label = f"[{tag}] {name}"
    w = round(len(label) * CHAR_W + 2 * PAD)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" width="{w}" height="{H}" role="img" aria-label="{name}">
  <title>{name}</title>
  <style>text {{ font-family: {FONT}; }}</style>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{H - 1}" rx="5" fill="#0d1117" stroke="#30363d"/>
  <text x="{PAD}" y="15" font-size="11" xml:space="preserve"><tspan fill="{color}">[{tag}]</tspan><tspan fill="#c9d1d9"> {name}</tspan></text>
</svg>
"""
    out = Path(__file__).resolve().parent.parent / "assets" / f"btn-{name}.svg"
    out.write_text(svg)
    print(f"wrote {out} ({w}x{H})")
