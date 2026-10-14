#!/usr/bin/env python3
"""Generate assets/training.svg: ten mini terminals printing production-style logs (with pauses) next to a scrolling btop-style loss graph."""
import math
import random
from pathlib import Path

FG, DIM, GREEN, AMBER, BLUE, RED = "#c9d1d9", "#6e7681", "#3fb950", "#d29922", "#58a6ff", "#f85149"
FONT = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'
LEVEL_COLOR = {"INFO": GREEN, "WARN": AMBER, "ERROR": RED, "DEBUG": BLUE}

# (service, start time, [(level, message), ...]) -- messages are at most 31 chars
SERVICES = [
    ("api-gateway", (11, 42, 7), [
        ("INFO", "GET /v1/users/42 200 12ms"), ("INFO", "POST /v1/events 201 8ms"), ("INFO", "GET /v1/me 200 4ms"),
        ("WARN", "rate limit 80% client=a91f"), ("INFO", "GET /healthz 200 1ms"), ("INFO", "GET /v1/orders 200 31ms"),
        ("ERROR", "upstream timeout 5002ms"), ("INFO", "retry 1/3 ok 118ms"), ("INFO", "GET /v1/users 200 9ms"),
        ("INFO", "GET /healthz 200 1ms")]),
    ("auth-svc", (11, 42, 9), [
        ("INFO", "login ok user=ezekiel"), ("INFO", "token issued ttl=3600s"), ("DEBUG", "jwks cache hit"),
        ("INFO", "refresh ok user=u_1042"), ("WARN", "bad password user=u_77"), ("INFO", "login ok user=u_318"),
        ("INFO", "session revoked sid=4f2a"), ("DEBUG", "jwks cache hit"), ("INFO", "login ok user=u_92")]),
    ("trainer", (11, 41, 55), [
        ("INFO", "epoch 01/50 loss=0.912"), ("INFO", "epoch 02/50 loss=0.644"), ("INFO", "checkpoint saved step=500"),
        ("INFO", "epoch 03/50 loss=0.381"), ("WARN", "grad norm 4.2 clipped"), ("INFO", "epoch 04/50 loss=0.214"),
        ("INFO", "eval acc=0.931"), ("INFO", "epoch 05/50 loss=0.158"), ("INFO", "checkpoint saved step=1000")]),
    ("test-runner", (11, 42, 1), [
        ("INFO", "running 42 tests"), ("INFO", "auth_test ........ ok"), ("INFO", "api_test ......... ok"),
        ("ERROR", "db_test FAILED 1 of 9"), ("INFO", "retrying db_test"), ("INFO", "db_test .......... ok"),
        ("INFO", "embed_test ....... ok"), ("INFO", "42 passed 0 failed 6.1s")]),
    ("embedder", (11, 42, 3), [
        ("INFO", "chunk doc=001 tokens=512"), ("INFO", "embed batch=32 41ms"), ("INFO", "chunk doc=002 tokens=498"),
        ("INFO", "embed batch=32 39ms"), ("WARN", "doc=003 truncated 8192"), ("INFO", "upsert vectors n=96"),
        ("INFO", "index refresh ok 120ms"), ("INFO", "chunk doc=004 tokens=511")]),
    ("git-sync", (11, 41, 48), [
        ("INFO", "fetch origin main"), ("INFO", "merge fast-forward 3 commits"), ("INFO", "push origin main"),
        ("INFO", "tag v1.4.2 created"), ("WARN", "stale branch fix/typo"), ("INFO", "gc --auto done"),
        ("INFO", "fetch origin main"), ("INFO", "up to date")]),
    ("postgres", (11, 42, 12), [
        ("INFO", "checkpoint starting: time"), ("INFO", "checkpoint complete 4.1s"), ("DEBUG", "autovacuum users 0.3s"),
        ("INFO", "conn accepted 10.0.0.12"), ("WARN", "slow query 842ms orders"), ("INFO", "conn closed 10.0.0.12"),
        ("INFO", "vacuum analyze events ok"), ("INFO", "checkpoint starting: time")]),
    ("deployer", (11, 41, 30), [
        ("INFO", "build image sha=9fd2c1a"), ("INFO", "push registry 34MB"), ("INFO", "rollout api-gw 1/3 ready"),
        ("INFO", "rollout api-gw 3/3 ready"), ("INFO", "health check 200 ok"), ("WARN", "old pod draining 30s"),
        ("INFO", "traffic shifted 100%"), ("INFO", "deploy complete 48s")]),
    ("linter", (11, 42, 5), [
        ("INFO", "lint src/*.c 0 issues"), ("INFO", "lint src/*.zig 0 issues"), ("WARN", "src/net.c:88 unused var"),
        ("INFO", "lint app/*.py 0 issues"), ("INFO", "lint web/*.js 0 issues"), ("WARN", "src/db.c:41 shadow decl"),
        ("INFO", "autofix applied 2 files"), ("INFO", "lint clean")]),
    ("agent", (11, 42, 10), [
        ("INFO", "plan: 3 steps"), ("INFO", 'tool grep "TODO" 12 hits'), ("INFO", "tool edit src/brain.py"),
        ("INFO", "observe tests 41 passed"), ("WARN", "1 flaky test, retrying"), ("INFO", "tool run pytest"),
        ("INFO", "observe tests 42 passed"), ("INFO", "reflect: goal met, done")]),
]

