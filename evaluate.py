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

# Watchlist: public, free, timely, but doesn't clear the >=3-recession
# backtestable-history bar the scored 20 require. Display-only -- never
# enters reds/available/fraction or any tier. Per spec-v0.5-candidates.md
# section 4. W3 (Census data-center construction) and W5 (BDC price-to-NAV)
# are named in that document but need a non-FRED data source with no clean
# free automated path, so they're not implemented here -- adding them would
# mean exactly the kind of manual/fragile dependency that got the BDC
# non-accrual composite rejected outright in the same document.
WATCHLIST = [
    {
        "id": "W1",
        "name": "Bank loans to nondepository financial institutions",
        "fred": "LNFACBW027SBOG",
        "freq": "w",
        "unit": "$ billions",
        "what_is_this": "Commercial bank lending to nonbank financial firms -- private credit funds, BDCs, and similar vehicles among them. The best available public, free, weekly bridge to private-credit stress: when private lenders draw on bank credit lines under pressure, it shows up here.",
    },
    {
        "id": "W2",
        "name": "JOLTS hires rate",
        "fred": "JTSHIR",
        "freq": "m",
        "unit": "%",
        "what_is_this": "New hires as a share of total employment. A direct read on how willing employers are to hire, independent of the labor-force-size arithmetic that can distort the unemployment rate.",
    },
    {
        "id": "W4",
        "name": "Business applications",
        "fred": "BABATOTALSAUS",
        "freq": "m",
        "unit": "applications",
        "what_is_this": "New business applications filed nationwide. A timely read on small-business formation -- and currently reads healthy, which is evidence against a broad SMB-collapse story, not for one.",
    },
]


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


def _trailing_run(metric, want_rising):
    """Count consecutive most-recent periods moving the same direction, for
    leg explanatory text only -- not spec-v0.6's trend channel (unimplemented;
    that has its own frequency-aware step size and deadband)."""
    n = 0
    i = len(metric) - 1
    while i > 0:
        step_rising = metric.iloc[i] > metric.iloc[i - 1]
        if step_rising != want_rising:
            break
        n += 1
        i -= 1
    return n


PERIOD_ADJ = {"d": "daily", "w": "weekly", "m": "monthly", "q": "quarterly"}


def _rising_leg(metric, p, period, freq):
    n = p["rising_periods"]
    rising = _is_rising(metric, n)
    adj = PERIOD_ADJ[freq]
    straight = "" if n == 1 else "straight "
    if rising:
        run = max(_trailing_run(metric, True), n)
        text = f"Risen for {run} straight {_n(period, run)}" if run > 1 else f"Risen for {run} {period}"
    else:
        decline_run = _trailing_run(metric, False)
        text = f"Has not risen for {n} {straight}{_n(period, n)}"
        if decline_run >= 2:
            text += f" — {decline_run} straight {adj} declines"
    return {"name": "rising", "met": rising, "text": text}


