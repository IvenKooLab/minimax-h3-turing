# minimax-h3-turing

English | [简体中文](README.md)

**A field-tested handbook for running MiniMax H3 local video generation on a 2080Ti 22G mod card (Turing / sm_75).**

Every conclusion here comes from a real production pipeline, not paper math. Applies to all Turing (sm_75) GPUs — 2080Ti 22G / 11G both work; the closer your VRAM is to 22G, the closer you are to this configuration.

## The Speed System at a Glance

One main path: official tutorial reference (20–30 min/clip) → cu130 dequantization + W4A8 → three acceleration branches (Turbo / T8 / PDD) → **PDD+T8 combo (210 s, 6/8 cache hits)** → the five-workflow kit.

The same 5-second clip: **20–30 min/clip** in a typical environment following the official tutorial, compressed to **4.7 min (final-shot standard) / 2.7 min (fast draft) / 3.5 min (PDD+T8 ultra draft)** — **5–11× faster**. Per-tier timings and data methodology: [08](docs/en/08-t8-blockcache-4step.md) / [09](docs/en/09-pdd-backport.md).

## What This Repo Gives You

- ✅ **Five ready-to-import workflows** (t2v/i2v, each with a final-shot tier and a T8 fast-draft tier, plus a PDD ultra tier) — all verified on real hardware, with preview screenshots: [workflows/README](workflows/README.md)
- ✅ **13 field-tested FAQ entries**: v3-node 400s on `/prompt`, same-seed re-runs diverging, idle auto-exit killing batches, antivirus slowing model loading by 27 minutes, silent prompt_id dedup drops… every one paid for in real time → [06](docs/en/06-faq.md)
- ✅ **Verdict table for every speedup route**: the full SageAttention crash autopsy, T8 BlockCache measured at −43%, TE-Speed permanently ruled out — which roads work and which are dead, so you don't have to try them again
- ✅ **A/B measurement methodology**: same-seed A/B control scripts ready to run for your own experiments → [scripts/](scripts/)

## The Optimization Roadmap

### ✅ Phase 1 · Get It Running — pick the only viable quantization route

- [x] Hardware math: sm_75 has no BF16/FP8 tensor cores and 616 GB/s bandwidth — know the ceiling first → [01](docs/en/01-hardware-limits.md)
- [x] Quantization verdict: **DiT must be INT8 (W4A8)**; W4A4 has 18× the reconstruction error and produces color tearing → [02](docs/en/02-w4a8-vs-w4a4.md)
- [x] The compat (degraded) workflows — `workflows/` imports directly

### ✅ Phase 2 · Keep It Stable — stability is the prerequisite for speed

- [x] Launch flags against TDR black-screens / OOM: `--reserve-vram 2.5 --vram-headroom 0.5 --disable-pinned-memory` → [scripts/](scripts/)
- [x] Antivirus real-time scanning slowing model loading by 27 minutes → disable while rendering, re-enable after, plus a resume-from-checkpoint fallback → [06](docs/en/06-faq.md)
- [x] Ten more pitfalls cleared: prompt_id dedup, queue residue, big-file downloads → [06](docs/en/06-faq.md)
- [x] Resolution top-up: generate at 640×352 → RTX VSR frame upscale to 1080p (47 ms/frame)

### ✅ Phase 3 · Speed Research — every route tested until it has a verdict

- [x] **The cu130 dequantization bonus**: the comfy-kitchen CUDA backend fully enabled — this is the root cause of 5.7 min vs the official 20–30 min. If W4A8 is absurdly slow on your box, check your runtime before blaming the GPU → [01](docs/en/01-hardware-limits.md)
- [x] SageAttention: Triton INT8 kernels fail to compile on sm_75 across all triton versions; the CUDA kernel runs standalone but crashes natively in the real pipeline → **ruled out**, fully rolled back → [03](docs/en/03-sageattention-crash.md)
- [x] TE-Speed: semantic collapse at short step counts → **permanently ruled out**, no new version will save it → [06](docs/en/06-faq.md)
- [x] **T8 BlockCache on real hardware: aggressive tier −43% = 2.7 min/clip**; corrected the "requires ComfyUI ≥0.34" misdiagnosis (v0.33.1 works); default params are a negative optimization on the 4-step route (0 hits); the cost = same-seed runs are no longer reproducible → drafts yes, final shots no → [08](docs/en/08-t8-blockcache-4step.md)

