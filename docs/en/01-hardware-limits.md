# 01 · What a 2080Ti 22G Can and Cannot Do

Understand what this card is missing first, and every dead-end route makes sense — **it's not your tuning, the silicon simply isn't there**.

## The Architecture Ledger

| Item | 2080Ti 22G mod | 3090 | 4090 |
|---|---|---|---|
| Architecture / compute capability | Turing / **sm_75** | Ampere / sm_86 | Ada / sm_89 |
| VRAM | 22G (modded) | 24G | 24G |
| Memory bandwidth | 616 GB/s | 936 GB/s | 1008 GB/s |
| BF16 / FP8 tensor cores | ❌ none | ✅ / ❌ | ✅ / ✅ |

The bandwidth gap is a physical ceiling: the DiT forward pass in video generation is memory-bound, and 616 GB/s means inherently ~1.5× slower than a 3090 and 2×+ slower than a 4090 at the same settings. **Don't try to "optimize" this away — get as close to it as you can.**

## A Lottery Ticket You Already Hold: cu130 Hardware Dequantization

The bandwidth math looks hopeless, but Turing users are already holding one bonus: **torch 2.9.1+cu130 fully enables comfy-kitchen's CUDA dequantization backend** (the full `w4a8_int8_linear` / `dequantize` capability set), so W4A8 weights dequantize through hardware instructions instead of a software fallback.

This is the root cause of the gap between this handbook's measured speed (~5.7 min/clip) and the official docs' 20–30 minutes — it's decided by the runtime version, not by tuning. The community handbook neng320/minimax-h3-local-deployment verified the same effect: 3–5 min/clip at 480p.

**Corollary**: if W4A8 runs absurdly slowly on an older torch / cu121 / cu124 setup, check your runtime before blaming the card.

## Three Direct Consequences for H3

### 1. SageAttention / T8 acceleration kernels target SM80+

SageAttention's Triton kernels and the T8 dual-clock sampler (BlockCache) optimization paths target newer architectures. On sm_75:

- The T8 BlockCache node fails to register out of the box on old setups (it needs the ComfyUI v3 Layers API — see [07](07-upgrade-watch.md) for the corrected picture)
- SageAttention's standalone kernels compile, but wiring them into the H3 pipeline triggers a native crash (see [03](03-sageattention-crash.md))

**Verdict: give up on acceleration kernels for sm_75 originally; use the compat workflows.** (T8 was later proven to work on v0.33.1 — see [08](08-t8-blockcache-4step.md).)

### 2. The DiT must run INT8 (W4A8)

Community-measured data on the same 2080Ti 22G card:

- W4A4 (4-bit weights + 4-bit activations): reconstruction error **0.2005**
- W4A8 (4-bit weights + INT8 activations): reconstruction error **0.0110**

An 18× error gap, directly visible: W4A4 produces **color tearing**. H3's official W4A8 mixed weights are the only usable form for this card.

### 3. VRAM is just barely enough — manage it

The INT8 DiT idles at ~19.5G, leaving only ~2.5G of headroom on 22G:

- Guard against TDR black-screens when the desktop shares the GPU (`--reserve-vram 2.5 --vram-headroom 0.5`)
- The pinned-memory `read_file_slice` failure path causes OOM — just `--disable-pinned-memory`
- Don't watch 4K video in a browser on this card while generating

## h3lite has no 2080-specific issues

As of writing, no 2080Ti-specific problems have been reported on the h3lite repo — indirect evidence that **compat + W4A8 is very likely already the optimum for this card**. Stop looking for a hidden "correct setup".

---

Next: [02 · W4A8 vs W4A4](02-w4a8-vs-w4a4.md)
