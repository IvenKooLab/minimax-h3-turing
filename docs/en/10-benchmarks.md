# 10 · The Benchmark Dataset (all measurements, 2026-09-01 → 09-05)

> Every number this handbook claims, on one page. **Each one was actually rendered**: same 2080Ti 22G, same methodology (same-seed controls, warm runs, wall-clock), environment noted row by row — nothing here is extrapolated or quoted second-hand.
> Full context for each experiment lives in its own doc; this page is the consolidated view.

## Environment Baseline

| Dimension | Configuration |
|---|---|
| GPU | 2080Ti 22G mod (Turing sm_75), 616 GB/s memory bandwidth |
| Runtime | PyTorch 2.9.1+cu130 (kitchen CUDA dequantization fully enabled) |
| ComfyUI | v0.33.1 (Sep 1–2 data) → master@345c919 (from Sep 3, the PDD backport) |
| Models | W4A8 mixed DiT + qwen3vl_4b + ClipProj + dual VAE + fl2v/Ref2VA LoRAs |
| Standard clip | 640×352 · 124 frames (≈5.2 s @ 24 fps) · native audio · seed 3013 |

## t2v (text-to-video) — Every Tier

| Date | Env | LoRA | Steps | T8 | Time | vs baseline | Doc |
|---|---|---|---|---|---|---|---|
| Sep 1 | 0.33.1 | Turbo 4-step | 4 | ✗ | **280 s** | baseline (final tier) | [08](08-t8-blockcache-4step.md) |
| Sep 1 | 0.33.1 | Turbo 4-step | 4 | defaults (0.12) | 290 s | **+3.6%** (0 hits, negative) | 08 |
| Sep 1 | 0.33.1 | Turbo 4-step | 4 | threshold 0.45 | 220 s | −21% (1/4 hits) | 08 |
| Sep 1 | 0.33.1 | Turbo 4-step | 4 | **threshold 1.0** | **160 s** | **−43%** (2/4 hits) | 08 |
| Sep 3 | master | Turbo 4-step | 4 | ✗ | 320 s | baseline (master) | [09](09-pdd-backport.md) |
| Sep 3 | master | **PDD FL2VA** | 8 | ✗ | 600 s | reproducible + distilled quality | 09 |
| Sep 3 | master | **PDD FL2VA** | 8 | **threshold 1.0** | **210 s** | **−34% vs master baseline** (6/8 hits) | 09 |

## i2v (image-to-video / face lock) — Every Tier

| Date | Env | LoRA | Steps | T8 | Time | vs baseline | Doc |
|---|---|---|---|---|---|---|---|
| Sep 2 | 0.33.1 | Turbo 4-step | 4 | ✗ | 417 s | baseline (0.33.1) | 08 |
| Sep 2 | 0.33.1 | Turbo 4-step | 4 | threshold 1.0 | 260 s | −38% (2/4 hits) | 08 |
| Sep 4 | master | Turbo 4-step | 4 | ✗ | 395 s | baseline (master, 5% faster than 0.33.1) | 09 |
| Sep 4 | master | **PDD Ref2VA** | 8 | ✗ | 933 s | reproducible + distilled quality | 09 |
| Sep 4 | master | **PDD Ref2VA** | 8 | **threshold 1.0** | **192 s** | **−51% (fastest in the project)** (6/8 hits) | 09 |

## T8 Hit-Rate × Scene Matrix (0.33.1, 4-step route)

| Scene | threshold 0.45 | threshold 1.0 |
|---|---|---|
| Static (dawn lake) | 2/4 | 2/4 |
| Light motion (misty bamboo walk) | 1/4 | 2/4 |
| Medium motion (market follow cam) | 1/4 | 2/4 |

Conclusion: **1.0 hits a stable 2/4 in every scene**; 0.45 depends on shot content. The 8-step route's hit window is 6/8 (first-step warm-up + one refresh is the structural ceiling).

## Mechanism Constants (reproduced across experiments)

- **Each cache hit ≈ one full forward saved**: ~60 s/hit on the 4-step route, ~75 s/hit on 8-step
- The i2v fixed overhead (first-frame conditioning, ~80 s) is not cacheable — **the pricier the shot, the more T8 saves in absolute terms** (t2v saves 120 s, i2v Turbo 157 s, i2v PDD 203 s)
- Official reference frame: typical environments render this spec at 20–30 min/clip → the fastest tier here is **6–9× faster** (192 s vs 1200–1800 s)

## Audio Measurements (ffmpeg volumedetect)

| Config | mean | max | Verdict |
|---|---|---|---|
| Turbo control | −14.0 dB | −0.6 dB | no clipping |
| T8 aggressive | −22.2 dB | −8.5 dB | no clipping, ~8 dB quiet (normalize in post) |
| PDD 8-step | −15.9 dB | −0.4 dB | no clipping |
| Ref2VA PDD+T8 | −33.6 dB | −18.0 dB | no clipping, quiet (same handling) |

Uniform countermeasure: a −1 dB limiter on the final-shot pipeline.

## Version Comparison (0.33.1 vs master@345c919)

| Route | 0.33.1 | master | Delta | Note |
|---|---|---|---|---|
| t2v Turbo 4-step | 280 s | 320 s | +14% | master-side t2v transcode/packaging overhead (suspected, unconfirmed) |
| i2v Turbo 4-step | 417 s | 395 s | **−5%** | master is actually faster here |
| Single-file backport smoke | — | pixel-identical (frame MAE = 0) | 0 | master's model.py is numerically equivalent on the plain path |

## Ruled-Out Routes at a Glance

| Route | Verdict | One-liner |
|---|---|---|
| SageAttention 2.2.0 (torch ≥ 2.9) | ❌ | Triton sm_75 compile failure; the CUDA kernel crashes natively in-pipeline ([03](03-sageattention-crash.md)) |
| TE-Speed | ❌ | semantic collapse at short step counts; permanently ruled out |
| T8 default params (0.12) | ❌ | zero hits on 4-step + 175 MB pure overhead |
| cache_device=gpu | ❌ | OOM death-loop on the 22G card (verified); cpu is correct |
| W4A4 quantization | ❌ | error 0.2005 vs W4A8's 0.0110 (18×); color tearing |

## Methodology Notes (for reproducers)

1. Timing: warm-run wall-clock (model resident in VRAM), from `/prompt` submission to history success — includes VAEDecode/packaging, excludes cold model load (another 40–60 s)
2. prompt_id determinism: identical inputs are silently deduplicated — any parameter change in an A/B (even just cache_device) yields a new pid; that's a feature
3. Environmental sensitivity of wall time: aggressive HTTP polling or background load can drift timings ±10%; **hit counts (cached X/N) are environment-independent** and the most reliable comparison dimension
4. Blind-test methodology: two same-seed, same-prompt clips shuffled into random A/B order (key kept offline), human picks the better one — used to adjudicate PDD vs Turbo final-shot quality

---

Everything is reproducible: scripts in [scripts/](../scripts/) (t8_ab_test / pdd_ab_test), workflows in [workflows/](../workflows/README.md). Question a number — open an issue and we'll compare notes.