### ✅ Phase 4 · The Endgame — PDD, ported without waiting for the official release (Sep 3)

- [x] **PDD LoRA master backport** (no waiting for v0.34.1+): single-file wasn't enough → full upgrade with three pitfalls solved (the comfy_api blind spot / PyAV / the T8 signature) → **PDD 8-step at 600 s reproducible, and PDD+T8 combo at 210 s (−34%) with 6/8 hits** → [09](docs/en/09-pdd-backport.md)
- [x] T8 node master-compat patch (self-adapting to the 7-arg FinalLayer signature), upstream feedback pending
- [ ] PDD vs Turbo final-shot quality blind test; Ref2VA (i2v) PDD variant pending

### 💡 Phase 5 · Watchlist

- [ ] H3 Max (fal.ai post-trained edition): **API-only, no open weights** — unusable locally; pay per clip for critical shots, wait for an open follow-up → [07](docs/en/07-upgrade-watch.md)

## Documentation

| Doc | Contents |
|---|---|
| [01 Hardware limits](docs/en/01-hardware-limits.md) | What sm_75 lacks, the bandwidth gap, the cu130 bonus, why W4A8 is the only route |
| [02 W4A8 vs W4A4](docs/en/02-w4a8-vs-w4a4.md) | Error data, production speed, another card's benchmark |
| [03 SageAttention crash autopsy](docs/en/03-sageattention-crash.md) | The 2.2.0 wheel pipeline crash → root-cause hunt → rollback verification |
| [04 Community tips verified](docs/en/04-community-tips.md) | Three directly-copyable tips + their applicability conditions |
| [05 Workflows](docs/en/05-workflows.md) | compat t2v/i2v import, placeholder replacement, model download list |
| [06 FAQ](docs/en/06-faq.md) | 13 entries: v3-node 400s, same-seed divergence, idle auto-exit, antivirus, prompt_id dedup, TE-Speed, audio clipping |
| [07 Upgrade-window watch](docs/en/07-upgrade-watch.md) | The full route verdict table, v0.34 assessment, PDD LoRA #15908, official T8 open-sourcing |
| [08 T8 on the 4-step route](docs/en/08-t8-blockcache-4step.md) | The −43% measurement: zero hits at defaults, 2.7 min/clip aggressive, the same-seed reproducibility cost |
| [09 PDD without waiting](docs/en/09-pdd-backport.md) | The master backport field report: PDD8+T8 **210 s (−34%), 6/8 hits**, three pitfalls solved |
| [workflows/](workflows/README.md) | The five-workflow kit (with previews): t2v/i2v × final/draft + PDD ultra, with import guide |
| [scripts/](scripts/) | Anti-black-screen launch template, T8 A/B harness, chart regen script |

## Reproduction Environment

- GPU: 2080Ti 22G mod (Turing, sm_75)
- ComfyUI: v0.33.1 baseline (the handbook also documents a full upgrade to master for PDD — see [09](docs/en/09-pdd-backport.md))
- Route: h3lite W4A8 compat + fl2v Turbo 4-step LoRA (optional T8 draft tier, see [08](docs/en/08-t8-blockcache-4step.md))

## Mirrors

| Platform | URL |
|---|---|
| Gitee (primary) | https://gitee.com/IvenKooLab/minimax-h3-turing |
| GitHub | https://github.com/IvenKooLab/minimax-h3-turing |

Both are auto-synced (Gitee is the authoritative source).

## License

MIT