# mini terminal geometry
MW, MH, GAPX, GAPY = 262, 50, 8, 6
X0, Y0 = 24, 56
FS, STRIDE, SHOWN = 9, 11, 3          # font size, line pitch, visible lines
BODY_Y = 16                           # body top inside a mini
rng = random.Random(7)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def holds(n):
    """Seconds each log state stays on screen: quick bursts, with the odd long pause."""
    out = []
    for _ in range(n):
        out.append(round(rng.choice([2.2, 2.8, 3.4]) if rng.random() < 0.28 else rng.choice([0.45, 0.6, 0.8, 1.0]), 2))
    return out


defs, minis = [], []
for i, (name, (hh, mm, ss), lines) in enumerate(SERVICES):
    ox = X0 + (i % 2) * (MW + GAPX)
    oy = Y0 + (i // 2) * (MH + GAPY)
    n = len(lines)
    hs = holds(n)
    t = hh * 3600 + mm * 60 + ss
    rows = []
    for k, (lvl, msg) in enumerate(lines):
        ts = f"{t // 3600 % 24:02d}:{t // 60 % 60:02d}:{t % 60:02d}"
        t += max(1, round(hs[k] * 2.5))
        rows.append(f'<text x="0" y="{k * STRIDE}" xml:space="preserve"><tspan fill="{DIM}">{ts}</tspan> '
                    f'<tspan fill="{LEVEL_COLOR[lvl]}">{lvl:<5}</tspan> <tspan fill="{FG}">{esc(msg)}</tspan></text>')
    defs.append(f'<g id="b{i}" font-size="{FS}">{"".join(rows)}</g>')
    total = sum(hs)
    cum, kts = 0.0, []
    for h in hs:
        kts.append(f"{cum / total:.4f}")
        cum += h
    vals = ";".join(f"0 {-k * STRIDE}" for k in range(n))
    dot = [GREEN, GREEN, GREEN, AMBER, GREEN][i % 5]
    minis.append(f"""<g>
    <rect x="{ox + .5}" y="{oy + .5}" width="{MW - 1}" height="{MH - 1}" rx="4" fill="#0d1117" stroke="#30363d"/>
    <path d="M{ox + 1} {oy + 14}V{oy + 5}a4 4 0 0 1 4-4h{MW - 10}a4 4 0 0 1 4 4V{oy + 14}z" fill="#161b22"/>
    <text x="{ox + 8}" y="{oy + 10.5}" font-size="9" fill="{DIM}">{name}</text>
    <circle cx="{ox + MW - 10}" cy="{oy + 7.5}" r="2.5" fill="{dot}"><animate attributeName="opacity" values="1;0.25;1" dur="{1.2 + (i % 4) * 0.35:g}s" repeatCount="indefinite"/></circle>
    <svg x="{ox + 8}" y="{oy + BODY_Y}" width="{MW - 16}" height="{SHOWN * STRIDE}" overflow="hidden">
      <g transform="translate(0 {FS})"><g>
        <animateTransform attributeName="transform" type="translate" calcMode="discrete" values="{vals}" keyTimes="{";".join(kts)}" dur="{total:.2f}s" repeatCount="indefinite"/>
        <use href="#b{i}"/><use href="#b{i}" y="{n * STRIDE}"/>
      </g></g>
    </svg>
  </g>""")
defs_svg = "\n    ".join(defs)
minis_svg = "\n  ".join(minis)

# --- loss graph (right): btop-style block graph that scrolls forever ---
FX, FY, FW, FH = 572, 56, 304, 274       # frame
CW, CH, ROWS = 6, 6, 36                   # cell width/height, rows
VIS = 44                                  # visible columns
P = 64                                    # columns in one seamless period
GX, GBOT = FX + 12, FY + 30 + ROWS * CH   # graph left, bottom y

def level(k):
    """Periodic 'loss' signal in 0..1 (integer harmonics, so the loop is seamless)."""
    w = 2 * math.pi * k / P
    v = 0.42 + 0.22 * math.sin(2 * w + 0.6) + 0.12 * math.sin(5 * w + 1.9) + 0.07 * math.sin(11 * w) + 0.05 * math.sin(17 * w + 0.3)
    return min(max(v, 0.05), 1.0)

cols = []
for k in range(P + VIS):
    h = max(1, round(level(k % P) * ROWS)) * CH
    cols.append(f'<rect x="{k * CW}" y="{GBOT - h}" width="{CW - 1}" height="{h}"/>')
cols_svg = "".join(cols)

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

scroll = scroll_attrs(11, GX, CW, P)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 350" width="900" height="350" role="img" aria-labelledby="t d">
  <title id="t">Training run</title>
  <desc id="d">Ten small terminals print production-style service logs with pauses between bursts, next to a scrolling btop-style loss graph.</desc>
  <style>text {{ font-family: {FONT}; }}</style>
  <defs>
    {defs_svg}
  </defs>

  <rect width="900" height="350" rx="10" fill="#0d1117"/>
  <text x="24" y="36" font-size="14" xml:space="preserve"><tspan fill="{GREEN}">zek@zek-debian</tspan><tspan fill="{DIM}">:</tspan><tspan fill="{BLUE}">~</tspan><tspan fill="{DIM}">$ </tspan><tspan fill="{FG}">tmux attach -t night-shift</tspan></text>

  {minis_svg}

  <!-- loss graph -->
  <defs>
    <linearGradient id="heat" gradientUnits="userSpaceOnUse" x1="0" y1="{GBOT}" x2="0" y2="{GBOT - ROWS * CH}">
      <stop offset="0" stop-color="#3fb950"/><stop offset="0.55" stop-color="#d29922"/><stop offset="1" stop-color="#f85149"/>
    </linearGradient>
    <pattern id="rowgap" width="{CW}" height="{CH}" patternUnits="userSpaceOnUse" y="{GBOT}">
      <rect width="{CW}" height="{CH}" fill="#fff"/><rect y="{CH - 1}" width="{CW}" height="1" fill="#000"/>
    </pattern>
    <mask id="cells" maskUnits="userSpaceOnUse" x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}">
      <rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}" fill="url(#rowgap)"/>
    </mask>
    <filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2"/></filter>
    <clipPath id="gclip"><rect x="{GX}" y="{GBOT - ROWS * CH}" width="{VIS * CW}" height="{ROWS * CH}"/></clipPath>
  </defs>
  <rect x="{FX}" y="{FY}" width="{FW}" height="{FH}" rx="6" fill="none" stroke="#30363d"/>
  <rect x="{FX + 14}" y="{FY - 8}" width="86" height="16" fill="#0d1117"/>
  <text x="{FX + 20}" y="{FY + 4}" font-size="12" fill="{GREEN}" xml:space="preserve">loss <tspan fill="{DIM}">/ step</tspan></text>
  <rect x="{FX + FW - 62}" y="{FY - 8}" width="52" height="16" fill="#0d1117"/>
  <circle cx="{FX + FW - 52}" cy="{FY}" r="4" fill="{GREEN}" filter="url(#glow)" opacity="0.5">
    <animate attributeName="r" values="3;5.5;3" dur="1.8s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.7;0.15;0.7" dur="1.8s" repeatCount="indefinite"/>
  </circle>
  <circle cx="{FX + FW - 52}" cy="{FY}" r="2.5" fill="{GREEN}"/>
  <text x="{FX + FW - 14}" y="{FY + 4}" font-size="11" fill="{GREEN}" text-anchor="end">live</text>
  <g mask="url(#cells)">
    <g clip-path="url(#gclip)">
      <g transform="translate({GX} 0)" fill="url(#heat)">
        <animateTransform attributeName="transform" type="translate" {scroll} repeatCount="indefinite"/>
        {cols_svg}
      </g>
    </g>
  </g>
  <text x="{FX + FW - 8}" y="{GBOT - ROWS * CH + 8}" font-size="10" fill="{DIM}" text-anchor="end">1.0</text>
  <text x="{FX + FW - 8}" y="{GBOT}" font-size="10" fill="{DIM}" text-anchor="end">0.0</text>
  <text x="{GX}" y="{GBOT + 16}" font-size="11" fill="{DIM}">step &#8594;</text>
</svg>
"""

out = Path(__file__).resolve().parent.parent / "assets" / "training.svg"
out.write_text(svg)
print(f"wrote {out} ({len(svg)} bytes)")
