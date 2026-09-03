# 06 · FAQ: Thirteen Field-Tested Pitfalls

All of these were actually hit on this box, ordered by how much they hurt.

## 1. "Model Initializing" stuck for 27 minutes

**Symptom**: the process is alive, the log sits at model initialization for 27 minutes. Normal sampling is 91 s/step — the bottleneck is nowhere near the GPU.

**Root cause**: disk loading + staging of the 12.5G model file is I/O-heavy, and **antivirus real-time protection** scans it chunk by chunk (our case was a third-party security suite, unnamed; any antivirus with active defense can do this).

**Fix**: manually disable real-time protection while rendering, re-enable after. Long batch runs additionally need a "detect stall → clean restart → resume from checkpoint" fallback (re-submit with the same seed from a graph snapshot).

## 2. Re-submissions with the same prompt_id are silently dropped

**Symptom**: after a crash you re-submit the same workflow and ComfyUI quietly does nothing. No error.

**Root cause**: H3 generates prompt_id **deterministically from the input** — same input, same id, so the frontend thinks the job already exists.

**Fix**: change an irrelevant value (e.g. seed+1) so the input changes; or clear the history manifest and re-submit.

## 3. Queue residue after killing ComfyUI

**Symptom**: after killing the process, a restart "revives" previously queued jobs.

**Root cause**: queue state is persisted to disk and restored on startup. Check here first when compute is mysteriously occupied.

**Fix**: clear the queue before shutdown if you want a clean restart; the `.submit.claim` concurrency-lock file can survive a crash and block new submissions — remove it manually.

## 4. T8 BlockCache "unusable" — that was our misdiagnosis

`MiniMaxH3BlockCacheT8` was long believed to fail registration on sm_75 ("needs the v3 Layers API, targets new architectures"). **Reversed on Sep 1 by measurement**: the node registers and runs fine on v0.33.1, delivering −43% in the aggressive tier. The real traps are that v3 nodes need every parameter passed explicitly over `/prompt` (see #11) and that the default threshold yields zero hits on a 4-step route (see [08](08-t8-blockcache-4step.md)). So the verdict is not "avoid it" — it's "configure it correctly".

## 5. aria2-downloaded model files "ghost-vanish"

**Symptom**: aria2 reports a completed download; a while later the file is gone.

**Root cause**: certain sandbox/security-software environments silently delete aria2's temp files (the `.aria2` control file plus unflushed data).

**Fix**: use a Python chunked downloader (requests + resume); far more stable. All 12.5G+ models on this box moved to that path.

## 6. pinned-memory read_file_slice OOM

`read_file_slice` failures in the launch log followed by OOM. Fix: `--disable-pinned-memory` in the launch flags — no side effects. See the launch template.

## 7. TDR black-screen on a desktop-shared GPU

When ComfyUI shares the 2080Ti with the desktop, tight VRAM triggers a driver TDR reset (screen blinks, job dies). Fix: `--reserve-vram 2.5 --vram-headroom 0.5` for desktop headroom. See the launch template.

## 8. A hidden gem inside KJNodes

KJNodes ships `MiniMaxH3MemoryEfficientSageAttentionPatch` (fused qkv + RMSRoPE, patching only the DiT self-attention) — an H3-specific native Sage patch, theoretically better-behaved than the third-party PatchSageAttentionKJ. **Not yet verified on sm_75 as of writing**; it stays on the watchlist (see [07](07-upgrade-watch.md)).

## 9. TE-Speed installs fine and destroys your output

**Symptom**: TE-Speed (text-encoder acceleration) installs and runs without errors and is genuinely faster — easy to misread as usable.

**Root cause**: H3's 4-step Turbo route has very few steps to begin with; TE-Speed's lossy compression causes **semantic collapse** at this step count — the output decouples from the prompt.

**Verdict**: **permanently ruled out** — not a version issue; no future release will fix it. For speedups see the route table in [07](07-upgrade-watch.md); don't spend time here.

## 10. Does native audio clip?

No — measured safe. ffmpeg `volumedetect`/`astats` on generated samples:

- Normal clip: mean −14.0 dB, **max −0.6 dB** (headroom before clipping)
- A louder outlier: mean −25.7 dB, max −10.2 dB

No firefighting needed. Put a **−1 dB limiter** on the final-shot pipeline as a safety net. Also: v0.33.1 already includes the native AV sampling fix (commit `bdcb886`) — if you hear distortion, check your build before reaching for fix-up plugins like DualClockSampler.

## 11. v3-API nodes return 400 when submitted via /prompt

**Symptom**: `MiniMaxH3BlockCacheT8` and other new-style nodes (the v3 `comfy_entrypoint` protocol) work fine in the ComfyUI UI, but submitting via the `/prompt` API returns 400 with a pile of `required_input_missing` — even `advanced: True` inputs count as missing.

**Root cause**: **v3 nodes do not apply server-side defaults** — every input declared in the schema must be given explicitly in the submission JSON, no exceptions. Old v2 nodes don't behave this way, which is why older tutorials don't cover it.

**Fix**: write every input (including advanced ones) explicitly into the API JSON. The draft-tier workflows in this repo's [workflows/](../workflows/README.md) are fully explicit — use them as the reference.

## 12. Cache-style accelerators break "same-seed re-runs"

**Symptom**: with T8 BlockCache or similar cache accelerators enabled, re-running with the same seed and parameters produces a **different clip**; any resume strategy built on "re-submit the failed shot with the same seed" stops working.

**Root cause**: not a bug — a cache hit reuses the previous step's residual, the numerical trajectory forks, and the same seed now walks a different sampling path. The output is a **different picture of equal quality** (measured frame PSNR around 14 dB with zero visible degradation; see [08](08-t8-blockcache-4step.md)).

**Fix**: tier your usage — drafts/shot selection on the accelerated tier (−43%), final shots on the cache-free baseline for reproducibility. The `workflows/` kit is split along exactly this line.

## 13. ComfyUI exits on idle, killing overnight batches

**Symptom**: you leave a batch running overnight and come back to a dead ComfyUI process, queue stopped mid-way.

**Root cause**: in some builds/environments ComfyUI exits after idle time (observed on v0.33.1); desktop session locks and VRAM driver resets can also trigger it.

**Fix**: long batches **must** run with a watchdog — "detect process death → clean restart → re-submit from the graph snapshot with the same seed". Never leave one bare. Save a graph snapshot before submission so restarts can resume; note that jobs using cache accelerators will change on re-submission (see the previous entry).

---

Next: [07 · Upgrade-window watch](07-upgrade-watch.md)
