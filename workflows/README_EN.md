# Workflows · The Five-Workflow Kit, Ready to Import

All verified on a 2080Ti 22G + ComfyUI + W4A8 mixed weights (same-night, same-seed A/B: t2v on Sep 1, i2v on Sep 2, PDD on Sep 3).

| Workflow | Purpose | Measured |
|---|---|---|
| [t2v final tier](#1-t2v--final-shot-tier) | everything that enters the cut | 280 s (4.7 min) |
| [t2v fast-draft tier](#2-t2v--fast-draft-tier-t8--43) | prompt iteration / shot selection | 160 s (2.7 min, **−43%**) |
| [i2v final tier](#3-i2v--first-frame-anchoring-face-lock) | face lock / continuation · final | 420 s (7.0 min) |
| [i2v fast-draft tier](#4-i2v--fast-draft-tier-t8--38) | drafts for face-locked shots | 260 s (4.3 min, **−38%**) |
| [PDD8+T8 ultra draft](#5-t2v--pdd8t8-ultra-draft-210-s--master-only) | fastest AND highest-quality drafts | **210 s (−34% vs Turbo)** |

---

## 1. t2v · Final-Shot Tier

![t2v final](preview/t2v_final.jpg)

**File**: [h3_w4a8_t2v_compat_api.json](h3_w4a8_t2v_compat_api.json) · **280 s/clip**

No T8 — same-seed **reproducible**: failed shots can be re-submitted identically and review results hold. **Use this for everything that enters the cut.**

## 2. t2v · Fast-Draft Tier (T8, −43%)

![t2v draft](preview/t2v_draft.jpg)

**File**: [h3_w4a8_t2v_t8draft_api.json](h3_w4a8_t2v_t8draft_api.json) · **160 s/clip**

T8 BlockCache at threshold 1.0, 43% faster. **Not same-seed reproducible** (cache hits fork the sampling trajectory) → for prompt iteration and shot selection only; what you pick is a "direction", not the final. Full analysis: [docs/08](../docs/en/08-t8-blockcache-4step.md).

> **The two preview images above were generated from the same seed (3013) and the same prompt** — that is T8's core trait: the trajectory forks, producing an **equal-quality but different** picture (composition, detail and lighting all intact; the content shifts). In practice: the draft tier tells you "what this prompt roughly looks like"; the final tier re-renders a reproducible shot for the cut.

## 3. i2v · First-Frame Anchoring (face lock) · Final Tier

![i2v](preview/i2v.jpg)

**File**: [h3_w4a8_i2v_compat_api.json](h3_w4a8_i2v_compat_api.json) · **420 s/clip (warm)**

Needs a first frame (a character reference frame or a frame extracted from an approved shot) — face consistency is markedly better than pure t2v. Same-seed reproducible. The repo ships a placeholder; point it at your own image.

## 4. i2v · Fast-Draft Tier (T8, −38%)

![i2v draft](preview/i2v_draft.jpg)

**File**: [h3_w4a8_i2v_t8draft_api.json](h3_w4a8_i2v_t8draft_api.json) · **260 s/clip**

Drafts for face-locked shots: 38% faster, and the **absolute saving (160 s/clip) beats the t2v draft tier's 120 s** — the pricier the shot, the more T8 saves. Same rules as the t2v draft tier: directions only; re-render finals on the final tier.

## 5. t2v · PDD8+T8 Ultra Draft (210 s, master only)

![pdd8 t8](preview/pdd8_t8.jpg)

**File**: [h3_w4a8_t2v_pdd8_t8_api.json](h3_w4a8_t2v_pdd8_t8_api.json) · **210 s/clip (−34% vs Turbo, 6/8 hits)**

The official PDD distilled LoRA (8-step) combined with the T8 cache: **currently the fastest tier and the highest quality** (the official 8-step distillation beats the community 4-step Turbo in blind comparison pending; official materials already show parity-or-better). Extra prerequisites: ① a ComfyUI **master environment** (backport recipe in [docs/09](../docs/en/09-pdd-backport.md), or wait for v0.34.1+) ② the PDD weights (download from the `Kijai/MiniMax-H3-experimental` repo, `loras/`) ③ the T8 node pack with the master-compat patch from docs/09. Not same-seed reproducible (drafts only); for reproducible PDD-quality finals, drop the T8 node and run pure 8-step (600 s).

---

## Import in Three Steps

1. Drag the JSON into the ComfyUI UI, or drop it in `user/default/workflows/`
2. Replace the `__H3_PROMPT__` placeholder in the prompt node with your prompt (i2v: also swap the first-frame loader)
3. Check the model file names against your local `models/` (W4A8 weight file names differ between download eras — rename to match)

## Prerequisites

- Model set: W4A8 mixed DiT + dual VAE (video fp16 / audio fp32) + qwen3vl_4b text encoder + ClipProj + fl2v Turbo 4-step LoRA (full list with links: [docs/05](../docs/en/05-workflows.md))
- **Fast-draft tiers additionally need**: the [T8mars/comfyui-minimax-h3-blockcache-T8](https://github.com/T8mars/comfyui-minimax-h3-blockcache-T8) node pack (drop into `custom_nodes/`, restart; works on v0.33.1 — no ComfyUI upgrade required)
- **The PDD ultra tier additionally needs**: a master-environment ComfyUI + the PDD weights + the T8 master-compat patch ([docs/09](../docs/en/09-pdd-backport.md))
- Launch flags (against TDR/OOM): `--reserve-vram 2.5 --vram-headroom 0.5 --disable-pinned-memory` — template at [scripts/h3_launch.example.sh](../scripts/h3_launch.example.sh)

## Two Known Traps (read before the draft tiers)

1. **The T8 node is a v3-API node**: dragging it in the ComfyUI UI is fine, but submissions over the `/prompt` API must pass **all 8 inputs explicitly** — v3 nodes get no server-side defaults; miss one and it's a 400 `required_input_missing`. (The workflow JSONs here are already fully explicit — importing them directly is safe.)
2. **The default threshold 0.12 is a negative optimization on the 4-step route**: zero hits plus 175 MB of cache overhead (measured 290 s vs 280 s). Don't "fix" it back to defaults — for a 4-step speedup you want 1.0. Why: [docs/08](../docs/en/08-t8-blockcache-4step.md).
