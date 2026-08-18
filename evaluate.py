#!/usr/bin/env python3
"""Economic Warning Board -- live evaluator (spec v0.3).

Ports the rule engine straight from backtest.py: evaluate(), is_stale(), and
score_board() are imported unmodified, so scoring semantics stay byte-identical
to the frozen backtest. The only thing this file replaces is data access --
ALFRED point-in-time vintages become a plain "latest observations" fetch,
since a daily live board only ever needs to know what the data says today.

Usage:
    export FRED_API_KEY=yourkey
    python evaluate.py --spec spec_v03.json --out board.json \
        --history-seed history_seed.json --previous https://<user>.github.io/<repo>/board.json

On any indicator-availability shortfall below what score_board can score, or
any hard fetch failure, this exits non-zero and writes nothing -- the caller
(the GitHub Action) must leave the previously published board.json in place.
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import requests
except ImportError:
    sys.exit("pip install requests pandas numpy")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backtest import evaluate, is_stale, score_board, _yoy  # noqa: E402

FRED_BASE = "https://api.stlouisfed.org/fred"
SP500_LIVE_SERIES = "SP500"  # live substitute for the backtest's SP500_EXTERNAL csv

BUCKET_LABELS = {
    "A": "Financial & Credit",
    "B": "Business",
    "C": "Household & Labor",
}

PERIOD_NOUN = {"d": "trading day", "w": "week", "m": "month", "q": "quarter"}

WHAT_IS_THIS = {
    1: "The gap between the 10-year and 3-month Treasury yields. When investors expect trouble, short-term rates can rise above long-term rates and the curve “inverts.”",
    2: "The extra yield investors demand to hold risky (“junk”) corporate bonds over safe Treasurys. It widens when credit markets get nervous.",
    3: "The extra yield investment-grade Baa-rated corporate bonds pay over 10-year Treasurys — a broader read on credit stress than high-yield alone.",
    4: "The Chicago Fed's National Financial Conditions Index, a broad gauge of how loose or tight financial conditions are across money, debt, and equity markets. Zero is the long-run average.",
    5: "The St. Louis Fed Financial Stress Index, built from dozens of interest rates, spreads, and volatility measures. Zero is normal stress; positive means more than average.",
    6: "The net share of banks reporting they tightened lending standards on commercial and industrial loans, from the Fed's quarterly Senior Loan Officer survey.",
    7: "How far the S&P 500 has fallen from its highest close in the past year. A confirming signal, not a leading one — markets often drop only after the economy is already stressed.",
    8: "The Chicago Fed National Activity Index, a blend of 85 economic indicators, averaged over three months. Zero means growth at trend; negative means below-trend growth.",
    9: "Total US factory, mining, and utility output, compared with a year earlier.",
    10: "Sales of heavy (Class 8) trucks — a classic early-cycle indicator, since fleets stop replacing trucks when they expect less freight to move.",
    11: "New residential building permits issued nationwide, compared with a year earlier — one of the most reliably leading housing indicators.",
    12: "New orders for non-defense capital goods excluding aircraft — a proxy for business investment plans.",
    13: "Employment at temp-staffing agencies. Companies often cut temp workers first, before permanent layoffs, making this an early labor-market signal.",
    14: "The delinquency rate on commercial & industrial loans at all US banks.",
    15: "New unemployment claims, averaged over four weeks. A lagging confirmation signal — it tends to rise only after job losses are already underway.",
    16: "The number of people continuing to receive unemployment benefits, compared with a year earlier.",
    17: "The Sahm Rule: the 3-month average unemployment rate compared with its low over the prior 12 months. Historically reliable, if late.",
    18: "The delinquency rate on credit card balances at commercial banks.",
    19: "The delinquency rate on single-family residential mortgages at commercial banks.",
    20: "Retail sales adjusted for inflation, compared with a year earlier.",
}

SUBJECT = {
    1: "the curve", 2: "the spread", 3: "the spread", 4: "the index",
    5: "the index", 6: "the net tightening share", 7: "the index",
    8: "the 3-month average", 9: "output", 10: "truck sales", 11: "permits",
    12: "orders", 13: "temp employment", 14: "the delinquency rate",
    15: "claims", 16: "claims", 17: "the Sahm Rule reading",
    18: "delinquencies", 19: "delinquencies", 20: "sales",
}

VERB = {
    1: "is", 2: "is", 3: "is", 4: "is", 5: "is", 6: "is", 7: "is", 8: "is",
    9: "is", 10: "are", 11: "are", 12: "are", 13: "is", 14: "is",
    15: "are", 16: "are", 17: "is", 18: "are", 19: "are", 20: "are",
}

UNIT = {
    1: "percentage points", 2: "percentage points", 3: "percentage points",
    4: "index level", 5: "index level", 6: "% of banks, net",
    7: "% below 1-year high", 8: "index level", 9: "% year-over-year",
    10: "% below 2-year high", 11: "% year-over-year", 12: "% year-over-year",
    13: "% year-over-year", 14: "%", 15: "% above 1-year low",
    16: "% year-over-year", 17: "percentage points", 18: "%", 19: "%",
    20: "% year-over-year",
}


def _n(period_word, n):
    return f"{period_word}s" if n != 1 else period_word


def threshold_text(ind):
    p = ind["params"]
    rule = ind["rule"]
    period = PERIOD_NOUN[ind["freq"]]

    if rule == "curve":
        months = round(p["lookback_days"] / 30.44)
        return (f"Red when inverted (below 0) for {p['streak_days']} straight "
                f"{_n(period, p['streak_days'])}, or if that happened within the past {months} months")
    if rule == "hy_spread":
        return (f"Red when the spread is above {p['level']} points, or has widened "
                f"{p['widen']} points from its 3-month low, for {p['streak_days']} "
                f"straight {_n(period, p['streak_days'])}")
    if rule == "level_above":
        n = p.get("streak", 1)
        tail = f" for {n} straight {_n(period, n)}" if n > 1 else ""
        return f"Red when the reading is above {p['level']}{tail}"
    if rule == "level_below":
        n = p.get("streak", 1)
        tail = f" for {n} straight {_n(period, n)}" if n > 1 else ""
        return f"Red when the reading is below {p['level']}{tail}"
    if rule == "drawdown":
        return (f"Red when the index is more than {p['drop'] * 100:.1f}% below its "
                f"1-year high for {p['streak_days']} straight {_n(period, p['streak_days'])}")
    if rule == "yoy_below":
        return (f"Red when down {abs(p['pct'])}% or more year-over-year for "
                f"{p['streak']} straight {_n(period, p['streak'])}")
    if rule == "drop_from_peak_ma":
        return (f"Red when the {p['ma']}-month average is {p['drop'] * 100:.0f}% or more "
                f"below its {p['peak_window']}-month high for {p['streak']} straight "
                f"{_n(period, p['streak'])}")
    if rule == "level_or_rising":
        return (f"Red when above {p['level']}, or rising for {p['rising_periods']} "
                f"straight {_n(period, p['rising_periods'])}")
    if rule == "level_and_rising":
        return (f"Red when above {p['level']} and rising for {p['rising_periods']} "
                f"straight {_n(period, p['rising_periods'])}")
    if rule == "claims_vs_low":
        return (f"Red when {p['rise'] * 100:.0f}% or more above the 1-year low for "
                f"{p['streak']} straight {_n(period, p['streak'])}")
    if rule == "yoy_above_weekly":
        return (f"Red when up {p['pct']}% or more year-over-year for {p['streak']} "
                f"straight {_n(period, p['streak'])}")
    raise ValueError(rule)


def _is_rising(metric, n):
    if len(metric) < n + 1:
        return False
    return all(metric.iloc[-i] > metric.iloc[-i - 1] for i in range(1, n + 1))


def why_text(ind, red, metric):
    p = ind["params"]
    rule = ind["rule"]
    subj = SUBJECT[ind["id"]]
    verb = VERB[ind["id"]]
    v = float(metric.iloc[-1])

    if rule == "curve":
        months = round(p["lookback_days"] / 30.44)
        if red:
            return f"{subj.capitalize()} is inverted at {v:.2f}, below zero."
        return f"{subj.capitalize()} is positive at {v:.2f} and has not been inverted in the past {months} months."
    if rule == "hy_spread":
        if red:
            return f"{subj.capitalize()} is elevated at {v:.2f} points, at or beyond the {p['level']}-point level."
        return f"{subj.capitalize()} is {v:.2f} points, below the {p['level']}-point level and not sharply wider than its recent low."
    if rule == "level_above":
        if red:
            return f"{subj.capitalize()} {verb} {v:.2f}, above the {p['level']} threshold."
        return f"{subj.capitalize()} {verb} {v:.2f}, below the {p['level']} threshold."
    if rule == "level_below":
        if red:
            return f"{subj.capitalize()} {verb} {v:.2f}, below the {p['level']} threshold."
        return f"{subj.capitalize()} {verb} {v:.2f}, above the {p['level']} threshold."
    if rule == "drawdown":
        if red:
            return f"{subj.capitalize()} {verb} {abs(v):.1f}% below its 1-year high."
        return f"{subj.capitalize()} {verb} {abs(v):.1f}% off its 1-year high, inside the {p['drop'] * 100:.1f}% drawdown threshold."
    if rule == "yoy_below":
        word = "up" if v >= 0 else "down"
        if red:
            return f"{subj.capitalize()} {verb} down {abs(v):.1f}% year-over-year, below the {p['pct']}% threshold."
        return f"{subj.capitalize()} {verb} {word} {abs(v):.1f}% year-over-year, above the {p['pct']}% threshold."
    if rule == "drop_from_peak_ma":
        if red:
            return f"{subj.capitalize()} {verb} {abs(v):.1f}% below their 2-year high (4-month average)."
        return f"{subj.capitalize()} {verb} {abs(v):.1f}% off their 2-year high, inside the {p['drop'] * 100:.0f}% threshold."
    if rule == "level_or_rising":
        above = v > p["level"]
        rising = _is_rising(metric, p["rising_periods"])
        if red:
            if above and rising:
                return f"{subj.capitalize()} {verb} {v:.2f} — above {p['level']} and rising."
            if above:
                return f"{subj.capitalize()} {verb} {v:.2f}, above the {p['level']} threshold."
            return f"{subj.capitalize()} {verb} {v:.2f}, below {p['level']} but has risen for {p['rising_periods']} straight periods."
        return f"{subj.capitalize()} {verb} {v:.2f}, below {p['level']} and not on a sustained rise."
    if rule == "level_and_rising":
        above = v > p["level"]
        rising = _is_rising(metric, p["rising_periods"])
        if red:
            return f"{subj.capitalize()} {verb} at {v:.2f}%, above the {p['level']}% threshold, and rising."
        if above and not rising:
            n = p["rising_periods"]
            return (f"{subj.capitalize()} {verb} at {v:.2f}%, above the {p['level']}% threshold, "
                    f"but {'has' if verb == 'is' else 'have'} not risen for {n} straight quarter{'s' if n != 1 else ''}.")
        return f"{subj.capitalize()} {verb} at {v:.2f}%, below the {p['level']}% threshold."
    if rule == "claims_vs_low":
        if red:
            return f"{subj.capitalize()} {verb} {v:.1f}% above their 1-year low."
        return f"{subj.capitalize()} {verb} {v:.1f}% above their 1-year low, inside the {p['rise'] * 100:.0f}% threshold."
    if rule == "yoy_above_weekly":
        if red:
            return f"{subj.capitalize()} {verb} up {v:.1f}% year-over-year, above the {p['pct']}% threshold."
        word = "up" if v >= 0 else "down"
        return f"{subj.capitalize()} {verb} {word} {abs(v):.1f}% year-over-year, below the {p['pct']}% threshold."
    raise ValueError(rule)


def metric_series(ind, df):
    """The rule's own metric, aligned to df['date'] -- what 'value' and the
    sparkline show, and the same units the threshold line is drawn in."""
    v = df["value"].reset_index(drop=True)
    p = ind["params"]
    rule = ind["rule"]

    if rule in ("curve", "hy_spread", "level_above", "level_below",
                "level_or_rising", "level_and_rising"):
        return v
    if rule == "drawdown":
        high = v.rolling(p["high_window"]).max()
        return (v / high - 1.0) * 100.0
    if rule == "yoy_below":
        return _yoy(v, 12)
    if rule == "drop_from_peak_ma":
        ma = v.rolling(p["ma"]).mean()
        peak = ma.rolling(p["peak_window"]).max()
        return (ma / peak - 1.0) * 100.0
    if rule == "claims_vs_low":
        ma = v.rolling(p["ma"]).mean()
        low = ma.rolling(p["low_window"]).min().shift(1)
        return (ma / low - 1.0) * 100.0
    if rule == "yoy_above_weekly":
        return _yoy(v, 52)
    raise ValueError(rule)


class LiveFred:
    def __init__(self, api_key):
        self.key = api_key
        self.session = requests.Session()

    def observations(self, series_id):
        params = {"series_id": series_id, "limit": 100000,
                  "observation_start": "1950-01-01",
                  "api_key": self.key, "file_type": "json"}
        data = None
        for attempt in range(6):
            r = self.session.get(f"{FRED_BASE}/series/observations", params=params, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            data = r.json()
            break
        if data is None:
            raise RuntimeError(f"FRED API kept failing for {series_id}")
        obs = data.get("observations", [])
        rows = [(o["date"], o["value"]) for o in obs if o["value"] not in (".", "", None)]
        if not rows:
            return pd.DataFrame(columns=["date", "value"])
        out = pd.DataFrame(rows, columns=["date", "value"])
        out["date"] = pd.to_datetime(out["date"])
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        return out.dropna().sort_values("date").reset_index(drop=True)


def evaluate_red(ind, df, D):
    """evaluate() + the v0.3 curve-variant-1b adoption, unmodified otherwise."""
    red, detail = evaluate(ind, df, D, scale=1.0)
    if red is None:
        return None
    if ind["rule"] == "curve":
        red = detail["variant_b"]
    return bool(red)


def bootstrap_indicator_since(ind, df, today, red_now, max_steps=1500):
    """No previous board.json to carry state from: walk the already-fetched
    (latest-vintage) history backward and find how long the current red/green
    reading has held. Not ALFRED point-in-time -- a display-only estimate for
    the very first run, per spec 1.1's 'no ALFRED vintages' simplification."""
    n = len(df)
    streak_idx = n - 1
    for i in range(n - 2, max(n - 2 - max_steps, -1), -1):
        sub = df.iloc[: i + 1]
        D = sub["date"].iloc[-1].date()
        red = evaluate_red(ind, sub, D)
        if red is None or red != red_now:
            break
        streak_idx = i
    since = df["date"].iloc[streak_idx].date()
    return since, (today - since).days


