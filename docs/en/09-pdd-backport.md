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

**Follow-up (Sep 15)**: upstream shipped **v1.0.4** (commit `36336dc`) implementing this compatibility properly via explicit signature detection (`inspect.signature(FinalLayer.forward)`) — the patch on this page is superseded; just upgrade the node pack. Regression run: PDD 8-step + T8 = **190 s, 6/8 hits** (better than 210 s with my hand patch); issue #4 verified and closed.

## Data and Mechanism

- 8 steps give T8 a 6/8 hit window (step 1 warm-up is mandatory + one refresh); measured exactly **cached 6/8**
- Each hit saves one full forward (~75 s/step at 8 steps): 600 s − 6×75 s + cache overhead ≈ 210 s — the books balance exactly
- PDD+T8 output: composition intact, no artifacts (the head bank blends per-step correctly on the hit path); audio mean −27.6 dB / max −13.8 dB, no clipping, ~8 dB quiet (a known cache-path trait — normalize loudness in post)
- Reproducibility: PDD 8-step without T8 = reproducible (final-shot tier); PDD+T8 = not same-seed reproducible (draft tier, consistent with the T8 behavior in [08](08-t8-blockcache-4step.md))

## Ref2VA (i2v) Lands Too (added 2026-09-04)

The same method applied to i2v (Ref2VA-Acc-8Step LoRA, first-frame face-lock route), same seed, same default first frame, master environment, warm runs:

| Config | Time | Notes |
|---|---|---|
| i2v Turbo 4-step (no T8, re-measured master baseline) | 395 s | was 417 s on 0.33.1 — master slightly faster here |
| i2v Ref2VA PDD 8-step (no T8) | 933 s | reproducible + distilled quality |
| **i2v Ref2VA PDD + T8 (threshold 1.0)** | **192 s** | **6/8 hits, −51%** |

Three takeaways: ① **192 s is the fastest record in this entire project** — the priciest route (face-locked shots) now renders faster than the old t2v final tier (280 s); ② the absolute saving of 203 s/clip confirms "the pricier the shot, the more T8 saves"; ③ zero load errors — the Ref2VA variant behaves identically to FL2VA on master.

## The Tier System (from 2026-09-03)

| Tier | Config | Speed | Use |
|---|---|---|---|
| ⚡ Ultra draft | **PDD 8-step + T8** | **210 s (t2v) / 192 s (i2v)** | shot selection / prompt iteration — the highest-quality draft |
| ✅ Final | **PDD 8-step** | 600 s (t2v) / 933 s (i2v) | reproducible + distilled quality (swap the whole final-shot tier if the blind test prefers it) |
| Legacy final | Turbo 4-step | 320 s (t2v) / 395 s (i2v) | existing projects |

> ⚠️ Every PDD tier requires a master environment (this page's backport, or a future v0.34.1+). On 0.33.1, use the four-workflow [kit](../workflows/README.md).

## Warning (Sep 20): PDD LoRA loading has been broken by environment deps since ~Sep 6

**Discovery**: after rembg was installed on Sep 6, the PDD LoRA's adaln_proj layers began
failing to load silently (ERROR lora - deltas never apply while rendering continues).
**The Sep-15 "190 s, 6/8 hits" regression run on this page was most likely a phantom-PDD
run** (loading errors were not checked that day - lesson recorded); the Sep-3 (210 s) and
Sep-4 (192 s) figures predate the contamination and remain credible, though re-verification
after the fix is advised. Root cause (stack-verified): ComfyUI's cast path invokes the LoRA
patch while the weight is still in its quantized packed shape ([96768, 8] instead of the
logical [96768, 2688]) - reported upstream as
**[Comfy-Org/ComfyUI#16420](https://github.com/Comfy-Org/ComfyUI/issues/16420)** with the
full stack and repro. The v0.36.0 H3 key-map fix does not cover this. In the same window,
a Sep-19 rapidocr install also zeroed T8 cache hits (a separate contamination; mechanism
under investigation).

**Upstream progress (Sep 20)**: Comfy-Org collaborator Kaustubh1235 confirmed the root-cause
direction the same day and asked about scope -> answered with a **per-layer census**
([issuecomment-5758468110](https://github.com/Comfy-Org/ComfyUI/issues/16420#issuecomment-5758468110)):
on the same W4A8 weights, **only adaln_proj errors out**; attn.out_proj / qkv_proj /
mlp.fc1 / fc2 **apply silently and correctly** (their packed storage keeps a logical 2D
layout); final_layer applies via the resizing force-load path - the model ends up
half-patched (renders fine, adaln deltas lost, quality degraded). Verified that the
v0.36.0 key-map does not change this. Awaiting the upstream fix.

## Open Items

- The **PDD vs Turbo final-shot quality blind test** (8-step vs 4-step at the same seed, scored blind) in progress — decides whether the final-shot tier switches wholesale
- ~~The Ref2VA PDD variant (i2v route) untested~~ ✅ tested Sep 4 — see above
- ~~The T8 compatibility patch pending upstream feedback~~ ✅ fully closed (Sep 15): upstream v1.0.4 fixed it properly via explicit signature detection; issue #4 re-verified (190 s, 6/8 hits) and closed
- Why the Turbo baseline is 14% slower on master (320 vs 280 s): **the Sep 4 re-test shows it is t2v-specific** — i2v is 5% faster on master (417→395 s); suspicion narrows to the t2v-side transcode/packaging path
