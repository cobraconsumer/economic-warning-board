# App Store listing — draft

## App name
Economic Warning Board

## Subtitle (30 chars max)
20 recession indicators, free

## Promotional text (170 chars max, editable without review)
Free government data, 20 indicators, one honest number. Quiet most of the time — which is the point. No predictions, no advice, no accounts.

## Description

A 20-indicator recession watchlist, built entirely from free government data
and updated once a day. No accounts, no subscriptions, no predictions.

**One number.** How many of 20 economic indicators are currently flashing
red — yield curve inversion, credit spreads, housing permits, unemployment
claims, and more, spanning credit markets, business activity, and household
finances. Tap any of them for a plain-English explanation of what it is,
what it's showing right now, and exactly what would make it red.

**Green gets explained too.** Every indicator's reading — red or green —
comes with a one-sentence reason. That's deliberate: a board that only
explains bad news trains you to expect bad news. This one explains both.

**Tested against 35 years of history.** The rules were backtested against
every US recession since 1988, not tuned after the fact. Out-of-sample, the
board's early-warning tier led the last three recessions by 12, 4, and 5
months, and never issued a false Warning-tier reading across four major
market scares (1998, 2011, 2015–16, 2022). The full methodology, spec, and
backtest results are public — see the in-app Methodology screen or the
GitHub repo.

**What this is not.** Not a prediction. Not a probability. Not financial
advice. Not a recommendation to buy or sell anything. It's an instrument
reading, not a forecast — and it says so, in the app, not just here.

**No subscription.** Running this costs nothing to operate, so there's
nothing to charge you for month after month.

## Keywords (100 chars max, comma-separated, no spaces after commas)
recession,economy,indicators,yield curve,fred,market,warning,economic data,indicator,downturn

## What's New (v1.0)
First release: the 20-indicator board, indicator detail screens, full
methodology and track record, and local notifications when the tier
changes (never on individual indicators).

## Support URL
https://github.com/cobraconsumer/economic-warning-board

## Marketing URL (optional)
https://github.com/cobraconsumer/economic-warning-board

## App Review notes
- Government data sources only (FRED). No user accounts, no financial
  connections, no purchases, no advice given.
- The methodology, spec, and full backtest results are public in the linked
  repo. The in-app Methodology screen states plainly that this is not a
  prediction, probability, or financial advice.
- Local notifications only (no push infrastructure); fires only on a tier
  change, never per-indicator.
- Free with the methodology public — no subscription to justify, since
  running costs are $0 (a daily GitHub Action + static JSON on GitHub
  Pages).

## Category
Finance (primary) — consider Business as secondary if allowed.

## Age rating
4+ — no objectionable content; note in review that it displays financial/
economic data only, no gambling, no trading, no user-generated content.

## Price
Free, or $1.99 one-time (per spec: no subscription, since there's no
ongoing cost to cover). Recommend shipping free for v1 — strongest trust
position, and this is a credibility play before a revenue play.
