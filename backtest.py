#!/usr/bin/env python3
"""
Economic Warning Board -- point-in-time backtest harness (spec v0.2, frozen).

Reconstructs the 20-light board month by month using ALFRED vintage data
(data as it existed at each evaluation date), scores alert-tier lead times
against NBER recessions, checks false-positive control windows, tests the
Bucket-C ignition hypothesis (H1), adjudicates yield-curve variants 1a/1b,
and runs the +/-20% threshold sensitivity analysis.

Usage:
    export FRED_API_KEY=yourkey
    python backtest.py --spec spec_v02.json --start 1988-01 --out results/
    python backtest.py --spec spec_v02.json --sp500-csv spx_daily.csv --sensitivity

Requires: python 3.9+, requests, pandas, numpy, matplotlib (optional, for plots).
First run downloads and caches several thousand small JSON responses; expect
30-90 minutes depending on FRED rate limiting. Subsequent runs are fast.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import requests
except ImportError:
    sys.exit("pip install requests pandas numpy matplotlib")

FRED_BASE = "https://api.stlouisfed.org/fred"
EARLIEST_REALTIME = "1776-07-04"  # ALFRED convention for 'beginning of time'


# ----------------------------------------------------------------------------
# Fetch layer with disk cache
# ----------------------------------------------------------------------------

class Fred:
    def __init__(self, api_key: str, cache_dir: Path):
        self.key = api_key
        self.cache = cache_dir
        self.cache.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    def _get(self, endpoint: str, params: dict) -> dict:
        """GET with disk cache keyed on endpoint+params (api key excluded)."""
        cache_key = hashlib.md5(
            json.dumps([endpoint, sorted(params.items())]).encode()
        ).hexdigest()
        cache_file = self.cache / f"{cache_key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())

        full = dict(params, api_key=self.key, file_type="json")
        for attempt in range(6):
            r = self.session.get(f"{FRED_BASE}/{endpoint}", params=full, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(15 * (attempt + 1))
                continue
            if r.status_code == 400 and "vintage" in r.text.lower():
                # e.g. realtime period predates first vintage
                data = {"error": r.text, "observations": []}
                cache_file.write_text(json.dumps(data))
                return data
            r.raise_for_status()
            data = r.json()
            cache_file.write_text(json.dumps(data))
            time.sleep(0.55)  # stay under 120 req/min
            return data
        raise RuntimeError(f"FRED API kept rate-limiting: {endpoint} {params}")

    def vintage_dates(self, series_id: str) -> list:
        data = self._get("series/vintagedates", {"series_id": series_id, "limit": 10000})
        return [datetime.strptime(d, "%Y-%m-%d").date() for d in data.get("vintage_dates", [])]

    def observations(self, series_id: str, realtime: str = None) -> pd.DataFrame:
        params = {"series_id": series_id, "limit": 100000,
                  "observation_start": "1950-01-01"}
        if realtime:
            params["realtime_start"] = realtime
            params["realtime_end"] = realtime
        data = self._get("series/observations", params)
        obs = data.get("observations", [])
        rows = [(o["date"], o["value"]) for o in obs if o["value"] not in (".", "", None)]
        if not rows:
            return pd.DataFrame(columns=["date", "value"])
        df = pd.DataFrame(rows, columns=["date", "value"])
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna().sort_values("date").reset_index(drop=True)


class SeriesStore:
    """Serves each series 'as known on date D', with an integrity flag."""

    def __init__(self, fred: Fred, sp500_csv: str = None):
        self.fred = fred
        self._market_cache = {}
        self._vintages = {}
        self.sp500 = None
        if sp500_csv:
            df = pd.read_csv(sp500_csv)
            df.columns = [c.strip().lower() for c in df.columns]
            date_col = "date"
            close_col = "close" if "close" in df.columns else df.columns[-1]
            self.sp500 = pd.DataFrame({
                "date": pd.to_datetime(df[date_col]),
                "value": pd.to_numeric(df[close_col], errors="coerce"),
            }).dropna().sort_values("date").reset_index(drop=True)

    def asof(self, ind: dict, D: date):
        """Return (df, integrity) where df has only data knowable on D.
        integrity in {'M','V','B','missing'}."""
        sid = ind["fred"]

        if sid == "SP500_EXTERNAL":
            if self.sp500 is None:
                return None, "missing"
            return self.sp500[self.sp500["date"] <= pd.Timestamp(D)], "M"

        if not ind.get("revised", True):
            if sid not in self._market_cache:
                self._market_cache[sid] = self.fred.observations(sid)
            df = self._market_cache[sid]
            return df[df["date"] <= pd.Timestamp(D)], "M"

        if sid not in self._vintages:
            self._vintages[sid] = self.fred.vintage_dates(sid)
        vintages = self._vintages[sid]
        if not vintages:
            return None, "missing"

        usable = [v for v in vintages if v <= D]
        if usable:
            v = usable[-1]
            df = self.fred.observations(sid, realtime=v.isoformat())
            return df[df["date"] <= pd.Timestamp(D)], "V"

        # Evaluation date precedes the first ALFRED vintage: honest
        # approximation = earliest vintage, truncated to observations <= D.
        v0 = vintages[0]
        df = self.fred.observations(sid, realtime=v0.isoformat())
        return df[df["date"] <= pd.Timestamp(D)], "B"


# ----------------------------------------------------------------------------
# Rule evaluation
# ----------------------------------------------------------------------------

def _streak_at_end(cond: pd.Series, n: int) -> bool:
    if len(cond) < n:
        return False
    return bool(cond.iloc[-n:].all())


def _yoy(values: pd.Series, periods: int) -> pd.Series:
    return (values / values.shift(periods) - 1.0) * 100.0


def evaluate(ind: dict, df: pd.DataFrame, D: date, scale: float = 1.0):
    """Returns (red: bool|None, detail: dict). None = insufficient history.
    `scale` multiplies scalable params for the sensitivity run."""
    p = dict(ind["params"])
    for k in ind.get("scalable", []):
        p[k] = p[k] * scale
    v = df["value"].reset_index(drop=True)
    rule = ind["rule"]

    if rule == "curve":
        cond = v < 0
        red_a = _streak_at_end(cond, p["streak_days"])
        # variant 1b: streak condition satisfied at any point in lookback window
        streak = cond.rolling(p["streak_days"]).min() == 1
        window_start = pd.Timestamp(D) - pd.Timedelta(days=p["lookback_days"])
        in_window = df["date"].reset_index(drop=True) >= window_start
        red_b = bool((streak & in_window).any())
        if len(v) < p["streak_days"]:
            return None, {}
        return red_a, {"variant_b": red_b}

    if rule == "hy_spread":
        if len(v) < p["low_window"] + p["streak_days"]:
            return None, {}
        low = v.rolling(p["low_window"]).min()
        cond = (v > p["level"]) | (v >= low + p["widen"])
        return _streak_at_end(cond, p["streak_days"]), {}

    if rule == "level_above":
        n = p.get("streak", 1)
        if len(v) < n:
            return None, {}
        return _streak_at_end(v > p["level"], n), {}

    if rule == "level_below":
        n = p.get("streak", 1)
        if len(v) < n:
            return None, {}
        return _streak_at_end(v < p["level"], n), {}

    if rule == "drawdown":
        if len(v) < p["high_window"] + p["streak_days"]:
            return None, {}
        high = v.rolling(p["high_window"]).max()
        cond = v < (1.0 - p["drop"]) * high
        return _streak_at_end(cond, p["streak_days"]), {}

    if rule == "yoy_below":
        if len(v) < 12 + p["streak"]:
            return None, {}
        cond = _yoy(v, 12) < p["pct"]
        return _streak_at_end(cond, p["streak"]), {}

    if rule == "drop_from_peak_ma":
        need = p["ma"] + p["peak_window"] + p["streak"]
        if len(v) < need:
            return None, {}
        ma = v.rolling(p["ma"]).mean()
        peak = ma.rolling(p["peak_window"]).max()
        cond = ma < (1.0 - p["drop"]) * peak
        return _streak_at_end(cond, p["streak"]), {}

    if rule == "level_or_rising":
        n = p["rising_periods"]
        if len(v) < n + 1:
            return None, {}
        rising = all(v.iloc[-i] > v.iloc[-i - 1] for i in range(1, n + 1))
        return bool(v.iloc[-1] > p["level"] or rising), {}

    if rule == "level_and_rising":
        n = p["rising_periods"]
        if len(v) < n + 1:
            return None, {}
        rising = all(v.iloc[-i] > v.iloc[-i - 1] for i in range(1, n + 1))
        return bool(v.iloc[-1] > p["level"] and rising), {}

    if rule == "claims_vs_low":
        need = p["ma"] + p["low_window"] + p["streak"]
        if len(v) < need:
            return None, {}
        ma = v.rolling(p["ma"]).mean()
        low = ma.rolling(p["low_window"]).min().shift(1)
        cond = ma > (1.0 + p["rise"]) * low
        return _streak_at_end(cond.fillna(False), p["streak"]), {}

    if rule == "yoy_above_weekly":
        if len(v) < 52 + p["streak"]:
            return None, {}
        cond = _yoy(v, 52) > p["pct"]
        return _streak_at_end(cond, p["streak"]), {}

    raise ValueError(f"unknown rule {rule}")


def is_stale(ind: dict, df: pd.DataFrame, D: date, staleness: dict) -> bool:
    limit = staleness[ind["freq"]]
    last = df["date"].iloc[-1].date()
    return (D - last).days > limit


# ----------------------------------------------------------------------------
# Board evaluation over the monthly grid
# ----------------------------------------------------------------------------

def month_grid(start: str, end: str) -> list:
    dates, cur = [], datetime.strptime(start + "-01", "%Y-%m-%d").date()
    stop = datetime.strptime(end + "-01", "%Y-%m-%d").date()
    while cur <= stop:
        dates.append(cur)
        cur = (cur.replace(day=28) + timedelta(days=8)).replace(day=1)
    return dates


def run_board(spec, store, dates, scale=1.0, curve_variant="a", quiet=False):
    rows = []
    n = len(dates)
    for i, D in enumerate(dates):
        if not quiet and i % 24 == 0:
            print(f"  evaluating {D} ({i + 1}/{n})", file=sys.stderr)
        row = {"date": D}
        for ind in spec["indicators"]:
            key = f"i{ind['id']:02d}"
            df, integrity = store.asof(ind, D)
            if df is None or df.empty or is_stale(ind, df, D, spec["staleness_days"]):
                row[key], row[key + "_q"] = np.nan, "missing"
                continue
            red, detail = evaluate(ind, df, D, scale=scale)
            if red is None:
                row[key], row[key + "_q"] = np.nan, "short"
                continue
            if ind["rule"] == "curve" and curve_variant == "b":
                red = detail["variant_b"]
            if ind["rule"] == "curve":
                row[key + "_alt"] = int(detail["variant_b"])
            row[key] = int(red)
            row[key + "_q"] = integrity
        rows.append(row)
    return pd.DataFrame(rows)


def score_board(board: pd.DataFrame, spec) -> pd.DataFrame:
    t = spec["tiers"]
    ig = spec["c_ignition"]
    buckets = {"A": [], "B": [], "C": []}
    conf_ids = set()
    for ind in spec["indicators"]:
        buckets[ind["bucket"]].append(f"i{ind['id']:02d}")
        if ind["role"] == "confirmation":
            conf_ids.add(f"i{ind['id']:02d}")

    out = []
    for _, r in board.iterrows():
        rec = {"date": r["date"]}
        total_red = total_avail = 0
        bucket_stats = {}
        for b, cols in buckets.items():
            vals = [r[c] for c in cols if pd.notna(r.get(c))]
            reds = int(sum(vals))
            avail = len(vals)
            bucket_stats[b] = (reds, avail)
            rec[f"{b}_red"], rec[f"{b}_avail"] = reds, avail
            total_red += reds
            total_avail += avail
        frac = total_red / total_avail if total_avail else 0.0
        rec["reds"], rec["available"], rec["fraction"] = total_red, total_avail, round(frac, 4)

        buckets_with_red = sum(1 for b in buckets if bucket_stats[b][0] > 0)
        broad_ok = all(
            (reds / avail) >= t["broad_bucket_fraction"]
            for reds, avail in bucket_stats.values()
            if avail >= t["broad_bucket_min_available"]
        )
        if frac >= t["broad_fraction"] and broad_ok:
            rec["tier"] = "BROAD"
        elif frac >= t["warning_fraction"] and buckets_with_red >= t["warning_min_buckets"]:
            rec["tier"] = "WARNING"
        elif frac >= t["watch_fraction"]:
            rec["tier"] = "WATCH"
        else:
            rec["tier"] = "-"

        a_ex_conf = int(sum(
            r[c] for c in buckets["A"] if c not in conf_ids and pd.notna(r.get(c))
        ))
        rec["c_ignition_cond"] = int(
            bucket_stats["C"][0] >= ig["c_min_reds"]
            and a_ex_conf >= ig["a_min_reds_ex_confirmation"]
            and bucket_stats["B"][0] >= ig["b_min_reds"]
        )
        out.append(rec)

    scored = pd.DataFrame(out)

    # First C-ignition per episode (episode resets after fraction < reset
    # threshold for reset_months consecutive months)
    reset_frac, reset_n = ig["episode_reset_fraction"], ig["episode_reset_months"]
    calm, in_episode, events = 0, False, []
    for _, r in scored.iterrows():
        calm = calm + 1 if r["fraction"] < reset_frac else 0
        if calm >= reset_n:
            in_episode = False
        if r["c_ignition_cond"] and not in_episode:
            events.append(r["date"])
            in_episode = True
    scored.attrs["c_ignition_events"] = events
    return scored


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

def months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def era_report(scored: pd.DataFrame, spec) -> str:
    lines = ["=" * 72, "ERA REPORT", "=" * 72]
    s = scored.set_index("date")

    for rec in spec["nber_recessions"]:
        start = datetime.strptime(rec["start"], "%Y-%m-%d").date()
        lines.append(f"\n{rec['name']} recession (starts {rec['start'][:7]})"
                     + ("  [external shock -- no lead expected]" if rec.get("external_shock") else ""))
        window = s[(s.index >= start - timedelta(days=760)) & (s.index <= start)]
        if window.empty:
            lines.append("  (outside evaluated range)")
            continue
        for tier in ["WATCH", "WARNING", "BROAD"]:
            order = {"-": 0, "WATCH": 1, "WARNING": 2, "BROAD": 3}
            hits = window[window["tier"].map(order) >= order[tier]]
            if hits.empty:
                lines.append(f"  {tier:8s}: never reached in prior 24 months")
            else:
                first = hits.index[0]
                lines.append(f"  {tier:8s}: first {first}  "
                             f"(lead {months_between(first, start)} mo, "
                             f"{int(hits.iloc[0]['reds'])}/{int(hits.iloc[0]['available'])} red)")
        igs = [d for d in scored.attrs["c_ignition_events"]
               if start - timedelta(days=760) <= d <= start + timedelta(days=95)]
        lines.append(f"  C-IGNITION: {igs[0] if igs else 'did not occur'}")

    lines.append("\n" + "-" * 72 + "\nFALSE-POSITIVE CONTROL WINDOWS\n" + "-" * 72)
    for w in spec["false_positive_windows"]:
        ws = datetime.strptime(w["start"], "%Y-%m-%d").date()
        we = datetime.strptime(w["end"], "%Y-%m-%d").date()
        window = s[(s.index >= ws) & (s.index <= we)]
        if window.empty:
            lines.append(f"\n{w['name']}: (outside evaluated range)")
            continue
        peak = window.loc[window["fraction"].idxmax()]
        tiers = set(window["tier"])
        worst = ("BROAD" if "BROAD" in tiers else
                 "WARNING" if "WARNING" in tiers else
                 "WATCH" if "WATCH" in tiers else "-")
        igs = [d for d in scored.attrs["c_ignition_events"] if ws <= d <= we]
        verdict = "FAIL (false BROAD)" if worst == "BROAD" else "ok"
        if igs:
            verdict += "  H1 VIOLATED (C-ignition fired)"
        lines.append(f"\n{w['name']}: peak {peak['fraction']:.0%} "
                     f"({int(peak['reds'])}/{int(peak['available'])}), "
                     f"worst tier {worst} -> {verdict}")
    return "\n".join(lines)


def monthly_narrative(scored: pd.DataFrame, spec) -> str:
    """The 'what did the board show on each date' table for recession run-ups."""
    lines = ["=" * 72, "BOARD READINGS -- RECESSION RUN-UPS (quarterly snapshots)", "=" * 72]
    s = scored.set_index("date")
    for rec in spec["nber_recessions"]:
        start = datetime.strptime(rec["start"], "%Y-%m-%d").date()
        lines.append(f"\n{rec['name']}:")
        for k in range(24, -1, -3):
            d = (pd.Timestamp(start) - pd.DateOffset(months=k)).date().replace(day=1)
            if d in s.index:
                r = s.loc[d]
                lines.append(f"  {d}  {int(r['reds']):2d}/{int(r['available'])}  "
                             f"{r['fraction']:.0%}  {r['tier']}"
                             f"  [A:{int(r['A_red'])} B:{int(r['B_red'])} C:{int(r['C_red'])}]")
    return "\n".join(lines)


def coverage_table(board: pd.DataFrame, spec) -> pd.DataFrame:
    """Authoritative availability/integrity table by era, from actual metadata."""
    eras = {r["name"]: r["start"][:7] for r in spec["nber_recessions"]}
    eras.update({w["name"]: w["start"][:7] for w in spec["false_positive_windows"]})
    rows = []
    b = board.set_index("date")
    for name, ym in sorted(eras.items(), key=lambda kv: kv[1]):
        d = datetime.strptime(ym + "-01", "%Y-%m-%d").date()
        if d not in b.index:
            continue
        r = b.loc[d]
        for ind in spec["indicators"]:
            q = r.get(f"i{ind['id']:02d}_q", "missing")
            rows.append({"era": name, "as_of": d, "indicator": ind["name"], "integrity": q})
    return pd.DataFrame(rows)


def plot_fraction(scored: pd.DataFrame, spec, path: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping plot", file=sys.stderr)
        return
    fig, ax = plt.subplots(figsize=(14, 5))
    d = pd.to_datetime(scored["date"])
    ax.plot(d, scored["fraction"] * 100, lw=1.2, color="#8B1E1E")
    for rec in spec["nber_recessions"]:
        ax.axvspan(pd.Timestamp(rec["start"]), pd.Timestamp(rec["end"]),
                   color="gray", alpha=0.25)
    for y, label in [(25, "Watch"), (40, "Warning"), (60, "Broad")]:
        ax.axhline(y, ls="--", lw=0.7, color="#666")
        ax.text(d.iloc[0], y + 1, label, fontsize=8, color="#666")
    ax.set_ylabel("% of available indicators red")
    ax.set_title("Economic Warning Board -- point-in-time red fraction (spec v0.2)")
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"wrote {path}")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="spec_v02.json")
    ap.add_argument("--start", default="1988-01")
    ap.add_argument("--end", default=date.today().strftime("%Y-%m"))
    ap.add_argument("--out", default="results")
    ap.add_argument("--cache", default=".fred_cache")
    ap.add_argument("--sp500-csv", default=None,
                    help="daily CSV with date,close columns (e.g. Stooq ^SPX export)")
    ap.add_argument("--curve-variant", choices=["a", "b", "both"], default="both")
    ap.add_argument("--sensitivity", action="store_true",
                    help="also run all scalable thresholds at x0.8 and x1.2")
    args = ap.parse_args()

    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        sys.exit("Set FRED_API_KEY (free key: https://fred.stlouisfed.org/docs/api/api_key.html)")

    spec = json.loads(Path(args.spec).read_text())
    spec_hash = hashlib.sha256(Path(args.spec).read_bytes()).hexdigest()[:16]
    print(f"Spec v{spec['spec_version']}  sha256:{spec_hash}  (record this hash)")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fred = Fred(api_key, Path(args.cache))
    store = SeriesStore(fred, sp500_csv=args.sp500_csv)
    dates = month_grid(args.start, args.end)

    variants = ["a", "b"] if args.curve_variant == "both" else [args.curve_variant]
    baseline_scored = {}
    for var in variants:
        print(f"\n== Baseline run, curve variant 1{var} ==")
        board = run_board(spec, store, dates, curve_variant=var)
        scored = score_board(board, spec)
        baseline_scored[var] = scored
        board.to_csv(out / f"board_variant_{var}.csv", index=False)
        scored.to_csv(out / f"scored_variant_{var}.csv", index=False)
        report = (era_report(scored, spec) + "\n\n" + monthly_narrative(scored, spec))
        (out / f"report_variant_{var}.txt").write_text(report)
        print(report)
        plot_fraction(scored, spec, out / f"fraction_variant_{var}.png")

    coverage_table(run_board(spec, store, dates[:1], quiet=True) if not baseline_scored
                   else pd.read_csv(out / f"board_variant_{variants[0]}.csv"),
                   spec).to_csv(out / "coverage_by_era.csv", index=False)

    if args.sensitivity:
        print("\n== Sensitivity: scalable thresholds x0.8 and x1.2 ==")
        var = variants[-1]
        summary = []
        for scale in (0.8, 1.2):
            board = run_board(spec, store, dates, scale=scale, curve_variant=var, quiet=True)
            scored = score_board(board, spec)
            scored.to_csv(out / f"scored_scale_{scale}.csv", index=False)
            s = scored.set_index("date")
            for rec in spec["nber_recessions"]:
                start = datetime.strptime(rec["start"], "%Y-%m-%d").date()
                w = s[(s.index >= start - timedelta(days=760)) & (s.index <= start)]
                hit = w[w["tier"].isin(["WARNING", "BROAD"])]
                summary.append({
                    "scale": scale, "era": rec["name"],
                    "warning_lead_mo": months_between(hit.index[0], start) if not hit.empty else None,
                })
            for wdef in spec["false_positive_windows"]:
                ws = datetime.strptime(wdef["start"], "%Y-%m-%d").date()
                we = datetime.strptime(wdef["end"], "%Y-%m-%d").date()
                w = s[(s.index >= ws) & (s.index <= we)]
                summary.append({
                    "scale": scale, "era": wdef["name"] + " (FP window)",
                    "false_broad": bool((w["tier"] == "BROAD").any()) if not w.empty else None,
                })
        pd.DataFrame(summary).to_csv(out / "sensitivity_summary.csv", index=False)
        print(pd.DataFrame(summary).to_string(index=False))

    print(f"\nAll output in {out}/  -- freeze report_variant_*.txt before touching any threshold.")


if __name__ == "__main__":
    main()
