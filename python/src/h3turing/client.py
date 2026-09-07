"""ComfyUI HTTP client with the operational discipline this handbook learned
the hard way:

* every request retries with backoff (ComfyUI's HTTP API lags or drops while
  the GPU is at 100% - a bare urlopen is how monitoring scripts die);
* 400 validation errors from v3-API nodes are parsed and surfaced with the
  actual missing-input list (they need EVERY parameter explicitly);
* same-seed re-submissions are silently deduplicated by ComfyUI's
  deterministic prompt_id - use :func:`bump_seed` when you truly want a
  re-render;
* polling includes stall detection (idle auto-exit and queue loss happen).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


def bump_seed(graph: dict[str, Any], delta: int = 1) -> dict[str, Any]:
    """Bump every noise_seed in the graph by ``delta`` (in place).

    Use after a crash/timeout when you want a *different* render: ComfyUI
    generates prompt_id deterministically from the input, so an unchanged
    graph is silently deduplicated. Note: on cache-accelerated tiers the
    re-render differs anyway (trajectory fork) - see the handbook FAQ #12.
    """
    for node in graph.values():
        inputs = node.get("inputs") if isinstance(node, dict) else None
        if inputs and "noise_seed" in inputs:
            inputs["noise_seed"] = int(inputs["noise_seed"]) + delta
    return graph


class ValidationError(RuntimeError):
    """ComfyUI rejected the graph; ``missing`` lists the offending inputs."""

    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        self.missing: list[tuple[str, str]] = []
        for nid, errs in (payload.get("node_errors") or {}).items():
            for e in errs.get("errors", []):
                if e.get("type") == "required_input_missing":
                    self.missing.append((nid, e.get("details") or e.get("message", "")))
        hint = ""
        if self.missing:
            hint = " (v3-API nodes need every input passed explicitly - see the handbook FAQ #11)"
        detail = "; ".join(f"node {n}: {d}" for n, d in self.missing)
        super().__init__(f"ComfyUI validation failed: {payload.get('error')}{hint} {detail}".strip())


class ComfyUI:
    def __init__(self, base: str = "http://127.0.0.1:8188",
                 timeout: float = 90.0, retries: int = 3, backoff: float = 5.0):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    # -- low level ---------------------------------------------------------
    def _call(self, path: str, payload: dict | None = None, method: str | None = None) -> dict:
        data = json.dumps(payload).encode() if payload is not None else None
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(
                    self.base + path, data=data, method=method,
                    headers={"Content-Type": "application/json"})
                return json.loads(urllib.request.urlopen(req, timeout=self.timeout).read())
            except urllib.error.HTTPError as e:
                if e.code == 400:
                    try:
                        raise ValidationError(json.loads(e.read().decode()))
                    except json.JSONDecodeError:
                        raise ValidationError({"error": {"message": e.read()[:400]}})
                last = e
            except Exception as e:  # timeout / conn refused while GPU is busy
                last = e
            time.sleep(self.backoff * (attempt + 1))
        raise RuntimeError(f"ComfyUI {self.base}{path} failed after {self.retries} attempts: {last}")

    # -- high level --------------------------------------------------------
    def alive(self) -> bool:
        try:
            self._call("/system_stats")
            return True
        except Exception:
            return False

    def queue(self) -> dict[str, list]:
        q = self._call("/queue")
        return {"running": q.get("queue_running", []),
                "pending": q.get("queue_pending", [])}

    def clear_queue(self) -> None:
        self._call("/queue", {"clear": True})

    def interrupt(self) -> None:
        self._call("/interrupt", {})

    def submit(self, graph: dict[str, Any], client_id: str = "h3turing") -> str:
        """Submit an API graph; returns prompt_id. Raises ValidationError on 400."""
        resp = self._call("/prompt", {"prompt": graph, "client_id": client_id})
        if "prompt_id" not in resp:  # defensive: some builds inline errors
            raise ValidationError(resp)
        return resp["prompt_id"]

    def history(self, prompt_id: str) -> dict[str, Any] | None:
        return self._call(f"/history/{prompt_id}").get(prompt_id)

    def wait(self, prompt_id: str, max_s: float = 1800.0,
             poll_every: float = 10.0, stall_polls: int = 5) -> dict[str, Any]:
        """Poll until the job completes. Returns the history entry.

        Raises RuntimeError on execution error, on losing the job from the
        queue without history (stall), or on ``max_s`` timeout.
        """
        t0 = time.time()
        stalled = 0
        while True:
            time.sleep(poll_every)
            try:
                h = self.history(prompt_id)
                q = self.queue()
            except Exception:
                continue  # transient API lag under GPU load - keep waiting
            if h:
                st = h.get("status", {})
                if st.get("completed") or st.get("status_str") == "success":
                    return h
                if st.get("status_str") == "error":
                    raise RuntimeError(f"execution error: {json.dumps(st)[:400]}")
                stalled = 0
            else:
                if not q["running"]:
                    stalled += 1
                    if stalled >= stall_polls:
                        raise RuntimeError(
                            f"job {prompt_id} vanished from the queue without history "
                            "(process died or job was cleared)")
                else:
                    stalled = 0
            if time.time() - t0 > max_s:
                raise RuntimeError(f"timeout after {max_s:.0f}s: {prompt_id}")

    def render(self, graph: dict[str, Any], max_s: float = 1800.0,
               client_id: str = "h3turing") -> dict[str, Any]:
        """Submit + wait. Convenience for one-shot scripts."""
        pid = self.submit(graph, client_id=client_id)
        return self.wait(pid, max_s=max_s)
