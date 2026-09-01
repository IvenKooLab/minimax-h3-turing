#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate docs/assets/speed-progress.svg - one simple question:

"一条 5 秒视频，本地要生成多久？" - horizontal bars, same-night A/B data.
Row 0 is the official-tutorial reference, drawn with an axis break so the
optimized bars stay readable. Pure stdlib on purpose. Rerun to regenerate.
"""
import os

W, H = 960, 470
X0, XMAX, VMAX = 300, 500, 5.2   # bar origin px, full-scale px, minutes
BAR_H, ROW_H, Y0 = 36, 56, 124

BLUE, RED, MID, GREEN = "#2563eb", "#dc2626", "#60a5fa", "#059669"
GREY, GRID, TXT, SUB = "#6b7280", "#e5e7eb", "#374151", "#9ca3af"

rows = [
    dict(label="官方教程路线（参照）", note="未吃到 cu130 反量化红利",
         color=GREY, value="20–30 分钟", brk=True),
    dict(label="不加 T8（成片标准）", mins=4.7, secs="280 s", note="✓ 可复现",
         color=BLUE),
    dict(label="T8 · 默认参数", mins=4.8, secs="290 s", note="0 次命中",
         color=RED, delta="+4% 更慢"),
    dict(label="T8 · 阈值 0.45", mins=3.7, secs="220 s", note="命中 1/4 步",
         color=MID, delta="−21%"),
    dict(label="T8 · 阈值 1.0（激进）", mins=2.7, secs="160 s",
         note="仅草稿 · 不可复现", color=GREEN, delta="−43%"),
]

def bx(v):
    return X0 + v / VMAX * XMAX

svg = []
svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
           'font-family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,'
           'PingFang SC,Microsoft YaHei,sans-serif">' % (W, H))
svg.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))
svg.append('<text x="30" y="38" font-size="20" font-weight="700" fill="#111827">'
           '一条 5 秒短视频，本地要生成多久？</text>')
svg.append('<text x="30" y="62" font-size="12.5" fill="%s">'
           'MiniMax H3 · 640×352 · 124 帧 · 2080Ti 22G 实测 · 同条件同 seed 对比'
           '</text>' % SUB)

# vertical grid + axis labels (behind bars)
for v in range(0, 6):
    gx = bx(v)
    svg.append('<line x1="%.0f" y1="%d" x2="%.0f" y2="%d" stroke="%s" '
               'stroke-width="1"/>' % (gx, Y0 - 12, gx, Y0 + 5 * ROW_H - 20, GRID))
    svg.append('<text x="%.0f" y="%d" font-size="11.5" fill="%s" '
               'text-anchor="middle">%d</text>' % (gx, Y0 + 5 * ROW_H - 2, SUB, v))
svg.append('<text x="%d" y="%d" font-size="11.5" fill="%s">分钟/镜</text>'
           % (bx(5) + 14, Y0 + 5 * ROW_H - 2, SUB))

for i, r in enumerate(rows):
    y = Y0 + i * ROW_H
    cy = y + BAR_H / 2
    svg.append('<text x="%d" y="%.0f" font-size="13.5" fill="%s" text-anchor="end" '
               'font-weight="600">%s</text>' % (X0 - 14, cy + 5, TXT, r["label"]))
    if r.get("brk"):
        # reference bar: drawn to scale end with a break mark (way off the chart)
        w = XMAX - 56
        svg.append('<rect x="%d" y="%d" width="%.0f" height="%d" rx="6" fill="%s"/>'
                   % (X0, y, w, BAR_H, r["color"]))
        svg.append('<text x="%d" y="%.0f" font-size="12" font-weight="600" '
                   'fill="#fff">%s</text>' % (X0 + 12, cy + 4, r["note"]))
        bxk = X0 + w + 6
        svg.append('<path d="M%.0f %d l14 %d M%.0f %d l14 %d" stroke="#9ca3af" '
                   'stroke-width="2" fill="none"/>'
                   % (bxk, y - 4, BAR_H + 8, bxk + 12, y - 4, BAR_H + 8))
        svg.append('<rect x="%.0f" y="%d" width="%.0f" height="%d" rx="6" '
                   'fill="%s" opacity="0.45"/>'
                   % (bxk + 32, y, X0 + XMAX - (bxk + 32), BAR_H, r["color"]))
        svg.append('<text x="%.0f" y="%.0f" font-size="15" font-weight="700" '
                   'fill="#4b5563">%s</text>'
                   % (X0 + XMAX + 14, cy + 5, r["value"]))
        continue
    w = bx(r["mins"]) - X0
    svg.append('<rect x="%d" y="%d" width="%.0f" height="%d" rx="6" fill="%s"/>'
               % (X0, y, w, BAR_H, r["color"]))
    svg.append('<text x="%d" y="%.0f" font-size="12" font-weight="600" fill="#fff">'
               '%s</text>' % (X0 + 12, cy + 4, r["note"]))
    tx = bx(r["mins"]) + 12
    svg.append('<text x="%.0f" y="%.0f" font-size="15" font-weight="700" fill="#111827">'
               '%.1f 分钟</text>' % (tx, cy + 5, r["mins"]))
    svg.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="%s">%s</text>'
               % (tx, cy + 20, SUB, r["secs"]))
    if r.get("delta"):
        good = r["delta"].startswith("−")
        svg.append('<text x="%.0f" y="%.0f" font-size="14.5" font-weight="700" '
                   'fill="%s">%s</text>'
                   % (tx + 78, cy + 5, GREEN if good else RED, r["delta"]))

svg.append('<text x="30" y="%d" font-size="11.5" fill="%s">'
           '同晚同 seed 热跑实测（2026-09-01）；T8 = MiniMax 官方 BlockCache 缓存节点，默认参数在 4 步路线上不生效。</text>'
           % (H - 40, SUB))
svg.append('<text x="30" y="%d" font-size="11.5" fill="%s">'
           '本机各档比官方教程参照快 5–11 倍。激进档提速的代价：同 seed 不可复现 → 只用于草稿/选镜头，成片请用无 T8 基线。详见 docs/08。</text>'
           % (H - 22, SUB))
svg.append("</svg>")

out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..",
                                    "docs", "assets", "speed-progress.svg"))
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print("written:", out)