def fetch_previous(path_or_url):
    try:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            r = requests.get(path_or_url, timeout=30)
            if r.status_code != 200:
                return None
            return r.json()
        p = Path(path_or_url)
        return json.loads(p.read_text()) if p.exists() else None
    except Exception:
        return None


def build_indicator(ind, fred, today, prev_indicators):
    sid = SP500_LIVE_SERIES if ind["fred"] == "SP500_EXTERNAL" else ind["fred"]
    df = fred.observations(sid)

    prev = prev_indicators.get(str(ind["id"]))

    if df.empty or is_stale(ind, df, today, SPEC["staleness_days"]):
        return {
            "id": ind["id"], "name": ind["name"], "bucket": ind["bucket"],
            "role": ind["role"], "state": "unavailable", "value": None,
            "unit": UNIT[ind["id"]], "threshold_text": threshold_text(ind),
            "why_text": "This indicator's data is currently stale or unavailable from the source.",
            "observation_date": (df["date"].iloc[-1].date().isoformat() if not df.empty else None),
            "days_in_state": 0, "source_name": f"Federal Reserve (FRED: {sid})",
            "source_url": f"https://fred.stlouisfed.org/series/{sid}", "sparkline": [],
        }, None

    red = evaluate_red(ind, df, today)
    if red is None:
        return {
            "id": ind["id"], "name": ind["name"], "bucket": ind["bucket"],
            "role": ind["role"], "state": "unavailable", "value": None,
            "unit": UNIT[ind["id"]], "threshold_text": threshold_text(ind),
            "why_text": "Not enough history yet to evaluate this indicator's rule.",
            "observation_date": df["date"].iloc[-1].date().isoformat(),
            "days_in_state": 0, "source_name": f"Federal Reserve (FRED: {sid})",
            "source_url": f"https://fred.stlouisfed.org/series/{sid}", "sparkline": [],
        }, None

    metric = metric_series(ind, df).reset_index(drop=True)
    value = float(metric.iloc[-1])
    state = "red" if red else "green"

    if prev and prev.get("state") in ("red", "green"):
        prev_days = int(prev.get("days_in_state", 0))
        if prev.get("state") == state:
            days_in_state = prev_days + 1
        else:
            days_in_state = 0
    else:
        _since, days_in_state = bootstrap_indicator_since(ind, df, today, red)

    sparkline = [round(float(x), 4) for x in metric.tail(60).tolist()]

    return {
        "id": ind["id"],
        "name": ind["name"],
        "bucket": ind["bucket"],
        "role": ind["role"],
        "state": state,
        "value": round(value, 4),
        "unit": UNIT[ind["id"]],
        "threshold_text": threshold_text(ind),
        "why_text": why_text(ind, red, metric),
        "observation_date": df["date"].iloc[-1].date().isoformat(),
        "days_in_state": days_in_state,
        "source_name": f"Federal Reserve (FRED: {sid})",
        "source_url": f"https://fred.stlouisfed.org/series/{sid}",
        "sparkline": sparkline,
    }, int(red)


