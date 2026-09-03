# 04 · Community Tips, Verified: Three You Can Copy Directly

All three come from field reports by another 2080Ti 22G owner, and all were verified on this production box.

## 1. SageAttention Still Delivers +16.8% on Turing

- **Claim**: enabling SageAttention on Turing yields a 16.8% speedup, and the fallback warnings in the logs are **noise, not symptoms** — don't try to "fix" them
- **Applicability**: ⚠️ version-sensitive — that conclusion corresponds to sageattention **1.0.6** + torch 2.6.0 + cu124 + triton 3.2.0. We crashed immediately with 2.2.0 + torch 2.9; see [03](03-sageattention-crash.md)
- **Action**: use it if your environment matches; don't force it otherwise

## 2. The Right `--reserve-vram` Value

| Scenario | Value |
|---|---|
| 5–6 s clips (≤124 frames) | **2.5** ✅ verified on this box |
| 15 s long clips (362 frames) | **4** |
| Desktop/monitor shares this GPU | Leave headroom at all times |

Too small → TDR black-screen (driver reset); too large → wasted VRAM. Launch template: [scripts/h3_launch.example.sh](../scripts/h3_launch.example.sh).

## 3. RTX VSR Upscaling Works on Turing

- **Claim**: NVIDIA VSR (video super resolution) works fully on Turing — measured at **47 ms/frame** with the newer nvidia-vfx wheel
- **Recipe**: H3 natively generates 640×352 (fast) → extract frames → RTX VSR upscale to 1080p → reassemble
- **Why bother**: low-resolution generation is where this card's speed comes from; recovering quality via VSR is far cheaper than generating 1080p natively (per-step time explodes)
- The community card's 15 s 1080p clip (23 minutes) used exactly this "generate at 960×540 → VSR upscale" route

## One Reverse Conclusion: T8 BlockCache — Don't Dismiss It

The T8 dual-clock sampler (MiniMaxH3BlockCacheT8) was officially open-sourced, and at the time of the first draft of this handbook:

- The node failed to register on sm_75 + the then-current ComfyUI (it needs the v3 Layers API)
- v0.33.1 already shipped the native H3 AV sampling fix (commit `bdcb886`), making the DualClock plugin unnecessary

**Update (Sep 1)**: that registration failure was our misdiagnosis — the node registers and runs on v0.33.1 and delivers −43% on the 4-step route; see [08](08-t8-blockcache-4step.md) for the full reversal.

---

Next: [05 · Workflows](05-workflows.md)
