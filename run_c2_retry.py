#!/usr/bin/env python3
"""
Retry of the v0.3 C2 candidate ("Technology Investment Reversal") using the
real (inflation-adjusted) series instead of the nominal one that made it
fail, per spec-v0.4-candidate-C2-retry.md. Read that file first -- the
acceptance criteria are pre-registered there, before this runs.

Reuses backtest.py and run_candidates.py's machinery unmodified.

Usage:
    export FRED_API_KEY=...
    python run_c2_retry.py --sp500-csv spx_daily.csv --out results_v04_retry/
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

import backtest as bt
import run_candidates as rc

C2_RETRY = {
    "id": 22, "name": "Real Tech Investment Reversal", "bucket": "B", "role": "leading",
    "fred": "B679RA3Q086SBEA", "freq": "q", "revised": True,
    "rule": "yoy_below_periods", "params": {"pct": 0.0, "periods": 4, "streak": 2},
    "scalable": [], "add_scalable": ["pct"], "add_offset": 1.5,
    "integrity_note": ("Real (chained quantity index, 2017=100) counterpart of "
                        "A679RC1Q027SBEA, the nominal series that made v0.3's C2 fail. "
                        "Retry per CHANGELOG's stated future-candidate note."),
}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="spec_v03.json")
    ap.add_argument("--start", default="1988-01")
    ap.add_argument("--end", default=date.today().strftime("%Y-%m"))
    ap.add_argument("--out", default="results_v04_retry")
    ap.add_argument("--cache", default=".fred_cache")
    ap.add_argument("--sp500-csv", default=None)
    ap.add_argument("--curve-variant", default="b", choices=["a", "b"])
    args = ap.parse_args()

    key = os.environ.get("FRED_API_KEY")
    if not key:
        sys.exit("Set FRED_API_KEY")

    base_spec = json.loads(Path(args.spec).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fred = bt.Fred(key, Path(args.cache))
    store = rc.ExtStore(fred, sp500_csv=args.sp500_csv, csv_sources={})
    dates = bt.month_grid(args.start, args.end)

    print("== baseline (v0.3, 20 indicators) ==", file=sys.stderr)
    base_board = rc.run_board_ext(base_spec, store, dates, curve_variant=args.curve_variant)
    base_scored = bt.score_board(base_board, base_spec)
    base_leads, base_fps, base_ig = rc.leads_and_fps(base_scored, base_spec)

    print("== C2 retry: Real Tech Investment Reversal ==", file=sys.stderr)
    sp = json.loads(json.dumps(base_spec))
    sp["indicators"] = sp["indicators"] + [C2_RETRY]
    board = rc.run_board_ext(sp, store, dates, curve_variant=args.curve_variant)
    scored = bt.score_board(board, sp)
    cl, cf, ig = rc.leads_and_fps(scored, sp)
    board.to_csv(out / "board_C2retry.csv", index=False)
    scored.to_csv(out / "scored_C2retry.csv", index=False)

    notes = []
    own = rc.indicator_red_before_onset(board, C2_RETRY["id"], sp)
    hits = sum(1 for v in own.values() if v)
    notes.append(f"own red pre-onset: {own} ({hits}/3)")
    if hits < 2:
        notes.append("CRITERION 2 FAIL: red in fewer than 2 of 3 recessions")

    verdict, fails, notes = rc.verdict("C2retry", base_leads, base_fps, cl, cf, notes)
    if any("CRITERION" in n for n in notes):
        verdict = "FAIL"

    print("\n== Sensitivity: +/-1.5pp ==", file=sys.stderr)
    sens = {}
    for scale in (0.8, 1.2):
        b = rc.run_board_ext(sp, store, dates, scale=scale, curve_variant=args.curve_variant)
        sc = bt.score_board(b, sp)
        sl, sf, _ = rc.leads_and_fps(sc, sp)
        sens[scale] = {"leads": sl, "fps": sf}
        for w, v in sf.items():
            if v["worst"] == "BROAD" and base_fps.get(w, {}).get("worst") != "BROAD":
                fails.append(f"sensitivity x{scale}: false BROAD in {w}")
                verdict = "FAIL"

    def fmt_leads(d):
        return "  ".join(
            f"{era}: W{v['WATCH'] if v['WATCH'] is not None else '-'}"
            f"/Wn{v['WARNING'] if v['WARNING'] is not None else '-'}"
            for era, v in d.items() if era != "2020")

    lines = ["=" * 74, "C2 RETRY -- Real Tech Investment Reversal (spec-v0.4-candidate-C2-retry.md)",
              "=" * 74, "",
              "BASELINE (v0.3, 20 indicators)",
              "  Watch/Warning lead months: " + fmt_leads(base_leads),
              "  control windows: " + ", ".join(
                  f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in base_fps.items()
                  if v["peak"] is not None), "",
              f"C2 RETRY: {verdict}",
              "  Watch/Warning lead months: " + fmt_leads(cl),
              "  control windows: " + ", ".join(
                  f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in cf.items()
                  if v["peak"] is not None)]
    for n in notes:
        lines.append(f"  note: {n}")
    for f in fails:
        lines.append(f"  FAIL: {f}")
    lines.append("")
    lines.append("SENSITIVITY (+/-1.5pp)")
    for scale, d in sens.items():
        bad = [k for k, v in d["fps"].items() if v["worst"] == "BROAD"]
        lines.append(f"  x{scale}: " + fmt_leads(d["leads"]) + f"   false BROAD: {bad if bad else 'none'}")
    lines.append("")

    last = scored.iloc[-1]
    lines += ["CURRENT READING (with C2 retry)",
              f"  {last['date']}  {int(last['reds'])}/{int(last['available'])} "
              f"({last['fraction']:.0%})  {last['tier']}", "",
              "DECISION",
              f"  {verdict}. " + (
                  "Meets every pre-registered criterion; may be proposed for a future spec."
                  if verdict == "PASS" else
                  "Recorded as tested-and-rejected. Must not be retained as commentary."
              )]

    report = "\n".join(lines)
    (out / "c2_retry_report.txt").write_text(report)
    print("\n" + report)
    print(f"\nWritten to {out}/")


if __name__ == "__main__":
    main()
