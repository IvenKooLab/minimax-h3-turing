"""Tier presets - the optimization experience, as data.

Every field here was measured on a 2080Ti 22G (Turing sm_75); see the
handbook's docs/10-benchmarks for the full dataset. The two invariants that
matter most:

* ``t8=True`` tiers are NOT same-seed reproducible (cache hits fork the
  sampling trajectory) - drafts only.
* PDD tiers require a master-environment ComfyUI (PR #15908 era); on
  v0.33.x they load but do nothing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tier:
    key: str
    route: str                 # "t2v" | "i2v"
    workflow: str              # bundled data file
    lora: str
    steps: int
    t8: bool
    reproducible: bool
    env: str                   # minimum ComfyUI environment
    measured_s: int            # 2080Ti 22G reference, warm run
    notes: str = ""


TIERS: dict[str, Tier] = {
    "t2v-final": Tier(
        key="t2v-final", route="t2v",
        workflow="h3_w4a8_t2v_compat_api.json",
        lora="minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_resized_avg_rank_21_bf16.safetensors",
        steps=4, t8=False, reproducible=True, env="0.33.1+",
        measured_s=280,
        notes="Baseline. Use for everything that enters the cut.",
    ),
    "t2v-draft": Tier(
        key="t2v-draft", route="t2v",
        workflow="h3_w4a8_t2v_t8draft_api.json",
        lora="minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_resized_avg_rank_21_bf16.safetensors",
        steps=4, t8=True, reproducible=False, env="0.33.1+",
        measured_s=160,
        notes="T8 threshold 1.0. Defaults (0.12) are a negative optimization on 4-step routes.",
    ),
    "i2v-final": Tier(
        key="i2v-final", route="i2v",
        workflow="h3_w4a8_i2v_compat_api.json",
        lora="minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_resized_avg_rank_21_bf16.safetensors",
        steps=4, t8=False, reproducible=True, env="0.33.1+",
        measured_s=420,
        notes="First-frame anchored (face lock). Needs your own first-frame image.",
    ),
    "i2v-draft": Tier(
        key="i2v-draft", route="i2v",
        workflow="h3_w4a8_i2v_t8draft_api.json",
        lora="minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_resized_avg_rank_21_bf16.safetensors",
        steps=4, t8=True, reproducible=False, env="0.33.1+",
        measured_s=260,
        notes="-38%; the absolute saving (160 s) beats t2v drafts - pricier shots save more.",
    ),
    "t2v-ultra": Tier(
        key="t2v-ultra", route="t2v",
        workflow="h3_w4a8_t2v_pdd8_t8_api.json",
        lora="MiniMax-H3-FL2VA-Acc-8Step_comfy.safetensors",
        steps=8, t8=True, reproducible=False, env="master (PDD backport, see docs/09)",
        measured_s=210,
        notes="Fastest t2v + distilled quality. 6/8 hits.",
    ),
    "i2v-ultra": Tier(
        key="i2v-ultra", route="i2v",
        workflow="h3_w4a8_i2v_pdd8_t8_api.json",
        lora="MiniMax-H3-Ref2VA-Acc-8Step_comfy.safetensors",
        steps=8, t8=True, reproducible=False, env="master (PDD backport, see docs/09)",
        measured_s=192,
        notes="Fastest record in the project (-51%). Face-locked ultra drafts.",
    ),
}

# Aliases for the common questions.
ALIASES = {
    "draft": "t2v-draft",
    "final": "t2v-final",
    "fastest": "i2v-ultra",
}


def get(key: str) -> Tier:
    """Resolve a tier by key or alias. Raises KeyError with the valid keys."""
    key = ALIASES.get(key, key)
    if key not in TIERS:
        raise KeyError(f"unknown tier {key!r}; valid: {sorted(TIERS)} + aliases {sorted(ALIASES)}")
    return TIERS[key]


def reproducible_only() -> dict[str, Tier]:
    """Tiers safe for final shots (same-seed reproducible)."""
    return {k: t for k, t in TIERS.items() if t.reproducible}
