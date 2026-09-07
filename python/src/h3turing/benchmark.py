"""Same-seed A/B benchmark harness - the methodology from the handbook, as code.

Two rules it enforces for you:

1. Same seed, same prompt, ONE variable - anything else is not an A/B.
2. Timings are warm-run wall clock; expect ±10% drift under background load.
   Cache hit counts (verbose mode) are the environment-independent metric.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .client import ComfyUI


@dataclass
class Result:
    label: str
    wall_s: float
    outputs: list[str] = field(default_factory=list)
    cache_hits: str | None = None   # e.g. "6/8" - requires T8 verbose=True and log_path
    error: str | None = None


def _parse_hits(log_path: str | None, since: float) -> str | None:
    """Scan ComfyUI's server log (appended since ``since`` epoch) for the
    latest 'cached X/N model forwards' line. Requires T8 verbose=True."""
    if not log_path:
        return None
    import os
    import re
    try:
        if os.path.getsize(log_path) < since:
            return None
        hits = None
        with open(log_path, "rb") as f:
            f.seek(max(0, int(since) - 4096))
            chunk = f.read().decode("utf-8", errors="replace")
        for m in re.finditer(r"cached (\d+)/(\d+) model forwards", chunk):
            hits = f"{m.group(1)}/{m.group(2)}"
        return hits
    except OSError:
        return None


def ab_pair(comfy: ComfyUI, graphs: dict[str, dict[str, Any]],
            log_path: str | None = None, max_s: float = 1800.0) -> dict[str, Result]:
    """Run labelled graphs sequentially (same GPU conditions), return results.

    ``graphs`` = {"control": graph, "treatment": graph}. The control runs
    first (cold), so for honest comparisons re-run the control warm or
    compare treatment-vs-treatment from the same warm state.
    """
    out: dict[str, Result] = {}
    for label, graph in graphs.items():
        mark = time.time()
        pid = comfy.submit(graph, client_id="h3turing-ab-" + label)
        h = comfy.wait(pid, max_s=max_s)
        wall = time.time() - mark
        outputs = []
        for node_out in h.get("outputs", {}).values():
            for key in ("gifs", "videos", "images"):
                for item in node_out.get(key, []):
                    if item.get("filename"):
                        outputs.append(item["filename"])
        hits = _parse_hits(log_path, mark) if log_path else None
        out[label] = Result(label=label, wall_s=wall, outputs=outputs, cache_hits=hits)
        print(f"[{label}] {wall:.0f}s hits={hits or '-'} outputs={outputs}", flush=True)
    return out


def speedup(control: Result, treatment: Result) -> float:
    """Percentage change (negative = treatment is faster)."""
    if control.wall_s <= 0:
        raise ValueError("control has no valid timing")
    return (treatment.wall_s - control.wall_s) / control.wall_s * 100.0


def save_report(results: dict[str, Result], path: str, meta: dict[str, Any] | None = None) -> None:
    import json
    payload = {k: vars(v) for k, v in results.items()}
    if meta:
        payload["_meta"] = meta
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
