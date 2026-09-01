#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate docs/assets/speed-progress.svg - speed optimization timeline.

Panel A: T8 parameter sweep, same-night A/B (seed 3013, warm, 2080Ti 22G)
Panel B: cumulative speedup across the whole project

Pure stdlib on purpose (repo has zero deps). Rerun to regenerate.
"""
import os

W, H = 960, 470
# panel geometry: two side-by-side plot areas
PA = dict(x=70, y=90, w=380, h=280)   # panel A plot box
PB = dict(x=560, y=90, w=340, h=280)  # panel B plot box

ACCENT = "#2563eb"   # main line
WARN = "#dc2626"     # negative-optimization point
OK = "#059669"       # best result
GRID = "#e5e7eb"
TXT = "#374151"
SUB = "#9ca3af"

def sx(panel, i, n):
    return panel["x"] + panel["w"] * (i + 0.5) / n

def sy(panel, v, vmax):
    return panel["y"] + panel["h"] * (1 - v / vmax)

def fmt_pct(v):
    return ("+" if v > 0 else "") + "%.0f%%" % v

svg = []
svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
           'font-family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,'
           'PingFang SC,Microsoft YaHei,sans-serif">' % (W, H))
svg.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))
svg.append('<text x="30" y="40" font-size="19" font-weight="700" fill="#111827">'
           '2080Ti 22G 跑 MiniMax H3：提速优化演进</text>')
svg.append('<text x="30" y="62" font-size="12" fill="%s">'
           '640×352 · 124 帧 · W4A8 · 4 步 Turbo · 原生音频 ｜ 同 seed 对照实测，非纸面推演'
           '</text>' % SUB)

# ---------------- Panel A: same-night T8 parameter sweep -----------------
svg.append('<text x="%d" y="%d" font-size="14" font-weight="600" fill="%s">'
           'A · T8 参数扫描（同晚 A/B，seed 3013 热跑）</text>'
           % (PA["x"] - 40, PA["y"] - 14, TXT))
a_pts = [
    ("无 T8\n(基线)", 280, ACCENT, ""),
    ("T8 默认\n0.12", 290, WARN, fmt_pct((290 - 280) / 280 * 100)),
    ("T8\n0.45", 220, ACCENT, fmt_pct((220 - 280) / 280 * 100)),
    ("T8\n1.0 激进", 160, OK, fmt_pct((160 - 280) / 280 * 100)),
]
A_MAX = 320
# gridlines + y labels (seconds)
for gv in range(0, 321, 80):
    gy = sy(PA, gv, A_MAX)
    svg.append('<line x1="%d" y1="%.0f" x2="%d" y2="%.0f" stroke="%s" '
               'stroke-width="1"/>' % (PA["x"], gy, PA["x"] + PA["w"], gy, GRID))
    svg.append('<text x="%d" y="%.0f" font-size="11" fill="%s" '
               'text-anchor="end">%ds</text>' % (PA["x"] - 8, gy + 4, SUB, gv))
path = []
for i, (_, v, _, _) in enumerate(a_pts):
    path.append("%s%.1f %.1f" % ("M" if i == 0 else "L",
                                 sx(PA, i, len(a_pts)), sy(PA, v, A_MAX)))
svg.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.5" '
           'stroke-linejoin="round"/>' % (" ".join(path), ACCENT))
for i, (label, v, color, pct) in enumerate(a_pts):
    px, py = sx(PA, i, len(a_pts)), sy(PA, v, A_MAX)
    svg.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" '
               'stroke="#fff" stroke-width="2"/>' % (px, py, color))
    up = v > 280
    svg.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="700" '
               'fill="%s" text-anchor="middle">%d s</text>' % (px, py - 12, color, v))
    if pct:
        svg.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" '
                   'text-anchor="middle">%s</text>'
                   % (px, py - 27, "#dc2626" if up else OK, pct))
    for j, ln in enumerate(label.split("\n")):
        svg.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" '
                   'text-anchor="middle">%s</text>'
                   % (px, PA["y"] + PA["h"] + 18 + j * 14, TXT, ln))
svg.append('<text x="%d" y="%d" font-size="11" fill="%s">cache 命中：0/4 → 0/4 → 1/4 → 2/4（每命中省约 60s）</text>'
           % (PA["x"] - 40, PA["y"] + PA["h"] + 64, SUB))

# ---------------- Panel B: cumulative evolution ---------------------------
svg.append('<text x="%d" y="%d" font-size="14" font-weight="600" fill="%s">'
           'B · 累计提速演进（跨配置）</text>' % (PB["x"] - 30, PB["y"] - 14, TXT))
b_pts = [
    ("官方手册参照\n(未吃到 cu130)", 25.0, SUB, "20-30 min"),
    ("cu130 红利\nW4A8+Turbo 基线", 5.7, ACCENT, "5.7 min"),
    ("+ T8 激进档\n(草稿可用)", 2.7, OK, "2.7 min"),
]
B_MAX = 28
for gv in range(0, 29, 7):
    gy = sy(PB, gv, B_MAX)
    svg.append('<line x1="%d" y1="%.0f" x2="%d" y2="%.0f" stroke="%s" '
               'stroke-width="1"/>' % (PB["x"], gy, PB["x"] + PB["w"], gy, GRID))
    svg.append('<text x="%d" y="%.0f" font-size="11" fill="%s" '
               'text-anchor="end">%dmin</text>' % (PB["x"] - 8, gy + 4, SUB, gv))
path = []
for i, (_, v, _, _) in enumerate(b_pts):
    path.append("%s%.1f %.1f" % ("M" if i == 0 else "L",
                                 sx(PB, i, len(b_pts)), sy(PB, v, B_MAX)))
svg.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.5" '
           'stroke-linejoin="round" opacity="0.55"/>' % (" ".join(path), SUB))
path2 = path[1:]
svg.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.5" '
           'stroke-linejoin="round"/>' % (" ".join(path2), ACCENT))
for i, (label, v, color, tag) in enumerate(b_pts):
    px, py = sx(PB, i, len(b_pts)), sy(PB, v, B_MAX)
    svg.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" '
               'stroke="#fff" stroke-width="2"/>' % (px, py, color))
    svg.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="700" '
               'fill="%s" text-anchor="middle">%s</text>'
               % (px, py - 12, "#111827" if i == 0 else color, tag))
    for j, ln in enumerate(label.split("\n")):
        svg.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" '
                   'text-anchor="middle">%s</text>'
                   % (px, PB["y"] + PB["h"] + 18 + j * 14, TXT, ln))
# multiplier brackets between points
svg.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="700" fill="%s" '
           'text-anchor="middle">↓ 4.4×</text>'
           % (sx(PB, 0, 3) + (sx(PB, 1, 3) - sx(PB, 0, 3)) / 2,
              sy(PB, 25.0, B_MAX) + 26, OK))
svg.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="700" fill="%s" '
           'text-anchor="middle">↓ 2.1×</text>'
           % (sx(PB, 1, 3) + (sx(PB, 2, 3) - sx(PB, 1, 3)) / 2,
              sy(PB, 5.7, B_MAX) + 26, OK))
svg.append('<text x="%d" y="%d" font-size="11" fill="%s">相对官方参照累计 ≈ 9.3×；T8 激进档代价：同 seed 不可复现（详见 docs/08）</text>'
           % (PB["x"] - 30, PB["y"] + PB["h"] + 64, SUB))

svg.append('<text x="30" y="%d" font-size="11" fill="%s">'
           '数据：2026-08-31 基线（340s 实测口径 5.7 min）与 2026-09-01 同晚 A/B（control 280s）。'
           '环境：ComfyUI v0.33.1 / torch 2.9.1+cu130 / W4A8 mixed + fl2v Turbo 4step。'
           '</text>' % (H - 26, SUB))
svg.append("</svg>")

out = os.path.join(os.path.dirname(__file__), "..", "docs", "assets",
                   "speed-progress.svg")
out = os.path.normpath(out)
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print("written:", out)
