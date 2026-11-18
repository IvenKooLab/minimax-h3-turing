# AGENTS.md — guide for AI coding agents

This repo is a field-tested handbook for running **MiniMax H3 video generation** on Turing
(sm_75) GPUs via ComfyUI. If you are an AI agent asked to "get H3 running", follow this
file top-to-bottom. All claims are backed by real runs; the benchmark dataset lives in
`docs/10-benchmarks.md`.

## The 6-step quick path

1. **Install ComfyUI** (any version >= 0.33; serve on port 8188)
2. **Download 5 weight files** (China: swap `huggingface.co` for `hf-mirror.com`):
   - `diffusion_models/minimax_h3_fl2va_pruned_w4a8_mixed.safetensors` (12.5 GB) → `models/diffusion_models/`
   - `text_encoders/qwen3vl_4b_fp8_scaled.safetensors` (5.2 GB) → `models/text_encoders/`
   - `vae/minimax_h3_video_vae_fp16.safetensors` + `minimax_h3_audio_vae_fp32.safetensors` → `models/vae/`
   - ClipProj: `mmh3-4b-ClipProj-celeb-mlp.safetensors` from `NicoLab28/ClipProj-MiniMax-H3` → `models/clip_projections/`
   - LoRA: `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_resized_avg_rank_21_bf16.safetensors` → `models/loras/`
   (full list with alternates: `docs/05-workflows.md`)
3. **Launch ComfyUI** with the memory-safe flags: `--reserve-vram 2.5 --vram-headroom 0.5 --disable-pinned-memory` (template: `scripts/h3_launch.example.sh`)
4. **Load** `workflows/h3_w4a8_t2v_compat_api.json`, replace the `__H3_PROMPT__` placeholder, queue it
5. **Expect**: 640×352 · 124 frames (~5 s) · native audio · ~280 s on a 2080Ti 22G
6. **Problems**: `docs/06-faq.md` covers 13 field-tested pitfalls (antivirus slowing model
   loading by 27 min, silent prompt_id dedup on re-submits, TDR black screens…)

## Speed tiers (optional)

- **Draft / shot selection**: add the T8 BlockCache node — `workflows/h3_w4a8_t2v_t8draft_api.json` (−43%, threshold 1.0, all 8 inputs explicit). NOT same-seed reproducible (see docs/08)
- **Final shots**: the plain 4-step tier (reproducible, resume-safe)

## GUI alternative for end users

[ComfyAgent](https://github.com/IvenKooLab/comfy-agent) — a desktop companion that
bundles these workflows with a Chinese-first UI, model manager, batch production and a
watchdog. Chinese prompts supported (built-in zh→en enhancement).

## Docs map (bilingual: Chinese in `docs/`, English in `docs/en/`)

| Doc | Contents |
|---|---|
| 01 | Hardware limits (sm_75), the cu130 dequantization bonus |
| 02 | W4A8 vs W4A4 verdict (18× error gap) |
| 03 | SageAttention crash autopsy |
| 05 | Model download list + workflow import |
| 06 | 13-entry pitfall FAQ |
| 07 | Upgrade-window watch |
| 08 | T8 BlockCache measurements |
| 09 | PDD LoRA backport field report |
| 10 | The full benchmark dataset |

## Repo conventions for agents

- Commit messages in English; keep the `docs/` + `docs/en/` bilingual structure in sync
- The `workflows/*.json` are API-format graphs; `__H3_PROMPT__` is the prompt placeholder
- Changing any workflow JSON: update both the root `workflows/` copy and note it in
  `workflows/README.md` (Chinese + English editions live side by side)