def compute_legs(ind, df, D, metric):
    """Per-leg breakdown for compound rules (spec-v0.6-tile-information.md
    section 5). `position` only ever measures one leg (`position_basis`);
    the state can be decided by an entirely different one -- #1 can be red
    on the lookback window while today's level is clear, #18 can already be
    past its level and held green purely by an unbroken rising requirement.
    Returns (legs: list[dict], position_basis: str). Every rule gets at
    least one leg so the client's handling is uniform; single-condition
    rules just get a length-1 legs list naming what threshold_value/
    compute_position already measure for that rule."""
    p = ind["params"]
    rule = ind["rule"]
    period = PERIOD_NOUN[ind["freq"]]
    v = metric

    if rule == "curve":
        red_a, detail = evaluate(ind, df, D, scale=1.0)
        lookback_met = bool(detail.get("variant_b", False))
        level_met = bool(red_a)
        months = round(p["lookback_days"] / 30.44)
        legs = [
            {"name": "level", "met": level_met,
             "text": "Inverted today" if level_met else "Not inverted today"},
            {"name": "lookback", "met": lookback_met,
             "text": (f"Inverted within the past {months} months" if lookback_met
                      else f"Not inverted in the past {months} months")},
        ]
        return legs, "level"

    if rule == "hy_spread":
        low = v.rolling(p["low_window"]).min()
        level_met = bool(v.iloc[-1] > p["level"])
        widen_met = bool(v.iloc[-1] >= low.iloc[-1] + p["widen"])
        legs = [
            {"name": "level", "met": level_met,
             "text": (f"Above {p['level']} points" if level_met
                      else f"Below {p['level']} points")},
            {"name": "widen", "met": widen_met,
             "text": (f"Widened {p['widen']} points from its 3-month low" if widen_met
                      else f"Not widened {p['widen']} points from its 3-month low")},
        ]
        return legs, "level"

    if rule in ("level_and_rising", "level_or_rising"):
        level_met = bool(v.iloc[-1] > p["level"])
        legs = [
            {"name": "level", "met": level_met,
             "text": f"Above {p['level']}" if level_met else f"Below {p['level']}"},
            _rising_leg(v, p, period, ind["freq"]),
        ]
        return legs, "level"

    if rule == "level_above":
        met = bool(v.iloc[-1] > p["level"])
        text = f"Above {p['level']}" if met else f"Below {p['level']}"
        return [{"name": "level", "met": met, "text": text}], "level"

    if rule == "level_below":
        met = bool(v.iloc[-1] < p["level"])
        text = f"Below {p['level']}" if met else f"Above {p['level']}"
        return [{"name": "level", "met": met, "text": text}], "level"

    if rule == "drawdown":
        met = bool(v.iloc[-1] < -(p["drop"] * 100.0))
        text = (f"More than {p['drop'] * 100:.1f}% below its 1-year high" if met
                else f"Within {p['drop'] * 100:.1f}% of its 1-year high")
        return [{"name": "drop", "met": met, "text": text}], "drop"

    if rule == "drop_from_peak_ma":
        met = bool(v.iloc[-1] < -(p["drop"] * 100.0))
        text = (f"{p['drop'] * 100:.0f}% or more below its {p['peak_window']}-month high" if met
                else f"Within {p['drop'] * 100:.0f}% of its {p['peak_window']}-month high")
        return [{"name": "drop", "met": met, "text": text}], "drop"

    if rule == "yoy_below":
        met = bool(v.iloc[-1] < p["pct"])
        text = (f"Down {abs(p['pct'])}% or more year-over-year" if met
                else f"Above the {p['pct']}% year-over-year threshold")
        return [{"name": "yoy", "met": met, "text": text}], "yoy"

    if rule == "yoy_above_weekly":
        met = bool(v.iloc[-1] > p["pct"])
        text = (f"Up {p['pct']}% or more year-over-year" if met
                else f"Below the {p['pct']}% year-over-year threshold")
        return [{"name": "yoy", "met": met, "text": text}], "yoy"

    if rule == "claims_vs_low":
        met = bool(v.iloc[-1] > p["rise"] * 100.0)
        text = (f"{p['rise'] * 100:.0f}% or more above the 1-year low" if met
                else "Inside the 1-year-low threshold")
        return [{"name": "rise", "met": met, "text": text}], "rise"

    raise ValueError(rule)


def pick_binding_leg(red, legs, position_basis):
    """For a red indicator, the leg that fired it; for a green one, the
    unmet leg keeping it green. Falls back to position_basis when every leg
    agrees (an AND-rule with both legs met, or an OR-rule with none met) --
    there's no single leg to name as the reason in that case."""
    if len(legs) == 1:
        return legs[0]["name"]
    if red:
        unmet = [leg["name"] for leg in legs if not leg["met"]]
        if not unmet:
            return position_basis
        met = [leg["name"] for leg in legs if leg["met"]]
        return met[0] if met else position_basis
    unmet = [leg["name"] for leg in legs if not leg["met"]]
    return unmet[0] if unmet else position_basis


def why_text(ind, red, metric):
    p = ind["params"]
    rule = ind["rule"]
    subj = SUBJECT[ind["id"]]
    verb = VERB[ind["id"]]
    v = float(metric.iloc[-1])

    if rule == "curve":
        months = round(p["lookback_days"] / 30.44)
        if red and v < 0:
            return f"{subj.capitalize()} is inverted at {v:.2f}, below zero."
        if red:
            return (f"{subj.capitalize()} is positive at {v:.2f} today, but was inverted "
                     f"within the past {months} months -- recessions have historically "
                     f"followed within roughly that window of an inversion ending.")
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


def threshold_value(ind):
    """The rule's threshold as a single scalar, in the same units
    metric_series returns. Mirrors the client's old static thresholdLine
    table -- computed here from params directly so there's one source of
    truth instead of two hand-kept copies."""
    p = ind["params"]
    rule = ind["rule"]
    if rule == "curve":
        return 0.0
    if rule in ("hy_spread", "level_above", "level_below",
                "level_or_rising", "level_and_rising"):
        return p["level"]
    if rule in ("drawdown", "drop_from_peak_ma"):
        return -p["drop"] * 100.0
    if rule in ("yoy_below", "yoy_above_weekly"):
        return p["pct"]
    if rule == "claims_vs_low":
        return p["rise"] * 100.0
    raise ValueError(rule)


