#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate docs/assets/speed-progress.svg - dark-card lollipop/bars.

Design: GitHub-dark card, gradient capsules, glowing end dots, axis break
for the official reference. System font stack only (no external assets).
Pure stdlib. Rerun to regenerate.
"""
import os

W, H = 960, 566
X0, XMAX, VMAX = 316, 500, 5.4     # track origin px, scale px, minutes
TRACK_Y, ROW_H, TOP = 0, 66, 128   # per-row geometry
BAR_H = 13

INK, SUB, FAINT = "#e6edf3", "#8b949e", "#6e7681"
BG, CARD, TRACK = "#ffffff", "#0d1117", "#161b22"
STROKE = "#30363d"

rows = [
    dict(main="官方教程路线",  sub="参照 · 未吃到 cu130 反量化红利",
         color=None, brk=True, tag="20–30 分钟", tagc=SUB),
    dict(main="不加 T8",      sub="成片标准 · 可复现", mins=4.7, secs="280 s",
         g=("c4", "c1"), valc=INK, tag="基线", tagc=SUB),
    dict(main="T8 · 默认参数", sub="4 步路线 0 次命中", mins=4.8, secs="290 s",
         g=("r2", "r1"), valc="#f85149", tag="+4% 更慢", tagc="#f85149"),
    dict(main="T8 · 阈值 0.45", sub="命中 1/4 步", mins=3.7, secs="220 s",
         g=("b4", "b1"), valc=INK, tag="−21%", tagc=SUB),
    dict(main="T8 · 阈值 1.0", sub="草稿档 · 同 seed 不可复现", mins=2.7, secs="160 s",
         g=("g2", "g1"), valc="#3fb950", tag="⚡ −43%", tagc="#3fb950"),
    dict(main="PDD 8 步+T8", sub="极速草稿 · 蒸馏画质 · 命中 6/8", mins=3.5, secs="210 s",
         g=("p2", "p1"), valc="#a371f7", tag="⚡ 画质+速度双冠", tagc="#a371f7"),
]

def px(v):
    return X0 + v / VMAX * XMAX

svg = []
A = svg.append
A('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
  'font-family="ui-sans-serif,-apple-system,Segoe UI,Roboto,PingFang SC,'
  'Microsoft YaHei,Noto Sans SC,sans-serif">' % (W, H))
A('<defs>')
A('<linearGradient id="c1" x1="0" y1="0" x2="1" y2="0">'
  '<stop offset="0" stop-color="#1f6feb"/><stop offset="1" stop-color="#58a6ff"/></linearGradient>')
A('<linearGradient id="c4" x1="0" y1="0" x2="1" y2="0">'
  '<stop offset="0" stop-color="#388bfd55"/><stop offset="1" stop-color="#58a6ff"/></linearGradient>')
A('<linearGradient id="p1" x1="0" y1="0" x2="1" y2="0">'
  '<stop offset="0" stop-color="#8957e5"/><stop offset="1" stop-color="#a371f7"/></linearGradient>')
A('<linearGradient id="p2" x1="0" y1="0" x2="1" y2="0">'
  '<stop offset="0" stop-color="#8957e5"/><stop offset="1" stop-color="#d2a8ff"/></linearGradient>')
A('<linearGradient id="g1" x1="0" y1="0" x2="1" y2="0">'
  '<stop offset="0" stop-color="#2ea043"/><stop offset="1" stop-color="#56d364"/></linearGradient>')
A('<linearGradient id="g2" x1="0" y1="0" x2="1" y2="0">'
  '<stop offset="0" stop-color="#2ea043"/><stop offset="1" stop-color="#7ee787"/></linearGradient>')
A('<linearGradient id="r1" x1="0" y1="0" x2="1" y2="0">'
  '<stop offset="0" stop-color="#da3633"/><stop offset="1" stop-color="#f85149"/></linearGradient>')
A('<linearGradient id="r2" x1="0" y1="0" x2="1" y2="0">'
  '<stop offset="0" stop-color="#da363366"/><stop offset="1" stop-color="#f85149"/></linearGradient>')
A('</defs>')
A('<rect x="8" y="8" width="%d" height="%d" rx="16" fill="%s" stroke="%s" '
  'stroke-width="1"/>' % (W - 16, H - 16, CARD, STROKE))

# header
A('<text x="36" y="56" font-size="21" font-weight="700" fill="%s">'
  '一条 5 秒视频，本地要生成多久？</text>' % INK)
A('<text x="36" y="80" font-size="12.5" fill="%s">'
  'MiniMax H3 · 640×352 · 124 帧 · 2080Ti 22G 实测 · 同条件同 seed 对照</text>' % SUB)
A('<rect x="742" y="38" width="182" height="34" rx="17" fill="#2ea04326" '
  'stroke="#2ea04366" stroke-width="1"/>')
A('<text x="833" y="60" font-size="14" font-weight="700" fill="#3fb950" '
  'text-anchor="middle">⚡ 快 5–11 倍</text>')

# axis gridlines + labels
for v in range(0, 6):
    gx = px(v)
    A('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#21262d" '
      'stroke-width="1" stroke-dasharray="2 5"/>' % (gx, TOP - 14, gx, TOP + 6 * ROW_H - 26))
    A('<text x="%.1f" y="%d" font-size="11" fill="%s" text-anchor="middle">%d</text>'
      % (gx, TOP + 6 * ROW_H - 8, FAINT, v))
A('<text x="%.1f" y="%d" font-size="11" fill="%s">分钟/镜</text>'
  % (px(5) + 16, TOP + 6 * ROW_H - 8, FAINT))

for i, r in enumerate(rows):
    y = TOP + i * ROW_H
    cy = y + TRACK_Y + 22
    # labels (right aligned, two lines)
    A('<text x="%d" y="%.0f" font-size="13.5" font-weight="600" fill="%s" '
      'text-anchor="end">%s</text>' % (X0 - 18, y + 18, INK, r["main"]))
    A('<text x="%d" y="%.0f" font-size="10.5" fill="%s" text-anchor="end">%s</text>'
      % (X0 - 18, y + 33, SUB, r["sub"]))
    # track
    A('<rect x="%d" y="%.0f" width="%d" height="%d" rx="%d" fill="%s"/>'
      % (X0, cy - BAR_H / 2, XMAX, BAR_H, BAR_H // 2, TRACK))
    if r.get("brk"):
        # reference: run to ~85%, break mark, faint tail, value text at right
        bw = int(XMAX * 0.82)
        A('<rect x="%d" y="%.0f" width="%d" height="%d" rx="%d" fill="#484f58"/>'
          % (X0, cy - BAR_H / 2, bw, BAR_H, BAR_H // 2))
        b1 = X0 + bw
        A('<path d="M%d %.0f l10 %d M%d %.0f l10 %d" stroke="%s" stroke-width="2.5" '
          'fill="none"/>' % (b1, cy - 13, 26, b1 + 9, cy - 13, 26, CARD))
        A('<rect x="%d" y="%.0f" width="%d" height="%d" rx="%d" fill="#484f58" '
          'opacity="0.35"/>' % (b1 + 26, cy - BAR_H / 2, X0 + XMAX - (b1 + 26), BAR_H, BAR_H // 2))
        A('<circle cx="%.1f" cy="%.0f" r="11" fill="#8b949e" opacity="0.18"/>'
          % (X0 + bw, cy))
        A('<circle cx="%.1f" cy="%.0f" r="5.5" fill="#8b949e"/>' % (X0 + bw, cy))
        A('<text x="%.1f" y="%.0f" font-size="15.5" font-weight="700" fill="%s">%s</text>'
          % (X0 + XMAX + 12, cy + 5, r["tagc"], r["tag"]))
        continue
    bw = px(r["mins"]) - X0
    A('<rect x="%d" y="%.0f" width="%.1f" height="%d" rx="%d" fill="url(#%s)"/>'
      % (X0, cy - BAR_H / 2, bw, BAR_H, BAR_H // 2, r["g"][1]))
    ex = px(r["mins"])
    # glowing end dot (halo + core)
    A('<circle cx="%.1f" cy="%.0f" r="12" fill="%s" opacity="0.16"/>'
      % (ex, cy, r["valc"]))
    A('<circle cx="%.1f" cy="%.0f" r="6" fill="%s" stroke="%s" stroke-width="2"/>'
      % (ex, cy, r["valc"], CARD))
    # value block right of dot
    A('<text x="%.1f" y="%.0f" font-size="15.5" font-weight="700" fill="%s">%.1f 分钟</text>'
      % (ex + 16, cy - 2, r["valc"], r["mins"]))
    A('<text x="%.1f" y="%.0f" font-size="10.5" fill="%s">%s · %s</text>'
      % (ex + 16, cy + 14, SUB, r["secs"], r["tag"]))

# footer
A('<line x1="36" y1="%d" x2="%d" y2="%d" stroke="#21262d" stroke-width="1"/>'
  % (H - 96, W - 36, H - 96))
A('<text x="36" y="%d" font-size="11" fill="%s">'
  '数据：2026-09-01 同晚同 seed 热跑实测；T8 = MiniMax 官方 BlockCache，默认参数在 4 步路线 0 命中（负优化）。</text>'
  % (H - 74, FAINT))
A('<text x="36" y="%d" font-size="11" fill="%s">'
  '激进档代价：同 seed 不可复现 → 只用于草稿/选镜头；成片请用无 T8 基线。详见 docs/08。</text>'
  % (H - 56, FAINT))
A('</svg>')

out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..",
                                    "docs", "assets", "speed-progress.svg"))
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print("written:", out)
