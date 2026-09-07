"""Environment checks - run before a production batch.

Every check maps to a handbook FAQ entry; failures here are the known ways a
batch dies hours later.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# Core weight set (docs/05 download list). File names as shipped; substitutes
# are fine if the workflow loader nodes are renamed to match.
CORE_WEIGHTS = {
    "diffusion_models": ["minimax_h3_fl2va_pruned_w4a8_mixed"],
    "text_encoders": ["qwen3vl_4b"],          # fp8_scaled / int4_convrot variants
    "clip_projections": ["mmh3-4b-ClipProj"],
    "vae": ["minimax_h3_video_vae_fp16", "minimax_h3_audio_vae_fp32"],
    "loras": ["fl2v_turbo_4step"],             # prefix match on either LoRA line
}


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def check_comfyui(base: str = "http://127.0.0.1:8188", timeout: float = 5.0) -> Check:
    try:
        urllib.request.urlopen(base + "/system_stats", timeout=timeout).read()
        return Check("comfyui_alive", True, base)
    except Exception as e:
        return Check("comfyui_alive", False, f"{base} unreachable ({e}) - start it via h3_launch")


def check_queue_clean(base: str = "http://127.0.0.1:8188", timeout: float = 10.0) -> Check:
    """A persisted queue revives jobs on restart (FAQ #3); clear it before prod."""
    try:
        q = json.loads(urllib.request.urlopen(base + "/queue", timeout=timeout).read())
        running, pending = len(q.get("queue_running", [])), len(q.get("queue_pending", []))
        ok = running == 0 and pending == 0
        return Check("queue_clean", ok, f"running={running} pending={pending}"
                     + ("" if ok else " - clear /queue before production"))
    except Exception as e:
        return Check("queue_clean", False, str(e))


def check_t8_node(base: str = "http://127.0.0.1:8188", timeout: float = 10.0) -> Check:
    """Draft tiers need MiniMaxH3BlockCacheT8 registered (docs/08)."""
    try:
        info = json.loads(urllib.request.urlopen(base + "/object_info", timeout=timeout).read())
        ok = "MiniMaxH3BlockCacheT8" in info
        return Check("t8_node", ok, "registered" if ok
                     else "missing - install T8mars node pack (draft tiers will 400)")
    except Exception as e:
        return Check("t8_node", False, str(e))


def check_weights(models_dir: str | Path) -> list[Check]:
    """Prefix-match the core weight set under a ComfyUI models directory."""
    root = Path(models_dir)
    checks: list[Check] = []
    for sub, prefixes in CORE_WEIGHTS.items():
        folder = root / sub
        present = {p.name.lower() for p in folder.glob("*.safetensors")} if folder.is_dir() else set()
        for prefix in prefixes:
            hit = any(name.startswith(prefix.lower()) or prefix.lower() in name for name in present)
            checks.append(Check(f"weights:{sub}/{prefix}", hit,
                                "found" if hit else f"not found under {folder}"))
    return checks


def run_all(base: str = "http://127.0.0.1:8188", models_dir: str | Path | None = None) -> list[Check]:
    results = [check_comfyui(base)]
    if results[0].ok:
        results.append(check_queue_clean(base))
        results.append(check_t8_node(base))
    if models_dir:
        results.extend(check_weights(models_dir))
    return results


def report(base: str = "http://127.0.0.1:8188", models_dir: str | Path | None = None) -> bool:
    """Run all checks, print a report, return overall pass."""
    results = run_all(base, models_dir)
    ok_all = True
    for c in results:
        mark = "✓" if c.ok else "✗"
        if not c.ok:
            ok_all = False
        print(f"{mark} {c.name}: {c.detail}")
    print("=> PASS" if ok_all else "=> FAIL")
    return ok_all
