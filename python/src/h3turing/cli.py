"""Command-line interface.

    h3turing doctor  [--base URL] [--models-dir DIR]
    h3turing bench   --a TIER --b TIER [--seed N] [--prompt TEXT]
                     [--log-path FILE] [--base URL] [--out FILE]
    h3turing tiers

Exit codes: 0 = success, 1 = checks failed / runtime error, 2 = bad usage.
"""

from __future__ import annotations

import argparse
import sys

DEFAULT_PROMPT = ("cinematic wide shot, a lone swordsman walking through a misty "
                  "bamboo forest at dawn, natural ambient audio")


def _cmd_doctor(args) -> int:
    from . import doctor
    ok = doctor.report(base=args.base, models_dir=args.models_dir)
    return 0 if ok else 1


def _cmd_tiers(_args) -> int:
    from .tiers import TIERS
    print(f"{'key':<12} {'route':<5} {'T8':<3} {'repro':<5} {'measured':>9}  env")
    for key, t in sorted(TIERS.items()):
        print(f"{key:<12} {t.route:<5} {'yes' if t.t8 else 'no':<3} "
              f"{'yes' if t.reproducible else 'NO':<5} {t.measured_s:>7}s  {t.env}")
    print("\ndraft tiers (T8) are NOT same-seed reproducible - finals only from plain tiers")
    return 0


def _cmd_bench(args) -> int:
    from .benchmark import ab_pair, save_report, speedup
    from .client import ComfyUI
    from .tiers import get
    from .workflows import load, set_prompt, set_seed

    comfy = ComfyUI(base=args.base)
    graphs = {}
    for label, key in (("control", args.a), ("treatment", args.b)):
        tier = get(key)
        g = load(tier.workflow)
        set_prompt(g, args.prompt)
        set_seed(g, args.seed)   # same seed across arms - the A/B invariant
        graphs[label] = g

    print(f"A/B: {args.a} (control) vs {args.b} (treatment) | seed {args.seed}", flush=True)
    results = ab_pair(comfy, graphs, log_path=args.log_path, max_s=args.max_s)
    delta = speedup(results["control"], results["treatment"])
    print(f"\n=> treatment {delta:+.1f}% vs control "
          f"({results['treatment'].wall_s:.0f}s vs {results['control'].wall_s:.0f}s)")
    if args.out:
        save_report(results, args.out, meta={"a": args.a, "b": args.b, "seed": args.seed})
        print("report saved:", args.out)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="h3turing",
        description="Field-tested toolkit for MiniMax H3 on Turing GPUs (see the handbook)")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="pre-production checks (ComfyUI alive, queue, T8 node, weights)")
    d.add_argument("--base", default="http://127.0.0.1:8188")
    d.add_argument("--models-dir", default=None, help="ComfyUI models dir for weight checks")

    b = sub.add_parser("bench", help="same-seed A/B benchmark between two tiers")
    b.add_argument("--a", required=True, help="control tier key (e.g. t2v-final)")
    b.add_argument("--b", required=True, help="treatment tier key (e.g. t2v-draft)")
    b.add_argument("--seed", type=int, default=3013)
    b.add_argument("--prompt", default=DEFAULT_PROMPT)
    b.add_argument("--log-path", default=None,
                   help="ComfyUI server log for cache-hit parsing (T8 verbose=True required)")
    b.add_argument("--base", default="http://127.0.0.1:8188")
    b.add_argument("--max-s", type=float, default=1800.0)
    b.add_argument("--out", default=None, help="save JSON report to this path")

    sub.add_parser("tiers", help="list the six tiers with measured timings")

    args = p.parse_args(argv)
    handlers = {"doctor": _cmd_doctor, "bench": _cmd_bench, "tiers": _cmd_tiers}
    try:
        return handlers[args.cmd](args)
    except KeyboardInterrupt:
        print("\ninterrupted")
        return 130
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