SPEC = None  # set in main(), read by build_indicator for staleness windows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="spec_v03.json")
    ap.add_argument("--out", default="board.json")
    ap.add_argument("--history-seed", default="history_seed.json")
    ap.add_argument("--previous", default=None,
                    help="path or URL to yesterday's board.json, for state continuity")
    args = ap.parse_args()

    api_key = __import__("os").environ.get("FRED_API_KEY")
    if not api_key:
        sys.exit("Set FRED_API_KEY (free key: https://fred.stlouisfed.org/docs/api/api_key.html)")

    global SPEC
    spec_path = Path(args.spec)
    SPEC = json.loads(spec_path.read_text())
    spec_hash = hashlib.sha256(spec_path.read_bytes()).hexdigest()[:16]

    today = datetime.now(timezone.utc).date()
    prev = fetch_previous(args.previous) if args.previous else None
    prev_indicators = {str(i["id"]): i for i in (prev or {}).get("indicators", [])}

    fred = LiveFred(api_key)

    row = {"date": pd.Timestamp(today)}
    indicators_out = []
    available = 0
    for ind in SPEC["indicators"]:
        entry, red_int = build_indicator(ind, fred, today, prev_indicators)
        indicators_out.append(entry)
        key = f"i{ind['id']:02d}"
        if red_int is None:
            row[key] = np.nan
        else:
            row[key] = red_int
            available += 1

    if available < len(SPEC["indicators"]) * 0.5:
        sys.exit(f"Only {available}/{len(SPEC['indicators'])} indicators available -- "
                 f"refusing to publish a partial board.")

    board_df = pd.DataFrame([row])
    scored = score_board(board_df, SPEC).iloc[0]

    tier_raw = scored["tier"]
    tier = "QUIET" if tier_raw == "-" else tier_raw

    if prev and prev.get("board", {}).get("tier") == tier:
        tier_since = prev["board"]["tier_since"]
    else:
        history_seed = json.loads(Path(args.history_seed).read_text()) if Path(args.history_seed).exists() else []
        base_history = (prev or {}).get("history") or history_seed
        tier_since = today.isoformat()
        for rec in reversed(base_history):
            if rec["tier"] != tier:
                break
            tier_since = rec["date"]

    buckets = {}
    for b in ("A", "B", "C"):
        buckets[b] = {
            "red": int(scored[f"{b}_red"]),
            "available": int(scored[f"{b}_avail"]),
            "label": BUCKET_LABELS[b],
        }

    history_seed = json.loads(Path(args.history_seed).read_text()) if Path(args.history_seed).exists() else []
    history = list((prev or {}).get("history") or history_seed)
    today_rec = {"date": today.isoformat(), "fraction": round(float(scored["fraction"]), 4), "tier": tier}
    if history and history[-1]["date"] == today.isoformat():
        history[-1] = today_rec
    else:
        history.append(today_rec)

    board = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spec_version": SPEC["spec_version"],
        "spec_hash": spec_hash,
        "board": {
            "reds": int(scored["reds"]),
            "available": int(scored["available"]),
            "fraction": round(float(scored["fraction"]), 4),
            "tier": tier,
            "tier_since": tier_since,
            "buckets": buckets,
            "ignition_active": bool(scored["c_ignition_cond"]),
        },
        "indicators": indicators_out,
        "history": history,
    }

    Path(args.out).write_text(json.dumps(board, indent=2) + "\n")
    print(f"wrote {args.out}: {board['board']['reds']}/{board['board']['available']} red, tier {tier}")


if __name__ == "__main__":
    main()