def compute_position(threshold, typical, value):
    """UI-only distance-to-threshold, on a scale where 1.0 IS the threshold
    and 0 is the metric's own typical historical level -- so direction
    (whether red means above or below) falls out of the sign of
    (threshold - typical) automatically, no separate direction table needed.
    Not part of the scoring rules; purely for the app's distance bar."""
    denom = threshold - typical
    if abs(denom) < 1e-6:
        return 1.15 if value >= threshold else -0.15
    return round((value - typical) / denom, 4)


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

    if prev and prev.get("state") == state and prev.get("since"):
        since = date.fromisoformat(prev["since"])
    elif prev and prev.get("state") in ("red", "green"):
        since = today
    else:
        since, _ = bootstrap_indicator_since(ind, df, today, red)
    days_in_state = (today - since).days

    sparkline = [round(float(x), 4) for x in metric.tail(60).tolist()]
    threshold = threshold_value(ind)
    typical = float(metric.median())
    position = compute_position(threshold, typical, value)
    legs, position_basis = compute_legs(ind, df, today, metric)
    binding_leg = pick_binding_leg(red, legs, position_basis)

    return {
        "id": ind["id"],
        "name": ind["name"],
        "bucket": ind["bucket"],
        "role": ind["role"],
        "state": state,
        "value": round(value, 4),
        "unit": UNIT[ind["id"]],
        "threshold": round(threshold, 4),
        "position": position,
        "legs": legs,
        "binding_leg": binding_leg,
        "position_basis": position_basis,
        "threshold_text": threshold_text(ind),
        "why_text": why_text(ind, red, metric),
        "observation_date": df["date"].iloc[-1].date().isoformat(),
        "days_in_state": days_in_state,
        "since": since.isoformat(),
        "source_name": f"Federal Reserve (FRED: {sid})",
        "source_url": f"https://fred.stlouisfed.org/series/{sid}",
        "sparkline": sparkline,
    }, int(red)


def build_watchlist_item(item, fred):
    """No rule, no red/green -- just today's reading, for context. Never
    touches reds/available/fraction."""
    df = fred.observations(item["fred"])
    if df.empty:
        return {
            "id": item["id"], "name": item["name"], "unit": item["unit"],
            "what_is_this": item["what_is_this"], "value": None,
            "observation_date": None, "sparkline": [],
            "source_name": f"Federal Reserve (FRED: {item['fred']})",
            "source_url": f"https://fred.stlouisfed.org/series/{item['fred']}",
        }
    v = df["value"].reset_index(drop=True)
    return {
        "id": item["id"],
        "name": item["name"],
        "unit": item["unit"],
        "what_is_this": item["what_is_this"],
        "value": round(float(v.iloc[-1]), 4),
        "observation_date": df["date"].iloc[-1].date().isoformat(),
        "sparkline": [round(float(x), 4) for x in v.tail(60).tolist()],
        "source_name": f"Federal Reserve (FRED: {item['fred']})",
        "source_url": f"https://fred.stlouisfed.org/series/{item['fred']}",
    }


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
    # A spec version bump changes the rules, not the underlying reality --
    # yesterday's board.json was computed under different params, so its
    # per-indicator states aren't a valid continuity baseline. Re-bootstrap
    # from real history instead of reading a rule change as "changed today."
    spec_changed = bool(prev) and prev.get("spec_hash") != spec_hash
    prev_indicators = {} if spec_changed else {str(i["id"]): i for i in (prev or {}).get("indicators", [])}

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

    watchlist_out = [build_watchlist_item(item, fred) for item in WATCHLIST]

    board_df = pd.DataFrame([row])
    scored = score_board(board_df, SPEC).iloc[0]

    tier_raw = scored["tier"]
    tier = "QUIET" if tier_raw == "-" else tier_raw

    if prev and not spec_changed and prev.get("board", {}).get("tier") == tier:
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
        "watchlist": watchlist_out,
    }

    Path(args.out).write_text(json.dumps(board, indent=2) + "\n")
    print(f"wrote {args.out}: {board['board']['reds']}/{board['board']['available']} red, tier {tier}")


if __name__ == "__main__":
    main()
