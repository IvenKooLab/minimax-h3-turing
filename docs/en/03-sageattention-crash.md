# 03 · The SageAttention Crash Autopsy (Turing + torch 2.9)

This is a "failure report" — one that can save you a full day of thrashing.

## Background

The community had a clear conclusion: SageAttention **still delivers +16.8% on Turing**, and "the fallback warnings are noise, not symptoms". Sounded like a free 17% for the 2080Ti, so we ran the full integration experiment.

## Experiment Environment

| Component | Version |
|---|---|
| sageattention wheel | **2.2.0** (+cu130/torch2.9-and-higher.post4, cp39-abi3) |
| triton | triton-windows |
| Node packs | ComfyUI-KJNodes (incl. PatchSageAttentionKJ and the H3-specific node) |
| ComfyUI | v0.33.1 |
| GPU | 2080Ti 22G (sm_75) |

## Results

### ✅ Standalone kernel: works

The CUDA kernel `sageattn_qk_int8_pv_fp16_cuda` **compiled and ran successfully** on sm_75. This proves SageAttention's CUDA path (as opposed to its Triton path) is alive on Turing.

### ❌ Wired into the real H3 pipeline: native crash

With the Sage patch inserted into the H3 workflow, the ComfyUI process died with a `python313.dll` native crash — not a Python exception, a process-level death. Root cause: **SageAttention 2.2.0's Triton path fails to compile on sm_75 outright**, and the failure happens inside the pipeline where no try/except can catch it.

### Rollback verification

- All patches removed/uninstalled → the production control clip rendered normally at **340 s**, back to baseline
- The crashing workflow is archived (for re-testing after an upgrade window)

## Why the Community Says "Works" While We Crashed

The key is the **version combination**:

| | The community's +16.8% environment | This box |
|---|---|---|
| torch | 2.6.0 + cu124 | 2.9.x |
| triton | 3.2.0 | newer triton-windows |
| sageattention | 1.0.6 | 2.2.0 |

Turing support in the 1.0.6 era and the Triton-based 2.2.0 implementation are not the same code. **Don't force the new wheel, and don't comfort yourself with old conclusions.**

## Actionable Advice for Turing Users

1. On torch 2.6.0 + cu124, try sageattention **1.0.6** (the community-verified combination)
2. On torch ≥ 2.9 with 2.2.0: standalone kernels run, **but pipeline integration will crash — keep it out of production**
3. Wait for an upgrade window: if a newer SageAttention restores a non-Triton path or triton-windows gains sm_75 compilation, re-test once
4. The crash is process-level — any automated pipeline needs a "watchdog + resume from checkpoint" fallback (this box uses a same-seed re-submit mechanism for automatic recovery after crashes)

---

Next: [04 · Community tips verified](04-community-tips.md)
