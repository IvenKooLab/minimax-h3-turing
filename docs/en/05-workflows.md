# 05 · The compat Workflows, Explained

## Model Download List (read this first)

The file names referenced by the workflows come from h3lite's W4A8 component Set A (a cloud-drive distribution); every measurement in this repo is based on **Route B (the HF-direct equivalent)** — the right column below is the recommended download source:

| Name referenced by workflows | Recommended actual download | Source | Target directory |
|---|---|---|---|
| minimax_h3_fl2va_pruned_w4a8_mixed_ax1y2jp.safetensors (12.5G) | minimax_h3_fl2va_pruned_w4a8_mixed.safetensors | [Kijai/MiniMax-H3-experimental](https://huggingface.co/Kijai/MiniMax-H3-experimental) | models/diffusion_models/ |
| qwen3vl_4b_int4_convrot.safetensors (2.8G) | qwen3vl_4b_fp8_scaled.safetensors (5.2G) | [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2) → text_encoders/ | models/text_encoders/ |
| mmh3-4b-ClipProj-celeb-mlp.safetensors (304M) | same name, direct | [NicoLab28/ClipProj-MiniMax-H3](https://huggingface.co/NicoLab28/ClipProj-MiniMax-H3) | models/clip_projections/ |
| minimax_h3_video_vae_fp16 / audio_vae_fp32 | same name, direct | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) → vae/ | models/vae/ |
| Turbo 4-step LoRA (fl2v/ref2v) | same name, direct | same repo → loras/ | models/loras/ |
| PDD Acc-8Step LoRA (for the fifth, ultra-draft workflow) | same name, direct | Kijai repo → loras/ | models/loras/ |

- **Renaming rule**: when using a substitute, edit the loader node's file name in the workflow JSON to match your actual download (or rename the files); the two W4A8 variants differ by ~26 KB (a quantization-config tweak) and produce identical output in our tests
- **If you insist on the ax1y2jp-named originals**: h3lite Set A, Baidu Pan `pan.baidu.com/s/1x5GGuJv0h8chApgVoDgIaQ` (code `1hjx`)
- **China mirror**: if huggingface.co won't connect, swap the domain for hf-mirror.com — paths unchanged; multi-threaded chunked downloads recommended for the big files

## Why "compat"

H3's official full workflows reference the T8 BlockCache node and full-precision model names — a **dead diagram** on a Turing card without T8 installed (missing nodes, mismatched models). The compat versions are community-maintained degradations:

- Acceleration nodes that can't run on sm_75 removed
- Model file names aligned to the W4A8 mixed weights actually in use
- The 4-step Turbo route + native audio preserved

compat + W4A8 measured as the optimum on this card (see [01](01-hardware-limits.md)) — there is no "loss" from not upgrading to the full workflows.

## Files

> Full tier matrix, three-step import, and pitfall notes: [workflows/README](../workflows/README.md).

| File | Purpose |
|---|---|
| [h3_w4a8_t2v_compat_api.json](../workflows/h3_w4a8_t2v_compat_api.json) | t2v · final-shot tier (280 s/clip, reproducible) |
| [h3_w4a8_t2v_t8draft_api.json](../workflows/h3_w4a8_t2v_t8draft_api.json) | t2v · fast-draft tier (160 s/clip, −43%, not same-seed reproducible) |
| [h3_w4a8_i2v_compat_api.json](../workflows/h3_w4a8_i2v_compat_api.json) | i2v (needs a first frame) |

## Import & Replace

1. Drag the JSON into the ComfyUI UI, or drop it in `user/default/workflows/`
2. Check the model loader nodes' file names against your local `models/` (W4A8 weight file names differ between download eras)
3. **i2v**: point the first-frame loader node at your own image (this repo ships no sample image)
4. Defaults: 640×352 · 124 frames · 4 steps · native audio

## Production Parameter Advice

- Short clips (5–6 s): use defaults, with `--reserve-vram 2.5` (see [04](04-community-tips.md))
- For 1080p deliverables: keep generating at 640×352 → extract frames → RTX VSR upscale. **Do not** raise the workflow resolution (VRAM and time both blow up)
- Write prompts in three beats: subject → action/camera → environment & light (see h3lite's official methodology)

## Common Import Failures

| Symptom | Cause |
|---|---|
| Red missing-node badges | H3 support node packs not installed (KJNodes etc.), or ComfyUI too old |
| Model loader node errors | Weight file name mismatch — double-click the node and select your local file |
| Color tearing in output | Wrong weights (W4A4) — switch to W4A8 mixed |
