#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate docs/assets/speed-progress.svg - one simple question:

"一条 5 秒视频，本地要生成多久？" - horizontal bars, same-night A/B data.
Pure stdlib on purpose (repo has zero deps). Rerun to regenerate.
"""
import os

W, H = 960, 430
X0, XMAX, VMAX = 300, 500, 5.2   # bar origin px, full-scale px, minutes
BAR_H, ROW_H, Y0 = 40, 62, 130

BLUE, RED, MID, GREEN = "#2563eb", "#dc2626", "#60a5fa", "#059669"
GRID, TXT, SUB = "#e5e7eb", "#374151", "#9ca3af"

rows = [
    ("不加 T8（成片标准）", 4.7, "280 s", None,  "✓ 可复现",        BLUE),
    ("T8 · 默认参数",       4.8, "290 s", "+4% 更慢", "0 次命中",     RED),
    ("T8 · 阈值 0.45",      3.7, "220 s", "−21%",    "命中 1/4 步",   MID),
    ("T8 · 阈值 1.0（激进）", 2.7, "160 s", "−43%",   "仅草稿 · 不可复现", GREEN),
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

# reference badge (top right)
svg.append('<rect x="608" y="76" width="322" height="34" rx="17" '
           'fill="#ecfdf5" stroke="%s" stroke-width="1"/>' % GREEN)
svg.append('<text x="769" y="98" font-size="12.5" font-weight="600" fill="#065f46" '
           'text-anchor="middle">参考：官方教程 20–30 分钟/镜 → 本机快 5–6 倍</text>')

# vertical grid + axis labels
for v in range(0, 6):
    gx = bx(v)
    svg.append('<line x1="%.0f" y1="%d" x2="%.0f" y2="%d" stroke="%s" '
               'stroke-width="1"/>' % (gx, Y0 - 12, gx, Y0 + 4 * ROW_H - 22, GRID))
    svg.append('<text x="%.0f" y="%d" font-size="11.5" fill="%s" '
               'text-anchor="middle">%d</text>' % (gx, Y0 + 4 * ROW_H - 4, SUB, v))
svg.append('<text x="%d" y="%d" font-size="11.5" fill="%s">分钟/镜</text>'
           % (bx(5) + 14, Y0 + 4 * ROW_H - 4, SUB))

# bars
for i, (label, vmin, secs, delta, note, color) in enumerate(rows):
    y = Y0 + i * ROW_H
    w = bx(vmin) - X0
    svg.append('<text x="%d" y="%.0f" font-size="13.5" fill="%s" text-anchor="end" '
               'font-weight="600">%s</text>' % (X0 - 14, y + BAR_H / 2 + 5, TXT, label))
    svg.append('<rect x="%d" y="%d" width="%.0f" height="%d" rx="6" fill="%s"/>'
               % (X0, y, w, BAR_H, color))
    # purpose note inside bar (white)
    svg.append('<text x="%d" y="%.0f" font-size="12" font-weight="600" fill="#fff">'
               '%s</text>' % (X0 + 12, y + BAR_H / 2 + 4, note))
    # value + seconds + delta after bar end
    tx = bx(vmin) + 12
    svg.append('<text x="%.0f" y="%.0f" font-size="15" font-weight="700" fill="%s">'
               '%.1f 分钟</text>' % (tx, y + BAR_H / 2 + 1, "#111827", vmin))
    svg.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="%s">%s</text>'
               % (tx, y + BAR_H / 2 + 17, SUB, secs))
    if delta:
        good = delta.startswith("−")
        svg.append('<text x="%.0f" y="%.0f" font-size="14.5" font-weight="700" '
                   'fill="%s">%s</text>'
                   % (tx + 78, y + BAR_H / 2 + 1,
                      GREEN if good else RED, delta))

svg.append('<text x="30" y="%d" font-size="11.5" fill="%s">'
           '同晚同 seed 热跑实测（2026-09-01）；T8 = MiniMax 官方 BlockCache 缓存节点，默认参数在 4 步路线上不生效。</text>'
           % (H - 26, SUB))
svg.append('<text x="30" y="%d" font-size="11.5" fill="%s">'
           '激进档提速的代价：同 seed 不可复现 → 只用于草稿/选镜头，成片请用无 T8 基线。详见 docs/08。</text>'
           % (H - 8, SUB))
svg.append("</svg>")

out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..",
                                    "docs", "assets", "speed-progress.svg"))
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print("written:", out)
