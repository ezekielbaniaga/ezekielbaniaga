#!/usr/bin/env python3
"""Bake scripts/preview.html: a self-contained page that mimics the README on GitHub (dark theme).
Run after every change to README.md or assets/*.svg."""
import base64
import html
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
md = (root / "README.md").read_text()


def inline(m):
    src = m.group(1)
    data = base64.b64encode((root / src).read_bytes()).decode()
    return f'src="data:image/svg+xml;base64,{data}"'


body = re.sub(r'src="(assets/[^"]+\.svg)"', inline, md)
# minimal markdown: `code` lines, ## / ### headings; raw HTML passes through
out = []
for line in body.splitlines():
    if line.startswith("### "):
        out.append(f"<h3>{html.escape(line[4:])}</h3>")
    elif line.startswith("## "):
        out.append(f"<h2>{html.escape(line[3:])}</h2>")
    elif line.startswith("`") and line.endswith("`"):
        out.append(f"<p><code>{html.escape(line.strip('`'))}</code></p>")
    else:
        out.append(line)

page = f"""<!doctype html>
<meta charset="utf-8">
<title>README preview</title>
<style>
  :root {{ --bg: #0d1117; --fg: #e6edf3; --code: #6e768166; }}
  :root[data-theme="light"] {{ --bg: #ffffff; --fg: #1f2328; --code: #818b981f; }}
  body {{ margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.5 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }}
  main {{ width: 838px; margin: 0 auto; padding: 32px; }}   /* the README column on github.com profiles (measured) */
  code {{ background: var(--code); padding: .2em .4em; border-radius: 6px; font-size: 85%; }}
  img {{ max-width: 100%; }}
  #theme {{ position: fixed; top: 12px; right: 12px; font: 12px ui-monospace, monospace; padding: 4px 10px;
           border-radius: 6px; border: 1px solid #8b949e; background: var(--bg); color: var(--fg); cursor: pointer; }}
</style>
<button id="theme">theme: dark</button>
<main>
{chr(10).join(out)}
</main>
<script>
  const root = document.documentElement, btn = document.getElementById("theme");
  function set(t) {{ root.dataset.theme = t; btn.textContent = "theme: " + t; }}
  set(location.hash === "#light" ? "light" : location.hash === "#dark" ? "dark"
      : matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  btn.onclick = () => set(root.dataset.theme === "light" ? "dark" : "light");
</script>
"""
(root / "scripts" / "preview.html").write_text(page)
print("baked scripts/preview.html")
