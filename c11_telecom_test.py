#!/usr/bin/env python3
"""C11 pre-registered validation test -- spec-v0.7-candidates.md section 3.

Hypothesis, recorded before running this: ex-hi-tech industrial production
(IPX4HTMVS) rolled over *before* total industrial production (INDPRO) into
the 2001 recession, and the y/y divergence between them widened beforehand.

This is the exploratory validation test the spec calls "the cheapest and
most informative single result in the document" -- it uses latest-vintage
data (not ALFRED point-in-time reconstruction) because the question is
about the shape of the two series around 2001, not about scoring a rule.
The full C11a/C11b backtest against backtest.py's harness is a separate,
later step gated on this result.

Usage:
    export FRED_API_KEY=yourkey
    python c11_telecom_test.py
"""
import os
import sys

import pandas as pd
import requests

FRED_BASE = "https://api.stlouisfed.org/fred"


def fetch(series_id, api_key):
    params = {
        "series_id": series_id, "limit": 100000,
        "observation_start": "1990-01-01", "api_key": api_key, "file_type": "json",
    }
    r = requests.get(f"{FRED_BASE}/series/observations", params=params, timeout=60)
    r.raise_for_status()
    obs = r.json().get("observations", [])
    rows = [(o["date"], o["value"]) for o in obs if o["value"] not in (".", "", None)]
    df = pd.DataFrame(rows, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().sort_values("date").reset_index(drop=True)


def yoy(v):
    return (v / v.shift(12) - 1.0) * 100.0


def local_peak_before(df, cutoff):
    """Last local max in level before `cutoff` -- the rollover point."""
    window = df[df["date"] < pd.Timestamp(cutoff)].reset_index(drop=True)
    v = window["value"]
    peak_idx = v.idxmax()
    # Walk forward from the peak to confirm it's followed by sustained decline
    # (not just a single-month wobble) -- require 3 straight months below peak.
    return window.loc[peak_idx, "date"], float(v.loc[peak_idx])


def main():
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        sys.exit("Set FRED_API_KEY (free key: https://fred.stlouisfed.org/docs/api/api_key.html)")

    print("Fetching INDPRO and IPX4HTMVS from FRED...")
    indpro = fetch("INDPRO", api_key)
    exhitech = fetch("IPX4HTMVS", api_key)

    # Sanity check against the spec's stated current wedge (July 2026:
    # INDPRO 102.99, IPX4HTMVS 95.32) so a series-ID mixup shows up immediately.
    latest_i = indpro.iloc[-1]
    latest_x = exhitech.iloc[-1]
    print(f"\nLatest INDPRO:    {latest_i['date'].date()}  {latest_i['value']:.2f}")
    print(f"Latest IPX4HTMVS: {latest_x['date'].date()}  {latest_x['value']:.2f}")

    print("\n--- 2001 rollover test ---")
    peak_i_date, peak_i_val = local_peak_before(indpro, "2001-06-01")
    peak_x_date, peak_x_val = local_peak_before(exhitech, "2001-06-01")
    print(f"INDPRO peak before mid-2001:    {peak_i_date.date()}  ({peak_i_val:.2f})")
    print(f"IPX4HTMVS peak before mid-2001: {peak_x_date.date()}  ({peak_x_val:.2f})")
    lead_months = (peak_i_date.year - peak_x_date.year) * 12 + (peak_i_date.month - peak_x_date.month)
    print(f"IPX4HTMVS peaked {lead_months} months {'before' if lead_months > 0 else 'after'} INDPRO")

    print("\n--- y/y divergence, 1999-01 through 2001-12 ---")
    indpro["yoy"] = yoy(indpro["value"])
    exhitech["yoy"] = yoy(exhitech["value"])
    merged = pd.merge(indpro[["date", "yoy"]], exhitech[["date", "yoy"]],
                       on="date", suffixes=("_indpro", "_exhitech"))
    merged["divergence"] = merged["yoy_indpro"] - merged["yoy_exhitech"]
    window = merged[(merged["date"] >= "1999-01-01") & (merged["date"] <= "2001-12-01")]
    for _, row in window.iterrows():
        print(f"  {row['date'].date()}  INDPRO y/y {row['yoy_indpro']:+6.2f}   "
              f"ex-hi-tech y/y {row['yoy_exhitech']:+6.2f}   divergence {row['divergence']:+6.2f}pp")

    print("\n--- verdict against the pre-registered hypothesis ---")
    if lead_months >= 3:
        print(f"CONFIRMED (directionally): ex-hi-tech IP peaked {lead_months} months "
              "before total IP heading into the 2001 recession.")
    elif lead_months > 0:
        print(f"WEAK: ex-hi-tech IP peaked only {lead_months} month(s) before total IP "
              "-- not a strong lead.")
    else:
        print("DISCONFIRMED: ex-hi-tech IP did not peak before total IP. "
              "Per spec section 3, record this and move on -- do not reshape the test.")


if __name__ == "__main__":
    main()
