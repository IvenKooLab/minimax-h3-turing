# 07 · ComfyUI Upgrade-Window Watch

This box's stance: **we are not latest-version zealots. Every release must answer "what does it do for Turing + H3" before we touch anything.**

## The Route Verdict Table (as of this writing)

First, one clear statement on "can it go faster": on the current software stack, **5.7 min/clip (640×352, W4A8, 4-step) is the physical limit of this card** — there is no immediately-free speedup left. (Since this table was first written, the PDD backport broke that limit — see [09](09-pdd-backport.md).)

| Route | Verdict | Notes |
|---|---|---|
| cu130 hardware dequantization | ✅ harvested | kitchen CUDA backend fully enabled — the root cause of our current speed (see [01](01-hardware-limits.md)); no action needed |
| SageAttention | ❌ ruled out | Triton INT8 kernels fail to compile on sm_75 (all versions 3.2.0–3.8.0); the CUDA kernel runs standalone but crashes natively in-pipeline (see [03](03-sageattention-crash.md)); re-test at an upgrade window |
| T8 dual-clock | ✅ **proven working** | Misdiagnosis corrected Sep 1: it runs on v0.33.1. Aggressive tier on the 4-step route **−43% (160 s/clip)**, but same-seed runs are not reproducible — T8 for drafts, not for final shots; see [08](08-t8-blockcache-4step.md) |
| PDD LoRA | ✅ **landed without waiting** (Sep 3, master backport): 8-step 600 s reproducible; **+T8 combo 210 s (−34%), 6/8 hits** — see [09](09-pdd-backport.md) |
| TE-Speed | ❌ permanently ruled out | Semantic collapse at short step counts; output ruined (see [06](06-faq.md) #9) |
| RTX VSR upscale | ✅ usable | Not a speedup but a resolution patch: 640×352 → 1080p at 47 ms/frame |

The original combined target once the window opened (T8 + PDD + a fixed sage) was **3 min/clip** — the PDD+T8 combo already sits under it at 210 s.

## Current Baseline

- ComfyUI **v0.33.1**: H3 W4A8 route fully green, native AV sampling fix included (commit `bdcb886`)
- Upgrade method: GitHub direct is unstable here, so file-by-file upgrades via jsdelivr (a reference for similar network environments)

## v0.34.0 Assessment (released; decision: not upgrading)

- Focused on stability and bug fixes; highlight is streaming video transcoding (no more full-frame buffering)
- **No H3-specific changes, no loading-mechanism changes**
- Community reports of breaking bugs; we skip first versions

While everything is green, don't operate.

## The Upgrade Trigger (half-met, then resolved by the backport)

**PR #15908 "MiniMax-H3: Support PDD LoRA" was merged into master on 2026-08-28** (not shipped with v0.34.0; as of Sep 1 the latest release was still v0.34.0):

- PDD = Parallel Decoding Distillation (Alibaba PAI's official distillation acceleration, 8 NFE)
- rank-64 LoRA + a 32-interval output head bank, Δt-weighted blending per step
- Official 8-step quality **may beat** the community Turbo LoRA

**PDD field notes (mined from the PR #15908 description, ready to apply)**:

- Weights: Kijai ships ComfyUI-converted versions (`Kijai/MiniMax-H3-experimental`, `loras/`) — saves a conversion step vs the official alibaba-pai originals; FL2VA (t2v) / Ref2VA (i2v) standard versions are ~1.6 GB each, pruned variants also exist
- **No new nodes needed**: the head bank lives inside a normal LoRA file (`set_weight`/`set_bias`), loaded by the stock LoRA loader
- Sampling: **`simple` scheduler, 8 steps + shifts 12/3** — lands exactly on the 32-grid boundaries, no custom schedule
- ⚠️ The loading logic lives in ComfyUI core (`FinalLayer` reading the bank) — **on older ComfyUI the LoRA loads but does nothing; an upgrade is mandatory**

**Action item**: wait for a release containing #15908 (v0.34.1+) → run the drill → A/B PDD vs the incumbent Turbo at the same seed → swap if it wins.

**What actually happened**: we stopped waiting — see [09](09-pdd-backport.md) for the master backport and the same-seed A/B results.

## The Upgrade Drill (follow this when the window opens)

1. Back up the entire ComfyUI directory
2. jsdelivr file-by-file upgrade (just change the script's TAG to the new release)
3. Smoke trio: H3 t2v output / image pipeline / batch production
4. Any failure → roll back from backup
5. T8 test (does the node register now that the v3 Layers API is current?)
6. PDD comparison: `simple` 8 steps + shifts 12/3 with the staged Acc-8Step LoRA, vs the Turbo 4-step at the same seed
7. While at it: re-test SageAttention on sm_75 (see [03](03-sageattention-crash.md)) and the KJNodes built-in H3 Sage patch (see [06](06-faq.md) #8)
8. If it wins → make it the production default and update the verdict table here

## Pre-Window Recon (completed 2026-09-02)

- **Change scope verified**: the PDD core lives in `comfy/ldm/minimax/model.py` (~195 lines vs v0.33.1; the `FinalLayer` head bank + `_pdd_head` interval blending confirmed on master); `comfy/lora.py`'s `set_bias` depends on the actual release tag
- **Zero changes needed to the upgrade tooling**: the jsdelivr script only needs a new TAG; the path already points at Comfy-Org; the backup directory is created automatically
- **rank-256 LoRA clarified**: the official alibaba-pai/MiniMax-H3-Acc-LoRAs repo contains **only 2 LoRAs** (FL2VA/Ref2VA Acc-8Step); the `minimax_h3_ref_lora_rank_256_bf16` (2.4G) in Kijai's repo is **not part of the PDD family** — undocumented, deferred
- **Free quality evidence**: the Acc repo's `results/` hosts three same-scene 768p comparison videos (baseline vs turbo 4-step vs acc 8-step) plus a `minimax_h3_pdd.py` reference implementation. Eyeball verdict: acc 8-step is on par with turbo; whether it replaces the production default is decided by a same-seed test
- ⚠️ The Acc repo's license is `other` (non-standard) — read the model card terms before commercial use

## Timeliness Notes (verified 2026-09-01)

- **The T8 dual-clock sampler was officially open-sourced** (hailuoai.com/h3-open), officially claimed +100% — but it needs the v3 Layers API, and whether Turing benefits depends on the implementation; verify at the upgrade window. The node pack (T8mars/comfyui-minimax-h3-blockcache-T8) latest commit 2026-08-24 — what's installed here is current
- **No new SageAttention**: the latest tag is still v2.2.0 (the version measured crashing on sm_75); re-testing must wait for upstream or a new triton-windows — try again at the upgrade window
- **DualClockSampler is retired**: ComfyUI ≥ commit `bdcb886` handles H3 AV sampling natively; the plugin only remains for old-workflow compatibility (upstream merged native-av-compat on Aug 7; latest version installed here)
- **The repo moved to Comfy-Org**: comfyanonymous/ComfyUI → Comfy-Org/ComfyUI (API 301) — the jsdelivr upgrade path already used `gh/Comfy-Org/ComfyUI`, zero impact
- H3 Max (fal.ai post-trained edition): **API-only, no open weights** — unusable locally; pay per clip for critical shots, or wait for an open follow-up
