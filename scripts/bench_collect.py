#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Collect A/B benchmark runs and render the handbook's markdown tables.

The example harnesses (t8_ab_test / pdd_ab_test) print timing lines like
`DONE t8: 290s (4.8 min)` and then you copy numbers into docs by hand.
This tool closes that gap:

  # record by hand (hits are read from ComfyUI's console output)
  python bench_collect.py record t8-default 290 "0/4" "threshold 0.12"
  python bench_collect.py record control 280 - "baseline"

  # or pipe the harness output straight in
  python t8_ab_test.example.py control | python bench_collect.py pipe - "baseline"

  # render the handbook table (percent deltas vs. the `control` row)
  python bench_collect.py table

Records live in scripts/bench.jsonl (one JSON per line; commit it — it is
the raw evidence behind the tables in docs/08 and friends).
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

STORE = Path(__file__).with_name("bench.jsonl")
_DONE = re.compile(r"DONE (\S+): (\d+(?:\.\d+)?)s")


def _load() -> list[dict]:
    if not STORE.exists():
        return []
    return [json.loads(ln) for ln in STORE.read_text(encoding="utf-8").splitlines() if ln.strip()]


def record(label: str, seconds: float, hits: str, note: str) -> None:
    rec = {"ts": datetime.now().isoformat(timespec="minutes"), "label": label,
           "s": round(float(seconds), 1), "hits": hits, "note": note}
    with STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("recorded:", json.dumps(rec, ensure_ascii=False))


def table() -> None:
    rows = _load()
    if not rows:
        print("(no records yet — see `record` usage in the docstring)")
        return
    base = next((r["s"] for r in rows if r["label"] == "control"), None)
    print("| config | wall time | vs control | cache hits | note |")
    print("|---|---|---|---|---|")
    for r in rows:
        if base and r["label"] != "control":
            pct = (r["s"] - base) / base * 100
            delta = f"**{pct:+.0f}%**"
        elif r["label"] == "control":
            delta = "基准"
        else:
            delta = "—"
        s = f"{r['s']:.0f}s" if r["s"] >= 60 or r["s"] == int(r["s"]) else f"{r['s']}s"
        print(f"| {r['label']} | {s} | {delta} | {r['hits']} | {r['note']} |")


def pipe(label: str, note: str) -> None:
    """Parse `DONE <tag>: <n>s` lines from stdin; label comes from argv."""
    found = False
    for line in sys.stdin:
        m = _DONE.search(line)
        if m:
            record(label, m.group(2), "-", note)
            found = True
    if not found:
        print("no DONE line seen on stdin", file=sys.stderr)
        sys.exit(2)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "record":
        record(sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else "")
    elif cmd == "pipe":
        pipe(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif cmd == "table":
        table()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
