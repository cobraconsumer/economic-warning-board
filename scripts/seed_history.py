#!/usr/bin/env python3
"""One-time seed: turn results_v03/scored_v03.csv (the frozen v0.3 backtest) into
history_seed.json — the static monthly {date, fraction, tier} array board.json ships
with. evaluate.py appends today's live reading on top of this each run.

Usage:
    python scripts/seed_history.py --csv results_v03/scored_v03.csv --out history_seed.json
"""

import argparse
import json
from pathlib import Path

import pandas as pd

TIER_MAP = {"-": "QUIET", "WATCH": "WATCH", "WARNING": "WARNING", "BROAD": "BROAD"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results_v03/scored_v03.csv")
    ap.add_argument("--out", default="history_seed.json")
    args = ap.parse_args()

    df = pd.read_csv(args.csv, parse_dates=["date"])
    rows = [
        {
            "date": r["date"].date().isoformat(),
            "fraction": round(float(r["fraction"]), 4),
            "tier": TIER_MAP[r["tier"]],
        }
        for _, r in df.sort_values("date").iterrows()
    ]
    Path(args.out).write_text(json.dumps(rows, indent=2) + "\n")
    print(f"wrote {len(rows)} monthly rows ({rows[0]['date']} .. {rows[-1]['date']}) to {args.out}")


if __name__ == "__main__":
    main()
