#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T8 BlockCache A/B harness for the 4-step Turbo route (see docs/08).

Runs your own t2v workflow (API format) with and without the T8 node,
same seed, and times both. Requires ComfyUI running on 127.0.0.1:8188
and a workflow JSON whose top level is {"api": {...}} (ComfyAgent layout)
or a bare API-format graph - adjust WF loading below to taste.

Usage:
  python t8_ab_test.example.py          # WITH T8 (aggressive: threshold 1.0)
  python t8_ab_test.example.py control  # WITHOUT T8 (baseline)

Insertion point: MODEL chain, after the acceleration LoRA, before the
guider/scheduler consumers. v3-API nodes need EVERY input passed
explicitly over /prompt - server-side defaults are not applied.
"""
import json, os, sys, time, urllib.request, uuid

API = "http://127.0.0.1:8188"
SEED = 3013
# edit to point at your workflow (ComfyAgent wrapper layout shown)
WF = os.path.expandvars(r"%APPDATA%\ComfyAgent\data\workflows\h3_t2v.json")
USE_T8 = (len(sys.argv) < 2 or sys.argv[1] != "control")
T8_NODE = "200"          # any unused node id in your graph
MODEL_SRC = "105:201"    # node id whose MODEL output feeds the guider
CONSUMERS = ["7", "9"]   # node ids taking that MODEL (guider, scheduler)

g = json.load(open(WF, encoding="utf-8"))
g = g["api"] if "api" in g else g
g["10"]["inputs"]["noise_seed"] = SEED  # the RandomNoise node in this graph

if USE_T8:
    g[T8_NODE] = {
        "class_type": "MiniMaxH3BlockCacheT8",
        "inputs": {
            "model": [MODEL_SRC, 0],
            # defaults are useless at 4 steps (0/4 hits); aggressive = 2/4 hits
            "residual_diff_threshold": 1.0,
            "start_percent": 0.0, "end_percent": 1.0,
            "max_consecutive_hits": 10,
            "cache_device": "cpu", "metric_stride": 8, "verbose": True,
        },
    }
    for c in CONSUMERS:
        g[c]["inputs"]["model"] = [T8_NODE, 0]

tag = "t8" if USE_T8 else "control"
req = urllib.request.Request(API + "/prompt",
    data=json.dumps({"prompt": g, "client_id": "t8-ab-" + tag}).encode(),
    headers={"Content-Type": "application/json"})
pid = json.loads(urllib.request.urlopen(req, timeout=30).read())["prompt_id"]
print("[%s] prompt_id=%s" % (tag, pid), flush=True)

t0 = time.time()
while True:
    time.sleep(10)
    h = json.loads(urllib.request.urlopen(API + "/history/" + pid,
                                          timeout=30).read()).get(pid)
    if h:
        st = h.get("status", {})
        if st.get("completed") or st.get("status_str") == "success":
            print("DONE %s: %.0fs (%.1f min)" % (tag, time.time()-t0,
                                                  (time.time()-t0)/60))
            break
        if st.get("status_str") == "error":
            print("ERROR:", json.dumps(st)[:400]); sys.exit(3)
    print("  %3.0fs" % (time.time()-t0), flush=True)
    if time.time()-t0 > 2400:
        print("TIMEOUT 40min"); sys.exit(5)
