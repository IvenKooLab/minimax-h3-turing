# 09 · PDD Without Waiting: a Master-Backport Field Report

> 2026-09-03. "Wait for a release containing #15908" is the safe route — we chose to port PDD ourselves instead. It worked on the first try, with complete solutions to three pitfalls along the way. Same-seed verdict: **PDD 8-step + T8 = 210 s/clip (−34%), with the official distillation quality**.

## TL;DR

| Config (same seed 3013, master@345c919, warm runs) | Time | Notes |
|---|---|---|
| Turbo 4-step (no T8) | 320 s | master-environment baseline (280 s on 0.33.1) |
| PDD 8-step (no T8) | 600 s | official distillation quality, **reproducible** |
| **PDD 8-step + T8 (threshold 1.0)** | **210 s** | **6/8 hits** — the fastest and the highest-quality tier |

PDD LoRA: `loras/MiniMax-H3-FL2VA-Acc-8Step_comfy.safetensors` from `Kijai/MiniMax-H3-experimental` (t2v; a Ref2VA variant exists for i2v). Sampling: `simple` 8 steps + shifts 12/3, no new nodes needed.

## The Backport Route (three pitfalls, told once)

### Pitfall 1: a single-file swap isn't enough — end with the full upgrade

We first replaced only `comfy/ldm/minimax/model.py` (the PDD core really is in that one file: the `FinalLayer` head bank + `_pdd_head` interval blending, ~+195 lines). The plain Turbo smoke test was **pixel-identical** (frame MAE = 0) — but loading the PDD LoRA immediately produced:

```
ERROR lora diffusion_model.blocks.N.adaln_proj.linear.weight
shape '[96768, 8]' is invalid for input of size 260112384
```

Root-cause chain: the PDD LoRA carries deltas for the adaln_proj layers (Turbo doesn't, which is why this never surfaced) → adaln_proj is quantized weight → the "quantized weights + LoRA" path has a bug on 0.33.1 → the fix lives in `model_patcher.py`'s `calculate_shape` force-reload logic (4 sites). The dependency closure snowballed (ops/model_base/samplers all have diffs) — file-by-file swapping loses to a full upgrade.

**Final solution**: jsdelivr file-by-file upgrade to an exact master commit (483→519 files, 89+36 changed, ~4 minutes). Full backup directory; rollback = copy back.

### Pitfall 2: the upgrade script's directory blind spot — comfy_api/

The upgrade script only covered `comfy/` and `comfy_extras/`, but in the master era **`comfy_api/` is an active directory** (the v3 node API). Symptom of missing it: `SaveVideo`/`CreateVideo` nodes vanish (`module 'comfy_api.latest._io_public' has no attribute 'VideoEdit'`). Fix: add `comfy_api/` to the filter prefixes.

### Pitfall 3: old PyAV + the T8 node's broken interface with master

- master's `nodes_video.py` needs the newer PyAV's `av.video.reformatter.ColorPrimaries` — `pip install -U av` (to 18.x)
- **The T8 BlockCache node (Aug 24 version) calls `FinalLayer.forward` with the 0.33.x 4-arg signature**, but master changed it to 7 args (+sigma, sample_sigmas, shifts), so combining PDD+T8 failed with `missing 3 required positional arguments`

The T8 adaptation patch (hit path in `custom_nodes/comfyui-minimax-h3-blockcache-T8-main/nodes.py`; self-adapting across both versions):

```python
try:
    _shift_v = float(transformer_options.get("minimax_h3_sigma_shift_video", model.sigma_shift_video))
    _shift_a = float(transformer_options.get("minimax_h3_sigma_shift_audio", model.sigma_shift_audio))
    _sigma_v = (timestep.flatten()[0] / 1000.0).float().clamp(min=1e-6)
    video_rows, audio_rows = model.final_layer(
        hit.hidden, hit.t_emb, hit.video_segment, hit.audio_segment,
        _sigma_v, transformer_options.get("sample_sigmas"), (_shift_v, _shift_a))
except TypeError:
    video_rows, audio_rows = model.final_layer(hit.hidden, hit.t_emb, hit.video_segment, hit.audio_segment)
```

The subtle part: **the hit path must pass `sample_sigmas` to final_layer** — the PDD head bank needs it to locate the current sigma interval for output-head blending; omit it and cache hits silently produce garbled bank results.

## Data and Mechanism

- 8 steps give T8 a 6/8 hit window (step 1 warm-up is mandatory + one refresh); measured exactly **cached 6/8**
- Each hit saves one full forward (~75 s/step at 8 steps): 600 s − 6×75 s + cache overhead ≈ 210 s — the books balance exactly
- PDD+T8 output: composition intact, no artifacts (the head bank blends per-step correctly on the hit path); audio mean −27.6 dB / max −13.8 dB, no clipping, ~8 dB quiet (a known cache-path trait — normalize loudness in post)
- Reproducibility: PDD 8-step without T8 = reproducible (final-shot tier); PDD+T8 = not same-seed reproducible (draft tier, consistent with the T8 behavior in [08](08-t8-blockcache-4step.md))

## The Tier System (from 2026-09-03)

| Tier | Config | Speed | Use |
|---|---|---|---|
| ⚡ Ultra draft | **PDD 8-step + T8** | **210 s** | shot selection / prompt iteration — the highest-quality draft |
| ✅ Final | **PDD 8-step** | 600 s | reproducible + distilled quality (swap the whole final-shot tier if the blind test prefers it) |
| Legacy final | Turbo 4-step | 320 s | existing projects |

> ⚠️ Every PDD tier requires a master environment (this page's backport, or a future v0.34.1+). On 0.33.1, use the four-workflow [kit](../workflows/README.md).

## Open Items

- The **PDD vs Turbo final-shot quality blind test** (8-step vs 4-step at the same seed, scored blind) — decides whether the final-shot tier switches wholesale
- The Ref2VA PDD variant (i2v route) untested
- The T8 compatibility patch pending upstream feedback (a follow-up on T8mars issue #4, or a PR)
- Why the Turbo baseline is 14% slower on master (320 vs 280 s) — uninvestigated (suspect: the new transcoding path)
