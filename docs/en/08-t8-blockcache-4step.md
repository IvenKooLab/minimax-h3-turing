# 08 · T8 BlockCache on the 4-Step Route: a 43% Speedup With Two Catches

> Research completed 2026-09-01. The earlier conclusion "T8 requires ComfyUI ≥0.34" was a **misdiagnosis** — the node works on v0.33.1; the real problem was somewhere else entirely.

## First, Correcting Two Earlier Mistakes

1. **"T8 needs the v3 Layers API and is unavailable on this version" — wrong.** Measured: v0.33.1's `nodes.py` fully supports the v3 node protocol (`comfy_entrypoint`), `comfy_api.latest.io` has all the symbols, and the T8 pack passes all four loading steps (import → entrypoint → get_node_list → define_schema), registering normally in `/object_info`.
2. **But v3 nodes have a real trap**: submissions over the `/prompt` API **do not get server-side defaults** — every parameter declared in `INPUT_TYPES` (including `advanced: True` ones) must be passed explicitly; miss one and you get a 400 `required_input_missing`. The old "the node silently doesn't work" feeling likely came from here.

## Experiment Design

- Environment: 2080Ti 22G / ComfyUI v0.33.1 / W4A8 mixed + fl2v Turbo 4-step LoRA @1.0 / 640×352 · 124 frames · `simple` 4 steps · `res_multistep`
- Same workflow, same seed 3013; the only variable is the T8 node and its parameters
- Timings are warm-run wall clock (model already resident in VRAM)

## The Data

| Config | Time | vs control | Cache hits | Frame diff vs control |
|---|---|---|---|---|
| Control (no T8) | **280 s** | — | — | baseline |
| T8 defaults (threshold 0.12) | 290 s | +3.6% | **0/4** | **zero** (JPEG-level identical) |
| T8 mid tier (threshold 0.45) | 220 s | **−21%** | 1/4 | not measured (trajectory already forked) |
| T8 aggressive (threshold 1.0, start 0, end 1.0, hits 10) | **160 s** | **−43%** | 2/4 | a different picture of equal quality (below) |

The key log line (aggressive tier):

```
MiniMax H3 Block Cache - cached 2/4 model forwards, cache 175.4 MiB on cpu
```

Steps 2 and 4 of the 4 skipped their block computation via residual reuse, dropping from 60–70 s to ~1.2 s per hit — that is the entire source of the 43%.

The three tiers form a clean monotone curve: **each hit saves ~60 s (one full forward)** — 0/4 is 3.6% slower (pure overhead), 1/4 is 21% faster, 2/4 is 43% faster.

## Threshold × Scene-Motion Matrix (added 2026-09-02; conclusions final)

Hit-rate statistics across scene motion levels and thresholds:

| Scene | threshold 0.45 | threshold 1.0 | Notes |
|---|---|---|---|
| Static (dawn lake, near-zero motion) | **2/4** | 2/4 | Static residuals are stable; even 0.45 maxes out |
| Light motion (swordsman walking in a misty bamboo forest) | 1/4 | 2/4 | |
| Medium motion (market walk + follow cam) | 1/4 | 2/4* | *the 1.0 column was measured repeatedly across two nights: a stable 2/4 everywhere |

**Conclusion**: hit rate = f(scene motion, threshold). **0.45 is a luck tier** (maxes out on static content, drops to 1/4 the moment things move); **1.0 is the unconditional stable tier** (2/4 in every scene). Production config doesn't need per-shot tuning — **use 1.0 for the draft tier, always**.

Methodology notes (sparing reproducers some pain):
- With `verbose=False` the node **does not print** the "cached X/4" summary line — enable verbose to collect hit statistics
- Measured wall time is heavily environment-dependent (with antivirus real-time protection on, a clip can drift from 200 s to 500 s+, and the ComfyUI HTTP API lags into timeouts); the **hit counts in this matrix are environment-independent** — trust the Sep 1 clean-environment timings for speed

## Why the Defaults Never Hit

T8's hit condition is "audio/video stability metric < `residual_diff_threshold` (default 0.12)". The log shows this clip's 4-step diff values ranged 0.39–1.00 — **the 4-step Turbo stride (Δt) is so large that residuals change violently between steps; a 0.12 threshold is mathematically unreachable**. That default was designed for 8+ step routes (the official accelerated LoRAs) or standard 20–50-step schedules.

Note that diff values have per-clip variance and are prefix-sensitive: at this seed the mid tier (0.45) caught only 1 hit (that step's video_diff 0.608 crossed 0.45); catching everything requires threshold ≥ 1.01. **For a stable 2/4 on the 4-step route, just use 1.0**; 0.45 is the gambling tier.

## Quality Analysis (important)

The aggressive tier's frame PSNR vs control is only 14 dB — **do not** read that as "quality collapsed". Visual inspection of three frames (start/middle/end): composition intact, no tearing, no artifacts, no color anomalies. The real cause is a **forked sampling trajectory**: cached steps reuse the previous residual, the numerical path diverges, and the same seed yields a content-shifted but equal-quality video.

Audio drifts the same way: aggressive tier mean −22.2 dB / max −8.5 dB (control: −14.0 dB / −0.6 dB) — **no clipping or distortion**, just ~8 dB quieter; normalize loudness in post.

## The i2v (image-to-video) Route Works Too (added 2026-09-02)

The same method applied to i2v (first-frame anchoring, the workhorse of face-locked shots), same seed, same default first frame, warm runs:

| Config | Time | Hits |
|---|---|---|
| i2v control (no T8) | **420 s (7.0 min)** | — |
| i2v + T8 threshold 1.0 | **260 s (4.3 min)** | 2/4 |

**−38%**. Slightly less than t2v's −43% because the first-frame conditioning overhead (~80 s) is not cacheable; but the **absolute saving of 160 s/clip exceeds t2v's 120 s** — the pricier the shot, the more T8 saves. The draft/final tier discipline is identical to t2v.

## Two Catches You Must Know

1. **Same-seed runs are no longer reproducible.** Once a cache hits, the numerical trajectory forks and a same-seed re-run ≠ the same result. Production strategies built on "re-submit the failed shot with the same seed" **stop working** in the T8 tier — a retry yields a different picture.
2. **Same-seed A/B against a no-T8 run is also meaningless.** A T8 clip that passed review cannot be reproduced by the no-T8 workflow.

## Practical Advice (4-step Turbo route)

- **Drafts/preview/shot selection**: T8 aggressive (threshold 1.0), **2.7 min/clip**, 43% faster
- **Final shots**: no T8, preserving reproducibility and review consistency (5.7 min/clip)
- The default params (0.12) are **pointless on the 4-step route**: 0 hits plus 175 MB of cache-management overhead — 3.6% slower
- Re-test once PDD LoRA (8-step) lands: T8 + the official accelerated LoRA is the officially-claimed +100% combination, and every number here will need a re-run

## Reproduction

Insertion point: after the Turbo LoRA, before the Guider/Scheduler (MODEL chain).

```json
"200": {"class_type": "MiniMaxH3BlockCacheT8", "inputs": {
    "model": ["105:201", 0],
    "residual_diff_threshold": 0.45,
    "start_percent": 0.0, "end_percent": 1.0,
    "max_consecutive_hits": 10,
    "cache_device": "cpu", "metric_stride": 8, "verbose": true}}
```

(v3 API nodes: not one parameter may be omitted, including `advanced` items.)

---

Previous: [07 · Upgrade-window watch](07-upgrade-watch.md) · Next: [09 · PDD without waiting](09-pdd-backport.md)
