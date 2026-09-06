#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PDD vs Turbo A/B harness (t2v route; adapt WF/nodes for i2v/Ref2VA).

Same seed, same prompt, only the LoRA + step count differ — per the PR #15908
recipe (simple scheduler 8 steps + shifts 12/3 for PDD). Prints wall time and
the "Prompt executed" figure from history. Requires a master-environment
ComfyUI for the PDD legs (see docs/en/09-pdd-backport.md).

Usage:
  python pdd_ab_test.example.py turbo   # 4-step control
  python pdd_ab_test.example.py pdd     # 8-step PDD
  python pdd_ab_test.example.py pdd_t8  # 8-step PDD + T8 cache (drafts only)
"""
import json, os, sys, time, urllib.request

API = "http://127.0.0.1:8188"
SEED = 3013
# edit to your workflow (ComfyAgent {"api": {...}} wrapper or bare API graph)
WF = os.path.expandvars(r"%APPDATA%\ComfyAgent\data\workflows\h3_t2v.json")
TURBO_LORA = "minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_resized_avg_rank_21_bf16.safetensors"
PDD_LORA = "MiniMax-H3-FL2VA-Acc-8Step_comfy.safetensors"
MODE = sys.argv[1] if len(sys.argv) > 1 else "pdd"

def http(path, payload=None, tries=3):
    for i in range(tries):
        try:
            data = json.dumps(payload).encode() if payload is not None else None
            req = urllib.request.Request(API + path, data=data,
                headers={"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
        except Exception:
            if i == tries - 1: raise
            time.sleep(5)

g = json.load(open(WF, encoding="utf-8"))
g = g["api"] if "api" in g else g
g["10"]["inputs"]["noise_seed"] = SEED   # the RandomNoise node in this graph

if MODE in ("pdd", "pdd_t8"):
    g["105:201"]["inputs"]["lora_name"] = PDD_LORA
    g["9"]["inputs"]["steps"] = 8
else:
    g["105:201"]["inputs"]["lora_name"] = TURBO_LORA
    g["9"]["inputs"]["steps"] = 4

if MODE == "pdd_t8":
    # v3-API node: every input must be explicit over /prompt (no server defaults)
    g["200"] = {"class_type": "MiniMaxH3BlockCacheT8", "inputs": {
        "model": ["105:201", 0],
        "residual_diff_threshold": 1.0,
        "start_percent": 0.0, "end_percent": 1.0,
        "max_consecutive_hits": 10,
        "cache_device": "cpu", "metric_stride": 8, "verbose": True}}
    g["7"]["inputs"]["model"] = ["200", 0]   # BasicGuider
    g["9"]["inputs"]["model"] = ["200", 0]   # BasicScheduler

pid = http("/prompt", {"prompt": g, "client_id": "pdd-ab-" + MODE})["prompt_id"]
print("[%s] submitted" % MODE, flush=True)
t0 = time.time()
while True:
    time.sleep(12)
    try:
        h = http("/history/" + pid).get(pid)
    except Exception:
        continue
    if h:
        st = h.get("status", {})
        if st.get("completed") or st.get("status_str") == "success":
            print("[%s] DONE %.0fs (%.1f min)" % (MODE, time.time()-t0,
                  (time.time()-t0)/60), flush=True)
            break
        if st.get("status_str") == "error":
            print("[%s] ERROR:" % MODE, json.dumps(st)[:400], flush=True)
            sys.exit(3)
    if time.time() - t0 > 1800:
        print("[%s] TIMEOUT" % MODE, flush=True); sys.exit(5)
