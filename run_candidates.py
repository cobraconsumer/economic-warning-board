#!/usr/bin/env python3
"""
Warning Board -- candidate indicator test harness (v0.3 candidates C1, C2, C3).

Does NOT modify backtest.py. Imports the frozen, validated harness and extends
it with the rule types the candidates need, then runs the board five ways:

    baseline (v0.2.1, 20 indicators)
    baseline + C1   Business Bankruptcy Filings
    baseline + C2   Technology Investment Reversal
    baseline + C3   Small-Firm Lending Standards
    baseline + all passing candidates

and evaluates each against the acceptance criteria pre-registered in
spec-v0.3-candidates.md and spec-v0.3-candidates-C2-C3.md.

Usage:
    export FRED_API_KEY=...
    python run_candidates.py --sp500-csv spx_daily.csv --out results_v03/

C1 additionally requires a CSV of US Courts Table F-2 business filings
(12-month rolling totals, quarterly). Without it C1 is skipped automatically
and C2/C3 still run. See --bankruptcy-csv and the README section printed at
the end of this file's docstring.

Expected CSV format (header required):
    date,value
    1988-03-31,63912
    1988-06-30,63234
    ...
where `date` is the quarter-end of the 12-month period and `value` is the
business filing count for that 12-month period.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import backtest as bt


# ---------------------------------------------------------------------------
# Candidate definitions (mirrors the pre-registered amendments exactly)
# ---------------------------------------------------------------------------

C1 = {
    "id": 21, "name": "Business Bankruptcy Filings", "bucket": "B", "role": "leading",
    "fred": "CSV:bankruptcies", "freq": "q", "revised": False,
    "pub_lag_days": 45,
    "rule": "yoy_above_periods", "params": {"pct": 15.0, "periods": 4, "streak": 2},
    "scalable": ["pct"],
    "integrity_note": "Class P: unrevised but not vintage-reconstructed; 45d publication lag imposed",
}

C2 = {
    "id": 22, "name": "Technology Investment Reversal", "bucket": "B", "role": "leading",
    "fred": "A679RC1Q027SBEA", "freq": "q", "revised": True,
    "rule": "yoy_below_periods", "params": {"pct": 0.0, "periods": 4, "streak": 2},
    "scalable": [], "add_scalable": ["pct"], "add_offset": 1.5,
    "integrity_note": "Zero threshold cannot scale multiplicatively; sensitivity uses +/-1.5pp (pre-registered)",
}

C3 = {
    "id": 23, "name": "Small-Firm Lending Standards", "bucket": "A", "role": "leading",
    "fred": "DRTSCIS", "freq": "q", "revised": True,
    "rule": "level_above", "params": {"level": 20.0, "streak": 1},
    "scalable": ["level"],
    "integrity_note": "Measures bank credit conditions facing small firms. NOT a private credit measure.",
}


# ---------------------------------------------------------------------------
# Extended rule evaluation
# ---------------------------------------------------------------------------

def evaluate_ext(ind, df, D, scale=1.0):
    """Handles the new candidate rule types; delegates everything else to the
    frozen harness so existing indicators evaluate byte-identically."""
    rule = ind["rule"]
    if rule not in ("yoy_above_periods", "yoy_below_periods"):
        return bt.evaluate(ind, df, D, scale=scale)

    p = dict(ind["params"])
    # multiplicative scaling (standard)
    for k in ind.get("scalable", []):
        p[k] = p[k] * scale
    # additive scaling, for thresholds at or near zero (C2)
    if scale != 1.0:
        off = ind.get("add_offset", 0.0)
        # scale<1 means "looser"; for a below-threshold rule looser = higher pct
        signed = off if scale < 1.0 else -off
        for k in ind.get("add_scalable", []):
            p[k] = p[k] + (signed if rule == "yoy_below_periods" else -signed)

    v = df["value"].reset_index(drop=True)
    n, s = p["periods"], p["streak"]
    if len(v) < n + s:
        return None, {}
    yoy = bt._yoy(v, n)
    cond = yoy < p["pct"] if rule == "yoy_below_periods" else yoy > p["pct"]
    return bt._streak_at_end(cond, s), {}


class ExtStore(bt.SeriesStore):
    """Adds CSV-backed series with an explicit publication lag."""

    def __init__(self, fred, sp500_csv=None, csv_sources=None):
        super().__init__(fred, sp500_csv)
        self.csvs = {}
        for key, path in (csv_sources or {}).items():
            if not path or not Path(path).exists():
                continue
            raw = pd.read_csv(path)
            raw.columns = [c.strip().lower() for c in raw.columns]
            df = pd.DataFrame({
                "date": pd.to_datetime(raw["date"]),
                "value": pd.to_numeric(raw["value"], errors="coerce"),
            }).dropna().sort_values("date").reset_index(drop=True)
            self.csvs[key] = df
            print(f"  loaded {key}: {len(df)} rows, "
                  f"{df.date.min().date()} to {df.date.max().date()}", file=sys.stderr)

    def asof(self, ind, D):
        sid = ind["fred"]
        if sid.startswith("CSV:"):
            key = sid[4:]
            if key not in self.csvs:
                return None, "missing"
            df = self.csvs[key]
            lag = pd.Timedelta(days=ind.get("pub_lag_days", 45))
            visible = df[df["date"] + lag <= pd.Timestamp(D)]
            if visible.empty:
                return None, "missing"
            return visible, "P"
        return super().asof(ind, D)


def run_board_ext(spec, store, dates, scale=1.0, curve_variant="b", quiet=True):
    """Copy of bt.run_board that routes through evaluate_ext."""
    rows = []
    for i, D in enumerate(dates):
        if not quiet and i % 48 == 0:
            print(f"    {D} ({i+1}/{len(dates)})", file=sys.stderr)
        row = {"date": D}
        for ind in spec["indicators"]:
            key = f"i{ind['id']:02d}"
            df, integrity = store.asof(ind, D)
            if df is None or df.empty or bt.is_stale(ind, df, D, spec["staleness_days"]):
                row[key], row[key + "_q"] = np.nan, "missing"
                continue
            red, detail = evaluate_ext(ind, df, D, scale=scale)
            if red is None:
                row[key], row[key + "_q"] = np.nan, "short"
                continue
            if ind["rule"] == "curve" and curve_variant == "b":
                red = detail["variant_b"]
            row[key] = int(red)
            row[key + "_q"] = integrity
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

TIER_ORDER = {"-": 0, "WATCH": 1, "WARNING": 2, "BROAD": 3}


def leads_and_fps(scored, spec):
    """Returns (leads dict, fp dict, ignition list)."""
    s = scored.set_index("date")
    leads = {}
    for rec in spec["nber_recessions"]:
        start = datetime.strptime(rec["start"], "%Y-%m-%d").date()
        w = s[(s.index >= start - timedelta(days=760)) & (s.index <= start)]
        entry = {}
        for tier in ("WATCH", "WARNING", "BROAD"):
            hits = w[w["tier"].map(TIER_ORDER) >= TIER_ORDER[tier]]
            entry[tier] = bt.months_between(hits.index[0], start) if not hits.empty else None
        leads[rec["name"]] = entry

    fps = {}
    for wdef in spec["false_positive_windows"]:
        ws = datetime.strptime(wdef["start"], "%Y-%m-%d").date()
        we = datetime.strptime(wdef["end"], "%Y-%m-%d").date()
        w = s[(s.index >= ws) & (s.index <= we)]
        if w.empty:
            fps[wdef["name"]] = {"peak": None, "worst": None}
            continue
        worst = max(w["tier"], key=lambda t: TIER_ORDER[t])
        fps[wdef["name"]] = {"peak": float(w["fraction"].max()), "worst": worst}
    return leads, fps, scored.attrs.get("c_ignition_events", [])


def redundancy(board, id_a, id_b):
    """Fraction of 'either red' months where the two indicators disagree."""
    a, b = board.get(f"i{id_a:02d}"), board.get(f"i{id_b:02d}")
    if a is None or b is None:
        return None
    df = pd.DataFrame({"a": a, "b": b}).dropna()
    either = df[(df.a == 1) | (df.b == 1)]
    if either.empty:
        return None
    return float((either.a != either.b).mean())


def verdict(name, base_leads, base_fps, cand_leads, cand_fps, extra_notes):
    """Applies the pre-registered acceptance criteria."""
    fails, notes = [], list(extra_notes)

    # 1. no new Warning/Broad in control windows
    for w, cf in cand_fps.items():
        bw = base_fps.get(w, {})
        if cf["worst"] is None or bw.get("worst") is None:
            continue
        if TIER_ORDER[cf["worst"]] > TIER_ORDER[bw["worst"]] and TIER_ORDER[cf["worst"]] >= 2:
            fails.append(f"raised {w} from {bw['worst']} to {cf['worst']}")

    # 2. red before/at onset in >= 2 of 3 pre-2020 recessions
    #    (proxied by the board reaching Watch, checked per-indicator separately)

    # 3. no reduction in Watch lead for 2001 or 2007
    for era in ("2001", "2007-09"):
        b = base_leads.get(era, {}).get("WATCH")
        c = cand_leads.get(era, {}).get("WATCH")
        if b is not None and (c is None or c < b):
            fails.append(f"{era} Watch lead {b}->{c} mo")

    return ("PASS" if not fails else "FAIL"), fails, notes


def indicator_red_before_onset(board, ind_id, spec, months_window=24):
    """Was this single indicator red at any point in the 24 months before onset?"""
    b = board.set_index("date")
    col = f"i{ind_id:02d}"
    out = {}
    for rec in spec["nber_recessions"]:
        if rec.get("external_shock"):
            continue
        start = datetime.strptime(rec["start"], "%Y-%m-%d").date()
        w = b[(b.index >= start - timedelta(days=months_window * 31)) & (b.index <= start)]
        vals = w[col].dropna() if col in w else pd.Series(dtype=float)
        out[rec["name"]] = bool((vals == 1).any()) if len(vals) else None
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="spec_v021.json")
    ap.add_argument("--start", default="1988-01")
    ap.add_argument("--end", default=date.today().strftime("%Y-%m"))
    ap.add_argument("--out", default="results_v03")
    ap.add_argument("--cache", default=".fred_cache")
    ap.add_argument("--sp500-csv", default=None)
    ap.add_argument("--bankruptcy-csv", default="bankruptcies.csv")
    ap.add_argument("--curve-variant", default="b", choices=["a", "b"])
    ap.add_argument("--sensitivity", action="store_true")
    args = ap.parse_args()

    key = os.environ.get("FRED_API_KEY")
    if not key:
        sys.exit("Set FRED_API_KEY")

    base_spec = json.loads(Path(args.spec).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fred = bt.Fred(key, Path(args.cache))
    print("Loading CSV sources:", file=sys.stderr)
    store = ExtStore(fred, sp500_csv=args.sp500_csv,
                     csv_sources={"bankruptcies": args.bankruptcy_csv})
    dates = bt.month_grid(args.start, args.end)

    candidates = [C2, C3]
    if "bankruptcies" in store.csvs:
        candidates.insert(0, C1)
    else:
        print(f"\n!! C1 skipped: no {args.bankruptcy_csv} found. C2/C3 will still run.\n",
              file=sys.stderr)

    def spec_with(cands):
        s = json.loads(json.dumps(base_spec))
        s["indicators"] = s["indicators"] + list(cands)
        return s

    # ---- baseline -------------------------------------------------------
    print("== baseline (v0.2.1) ==", file=sys.stderr)
    base_board = run_board_ext(base_spec, store, dates, curve_variant=args.curve_variant)
    base_scored = bt.score_board(base_board, base_spec)
    base_leads, base_fps, base_ig = leads_and_fps(base_scored, base_spec)
    base_board.to_csv(out / "board_baseline.csv", index=False)

    results = {}

    # ---- each candidate alone ------------------------------------------
    for cand in candidates:
        tag = f"C{cand['id'] - 20}"
        print(f"== {tag}: {cand['name']} ==", file=sys.stderr)
        sp = spec_with([cand])
        board = run_board_ext(sp, store, dates, curve_variant=args.curve_variant)
        scored = bt.score_board(board, sp)
        cl, cf, ig = leads_and_fps(scored, sp)
        board.to_csv(out / f"board_{tag}.csv", index=False)
        scored.to_csv(out / f"scored_{tag}.csv", index=False)

        notes = []
        # criterion 2: indicator itself red before/at onset in >=2 of 3
        own = indicator_red_before_onset(board, cand["id"], sp)
        hits = sum(1 for v in own.values() if v)
        notes.append(f"own red pre-onset: {own} ({hits}/3)")
        if hits < 2:
            notes.append("CRITERION 2 FAIL: red in fewer than 2 of 3 recessions")

        # C3-specific redundancy criterion vs #6
        if cand["id"] == 23:
            r = redundancy(board, 6, 23)
            notes.append(f"disagreement with #6 (DRTSCILM): "
                         f"{'n/a' if r is None else f'{r:.0%}'} (needs >=25%)")
            if r is not None and r < 0.25:
                notes.append("CRITERION FAIL: redundant with #6")

        v, fails, notes = verdict(tag, base_leads, base_fps, cl, cf, notes)
        if any("CRITERION" in n for n in notes):
            v = "FAIL"
        results[tag] = {"name": cand["name"], "verdict": v, "fails": fails,
                        "notes": notes, "leads": cl, "fps": cf,
                        "ignition": [str(d) for d in ig]}

    # ---- all candidates together ---------------------------------------
    print("== all candidates ==", file=sys.stderr)
    sp_all = spec_with(candidates)
    board_all = run_board_ext(sp_all, store, dates, curve_variant=args.curve_variant)
    scored_all = bt.score_board(board_all, sp_all)
    al, af, aig = leads_and_fps(scored_all, sp_all)
    board_all.to_csv(out / "board_all.csv", index=False)
    scored_all.to_csv(out / "scored_all.csv", index=False)

    # ---- sensitivity ----------------------------------------------------
    sens = {}
    if args.sensitivity:
        print("== sensitivity on full candidate board ==", file=sys.stderr)
        for scale in (0.8, 1.2):
            b = run_board_ext(sp_all, store, dates, scale=scale,
                              curve_variant=args.curve_variant)
            sc = bt.score_board(b, sp_all)
            sl, sf, _ = leads_and_fps(sc, sp_all)
            sens[scale] = {"leads": sl, "fps": sf}

    # ---- report ---------------------------------------------------------
    lines = ["=" * 74, "CANDIDATE EVALUATION -- v0.3", "=" * 74, ""]

    def fmt_leads(d):
        return "  ".join(
            f"{era}: W{v['WATCH'] if v['WATCH'] is not None else '-'}"
            f"/Wn{v['WARNING'] if v['WARNING'] is not None else '-'}"
            for era, v in d.items() if era != "2020")

    lines += ["BASELINE (v0.2.1, 20 indicators)",
              "  Watch/Warning lead months: " + fmt_leads(base_leads),
              "  control windows: " + ", ".join(
                  f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in base_fps.items()
                  if v["peak"] is not None), ""]

    for tag, r in results.items():
        lines += [f"{tag} -- {r['name']}: {r['verdict']}",
                  "  Watch/Warning lead months: " + fmt_leads(r["leads"]),
                  "  control windows: " + ", ".join(
                      f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in r["fps"].items()
                      if v["peak"] is not None)]
        for n in r["notes"]:
            lines.append(f"  note: {n}")
        for f in r["fails"]:
            lines.append(f"  FAIL: {f}")
        lines.append("")

    lines += ["ALL CANDIDATES TOGETHER",
              "  Watch/Warning lead months: " + fmt_leads(al),
              "  control windows: " + ", ".join(
                  f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in af.items()
                  if v["peak"] is not None),
              f"  C-ignition events: {[str(d) for d in aig]}", ""]

    if sens:
        lines.append("SENSITIVITY (full candidate board)")
        for scale, d in sens.items():
            bad = [k for k, v in d["fps"].items() if v["worst"] == "BROAD"]
            lines.append(f"  x{scale}: " + fmt_leads(d["leads"])
                         + f"   false BROAD: {bad if bad else 'none'}")
        lines.append("")

    # current reading with candidates
    last = scored_all.iloc[-1]
    lines += ["CURRENT READING (with candidates)",
              f"  {last['date']}  {int(last['reds'])}/{int(last['available'])} "
              f"({last['fraction']:.0%})  {last['tier']}"
              f"  [A:{int(last['A_red'])} B:{int(last['B_red'])} C:{int(last['C_red'])}]", ""]

    lines += ["DECISION",
              "  Candidates marked PASS meet every pre-registered criterion and may",
              "  join the board as v0.3. Candidates marked FAIL are recorded as",
              "  tested-and-rejected and must NOT be retained as commentary."]

    report = "\n".join(lines)
    (out / "candidate_report.txt").write_text(report)
    json.dump(results, open(out / "candidate_results.json", "w"), indent=2, default=str)
    print("\n" + report)
    print(f"\nWritten to {out}/")


if __name__ == "__main__":
    main()
